"""
Optimized FastAPI server with:
- O(1) job lookups using dict (active jobs only)
- SQLite database for persistent storage of completed runs
- Cached regex patterns
- Minimal string operations
- Efficient JSON serialization
- GitHub OAuth authentication
- Per-user GitHub token management
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from functools import lru_cache
import asyncio
import uuid
import json
import os
import pathlib
import time
import subprocess
import re
import urllib.request
import urllib.parse
import urllib.error

from database import init_db, save_user, get_user_by_github_id, save_run, get_user_runs

load_dotenv()

# Initialize database
init_db()

app = FastAPI(title="RIFT Healing Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
def startup_event():
    """Initialize database tables on server startup."""
    init_db()
    print("[STARTUP] Database initialized successfully")

# In-memory store for ACTIVE jobs only (needed for SSE streaming)
jobs: dict = {}  # O(1) lookup by job_id

# Pre-compiled regex patterns for O(1) reuse
URL_PATTERN = re.compile(r'^https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$')
CLEAN_PATTERN = re.compile(r'[^A-Z0-9_]')

class RunRequest(BaseModel):
    github_url: str
    team_name: str
    leader_name: str
    branch_name: str = None

@lru_cache(maxsize=256)
def validate_github_url(url: str) -> str:
    """Cached URL validation - O(1) for repeated URLs."""
    url = url.strip().rstrip("/")
    
    match = URL_PATTERN.match(url)
    if not match:
        return "Invalid URL format. Expected: https://github.com/owner/repo"
    
    owner, repo = match.groups()
    if not owner or not repo:
        return "Invalid URL format. Expected: https://github.com/owner/repo"
    
    return None  # valid

def check_repo_exists(github_url: str, github_token: str) -> str:
    """Fast repo existence check with timeout."""
    url = github_url.strip().rstrip("/")
    if not url.endswith(".git"):
        url = url + ".git"
    
    auth_url = url.replace("https://", f"https://x-token:{github_token}@") if github_token else url
    
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--exit-code", auth_url, "HEAD"],
            capture_output=True, text=True, timeout=10  # Reduced timeout
        )
        
        if result.returncode == 0:
            return None
        
        stderr_lower = result.stderr.lower()
        if "not found" in stderr_lower or "repository" in stderr_lower:
            return f"Repository not found: {github_url}"
        elif "authentication" in stderr_lower or "denied" in stderr_lower or "403" in stderr_lower:
            return "GitHub token is invalid or expired"
        elif "could not resolve" in stderr_lower:
            return "Cannot reach GitHub"
        else:
            return f"Repository not accessible: {github_url}"
    
    except subprocess.TimeoutExpired:
        return "Timed out connecting to GitHub"
    except FileNotFoundError:
        return "Git is not installed"
    except Exception as e:
        return f"GitHub validation failed: {str(e)}"

@lru_cache(maxsize=256)
def clean_name(name: str) -> str:
    """Cached name cleaning - O(1) for repeated names."""
    cleaned = CLEAN_PATTERN.sub('_', name.upper().replace(" ", "_"))
    return re.sub(r'_+', '_', cleaned).strip('_')

# ─── GitHub OAuth Endpoints ───────────────────────────────────────

class GitHubAuthRequest(BaseModel):
    code: str

class TokenVerifyRequest(BaseModel):
    github_token: str

@app.post("/api/auth/github")
async def auth_github(req: GitHubAuthRequest):
    """Exchange GitHub OAuth code for access token and save user."""
    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return JSONResponse(status_code=500, content={"detail": "GitHub OAuth not configured"})
    
    # Exchange code for token
    try:
        token_data_str = json.dumps({"client_id": client_id, "client_secret": client_secret, "code": req.code})
        token_req = urllib.request.Request(
            "https://github.com/login/oauth/access_token",
            data=token_data_str.encode('utf-8'),
            headers={"Accept": "application/json", "Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(token_req, timeout=10) as token_resp:
            token_data = json.loads(token_resp.read().decode('utf-8'))
        
        access_token = token_data.get("access_token")
        
        if not access_token:
            error = token_data.get("error_description", "No access token returned")
            return JSONResponse(status_code=400, content={"detail": error})
        
        # Fetch user profile
        user_req = urllib.request.Request(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        )
        
        with urllib.request.urlopen(user_req, timeout=10) as user_resp:
            user_data = json.loads(user_resp.read().decode('utf-8'))
    
    except urllib.error.HTTPError as e:
        return JSONResponse(status_code=400, content={"detail": f"GitHub API error: {e.code}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"OAuth failed: {str(e)}"})
    
    # Save user to database
    user_id = save_user(
        github_id=str(user_data.get("id")),
        username=user_data.get("login", ""),
        email=user_data.get("email", ""),
        avatar_url=user_data.get("avatar_url", ""),
        github_token=access_token
    )
    
    print(f"[AUTH] User {user_data.get('login')} logged in (id={user_id})")
    
    return {
        "user_id": user_id,
        "username": user_data.get("login"),
        "avatar_url": user_data.get("avatar_url"),
        "github_token": access_token
    }

@app.post("/api/auth/verify-token")
async def verify_token(req: TokenVerifyRequest):
    """Verify a GitHub token is valid."""
    try:
        user_req = urllib.request.Request(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {req.github_token}", "Accept": "application/json"}
        )
        
        with urllib.request.urlopen(user_req, timeout=10) as resp:
            user_data = json.loads(resp.read().decode('utf-8'))
        
        # Save/update user in DB
        user_id = save_user(
            github_id=str(user_data.get("id")),
            username=user_data.get("login", ""),
            email=user_data.get("email", ""),
            avatar_url=user_data.get("avatar_url", ""),
            github_token=req.github_token
        )
        
        return {
            "user_id": user_id,
            "username": user_data.get("login"),
            "avatar_url": user_data.get("avatar_url"),
            "github_token": req.github_token
        }
    except urllib.error.HTTPError:
        return JSONResponse(status_code=401, content={"detail": "Invalid GitHub token"})

@app.get("/api/auth/me")
async def get_me(authorization: str = Header(None)):
    """Get current user info from token."""
    if not authorization:
        return JSONResponse(status_code=401, content={"detail": "No token provided"})
    
    token = authorization.replace("Bearer ", "").replace("token ", "")
    
    try:
        user_req = urllib.request.Request(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}
        )
        
        with urllib.request.urlopen(user_req, timeout=10) as resp:
            user_data = json.loads(resp.read().decode('utf-8'))
        
        return {
            "username": user_data.get("login"),
            "avatar_url": user_data.get("avatar_url"),
            "email": user_data.get("email")
        }
    except urllib.error.HTTPError:
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})

@app.get("/api/auth/client-id")
async def get_client_id():
    """Return the GitHub OAuth client ID for frontend redirect."""
    client_id = os.getenv("GITHUB_CLIENT_ID")
    if not client_id:
        return JSONResponse(status_code=500, content={"detail": "OAuth not configured"})
    return {"client_id": client_id}

# ─── Run Agent ────────────────────────────────────────────────────

@app.post("/api/run-agent")
async def run_agent(req: RunRequest, bg: BackgroundTasks, authorization: str = Header(None)):
    """Optimized run agent endpoint. Uses user's OAuth token or falls back to .env."""
    
    # Fast validation
    url_error = validate_github_url(req.github_url)
    if url_error:
        return JSONResponse(status_code=400, content={"detail": url_error})
    
    # Get GitHub token: user's OAuth token first, then .env fallback
    github_token = None
    if authorization:
        github_token = authorization.replace("Bearer ", "").replace("token ", "")
    if not github_token:
        github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        return JSONResponse(status_code=401, content={"detail": "No GitHub token. Please login with GitHub first."})
    
    # Async repo check (non-blocking)
    repo_error = check_repo_exists(req.github_url, github_token)
    if repo_error:
        return JSONResponse(status_code=400, content={"detail": repo_error})
    
    # Fast branch name generation with caching
    team_clean = clean_name(req.team_name)
    leader_clean = clean_name(req.leader_name)
    branch = f"{team_clean}_{leader_clean}_AI_Fix"
    
    # Fast job creation
    job_id = str(uuid.uuid4())
    current_time = time.time()
    
    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "branch_name": branch,
        "current_agent": "Initializing",
        "errors_found": 0,
        "errors_fixed": 0,
        "commit_count": 0,
        "timeline": [],
        "fixes": [],
        "score": {},
        "repo_url": req.github_url,
        "team_name": req.team_name,
        "leader_name": req.leader_name,
        "start_time": current_time,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(current_time)),
        "verify_passed": False,
        "repo_language": "unknown",
        "push_success": False,
        "ci_status": "PENDING"
    }
    
    bg.add_task(run_pipeline, job_id, req, branch, github_token)
    
    return {"job_id": job_id, "branch_name": branch}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """O(1) job status lookup."""
    return jobs.get(job_id, {"error": "Not found"})

@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """Results lookup: in-memory → file cache → database."""
    # Check active jobs first (O(1))
    if job_id in jobs:
        return jobs[job_id]
    
    # Check file cache
    path = pathlib.Path(f"results/{job_id}.json")
    if path.exists():
        return json.loads(path.read_text())
    
    # Check database (persistent storage)
    db = SessionLocal()
    try:
        run = crud.get_run(db, job_id)
        if run:
            return run.to_dict()
    finally:
        db.close()
    
    return {"error": "Not found"}

@app.get("/api/stream/{job_id}")
async def stream(job_id: str):
    """Optimized SSE streaming with reduced polling."""
    async def generator():
        last_status = None
        
        while True:
            job = jobs.get(job_id)
            if not job:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Job not found'})}\n\n"
                break
            
            # Only send if status changed (reduces bandwidth)
            current_status = job.get("status")
            if current_status != last_status or current_status in ("done", "failed"):
                yield f"data: {json.dumps(job, default=str)}\n\n"
                last_status = current_status
            
            if current_status in ("done", "failed"):
                break
            
            await asyncio.sleep(0.3)  # Reduced polling interval
    
    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Connection": "keep-alive"
        }
    )

def archive_job(job_id: str):
    """Archive completed job to database for persistent storage."""
    if job_id not in jobs:
        return
    
    job_data = jobs[job_id].copy()
    job_data["job_id"] = job_id
    
    # Ensure timestamp
    if "timestamp" not in job_data:
        job_data["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    # Compute elapsed time
    start = job_data.get("start_time", time.time())
    elapsed = time.time() - start
    
    if "score" not in job_data or not isinstance(job_data["score"], dict):
        job_data["score"] = {}
    
    job_data["score"]["elapsed_seconds"] = elapsed
    
    if "total" not in job_data["score"]:
        job_data["score"]["total"] = job_data.get("errors_fixed", 0) * 10 + (20 if job_data.get("ci_status") == "PASSED" else 0)
    
    # Persist to database using save_run
    try:
        default_user_id = save_user(
            github_id="default",
            username="default_user",
            email="",
            avatar_url="",
            github_token=""
        )
        save_run(job_id, default_user_id, job_data)
        print(f"[ARCHIVE] Job {job_id} saved to database")
    except Exception as e:
        print(f"[ARCHIVE] Error saving job {job_id} to DB: {e}")

def run_pipeline(job_id: str, req: RunRequest, branch: str, github_token: str):
    """Run pipeline with error handling and database save."""
    try:
        jobs[job_id]["status"] = "cloning"
        jobs[job_id]["progress"] = 5
        jobs[job_id]["current_agent"] = "Clone Agent"
        
        from agent.orchestrator import HealingOrchestrator
        
        orchestrator = HealingOrchestrator(job_id, jobs)
        orchestrator.run(
            repo_url=req.github_url,
            branch_name=branch,
            github_token=github_token,
            team_name=req.team_name,
            leader_name=req.leader_name
        )
        
        # Save to database (with default user_id = 1)
        try:
            if job_id in jobs:
                # Ensure default user exists
                from database import save_user, save_run
                
                # Create/get default user
                default_user_id = save_user(
                    github_id="default",
                    username="default_user",
                    email="",
                    avatar_url="",
                    github_token=github_token
                )
                
                # Save run to database
                save_run(job_id, default_user_id, jobs[job_id])
                print(f"[DB] Saved run {job_id} to database")
        except Exception as db_error:
            print(f"[DB] Failed to save to database: {db_error}")
            # Don't fail the whole pipeline if DB save fails
            
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error_message"] = str(e)
        jobs[job_id]["progress"] = 0
        jobs[job_id]["ci_status"] = "FAILED"
        print(f"Pipeline error for {job_id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        archive_job(job_id)

@app.get("/api/health")
async def health():
    """Fast health check."""
    return {"status": "ok", "active_jobs": len(jobs)}

@app.get("/api/test-github")
async def test_github():
    """Test GitHub API connectivity."""
    try:
        req = urllib.request.Request("https://api.github.com/zen")
        with urllib.request.urlopen(req, timeout=5) as response:
            return {"status": "ok", "github_reachable": True, "message": response.read().decode('utf-8')}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/jobs")
async def list_jobs():
    """List active jobs - O(1) dict access."""
    return jobs

@app.get("/api/runs")
async def list_runs():
    """Return completed runs from database."""
    try:
        runs = get_user_runs(1, limit=100)
        return runs
    except Exception as e:
        return []

@app.get("/api/db/runs")
async def list_db_runs():
    """Get runs from database."""
    try:
        from database import get_user_runs
        # Get runs for default user (user_id = 1)
        runs = get_user_runs(1, limit=50)
        return runs
    except Exception as e:
        return {"error": str(e), "runs": []}

@app.get("/api/db/run/{job_id}")
async def get_db_run(job_id: str):
    """Get specific run from database."""
    try:
        from database import get_run_details
        run = get_run_details(job_id)
        if run:
            return run
        return {"error": "Run not found"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/stats")
async def get_stats():
    """Dashboard stats computed using direct O(1) SQLite aggregations."""
    try:
        import sqlite3
        from datetime import datetime
        conn = sqlite3.connect("data/rift_agent.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM runs WHERE status IN ('done', 'failed')")
        total_runs = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM runs WHERE status IN ('done', 'failed') AND ci_status='PASSED'")
        passed = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COALESCE(SUM(errors_fixed), 0) FROM runs WHERE status IN ('done', 'failed')")
        total_fixes = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COALESCE(AVG(elapsed_seconds), 0) FROM runs WHERE status IN ('done', 'failed')")
        avg_time = cursor.fetchone()[0] or 0

        # Bug types aggregation
        cursor.execute('''
            SELECT f.type, COUNT(f.id) 
            FROM fixes f 
            JOIN runs r ON f.run_id = r.id 
            WHERE r.status IN ('done', 'failed') 
            GROUP BY f.type
        ''')
        by_bug_type = {row[0] or "UNKNOWN": row[1] for row in cursor.fetchall()}

        now = datetime.now()
        this_month = now.month
        this_year = now.year
        last_month_num = 12 if this_month == 1 else this_month - 1
        last_year = this_year - 1 if this_month == 1 else this_year

        this_month_prefix = f"{this_year}-{this_month:02d}"
        last_month_prefix = f"{last_year}-{last_month_num:02d}"

        # Monthly Success rates
        cursor.execute('''
            SELECT substr(timestamp, 1, 7) as month, COUNT(id), SUM(CASE WHEN ci_status = 'PASSED' THEN 1 ELSE 0 END)
            FROM runs
            WHERE status IN ('done', 'failed') AND substr(timestamp, 1, 7) IN (?, ?)
            GROUP BY substr(timestamp, 1, 7)
        ''', (this_month_prefix, last_month_prefix))
        
        this_month_rate = 0
        last_month_rate = 0
        for row in cursor.fetchall():
            rate = (row[2] / row[1] * 100) if row[1] > 0 else 0
            if row[0] == this_month_prefix:
                this_month_rate = rate
            elif row[0] == last_month_prefix:
                last_month_rate = rate

        # By Day grouping using python for last 7 days bounded calculation
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        by_day = {day_names[(now.weekday() - i) % 7]: {"runs": 0, "fixes": 0} for i in range(6, -1, -1)}
        
        fallback_epoch_ts = time.time() - 7 * 86400

        cursor.execute('''
            SELECT timestamp, errors_fixed FROM runs 
            WHERE status IN ('done', 'failed') 
            AND (start_time >= ? OR start_time IS NULL)
        ''', (fallback_epoch_ts,))

        for row in cursor.fetchall():
            ts, r_fixes = row
            try:
                if ts:
                    dt = datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")
                    if (now - dt).days <= 7:
                        dn = day_names[dt.weekday()]
                        if dn in by_day:
                            by_day[dn]["runs"] += 1
                            by_day[dn]["fixes"] += (r_fixes or 0)
            except Exception:
                pass

        conn.close()
        
        return {
            "totalRuns": total_runs,
            "successRate": round((passed / total_runs * 100) if total_runs > 0 else 0, 1),
            "totalFixes": total_fixes,
            "avgFixTime": round(avg_time, 1),
            "byBugType": by_bug_type,
            "thisMonth": round(this_month_rate, 1),
            "lastMonth": round(last_month_rate, 1),
            "byDay": by_day
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"totalRuns": 0, "successRate": 0, "totalFixes": 0, "avgFixTime": 0, "byBugType": {}, "thisMonth": 0, "lastMonth": 0, "byDay": {}}

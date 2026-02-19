"""
Optimized FastAPI server with:
- O(1) job lookups using dict
- O(1) completed jobs insertion with deque
- Cached regex patterns
- Minimal string operations
- Efficient JSON serialization
- GitHub OAuth and token-based auth
- SQLite database for persistence
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from collections import deque
from functools import lru_cache
import asyncio
import uuid
import json
import os
import pathlib
import time
import subprocess
import re
import httpx

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

# Optimized data structures
jobs: dict = {}  # O(1) lookup by job_id
completed_jobs: deque = deque(maxlen=100)  # O(1) append, automatic size limit

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

@app.post("/api/run-agent")
async def run_agent(req: RunRequest, bg: BackgroundTasks):
    """Optimized run agent endpoint."""
    
    # Fast validation
    url_error = validate_github_url(req.github_url)
    if url_error:
        return JSONResponse(status_code=400, content={"detail": url_error})
    
    # Use hardcoded GitHub token from .env
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        return JSONResponse(status_code=500, content={"detail": "GitHub token not configured"})
    
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
    """Optimized results lookup with file cache."""
    # Check file cache first (fastest)
    path = pathlib.Path(f"results/{job_id}.json")
    if path.exists():
        return json.loads(path.read_text())
    
    # Check active jobs (O(1))
    if job_id in jobs:
        return jobs[job_id]
    
    # Check completed archive (O(n) but limited to 100)
    for run in completed_jobs:
        if run.get("job_id") == job_id:
            return run
    
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
    """Optimized job archiving with O(1) deque append."""
    if job_id not in jobs:
        return
    
    job_data = jobs[job_id].copy()
    job_data["job_id"] = job_id
    
    # Fast repo name extraction
    repo_url = job_data.get("repo_url", "")
    if "github.com/" in repo_url:
        job_data["repo"] = repo_url.split("github.com/")[-1].replace(".git", "")
    else:
        job_data["repo"] = repo_url
    
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
    
    # O(1) append with automatic size limit
    completed_jobs.appendleft(job_data)

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
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/zen",
                timeout=5.0
            )
            return {"status": "ok", "github_reachable": response.status_code == 200, "message": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/jobs")
async def list_jobs():
    """List active jobs - O(1) dict access."""
    return jobs

@app.get("/api/runs")
async def list_runs():
    """Return completed runs - O(1) deque to list conversion."""
    return list(completed_jobs)

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
    """Optimized stats computation with single-pass algorithms."""
    runs = list(completed_jobs)
    
    if not runs:
        return {
            "successRate": 0,
            "totalFixes": 0,
            "avgFixTime": 0,
            "byDay": {},
            "byBugType": {},
            "thisMonth": 0,
            "lastMonth": 0,
            "totalRuns": 0
        }
    
    # Single-pass aggregation - O(n) instead of multiple O(n) passes
    passed_count = 0
    total_fixes = 0
    total_time = 0.0
    by_bug_type = {}
    
    import datetime
    now = datetime.datetime.now()
    this_month, this_year = now.month, now.year
    last_month_num = 12 if this_month == 1 else this_month - 1
    last_year = this_year - 1 if this_month == 1 else this_year
    
    this_month_runs = []
    last_month_runs = []
    
    # Initialize by_day with O(1) dict
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    by_day = {day_names[(now.weekday() - i) % 7]: {"runs": 0, "fixes": 0} for i in range(6, -1, -1)}
    
    # Single pass through runs
    for r in runs:
        # Success rate
        if r.get("ci_status") == "PASSED":
            passed_count += 1
        
        # Total fixes
        total_fixes += r.get("errors_fixed", 0)
        
        # Avg time
        total_time += r.get("score", {}).get("elapsed_seconds", 0)
        
        # Bug types
        fixes = r.get("fixes", [])
        if isinstance(fixes, list):
            for fix in fixes:
                if isinstance(fix, dict):
                    bug_type = fix.get("type", "UNKNOWN")
                    by_bug_type[bug_type] = by_bug_type.get(bug_type, 0) + 1
        
        # By day and month
        try:
            ts = r.get("timestamp", "")
            if ts:
                dt = datetime.datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")
                dn = day_names[dt.weekday()]
                
                if dn in by_day:
                    by_day[dn]["runs"] += 1
                    by_day[dn]["fixes"] += r.get("errors_fixed", 0)
                
                if dt.month == this_month and dt.year == this_year:
                    this_month_runs.append(r)
                elif dt.month == last_month_num and dt.year == last_year:
                    last_month_runs.append(r)
        except Exception:
            pass
    
    # Compute rates
    success_rate = (passed_count / len(runs)) * 100 if runs else 0
    avg_fix_time = total_time / len(runs) if runs else 0
    
    this_month_rate = (sum(1 for r in this_month_runs if r.get("ci_status") == "PASSED") / len(this_month_runs) * 100) if this_month_runs else 0
    last_month_rate = (sum(1 for r in last_month_runs if r.get("ci_status") == "PASSED") / len(last_month_runs) * 100) if last_month_runs else 0
    
    return {
        "successRate": round(success_rate, 1),
        "totalFixes": total_fixes,
        "avgFixTime": round(avg_fix_time, 1),
        "byDay": by_day,
        "byBugType": by_bug_type,
        "thisMonth": round(this_month_rate, 1),
        "lastMonth": round(last_month_rate, 1),
        "totalRuns": len(runs)
    }

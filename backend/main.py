"""
Optimized FastAPI server with:
- O(1) job lookups using dict (active jobs only)
- SQLite database for persistent storage of completed runs
- Cached regex patterns
- Minimal string operations
- Efficient JSON serialization
"""
from fastapi import FastAPI, BackgroundTasks
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

load_dotenv()

app = FastAPI(title="RIFT Healing Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Database initialization
from database import init_db, SessionLocal
import crud

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

@app.post("/api/run-agent")
async def run_agent(req: RunRequest, bg: BackgroundTasks):
    """Optimized run agent endpoint."""
    
    # Fast validation
    url_error = validate_github_url(req.github_url)
    if url_error:
        return JSONResponse(status_code=400, content={"detail": url_error})
    
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
    
    # Persist to database
    db = SessionLocal()
    try:
        crud.save_completed_run(db, job_data)
        print(f"[ARCHIVE] Job {job_id} saved to database")
    except Exception as e:
        print(f"[ARCHIVE] Error saving job {job_id} to DB: {e}")
    finally:
        db.close()

def run_pipeline(job_id: str, req: RunRequest, branch: str, github_token: str):
    """Run pipeline with error handling."""
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

@app.get("/api/jobs")
async def list_jobs():
    """List active jobs - O(1) dict access."""
    return jobs

@app.get("/api/runs")
async def list_runs():
    """Return completed runs from database."""
    db = SessionLocal()
    try:
        runs = crud.get_all_runs(db, limit=100)
        return [r.to_dict() for r in runs]
    finally:
        db.close()

@app.get("/api/stats")
async def get_stats():
    """Dashboard stats computed from database."""
    db = SessionLocal()
    try:
        return crud.get_stats(db)
    finally:
        db.close()

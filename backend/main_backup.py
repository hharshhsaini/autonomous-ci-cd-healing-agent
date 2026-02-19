from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import asyncio
import uuid
import json
import os
import pathlib
import time
import subprocess

load_dotenv()

app = FastAPI(title="RIFT Healing Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Active (in-progress) jobs
jobs: dict = {}

# Completed jobs archive — persists finished runs for the dashboard
completed_jobs: list = []

class RunRequest(BaseModel):
    github_url: str
    team_name: str
    leader_name: str
    branch_name: str = None  # optional override


def validate_github_url(url: str) -> str:
    """Basic validation that the URL looks like a valid GitHub repo URL."""
    url = url.strip().rstrip("/")
    if not url.startswith("https://github.com/"):
        return "Invalid URL. Must start with https://github.com/"
    
    # Extract owner/repo from URL
    path = url.replace("https://github.com/", "").replace(".git", "")
    parts = path.split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return "Invalid URL format. Expected: https://github.com/owner/repo"
    
    return None  # valid


def check_repo_exists(github_url: str, github_token: str) -> str:
    """Check if a GitHub repo exists using git ls-remote.
    Returns error message string, or None if repo exists."""
    url = github_url.strip().rstrip("/")
    if not url.endswith(".git"):
        url = url + ".git"
    
    # Inject token for auth
    if github_token:
        auth_url = url.replace("https://", f"https://x-token:{github_token}@")
    else:
        auth_url = url
    
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--exit-code", auth_url, "HEAD"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            return None  # repo exists
        
        stderr = result.stderr.lower()
        if "not found" in stderr or "repository" in stderr:
            return f"Repository not found: {github_url} — Check that the URL is correct and the repo is accessible with your token."
        elif "authentication" in stderr or "denied" in stderr or "403" in stderr:
            return "GitHub token is invalid or expired. Please update GITHUB_TOKEN in backend/.env"
        elif "could not resolve" in stderr:
            return "Cannot reach GitHub. Check your internet connection."
        else:
            return f"Repository not accessible: {github_url} — {result.stderr.strip()}"
    
    except subprocess.TimeoutExpired:
        return "Timed out connecting to GitHub. Check your internet connection."
    except FileNotFoundError:
        return "Git is not installed on the server."
    except Exception as e:
        return f"GitHub validation failed: {str(e)}"


def check_branch_exists(github_url: str, branch_name: str, github_token: str) -> str:
    """Check if a specific branch exists in the repo using git ls-remote."""
    url = github_url.strip().rstrip("/")
    if not url.endswith(".git"):
        url = url + ".git"
    
    if github_token:
        auth_url = url.replace("https://", f"https://x-token:{github_token}@")
    else:
        auth_url = url
    
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--heads", auth_url, branch_name],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and branch_name in result.stdout:
            return None  # branch exists
        elif result.returncode == 0:
            return f"Branch '{branch_name}' not found in repository. Check available branches at: {github_url}/branches"
        else:
            return None  # fail open if we can't check
    except Exception:
        return None  # fail open — don't block on branch check issues


@app.post("/api/run-agent")
async def run_agent(req: RunRequest, bg: BackgroundTasks):
    """Start a new healing agent job."""
    
    # 1. Validate GitHub URL format
    url_error = validate_github_url(req.github_url)
    if url_error:
        return JSONResponse(status_code=400, content={"detail": url_error})
    
    # 2. Get GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        return JSONResponse(
            status_code=500,
            content={"detail": "GitHub token not configured in backend. Please set GITHUB_TOKEN in backend/.env"}
        )
    
    # 3. Validate repo exists
    repo_error = check_repo_exists(req.github_url, github_token)
    if repo_error:
        return JSONResponse(status_code=400, content={"detail": repo_error})
    
    # 4. Generate branch name (always auto-generate from team and leader names)
    # Format: TEAMNAME_LEADERNAME_AI_Fix (all uppercase, spaces → underscores, no special chars)
    import re
    team_clean = re.sub(r'[^A-Z0-9_]', '_', req.team_name.upper().replace(" ", "_"))
    team_clean = re.sub(r'_+', '_', team_clean).strip('_')
    
    leader_clean = re.sub(r'[^A-Z0-9_]', '_', req.leader_name.upper().replace(" ", "_"))
    leader_clean = re.sub(r'_+', '_', leader_clean).strip('_')
    
    branch = f"{team_clean}_{leader_clean}_AI_Fix"
    
    # 5. Create job
    job_id = str(uuid.uuid4())
    
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
        "start_time": time.time(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verify_passed": False,
        "repo_language": "unknown",
        "push_success": False,
        "ci_status": "PENDING"
    }
    
    bg.add_task(run_pipeline, job_id, req, branch, github_token)
    
    return {"job_id": job_id, "branch_name": branch}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """Get current status of a job."""
    return jobs.get(job_id, {"error": "Not found"})

@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """Get final results of a completed job."""
    # Check saved results file first
    path = pathlib.Path(f"results/{job_id}.json")
    if path.exists():
        return json.loads(path.read_text())
    # Check active jobs
    if job_id in jobs:
        return jobs[job_id]
    # Check completed archive
    for run in completed_jobs:
        if run.get("job_id") == job_id:
            return run
    return {"error": "Not found"}

@app.get("/api/stream/{job_id}")
async def stream(job_id: str):
    """Stream real-time updates for a job."""
    async def generator():
        while True:
            job = jobs.get(job_id)
            if not job:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Job not found'}, default=str)}\n\n"
                break
            
            yield f"data: {json.dumps(job, default=str)}\n\n"
            
            if job.get("status") in ("done", "failed"):
                break
            
            await asyncio.sleep(0.5)
    
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
    """Move a finished job from active to completed archive."""
    if job_id in jobs:
        job_data = dict(jobs[job_id])
        job_data["job_id"] = job_id
        # Extract a clean repo name from URL
        repo_url = job_data.get("repo_url", "")
        if "github.com/" in repo_url:
            job_data["repo"] = repo_url.split("github.com/")[-1].replace(".git", "")
        else:
            job_data["repo"] = repo_url
        # Ensure timestamp exists
        if "timestamp" not in job_data:
            job_data["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        # Compute elapsed time
        start = job_data.get("start_time", time.time())
        elapsed = time.time() - start
        if "score" not in job_data or not isinstance(job_data["score"], dict):
            job_data["score"] = {}
        job_data["score"]["elapsed_seconds"] = elapsed
        # Compute a simple score total based on fixes
        if "total" not in job_data["score"]:
            job_data["score"]["total"] = job_data.get("errors_fixed", 0) * 10 + (20 if job_data.get("ci_status") == "PASSED" else 0)
        completed_jobs.insert(0, job_data)
        # Keep last 100 runs
        if len(completed_jobs) > 100:
            completed_jobs.pop()

def run_pipeline(job_id: str, req: RunRequest, branch: str, github_token: str):
    """Run the healing pipeline in background."""
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
        # Always archive the job when finished
        archive_job(job_id)


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "active_jobs": len(jobs)}

@app.get("/api/jobs")
async def list_jobs():
    """List all active jobs with full data."""
    return {
        jid: j for jid, j in jobs.items()
    }

@app.get("/api/runs")
async def list_runs():
    """Return all completed runs for the dashboard."""
    return completed_jobs

@app.get("/api/stats")
async def get_stats():
    """Return pre-computed dashboard statistics from completed runs."""
    runs = completed_jobs
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

    # Success rate
    passed = sum(1 for r in runs if r.get("ci_status") == "PASSED")
    success_rate = (passed / len(runs)) * 100 if runs else 0

    # Total fixes
    total_fixes = sum(r.get("errors_fixed", 0) for r in runs)

    # Avg fix time
    total_time = sum(r.get("score", {}).get("elapsed_seconds", 0) for r in runs)
    avg_fix_time = total_time / len(runs) if runs else 0

    # By day (last 7 days)
    import datetime
    now = datetime.datetime.now()
    by_day = {}
    for i in range(6, -1, -1):
        d = now - datetime.timedelta(days=i)
        day_names_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        dn = day_names_map[d.weekday()]
        by_day[dn] = {"runs": 0, "fixes": 0}

    for r in runs:
        try:
            ts = r.get("timestamp", "")
            if ts:
                dt = datetime.datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")
                day_names_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                dn = day_names_map[dt.weekday()]
                if dn in by_day:
                    by_day[dn]["runs"] += 1
                    by_day[dn]["fixes"] += r.get("errors_fixed", 0)
        except Exception:
            pass

    # By bug type
    by_bug_type = {}
    for r in runs:
        fixes = r.get("fixes", [])
        if isinstance(fixes, list):
            for fix in fixes:
                if isinstance(fix, dict):
                    bug_type = fix.get("type", "UNKNOWN")
                    by_bug_type[bug_type] = by_bug_type.get(bug_type, 0) + 1

    # This month vs last month
    this_month = now.month
    this_year = now.year
    last_month_num = 12 if this_month == 1 else this_month - 1
    last_year = this_year - 1 if this_month == 1 else this_year

    this_month_runs = []
    last_month_runs = []
    for r in runs:
        try:
            ts = r.get("timestamp", "")
            if ts:
                dt = datetime.datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")
                if dt.month == this_month and dt.year == this_year:
                    this_month_runs.append(r)
                elif dt.month == last_month_num and dt.year == last_year:
                    last_month_runs.append(r)
        except Exception:
            pass

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

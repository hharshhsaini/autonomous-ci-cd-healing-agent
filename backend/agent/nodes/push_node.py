import git
import json
import time
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict
from ..state import AgentState

def sanitize_branch_name(name: str) -> str:
    """Make any branch name valid for git.
    Rules:
    - No spaces → replace with _
    - No special chars except _ - and /
    - No double underscores
    - Max 100 chars
    - Must end with _AI_Fix if it doesn't already
    """
    name = name.strip()
    name = re.sub(r'[^a-zA-Z0-9_\-/.]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_').strip('-')
    
    if not name.upper().endswith('_AI_FIX'):
        name = name + '_AI_Fix'
    
    return name[:100]

def push_to_branch(state: AgentState) -> Dict:
    """Push fixes to a new branch and calculate final score."""
    try:
        # Check if any fixes were actually applied
        fixes_applied = [f for f in state["fixes"] if f.get("status") == "fixed"]
        fixes_failed = [f for f in state["fixes"] if f.get("status") == "failed"]
        
        print(f"[PUSH] Fixes applied: {len(fixes_applied)}, Fixes failed: {len(fixes_failed)}")
        
        # If all fixes failed and none succeeded, don't push
        if len(fixes_failed) > 0 and len(fixes_applied) == 0:
            error_msg = f"All {len(fixes_failed)} fixes failed - cannot push without successful fixes"
            print(f"[PUSH] ✗ {error_msg}")
            
            # Get the first failure reason
            first_failure = fixes_failed[0].get("fix_description", "Unknown error")
            
            return {
                "status": "failed",
                "error_message": error_msg,
                "progress": 100,
                "push_success": False,
                "ci_status": "FAILED",
                "timeline": state.get("timeline", []) + [{
                    "agent": "Git Push Agent",
                    "msg": f"✗ Cannot push - all fixes failed: {first_failure[:100]}",
                    "timestamp": datetime.now().isoformat(),
                    "iteration": state.get("retry_count", 0),
                    "passed": False
                }]
            }
        
        # Sanitize branch name first
        safe_branch = sanitize_branch_name(state["branch_name"])
        
        # Open repo
        repo = git.Repo(state["repo_path"])
        
        # Configure git identity
        repo.config_writer().set_value("user", "name", "RIFT AI Agent").release()
        repo.config_writer().set_value("user", "email", "agent@rift2026.ai").release()
        
        # Detach from current branch safely
        repo.git.checkout("HEAD", "--detach")
        
        # Delete branch if already exists locally
        for branch in repo.branches:
            if branch.name == safe_branch:
                repo.git.branch("-D", safe_branch)
                break
        
        # Create new branch from detached HEAD
        repo.git.checkout("-b", safe_branch)
        
        # Stage ALL changes (fixed files)
        repo.git.add(A=True)
        
        # Check if we have any fixes that were applied
        fixes_applied = [f for f in state["fixes"] if f.get("status") == "fixed"]
        
        # Commit if we have fixes OR if repo is dirty
        if fixes_applied or repo.is_dirty(untracked_files=True):
            # Build commit message from fixed error types
            types_fixed = list(set(f["type"] for f in fixes_applied))
            if types_fixed:
                summary = ", ".join(types_fixed)
                commit_msg = f"[AI-AGENT] Fix {len(fixes_applied)} errors: {summary}"
            else:
                commit_msg = f"[AI-AGENT] Apply code quality improvements"
            
            print(f"[PUSH] Committing: {commit_msg}")
            repo.index.commit(commit_msg)
            commit_count = state["commit_count"] + 1
            print(f"[PUSH] ✓ Committed changes (total commits: {commit_count})")
        else:
            commit_count = state["commit_count"]
            print(f"[PUSH] No changes to commit")
        
        # Push with token - MUST succeed for workflow to complete
        token = state.get("github_token", "")
        remote_url = state["repo_url"]
        
        if not token:
            raise Exception("GitHub token not configured - cannot push to remote")
        
        # Inject token into URL
        remote_url = remote_url.replace("https://", f"https://x-token:{token}@")
        
        # Push to remote - this MUST succeed
        origin = repo.remote("origin")
        origin.set_url(remote_url)
        
        print(f"[PUSH] Pushing branch {safe_branch} to {state['repo_url']}...")
        origin.push(refspec=f"{safe_branch}:{safe_branch}", force=True)
        print(f"[PUSH] ✓ Successfully pushed to branch {safe_branch}")
        
        push_success = True
        
        # CI status logic — CORRECT VERSION
        # PASSED = no errors found, OR all errors were fixed
        # FAILED = errors remain after max retries
        if state["errors_found"] == 0:
            ci_status = "PASSED"
            verify_passed = True
        elif state["errors_fixed"] == state["errors_found"]:
            ci_status = "PASSED"
            verify_passed = True
        elif state.get("verify_passed", False):
            ci_status = "PASSED"
            verify_passed = True
        else:
            ci_status = "FAILED"
            verify_passed = False
        
        # Calculate score
        elapsed = time.time() - state["start_time"]
        bonus = 10 if elapsed < 300 else 0
        over = max(0, commit_count - 20)
        penalty = over * 2
        score = {
            "base": 100,
            "speed_bonus": bonus,
            "penalty": penalty,
            "total": 100 + bonus - penalty,
            "elapsed_seconds": round(elapsed, 2),
            "commit_count": commit_count
        }
        
        # Write results.json with ALL fields
        results = {
            "job_id": state["job_id"],
            "repo_url": state["repo_url"],
            "repo_language": state.get("repo_language", "python"),
            "team_name": state["team_name"],
            "leader_name": state["leader_name"],
            "branch_name": safe_branch,
            "errors_found": state["errors_found"],
            "errors_fixed": state["errors_fixed"],
            "commit_count": commit_count,
            "verify_passed": verify_passed,
            "ci_status": ci_status,
            "push_success": push_success,
            "score": score,
            "fixes": state["fixes"],
            "timeline": state["timeline"],
            "repo_language": state.get("repo_language", "unknown")
        }
        
        # Write to backend/results/{job_id}.json for API access
        os.makedirs("results", exist_ok=True)
        Path(f"results/{state['job_id']}.json").write_text(
            json.dumps(results, indent=2, default=str)
        )
        
        return {
            "status": "done",
            "progress": 100,
            "branch_name": safe_branch,
            "score": score,
            "commit_count": commit_count,
            "verify_passed": verify_passed,
            "ci_status": ci_status,
            "push_success": True,
            "timeline": state["timeline"] + [{
                "agent": "Git Push Agent",
                "msg": f"✓ Committed {commit_count} change(s) and pushed to branch {safe_branch}",
                "timestamp": datetime.now().isoformat(),
                "iteration": state["retry_count"],
                "passed": True
            }]
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"[PUSH] ✗ Push failed: {error_msg}")
        return {
            "status": "failed",
            "error_message": f"Push failed: {error_msg}",
            "progress": 100,
            "push_success": False,
            "ci_status": "FAILED",
            "timeline": state.get("timeline", []) + [{
                "agent": "Git Push Agent",
                "msg": f"✗ Push failed: {error_msg}",
                "timestamp": datetime.now().isoformat(),
                "iteration": state.get("retry_count", 0),
                "passed": False
            }]
        }

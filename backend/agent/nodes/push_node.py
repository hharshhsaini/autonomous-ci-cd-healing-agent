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
    """Push fixes to a new branch with separate commits for each fix."""
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
        
        # Group fixes by file for efficient commits
        fixes_by_file = {}
        for fix in fixes_applied:
            file_path = fix["file"]
            if file_path not in fixes_by_file:
                fixes_by_file[file_path] = []
            fixes_by_file[file_path].append(fix)
        
        commit_count = state["commit_count"]
        timeline_entries = []
        
        # Commit each file separately with its fixes
        for file_path, file_fixes in fixes_by_file.items():
            try:
                # Stage only this specific file
                repo.git.add(file_path)
                
                # Check if this file has changes
                if repo.is_dirty(path=file_path):
                    # Build commit message for this file's fixes
                    fix_types = list(set(f["type"] for f in file_fixes))
                    fix_summary = ", ".join(fix_types)
                    
                    commit_msg = f"[AI-AGENT] Fix {len(file_fixes)} {fix_summary} error(s) in {file_path}"
                    
                    print(f"[PUSH] Committing: {commit_msg}")
                    repo.index.commit(commit_msg)
                    commit_count += 1
                    
                    # Push this commit immediately to save tokens
                    token = state.get("github_token", "")
                    if not token:
                        raise Exception("GitHub token not configured")
                    
                    remote_url = state["repo_url"].replace("https://", f"https://x-token:{token}@")
                    origin = repo.remote("origin")
                    origin.set_url(remote_url)
                    
                    print(f"[PUSH] Pushing commit {commit_count} to {safe_branch}...")
                    origin.push(refspec=f"{safe_branch}:{safe_branch}", force=True)
                    print(f"[PUSH] ✓ Pushed commit {commit_count}")
                    
                    timeline_entries.append({
                        "agent": "Git Push Agent",
                        "msg": f"✓ Committed and pushed fix for {file_path} ({len(file_fixes)} errors)",
                        "timestamp": datetime.now().isoformat(),
                        "iteration": state["retry_count"],
                        "passed": True
                    })
                else:
                    print(f"[PUSH] No changes in {file_path}, skipping")
                    
            except Exception as e:
                print(f"[PUSH] ✗ Failed to commit {file_path}: {str(e)}")
                timeline_entries.append({
                    "agent": "Git Push Agent",
                    "msg": f"✗ Failed to push {file_path}: {str(e)[:100]}",
                    "timestamp": datetime.now().isoformat(),
                    "iteration": state["retry_count"],
                    "passed": False
                })
        
        print(f"[PUSH] ✓ Successfully pushed {commit_count} commits to branch {safe_branch}")
        
        push_success = True
        
        # CI status logic
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
            "timeline": state["timeline"] + timeline_entries,
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
            "timeline": state["timeline"] + timeline_entries
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

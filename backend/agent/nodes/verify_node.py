import subprocess
import os
from datetime import datetime
from typing import Dict
from ..state import AgentState

def verify_fixes(state: AgentState) -> Dict:
    """Verify that fixes resolved the errors by re-running tests."""
    print(f"[VERIFY] Starting verification (iteration {state['retry_count'] + 1}/{state['retry_limit']})")
    
    # If no errors were found at all — clean repo — PASS immediately
    if state["errors_found"] == 0:
        print(f"[VERIFY] ✓ Repository is clean - no errors detected")
        return {
            "verify_passed": True,
            "status": "pushing",
            "progress": 92,
            "current_agent": "Git Push Agent",
            "timeline": state["timeline"] + [{
                "agent": "Verify Agent",
                "msg": "Repository is already clean — no errors detected",
                "timestamp": datetime.now().isoformat(),
                "iteration": 0,
                "passed": True
            }]
        }
    
    # Re-run tests on patched repo
    lang = state.get("repo_language", "python")
    repo_path = state["repo_path"]
    verify_output = ""
    
    try:
        if lang == "python":
            # Run flake8
            verify_output += "=FLAKE8=\n"
            try:
                result = subprocess.run(
                    ["flake8", ".", "--max-line-length=120", 
                     "--exclude=.git,__pycache__,node_modules,venv,dist,build",
                     "--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                verify_output += result.stdout + result.stderr
            except:
                pass
            
            # Run mypy
            verify_output += "\n=MYPY=\n"
            try:
                result = subprocess.run(
                    ["mypy", ".", "--ignore-missing-imports"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                verify_output += result.stdout + result.stderr
            except:
                pass
            
            # Run pytest
            verify_output += "\n=PYTEST=\n"
            try:
                result = subprocess.run(
                    ["pytest", "--tb=short", "-q"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                verify_output += result.stdout + result.stderr
            except:
                pass
        
        elif lang in ("javascript", "typescript"):
            verify_output += "=ESLINT=\n"
            try:
                result = subprocess.run(
                    ["npx", "--yes", "eslint", ".", "--ext", ".js,.jsx,.ts,.tsx", "--format", "compact"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                verify_output += result.stdout + result.stderr
            except:
                pass
        
        elif lang == "go":
            # Run go build
            verify_output += "=GOBUILD=\n"
            try:
                result = subprocess.run(
                    ["go", "build", "./..."],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                verify_output += result.stdout + result.stderr
            except:
                pass
            
            # Run go vet
            verify_output += "\n=GOVET=\n"
            try:
                result = subprocess.run(
                    ["go", "vet", "./..."],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                verify_output += result.stdout + result.stderr
            except:
                pass
            
            # Run go test
            verify_output += "\n=GOTEST=\n"
            try:
                result = subprocess.run(
                    ["go", "test", "./...", "-v"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                verify_output += result.stdout + result.stderr
            except:
                pass
    
    except Exception as e:
        verify_output = f"ERROR: {str(e)}"
    
    # Parse remaining errors
    from .analyze_node import analyze_errors
    temp_state = {**state, "raw_test_output": verify_output, "timeline": []}
    analysis = analyze_errors(temp_state)
    remaining = analysis.get("fixes", [])
    
    iteration = state["retry_count"]
    passed = len(remaining) == 0
    
    timeline_event = {
        "agent": "Verify Agent",
        "msg": f"Iteration {iteration + 1}/5 — {len(remaining)} errors remaining" if not passed else "All errors fixed — tests passing",
        "timestamp": datetime.now().isoformat(),
        "iteration": iteration,
        "passed": passed
    }
    
    print(f"[VERIFY] {'✓' if passed else '✗'} Verification result: {len(remaining)} errors remaining")
    
    if passed:
        return {
            "verify_passed": True,
            "status": "pushing",
            "progress": 92,
            "current_agent": "Git Push Agent",
            "timeline": state["timeline"] + [timeline_event]
        }
    elif state["retry_count"] < state["retry_limit"]:
        return {
            "fixes": remaining,
            "errors_found": len(remaining),
            "verify_passed": False,
            "retry_count": state["retry_count"] + 1,
            "status": "fixing",
            "progress": 60,
            "current_agent": "Fix Agent",
            "timeline": state["timeline"] + [timeline_event]
        }
    else:
        # Max retries hit — push whatever was fixed
        return {
            "verify_passed": False,
            "status": "pushing",
            "progress": 92,
            "current_agent": "Git Push Agent",
            "timeline": state["timeline"] + [timeline_event]
        }

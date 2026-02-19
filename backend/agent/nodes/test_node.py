import subprocess
import os
from datetime import datetime
from typing import Dict
from ..state import AgentState

def detect_language(repo_path: str) -> str:
    """Detect primary language - supports Python, JS, TS, Go only."""
    counts = {"python": 0, "javascript": 0, "typescript": 0, "go": 0}
    ext_map = {
        ".py": "python",
        ".js": "javascript", ".jsx": "javascript",
        ".ts": "typescript", ".tsx": "typescript",
        ".go": "go"
    }
    skip_dirs = {'.git', 'node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build', '.next'}
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in ext_map:
                counts[ext_map[ext]] += 1
    
    return max(counts, key=counts.get) if any(counts.values()) else "python"

def run_tests(state: AgentState) -> Dict:
    """Run tests - supports Python, JavaScript, TypeScript, React, Go."""
    lang = detect_language(state["repo_path"])
    repo_path = state["repo_path"]
    output = ""
    skip_dirs = {'.git', 'node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build', '.next'}
    
    print(f"[TEST] Detected language: {lang}")
    print(f"[TEST] Running tests in: {repo_path}")
    
    try:
        if lang == "python":
            # Run flake8
            output += "=FLAKE8=\n"
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
                output += result.stdout + result.stderr
            except Exception as e:
                output += f"flake8 not available or failed: {str(e)}\n"
            
            # Run mypy
            output += "\n=MYPY=\n"
            try:
                result = subprocess.run(
                    ["mypy", ".", "--ignore-missing-imports"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                output += result.stdout + result.stderr
            except Exception as e:
                output += f"mypy not available or failed: {str(e)}\n"
            
            # Run pytest
            output += "\n=PYTEST=\n"
            try:
                result = subprocess.run(
                    ["pytest", "--tb=short", "-q"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                output += result.stdout + result.stderr
            except Exception as e:
                output += f"pytest not available or failed: {str(e)}\n"
        
        elif lang in ("javascript", "typescript"):
            # Run Node.js syntax check
            output += "=NODE_SYNTAX=\n"
            try:
                js_files = []
                for root, dirs, files in os.walk(repo_path):
                    dirs[:] = [d for d in dirs if d not in skip_dirs]
                    for f in files:
                        if f.endswith(('.js', '.jsx')):
                            js_files.append(os.path.join(root, f))
                
                syntax_errors = 0
                for file_path in js_files[:50]:  # Check max 50 files
                    result = subprocess.run(
                        ["node", "--check", file_path],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode != 0:
                        rel_path = os.path.relpath(file_path, repo_path)
                        output += f"{rel_path}:\n{result.stderr}\n"
                        syntax_errors += 1
                
                if syntax_errors == 0:
                    output += f"Checked {min(len(js_files), 50)} files - all have valid syntax\n"
            except Exception as e:
                output += f"Node syntax check failed: {str(e)}\n"
            
            # Run ESLint
            output += "\n=ESLINT=\n"
            try:
                result = subprocess.run(
                    ["npx", "--yes", "eslint@8", ".", "--ext", ".js,.jsx,.ts,.tsx", 
                     "--format", "compact", "--no-eslintrc"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                output += result.stdout + result.stderr
            except Exception as e:
                output += f"ESLint not available or failed: {str(e)}\n"
            
            # Run Jest
            output += "\n=JEST=\n"
            try:
                result = subprocess.run(
                    ["npx", "--yes", "jest", "--passWithNoTests", "--forceExit"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                output += result.stdout + result.stderr
            except Exception as e:
                output += f"Jest not available or failed: {str(e)}\n"
            
            # Run tsc
            output += "\n=TSCCHECK=\n"
            try:
                result = subprocess.run(
                    ["npx", "--yes", "tsc", "--noEmit"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                output += result.stdout + result.stderr
            except Exception as e:
                output += f"TypeScript check not available or failed: {str(e)}\n"
        
        elif lang == "go":
            # Run go build
            output += "=GOBUILD=\n"
            try:
                result = subprocess.run(
                    ["go", "build", "./..."],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                output += result.stdout + result.stderr
            except Exception as e:
                output += f"go build failed: {str(e)}\n"
            
            # Run go vet
            output += "\n=GOVET=\n"
            try:
                result = subprocess.run(
                    ["go", "vet", "./..."],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                output += result.stdout + result.stderr
            except Exception as e:
                output += f"go vet failed: {str(e)}\n"
            
            # Run go test
            output += "\n=GOTEST=\n"
            try:
                result = subprocess.run(
                    ["go", "test", "./...", "-v"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                output += result.stdout + result.stderr
            except Exception as e:
                output += f"go test failed: {str(e)}\n"
            
            # Run gofmt
            output += "\n=GOFMT=\n"
            try:
                result = subprocess.run(
                    ["gofmt", "-l", "."],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.stdout.strip():
                    output += "Files need formatting:\n" + result.stdout
                else:
                    output += "All files properly formatted\n"
                output += result.stderr
            except Exception as e:
                output += f"gofmt failed: {str(e)}\n"
        
        else:
            output = f"=INFO=\nLanguage {lang} not supported. Only Python, JavaScript, TypeScript (React), and Go are supported.\n"
    
    except Exception as e:
        output = f"ERROR: Test execution failed: {str(e)}"
        print(f"[TEST] ✗ Test execution failed: {str(e)}")
    
    print(f"[TEST] ✓ Tests completed for {lang}")
    
    return {
        "raw_test_output": output,
        "repo_language": lang,
        "status": "analyzing",
        "progress": 35,
        "current_agent": "Analyze Agent",
        "timeline": state["timeline"] + [{
            "agent": "Test Agent",
            "msg": f"Ran {lang} tests",
            "timestamp": datetime.now().isoformat(),
            "iteration": state["retry_count"],
            "passed": True
        }]
    }

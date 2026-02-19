from datetime import datetime
from typing import Dict
from ..parsers import (
    parse_flake8, parse_mypy, parse_pytest,
    parse_eslint, parse_tsc, parse_jest, parse_node_syntax,
    parse_go, parse_java, parse_rust,
    deduplicate
)
from ..state import AgentState

def analyze_errors(state: AgentState) -> Dict:
    """Analyze test output and extract all errors based on language."""
    raw = state["raw_test_output"]
    lang = state.get("repo_language", "python")
    fixes = []
    
    def section(tag1, tag2=None):
        """Extract section between two tags."""
        if tag1 not in raw:
            return ""
        part = raw.split(tag1)[1]
        if tag2 and tag2 in part:
            part = part.split(tag2)[0]
        return part
    
    # Route to correct parser based on language
    if lang == "python":
        fixes += parse_flake8(section("=FLAKE8=", "=MYPY="))
        fixes += parse_mypy(section("=MYPY=", "=PYTEST="))
        fixes += parse_pytest(section("=PYTEST="))
    
    elif lang in ("javascript", "typescript"):
        fixes += parse_node_syntax(section("=NODE_SYNTAX=", "=ESLINT="))
        fixes += parse_eslint(section("=ESLINT=", "=JEST="))
        fixes += parse_jest(section("=JEST=", "=TSCCHECK="))
        fixes += parse_tsc(section("=TSCCHECK="))
    
    elif lang == "go":
        fixes += parse_go(section("=GOBUILD=", "=GOVET="))
        fixes += parse_go(section("=GOVET=", "=GOTEST="))
        fixes += parse_go(section("=GOTEST=", "=GOFMT="))
        fixes += parse_go(section("=GOFMT="))
    
    fixes = deduplicate(fixes)[:50]  # Limit to max 50 errors
    unique_files = len(set(f['file'] for f in fixes)) if fixes else 0
    
    print(f"[ANALYZE] Found {len(fixes)} errors in {lang} repo across {unique_files} files")
    if fixes:
        for fix in fixes[:5]:  # Show first 5 errors
            print(f"[ANALYZE]   - {fix['type']} in {fix['file']} line {fix['line']}")
        if len(fixes) > 5:
            print(f"[ANALYZE]   ... and {len(fixes) - 5} more errors")
    
    return {
        "fixes": fixes,
        "errors_found": len(fixes),
        "status": "fixing" if fixes else "verifying",
        "progress": 55 if fixes else 88,
        "current_agent": "Fix Agent" if fixes else "Verify Agent",
        "timeline": state["timeline"] + [{
            "agent": "Analyze Agent",
            "msg": f"Found {len(fixes)} errors in {lang} repo across {unique_files} files",
            "timestamp": datetime.now().isoformat(),
            "iteration": state["retry_count"],
            "passed": len(fixes) == 0
        }]
    }

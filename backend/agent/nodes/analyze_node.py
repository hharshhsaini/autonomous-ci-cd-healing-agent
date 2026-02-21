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
    new_fixes = []
    
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
        new_fixes += parse_flake8(section("=FLAKE8=", "=MYPY="))
        new_fixes += parse_mypy(section("=MYPY=", "=PYTEST="))
        new_fixes += parse_pytest(section("=PYTEST="))
    
    elif lang in ("javascript", "typescript"):
        new_fixes += parse_node_syntax(section("=NODE_SYNTAX=", "=ESLINT="))
        new_fixes += parse_eslint(section("=ESLINT=", "=JEST="))
        new_fixes += parse_jest(section("=JEST=", "=TSCCHECK="))
        new_fixes += parse_tsc(section("=TSCCHECK="))
    
    elif lang == "go":
        new_fixes += parse_go(section("=GOBUILD=", "=GOVET="))
        new_fixes += parse_go(section("=GOVET=", "=GOTEST="))
        new_fixes += parse_go(section("=GOTEST=", "=GOFMT="))
        new_fixes += parse_go(section("=GOFMT="))
    
    new_fixes = deduplicate(new_fixes)[:50]  # Limit to max 50 errors per pass
    unique_files = len(set(f['file'] for f in new_fixes)) if new_fixes else 0
    
    # Preserve existing fixes from past iterations that aren't pending
    existing_fixes = [f for f in state.get("fixes", []) if f.get("status") in ("fixed", "failed", "skipped")]
    
    # Only add new fixes that haven't been seen before (by id or file+line combination)
    existing_fingerprints = set(f"{f['file']}:{f['line']}:{f.get('type','')}" for f in existing_fixes)
    filtered_new_fixes = []
    for nf in new_fixes:
        fingerprint = f"{nf['file']}:{nf['line']}:{nf.get('type','')}"
        if fingerprint not in existing_fingerprints:
            filtered_new_fixes.append(nf)
            existing_fingerprints.add(fingerprint)
            
    # Combine old fixed items + new unhandled errors
    combined_fixes = existing_fixes + filtered_new_fixes
    
    print(f"[ANALYZE] Found {len(filtered_new_fixes)} new errors in {lang} repo across {unique_files} files")
    if filtered_new_fixes:
        for fix in filtered_new_fixes[:5]:  # Show first 5 errors
            print(f"[ANALYZE]   - {fix['type']} in {fix['file']} line {fix['line']}")
        if len(filtered_new_fixes) > 5:
            print(f"[ANALYZE]   ... and {len(filtered_new_fixes) - 5} more errors")
    
    return {
        "fixes": combined_fixes,
        "errors_found": len(filtered_new_fixes),
        "status": "fixing" if filtered_new_fixes else "verifying",
        "progress": 55 if filtered_new_fixes else 88,
        "current_agent": "Fix Agent" if filtered_new_fixes else "Verify Agent",
        "timeline": state["timeline"] + [{
            "agent": "Analyze Agent",
            "msg": f"Found {len(filtered_new_fixes)} new errors in {lang} repo across {unique_files} files",
            "timestamp": datetime.now().isoformat(),
            "iteration": state["retry_count"],
            "passed": len(filtered_new_fixes) == 0
        }]
    }

"""Quick integration test for the database layer."""
from database import SessionLocal, init_db
import crud
import time
import uuid

init_db()
db = SessionLocal()

# Test: create and save a completed run
job_id = str(uuid.uuid4())
test_data = {
    "job_id": job_id,
    "repo_url": "https://github.com/test/repo",
    "team_name": "RIFT ORGANISERS",
    "leader_name": "Saiyam Kumar",
    "branch_name": "RIFT_ORGANISERS_SAIYAM_KUMAR_AI_Fix",
    "status": "done",
    "progress": 100,
    "current_agent": "Git Push Agent",
    "errors_found": 3,
    "errors_fixed": 2,
    "commit_count": 2,
    "retry_count": 1,
    "retry_limit": 5,
    "verify_passed": True,
    "repo_language": "python",
    "push_success": True,
    "ci_status": "PASSED",
    "start_time": time.time() - 120,
    "timestamp": "2026-02-20T02:15:00Z",
    "score": {"total": 40, "elapsed_seconds": 120},
    "fixes": [
        {
            "id": "LINTING_src_utils_py_15", "type": "LINTING",
            "file": "src/utils.py", "line": 15,
            "message": "Unused import os",
            "formatted": "LINTING error in src/utils.py line 15 -> Fix: remove the import statement",
            "fix_description": "remove the import statement",
            "commit_message": "[AI-AGENT] Fix LINTING in src/utils.py line 15",
            "status": "fixed"
        },
        {
            "id": "SYNTAX_src_validator_py_8", "type": "SYNTAX",
            "file": "src/validator.py", "line": 8,
            "message": "Missing colon",
            "formatted": "SYNTAX error in src/validator.py line 8 -> Fix: add the colon",
            "fix_description": "add the colon at the correct position",
            "commit_message": "[AI-AGENT] Fix SYNTAX in src/validator.py line 8",
            "status": "fixed"
        }
    ],
    "timeline": [
        {"agent": "Clone Agent", "msg": "Cloned repo",
         "timestamp": "2026-02-20T02:13:00Z", "iteration": 0, "passed": True},
        {"agent": "Verify Agent", "msg": "Iteration 1/5 - 0 errors remaining",
         "timestamp": "2026-02-20T02:14:00Z", "iteration": 1, "passed": True}
    ]
}

# 1. Save run
run = crud.save_completed_run(db, test_data)
print(f"[PASS] Saved run: {run.id}")

# 2. Read back
r = crud.get_run(db, job_id)
d = r.to_dict()
assert d["job_id"] == job_id
assert d["ci_status"] == "PASSED"
assert len(d["fixes"]) == 2
assert len(d["timeline"]) == 2
assert d["score"]["total"] == 40
print(f"[PASS] Read back with correct data: {len(d['fixes'])} fixes, {len(d['timeline'])} timeline events")

# 3. List runs
runs = crud.get_all_runs(db)
assert len(runs) >= 1
print(f"[PASS] Total runs in DB: {len(runs)}")

# 4. Stats
stats = crud.get_stats(db)
assert stats["successRate"] > 0
assert stats["totalFixes"] >= 2
assert stats["totalRuns"] >= 1
print(f"[PASS] Stats: successRate={stats['successRate']}%, totalFixes={stats['totalFixes']}, totalRuns={stats['totalRuns']}")

db.close()
print("\n=== ALL TESTS PASSED ===")

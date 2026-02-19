"""
CRUD operations for the Healing Agent database.
All functions accept a SQLAlchemy session and return dicts/models.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import time

from models import Run, Fix, TimelineEvent


# ─── Run Operations ─────────────────────────────────────────────

def create_run(db: Session, job_data: dict) -> Run:
    """Create a new run from the in-memory job dict."""
    run = Run(
        id=job_data["job_id"],
        repo_url=job_data.get("repo_url", ""),
        team_name=job_data.get("team_name", ""),
        leader_name=job_data.get("leader_name", ""),
        branch_name=job_data.get("branch_name", ""),
        status=job_data.get("status", "queued"),
        progress=job_data.get("progress", 0),
        current_agent=job_data.get("current_agent", "Initializing"),
        error_message=job_data.get("error_message", ""),
        errors_found=job_data.get("errors_found", 0),
        errors_fixed=job_data.get("errors_fixed", 0),
        commit_count=job_data.get("commit_count", 0),
        retry_count=job_data.get("retry_count", 0),
        retry_limit=job_data.get("retry_limit", 5),
        verify_passed=job_data.get("verify_passed", False),
        repo_language=job_data.get("repo_language", "unknown"),
        push_success=job_data.get("push_success", False),
        ci_status=job_data.get("ci_status", "PENDING"),
        start_time=job_data.get("start_time", time.time()),
        timestamp=job_data.get("timestamp", ""),
        raw_test_output=job_data.get("raw_test_output", ""),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def save_completed_run(db: Session, job_data: dict) -> Run:
    """
    Save or update a completed run with all its fixes and timeline events.
    This replaces the old archive_job() deque logic.
    """
    # Check if run already exists
    existing = db.query(Run).filter(Run.id == job_data.get("job_id")).first()

    if existing:
        run = existing
    else:
        run = Run(id=job_data["job_id"])
        db.add(run)

    # Update all fields
    run.repo_url = job_data.get("repo_url", "")
    run.team_name = job_data.get("team_name", "")
    run.leader_name = job_data.get("leader_name", "")
    run.branch_name = job_data.get("branch_name", "")
    run.status = job_data.get("status", "done")
    run.progress = job_data.get("progress", 100)
    run.current_agent = job_data.get("current_agent", "")
    run.error_message = job_data.get("error_message", "")
    run.errors_found = job_data.get("errors_found", 0)
    run.errors_fixed = job_data.get("errors_fixed", 0)
    run.commit_count = job_data.get("commit_count", 0)
    run.retry_count = job_data.get("retry_count", 0)
    run.retry_limit = job_data.get("retry_limit", 5)
    run.verify_passed = job_data.get("verify_passed", False)
    run.repo_language = job_data.get("repo_language", "unknown")
    run.push_success = job_data.get("push_success", False)
    run.ci_status = job_data.get("ci_status", "PENDING")
    run.start_time = job_data.get("start_time")
    run.timestamp = job_data.get("timestamp", "")
    run.raw_test_output = job_data.get("raw_test_output", "")

    # Compute elapsed time and score
    start = job_data.get("start_time", time.time())
    elapsed = time.time() - start
    run.elapsed_seconds = elapsed

    score = job_data.get("score", {})
    if isinstance(score, dict):
        run.score_total = score.get("total",
                                    job_data.get("errors_fixed", 0) * 10 +
                                    (20 if job_data.get("ci_status") == "PASSED" else 0))
        run.score_base = score.get("base", 100)
        run.score_speed_bonus = score.get("speed_bonus", 10 if elapsed < 300 else 0)
        run.score_efficiency_penalty = score.get("efficiency_penalty",
                                                  max(0, (job_data.get("commit_count", 0) - 20) * 2))
        run.elapsed_seconds = score.get("elapsed_seconds", elapsed)
    else:
        run.score_total = job_data.get("errors_fixed", 0) * 10 + (20 if job_data.get("ci_status") == "PASSED" else 0)

    run.updated_at = datetime.now(timezone.utc)

    # Clear existing fixes and timeline (replace with latest)
    db.query(Fix).filter(Fix.run_id == run.id).delete()
    db.query(TimelineEvent).filter(TimelineEvent.run_id == run.id).delete()

    # Insert fixes
    fixes_data = job_data.get("fixes", [])
    if isinstance(fixes_data, list):
        for fix in fixes_data:
            if isinstance(fix, dict):
                db.add(Fix(
                    run_id=run.id,
                    fix_id=fix.get("id", ""),
                    type=fix.get("type", "UNKNOWN"),
                    file=fix.get("file", ""),
                    line=fix.get("line", 0),
                    message=fix.get("message", ""),
                    formatted=fix.get("formatted", ""),
                    fix_description=fix.get("fix_description", ""),
                    commit_message=fix.get("commit_message", ""),
                    status=fix.get("status", "pending"),
                ))

    # Insert timeline events
    timeline_data = job_data.get("timeline", [])
    if isinstance(timeline_data, list):
        for event in timeline_data:
            if isinstance(event, dict):
                db.add(TimelineEvent(
                    run_id=run.id,
                    agent=event.get("agent", ""),
                    msg=event.get("msg", ""),
                    timestamp=event.get("timestamp", ""),
                    iteration=event.get("iteration", 0),
                    passed=event.get("passed", False),
                ))

    db.commit()
    db.refresh(run)
    return run


def get_run(db: Session, job_id: str) -> Optional[Run]:
    """Get a single run by job_id."""
    return db.query(Run).filter(Run.id == job_id).first()


def get_all_runs(db: Session, limit: int = 100, offset: int = 0) -> List[Run]:
    """Get completed runs, ordered by newest first."""
    return (
        db.query(Run)
        .filter(Run.status.in_(["done", "failed"]))
        .order_by(Run.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_run_count(db: Session) -> int:
    """Get total number of completed runs."""
    return db.query(func.count(Run.id)).filter(
        Run.status.in_(["done", "failed"])
    ).scalar()


# ─── Stats Operations ───────────────────────────────────────────

def get_stats(db: Session) -> dict:
    """
    Compute dashboard stats from the database.
    Replaces the in-memory stats computation in main.py.
    """
    runs = get_all_runs(db, limit=1000)

    if not runs:
        return {
            "successRate": 0,
            "totalFixes": 0,
            "avgFixTime": 0,
            "byDay": {},
            "byBugType": {},
            "thisMonth": 0,
            "lastMonth": 0,
            "totalRuns": 0,
        }

    total = len(runs)
    passed_count = 0
    total_fixes = 0
    total_time = 0.0
    by_bug_type = {}

    now = datetime.now()
    this_month, this_year = now.month, now.year
    last_month_num = 12 if this_month == 1 else this_month - 1
    last_year = this_year - 1 if this_month == 1 else this_year

    this_month_runs = []
    last_month_runs = []

    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    by_day = {day_names[(now.weekday() - i) % 7]: {"runs": 0, "fixes": 0} for i in range(6, -1, -1)}

    for r in runs:
        if r.ci_status == "PASSED":
            passed_count += 1

        total_fixes += r.errors_fixed or 0
        total_time += r.elapsed_seconds or 0

        # Bug types from fixes
        for fix in r.fixes:
            bug_type = fix.type or "UNKNOWN"
            by_bug_type[bug_type] = by_bug_type.get(bug_type, 0) + 1

        # By day and month
        try:
            ts = r.timestamp
            if ts:
                dt = datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")
                dn = day_names[dt.weekday()]
                if dn in by_day:
                    by_day[dn]["runs"] += 1
                    by_day[dn]["fixes"] += r.errors_fixed or 0

                if dt.month == this_month and dt.year == this_year:
                    this_month_runs.append(r)
                elif dt.month == last_month_num and dt.year == last_year:
                    last_month_runs.append(r)
        except Exception:
            pass

    success_rate = (passed_count / total) * 100 if total else 0
    avg_fix_time = total_time / total if total else 0

    this_month_rate = (
        sum(1 for r in this_month_runs if r.ci_status == "PASSED") / len(this_month_runs) * 100
    ) if this_month_runs else 0

    last_month_rate = (
        sum(1 for r in last_month_runs if r.ci_status == "PASSED") / len(last_month_runs) * 100
    ) if last_month_runs else 0

    return {
        "successRate": round(success_rate, 1),
        "totalFixes": total_fixes,
        "avgFixTime": round(avg_fix_time, 1),
        "byDay": by_day,
        "byBugType": by_bug_type,
        "thisMonth": round(this_month_rate, 1),
        "lastMonth": round(last_month_rate, 1),
        "totalRuns": total,
    }

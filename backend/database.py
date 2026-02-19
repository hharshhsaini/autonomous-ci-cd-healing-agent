import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

DB_PATH = "data/rift_agent.db"

def init_db():
    """Initialize database with tables."""
    Path("data").mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            github_id TEXT UNIQUE,
            username TEXT,
            email TEXT,
            avatar_url TEXT,
            github_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Runs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT UNIQUE,
            user_id INTEGER,
            repo_url TEXT,
            repo_language TEXT,
            team_name TEXT,
            leader_name TEXT,
            branch_name TEXT,
            errors_found INTEGER,
            errors_fixed INTEGER,
            commit_count INTEGER,
            verify_passed BOOLEAN,
            ci_status TEXT,
            push_success BOOLEAN,
            score_total INTEGER,
            elapsed_seconds REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Fixes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fixes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            fix_id TEXT,
            type TEXT,
            file TEXT,
            line INTEGER,
            message TEXT,
            fix_description TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("[DB] Database initialized")

def save_user(github_id: str, username: str, email: str, avatar_url: str, github_token: str) -> int:
    """Save or update user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO users (github_id, username, email, avatar_url, github_token)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(github_id) DO UPDATE SET
            username=excluded.username,
            email=excluded.email,
            avatar_url=excluded.avatar_url,
            github_token=excluded.github_token
    """, (github_id, username, email, avatar_url, github_token))
    
    user_id = cursor.lastrowid
    if user_id == 0:
        cursor.execute("SELECT id FROM users WHERE github_id=?", (github_id,))
        user_id = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    return user_id

def get_user_by_github_id(github_id: str) -> Optional[Dict]:
    """Get user by GitHub ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE github_id=?", (github_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "github_id": row[1],
            "username": row[2],
            "email": row[3],
            "avatar_url": row[4],
            "github_token": row[5],
            "created_at": row[6]
        }
    return None

def save_run(job_id: str, user_id: int, results: Dict) -> int:
    """Save run results."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO runs (
            job_id, user_id, repo_url, repo_language, team_name, leader_name,
            branch_name, errors_found, errors_fixed, commit_count,
            verify_passed, ci_status, push_success, score_total, elapsed_seconds
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_id, user_id, results.get("repo_url"), results.get("repo_language"),
        results.get("team_name"), results.get("leader_name"), results.get("branch_name"),
        results.get("errors_found", 0), results.get("errors_fixed", 0),
        results.get("commit_count", 0), results.get("verify_passed", False),
        results.get("ci_status"), results.get("push_success", False),
        results.get("score", {}).get("total", 0),
        results.get("score", {}).get("elapsed_seconds", 0)
    ))
    
    run_id = cursor.lastrowid
    
    # Save fixes
    for fix in results.get("fixes", []):
        cursor.execute("""
            INSERT INTO fixes (run_id, fix_id, type, file, line, message, fix_description, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, fix.get("id"), fix.get("type"), fix.get("file"),
            fix.get("line"), fix.get("message"), fix.get("fix_description"),
            fix.get("status")
        ))
    
    conn.commit()
    conn.close()
    return run_id

def get_user_runs(user_id: int, limit: int = 10) -> List[Dict]:
    """Get user's recent runs."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM runs WHERE user_id=? ORDER BY created_at DESC LIMIT ?
    """, (user_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    runs = []
    for row in rows:
        runs.append({
            "id": row[0],
            "job_id": row[1],
            "repo_url": row[3],
            "repo_language": row[4],
            "branch_name": row[7],
            "errors_found": row[8],
            "errors_fixed": row[9],
            "ci_status": row[12],
            "score_total": row[14],
            "created_at": row[16]
        })
    
    return runs

def get_run_details(job_id: str) -> Optional[Dict]:
    """Get run details with fixes."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM runs WHERE job_id=?", (job_id,))
    run_row = cursor.fetchone()
    
    if not run_row:
        conn.close()
        return None
    
    cursor.execute("SELECT * FROM fixes WHERE run_id=?", (run_row[0],))
    fix_rows = cursor.fetchall()
    conn.close()
    
    fixes = []
    for row in fix_rows:
        fixes.append({
            "id": row[2],
            "type": row[3],
            "file": row[4],
            "line": row[5],
            "message": row[6],
            "fix_description": row[7],
            "status": row[8]
        })
    
    return {
        "job_id": run_row[1],
        "repo_url": run_row[3],
        "repo_language": run_row[4],
        "team_name": run_row[5],
        "leader_name": run_row[6],
        "branch_name": run_row[7],
        "errors_found": run_row[8],
        "errors_fixed": run_row[9],
        "commit_count": run_row[10],
        "ci_status": run_row[12],
        "score_total": run_row[14],
        "elapsed_seconds": run_row[15],
        "created_at": run_row[16],
        "fixes": fixes
    }

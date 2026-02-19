from typing import TypedDict, List, Dict

class FixItem(TypedDict):
    id: str
    type: str  # LINTING|SYNTAX|LOGIC|TYPE_ERROR|IMPORT|INDENTATION
    file: str
    line: int
    message: str
    formatted: str  # "LINTING error in src/utils.py line 15 → Fix: remove the import statement"
    fix_description: str
    commit_message: str  # "[AI-AGENT] Fix LINTING in src/utils.py line 15"
    status: str  # pending|fixed|failed

class TimelineItem(TypedDict):
    agent: str
    msg: str
    timestamp: str
    iteration: int
    passed: bool

class AgentState(TypedDict):
    job_id: str
    repo_url: str
    repo_path: str
    team_name: str
    leader_name: str
    github_token: str
    branch_name: str
    status: str
    progress: int
    current_agent: str
    raw_test_output: str
    fixes: List[FixItem]
    errors_found: int
    errors_fixed: int
    commit_count: int
    retry_count: int
    retry_limit: int
    verify_passed: bool
    timeline: List[TimelineItem]
    score: Dict
    start_time: float
    error_message: str
    repo_language: str        # detected language
    push_success: bool        # whether git push worked
    ci_status: str            # "PASSED" or "FAILED" or "PENDING"

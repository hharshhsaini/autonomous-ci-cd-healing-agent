from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes.clone_node import clone_repo
from .nodes.test_node import run_tests
from .nodes.analyze_node import analyze_errors
from .nodes.fix_node import apply_fixes
from .nodes.verify_node import verify_fixes
from .nodes.push_node import push_to_branch
import time

# Build the graph
builder = StateGraph(AgentState)

# Add nodes
builder.add_node("clone", clone_repo)
builder.add_node("test", run_tests)
builder.add_node("analyze", analyze_errors)
builder.add_node("fix", apply_fixes)
builder.add_node("verify", verify_fixes)
builder.add_node("push", push_to_branch)

# Set entry point
builder.set_entry_point("clone")

# Add edges: clone → test → analyze
builder.add_edge("clone", "test")
builder.add_edge("test", "analyze")

# Conditional routing from analyze
def route_after_analyze(state: AgentState) -> str:
    """Route after analyze - if no errors, skip fix and go to verify."""
    if state["errors_found"] == 0:
        return "verify"  # verify will detect 0 errors and go to push
    return "fix"

builder.add_conditional_edges("analyze", route_after_analyze, {
    "fix": "fix",
    "verify": "verify"
})

# Conditional routing from fix
def route_after_fix(state: AgentState) -> str:
    """Route from fix node - if all fixes failed, end workflow."""
    if state.get("status") == "failed":
        return END
    if state.get("status") == "quota_reached":
        return "push"
    return "verify"

builder.add_conditional_edges("fix", route_after_fix, {
    "verify": "verify",
    "push": "push",
    END: END
})

# Conditional routing from verify
def route_after_verify(state: AgentState) -> str:
    """Route from verify node - either retry fix or push."""
    if state["status"] == "fixing":
        return "fix"
    return "push"

builder.add_conditional_edges("verify", route_after_verify, {
    "fix": "fix",
    "push": "push"
})

builder.add_edge("push", END)

# Compile the graph
compiled_graph = builder.compile()

class HealingOrchestrator:
    """Orchestrator for the healing agent workflow."""
    
    def __init__(self, job_id: str, jobs_store: dict):
        self.job_id = job_id
        self.jobs = jobs_store
    
    def run(self, repo_url: str, branch_name: str, github_token: str, team_name: str, leader_name: str):
        """Run the healing workflow for a repository."""
        initial_state: AgentState = {
            "job_id": self.job_id,
            "repo_url": repo_url,
            "repo_path": f"/tmp/repos/{self.job_id}",
            "team_name": team_name,
            "leader_name": leader_name,
            "github_token": github_token,
            "branch_name": branch_name,
            "status": "cloning",
            "progress": 5,
            "current_agent": "Clone Agent",
            "raw_test_output": "",
            "fixes": [],
            "errors_found": 0,
            "errors_fixed": 0,
            "commit_count": 0,
            "retry_count": 0,
            "retry_limit": 5,
            "verify_passed": False,
            "timeline": [],
            "score": {},
            "start_time": time.time(),
            "error_message": "",
            "repo_language": "unknown",
            "push_success": False,
            "ci_status": "PENDING"
        }
        
        # Sync initial state
        self.jobs[self.job_id].update(initial_state)
        
        try:
            # Stream through the graph and update job state
            for step_output in compiled_graph.stream(initial_state):
                node_name = list(step_output.keys())[0]
                updated = step_output[node_name]
                
                # Update jobs dict so SSE can stream it
                self.jobs[self.job_id].update(updated)
                print(f"[{self.job_id}] Node '{node_name}' completed — status: {self.jobs[self.job_id].get('status')}")
        except Exception as e:
            self.jobs[self.job_id]["status"] = "failed"
            self.jobs[self.job_id]["error_message"] = str(e)
            import traceback
            traceback.print_exc()

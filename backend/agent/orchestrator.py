from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes.clone_node import clone_repo
from .nodes.test_node import run_tests
from .nodes.analyze_node import analyze_errors
from .nodes.fix_node import apply_fixes
from .nodes.verify_node import verify_fixes
import time

# Build the graph
builder = StateGraph(AgentState)

# Add nodes
builder.add_node("clone", clone_repo)
builder.add_node("test", run_tests)
builder.add_node("analyze", analyze_errors)
builder.add_node("fix", apply_fixes)
builder.add_node("verify", verify_fixes)

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
    if state.get("status") == "quota_reached" or state.get("status") == "awaiting_review":
        return END
    return "verify"

builder.add_conditional_edges("fix", route_after_fix, {
    "verify": "verify",
    END: END
})

# Conditional routing from verify
def route_after_verify(state: AgentState) -> str:
    """Route from verify node - either retry fix or await review."""
    if state["status"] == "fixing":
        return "fix"
    return END

builder.add_conditional_edges("verify", route_after_verify, {
    "fix": "fix",
    END: END
})

# Push node is now intentionally disconnected from the automatic loop. 
# It will be called explicitly by a new manual API endpoint when the user hits 'Push Checked Files'

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
            for step_output in compiled_graph.stream(initial_state, config={"recursion_limit": 100}):
                node_name = list(step_output.keys())[0]
                updated = step_output[node_name]
                
                # Update jobs dict so SSE can stream it
                self.jobs[self.job_id].update(updated)
                print(f"[{self.job_id}] Node '{node_name}' completed — status: {self.jobs[self.job_id].get('status')}")
                
            # Keep job open in memory if it requires human review
            if self.jobs[self.job_id].get("status") == "awaiting_review":
                print(f"[{self.job_id}] Pipeline paused: awaiting user review.")
                
        except Exception as e:
            self.jobs[self.job_id]["status"] = "failed"
            self.jobs[self.job_id]["error_message"] = str(e)
            import traceback
            traceback.print_exc()

def execute_review_push(job_id: str, jobs_store: dict, declined_files: list) -> dict:
    """Executes the final push step manually after user review."""
    if job_id not in jobs_store:
        raise ValueError(f"Job {job_id} not found entirely in active memory.")
        
    state = jobs_store[job_id]
    if state["status"] != "awaiting_review":
        raise ValueError(f"Job {job_id} is in status {state['status']}, not awaiting_review.")
        
    state["status"] = "pushing"
    state["progress"] = 92
    state["current_agent"] = "Git Push Agent"
    state["timeline"].append({
        "agent": "Review Agent",
        "msg": f"User review complete. Declined {len(declined_files)} files. Proceeding to push...",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "iteration": state["retry_count"],
        "passed": True
    })
    
    # We will let the push_node handle the actual physical git logic and job finalization!
    # Update state via direct invocation
    from .nodes.push_node import push_to_branch
    
    # Track the declined files specifically to tell push node to revert them
    state["declined_files"] = declined_files
    
    final_output = push_to_branch(state)
    jobs_store[job_id].update(final_output)
    print(f"[{job_id}] Final Push executed.")
    return jobs_store[job_id]

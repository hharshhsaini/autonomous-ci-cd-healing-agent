import git
import os
import shutil
from datetime import datetime
from typing import Dict
from ..state import AgentState

def clone_repo(state: AgentState) -> Dict:
    """Clone the repository and prepare for testing."""
    try:
        # Clean existing directory if exists
        if os.path.exists(state["repo_path"]):
            shutil.rmtree(state["repo_path"])
        
        # Inject token into URL if provided
        url = state["repo_url"]
        if state["github_token"]:
            url = url.replace("https://", f"https://x-token:{state['github_token']}@")
        
        # Clone repository
        git.Repo.clone_from(url, state["repo_path"])
        
        # Return only changed fields (LangGraph pattern)
        return {
            "repo_path": state["repo_path"],
            "status": "testing",
            "progress": 15,
            "current_agent": "Test Agent",
            "timeline": state["timeline"] + [{
                "agent": "Clone Agent",
                "msg": f"Cloned {state['repo_url']} successfully",
                "timestamp": datetime.now().isoformat(),
                "iteration": 0,
                "passed": True
            }]
        }
    
    except Exception as e:
        return {
            "status": "failed",
            "error_message": str(e)
        }

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
        
        # Check if repo was cloned into a nested folder (GitPython sometimes does this)
        # If so, move contents up one level
        repo_name = state["repo_url"].rstrip('/').split('/')[-1].replace('.git', '')
        nested_path = os.path.join(state["repo_path"], repo_name)
        
        if os.path.exists(nested_path) and os.path.isdir(nested_path):
            # Move all contents from nested folder to parent
            for item in os.listdir(nested_path):
                src = os.path.join(nested_path, item)
                dst = os.path.join(state["repo_path"], item)
                if os.path.exists(dst):
                    if os.path.isdir(dst):
                        shutil.rmtree(dst)
                    else:
                        os.remove(dst)
                shutil.move(src, dst)
            # Remove empty nested folder
            os.rmdir(nested_path)
        
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

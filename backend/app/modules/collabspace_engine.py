from typing import Dict, Any

def sync_workspace_state(workspace_id: int, user: str, action: str) -> Dict[str, Any]:
    """
    Mock function to simulate real-time WebSockets/sync logic.
    """
    return {
        "workspace_id": workspace_id,
        "active_users": [user, "Analyst_02", "Agent_Smith"],
        "latest_action": action,
        "status": "Synced"
    }

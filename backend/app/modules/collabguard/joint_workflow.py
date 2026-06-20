import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class JointWorkflow:
    def __init__(self):
        self.investigations = {}

    async def create_investigation(self, lead_agency: str, title: str) -> str:
        """
        Initializes a joint investigation workspace.
        """
        inv_id = f"inv_{len(self.investigations) + 1}"
        self.investigations[inv_id] = {
            "title": title,
            "lead_agency": lead_agency,
            "participants": [lead_agency],
            "status": "open",
            "notes": []
        }
        logger.info(f"Investigation {inv_id} created by {lead_agency}.")
        return inv_id

    async def add_participant(self, inv_id: str, new_agency: str) -> bool:
        if inv_id in self.investigations:
            if new_agency not in self.investigations[inv_id]["participants"]:
                self.investigations[inv_id]["participants"].append(new_agency)
                return True
        return False

    async def add_note(self, inv_id: str, agency: str, note: str) -> bool:
        if inv_id in self.investigations and agency in self.investigations[inv_id]["participants"]:
            self.investigations[inv_id]["notes"].append({"agency": agency, "note": note})
            return True
        return False

joint_workflow = JointWorkflow()

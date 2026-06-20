import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HITLFeedbackSystem:
    def __init__(self):
        self.feedback_queue = []

    async def submit_feedback(self, data_id: str, corrected_label: str, analyst: str) -> Dict[str, Any]:
        """
        Ingests Human-in-the-Loop corrections for misclassified threats.
        """
        logger.info(f"Analyst {analyst} submitted correction for {data_id}: {corrected_label}")
        
        entry = {
            "data_id": data_id,
            "corrected_label": corrected_label,
            "analyst": analyst,
            "status": "pending_curation"
        }
        self.feedback_queue.append(entry)
        
        return entry

hitl_feedback = HITLFeedbackSystem()

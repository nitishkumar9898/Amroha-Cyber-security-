import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ContainmentAdvisor:
    def __init__(self):
        pass

    async def suggest_containment_actions(self, telemetry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyzes live telemetry to suggest immediate containment actions.
        """
        logger.info("Analyzing telemetry for containment suggestions...")
        suggestions = []
        
        # Mocked rules
        if telemetry.get("high_cpu_usage") and telemetry.get("unauthorized_processes"):
            suggestions.append({
                "target": telemetry.get("host_id", "unknown_host"),
                "action": "isolate_host",
                "reason": "High CPU usage coupled with unauthorized process execution detected."
            })
            
        if telemetry.get("failed_logins", 0) > 10:
            suggestions.append({
                "target": telemetry.get("user_id", "unknown_user"),
                "action": "disable_account",
                "reason": f"Excessive failed login attempts ({telemetry.get('failed_logins')}) detected."
            })
            
        return suggestions

containment_advisor = ContainmentAdvisor()

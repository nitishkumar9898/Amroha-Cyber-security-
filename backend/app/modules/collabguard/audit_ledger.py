import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class AuditLedger:
    def __init__(self):
        self.ledger = []

    async def append_log(self, actor: str, action: str, resource: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Appends an immutable record to the audit ledger.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "actor": actor,
            "action": action,
            "resource": resource,
            "metadata": metadata or {}
        }
        self.ledger.append(entry)
        logger.info(f"Audit log appended: {actor} performed {action} on {resource}.")
        return entry

    async def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieves recent audit logs.
        """
        return self.ledger[-limit:]

audit_ledger = AuditLedger()

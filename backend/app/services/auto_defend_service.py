# backend/app/services/auto_defend_service.py
"""AutoDefend core service.
Provides:
- Real‑time anomaly detection (placeholder logic).
- Auto‑remediation via existing AutoRemediationService.
- Predictive patch suggestions (static stub).
- Audit‑proof recovery log creation signed with ZKP.
"""

from typing import Dict, List
from datetime import datetime

from .remediation import AutoRemediationService
from ..models import RecoveryLog
from ..zkp import zkp_signer
from ..database import SessionLocal

class AutoDefendService:
    """Stateless service class for AutoDefend operations."""

    @staticmethod
    def detect_anomaly(event: Dict) -> bool:
        """Simple anomaly detection placeholder.
        Returns True for events containing the key 'severity' with value >= 7.
        """
        return event.get("severity", 0) >= 7

    @staticmethod
    def handle_anomaly(event: Dict) -> Dict:
        """Handle a detected anomaly.
        - Executes remediation.
        - Stores a signed recovery log.
        Returns the remediation response.
        """
        # Execute remediation using the threat signature from the event
        threat_sig = event.get("threat_signature", "unknown_threat")
        remediation_result = AutoRemediationService.execute_remediation(threat_sig)

        # Record recovery log
        db = SessionLocal()
        try:
            log_entry = RecoveryLog(
                timestamp=datetime.utcnow(),
                event_type="ANOMALY_DETECTED",
                detail=f"Anomaly detected: {event}. Remediation actions executed.",
                zkp_signature=zkp_signer.generate_proof(
                    {
                        "event": event,
                        "remediation": remediation_result,
                    },
                    author="AutoDefend",
                ),
            )
            db.add(log_entry)
            db.commit()
        finally:
            db.close()

        return remediation_result

    @staticmethod
    def suggest_patches(vuln_id: str) -> List[str]:
        """Return a static list of patch suggestions for a given vulnerability ID.
        In a real system this would query CVE databases.
        """
        # Placeholder mapping
        mapping = {
            "CVE-2023-1234": ["Update library X to >=2.1.0", "Apply configuration hardening"],
            "CVE-2024-5678": ["Patch kernel to 5.15.12", "Enable SELinux"],
        }
        return mapping.get(vuln_id, ["No specific patches found; consider a full system audit."])

    @staticmethod
    def get_logs(limit: int = 100) -> List[RecoveryLog]:
        """Fetch the most recent recovery logs (audit‑proof)."""
        db = SessionLocal()
        try:
            return db.query(RecoveryLog).order_by(RecoveryLog.timestamp.desc()).limit(limit).all()
        finally:
            db.close()
}

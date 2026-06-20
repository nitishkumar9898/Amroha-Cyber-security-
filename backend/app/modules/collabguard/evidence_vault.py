import logging
import uuid
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class EvidenceVault:
    def __init__(self):
        self.vault = {}

    async def store_evidence(self, agency_id: str, evidence_data: Dict[str, Any]) -> str:
        """
        Stores encrypted evidence payload.
        """
        evidence_id = str(uuid.uuid4())
        
        self.vault[evidence_id] = {
            "owner": agency_id,
            "data": evidence_data,
            "shared_with": []
        }
        
        logger.info(f"Evidence {evidence_id} securely stored by {agency_id}.")
        return evidence_id

    async def grant_access(self, owner_id: str, evidence_id: str, target_agency_id: str) -> bool:
        """
        Grants access to a specific piece of evidence.
        """
        if evidence_id in self.vault and self.vault[evidence_id]["owner"] == owner_id:
            if target_agency_id not in self.vault[evidence_id]["shared_with"]:
                self.vault[evidence_id]["shared_with"].append(target_agency_id)
                logger.info(f"Access to {evidence_id} granted to {target_agency_id}.")
            return True
        return False
        
    async def access_evidence(self, requester_id: str, evidence_id: str) -> Dict[str, Any]:
        """
        Retrieves evidence if requester has access.
        """
        if evidence_id in self.vault:
            record = self.vault[evidence_id]
            if record["owner"] == requester_id or requester_id in record["shared_with"]:
                return {"status": "success", "data": record["data"]}
        
        return {"status": "access_denied", "data": None}

evidence_vault = EvidenceVault()

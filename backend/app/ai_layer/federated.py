"""
Federated Learning utilities for DarkIntel.
Provides a simple node representation and DP update generation.
"""
import json
import hashlib
from typing import Dict, Any

class FederatedLearningNode:
    """Represents a local agency node in the federated DarkIntel network.
    Stores lightweight model weights and can generate a differentially private
    update signed with a Zero‑Knowledge Proof.
    """

    def __init__(self, agency_name: str):
        self.agency_name = agency_name
        # Simple mock model weights – thresholds for threat detection
        self.local_model_weights: Dict[str, float] = {
            "threat_threshold": 0.5,  # default sensitivity
            "risk_factor": 1.0,
        }

    def generate_differential_privacy_update(self, zkp_proof: Dict[str, Any]) -> str:
        """Create a DP‑protected update payload.
        The payload includes a hash of the ZKP proof to bind the update to the
        proof without exposing its contents.
        Returns a JSON string for easy transport.
        """
        # Compute a simple hash of the proof to serve as a commitment
        proof_serialized = json.dumps(zkp_proof, sort_keys=True).encode("utf-8")
        proof_hash = hashlib.sha256(proof_serialized).hexdigest()

        update_payload = {
            "agency": self.agency_name,
            "model_weights": self.local_model_weights,
            "proof_hash": proof_hash,
        }
        return json.dumps(update_payload)

def global_aggregator(updates: list) -> Dict[str, Any]:
    """Aggregate a list of node updates into a global model.
    This mock simply averages numeric weights across updates.
    """
    if not updates:
        return {}
    # Parse JSON strings
    parsed = [json.loads(u) for u in updates]
    # Aggregate weights
    agg_weights: Dict[str, float] = {}
    count = len(parsed)
    for upd in parsed:
        for k, v in upd.get("model_weights", {}).items():
            agg_weights[k] = agg_weights.get(k, 0.0) + v / count
    return {"global_model_weights": agg_weights}

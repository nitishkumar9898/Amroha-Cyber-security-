# backend/app/services/behavioral_service.py
"""
Behavioral profiling service for PsycheGuard.
Provides high‑level API used by FastAPI endpoints to generate profiles, run scans,
and predict insider‑threat probabilities.
"""
from typing import Dict, Any

from ..modules.behavioral import parse_digital_footprint, detect_social_engineering, insider_threat_score
from ..ai_layer.behavioral_models import BehavioralProfiler
from ..zkp import zkp_signer
from ..compliance_engine import monitor, audit_trail

# Instantiate the profiler once for reuse (lightweight placeholder)
_profiler = BehavioralProfiler()


def run_profile(user_id: str, footprint: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a full behavioral profile for a given user.
    The `footprint` should be a dict containing "messages" and "activities".
    Returns a dict with the profile data and a ZKP proof of authenticity.
    """
    # Normalize footprint
    normalized = parse_digital_footprint(footprint)
    # Use AI layer to produce embedding and basic signals
    profile = _profiler.profile(normalized)
    # Add user identifier
    profile["user_id"] = user_id
    # Sign the profile with ZKP for compliance
    proof = zkp_signer.generate_proof(profile, user_id)
    profile["zkp_proof"] = proof
    # Record compliance event and audit trail
    monitor.record_event('run_profile', {"user_id": user_id, "action": "profile_generated"})
    audit_trail.log_action('run_profile', {"user_id": user_id, "profile": profile})
    return profile


def scan_footprint(footprint: Dict[str, Any]) -> Dict[str, Any]:
    """Perform an asynchronous scan of a digital footprint.
    Returns a quick summary useful for batch processing.
    """
    normalized = parse_digital_footprint(footprint)
    messages = " ".join(normalized.get("messages", []))
    social = detect_social_engineering(messages)
    insider = insider_threat_score(normalized.get("activities", []))
    return {
        "social_engineering": social,
        "insider_threat_score": insider,
    }


def predict_insider_threat(user_id: str, activities: list) -> Dict[str, Any]:
    """Return only the insider‑threat probability for a user.
    This is a thin wrapper around the heuristic function.
    """
    score = insider_threat_score(activities)
    proof = zkp_signer.generate_proof({"user_id": user_id, "insider_threat_score": score}, user_id)
    return {"user_id": user_id, "insider_threat_score": score, "zkp_proof": proof}

"""
IPShield Core Engine
====================
Data-exfiltration pattern recognition, insider ↔ external actor
correlation scoring, and trade-secret protection simulation.
"""

import datetime
import math
import random
from typing import Dict, Any, List, Optional

# ── Exfiltration Risk Scoring ─────────────────────────────────────────

# Weight table: higher weight → more suspicious channel
_CHANNEL_WEIGHTS: Dict[str, float] = {
    "usb_copy":         0.8,
    "cloud_upload":     0.7,
    "email_attachment":  0.6,
    "print":            0.4,
    "screen_capture":   0.5,
    "airdrop":          0.75,
    "unknown":          0.9,
}

_VOLUME_THRESHOLDS_MB = {
    "low":  50,
    "med":  500,
    "high": 2000,
}


def compute_exfiltration_risk(event_type: str, data_volume_mb: Optional[float],
                              actor_type: str) -> float:
    """Return a risk score 0–1 for a potential exfiltration event.

    Factors:
      • Channel suspiciousness (usb > email > print)
      • Data volume relative to thresholds
      • Actor type (external actors score higher)
    """
    channel_w = _CHANNEL_WEIGHTS.get(event_type, 0.5)

    volume_w = 0.0
    if data_volume_mb is not None:
        if data_volume_mb >= _VOLUME_THRESHOLDS_MB["high"]:
            volume_w = 1.0
        elif data_volume_mb >= _VOLUME_THRESHOLDS_MB["med"]:
            volume_w = 0.6
        elif data_volume_mb >= _VOLUME_THRESHOLDS_MB["low"]:
            volume_w = 0.3

    actor_w = 0.7 if actor_type == "external" else 0.4

    # Weighted combination
    risk = 0.45 * channel_w + 0.35 * volume_w + 0.20 * actor_w
    return round(min(risk, 1.0), 4)


# ── Insider ↔ External Actor Correlation ──────────────────────────────

_CORRELATION_INDICATORS = [
    "shared_ip",
    "simultaneous_login",
    "data_relay_pattern",
    "common_file_access",
    "encrypted_channel_use",
    "after_hours_activity",
    "anomalous_travel",
]


def compute_correlation_score(indicators: Optional[List[Dict[str, Any]]]) -> float:
    """Score how strongly an insider and external actor are linked.

    Each indicator that matches a known pattern adds weight.
    """
    if not indicators:
        return 0.0
    known_set = set(_CORRELATION_INDICATORS)
    hits = sum(1 for ind in indicators if ind.get("type") in known_set)
    return round(min(hits / max(len(known_set) * 0.3, 1), 1.0), 4)


# ── Trade-Secret Protection Simulation ────────────────────────────────

_ATTACK_VECTORS = [
    "mass_download",
    "selective_exfil",
    "credential_theft",
    "social_engineering",
    "supply_chain_compromise",
]


def simulate_trade_secret_attack(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Run a deterministic simulation of a trade-secret theft attempt.

    Parameters may include:
      • attack_vector (str)
      • attacker_skill (float 0–1)
      • defence_level (float 0–1)
    """
    attack_vector = parameters.get("attack_vector", "mass_download")
    attacker_skill = parameters.get("attacker_skill", 0.5)
    defence_level = parameters.get("defence_level", 0.5)

    # Simple model: protection score increases with defence_level, decreases with skill
    base_protection = defence_level * 0.7 + 0.15
    skill_penalty = attacker_skill * 0.5
    protection_score = max(0.0, min(base_protection - skill_penalty + 0.1, 1.0))

    # Determine if the simulated attack succeeds
    breach = protection_score < 0.4
    exfiltrated_pct = max(0, round((1 - protection_score) * 100, 1)) if breach else 0

    return {
        "scenario_name": f"sim_{attack_vector}",
        "attack_vector": attack_vector,
        "attacker_skill": attacker_skill,
        "defence_level": defence_level,
        "protection_score": round(protection_score, 4),
        "breach": breach,
        "exfiltrated_pct": exfiltrated_pct,
        "recommendation": "Increase DLP controls" if breach else "Defences adequate",
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


# ── Pattern-matching helpers (used by service layer) ──────────────────

def detect_bulk_transfer_pattern(events: List[Dict[str, Any]]) -> bool:
    """Return True if there's a cluster of large transfers within a short window."""
    if len(events) < 3:
        return False
    timestamps = sorted(
        datetime.datetime.fromisoformat(e["detected_at"]) for e in events if e.get("detected_at")
    )
    for i in range(len(timestamps) - 2):
        window = (timestamps[i + 2] - timestamps[i]).total_seconds()
        if window < 600:  # 3 events within 10 minutes
            return True
    return False

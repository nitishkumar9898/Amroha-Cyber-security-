# backend/app/modules/behavioral.py
"""
Behavioral profiling module for cybercriminals and victims.
Provides utilities to ingest digital footprints and extract psychological patterns,
social‑engineering cues, and insider‑threat signals.
"""
import re
from ..compliance_engine.monitor import record_event
from typing import List, Dict


def _extract_keywords(text: str, keywords: List[str]) -> List[str]:
    """Return a list of keywords found in the given text (case‑insensitive)."""
    lower = text.lower()
    return [kw for kw in keywords if kw.lower() in lower]


def detect_social_engineering(text: str) -> Dict[str, any]:
    """Simple heuristic to detect social‑engineering language.
    Returns a dict with a boolean flag and matched cues.
    """
    cues = [
        "urgent",
        "immediate action",
        "click here",
        "verify your account",
        "password",
        "login",
        "security alert",
    ]
    matches = _extract_keywords(text, cues)
    return {
        "is_social_engineering": bool(matches),
        "matched_cues": matches,
    }


def insider_threat_score(activities: List[Dict[str, str]]) -> float:
    """Calculate a naive insider‑threat probability based on activity patterns.
    `activities` is a list of dicts with keys like "type" and "detail".
    Returns a float between 0 and 1.
    """
    risky_actions = {"access_sensitive_file", "download_bulk_data", "privilege_escalation"}
    count = sum(1 for act in activities if act.get("type") in risky_actions)
    total = len(activities) or 1
    # Simple linear scaling with a cap
    score = min(0.9, (count / total) * 0.9)
    return round(score, 3)


def parse_digital_footprint(footprint: Dict[str, any]) -> Dict[str, any]:
    """Normalize incoming footprint data.
    Expected keys: "messages" (list of strings), "activities" (list of dicts).
    """
    messages = footprint.get("messages", [])
    activities = footprint.get("activities", [])
    result = {
        "messages": messages,
        "activities": activities,
    }
    # Record that a digital footprint was parsed for compliance monitoring
    record_event('parse_digital_footprint', result)
    return result

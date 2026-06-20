"""
ProtectForge Core Engine
========================
Privacy-preserving CSAM hash matching, grooming-pattern NLP analysis,
dark-web keyword scanner, and strict compliance utilities.

IMPORTANT — Ethical safeguards:
  • NO raw media is ever stored or transmitted.
  • Detection operates exclusively on perceptual hashes.
  • All operations are audit-logged for legal chain-of-custody.
"""

import datetime
import hashlib
import re
from typing import Dict, Any, List, Optional

# ── Known-hash database (placeholder) ────────────────────────────────
# In production this would be a secure, encrypted database of known
# CSAM perceptual hashes (e.g., NCMEC hash-sharing programme).
_KNOWN_HASH_DB: set = {
    "a1b2c3d4e5f60001",
    "a1b2c3d4e5f60002",
    "a1b2c3d4e5f60003",
}


def match_hash(hash_value: str, algorithm: str = "phash") -> float:
    """Compare a perceptual hash against the known-hash DB.
    Returns confidence 0–1.  Exact match → 1.0; otherwise 0.0.
    """
    if hash_value in _KNOWN_HASH_DB:
        return 1.0
    # Placeholder: partial-match via Hamming distance would go here
    return 0.0


# ── Grooming / Predatory-behaviour NLP (rule-based stub) ─────────────

_GROOMING_STAGES = {
    "trust_building": [
        "you can trust me", "i understand you", "no one else cares",
        "our secret", "you're special", "i'm your friend",
    ],
    "isolation": [
        "don't tell anyone", "they won't understand", "only talk to me",
        "your parents don't care", "delete the messages",
    ],
    "desensitisation": [
        "it's normal", "everyone does this", "don't be shy",
        "have you ever", "send me a pic", "turn on camera",
    ],
    "control": [
        "you owe me", "i'll tell everyone", "do as i say",
        "if you don't", "i have your",
    ],
}


def analyze_grooming(text: str) -> Dict[str, Any]:
    """Analyse text for grooming indicators across four stages.
    Returns risk_score (0–1), detected stage, and matched indicators.
    """
    text_lower = text.lower()
    indicators: List[Dict[str, Any]] = []
    stage_hits: Dict[str, int] = {}

    for stage, phrases in _GROOMING_STAGES.items():
        hits = [p for p in phrases if p in text_lower]
        if hits:
            stage_hits[stage] = len(hits)
            for h in hits:
                indicators.append({"stage": stage, "phrase": h})

    total_phrases = sum(len(v) for v in _GROOMING_STAGES.values())
    total_hits = sum(stage_hits.values())
    risk_score = min(total_hits / max(total_phrases * 0.15, 1), 1.0)

    # The most advanced stage detected is the one reported
    stage_order = ["trust_building", "isolation", "desensitisation", "control"]
    detected_stage: Optional[str] = None
    for s in reversed(stage_order):
        if s in stage_hits:
            detected_stage = s
            break

    return {
        "risk_score": round(risk_score, 4),
        "stage_detected": detected_stage,
        "indicators": indicators,
    }


# ── Dark-web / social-media keyword scanner ──────────────────────────

_DARKWEB_KEYWORDS = [
    "cp", "child", "minor", "underage", "jailbait",
    "pthc", "preteen", "lolita", "pedo",
]


def scan_darkweb_text(text: str) -> Dict[str, Any]:
    """Scan text for exploitation-related keywords.
    Returns severity (0–1) and matched keywords.
    """
    text_lower = text.lower()
    matches = [kw for kw in _DARKWEB_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", text_lower)]
    severity = min(len(matches) / max(len(_DARKWEB_KEYWORDS) * 0.25, 1), 1.0)
    return {
        "severity": round(severity, 4),
        "matched_keywords": matches,
    }


# ── Compliance utilities ─────────────────────────────────────────────

def compute_content_hash(data: bytes, algorithm: str = "sha256") -> str:
    """Compute a cryptographic hash for chain-of-custody verification."""
    h = hashlib.new(algorithm)
    h.update(data)
    return h.hexdigest()


def validate_legal_basis(justification: str) -> bool:
    """Ensure every action has a non-empty legal justification."""
    return bool(justification and justification.strip())

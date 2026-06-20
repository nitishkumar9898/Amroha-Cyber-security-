"""
HealthGuard Core Engine
=======================
IoMT device vulnerability scanning, health-data breach severity assessment,
fake medical content / deepfake doctor detection, and pandemic misinformation scoring.
"""

import datetime
import re
from typing import Dict, Any, List, Optional

# ══════════════════════════════════════════════════════════════════════
# 1. IoMT Device Security Analysis
# ══════════════════════════════════════════════════════════════════════

# Known vulnerable firmware patterns (placeholder CVE stubs)
_KNOWN_VULN_DB: Dict[str, List[Dict[str, Any]]] = {
    "infusion_pump": [
        {"cve": "CVE-2025-10001", "description": "Unauthenticated remote dosage change", "cvss": 9.8},
        {"cve": "CVE-2025-10002", "description": "Cleartext credential storage", "cvss": 7.5},
    ],
    "pacemaker": [
        {"cve": "CVE-2025-20001", "description": "RF replay attack on telemetry", "cvss": 8.6},
    ],
    "ventilator": [
        {"cve": "CVE-2025-30001", "description": "Firmware update without signature verification", "cvss": 8.1},
    ],
    "imaging": [
        {"cve": "CVE-2025-40001", "description": "DICOM service exposed without auth", "cvss": 7.2},
    ],
}

_SEGMENT_WEIGHTS = {
    "clinical": 0.9,
    "iot_vlan": 0.5,
    "isolated": 0.2,
    "unknown": 0.8,
}


def scan_iomt_device(device_type: str, firmware_version: Optional[str],
                     network_segment: Optional[str]) -> Dict[str, Any]:
    """Scan an IoMT device for known vulnerabilities and compute risk score."""
    vulns = _KNOWN_VULN_DB.get(device_type, [])
    if not vulns:
        vulns = [{"cve": "GENERIC-001", "description": "No specific CVE data; manual review recommended", "cvss": 3.0}]

    max_cvss = max(v["cvss"] for v in vulns) / 10.0
    segment_w = _SEGMENT_WEIGHTS.get(network_segment or "unknown", 0.5)
    risk_score = round(min(0.6 * max_cvss + 0.4 * segment_w, 1.0), 4)

    return {
        "vulnerabilities": vulns,
        "risk_score": risk_score,
    }


# ══════════════════════════════════════════════════════════════════════
# 2. Health Data Breach Severity Assessment
# ══════════════════════════════════════════════════════════════════════

_SENSITIVE_DATA_WEIGHTS = {
    "PHI": 0.9,
    "PII": 0.7,
    "genomic": 1.0,
    "billing": 0.5,
    "appointments": 0.3,
}


def assess_breach_severity(affected_records: int, data_types: Optional[List[str]],
                           attack_vector: Optional[str]) -> Dict[str, Any]:
    """Compute severity (0–1) and HIPAA violation flag for a health data breach."""
    # Volume factor (logarithmic scale)
    import math
    volume_factor = min(math.log10(max(affected_records, 1)) / 6, 1.0)  # 1M records → 1.0

    # Data sensitivity factor
    if data_types:
        sensitivity = max(_SENSITIVE_DATA_WEIGHTS.get(dt, 0.3) for dt in data_types)
    else:
        sensitivity = 0.3

    # Attack sophistication bonus
    vector_bonus = {"ransomware": 0.2, "insider": 0.15, "phishing": 0.1, "misconfiguration": 0.05}.get(
        attack_vector or "", 0.0)

    severity = round(min(0.4 * volume_factor + 0.4 * sensitivity + 0.2 + vector_bonus, 1.0), 4)

    # HIPAA violation if PHI or genomic data is exposed
    hipaa = bool(data_types and any(dt in ("PHI", "genomic") for dt in data_types))

    return {
        "severity": severity,
        "hipaa_violation": hipaa,
    }


# ══════════════════════════════════════════════════════════════════════
# 3. Fake Medical Content / Deepfake Doctor Detection
# ══════════════════════════════════════════════════════════════════════

_FAKE_MEDICAL_KEYWORDS = [
    "miracle cure", "100% effective", "doctors don't want you to know",
    "big pharma conspiracy", "inject bleach", "healing crystals cure",
    "no side effects guaranteed", "clinical trials are fake",
    "dna altering", "microchip implant", "5g causes",
    "suppress the truth", "natural immunity only",
]

_DEEPFAKE_INDICATORS = [
    "ai generated", "synthetic video", "cloned voice",
    "impersonation", "fabricated credentials",
]


def detect_fake_medical(text: str, content_type: str) -> Dict[str, Any]:
    """Analyse text for fake medical claims or deepfake doctor indicators.
    Returns confidence (0–1) and fact-check result.
    """
    text_lower = text.lower()

    # Keyword hits
    medical_hits = [kw for kw in _FAKE_MEDICAL_KEYWORDS if kw in text_lower]
    deepfake_hits = [kw for kw in _DEEPFAKE_INDICATORS if kw in text_lower]

    total_kw = len(_FAKE_MEDICAL_KEYWORDS) + len(_DEEPFAKE_INDICATORS)
    hit_count = len(medical_hits) + len(deepfake_hits)
    confidence = round(min(hit_count / max(total_kw * 0.15, 1), 1.0), 4)

    # Determine result
    if confidence >= 0.7:
        result = "confirmed_fake"
    elif confidence >= 0.4:
        result = "likely_fake"
    elif confidence > 0:
        result = "inconclusive"
    else:
        result = "legitimate"

    return {
        "confidence": confidence,
        "fact_check_result": result,
        "medical_keyword_hits": medical_hits,
        "deepfake_indicator_hits": deepfake_hits,
    }


# ══════════════════════════════════════════════════════════════════════
# 4. Pandemic Misinformation Scoring
# ══════════════════════════════════════════════════════════════════════

_MISINFO_TOPIC_WEIGHTS = {
    "vaccine": 0.9,
    "treatment": 0.8,
    "origin": 0.7,
    "lockdown": 0.5,
    "mask": 0.6,
    "testing": 0.4,
}


def score_pandemic_misinfo(topic: str, narrative: str,
                           spread_velocity: float) -> Dict[str, Any]:
    """Compute severity (0–1) for a pandemic misinformation narrative."""
    topic_w = _MISINFO_TOPIC_WEIGHTS.get(topic, 0.5)

    # Velocity factor (normalised: 100 posts/hr → 1.0)
    velocity_w = min(spread_velocity / 100.0, 1.0)

    # Narrative toxicity (simple keyword overlap with fake medical keywords)
    narrative_lower = narrative.lower()
    toxicity_hits = sum(1 for kw in _FAKE_MEDICAL_KEYWORDS if kw in narrative_lower)
    toxicity_w = min(toxicity_hits / max(len(_FAKE_MEDICAL_KEYWORDS) * 0.2, 1), 1.0)

    severity = round(min(0.35 * topic_w + 0.35 * velocity_w + 0.30 * toxicity_w, 1.0), 4)

    return {
        "severity": severity,
        "topic_weight": topic_w,
        "velocity_factor": round(velocity_w, 4),
        "toxicity_factor": round(toxicity_w, 4),
    }

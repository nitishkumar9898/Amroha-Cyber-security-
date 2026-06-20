"""
MaritimeGuard Core Engine
=========================
AIS spoofing detection (haversine + speed/course anomalies),
shipboard OT/IT severity scoring, port supply-chain attack simulation,
and maritime cybersecurity compliance assessment.
"""

import datetime
import math
from typing import Dict, Any, List, Optional

# ══════════════════════════════════════════════════════════════════════
# 1. AIS Signal Analysis & Spoofing Detection
# ══════════════════════════════════════════════════════════════════════

_EARTH_RADIUS_KM = 6371.0
_KNOTS_TO_KMH = 1.852
_MAX_VESSEL_SPEED_KNOTS = 45.0     # fastest container ships ~25 kn; 45 is generous ceiling
_MAX_COURSE_CHANGE_DEG = 90.0      # >90° course change between consecutive pings is suspicious


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return _EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def analyze_ais_signal(current: Dict[str, Any],
                       previous: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Detect AIS spoofing by comparing consecutive signals.

    Checks:
      • Impossible speed (implied displacement vs. time)
      • On-land position (basic bounding-box for deep ocean only — stub)
      • Sudden course reversal
      • Reported speed vs. implied speed mismatch
    """
    anomalies: List[Dict[str, Any]] = []
    spoof = False

    if previous:
        try:
            t0 = datetime.datetime.fromisoformat(previous["timestamp"]) if isinstance(previous["timestamp"], str) else previous["timestamp"]
            t1 = datetime.datetime.fromisoformat(current["timestamp"]) if isinstance(current["timestamp"], str) else current["timestamp"]
        except (KeyError, ValueError):
            t0 = t1 = datetime.datetime.utcnow()

        dt_hours = max((t1 - t0).total_seconds() / 3600, 1e-6)
        dist_km = _haversine(previous["latitude"], previous["longitude"],
                             current["latitude"], current["longitude"])
        implied_speed_kn = (dist_km / _KNOTS_TO_KMH) / dt_hours

        # Check impossible speed
        if implied_speed_kn > _MAX_VESSEL_SPEED_KNOTS * 2:
            spoof = True
            anomalies.append({
                "type": "impossible_speed",
                "implied_knots": round(implied_speed_kn, 2),
                "max_expected": _MAX_VESSEL_SPEED_KNOTS,
            })

        # Check reported vs implied speed mismatch
        reported = current.get("speed_knots")
        if reported is not None and implied_speed_kn > 1:
            ratio = abs(reported - implied_speed_kn) / max(implied_speed_kn, 0.1)
            if ratio > 2.0:
                anomalies.append({
                    "type": "speed_mismatch",
                    "reported_knots": reported,
                    "implied_knots": round(implied_speed_kn, 2),
                })

        # Course reversal
        prev_course = previous.get("course")
        curr_course = current.get("course")
        if prev_course is not None and curr_course is not None:
            delta = abs(curr_course - prev_course)
            if delta > 180:
                delta = 360 - delta
            if delta > _MAX_COURSE_CHANGE_DEG:
                anomalies.append({
                    "type": "sudden_course_change",
                    "delta_degrees": round(delta, 1),
                })

    # Position sanity (very rough: lat must be -90..90, lon -180..180)
    if not (-90 <= current["latitude"] <= 90) or not (-180 <= current["longitude"] <= 180):
        spoof = True
        anomalies.append({"type": "invalid_coordinates"})

    confidence = min(len(anomalies) / 3, 1.0) if anomalies else 0.0
    if confidence >= 0.5:
        spoof = True

    return {
        "spoof_detected": spoof,
        "spoof_confidence": round(confidence, 4),
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
    }


# ══════════════════════════════════════════════════════════════════════
# 2. Shipboard OT/IT Severity Scoring
# ══════════════════════════════════════════════════════════════════════

_SYSTEM_CRITICALITY = {
    "ECDIS":           0.95,
    "engine_control":  0.90,
    "ballast":         0.85,
    "cargo":           0.75,
    "nav_radar":       0.80,
    "GMDSS":           0.70,
    "crew_wifi":       0.30,
}

_INCIDENT_SEVERITY = {
    "malware":            0.9,
    "unauthorised_access": 0.8,
    "config_tamper":      0.7,
    "firmware_mod":       0.85,
    "dos":                0.6,
}


def assess_shipboard_severity(system_type: str, incident_type: Optional[str],
                               findings: Optional[List[Dict[str, Any]]]) -> float:
    """Compute overall severity (0–1) for a shipboard OT/IT incident."""
    sys_w = _SYSTEM_CRITICALITY.get(system_type, 0.5)
    inc_w = _INCIDENT_SEVERITY.get(incident_type or "", 0.5)
    finding_w = min(len(findings or []) * 0.1, 0.3)
    return round(min(0.45 * sys_w + 0.40 * inc_w + finding_w, 1.0), 4)


# ══════════════════════════════════════════════════════════════════════
# 3. Port Supply-Chain Attack Simulation
# ══════════════════════════════════════════════════════════════════════

_PORT_ATTACK_VECTORS = {
    "crane_control":   {"base_impact": 0.9,  "description": "Compromised STS crane PLC"},
    "TOS_compromise":  {"base_impact": 0.85, "description": "Terminal Operating System ransomware"},
    "gate_system":     {"base_impact": 0.6,  "description": "Automated gate / truck queue manipulation"},
    "fuel_bunker":     {"base_impact": 0.7,  "description": "Fuel management system tampering"},
    "ais_injection":   {"base_impact": 0.75, "description": "Fake AIS signals near port approach"},
}


def simulate_port_attack(port_name: str, attack_vector: str,
                         parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Run a deterministic port supply-chain attack simulation."""
    vector_info = _PORT_ATTACK_VECTORS.get(attack_vector, {
        "base_impact": 0.5, "description": "Unknown vector"
    })
    defence_level = parameters.get("defence_level", 0.5)
    attacker_skill = parameters.get("attacker_skill", 0.5)

    # Resilience model
    base = defence_level * 0.65 + 0.15
    penalty = attacker_skill * vector_info["base_impact"] * 0.5
    resilience = max(0.0, min(base - penalty + 0.1, 1.0))

    breach = resilience < 0.4
    downtime_hours = round((1 - resilience) * 72, 1) if breach else 0  # up to 72h port shutdown

    return {
        "port_name": port_name,
        "attack_vector": attack_vector,
        "vector_description": vector_info["description"],
        "resilience_score": round(resilience, 4),
        "breach": breach,
        "estimated_downtime_hours": downtime_hours,
        "economic_impact_estimate": f"${round(downtime_hours * 2.5, 1)}M" if breach else "$0",
        "recommendation": "Strengthen OT segmentation and incident response" if breach else "Current defences adequate",
    }


# ══════════════════════════════════════════════════════════════════════
# 4. Maritime Compliance Assessment
# ══════════════════════════════════════════════════════════════════════

_COMPLIANCE_FRAMEWORKS: Dict[str, List[Dict[str, Any]]] = {
    "IMO_MSC428": [
        {"control": "Cyber risk in SMS", "weight": 0.2},
        {"control": "Incident response plan", "weight": 0.2},
        {"control": "Network segmentation", "weight": 0.15},
        {"control": "Access control policy", "weight": 0.15},
        {"control": "Software update management", "weight": 0.15},
        {"control": "Crew cyber awareness training", "weight": 0.15},
    ],
    "ISPS_Code": [
        {"control": "Ship Security Plan cyber annex", "weight": 0.25},
        {"control": "Port facility security assessment", "weight": 0.25},
        {"control": "Communication security", "weight": 0.25},
        {"control": "Security drill with cyber scenario", "weight": 0.25},
    ],
    "BIMCO": [
        {"control": "Identify threats", "weight": 0.2},
        {"control": "Identify vulnerabilities", "weight": 0.2},
        {"control": "Risk assessment", "weight": 0.2},
        {"control": "Protective measures", "weight": 0.2},
        {"control": "Contingency planning", "weight": 0.2},
    ],
}


def assess_compliance(framework: str) -> Dict[str, Any]:
    """Generate a stub compliance assessment.
    In production this would pull real audit data.
    Returns score, findings, and recommendations.
    """
    controls = _COMPLIANCE_FRAMEWORKS.get(framework, [])
    if not controls:
        return {
            "overall_score": 0.0,
            "findings": [{"control": "Unknown framework", "status": "not_assessed"}],
            "recommendations": [{"action": f"Framework '{framework}' not recognised. Use IMO_MSC428, ISPS_Code, or BIMCO."}],
        }

    # Stub: assume 60% compliance on each control (placeholder for real audit)
    compliance_pct = 0.6
    findings = []
    recommendations = []
    score = 0.0

    for ctrl in controls:
        passed = compliance_pct >= 0.5
        findings.append({
            "control": ctrl["control"],
            "status": "pass" if passed else "fail",
            "compliance_pct": compliance_pct,
        })
        score += ctrl["weight"] * compliance_pct
        if not passed:
            recommendations.append({
                "control": ctrl["control"],
                "action": f"Implement or improve '{ctrl['control']}'",
                "priority": "high",
            })

    if not recommendations:
        recommendations.append({"action": "Continue current cyber hygiene practices", "priority": "low"})

    return {
        "overall_score": round(score, 4),
        "findings": findings,
        "recommendations": recommendations,
    }

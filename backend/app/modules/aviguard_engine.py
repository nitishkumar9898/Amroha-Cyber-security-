"""
AviGuard Core Engine
====================
ADS-B spoofing detection, avionics severity scoring, airport network
vulnerability assessment, drone interference simulation, and aviation
regulatory compliance (DGCA / ICAO / EASA).
"""

import datetime
import math
from typing import Dict, Any, List, Optional

# ══════════════════════════════════════════════════════════════════════
# 1. ADS-B Signal Analysis & Spoofing Detection
# ══════════════════════════════════════════════════════════════════════

_EARTH_RADIUS_KM = 6371.0
_KNOTS_TO_KMH = 1.852
_MAX_AIRCRAFT_SPEED_KN = 600.0      # supersonic ceiling for commercial
_MAX_CLIMB_RATE_FPM = 6000.0        # feet per minute
_EMERGENCY_SQUAWKS = {"7500", "7600", "7700"}


def _haversine(lat1, lon1, lat2, lon2):
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return _EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def analyze_adsb_signal(current: Dict[str, Any],
                        previous: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Detect ADS-B spoofing via speed, altitude rate, coordinate, and squawk checks."""
    anomalies: List[Dict[str, Any]] = []
    spoof = False

    # Coordinate validity
    if not (-90 <= current["latitude"] <= 90) or not (-180 <= current["longitude"] <= 180):
        spoof = True
        anomalies.append({"type": "invalid_coordinates"})

    # Squawk analysis
    squawk = current.get("squawk")
    if squawk and squawk in _EMERGENCY_SQUAWKS:
        anomalies.append({"type": "emergency_squawk", "code": squawk})

    if previous:
        try:
            t0 = previous["timestamp"] if isinstance(previous["timestamp"], datetime.datetime) else datetime.datetime.fromisoformat(previous["timestamp"])
            t1 = current.get("timestamp", datetime.datetime.utcnow())
            if isinstance(t1, str):
                t1 = datetime.datetime.fromisoformat(t1)
        except (KeyError, ValueError):
            t0 = t1 = datetime.datetime.utcnow()

        dt_hours = max((t1 - t0).total_seconds() / 3600, 1e-6)
        dt_minutes = dt_hours * 60

        # Impossible speed
        dist_km = _haversine(previous["latitude"], previous["longitude"],
                             current["latitude"], current["longitude"])
        implied_kn = (dist_km / _KNOTS_TO_KMH) / dt_hours
        if implied_kn > _MAX_AIRCRAFT_SPEED_KN * 1.5:
            spoof = True
            anomalies.append({"type": "impossible_speed", "implied_knots": round(implied_kn, 1)})

        # Impossible climb/descent rate
        prev_alt = previous.get("altitude_ft")
        curr_alt = current.get("altitude_ft")
        if prev_alt is not None and curr_alt is not None and dt_minutes > 0:
            climb_rate = abs(curr_alt - prev_alt) / dt_minutes
            if climb_rate > _MAX_CLIMB_RATE_FPM * 2:
                spoof = True
                anomalies.append({"type": "impossible_climb_rate", "fpm": round(climb_rate, 0)})

        # Heading reversal
        prev_hdg = previous.get("heading")
        curr_hdg = current.get("heading")
        if prev_hdg is not None and curr_hdg is not None:
            delta = abs(curr_hdg - prev_hdg)
            if delta > 180:
                delta = 360 - delta
            if delta > 120:
                anomalies.append({"type": "sudden_heading_change", "delta": round(delta, 1)})

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
# 2. Avionics Severity Scoring
# ══════════════════════════════════════════════════════════════════════

_AVIONICS_CRITICALITY = {
    "FMS":    0.95,   # Flight Management System
    "EFB":    0.70,   # Electronic Flight Bag
    "IFE":    0.30,   # In-Flight Entertainment
    "ACARS":  0.85,   # Aircraft Communications
    "SATCOM": 0.75,
    "TCAS":   0.90,   # Traffic Collision Avoidance
}

_INCIDENT_WEIGHTS = {
    "malware":            0.90,
    "firmware_tamper":    0.85,
    "config_change":      0.70,
    "unauthorised_access": 0.80,
}


def assess_avionics_severity(system_type: str, incident_type: Optional[str],
                              findings: Optional[List[Dict[str, Any]]]) -> float:
    sys_w = _AVIONICS_CRITICALITY.get(system_type, 0.5)
    inc_w = _INCIDENT_WEIGHTS.get(incident_type or "", 0.5)
    finding_w = min(len(findings or []) * 0.1, 0.3)
    return round(min(0.45 * sys_w + 0.40 * inc_w + finding_w, 1.0), 4)


# ══════════════════════════════════════════════════════════════════════
# 3. Airport Network Vulnerability Assessment
# ══════════════════════════════════════════════════════════════════════

def scan_airport_network(airport_code: str, scan_type: str) -> Dict[str, Any]:
    """Simulate airport network/security scan (placeholder findings)."""
    findings: List[Dict[str, Any]] = []

    if scan_type == "network_segmentation":
        findings = [
            {"type": "flat_network", "severity": "high", "detail": "OT and IT on same VLAN", "recommendation": "Segment OT/IT networks"},
            {"type": "unpatched_switch", "severity": "medium", "detail": "Core switch firmware outdated", "recommendation": "Apply vendor patch"},
        ]
    elif scan_type == "pax_data_audit":
        findings = [
            {"type": "unencrypted_pnr", "severity": "critical", "detail": "PNR data transmitted in cleartext", "recommendation": "Encrypt all PII in transit and at rest"},
        ]
    elif scan_type == "wifi_security":
        findings = [
            {"type": "open_wifi", "severity": "high", "detail": "Staff Wi-Fi SSID has no WPA3", "recommendation": "Enforce WPA3-Enterprise"},
        ]
    elif scan_type == "cctv_network":
        findings = [
            {"type": "default_creds", "severity": "critical", "detail": "CCTV NVR using default admin password", "recommendation": "Change credentials and disable default accounts"},
        ]

    sev_map = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
    risk = max((sev_map.get(f.get("severity", "low"), 0.2) for f in findings), default=0.0)
    return {"findings": findings, "risk_score": round(risk, 4)}


# ══════════════════════════════════════════════════════════════════════
# 4. Drone Interference Simulation
# ══════════════════════════════════════════════════════════════════════

_DRONE_VECTORS = {
    "gps_jam":          {"base_impact": 0.85, "desc": "GPS jamming near approach path"},
    "rf_hijack":        {"base_impact": 0.80, "desc": "RF command hijack of commercial drone"},
    "swarm_incursion":  {"base_impact": 0.90, "desc": "Coordinated drone swarm runway incursion"},
    "runway_intrusion": {"base_impact": 0.75, "desc": "Single drone runway incursion"},
}


def simulate_drone_interference(scenario_name: str, attack_vector: str,
                                 parameters: Dict[str, Any]) -> Dict[str, Any]:
    vec = _DRONE_VECTORS.get(attack_vector, {"base_impact": 0.5, "desc": "Unknown vector"})
    defence = parameters.get("defence_level", 0.5)
    attacker = parameters.get("attacker_skill", 0.5)

    base = defence * 0.65 + 0.15
    penalty = attacker * vec["base_impact"] * 0.5
    resilience = max(0.0, min(base - penalty + 0.1, 1.0))
    breach = resilience < 0.4
    downtime_min = round((1 - resilience) * 180, 0) if breach else 0

    return {
        "scenario_name": scenario_name,
        "attack_vector": attack_vector,
        "vector_description": vec["desc"],
        "resilience_score": round(resilience, 4),
        "breach": breach,
        "estimated_runway_closure_min": downtime_min,
        "recommendation": "Deploy counter-UAS systems and GNSS backup" if breach else "Current defences adequate",
    }


# ══════════════════════════════════════════════════════════════════════
# 5. Aviation Compliance (DGCA / ICAO / EASA)
# ══════════════════════════════════════════════════════════════════════

_AVIATION_FRAMEWORKS: Dict[str, List[Dict[str, Any]]] = {
    "ICAO_Annex17": [
        {"control": "Cybersecurity in aviation security programme", "weight": 0.20},
        {"control": "Access control to critical systems", "weight": 0.20},
        {"control": "Incident detection and response", "weight": 0.15},
        {"control": "Supply chain security", "weight": 0.15},
        {"control": "Personnel training", "weight": 0.15},
        {"control": "Information sharing with authorities", "weight": 0.15},
    ],
    "DGCA_CAR": [
        {"control": "Cyber risk assessment", "weight": 0.25},
        {"control": "Network segmentation", "weight": 0.20},
        {"control": "Periodic vulnerability assessment", "weight": 0.20},
        {"control": "SOC/CERT integration", "weight": 0.20},
        {"control": "Regulatory reporting", "weight": 0.15},
    ],
    "EASA_Part_IS": [
        {"control": "Information security management system", "weight": 0.20},
        {"control": "Risk treatment plan", "weight": 0.20},
        {"control": "Incident management", "weight": 0.20},
        {"control": "Human factors", "weight": 0.20},
        {"control": "External service provider oversight", "weight": 0.20},
    ],
}


def assess_aviation_compliance(framework: str) -> Dict[str, Any]:
    controls = _AVIATION_FRAMEWORKS.get(framework, [])
    if not controls:
        return {
            "overall_score": 0.0,
            "findings": [{"control": "Unknown framework", "status": "not_assessed"}],
            "recommendations": [{"action": f"Framework '{framework}' not recognised."}],
        }

    compliance_pct = 0.6  # stub
    findings = []
    recommendations = []
    score = 0.0

    for ctrl in controls:
        passed = compliance_pct >= 0.5
        findings.append({"control": ctrl["control"], "status": "pass" if passed else "fail", "compliance_pct": compliance_pct})
        score += ctrl["weight"] * compliance_pct
        if not passed:
            recommendations.append({"control": ctrl["control"], "action": f"Implement '{ctrl['control']}'", "priority": "high"})

    if not recommendations:
        recommendations.append({"action": "Continue current cybersecurity practices", "priority": "low"})

    return {"overall_score": round(score, 4), "findings": findings, "recommendations": recommendations}

"""
EcoGuard Core Engine
====================
Dark-web wildlife trade classification, GPS spoof detection,
environmental data tamper scoring, and lightweight search index.
"""

import datetime
import math
import uuid
from typing import Dict, Any, List

# ── Dark-web Wildlife Trade Classifier (rule-based stub) ──────────────

_WILDLIFE_KEYWORDS = [
    "ivory", "tusk", "rhino horn", "pangolin", "scales", "tiger bone",
    "bushmeat", "parrot", "tortoise", "reptile", "exotic pet",
    "cites", "endangered", "smuggle", "poaching", "trafficking",
]

def classify_listing(text: str) -> float:
    """Return a confidence score (0–1) that the text describes an illegal
    wildlife trade listing.  Placeholder: weighted keyword overlap."""
    text_lower = text.lower()
    hits = sum(1 for kw in _WILDLIFE_KEYWORDS if kw in text_lower)
    return min(hits / max(len(_WILDLIFE_KEYWORDS) * 0.3, 1), 1.0)


# ── GPS Spoof Detection ──────────────────────────────────────────────

_EARTH_RADIUS_KM = 6371.0
_MAX_SPEED_KMH = 900.0  # commercial aircraft ceiling; anything above is suspicious

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in km between two geographic points."""
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return _EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def analyze_gps(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Examine a list of waypoints for impossible jumps.

    Expected payload format::

        {"waypoints": [
            {"lat": 28.6, "lon": 77.2, "timestamp": "2026-06-01T12:00:00", "speed": 50},
            ...
        ]}
    """
    waypoints = payload.get("waypoints", [])
    anomalies: List[Dict[str, Any]] = []
    spoof_detected = False

    for i in range(1, len(waypoints)):
        prev, curr = waypoints[i - 1], waypoints[i]
        try:
            t0 = datetime.datetime.fromisoformat(prev["timestamp"])
            t1 = datetime.datetime.fromisoformat(curr["timestamp"])
        except (KeyError, ValueError):
            continue
        dt_hours = max((t1 - t0).total_seconds() / 3600, 1e-6)
        dist_km = _haversine(prev["lat"], prev["lon"], curr["lat"], curr["lon"])
        implied_speed = dist_km / dt_hours

        if implied_speed > _MAX_SPEED_KMH:
            spoof_detected = True
            anomalies.append({
                "from_index": i - 1,
                "to_index": i,
                "distance_km": round(dist_km, 2),
                "time_hours": round(dt_hours, 4),
                "implied_speed_kmh": round(implied_speed, 2),
                "reason": "impossible_speed",
            })

        # Check for time travel (non-monotonic timestamps)
        if t1 < t0:
            spoof_detected = True
            anomalies.append({
                "from_index": i - 1,
                "to_index": i,
                "reason": "time_travel",
            })

    return {
        "spoof_detected": spoof_detected,
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
    }


# ── Environmental Tamper Detection ────────────────────────────────────

def compute_tamper_score(readings: List[float]) -> float:
    """Simple statistical outlier score.  Returns 0–1 where >0.7 is suspicious.

    Computes the ratio of readings beyond 2σ from the mean.
    """
    if len(readings) < 3:
        return 0.0
    mean = sum(readings) / len(readings)
    variance = sum((r - mean) ** 2 for r in readings) / len(readings)
    std = math.sqrt(variance) if variance > 0 else 1e-9
    outliers = sum(1 for r in readings if abs(r - mean) > 2 * std)
    return min(outliers / len(readings) * 2, 1.0)  # scale up slightly


# ── Lightweight Search Index ──────────────────────────────────────────

_index: Dict[int, Dict[str, int]] = {}  # record_id → word→freq

def _tokenize(text: str) -> List[str]:
    return [t.lower().strip(".,;:!?()[]{}\"'") for t in text.split() if len(t) > 1]

def index_record(record_id: int, text: str):
    freq: Dict[str, int] = {}
    for tok in _tokenize(text):
        freq[tok] = freq.get(tok, 0) + 1
    _index[record_id] = freq

def search_index(query: str, top_k: int = 10) -> List[int]:
    tokens = set(_tokenize(query))
    scores = []
    for rid, freq in _index.items():
        score = sum(freq.get(t, 0) for t in tokens)
        if score:
            scores.append((rid, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [rid for rid, _ in scores[:top_k]]


# ── Agency Collaboration Token ────────────────────────────────────────

def generate_agency_token(agency_name: str) -> str:
    """Generate a simple API-key token for an enforcement agency."""
    return f"ECO-{uuid.uuid4().hex[:16].upper()}"

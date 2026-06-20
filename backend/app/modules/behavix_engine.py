from typing import Dict, Any

def analyze_behavior(baseline_key: float, baseline_mouse: float, session_metrics: Dict[str, float]) -> Dict[str, Any]:
    """
    Analyzes current session metrics against baseline profiles.
    """
    key_diff = abs(baseline_key - session_metrics["keystroke_speed"])
    mouse_diff = abs(baseline_mouse - session_metrics["mouse_jerkiness"])
    
    risk_score = (key_diff * 0.6) + (mouse_diff * 0.4)
    anomaly = risk_score > 0.5
    
    reason = "Significant deviation from historical interaction patterns." if anomaly else "Behavior within normal bounds."
    
    return {
        "anomaly_detected": anomaly,
        "risk_score": min(risk_score, 1.0),
        "reason": reason
    }

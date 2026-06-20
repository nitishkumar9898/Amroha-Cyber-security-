from typing import Dict, Any

def analyze_anomaly(source: str, observed: float, expected: float) -> Dict[str, Any]:
    """
    Simulates central anomaly detection and root cause analysis.
    """
    deviation = abs(observed - expected) / max(expected, 0.01)
    
    if deviation > 0.5:
        cause = "High likelihood of lateral movement or unauthorized data exfiltration."
    else:
        cause = "Possible benign misconfiguration or intermittent network delay."
        
    return {
        "deviation_score": min(deviation, 1.0),
        "root_cause_hypothesis": cause
    }

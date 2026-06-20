from typing import Dict, Any

def analyze_hybrid_threat(sector: str, vector: str) -> Dict[str, Any]:
    """
    Simulates detection of state-sponsored cyber terrorism and hybrid warfare.
    """
    prob = 0.92 if "grid" in sector.lower() or "apt" in vector.lower() else 0.15
    level = "Critical" if prob > 0.8 else "Elevated"
    
    return {
        "state_sponsor_prob": prob,
        "threat_level": level
    }

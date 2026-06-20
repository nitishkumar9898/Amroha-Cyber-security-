from typing import Dict, Any

def analyze_legacy_system(system: str, protocol: str, air_gap: str) -> Dict[str, Any]:
    """
    Simulates reverse engineering and OT migration risk assessment.
    """
    risk = 0.85 if "modbus" in protocol.lower() or "scada" in system.lower() else 0.35
    if air_gap.lower() == "compromised":
        risk += 0.15
        
    return {
        "migration_risk_score": min(risk, 1.0)
    }

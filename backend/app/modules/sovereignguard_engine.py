from typing import Dict, Any

def check_data_sovereignty(classification: str, region: str) -> Dict[str, Any]:
    """
    Simulates data sovereignty checks against cross-border transfers.
    """
    risk = 0.95 if "top secret" in classification.lower() and region.upper() not in ["US", "EU-LOCAL"] else 0.10
    status = "Violated" if risk > 0.5 else "Compliant"
    
    return {
        "compliance_status": status,
        "violation_risk_score": risk
    }

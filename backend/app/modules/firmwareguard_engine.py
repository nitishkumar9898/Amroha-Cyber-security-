from typing import Dict, Any, List

def analyze_firmware(file_hash: str, is_signed: bool) -> Dict[str, Any]:
    """
    Simulates reverse engineering and analysis of a firmware image.
    Checks for hardcoded secrets, backdoors, and secure boot validity.
    """
    findings = []
    risk_score = 0.1

    if not is_signed:
        findings.append("Unsigned firmware detected (Secure Boot validation failed).")
        risk_score += 0.5
    
    # Mock analysis based on hash
    if "bad" in file_hash.lower():
        findings.append("Hardcoded credentials found in binaries.")
        risk_score += 0.3

    return {
        "risk_score": min(risk_score, 1.0),
        "findings": findings if findings else ["No significant threats detected."],
        "status": "Analysis Complete"
    }

class PhishingDetector:
    """Analyzes text for phishing/vishing keywords and domain spoofing."""
    @staticmethod
    def detect(content_body: str, sender_domain: str) -> dict:
        content_lower = content_body.lower()
        phishing_keywords = ["reset your password", "wire transfer", "gift card", "verify your account", "urgent action required"]
        
        matches = [kw for kw in phishing_keywords if kw in content_lower]
        is_spoofed = sender_domain.endswith(".co") or "support-" in sender_domain
        
        confidence = 0.0
        if matches:
            confidence += len(matches) * 20.0
        if is_spoofed:
            confidence += 40.0
            
        is_phishing = confidence >= 50.0
        
        return {
            "is_phishing": is_phishing,
            "confidence_score": min(confidence, 100.0),
            "detected_markers": f"Keywords: {len(matches)}, Spoofed Domain: {is_spoofed}"
        }

class PsychologyAnalyzer:
    """Detects cognitive bias exploitation in communication."""
    @staticmethod
    def analyze(urgency_level: float, authority_impersonation: bool) -> dict:
        manipulation_type = "NONE"
        severity = "LOW"
        
        if urgency_level > 7.0 and authority_impersonation:
            manipulation_type = "COGNITIVE_EXPLOITATION (Urgency + Authority)"
            severity = "CRITICAL"
        elif urgency_level > 7.0:
            manipulation_type = "ARTIFICIAL_URGENCY"
            severity = "HIGH"
        elif authority_impersonation:
            manipulation_type = "AUTHORITY_BIAS_EXPLOIT"
            severity = "HIGH"
            
        return {
            "manipulation_type": manipulation_type,
            "severity_level": severity
        }

class TrainingSimulator:
    """Generates mock phishing payloads based on employee vulnerability."""
    @staticmethod
    def simulate(target_vulnerability: str) -> dict:
        if target_vulnerability == "FINANCIAL_URGENCY":
            payload = "URGENT: Your recent payroll deposit has been suspended. Click here to verify your banking details within 24 hours."
            difficulty = 8.5
        elif target_vulnerability == "IT_SUPPORT_SPOOF":
            payload = "IT Desk: Mandatory software update required for your workstation. Run the attached executable to maintain network access."
            difficulty = 7.0
        else:
            payload = "Generic Newsletter: Click here to view the latest company news."
            difficulty = 3.0
            
        return {
            "scenario_type": f"MOCK_PHISHING_{target_vulnerability}",
            "payload_content": payload,
            "difficulty_rating": difficulty
        }

class InsiderProfiler:
    """Links social engineering vulnerability to insider threat scores."""
    @staticmethod
    def link_profile(base_risk: float, failed_simulations: int) -> dict:
        # Each failed simulation increases the insider risk multiplier
        penalty_multiplier = 1.0 + (failed_simulations * 0.15)
        adjusted_risk = min(base_risk * penalty_multiplier, 100.0)
        
        reasoning = f"Base risk {base_risk} elevated by {penalty_multiplier}x multiplier due to {failed_simulations} failed psychological assessments."
        
        return {
            "adjusted_insider_risk": adjusted_risk,
            "reasoning": reasoning
        }

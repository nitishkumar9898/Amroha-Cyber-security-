class IdeaDetector:
    """Analyzes research text to autonomously detect patentable IP."""
    @staticmethod
    def detect(text: str) -> dict:
        text_lower = text.lower()
        
        # Simple heuristic for demonstration
        if "novel" in text_lower and ("algorithm" in text_lower or "hardware" in text_lower or "sensor" in text_lower):
            topic = "Advanced Hardware/Algorithm Architecture"
            score = 92.5
            claim = "A method and apparatus comprising a novel sensory architecture that..."
        elif "quantum" in text_lower or "nano" in text_lower:
            topic = "Sub-Molecular/Quantum Process"
            score = 88.0
            claim = "A system for executing sub-molecular operations wherein..."
        else:
            topic = "General Research"
            score = 35.0
            claim = "No patentable claim generated. High prior art probability."
            
        return {
            "detected_topic": topic,
            "novelty_score": score,
            "generated_claim": claim
        }

class IPTheftInvestigator:
    """Heuristic for detecting IP exfiltration from access logs."""
    @staticmethod
    def investigate(volume_gb: float, time_of_access: str) -> dict:
        time_of_access = time_of_access.upper()
        
        # Trigger if downloading > 5GB outside business hours
        if volume_gb > 5.0 and time_of_access == "NON_BUSINESS":
            is_risk = True
            action = "IP_EXFILTRATION_RISK: Account locked down. Security team dispatched."
        elif volume_gb > 10.0:
            is_risk = True
            action = "ANOMALOUS_VOLUME: Temporary throttle applied. Manager review required."
        else:
            is_risk = False
            action = "Access nominal. No action taken."
            
        return {
            "is_exfiltration_risk": is_risk,
            "action_taken": action
        }

class InnovationTracker:
    """State machine for tracking innovation lifecycle."""
    @staticmethod
    def update_stage(current: str) -> dict:
        current = current.upper()
        valid_stages = ["RAW_RESEARCH", "PATENT_PENDING", "SECURED"]
        
        if current not in valid_stages:
            return {
                "stage": "ERROR",
                "message": f"Invalid stage: {current}. Must be one of {valid_stages}."
            }
            
        return {
            "stage": current,
            "message": f"Innovation track updated to {current}."
        }

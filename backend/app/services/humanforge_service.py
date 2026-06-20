from sqlalchemy.orm import Session
from ..models.humanforge import PhishingAnalysis, PsychologicalManipulation, AwarenessSimulation, InsiderThreatLink
from ..schemas.humanforge import PhishingDetectionRequest, ManipulationAnalysisRequest, AwarenessSimulationRequest, InsiderLinkRequest
from ..modules.humanforge_engine import PhishingDetector, PsychologyAnalyzer, TrainingSimulator, InsiderProfiler

class HumanForgeService:
    @staticmethod
    def detect_phishing(db: Session, payload: PhishingDetectionRequest) -> dict:
        result = PhishingDetector.detect(payload.content_body, payload.sender_domain)
        
        analysis = PhishingAnalysis(
            message_id=payload.message_id,
            is_phishing=result["is_phishing"],
            confidence_score=result["confidence_score"],
            detected_markers=result["detected_markers"]
        )
        db.add(analysis)
        db.commit()
        
        return {
            "message_id": payload.message_id,
            "is_phishing": result["is_phishing"],
            "confidence_score": result["confidence_score"],
            "detected_markers": result["detected_markers"]
        }

    @staticmethod
    def analyze_manipulation(db: Session, payload: ManipulationAnalysisRequest) -> dict:
        result = PsychologyAnalyzer.analyze(payload.urgency_level, payload.authority_impersonation)
        
        manipulation = PsychologicalManipulation(
            transcript_id=payload.transcript_id,
            manipulation_type=result["manipulation_type"],
            severity_level=result["severity_level"]
        )
        db.add(manipulation)
        db.commit()
        
        return {
            "transcript_id": payload.transcript_id,
            "manipulation_type": result["manipulation_type"],
            "severity_level": result["severity_level"]
        }

    @staticmethod
    def simulate_awareness(db: Session, payload: AwarenessSimulationRequest) -> dict:
        result = TrainingSimulator.simulate(payload.target_vulnerability)
        
        simulation = AwarenessSimulation(
            employee_id=payload.employee_id,
            scenario_type=result["scenario_type"],
            payload_content=result["payload_content"],
            difficulty_rating=result["difficulty_rating"]
        )
        db.add(simulation)
        db.commit()
        
        return {
            "employee_id": payload.employee_id,
            "scenario_type": result["scenario_type"],
            "payload_content": result["payload_content"],
            "difficulty_rating": result["difficulty_rating"]
        }

    @staticmethod
    def link_insider(db: Session, payload: InsiderLinkRequest) -> dict:
        result = InsiderProfiler.link_profile(payload.base_insider_risk, payload.failed_simulations_count)
        
        link = InsiderThreatLink(
            employee_id=payload.employee_id,
            base_insider_risk=payload.base_insider_risk,
            adjusted_insider_risk=result["adjusted_insider_risk"],
            reasoning=result["reasoning"]
        )
        db.add(link)
        db.commit()
        
        return {
            "employee_id": payload.employee_id,
            "base_insider_risk": payload.base_insider_risk,
            "adjusted_insider_risk": result["adjusted_insider_risk"],
            "reasoning": result["reasoning"]
        }

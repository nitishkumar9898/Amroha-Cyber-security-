from sqlalchemy.orm import Session
from ..models.innovateguard import PatentableIdea, IPTheftInvestigation, InnovationTrack
from ..schemas.innovateguard import IdeaDetectionRequest, IPTheftRequest, InnovationTrackRequest
from ..modules.innovateguard_engine import IdeaDetector, IPTheftInvestigator, InnovationTracker

class InnovateGuardService:
    @staticmethod
    def detect_idea(db: Session, payload: IdeaDetectionRequest) -> dict:
        result = IdeaDetector.detect(payload.research_text)
        
        idea = PatentableIdea(
            research_data_id=payload.research_data_id,
            detected_topic=result["detected_topic"],
            novelty_score=result["novelty_score"],
            generated_claim=result["generated_claim"]
        )
        db.add(idea)
        db.commit()
        
        return {
            "research_data_id": payload.research_data_id,
            "detected_topic": result["detected_topic"],
            "novelty_score": result["novelty_score"],
            "generated_claim": result["generated_claim"]
        }

    @staticmethod
    def investigate_theft(db: Session, payload: IPTheftRequest) -> dict:
        result = IPTheftInvestigator.investigate(payload.data_volume_gb, payload.time_of_access)
        
        investigation = IPTheftInvestigation(
            user_id=payload.user_id,
            data_volume_gb=payload.data_volume_gb,
            time_of_access=payload.time_of_access,
            is_exfiltration_risk=result["is_exfiltration_risk"],
            action_taken=result["action_taken"]
        )
        db.add(investigation)
        db.commit()
        
        return {
            "user_id": payload.user_id,
            "is_exfiltration_risk": result["is_exfiltration_risk"],
            "action_taken": result["action_taken"]
        }

    @staticmethod
    def track_innovation(db: Session, payload: InnovationTrackRequest) -> dict:
        result = InnovationTracker.update_stage(payload.current_stage)
        
        if result["stage"] != "ERROR":
            track = InnovationTrack(
                project_name=payload.project_name,
                current_stage=result["stage"],
                owner_id=payload.owner_id
            )
            db.add(track)
            db.commit()
            
        return {
            "project_name": payload.project_name,
            "owner_id": payload.owner_id,
            "current_stage": result["stage"],
            "message": result["message"]
        }

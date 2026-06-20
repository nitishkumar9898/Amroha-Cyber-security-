from sqlalchemy.orm import Session
from ..models.zerotrustforge import AuthenticationEvent, MicroSegment, AccessRequest, SecurityPolicyAction
from ..schemas.zerotrustforge import AuthCheckRequest, SegmentCreateRequest, AccessEvaluationRequest, PolicyEnforcementRequest
from ..modules.zerotrustforge_engine import ContinuousAuthenticator, MicroSegmenter, LeastPrivilegeEvaluator, PolicyEnforcer

class ZeroTrustForgeService:
    @staticmethod
    def authenticate(db: Session, payload: AuthCheckRequest) -> dict:
        result = ContinuousAuthenticator.evaluate(payload.is_off_hours, payload.geo_location_anomaly)
        
        event = AuthenticationEvent(
            user_id=payload.user_id,
            device_id=payload.device_id,
            ip_address=payload.ip_address,
            context_anomalies=result["context_anomalies"],
            trust_score=result["trust_score"]
        )
        db.add(event)
        db.commit()
        
        return {
            "user_id": payload.user_id,
            "trust_score": result["trust_score"],
            "context_anomalies": result["context_anomalies"],
            "auth_status": result["auth_status"]
        }

    @staticmethod
    def create_segment(db: Session, payload: SegmentCreateRequest) -> dict:
        result = MicroSegmenter.evaluate_route(payload.source_segment, payload.target_segment, payload.is_whitelisted)
        
        segment = MicroSegment(
            source_segment=payload.source_segment,
            target_segment=payload.target_segment,
            is_whitelisted=payload.is_whitelisted
        )
        db.add(segment)
        db.commit()
        
        return {
            "source_segment": payload.source_segment,
            "target_segment": payload.target_segment,
            "is_whitelisted": payload.is_whitelisted,
            "status": result["status"]
        }

    @staticmethod
    def evaluate_access(db: Session, payload: AccessEvaluationRequest) -> dict:
        result = LeastPrivilegeEvaluator.evaluate(payload.user_trust_score, payload.required_trust_score)
        
        req = AccessRequest(
            user_id=payload.user_id,
            resource_id=payload.resource_id,
            required_trust_score=payload.required_trust_score,
            user_trust_score=payload.user_trust_score,
            access_granted=result["access_granted"]
        )
        db.add(req)
        db.commit()
        
        return {
            "user_id": payload.user_id,
            "resource_id": payload.resource_id,
            "access_granted": result["access_granted"],
            "reason": result["reason"]
        }

    @staticmethod
    def enforce_policy(db: Session, payload: PolicyEnforcementRequest) -> dict:
        result = PolicyEnforcer.enforce(payload.trigger_event, payload.trust_score)
        
        action = SecurityPolicyAction(
            trigger_event=payload.trigger_event,
            action_taken=result["action_taken"],
            target_user=payload.target_user
        )
        db.add(action)
        db.commit()
        
        return {
            "target_user": payload.target_user,
            "action_taken": result["action_taken"],
            "timestamp": result["timestamp"]
        }

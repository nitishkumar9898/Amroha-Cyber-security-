from sqlalchemy.orm import Session
from ..models.ethicsforge import GovernancePolicy, AIAuditLog, BiasDetectionReport
from ..schemas.ethicsforge import PolicyCreate, ActionEvaluationRequest, BiasScanRequest
from ..modules.ethicsforge_engine import BiasScanner, EthicalArbiter, TransparencyReporter

class EthicsForgeService:
    @staticmethod
    def create_policy(db: Session, payload: PolicyCreate) -> GovernancePolicy:
        policy = GovernancePolicy(
            policy_name=payload.policy_name,
            description=payload.description,
            severity_level=payload.severity_level
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        return policy

    @staticmethod
    def scan_bias(db: Session, payload: BiasScanRequest) -> dict:
        result = BiasScanner.scan(payload.model_name, payload.dataset_signature)
        
        report = BiasDetectionReport(
            model_name=payload.model_name,
            dataset_signature=payload.dataset_signature,
            bias_score=result["bias_score"],
            demographic_skew_detected=result["demographic_skew_detected"],
            mitigation_applied=result["mitigation_applied"]
        )
        db.add(report)
        db.commit()
        
        return {
            "model_name": payload.model_name,
            "bias_score": result["bias_score"],
            "demographic_skew_detected": result["demographic_skew_detected"],
            "mitigation_applied": result["mitigation_applied"]
        }

    @staticmethod
    def evaluate_action(db: Session, payload: ActionEvaluationRequest) -> dict:
        active_policies = db.query(GovernancePolicy).filter(GovernancePolicy.is_active == True).all()
        
        eval_result = EthicalArbiter.evaluate(payload.proposed_action, payload.action_context, active_policies)
        
        # Log to audit trail
        audit_log = AIAuditLog(
            module_source=payload.module_source,
            proposed_action=payload.proposed_action,
            decision=eval_result["decision"],
            policy_id=eval_result["violating_policy_id"],
            justification=eval_result["justification"]
        )
        db.add(audit_log)
        db.commit()
        
        return {
            "decision": eval_result["decision"],
            "justification": eval_result["justification"],
            "violating_policy_id": eval_result["violating_policy_id"]
        }

    @staticmethod
    def generate_transparency_report(db: Session, log_id: int) -> dict:
        log = db.query(AIAuditLog).filter(AIAuditLog.id == log_id).first()
        if not log:
            raise ValueError("Audit log not found")
            
        xai = TransparencyReporter.generate_explanation(log.proposed_action, log.decision, log.justification)
        
        return {
            "log_id": log.id,
            "module_source": log.module_source,
            "proposed_action": log.proposed_action,
            "decision": log.decision,
            "justification": log.justification,
            "xai_explanation": xai
        }

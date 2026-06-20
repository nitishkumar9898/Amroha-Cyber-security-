from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class GovernancePolicy(Base):
    __tablename__ = "ethicsforge_policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_name = Column(String, index=True)
    description = Column(String)
    severity_level = Column(String) # CRITICAL (Hard Block), WARNING (Soft Advisory)
    is_active = Column(Boolean, default=True)

class AIAuditLog(Base):
    __tablename__ = "ethicsforge_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    module_source = Column(String) # e.g., ResponseForge, InsiderShield
    proposed_action = Column(String)
    decision = Column(String) # APPROVED, VETOED
    policy_id = Column(Integer, nullable=True) # The policy that triggered the veto, if any
    justification = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class BiasDetectionReport(Base):
    __tablename__ = "ethicsforge_bias_reports"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String)
    dataset_signature = Column(String)
    bias_score = Column(Float) # 0.0 to 1.0
    demographic_skew_detected = Column(Boolean)
    mitigation_applied = Column(Boolean, default=False)

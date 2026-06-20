from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class PolicyBase(BaseModel):
    policy_name: str
    description: str
    severity_level: str # CRITICAL, WARNING

class PolicyCreate(PolicyBase):
    pass

class PolicyOut(PolicyBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class ActionEvaluationRequest(BaseModel):
    module_source: str
    proposed_action: str
    action_context: str # Stringified JSON or text describing the context

class ActionEvaluationResult(BaseModel):
    decision: str # APPROVED, VETOED, WARNING
    justification: str
    violating_policy_id: Optional[int]

class BiasScanRequest(BaseModel):
    model_name: str
    dataset_signature: str

class BiasScanResult(BaseModel):
    model_name: str
    bias_score: float
    demographic_skew_detected: bool
    mitigation_applied: bool

class TransparencyReportOut(BaseModel):
    log_id: int
    module_source: str
    proposed_action: str
    decision: str
    justification: str
    xai_explanation: str

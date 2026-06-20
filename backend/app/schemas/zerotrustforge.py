from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class AuthCheckRequest(BaseModel):
    user_id: str
    device_id: str
    ip_address: str
    is_off_hours: bool
    geo_location_anomaly: bool

class AuthCheckResult(BaseModel):
    user_id: str
    trust_score: float
    context_anomalies: int
    auth_status: str

class SegmentCreateRequest(BaseModel):
    source_segment: str
    target_segment: str
    is_whitelisted: bool

class SegmentCreateResult(BaseModel):
    source_segment: str
    target_segment: str
    is_whitelisted: bool
    status: str

class AccessEvaluationRequest(BaseModel):
    user_id: str
    resource_id: str
    user_trust_score: float
    required_trust_score: float

class AccessEvaluationResult(BaseModel):
    user_id: str
    resource_id: str
    access_granted: bool
    reason: str

class PolicyEnforcementRequest(BaseModel):
    trigger_event: str
    target_user: str
    trust_score: float

class PolicyEnforcementResult(BaseModel):
    target_user: str
    action_taken: str
    timestamp: str

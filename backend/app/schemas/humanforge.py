from pydantic import BaseModel, ConfigDict
from typing import Optional

class PhishingDetectionRequest(BaseModel):
    message_id: str
    content_body: str
    sender_domain: str

class PhishingDetectionResult(BaseModel):
    message_id: str
    is_phishing: bool
    confidence_score: float
    detected_markers: str

class ManipulationAnalysisRequest(BaseModel):
    transcript_id: str
    urgency_level: float # 0.0 to 10.0
    authority_impersonation: bool

class ManipulationAnalysisResult(BaseModel):
    transcript_id: str
    manipulation_type: str
    severity_level: str

class AwarenessSimulationRequest(BaseModel):
    employee_id: str
    target_vulnerability: str # e.g., "FINANCIAL_URGENCY", "IT_SUPPORT_SPOOF"

class AwarenessSimulationResult(BaseModel):
    employee_id: str
    scenario_type: str
    payload_content: str
    difficulty_rating: float

class InsiderLinkRequest(BaseModel):
    employee_id: str
    base_insider_risk: float
    failed_simulations_count: int

class InsiderLinkResult(BaseModel):
    employee_id: str
    base_insider_risk: float
    adjusted_insider_risk: float
    reasoning: str

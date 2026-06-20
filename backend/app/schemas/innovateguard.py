from pydantic import BaseModel, ConfigDict
from typing import Optional

class IdeaDetectionRequest(BaseModel):
    research_data_id: str
    research_text: str

class IdeaDetectionResult(BaseModel):
    research_data_id: str
    detected_topic: str
    novelty_score: float
    generated_claim: str

class IPTheftRequest(BaseModel):
    user_id: str
    data_volume_gb: float
    time_of_access: str

class IPTheftResult(BaseModel):
    user_id: str
    is_exfiltration_risk: bool
    action_taken: str

class InnovationTrackRequest(BaseModel):
    project_name: str
    owner_id: str
    current_stage: str

class InnovationTrackResult(BaseModel):
    project_name: str
    owner_id: str
    current_stage: str
    message: str

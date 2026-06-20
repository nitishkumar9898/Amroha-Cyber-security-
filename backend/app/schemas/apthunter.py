from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class ThreatActorBase(BaseModel):
    actor_name: str
    aliases: Optional[List[str]] = []
    origin_country: Optional[str] = None
    target_sectors: Optional[List[str]] = []

class ThreatActorCreate(ThreatActorBase):
    pass

class ThreatActorRead(ThreatActorBase):
    id: int
    first_seen: Optional[datetime] = None

class APTCampaignBase(BaseModel):
    campaign_name: str
    threat_actor_id: Optional[int] = None
    attribution_confidence: Optional[float] = 0.0

class APTCampaignCreate(APTCampaignBase):
    additional_metadata: Optional[Dict[str, Any]] = None

class APTCampaignRead(APTCampaignBase):
    id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    additional_metadata: Optional[Dict[str, Any]] = None

class TTPMappingRead(BaseModel):
    id: int
    campaign_id: int
    technique_id: str
    technique_name: str
    graph_node_id: Optional[str] = None
    detection_score: float

class PersistenceArtifactBase(BaseModel):
    artifact_type: str = Field(..., description="e.g., registry, wmi, scheduled_task")
    artifact_value: str

class PersistenceArtifactCreate(PersistenceArtifactBase):
    campaign_id: Optional[int] = None

class PersistenceArtifactRead(PersistenceArtifactBase):
    id: int
    campaign_id: Optional[int] = None
    stealth_score: float
    detected_at: datetime

class AnalyzePersistenceRequest(BaseModel):
    scan_data: List[Dict[str, Any]] = Field(..., description="Raw system scan data objects")

class CampaignReconstructionRequest(BaseModel):
    artifact_ids: List[int] = Field(..., description="List of persistence artifact IDs to analyze")

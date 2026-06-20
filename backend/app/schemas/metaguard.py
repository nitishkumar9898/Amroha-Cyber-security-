from pydantic import BaseModel, ConfigDict
from typing import Optional

class AssetTrackingRequest(BaseModel):
    asset_id: str
    wallet_hops: int
    time_window_seconds: float

class AssetTrackingResult(BaseModel):
    asset_id: str
    is_laundering_risk: bool
    action_taken: str

class AvatarBehaviorRequest(BaseModel):
    avatar_id: str
    kinematic_jitter: float
    manipulative_language: bool

class AvatarBehaviorResult(BaseModel):
    avatar_id: str
    social_engineering_risk: bool
    risk_assessment: str

class CrimeCorrelationRequest(BaseModel):
    virtual_incident_id: str
    virtual_ip_log: str

class CrimeCorrelationResult(BaseModel):
    virtual_incident_id: str
    hardware_id_hash: str
    physical_location_estimate: str

class EvidenceVisualizationRequest(BaseModel):
    scene_id: str
    raw_spatial_data: str

class EvidenceVisualizationResult(BaseModel):
    scene_id: str
    manifest_url: str
    is_training_ready: bool

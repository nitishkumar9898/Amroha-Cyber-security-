from pydantic import BaseModel, ConfigDict
from typing import Optional

class AudioIngestRequest(BaseModel):
    sample_id: str
    filename: str
    duration_seconds: float
    format: str

class AudioIngestResult(BaseModel):
    sample_id: str
    status: str

class DeepfakeDetectionRequest(BaseModel):
    sample_id: str
    claimed_identity: str

class DeepfakeDetectionResult(BaseModel):
    sample_id: str
    claimed_identity: str
    match_confidence: float
    liveness_score: float
    is_spoofed: bool
    high_freq_artifacts: float
    ai_probability: float
    is_deepfake: bool

class EnvironmentReconstructionRequest(BaseModel):
    sample_id: str

class EnvironmentReconstructionResult(BaseModel):
    sample_id: str
    rt60_decay: float
    background_noise_profile: str
    estimated_environment: str

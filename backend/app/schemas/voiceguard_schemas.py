from pydantic import BaseModel
from datetime import datetime

class AudioAnalysisRequest(BaseModel):
    audio_file_hash: str
    speaker_id: str

class AudioAnalysisRead(AudioAnalysisRequest):
    id: int
    synthetic_probability: float
    spectral_anomalies: str
    analyzed_at: datetime

    class Config:
        from_attributes = True

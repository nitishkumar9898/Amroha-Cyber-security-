from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

class FirmwareUploadBase(BaseModel):
    filename: str
    sha256: str
    size_bytes: int

class FirmwareAnalysisOut(FirmwareUploadBase):
    id: int
    entropy: float
    analysis_results: Dict[str, Any]
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

class TraceAnalysisRequest(BaseModel):
    device_id: str
    trace_type: str
    data_points: List[float]

class TraceAnalysisOut(BaseModel):
    trace_type: str
    anomaly_score: float
    attack_detected: bool
    details: str

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FirmwareCreate(BaseModel):
    device_model: str
    version: str
    file_hash: str
    is_signed: bool = False

class FirmwareRead(FirmwareCreate):
    id: int
    risk_score: float
    uploaded_at: datetime
    status: str

    class Config:
        from_attributes = True

class FirmwareAnalysisResult(BaseModel):
    firmware_id: int
    risk_score: float
    findings: list
    status: str

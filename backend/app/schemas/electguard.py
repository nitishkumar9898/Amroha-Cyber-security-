from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class VoteLogCreate(BaseModel):
    election_id: str = Field(..., example="2024_general")
    voter_id_hashed: str = Field(..., description="Hashed voter identifier")
    raw_log: Dict[str, Any] = Field(..., description="Raw voting system log data")

class VoteLogRead(BaseModel):
    id: int
    election_id: str
    voter_id_hashed: str
    timestamp: str
    raw_log: Dict[str, Any]

    class Config:
        from_attributes = True

class MisinformationAlertRead(BaseModel):
    id: int
    source: str
    detected_at: str
    confidence: float
    severity: float
    description: str
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

class VoterDataAnomalyRead(BaseModel):
    id: int
    voter_id_hashed: str
    election_id: str
    detected_at: str
    anomaly_type: str
    details: Dict[str, Any]

    class Config:
        from_attributes = True

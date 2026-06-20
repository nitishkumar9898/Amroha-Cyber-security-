from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class EvidenceCreate(BaseModel):
    evidence_type: str = Field(..., example="log")
    raw_data: bytes = Field(..., description="Raw evidence data (will be encrypted)")
    additional_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class EvidenceRead(BaseModel):
    id: int
    evidence_type: str
    created_at: str
    expires_at: Optional[str]
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

class RetentionPolicyRead(BaseModel):
    evidence_type: str
    retention_days: int

    class Config:
        from_attributes = True

class MigrationLogRead(BaseModel):
    id: int
    record_id: int
    from_format: str
    to_format: str
    migrated_at: str

    class Config:
        from_attributes = True

"""
Pydantic Schemas Package Entrypoint
Exposes core schemas and allows submodules (supplychain, insider_shield, osint) to be imported.
"""

from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    agency: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    agency: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ScenarioCreate(BaseModel):
    scenario_id: str
    name: str
    threat_actor: str
    target_sector: str

class ScenarioResponse(BaseModel):
    id: int
    scenario_id: str
    name: str
    threat_actor: str
    target_sector: str
    status: str
    start_time: datetime
    completed_phases: str

    class Config:
        from_attributes = True

class CustodyRecordResponse(BaseModel):
    id: int
    timestamp: datetime
    item_name: str
    file_path: str
    sha256_hash: str
    action: str
    officer_name: str
    agency_id: str
    description: str
    entry_signature: str

    class Config:
        from_attributes = True

class BSAExchangeRequest(BaseModel):
    filepath: str
    examiner_designation: str

class BSAExchangeResponse(BaseModel):
    legal_provision: str
    certification_date: str
    evidence_name: str
    sha256_checksum: str
    examiner_details: dict
    declaration: str

# Training session schemas
class TrainingSessionCreate(BaseModel):
    user_id: str
    scenario_name: str
    config: Optional[dict] = None

class TrainingSessionResponse(BaseModel):
    id: int
    user_id: str
    scenario_name: str
    start_time: datetime
    status: str
    config: Optional[dict] = None

    class Config:
        from_attributes = True

class TrainingResultCreate(BaseModel):
    session_id: int
    metric_name: str
    metric_value: float
    details: Optional[dict] = None

class TrainingResultResponse(BaseModel):
    id: int
    session_id: int
    timestamp: datetime
    metric_name: str
    metric_value: float
    details: Optional[dict] = None

    class Config:
        from_attributes = True

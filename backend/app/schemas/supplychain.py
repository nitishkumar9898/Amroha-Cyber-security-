from pydantic import ConfigDict
# backend/app/schemas/supplychain.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class SupplyChainEntitySchema(BaseModel):
    id: Optional[int] = None
    name: str
    type: str
    version: Optional[str] = None
    provenance_hash: str
    additional_metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class RiskEventSchema(BaseModel):
    id: Optional[int] = None
    entity_id: int
    severity: float
    description: str
    timestamp: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class AnomalySchema(BaseModel):
    id: Optional[int] = None
    entity_id: int
    score: float
    details: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class SimulationScenarioSchema(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    generated_plan: Dict[str, Any]
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Request bodies
class SBOMIngestRequest(BaseModel):
    sbom: Dict[str, Any] = Field(..., description="Raw SBOM JSON (SPDX, CycloneDX, etc.)")

class AnomalyDetectRequest(BaseModel):
    entity_id: int
    data: Dict[str, Any] = Field(..., description="Telemetry or metadata for the entity")

class SimulationRequest(BaseModel):
    name: str
    parameters: Optional[Dict[str, Any]] = None

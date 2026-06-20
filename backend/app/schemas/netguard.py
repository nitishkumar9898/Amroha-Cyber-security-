from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class NodeBase(BaseModel):
    node_name: str
    node_type: str # TELECOM, SCADA, STANDARD
    ip_address: str

class NodeRegister(NodeBase):
    pass

class NodeResponse(NodeBase):
    id: int
    is_active: bool
    registered_at: datetime

    class Config:
        from_attributes = True

class TrafficIngestRequest(BaseModel):
    node_id: int
    protocol: str
    bytes_transferred: int
    payload_signature: str

class AnalysisResult(BaseModel):
    node_id: int
    is_anomalous: bool
    threat_type: Optional[str]
    confidence: float

class SimulationRequest(BaseModel):
    node_id: int
    simulation_type: str # DDOS, APT

class SimulationReport(BaseModel):
    node_id: int
    simulation_type: str
    predicted_impact_hours: float
    recommended_action: str

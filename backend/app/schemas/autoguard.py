from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class VehicleLogCreate(BaseModel):
    vehicle_id: str = Field(..., example="VIN1234567890")
    raw_data: str = Field(..., description="JSON string or hex representation of CAN frames")

class VehicleLogRead(BaseModel):
    id: int
    vehicle_id: str
    timestamp: str
    raw_data: str

    class Config:
        from_attributes = True

class MalwareAlertRead(BaseModel):
    id: int
    vehicle_id: str
    detected_at: str
    signature_id: Optional[str]
    severity: float
    description: str

    class Config:
        from_attributes = True

class SwarmScenarioCreate(BaseModel):
    scenario_name: str
    parameters: Dict[str, Any]

class SwarmScenarioRead(BaseModel):
    id: int
    scenario_name: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    created_at: str

    class Config:
        from_attributes = True

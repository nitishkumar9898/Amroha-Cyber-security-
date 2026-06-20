from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# --- Wildlife Listing ---
class ListingCreate(BaseModel):
    source_url: Optional[str] = None
    title: str = Field(..., example="Ivory tusks – discreet shipping")
    description: str = Field(..., description="Full listing text from dark-web source")
    additional_metadata: Optional[Dict[str, Any]] = None

class ListingRead(BaseModel):
    id: int
    source_url: Optional[str]
    title: str
    description: str
    detected_at: str
    confidence: float
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# --- GPS Forensics ---
class GPSPayloadCreate(BaseModel):
    device_id: str = Field(..., example="TRACKER-9281")
    raw_payload: Dict[str, Any] = Field(..., description="JSON object containing GPS waypoints with lat, lon, timestamp, speed")

class GPSPayloadRead(BaseModel):
    id: int
    device_id: str
    uploaded_at: str
    raw_payload: Dict[str, Any]
    spoof_detected: bool
    analysis: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# --- Environmental Data ---
class EnvRecordCreate(BaseModel):
    sensor_id: str = Field(..., example="AIR-Q-007")
    raw_data: Dict[str, Any] = Field(..., description="Sensor readings as JSON")
    additional_metadata: Optional[Dict[str, Any]] = None

class EnvRecordRead(BaseModel):
    id: int
    sensor_id: str
    timestamp: str
    raw_data: Dict[str, Any]
    tamper_score: float
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# --- Collaboration ---
class CollabRequestCreate(BaseModel):
    agency_name: str = Field(..., example="INTERPOL Wildlife Unit")
    case_id: str = Field(..., example="CASE-2026-4421")
    request_payload: Dict[str, Any] = Field(..., description="Details of the collaboration request")

class CollabRequestRead(BaseModel):
    id: int
    agency_name: str
    case_id: str
    request_payload: Dict[str, Any]
    status: str
    created_at: str

    class Config:
        from_attributes = True

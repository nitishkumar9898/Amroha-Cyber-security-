from pydantic import BaseModel
from datetime import datetime

class CityEventCreate(BaseModel):
    city_zone: str
    iot_device_type: str
    device_id: str

class CityEventRead(CityEventCreate):
    id: int
    anomaly_score: float
    event_status: str
    detected_at: datetime

    class Config:
        from_attributes = True

class IsolationResponse(BaseModel):
    event_id: int
    status: str
    action_taken: str

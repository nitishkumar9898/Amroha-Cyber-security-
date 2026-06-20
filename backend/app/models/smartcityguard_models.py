from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base

class SmartCityEvent(Base):
    __tablename__ = "smartcityguard_events"
    id = Column(Integer, primary_key=True, index=True)
    city_zone = Column(String)
    iot_device_type = Column(String)
    device_id = Column(String)
    anomaly_score = Column(Float, default=0.0)
    event_status = Column(String, default="Active")
    detected_at = Column(DateTime, default=datetime.utcnow)

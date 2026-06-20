from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class NetworkNode(Base):
    __tablename__ = "netguard_nodes"

    id = Column(Integer, primary_key=True, index=True)
    node_name = Column(String, index=True)
    node_type = Column(String) # TELECOM, SCADA, STANDARD
    ip_address = Column(String)
    is_active = Column(Boolean, default=True)
    registered_at = Column(DateTime, default=datetime.datetime.utcnow)

class TrafficLog(Base):
    __tablename__ = "netguard_traffic"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer)
    protocol = Column(String)
    bytes_transferred = Column(Integer)
    is_anomalous = Column(Boolean, default=False)
    threat_type = Column(String, nullable=True) # e.g., DDOS, SLICE_VIOLATION, APT

class ThreatForecast(Base):
    __tablename__ = "netguard_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer)
    predicted_attack_type = Column(String)
    confidence_score = Column(Float)
    time_to_impact_hours = Column(Float)

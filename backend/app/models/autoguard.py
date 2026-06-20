from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class VehicleLog(Base):
    __tablename__ = "autoguard_vehicle_logs"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    raw_data = Column(String)  # JSON or hex string of CAN frames

class MalwareAlert(Base):
    __tablename__ = "autoguard_malware_alerts"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, index=True)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    signature_id = Column(String, nullable=True)
    severity = Column(Float)
    description = Column(String)

class SwarmAttackScenario(Base):
    __tablename__ = "autoguard_swarm_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    scenario_name = Column(String)
    parameters = Column(String)  # JSON encoded parameters
    result = Column(String)      # JSON summary of outcome
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

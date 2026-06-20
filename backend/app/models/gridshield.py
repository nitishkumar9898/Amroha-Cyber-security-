from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class ScadaAnomaly(Base):
    __tablename__ = "gridshield_scada"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    protocol = Column(String) # e.g., "Modbus", "DNP3"
    is_anomalous = Column(Boolean)
    flag_reason = Column(String)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)

class CyberPhysicalSimulation(Base):
    __tablename__ = "gridshield_kinetic"

    id = Column(Integer, primary_key=True, index=True)
    target_component = Column(String, index=True) # e.g., "Turbine-A"
    injected_rpm = Column(Float)
    kinetic_damage_probability = Column(Float)
    simulated_at = Column(DateTime, default=datetime.datetime.utcnow)

class ResiliencePlan(Base):
    __tablename__ = "gridshield_resilience"

    id = Column(Integer, primary_key=True, index=True)
    grid_sector = Column(String, index=True)
    load_shedding_percentage = Column(Float)
    islanding_required = Column(Boolean)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)

class ThreatForecast(Base):
    __tablename__ = "gridshield_forecast"

    id = Column(Integer, primary_key=True, index=True)
    region = Column(String, index=True)
    five_year_risk_score = Column(Float)
    primary_threat_vector = Column(String)
    forecasted_at = Column(DateTime, default=datetime.datetime.utcnow)

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
import datetime
from ..database import Base


class AISSignalRecord(Base):
    """AIS signal analysis and spoofing detection record."""
    __tablename__ = "maritimeguard_ais_signals"

    id = Column(Integer, primary_key=True, index=True)
    mmsi = Column(String, index=True)                    # Maritime Mobile Service Identity
    vessel_name = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    latitude = Column(Float)
    longitude = Column(Float)
    speed_knots = Column(Float, nullable=True)
    course = Column(Float, nullable=True)
    spoof_detected = Column(Boolean, default=False)
    spoof_confidence = Column(Float, default=0.0)        # 0–1
    analysis = Column(JSON, nullable=True)               # anomaly details
    additional_metadata = Column("metadata", JSON, nullable=True)


class ShipboardForensic(Base):
    """Shipboard OT/IT system forensic investigation record."""
    __tablename__ = "maritimeguard_shipboard_forensics"

    id = Column(Integer, primary_key=True, index=True)
    vessel_id = Column(String, index=True)
    system_type = Column(String, index=True)             # ECDIS, engine_control, ballast, cargo, nav_radar, GMDSS
    incident_type = Column(String, nullable=True)        # malware, unauthorised_access, config_tamper, firmware_mod
    severity = Column(Float, default=0.0)
    findings = Column(JSON, nullable=True)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="open")              # open, investigating, contained, closed
    additional_metadata = Column("metadata", JSON, nullable=True)


class PortAttackSimulation(Base):
    """Supply-chain attack simulation on port infrastructure."""
    __tablename__ = "maritimeguard_port_simulations"

    id = Column(Integer, primary_key=True, index=True)
    port_name = Column(String, index=True)
    scenario_name = Column(String)
    attack_vector = Column(String)                       # crane_control, TOS_compromise, gate_system, fuel_bunker
    parameters = Column(JSON)
    result = Column(JSON, nullable=True)
    resilience_score = Column(Float, default=0.0)        # 0–1 how well defences held
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class MaritimeComplianceCheck(Base):
    """International maritime law and cybersecurity compliance assessment."""
    __tablename__ = "maritimeguard_compliance"

    id = Column(Integer, primary_key=True, index=True)
    vessel_id = Column(String, index=True)
    framework = Column(String, index=True)               # IMO_MSC428, ISPS_Code, BIMCO, NIST_CSF, IEC_62443
    overall_score = Column(Float, default=0.0)           # 0–1
    findings = Column(JSON, nullable=True)               # list of compliance gap objects
    recommendations = Column(JSON, nullable=True)
    assessed_at = Column(DateTime, default=datetime.datetime.utcnow)
    additional_metadata = Column("metadata", JSON, nullable=True)

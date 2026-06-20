from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
import datetime
from ..database import Base


class ADSBSignalRecord(Base):
    """ADS-B / radar signal forensic record."""
    __tablename__ = "aviguard_adsb_signals"

    id = Column(Integer, primary_key=True, index=True)
    icao_hex = Column(String, index=True)                # 24-bit ICAO address
    callsign = Column(String, nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    latitude = Column(Float)
    longitude = Column(Float)
    altitude_ft = Column(Float, nullable=True)
    speed_knots = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)
    squawk = Column(String, nullable=True)               # transponder code
    spoof_detected = Column(Boolean, default=False)
    spoof_confidence = Column(Float, default=0.0)
    analysis = Column(JSON, nullable=True)
    additional_metadata = Column("metadata", JSON, nullable=True)


class AvionicsForensic(Base):
    """Aircraft avionics malware / incident analysis."""
    __tablename__ = "aviguard_avionics_forensics"

    id = Column(Integer, primary_key=True, index=True)
    aircraft_id = Column(String, index=True)             # tail number or registration
    system_type = Column(String, index=True)             # FMS, EFB, IFE, ACARS, SATCOM, TCAS
    incident_type = Column(String, nullable=True)        # malware, firmware_tamper, config_change, unauthorised_access
    severity = Column(Float, default=0.0)
    findings = Column(JSON, nullable=True)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="open")
    additional_metadata = Column("metadata", JSON, nullable=True)


class AirportNetworkScan(Base):
    """Airport network and passenger data protection scan."""
    __tablename__ = "aviguard_airport_scans"

    id = Column(Integer, primary_key=True, index=True)
    airport_code = Column(String, index=True)            # IATA code
    scan_type = Column(String, index=True)               # network_segmentation, pax_data_audit, wifi_security, cctv_network
    risk_score = Column(Float, default=0.0)
    findings = Column(JSON, nullable=True)
    scanned_at = Column(DateTime, default=datetime.datetime.utcnow)
    additional_metadata = Column("metadata", JSON, nullable=True)


class DroneInterferenceSimulation(Base):
    """Drone interference and cyber-physical attack simulation."""
    __tablename__ = "aviguard_drone_simulations"

    id = Column(Integer, primary_key=True, index=True)
    scenario_name = Column(String)
    attack_vector = Column(String)                       # gps_jam, rf_hijack, swarm_incursion, runway_intrusion
    parameters = Column(JSON)
    result = Column(JSON, nullable=True)
    resilience_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AviationComplianceCheck(Base):
    """DGCA / ICAO regulatory compliance assessment."""
    __tablename__ = "aviguard_compliance"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(String, index=True)               # airline or airport code
    entity_type = Column(String, default="airline")       # airline, airport, MRO
    framework = Column(String, index=True)               # ICAO_Annex17, DGCA_CAR, EASA_Part_IS
    overall_score = Column(Float, default=0.0)
    findings = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    assessed_at = Column(DateTime, default=datetime.datetime.utcnow)
    additional_metadata = Column("metadata", JSON, nullable=True)

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
import datetime
from ..database import Base


class IoMTDevice(Base):
    """Internet of Medical Things device security record."""
    __tablename__ = "healthguard_iomt_devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True)
    device_type = Column(String, index=True)            # infusion_pump, pacemaker, ventilator, imaging, etc.
    manufacturer = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    risk_score = Column(Float, default=0.0)             # 0–1 overall security posture
    vulnerabilities = Column(JSON, nullable=True)       # list of CVE-like objects
    last_scanned = Column(DateTime, default=datetime.datetime.utcnow)
    network_segment = Column(String, nullable=True)
    additional_metadata = Column("metadata", JSON, nullable=True)


class HealthDataBreach(Base):
    """Health data breach investigation record."""
    __tablename__ = "healthguard_data_breaches"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, unique=True, index=True)
    affected_records = Column(Integer, default=0)
    data_types_exposed = Column(JSON, nullable=True)    # ["PHI", "PII", "genomic", "billing"]
    attack_vector = Column(String, nullable=True)       # ransomware, insider, misconfiguration, phishing
    source_ip = Column(String, nullable=True)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    hipaa_violation = Column(Boolean, default=False)
    severity = Column(Float, default=0.0)
    status = Column(String, default="open")             # open, investigating, contained, closed
    additional_metadata = Column("metadata", JSON, nullable=True)


class FakeMedicalContent(Base):
    """Detected fake medical information or deepfake doctor content."""
    __tablename__ = "healthguard_fake_medical"

    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(String, index=True)           # article, video, social_post, deepfake_doctor
    source_url_hash = Column(String, nullable=True)     # hashed URL for privacy
    platform = Column(String, nullable=True)
    confidence = Column(Float, default=0.0)             # 0–1 fake detection confidence
    claim_summary = Column(String, nullable=True)
    fact_check_result = Column(String, nullable=True)   # confirmed_fake, likely_fake, inconclusive, legitimate
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    additional_metadata = Column("metadata", JSON, nullable=True)


class PandemicMisinformation(Base):
    """Pandemic-specific misinformation tracking record."""
    __tablename__ = "healthguard_pandemic_misinfo"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)                  # vaccine, treatment, origin, lockdown, etc.
    narrative = Column(String)                          # summary of the misinformation narrative
    spread_velocity = Column(Float, default=0.0)        # posts/hour rate
    platforms_detected = Column(JSON, nullable=True)    # list of platform names
    severity = Column(Float, default=0.0)
    first_seen = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="active")           # active, declining, debunked, archived
    additional_metadata = Column("metadata", JSON, nullable=True)

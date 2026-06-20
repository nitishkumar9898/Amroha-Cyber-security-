from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import datetime

from ..database import Base

class CloudIncident(Base):
    __tablename__ = "cloud_incidents"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, index=True) # AWS, AZURE, GCP, MULTI
    reported_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="INVESTIGATING")
    severity = Column(String)

class CloudLogEvidence(Base):
    __tablename__ = "cloud_log_evidences"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("cloud_incidents.id"))
    log_source = Column(String) # e.g., CloudTrail, AzureMonitor
    raw_log = Column(JSON)
    anomaly_score = Column(Float)
    is_anomalous = Column(Boolean, default=False)
    findings = Column(String)

class ContainerForensicRecord(Base):
    __tablename__ = "container_forensic_records"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("cloud_incidents.id"))
    image_hash = Column(String, index=True)
    namespace = Column(String)
    vulnerabilities = Column(JSON)
    escape_detected = Column(Boolean, default=False)

class ServerlessTrace(Base):
    __tablename__ = "serverless_traces"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("cloud_incidents.id"))
    function_name = Column(String)
    execution_path = Column(JSON)
    duration_ms = Column(Float)
    contains_malicious_payload = Column(Boolean, default=False)

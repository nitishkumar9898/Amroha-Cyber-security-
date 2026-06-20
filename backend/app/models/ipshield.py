from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
import datetime
from ..database import Base


class ExfiltrationEvent(Base):
    """Detected or suspected data exfiltration event."""
    __tablename__ = "ipshield_exfiltration_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)            # usb_copy, cloud_upload, email_attachment, print, screen_capture
    actor_id = Column(String, index=True)               # employee ID or external actor identifier
    actor_type = Column(String, default="insider")      # insider, external, unknown
    risk_score = Column(Float, default=0.0)             # 0–1
    data_volume_mb = Column(Float, nullable=True)
    destination = Column(String, nullable=True)          # URL, device serial, email address
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="open")             # open, investigating, confirmed, false_positive, closed
    additional_metadata = Column("metadata", JSON, nullable=True)


class ActorCorrelation(Base):
    """Link between insider and external actors identified through behavioural or network analysis."""
    __tablename__ = "ipshield_actor_correlations"

    id = Column(Integer, primary_key=True, index=True)
    insider_id = Column(String, index=True)
    external_id = Column(String, index=True)
    correlation_score = Column(Float, default=0.0)      # 0–1 confidence
    evidence_summary = Column(String, nullable=True)
    indicators = Column(JSON, nullable=True)            # list of indicator objects
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    case_id = Column(String, nullable=True, index=True)


class TradeSecretSimulation(Base):
    """Simulated attack scenario testing trade-secret protections."""
    __tablename__ = "ipshield_trade_secret_simulations"

    id = Column(Integer, primary_key=True, index=True)
    scenario_name = Column(String)
    parameters = Column(JSON)                           # simulation config
    result = Column(JSON, nullable=True)                # outcome summary
    protection_score = Column(Float, default=0.0)       # 0–1 how well defences held
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class IPShieldAlert(Base):
    """Unified alert aggregating exfiltration events and correlations."""
    __tablename__ = "ipshield_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String, index=True)             # exfiltration, correlation, simulation_failure
    severity = Column(Float, default=0.0)
    description = Column(String)
    related_event_ids = Column(JSON, nullable=True)     # list of ExfiltrationEvent IDs
    related_correlation_ids = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="new")              # new, investigating, escalated, resolved
    additional_metadata = Column("metadata", JSON, nullable=True)

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
import datetime
from ..database import Base


class CSAMHashReport(Base):
    """Privacy-preserving CSAM detection record.
    Stores ONLY perceptual hashes — never raw media content.
    """
    __tablename__ = "protectforge_csam_hash_reports"

    id = Column(Integer, primary_key=True, index=True)
    hash_value = Column(String, index=True)          # perceptual hash (e.g., PhotoDNA-style)
    hash_algorithm = Column(String, default="phash")  # phash, md5, sha256, photodna
    match_confidence = Column(Float, default=0.0)     # 0–1 confidence against known DB
    source_platform = Column(String, nullable=True)
    reported_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="pending")        # pending, confirmed, false_positive, escalated
    case_id = Column(String, nullable=True, index=True)
    additional_metadata = Column("metadata", JSON, nullable=True)


class GroomingAnalysis(Base):
    """Text-based grooming and predatory behaviour analysis record."""
    __tablename__ = "protectforge_grooming_analyses"

    id = Column(Integer, primary_key=True, index=True)
    conversation_hash = Column(String, index=True)   # hash of the conversation (never raw text in prod)
    platform = Column(String, nullable=True)
    risk_score = Column(Float, default=0.0)           # 0–1 overall grooming risk
    stage_detected = Column(String, nullable=True)    # e.g., trust_building, isolation, desensitisation
    indicators = Column(JSON, nullable=True)          # list of detected indicator objects
    analyzed_at = Column(DateTime, default=datetime.datetime.utcnow)
    case_id = Column(String, nullable=True, index=True)


class DarkWebAlert(Base):
    """Alert from dark-web or social-media monitoring."""
    __tablename__ = "protectforge_darkweb_alerts"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True)              # tor_marketplace, social_media, forum
    url_hash = Column(String, nullable=True)         # hashed URL for privacy
    description = Column(String)
    severity = Column(Float, default=0.0)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="new")           # new, investigating, escalated, closed
    additional_metadata = Column("metadata", JSON, nullable=True)


class ComplianceAuditLog(Base):
    """Immutable audit trail for every action taken in the module."""
    __tablename__ = "protectforge_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, index=True)              # hash_check, grooming_analysis, alert_review, etc.
    actor = Column(String, index=True)               # user/system performing the action
    target_id = Column(Integer, nullable=True)        # FK to the record acted upon
    target_type = Column(String, nullable=True)       # csam_report, grooming, darkweb_alert
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    justification = Column(String, nullable=True)     # legal basis / reason
    details = Column(JSON, nullable=True)

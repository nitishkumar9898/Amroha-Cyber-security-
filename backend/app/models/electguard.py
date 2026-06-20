from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
import datetime
from ..database import Base

class VoteLog(Base):
    __tablename__ = "electguard_vote_logs"

    id = Column(Integer, primary_key=True, index=True)
    election_id = Column(String, index=True)
    voter_id_hashed = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    raw_log = Column(JSON)  # Store raw voting system log as JSON

class MisinformationAlert(Base):
    __tablename__ = "electguard_misinformation_alerts"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True)  # e.g., Twitter, Reddit URL
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    confidence = Column(Float)
    severity = Column(Float)
    description = Column(String)
    additional_metadata = Column(JSON, nullable=True)

class VoterDataAnomaly(Base):
    __tablename__ = "electguard_voter_anomalies"

    id = Column(Integer, primary_key=True, index=True)
    voter_id_hashed = Column(String, index=True)
    election_id = Column(String, index=True)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    anomaly_type = Column(String)
    details = Column(JSON)

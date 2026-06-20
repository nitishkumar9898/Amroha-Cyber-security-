from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
import datetime
from ..database import Base

class EncryptedMessage(Base):
    __tablename__ = "commforensix_encrypted_message"
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String, index=True)
    message_hash = Column(String, unique=True)
    sender_id = Column(String)
    receiver_id = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    algorithm = Column(String)  # e.g., SignalProtocol, WhatsApp, Telegram
    key_size = Column(Integer)
    is_quantum_safe = Column(Boolean, default=False)

class VoIPCall(Base):
    __tablename__ = "commforensix_voip_call"
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String, index=True)
    call_id = Column(String, unique=True)
    caller_id = Column(String)
    callee_id = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    codec = Column(String)
    packet_count = Column(Integer)
    is_encrypted = Column(Boolean, default=True)

class TrafficPattern(Base):
    __tablename__ = "commforensix_traffic_pattern"
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String, index=True)
    total_bytes = Column(Integer)
    packet_rate = Column(Float)
    avg_packet_size = Column(Float)
    duration_seconds = Column(Float)

class SideChannelFinding(Base):
    __tablename__ = "commforensix_sidechannel_finding"
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String, index=True)
    finding_type = Column(String)  # e.g., timing, power
    severity = Column(String)
    description = Column(String)

class EvidenceRecord(Base):
    __tablename__ = "commforensix_evidence_record"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, index=True)
    scan_id = Column(String, index=True)
    evidence_type = Column(String)  # metadata, payload excerpt
    data_blob = Column(String)  # could be JSON string or link
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

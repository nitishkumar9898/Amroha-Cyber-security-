from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EncryptedMessageBase(BaseModel):
    scan_id: str
    message_hash: str
    sender_id: str
    receiver_id: str
    timestamp: datetime
    algorithm: str
    key_size: int
    is_quantum_safe: bool = False

class EncryptedMessageRead(EncryptedMessageBase):
    id: int

class VoIPCallBase(BaseModel):
    scan_id: str
    call_id: str
    caller_id: str
    callee_id: str
    start_time: datetime
    end_time: datetime
    codec: str
    packet_count: int
    is_encrypted: bool = True

class VoIPCallRead(VoIPCallBase):
    id: int

class TrafficPatternBase(BaseModel):
    scan_id: str
    total_bytes: int
    packet_rate: float
    avg_packet_size: float
    duration_seconds: float

class TrafficPatternRead(TrafficPatternBase):
    id: int

class SideChannelFindingBase(BaseModel):
    scan_id: str
    finding_type: str
    severity: str
    description: str

class SideChannelFindingRead(SideChannelFindingBase):
    id: int

class EvidenceRecordBase(BaseModel):
    case_id: str
    scan_id: str
    evidence_type: str
    data_blob: str
    created_at: Optional[datetime] = None

class EvidenceRecordRead(EvidenceRecordBase):
    id: int

class MessageUpload(BaseModel):
    messages: List[EncryptedMessageBase]

class CallUpload(BaseModel):
    calls: List[VoIPCallBase]

class TrafficPatternResponse(BaseModel):
    patterns: List[TrafficPatternRead]

class SideChannelResult(BaseModel):
    findings: List[SideChannelFindingRead]

class EvidenceExport(BaseModel):
    evidence: List[EvidenceRecordRead]

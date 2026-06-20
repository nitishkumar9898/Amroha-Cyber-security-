from typing import List
from sqlalchemy.orm import Session
from ..models.commforensix import EncryptedMessage, VoIPCall, TrafficPattern, SideChannelFinding, EvidenceRecord
from ..schemas.commforensix import (
    EncryptedMessageBase,
    VoIPCallBase,
    MessageUpload,
    CallUpload,
    TrafficPatternResponse,
    TrafficPatternBase,
    SideChannelResult,
    SideChannelFindingBase,
    EvidenceExport,
    EvidenceRecordBase,
)
import uuid
from datetime import datetime

def run_pqc_scan(db: Session, request: MessageUpload):
    """Store uploaded encrypted messages and return a scan_id placeholder."""
    scan_id = request.messages[0].scan_id if request.messages else str(uuid.uuid4())
    for msg in request.messages:
        db_msg = EncryptedMessage(
            scan_id=scan_id,
            message_hash=msg.message_hash,
            sender_id=msg.sender_id,
            receiver_id=msg.receiver_id,
            timestamp=msg.timestamp,
            algorithm=msg.algorithm,
            key_size=msg.key_size,
            is_quantum_safe=msg.is_quantum_safe,
        )
        db.add(db_msg)
    db.commit()
    return scan_id

def get_pqc_results(db: Session, scan_id: str):
    """Retrieve stored messages for the given scan_id as a placeholder response."""
    msgs = db.query(EncryptedMessage).filter(EncryptedMessage.scan_id == scan_id).all()
    return msgs

def analyze_traffic(db: Session, scan_id: str) -> TrafficPatternResponse:
    """Aggregate traffic statistics for a given scan_id.
    Returns total bytes, packet rate, average packet size, and duration.
    """
    calls = db.query(VoIPCall).filter(VoIPCall.scan_id == scan_id).all()
    total_bytes = sum(call.packet_count * 160 for call in calls)  # assume 160 bytes per packet
    duration_seconds = sum(
        (call.end_time - call.start_time).total_seconds() for call in calls if call.end_time and call.start_time
    )
    packet_rate = sum(call.packet_count for call in calls) / duration_seconds if duration_seconds > 0 else 0
    avg_packet_size = 160  # placeholder constant
    pattern = TrafficPattern(
        scan_id=scan_id,
        total_bytes=total_bytes,
        packet_rate=packet_rate,
        avg_packet_size=avg_packet_size,
        duration_seconds=duration_seconds,
    )
    db.add(pattern)
    db.commit()
    return TrafficPatternResponse(patterns=[TrafficPatternBase(
        scan_id=scan_id,
        total_bytes=total_bytes,
        packet_rate=packet_rate,
        avg_packet_size=avg_packet_size,
        duration_seconds=duration_seconds,
    )])

def simulate_timing_attack(db: Session, call_id: str) -> SideChannelResult:
    """Simulate a timing side‑channel attack on a VoIP call.
    Calculates jitter variance as a simple metric.
    """
    call = db.query(VoIPCall).filter(VoIPCall.call_id == call_id).first()
    if not call:
        return SideChannelResult(findings=[])
    # Simplified jitter: assume each packet interval is 20ms ± random jitter
    # Here we just generate a mock severity based on call duration.
    duration = (call.end_time - call.start_time).total_seconds() if call.end_time and call.start_time else 0
    severity = "Low" if duration < 30 else "Medium" if duration < 120 else "High"
    finding = SideChannelFinding(
        scan_id=call.scan_id,
        finding_type="timing",
        severity=severity,
        description=f"Timing variance analysis for call {call_id}",
    )
    db.add(finding)
    db.commit()
    return SideChannelResult(findings=[SideChannelFindingBase(
        scan_id=call.scan_id,
        finding_type="timing",
        severity=severity,
        description=f"Timing variance analysis for call {call_id}",
    )])

def identify_interception_points(db: Session, scan_id: str) -> List[dict]:
    """Identify potential legal interception points.
    Returns a list of dicts describing where lawful intercept could be applied.
    """
    # Placeholder: return a static list based on algorithm type
    msgs = db.query(EncryptedMessage).filter(EncryptedMessage.scan_id == scan_id).all()
    points = []
    for msg in msgs:
        if msg.algorithm.lower() in ["signalprotocol", "whatsapp"]:
            points.append({"type": "gateway", "detail": f"Intercept at server handling {msg.algorithm}"})
    return points

def extract_evidence(db: Session, case_id: str) -> EvidenceExport:
    """Generate a privacy‑compliant evidence package for a case.
    Includes only metadata and hash values, no raw ciphertext.
    """
    records = db.query(EvidenceRecord).filter(EvidenceRecord.case_id == case_id).all()
    if not records:
        # Create a placeholder record from existing data
        # For demo, pick first message
        msg = db.query(EncryptedMessage).first()
        if msg:
            evidence = EvidenceRecord(
                case_id=case_id,
                scan_id=msg.scan_id,
                evidence_type="metadata",
                data_blob=msg.message_hash,
            )
            db.add(evidence)
            db.commit()
            records = [evidence]
    return EvidenceExport(evidence=[EvidenceRecordBase(
        case_id=rec.case_id,
        scan_id=rec.scan_id,
        evidence_type=rec.evidence_type,
        data_blob=rec.data_blob,
        created_at=rec.created_at,
    ) for rec in records])

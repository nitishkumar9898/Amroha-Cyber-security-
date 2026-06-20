from sqlalchemy.orm import Session
from ..models.electguard import VoteLog, MisinformationAlert, VoterDataAnomaly
from ..schemas.electguard import VoteLogCreate, VoterDataAnomalyRead
from ..modules.electguard_engine import parse_vote_log, compute_integrity_hashes, detect_misinformation, analyze_voter_anomaly
import json

def store_vote_log(db: Session, payload: VoteLogCreate) -> VoteLog:
    # Parse and normalize the incoming log
    parsed = parse_vote_log(payload.raw_log)
    vote_log = VoteLog(
        election_id=payload.election_id,
        voter_id_hashed=payload.voter_id_hashed,
        raw_log=parsed,
    )
    db.add(vote_log)
    db.commit()
    db.refresh(vote_log)
    return vote_log

def run_integrity_check(db: Session, election_id: str) -> dict:
    # Retrieve all logs for this election and compute a simple integrity hash
    logs = db.query(VoteLog).filter(VoteLog.election_id == election_id).all()
    if not logs:
        return {"status": "no_logs", "hash": None}
    raw_logs = [log.raw_log for log in logs]
    integrity_hash = compute_integrity_hashes(raw_logs)
    return {"status": "checked", "hash": integrity_hash}

def detect_misinformation_alert(db: Session, source_payload: dict) -> MisinformationAlert:
    result = detect_misinformation(source_payload)
    alert = MisinformationAlert(
        source=source_payload.get("source", "unknown"),
        confidence=result["confidence"],
        severity=result["severity"],
        description=result["description"],
        additional_metadata=result.get("metadata"),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

def analyze_voter_anomaly(db: Session, voter_id_hashed: str, election_id: str) -> VoterDataAnomaly:
    # Gather the last 24h logs for the voter
    logs = (
        db.query(VoteLog)
        .filter(VoteLog.voter_id_hashed == voter_id_hashed, VoteLog.election_id == election_id)
        .order_by(VoteLog.timestamp.desc())
        .limit(100)
        .all()
    )
    raw_logs = [log.raw_log for log in logs]
    analysis = analyze_voter_anomaly(raw_logs)
    anomaly = VoterDataAnomaly(
        voter_id_hashed=voter_id_hashed,
        election_id=election_id,
        anomaly_type=analysis["anomaly_type"],
        details=analysis["details"],
    )
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)
    return anomaly

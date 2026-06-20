from sqlalchemy.orm import Session
from ..models.maritimeguard import AISSignalRecord, ShipboardForensic, PortAttackSimulation, MaritimeComplianceCheck
from ..schemas.maritimeguard import (
    AISSignalCreate, AISBatchCreate,
    ShipboardForensicCreate, PortSimulationCreate, ComplianceCheckCreate,
)
from ..modules.maritimeguard_engine import (
    analyze_ais_signal,
    assess_shipboard_severity,
    simulate_port_attack,
    assess_compliance,
)
from typing import List, Optional


# ── AIS Signals ──────────────────────────────────────────────────────

def store_ais_signal(db: Session, payload: AISSignalCreate,
                     previous: Optional[dict] = None) -> AISSignalRecord:
    current = {
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "speed_knots": payload.speed_knots,
        "course": payload.course,
        "timestamp": None,  # will be set by DB default
    }
    analysis = analyze_ais_signal(current, previous)
    record = AISSignalRecord(
        mmsi=payload.mmsi,
        vessel_name=payload.vessel_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        speed_knots=payload.speed_knots,
        course=payload.course,
        spoof_detected=analysis["spoof_detected"],
        spoof_confidence=analysis["spoof_confidence"],
        analysis=analysis,
        additional_metadata=payload.additional_metadata,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def store_ais_batch(db: Session, batch: AISBatchCreate) -> List[AISSignalRecord]:
    """Process a batch of AIS signals, comparing each to its predecessor."""
    results = []
    previous = None
    for sig in batch.signals:
        current_dict = {
            "latitude": sig.latitude,
            "longitude": sig.longitude,
            "speed_knots": sig.speed_knots,
            "course": sig.course,
            "timestamp": None,
        }
        rec = store_ais_signal(db, sig, previous)
        results.append(rec)
        previous = {
            "latitude": sig.latitude,
            "longitude": sig.longitude,
            "speed_knots": sig.speed_knots,
            "course": sig.course,
            "timestamp": rec.timestamp,
        }
    return results

def get_ais_signal(db: Session, signal_id: int) -> AISSignalRecord:
    rec = db.query(AISSignalRecord).filter(AISSignalRecord.id == signal_id).first()
    if not rec:
        raise ValueError("AISSignalRecord not found")
    return rec

def list_ais_signals(db: Session, mmsi: str = None, spoofed_only: bool = False) -> List[AISSignalRecord]:
    q = db.query(AISSignalRecord)
    if mmsi:
        q = q.filter(AISSignalRecord.mmsi == mmsi)
    if spoofed_only:
        q = q.filter(AISSignalRecord.spoof_detected == True)
    return q.order_by(AISSignalRecord.timestamp.desc()).limit(200).all()


# ── Shipboard Forensics ─────────────────────────────────────────────

def create_shipboard_forensic(db: Session, payload: ShipboardForensicCreate) -> ShipboardForensic:
    severity = assess_shipboard_severity(payload.system_type, payload.incident_type, payload.findings)
    record = ShipboardForensic(
        vessel_id=payload.vessel_id,
        system_type=payload.system_type,
        incident_type=payload.incident_type,
        severity=severity,
        findings=payload.findings,
        additional_metadata=payload.additional_metadata,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_shipboard_forensic(db: Session, forensic_id: int) -> ShipboardForensic:
    rec = db.query(ShipboardForensic).filter(ShipboardForensic.id == forensic_id).first()
    if not rec:
        raise ValueError("ShipboardForensic not found")
    return rec

def list_shipboard_forensics(db: Session, vessel_id: str = None) -> List[ShipboardForensic]:
    q = db.query(ShipboardForensic)
    if vessel_id:
        q = q.filter(ShipboardForensic.vessel_id == vessel_id)
    return q.order_by(ShipboardForensic.severity.desc()).all()


# ── Port Simulations ────────────────────────────────────────────────

def run_port_simulation(db: Session, payload: PortSimulationCreate) -> PortAttackSimulation:
    result = simulate_port_attack(payload.port_name, payload.attack_vector, payload.parameters)
    sim = PortAttackSimulation(
        port_name=payload.port_name,
        scenario_name=payload.scenario_name,
        attack_vector=payload.attack_vector,
        parameters=payload.parameters,
        result=result,
        resilience_score=result["resilience_score"],
    )
    db.add(sim)
    db.commit()
    db.refresh(sim)
    return sim

def get_port_simulation(db: Session, sim_id: int) -> PortAttackSimulation:
    rec = db.query(PortAttackSimulation).filter(PortAttackSimulation.id == sim_id).first()
    if not rec:
        raise ValueError("PortAttackSimulation not found")
    return rec


# ── Maritime Compliance ──────────────────────────────────────────────

def run_compliance_check(db: Session, payload: ComplianceCheckCreate) -> MaritimeComplianceCheck:
    assessment = assess_compliance(payload.framework)
    check = MaritimeComplianceCheck(
        vessel_id=payload.vessel_id,
        framework=payload.framework,
        overall_score=assessment["overall_score"],
        findings=assessment["findings"],
        recommendations=assessment["recommendations"],
        additional_metadata=payload.additional_metadata,
    )
    db.add(check)
    db.commit()
    db.refresh(check)
    return check

def get_compliance_check(db: Session, check_id: int) -> MaritimeComplianceCheck:
    rec = db.query(MaritimeComplianceCheck).filter(MaritimeComplianceCheck.id == check_id).first()
    if not rec:
        raise ValueError("MaritimeComplianceCheck not found")
    return rec

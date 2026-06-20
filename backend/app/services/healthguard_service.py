from sqlalchemy.orm import Session
from ..models.healthguard import IoMTDevice, HealthDataBreach, FakeMedicalContent, PandemicMisinformation
from ..schemas.healthguard import (
    IoMTDeviceCreate, HealthDataBreachCreate,
    FakeMedicalContentCreate, PandemicMisinfoCreate,
)
from ..modules.healthguard_engine import (
    scan_iomt_device,
    assess_breach_severity,
    detect_fake_medical,
    score_pandemic_misinfo,
)
from typing import List


# ── IoMT Devices ─────────────────────────────────────────────────────

def register_and_scan_device(db: Session, payload: IoMTDeviceCreate) -> IoMTDevice:
    scan = scan_iomt_device(payload.device_type, payload.firmware_version, payload.network_segment)
    device = IoMTDevice(
        device_id=payload.device_id,
        device_type=payload.device_type,
        manufacturer=payload.manufacturer,
        firmware_version=payload.firmware_version,
        risk_score=scan["risk_score"],
        vulnerabilities=scan["vulnerabilities"],
        network_segment=payload.network_segment,
        additional_metadata=payload.additional_metadata,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device

def get_device(db: Session, device_db_id: int) -> IoMTDevice:
    rec = db.query(IoMTDevice).filter(IoMTDevice.id == device_db_id).first()
    if not rec:
        raise ValueError("IoMTDevice not found")
    return rec

def list_devices(db: Session, device_type: str = None) -> List[IoMTDevice]:
    q = db.query(IoMTDevice)
    if device_type:
        q = q.filter(IoMTDevice.device_type == device_type)
    return q.order_by(IoMTDevice.risk_score.desc()).all()

def rescan_device(db: Session, device_db_id: int) -> IoMTDevice:
    device = get_device(db, device_db_id)
    scan = scan_iomt_device(device.device_type, device.firmware_version, device.network_segment)
    device.risk_score = scan["risk_score"]
    device.vulnerabilities = scan["vulnerabilities"]
    import datetime
    device.last_scanned = datetime.datetime.utcnow()
    db.commit()
    db.refresh(device)
    return device


# ── Health Data Breaches ─────────────────────────────────────────────

def report_breach(db: Session, payload: HealthDataBreachCreate) -> HealthDataBreach:
    assessment = assess_breach_severity(payload.affected_records, payload.data_types_exposed, payload.attack_vector)
    breach = HealthDataBreach(
        incident_id=payload.incident_id,
        affected_records=payload.affected_records,
        data_types_exposed=payload.data_types_exposed,
        attack_vector=payload.attack_vector,
        source_ip=payload.source_ip,
        hipaa_violation=assessment["hipaa_violation"],
        severity=assessment["severity"],
        additional_metadata=payload.additional_metadata,
    )
    db.add(breach)
    db.commit()
    db.refresh(breach)
    return breach

def get_breach(db: Session, breach_id: int) -> HealthDataBreach:
    rec = db.query(HealthDataBreach).filter(HealthDataBreach.id == breach_id).first()
    if not rec:
        raise ValueError("HealthDataBreach not found")
    return rec

def list_breaches(db: Session, status: str = None) -> List[HealthDataBreach]:
    q = db.query(HealthDataBreach)
    if status:
        q = q.filter(HealthDataBreach.status == status)
    return q.order_by(HealthDataBreach.severity.desc()).all()


# ── Fake Medical Content ─────────────────────────────────────────────

def analyse_fake_medical(db: Session, payload: FakeMedicalContentCreate) -> FakeMedicalContent:
    result = detect_fake_medical(payload.text_content, payload.content_type)
    record = FakeMedicalContent(
        content_type=payload.content_type,
        source_url_hash=payload.source_url_hash,
        platform=payload.platform,
        confidence=result["confidence"],
        claim_summary=payload.claim_summary,
        fact_check_result=result["fact_check_result"],
        metadata={
            **(payload.additional_metadata or {}),
            "medical_keyword_hits": result["medical_keyword_hits"],
            "deepfake_indicator_hits": result["deepfake_indicator_hits"],
        },
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_fake_content(db: Session, content_id: int) -> FakeMedicalContent:
    rec = db.query(FakeMedicalContent).filter(FakeMedicalContent.id == content_id).first()
    if not rec:
        raise ValueError("FakeMedicalContent not found")
    return rec


# ── Pandemic Misinformation ──────────────────────────────────────────

def track_pandemic_misinfo(db: Session, payload: PandemicMisinfoCreate) -> PandemicMisinformation:
    scored = score_pandemic_misinfo(payload.topic, payload.narrative, payload.spread_velocity)
    record = PandemicMisinformation(
        topic=payload.topic,
        narrative=payload.narrative,
        spread_velocity=payload.spread_velocity,
        platforms_detected=payload.platforms_detected,
        severity=scored["severity"],
        metadata={**(payload.additional_metadata or {}), **scored},
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_misinfo(db: Session, misinfo_id: int) -> PandemicMisinformation:
    rec = db.query(PandemicMisinformation).filter(PandemicMisinformation.id == misinfo_id).first()
    if not rec:
        raise ValueError("PandemicMisinformation not found")
    return rec

def list_misinfo(db: Session, topic: str = None, status: str = None) -> List[PandemicMisinformation]:
    q = db.query(PandemicMisinformation)
    if topic:
        q = q.filter(PandemicMisinformation.topic == topic)
    if status:
        q = q.filter(PandemicMisinformation.status == status)
    return q.order_by(PandemicMisinformation.severity.desc()).all()

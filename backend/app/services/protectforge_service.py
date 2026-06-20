from sqlalchemy.orm import Session
from ..models.protectforge import CSAMHashReport, GroomingAnalysis, DarkWebAlert, ComplianceAuditLog
from ..schemas.protectforge import CSAMHashReportCreate, GroomingAnalysisCreate, DarkWebAlertCreate
from ..modules.protectforge_engine import match_hash, analyze_grooming, scan_darkweb_text, validate_legal_basis
from typing import List


# ── Audit helper (every action is logged) ─────────────────────────────

def _audit(db: Session, action: str, actor: str, target_id: int = None,
           target_type: str = None, justification: str = None, details: dict = None):
    log = ComplianceAuditLog(
        action=action,
        actor=actor,
        target_id=target_id,
        target_type=target_type,
        justification=justification,
        details=details,
    )
    db.add(log)
    # Commit happens with the calling transaction


# ── CSAM Hash Reports ────────────────────────────────────────────────

def submit_hash_report(db: Session, payload: CSAMHashReportCreate, actor: str = "system") -> CSAMHashReport:
    confidence = match_hash(payload.hash_value, payload.hash_algorithm)
    status = "confirmed" if confidence >= 0.95 else "pending"
    report = CSAMHashReport(
        hash_value=payload.hash_value,
        hash_algorithm=payload.hash_algorithm,
        match_confidence=confidence,
        source_platform=payload.source_platform,
        status=status,
        case_id=payload.case_id,
        additional_metadata=payload.additional_metadata,
    )
    db.add(report)
    _audit(db, "hash_check", actor, target_type="csam_report",
           justification="Automated hash comparison against known-hash DB",
           details={"confidence": confidence, "status": status})
    db.commit()
    db.refresh(report)
    return report

def get_hash_report(db: Session, report_id: int) -> CSAMHashReport:
    rec = db.query(CSAMHashReport).filter(CSAMHashReport.id == report_id).first()
    if not rec:
        raise ValueError("CSAMHashReport not found")
    return rec

def list_hash_reports(db: Session, case_id: str = None) -> List[CSAMHashReport]:
    q = db.query(CSAMHashReport)
    if case_id:
        q = q.filter(CSAMHashReport.case_id == case_id)
    return q.order_by(CSAMHashReport.reported_at.desc()).all()


# ── Grooming Analysis ─────────────────────────────────────────────────

def run_grooming_analysis(db: Session, payload: GroomingAnalysisCreate, actor: str = "system") -> GroomingAnalysis:
    result = analyze_grooming(payload.text_snippet)
    analysis = GroomingAnalysis(
        conversation_hash=payload.conversation_hash,
        platform=payload.platform,
        risk_score=result["risk_score"],
        stage_detected=result["stage_detected"],
        indicators=result["indicators"],
        case_id=payload.case_id,
    )
    db.add(analysis)
    _audit(db, "grooming_analysis", actor, target_type="grooming",
           justification="Automated grooming-pattern analysis on anonymised text",
           details={"risk_score": result["risk_score"], "stage": result["stage_detected"]})
    db.commit()
    db.refresh(analysis)
    return analysis

def get_grooming_analysis(db: Session, analysis_id: int) -> GroomingAnalysis:
    rec = db.query(GroomingAnalysis).filter(GroomingAnalysis.id == analysis_id).first()
    if not rec:
        raise ValueError("GroomingAnalysis not found")
    return rec


# ── Dark Web Alerts ──────────────────────────────────────────────────

def create_darkweb_alert(db: Session, payload: DarkWebAlertCreate, actor: str = "system") -> DarkWebAlert:
    scan = scan_darkweb_text(payload.description)
    severity = max(payload.severity, scan["severity"])
    alert = DarkWebAlert(
        source=payload.source,
        url_hash=payload.url_hash,
        description=payload.description,
        severity=severity,
        metadata={**(payload.additional_metadata or {}), "matched_keywords": scan["matched_keywords"]},
    )
    db.add(alert)
    _audit(db, "darkweb_scan", actor, target_type="darkweb_alert",
           justification="Automated dark-web keyword scan",
           details={"severity": severity})
    db.commit()
    db.refresh(alert)
    return alert

def get_darkweb_alert(db: Session, alert_id: int) -> DarkWebAlert:
    rec = db.query(DarkWebAlert).filter(DarkWebAlert.id == alert_id).first()
    if not rec:
        raise ValueError("DarkWebAlert not found")
    return rec

def update_alert_status(db: Session, alert_id: int, status: str, actor: str = "system",
                        justification: str = "") -> DarkWebAlert:
    if not validate_legal_basis(justification):
        raise ValueError("A legal justification is required for status changes")
    alert = get_darkweb_alert(db, alert_id)
    alert.status = status
    _audit(db, "alert_status_update", actor, target_id=alert_id,
           target_type="darkweb_alert", justification=justification,
           details={"new_status": status})
    db.commit()
    db.refresh(alert)
    return alert


# ── Audit Log Retrieval ──────────────────────────────────────────────

def get_audit_logs(db: Session, limit: int = 50) -> List[ComplianceAuditLog]:
    return db.query(ComplianceAuditLog).order_by(ComplianceAuditLog.timestamp.desc()).limit(limit).all()

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .. import dependencies
from ..schemas.protectforge import (
    CSAMHashReportCreate, CSAMHashReportRead,
    GroomingAnalysisCreate, GroomingAnalysisRead,
    DarkWebAlertCreate, DarkWebAlertRead,
    AuditLogRead,
)
from ..services.protectforge_service import (
    submit_hash_report, get_hash_report, list_hash_reports,
    run_grooming_analysis, get_grooming_analysis,
    create_darkweb_alert, get_darkweb_alert, update_alert_status,
    get_audit_logs,
)
from typing import List

router = APIRouter()

# ── CSAM Hash Reports ────────────────────────────────────────────────

@router.post("/hash_report", response_model=CSAMHashReportRead)
def submit_hash(payload: CSAMHashReportCreate, db: Session = Depends(dependencies.get_db)):
    """Submit a perceptual hash for comparison against the known-hash database."""
    return submit_hash_report(db, payload)

@router.get("/hash_report/{report_id}", response_model=CSAMHashReportRead)
def read_hash_report(report_id: int, db: Session = Depends(dependencies.get_db)):
    return get_hash_report(db, report_id)

@router.get("/hash_reports", response_model=List[CSAMHashReportRead])
def list_reports(case_id: str = None, db: Session = Depends(dependencies.get_db)):
    return list_hash_reports(db, case_id)

# ── Grooming Analysis ─────────────────────────────────────────────────

@router.post("/grooming", response_model=GroomingAnalysisRead)
def analyze_grooming_endpoint(payload: GroomingAnalysisCreate, db: Session = Depends(dependencies.get_db)):
    """Analyse anonymised conversation text for grooming indicators."""
    return run_grooming_analysis(db, payload)

@router.get("/grooming/{analysis_id}", response_model=GroomingAnalysisRead)
def read_grooming(analysis_id: int, db: Session = Depends(dependencies.get_db)):
    return get_grooming_analysis(db, analysis_id)

# ── Dark Web Alerts ──────────────────────────────────────────────────

@router.post("/darkweb_alert", response_model=DarkWebAlertRead)
def create_alert(payload: DarkWebAlertCreate, db: Session = Depends(dependencies.get_db)):
    """Ingest a dark-web or social-media alert for keyword scanning."""
    return create_darkweb_alert(db, payload)

@router.get("/darkweb_alert/{alert_id}", response_model=DarkWebAlertRead)
def read_alert(alert_id: int, db: Session = Depends(dependencies.get_db)):
    return get_darkweb_alert(db, alert_id)

@router.patch("/darkweb_alert/{alert_id}")
def patch_alert_status(alert_id: int, status: str, justification: str = Query(...),
                       db: Session = Depends(dependencies.get_db)):
    """Update alert status.  A legal justification is REQUIRED."""
    valid = {"new", "investigating", "escalated", "closed"}
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"status must be one of {valid}")
    try:
        return update_alert_status(db, alert_id, status, justification=justification)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ── Compliance Audit Log ─────────────────────────────────────────────

@router.get("/audit_log", response_model=List[AuditLogRead])
def read_audit_log(limit: int = 50, db: Session = Depends(dependencies.get_db)):
    """Retrieve the immutable compliance audit trail."""
    return get_audit_logs(db, limit)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.ransomguard import IncidentCreate, IncidentResponse, TraceRequest, ComplianceReportOut
from ..services.ransomguard_service import RansomGuardService

router = APIRouter()

@router.post("/incidents", response_model=IncidentResponse)
def report_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    """Report a new ransomware incident."""
    try:
        incident = RansomGuardService.report_incident(db, payload)
        return incident
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trace")
def trace_crypto_funds(payload: TraceRequest, db: Session = Depends(get_db)):
    """Initiate AI wallet tracing and payment tracking."""
    try:
        report = RansomGuardService.trace_crypto(db, payload)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance/{incident_id}", response_model=ComplianceReportOut)
def generate_compliance_report(incident_id: int, db: Session = Depends(get_db)):
    """Export a compliance-ready forensic evidence report with hash verification."""
    try:
        report = RansomGuardService.generate_compliance_report(db, incident_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

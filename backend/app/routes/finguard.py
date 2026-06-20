from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.finguard import TransactionAnomalyRequest, TransactionAnomalyResult, PaymentTraceRequest, PaymentTraceResult, LaunderingPatternRequest, LaunderingPatternResult, ComplianceReportRequest, ComplianceReportResult
from ..services.finguard_service import FinGuardService

router = APIRouter()

@router.post("/detect-anomaly", response_model=TransactionAnomalyResult)
def detect_anomaly(payload: TransactionAnomalyRequest, db: Session = Depends(get_db)):
    try:
        return FinGuardService.detect_anomaly(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trace-payment", response_model=PaymentTraceResult)
def trace_payment(payload: PaymentTraceRequest, db: Session = Depends(get_db)):
    try:
        return FinGuardService.trace_payment(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-laundering", response_model=LaunderingPatternResult)
def analyze_laundering(payload: LaunderingPatternRequest, db: Session = Depends(get_db)):
    try:
        return FinGuardService.analyze_laundering(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-compliance", response_model=ComplianceReportResult)
def generate_compliance(payload: ComplianceReportRequest, db: Session = Depends(get_db)):
    try:
        return FinGuardService.generate_compliance(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

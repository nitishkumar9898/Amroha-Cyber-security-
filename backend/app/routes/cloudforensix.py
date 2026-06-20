from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.cloudforensix import IncidentCreate, IncidentResponse, LogAnalysisRequest, LogAnalysisResponse, ContainerScanRequest, ContainerScanResult, ServerlessTraceRequest, TracePathOut, ComplianceCheckResponse
from ..services.cloudforensix_service import CloudForensixService

router = APIRouter()

@router.post("/incidents", response_model=IncidentResponse)
def report_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    try:
        return CloudForensixService.report_incident(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-logs", response_model=LogAnalysisResponse)
def analyze_logs(payload: LogAnalysisRequest, db: Session = Depends(get_db)):
    try:
        return CloudForensixService.analyze_logs(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/scan-container", response_model=ContainerScanResult)
def scan_container(payload: ContainerScanRequest, db: Session = Depends(get_db)):
    try:
        return CloudForensixService.scan_container(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/trace-serverless", response_model=TracePathOut)
def trace_serverless(payload: ServerlessTraceRequest, db: Session = Depends(get_db)):
    try:
        return CloudForensixService.trace_serverless(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/residency-compliance/{incident_id}", response_model=ComplianceCheckResponse)
def check_residency(incident_id: int, db: Session = Depends(get_db)):
    try:
        return CloudForensixService.check_residency(db, incident_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

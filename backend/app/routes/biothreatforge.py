from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.biothreatforge import (
    SequenceAnalysisRequest, SequenceAnalysisResult,
    FacilityMonitorRequest, FacilityMonitorResult
)
from ..services.biothreatforge_service import BioThreatForgeService

router = APIRouter()

@router.post("/analyze-sequence", response_model=SequenceAnalysisResult)
def analyze_sequence(payload: SequenceAnalysisRequest, db: Session = Depends(get_db)):
    try:
        return BioThreatForgeService.analyze_sequence(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitor-facility", response_model=FacilityMonitorResult)
def monitor_facility(payload: FacilityMonitorRequest, db: Session = Depends(get_db)):
    try:
        return BioThreatForgeService.monitor_facility(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.metaguard import AssetTrackingRequest, AssetTrackingResult, AvatarBehaviorRequest, AvatarBehaviorResult, CrimeCorrelationRequest, CrimeCorrelationResult, EvidenceVisualizationRequest, EvidenceVisualizationResult
from ..services.metaguard_service import MetaGuardService

router = APIRouter()

@router.post("/track-asset", response_model=AssetTrackingResult)
def track_asset(payload: AssetTrackingRequest, db: Session = Depends(get_db)):
    try:
        return MetaGuardService.track_asset(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-avatar", response_model=AvatarBehaviorResult)
def analyze_avatar(payload: AvatarBehaviorRequest, db: Session = Depends(get_db)):
    try:
        return MetaGuardService.analyze_avatar(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/correlate-crime", response_model=CrimeCorrelationResult)
def correlate_crime(payload: CrimeCorrelationRequest, db: Session = Depends(get_db)):
    try:
        return MetaGuardService.correlate_crime(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/visualize-evidence", response_model=EvidenceVisualizationResult)
def visualize_evidence(payload: EvidenceVisualizationRequest, db: Session = Depends(get_db)):
    try:
        return MetaGuardService.visualize_evidence(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.innovateguard import IdeaDetectionRequest, IdeaDetectionResult, IPTheftRequest, IPTheftResult, InnovationTrackRequest, InnovationTrackResult
from ..services.innovateguard_service import InnovateGuardService

router = APIRouter()

@router.post("/detect-idea", response_model=IdeaDetectionResult)
def detect_idea(payload: IdeaDetectionRequest, db: Session = Depends(get_db)):
    try:
        return InnovateGuardService.detect_idea(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/investigate-theft", response_model=IPTheftResult)
def investigate_theft(payload: IPTheftRequest, db: Session = Depends(get_db)):
    try:
        return InnovateGuardService.investigate_theft(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/track-innovation", response_model=InnovationTrackResult)
def track_innovation(payload: InnovationTrackRequest, db: Session = Depends(get_db)):
    try:
        return InnovateGuardService.track_innovation(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

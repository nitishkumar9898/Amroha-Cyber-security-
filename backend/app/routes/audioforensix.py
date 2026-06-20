from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.audioforensix import (
    AudioIngestRequest, AudioIngestResult,
    DeepfakeDetectionRequest, DeepfakeDetectionResult,
    EnvironmentReconstructionRequest, EnvironmentReconstructionResult
)
from ..services.audioforensix_service import AudioForensixService

router = APIRouter()

@router.post("/ingest", response_model=AudioIngestResult)
def ingest_audio(payload: AudioIngestRequest, db: Session = Depends(get_db)):
    try:
        return AudioForensixService.ingest_audio(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect-deepfake", response_model=DeepfakeDetectionResult)
def detect_deepfake(payload: DeepfakeDetectionRequest, db: Session = Depends(get_db)):
    try:
        return AudioForensixService.detect_deepfake(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reconstruct-environment", response_model=EnvironmentReconstructionResult)
def reconstruct_environment(payload: EnvironmentReconstructionRequest, db: Session = Depends(get_db)):
    try:
        return AudioForensixService.reconstruct_environment(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

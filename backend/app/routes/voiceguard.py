from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import voiceguard_models as models
from ..schemas import voiceguard_schemas as schemas
from ..modules import voiceguard_engine as engine

router = APIRouter(prefix="/voiceguard", tags=["VoiceGuard"])

@router.post("/analyze", response_model=schemas.AudioAnalysisRead)
def analyze_audio(req: schemas.AudioAnalysisRequest, db: Session = Depends(get_db)):
    result = engine.analyze_audio_forensics(req.audio_file_hash, req.speaker_id)
    
    db_task = models.AudioForensicsTask(
        audio_file_hash=req.audio_file_hash,
        speaker_id=req.speaker_id,
        synthetic_probability=result["synthetic_probability"],
        spectral_anomalies=result["spectral_anomalies"]
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/tasks", response_model=List[schemas.AudioAnalysisRead])
def get_tasks(db: Session = Depends(get_db)):
    return db.query(models.AudioForensicsTask).order_by(models.AudioForensicsTask.analyzed_at.desc()).all()

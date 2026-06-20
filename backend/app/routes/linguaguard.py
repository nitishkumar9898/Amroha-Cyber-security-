from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import linguaguard_models as models
from ..schemas import linguaguard_schemas as schemas
from ..modules import linguaguard_engine as engine

router = APIRouter(prefix="/linguaguard", tags=["LinguaGuard"])

@router.post("/translate", response_model=schemas.TranslationRead)
def translate_threat(req: schemas.TranslateRequest, db: Session = Depends(get_db)):
    result = engine.analyze_and_translate(req.source_language, req.original_text)
    
    db_task = models.TranslationTask(
        source_language=req.source_language,
        original_text=req.original_text,
        translated_text=result["translated_text"],
        threat_intent_score=result["threat_intent_score"]
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/tasks", response_model=List[schemas.TranslationRead])
def get_tasks(db: Session = Depends(get_db)):
    return db.query(models.TranslationTask).order_by(models.TranslationTask.created_at.desc()).all()

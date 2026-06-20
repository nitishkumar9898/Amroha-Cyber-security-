from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import learnforge_models as models
from ..schemas import learnforge_schemas as schemas
from ..modules import learnforge_engine as engine

router = APIRouter(prefix="/learnforge", tags=["LearnForge"])

@router.post("/extract", response_model=schemas.LessonRead)
def extract_incident_lessons(req: schemas.LessonExtractRequest, db: Session = Depends(get_db)):
    result = engine.extract_lessons(req.incident_id, req.raw_report_text)
    
    db_lesson = models.PostIncidentLesson(
        incident_id=req.incident_id,
        extracted_knowledge=result["extracted_knowledge"],
        relevance_score=result["relevance_score"],
        status=result["status"]
    )
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson

@router.get("/lessons", response_model=List[schemas.LessonRead])
def get_lessons(db: Session = Depends(get_db)):
    return db.query(models.PostIncidentLesson).all()

@router.post("/lessons/{lesson_id}/update-graph", response_model=schemas.KnowledgeGraphUpdateResult)
def update_graph(lesson_id: int, db: Session = Depends(get_db)):
    lesson = db.query(models.PostIncidentLesson).filter(models.PostIncidentLesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
        
    result = engine.update_knowledge_graph(lesson.id, lesson.extracted_knowledge)
    lesson.status = "Graph Updated"
    db.commit()
    return result

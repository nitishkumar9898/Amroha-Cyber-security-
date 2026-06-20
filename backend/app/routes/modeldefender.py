from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import modeldefender_models as models
from ..schemas import modeldefender_schemas as schemas
from ..modules import modeldefender_engine as engine

router = APIRouter(prefix="/modeldefender", tags=["ModelDefender"])

@router.post("/logs", response_model=schemas.ModelDefenderLogRead)
def create_log(log: schemas.ModelDefenderLogCreate, db: Session = Depends(get_db)):
    db_log = models.ModelDefenderLog(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

@router.get("/logs", response_model=List[schemas.ModelDefenderLogRead])
def get_logs(db: Session = Depends(get_db)):
    return db.query(models.ModelDefenderLog).all()

@router.post("/watermark", response_model=schemas.WatermarkResponse)
def apply_watermark(req: schemas.WatermarkRequest):
    w_hash = engine.generate_watermark(req.model_name, req.owner_id)
    return schemas.WatermarkResponse(
        model_name=req.model_name,
        watermark_hash=w_hash,
        status="Watermark Applied Successfully"
    )

@router.post("/detect-extraction")
def detect_extraction(query_patterns: List[str]):
    score = engine.detect_extraction_attack(query_patterns)
    action = "Block IP" if score > 0.8 else "Monitor"
    return {"threat_score": score, "recommended_action": action}

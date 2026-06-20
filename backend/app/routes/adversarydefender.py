from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import adversarydefender_models as models
from ..schemas import adversarydefender_schemas as schemas
from ..modules import adversarydefender_engine as engine

router = APIRouter(prefix="/adversarydefender", tags=["AdversaryDefender"])

@router.post("/detect", response_model=schemas.DetectionRead)
def detect_poisoning(req: schemas.DetectionRequest, db: Session = Depends(get_db)):
    result = engine.detect_data_poisoning(req.dataset_name, req.sample_id)
    
    db_det = models.PoisoningDetection(
        dataset_name=req.dataset_name,
        sample_id=req.sample_id,
        poison_probability=result["poison_probability"],
        perturbation_type=result["perturbation_type"]
    )
    db.add(db_det)
    db.commit()
    db.refresh(db_det)
    return db_det

@router.get("/detections", response_model=List[schemas.DetectionRead])
def get_detections(db: Session = Depends(get_db)):
    return db.query(models.PoisoningDetection).order_by(models.PoisoningDetection.detected_at.desc()).all()

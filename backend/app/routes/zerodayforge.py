from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import zerodayforge_models as models
from ..schemas import zerodayforge_schemas as schemas
from ..modules import zerodayforge_engine as engine

router = APIRouter(prefix="/zerodayforge", tags=["ZeroDayForge"])

@router.post("/predict", response_model=schemas.PredictionRead)
def predict_vulnerability(req: schemas.PredictionRequest, db: Session = Depends(get_db)):
    result = engine.predict_vulnerability(req.software_component, req.version)
    
    db_pred = models.VulnerabilityPrediction(
        software_component=req.software_component,
        version=req.version,
        predicted_cve_severity=result["predicted_cve_severity"],
        vulnerability_type=result["vulnerability_type"]
    )
    db.add(db_pred)
    db.commit()
    db.refresh(db_pred)
    return db_pred

@router.get("/predictions", response_model=List[schemas.PredictionRead])
def get_predictions(db: Session = Depends(get_db)):
    return db.query(models.VulnerabilityPrediction).order_by(models.VulnerabilityPrediction.created_at.desc()).all()

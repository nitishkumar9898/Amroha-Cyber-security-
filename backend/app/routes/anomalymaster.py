from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import anomalymaster_models as models
from ..schemas import anomalymaster_schemas as schemas
from ..modules import anomalymaster_engine as engine

router = APIRouter(prefix="/anomalymaster", tags=["AnomalyMaster"])

@router.post("/report", response_model=schemas.AnomalyRead)
def report_anomaly(req: schemas.AnomalyReport, db: Session = Depends(get_db)):
    result = engine.analyze_anomaly(req.metric_source, req.observed_value, req.expected_value)
    
    db_anomaly = models.SystemAnomaly(
        metric_source=req.metric_source,
        observed_value=req.observed_value,
        expected_value=req.expected_value,
        deviation_score=result["deviation_score"],
        root_cause_hypothesis=result["root_cause_hypothesis"]
    )
    db.add(db_anomaly)
    db.commit()
    db.refresh(db_anomaly)
    return db_anomaly

@router.get("/anomalies", response_model=List[schemas.AnomalyRead])
def get_anomalies(db: Session = Depends(get_db)):
    return db.query(models.SystemAnomaly).order_by(models.SystemAnomaly.detected_at.desc()).all()

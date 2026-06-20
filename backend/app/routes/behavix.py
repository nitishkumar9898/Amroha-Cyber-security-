from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import behavix_models as models
from ..schemas import behavix_schemas as schemas
from ..modules import behavix_engine as engine

router = APIRouter(prefix="/behavix", tags=["Behavix"])

@router.post("/profiles", response_model=schemas.BehaviorProfileRead)
def create_profile(profile: schemas.BehaviorProfileCreate, db: Session = Depends(get_db)):
    db_profile = models.BehaviorProfile(username=profile.username)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@router.get("/profiles", response_model=List[schemas.BehaviorProfileRead])
def get_profiles(db: Session = Depends(get_db)):
    return db.query(models.BehaviorProfile).all()

@router.post("/analyze-session", response_model=schemas.AnomalyResult)
def analyze_session(metrics: schemas.SessionMetrics, db: Session = Depends(get_db)):
    profile = db.query(models.BehaviorProfile).filter(models.BehaviorProfile.username == metrics.username).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    result = engine.analyze_behavior(
        profile.baseline_keystroke_dynamics, 
        profile.baseline_mouse_patterns, 
        metrics.dict()
    )
    
    profile.current_risk_score = result["risk_score"]
    db.commit()
    
    return schemas.AnomalyResult(
        username=profile.username,
        anomaly_detected=result["anomaly_detected"],
        risk_score=result["risk_score"],
        reason=result["reason"]
    )

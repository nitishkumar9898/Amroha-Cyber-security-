from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import legacyshield_models as models
from ..schemas import legacyshield_schemas as schemas
from ..modules import legacyshield_engine as engine

router = APIRouter(prefix="/legacyshield", tags=["LegacyShield"])

@router.post("/investigate", response_model=schemas.InvestigationRead)
def investigate_system(req: schemas.InvestigationRequest, db: Session = Depends(get_db)):
    result = engine.analyze_legacy_system(req.system_type, req.protocol, req.air_gap_status)
    
    db_inv = models.LegacyInvestigation(
        system_type=req.system_type,
        protocol=req.protocol,
        air_gap_status=req.air_gap_status,
        migration_risk_score=result["migration_risk_score"]
    )
    db.add(db_inv)
    db.commit()
    db.refresh(db_inv)
    return db_inv

@router.get("/investigations", response_model=List[schemas.InvestigationRead])
def get_investigations(db: Session = Depends(get_db)):
    return db.query(models.LegacyInvestigation).order_by(models.LegacyInvestigation.investigated_at.desc()).all()

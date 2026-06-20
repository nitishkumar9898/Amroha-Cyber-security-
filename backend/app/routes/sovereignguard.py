from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import sovereignguard_models as models
from ..schemas import sovereignguard_schemas as schemas
from ..modules import sovereignguard_engine as engine

router = APIRouter(prefix="/sovereignguard", tags=["SovereignGuard"])

@router.post("/check", response_model=schemas.SovereigntyCheckRead)
def check_sovereignty(req: schemas.SovereigntyCheckRequest, db: Session = Depends(get_db)):
    result = engine.check_data_sovereignty(req.data_classification, req.destination_region)
    
    db_check = models.DataSovereigntyCheck(
        data_classification=req.data_classification,
        destination_region=req.destination_region,
        compliance_status=result["compliance_status"],
        violation_risk_score=result["violation_risk_score"]
    )
    db.add(db_check)
    db.commit()
    db.refresh(db_check)
    return db_check

@router.get("/checks", response_model=List[schemas.SovereigntyCheckRead])
def get_checks(db: Session = Depends(get_db)):
    return db.query(models.DataSovereigntyCheck).order_by(models.DataSovereigntyCheck.checked_at.desc()).all()

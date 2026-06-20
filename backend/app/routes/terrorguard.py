from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import terrorguard_models as models
from ..schemas import terrorguard_schemas as schemas
from ..modules import terrorguard_engine as engine

router = APIRouter(prefix="/terrorguard", tags=["TerrorGuard"])

@router.post("/analyze", response_model=schemas.ThreatRead)
def analyze_threat(req: schemas.ThreatRequest, db: Session = Depends(get_db)):
    result = engine.analyze_hybrid_threat(req.target_sector, req.attack_vector)
    
    db_threat = models.HybridWarfareThreat(
        target_sector=req.target_sector,
        attack_vector=req.attack_vector,
        state_sponsor_prob=result["state_sponsor_prob"],
        threat_level=result["threat_level"]
    )
    db.add(db_threat)
    db.commit()
    db.refresh(db_threat)
    return db_threat

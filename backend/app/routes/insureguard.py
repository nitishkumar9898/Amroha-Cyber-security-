from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import insureguard_models as models
from ..schemas import insureguard_schemas as schemas
from ..modules import insureguard_engine as engine
from typing import List

router = APIRouter(prefix="/insureguard", tags=["InsureGuard"])

@router.post("/policy", response_model=schemas.PolicyRead)
def create_policy(policy: schemas.PolicyCreate, db: Session = Depends(get_db)):
    db_policy = models.Policy(**policy.dict())
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)
    return db_policy

@router.get("/policy", response_model=List[schemas.PolicyRead])
def list_policies(db: Session = Depends(get_db)):
    return db.query(models.Policy).all()

@router.post("/claim", response_model=schemas.ClaimRead)
def submit_claim(claim: schemas.ClaimCreate, db: Session = Depends(get_db)):
    policy = db.query(models.Policy).filter(models.Policy.id == claim.policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    risk = engine.score_risk({
        "coverage_limit": policy.coverage_limit,
        "premium": policy.premium,
        "insured_entity": policy.insured_entity,
    })
    simulated = engine.simulate_claim_impact(risk, claim.reported_loss)
    db_claim = models.Claim(
        policy_id=claim.policy_id,
        incident_type=claim.incident_type,
        reported_loss=claim.reported_loss,
        simulated_loss=simulated,
    )
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
    return db_claim

@router.get("/policy/{policy_id}/premium-recommendation")
def premium_recommendation(policy_id: int, db: Session = Depends(get_db)):
    policy = db.query(models.Policy).filter(models.Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    risk = engine.score_risk({
        "coverage_limit": policy.coverage_limit,
        "premium": policy.premium,
        "insured_entity": policy.insured_entity,
    })
    new_premium = engine.recommend_premium({
        "coverage_limit": policy.coverage_limit,
        "premium": policy.premium,
        "insured_entity": policy.insured_entity,
    }, risk)
    return {"recommended_premium": new_premium, "risk_scores": risk}

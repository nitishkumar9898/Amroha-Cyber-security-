from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import psyopsforge_models as models
from ..schemas import psyopsforge_schemas as schemas
from ..modules import psyopsforge_engine as engine

router = APIRouter(prefix="/psyopsforge", tags=["PsyOpsForge"])

@router.post("/campaigns", response_model=schemas.PsyOpsCampaignRead)
def create_campaign(campaign: schemas.PsyOpsCampaignCreate, db: Session = Depends(get_db)):
    result = engine.simulate_campaign(campaign.target_demographic, campaign.misinformation_type)
    
    db_campaign = models.PsyOpsCampaign(
        target_demographic=campaign.target_demographic,
        misinformation_type=campaign.misinformation_type,
        sentiment_impact=result["sentiment_impact"],
        status=result["status"]
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

@router.get("/campaigns", response_model=List[schemas.PsyOpsCampaignRead])
def get_campaigns(db: Session = Depends(get_db)):
    return db.query(models.PsyOpsCampaign).all()

@router.get("/campaigns/{campaign_id}/counter", response_model=schemas.CounterStrategyResponse)
def get_counter_strategy(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(models.PsyOpsCampaign).filter(models.PsyOpsCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    result = engine.generate_counter_strategy(campaign.sentiment_impact)
    return schemas.CounterStrategyResponse(
        campaign_id=campaign.id,
        strategy=result["strategy"],
        predicted_recovery=result["predicted_recovery"]
    )

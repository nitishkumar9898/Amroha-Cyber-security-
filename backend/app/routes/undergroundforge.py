from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import undergroundforge_models as models
from ..schemas import undergroundforge_schemas as schemas
from ..modules import undergroundforge_engine as engine

router = APIRouter(prefix="/undergroundforge", tags=["UndergroundForge"])

@router.post("/scan", response_model=schemas.UndergroundAlertRead)
def scan_marketplace(req: schemas.ScrapeRequest, db: Session = Depends(get_db)):
    result = engine.simulate_darkweb_scrape(req.marketplace_url, req.target_keyword)
    
    db_alert = models.UndergroundAlert(
        marketplace=result["marketplace"],
        keyword=result["keyword"],
        match_context=result["match_context"],
        threat_level=result["threat_level"]
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

@router.get("/alerts", response_model=List[schemas.UndergroundAlertRead])
def get_alerts(db: Session = Depends(get_db)):
    return db.query(models.UndergroundAlert).order_by(models.UndergroundAlert.scraped_at.desc()).all()

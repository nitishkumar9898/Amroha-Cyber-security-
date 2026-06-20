from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import smartcityguard_models as models
from ..schemas import smartcityguard_schemas as schemas
from ..modules import smartcityguard_engine as engine

router = APIRouter(prefix="/smartcityguard", tags=["SmartCityGuard"])

@router.post("/events", response_model=schemas.CityEventRead)
def report_event(event: schemas.CityEventCreate, db: Session = Depends(get_db)):
    result = engine.analyze_city_event(event.city_zone, event.iot_device_type, event.device_id)
    
    db_event = models.SmartCityEvent(
        city_zone=event.city_zone,
        iot_device_type=event.iot_device_type,
        device_id=event.device_id,
        anomaly_score=result["anomaly_score"],
        event_status=result["event_status"]
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.get("/events", response_model=List[schemas.CityEventRead])
def get_events(db: Session = Depends(get_db)):
    return db.query(models.SmartCityEvent).order_by(models.SmartCityEvent.detected_at.desc()).all()

@router.post("/events/{event_id}/isolate", response_model=schemas.IsolationResponse)
def trigger_isolation(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.SmartCityEvent).filter(models.SmartCityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    result = engine.isolate_device(event.id)
    event.event_status = "Isolated"
    db.commit()
    return result

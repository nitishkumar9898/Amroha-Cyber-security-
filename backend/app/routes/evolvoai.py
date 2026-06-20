from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models.evolvoai import HITLFeedback, AIModelVersion
from app.schemas.evolvoai import FeedbackRequest, FeedbackOut, ModelRegistryRequest, ModelRegistryOut
from app.modules.evolvoai.continual_learner import continual_learner
from app.modules.evolvoai.dataset_curator import dataset_curator
from app.modules.evolvoai.performance_monitor import performance_monitor
from app.modules.evolvoai.model_registry import model_registry
from app.modules.evolvoai.hitl_feedback import hitl_feedback

router = APIRouter()

@router.post("/feedback", response_model=FeedbackOut)
async def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    result = await hitl_feedback.submit_feedback(request.data_id, request.corrected_label, request.analyst)
    
    db_feedback = HITLFeedback(
        data_id=request.data_id,
        corrected_label=request.corrected_label,
        analyst=request.analyst
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback

@router.post("/curate")
async def curate_dataset(raw_data: List[Dict[str, Any]]):
    result = await dataset_curator.curate_from_modules(raw_data)
    return result

@router.get("/monitor/{model_id}")
async def check_model_performance(model_id: str, recent_accuracy: float):
    result = await performance_monitor.check_drift(model_id, recent_accuracy)
    return result

@router.post("/train/{model_id}")
async def trigger_training(model_id: str, dataset_id: str):
    result = await continual_learner.train_incremental(model_id, dataset_id)
    return result

@router.post("/registry", response_model=ModelRegistryOut)
async def register_model(request: ModelRegistryRequest, db: Session = Depends(get_db)):
    await model_registry.register_model(request.model_id, request.version, request.metrics)
    
    db_model = AIModelVersion(
        model_id=request.model_id,
        version=request.version,
        metrics=request.metrics
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    
    return db_model

@router.put("/registry/{model_id}/promote/{version}")
async def promote_model(model_id: str, version: str, db: Session = Depends(get_db)):
    success = await model_registry.promote_model(model_id, version)
    
    db_model = db.query(AIModelVersion).filter_by(model_id=model_id, version=version).first()
    if db_model:
        db_model.status = "production"
        db.commit()
        
    return {"success": success}

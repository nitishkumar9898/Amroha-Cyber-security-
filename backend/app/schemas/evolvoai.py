from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

class FeedbackRequest(BaseModel):
    data_id: str
    corrected_label: str
    analyst: str

class FeedbackOut(FeedbackRequest):
    id: int
    status: str
    submitted_at: datetime
    
    class Config:
        from_attributes = True

class ModelRegistryRequest(BaseModel):
    model_id: str
    version: str
    metrics: Dict[str, Any]

class ModelRegistryOut(ModelRegistryRequest):
    id: int
    status: str
    registered_at: datetime
    
    class Config:
        from_attributes = True

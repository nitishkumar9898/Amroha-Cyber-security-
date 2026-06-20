from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CorrelationJobCreate(BaseModel):
    source_module: str
    target_module: str

class CorrelationJobRead(CorrelationJobCreate):
    id: int
    confidence_score: float
    created_at: datetime
    status: str

    class Config:
        from_attributes = True

class GraphNode(BaseModel):
    id: str
    label: str
    type: str

class GraphLink(BaseModel):
    source: str
    target: str
    relationship: str
    weight: float

class CorrelationGraphResponse(BaseModel):
    job_id: int
    nodes: list[GraphNode]
    links: list[GraphLink]

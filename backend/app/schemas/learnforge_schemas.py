from pydantic import BaseModel
from datetime import datetime

class LessonExtractRequest(BaseModel):
    incident_id: str
    raw_report_text: str

class LessonRead(BaseModel):
    id: int
    incident_id: str
    extracted_knowledge: str
    relevance_score: float
    created_at: datetime
    status: str

    class Config:
        from_attributes = True

class KnowledgeGraphUpdateResult(BaseModel):
    lesson_id: int
    nodes_added: int
    edges_added: int
    status: str

from pydantic import BaseModel
from datetime import datetime

class TranslateRequest(BaseModel):
    source_language: str
    original_text: str

class TranslationRead(TranslateRequest):
    id: int
    translated_text: str
    threat_intent_score: float
    created_at: datetime

    class Config:
        from_attributes = True

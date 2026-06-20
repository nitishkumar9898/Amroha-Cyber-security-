from pydantic import ConfigDict
# backend/app/schemas/osint.py

from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field

class SocialPostBase(BaseModel):
    platform: str = Field(..., max_length=50)
    post_id: str = Field(..., max_length=200)
    content: Any = Field(..., description="Full post payload (JSON)")
    author_hash: str = Field(..., max_length=64, description="Hashed identifier for privacy")
    url: Optional[str] = Field(None, max_length=500)
    raw_json: Optional[Any] = None

class SocialPostCreate(SocialPostBase):
    pass

class SocialPostOut(SocialPostBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class ActorProfileBase(BaseModel):
    name_hash: str = Field(..., max_length=64)
    platforms: Optional[List[str]] = None
    affiliations: Optional[List[str]] = None
    risk_score: float = 0.0

class ActorProfileOut(ActorProfileBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class MisinformationEventBase(BaseModel):
    post_id: int
    claim_text: str = Field(..., max_length=500)
    fact_check_url: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)

class MisinformationEventOut(MisinformationEventBase):
    id: int
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CrawlJobBase(BaseModel):
    platform: str = Field(..., max_length=50)
    query: str = Field(..., max_length=200)
    schedule: Optional[str] = None  # cron expression or "once"

class CrawlJobCreate(CrawlJobBase):
    pass

class CrawlJobOut(CrawlJobBase):
    id: int
    status: str = Field(..., max_length=20)
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


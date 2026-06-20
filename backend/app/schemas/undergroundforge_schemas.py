from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ScrapeRequest(BaseModel):
    marketplace_url: str
    target_keyword: str

class UndergroundAlertRead(BaseModel):
    id: int
    marketplace: str
    keyword: str
    match_context: str
    threat_level: float
    scraped_at: datetime

    class Config:
        from_attributes = True

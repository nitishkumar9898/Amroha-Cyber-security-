from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TransactionRequest(BaseModel):
    wallet_address: str
    transaction_hash: str

class TransactionRead(TransactionRequest):
    id: int
    risk_score: float
    flags: str
    analyzed_at: datetime

    class Config:
        from_attributes = True

class TracingResponse(BaseModel):
    transaction_hash: str
    hops: int
    associated_entities: str

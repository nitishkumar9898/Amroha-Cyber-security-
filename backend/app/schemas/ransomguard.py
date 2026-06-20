from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class IncidentBase(BaseModel):
    target_entity: str
    ransom_note: str
    demanded_amount: float
    currency: Optional[str] = "BTC"

class IncidentCreate(IncidentBase):
    pass

class IncidentResponse(IncidentBase):
    id: int
    status: str
    reported_at: datetime

    class Config:
        from_attributes = True

class TraceRequest(BaseModel):
    incident_id: int
    initial_wallet_address: str

class WalletSchema(BaseModel):
    address: str
    wallet_type: str
    balance: float

class TraceSchema(BaseModel):
    from_address: str
    to_address: str
    amount: float
    risk_score: float

class TraceReport(BaseModel):
    incident_id: int
    wallets_identified: List[WalletSchema]
    transaction_graph: List[TraceSchema]
    attribution: str

class ComplianceReportOut(BaseModel):
    incident_id: int
    chain_of_custody_hash: str
    evidence_logs: List[Dict[str, Any]]
    generated_at: datetime

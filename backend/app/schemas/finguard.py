from pydantic import BaseModel, ConfigDict
from typing import Optional

class TransactionAnomalyRequest(BaseModel):
    transaction_id: str
    amount: float
    velocity_score: float # Transactions per minute from the same source

class TransactionAnomalyResult(BaseModel):
    transaction_id: str
    is_anomalous: bool
    action_taken: str

class PaymentTraceRequest(BaseModel):
    trace_id: str
    hop_sequence: str # e.g., "UPI -> Crypto -> SWIFT"

class PaymentTraceResult(BaseModel):
    trace_id: str
    complexity_score: float
    crosses_borders: bool
    trace_status: str

class LaunderingPatternRequest(BaseModel):
    entity_id: str
    transaction_count: int
    average_amount: float
    osint_threat_intel: bool
    ransomware_watchlist: bool

class LaunderingPatternResult(BaseModel):
    entity_id: str
    pattern_type: str
    risk_level: str

class ComplianceReportRequest(BaseModel):
    agency: str
    raw_financial_data: str

class ComplianceReportResult(BaseModel):
    report_id: str
    agency: str
    report_hash: str
    submission_status: str

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# ── Cryptanalysis Job ─────────────────────────────────────────────────

class CryptanalysisJobCreate(BaseModel):
    algorithm: str = Field(..., example="RSA")
    key_size: int = Field(..., example=2048)
    attack_type: str = Field(..., example="shor")
    additional_metadata: Optional[Dict[str, Any]] = None

class CryptanalysisJobRead(BaseModel):
    id: int
    algorithm: str
    key_size: int
    attack_type: str
    estimated_qubits: Optional[int]
    estimated_time_years: Optional[float]
    status: str
    result: Optional[Dict[str, Any]]
    created_at: str
    completed_at: Optional[str]
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# ── Weak Encryption Scan ─────────────────────────────────────────────

class WeakEncryptionScanCreate(BaseModel):
    target: str = Field(..., example="api.example.com")
    scan_type: str = Field(default="tls_scan", example="tls_scan")
    additional_metadata: Optional[Dict[str, Any]] = None

class WeakEncryptionScanRead(BaseModel):
    id: int
    target: str
    scan_type: str
    findings: Optional[List[Dict[str, Any]]]
    risk_score: float
    scanned_at: str
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# ── Side-Channel Test ────────────────────────────────────────────────

class SideChannelTestCreate(BaseModel):
    channel_type: str = Field(..., example="timing")
    target_algorithm: str = Field(..., example="AES-256-CBC")
    target_implementation: Optional[str] = Field(None, example="openssl-3.1.4")
    additional_metadata: Optional[Dict[str, Any]] = None

class SideChannelTestRead(BaseModel):
    id: int
    channel_type: str
    target_algorithm: str
    target_implementation: Optional[str]
    vulnerable: bool
    leakage_score: float
    details: Optional[Dict[str, Any]]
    tested_at: str
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# ── Quantum Readiness Report ─────────────────────────────────────────

class QuantumReadinessCreate(BaseModel):
    organisation: str = Field(..., example="Acme Corp")
    algorithms_in_use: List[Dict[str, Any]] = Field(..., description="List of {algorithm, key_size} objects")
    additional_metadata: Optional[Dict[str, Any]] = None

class QuantumReadinessRead(BaseModel):
    id: int
    organisation: str
    algorithms_in_use: Optional[List[Dict[str, Any]]]
    overall_score: float
    recommendations: Optional[List[Dict[str, Any]]]
    generated_at: str
    additional_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

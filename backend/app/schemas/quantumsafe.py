from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CryptoAssetBase(BaseModel):
    scan_id: str
    asset_name: str
    algorithm: str
    key_size: int
    is_quantum_safe: bool

class CryptoAssetRead(CryptoAssetBase):
    id: int
    discovery_date: datetime

class PQCVulnerabilityRead(BaseModel):
    id: int
    asset_id: int
    hndl_risk_score: float
    estimated_qday_years: int
    criticality: str

class MigrationSimulationRead(BaseModel):
    id: int
    asset_id: int
    recommended_pqc: str
    legacy_latency_ms: float
    pqc_latency_ms: float
    memory_overhead_kb: float

class PQCScanRequest(BaseModel):
    target_system: str
    scan_id: str

class AssetAnalysisResult(BaseModel):
    asset: CryptoAssetRead
    vulnerability: Optional[PQCVulnerabilityRead]
    migration: Optional[MigrationSimulationRead]

class PQCScanResponse(BaseModel):
    scan_id: str
    target_system: str
    assets: List[AssetAnalysisResult]

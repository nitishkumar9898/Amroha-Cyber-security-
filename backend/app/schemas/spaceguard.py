from pydantic import BaseModel, ConfigDict
from typing import Optional

class SatCommRequest(BaseModel):
    satellite_id: str
    protocol: str
    signal_to_noise_ratio: float
    auth_handshake_valid: bool

class SatCommResult(BaseModel):
    satellite_id: str
    is_hijacked: bool
    status_message: str

class OrbitalSimRequest(BaseModel):
    mission_name: str
    payload_type: str
    firmware_hash: str

class OrbitalSimResult(BaseModel):
    mission_name: str
    orbital_risk_score: float
    vulnerability_found: bool
    details: str

class AssetProtectionRequest(BaseModel):
    asset_id: str
    threat_intel_level: str # LOW, ELEVATED, CRITICAL

class AssetProtectionResult(BaseModel):
    asset_id: str
    defensive_posture: str

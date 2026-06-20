from pydantic import BaseModel, ConfigDict
from typing import Optional

class NanoScanRequest(BaseModel):
    device_id: str
    electron_spin_variance: float
    entanglement_stable: bool

class NanoScanResult(BaseModel):
    device_id: str
    is_hijacked: bool
    status_message: str

class NanoSimRequest(BaseModel):
    threat_type: str
    time_elapsed_seconds: int

class NanoSimResult(BaseModel):
    threat_type: str
    replication_rate: float
    material_consumed_kg: float
    countermeasure_deployed: str

class HardwareValidationRequest(BaseModel):
    hardware_id: str
    pqc_algorithm_applied: str

class HardwareValidationResult(BaseModel):
    hardware_id: str
    atomic_integrity_verified: bool
    message: str

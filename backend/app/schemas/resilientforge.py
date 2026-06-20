from pydantic import BaseModel, ConfigDict
from typing import Optional

class SimulationRequest(BaseModel):
    scenario_name: str
    target_infrastructure: str
    simulated_downtime_hours: float

class SimulationReport(BaseModel):
    scenario_name: str
    target_infrastructure: str
    optimized_rto_hours: float
    optimization_strategy: str

class BackupVerifyRequest(BaseModel):
    backup_id: str
    file_signature: str

class BackupVerifyResult(BaseModel):
    backup_id: str
    is_corrupt: bool
    malware_detected: bool
    status_message: str

class HealRequest(BaseModel):
    asset_id: str
    initial_state: str # e.g. CORRUPTED

class HealResult(BaseModel):
    asset_id: str
    final_state: str
    reconstruction_method: str

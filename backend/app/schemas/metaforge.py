from pydantic import BaseModel, ConfigDict
from typing import Optional

class MetricIngestRequest(BaseModel):
    source_module: str
    latency_ms: float
    error_rate: float

class MetricIngestResult(BaseModel):
    source_module: str
    optimization_suggestion: str

class EvolutionRequest(BaseModel):
    target_module: str
    current_version: str

class EvolutionResult(BaseModel):
    target_module: str
    proposed_version: str
    upgrade_manifest: str

class InternalAnomalyRequest(BaseModel):
    subsystem: str
    anomaly_type: str

class InternalAnomalyResult(BaseModel):
    subsystem: str
    severity: str
    action_taken: str

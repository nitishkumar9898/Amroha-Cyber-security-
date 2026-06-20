from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class IncidentBase(BaseModel):
    provider: str
    severity: str

class IncidentCreate(IncidentBase):
    pass

class IncidentResponse(IncidentBase):
    id: int
    status: str
    reported_at: datetime

    class Config:
        from_attributes = True

class LogAnalysisRequest(BaseModel):
    incident_id: int
    log_source: str
    raw_logs: List[Dict[str, Any]]

class LogAnalysisResponse(BaseModel):
    incident_id: int
    analyzed_count: int
    anomalies_detected: int
    findings: List[str]

class ContainerScanRequest(BaseModel):
    incident_id: int
    image_hash: str
    namespace: str

class ContainerScanResult(BaseModel):
    incident_id: int
    image_hash: str
    escape_detected: bool = False
    vulnerabilities: List[str]

class ServerlessTraceRequest(BaseModel):
    incident_id: int
    function_name: str

class TracePathOut(BaseModel):
    incident_id: int
    function_name: str
    execution_path: List[str]
    malicious_payload_detected: bool

class ComplianceCheckResponse(BaseModel):
    incident_id: int
    is_compliant: bool
    violations: List[str]

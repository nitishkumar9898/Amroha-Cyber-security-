from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime


class Modality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    BINARY = "binary"
    NETWORK = "network"
    MULTI = "multi"


class Domain(str, Enum):
    DEEPFAKE = "deepfake"
    MALWARE = "malware_analysis"
    MOBILE = "mobile_forensics"
    IOT = "iot_forensics"
    DARKWEB = "darkweb_intel"
    CYBER_PSYCHOLOGY = "cyber_psychology"
    OSINT = "osint"
    PREDICTIVE = "predictive_analytics"
    CORRELATION = "evidence_correlation"
    DIGITAL_FORENSICS = "digital_forensics"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ChainOfCustodyStatus(str, Enum):
    ACQUIRED = "acquired"
    ANALYZING = "analyzing"
    VERIFIED = "verified"
    CHALLENGED = "challenged"
    ADMISSIBLE = "admissible"
    REJECTED = "rejected"


@dataclass
class CustodyEvent:
    timestamp: str
    action: str
    actor: str
    module: str
    hash: str
    notes: str = ""


@dataclass
class EvidenceMetadata:
    evidence_id: str
    case_id: str
    modality: Modality
    domain: Domain
    acquired_at: str
    acquired_by: str
    source: str
    size_bytes: int
    hash_sha256: str
    chain_of_custody: list[CustodyEvent] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class AIAnalysisResult:
    evidence_id: str
    module_id: str
    domain: Domain
    findings: list[dict[str, Any]]
    confidence: float
    processing_time_ms: int
    model_version: str
    xai_explanation: Optional[dict[str, Any]] = None
    raw_output: dict[str, Any] = field(default_factory=dict)


@dataclass
class InvestigationReport:
    report_id: str
    case_id: str
    generated_at: str
    generated_by: str
    modules_involved: list[str]
    evidence_count: int
    findings: list[dict[str, Any]]
    graph_summary: Optional[dict[str, Any]] = None
    recommendations: list[str] = field(default_factory=list)
    section_65b_compliant: bool = False

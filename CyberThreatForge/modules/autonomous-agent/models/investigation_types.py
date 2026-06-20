from enum import Enum
from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field


class InvestigationType(str, Enum):
    MALWARE_OUTBREAK = "malware_outbreak"
    PHISHING_CAMPAIGN = "phishing_campaign"
    INSIDER_THREAT = "insider_threat"
    APT_INVESTIGATION = "apt_investigation"
    DATA_BREACH = "data_breach"
    CUSTOM = "custom"


class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    APPROVED = "approved"
    REJECTED = "rejected"
    AWAITING_APPROVAL = "awaiting_approval"


class InvestigationStatus(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CheckpointType(str, Enum):
    BEFORE_DANGEROUS = "before_dangerous"
    BEFORE_DATA_SHARING = "before_data_sharing"
    BEFORE_FINAL_REPORT = "before_final_report"
    CUSTOM = "custom"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvidenceCategory(str, Enum):
    FILE = "file"
    NETWORK = "network"
    PROCESS = "process"
    REGISTRY = "registry"
    MEMORY = "memory"
    LOG = "log"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    EMAIL = "email"
    DOMAIN = "domain"
    IP_ADDRESS = "ip_address"
    SOCIAL = "social"
    DARKWEB = "darkweb"
    OTHER = "other"


class ToolCall(BaseModel):
    tool_name: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 60
    retry_count: int = 3


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: int = 0
    confidence: float = 1.0


class InvestigationStep(BaseModel):
    step_id: str
    name: str
    description: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: Optional[ToolResult] = None
    risk_level: RiskLevel = RiskLevel.LOW
    requires_approval: bool = False
    checkpoint_type: Optional[CheckpointType] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


class InvestigationPlan(BaseModel):
    plan_id: str
    investigation_type: InvestigationType
    case_id: str
    description: str = ""
    steps: list[InvestigationStep] = Field(default_factory=list)
    risk_assessment: dict[str, Any] = Field(default_factory=dict)
    estimated_duration_minutes: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)


class InvestigationResult(BaseModel):
    step_id: str
    findings: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    summary: str = ""
    confidence: float = 0.0
    gaps: list[str] = Field(default_factory=list)
    follow_up_steps: list[str] = Field(default_factory=list)
    chain_of_custody: list[dict[str, Any]] = Field(default_factory=list)


class AgentState(BaseModel):
    investigation_id: str
    plan: Optional[InvestigationPlan] = None
    current_step_index: int = 0
    status: InvestigationStatus = InvestigationStatus.CREATED
    results: dict[str, InvestigationResult] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    memory: list[dict[str, Any]] = Field(default_factory=list)
    pending_approval: Optional[InvestigationStep] = None
    errors: list[str] = Field(default_factory=list)
    custody_events: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


class HumanFeedback(BaseModel):
    step_id: str
    approved: bool
    feedback: str = ""
    modifications: Optional[dict[str, Any]] = None
    provided_by: str = "analyst"
    provided_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CaseContext(BaseModel):
    case_id: str
    title: str = ""
    description: str = ""
    investigation_type: InvestigationType = InvestigationType.CUSTOM
    evidence_items: list[dict[str, Any]] = Field(default_factory=list)
    targets: list[str] = Field(default_factory=list)
    priority: str = "medium"
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InvestigationSummary(BaseModel):
    investigation_id: str
    status: InvestigationStatus
    plan_id: str = ""
    steps_completed: int = 0
    steps_total: int = 0
    findings_count: int = 0
    confidence_overall: float = 0.0
    duration_seconds: int = 0
    summary: str = ""
    recommendations: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    custody_chain_integrity: bool = True


class StartInvestigationResponse(BaseModel):
    investigation_id: str
    status: InvestigationStatus
    message: str = ""


class StepExecutionResponse(BaseModel):
    step_id: str
    status: StepStatus
    result: Optional[ToolResult] = None
    requires_approval: bool = False
    message: str = ""


class PlanResponse(BaseModel):
    plan_id: str
    investigation_type: InvestigationType
    steps: list[InvestigationStep]
    risk_assessment: dict[str, Any]
    estimated_duration_minutes: int
    message: str = ""

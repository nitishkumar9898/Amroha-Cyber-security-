import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from models.investigation_types import (
    InvestigationType,
    InvestigationPlan,
    InvestigationStep,
    ToolCall,
    StepStatus,
    RiskLevel,
    CheckpointType,
    CaseContext,
)

logger = logging.getLogger(__name__)

INVESTIGATION_TEMPLATES: dict[InvestigationType, dict[str, Any]] = {
    InvestigationType.MALWARE_OUTBREAK: {
        "description": "Automated malware outbreak investigation across endpoints and network",
        "estimated_minutes": 45,
        "steps": [
            {
                "name": "Initial Triage",
                "description": "Collect initial indicators and scope of outbreak",
                "tool_calls": [
                    ToolCall(tool_name="sentinel.list_indicators", parameters={}, timeout_seconds=30),
                ],
                "risk_level": RiskLevel.LOW,
            },
            {
                "name": "Sample Acquisition",
                "description": "Acquire malware samples from affected endpoints",
                "tool_calls": [
                    ToolCall(tool_name="malware-sandbox.acquire_sample", parameters={}, timeout_seconds=120),
                ],
                "risk_level": RiskLevel.MEDIUM,
                "requires_approval": True,
                "checkpoint_type": CheckpointType.BEFORE_DANGEROUS,
            },
            {
                "name": "Static Analysis",
                "description": "Perform static analysis on acquired samples",
                "tool_calls": [
                    ToolCall(tool_name="malware-sandbox.static_analysis", parameters={}, timeout_seconds=60),
                    ToolCall(tool_name="malware-sandbox.yara_scan", parameters={}, timeout_seconds=30),
                ],
                "depends_on": ["Sample Acquisition"],
                "risk_level": RiskLevel.LOW,
            },
            {
                "name": "Dynamic Analysis",
                "description": "Execute samples in sandbox for behavioral analysis",
                "tool_calls": [
                    ToolCall(tool_name="malware-sandbox.dynamic_analysis", parameters={}, timeout_seconds=300),
                ],
                "depends_on": ["Static Analysis"],
                "risk_level": RiskLevel.HIGH,
                "requires_approval": True,
                "checkpoint_type": CheckpointType.BEFORE_DANGEROUS,
            },
            {
                "name": "Network Indicators",
                "description": "Extract network indicators from malware analysis",
                "tool_calls": [
                    ToolCall(tool_name="osint-social-intel.domain_lookup", parameters={}, timeout_seconds=30),
                    ToolCall(tool_name="osint-social-intel.ip_reputation", parameters={}, timeout_seconds=30),
                ],
                "depends_on": ["Dynamic Analysis"],
                "risk_level": RiskLevel.LOW,
            },
            {
                "name": "Correlation & Spreading",
                "description": "Correlate findings and identify lateral movement",
                "tool_calls": [
                    ToolCall(tool_name="evidence-correlation.graph_analysis", parameters={}, timeout_seconds=60),
                    ToolCall(tool_name="evidence-correlation.temporal_analysis", parameters={}, timeout_seconds=60),
                ],
                "depends_on": ["Network Indicators"],
                "risk_level": RiskLevel.MEDIUM,
            },
            {
                "name": "Impact Assessment",
                "description": "Assess business impact and recommend containment",
                "tool_calls": [
                    ToolCall(tool_name="predictive-analytics.risk_scoring", parameters={}, timeout_seconds=30),
                ],
                "depends_on": ["Correlation & Spreading"],
                "risk_level": RiskLevel.LOW,
                "requires_approval": True,
                "checkpoint_type": CheckpointType.BEFORE_FINAL_REPORT,
            },
        ],
    },
    InvestigationType.PHISHING_CAMPAIGN: {
        "description": "Automated phishing campaign investigation from email analysis to infrastructure takedown",
        "estimated_minutes": 30,
        "steps": [
            {
                "name": "Email Header Analysis",
                "description": "Extract and analyze email headers for spoofing and routing",
                "tool_calls": [
                    ToolCall(tool_name="osint-social-intel.email_header_parse", parameters={}, timeout_seconds=30),
                ],
                "risk_level": RiskLevel.LOW,
            },
            {
                "name": "URL & Attachment Analysis",
                "description": "Extract and analyze URLs and attachments from phishing email",
                "tool_calls": [
                    ToolCall(tool_name="malware-sandbox.url_scan", parameters={}, timeout_seconds=60),
                    ToolCall(tool_name="malware-sandbox.attachment_analysis", parameters={}, timeout_seconds=60),
                ],
                "depends_on": ["Email Header Analysis"],
                "risk_level": RiskLevel.MEDIUM,
            },
            {
                "name": "Infrastructure Recon",
                "description": "Reconnaissance on phishing infrastructure (domains, IPs, hosting)",
                "tool_calls": [
                    ToolCall(tool_name="osint-social-intel.domain_whois", parameters={}, timeout_seconds=30),
                    ToolCall(tool_name="darkweb-intel.check_breach_data", parameters={}, timeout_seconds=30),
                ],
                "depends_on": ["URL & Attachment Analysis"],
                "risk_level": RiskLevel.LOW,
            },
            {
                "name": "Impact & Reporting",
                "description": "Determine affected users and generate report",
                "tool_calls": [
                    ToolCall(tool_name="cyber-psychology.target_profiling", parameters={}, timeout_seconds=30),
                ],
                "depends_on": ["Infrastructure Recon"],
                "risk_level": RiskLevel.LOW,
                "requires_approval": True,
                "checkpoint_type": CheckpointType.BEFORE_FINAL_REPORT,
            },
        ],
    },
    InvestigationType.INSIDER_THREAT: {
        "description": "Automated insider threat investigation using behavioral analytics and data access patterns",
        "estimated_minutes": 60,
        "steps": [
            {
                "name": "User Context Collection",
                "description": "Gather user role, access patterns, and historical behavior",
                "tool_calls": [
                    ToolCall(tool_name="cyber-psychology.behavioral_profile", parameters={}, timeout_seconds=30),
                ],
                "risk_level": RiskLevel.LOW,
            },
            {
                "name": "Data Access Audit",
                "description": "Audit data access logs and identify anomalies",
                "tool_calls": [
                    ToolCall(tool_name="evidence-correlation.temporal_analysis", parameters={}, timeout_seconds=60),
                ],
                "depends_on": ["User Context Collection"],
                "risk_level": RiskLevel.MEDIUM,
            },
            {
                "name": "Communication Analysis",
                "description": "Analyze communication patterns for exfiltration signals",
                "tool_calls": [
                    ToolCall(tool_name="mobile-iot-forensics.communication_analysis", parameters={}, timeout_seconds=60),
                    ToolCall(tool_name="cyber-psychology.linguistic_analysis", parameters={}, timeout_seconds=30),
                ],
                "depends_on": ["Data Access Audit"],
                "risk_level": RiskLevel.HIGH,
                "requires_approval": True,
                "checkpoint_type": CheckpointType.BEFORE_DATA_SHARING,
            },
            {
                "name": "Evidence Correlation",
                "description": "Correlate all findings for insider threat pattern",
                "tool_calls": [
                    ToolCall(tool_name="evidence-correlation.pattern_analysis", parameters={}, timeout_seconds=60),
                    ToolCall(tool_name="predictive-analytics.risk_scoring", parameters={}, timeout_seconds=30),
                ],
                "depends_on": ["Communication Analysis"],
                "risk_level": RiskLevel.MEDIUM,
            },
            {
                "name": "Report Generation",
                "description": "Generate insider threat report with chain of custody",
                "tool_calls": [],
                "depends_on": ["Evidence Correlation"],
                "risk_level": RiskLevel.LOW,
                "requires_approval": True,
                "checkpoint_type": CheckpointType.BEFORE_FINAL_REPORT,
            },
        ],
    },
    InvestigationType.APT_INVESTIGATION: {
        "description": "Advanced persistent threat investigation across multiple kill-chain phases",
        "estimated_minutes": 120,
        "steps": [
            {
                "name": "Initial Access Analysis",
                "description": "Identify initial compromise vector and entry point",
                "tool_calls": [
                    ToolCall(tool_name="malware-sandbox.vector_analysis", parameters={}, timeout_seconds=60),
                ],
                "risk_level": RiskLevel.MEDIUM,
            },
            {
                "name": "Persistence Mechanism Discovery",
                "description": "Identify persistence mechanisms used by threat actor",
                "tool_calls": [
                    ToolCall(tool_name="mobile-iot-forensics.process_audit", parameters={}, timeout_seconds=60),
                    ToolCall(tool_name="malware-sandbox.persistence_check", parameters={}, timeout_seconds=60),
                ],
                "depends_on": ["Initial Access Analysis"],
                "risk_level": RiskLevel.HIGH,
                "requires_approval": True,
                "checkpoint_type": CheckpointType.BEFORE_DANGEROUS,
            },
            {
                "name": "C2 Infrastructure Mapping",
                "description": "Map command and control infrastructure",
                "tool_calls": [
                    ToolCall(tool_name="osint-social-intel.c2_tracking", parameters={}, timeout_seconds=60),
                    ToolCall(tool_name="darkweb-intel.threat_actor_profiling", parameters={}, timeout_seconds=60),
                ],
                "depends_on": ["Persistence Mechanism Discovery"],
                "risk_level": RiskLevel.MEDIUM,
            },
            {
                "name": "Lateral Movement Analysis",
                "description": "Trace lateral movement across the environment",
                "tool_calls": [
                    ToolCall(tool_name="evidence-correlation.graph_analysis", parameters={"depth": "full"}, timeout_seconds=120),
                    ToolCall(tool_name="mobile-iot-forensics.network_flows", parameters={}, timeout_seconds=60),
                ],
                "depends_on": ["C2 Infrastructure Mapping"],
                "risk_level": RiskLevel.HIGH,
            },
            {
                "name": "Data Exfiltration Assessment",
                "description": "Assess data exfiltration scope and impact",
                "tool_calls": [
                    ToolCall(tool_name="predictive-analytics.impact_forecast", parameters={}, timeout_seconds=60),
                    ToolCall(tool_name="evidence-correlation.temporal_analysis", parameters={"window": "exfiltration"}, timeout_seconds=60),
                ],
                "depends_on": ["Lateral Movement Analysis"],
                "risk_level": RiskLevel.CRITICAL,
                "requires_approval": True,
                "checkpoint_type": CheckpointType.BEFORE_DATA_SHARING,
            },
            {
                "name": "Final APT Report",
                "description": "Generate comprehensive APT investigation report",
                "tool_calls": [],
                "depends_on": ["Data Exfiltration Assessment"],
                "risk_level": RiskLevel.LOW,
                "requires_approval": True,
                "checkpoint_type": CheckpointType.BEFORE_FINAL_REPORT,
            },
        ],
    },
    InvestigationType.DATA_BREACH: {
        "description": "Automated data breach investigation: scope, impact, and notification",
        "estimated_minutes": 45,
        "steps": [
            {
                "name": "Breach Scope Assessment",
                "description": "Determine scope of data breach",
                "tool_calls": [
                    ToolCall(tool_name="evidence-correlation.entity_correlation", parameters={}, timeout_seconds=60),
                ],
                "risk_level": RiskLevel.MEDIUM,
            },
            {
                "name": "Data Access Audit",
                "description": "Audit who accessed what and when",
                "tool_calls": [
                    ToolCall(tool_name="mobile-iot-forensics.access_log_analysis", parameters={}, timeout_seconds=60),
                    ToolCall(tool_name="evidence-correlation.temporal_analysis", parameters={"window_size": 86400}, timeout_seconds=60),
                ],
                "depends_on": ["Breach Scope Assessment"],
                "risk_level": RiskLevel.HIGH,
            },
            {
                "name": "Exfiltration Path Analysis",
                "description": "Trace data exfiltration paths and destinations",
                "tool_calls": [
                    ToolCall(tool_name="osint-social-intel.data_exfil_tracking", parameters={}, timeout_seconds=60),
                    ToolCall(tool_name="darkweb-intel.breach_monitoring", parameters={}, timeout_seconds=60),
                ],
                "depends_on": ["Data Access Audit"],
                "risk_level": RiskLevel.CRITICAL,
                "requires_approval": True,
                "checkpoint_type": CheckpointType.BEFORE_DATA_SHARING,
            },
            {
                "name": "Impact Quantification",
                "description": "Quantify business and regulatory impact",
                "tool_calls": [
                    ToolCall(tool_name="predictive-analytics.risk_scoring", parameters={}, timeout_seconds=30),
                ],
                "depends_on": ["Exfiltration Path Analysis"],
                "risk_level": RiskLevel.HIGH,
            },
            {
                "name": "Notification & Remediation Plan",
                "description": "Generate breach notification and remediation recommendations",
                "tool_calls": [],
                "depends_on": ["Impact Quantification"],
                "risk_level": RiskLevel.LOW,
                "requires_approval": True,
                "checkpoint_type": CheckpointType.BEFORE_FINAL_REPORT,
            },
        ],
    },
}


class InvestigationPlanner:
    def __init__(self, llm_endpoint: Optional[str] = None, llm_api_key: Optional[str] = None):
        self._llm_endpoint = llm_endpoint
        self._llm_api_key = llm_api_key

    async def create_plan(
        self,
        case_context: CaseContext,
        plan_id: Optional[str] = None,
    ) -> InvestigationPlan:
        inv_type = case_context.investigation_type
        template = INVESTIGATION_TEMPLATES.get(inv_type)

        if template is None:
            return await self._generate_custom_plan(case_context, plan_id)

        steps = []
        for i, step_def in enumerate(template["steps"]):
            step_id = f"step_{uuid.uuid4().hex[:12]}"
            deps = []
            for dep_name in step_def.get("depends_on", []):
                for existing in steps:
                    if existing.name == dep_name:
                        deps.append(existing.step_id)
                        break

            step = InvestigationStep(
                step_id=step_id,
                name=step_def["name"],
                description=step_def["description"],
                tool_calls=step_def.get("tool_calls", []),
                depends_on=deps,
                status=StepStatus.PENDING,
                risk_level=step_def.get("risk_level", RiskLevel.LOW),
                requires_approval=step_def.get("requires_approval", False),
                checkpoint_type=step_def.get("checkpoint_type"),
                metadata={"step_order": i, "template": inv_type.value},
            )
            steps.append(step)

        risk_assessment = self._assess_risks(steps)

        return InvestigationPlan(
            plan_id=plan_id or f"plan_{uuid.uuid4().hex[:12]}",
            investigation_type=inv_type,
            case_id=case_context.case_id,
            description=template["description"],
            steps=steps,
            risk_assessment=risk_assessment,
            estimated_duration_minutes=template["estimated_minutes"],
            metadata={
                "source": "template",
                "template_type": inv_type.value,
                "case_title": case_context.title,
            },
        )

    async def _generate_custom_plan(
        self,
        case_context: CaseContext,
        plan_id: Optional[str] = None,
    ) -> InvestigationPlan:
        if self._llm_endpoint:
            return await self._llm_plan(case_context, plan_id)

        return self._rule_based_plan(case_context, plan_id)

    def _rule_based_plan(
        self,
        case_context: CaseContext,
        plan_id: Optional[str] = None,
    ) -> InvestigationPlan:
        steps: list[InvestigationStep] = []
        evidence_map: dict[str, list[str]] = {}
        for item in case_context.evidence_items:
            etype = item.get("type", "other")
            evidence_map.setdefault(etype, []).append(item.get("id", ""))

        step_order = [
            ("Initial Triage", RiskLevel.LOW, False, None, []),
            ("Evidence Acquisition", RiskLevel.LOW, False, None, []),
            ("Preliminary Analysis", RiskLevel.MEDIUM, False, None, []),
        ]

        if "file" in evidence_map or "binary" in evidence_map:
            step_order.append(("Static File Analysis", RiskLevel.MEDIUM, False, None, []))
            step_order.append(("Dynamic File Analysis", RiskLevel.HIGH, True, CheckpointType.BEFORE_DANGEROUS, []))
        if "network" in evidence_map or "domain" in evidence_map or "ip_address" in evidence_map:
            step_order.append(("Network Intelligence Gathering", RiskLevel.MEDIUM, False, None, []))
        if "email" in evidence_map:
            step_order.append(("Email & Communication Analysis", RiskLevel.MEDIUM, False, None, []))
        if "image" in evidence_map or "video" in evidence_map or "audio" in evidence_map:
            step_order.append(("Media Forensics Analysis", RiskLevel.MEDIUM, False, None, []))

        step_order.append(("Cross-Module Correlation", RiskLevel.LOW, False, None, []))
        step_order.append(("Findings Consolidation", RiskLevel.LOW, True, CheckpointType.BEFORE_FINAL_REPORT, []))

        previous_ids: list[str] = []
        for name, risk, requires_approval, checkpoint, _ in step_order:
            step_id = f"step_{uuid.uuid4().hex[:12]}"
            step = InvestigationStep(
                step_id=step_id,
                name=name,
                description=f"Automated step: {name}",
                tool_calls=[],
                depends_on=list(previous_ids),
                status=StepStatus.PENDING,
                risk_level=risk,
                requires_approval=requires_approval,
                checkpoint_type=checkpoint,
                metadata={"step_order": len(steps)},
            )
            steps.append(step)
            previous_ids.append(step_id)

        risk_assessment = self._assess_risks(steps)

        return InvestigationPlan(
            plan_id=plan_id or f"plan_{uuid.uuid4().hex[:12]}",
            investigation_type=InvestigationType.CUSTOM,
            case_id=case_context.case_id,
            description=f"Custom investigation: {case_context.title}",
            steps=steps,
            risk_assessment=risk_assessment,
            estimated_duration_minutes=len(steps) * 10,
            metadata={
                "source": "rule_based",
                "case_title": case_context.title,
                "evidence_types": list(evidence_map.keys()),
            },
        )

    async def _llm_plan(
        self,
        case_context: CaseContext,
        plan_id: Optional[str] = None,
    ) -> InvestigationPlan:
        logger.warning("LLM planning requested but not fully implemented; falling back to rule-based")
        return self._rule_based_plan(case_context, plan_id)

    def _assess_risks(self, steps: list[InvestigationStep]) -> dict[str, Any]:
        risk_counts: dict[str, int] = {}
        high_risk_steps: list[str] = []
        for step in steps:
            level = step.risk_level.value
            risk_counts[level] = risk_counts.get(level, 0) + 1
            if step.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                high_risk_steps.append(step.name)

        return {
            "risk_summary": risk_counts,
            "high_risk_count": len(high_risk_steps),
            "high_risk_steps": high_risk_steps,
            "approval_required_count": sum(1 for s in steps if s.requires_approval),
            "total_steps": len(steps),
        }

    def dynamic_replan(
        self,
        current_plan: InvestigationPlan,
        completed_step_id: str,
        results: dict[str, Any],
    ) -> InvestigationPlan:
        logger.info("Dynamic re-planning after step %s", completed_step_id)
        completed_idx = -1
        for i, s in enumerate(current_plan.steps):
            if s.step_id == completed_step_id:
                completed_idx = i
                break

        if completed_idx < 0:
            return current_plan

        new_steps: list[InvestigationStep] = []
        for i, step in enumerate(current_plan.steps):
            if i <= completed_idx:
                new_steps.append(step)
                continue

            if self._should_skip_step(step, results):
                step.status = StepStatus.SKIPPED
                step.metadata["skipped_reason"] = "No longer relevant based on previous results"
                new_steps.append(step)
            else:
                current_plan_deps = step.depends_on
                new_deps = [d for d in current_plan_deps if d != completed_step_id] + [completed_step_id]
                step.depends_on = new_deps
                new_steps.append(step)

        if self._should_add_steps(results):
            gap_steps = self._generate_gap_steps(results)
            new_steps.extend(gap_steps)

        current_plan.steps = new_steps
        current_plan.estimated_duration_minutes = len(new_steps) * 10
        return current_plan

    def _should_skip_step(self, step: InvestigationStep, results: dict[str, Any]) -> bool:
        if "no_malware_found" in results and "malware" in step.name.lower():
            return True
        if "no_network_indicators" in results and "network" in step.name.lower():
            return True
        return False

    def _should_add_steps(self, results: dict[str, Any]) -> bool:
        return bool(results.get("additional_analysis_needed"))

    def _generate_gap_steps(self, results: dict[str, Any]) -> list[InvestigationStep]:
        gaps = results.get("gaps", [])
        new_steps: list[InvestigationStep] = []
        for gap in gaps:
            step = InvestigationStep(
                step_id=f"step_{uuid.uuid4().hex[:12]}",
                name=f"Follow-up: {gap}",
                description=f"Additional investigation step for gap: {gap}",
                tool_calls=[],
                depends_on=[],
                status=StepStatus.PENDING,
                risk_level=RiskLevel.LOW,
                metadata={"gap_follow_up": True, "original_gap": gap},
            )
            new_steps.append(step)
        return new_steps

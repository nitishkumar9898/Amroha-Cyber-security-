import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Body

from models.investigation_types import (
    AgentState,
    CaseContext,
    HumanFeedback,
    InvestigationPlan,
    InvestigationResult,
    InvestigationStatus,
    InvestigationSummary,
    InvestigationType,
    StepStatus,
    PlanResponse,
    StartInvestigationResponse,
    StepExecutionResponse,
    ToolCall,
)
from engine.planner import InvestigationPlanner
from engine.tool_registry import ToolRegistry
from engine.executor import InvestigationExecutor, InvestigationRunner
from engine.reflector import ReflectionEngine

MODULE_ID = "autonomous-agent"
MODULE_VERSION = "1.0.0"

logger = logging.getLogger(__name__)

SENTINEL_URL = os.getenv("SENTINEL_CORE_URL", "http://backend:3000/api/v1")
SENTINEL_API_KEY = os.getenv("SENTINEL_API_KEY", "")

tool_registry = ToolRegistry()
planner = InvestigationPlanner()
executor = InvestigationExecutor(tool_registry)
runner = InvestigationRunner(tool_registry, executor)
reflector = ReflectionEngine()

app = FastAPI(
    title="Autonomous Investigation Agent",
    description="LangGraph-style autonomous agent for planning and executing "
                "forensic investigations across all CyberThreatForge modules. "
                "Features DAG-based workflow, tool calling, reflection, "
                "and human-in-the-loop checkpoints.",
    version=MODULE_VERSION,
)


@app.on_event("startup")
async def startup():
    _register_default_tools()
    logger.info("Autonomous Agent module started, %d tools registered", len(tool_registry.list_tools()))


def _register_default_tools():
    async def _list_indicators(case_id: str = ""):
        return {"findings": [], "artifacts": [], "confidence": 0.8}

    async def _risk_score(case_id: str = "", data: Optional[dict] = None):
        return {"findings": [{"type": "risk_assessment", "score": 0.5}], "confidence": 0.7}

    async def _graph_analysis(evidence_ids: Optional[list] = None, depth: str = "basic"):
        return {"findings": [{"type": "graph_analysis", "depth": depth}], "confidence": 0.75}

    async def _temporal_analysis(events: Optional[list] = None, window_size: int = 3600):
        return {"findings": [{"type": "temporal_analysis", "windows_analyzed": 1}], "confidence": 0.7}

    tool_registry.register_tool(
        "sentinel.list_indicators", "List investigation indicators from SentinelCore", _list_indicators,
        parameters={"case_id": {"type": "string"}}, module_id="sentinel",
    )
    tool_registry.register_tool(
        "predictive-analytics.risk_scoring", "Score risk based on findings", _risk_score,
        parameters={"case_id": {"type": "string"}, "data": {"type": "object"}}, module_id="predictive-analytics",
    )
    tool_registry.register_tool(
        "evidence-correlation.graph_analysis", "Run graph-based evidence correlation", _graph_analysis,
        parameters={"evidence_ids": {"type": "array"}, "depth": {"type": "string"}}, module_id="evidence-correlation",
    )
    tool_registry.register_tool(
        "evidence-correlation.temporal_analysis", "Run temporal link analysis", _temporal_analysis,
        parameters={"events": {"type": "array"}, "window_size": {"type": "integer"}}, module_id="evidence-correlation",
    )


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_state(investigation_id: str) -> AgentState:
    state = runner.get_state(investigation_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Investigation not found: {investigation_id}")
    return state


@app.get("/health")
async def health():
    return {
        "module": MODULE_ID,
        "version": MODULE_VERSION,
        "status": "healthy",
        "timestamp": _ts(),
        "tools_registered": len(tool_registry.list_tools()),
        "active_investigations": len(runner.list_active()),
    }


@app.post("/investigation/start", response_model=StartInvestigationResponse)
async def start_investigation(context: CaseContext = Body(...)):
    inv_id = f"inv_{_id()}"
    plan = await planner.create_plan(context, plan_id=f"plan_{_id()}")
    state = await runner.start_investigation(plan, inv_id)

    state.context["evidence_types"] = [e.get("type", "") for e in context.evidence_items]
    state.context["targets"] = context.targets
    state.context["priority"] = context.priority
    state.context["tags"] = context.tags

    return StartInvestigationResponse(
        investigation_id=inv_id,
        status=state.status,
        message=f"Investigation created with {len(plan.steps)} steps",
    )


@app.post("/investigation/step", response_model=StepExecutionResponse)
async def execute_step(
    investigation_id: str = Body(..., embed=True),
    user_clearance: str = Body("analyst", embed=True),
):
    state = _get_state(investigation_id)
    if state.status == InvestigationStatus.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=409,
            detail="Investigation is awaiting approval. Use /approve or /reject first.",
        )

    step, result = await runner.execute_next_step(investigation_id, user_clearance)

    if step is None and result is None:
        return StepExecutionResponse(
            step_id="",
            status=StepStatus.COMPLETED,
            message="Investigation completed - all steps executed",
        )

    if step and step.requires_approval and result is None:
        return StepExecutionResponse(
            step_id=step.step_id,
            status=StepStatus.AWAITING_APPROVAL,
            requires_approval=True,
            message=f"Step '{step.name}' requires human approval",
        )

    return StepExecutionResponse(
        step_id=step.step_id if step else "",
        status=step.status if step else StepStatus.COMPLETED,
        result=step.result if step else None,
        message=f"Step '{step.name if step else ''}' completed" if step else "Investigation completed",
    )


@app.post("/investigation/plan", response_model=PlanResponse)
async def generate_plan(context: CaseContext = Body(...)):
    plan = await planner.create_plan(context, plan_id=f"plan_{_id()}")
    return PlanResponse(
        plan_id=plan.plan_id,
        investigation_type=plan.investigation_type,
        steps=plan.steps,
        risk_assessment=plan.risk_assessment,
        estimated_duration_minutes=plan.estimated_duration_minutes,
        message=f"Plan generated with {len(plan.steps)} steps",
    )


@app.get("/investigation/{investigation_id}/status")
async def get_status(investigation_id: str):
    state = _get_state(investigation_id)
    plan = state.plan
    current_step = None
    if plan and 0 <= state.current_step_index < len(plan.steps):
        current_step = plan.steps[state.current_step_index]

    pending = None
    if state.pending_approval:
        pending = state.pending_approval.model_dump()

    return {
        "investigation_id": investigation_id,
        "status": state.status.value,
        "current_step_index": state.current_step_index,
        "total_steps": len(plan.steps) if plan else 0,
        "completed_steps": sum(
            1 for s in (plan.steps if plan else [])
            if s.status in ("completed", "approved", "skipped", "rejected")
        ),
        "current_step": current_step.model_dump() if current_step else None,
        "pending_approval": pending,
        "errors": state.errors,
        "created_at": state.created_at,
        "updated_at": state.updated_at,
        "completed_at": state.completed_at,
    }


@app.post("/investigation/{investigation_id}/approve")
async def approve_step(
    investigation_id: str,
    feedback: str = Body("", embed=True),
    modifications: Optional[dict[str, Any]] = Body(None, embed=True),
    user_clearance: str = Body("analyst", embed=True),
):
    state = _get_state(investigation_id)
    if state.status != InvestigationStatus.AWAITING_APPROVAL:
        raise HTTPException(status_code=409, detail="No step is currently awaiting approval")

    step, result = await runner.approve_step(investigation_id, feedback, modifications, user_clearance)

    return {
        "step_id": step.step_id if step else "",
        "status": StepStatus.APPROVED.value,
        "message": f"Step '{step.name if step else ''}' approved and executed",
        "result": result.model_dump() if result else None,
    }


@app.post("/investigation/{investigation_id}/reject")
async def reject_step(
    investigation_id: str,
    feedback: str = Body(..., embed=True),
):
    state = _get_state(investigation_id)
    if state.status != InvestigationStatus.AWAITING_APPROVAL:
        raise HTTPException(status_code=409, detail="No step is currently awaiting approval")

    step = await runner.reject_step(investigation_id, feedback)

    return {
        "step_id": step.step_id,
        "status": StepStatus.REJECTED.value,
        "message": f"Step '{step.name}' rejected: {feedback}",
    }


@app.get("/investigation/{investigation_id}/results")
async def get_results(investigation_id: str):
    state = _get_state(investigation_id)
    plan = state.plan

    steps_summary = []
    if plan:
        for s in plan.steps:
            result = state.results.get(s.step_id)
            steps_summary.append({
                "step_id": s.step_id,
                "name": s.name,
                "status": s.status.value,
                "risk_level": s.risk_level.value,
                "result": result.model_dump() if result else None,
                "completed_at": s.completed_at,
            })

    all_findings = []
    for r in state.results.values():
        all_findings.extend(r.findings)

    reflection = reflector.analyze_results(state)
    gaps = reflector.identify_gaps(state)
    suggestions = reflector.suggest_follow_up(state)
    confidence = reflector.assess_confidence(state)

    summary = reflector.generate_summary(state)

    return {
        "investigation_id": investigation_id,
        "status": state.status.value,
        "steps": steps_summary,
        "total_findings": len(all_findings),
        "findings": all_findings,
        "reflection": {
            "analysis": reflection,
            "gaps": gaps,
            "suggestions": suggestions,
            "confidence": confidence,
        },
        "summary": summary.model_dump(),
        "context": state.context,
        "errors": state.errors,
        "created_at": state.created_at,
        "completed_at": state.completed_at,
    }


@app.post("/investigation/{investigation_id}/feedback")
async def provide_feedback(investigation_id: str, feedback: HumanFeedback = Body(...)):
    state = _get_state(investigation_id)

    step = None
    if state.plan:
        for s in state.plan.steps:
            if s.step_id == feedback.step_id:
                step = s
                break

    if step is None:
        raise HTTPException(status_code=404, detail=f"Step not found: {feedback.step_id}")

    if "feedback" not in step.metadata:
        step.metadata["feedback"] = []
    step.metadata["feedback"].append({
        "approved": feedback.approved,
        "feedback": feedback.feedback,
        "provided_by": feedback.provided_by,
        "provided_at": feedback.provided_at,
    })

    if feedback.modifications:
        step.tool_calls = [
            ToolCall(
                tool_name=tc.tool_name,
                parameters={**tc.parameters, **(feedback.modifications.get(tc.tool_name, {}))},
                timeout_seconds=tc.timeout_seconds,
                retry_count=tc.retry_count,
            )
            for tc in step.tool_calls
        ]

    state.updated_at = _ts()

    return {
        "message": f"Feedback recorded for step '{step.name}'",
        "step_id": feedback.step_id,
    }




import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from models.investigation_types import (
    InvestigationPlan,
    InvestigationStep,
    InvestigationResult,
    ToolCall,
    ToolResult,
    StepStatus,
    AgentState,
    InvestigationStatus,
    CheckpointType,
)
from engine.tool_registry import ToolRegistry
from engine.workflow_graph import WorkflowGraph

logger = logging.getLogger(__name__)


class InvestigationExecutor:
    def __init__(self, tool_registry: ToolRegistry):
        self._tool_registry = tool_registry
        self._progress_handlers: list[Any] = []

    def on_progress(self, handler: Any) -> None:
        self._progress_handlers.append(handler)

    async def _notify_progress(self, step: InvestigationStep, state: AgentState) -> None:
        for handler in self._progress_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(step, state)
                else:
                    handler(step, state)
            except Exception as e:
                logger.warning("Progress handler error: %s", e)

    async def execute_step(
        self,
        step: InvestigationStep,
        context: dict[str, Any],
        user_clearance: str = "analyst",
    ) -> InvestigationResult:
        step.status = StepStatus.IN_PROGRESS
        start_time = time.monotonic()

        findings: list[dict[str, Any]] = []
        artifacts: list[str] = []
        gaps: list[str] = []
        follow_up_steps: list[str] = []
        max_confidence = 0.0
        custody_events: list[dict[str, Any]] = []

        for tool_call in step.tool_calls:
            result = await self._execute_tool(tool_call, user_clearance, context)
            custody_events.append({
                "tool": tool_call.tool_name,
                "success": result.success,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            if result.success:
                data = result.data
                if "findings" in data:
                    findings.extend(data["findings"])
                if "artifacts" in data:
                    artifacts.extend(data["artifacts"])
                if "gaps" in data:
                    gaps.extend(data["gaps"])
                if "follow_up" in data:
                    follow_up_steps.extend(data["follow_up"])
                max_confidence = max(max_confidence, result.confidence)
                context.update({tool_call.tool_name: data})
            else:
                error_entry = {
                    "tool": tool_call.tool_name,
                    "error": result.error,
                    "step": step.name,
                }
                findings.append({"type": "error", "detail": error_entry})

        duration_ms = int((time.monotonic() - start_time) * 1000)
        step.result = ToolResult(
            tool_name=",".join(tc.tool_name for tc in step.tool_calls),
            success=len(findings) > 0 or not step.tool_calls,
            data={
                "findings": findings,
                "artifacts": artifacts,
                "gaps": gaps,
                "follow_up": follow_up_steps,
            },
            execution_time_ms=duration_ms,
            confidence=max_confidence if findings else 0.0,
        )
        step.status = StepStatus.COMPLETED
        step.completed_at = datetime.now(timezone.utc).isoformat()

        return InvestigationResult(
            step_id=step.step_id,
            findings=findings,
            artifacts=artifacts,
            summary=self._generate_step_summary(step),
            confidence=max_confidence,
            gaps=gaps,
            follow_up_steps=follow_up_steps,
            chain_of_custody=custody_events,
        )

    async def _execute_tool(
        self,
        tool_call: ToolCall,
        user_clearance: str,
        context: dict[str, Any],
    ) -> ToolResult:
        enriched_params = dict(tool_call.parameters)
        for key, value in enriched_params.items():
            if isinstance(value, str) and value.startswith("$context."):
                ctx_key = value[9:]
                enriched_params[key] = context.get(ctx_key, value)

        try:
            raw = await self._tool_registry.execute_tool(
                tool_name=tool_call.tool_name,
                parameters=enriched_params,
                user_clearance=user_clearance,
                timeout=tool_call.timeout_seconds,
                retries=tool_call.retry_count,
            )

            return ToolResult(
                tool_name=tool_call.tool_name,
                success=raw.get("success", False),
                data=raw.get("data", {}),
                error=raw.get("error"),
                execution_time_ms=raw.get("execution_time_ms", 0),
                confidence=raw.get("data", {}).get("confidence", 1.0),
            )
        except Exception as e:
            logger.exception("Unexpected error executing tool %s", tool_call.tool_name)
            return ToolResult(
                tool_name=tool_call.tool_name,
                success=False,
                error=str(e),
                execution_time_ms=0,
                confidence=0.0,
            )

    async def execute_parallel_steps(
        self,
        steps: list[InvestigationStep],
        context: dict[str, Any],
        user_clearance: str = "analyst",
    ) -> dict[str, InvestigationResult]:
        tasks = {s.step_id: self.execute_step(s, context, user_clearance) for s in steps}
        results = {}
        for sid, task in tasks.items():
            results[sid] = await task
        return results

    def _generate_step_summary(self, step: InvestigationStep) -> str:
        if not step.tool_calls:
            return f"Step '{step.name}' completed with no tool calls."
        tool_names = [t.tool_name for t in step.tool_calls]
        return f"Executed {len(step.tool_calls)} tool(s): {', '.join(tool_names)}"

    def check_approval_required(self, step: InvestigationStep) -> bool:
        return step.requires_approval

    def check_checkpoint(self, step: InvestigationStep) -> Optional[CheckpointType]:
        return step.checkpoint_type


class InvestigationRunner:
    def __init__(self, tool_registry: ToolRegistry, executor: InvestigationExecutor):
        self._tool_registry = tool_registry
        self._executor = executor
        self._active_investigations: dict[str, AgentState] = {}
        self._lock = asyncio.Lock()

    async def start_investigation(
        self,
        plan: InvestigationPlan,
        investigation_id: str,
    ) -> AgentState:
        state = AgentState(
            investigation_id=investigation_id,
            plan=plan,
            current_step_index=0,
            status=InvestigationStatus.PLANNING,
            context={
                "case_id": plan.case_id,
                "investigation_type": plan.investigation_type.value,
                "plan_id": plan.plan_id,
            },
        )
        state.status = InvestigationStatus.IN_PROGRESS
        async with self._lock:
            self._active_investigations[investigation_id] = state
        return state

    async def execute_next_step(
        self,
        investigation_id: str,
        user_clearance: str = "analyst",
    ) -> tuple[Optional[InvestigationStep], Optional[InvestigationResult]]:
        async with self._lock:
            state = self._active_investigations.get(investigation_id)
            if state is None:
                raise ValueError(f"Investigation not found: {investigation_id}")

            if state.status in (InvestigationStatus.COMPLETED, InvestigationStatus.FAILED, InvestigationStatus.CANCELLED):
                raise ValueError(f"Investigation is already {state.status.value}")

            plan = state.plan
            if plan is None:
                raise ValueError("Investigation has no plan")

        step = await self._resolve_next_step(state)
        if step is None:
            async with self._lock:
                state.status = InvestigationStatus.COMPLETED
                state.completed_at = datetime.now(timezone.utc).isoformat()
            return None, None

        if step.requires_approval:
            async with self._lock:
                step.status = StepStatus.AWAITING_APPROVAL
                state.status = InvestigationStatus.AWAITING_APPROVAL
                state.pending_approval = step
                state.updated_at = datetime.now(timezone.utc).isoformat()
            return step, None

        result = await self._executor.execute_step(step, state.context, user_clearance)

        async with self._lock:
            state.results[step.step_id] = result
            state.current_step_index = self._find_step_index(plan, step.step_id) + 1
            state.updated_at = datetime.now(timezone.utc).isoformat()
            await self._notify_step_completed(state, step, result)

        return step, result

    async def approve_step(
        self,
        investigation_id: str,
        feedback: str = "",
        modifications: Optional[dict[str, Any]] = None,
        user_clearance: str = "analyst",
    ) -> tuple[Optional[InvestigationStep], Optional[InvestigationResult]]:
        async with self._lock:
            state = self._active_investigations.get(investigation_id)
            if state is None:
                raise ValueError(f"Investigation not found: {investigation_id}")

            pending = state.pending_approval
            if pending is None:
                raise ValueError("No step pending approval")

            if modifications:
                for tc in pending.tool_calls:
                    tc.parameters.update(modifications)
                pending.metadata["modified"] = True

            pending.status = StepStatus.APPROVED

        result = await self._executor.execute_step(pending, state.context, user_clearance)

        async with self._lock:
            state.results[pending.step_id] = result
            state.pending_approval = None
            state.status = InvestigationStatus.IN_PROGRESS
            state.current_step_index = self._find_step_index(state.plan, pending.step_id) + 1
            state.updated_at = datetime.now(timezone.utc).isoformat()
            await self._notify_step_completed(state, pending, result)

        return pending, result

    async def reject_step(
        self,
        investigation_id: str,
        feedback: str,
    ) -> InvestigationStep:
        async with self._lock:
            state = self._active_investigations.get(investigation_id)
            if state is None:
                raise ValueError(f"Investigation not found: {investigation_id}")

            pending = state.pending_approval
            if pending is None:
                raise ValueError("No step pending approval")

            pending.status = StepStatus.REJECTED
            pending.metadata["rejection_feedback"] = feedback
            state.pending_approval = None
            state.status = InvestigationStatus.IN_PROGRESS
            state.current_step_index = self._find_step_index(state.plan, pending.step_id) + 1
            state.updated_at = datetime.now(timezone.utc).isoformat()

        return pending

    async def _resolve_next_step(self, state: AgentState) -> Optional[InvestigationStep]:
        plan = state.plan
        if plan is None:
            return None

        if state.current_step_index >= len(plan.steps):
            return None

        for i in range(state.current_step_index, len(plan.steps)):
            step = plan.steps[i]
            if step.status in (StepStatus.COMPLETED, StepStatus.SKIPPED, StepStatus.REJECTED):
                continue

            deps_met = all(
                dep_status(plan, dep) in (StepStatus.COMPLETED, StepStatus.SKIPPED)
                for dep in step.depends_on
            )
            if deps_met:
                return step

        all_done = all(
            s.status in (StepStatus.COMPLETED, StepStatus.SKIPPED, StepStatus.REJECTED)
            for s in plan.steps
        )
        return None if all_done else None

    def _find_step_index(self, plan: InvestigationPlan, step_id: str) -> int:
        for i, s in enumerate(plan.steps):
            if s.step_id == step_id:
                return i
        return -1

    async def _notify_step_completed(
        self, state: AgentState, step: InvestigationStep, result: InvestigationResult
    ) -> None:
        logger.info(
            "Step %s (%s) completed: %d findings, confidence=%.2f",
            step.step_id, step.name, len(result.findings), result.confidence,
        )

    def get_state(self, investigation_id: str) -> Optional[AgentState]:
        return self._active_investigations.get(investigation_id)

    def list_active(self) -> dict[str, AgentState]:
        return dict(self._active_investigations)


def dep_status(plan: InvestigationPlan, step_id: str) -> StepStatus:
    for s in plan.steps:
        if s.step_id == step_id:
            return s.status
    return StepStatus.SKIPPED

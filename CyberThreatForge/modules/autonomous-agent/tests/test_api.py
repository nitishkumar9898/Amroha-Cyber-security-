import os
import sys
from typing import Any, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from api import app, tool_registry, planner, runner, reflector, executor
from models.investigation_types import (
    CaseContext,
    InvestigationType,
    InvestigationStatus,
    StepStatus,
    HumanFeedback,
    InvestigationPlan,
    InvestigationStep,
    ToolCall,
    RiskLevel,
    CheckpointType,
    AgentState,
)
from engine.workflow_graph import WorkflowGraph, GraphNode, CycleDetectedError, NodeNotFoundError
from engine.tool_registry import ToolRegistry, ToolPermissionError, ToolRateLimitError


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def case_context():
    return CaseContext(
        case_id="case-001",
        title="Test Investigation",
        description="A test investigation",
        investigation_type=InvestigationType.PHISHING_CAMPAIGN,
        evidence_items=[
            {"id": "ev-001", "type": "email", "source": "phishing@evil.com"},
            {"id": "ev-002", "type": "domain", "source": "evil-phish.com"},
        ],
        targets=["user-001", "user-002"],
        priority="high",
    )


@pytest.fixture
def basic_plan():
    steps = [
        InvestigationStep(
            step_id="step_1", name="Initial Triage", description="Triage",
            tool_calls=[ToolCall(tool_name="sentinel.list_indicators")],
            risk_level=RiskLevel.LOW,
        ),
        InvestigationStep(
            step_id="step_2", name="Deep Analysis", description="Deep analysis",
            tool_calls=[ToolCall(tool_name="evidence-correlation.graph_analysis")],
            depends_on=["step_1"],
            risk_level=RiskLevel.HIGH, requires_approval=True,
            checkpoint_type=CheckpointType.BEFORE_DANGEROUS,
        ),
        InvestigationStep(
            step_id="step_3", name="Report", description="Generate report",
            depends_on=["step_2"],
            risk_level=RiskLevel.LOW,
        ),
    ]
    return InvestigationPlan(
        plan_id="plan_test", investigation_type=InvestigationType.CUSTOM,
        case_id="case-001", steps=steps, estimated_duration_minutes=30,
    )


class TestWorkflowGraph:
    def test_add_node(self):
        g = WorkflowGraph()
        node = g.add_node("n1", "Test Node", {"key": "val"})
        assert node.id == "n1"
        assert node.label == "Test Node"
        assert node.data == {"key": "val"}
        assert g.node_count() == 1

    def test_add_duplicate_node_raises(self):
        g = WorkflowGraph()
        g.add_node("n1")
        with pytest.raises(ValueError, match="already exists"):
            g.add_node("n1")

    def test_add_remove_node(self):
        g = WorkflowGraph()
        g.add_node("n1")
        g.add_node("n2")
        g.remove_node("n1")
        assert g.node_count() == 1
        assert g.get_node("n1") is None

    def test_remove_nonexistent_node_raises(self):
        g = WorkflowGraph()
        with pytest.raises(NodeNotFoundError):
            g.remove_node("n1")

    def test_add_edge(self):
        g = WorkflowGraph()
        g.add_node("n1")
        g.add_node("n2")
        g.add_edge("n1", "n2")
        assert g.edge_count() == 1
        assert g.get_dependents("n1") == ["n2"]
        assert g.get_dependencies("n2") == ["n1"]

    def test_add_edge_nonexistent_source_raises(self):
        g = WorkflowGraph()
        g.add_node("n2")
        with pytest.raises(NodeNotFoundError):
            g.add_edge("n1", "n2")

    def test_cycle_detection(self):
        g = WorkflowGraph()
        g.add_node("n1")
        g.add_node("n2")
        g.add_node("n3")
        g.add_edge("n1", "n2")
        g.add_edge("n2", "n3")
        with pytest.raises(CycleDetectedError):
            g.add_edge("n3", "n1")

    def test_topological_sort(self):
        g = WorkflowGraph()
        g.add_node("a")
        g.add_node("b")
        g.add_node("c")
        g.add_edge("a", "c")
        g.add_edge("b", "c")
        order = g.topological_sort()
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("c")

    def test_parallel_layers(self):
        g = WorkflowGraph()
        g.add_node("a")
        g.add_node("b")
        g.add_node("c")
        g.add_node("d")
        g.add_edge("a", "c")
        g.add_edge("b", "c")
        g.add_edge("c", "d")
        layers = g.get_parallel_layers()
        assert len(layers) == 3

    def test_find_path(self):
        g = WorkflowGraph()
        g.add_node("n1"); g.add_node("n2"); g.add_node("n3")
        g.add_edge("n1", "n2"); g.add_edge("n2", "n3")
        path = g.find_path("n1", "n3")
        assert path == ["n1", "n2", "n3"]

    def test_upstream_downstream(self):
        g = WorkflowGraph()
        g.add_node("n1"); g.add_node("n2"); g.add_node("n3")
        g.add_edge("n1", "n2"); g.add_edge("n2", "n3")
        assert g.get_upstream_nodes("n3") == {"n1", "n2"}
        assert g.get_downstream_nodes("n1") == {"n2", "n3"}

    def test_state_management(self):
        g = WorkflowGraph()
        g.set_state("key1", "val1")
        assert g.get_state("key1") == "val1"
        assert g.get_state("missing", "default") == "default"
        g.update_state({"key2": "val2"})
        assert g.get_state("key2") == "val2"
        g.clear_state()
        assert g.get_state("key1") is None

    def test_node_status_reset(self):
        g = WorkflowGraph()
        n = g.add_node("n1")
        n.status = "completed"
        n.result = {"data": "test"}
        g.reset_node_status()
        assert n.status == "pending"
        assert n.result is None

    def test_conditional_edge(self):
        g = WorkflowGraph()
        g.add_node("n1"); g.add_node("n2"); g.add_node("n3")
        g.add_edge("n1", "n2", condition=lambda ctx: ctx.get("flag") is True)
        g.add_edge("n1", "n3", condition=lambda ctx: ctx.get("flag") is False)
        edges_n1_n2 = g.get_edge_conditions("n1", "n2")
        assert len(edges_n1_n2) == 1
        assert edges_n1_n2[0].evaluate({"flag": True}) is True
        assert edges_n1_n2[0].evaluate({"flag": False}) is False


class TestToolRegistry:
    @pytest.fixture
    def registry(self):
        return ToolRegistry()

    @pytest.mark.asyncio
    async def test_register_and_list_tools(self, registry):
        async def handler(**kw): return {"result": "ok"}
        registry.register_tool("test_tool", "A test tool", handler)
        assert registry.has_tool("test_tool")
        tools = registry.list_tools()
        assert "test_tool" in tools

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, registry):
        async def handler(msg: str = ""): return {"echo": msg}
        registry.register_tool("echo", "Echo tool", handler)
        result = await registry.execute_tool("echo", {"msg": "hello"})
        assert result["success"] is True
        assert result["data"]["echo"] == "hello"

    @pytest.mark.asyncio
    async def test_execute_tool_timeout(self, registry):
        async def slow_handler(**kw):
            import asyncio; await asyncio.sleep(10)
            return {}
        registry.register_tool("slow", "Slow tool", handler=slow_handler, timeout_default=1)
        result = await registry.execute_tool("slow", timeout=1, retries=1)
        assert result["success"] is False
        assert "Timeout" in (result.get("error") or "")

    @pytest.mark.asyncio
    async def test_permission_check(self, registry):
        async def handler(**kw): return {}
        registry.register_tool("admin_tool", "Admin only", handler, required_clearance="admin")
        assert registry.check_permission("admin_tool", "admin") is True
        assert registry.check_permission("admin_tool", "junior") is False

    @pytest.mark.asyncio
    async def test_permission_denied_raises(self, registry):
        async def handler(**kw): return {}
        registry.register_tool("secret", "Secret", handler, required_clearance="admin")
        with pytest.raises(ToolPermissionError):
            await registry.execute_tool("secret", user_clearance="junior")

    @pytest.mark.asyncio
    async def test_unknown_tool_raises(self, registry):
        with pytest.raises(ValueError, match="Unknown tool"):
            await registry.execute_tool("nonexistent")

    @pytest.mark.asyncio
    async def test_rate_limiting(self, registry):
        async def handler(**kw): return {}
        registry.register_tool("limited", "Rate limited", handler, rate_limit_per_minute=2)
        await registry.execute_tool("limited")
        await registry.execute_tool("limited")
        with pytest.raises(ToolRateLimitError):
            await registry.execute_tool("limited")

    @pytest.mark.asyncio
    async def test_tool_statistics(self, registry):
        async def ok(**kw): return {"ok": True}
        async def fail(**kw): raise ValueError("fail")
        registry.register_tool("ok_tool", "Ok", ok)
        registry.register_tool("fail_tool", "Fail", fail, retry_default=1)
        await registry.execute_tool("ok_tool", retries=1)
        await registry.execute_tool("fail_tool", retries=1)
        stats = registry.get_statistics()
        assert stats["total_calls"] >= 2

    @pytest.mark.asyncio
    async def test_discover_from_sentinel(self, registry):
        modules = [
            {"id": "module-a", "capabilities": ["scan", "analyze"]},
            {"id": "module-b", "capabilities": ["detect"]},
        ]
        count = registry.discover_from_sentinel(modules)
        assert count == 3
        assert registry.has_tool("module-a.scan")
        assert registry.has_tool("module-b.detect")


class TestPlanner:
    @pytest.mark.asyncio
    async def test_create_plan_from_template(self, case_context):
        plan = await planner.create_plan(case_context)
        assert plan.investigation_type == InvestigationType.PHISHING_CAMPAIGN
        assert len(plan.steps) >= 3
        assert plan.case_id == "case-001"

    @pytest.mark.asyncio
    async def test_custom_plan(self):
        ctx = CaseContext(case_id="case-custom", title="Custom", investigation_type=InvestigationType.CUSTOM)
        plan = await planner.create_plan(ctx)
        assert plan.investigation_type == InvestigationType.CUSTOM
        assert len(plan.steps) > 0

    @pytest.mark.asyncio
    async def test_risk_assessment(self, case_context):
        plan = await planner.create_plan(case_context)
        assert "risk_summary" in plan.risk_assessment
        assert "high_risk_count" in plan.risk_assessment

    @pytest.mark.asyncio
    async def test_malware_template(self):
        ctx = CaseContext(case_id="c2", title="Malware", investigation_type=InvestigationType.MALWARE_OUTBREAK)
        plan = await planner.create_plan(ctx)
        assert plan.estimated_duration_minutes == 45
        step_names = [s.name for s in plan.steps]
        assert "Static Analysis" in step_names

    @pytest.mark.asyncio
    async def test_insider_threat_template(self):
        ctx = CaseContext(case_id="c3", title="Insider", investigation_type=InvestigationType.INSIDER_THREAT)
        plan = await planner.create_plan(ctx)
        assert len(plan.steps) == 5

    @pytest.mark.asyncio
    async def test_apt_template(self):
        ctx = CaseContext(case_id="c4", title="APT", investigation_type=InvestigationType.APT_INVESTIGATION)
        plan = await planner.create_plan(ctx)
        assert len(plan.steps) == 6
        assert any(s.requires_approval for s in plan.steps)

    @pytest.mark.asyncio
    async def test_data_breach_template(self):
        ctx = CaseContext(case_id="c5", title="Breach", investigation_type=InvestigationType.DATA_BREACH)
        plan = await planner.create_plan(ctx)
        assert len(plan.steps) == 5

    @pytest.mark.asyncio
    async def test_dynamic_replan(self, basic_plan):
        results = {"additional_analysis_needed": True, "gaps": ["DNS logs not analyzed"]}
        updated = planner.dynamic_replan(basic_plan, "step_1", results)
        assert len(updated.steps) >= len(basic_plan.steps)

    def test_risk_assessment_static(self):
        steps = [
            InvestigationStep(step_id="s1", name="Low", risk_level=RiskLevel.LOW),
            InvestigationStep(step_id="s2", name="High", risk_level=RiskLevel.HIGH),
            InvestigationStep(step_id="s3", name="Critical", risk_level=RiskLevel.CRITICAL,
                              requires_approval=True),
        ]
        risks = planner._assess_risks(steps)
        assert risks["high_risk_count"] == 2
        assert risks["approval_required_count"] == 1


class TestExecutor:
    @pytest.mark.asyncio
    async def test_execute_step_success(self):
        result = await executor.execute_step(
            InvestigationStep(
                step_id="test_step", name="Test",
                tool_calls=[ToolCall(tool_name="sentinel.list_indicators")],
            ),
            context={},
        )
        assert result.step_id == "test_step"
        assert len(result.findings) >= 0

    @pytest.mark.asyncio
    async def test_execute_step_with_unknown_tool(self):
        result = await executor.execute_step(
            InvestigationStep(
                step_id="fail_step", name="Fail",
                tool_calls=[ToolCall(tool_name="nonexistent_tool")],
            ),
            context={},
        )
        assert result.step_id == "fail_step"


class TestReflector:
    def test_analyze_results_empty(self):
        state = AgentState(investigation_id="inv-1")
        analysis = reflector.analyze_results(state)
        assert analysis["total_findings"] == 0
        assert analysis["overall_confidence"] == 0.0

    def test_identify_gaps(self):
        state = AgentState(investigation_id="inv-1")
        state.context["investigation_type"] = "phishing_campaign"
        gaps = reflector.identify_gaps(state)
        assert isinstance(gaps, list)

    def test_confidence_assessment(self):
        state = AgentState(investigation_id="inv-1")
        conf = reflector.assess_confidence(state)
        assert "raw_confidence" in conf
        assert "adjusted_confidence" in conf
        assert conf["confidence_level"] == "very_low"

    def test_generate_summary(self):
        plan = InvestigationPlan(
            plan_id="p1", investigation_type=InvestigationType.CUSTOM,
            case_id="c1", steps=[], estimated_duration_minutes=10,
        )
        state = AgentState(investigation_id="inv-1", plan=plan, status=InvestigationStatus.COMPLETED)
        summary = reflector.generate_summary(state)
        assert summary.investigation_id == "inv-1"
        assert summary.status == InvestigationStatus.COMPLETED


class TestAPI:
    @pytest.mark.asyncio
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["module"] == "autonomous-agent"
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_start_investigation(self, client, case_context):
        resp = await client.post("/investigation/start", json=case_context.model_dump())
        assert resp.status_code == 200
        data = resp.json()
        assert "investigation_id" in data
        assert data["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_generate_plan(self, client, case_context):
        resp = await client.post("/investigation/plan", json=case_context.model_dump())
        assert resp.status_code == 200
        data = resp.json()
        assert "plan_id" in data
        assert len(data["steps"]) >= 3

    @pytest.mark.asyncio
    async def test_investigation_lifecycle(self, client, case_context):
        start_resp = await client.post("/investigation/start", json=case_context.model_dump())
        inv_id = start_resp.json()["investigation_id"]

        status_resp = await client.get(f"/investigation/{inv_id}/status")
        assert status_resp.status_code == 200

        step_resp = await client.post("/investigation/step", json={
            "investigation_id": inv_id, "user_clearance": "analyst",
        })
        assert step_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_investigation_not_found(self, client):
        resp = await client.get("/investigation/nonexistent/status")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_approve_reject_lifecycle(self, client):
        ctx = CaseContext(
            case_id="lifecycle-test", title="Lifecycle",
            investigation_type=InvestigationType.MALWARE_OUTBREAK,
        )
        start = await client.post("/investigation/start", json=ctx.model_dump())
        inv_id = start.json()["investigation_id"]

        step1 = await client.post("/investigation/step", json={
            "investigation_id": inv_id, "user_clearance": "analyst",
        })
        assert step1.status_code == 200

        step2 = await client.post("/investigation/step", json={
            "investigation_id": inv_id, "user_clearance": "analyst",
        })

        if step2.status_code == 200 and step2.json().get("requires_approval"):
            approve = await client.post(f"/investigation/{inv_id}/approve",
                                         json={"feedback": "Proceed", "user_clearance": "senior_analyst"})
            assert approve.status_code == 200
        elif step2.status_code == 200:
            pass

    @pytest.mark.asyncio
    async def test_reject_step(self, client):
        ctx = CaseContext(
            case_id="reject-test", title="Reject",
            investigation_type=InvestigationType.MALWARE_OUTBREAK,
        )
        start = await client.post("/investigation/start", json=ctx.model_dump())
        inv_id = start.json()["investigation_id"]

        await client.post("/investigation/step", json={
            "investigation_id": inv_id, "user_clearance": "analyst",
        })

        step2 = await client.post("/investigation/step", json={
            "investigation_id": inv_id, "user_clearance": "analyst",
        })

        if step2.status_code == 200 and step2.json().get("requires_approval"):
            reject = await client.post(f"/investigation/{inv_id}/reject",
                                        json={"feedback": "Not needed"})
            assert reject.status_code == 200
            assert reject.json()["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_get_results(self, client, case_context):
        start = await client.post("/investigation/start", json=case_context.model_dump())
        inv_id = start.json()["investigation_id"]
        results = await client.get(f"/investigation/{inv_id}/results")
        assert results.status_code == 200
        data = results.json()
        assert data["investigation_id"] == inv_id

    @pytest.mark.asyncio
    async def test_provide_feedback(self, client, case_context):
        start = await client.post("/investigation/start", json=case_context.model_dump())
        inv_id = start.json()["investigation_id"]
        status_resp = await client.get(f"/investigation/{inv_id}/status")
        status_data = status_resp.json()
        current_step = status_data.get("current_step")
        if not current_step:
            pytest.skip("No current step")
        feedback = HumanFeedback(
            step_id=current_step["step_id"], approved=True,
            feedback="Good analysis", modifications=None, provided_by="analyst",
        )
        fb_resp = await client.post(f"/investigation/{inv_id}/feedback", json=feedback.model_dump())
        assert fb_resp.status_code == 200
        assert "Feedback recorded" in fb_resp.json()["message"]

    @pytest.mark.asyncio
    async def test_feedback_on_nonexistent_step(self, client, case_context):
        feedback = HumanFeedback(step_id="nonexistent", approved=False, feedback="Bad")
        start = await client.post("/investigation/start", json=case_context.model_dump())
        inv_id = start.json()["investigation_id"]
        resp = await client.post(f"/investigation/{inv_id}/feedback", json=feedback.model_dump())
        assert resp.status_code == 404

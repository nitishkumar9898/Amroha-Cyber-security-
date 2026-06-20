import pytest
from app.modules.responseforge.playbook_engine import playbook_engine
from app.modules.responseforge.containment_advisor import containment_advisor
from app.modules.responseforge.forensics_analyzer import forensics_analyzer
from app.modules.responseforge.self_healing_bridge import self_healing_bridge
from app.modules.responseforge.incident_reporter import incident_reporter

@pytest.mark.asyncio
async def test_playbook_engine():
    playbook = await playbook_engine.generate_playbook("ransomware", {})
    assert len(playbook) > 0
    assert playbook[0]["action"] == "isolate_network"

@pytest.mark.asyncio
async def test_containment_advisor():
    telemetry = {"high_cpu_usage": True, "unauthorized_processes": True, "host_id": "server-01"}
    suggestions = await containment_advisor.suggest_containment_actions(telemetry)
    assert len(suggestions) > 0
    assert suggestions[0]["action"] == "isolate_host"

@pytest.mark.asyncio
async def test_forensics_analyzer():
    artifacts = {"logs": ["some logs"]}
    analysis = await forensics_analyzer.analyze_artifacts("inc-123", artifacts)
    assert analysis["incident_id"] == "inc-123"
    assert "timeline" in analysis

@pytest.mark.asyncio
async def test_self_healing_bridge():
    actions = [{"action": "isolate_host", "target": "server-01"}]
    result = await self_healing_bridge.execute_actions(actions)
    assert result["status"] == "completed"
    assert len(result["executed_actions"]) == 1

@pytest.mark.asyncio
async def test_incident_reporter():
    data = {"incident_id": "inc-123", "root_cause": "Phishing"}
    report = await incident_reporter.generate_report(data)
    assert "inc-123" in report
    assert "Phishing" in report

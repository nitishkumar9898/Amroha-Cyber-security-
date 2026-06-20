import json
import os
import sys
from pathlib import Path

# Ensure the project root is on PYTHONPATH for imports
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

import pytest

from compliance_engine import engine, load_rules_into_engine
from compliance_engine.admissibility_checker import is_admissible
from compliance_engine.monitor import record_event, get_audit_log
from compliance_engine.report_generator import render_report
from compliance_engine.models.evidence import Evidence

@pytest.fixture(autouse=True)
def reset_engine():
    """Reset the global engine before each test."""
    engine.rules.clear()
    load_rules_into_engine(engine)
    yield
    engine.rules.clear()

def test_rules_loaded():
    """Verify that rules from compliance.yaml are loaded into the engine."""
    rule_names = {rule.name for rule in engine.rules}
    assert "ITAct2000_Section5" in rule_names
    assert "DPDP2023_Consent" in rule_names

def test_admissibility_checks():
    """Test admissibility logic for various evidence scenarios."""
    # Fully admissible evidence
    e1 = Evidence(
        id="e1",
        description="Forensic capture",
        collection_method="forensic_tool",
        source="file.pcap",
        timestamp="2026-06-19T12:00:00Z",
        has_consent=True,
    )
    assert is_admissible(e1.__dict__) is True

    # Missing consent
    e2 = Evidence(
        id="e2",
        description="Manual note",
        collection_method="manual",
        source="notes.txt",
        timestamp="2026-06-19T13:00:00Z",
        has_consent=False,
    )
    assert is_admissible(e2.__dict__) is False

    # Wrong collection method
    e3 = Evidence(
        id="e3",
        description="API dump",
        collection_method="api",
        source="endpoint.json",
        timestamp="2026-06-19T14:00:00Z",
        has_consent=True,
    )
    assert is_admissible(e3.__dict__) is False

def test_audit_trail_and_monitor():
    """Record an event and ensure it appears in the audit log."""
    # Clean any existing log file
    log_path = Path(__file__).resolve().parents[3] / "backend" / "app" / "compliance_engine" / "audit_log.jsonl"
    if log_path.exists():
        log_path.unlink()

    # Record an event
    record_event("test_event", {"key": "value"})

    # Retrieve audit log
    log_entries = get_audit_log()
    assert len(log_entries) == 1
    entry = log_entries[0]
    assert entry["action"] == "test_event"
    assert entry["metadata"]["key"] == "value"
    assert "timestamp" in entry
    assert "signature" in entry

def test_report_rendering():
    """Render a compliance report using the Jinja2 template."""
    context = {
        "generated_at": "2026-06-19T15:00:00Z",
        "results": {"ITAct2000_Section5": True, "DPDP2023_Consent": False},
    }
    html = render_report(context, template_name="compliance_report.html")
    assert "<html" in html
    assert "Compliance Evaluation Report" in html
    assert "ITAct2000_Section5" in html
    assert "False" in html

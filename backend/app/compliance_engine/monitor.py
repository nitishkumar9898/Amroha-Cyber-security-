# compliance_engine/monitor.py
"""Simple event monitor for real‑time compliance checks.
Modules can call `record_event` to log actions and trigger rule evaluation.
"""
from typing import Dict, Any
from .audit_trail import log_action
from .rule_engine import RuleEngine, ComplianceRule

# Global rule engine instance (populate elsewhere with rules from config)
engine = RuleEngine()

def record_event(action: str, metadata: Dict[str, Any]):
    """Record an event and evaluate compliance rules.
    Args:
        action: Description of the event.
        metadata: Additional context data.
    """
    # Log to immutable audit trail
    log_action(action, metadata)
    # Evaluate all rules (placeholder – in real system, use context)
    context = {"action": action, **metadata}
    results = engine.evaluate_all(context)
    # For now, just print results (could be stored or trigger alerts)
    print(f"Compliance evaluation for {action}: {results}")
from .config_loader import load_rules_into_engine
# Load compliance rules at startup
load_rules_into_engine(engine)

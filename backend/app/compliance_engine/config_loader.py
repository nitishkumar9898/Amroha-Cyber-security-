# compliance_engine/config_loader.py
"""Load compliance configuration and register rules.
This module reads ``config/compliance.yaml`` and populates the global
:class:`~compliance_engine.monitor.engine` with :class:`ComplianceRule`
instances.
"""
import os
import yaml
from .rule_engine import ComplianceRule, RuleEngine
from .admissibility_checker import is_admissible

# Path to the YAML config – relative to project root (APP_ROOT)
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
CONFIG_PATH = os.path.join(APP_ROOT, "config", "compliance.yaml")

def _load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _build_rule(rule_cfg: dict) -> ComplianceRule:
    name = rule_cfg.get("name")
    description = rule_cfg.get("description", "")
    # Simple mapping: if rule name matches known checks, bind the appropriate function
    if name == "ITAct2000_Section5":
        condition = lambda ctx: is_admissible({
            "collection_method": ctx.get("collection_method"),
            "has_consent": ctx.get("has_consent", False)
        })
    elif name == "DPDP2023_Consent":
        condition = lambda ctx: ctx.get("has_consent", False)
    else:
        # Default: always True (placeholder)
        condition = lambda ctx: True
    return ComplianceRule(name=name, description=description, condition=condition)

def load_rules_into_engine(engine: RuleEngine):
    """Parse ``compliance.yaml`` and register enabled rules.
    Args:
        engine: The global RuleEngine instance from ``monitor``.
    """
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Compliance config not found at {CONFIG_PATH}")
    cfg = _load_yaml(CONFIG_PATH)
    for rule_cfg in cfg.get("rules", []):
        if rule_cfg.get("enabled", False):
            rule = _build_rule(rule_cfg)
            engine.add_rule(rule)

# Load rules at import time so the monitor is ready
if __name__ == "__main__":
    # Simple manual test
    from .monitor import engine
    load_rules_into_engine(engine)
    print(f"Loaded rules: {[r.name for r in engine.rules]}")

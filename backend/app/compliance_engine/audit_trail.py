# compliance_engine/audit_trail.py
"""Simple immutable audit trail implementation.
Writes JSON lines to a log file; each entry is timestamped and signed (placeholder).
In production replace with blockchain or append‑only ledger.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any

LOG_FILE = os.path.join(os.path.dirname(__file__), "audit_log.jsonl")

def _write_entry(entry: Dict[str, Any]):
    entry.setdefault('timestamp', datetime.utcnow().isoformat() + 'Z')
    # Placeholder for digital signature / hash chaining
    entry['signature'] = 'placeholder-signature'
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def log_action(action: str, metadata: Dict[str, Any]):
    """Record an action in the immutable audit trail.
    Args:
        action: Short description of what happened.
        metadata: Arbitrary key/value data about the action.
    """
    _write_entry({"action": action, "metadata": metadata})

def get_audit_log() -> list:
    """Read the full audit log as a list of dicts (for testing/reporting)."""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

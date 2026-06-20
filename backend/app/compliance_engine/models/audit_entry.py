# compliance_engine/models/audit_entry.py
"""Data model for an audit trail entry."""

from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class AuditEntry:
    timestamp: str  # ISO‑8601 UTC
    action: str
    metadata: Dict[str, Any]
    signature: str = "placeholder-signature"

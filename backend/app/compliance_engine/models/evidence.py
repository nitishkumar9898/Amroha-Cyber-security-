# compliance_engine/models/evidence.py
"""Data model for a piece of digital evidence used in compliance checks."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class Evidence:
    id: str
    description: str
    collection_method: str  # e.g., "forensic_tool", "manual", "api"
    source: str  # e.g., file path, URL, device ID
    timestamp: str  # ISO‑8601 UTC string
    metadata: Optional[Dict[str, Any]] = None
    has_consent: bool = False  # DPDP requirement flag

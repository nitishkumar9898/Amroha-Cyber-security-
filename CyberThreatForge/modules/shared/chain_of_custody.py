import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from .evidence_types import CustodyEvent, ChainOfCustodyStatus


class ChainOfCustodyManager:
    def __init__(self):
        self._events: list[CustodyEvent] = []

    def record(
        self,
        action: str,
        actor: str,
        module: str,
        data: Optional[dict] = None,
        previous_hash: Optional[str] = None,
    ) -> CustodyEvent:
        ts = datetime.now(timezone.utc).isoformat()
        payload = json.dumps({
            "action": action,
            "actor": actor,
            "module": module,
            "timestamp": ts,
            "data": data or {},
            "previous_hash": previous_hash or "",
        }, sort_keys=True, default=str)
        hash_value = hashlib.sha256(payload.encode()).hexdigest()

        event = CustodyEvent(
            timestamp=ts,
            action=action,
            actor=actor,
            module=module,
            hash=hash_value,
            notes=json.dumps(data) if data else "",
        )
        self._events.append(event)
        return event

    def verify_chain(self) -> tuple[bool, list[str]]:
        issues = []
        for i, event in enumerate(self._events):
            expected_hash = hashlib.sha256(
                json.dumps({
                    "action": event.action,
                    "actor": event.actor,
                    "module": event.module,
                    "timestamp": event.timestamp,
                    "data": event.notes,
                    "previous_hash": self._events[i - 1].hash if i > 0 else "",
                }, sort_keys=True, default=str).encode()
            ).hexdigest()
            if event.hash != expected_hash:
                issues.append(f"Hash mismatch at index {i}: {event.action}")
        return len(issues) == 0, issues

    def to_dict(self) -> list[dict]:
        return [
            {
                "timestamp": e.timestamp,
                "action": e.action,
                "actor": e.actor,
                "module": e.module,
                "hash": e.hash,
                "notes": e.notes,
            }
            for e in self._events
        ]

    @classmethod
    def from_dict(cls, events: list[dict]) -> "ChainOfCustodyManager":
        mgr = cls()
        mgr._events = [
            CustodyEvent(
                timestamp=e["timestamp"],
                action=e["action"],
                actor=e["actor"],
                module=e["module"],
                hash=e["hash"],
                notes=e.get("notes", ""),
            )
            for e in events
        ]
        return mgr

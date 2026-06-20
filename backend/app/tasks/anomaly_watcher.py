# backend/app/tasks/anomaly_watcher.py
"""Background task that watches for anomaly events.
For the prototype, it reads from a simple in‑memory queue (list) that can be
populated via the /api/auto_defend/trigger endpoint.
"""

import asyncio
from typing import List, Dict

from ..services.auto_defend_service import AutoDefendService

# Simple in‑memory event queue (would be a message broker in production)
_event_queue: List[Dict] = []

def enqueue_event(event: Dict) -> None:
    """Add an event to the queue (called by the API endpoint)."""
    _event_queue.append(event)

async def anomaly_watcher() -> None:
    """Continuously poll the queue for high‑severity events.
    When an event passes `detect_anomaly`, `handle_anomaly` is invoked.
    """
    while True:
        if _event_queue:
            event = _event_queue.pop(0)
            if AutoDefendService.detect_anomaly(event):
                # Fire and forget – handling is synchronous but fast
                AutoDefendService.handle_anomaly(event)
        await asyncio.sleep(1)  # poll interval

import json
import datetime
from typing import List, Dict, Any

# Simple heuristic detection for CAN bus data
def parse_can_message(raw_data: str) -> List[Dict[str, Any]]:
    """Parse raw CAN data (JSON string) into a list of message dicts.
    Expected format: [{"id": int, "data": "hex", "timestamp": "ISO"}, ...]
    """
    try:
        messages = json.loads(raw_data)
        return messages if isinstance(messages, list) else []
    except json.JSONDecodeError:
        return []

def heuristic_malware_detection(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Very simple heuristic: flag if any message ID is in a suspicious range (0x700-0x7FF).
    Returns a dict with severity (0-100) and description.
    """
    suspicious = [msg for msg in messages if 0x700 <= int(msg.get('id', 0)) <= 0x7FF]
    severity = min(100, len(suspicious) * 10)
    description = f"Detected {len(suspicious)} suspicious CAN IDs out of {len(messages)} messages."
    return {"severity": severity, "description": description, "suspicious_count": len(suspicious)}

def simulate_swarm_attack(num_vehicles: int = 5, duration_seconds: int = 10) -> Dict[str, Any]:
    """Generate synthetic CAN traffic for a swarm of vehicles.
    Returns summary stats.
    """
    total_messages = num_vehicles * duration_seconds * 20  # 20 msgs/sec per vehicle
    result = {
        "scenario_name": f"SwarmAttack_{num_vehicles}v_{duration_seconds}s",
        "parameters": {"num_vehicles": num_vehicles, "duration_seconds": duration_seconds},
        "generated_messages": total_messages,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    return result

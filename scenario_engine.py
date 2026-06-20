"""
Scenario Engine for CyberThreatForge
Orchestrates training scenario states, threat timelines, and simulated phases.
"""

import json
from datetime import datetime, timedelta

class ScenarioPhase:
    def __init__(self, name, description, trigger_delay_minutes=0):
        self.name = name
        self.description = description
        self.trigger_delay_minutes = trigger_delay_minutes
        self.is_active = False
        self.completed = False

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "trigger_delay_minutes": self.trigger_delay_minutes,
            "is_active": self.is_active,
            "completed": self.completed
        }

class ThreatScenario:
    def __init__(self, scenario_id, name, threat_actor, target_sector):
        self.scenario_id = scenario_id
        self.name = name
        self.threat_actor = threat_actor
        self.target_sector = target_sector
        self.phases = []
        self.start_time = None
        self.status = "PENDING"  # PENDING, RUNNING, COMPLETED

    def add_phase(self, phase: ScenarioPhase):
        self.phases.append(phase)

    def start(self):
        self.start_time = datetime.now()
        self.status = "RUNNING"
        if self.phases:
            self.phases[0].is_active = True

    def update_timeline(self):
        if not self.start_time or self.status != "RUNNING":
            return

        elapsed = datetime.now() - self.start_time
        active_phase_changed = False

        for i, phase in enumerate(self.phases):
            if not phase.completed:
                required_delay = timedelta(minutes=phase.trigger_delay_minutes)
                if elapsed >= required_delay:
                    if not phase.is_active:
                        phase.is_active = True
                        active_phase_changed = True
                    break
        
        # Check if all completed
        if all(phase.completed for phase in self.phases):
            self.status = "COMPLETED"

    def mark_phase_complete(self, phase_name):
        for i, phase in enumerate(self.phases):
            if phase.name == phase_name:
                phase.completed = True
                phase.is_active = False
                # Activate next phase if delay conditions met
                if i + 1 < len(self.phases):
                    self.phases[i + 1].is_active = True
                break
        self.update_timeline()

    def get_status_report(self):
        self.update_timeline()
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "threat_actor": self.threat_actor,
            "target_sector": self.target_sector,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "phases": [p.to_dict() for p in self.phases]
        }

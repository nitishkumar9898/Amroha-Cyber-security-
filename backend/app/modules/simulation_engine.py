# backend/app/modules/simulation_engine.py
"""
Core simulation engine for SimuForge.
Provides scenario generation, adaptive RL agents, and a runner that advances time.
"""
import random
import numpy as np
from typing import List, Dict, Any
from datetime import datetime

# ------------------------------------------------------------
# Helper for mapping simulation ticks to calendar years (2026 + tick)
# ------------------------------------------------------------
def tick_to_year(tick: int) -> int:
    """Map a simulation tick (year offset) to a calendar year."""
    return 2026 + tick

# ------------------------------------------------------------
# Scenario definition
# ------------------------------------------------------------
class Scenario:
    """Container for a generated future cyber‑threat scenario.
    `duration` is in ticks (years). `threats` is a list of threat type strings.
    """
    def __init__(self, name: str, duration: int, threats: List[str]):
        self.name = name
        self.duration = duration
        self.threats = threats
        self.start_year = 2026
        self.end_year = tick_to_year(duration)
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "duration": self.duration,
            "threats": self.threats,
            "start_year": self.start_year,
            "end_year": self.end_year,
            "metadata": self.metadata,
        }

# ------------------------------------------------------------
# Adaptive RL Agent base class
# ------------------------------------------------------------
class AdaptiveAgent:
    """Base class for attacker/defender agents.
    Sub‑classes should implement `step(state)` and `learn(reward)`.
    """
    def __init__(self, agent_id: str, role: str):
        self.agent_id = agent_id
        self.role = role  # "attacker" or "defender"
        self.state = None
        self.policy = None  # placeholder for RL policy object

    def step(self, env_state: Dict[str, Any]) -> Dict[str, Any]:
        """Take an action based on the environment state.
        Returns an action dict.
        """
        raise NotImplementedError

    def learn(self, reward: float, next_state: Dict[str, Any]):
        """Update the internal policy using the received reward.
        """
        raise NotImplementedError

# ------------------------------------------------------------
# Simple placeholder agents (no heavy RL libs for now)
# ------------------------------------------------------------
class RandomAttacker(AdaptiveAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, role="attacker")

    def step(self, env_state: Dict[str, Any]) -> Dict[str, Any]:
        # Choose a random target from the network nodes
        target = random.choice(env_state.get("nodes", []))
        return {"action": "exploit", "target": target}

    def learn(self, reward: float, next_state: Dict[str, Any]):
        # No learning for random agent
        pass

class SimpleDefender(AdaptiveAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, role="defender")

    def step(self, env_state: Dict[str, Any]) -> Dict[str, Any]:
        # Randomly patch a vulnerable node if any exist
        vulnerable = [n for n in env_state.get("nodes", []) if n.get("vulnerable", False)]
        if vulnerable:
            node = random.choice(vulnerable)
            return {"action": "patch", "node": node}
        return {"action": "monitor"}

    def learn(self, reward: float, next_state: Dict[str, Any]):
        pass

# ------------------------------------------------------------
# Simulation runner
# ------------------------------------------------------------
class SimulationRunner:
    """Runs a scenario with a set of agents.
    `agents` is a list of AdaptiveAgent instances.
    `environment` is a mutable dict representing the network state.
    """
    def __init__(self, scenario: Scenario, agents: List[AdaptiveAgent]):
        self.scenario = scenario
        self.agents = agents
        self.current_tick = 0
        # Simple network model: list of nodes with vulnerability flag
        self.environment = {
            "nodes": [{"id": f"node_{i}", "vulnerable": random.random() < 0.3} for i in range(10)],
            "events": [],
        }
        self.history: List[Dict[str, Any]] = []
        self.finished = False
        self.metrics: Dict[str, Any] = {
            "attacker_success": 0,
            "defender_success": 0,
        }

    def step(self):
        """Advance a single simulation tick (year)."""
        if self.finished:
            return
        actions = []
        for agent in self.agents:
            act = agent.step(self.environment)
            actions.append({"agent_id": agent.agent_id, "role": agent.role, "action": act})
        # Simple deterministic outcome evaluation
        for a in actions:
            if a["role"] == "attacker" and a["action"]["action"] == "exploit":
                target = a["action"]["target"]
                if target.get("vulnerable", False):
                    self.metrics["attacker_success"] += 1
                    target["compromised"] = True
            elif a["role"] == "defender" and a["action"]["action"] == "patch":
                node = a["action"]["node"]
                node["vulnerable"] = False
                self.metrics["defender_success"] += 1
        # Record snapshot for this tick
        self.history.append({
            "tick": self.current_tick,
            "year": tick_to_year(self.current_tick),
            "environment": self.environment.copy(),
            "actions": actions,
        })
        self.current_tick += 1
        if self.current_tick >= self.scenario.duration:
            self.finished = True

    def run(self):
        while not self.finished:
            self.step()
        return {
            "scenario": self.scenario.to_dict(),
            "metrics": self.metrics,
            "history": self.history,
        }

# ------------------------------------------------------------
# Scenario generator – simple probabilistic template
# ------------------------------------------------------------
def generate_scenario(name: str = None, duration: int = 30, threat_mix: List[str] = None) -> Scenario:
    if name is None:
        name = f"FutureScenario_{datetime.utcnow().isoformat()}"
    if threat_mix is None:
        threat_mix = random.sample([
            "phishing", "ransomware", "supply_chain", "AI_deepfake", "IoT_botnet",
            "quantum_crypto_break", "zero_day_exploit", "insider_leak"
        ], k=3)
    return Scenario(name=name, duration=duration, threats=threat_mix)

# ------------------------------------------------------------
# What‑if analysis helper (simple deterministic projection)
# ------------------------------------------------------------
def what_if_analysis(base_result: Dict[str, Any], alteration: Dict[str, Any]) -> Dict[str, Any]:
    """Return a projected result if `alteration` were applied.
    `alteration` can contain keys like `"add_agent"`, `"remove_agent"`, or
    `"force_success"` for the attacker.
    """
    import copy
    projected = copy.deepcopy(base_result)
    if alteration.get("force_success"):
        projected["metrics"]["attacker_success"] += alteration["force_success"]
    return projected

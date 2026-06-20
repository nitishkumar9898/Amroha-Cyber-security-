# backend/app/services/simu_forge_service.py
"""
Service layer that bridges FastAPI endpoints with the SimuForge simulation engine.
It provides thin wrappers for scenario generation, simulation execution, status
polling, and what‑if analysis.
"""
from typing import Dict, Any, List
from uuid import uuid4
import asyncio

from ..modules.simulation_engine import (
    generate_scenario,
    SimulationRunner,
    what_if_analysis,
)

# In‑memory store for running simulations – suitable for dev/testing.
# In production this would be replaced by a persisted job queue / database.
_SIMULATION_REGISTRY: Dict[str, Dict[str, Any]] = {}

async def _run_async_simulation(run_id: str, scenario_dict: Dict[str, Any], agents: List[Any]):
    """Background coroutine that executes the simulation and stores the result."""
    scenario = generate_scenario(
        name=scenario_dict.get("name"),
        duration=scenario_dict.get("duration", 30),
        threat_mix=scenario_dict.get("threats"),
    )
    runner = SimulationRunner(scenario=scenario, agents=agents)
    result = runner.run()
    _SIMULATION_REGISTRY[run_id]["status"] = "COMPLETED"
    _SIMULATION_REGISTRY[run_id]["result"] = result

def create_simulation(scenario: Dict[str, Any]) -> str:
    """Create a new simulation run and start it asynchronously.
    Returns a unique run_id that can be used to poll status.
    """
    run_id = str(uuid4())
    # For now we instantiate a simple attacker and defender.
    from ..modules.simulation_engine import RandomAttacker, SimpleDefender
    agents = [RandomAttacker(agent_id="attacker_1"), SimpleDefender(agent_id="defender_1")]
    _SIMULATION_REGISTRY[run_id] = {
        "status": "RUNNING",
        "scenario": scenario,
        "agents": agents,
        "result": None,
    }
    # Schedule background execution – FastAPI will run the event loop.
    asyncio.create_task(_run_async_simulation(run_id, scenario, agents))
    return run_id

def get_simulation_status(run_id: str) -> Dict[str, Any]:
    """Retrieve the current status and, if finished, the result of a simulation."""
    entry = _SIMULATION_REGISTRY.get(run_id)
    if not entry:
        raise ValueError("Simulation run_id not found")
    return {"status": entry["status"], "result": entry.get("result")}

def what_if(run_id: str, alteration: Dict[str, Any]) -> Dict[str, Any]:
    """Perform a what‑if projection on a completed run.
    The `alteration` argument follows the schema of `what_if_analysis`.
    """
    entry = _SIMULATION_REGISTRY.get(run_id)
    if not entry or entry["status"] != "COMPLETED":
        raise ValueError("Simulation must be completed before what‑if analysis")
    base_result = entry["result"]
    return what_if_analysis(base_result, alteration)

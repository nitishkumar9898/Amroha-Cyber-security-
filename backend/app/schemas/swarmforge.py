from pydantic import BaseModel, ConfigDict
from typing import Optional

class SwarmSimRequest(BaseModel):
    target_infrastructure: str
    swarm_size: int
    attack_vector: str

class SwarmSimResult(BaseModel):
    simulation_id: int
    status: str
    initial_coordination_score: float

class AgentBehaviorReport(BaseModel):
    simulation_id: int
    coordination_score: float
    mutation_velocity: float
    predicted_pivot_target: str

class CounterSwarmRequest(BaseModel):
    simulation_id: int
    strategy_used: str # HONEYPOT_DECOY, SIGNAL_JAMMING

class CounterSwarmResult(BaseModel):
    simulation_id: int
    strategy_used: str
    neutralization_percentage: float
    swarm_deactivated: bool

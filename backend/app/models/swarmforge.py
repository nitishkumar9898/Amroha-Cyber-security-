from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class SwarmSimulation(Base):
    __tablename__ = "swarmforge_simulations"

    id = Column(Integer, primary_key=True, index=True)
    target_infrastructure = Column(String)
    swarm_size = Column(Integer)
    attack_vector = Column(String) # DDOS, LATERAL_MOVEMENT, DATA_EXFIL
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AgentMetrics(Base):
    __tablename__ = "swarmforge_metrics"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer)
    coordination_score = Column(Float) # 0.0 to 1.0
    mutation_velocity = Column(Float) # Adapts to defenses
    predicted_pivot_target = Column(String)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

class CounterSwarmDeployment(Base):
    __tablename__ = "swarmforge_counter_swarms"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer)
    strategy_used = Column(String) # HONEYPOT_DECOY, SIGNAL_JAMMING
    neutralization_percentage = Column(Float)
    deployed_at = Column(DateTime, default=datetime.datetime.utcnow)

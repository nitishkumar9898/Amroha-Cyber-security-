from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime

from ..database import Base

class RedTeamScenario(Base):
    __tablename__ = "redteam_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    attack_graph = Column(JSON) # Abstract JSON graph of attack vectors
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("redteam_scenarios.id"))
    status = Column(String, default="PENDING") # PENDING, IN_PROGRESS, COMPLETED
    metrics = Column(JSON) # Post-exercise metrics
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class VulnerabilityFinding(Base):
    __tablename__ = "vulnerability_findings"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("simulation_runs.id"))
    asset_name = Column(String)
    vulnerability_type = Column(String)
    severity = Column(String)
    description = Column(String)
    discovered_at = Column(DateTime, default=datetime.datetime.utcnow)

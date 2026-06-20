from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class GlobalScenario(Base):
    __tablename__ = "omnisimulator_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(String, index=True, unique=True)
    name = Column(String)
    description = Column(String)
    active_modules_count = Column(Integer)
    global_resilience_score = Column(Float, default=100.0)
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ScenarioTimelineEvent(Base):
    __tablename__ = "omnisimulator_timeline"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(String, index=True)
    event_id = Column(String)
    source_module = Column(String)
    event_description = Column(String)
    severity = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class CrossModuleCascade(Base):
    __tablename__ = "omnisimulator_cascades"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(String, index=True)
    source_event_id = Column(String)
    target_module = Column(String)
    cascade_probability = Column(Float)
    impact_description = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

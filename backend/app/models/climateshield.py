from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class InfraAttackSim(Base):
    __tablename__ = "climateshield_infra_sims"

    id = Column(Integer, primary_key=True, index=True)
    infrastructure_type = Column(String, index=True) # POWER, WATER, AGRICULTURE
    weather_event = Column(String) # HEATWAVE, DROUGHT, FLOOD
    cyber_attack_vector = Column(String)
    cascading_impact_score = Column(Float) # 0.0 to 10.0
    simulated_at = Column(DateTime, default=datetime.datetime.utcnow)

class ClimateManipulationSim(Base):
    __tablename__ = "climateshield_geo_sims"

    id = Column(Integer, primary_key=True, index=True)
    manipulation_vector = Column(String) # ROGUE_AEROSOL, CLOUD_SEEDING_HIJACK
    projected_years = Column(Integer) # 50+
    ecological_damage_index = Column(Float)
    economic_impact_trillions = Column(Float)
    simulated_at = Column(DateTime, default=datetime.datetime.utcnow)

class ResiliencePlan(Base):
    __tablename__ = "climateshield_resilience_plans"

    id = Column(Integer, primary_key=True, index=True)
    scenario_trigger = Column(String)
    recovery_strategy = Column(String)
    estimated_recovery_days = Column(Integer)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)

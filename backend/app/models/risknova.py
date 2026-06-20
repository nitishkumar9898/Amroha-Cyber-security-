from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey
import datetime
from ..database import Base

class TechnologyProfile(Base):
    __tablename__ = "risknova_tech_profile"

    id = Column(Integer, primary_key=True, index=True)
    tech_name = Column(String, index=True) # e.g., AI, Quantum, Biotech, Space
    sub_category = Column(String, nullable=True) # e.g., LLM, CRISPR
    adoption_phase = Column(String) # R&D, EarlyAdoption, Mainstream
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

class RiskAssessment(Base):
    __tablename__ = "risknova_assessment"

    id = Column(Integer, primary_key=True, index=True)
    tech_id = Column(Integer, ForeignKey("risknova_tech_profile.id"))
    cyber_risk_score = Column(Float, default=0.0)
    physical_risk_score = Column(Float, default=0.0)
    operational_risk_score = Column(Float, default=0.0)
    composite_score = Column(Float, default=0.0)
    assessment_date = Column(DateTime, default=datetime.datetime.utcnow)

class RiskScenario(Base):
    __tablename__ = "risknova_scenario"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("risknova_assessment.id"))
    scenario_name = Column(String)
    description = Column(String)
    probability = Column(Float)
    impact_level = Column(String) # Low, Medium, High, Critical
    timeframe_years = Column(Integer) # Estimated years until realization

class MitigationRoadmap(Base):
    __tablename__ = "risknova_roadmap"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("risknova_scenario.id"))
    step_order = Column(Integer)
    action_item = Column(String)
    resource_requirement = Column(String) # Low, Medium, High
    status = Column(String, default="Pending")

# backend/app/models/supplychain.py

from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

# Assumes there is a Base declarative class defined in backend/app/models/base.py or similar
# Adjust import as needed for your project structure
from .base import Base

class SupplyChainEntity(Base):
    __tablename__ = "supply_chain_entities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # e.g., "software", "hardware", "vendor"
    version = Column(String, nullable=True)
    provenance_hash = Column(String, nullable=False, unique=True)
    entity_metadata = Column(JSON, nullable=True)

    risk_events = relationship("RiskEvent", back_populates="entity", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="entity", cascade="all, delete-orphan")

class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("supply_chain_entities.id"), nullable=False)
    severity = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    entity = relationship("SupplyChainEntity", back_populates="risk_events")

class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("supply_chain_entities.id"), nullable=False)
    score = Column(Float, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    entity = relationship("SupplyChainEntity", back_populates="anomalies")

class SimulationScenario(Base):
    __tablename__ = "simulation_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    generated_plan = Column(JSON, nullable=False)  # Full mitigation plan JSON
    created_at = Column(DateTime, default=datetime.utcnow)

    # No direct foreign key – the plan may reference many entities; stored as JSON for flexibility

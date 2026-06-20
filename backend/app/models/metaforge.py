from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class PlatformMetric(Base):
    __tablename__ = "metaforge_metrics"

    id = Column(Integer, primary_key=True, index=True)
    source_module = Column(String, index=True) # e.g. QuantumSafe, SpaceGuard
    latency_ms = Column(Float)
    error_rate = Column(Float)
    optimization_suggestion = Column(String)
    logged_at = Column(DateTime, default=datetime.datetime.utcnow)

class EvolutionLog(Base):
    __tablename__ = "metaforge_evolutions"

    id = Column(Integer, primary_key=True, index=True)
    target_module = Column(String)
    current_version = Column(String)
    proposed_version = Column(String)
    upgrade_manifest = Column(String)
    drafted_at = Column(DateTime, default=datetime.datetime.utcnow)

class InternalAnomaly(Base):
    __tablename__ = "metaforge_anomalies"

    id = Column(Integer, primary_key=True, index=True)
    subsystem = Column(String)
    anomaly_type = Column(String) # LATENCY_SPIKE, BYPASS_ATTEMPT
    severity = Column(String) # LOW, MEDIUM, CRITICAL
    action_taken = Column(String)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)

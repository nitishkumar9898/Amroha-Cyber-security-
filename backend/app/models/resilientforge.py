from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class DisasterSimulation(Base):
    __tablename__ = "resilientforge_simulations"

    id = Column(Integer, primary_key=True, index=True)
    scenario_name = Column(String) # e.g., DATACENTER_FIRE, RANSOMWARE
    target_infrastructure = Column(String)
    simulated_downtime_hours = Column(Float)
    optimized_rto_hours = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class BackupIntegrityLog(Base):
    __tablename__ = "resilientforge_backup_logs"

    id = Column(Integer, primary_key=True, index=True)
    backup_id = Column(String)
    file_signature = Column(String)
    is_corrupt = Column(Boolean)
    malware_detected = Column(Boolean)
    verified_at = Column(DateTime, default=datetime.datetime.utcnow)

class SelfHealingEvent(Base):
    __tablename__ = "resilientforge_heal_events"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String)
    initial_state = Column(String) # CORRUPTED, OFFLINE
    final_state = Column(String) # HEALED, RESTORED
    reconstruction_method = Column(String) # AI_REBUILD, CLEAN_BACKUP
    healed_at = Column(DateTime, default=datetime.datetime.utcnow)

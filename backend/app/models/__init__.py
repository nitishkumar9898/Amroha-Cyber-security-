"""
SQL Database Models Package
Exposes core models and allows submodules (supplychain, insider_shield, osint, identity, training) to be imported.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from datetime import datetime
from ..database import Base

class DBUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="analyst")
    agency = Column(String, default="STATE-POLICE")

class DBScenarioRun(Base):
    __tablename__ = "scenario_runs"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(String, index=True)
    name = Column(String)
    threat_actor = Column(String)
    target_sector = Column(String)
    status = Column(String, default="PENDING")
    start_time = Column(DateTime, default=datetime.utcnow)
    completed_phases = Column(String, default="")  # Comma separated phase names

class DBCustodyRecord(Base):
    __tablename__ = "custody_records"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    item_name = Column(String, index=True)
    file_path = Column(String)
    sha256_hash = Column(String)
    action = Column(String)  # COLLECTED, VERIFIED, TRANSFERRED, etc.
    officer_name = Column(String)
    agency_id = Column(String)
    description = Column(String)
    entry_signature = Column(String)

# ----- AutoDefend Recovery Log -----
class RecoveryLog(Base):
    """Audit‑proof log of auto‑remediation actions.
    Each entry is cryptographically signed using the existing ZKP signer.
    """
    __tablename__ = "recovery_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String)  # e.g., 'ANOMALY_DETECTED', 'PATCH_APPLIED'
    detail = Column(String)      # Human‑readable description of the event
    zkp_signature = Column(String)  # Signed proof of the log entry

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
import datetime
from ..database import Base

class CryptoAsset(Base):
    __tablename__ = "quantumsafe_asset"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String, index=True) # Groups assets by scan
    asset_name = Column(String)
    algorithm = Column(String) # RSA, ECC, AES
    key_size = Column(Integer)
    is_quantum_safe = Column(Boolean, default=False)
    discovery_date = Column(DateTime, default=datetime.datetime.utcnow)

class PQCVulnerability(Base):
    __tablename__ = "quantumsafe_vulnerability"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("quantumsafe_asset.id"))
    hndl_risk_score = Column(Float) # Harvest Now, Decrypt Later risk
    estimated_qday_years = Column(Integer)
    criticality = Column(String)

class MigrationSimulation(Base):
    __tablename__ = "quantumsafe_migration"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("quantumsafe_asset.id"))
    recommended_pqc = Column(String) # Kyber, Dilithium
    legacy_latency_ms = Column(Float)
    pqc_latency_ms = Column(Float)
    memory_overhead_kb = Column(Float)

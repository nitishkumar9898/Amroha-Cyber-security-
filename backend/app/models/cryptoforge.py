from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
import datetime
from ..database import Base


class CryptanalysisJob(Base):
    """Post-quantum or classical cryptanalysis simulation job."""
    __tablename__ = "cryptoforge_cryptanalysis_jobs"

    id = Column(Integer, primary_key=True, index=True)
    algorithm = Column(String, index=True)              # RSA, AES, ECC, Kyber, Dilithium, NTRU, etc.
    key_size = Column(Integer)
    attack_type = Column(String, index=True)             # brute_force, shor, grover, lattice_reduction, meet_in_middle
    estimated_qubits = Column(Integer, nullable=True)    # quantum resources required
    estimated_time_years = Column(Float, nullable=True)  # classical or quantum time estimate
    status = Column(String, default="pending")           # pending, running, completed, failed
    result = Column(JSON, nullable=True)                 # detailed simulation outcome
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    additional_metadata = Column("metadata", JSON, nullable=True)


class WeakEncryptionScan(Base):
    """Scan result for weak encryption detected in a real system."""
    __tablename__ = "cryptoforge_weak_scans"

    id = Column(Integer, primary_key=True, index=True)
    target = Column(String, index=True)                  # hostname, IP, service URL, certificate CN
    scan_type = Column(String, index=True)               # tls_scan, cert_audit, cipher_suite, key_exchange
    findings = Column(JSON, nullable=True)               # list of weakness objects
    risk_score = Column(Float, default=0.0)              # 0–1
    scanned_at = Column(DateTime, default=datetime.datetime.utcnow)
    additional_metadata = Column("metadata", JSON, nullable=True)


class SideChannelTest(Base):
    """Side-channel attack simulation record."""
    __tablename__ = "cryptoforge_sidechannel_tests"

    id = Column(Integer, primary_key=True, index=True)
    channel_type = Column(String, index=True)            # timing, power, cache, electromagnetic
    target_algorithm = Column(String)
    target_implementation = Column(String, nullable=True) # e.g., "openssl-3.1.4"
    vulnerable = Column(Boolean, default=False)
    leakage_score = Column(Float, default=0.0)           # 0–1 information leakage estimate
    details = Column(JSON, nullable=True)
    tested_at = Column(DateTime, default=datetime.datetime.utcnow)
    additional_metadata = Column("metadata", JSON, nullable=True)


class QuantumReadinessReport(Base):
    """Assessment of an organisation's quantum-readiness posture."""
    __tablename__ = "cryptoforge_quantum_readiness"

    id = Column(Integer, primary_key=True, index=True)
    organisation = Column(String, index=True)
    algorithms_in_use = Column(JSON, nullable=True)      # list of {"algorithm", "key_size", "quantum_safe"}
    overall_score = Column(Float, default=0.0)           # 0–1 quantum readiness
    recommendations = Column(JSON, nullable=True)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)
    additional_metadata = Column("metadata", JSON, nullable=True)

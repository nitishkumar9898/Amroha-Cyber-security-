from sqlalchemy.orm import Session
from ..models.cryptoforge import CryptanalysisJob, WeakEncryptionScan, SideChannelTest, QuantumReadinessReport
from ..schemas.cryptoforge import (
    CryptanalysisJobCreate, WeakEncryptionScanCreate,
    SideChannelTestCreate, QuantumReadinessCreate,
)
from ..modules.cryptoforge_engine import (
    simulate_cryptanalysis,
    scan_weak_encryption,
    assess_side_channel,
    assess_quantum_readiness,
)
from typing import List
import datetime


# ── Cryptanalysis Jobs ───────────────────────────────────────────────

def create_cryptanalysis_job(db: Session, payload: CryptanalysisJobCreate) -> CryptanalysisJob:
    result = simulate_cryptanalysis(payload.algorithm, payload.key_size, payload.attack_type)
    job = CryptanalysisJob(
        algorithm=payload.algorithm,
        key_size=payload.key_size,
        attack_type=payload.attack_type,
        estimated_qubits=result.get("estimated_qubits"),
        estimated_time_years=result.get("estimated_time_years"),
        status="completed",
        result=result,
        completed_at=datetime.datetime.utcnow(),
        additional_metadata=payload.additional_metadata,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def get_cryptanalysis_job(db: Session, job_id: int) -> CryptanalysisJob:
    rec = db.query(CryptanalysisJob).filter(CryptanalysisJob.id == job_id).first()
    if not rec:
        raise ValueError("CryptanalysisJob not found")
    return rec

def list_cryptanalysis_jobs(db: Session, algorithm: str = None) -> List[CryptanalysisJob]:
    q = db.query(CryptanalysisJob)
    if algorithm:
        q = q.filter(CryptanalysisJob.algorithm == algorithm)
    return q.order_by(CryptanalysisJob.created_at.desc()).all()


# ── Weak Encryption Scans ───────────────────────────────────────────

def run_weak_encryption_scan(db: Session, payload: WeakEncryptionScanCreate) -> WeakEncryptionScan:
    result = scan_weak_encryption(payload.target, payload.scan_type)
    scan = WeakEncryptionScan(
        target=payload.target,
        scan_type=payload.scan_type,
        findings=result["findings"],
        risk_score=result["risk_score"],
        additional_metadata=payload.additional_metadata,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan

def get_weak_scan(db: Session, scan_id: int) -> WeakEncryptionScan:
    rec = db.query(WeakEncryptionScan).filter(WeakEncryptionScan.id == scan_id).first()
    if not rec:
        raise ValueError("WeakEncryptionScan not found")
    return rec

def list_weak_scans(db: Session, target: str = None) -> List[WeakEncryptionScan]:
    q = db.query(WeakEncryptionScan)
    if target:
        q = q.filter(WeakEncryptionScan.target == target)
    return q.order_by(WeakEncryptionScan.scanned_at.desc()).all()


# ── Side-Channel Tests ──────────────────────────────────────────────

def run_side_channel_test(db: Session, payload: SideChannelTestCreate) -> SideChannelTest:
    result = assess_side_channel(payload.channel_type, payload.target_algorithm, payload.target_implementation)
    test = SideChannelTest(
        channel_type=payload.channel_type,
        target_algorithm=payload.target_algorithm,
        target_implementation=payload.target_implementation,
        vulnerable=result["vulnerable"],
        leakage_score=result["leakage_score"],
        details=result["details"],
        additional_metadata=payload.additional_metadata,
    )
    db.add(test)
    db.commit()
    db.refresh(test)
    return test

def get_side_channel_test(db: Session, test_id: int) -> SideChannelTest:
    rec = db.query(SideChannelTest).filter(SideChannelTest.id == test_id).first()
    if not rec:
        raise ValueError("SideChannelTest not found")
    return rec


# ── Quantum Readiness Reports ───────────────────────────────────────

def generate_quantum_readiness(db: Session, payload: QuantumReadinessCreate) -> QuantumReadinessReport:
    assessment = assess_quantum_readiness(payload.algorithms_in_use)
    report = QuantumReadinessReport(
        organisation=payload.organisation,
        algorithms_in_use=payload.algorithms_in_use,
        overall_score=assessment["overall_score"],
        recommendations=assessment["recommendations"],
        additional_metadata=payload.additional_metadata,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

def get_quantum_readiness(db: Session, report_id: int) -> QuantumReadinessReport:
    rec = db.query(QuantumReadinessReport).filter(QuantumReadinessReport.id == report_id).first()
    if not rec:
        raise ValueError("QuantumReadinessReport not found")
    return rec

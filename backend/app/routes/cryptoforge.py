from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import dependencies
from ..schemas.cryptoforge import (
    CryptanalysisJobCreate, CryptanalysisJobRead,
    WeakEncryptionScanCreate, WeakEncryptionScanRead,
    SideChannelTestCreate, SideChannelTestRead,
    QuantumReadinessCreate, QuantumReadinessRead,
)
from ..services.cryptoforge_service import (
    create_cryptanalysis_job, get_cryptanalysis_job, list_cryptanalysis_jobs,
    run_weak_encryption_scan, get_weak_scan, list_weak_scans,
    run_side_channel_test, get_side_channel_test,
    generate_quantum_readiness, get_quantum_readiness,
)
from typing import List

router = APIRouter()

# ── Cryptanalysis Jobs ───────────────────────────────────────────────

@router.post("/cryptanalysis", response_model=CryptanalysisJobRead)
def submit_cryptanalysis(payload: CryptanalysisJobCreate, db: Session = Depends(dependencies.get_db)):
    """Simulate a cryptanalysis attack on the specified algorithm and key size."""
    return create_cryptanalysis_job(db, payload)

@router.get("/cryptanalysis/{job_id}", response_model=CryptanalysisJobRead)
def read_cryptanalysis(job_id: int, db: Session = Depends(dependencies.get_db)):
    return get_cryptanalysis_job(db, job_id)

@router.get("/cryptanalyses", response_model=List[CryptanalysisJobRead])
def get_cryptanalyses(algorithm: str = None, db: Session = Depends(dependencies.get_db)):
    return list_cryptanalysis_jobs(db, algorithm)

# ── Weak Encryption Scans ───────────────────────────────────────────

@router.post("/weak_scan", response_model=WeakEncryptionScanRead)
def submit_scan(payload: WeakEncryptionScanCreate, db: Session = Depends(dependencies.get_db)):
    """Scan a target for weak encryption configurations."""
    return run_weak_encryption_scan(db, payload)

@router.get("/weak_scan/{scan_id}", response_model=WeakEncryptionScanRead)
def read_scan(scan_id: int, db: Session = Depends(dependencies.get_db)):
    return get_weak_scan(db, scan_id)

@router.get("/weak_scans", response_model=List[WeakEncryptionScanRead])
def get_scans(target: str = None, db: Session = Depends(dependencies.get_db)):
    return list_weak_scans(db, target)

# ── Side-Channel Tests ──────────────────────────────────────────────

@router.post("/sidechannel", response_model=SideChannelTestRead)
def submit_sidechannel(payload: SideChannelTestCreate, db: Session = Depends(dependencies.get_db)):
    """Assess side-channel vulnerability for a given algorithm and channel type."""
    return run_side_channel_test(db, payload)

@router.get("/sidechannel/{test_id}", response_model=SideChannelTestRead)
def read_sidechannel(test_id: int, db: Session = Depends(dependencies.get_db)):
    return get_side_channel_test(db, test_id)

# ── Quantum Readiness ───────────────────────────────────────────────

@router.post("/quantum_readiness", response_model=QuantumReadinessRead)
def submit_readiness(payload: QuantumReadinessCreate, db: Session = Depends(dependencies.get_db)):
    """Generate a quantum-readiness report for an organisation's cryptographic inventory."""
    return generate_quantum_readiness(db, payload)

@router.get("/quantum_readiness/{report_id}", response_model=QuantumReadinessRead)
def read_readiness(report_id: int, db: Session = Depends(dependencies.get_db)):
    return get_quantum_readiness(db, report_id)

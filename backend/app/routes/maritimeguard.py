from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import dependencies
from ..schemas.maritimeguard import (
    AISSignalCreate, AISSignalRead, AISBatchCreate,
    ShipboardForensicCreate, ShipboardForensicRead,
    PortSimulationCreate, PortSimulationRead,
    ComplianceCheckCreate, ComplianceCheckRead,
)
from ..services.maritimeguard_service import (
    store_ais_signal, store_ais_batch, get_ais_signal, list_ais_signals,
    create_shipboard_forensic, get_shipboard_forensic, list_shipboard_forensics,
    run_port_simulation, get_port_simulation,
    run_compliance_check, get_compliance_check,
)
from typing import List

router = APIRouter()

# ── AIS Signals ──────────────────────────────────────────────────────

@router.post("/ais", response_model=AISSignalRead)
def submit_ais_signal(payload: AISSignalCreate, db: Session = Depends(dependencies.get_db)):
    """Submit a single AIS signal for spoofing analysis."""
    return store_ais_signal(db, payload)

@router.post("/ais/batch", response_model=List[AISSignalRead])
def submit_ais_batch(batch: AISBatchCreate, db: Session = Depends(dependencies.get_db)):
    """Submit a batch of AIS signals for sequential spoof detection."""
    return store_ais_batch(db, batch)

@router.get("/ais/{signal_id}", response_model=AISSignalRead)
def read_ais(signal_id: int, db: Session = Depends(dependencies.get_db)):
    return get_ais_signal(db, signal_id)

@router.get("/ais", response_model=List[AISSignalRead])
def get_ais(mmsi: str = None, spoofed_only: bool = False,
            db: Session = Depends(dependencies.get_db)):
    return list_ais_signals(db, mmsi, spoofed_only)

# ── Shipboard Forensics ─────────────────────────────────────────────

@router.post("/forensic", response_model=ShipboardForensicRead)
def submit_forensic(payload: ShipboardForensicCreate, db: Session = Depends(dependencies.get_db)):
    """Log a shipboard OT/IT forensic investigation."""
    return create_shipboard_forensic(db, payload)

@router.get("/forensic/{forensic_id}", response_model=ShipboardForensicRead)
def read_forensic(forensic_id: int, db: Session = Depends(dependencies.get_db)):
    return get_shipboard_forensic(db, forensic_id)

@router.get("/forensics", response_model=List[ShipboardForensicRead])
def get_forensics(vessel_id: str = None, db: Session = Depends(dependencies.get_db)):
    return list_shipboard_forensics(db, vessel_id)

# ── Port Attack Simulations ─────────────────────────────────────────

@router.post("/port_simulation", response_model=PortSimulationRead)
def submit_simulation(payload: PortSimulationCreate, db: Session = Depends(dependencies.get_db)):
    """Run a supply-chain attack simulation on port infrastructure."""
    return run_port_simulation(db, payload)

@router.get("/port_simulation/{sim_id}", response_model=PortSimulationRead)
def read_simulation(sim_id: int, db: Session = Depends(dependencies.get_db)):
    return get_port_simulation(db, sim_id)

# ── Maritime Compliance ─────────────────────────────────────────────

@router.post("/compliance", response_model=ComplianceCheckRead)
def submit_compliance(payload: ComplianceCheckCreate, db: Session = Depends(dependencies.get_db)):
    """Assess a vessel against a maritime cybersecurity framework."""
    return run_compliance_check(db, payload)

@router.get("/compliance/{check_id}", response_model=ComplianceCheckRead)
def read_compliance(check_id: int, db: Session = Depends(dependencies.get_db)):
    return get_compliance_check(db, check_id)

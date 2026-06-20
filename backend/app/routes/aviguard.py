from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import dependencies
from ..schemas.aviguard import (
    ADSBSignalCreate, ADSBSignalRead, ADSBBatchCreate,
    AvionicsForensicCreate, AvionicsForensicRead,
    AirportScanCreate, AirportScanRead,
    DroneSimCreate, DroneSimRead,
    AviationComplianceCreate, AviationComplianceRead,
)
from ..services.aviguard_service import (
    store_adsb_signal, store_adsb_batch, get_adsb_signal, list_adsb_signals,
    create_avionics_forensic, get_avionics_forensic, list_avionics_forensics,
    run_airport_scan, get_airport_scan,
    run_drone_simulation, get_drone_simulation,
    run_aviation_compliance, get_aviation_compliance,
)
from typing import List

router = APIRouter()

# ── ADS-B Signals ────────────────────────────────────────────────────

@router.post("/adsb", response_model=ADSBSignalRead)
def submit_adsb(payload: ADSBSignalCreate, db: Session = Depends(dependencies.get_db)):
    """Submit a single ADS-B signal for spoofing analysis."""
    return store_adsb_signal(db, payload)

@router.post("/adsb/batch", response_model=List[ADSBSignalRead])
def submit_adsb_batch(batch: ADSBBatchCreate, db: Session = Depends(dependencies.get_db)):
    """Submit a batch of ADS-B signals for sequential trajectory spoof detection."""
    return store_adsb_batch(db, batch)

@router.get("/adsb/{signal_id}", response_model=ADSBSignalRead)
def read_adsb(signal_id: int, db: Session = Depends(dependencies.get_db)):
    return get_adsb_signal(db, signal_id)

@router.get("/adsb", response_model=List[ADSBSignalRead])
def get_adsb(icao_hex: str = None, spoofed_only: bool = False, db: Session = Depends(dependencies.get_db)):
    return list_adsb_signals(db, icao_hex, spoofed_only)

# ── Avionics Forensics ──────────────────────────────────────────────

@router.post("/avionics", response_model=AvionicsForensicRead)
def submit_avionics(payload: AvionicsForensicCreate, db: Session = Depends(dependencies.get_db)):
    """Log an avionics OT/IT forensic investigation."""
    return create_avionics_forensic(db, payload)

@router.get("/avionics/{forensic_id}", response_model=AvionicsForensicRead)
def read_avionics(forensic_id: int, db: Session = Depends(dependencies.get_db)):
    return get_avionics_forensic(db, forensic_id)

@router.get("/avionics", response_model=List[AvionicsForensicRead])
def get_avionics(aircraft_id: str = None, db: Session = Depends(dependencies.get_db)):
    return list_avionics_forensics(db, aircraft_id)

# ── Airport Network Scans ───────────────────────────────────────────

@router.post("/airport_scan", response_model=AirportScanRead)
def submit_airport_scan(payload: AirportScanCreate, db: Session = Depends(dependencies.get_db)):
    """Run a simulated network/data protection scan on an airport."""
    return run_airport_scan(db, payload)

@router.get("/airport_scan/{scan_id}", response_model=AirportScanRead)
def read_airport_scan(scan_id: int, db: Session = Depends(dependencies.get_db)):
    return get_airport_scan(db, scan_id)

# ── Drone Interference Simulations ──────────────────────────────────

@router.post("/drone_sim", response_model=DroneSimRead)
def submit_drone_sim(payload: DroneSimCreate, db: Session = Depends(dependencies.get_db)):
    """Run a drone interference and cyber-physical attack simulation."""
    return run_drone_simulation(db, payload)

@router.get("/drone_sim/{sim_id}", response_model=DroneSimRead)
def read_drone_sim(sim_id: int, db: Session = Depends(dependencies.get_db)):
    return get_drone_simulation(db, sim_id)

# ── Aviation Compliance ──────────────────────────────────────────────

@router.post("/compliance", response_model=AviationComplianceRead)
def submit_compliance(payload: AviationComplianceCreate, db: Session = Depends(dependencies.get_db)):
    """Assess an airline or airport against DGCA, ICAO, or EASA cybersecurity frameworks."""
    return run_aviation_compliance(db, payload)

@router.get("/compliance/{check_id}", response_model=AviationComplianceRead)
def read_compliance(check_id: int, db: Session = Depends(dependencies.get_db)):
    return get_aviation_compliance(db, check_id)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import dependencies
from ..schemas.healthguard import (
    IoMTDeviceCreate, IoMTDeviceRead,
    HealthDataBreachCreate, HealthDataBreachRead,
    FakeMedicalContentCreate, FakeMedicalContentRead,
    PandemicMisinfoCreate, PandemicMisinfoRead,
)
from ..services.healthguard_service import (
    register_and_scan_device, get_device, list_devices, rescan_device,
    report_breach, get_breach, list_breaches,
    analyse_fake_medical, get_fake_content,
    track_pandemic_misinfo, get_misinfo, list_misinfo,
)
from typing import List

router = APIRouter()

# ── IoMT Devices ─────────────────────────────────────────────────────

@router.post("/device", response_model=IoMTDeviceRead)
def register_device(payload: IoMTDeviceCreate, db: Session = Depends(dependencies.get_db)):
    """Register an IoMT device and perform an initial security scan."""
    return register_and_scan_device(db, payload)

@router.get("/device/{device_db_id}", response_model=IoMTDeviceRead)
def read_device(device_db_id: int, db: Session = Depends(dependencies.get_db)):
    return get_device(db, device_db_id)

@router.get("/devices", response_model=List[IoMTDeviceRead])
def get_devices(device_type: str = None, db: Session = Depends(dependencies.get_db)):
    return list_devices(db, device_type)

@router.post("/device/{device_db_id}/rescan", response_model=IoMTDeviceRead)
def rescan(device_db_id: int, db: Session = Depends(dependencies.get_db)):
    """Re-scan an existing device for updated vulnerabilities."""
    return rescan_device(db, device_db_id)

# ── Health Data Breaches ─────────────────────────────────────────────

@router.post("/breach", response_model=HealthDataBreachRead)
def create_breach(payload: HealthDataBreachCreate, db: Session = Depends(dependencies.get_db)):
    """Report a health data breach for severity assessment."""
    return report_breach(db, payload)

@router.get("/breach/{breach_id}", response_model=HealthDataBreachRead)
def read_breach(breach_id: int, db: Session = Depends(dependencies.get_db)):
    return get_breach(db, breach_id)

@router.get("/breaches", response_model=List[HealthDataBreachRead])
def get_breaches(status: str = None, db: Session = Depends(dependencies.get_db)):
    return list_breaches(db, status)

# ── Fake Medical Content ─────────────────────────────────────────────

@router.post("/fake_medical", response_model=FakeMedicalContentRead)
def submit_fake_medical(payload: FakeMedicalContentCreate, db: Session = Depends(dependencies.get_db)):
    """Analyse content for fake medical claims or deepfake doctor indicators."""
    return analyse_fake_medical(db, payload)

@router.get("/fake_medical/{content_id}", response_model=FakeMedicalContentRead)
def read_fake_medical(content_id: int, db: Session = Depends(dependencies.get_db)):
    return get_fake_content(db, content_id)

# ── Pandemic Misinformation ──────────────────────────────────────────

@router.post("/pandemic_misinfo", response_model=PandemicMisinfoRead)
def submit_misinfo(payload: PandemicMisinfoCreate, db: Session = Depends(dependencies.get_db)):
    """Track a pandemic misinformation narrative for severity scoring."""
    return track_pandemic_misinfo(db, payload)

@router.get("/pandemic_misinfo/{misinfo_id}", response_model=PandemicMisinfoRead)
def read_misinfo(misinfo_id: int, db: Session = Depends(dependencies.get_db)):
    return get_misinfo(db, misinfo_id)

@router.get("/pandemic_misinfos", response_model=List[PandemicMisinfoRead])
def get_misinfos(topic: str = None, status: str = None, db: Session = Depends(dependencies.get_db)):
    return list_misinfo(db, topic, status)

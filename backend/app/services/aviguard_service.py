from sqlalchemy.orm import Session
from ..models.aviguard import (
    ADSBSignalRecord, AvionicsForensic, AirportNetworkScan,
    DroneInterferenceSimulation, AviationComplianceCheck,
)
from ..schemas.aviguard import (
    ADSBSignalCreate, ADSBBatchCreate,
    AvionicsForensicCreate, AirportScanCreate,
    DroneSimCreate, AviationComplianceCreate,
)
from ..modules.aviguard_engine import (
    analyze_adsb_signal,
    assess_avionics_severity,
    scan_airport_network,
    simulate_drone_interference,
    assess_aviation_compliance,
)
from typing import List, Optional
import datetime


# ── ADS-B Signals ────────────────────────────────────────────────────

def store_adsb_signal(db: Session, payload: ADSBSignalCreate,
                      previous: Optional[dict] = None) -> ADSBSignalRecord:
    current = {
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "altitude_ft": payload.altitude_ft,
        "speed_knots": payload.speed_knots,
        "heading": payload.heading,
        "squawk": payload.squawk,
        "timestamp": datetime.datetime.utcnow(),
    }
    analysis = analyze_adsb_signal(current, previous)
    rec = ADSBSignalRecord(
        icao_hex=payload.icao_hex,
        callsign=payload.callsign,
        latitude=payload.latitude,
        longitude=payload.longitude,
        altitude_ft=payload.altitude_ft,
        speed_knots=payload.speed_knots,
        heading=payload.heading,
        squawk=payload.squawk,
        spoof_detected=analysis["spoof_detected"],
        spoof_confidence=analysis["spoof_confidence"],
        analysis=analysis,
        additional_metadata=payload.additional_metadata,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

def store_adsb_batch(db: Session, batch: ADSBBatchCreate) -> List[ADSBSignalRecord]:
    results = []
    previous = None
    for sig in batch.signals:
        rec = store_adsb_signal(db, sig, previous)
        results.append(rec)
        previous = {
            "latitude": sig.latitude,
            "longitude": sig.longitude,
            "altitude_ft": sig.altitude_ft,
            "speed_knots": sig.speed_knots,
            "heading": sig.heading,
            "squawk": sig.squawk,
            "timestamp": rec.timestamp,
        }
    return results

def get_adsb_signal(db: Session, signal_id: int) -> ADSBSignalRecord:
    rec = db.query(ADSBSignalRecord).filter(ADSBSignalRecord.id == signal_id).first()
    if not rec:
        raise ValueError("ADSBSignalRecord not found")
    return rec

def list_adsb_signals(db: Session, icao_hex: str = None, spoofed_only: bool = False) -> List[ADSBSignalRecord]:
    q = db.query(ADSBSignalRecord)
    if icao_hex:
        q = q.filter(ADSBSignalRecord.icao_hex == icao_hex)
    if spoofed_only:
        q = q.filter(ADSBSignalRecord.spoof_detected == True)
    return q.order_by(ADSBSignalRecord.timestamp.desc()).limit(200).all()


# ── Avionics Forensics ──────────────────────────────────────────────

def create_avionics_forensic(db: Session, payload: AvionicsForensicCreate) -> AvionicsForensic:
    severity = assess_avionics_severity(payload.system_type, payload.incident_type, payload.findings)
    rec = AvionicsForensic(
        aircraft_id=payload.aircraft_id,
        system_type=payload.system_type,
        incident_type=payload.incident_type,
        severity=severity,
        findings=payload.findings,
        additional_metadata=payload.additional_metadata,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

def get_avionics_forensic(db: Session, forensic_id: int) -> AvionicsForensic:
    rec = db.query(AvionicsForensic).filter(AvionicsForensic.id == forensic_id).first()
    if not rec:
        raise ValueError("AvionicsForensic not found")
    return rec

def list_avionics_forensics(db: Session, aircraft_id: str = None) -> List[AvionicsForensic]:
    q = db.query(AvionicsForensic)
    if aircraft_id:
        q = q.filter(AvionicsForensic.aircraft_id == aircraft_id)
    return q.order_by(AvionicsForensic.severity.desc()).all()


# ── Airport Network Scans ───────────────────────────────────────────

def run_airport_scan(db: Session, payload: AirportScanCreate) -> AirportNetworkScan:
    result = scan_airport_network(payload.airport_code, payload.scan_type)
    rec = AirportNetworkScan(
        airport_code=payload.airport_code,
        scan_type=payload.scan_type,
        risk_score=result["risk_score"],
        findings=result["findings"],
        additional_metadata=payload.additional_metadata,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

def get_airport_scan(db: Session, scan_id: int) -> AirportNetworkScan:
    rec = db.query(AirportNetworkScan).filter(AirportNetworkScan.id == scan_id).first()
    if not rec:
        raise ValueError("AirportNetworkScan not found")
    return rec


# ── Drone Interference Simulations ──────────────────────────────────

def run_drone_simulation(db: Session, payload: DroneSimCreate) -> DroneInterferenceSimulation:
    result = simulate_drone_interference(payload.scenario_name, payload.attack_vector, payload.parameters)
    sim = DroneInterferenceSimulation(
        scenario_name=payload.scenario_name,
        attack_vector=payload.attack_vector,
        parameters=payload.parameters,
        result=result,
        resilience_score=result["resilience_score"],
    )
    db.add(sim)
    db.commit()
    db.refresh(sim)
    return sim

def get_drone_simulation(db: Session, sim_id: int) -> DroneInterferenceSimulation:
    rec = db.query(DroneInterferenceSimulation).filter(DroneInterferenceSimulation.id == sim_id).first()
    if not rec:
        raise ValueError("DroneInterferenceSimulation not found")
    return rec


# ── Aviation Compliance ──────────────────────────────────────────────

def run_aviation_compliance(db: Session, payload: AviationComplianceCreate) -> AviationComplianceCheck:
    assessment = assess_aviation_compliance(payload.framework)
    rec = AviationComplianceCheck(
        entity_id=payload.entity_id,
        entity_type=payload.entity_type,
        framework=payload.framework,
        overall_score=assessment["overall_score"],
        findings=assessment["findings"],
        recommendations=assessment["recommendations"],
        additional_metadata=payload.additional_metadata,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

def get_aviation_compliance(db: Session, check_id: int) -> AviationComplianceCheck:
    rec = db.query(AviationComplianceCheck).filter(AviationComplianceCheck.id == check_id).first()
    if not rec:
        raise ValueError("AviationComplianceCheck not found")
    return rec

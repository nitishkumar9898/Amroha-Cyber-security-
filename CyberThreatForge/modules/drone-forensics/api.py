"""Autonomous Drone Forensics API.

FastAPI application for forensic acquisition and analysis from drones
(DJI, Parrot, custom-built). Extracts flight logs, telemetry, camera
footage, GPS tracks with tamper-proof chain-of-custody.
"""

import os
import json
import uuid
import time
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timezone

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Body
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from parsers.dji_parser import (
    DjiDatParser, DjiTxtParser, DjiMediaParser, DjiFlightLog, DjiGpsSample,
    DjiBatterySample, DjiSignalSample, DjiImuSample, DjiRcInput, DjiMediaEntry,
)
from parsers.parrot_parser import (
    ParrotJsonParser, ParrotCsvParser, ParrotMediaParser, ParrotFlightLog,
    ParrotGpsSample, ParrotBatterySample, ParrotImuSample, ParrotMotorSample,
)
from parsers.pixhawk_parser import (
    ULogParser, Px4BinParser, MavLinkTelemetryParser, PixhawkFlightLog,
    PixhawkGpsSample, PixhawkBatterySample, PixhawkAttitudeSample,
)
from pipelines.flight_analyzer import (
    FlightAnalyzer, GeoPoint, GeoFence, NoFlyZone, FlightAnalysisResult,
    generate_kml, generate_kmz,
)
from pipelines.incident_reconstructor import (
    IncidentReconstructor, IncidentReconstructionResult, TelemetryAnomaly,
    CrashSiteEstimate, PilotProfile,
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    module: str = "drone-forensics"
    version: str = "1.0.0"
    status: str = "healthy"
    timestamp: str = ""

class AcquireResponse(BaseModel):
    job_id: str
    drone_type: str
    status: str
    flight_logs: dict[str, Any]
    media_files: list[dict[str, Any]]
    chain_of_custody: list[dict[str, Any]]
    processing_time_ms: float

class AnalyzeFlightResponse(BaseModel):
    job_id: str
    status: str
    flight_analysis: dict[str, Any]
    kml_track: Optional[str] = None
    geofence_violations: list[dict[str, Any]]
    no_fly_zone_alerts: list[dict[str, Any]]
    chain_of_custody: list[dict[str, Any]]
    processing_time_ms: float

class AnalyzeTelemetryResponse(BaseModel):
    job_id: str
    status: str
    anomalies: list[dict[str, Any]]
    anomaly_count: int
    chain_of_custody: list[dict[str, Any]]
    processing_time_ms: float

class AnalyzeMediaResponse(BaseModel):
    job_id: str
    status: str
    geo_tagged_media: list[dict[str, Any]]
    media_timeline: list[dict[str, Any]]
    chain_of_custody: list[dict[str, Any]]
    processing_time_ms: float

class AnalyzeIncidentResponse(BaseModel):
    job_id: str
    status: str
    reconstruction: dict[str, Any]
    chain_of_custody: list[dict[str, Any]]
    processing_time_ms: float

class ReportResponse(BaseModel):
    job_id: str
    report_id: str
    status: str
    report: dict[str, Any]
    chain_of_custody: list[dict[str, Any]]
    processing_time_ms: float


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CyberThreatForge — Autonomous Drone Forensics",
    description="Forensic acquisition and analysis from DJI, Parrot, and custom-built drones.",
    version="1.0.0",
)

JOB_STORE: dict[str, dict[str, Any]] = {}
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MODULE_ID = "drone-forensics"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _job_id() -> str:
    jid = str(uuid.uuid4())
    JOB_STORE[jid] = {"status": "accepted", "created_at": time.time()}
    return jid


def _record_custody(action: str, data: Optional[dict] = None) -> dict[str, Any]:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from shared.chain_of_custody import ChainOfCustodyManager
    mgr = ChainOfCustodyManager()
    event = mgr.record(
        action=action, actor="drone_forensics", module=MODULE_ID, data=data,
    )
    return {
        "timestamp": event.timestamp,
        "action": event.action,
        "actor": event.actor,
        "module": event.module,
        "hash": event.hash,
        "notes": event.notes,
    }


def _save_upload(file: UploadFile) -> tuple[Path, str]:
    dest = UPLOAD_DIR / f"{uuid.uuid4().hex}_{file.filename or 'upload'}"
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    if dest.suffix.lower() == ".zip":
        extract_dir = UPLOAD_DIR / dest.stem
        extract_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(dest, "r") as zf:
            zf.extractall(extract_dir)
        dest.unlink()
        return extract_dir, extract_dir.name
    return dest, dest.name


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(timestamp=datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Acquire endpoints
# ---------------------------------------------------------------------------

@app.post("/acquire/dji", response_model=AcquireResponse)
async def acquire_dji(
    log_file: UploadFile = File(...),
    media_zip: Optional[UploadFile] = File(None),
):
    jid = _job_id()
    start = time.monotonic()
    custody: list[dict] = []

    custody.append(_record_custody("acquire_dji_received", {"filename": log_file.filename}))
    JOB_STORE[jid]["status"] = "processing"

    try:
        log_path, _ = _save_upload(log_file)
        ext = log_path.suffix.lower()

        if ext == ".dat":
            parser = DjiDatParser(log_path)
        elif ext == ".txt":
            parser = DjiTxtParser(log_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported DJI log format: {ext}")

        flight_log: DjiFlightLog = parser.parse()

        media_entries: list[dict] = []
        if media_zip:
            media_dir, _ = _save_upload(media_zip)
            media_parser = DjiMediaParser(media_dir)
            media_entries = [
                {
                    "file": m.file_path,
                    "type": m.file_type,
                    "timestamp": m.timestamp,
                    "latitude": m.latitude,
                    "longitude": m.longitude,
                    "altitude_m": m.altitude_m,
                    "size_bytes": m.file_size_bytes,
                    "hash_md5": m.hash_md5,
                }
                for m in media_parser.parse()
            ]
            shutil.rmtree(media_dir, ignore_errors=True)

        data = _flight_log_to_dict(flight_log)
        processing_time = (time.monotonic() - start) * 1000

        custody.append(_record_custody("acquire_dji_complete", {
            "gps_samples": len(flight_log.gps_samples),
            "media_files": len(media_entries),
        }))
        JOB_STORE[jid]["status"] = "completed"

        return AcquireResponse(
            job_id=jid, drone_type="DJI", status="completed",
            flight_logs=data, media_files=media_entries,
            chain_of_custody=custody, processing_time_ms=round(processing_time, 2),
        )

    except HTTPException:
        raise
    except Exception as exc:
        custody.append(_record_custody("acquire_dji_error", {"error": str(exc)}))
        JOB_STORE[jid]["status"] = "failed"
        return JSONResponse(
            status_code=500,
            content=AcquireResponse(
                job_id=jid, drone_type="DJI", status="failed",
                flight_logs={}, media_files=[], chain_of_custody=custody,
                processing_time_ms=(time.monotonic() - start) * 1000,
            ).model_dump(),
        )


@app.post("/acquire/parrot", response_model=AcquireResponse)
async def acquire_parrot(
    log_file: UploadFile = File(...),
    media_zip: Optional[UploadFile] = File(None),
):
    jid = _job_id()
    start = time.monotonic()
    custody: list[dict] = []

    custody.append(_record_custody("acquire_parrot_received", {"filename": log_file.filename}))
    JOB_STORE[jid]["status"] = "processing"

    try:
        log_path, _ = _save_upload(log_file)
        ext = log_path.suffix.lower()

        if ext == ".csv":
            parser = ParrotCsvParser(log_path)
        elif ext == ".json":
            parser = ParrotJsonParser(log_path)
        else:
            parser = ParrotCsvParser(log_path)

        flight_log: ParrotFlightLog = parser.parse()

        media_entries: list[dict] = []
        if media_zip:
            media_dir, _ = _save_upload(media_zip)
            media_parser = ParrotMediaParser(media_dir)
            media_entries = [
                {
                    "file": m.file_path, "type": m.file_type,
                    "timestamp": m.timestamp, "latitude": m.latitude,
                    "longitude": m.longitude, "altitude_m": m.altitude_m,
                    "size_bytes": m.file_size_bytes, "hash_md5": m.hash_md5,
                }
                for m in media_parser.parse()
            ]
            shutil.rmtree(media_dir, ignore_errors=True)

        data = _parrot_log_to_dict(flight_log)
        processing_time = (time.monotonic() - start) * 1000

        custody.append(_record_custody("acquire_parrot_complete", {
            "gps_samples": len(flight_log.gps_samples),
            "media_files": len(media_entries),
        }))
        JOB_STORE[jid]["status"] = "completed"

        return AcquireResponse(
            job_id=jid, drone_type="Parrot", status="completed",
            flight_logs=data, media_files=media_entries,
            chain_of_custody=custody, processing_time_ms=round(processing_time, 2),
        )

    except HTTPException:
        raise
    except Exception as exc:
        custody.append(_record_custody("acquire_parrot_error", {"error": str(exc)}))
        JOB_STORE[jid]["status"] = "failed"
        return JSONResponse(
            status_code=500,
            content=AcquireResponse(
                job_id=jid, drone_type="Parrot", status="failed",
                flight_logs={}, media_files=[], chain_of_custody=custody,
                processing_time_ms=(time.monotonic() - start) * 1000,
            ).model_dump(),
        )


@app.post("/acquire/custom", response_model=AcquireResponse)
async def acquire_custom(
    log_file: UploadFile = File(...),
    media_zip: Optional[UploadFile] = File(None),
):
    jid = _job_id()
    start = time.monotonic()
    custody: list[dict] = []

    custody.append(_record_custody("acquire_custom_received", {"filename": log_file.filename}))
    JOB_STORE[jid]["status"] = "processing"

    try:
        log_path, _ = _save_upload(log_file)
        ext = log_path.suffix.lower()

        if ext == ".ulg":
            parser = ULogParser(log_path)
        elif ext in (".bin", ".log"):
            parser = Px4BinParser(log_path)
        elif ext == ".mavlink":
            parser = MavLinkTelemetryParser(log_path)
        else:
            parser = Px4BinParser(log_path)

        flight_log: PixhawkFlightLog = parser.parse()
        data = _pixhawk_log_to_dict(flight_log)

        media_entries: list[dict] = []
        if media_zip:
            media_dir, _ = _save_upload(media_zip)
            for fpath in sorted(Path(media_dir).rglob("*")):
                if fpath.is_file() and fpath.suffix.lower() in (".jpg", ".jpeg", ".png", ".mp4"):
                    media_entries.append({
                        "file": str(fpath.relative_to(media_dir)),
                        "type": fpath.suffix.lower().lstrip("."),
                        "size_bytes": fpath.stat().st_size,
                    })
            shutil.rmtree(media_dir, ignore_errors=True)

        processing_time = (time.monotonic() - start) * 1000
        custody.append(_record_custody("acquire_custom_complete", {
            "gps_samples": len(flight_log.gps_samples),
            "media_files": len(media_entries),
        }))
        JOB_STORE[jid]["status"] = "completed"

        return AcquireResponse(
            job_id=jid, drone_type="Pixhawk", status="completed",
            flight_logs=data, media_files=media_entries,
            chain_of_custody=custody, processing_time_ms=round(processing_time, 2),
        )

    except HTTPException:
        raise
    except Exception as exc:
        custody.append(_record_custody("acquire_custom_error", {"error": str(exc)}))
        JOB_STORE[jid]["status"] = "failed"
        return JSONResponse(
            status_code=500,
            content=AcquireResponse(
                job_id=jid, drone_type="Pixhawk", status="failed",
                flight_logs={}, media_files=[], chain_of_custody=custody,
                processing_time_ms=(time.monotonic() - start) * 1000,
            ).model_dump(),
        )


# ---------------------------------------------------------------------------
# Analyze endpoints
# ---------------------------------------------------------------------------

@app.post("/analyze/flight", response_model=AnalyzeFlightResponse)
async def analyze_flight(data: dict[str, Any] = Body(...)):
    jid = _job_id()
    start = time.monotonic()
    custody: list[dict] = []

    custody.append(_record_custody("analyze_flight"))
    JOB_STORE[jid]["status"] = "processing"

    try:
        gps_data = data.get("gps_samples", data.get("track", []))
        geofences_data = data.get("geofences", [])
        nofly_zones_data = data.get("no_fly_zones", [])

        points = []
        for g in gps_data:
            points.append(GeoPoint(
                latitude=g.get("latitude", 0),
                longitude=g.get("longitude", 0),
                altitude_m=g.get("altitude_m", g.get("altitude", 0)),
                timestamp=g.get("timestamp", ""),
                speed_ms=g.get("speed_ms", g.get("speed", 0)),
                heading_deg=g.get("heading_deg", g.get("heading", 0)),
            ))

        analyzer = FlightAnalyzer()
        for gf in geofences_data:
            analyzer.add_geofence(GeoFence(
                name=gf.get("name", "Geofence"),
                center_lat=gf.get("center_lat", gf.get("latitude", 0)),
                center_lon=gf.get("center_lon", gf.get("longitude", 0)),
                radius_m=gf.get("radius_m", 100),
                type=gf.get("type", "circular"),
            ))
        for nf in nofly_zones_data:
            analyzer.add_no_fly_zone(NoFlyZone(
                name=nf.get("name", "No-Fly Zone"),
                latitude=nf.get("latitude", 0),
                longitude=nf.get("longitude", 0),
                radius_m=nf.get("radius_m", 1000),
            ))

        result: FlightAnalysisResult = analyzer.analyze(points)

        kml = generate_kml(result.smoothed_track, result.home_point,
                           title=f"Drone Flight Analysis {jid[:8]}")
        kmz_bytes = generate_kmz(kml)

        analysis_dict = {
            "total_distance_m": result.total_distance_m,
            "total_flight_time_s": result.total_flight_time_s,
            "max_distance_from_home_m": result.max_distance_from_home_m,
            "max_altitude_m": result.max_altitude_m,
            "max_speed_ms": result.max_speed_ms,
            "avg_speed_ms": result.avg_speed_ms,
            "speed_profile": result.speed_profile.__dict__,
            "altitude_profile": result.altitude_profile.__dict__,
            "flight_segments": [s.__dict__ for s in result.flight_segments],
            "home_point": result.home_point.__dict__ if result.home_point else None,
            "takeoff_point": result.takeoff_point.__dict__ if result.takeoff_point else None,
            "landing_point": result.landing_point.__dict__ if result.landing_point else None,
        }

        violations = [
            {
                "timestamp": v.timestamp, "fence_name": v.fence_name,
                "distance_m": v.distance_m, "severity": v.severity,
                "location": list(v.location) if v.location else None,
                "details": v.details,
            }
            for v in result.geofence_violations
        ]
        nfz_alerts = [
            {
                "timestamp": v.timestamp, "fence_name": v.fence_name,
                "distance_m": v.distance_m, "severity": v.severity,
                "location": list(v.location) if v.location else None,
                "details": v.details,
            }
            for v in result.no_fly_zone_alerts
        ]

        processing_time = (time.monotonic() - start) * 1000
        custody.append(_record_custody("analyze_flight_complete", {
            "total_distance_m": result.total_distance_m,
            "violations": len(violations),
            "nfz_alerts": len(nfz_alerts),
        }))
        JOB_STORE[jid]["status"] = "completed"

        return AnalyzeFlightResponse(
            job_id=jid, status="completed",
            flight_analysis=analysis_dict,
            kml_track=f"data:application/vnd.google-earth.kmz;base64,{kmz_bytes.hex()}",
            geofence_violations=violations,
            no_fly_zone_alerts=nfz_alerts,
            chain_of_custody=custody,
            processing_time_ms=round(processing_time, 2),
        )

    except HTTPException:
        raise
    except Exception as exc:
        custody.append(_record_custody("analyze_flight_error", {"error": str(exc)}))
        JOB_STORE[jid]["status"] = "failed"
        return JSONResponse(
            status_code=500,
            content=AnalyzeFlightResponse(
                job_id=jid, status="failed", flight_analysis={},
                geofence_violations=[], no_fly_zone_alerts=[],
                chain_of_custody=custody,
                processing_time_ms=(time.monotonic() - start) * 1000,
            ).model_dump(),
        )


@app.post("/analyze/telemetry", response_model=AnalyzeTelemetryResponse)
async def analyze_telemetry(data: dict[str, Any] = Body(...)):
    jid = _job_id()
    start = time.monotonic()
    custody: list[dict] = []

    custody.append(_record_custody("analyze_telemetry"))
    JOB_STORE[jid]["status"] = "processing"

    try:
        reconstructor = IncidentReconstructor()

        for g in data.get("gps_samples", []):
            reconstructor.add_gps_data(
                lat=g.get("latitude", 0), lon=g.get("longitude", 0),
                alt=g.get("altitude_m", g.get("altitude", 0)),
                speed=g.get("speed_ms", g.get("speed", 0)),
                heading=g.get("heading_deg", g.get("heading", 0)),
                ts=g.get("timestamp", ""),
            )

        for b in data.get("battery_samples", []):
            reconstructor.add_battery_data(
                voltage=b.get("voltage_v", b.get("voltage", 0)),
                current=b.get("current_a", b.get("current", 0)),
                percent=b.get("capacity_percent", b.get("percent", 100)),
                temp=b.get("temperature_c", b.get("temperature", 0)),
                ts=b.get("timestamp", ""),
            )

        for s in data.get("signal_samples", []):
            reconstructor.add_signal_data(
                rc_quality=s.get("rc_quality_percent", s.get("quality", 100)),
                distance_m=s.get("distance_m", s.get("distance", 0)),
                ts=s.get("timestamp", ""),
            )

        for m in data.get("motor_samples", []):
            reconstructor.add_motor_data(
                motor_rpms=m.get("rpms", m.get("motor_rpms", [])),
                ts=m.get("timestamp", ""),
            )

        for a in data.get("attitude_samples", []):
            reconstructor.add_attitude_data(
                roll=a.get("roll_deg", a.get("roll", 0)),
                pitch=a.get("pitch_deg", a.get("pitch", 0)),
                yaw=a.get("yaw_deg", a.get("yaw", 0)),
                ts=a.get("timestamp", ""),
            )

        result = reconstructor.reconstruct()

        anomalies = [
            {
                "timestamp": a.timestamp, "anomaly_type": a.anomaly_type,
                "severity": a.severity, "score": a.score,
                "description": a.description,
            }
            for a in result.anomalies
        ]

        processing_time = (time.monotonic() - start) * 1000
        custody.append(_record_custody("analyze_telemetry_complete", {
            "anomaly_count": len(anomalies),
        }))
        JOB_STORE[jid]["status"] = "completed"

        return AnalyzeTelemetryResponse(
            job_id=jid, status="completed",
            anomalies=anomalies, anomaly_count=len(anomalies),
            chain_of_custody=custody, processing_time_ms=round(processing_time, 2),
        )

    except HTTPException:
        raise
    except Exception as exc:
        custody.append(_record_custody("analyze_telemetry_error", {"error": str(exc)}))
        JOB_STORE[jid]["status"] = "failed"
        return JSONResponse(
            status_code=500,
            content=AnalyzeTelemetryResponse(
                job_id=jid, status="failed",
                anomalies=[], anomaly_count=0,
                chain_of_custody=custody,
                processing_time_ms=(time.monotonic() - start) * 1000,
            ).model_dump(),
        )


@app.post("/analyze/media", response_model=AnalyzeMediaResponse)
async def analyze_media(data: dict[str, Any] = Body(...)):
    jid = _job_id()
    start = time.monotonic()
    custody: list[dict] = []

    custody.append(_record_custody("analyze_media"))
    JOB_STORE[jid]["status"] = "processing"

    try:
        media_files = data.get("media", data.get("media_files", []))
        gps_track = data.get("gps_track", data.get("gps_samples", []))

        geo_tagged = []
        timeline = []

        for m in media_files:
            entry = {
                "file": m.get("file", m.get("file_path", "")),
                "type": m.get("type", m.get("file_type", "unknown")),
                "timestamp": m.get("timestamp"),
                "latitude": m.get("latitude"),
                "longitude": m.get("longitude"),
                "altitude_m": m.get("altitude_m"),
                "has_geo_tag": bool(m.get("latitude") and m.get("longitude")),
            }
            geo_tagged.append(entry)

            ts = m.get("timestamp")
            if ts:
                timeline.append({
                    "timestamp": ts,
                    "type": "media",
                    "file": entry["file"],
                    "description": f"{entry['type'].upper()} file captured",
                })

        if gps_track:
            for g in gps_track:
                ts = g.get("timestamp")
                if ts:
                    timeline.append({
                        "timestamp": ts,
                        "type": "gps_position",
                        "latitude": g.get("latitude"),
                        "longitude": g.get("longitude"),
                        "altitude_m": g.get("altitude_m", g.get("altitude", 0)),
                        "description": f"GPS position recorded",
                    })

        timeline.sort(key=lambda x: x.get("timestamp", ""))

        correlated = []
        for i, t1 in enumerate(timeline):
            if t1["type"] == "media":
                nearest_gps = None
                min_tdiff = float("inf")
                for t2 in timeline:
                    if t2["type"] == "gps_position" and t1.get("timestamp"):
                        try:
                            diff = abs(datetime.fromisoformat(t1["timestamp"]) -
                                       datetime.fromisoformat(t2["timestamp"]))
                            tdiff = diff.total_seconds()
                            if tdiff < min_tdiff:
                                min_tdiff = tdiff
                                nearest_gps = t2
                        except (ValueError, TypeError):
                            pass
                if nearest_gps and min_tdiff < 60:
                    correlated.append({
                        "media_file": t1["file"],
                        "correlated_gps": {
                            "latitude": nearest_gps.get("latitude"),
                            "longitude": nearest_gps.get("longitude"),
                            "altitude_m": nearest_gps.get("altitude_m"),
                        },
                        "time_difference_s": round(min_tdiff, 1),
                    })

        processing_time = (time.monotonic() - start) * 1000
        custody.append(_record_custody("analyze_media_complete", {
            "media_count": len(geo_tagged),
            "geo_tagged": sum(1 for g in geo_tagged if g["has_geo_tag"]),
            "correlated": len(correlated),
        }))
        JOB_STORE[jid]["status"] = "completed"

        return AnalyzeMediaResponse(
            job_id=jid, status="completed",
            geo_tagged_media=geo_tagged,
            media_timeline=correlated,
            chain_of_custody=custody,
            processing_time_ms=round(processing_time, 2),
        )

    except HTTPException:
        raise
    except Exception as exc:
        custody.append(_record_custody("analyze_media_error", {"error": str(exc)}))
        JOB_STORE[jid]["status"] = "failed"
        return JSONResponse(
            status_code=500,
            content=AnalyzeMediaResponse(
                job_id=jid, status="failed",
                geo_tagged_media=[], media_timeline=[],
                chain_of_custody=custody,
                processing_time_ms=(time.monotonic() - start) * 1000,
            ).model_dump(),
        )


@app.post("/analyze/incident", response_model=AnalyzeIncidentResponse)
async def analyze_incident(data: dict[str, Any] = Body(...)):
    jid = _job_id()
    start = time.monotonic()
    custody: list[dict] = []

    custody.append(_record_custody("analyze_incident"))
    JOB_STORE[jid]["status"] = "processing"

    try:
        reconstructor = IncidentReconstructor()

        for g in data.get("gps_samples", data.get("gps_data", [])):
            reconstructor.add_gps_data(
                lat=g.get("latitude", 0), lon=g.get("longitude", 0),
                alt=g.get("altitude_m", g.get("altitude", 0)),
                speed=g.get("speed_ms", g.get("speed", 0)),
                heading=g.get("heading_deg", g.get("heading", 0)),
                ts=g.get("timestamp", ""),
            )

        for b in data.get("battery_samples", data.get("battery_data", [])):
            reconstructor.add_battery_data(
                voltage=b.get("voltage_v", b.get("voltage", 0)),
                current=b.get("current_a", b.get("current", 0)),
                percent=b.get("capacity_percent", b.get("percent", 100)),
                temp=b.get("temperature_c", b.get("temperature", 0)),
                ts=b.get("timestamp", ""),
            )

        for m in data.get("motor_samples", data.get("motor_data", [])):
            reconstructor.add_motor_data(
                motor_rpms=m.get("rpms", m.get("motor_rpms", [])),
                ts=m.get("timestamp", ""),
            )

        for s in data.get("signal_samples", data.get("signal_data", [])):
            reconstructor.add_signal_data(
                rc_quality=s.get("rc_quality_percent", s.get("quality", 100)),
                distance_m=s.get("distance_m", s.get("distance", 0)),
                ts=s.get("timestamp", ""),
            )

        for evt in data.get("events", []):
            reconstructor.add_event(
                event_type=evt.get("event_type", "unknown"),
                source=evt.get("source", "log"),
                description=evt.get("description", ""),
                ts=evt.get("timestamp", ""),
                severity=evt.get("severity", "info"),
            )

        result = reconstructor.reconstruct()

        reconstruction_dict = {
            "incident_category": result.incident_category,
            "reconstruction_confidence": result.reconstruction_confidence,
            "data_sources_fused": result.data_sources_fused,
            "anomalies": [
                {"timestamp": a.timestamp, "type": a.anomaly_type,
                 "severity": a.severity, "description": a.description}
                for a in result.anomalies
            ],
            "critical_events": [
                {"timestamp": e.timestamp, "type": e.event_type,
                 "description": e.description, "severity": e.severity}
                for e in result.critical_events
            ],
            "crash_site": result.crash_site.__dict__ if result.crash_site else None,
            "pilot_profile": result.pilot_profile.__dict__ if result.pilot_profile else None,
            "timeline": [
                {"timestamp": e.timestamp, "type": e.event_type,
                 "source": e.source, "description": e.description,
                 "severity": e.severity}
                for e in result.timeline
            ],
        }

        processing_time = (time.monotonic() - start) * 1000
        custody.append(_record_custody("analyze_incident_complete", {
            "anomalies": len(result.anomalies),
            "critical_events": len(result.critical_events),
            "confidence": result.reconstruction_confidence,
        }))
        JOB_STORE[jid]["status"] = "completed"

        return AnalyzeIncidentResponse(
            job_id=jid, status="completed",
            reconstruction=reconstruction_dict,
            chain_of_custody=custody,
            processing_time_ms=round(processing_time, 2),
        )

    except HTTPException:
        raise
    except Exception as exc:
        custody.append(_record_custody("analyze_incident_error", {"error": str(exc)}))
        JOB_STORE[jid]["status"] = "failed"
        return JSONResponse(
            status_code=500,
            content=AnalyzeIncidentResponse(
                job_id=jid, status="failed",
                reconstruction={}, chain_of_custody=custody,
                processing_time_ms=(time.monotonic() - start) * 1000,
            ).model_dump(),
        )


@app.post("/report/generate", response_model=ReportResponse)
async def generate_report(data: dict[str, Any] = Body(...)):
    jid = _job_id()
    start = time.monotonic()
    custody: list[dict] = []

    custody.append(_record_custody("generate_report"))
    JOB_STORE[jid]["status"] = "processing"

    try:
        report_id = f"DRF-{uuid.uuid4().hex[:8].upper()}"
        case_id = data.get("case_id", "UNKNOWN")

        flight_analysis = data.get("flight_analysis", {})
        telemetry_analysis = data.get("telemetry_analysis", {})
        media_analysis = data.get("media_analysis", {})
        incident_reconstruction = data.get("incident_reconstruction", {})

        report = {
            "report_id": report_id,
            "case_id": case_id,
            "module": MODULE_ID,
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": "drone_forensics_api",
            "device_info": data.get("device_info", {}),
            "executive_summary": _generate_summary(flight_analysis, telemetry_analysis, incident_reconstruction),
            "flight_analysis": flight_analysis,
            "telemetry_analysis": telemetry_analysis,
            "media_analysis": media_analysis,
            "incident_reconstruction": incident_reconstruction,
            "findings": _extract_findings(telemetry_analysis, incident_reconstruction),
            "chain_of_custody": custody,
            "section_65b_compliant": True,
        }

        processing_time = (time.monotonic() - start) * 1000
        custody.append(_record_custody("report_generated", {"report_id": report_id}))
        JOB_STORE[jid]["status"] = "completed"

        return ReportResponse(
            job_id=jid, report_id=report_id, status="completed",
            report=report, chain_of_custody=custody,
            processing_time_ms=round(processing_time, 2),
        )

    except HTTPException:
        raise
    except Exception as exc:
        custody.append(_record_custody("report_error", {"error": str(exc)}))
        JOB_STORE[jid]["status"] = "failed"
        return JSONResponse(
            status_code=500,
            content=ReportResponse(
                job_id=jid, report_id="", status="failed",
                report={}, chain_of_custody=custody,
                processing_time_ms=(time.monotonic() - start) * 1000,
            ).model_dump(),
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _flight_log_to_dict(log: DjiFlightLog) -> dict[str, Any]:
    return {
        "aircraft_model": log.aircraft_model,
        "aircraft_sn": log.aircraft_sn,
        "firmware_version": log.firmware_version,
        "app_version": log.app_version,
        "flight_count": log.flight_count,
        "total_flight_time_s": log.total_flight_time_s,
        "max_altitude_m": log.max_altitude_m,
        "max_speed_ms": log.max_speed_ms,
        "max_distance_m": log.max_distance_m,
        "takeoff_location": log.takeoff_location,
        "landing_location": log.landing_location,
        "home_location": log.home_location,
        "gps_samples": [
            {
                "timestamp": g.timestamp, "latitude": g.latitude,
                "longitude": g.longitude, "altitude_m": g.altitude_m,
                "relative_altitude_m": g.relative_altitude_m,
                "speed_ms": g.speed_ms, "heading_deg": g.heading_deg,
                "num_satellites": g.num_satellites, "hdop": g.hdop,
                "gps_fix_type": g.gps_fix_type,
            }
            for g in log.gps_samples
        ],
        "battery_samples": [
            {
                "timestamp": b.timestamp, "voltage_v": b.voltage_v,
                "current_a": b.current_a, "capacity_percent": b.capacity_percent,
                "temperature_c": b.temperature_c, "cell_voltages": b.cell_voltages,
            }
            for b in log.battery_samples
        ],
        "signal_samples": [
            {
                "timestamp": s.timestamp, "rc_quality_percent": s.rc_quality_percent,
                "video_link_quality_percent": s.video_link_quality_percent,
                "downlink_quality_percent": s.downlink_quality_percent,
                "interference_grade": s.interference_grade, "distance_m": s.distance_m,
            }
            for s in log.signal_samples
        ],
        "flight_modes": [
            {"timestamp": m.timestamp, "mode": m.mode}
            for m in log.flight_modes
        ],
    }


def _parrot_log_to_dict(log: ParrotFlightLog) -> dict[str, Any]:
    return {
        "aircraft_model": log.aircraft_model,
        "aircraft_sn": log.aircraft_sn,
        "firmware_version": log.firmware_version,
        "total_flight_time_s": log.total_flight_time_s,
        "max_altitude_m": log.max_altitude_m,
        "max_speed_ms": log.max_speed_ms,
        "max_distance_m": log.max_distance_m,
        "takeoff_location": log.takeoff_location,
        "landing_location": log.landing_location,
        "home_location": log.home_location,
        "gps_samples": [
            {
                "timestamp": g.timestamp, "latitude": g.latitude,
                "longitude": g.longitude, "altitude_m": g.altitude_m,
                "relative_altitude_m": g.relative_altitude_m,
                "speed_ms": g.speed_ms, "heading_deg": g.heading_deg,
                "num_satellites": g.num_satellites, "gps_fix": g.gps_fix,
            }
            for g in log.gps_samples
        ],
        "battery_samples": [
            {
                "timestamp": b.timestamp, "voltage_v": b.voltage_v,
                "current_a": b.current_a, "capacity_percent": b.capacity_percent,
                "temperature_c": b.temperature_c,
            }
            for b in log.battery_samples
        ],
        "imu_samples": [
            {
                "timestamp": imu.timestamp, "accel_x": imu.accel_x,
                "accel_y": imu.accel_y, "accel_z": imu.accel_z,
                "gyro_x": imu.gyro_x, "gyro_y": imu.gyro_y,
                "gyro_z": imu.gyro_z, "pitch_deg": imu.pitch_deg,
                "roll_deg": imu.roll_deg, "yaw_deg": imu.yaw_deg,
            }
            for imu in log.imu_samples
        ],
    }


def _pixhawk_log_to_dict(log: PixhawkFlightLog) -> dict[str, Any]:
    return {
        "vehicle_type": log.vehicle_type,
        "autopilot": log.autopilot,
        "firmware_version": log.firmware_version,
        "total_flight_time_s": log.total_flight_time_s,
        "max_altitude_m": log.max_altitude_m,
        "max_speed_ms": log.max_speed_ms,
        "max_distance_m": log.max_distance_m,
        "takeoff_location": log.takeoff_location,
        "landing_location": log.landing_location,
        "home_location": log.home_location,
        "arm_count": log.arm_count,
        "gps_samples": [
            {
                "timestamp": g.timestamp, "latitude": g.latitude,
                "longitude": g.longitude, "altitude_m": g.altitude_m,
                "relative_alt_m": g.relative_alt_m, "speed_ms": g.speed_ms,
                "heading_deg": g.heading_deg, "num_satellites": g.num_satellites,
                "hdop": g.hdop, "fix_type": g.fix_type,
            }
            for g in log.gps_samples
        ],
        "attitude_samples": [
            {
                "timestamp": a.timestamp, "roll_deg": a.roll_deg,
                "pitch_deg": a.pitch_deg, "yaw_deg": a.yaw_deg,
            }
            for a in log.attitude_samples
        ],
        "battery_samples": [
            {
                "timestamp": b.timestamp, "voltage_v": b.voltage_v,
                "current_a": b.current_a, "remaining_percent": b.remaining_percent,
                "temperature_c": b.temperature_c,
            }
            for b in log.battery_samples
        ],
    }


def _generate_summary(flight: dict, telemetry: dict, incident: dict) -> str:
    parts = []
    if flight:
        parts.append(f"Flight covered {flight.get('total_distance_m', 0):.1f}m "
                      f"with max altitude {flight.get('max_altitude_m', 0):.1f}m")
    if telemetry:
        anomalies = telemetry.get("anomalies", telemetry.get("anomaly_count", 0))
        parts.append(f"{anomalies} telemetry anomalies detected")
    if incident:
        parts.append(f"Incident category: {incident.get('incident_category', 'none')}")
    if not parts:
        return "No analysis data available."
    return ". ".join(parts) + "."


def _extract_findings(telemetry: dict, incident: dict) -> list[dict]:
    findings: list[dict] = []
    for a in telemetry.get("anomalies", []):
        findings.append({
            "type": a.get("anomaly_type", a.get("type", "anomaly")),
            "severity": a.get("severity", "info"),
            "description": a.get("description", ""),
            "timestamp": a.get("timestamp", ""),
        })
    for c in incident.get("critical_events", []):
        findings.append({
            "type": c.get("type", c.get("event_type", "critical_event")),
            "severity": c.get("severity", "critical"),
            "description": c.get("description", ""),
            "timestamp": c.get("timestamp", ""),
        })
    return findings

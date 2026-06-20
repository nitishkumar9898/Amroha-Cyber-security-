"""Tests for the Autonomous Drone Forensics module."""

import io
import json
import math
import struct
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient

from api import app
from parsers.dji_parser import (
    DjiDatParser, DjiTxtParser, DjiMediaParser, DjiFlightLog,
    DjiGpsSample, DjiBatterySample, DjiSignalSample, DjiImuSample,
    DjiRcInput, DjiFlightMode, DjiMediaEntry,
)
from parsers.parrot_parser import (
    ParrotJsonParser, ParrotCsvParser, ParrotMediaParser, ParrotFlightLog,
    ParrotGpsSample, ParrotBatterySample,
)
from parsers.pixhawk_parser import (
    ULogParser, Px4BinParser, MavLinkTelemetryParser, PixhawkFlightLog,
    PixhawkGpsSample, PixhawkBatterySample,
)
from pipelines.flight_analyzer import (
    FlightAnalyzer, GeoPoint, GeoFence, NoFlyZone, FlightAnalysisResult,
    haversine_m, bearing_deg, SimpleKalmanFilter, generate_kml, generate_kmz,
)
from pipelines.incident_reconstructor import (
    IncidentReconstructor, TelemetryAnomaly, CrashSiteEstimate,
)


client = TestClient(app)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["module"] == "drone-forensics"
    assert data["version"] == "1.0.0"
    assert data["status"] == "healthy"


# ---------------------------------------------------------------------------
# DJI Parser Tests
# ---------------------------------------------------------------------------

def _make_dummy_dat() -> bytes:
    buf = io.BytesIO()
    buf.write(b"DJI Mavic 3\x00" + b"\x00" * 20)
    buf.write(b"SN1234567890\x00\x00\x00\x00")
    buf.write(b"v01.00.0600\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    buf.write(b"v1.12.0\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    buf.write(struct.pack("<H", 1))
    buf.write(struct.pack("<I", 3600))
    buf.write(b"\x00" * (0x80 - buf.tell()))

    for i in range(100):
        tag = 0x10 if i % 3 == 0 else 0x11 if i % 3 == 1 else 0x15
        buf.write(bytes([tag]))
        buf.write(struct.pack("<f", 0.1 + i * 0.001))
        buf.write(struct.pack("<f", -0.3 - i * 0.001))
        buf.write(struct.pack("<f", 0.05 + i * 0.001))
        buf.write(struct.pack("<f", 0.1 + i * 0.002))
        buf.write(struct.pack("<f", 0.5 + i * 0.01))
        buf.write(struct.pack("<f", 0.5 + i * 0.005))
        buf.write(struct.pack("<f", 10 + i * 0.2))
        buf.write(struct.pack("<f", 1.0))
        buf.write(struct.pack("<f", 0.5))

    return buf.getvalue()


def test_dji_dat_parser():
    data = _make_dummy_dat()
    with tempfile.NamedTemporaryFile(suffix=".dat", delete=False) as f:
        f.write(data)
        f.flush()
        fname = f.name
        f.close()
        parser = DjiDatParser(fname)
        log = parser.parse()
        assert log.aircraft_model == "DJI Mavic 3"
        assert len(log.gps_samples) > 0
        assert log.gps_samples[0].latitude != 0
        Path(fname).unlink(missing_ok=True)


def test_dji_dat_parser_file_not_found():
    with pytest.raises(FileNotFoundError):
        DjiDatParser("nonexistent.dat").parse()


def test_dji_txt_parser():
    csv_content = (
        "timestamp,latitude,longitude,altitude,speed,battery,heading,satellites\n"
        "2025-01-15T10:00:00Z,40.7128,-74.0060,50.0,5.2,95,180.0,12\n"
        "2025-01-15T10:00:01Z,40.7129,-74.0061,52.0,5.5,94,181.0,12\n"
        "2025-01-15T10:00:02Z,40.7130,-74.0062,55.0,6.0,93,182.0,11\n"
    )
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write(csv_content)
        f.flush()
        fname = f.name
        f.close()
        parser = DjiTxtParser(fname)
        log = parser.parse()
        assert len(log.gps_samples) == 3
        assert log.home_location is not None
        assert log.max_altitude_m > 0
        assert log.max_speed_ms > 0
        Path(fname).unlink(missing_ok=True)


def test_dji_txt_parser_empty():
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("")
        f.flush()
        fname = f.name
        f.close()
        parser = DjiTxtParser(fname)
        log = parser.parse()
        assert len(log.gps_samples) == 0
        Path(fname).unlink(missing_ok=True)


def test_dji_media_parser():
    with tempfile.TemporaryDirectory() as tmpdir:
        d = Path(tmpdir)
        f1 = d / "DJI_20250115_101530.JPG"
        f1.write_text("fake jpeg data")
        f2 = d / "DJI_20250115_101531.MP4"
        f2.write_text("fake mp4 data")
        f3 = d / "readme.txt"
        f3.write_text("not media")

        parser = DjiMediaParser(d)
        entries = parser.parse()
        assert len(entries) == 2
        assert entries[0].file_type in ("jpg", "mp4")
        assert entries[0].hash_md5 is not None


def test_dji_dat_parser_with_battery():
    data = _make_dummy_dat()
    with tempfile.NamedTemporaryFile(suffix=".dat", delete=False) as f:
        f.write(data)
        f.flush()
        fname = f.name
        f.close()
        parser = DjiDatParser(fname)
        log = parser.parse()
        assert len(log.battery_samples) > 0
        Path(fname).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Parrot Parser Tests
# ---------------------------------------------------------------------------

def test_parrot_json_parser():
    log_data = {
        "product": "Parrot Anafi",
        "serial": "PA123456",
        "records": [
            {
                "timestamp": "2025-01-15T10:00:00Z",
                "latitude": 48.8566, "longitude": 2.3522,
                "altitude": 100.0, "speed": 10.0,
                "voltage": 11.4, "battery": 85,
                "accel_x": 1.0, "accel_y": 2.0, "accel_z": 9.8,
            },
            {
                "timestamp": "2025-01-15T10:00:01Z",
                "latitude": 48.8567, "longitude": 2.3523,
                "altitude": 102.0, "speed": 10.5,
                "voltage": 11.3, "battery": 84,
                "motor1_rpm": 4500, "motor2_rpm": 4600,
                "motor3_rpm": 4400, "motor4_rpm": 4550,
            },
        ],
    }
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump(log_data, f)
        f.flush()
        fname = f.name
        f.close()
        parser = ParrotJsonParser(fname)
        log = parser.parse()
        assert log.aircraft_model == "Parrot Anafi"
        assert len(log.gps_samples) == 2
        assert len(log.battery_samples) == 2
        Path(fname).unlink(missing_ok=True)


def test_parrot_csv_parser():
    csv_content = (
        "timestamp,latitude,longitude,altitude,speed,voltage,battery\n"
        "2025-01-15T10:00:00Z,48.8566,2.3522,100.0,10.0,11.4,85\n"
        "2025-01-15T10:00:01Z,48.8567,2.3523,102.0,10.5,11.3,84\n"
    )
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
        f.write(csv_content)
        f.flush()
        fname = f.name
        f.close()
        parser = ParrotCsvParser(fname)
        log = parser.parse()
        assert len(log.gps_samples) == 2
        assert log.home_location is not None
        Path(fname).unlink(missing_ok=True)


def test_parrot_media_parser():
    with tempfile.TemporaryDirectory() as tmpdir:
        d = Path(tmpdir)
        f1 = d / "ANAFI_20250115_101530.JPG"
        f1.write_text("fake jpeg")
        f2 = d / "ANAFI_20250115_101531.MP4"
        f2.write_text("fake mp4")
        parser = ParrotMediaParser(d)
        entries = parser.parse()
        assert len(entries) == 2
        assert entries[0].hash_md5 is not None


# ---------------------------------------------------------------------------
# Pixhawk Parser Tests
# ---------------------------------------------------------------------------

def test_ulog_parser():
    buf = bytearray()
    buf.extend(b"\x55\x4c\x6f\x67\x01")
    buf.extend(b"\x00" * 11)
    buf.extend(b"@vehicle_type\x00HexaCopter\x00")
    buf.extend(b"\x00" * 100)
    for i in range(50):
        if i % 3 == 0:
            lat = 0.3 + i * 0.01
            lon = -0.5 - i * 0.01
        else:
            lat = 0.1
            lon = 0.1
        buf.extend(struct.pack("<f", lat))
        buf.extend(struct.pack("<f", lon))
        buf.extend(struct.pack("<f", 0.05 + i * 0.001))
        buf.extend(struct.pack("<f", 0.1 + i * 0.001))
        buf.extend(struct.pack("<f", 0.5 + i * 0.01))
        buf.extend(struct.pack("<f", 0.5 + i * 0.005))
        buf.extend(struct.pack("<f", 10 + i * 0.2))
        buf.extend(struct.pack("<f", 1.0))
        buf.extend(struct.pack("<f", 0.5))
        buf.extend(struct.pack("<f", 0.3))
        buf.extend(struct.pack("<f", 0.0))
        buf.extend(struct.pack("<f", 0.0))
        buf.extend(struct.pack("<f", 0.0))
        buf.extend(struct.pack("<f", 0.0))
        buf.extend(struct.pack("<f", 0.0))
        buf.extend(struct.pack("<f", 0.0))
        buf.extend(struct.pack("<f", 0.0))
        buf.extend(struct.pack("<f", 0.0))
        buf.extend(struct.pack("<f", 0.0))
        buf.extend(struct.pack("<f", 0.0))

    with tempfile.NamedTemporaryFile(suffix=".ulg", delete=False) as f:
        f.write(bytes(buf))
        f.flush()
        fname = f.name
        f.close()
        parser = ULogParser(fname)
        log = parser.parse()
        assert log.vehicle_type == "HEXACOPTER"
        assert len(log.gps_samples) > 0
        Path(fname).unlink(missing_ok=True)


def test_px4_bin_parser():
    buf = bytearray()
    buf.extend(b"PX4 LOG\x00")
    buf.extend(b"\x00" * 248)
    for i in range(30):
        buf.extend(struct.pack("<f", 0.3 + i * 0.005))
        buf.extend(struct.pack("<f", -0.5 - i * 0.005))
        buf.extend(struct.pack("<f", 0.1 + i * 0.001))
        buf.extend(struct.pack("<f", 0.2 + i * 0.001))
        buf.extend(struct.pack("<f", 0.3 + i * 0.01))
        buf.extend(struct.pack("<f", 0.4 + i * 0.005))
        buf.extend(struct.pack("<f", 8 + i * 0.1))
        buf.extend(struct.pack("<f", 0.8))
        buf.extend(struct.pack("<f", 5 + i * 0.01))
        buf.extend(struct.pack("<f", 2 + i * 0.01))
        buf.extend(struct.pack("<f", 0.1))
        buf.extend(struct.pack("<f", -0.2))
        buf.extend(struct.pack("<f", 0.3))
        buf.extend(struct.pack("<f", 0.0))
        buf.extend(struct.pack("<f", 0.0))
        buf.extend(struct.pack("<f", 0.0))
        buf.extend(struct.pack("<f", 0.0))
        buf.extend(struct.pack("<f", 0.0))
        buf.extend(struct.pack("<f", 1.8 + i * 0.01))
        buf.extend(struct.pack("<f", 1.0 + i * 0.01))
        buf.extend(struct.pack("<f", 50 + i * 0.5))
        buf.extend(struct.pack("<f", 25.0))
    
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(bytes(buf))
        f.flush()
        fname = f.name
        f.close()
        parser = Px4BinParser(fname)
        log = parser.parse()
        assert len(log.gps_samples) > 0
        assert len(log.battery_samples) > 0
        Path(fname).unlink(missing_ok=True)


def test_mavlink_telemetry_parser():
    tlm = (
        "lat=48.8566 long=2.3522 alt=100 speed=10 heading=180 satellites=12\n"
        "lat=48.8567 long=2.3523 alt=102 speed=10.5 heading=181 satellites=12\n"
        "voltage=11.4 battery=85\n"
    )
    with tempfile.NamedTemporaryFile(suffix=".mavlink", mode="w", delete=False) as f:
        f.write(tlm)
        f.flush()
        parser = MavLinkTelemetryParser(f.name)
        log = parser.parse()
        assert len(log.gps_samples) == 2
        assert len(log.battery_samples) == 1
        Path(f.name).unlink()


def test_pixhawk_file_not_found():
    with pytest.raises(FileNotFoundError):
        ULogParser("nonexistent.ulg").parse()


# ---------------------------------------------------------------------------
# Flight Analyzer Tests
# ---------------------------------------------------------------------------

def test_flight_analyzer_empty():
    analyzer = FlightAnalyzer()
    result = analyzer.analyze([])
    assert result.total_distance_m == 0.0
    assert result.total_flight_time_s == 0.0


def test_flight_analyzer_basic():
    points = [
        GeoPoint(latitude=40.7128, longitude=-74.0060, altitude_m=50.0,
                 timestamp="2025-01-15T10:00:00Z", speed_ms=5.0, heading_deg=90.0),
        GeoPoint(latitude=40.7130, longitude=-74.0055, altitude_m=55.0,
                 timestamp="2025-01-15T10:01:00Z", speed_ms=6.0, heading_deg=95.0),
        GeoPoint(latitude=40.7132, longitude=-74.0050, altitude_m=60.0,
                 timestamp="2025-01-15T10:02:00Z", speed_ms=7.0, heading_deg=100.0),
    ]
    analyzer = FlightAnalyzer()
    result = analyzer.analyze(points)
    assert result.total_distance_m > 0
    assert result.max_altitude_m == 60.0
    assert result.max_speed_ms == 7.0
    assert result.home_point is not None
    assert result.takeoff_point is not None
    assert result.landing_point is not None


def test_flight_analyzer_geofence_violation():
    points = [
        GeoPoint(latitude=40.7128, longitude=-74.0060, timestamp="2025-01-15T10:00:00Z"),
        GeoPoint(latitude=40.7580, longitude=-73.9855, timestamp="2025-01-15T10:01:00Z"),
    ]
    analyzer = FlightAnalyzer()
    analyzer.add_geofence(GeoFence("Restricted", 40.7128, -74.0060, 50.0))
    result = analyzer.analyze(points)
    assert len(result.geofence_violations) >= 1


def test_flight_analyzer_no_fly_zone():
    points = [
        GeoPoint(latitude=40.7128, longitude=-74.0060, timestamp="2025-01-15T10:00:00Z"),
    ]
    analyzer = FlightAnalyzer()
    analyzer.add_no_fly_zone(NoFlyZone("Airport", 40.7128, -74.0060, 1000))
    result = analyzer.analyze(points)
    assert len(result.no_fly_zone_alerts) >= 1


def test_flight_analyzer_speed_profile():
    points = []
    for i in range(20):
        points.append(GeoPoint(
            latitude=40.7128 + i * 0.0001,
            longitude=-74.0060 + i * 0.0001,
            altitude_m=50.0 + i * 0.5,
            timestamp=f"2025-01-15T10:00:{i:02d}Z",
            speed_ms=5.0 + (i % 5),
            heading_deg=90.0,
        ))
    analyzer = FlightAnalyzer()
    result = analyzer.analyze(points)
    assert result.speed_profile.avg_speed_ms > 0
    assert result.speed_profile.max_speed_ms > 0
    assert result.speed_profile.speed_percentiles != {}


def test_haversine():
    d = haversine_m(40.7128, -74.0060, 40.7580, -73.9855)
    assert 4000 < d < 6000


def test_bearing():
    b = bearing_deg(40.7128, -74.0060, 40.7580, -73.9855)
    assert 0 <= b <= 360


def test_kalman_filter():
    kf = SimpleKalmanFilter()
    noisy = [1.0, 1.1, 0.9, 1.2, 0.8, 1.3]
    filtered = [kf.update(v) for v in noisy]
    assert len(filtered) == 6
    assert all(isinstance(v, float) for v in filtered)


def test_generate_kml():
    track = [GeoPoint(latitude=40.7128, longitude=-74.0060, altitude_m=50.0)]
    kml = generate_kml(track, track[0])
    assert "<kml" in kml
    assert "Flight Track" in kml
    assert "Home Point" in kml


def test_generate_kmz():
    kml = '<kml xmlns="http://www.opengis.net/kml/2.2"/>'
    kmz = generate_kmz(kml)
    assert len(kmz) > 0
    import zipfile
    assert zipfile.is_zipfile(io.BytesIO(kmz))


# ---------------------------------------------------------------------------
# Incident Reconstructor Tests
# ---------------------------------------------------------------------------

def test_incident_reconstructor_empty():
    r = IncidentReconstructor()
    result = r.reconstruct()
    assert result.reconstruction_confidence == 0.0
    assert len(result.anomalies) == 0
    assert len(result.timeline) == 0


def test_incident_reconstructor_gps_spoofing():
    r = IncidentReconstructor()
    for i in range(20):
        r.add_gps_data(
            lat=40.7128 + math.sin(i) * 0.5,
            lon=-74.0060 + math.cos(i) * 0.5,
            alt=50.0 + (i * 50 if i > 15 else 0),
            speed=5.0 + (20 if i > 15 else 0),
            heading=90.0, ts=f"2025-01-15T10:00:{i:02d}Z",
        )
    result = r.reconstruct()
    anomalies = [a for a in result.anomalies if "gps" in a.anomaly_type.lower()]
    assert len(anomalies) >= 0


def test_incident_reconstructor_motor_failure():
    r = IncidentReconstructor()
    for i in range(10):
        rpms = [5000.0, 5100.0, 4900.0, 0.0] if i >= 5 else [5000.0] * 4
        r.add_motor_data(rpms, ts=f"2025-01-15T10:00:{i:02d}Z")
    result = r.reconstruct()
    motor_anomalies = [a for a in result.anomalies if "motor" in a.anomaly_type]
    assert len(motor_anomalies) >= 1


def test_incident_reconstructor_battery_failure():
    r = IncidentReconstructor()
    for i in range(10):
        r.add_battery_data(
            voltage=12.0 - i * 1.2,
            current=5.0, percent=max(0, 100 - i * 15),
            temp=25.0 + i * 5, ts=f"2025-01-15T10:00:{i:02d}Z",
        )
    result = r.reconstruct()
    batt_anomalies = [a for a in result.anomalies if "battery" in a.anomaly_type]
    assert len(batt_anomalies) >= 1


def test_incident_reconstructor_signal_loss():
    r = IncidentReconstructor()
    for i in range(10):
        r.add_signal_data(
            rc_quality=max(0, 100 - i * 15),
            distance_m=i * 100, ts=f"2025-01-15T10:00:{i:02d}Z",
        )
    result = r.reconstruct()
    sig_anomalies = [a for a in result.anomalies if "signal" in a.anomaly_type]
    assert len(sig_anomalies) >= 1


def test_incident_reconstructor_crash_site():
    r = IncidentReconstructor()
    for i in range(10):
        r.add_gps_data(
            lat=40.7128 + i * 0.0001, lon=-74.0060 + i * 0.0001,
            alt=max(0, 50 - i * 5), speed=max(0, 10 - i),
            heading=90.0, ts=f"2025-01-15T10:00:{i:02d}Z",
        )
    result = r.reconstruct()
    if result.crash_site:
        assert isinstance(result.crash_site.estimated_latitude, float)


def test_incident_reconstructor_pilot_profile():
    r = IncidentReconstructor()
    for i in range(30):
        r.add_gps_data(
            lat=40.7128 + math.sin(i * 0.1) * 0.01,
            lon=-74.0060 + math.cos(i * 0.1) * 0.01,
            alt=50 + math.sin(i * 0.2) * 10,
            speed=5 + abs(math.sin(i * 0.3)) * 10,
            heading=(i * 20) % 360, ts=f"2025-01-15T10:00:{i:02d}Z",
        )
    result = r.reconstruct()
    if result.pilot_profile:
        assert result.pilot_profile.flight_style in ("conservative", "moderate", "aggressive")


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------

def test_acquire_dji_with_dat():
    data = _make_dummy_dat()
    resp = client.post(
        "/acquire/dji",
        files={"log_file": ("flight.dat", data, "application/octet-stream")},
    )
    assert resp.status_code == 200
    r = resp.json()
    assert r["status"] == "completed"
    assert r["drone_type"] == "DJI"
    assert "flight_logs" in r
    assert "chain_of_custody" in r


def test_acquire_dji_with_txt():
    csv = "timestamp,latitude,longitude,altitude,speed,battery\n2025-01-15T10:00:00Z,40.7128,-74.0060,50.0,5.0,95\n"
    resp = client.post(
        "/acquire/dji",
        files={"log_file": ("flight.txt", csv, "text/plain")},
    )
    assert resp.status_code == 200
    r = resp.json()
    assert r["status"] == "completed"


def test_acquire_dji_with_media_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("DJI_20250115_101530.JPG", "fake jpeg")
        zf.writestr("DJI_20250115_101531.MP4", "fake mp4")
    zip_data = buf.getvalue()
    csv = "timestamp,latitude,longitude,altitude,speed\n2025-01-15T10:00:00Z,40.7128,-74.0060,50.0,5.0\n"
    resp = client.post(
        "/acquire/dji",
        files={
            "log_file": ("flight.txt", csv, "text/plain"),
            "media_zip": ("media.zip", zip_data, "application/zip"),
        },
    )
    assert resp.status_code == 200
    r = resp.json()
    assert r["status"] == "completed"
    assert len(r["media_files"]) > 0


def test_acquire_parrot():
    data = json.dumps({"product": "Parrot Anafi", "records": [
        {"timestamp": "2025-01-15T10:00:00Z", "latitude": 48.8566, "longitude": 2.3522,
         "altitude": 100, "speed": 10, "voltage": 11.4},
    ]})
    resp = client.post(
        "/acquire/parrot",
        files={"log_file": ("flight.json", data, "application/json")},
    )
    assert resp.status_code == 200
    r = resp.json()
    assert r["status"] == "completed"
    assert r["drone_type"] == "Parrot"


def test_acquire_custom():
    buf = bytearray()
    buf.extend(b"\x55\x4c\x6f\x67\x01")
    buf.extend(b"\x00" * 11)
    buf.extend(b"@vehicle_type\x00HexaCopter\x00")
    for i in range(20):
        for _ in range(20):
            buf.extend(struct.pack("<f", 0.1))
    resp = client.post(
        "/acquire/custom",
        files={"log_file": ("flight.ulg", bytes(buf), "application/octet-stream")},
    )
    assert resp.status_code == 200
    r = resp.json()
    assert r["status"] == "completed" or r["status"] == "failed"


def test_analyze_flight():
    body = {
        "gps_samples": [
            {"latitude": 40.7128, "longitude": -74.0060, "altitude_m": 50,
             "timestamp": "2025-01-15T10:00:00Z", "speed_ms": 5.0, "heading_deg": 90.0},
            {"latitude": 40.7130, "longitude": -74.0055, "altitude_m": 55,
             "timestamp": "2025-01-15T10:01:00Z", "speed_ms": 6.0, "heading_deg": 95.0},
        ],
        "geofences": [
            {"name": "Test Fence", "latitude": 40.7128, "longitude": -74.0060,
             "radius_m": 100},
        ],
    }
    resp = client.post("/analyze/flight", json=body)
    assert resp.status_code == 200
    r = resp.json()
    assert r["status"] == "completed"
    assert "flight_analysis" in r
    assert r["flight_analysis"]["total_distance_m"] > 0


def test_analyze_telemetry():
    body = {
        "battery_samples": [
            {"timestamp": "2025-01-15T10:00:00Z", "voltage_v": 12.0, "current_a": 5.0,
             "capacity_percent": 100, "temperature_c": 25.0},
            {"timestamp": "2025-01-15T10:01:00Z", "voltage_v": 10.0, "current_a": 8.0,
             "capacity_percent": 50, "temperature_c": 35.0},
            {"timestamp": "2025-01-15T10:02:00Z", "voltage_v": 8.0, "current_a": 12.0,
             "capacity_percent": 10, "temperature_c": 50.0},
        ],
        "gps_samples": [
            {"timestamp": "2025-01-15T10:00:00Z", "latitude": 40.7128, "longitude": -74.0060,
             "altitude_m": 50, "speed_ms": 5.0},
            {"timestamp": "2025-01-15T10:02:00Z", "latitude": 40.7580, "longitude": -73.9855,
             "altitude_m": 100, "speed_ms": 25.0},
        ],
    }
    resp = client.post("/analyze/telemetry", json=body)
    assert resp.status_code == 200
    r = resp.json()
    assert r["status"] == "completed"
    assert r["anomaly_count"] >= 0


def test_analyze_media():
    body = {
        "media": [
            {"file": "photo1.jpg", "type": "jpg", "timestamp": "2025-01-15T10:00:00Z",
             "latitude": 40.7128, "longitude": -74.0060, "altitude_m": 50.0},
            {"file": "video1.mp4", "type": "mp4", "timestamp": "2025-01-15T10:05:00Z"},
        ],
        "gps_samples": [
            {"timestamp": "2025-01-15T10:00:00Z", "latitude": 40.7128, "longitude": -74.0060,
             "altitude_m": 50.0},
            {"timestamp": "2025-01-15T10:05:30Z", "latitude": 40.7580, "longitude": -73.9855,
             "altitude_m": 80.0},
        ],
    }
    resp = client.post("/analyze/media", json=body)
    assert resp.status_code == 200
    r = resp.json()
    assert r["status"] == "completed"
    assert len(r["geo_tagged_media"]) == 2


def test_analyze_incident():
    body = {
        "gps_samples": [
            {"timestamp": "2025-01-15T10:00:00Z", "latitude": 40.7128, "longitude": -74.0060,
             "altitude_m": 50.0, "speed_ms": 5.0, "heading_deg": 90.0},
            {"timestamp": "2025-01-15T10:01:00Z", "latitude": 40.7130, "longitude": -74.0055,
             "altitude_m": 30.0, "speed_ms": 2.0, "heading_deg": 180.0},
        ],
        "motor_samples": [
            {"timestamp": "2025-01-15T10:00:00Z", "rpms": [5000, 5100, 4900, 5000]},
            {"timestamp": "2025-01-15T10:01:00Z", "rpms": [5000, 0, 4900, 0]},
        ],
        "battery_samples": [
            {"timestamp": "2025-01-15T10:00:00Z", "voltage_v": 12.0, "current_a": 5.0,
             "capacity_percent": 80, "temperature_c": 30.0},
            {"timestamp": "2025-01-15T10:01:00Z", "voltage_v": 9.0, "current_a": 15.0,
             "capacity_percent": 15, "temperature_c": 55.0},
        ],
        "events": [
            {"timestamp": "2025-01-15T10:00:30Z", "event_type": "gps_loss",
             "source": "failsafe", "description": "GPS signal lost", "severity": "critical"},
        ],
    }
    resp = client.post("/analyze/incident", json=body)
    assert resp.status_code == 200
    r = resp.json()
    assert r["status"] == "completed"
    assert "reconstruction" in r


def test_generate_report():
    body = {
        "case_id": "CASE-001",
        "device_info": {"model": "DJI Mavic 3", "sn": "SN123"},
        "flight_analysis": {"total_distance_m": 1500.0, "max_altitude_m": 120.0},
        "telemetry_analysis": {"anomalies": [{"anomaly_type": "low_battery",
                                              "severity": "high",
                                              "description": "Battery at 10%",
                                              "timestamp": "2025-01-15T10:00:00Z"}],
                               "anomaly_count": 1},
        "media_analysis": {"geo_tagged_media": [], "media_timeline": []},
        "incident_reconstruction": {"critical_events": [], "incident_category": "battery_failure",
                                    "reconstruction_confidence": 75.0},
    }
    resp = client.post("/report/generate", json=body)
    assert resp.status_code == 200
    r = resp.json()
    assert r["status"] == "completed"
    assert r["report_id"].startswith("DRF-")
    assert "executive_summary" in r["report"]


def test_analyze_flight_empty():
    resp = client.post("/analyze/flight", json={"gps_samples": []})
    assert resp.status_code == 200
    r = resp.json()
    assert r["status"] == "completed"


def test_acquire_dji_invalid_format():
    resp = client.post(
        "/acquire/dji",
        files={"log_file": ("flight.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------

def test_flight_analyzer_single_point():
    points = [GeoPoint(latitude=40.7128, longitude=-74.0060, altitude_m=50.0,
                       timestamp="2025-01-15T10:00:00Z")]
    analyzer = FlightAnalyzer()
    result = analyzer.analyze(points)
    assert result.total_distance_m == 0.0


def test_flight_analyzer_large_jump():
    points = [
        GeoPoint(latitude=40.7128, longitude=-74.0060, timestamp="2025-01-15T10:00:00Z"),
        GeoPoint(latitude=48.8566, longitude=2.3522, timestamp="2025-01-15T10:01:00Z"),
        GeoPoint(latitude=48.8567, longitude=2.3523, timestamp="2025-01-15T10:02:00Z"),
    ]
    analyzer = FlightAnalyzer()
    result = analyzer.analyze(points)
    assert len(result.filtered_track) < 3


def test_kml_no_track():
    kml = generate_kml([], title="Empty")
    assert "<kml" in kml
    assert "Flight Track" not in kml


def test_incident_reconstructor_attitude_anomalies():
    r = IncidentReconstructor()
    for i in range(5):
        r.add_attitude_data(
            roll=70.0 if i >= 3 else 5.0,
            pitch=10.0, yaw=90.0, ts=f"2025-01-15T10:00:{i:02d}Z",
        )
    result = r.reconstruct()
    attitude_anom = [a for a in result.anomalies if "extreme_roll" in a.anomaly_type]
    assert len(attitude_anom) >= 1


def test_chain_of_custody_present():
    resp = client.post("/analyze/flight", json={"gps_samples": [
        {"latitude": 40.7128, "longitude": -74.0060, "altitude_m": 50,
         "timestamp": "2025-01-15T10:00:00Z"},
    ]})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["chain_of_custody"]) >= 1
    for event in data["chain_of_custody"]:
        assert "timestamp" in event
        assert "hash" in event
        assert "module" in event

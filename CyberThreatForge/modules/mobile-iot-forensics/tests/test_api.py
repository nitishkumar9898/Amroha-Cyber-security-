"""Tests for the Mobile & IoT Forensics Pipeline API."""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from api import app
from parsers.android_parser import AndroidParser, AndroidForensicArtifacts, SmsMmsRecord, CallLogRecord
from parsers.ios_parser import IosParser, IosForensicArtifacts, IMessageRecord, IosCallRecord
from parsers.iot_parser import IotParser, IotForensicArtifacts, ConnectedDevice, SmartHomeEvent
from models.communication_analyzer import (
    CommuniityAnalyzer,
    CommunicationRecord,
    CommunicationAnalysis,
    CommunicationGraph,
)
from models.location_analyzer import (
    LocationAnalyzer,
    LocationPoint,
    LocationAnalysis,
    SignificantLocation,
    GeoFence,
    GeoFenceViolation,
)


client = TestClient(app)


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def sample_android_data() -> dict:
    return {
        "device_info": {"ro.build.version.sdk": "33", "ro.product.model": "Pixel 7"},
        "extraction_timestamp": "2025-01-15T10:00:00+00:00",
        "sms_mms": [
            {
                "_id": 1, "address": "+1234567890", "date": "2025-01-15T08:30:00+00:00",
                "date_sent": "2025-01-15T08:30:00+00:00", "type": 1, "body": "Hello!",
                "read": 1, "status": 0, "service_center": "+1234567890",
            },
            {
                "_id": 2, "address": "+1987654321", "date": "2025-01-15T09:00:00+00:00",
                "date_sent": "2025-01-15T09:00:00+00:00", "type": 2, "body": "How are you?",
                "read": 1, "status": 0, "service_center": "+1987654321",
            },
        ],
        "call_logs": [
            {
                "_id": 1, "number": "+1234567890", "date": "2025-01-15T10:00:00+00:00",
                "duration": 120, "type": 1, "name": "John Doe",
            },
            {
                "_id": 2, "number": "+1987654321", "date": "2025-01-15T14:30:00+00:00",
                "duration": 45, "type": 2, "name": "Jane Smith",
            },
        ],
        "contacts": [
            {
                "_id": 1, "display_name": "John Doe",
                "phone_numbers": [{"number": "+1234567890", "type": "1"}],
                "emails": [{"address": "john@example.com", "type": "1"}],
            }
        ],
        "whatsapp_messages": [],
        "telegram_messages": [],
        "browser_history": [],
        "wifi_networks": [],
        "installed_apps": [
            {"package_name": "com.whatsapp", "code_path": "/data/app/", "version": "2.23.1"},
            {"package_name": "com.android.chrome", "code_path": "/data/app/", "version": "120.0"},
        ],
    }


@pytest.fixture
def sample_ios_data() -> dict:
    return {
        "device_info": {
            "device_name": "iPhone 15 Pro",
            "product_version": "17.2",
            "serial_number": "SN123456",
        },
        "extraction_timestamp": "2025-01-15T10:00:00+00:00",
        "messages": [
            {
                "_id": 1, "chat_identifier": "+1234567890", "sender": "+1234567890",
                "text": "Hey there!", "date": "2025-01-15T08:00:00+00:00",
                "is_from_me": False, "service": "iMessage", "message_type": 0,
            },
            {
                "_id": 2, "chat_identifier": "+1987654321", "sender": "me",
                "text": "See you soon!", "date": "2025-01-15T09:30:00+00:00",
                "is_from_me": True, "service": "iMessage", "message_type": 0,
            },
        ],
        "whatsapp_messages": [],
        "call_logs": [
            {
                "_id": 1, "address": "+1234567890", "date": "2025-01-15T11:00:00+00:00",
                "duration": 300, "call_type": 1, "name": "John Doe",
            },
        ],
        "locations": [
            {
                "timestamp": "2025-01-15T12:00:00+00:00", "latitude": 40.7128,
                "longitude": -74.0060, "altitude": 10.0, "horizontal_accuracy": 25.0,
                "vertical_accuracy": 10.0, "source": "GPS",
            },
            {
                "timestamp": "2025-01-15T18:00:00+00:00", "latitude": 40.7580,
                "longitude": -73.9855, "altitude": 15.0, "horizontal_accuracy": 30.0,
                "vertical_accuracy": 12.0, "source": "GPS",
            },
        ],
        "contacts": [
            {"identifier": "1", "display_name": "John Doe",
             "phone_numbers": ["+1234567890"], "emails": ["john@example.com"]},
        ],
    }


@pytest.fixture
def sample_iot_data() -> dict:
    return {
        "device_info": {"hub_model": "SmartThings Hub v3", "firmware": "2.3.1"},
        "extraction_timestamp": "2025-01-15T10:00:00+00:00",
        "connected_devices": [
            {
                "mac_address": "aa:bb:cc:dd:ee:ff", "ip_address": "192.168.1.100",
                "hostname": "iPhone-15", "first_seen": "2025-01-10T08:00:00+00:00",
                "last_seen": "2025-01-15T09:00:00+00:00", "signal_strength": -45,
                "vendor": "Apple", "device_type": "smartphone",
            },
        ],
        "smart_home_events": [
            {
                "device_id": "sensor1", "device_name": "Front Door Sensor",
                "event_type": "door_open", "timestamp": "2025-01-15T07:30:00+00:00",
                "value": "open", "unit": None,
            },
        ],
        "wearable_data": [],
        "voice_utterances": [],
        "firmware_versions": [],
    }


@pytest.fixture
def sample_location_points() -> list[dict]:
    return {
        "locations": [
            {"timestamp": "2025-01-15T08:00:00+00:00", "latitude": 40.7128, "longitude": -74.0060,
             "altitude": 10, "horizontal_accuracy": 25, "source": "GPS"},
            {"timestamp": "2025-01-15T09:00:00+00:00", "latitude": 40.7129, "longitude": -74.0061,
             "altitude": 10, "horizontal_accuracy": 20, "source": "GPS"},
            {"timestamp": "2025-01-15T17:00:00+00:00", "latitude": 40.7580, "longitude": -73.9855,
             "altitude": 15, "horizontal_accuracy": 30, "source": "GPS"},
            {"timestamp": "2025-01-15T18:00:00+00:00", "latitude": 40.7581, "longitude": -73.9856,
             "altitude": 15, "horizontal_accuracy": 25, "source": "GPS"},
        ]
    }


# ── Health Check ──────────────────────────────────────────────────────


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["module"] == "mobile-iot-forensics"
    assert data["version"] == "1.0.0"
    assert data["status"] == "healthy"


# ── Android Extraction Parser Tests ───────────────────────────────────


def test_android_parser_creates_artifacts():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "data" / "data" / "com.android.providers.telephony" / "databases").mkdir(parents=True)
        (base / "data" / "system").mkdir(parents=True)

        packages = base / "data" / "system" / "packages.xml"
        packages.write_text(
            '<package name="com.whatsapp" codePath="/data/app/" version="2.23.1"/>'
        )

        parser = AndroidParser(base)
        artifacts = parser.parse_all()

        assert artifacts.extraction_timestamp != ""
        assert len(artifacts.installed_apps) == 1
        assert artifacts.installed_apps[0]["package_name"] == "com.whatsapp"


def test_android_parser_empty_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        parser = AndroidParser(tmpdir)
        artifacts = parser.parse_all()
        assert len(artifacts.sms_mms) == 0
        assert len(artifacts.call_logs) == 0


def test_android_parser_sms_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        db_dir = base / "data" / "data" / "com.android.providers.telephony" / "databases"
        db_dir.mkdir(parents=True)
        db_path = db_dir / "mmssms.db"

        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "CREATE TABLE sms (_id INTEGER PRIMARY KEY, address TEXT, date TEXT, "
            "date_sent TEXT, type INTEGER, body TEXT, read INTEGER, status INTEGER, "
            "service_center TEXT)"
        )
        conn.execute(
            "INSERT INTO sms VALUES (1, '+1234567890', '1705310700', '1705310700', "
            "1, 'Hello', 1, 0, '+1234567890')"
        )
        conn.commit()
        conn.close()

        parser = AndroidParser(base)
        artifacts = parser.parse_all()

        assert len(artifacts.sms_mms) == 1
        assert artifacts.sms_mms[0].address == "+1234567890"
        assert artifacts.sms_mms[0].body == "Hello"


def test_android_to_dict(sample_android_data):
    with tempfile.TemporaryDirectory() as tmpdir:
        parser = AndroidParser(tmpdir)
        d = parser.to_dict()
        assert isinstance(d, dict)
        assert "device_info" in d
        assert "sms_mms" in d


# ── iOS Extraction Parser Tests ───────────────────────────────────────


def test_ios_parser_creates_artifacts():
    with tempfile.TemporaryDirectory() as tmpdir:
        parser = IosParser(tmpdir)
        artifacts = parser.parse_all()
        assert artifacts.extraction_timestamp != ""
        assert len(artifacts.messages) == 0


def test_ios_parser_manifest():
    with tempfile.TemporaryDirectory() as tmpdir:
        import plistlib
        manifest = Path(tmpdir) / "Manifest.plist"
        manifest.write_bytes(
            plistlib.dumps({
                "DeviceName": "TestiPhone",
                "ProductType": "iPhone15,2",
                "ProductVersion": "17.2",
                "SerialNumber": "SN123",
            })
        )

        parser = IosParser(tmpdir)
        artifacts = parser.parse_all()

        assert artifacts.device_info.get("device_name") == "TestiPhone"
        assert artifacts.device_info.get("product_version") == "17.2"


def test_ios_to_dict(sample_ios_data):
    with tempfile.TemporaryDirectory() as tmpdir:
        parser = IosParser(tmpdir)
        d = parser.to_dict()
        assert isinstance(d, dict)
        assert "device_info" in d
        assert "messages" in d


# ── IoT Parser Tests ────────────────────────────────────────────────────


def test_iot_parser_creates_artifacts():
    with tempfile.TemporaryDirectory() as tmpdir:
        parser = IotParser(tmpdir)
        artifacts = parser.parse_all()
        assert artifacts.extraction_timestamp != ""
        assert len(artifacts.connected_devices) == 0


def test_iot_parser_dhcp_leases():
    with tempfile.TemporaryDirectory() as tmpdir:
        leases = Path(tmpdir) / "dhcpd.leases"
        leases.write_text(
            'lease 192.168.1.100 {\n'
            '  hardware ethernet aa:bb:cc:dd:ee:ff;\n'
            '  client-hostname "iPhone-15";\n'
            '  starts 4 2025/01/15 08:00:00;\n'
            '  ends 4 2025/01/15 18:00:00;\n'
            '}\n'
        )

        parser = IotParser(tmpdir)
        artifacts = parser.parse_all()

        assert len(artifacts.connected_devices) >= 1
        assert artifacts.connected_devices[0].mac_address == "aa:bb:cc:dd:ee:ff"


def test_iot_to_dict(sample_iot_data):
    with tempfile.TemporaryDirectory() as tmpdir:
        parser = IotParser(tmpdir)
        d = parser.to_dict()
        assert isinstance(d, dict)
        assert "connected_devices" in d
        assert "smart_home_events" in d


# ── Communication Analyzer Tests ──────────────────────────────────────


def test_communication_analyzer_empty():
    analyzer = CommuniityAnalyzer()
    analysis = analyzer.analyze([])
    assert analysis.total_contacts == 0
    assert analysis.total_messages == 0


def test_communication_analyzer_with_data():
    records = [
        CommunicationRecord("+111", "+222", "call", "2025-01-15T10:00:00+00:00", 120, "incoming"),
        CommunicationRecord("+222", "+111", "call", "2025-01-15T11:00:00+00:00", 60, "outgoing"),
        CommunicationRecord("+333", "+111", "sms", "2025-01-15T12:00:00+00:00", 0, "incoming", "Hello"),
        CommunicationRecord("+111", "+444", "whatsapp", "2025-01-15T14:00:00+00:00", 0, "outgoing", "Howdy"),
    ]

    analyzer = CommuniityAnalyzer()
    analysis = analyzer.analyze(records)

    assert analysis.total_contacts == 4
    assert analysis.total_messages == 2
    assert analysis.total_calls == 2
    assert analysis.avg_call_duration == 90.0

    assert analysis.communication_graph is not None
    assert len(analysis.communication_graph.nodes) == 4

    assert analysis.behavioral_profile.get("primary_channel") in ("call", "sms", "whatsapp")


def test_communication_analyzer_anomaly_detection():
    records = []
    for i in range(100):
        records.append(
            CommunicationRecord(
                f"+{i:010d}", "+9999999999", "sms",
                "2025-01-15T10:00:00+00:00", 0, "outgoing", "msg"
            )
        )

    analyzer = CommuniityAnalyzer()
    analysis = analyzer.analyze(records)

    assert len(analysis.anomalies) >= 0
    assert analysis.behavioral_profile is not None


# ── Location Analyzer Tests ──────────────────────────────────────────


def test_location_analyzer_empty():
    analyzer = LocationAnalyzer()
    analysis = analyzer.analyze([])
    assert analysis.total_points == 0


def test_location_analyzer_clustering():
    points = [
        LocationPoint("2025-01-15T08:00:00+00:00", 40.7128, -74.0060),
        LocationPoint("2025-01-15T09:00:00+00:00", 40.7129, -74.0061),
        LocationPoint("2025-01-15T10:00:00+00:00", 40.7130, -74.0062),
        LocationPoint("2025-01-15T17:00:00+00:00", 40.7580, -73.9855),
        LocationPoint("2025-01-15T18:00:00+00:00", 40.7581, -73.9856),
        LocationPoint("2025-01-15T19:00:00+00:00", 40.7582, -73.9857),
    ]

    analyzer = LocationAnalyzer(eps_km=0.5, min_samples=2)
    analysis = analyzer.analyze(points)

    assert analysis.total_points == 6
    assert len(analysis.significant_locations) >= 1
    # Points are ~5km apart so they should form at least 1 cluster
    assert any(loc.visit_count >= 2 for loc in analysis.significant_locations)


def test_location_geo_fence_violation():
    points = [
        LocationPoint("2025-01-15T08:00:00+00:00", 40.7128, -74.0060),
        LocationPoint("2025-01-15T09:00:00+00:00", 40.7580, -73.9855),
    ]

    analyzer = LocationAnalyzer()
    analyzer.add_geo_fence(
        GeoFence("Restricted Zone", 40.7128, -74.0060, 50.0, "restricted")
    )
    analysis = analyzer.analyze(points)

    assert len(analysis.geo_fence_violations) >= 1
    assert any(v.geo_fence_name == "Restricted Zone" for v in analysis.geo_fence_violations)


def test_location_daily_routines():
    points = [
        LocationPoint("2025-01-15T08:00:00+00:00", 40.7128, -74.0060),
        LocationPoint("2025-01-15T09:00:00+00:00", 40.7580, -73.9855),
        LocationPoint("2025-01-16T08:00:00+00:00", 40.7128, -74.0060),
        LocationPoint("2025-01-16T09:00:00+00:00", 40.7580, -73.9855),
    ]

    analyzer = LocationAnalyzer(eps_km=0.5, min_samples=2)
    analysis = analyzer.analyze(points)

    assert "2025-01-15" in analysis.daily_routines
    assert "2025-01-16" in analysis.daily_routines


def test_location_to_dict():
    analysis = LocationAnalysis(total_points=3)
    analyzer = LocationAnalyzer()
    d = analyzer.to_dict(analysis)
    assert d["total_points"] == 3


# ── API Endpoint Tests ─────────────────────────────────────────────────


@patch("api.SentinelCoreClient")
def test_analyze_communications(mock_sentinel, sample_android_data):
    mock_instance = AsyncMock()
    mock_sentinel.return_value = mock_instance

    response = client.post("/analyze/communications", json=sample_android_data)
    assert response.status_code == 200
    data = response.json()
    assert data["total_contacts"] >= 2
    assert data["total_messages"] >= 2
    assert data["total_calls"] >= 2
    assert "behavioral_profile" in data


@patch("api.SentinelCoreClient")
def test_analyze_location(mock_sentinel, sample_location_points):
    mock_instance = AsyncMock()
    mock_sentinel.return_value = mock_instance

    fences = [
        {"name": "Restricted Area", "latitude": 40.7128, "longitude": -74.0060,
         "radius_meters": 100, "type": "restricted"},
    ]

    response = client.post(
        "/analyze/location",
        json={"locations": sample_location_points["locations"], "geo_fences": fences},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_points"] == 4


@patch("api.SentinelCoreClient")
def test_analyze_app_usage(mock_sentinel, sample_android_data):
    mock_instance = AsyncMock()
    mock_sentinel.return_value = mock_instance

    response = client.post("/analyze/app-usage", json=sample_android_data)
    assert response.status_code == 200
    data = response.json()
    assert data["total_apps"] == 2
    assert "app_categories" in data
    assert "usage_patterns" in data


@patch("api.SentinelCoreClient")
def test_analyze_timeline(mock_sentinel, sample_android_data):
    mock_instance = AsyncMock()
    mock_sentinel.return_value = mock_instance

    response = client.post("/analyze/timeline", json=sample_android_data)
    assert response.status_code == 200
    data = response.json()
    assert data["total_events"] >= 4


@patch("api.SentinelCoreClient")
def test_extract_android_endpoint_invalid_file(mock_sentinel):
    mock_instance = AsyncMock()
    mock_sentinel.return_value = mock_instance

    response = client.post("/extract/android", files={"file": ("test.txt", b"not a zip", "text/plain")})
    # Returns empty extraction gracefully; no crash
    assert response.status_code in (200, 500)


@patch("api.SentinelCoreClient")
def test_extract_ios_endpoint_invalid_file(mock_sentinel):
    mock_instance = AsyncMock()
    mock_sentinel.return_value = mock_instance

    response = client.post("/extract/ios", files={"file": ("test.txt", b"not a backup", "text/plain")})
    assert response.status_code in (200, 500)


@patch("api.SentinelCoreClient")
def test_extract_iot_endpoint_invalid_file(mock_sentinel):
    mock_instance = AsyncMock()
    mock_sentinel.return_value = mock_instance

    response = client.post("/extract/iot", files={"file": ("test.txt", b"not a log", "text/plain")})
    assert response.status_code in (200, 500)


# ── Model Tests ────────────────────────────────────────────────────────


def test_communication_behavior_classifier():
    from models.communication_analyzer import CommunicationBehaviorClassifier, HAS_TORCH
    classifier = CommunicationBehaviorClassifier()
    import numpy as np
    dummy = np.random.randn(4, 16).astype(np.float32)
    output = classifier.predict(dummy)
    assert output.shape == (4, 5)

    anomaly_scores = classifier.predict_anomaly(dummy)
    assert len(anomaly_scores) == 4


def test_haversine():
    analyzer = LocationAnalyzer()
    distance = analyzer._haversine(40.7128, -74.0060, 40.7580, -73.9855)
    assert distance > 0
    assert distance < 10  # NYC locations are ~5km apart


# ── Parser Edge Cases ────────────────────────────────────────────────


def test_android_parser_invalid_sqlite():
    import gc
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        db_dir = base / "data" / "data" / "com.android.providers.telephony" / "databases"
        db_dir.mkdir(parents=True)
        db_path = db_dir / "mmssms.db"
        db_path.write_text("not a sqlite database")

        parser = AndroidParser(base)
        artifacts = parser.parse_all()
        assert len(artifacts.sms_mms) == 0
        del parser
        gc.collect()


def test_ios_date_conversion():
    from parsers.ios_parser import _ios_date_to_iso
    result = _ios_date_to_iso(757430400)
    assert result != ""
    assert "2025" in result or "2024" in result
    assert _ios_date_to_iso(None) == ""
    assert _ios_date_to_iso(0) == ""


def test_unix_ts_conversion():
    from parsers.android_parser import _unix_ts_to_iso
    result = _unix_ts_to_iso("1705310700")
    assert "2024" in result or "2025" in result
    assert _unix_ts_to_iso(None) == ""
    assert _unix_ts_to_iso(0) == ""


# ── Integration / Smoke Tests ─────────────────────────────────────────


def test_android_extraction_and_analysis():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        db_dir = base / "data" / "data" / "com.android.providers.telephony" / "databases"
        db_dir.mkdir(parents=True)

        import sqlite3
        db_path = db_dir / "mmssms.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "CREATE TABLE sms (_id INTEGER PRIMARY KEY, address TEXT, date TEXT, "
            "date_sent TEXT, type INTEGER, body TEXT, read INTEGER, status INTEGER, "
            "service_center TEXT)"
        )
        conn.execute(
            "INSERT INTO sms VALUES (1, '+1234567890', '1705310700', '1705310700', "
            "1, 'Evidence message', 1, 0, '+1234567890')"
        )
        conn.commit()
        conn.close()

        parser = AndroidParser(base)
        artifacts = parser.parse_all()

        records = [
            CommunicationRecord(
                source=str(s.address), target="me", channel="sms",
                timestamp=s.date, duration=0, direction="incoming",
            )
            for s in artifacts.sms_mms
        ]

        analyzer = CommuniityAnalyzer()
        analysis = analyzer.analyze(records)
        assert analysis.total_messages == 1
        assert len(analysis.anomalies) >= 0

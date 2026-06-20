import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_analyze_persistence():
    payload = {
        "scan_data": [
            {"type": "registry", "value": "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\Malicious"},
            {"type": "wmi", "value": "EventConsumer EvilConsumer"}
        ]
    }
    response = client.post("/api/apthunter/analyze-persistence", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["stealth_score"] > 0.0

def test_map_campaign():
    # First create artifacts to map
    payload = {
        "scan_data": [
            {"type": "registry", "value": "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\Malicious"},
            {"type": "wmi", "value": "EventConsumer EvilConsumer"}
        ]
    }
    pers_res = client.post("/api/apthunter/analyze-persistence", json=payload)
    art_ids = [a["id"] for a in pers_res.json()]
    
    # Map Campaign
    camp_payload = {"artifact_ids": art_ids}
    response = client.post("/api/apthunter/map-campaign", json=camp_payload)
    assert response.status_code == 200
    data = response.json()
    assert "Op-Graphite-" in data["campaign_name"]
    assert data["threat_actor_id"] is not None

def test_get_threat_actors():
    response = client.get("/api/apthunter/actors")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

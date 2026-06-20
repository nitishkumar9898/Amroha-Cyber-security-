"""backend/tests/test_supplychain.py

import json
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

# Sample SBOM payload (simplified)
sbom_payload = {
    "content": {
        "components": [
            {"name": "openssl", "version": "1.1.1"},
            {"name": "sqlite", "version": "3.36.0"}
        ]
    }
}

def test_ingest_sbom():
    response = client.post("/supplychain/ingest_sbom", json=sbom_payload)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data and data["message"] == "SBOM ingested successfully"
    assert "sbom_id" in data

def test_get_risk_graph():
    # First ingest SBOM to have data
    client.post("/supplychain/ingest_sbom", json=sbom_payload)
    response = client.get("/supplychain/risk_graph")
    assert response.status_code == 200
    data = response.json()
    # Expect a list of nodes and edges (could be empty if no risk detected)
    assert isinstance(data, dict)
    assert "nodes" in data and isinstance(data["nodes"], list)
    assert "edges" in data and isinstance(data["edges"], list)

def test_detect_anomaly():
    # Ensure some activity exists; we reuse the same SBOM
    client.post("/supplychain/ingest_sbom", json=sbom_payload)
    response = client.get("/supplychain/detect_anomaly")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Each anomaly entry should contain required keys
    for anomaly in data:
        assert "entity_id" in anomaly
        assert "anomaly_type" in anomaly
        assert "severity_score" in anomaly

def test_simulate_apt():
    response = client.post("/supplychain/simulate_apt", json={})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for sim in data:
        assert "scenario_name" in sim
        assert "description" in sim
        assert "parameters" in sim
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_analyze_campaign():
    payload = {
        "media_url": "https://fake-video-hub.example/v/123991.mp4",
        "target_entity": "Elections2028"
    }
    response = client.post("/api/campaignguard/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "campaign" in data
    assert "bot_nodes" in data
    assert "impact" in data
    assert "recommendations" in data
    
    assert data["campaign"]["target_entity"] == "Elections2028"
    assert len(data["bot_nodes"]) >= 3 # at least origin + some amplifiers
    assert data["impact"]["reach_estimate"] > 0
    assert len(data["recommendations"]) > 0

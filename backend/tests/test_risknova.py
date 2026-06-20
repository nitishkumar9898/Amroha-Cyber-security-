import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_assess_technology():
    payload = {
        "tech_name": "Autonomous LLM Agents",
        "sub_category": "Generative AI",
        "adoption_phase": "EarlyAdoption"
    }
    response = client.post("/api/risknova/assess", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Assert correct structure
    assert "profile" in data
    assert "assessment" in data
    assert "scenarios" in data
    assert "roadmaps" in data
    
    # Assert values
    assert data["profile"]["tech_name"] == "Autonomous LLM Agents"
    assert data["assessment"]["composite_score"] > 0
    
    # We expect scenarios to be generated
    assert len(data["scenarios"]) > 0
    
    # And roadmaps connected to scenarios
    assert len(data["roadmaps"]) > 0

"""Tests for the OSINT & Social Media Intelligence API."""

import pytest
from httpx import AsyncClient, ASGITransport
from api import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["module"] == "osint-social-intel"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_collect_social_media(client):
    payload = {
        "platforms": ["twitter", "reddit"],
        "query": "cybersecurity threat",
        "limit": 5,
    }
    resp = await client.post("/collect/social-media", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "cybersecurity threat"
    assert "twitter" in data["platforms"]
    assert "reddit" in data["platforms"]
    assert data["total_posts"] > 0
    assert "chain_of_custody" in data


@pytest.mark.asyncio
async def test_collect_social_media_invalid_platform(client):
    payload = {
        "platforms": ["invalid_platform"],
        "query": "test",
        "limit": 5,
    }
    resp = await client.post("/collect/social-media", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data["platforms"]["invalid_platform"]


@pytest.mark.asyncio
async def test_collect_domain(client):
    payload = {"domain": "example.com"}
    resp = await client.post("/collect/domain", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["domain"] == "example.com"
    assert "whois" in data
    assert "dns" in data
    assert "subdomains" in data
    assert "ssl" in data
    assert "reputation" in data


@pytest.mark.asyncio
async def test_collect_ip(client):
    payload = {"ip": "8.8.8.8", "scan_ports": False, "check_threat_feeds": False}
    resp = await client.post("/collect/ip", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ip"] == "8.8.8.8"
    assert "geolocation" in data
    assert "reverse_dns" in data
    assert "reputation" in data


@pytest.mark.asyncio
async def test_collect_email(client):
    payload = {"email": "test@example.com"}
    resp = await client.post("/collect/email", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert "breaches" in data
    assert "social_profiles" in data
    assert "verification" in data
    assert "risk_score" in data


@pytest.mark.asyncio
async def test_collect_email_invalid(client):
    payload = {"email": "notanemail"}
    resp = await client.post("/collect/email", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["verification"]["format_valid"] is False


@pytest.mark.asyncio
async def test_analyze_entity(client):
    payload = {
        "names": ["John Doe", "J. Doe"],
        "usernames": {"twitter": ["johndoe"], "github": ["jdoe"]},
        "emails": ["john.doe@example.com"],
        "threshold": 0.5,
    }
    resp = await client.post("/analyze/entity", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["entity_id"]
    assert len(data["names"]) > 0
    assert "twitter" in data["usernames"]
    assert data["confidence"] > 0
    assert "correlations" in data
    assert "social_graph" in data


@pytest.mark.asyncio
async def test_analyze_sentiment(client):
    payload = {
        "texts": [
            {"text": "This product is amazing and very secure!", "entity": "ProductX", "source": "twitter"},
            {"text": "Terrible experience, complete failure and data breach", "entity": "ProductX", "source": "reddit"},
            {"text": "It works fine, nothing special", "entity": "ProductX", "source": "twitter"},
        ],
        "detect_anomalies": True,
    }
    resp = await client.post("/analyze/sentiment", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["analysis_id"]
    assert data["total_texts"] == 3
    assert "overall_sentiment" in data
    assert "results" in data
    assert len(data["results"]) == 3


@pytest.mark.asyncio
async def test_analyze_network(client):
    payload = {
        "entities": [
            {"id": "1", "name": "Alice", "platforms": ["twitter"], "connections": ["2", "3"]},
            {"id": "2", "name": "Bob", "platforms": ["reddit"], "connections": ["1"]},
            {"id": "3", "name": "Charlie", "platforms": ["twitter", "github"], "connections": ["1"]},
            {"id": "4", "name": "Diana", "platforms": ["telegram"], "connections": []},
        ],
        "min_community_size": 2,
    }
    resp = await client.post("/analyze/network", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "graph_summary" in data
    assert data["graph_summary"]["node_count"] == 4
    assert "communities" in data
    assert "influence_scores" in data


@pytest.mark.asyncio
async def test_analyze_footprint(client):
    payload = {
        "target_identifier": "johndoe",
        "names": ["John Doe"],
        "usernames": {"twitter": ["johndoe"], "reddit": ["jdoe"]},
        "emails": ["john@example.com"],
        "domains": ["example.com"],
        "ips": ["8.8.8.8"],
    }
    resp = await client.post("/analyze/footprint", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["footprint_id"]
    assert data["target"] == "johndoe"
    assert "digital_presence" in data
    assert "timeline" in data
    assert "risk_assessment" in data
    assert "exposure_score" in data
    assert "chain_of_custody" in data


@pytest.mark.asyncio
async def test_analyze_footprint_minimal(client):
    payload = {
        "target_identifier": "testuser",
        "names": [],
        "usernames": {},
        "emails": [],
        "domains": [],
        "ips": [],
    }
    resp = await client.post("/analyze/footprint", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["target"] == "testuser"
    assert data["exposure_score"] == 0.0


@pytest.mark.asyncio
async def test_sentiment_trend(client):
    payload = {
        "texts": [
            {"text": "Great update, love the new features!", "entity": "App v2", "source": "twitter"},
            {"text": "Pretty good so far, minor bugs", "entity": "App v2", "source": "twitter"},
            {"text": "Awful, keeps crashing, worst update ever", "entity": "App v2", "source": "reddit"},
        ],
    }
    resp = await client.post("/analyze/sentiment", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_texts"] == 3
    assert "entity_trends" in data
    assert "App v2" in data["entity_trends"]


@pytest.mark.asyncio
async def test_health_with_client_state(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["timestamp"], str)

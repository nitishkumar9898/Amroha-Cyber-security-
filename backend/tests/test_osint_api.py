# backend/tests/test_osint_api.py

import json
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_start_crawl_and_flow():
    # Initiate a crawl job (using dummy platform/query)
    payload = {"platform": "twitter", "query": "#test", "schedule": "once"}
    resp = client.post("/api/osint/crawl", json=payload)
    assert resp.status_code == 200
    job = resp.json()
    assert job["status"] == "running" or job["status"] == "pending"
    job_id = job["id"]
    # Poll job status until completed (simplified: one fetch)
    resp_status = client.get(f"/api/osint/job/{job_id}")
    assert resp_status.status_code == 200
    status_data = resp_status.json()
    assert "status" in status_data
    # Fetch network (might be empty if no posts yet)
    net_resp = client.get(f"/api/osint/network/{job_id}")
    assert net_resp.status_code == 200
    net = net_resp.json()
    assert isinstance(net, dict)
    # Fetch misinformation list (should be list)
    mis_resp = client.get("/api/osint/misinformation")
    assert mis_resp.status_code == 200
    mis = mis_resp.json()
    assert isinstance(mis, list)
    # Fetch summary (string inside dict)
    sum_resp = client.get(f"/api/osint/summary/{job_id}")
    assert sum_resp.status_code == 200
    summ = sum_resp.json()
    assert "summary" in summ
    assert isinstance(summ["summary"], str)

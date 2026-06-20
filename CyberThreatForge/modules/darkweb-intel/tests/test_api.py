"""Tests for the Dark Web Intelligence API module."""

import json
import pytest
from fastapi.testclient import TestClient

from api import app, _strip_pii

client = TestClient(app)


class TestHealth:
    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["module"] == "darkweb-intel"


class TestCrawlTor:
    def test_rejects_non_onion(self):
        resp = client.post(
            "/crawl/tor",
            json={"url": "https://example.com", "max_pages": 1, "delay": 1.0},
        )
        assert resp.status_code == 400
        assert "onion" in resp.text.lower()

    def test_validates_schema(self):
        resp = client.post("/crawl/tor", json={})
        assert resp.status_code == 422


class TestCrawlI2P:
    def test_rejects_non_i2p(self):
        resp = client.post(
            "/crawl/i2p",
            json={"url": "https://example.com", "max_pages": 1, "delay": 1.0},
        )
        assert resp.status_code == 400
        assert "i2p" in resp.text.lower()


class TestBreachCheck:
    def test_empty_email_list(self):
        resp = client.post(
            "/monitor/breaches",
            json={"emails": [], "domains": []},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "query_id" in body
        assert body["emails_checked"] == 0
        assert body["domains_checked"] == 0

    def test_invalid_email_skipped(self):
        resp = client.post(
            "/monitor/breaches",
            json={"emails": ["notanemail"], "domains": []},
        )
        assert resp.status_code == 200
        assert resp.json()["emails_checked"] == 0


class TestMarketplace:
    def test_empty_markets_list(self):
        resp = client.post(
            "/monitor/marketplace",
            json={"markets": [], "categories": []},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["listings_scraped"] == 0


class TestActorProfiling:
    def test_profiles_from_posts(self):
        resp = client.post(
            "/analyze/actor",
            json={
                "forum_posts": [
                    "I have a new exploit for CVE-2024-1234 available.",
                    "This RAT is fully undetectable, PM for price.",
                ],
                "usernames": ["dark_hat"],
                "platforms": ["darkweb_forum"],
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "profile_id" in body
        assert isinstance(body["risk_score"], (int, float))
        assert isinstance(body["reputation_score"], (int, float))
        assert "stylometry" in body

    def test_empty_posts_rejected(self):
        resp = client.post("/analyze/actor", json={"forum_posts": []})
        assert resp.status_code == 422


class TestThreatAnalysis:
    def test_analyzes_indicators(self):
        resp = client.post(
            "/analyze/threat",
            json={
                "indicators": [
                    "8.8.8.8",
                    "malware.example.com",
                    "e99a18c428cb38d5f260853678922e03",
                ],
                "context": "ransomware campaign targeting healthcare",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "analysis_id" in body
        assert "threat_score" in body
        assert "mitre_techniques" in body
        assert "enriched_indicators" in body
        assert isinstance(body["false_positive"], bool)

    def test_empty_indicators_defaults(self):
        resp = client.post("/analyze/threat", json={"indicators": []})
        assert resp.status_code == 200
        assert resp.json()["false_positive"] is True


class TestRansomwareTracking:
    def test_no_groups_provided(self):
        resp = client.post(
            "/track/ransomware",
            json={"groups": [], "refresh": False},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "track_id" in body
        assert isinstance(body["victims"], list)


class TestPIIStripping:
    def test_strips_email(self):
        text = "Contact me at hacker@onionmail.com for details."
        cleaned = _strip_pii(text)
        assert "[EMAIL]" in cleaned
        assert "hacker@onionmail.com" not in cleaned

    def test_strips_phone(self):
        text = "Call 555-123-4567 for the dump."
        cleaned = _strip_pii(text)
        assert "[PHONE]" in cleaned

    def test_strips_ssn(self):
        text = "SSN: 123-45-6789"
        cleaned = _strip_pii(text)
        assert "[SSN]" in cleaned

    def test_strips_cc(self):
        text = "CC: 4111111111111111"
        cleaned = _strip_pii(text)
        assert "[CC]" in cleaned

    def test_preserves_normal_text(self):
        text = "This is a normal forum post about exploits."
        cleaned = _strip_pii(text)
        assert cleaned == text


class TestCrawlRequestValidation:
    def test_max_pages_bounds(self):
        resp = client.post(
            "/crawl/tor",
            json={"url": "http://xyz.onion", "max_pages": 1000, "delay": 1.0},
        )
        assert resp.status_code == 422

    def test_delay_bounds(self):
        resp = client.post(
            "/crawl/tor",
            json={"url": "http://xyz.onion", "max_pages": 5, "delay": 60},
        )
        assert resp.status_code == 422


class TestBreachRequestValidation:
    def test_too_many_emails(self):
        resp = client.post(
            "/monitor/breaches",
            json={"emails": [f"user{i}@test.com" for i in range(200)]},
        )
        assert resp.status_code == 422


class TestActorSchema:
    def test_max_posts_bounds(self):
        resp = client.post(
            "/analyze/actor",
            json={"forum_posts": ["post"] * 600},
        )
        assert resp.status_code == 422

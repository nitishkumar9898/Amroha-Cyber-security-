# backend/tests/test_behavioral_service.py
"""
Unit tests for the PsycheGuard behavioral profiling service.
"""
import pytest
from fastapi import Depends

# Import the service functions
from backend.app.services.behavioral_service import run_profile, scan_footprint, predict_insider_threat

# Mock footprint data
MOCK_FOOTPRINT = {
    "messages": [
        "Urgent! Please verify your account immediately.",
        "Click here to reset your password."
    ],
    "activities": [
        {"type": "access_sensitive_file", "detail": "read finance.xlsx"},
        {"type": "login", "detail": "user login from VPN"},
        {"type": "download_bulk_data", "detail": "downloaded 2GB of logs"},
    ],
}

def test_detect_social_engineering_scan():
    result = scan_footprint(MOCK_FOOTPRINT)
    assert result["social_engineering"]["is_social_engineering"] is True
    # Expect at least two cues detected
    assert len(result["social_engineering"]["matched_cues"]) >= 2
    assert 0 <= result["insider_threat_score"] <= 1

def test_run_profile_contains_proof_and_score():
    user_id = "test_user"
    profile = run_profile(user_id, MOCK_FOOTPRINT)
    # Basic keys
    assert profile["user_id"] == user_id
    assert "zkp_proof" in profile
    # Social engineering detection inside profile
    se = profile["social_engineering"]
    assert se["is_social_engineering"] is True
    # Insider threat score bounds
    score = profile["insider_threat_score"]
    assert 0 <= score <= 1

def test_predict_insider_threat_returns_proof():
    user_id = "insider_user"
    activities = MOCK_FOOTPRINT["activities"]
    result = predict_insider_threat(user_id, activities)
    assert result["user_id"] == user_id
    assert "insider_threat_score" in result
    assert 0 <= result["insider_threat_score"] <= 1
    assert "zkp_proof" in result

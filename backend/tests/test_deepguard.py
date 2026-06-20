import pytest
from backend.app.modules.deepfake import DeepfakeDetector
from backend.app.modules.misinfo_propagation import MisinfoPropagationTracker
from backend.app.modules.psychology import CyberPsychologyProfiler
from backend.app.services.deepguard_service import deepguard_engine

def test_deepfake_detector_authentic():
    res = DeepfakeDetector.analyze_media("clean_photo.png")
    assert res["classification"] == "AUTHENTIC"
    assert res["authenticity_score"] >= 0.5
    assert "image_forensics" in res["detectors"]
    assert "diffusion_model_denoising_artifact" in res["detectors"]["image_forensics"]
    assert res["detectors"]["image_forensics"]["diffusion_model_denoising_artifact"] == "NONE"

def test_deepfake_detector_manipulated():
    res = DeepfakeDetector.analyze_media("fake_video_clip.mp4")
    assert res["classification"] == "MANIPULATED"
    assert res["authenticity_score"] < 0.5
    assert "video_forensics" in res["detectors"]
    assert res["detectors"]["video_forensics"]["blink_rate_frequency"] == "CRITICAL_MISSING"

def test_misinfo_propagation_organic():
    res = MisinfoPropagationTracker.analyze_propagation("This is a simple query about weather schedules.")
    assert res["campaign_verdict"] == "ORGANIC_传播"
    assert res["metrics"]["bot_influence_ratio"] < 0.35
    assert res["metrics"]["effective_reproduction_number_re"] < 1.0

def test_misinfo_propagation_coordinated():
    res = MisinfoPropagationTracker.analyze_propagation("Secret minister payoff details leaked by hacker group!")
    assert res["campaign_verdict"] == "COORDINATED_INAUTHENTIC_BEHAVIOR"
    assert res["metrics"]["bot_influence_ratio"] >= 0.35
    assert len(res["darkweb_attribution"]["bot_farm_matches"]) > 0

def test_psychology_profiler_financial():
    res = CyberPsychologyProfiler.profile_incident_text("You must pay 5 BTC immediately to unlock the server files.")
    assert res["cognitive_profile"]["motivational_driver"] == "Financial Extortion"
    assert "Artificial Urgency" in res["cognitive_profile"]["manipulation_strategies_deployed"]
    assert "Loss Aversion / Hyperbolic Discounting" in res["cognitive_profile"]["targeted_cognitive_vulnerabilities"]

def test_psychology_profiler_disinfo():
    res = CyberPsychologyProfiler.profile_incident_text("A massive cover-up conspiracy has just been exposed by secret insider files!")
    assert "Outrage Amplification & Gaslighting" in res["cognitive_profile"]["manipulation_strategies_deployed"]
    assert "Confirmation Bias" in res["cognitive_profile"]["targeted_cognitive_vulnerabilities"]

def test_deepguard_service_authentic():
    res = deepguard_engine.evaluate_incident("authentic_cam_feed.jpg", "A routine report of local patrol shifts.")
    assert res["incident_verdict"] == "VERIFIED_AUTHENTIC"
    assert res["credibility_index"] > 0.70
    assert len(res["explainability_report"]["decision_rationales"]) > 0

def test_deepguard_service_malicious_campaign():
    res = deepguard_engine.evaluate_incident("fake_deepfake_video.mp4", "Secret minister payoff details leaked! Urgent cover-up exposed!")
    assert res["incident_verdict"] == "HIGH_RISK_INFLUENCE_CAMPAIGN"
    assert res["credibility_index"] < 0.40
    # Checks that all modality elements are integrated
    assert "forensic_analysis" in res["components"]
    assert "psychological_profile" in res["components"]
    assert "propagation_cascade" in res["components"]

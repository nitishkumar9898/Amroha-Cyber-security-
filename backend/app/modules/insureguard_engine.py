import joblib, os
from typing import Dict, Any, List
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), "ml_model.joblib")

def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    raise FileNotFoundError("ML model not found. Please provide a pretrained model.")

def score_risk(policy_data: Dict[str, Any]) -> Dict[str, float]:
    """Return cyber and financial risk scores (0‑1)."""
    model = load_model()
    features = np.array([
        policy_data.get("coverage_limit", 0),
        policy_data.get("premium", 0),
        policy_data.get("insured_entity", "").__hash__() % 1000,
    ]).reshape(1, -1)
    prob = model.predict_proba(features)[0, 1]
    cyber = min(1.0, prob * 0.7)
    financial = min(1.0, prob * 0.5)
    composite = 0.5 * cyber + 0.5 * financial
    return {"cyber_risk": cyber, "financial_risk": financial, "composite_score": composite}

def simulate_claim_impact(risk_scores: Dict[str, float], reported_loss: float) -> float:
    multiplier = 1 + (risk_scores["cyber_risk"] - 0.5) * 0.4
    return round(reported_loss * multiplier, 2)

def recommend_premium(policy_data: Dict[str, Any], risk_scores: Dict[str, float]) -> float:
    base = policy_data.get("premium", 0)
    adjustment = (risk_scores["composite_score"] - 0.5) * 0.2
    return round(base * (1 + adjustment), 2)

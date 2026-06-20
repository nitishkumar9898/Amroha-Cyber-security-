"""Cyber Psychology Behavioral Profiler — FastAPI Application.

Profiles cybercriminal behavior, assesses insider threat risk,
analyzes social engineering susceptibility, and generates behavioral
baselines from digital evidence using PyTorch and NLP.
"""

import hashlib
import json
import logging
import re
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from models.behavioral_rnn import (
    BehavioralGRU,
    analyze_circadian_rhythm,
    detect_anomalous_behavior,
)
from models.linguistic_profiler import (
    LinguisticProfiler,
    extract_liwc_categories,
    extract_stylometry,
)
from profiles.attacker_profile import AttackerPsychProfiler
from profiles.insight_engine import InsightEngine
from profiles.victim_profile import VictimPsychProfiler

logger = logging.getLogger("cyber_psychology")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="CyberThreatForge — Cyber Psychology Behavioral Profiler",
    version="1.0.0",
    description="Psychological profiling, threat assessment, and behavioral analysis for cyber investigations.",
)

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_linguistic_model: Optional[LinguisticProfiler] = None
_behavioral_model: Optional[BehavioralGRU] = None
_insight_engine = InsightEngine()
_attacker_profiler = AttackerPsychProfiler()
_victim_profiler = VictimPsychProfiler()

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _get_linguistic_model() -> LinguisticProfiler:
    global _linguistic_model
    if _linguistic_model is None:
        _linguistic_model = LinguisticProfiler().to(DEVICE)
        _linguistic_model.eval()
    return _linguistic_model


def _get_behavioral_model() -> BehavioralGRU:
    global _behavioral_model
    if _behavioral_model is None:
        _behavioral_model = BehavioralGRU(num_classes=4).to(DEVICE)
        _behavioral_model.eval()
    return _behavioral_model


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class DigitalEvidence(BaseModel):
    texts: list[str] = Field(default_factory=list, description="Writing samples, messages, forum posts")
    timestamps: list[str] = Field(default_factory=list, description="ISO-8601 timestamps")
    ttps: list[str] = Field(default_factory=list, description="MITRE ATT&CK technique IDs or free-text TTPs")
    platforms: list[str] = Field(default_factory=list, description="Source platforms (forum, chat, email, etc.)")
    usernames: list[str] = Field(default_factory=list)


class AttackerProfileResponse(BaseModel):
    profile_id: str
    attacker_type: str
    confidence: float
    confidence_interval: list[float]
    motivation: str
    skill_level: str
    personality_traits: dict[str, float]
    risk_factors: dict[str, float]
    escalation_likelihood: float
    behavioral_fingerprint: dict[str, Any]
    matched_ttps: list[str]
    archetype_scores: dict[str, float]
    insight: dict[str, Any]
    chain_of_custody: list[dict[str, Any]]


class InsiderThreatRequest(BaseModel):
    communications: list[dict[str, Any]] = Field(..., description="Message/call records with timestamps, channels, durations")
    access_patterns: list[dict[str, Any]] = Field(default_factory=list, description="Access logs with resource, timestamp")
    hr_indicators: list[str] = Field(default_factory=list, description="HR flags: 'grievance', 'termination_notice', 'policy_violation', etc.")
    writing_samples: list[str] = Field(default_factory=list)


class InsiderThreatResponse(BaseModel):
    assessment_id: str
    risk_score: float
    risk_level: str
    behavioral_anomalies: list[dict[str, Any]]
    linguistic_flags: dict[str, Any]
    circadian_pattern: dict[str, Any]
    confidence: float
    insight: dict[str, Any]
    chain_of_custody: list[dict[str, Any]]


class SocialEngineeringRequest(BaseModel):
    message_threads: list[list[str]] = Field(..., min_length=1, description="List of message threads (each thread is a list of strings)")
    target_role: str = Field(default="unknown", description="Victim role/position")
    context: str = Field(default="", description="Additional context about the communication")


class SocialEngineeringResponse(BaseModel):
    analysis_id: str
    susceptibility_score: float
    manipulation_tactics: list[dict[str, Any]]
    high_risk_threads: list[int]
    targeting_analysis: dict[str, Any]
    impact_assessment: dict[str, Any]
    insight: dict[str, Any]
    chain_of_custody: list[dict[str, Any]]


class LinguisticAnalysisRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=100)
    extract_personality: bool = True
    extract_stylometry: bool = True


class LinguisticAnalysisResponse(BaseModel):
    analysis_id: str
    per_text: list[dict[str, Any]]
    aggregate: dict[str, Any]
    chain_of_custody: list[dict[str, Any]]


class BehavioralTimelineRequest(BaseModel):
    communications: list[dict[str, Any]] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)


class BehavioralTimelineResponse(BaseModel):
    timeline_id: str
    total_events: int
    circadian_rhythm: dict[str, Any]
    anomalies: list[dict[str, Any]]
    behavioral_sequence: list[list[float]]
    insight: dict[str, Any]
    chain_of_custody: list[dict[str, Any]]


class VictimPsychologyRequest(BaseModel):
    incident_type: str = Field(..., description="Type of cyber incident")
    victim_role: str = Field(..., description="Victim's role or position")
    exposure_indicators: list[str] = Field(default_factory=list, description="Indicators of exposure or attack vectors")
    context: str = Field(default="", description="Free-text context about the incident")
    message_evidence: list[str] = Field(default_factory=list, description="Messages exchanged with attacker if available")


class VictimPsychologyResponse(BaseModel):
    assessment_id: str
    impact_severity: str
    impact_score: float
    targeting_analysis: dict[str, Any]
    social_engineering_vulnerability: float
    manipulation_detected: list[dict[str, Any]]
    insight: dict[str, Any]
    chain_of_custody: list[dict[str, Any]]


class EscalationPredictionRequest(BaseModel):
    behavior_sequences: list[list[float]] = Field(..., description="Sequence of behavioral feature vectors")
    timestamps: list[str] = Field(default_factory=list)
    recent_ttps: list[str] = Field(default_factory=list)


class EscalationPredictionResponse(BaseModel):
    prediction_id: str
    escalation_probability: float
    escalation_class: str
    class_probabilities: dict[str, float]
    contributing_factors: list[str]
    insight: dict[str, Any]
    chain_of_custody: list[dict[str, Any]]


class CoercionDetectionRequest(BaseModel):
    messages: list[str] = Field(..., min_length=1, max_length=500)
    metadata: Optional[dict[str, Any]] = None


class CoercionDetectionResponse(BaseModel):
    analysis_id: str
    coercion_score: float
    coercion_indicators: list[dict[str, Any]]
    high_risk_messages: list[int]
    power_imbalance: dict[str, float]
    timeline_pattern: dict[str, Any]
    chain_of_custody: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_coc(step: str, detail: str) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "step": step,
        "detail": detail,
        "handler_id": hashlib.sha256(str(uuid4()).encode()).hexdigest()[:16],
    }


def _strip_pii(text: str) -> str:
    import re
    patterns = [
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[EMAIL]"),
        (r"\b(?:\d{3}[-.]?){2}\d{4}\b", "[PHONE]"),
        (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
        (r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b", "[CC]"),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text


def _run_linguistic_analysis(texts: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    per_text = []
    liwc_all: Counter[str] = Counter()
    stylo_all: dict[str, list[float]] = {}
    sentiment_scores: list[dict[str, float]] = []

    model = _get_linguistic_model()

    for text in texts:
        cleaned = _strip_pii(text)
        liwc = extract_liwc_categories(cleaned)
        stylo = extract_stylometry(cleaned)

        for cat, score in liwc.items():
            liwc_all[cat] += score
        for key, val in stylo.items():
            if isinstance(val, (int, float)):
                stylo_all.setdefault(key, []).append(float(val))

        sentiment = {
            "positive": 0.0,
            "negative": 0.0,
            "anger": liwc.get("anger", 0),
            "fear": liwc.get("fear", 0),
            "neutral": liwc.get("assent", 0),
        }
        sentiment_scores.append(sentiment)

        deception_score = 0.0
        if liwc.get("deception_marker", 0) > 0.02 or liwc.get("negation", 0) > 0.05:
            deception_score = min(liwc["negation"] * 5 + liwc["deception_marker"] * 10, 1.0)

        per_text.append({
            "char_count": len(cleaned),
            "word_count": len(cleaned.split()),
            "liwc_categories": liwc,
            "stylometry": stylo,
            "sentiment": sentiment,
            "deception_score": round(deception_score, 4),
        })

    aggregate = {
        "text_count": len(texts),
        "avg_deception_score": round(np.mean([t["deception_score"] for t in per_text]), 4) if per_text else 0.0,
        "dominant_sentiment": max(set(t["sentiment"]["neutral"] for t in per_text), default="neutral") if per_text else "neutral",
        "liwc_summary": dict(liwc_all.most_common(15)),
        "stylometry_avg": {k: round(np.mean(v), 4) for k, v in stylo_all.items() if v} if stylo_all else {},
    }

    return per_text, aggregate


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def startup():
    _get_linguistic_model()
    _get_behavioral_model()
    logger.info("Cyber-Psychology module initialised on %s", DEVICE)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "module": "cyber-psychology",
        "device": str(DEVICE),
        "torch_version": torch.__version__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/profile/attacker", response_model=AttackerProfileResponse)
async def profile_attacker(evidence: DigitalEvidence):
    coc: list[dict[str, Any]] = [_make_coc("attacker_profile", f"Received evidence with {len(evidence.texts)} texts, {len(evidence.ttps)} TTPs")]
    try:
        profile = _attacker_profiler.profile_from_ttps(evidence.ttps, " ".join(evidence.texts))
        insight = _insight_engine.generate_attacker_insight({
            "attacker_type": profile.attacker_type,
            "confidence": profile.confidence,
            "motivation": profile.motivation,
            "skill_level": profile.skill_level,
            "escalation_likelihood": profile.escalation_likelihood,
            "personality_traits": profile.personality_traits,
            "risk_factors": profile.risk_factors,
            "matched_ttps": profile.matched_ttps,
            "archetype_scores": profile.archetype_scores,
            "behavioral_fingerprint": profile.behavioral_fingerprint,
        })
        coc.append(_make_coc("profile_complete", f"Classified as {profile.attacker_type} with confidence {profile.confidence:.3f}"))
        return AttackerProfileResponse(
            profile_id=profile.profile_id,
            attacker_type=profile.attacker_type,
            confidence=profile.confidence,
            confidence_interval=list(profile.confidence_interval),
            motivation=profile.motivation,
            skill_level=profile.skill_level,
            personality_traits=profile.personality_traits,
            risk_factors=profile.risk_factors,
            escalation_likelihood=profile.escalation_likelihood,
            behavioral_fingerprint=profile.behavioral_fingerprint,
            matched_ttps=profile.matched_ttps,
            archetype_scores=profile.archetype_scores,
            insight=insight,
            chain_of_custody=coc,
        )
    except Exception as exc:
        logger.exception("Attacker profiling failed")
        raise HTTPException(500, f"Attacker profiling failed: {exc}")


@app.post("/profile/insider-threat", response_model=InsiderThreatResponse)
async def insider_threat_assessment(req: InsiderThreatRequest):
    coc: list[dict[str, Any]] = [_make_coc("insider_assessment", f"Received {len(req.communications)} comms, {len(req.hr_indicators)} HR flags")]
    try:
        circadian = analyze_circadian_rhythm([c.get("timestamp", "") for c in req.communications])

        hourly_counts: Counter[int] = Counter()
        for c in req.communications:
            ts = c.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                hourly_counts[dt.hour] += 1
            except (ValueError, TypeError):
                pass
        behavior_sequences = []
        for h in range(24):
            behavior_sequences.append({"hour": str(h), "frequency": hourly_counts.get(h, 0), "avg_duration": 0})

        anomalies = detect_anomalous_behavior(behavior_sequences, threshold=1.8)

        linguistic_flags: dict[str, Any] = {"deception_indicators": [], "sentiment_shift": False}
        if req.writing_samples:
            per_text, agg = _run_linguistic_analysis(req.writing_samples)
            linguistic_flags["per_text"] = per_text
            linguistic_flags["aggregate"] = agg
            linguistic_flags["sentiment_shift"] = agg["avg_deception_score"] > 0.3

        risk_score = 0.2
        hr_risk_map = {"grievance": 0.3, "termination_notice": 0.4, "policy_violation": 0.25, "financial_stress": 0.3, "performance_issue": 0.2, "access_anomaly": 0.35}
        for indicator in req.hr_indicators:
            risk_score += hr_risk_map.get(indicator.lower().replace(" ", "_"), 0.1)
        risk_score += circadian.get("night_ratio", 0) * 0.15
        risk_score += len(anomalies) * 0.1
        risk_score = float(np.clip(risk_score, 0.0, 1.0))

        risk_level = "critical" if risk_score >= 0.7 else "high" if risk_score >= 0.5 else "medium" if risk_score >= 0.3 else "low"
        confidence = float(np.clip(0.5 + len(req.communications) * 0.01 + len(req.hr_indicators) * 0.05, 0.1, 0.95))

        insight = _insight_engine.generate_behavioral_insight({
            "total_events": len(req.communications),
            "circadian_rhythm": circadian,
            "anomalies": anomalies,
        })

        coc.append(_make_coc("assessment_complete", f"Risk level: {risk_level}, score: {risk_score:.3f}"))

        return InsiderThreatResponse(
            assessment_id=str(uuid4()),
            risk_score=round(risk_score, 3),
            risk_level=risk_level,
            behavioral_anomalies=anomalies,
            linguistic_flags=linguistic_flags,
            circadian_pattern=circadian,
            confidence=round(confidence, 3),
            insight=insight,
            chain_of_custody=coc,
        )
    except Exception as exc:
        logger.exception("Insider threat assessment failed")
        raise HTTPException(500, f"Insider threat assessment failed: {exc}")


@app.post("/analyze/social-engineering", response_model=SocialEngineeringResponse)
async def analyze_social_engineering(req: SocialEngineeringRequest):
    coc: list[dict[str, Any]] = [_make_coc("se_analysis", f"Analyzing {len(req.message_threads)} message threads")]
    try:
        all_messages = [msg for thread in req.message_threads for msg in thread]
        assessment = _victim_profiler.assess_impact("social_engineering", req.target_role, [], req.context)
        thread_assessment = _victim_profiler.analyze_messages(all_messages)

        high_risk_threads = []
        for idx, thread in enumerate(req.message_threads):
            thread_text = " ".join(thread)
            thread_manip = _victim_profiler._detect_manipulation(thread_text, [])
            if any(m.get("confidence", 0) > 0.6 for m in thread_manip):
                high_risk_threads.append(idx)

        insight = _insight_engine.generate_victim_insight({
            "impact_severity": assessment.impact_severity,
            "impact_score": assessment.impact_score,
            "targeting_analysis": assessment.targeting_analysis,
            "social_engineering_vulnerability": assessment.social_engineering_vulnerability,
            "manipulation_detected": thread_assessment.manipulation_detected,
            "recommendation": assessment.recommendation,
        })

        coc.append(_make_coc("se_complete", f"Found {len(thread_assessment.manipulation_detected)} manipulation tactics, {len(high_risk_threads)} high-risk threads"))

        return SocialEngineeringResponse(
            analysis_id=str(uuid4()),
            susceptibility_score=assessment.social_engineering_vulnerability,
            manipulation_tactics=thread_assessment.manipulation_detected,
            high_risk_threads=high_risk_threads,
            targeting_analysis=assessment.targeting_analysis,
            impact_assessment={
                "severity": assessment.impact_severity,
                "score": assessment.impact_score,
                "recommendation": assessment.recommendation,
            },
            insight=insight,
            chain_of_custody=coc,
        )
    except Exception as exc:
        logger.exception("Social engineering analysis failed")
        raise HTTPException(500, f"Social engineering analysis failed: {exc}")


@app.post("/analyze/linguistic", response_model=LinguisticAnalysisResponse)
async def analyze_linguistic(req: LinguisticAnalysisRequest):
    coc: list[dict[str, Any]] = [_make_coc("linguistic_analysis", f"Analyzing {len(req.texts)} text samples")]
    try:
        per_text, aggregate = _run_linguistic_analysis(req.texts)

        if req.extract_personality:
            for pt in per_text:
                stylo = pt["stylometry"]
                pt["personality_estimate"] = {
                    "openness": round(float(np.clip(stylo.get("type_token_ratio", 0.5) * 0.8 + 0.2, 0, 1)), 3),
                    "conscientiousness": round(float(np.clip((1 - stylo.get("uppercase_rate", 0)) * 0.7 + 0.3, 0, 1)), 3),
                    "extraversion": round(float(np.clip((1 - stylo.get("avg_word_length", 0.5) / 10) * 0.6 + 0.2, 0, 1)), 3),
                    "agreeableness": round(float(np.clip(1 - pt.get("deception_score", 0) * 0.8, 0, 1)), 3),
                    "neuroticism": round(float(np.clip(pt.get("deception_score", 0) * 0.7 + pt["sentiment"].get("anger", 0) * 0.5, 0, 1)), 3),
                }

        coc.append(_make_coc("linguistic_complete", f"Extracted features from {len(per_text)} texts"))

        return LinguisticAnalysisResponse(
            analysis_id=str(uuid4()),
            per_text=per_text,
            aggregate=aggregate,
            chain_of_custody=coc,
        )
    except Exception as exc:
        logger.exception("Linguistic analysis failed")
        raise HTTPException(500, f"Linguistic analysis failed: {exc}")


@app.post("/analyze/behavioral-timeline", response_model=BehavioralTimelineResponse)
async def behavioral_timeline(req: BehavioralTimelineRequest):
    coc: list[dict[str, Any]] = [_make_coc("behavioral_timeline", f"Building timeline from {len(req.communications)} comms, {len(req.events)} events")]
    try:
        all_entries = req.communications + req.events
        timestamps = [e.get("timestamp", "") for e in all_entries if e.get("timestamp")]
        circadian = analyze_circadian_rhythm(timestamps)

        hourly_agg = {}
        for e in all_entries:
            ts = e.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                hour_key = dt.strftime("%Y-%m-%d %H:00")
                if hour_key not in hourly_agg:
                    hourly_agg[hour_key] = {"count": 0, "durations": [], "channels": set()}
                hourly_agg[hour_key]["count"] += 1
                if e.get("duration"):
                    hourly_agg[hour_key]["durations"].append(float(e["duration"]))
                if e.get("channel"):
                    hourly_agg[hour_key]["channels"].add(e["channel"])
            except (ValueError, TypeError):
                pass

        behavior_sequences_list = []
        for hour_key, agg in sorted(hourly_agg.items()):
            behavior_sequences_list.append({
                "hour": str(datetime.strptime(hour_key, "%Y-%m-%d %H:00").hour),
                "frequency": agg["count"],
                "avg_duration": round(np.mean(agg["durations"]), 2) if agg["durations"] else 0,
            })

        anomalies = detect_anomalous_behavior(behavior_sequences_list, threshold=1.8)

        sequence_vectors = [[b.get("frequency", 0), b.get("avg_duration", 0)] for b in behavior_sequences_list]

        insight = _insight_engine.generate_behavioral_insight({
            "total_events": len(all_entries),
            "circadian_rhythm": circadian,
            "anomalies": anomalies,
        })

        coc.append(_make_coc("timeline_complete", f"Generated timeline with {len(all_entries)} events, {len(anomalies)} anomalies"))

        return BehavioralTimelineResponse(
            timeline_id=str(uuid4()),
            total_events=len(all_entries),
            circadian_rhythm=circadian,
            anomalies=anomalies,
            behavioral_sequence=sequence_vectors,
            insight=insight,
            chain_of_custody=coc,
        )
    except Exception as exc:
        logger.exception("Behavioral timeline failed")
        raise HTTPException(500, f"Behavioral timeline analysis failed: {exc}")


@app.post("/analyze/victim-psychology", response_model=VictimPsychologyResponse)
async def victim_psychology(req: VictimPsychologyRequest):
    coc: list[dict[str, Any]] = [_make_coc("victim_psychology", f"Assessing impact for {req.incident_type} incident")]
    try:
        assessment = _victim_profiler.assess_impact(req.incident_type, req.victim_role, req.exposure_indicators, req.context)

        if req.message_evidence:
            msg_assessment = _victim_profiler.analyze_messages(req.message_evidence)
            manipulation = msg_assessment.manipulation_detected
        else:
            manipulation = assessment.manipulation_detected

        insight = _insight_engine.generate_victim_insight({
            "impact_severity": assessment.impact_severity,
            "impact_score": assessment.impact_score,
            "targeting_analysis": assessment.targeting_analysis,
            "social_engineering_vulnerability": assessment.social_engineering_vulnerability,
            "manipulation_detected": manipulation,
            "recommendation": assessment.recommendation,
        })

        coc.append(_make_coc("victim_assessment_complete", f"Severity: {assessment.impact_severity}, score: {assessment.impact_score:.3f}"))

        return VictimPsychologyResponse(
            assessment_id=assessment.assessment_id,
            impact_severity=assessment.impact_severity,
            impact_score=assessment.impact_score,
            targeting_analysis=assessment.targeting_analysis,
            social_engineering_vulnerability=assessment.social_engineering_vulnerability,
            manipulation_detected=manipulation,
            insight=insight,
            chain_of_custody=coc,
        )
    except Exception as exc:
        logger.exception("Victim psychology assessment failed")
        raise HTTPException(500, f"Victim psychology assessment failed: {exc}")


@app.post("/predict/escalation", response_model=EscalationPredictionResponse)
async def predict_escalation(req: EscalationPredictionRequest):
    coc: list[dict[str, Any]] = [_make_coc("escalation_prediction", f"Predicting escalation from {len(req.behavior_sequences)} sequences")]
    try:
        if not req.behavior_sequences:
            raise HTTPException(400, "At least one behavior sequence is required")

        class_names = ["de_escalation", "stable", "escalating", "critical"]
        arr = np.array(req.behavior_sequences, dtype=np.float32)
        if arr.ndim == 1:
            arr = arr.reshape(1, 1, -1)
        elif arr.ndim == 2:
            arr = arr.reshape(1, *arr.shape)

        tensor = torch.from_numpy(arr).to(DEVICE)
        model = _get_behavioral_model()

        with torch.no_grad():
            logits = model(tensor)
            probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]

        class_probs = {name: round(float(prob), 4) for name, prob in zip(class_names, probs)}
        predicted_idx = int(np.argmax(probs))
        escalation_class = class_names[predicted_idx]
        escalation_prob = float(probs[predicted_idx])

        contributing = []
        if escalation_class in ("escalating", "critical"):
            contributing.append("Behavioral sequence deviation detected")
        if req.recent_ttps:
            high_risk_ttps = {"ransomware", "data_exfil", "sabotage", "privilege_abuse"}
            matched = [t for t in req.recent_ttps if t.lower().replace(" ", "_") in high_risk_ttps]
            if matched:
                contributing.append(f"High-risk TTPs detected: {', '.join(matched)}")

        insight = _insight_engine.generate_behavioral_insight({
            "total_events": len(req.behavior_sequences),
            "circadian_rhythm": {},
            "anomalies": [{"metric": "escalation", "z_score": escalation_prob * 4, "severity": "high" if escalation_prob > 0.6 else "medium"}],
        })

        coc.append(_make_coc("prediction_complete", f"Escalation class: {escalation_class}, probability: {escalation_prob:.3f}"))

        return EscalationPredictionResponse(
            prediction_id=str(uuid4()),
            escalation_probability=round(escalation_prob, 3),
            escalation_class=escalation_class,
            class_probabilities=class_probs,
            contributing_factors=contributing,
            insight=insight,
            chain_of_custody=coc,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Escalation prediction failed")
        raise HTTPException(500, f"Escalation prediction failed: {exc}")


@app.post("/analyze/coercion", response_model=CoercionDetectionResponse)
async def detect_coercion(req: CoercionDetectionRequest):
    coc: list[dict[str, Any]] = [_make_coc("coercion_detection", f"Analyzing {len(req.messages)} messages for coercion indicators")]
    try:
        coercion_indicators = []
        power_imbalance_scores: dict[str, float] = {"demand_ratio": 0.0, "threat_density": 0.0, "urgency_pressure": 0.0}
        high_risk_messages = []

        demand_patterns = [
            (r"\b(?:must|need|required|demand|expect|obligated)\b", "demand", 0.6),
            (r"\b(?:if\s+you\s+don'?t|unless\s+you|or\s+else)\b", "conditional_threat", 0.85),
            (r"\b(?:deadline|due\s+date|time\s+is\s+running|hurry)\b", "deadline_pressure", 0.7),
            (r"\b(?:expose|reveal|tell|report|release)\b", "exposure_threat", 0.8),
            (r"\b(?:pay|send|transfer|give\s+me|hand\s+over)\b", "demand_for_assets", 0.75),
            (r"\b(?:don'?t\s+(?:tell|say|contact)|keep\s+(?:quiet|silent|secret))\b", "silencing", 0.8),
            (r"\b(?:comply|cooperate|follow|obey)\b", "compliance_demand", 0.65),
            (r"\b(?:watch|follow|track|surveil|monitor)\b", "surveillance_threat", 0.7),
        ]

        for idx, msg in enumerate(req.messages):
            msg_lower = msg.lower()
            msg_indicators = []
            for pat, tactic, weight in demand_patterns:
                if re.search(pat, msg_lower):
                    msg_indicators.append({"tactic": tactic, "weight": weight, "matched": tactic in ["demand", "conditional_threat"]})
                    if tactic in ("demand", "conditional_threat", "demand_for_assets"):
                        power_imbalance_scores["demand_ratio"] += weight
                    if tactic in ("conditional_threat", "exposure_threat"):
                        power_imbalance_scores["threat_density"] += weight
                    if tactic == "deadline_pressure":
                        power_imbalance_scores["urgency_pressure"] += weight

            if msg_indicators:
                max_ci = max(m.get("weight", 0) for m in msg_indicators)
                coercion_indicators.append({
                    "message_index": idx,
                    "indicators": msg_indicators,
                    "coercion_intensity": round(min(max_ci + 0.1 * (len(msg_indicators) - 1), 1.0), 3),
                })
                if max_ci > 0.7:
                    high_risk_messages.append(idx)

        n = max(len(req.messages), 1)
        for key in power_imbalance_scores:
            power_imbalance_scores[key] = round(min(power_imbalance_scores[key] / n, 1.0), 3)

        coercion_score = round(
            min(
                (power_imbalance_scores["demand_ratio"] * 0.4
                 + power_imbalance_scores["threat_density"] * 0.35
                 + power_imbalance_scores["urgency_pressure"] * 0.25)
                + len(high_risk_messages) * 0.05,
                1.0,
            ),
            3,
        )

        coc.append(_make_coc("coercion_analysis_complete", f"Coercion score: {coercion_score}, high-risk messages: {len(high_risk_messages)}"))

        return CoercionDetectionResponse(
            analysis_id=str(uuid4()),
            coercion_score=coercion_score,
            coercion_indicators=coercion_indicators,
            high_risk_messages=high_risk_messages,
            power_imbalance=power_imbalance_scores,
            timeline_pattern={"coercion_escalation": coercion_score > 0.5, "message_count": len(req.messages)},
            chain_of_custody=coc,
        )
    except Exception as exc:
        logger.exception("Coercion detection failed")
        raise HTTPException(500, f"Coercion detection failed: {exc}")

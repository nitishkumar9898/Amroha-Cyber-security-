from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .forecasters.campaign_tracker import CampaignEvent, CampaignTracker
from .forecasters.ensemble_fuser import EnsembleFuser, ForecastOutput
from .forecasters.prophet_forecaster import ProphetForecaster
from .models.attack_graph_gnn import AttackGraphGNN
from .models.risk_scorer import RiskScorer
from .models.threat_lstm import ThreatLSTM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("predictive-analytics")

app = FastAPI(title="Predictive Analytics & Threat Forecasting", version="1.0.0")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

threat_lstm: Optional[ThreatLSTM] = None
attack_gnn: Optional[AttackGraphGNN] = None
risk_scorer: Optional[RiskScorer] = None
prophet: Optional[ProphetForecaster] = None
ensemble_fuser: Optional[EnsembleFuser] = None
campaign_tracker: Optional[CampaignTracker] = None


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ThreatForecastRequest(BaseModel):
    time_series: list[float] = Field(..., description="Historical threat level values")
    timestamps: list[str] = Field(..., description="ISO timestamps for each value")
    horizon_days: int = Field(default=7, ge=1, le=90)
    include_uncertainty: bool = True
    feature_names: Optional[list[str]] = None


class ThreatForecastResponse(BaseModel):
    forecast: dict[str, list[dict[str, Any]]]
    confidence_intervals: dict[str, list[dict[str, Any]]]
    feature_importance: Optional[dict[str, float]] = None
    model_used: str = "prophet_lstm_ensemble"
    forecast_horizons: list[int]


class AttackPredictionRequest(BaseModel):
    graph_edges: list[list[int]] = Field(..., description="Edge list [[src, dst], ...]")
    node_features: list[list[float]] = Field(..., description="Node feature vectors")
    current_targets: list[int] = Field(..., description="Currently compromised node indices")
    top_k: int = Field(default=5, ge=1, le=20)


class AttackPredictionResponse(BaseModel):
    predicted_targets: list[dict[str, Any]]
    attack_paths: list[list[int]]
    target_scores: list[float]
    risk_scores: list[float]
    edge_probabilities: list[dict[str, Any]]


class RiskScoreRequest(BaseModel):
    entity_id: str
    factors: list[dict[str, Any]] = Field(default_factory=list)
    metadata: Optional[dict[str, Any]] = None


class RiskScoreResponse(BaseModel):
    entity_id: str
    risk_score: float
    risk_level: str
    confidence: float
    factor_contributions: dict[str, float]
    top_factors: list[str]
    explanation: str
    threshold_breached: bool
    timestamp: str


class TrendAnalysisRequest(BaseModel):
    historical_data: list[dict[str, Any]] = Field(..., description="List of {timestamp, value} dicts")
    granularity: str = Field(default="daily", pattern="^(hourly|daily|weekly|monthly)$")
    seasonality_modes: Optional[list[str]] = None
    detect_changepoints: bool = True


class TrendAnalysisResponse(BaseModel):
    trend_components: dict[str, list[float]]
    seasonal_patterns: dict[str, list[float]]
    changepoints: list[dict[str, Any]]
    forecast: list[dict[str, Any]]
    anomaly_scores: list[float]
    decomposition: dict[str, list[float]]


class EscalationPredictionRequest(BaseModel):
    incident_id: str
    current_severity: float = Field(..., ge=0.0, le=1.0)
    timeline_minutes: list[int] = Field(..., description="Minutes since detection")
    severity_history: list[float] = Field(..., description="Severity at each timeline point")
    indicators: list[str] = Field(default_factory=list)
    asset_criticality: float = Field(default=0.5, ge=0.0, le=1.0)


class EscalationPredictionResponse(BaseModel):
    incident_id: str
    escalation_probability: float
    predicted_severity: float
    predicted_severity_range: dict[str, float]
    time_to_critical_minutes: Optional[float]
    contributing_factors: list[dict[str, Any]]
    recommended_actions: list[str]


class CampaignAnalysisRequest(BaseModel):
    events: list[dict[str, Any]] = Field(..., description="List of security events")
    known_campaigns: Optional[list[dict[str, Any]]] = None


class CampaignAnalysisResponse(BaseModel):
    campaigns: list[dict[str, Any]]
    unassigned_events: list[dict[str, Any]]
    new_campaigns: list[dict[str, Any]]
    clustering_metrics: dict[str, float]
    attribution_scores: list[dict[str, Any]]


class GeopoliticalForecastRequest(BaseModel):
    region: str
    historical_tensions: list[float] = Field(..., description="Monthly tension index 0-1")
    timestamps: list[str]
    include_economic_indicators: bool = False
    horizon_months: int = Field(default=6, ge=1, le=24)


class GeopoliticalForecastResponse(BaseModel):
    region: str
    forecast: list[dict[str, Any]]
    risk_trajectory: str
    key_drivers: list[str]
    confidence_intervals: list[dict[str, Any]]
    historical_analogs: list[dict[str, Any]]


class SeasonalAnalysisRequest(BaseModel):
    time_series: list[float]
    timestamps: list[str]
    expected_seasonality: Optional[list[str]] = None
    decompose: bool = True


class SeasonalAnalysisResponse(BaseModel):
    seasonal_patterns: dict[str, list[float]]
    trend: list[float]
    residual: list[float]
    periodicity_scores: dict[str, float]
    peak_seasons: list[dict[str, Any]]
    anomaly_windows: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup() -> None:
    global threat_lstm, attack_gnn, risk_scorer, prophet, ensemble_fuser, campaign_tracker
    try:
        threat_lstm = ThreatLSTM(input_size=64, hidden_size=256, num_layers=3)
        logger.info("ThreatLSTM model initialized")
    except Exception as e:
        logger.warning(f"ThreatLSTM init failed: {e}")

    try:
        attack_gnn = AttackGraphGNN(node_features=128, hidden_channels=256, num_layers=3)
        logger.info("AttackGraphGNN model initialized")
    except Exception as e:
        logger.warning(f"AttackGraphGNN init failed: {e}")

    risk_scorer = RiskScorer()
    prophet = ProphetForecaster()
    ensemble_fuser = EnsembleFuser()
    campaign_tracker = CampaignTracker()
    logger.info("All services initialized")


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _make_forecast_output(values: list[float], lower: list[float], upper: list[float],
                          timestamps: list[datetime], name: str) -> ForecastOutput:
    return ForecastOutput(
        values=np.array(values),
        lower_bound=np.array(lower),
        upper_bound=np.array(upper),
        timestamps=timestamps,
        model_name=name,
    )


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/forecast/threat", response_model=ThreatForecastResponse)
async def forecast_threat(req: ThreatForecastRequest) -> dict[str, Any]:
    if prophet is None or threat_lstm is None or ensemble_fuser is None:
        raise HTTPException(503, "Forecasting models not available")

    try:
        timestamps_dt = [datetime.fromisoformat(t) for t in req.timestamps]
        import pandas as pd
        df = pd.DataFrame({"ds": req.timestamps, "y": req.time_series})

        prophet.fit(df)
        prophet_fc = prophet.predict(periods=req.horizon_days, freq="D")
        prophet_out = _make_forecast_output(
            prophet_fc.yhat.tolist(),
            prophet_fc.yhat_lower.tolist(),
            prophet_fc.yhat_upper.tolist(),
            prophet_fc.ds,
            "prophet",
        )

        lstm_input = torch.tensor(req.time_series[-64:]).float().unsqueeze(0).unsqueeze(-1)
        lstm_padding = 64 - lstm_input.size(1)
        if lstm_padding > 0:
            lstm_input = torch.nn.functional.pad(lstm_input, (0, 0, 0, lstm_padding))
        if lstm_input.size(1) < 64:
            lstm_input = lstm_input.expand(-1, 64, -1)

        if req.include_uncertainty:
            lstm_out = threat_lstm.predict_with_uncertainty(lstm_input)
        else:
            lstm_out_raw = threat_lstm(lstm_input)
            lstm_out = {h: {"mean": lstm_out_raw[h]} for h in threat_lstm.output_horizons}

        lstm_out_obj = _make_forecast_output(
            lstm_out.get("1", {}).get("mean", torch.zeros(req.horizon_days)).squeeze().tolist() if req.horizon_days >= 1 else [],
            lstm_out.get("1", {}).get("ci_lower", torch.zeros(req.horizon_days)).squeeze().tolist() if req.horizon_days >= 1 else [],
            lstm_out.get("1", {}).get("ci_upper", torch.zeros(req.horizon_days)).squeeze().tolist() if req.horizon_days >= 1 else [],
            prophet_fc.ds[:req.horizon_days],
            "lstm",
        )

        fused = ensemble_fuser.fuse([prophet_out, lstm_out_obj])

        forecast_by_horizon: dict[str, list[dict[str, Any]]] = {}
        ci_by_horizon: dict[str, list[dict[str, Any]]] = {}
        horizons = [1, 7, 30]

        for h in horizons:
            if h <= req.horizon_days:
                forecast_by_horizon[str(h)] = [
                    {"timestamp": t.isoformat(), "value": float(v)}
                    for t, v in zip(fused.timestamps[:h], fused.values[:h])
                ]
                ci_by_horizon[str(h)] = [
                    {"timestamp": t.isoformat(), "lower": float(l), "upper": float(u)}
                    for t, l, u in zip(fused.timestamps[:h], fused.lower_bound[:h], fused.upper_bound[:h])
                ]

        return ThreatForecastResponse(
            forecast=forecast_by_horizon,
            confidence_intervals=ci_by_horizon,
            forecast_horizons=[h for h in horizons if h <= req.horizon_days],
        )

    except Exception as e:
        logger.exception("Threat forecasting failed")
        raise HTTPException(500, f"Forecasting error: {str(e)}")


@app.post("/predict/attack", response_model=AttackPredictionResponse)
async def predict_attack(req: AttackPredictionRequest) -> dict[str, Any]:
    if attack_gnn is None:
        raise HTTPException(503, "Attack prediction model not available")

    try:
        x = torch.tensor(req.node_features, dtype=torch.float32)
        edge_index = torch.tensor(req.graph_edges, dtype=torch.long).t().contiguous()
        current = torch.tensor(req.current_targets)

        with torch.no_grad():
            out = attack_gnn(x, edge_index)
            next_targets, target_scores = attack_gnn.predict_next_targets(x, edge_index, current, req.top_k)
            paths = attack_gnn.predict_attack_path(x, edge_index, int(req.current_targets[0]), max_steps=10, top_k=req.top_k)

        predicted_targets = [
            {"node": int(n), "score": float(s)}
            for n, s in zip(next_targets, target_scores)
        ]

        edge_probs = []
        row, col = edge_index
        for i in range(edge_index.size(1)):
            edge_probs.append({
                "source": int(row[i]), "target": int(col[i]),
                "probability": float(out["edge_probabilities"][i]),
            })

        risk_scores = out["risk_scores"].squeeze(-1).tolist()

        sorted_edges = sorted(edge_probs, key=lambda e: e["probability"], reverse=True)[:20]

        return AttackPredictionResponse(
            predicted_targets=predicted_targets,
            attack_paths=paths,
            target_scores=target_scores.tolist(),
            risk_scores=risk_scores,
            edge_probabilities=sorted_edges,
        )

    except Exception as e:
        logger.exception("Attack prediction failed")
        raise HTTPException(500, f"Attack prediction error: {str(e)}")


@app.post("/score/risk", response_model=RiskScoreResponse)
async def score_risk(req: RiskScoreRequest) -> dict[str, Any]:
    if risk_scorer is None:
        raise HTTPException(503, "Risk scorer not available")

    try:
        for factor in req.factors:
            risk_scorer.add_factor(
                entity_id=req.entity_id,
                factor_name=factor.get("name", "unknown"),
                base_score=factor.get("score", 0.5),
                weight=factor.get("weight", 1.0),
                decay_hours=factor.get("decay_hours"),
                evidence=factor.get("evidence", []),
                category=factor.get("category", "general"),
            )

        if req.metadata:
            risk_scorer.update_entity_metadata(req.entity_id, req.metadata)

        result = risk_scorer.compute_risk(req.entity_id, use_xai=True)
        if result is None:
            result = risk_scorer.compute_risk(req.entity_id, use_xai=True)

        if result is None:
            return RiskScoreResponse(
                entity_id=req.entity_id,
                risk_score=0.0,
                risk_level="UNKNOWN",
                confidence=0.0,
                factor_contributions={},
                top_factors=[],
                explanation="Insufficient data for risk assessment.",
                threshold_breached=False,
                timestamp=_now_iso(),
            )

        return RiskScoreResponse(
            entity_id=result.entity_id,
            risk_score=result.risk_score,
            risk_level=result.risk_level,
            confidence=result.confidence,
            factor_contributions=result.factor_contributions,
            top_factors=result.top_factors,
            explanation=result.explanation,
            threshold_breached=result.threshold_breached,
            timestamp=result.timestamp.isoformat() + "Z",
        )

    except Exception as e:
        logger.exception("Risk scoring failed")
        raise HTTPException(500, f"Risk scoring error: {str(e)}")


@app.post("/analyze/trend", response_model=TrendAnalysisResponse)
async def analyze_trend(req: TrendAnalysisRequest) -> dict[str, Any]:
    if prophet is None:
        raise HTTPException(503, "Trend analysis model not available")

    try:
        import pandas as pd
        df = pd.DataFrame(req.historical_data)
        df.columns = ["ds", "y"] if list(df.columns) == ["timestamp", "value"] else df.columns
        if "ds" not in df.columns:
            df = df.rename(columns={df.columns[0]: "ds", df.columns[1]: "y"})
        df["ds"] = pd.to_datetime(df["ds"])

        if req.seasonality_modes:
            prophet.seasonality_modes = req.seasonality_modes

        prophet.fit(df)
        decomp = prophet.get_decomposition()

        fc = prophet.predict(periods=30, freq="D")
        seasonal_patterns = {k: v.tolist() for k, v in fc.seasonal.items()} if fc.seasonal else {}

        changepoints = []
        if req.detect_changepoints:
            for cp in prophet.get_changepoints(top_k=10):
                changepoints.append({
                    "timestamp": cp.timestamp.isoformat(),
                    "delta": cp.delta,
                    "significance": cp.significance,
                })

        anomaly_df = prophet.detect_anomalies(df)
        anomaly_scores = anomaly_df["anomaly_score"].tolist()

        decomposition = {}
        if decomp:
            decomposition = {
                "trend": decomp.trend.tolist(),
                "seasonal": decomp.seasonal.tolist(),
                "residual": decomp.residual.tolist(),
            }

        forecast_list = [
            {"timestamp": t.isoformat(), "value": float(v),
             "lower": float(l), "upper": float(u)}
            for t, v, l, u in zip(fc.ds, fc.yhat, fc.yhat_lower, fc.yhat_upper)
        ]

        return TrendAnalysisResponse(
            trend_components={"trend": fc.trend.tolist()},
            seasonal_patterns=seasonal_patterns,
            changepoints=changepoints,
            forecast=forecast_list,
            anomaly_scores=anomaly_scores,
            decomposition=decomposition,
        )

    except Exception as e:
        logger.exception("Trend analysis failed")
        raise HTTPException(500, f"Trend analysis error: {str(e)}")


@app.post("/predict/escalation", response_model=EscalationPredictionResponse)
async def predict_escalation(req: EscalationPredictionRequest) -> dict[str, Any]:
    try:
        sev = np.array(req.severity_history)
        times = np.array(req.timeline_minutes)

        if len(sev) >= 2:
            gradient = np.gradient(sev, times)
            acceleration = np.gradient(gradient, times)
            velocity = gradient[-1] if len(gradient) > 0 else 0.0
            accel = acceleration[-1] if len(acceleration) > 0 else 0.0
        else:
            velocity = 0.0
            accel = 0.0

        base_escalation = req.current_severity * 0.4 + velocity * 10.0 + accel * 50.0
        indicator_boost = min(len(req.indicators) * 0.05, 0.3)
        criticality_boost = req.asset_criticality * 0.15

        escalation_prob = min(max(base_escalation + indicator_boost + criticality_boost, 0.0), 1.0)
        predicted_severity = min(max(req.current_severity + escalation_prob * 0.3, 0.0), 1.0)

        severity_range = {
            "lower": max(0.0, predicted_severity - 0.15),
            "upper": min(1.0, predicted_severity + 0.15),
        }

        time_to_critical = None
        if velocity > 0 and req.current_severity < 0.85:
            remaining = 0.85 - req.current_severity
            time_to_critical = remaining / (velocity + 1e-6)

        contrib_factors = [
            {"factor": "Current severity", "impact": round(req.current_severity * 0.4, 4)},
            {"factor": "Escalation velocity", "impact": round(float(velocity) * 10.0, 4)},
            {"factor": "Indicator count", "impact": indicator_boost},
            {"factor": "Asset criticality", "impact": criticality_boost},
        ]

        recommendations = []
        if escalation_prob > 0.7:
            recommendations.append("Escalate to SOC manager immediately")
            recommendations.append("Engage incident response team")
        if velocity > 0.05:
            recommendations.append("Implement containment measures")
            recommendations.append("Isolate affected systems")
        if len(req.indicators) > 3:
            recommendations.append("Correlate indicators across threat intelligence feeds")
        if req.asset_criticality > 0.7:
            recommendations.append("Prioritize this incident due to asset criticality")

        return EscalationPredictionResponse(
            incident_id=req.incident_id,
            escalation_probability=round(escalation_prob, 4),
            predicted_severity=round(predicted_severity, 4),
            predicted_severity_range={k: round(v, 4) for k, v in severity_range.items()},
            time_to_critical_minutes=round(time_to_critical, 2) if time_to_critical is not None else None,
            contributing_factors=contrib_factors,
            recommended_actions=recommendations,
        )

    except Exception as e:
        logger.exception("Escalation prediction failed")
        raise HTTPException(500, f"Escalation prediction error: {str(e)}")


@app.post("/analyze/campaign", response_model=CampaignAnalysisResponse)
async def analyze_campaign(req: CampaignAnalysisRequest) -> dict[str, Any]:
    if campaign_tracker is None:
        raise HTTPException(503, "Campaign tracker not available")

    try:
        events = [
            CampaignEvent(
                event_id=e.get("event_id", str(uuid.uuid4())),
                timestamp=datetime.fromisoformat(e["timestamp"]),
                source_ip=e.get("source_ip", ""),
                target_ip=e.get("target_ip", ""),
                attack_type=e.get("attack_type", ""),
                ttp_codes=e.get("ttp_codes", []),
                severity=e.get("severity", 0.5),
                indicators=e.get("indicators", []),
            )
            for e in req.events
        ]

        known = None
        if req.known_campaigns:
            known = [
                Campaign(
                    campaign_id=k["campaign_id"],
                    name=k.get("name", ""),
                    events=[],
                    primary_ttp=k.get("primary_ttp", []),
                    confidence=k.get("confidence", 0.5),
                    first_seen=datetime.fromisoformat(k["first_seen"]),
                    last_seen=datetime.fromisoformat(k["last_seen"]),
                    target_sectors=k.get("target_sectors", []),
                    attribution=k.get("attribution", "Unknown"),
                    attribution_confidence=k.get("attribution_confidence", 0.0),
                    evolution_stage=k.get("evolution_stage", "active"),
                )
                for k in req.known_campaigns
            ]

        result = campaign_tracker.process_events(events, known)

        attribution_scores = []
        for c in result.campaigns:
            attr = campaign_tracker.attribute_campaign(c.campaign_id)
            if attr:
                attribution_scores.append(attr)

        return CampaignAnalysisResponse(
            campaigns=[
                {
                    "campaign_id": c.campaign_id,
                    "name": c.name,
                    "event_count": c.event_count,
                    "primary_ttp": c.primary_ttp,
                    "confidence": c.confidence,
                    "first_seen": c.first_seen.isoformat(),
                    "last_seen": c.last_seen.isoformat(),
                    "evolution_stage": c.evolution_stage,
                    "duration_hours": c.duration_hours,
                    "intensity": c.intensity,
                    "attribution": c.attribution,
                    "attribution_confidence": c.attribution_confidence,
                }
                for c in result.campaigns
            ],
            unassigned_events=[
                {
                    "event_id": e.event_id,
                    "timestamp": e.timestamp.isoformat(),
                    "attack_type": e.attack_type,
                    "source_ip": e.source_ip,
                    "target_ip": e.target_ip,
                    "ttp_codes": e.ttp_codes,
                    "severity": e.severity,
                }
                for e in result.unassigned_events
            ],
            new_campaigns=[
                {
                    "campaign_id": c.campaign_id,
                    "name": c.name,
                    "primary_ttp": c.primary_ttp,
                }
                for c in result.new_campaigns
            ],
            clustering_metrics=result.clustering_metrics,
            attribution_scores=attribution_scores,
        )

    except Exception as e:
        logger.exception("Campaign analysis failed")
        raise HTTPException(500, f"Campaign analysis error: {str(e)}")


@app.post("/forecast/geopolitical", response_model=GeopoliticalForecastResponse)
async def forecast_geopolitical(req: GeopoliticalForecastRequest) -> dict[str, Any]:
    if prophet is None:
        raise HTTPException(503, "Geopolitical forecasting model not available")

    try:
        import pandas as pd
        df = pd.DataFrame({"ds": req.timestamps, "y": req.historical_tensions})

        prophet.seasonality_modes = ["yearly", "monthly"]
        prophet.fit(df)
        fc = prophet.predict(periods=req.horizon_months, freq="D")

        avg_tension = float(np.mean(fc.yhat[-req.horizon_months:]))
        current_tension = req.historical_tensions[-1] if req.historical_tensions else 0.5
        delta = avg_tension - current_tension

        if delta > 0.1:
            trajectory = "escalating"
        elif delta < -0.1:
            trajectory = "de-escalating"
        else:
            trajectory = "stable"

        key_drivers = [
            "Historical tension trend",
            "Rate of change in aggression indicators",
            "Seasonal geopolitical patterns",
        ]
        if req.include_economic_indicators:
            key_drivers.append("Economic pressure index")
            key_drivers.append("Trade sanction impacts")

        forecast_list = [
            {"timestamp": t.isoformat(), "tension_index": float(v),
             "lower": float(l), "upper": float(u)}
            for t, v, l, u in zip(fc.ds, fc.yhat, fc.yhat_lower, fc.yhat_upper)
        ]

        ci_list = [
            {"timestamp": t.isoformat(), "lower": float(l), "upper": float(u)}
            for t, l, u in zip(fc.ds, fc.yhat_lower, fc.yhat_upper)
        ]

        return GeopoliticalForecastResponse(
            region=req.region,
            forecast=forecast_list,
            risk_trajectory=trajectory,
            key_drivers=key_drivers,
            confidence_intervals=ci_list,
            historical_analogs=[],
        )

    except Exception as e:
        logger.exception("Geopolitical forecasting failed")
        raise HTTPException(500, f"Geopolitical forecasting error: {str(e)}")


@app.post("/analyze/seasonal", response_model=SeasonalAnalysisResponse)
async def analyze_seasonal(req: SeasonalAnalysisRequest) -> dict[str, Any]:
    if prophet is None:
        raise HTTPException(503, "Seasonal analysis model not available")

    try:
        import pandas as pd
        df = pd.DataFrame({"ds": req.timestamps, "y": req.time_series})
        df["ds"] = pd.to_datetime(df["ds"])

        if req.expected_seasonality:
            prophet.seasonality_modes = req.expected_seasonality

        prophet.fit(df)
        decomp = prophet.get_decomposition()

        periodicity_scores: dict[str, float] = {}
        if decomp is not None:
            seasonal = decomp.seasonal
            if len(seasonal) > 1:
                autocorr = np.correlate(seasonal - seasonal.mean(), seasonal - seasonal.mean(), mode="full")
                autocorr = autocorr[len(autocorr) // 2:]
                autocorr = autocorr / (autocorr[0] + 1e-8)
                for mode in prophet.seasonality_modes:
                    if mode == "hourly":
                        lag = 24
                    elif mode == "daily":
                        lag = 7
                    elif mode == "weekly":
                        lag = 4
                    elif mode == "yearly":
                        lag = 12
                    else:
                        lag = 1
                    if lag < len(autocorr):
                        periodicity_scores[mode] = float(autocorr[lag])
                    else:
                        periodicity_scores[mode] = 0.0

        trend_list = decomp.trend.tolist() if decomp else []
        seasonal_list = decomp.seasonal.tolist() if decomp else []
        residual_list = decomp.residual.tolist() if decomp else []

        fc = prophet.predict(periods=30, freq="D")

        seasonal_patterns_out: dict[str, list[float]] = {}
        if fc.seasonal:
            for mode, comp in fc.seasonal.items():
                seasonal_patterns_out[mode] = comp.tolist()

        peak_seasons = []
        if seasonal_list:
            arr = np.array(seasonal_list)
            threshold = np.percentile(arr, 80)
            for i in range(len(arr) - 1):
                if arr[i] > threshold and (i == 0 or arr[i - 1] <= arr[i]):
                    peak_seasons.append({
                        "index": i,
                        "timestamp": req.timestamps[i],
                        "magnitude": float(arr[i]),
                    })

        anomaly_windows = []
        if residual_list:
            resid = np.array(residual_list)
            resid_std = np.std(resid)
            in_anomaly = False
            window_start = 0
            for i in range(len(resid)):
                is_anomalous = abs(resid[i]) > 2 * resid_std
                if is_anomalous and not in_anomaly:
                    window_start = i
                    in_anomaly = True
                elif not is_anomalous and in_anomaly:
                    anomaly_windows.append({
                        "start_index": window_start,
                        "end_index": i - 1,
                        "start_timestamp": req.timestamps[window_start],
                        "end_timestamp": req.timestamps[i - 1],
                        "max_magnitude": float(np.max(np.abs(resid[window_start:i]))),
                    })
                    in_anomaly = False
            if in_anomaly:
                anomaly_windows.append({
                    "start_index": window_start,
                    "end_index": len(resid) - 1,
                    "start_timestamp": req.timestamps[window_start],
                    "end_timestamp": req.timestamps[-1],
                    "max_magnitude": float(np.max(np.abs(resid[window_start:]))),
                })

        return SeasonalAnalysisResponse(
            seasonal_patterns=seasonal_patterns_out,
            trend=trend_list,
            residual=residual_list,
            periodicity_scores=periodicity_scores,
            peak_seasons=peak_seasons[:10],
            anomaly_windows=anomaly_windows,
        )

    except Exception as e:
        logger.exception("Seasonal analysis failed")
        raise HTTPException(500, f"Seasonal analysis error: {str(e)}")


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "service": "predictive-analytics",
        "version": "1.0.0",
        "models_loaded": {
            "threat_lstm": threat_lstm is not None,
            "attack_gnn": attack_gnn is not None,
            "risk_scorer": risk_scorer is not None,
            "prophet": prophet is not None,
            "ensemble_fuser": ensemble_fuser is not None,
            "campaign_tracker": campaign_tracker is not None,
        },
        "device": str(DEVICE),
        "timestamp": _now_iso(),
    }

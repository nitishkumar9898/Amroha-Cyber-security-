from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

import numpy as np


@dataclass
class RiskFactor:
    """Individual risk factor with temporal tracking."""

    name: str
    base_score: float
    weight: float = 1.0
    decay_hours: float = 24.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    evidence: list[str] = field(default_factory=list)
    category: str = "general"

    @property
    def effective_score(self) -> float:
        hours_elapsed = (datetime.utcnow() - self.timestamp).total_seconds() / 3600.0
        decay = math.exp(-hours_elapsed / self.decay_hours) if self.decay_hours > 0 else 1.0
        return self.base_score * self.weight * decay


@dataclass
class RiskResult:
    """Complete risk assessment result."""

    entity_id: str
    risk_score: float
    risk_level: str
    factor_contributions: dict[str, float]
    top_factors: list[str]
    confidence: float
    explanation: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    threshold_breached: bool = False


class RiskScorer:
    """
    Real-time risk scorer with multi-factor aggregation, temporal decay,
    threshold-based alerting, and explainable AI (XAI) for risk explanation.
    """

    def __init__(
        self,
        base_threshold: float = 0.7,
        high_threshold: float = 0.85,
        critical_threshold: float = 0.95,
        default_decay_hours: float = 48.0,
    ) -> None:
        self.base_threshold = base_threshold
        self.high_threshold = high_threshold
        self.critical_threshold = critical_threshold
        self.default_decay_hours = default_decay_hours
        self._factors: dict[str, list[RiskFactor]] = {}
        self._entity_metadata: dict[str, dict[str, Any]] = {}

    def add_factor(
        self,
        entity_id: str,
        factor_name: str,
        base_score: float,
        weight: float = 1.0,
        decay_hours: Optional[float] = None,
        evidence: Optional[list[str]] = None,
        category: str = "general",
    ) -> None:
        factor = RiskFactor(
            name=factor_name,
            base_score=min(max(base_score, 0.0), 1.0),
            weight=weight,
            decay_hours=decay_hours or self.default_decay_hours,
            evidence=evidence or [],
            category=category,
        )
        if entity_id not in self._factors:
            self._factors[entity_id] = []
        self._factors[entity_id].append(factor)

    def remove_expired_factors(self, entity_id: str, max_age_hours: float = 168.0) -> None:
        if entity_id not in self._factors:
            return
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        self._factors[entity_id] = [
            f for f in self._factors[entity_id] if f.timestamp > cutoff
        ]

    def compute_risk(self, entity_id: str, use_xai: bool = True) -> Optional[RiskResult]:
        if entity_id not in self._factors or not self._factors[entity_id]:
            return None

        self.remove_expired_factors(entity_id)
        factors = self._factors[entity_id]

        if not factors:
            return None

        total_weight = sum(f.weight for f in factors)
        if total_weight == 0:
            return None

        weighted_score = sum(f.effective_score for f in factors) / total_weight
        confidence = self._compute_confidence(factors)

        factor_contributions: dict[str, float] = {
            f.name: f.effective_score / (weighted_score + 1e-8) * 100.0
            for f in factors
        }

        sorted_factors = sorted(factors, key=lambda f: f.effective_score, reverse=True)
        top_factors = [f.name for f in sorted_factors[:3]]

        risk_level = self._risk_level(weighted_score)
        threshold_breached = weighted_score >= self.base_threshold

        explanation = ""
        if use_xai:
            explanation = self._generate_explanation(
                entity_id, weighted_score, sorted_factors, factor_contributions
            )

        return RiskResult(
            entity_id=entity_id,
            risk_score=round(weighted_score, 4),
            risk_level=risk_level,
            factor_contributions=factor_contributions,
            top_factors=top_factors,
            confidence=round(confidence, 4),
            explanation=explanation,
            threshold_breached=threshold_breached,
        )

    def _compute_confidence(self, factors: list[RiskFactor]) -> float:
        if not factors:
            return 0.0
        recency = sum(
            math.exp(-((datetime.utcnow() - f.timestamp).total_seconds() / 3600.0) / 24.0)
            for f in factors
        )
        evidence_count = sum(len(f.evidence) for f in factors)
        confidence = min(1.0, (recency / len(factors)) * 0.6 + min(evidence_count, 10) / 10.0 * 0.4)
        return confidence

    def _risk_level(self, score: float) -> str:
        if score >= self.critical_threshold:
            return "CRITICAL"
        elif score >= self.high_threshold:
            return "HIGH"
        elif score >= self.base_threshold:
            return "MEDIUM"
        else:
            return "LOW"

    def _generate_explanation(
        self,
        entity_id: str,
        score: float,
        sorted_factors: list[RiskFactor],
        contributions: dict[str, float],
    ) -> str:
        top = sorted_factors[:3]
        parts: list[str] = [
            f"Risk score {score:.3f} for '{entity_id}' "
            f"({self._risk_level(score)} severity)."
        ]

        for i, f in enumerate(top, 1):
            contrib = contributions.get(f.name, 0.0)
            parts.append(
                f"Factor {i}: '{f.name}' ({f.category}) contributes "
                f"{contrib:.1f}% (base={f.base_score:.2f}, weight={f.weight:.1f})."
            )
            if f.evidence:
                evidence_str = "; ".join(f.evidence[:2])
                parts.append(f"  Evidence: {evidence_str}")

        total_weight = sum(f.weight for f in sorted_factors)
        non_top_contrib = 100.0 - sum(contributions.get(f.name, 0.0) for f in top)
        if non_top_contrib > 5.0 and len(sorted_factors) > 3:
            parts.append(f"Remaining {len(sorted_factors) - 3} factor(s) contribute "
                         f"{non_top_contrib:.1f}% collectively.")

        return " ".join(parts)

    def batch_risk_assessment(self, entity_ids: list[str]) -> dict[str, Optional[RiskResult]]:
        return {eid: self.compute_risk(eid) for eid in entity_ids}

    def set_thresholds(
        self,
        base: Optional[float] = None,
        high: Optional[float] = None,
        critical: Optional[float] = None,
    ) -> None:
        if base is not None:
            self.base_threshold = base
        if high is not None:
            self.high_threshold = high
        if critical is not None:
            self.critical_threshold = critical

    def get_risk_breakdown(self, entity_id: str) -> dict[str, Any]:
        result = self.compute_risk(entity_id, use_xai=True)
        if result is None:
            return {"entity_id": entity_id, "risk_score": 0.0, "risk_level": "UNKNOWN", "factors": []}

        factors_detail = []
        for f in self._factors.get(entity_id, []):
            factors_detail.append({
                "name": f.name,
                "base_score": f.base_score,
                "weight": f.weight,
                "decay_hours": f.decay_hours,
                "effective_score": round(f.effective_score, 4),
                "category": f.category,
                "evidence": f.evidence,
                "age_hours": round((datetime.utcnow() - f.timestamp).total_seconds() / 3600.0, 2),
            })

        return {
            "entity_id": result.entity_id,
            "risk_score": result.risk_score,
            "risk_level": result.risk_level,
            "confidence": result.confidence,
            "threshold_breached": result.threshold_breached,
            "top_factors": result.top_factors,
            "explanation": result.explanation,
            "factors_detail": factors_detail,
        }

    def update_entity_metadata(self, entity_id: str, metadata: dict[str, Any]) -> None:
        self._entity_metadata[entity_id] = metadata

    def clear_factors(self, entity_id: str) -> None:
        self._factors.pop(entity_id, None)

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

import numpy as np


@dataclass
class ForecastOutput:
    """Standardized forecast output from any model."""

    values: np.ndarray
    lower_bound: np.ndarray
    upper_bound: np.ndarray
    timestamps: list[datetime]
    model_name: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EnsembleForecast:
    """Fused ensemble forecast with calibrated confidence."""

    values: np.ndarray
    lower_bound: np.ndarray
    upper_bound: np.ndarray
    timestamps: list[datetime]
    weights: dict[str, float]
    individual_forecasts: list[ForecastOutput]
    confidence_score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class EnsembleFuser:
    """
    Ensemble fusion engine combining Prophet + LSTM + ARIMA forecasts.

    Features:
    - Weighted averaging with dynamic weight adjustment
    - Confidence calibration based on recent performance
    - Model selection based on data characteristics
    - Prediction interval construction via quantile aggregation
    """

    def __init__(
        self,
        default_weights: Optional[dict[str, float]] = None,
        performance_window: int = 10,
        adaptation_rate: float = 0.1,
        confidence_alpha: float = 0.05,
    ) -> None:
        self.default_weights = default_weights or {
            "prophet": 0.35,
            "lstm": 0.40,
            "arima": 0.25,
        }
        self.performance_window = performance_window
        self.adaptation_rate = adaptation_rate
        self.confidence_alpha = confidence_alpha

        self._weights: dict[str, float] = self.default_weights.copy()
        self._performance_history: dict[str, list[float]] = {
            k: [] for k in self.default_weights
        }
        self._data_characteristics: dict[str, Any] = {}

    def fuse(self, forecasts: list[ForecastOutput]) -> EnsembleForecast:
        if not forecasts:
            raise ValueError("At least one forecast required for fusion")

        self._validate_forecasts(forecasts)
        self._normalize_weights()

        n = len(forecasts[0].values)
        weighted_sum = np.zeros(n)
        lower_bounds = np.zeros((len(forecasts), n))
        upper_bounds = np.zeros((len(forecasts), n))

        for i, fc in enumerate(forecasts):
            w = self._weights.get(fc.model_name, 1.0 / len(forecasts))
            weighted_sum += w * fc.values
            lower_bounds[i] = fc.lower_bound
            upper_bounds[i] = fc.upper_bound

        agg_lower = np.percentile(lower_bounds, self.confidence_alpha * 50, axis=0)
        agg_upper = np.percentile(upper_bounds, 100 - self.confidence_alpha * 50, axis=0)

        individual_scores = [np.std(fc.values) for fc in forecasts]
        total_variance = np.var([fc.values for fc in forecasts], axis=0).mean()
        confidence_score = float(np.clip(1.0 - total_variance / (np.mean(individual_scores) + 1e-8), 0.0, 1.0))

        return EnsembleForecast(
            values=weighted_sum,
            lower_bound=agg_lower,
            upper_bound=agg_upper,
            timestamps=forecasts[0].timestamps,
            weights=self._weights.copy(),
            individual_forecasts=forecasts,
            confidence_score=confidence_score,
            metadata={
                "fusion_method": "weighted_average",
                "num_models": len(forecasts),
                "total_variance": float(total_variance),
            },
        )

    def _validate_forecasts(self, forecasts: list[ForecastOutput]) -> None:
        n = len(forecasts[0].values)
        for fc in forecasts:
            if len(fc.values) != n:
                raise ValueError(f"Forecast length mismatch: {len(fc.values)} != {n}")
            if len(fc.timestamps) != n:
                raise ValueError(f"Timestamp length mismatch: {len(fc.timestamps)} != {n}")

    def _normalize_weights(self) -> None:
        total = sum(self._weights.values())
        if total > 0:
            for k in self._weights:
                self._weights[k] /= total

    def update_weights(
        self,
        model_name: str,
        error: float,
    ) -> None:
        neg_error = -error
        self._performance_history[model_name].append(neg_error)
        if len(self._performance_history[model_name]) > self.performance_window:
            self._performance_history[model_name].pop(0)

        recent_perf = np.mean(self._performance_history[model_name]) if self._performance_history[model_name] else 0.0
        perf_signal = np.tanh(recent_perf * self.adaptation_rate)

        adjustment = 1.0 + perf_signal * self.adaptation_rate
        self._weights[model_name] *= adjustment
        self._normalize_weights()

    def update_weights_batch(self, errors: dict[str, float]) -> None:
        for model_name, error in errors.items():
            self.update_weights(model_name, error)

    def select_best_model(self, forecasts: list[ForecastOutput]) -> ForecastOutput:
        if not forecasts:
            raise ValueError("No forecasts to select from")
        return max(forecasts, key=lambda fc: self._weights.get(fc.model_name, 0.0))

    def set_data_characteristics(
        self,
        trend_strength: Optional[float] = None,
        seasonality_strength: Optional[float] = None,
        noise_level: Optional[float] = None,
        non_stationarity: Optional[float] = None,
    ) -> None:
        if trend_strength is not None:
            self._data_characteristics["trend_strength"] = trend_strength
        if seasonality_strength is not None:
            self._data_characteristics["seasonality_strength"] = seasonality_strength
        if noise_level is not None:
            self._data_characteristics["noise_level"] = noise_level
        if non_stationarity is not None:
            self._data_characteristics["non_stationarity"] = non_stationarity

        if trend_strength is not None and trend_strength > 0.6:
            self._weights["prophet"] *= 1.2
        if seasonality_strength is not None and seasonality_strength > 0.5:
            self._weights["prophet"] *= 1.1
        if noise_level is not None and noise_level > 0.4:
            self._weights["lstm"] *= 1.15
        if non_stationarity is not None and non_stationarity > 0.3:
            self._weights["arima"] *= 1.1

        self._normalize_weights()

    def get_weights(self) -> dict[str, float]:
        return self._weights.copy()

    def reset_weights(self) -> None:
        self._weights = self.default_weights.copy()
        self._performance_history = {k: [] for k in self.default_weights}

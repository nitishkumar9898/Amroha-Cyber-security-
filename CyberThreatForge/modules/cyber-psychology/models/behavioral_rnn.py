"""Behavioral pattern RNN — temporal behavior classification, anomaly detection, escalation prediction, circadian rhythm analysis."""

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np
import torch
import torch.nn as nn


class BehavioralGRU(nn.Module):
    """GRU-based model for temporal behavior sequence analysis."""

    def __init__(
        self,
        input_dim: int = 32,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        num_classes: int = 4,
        bidirectional: bool = True,
    ):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.num_directions = 2 if bidirectional else 1

        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
            bidirectional=bidirectional,
        )
        self.layer_norm = nn.LayerNorm(hidden_dim * self.num_directions)
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim * self.num_directions, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * self.num_directions, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_classes),
        )

    def forward(self, x: torch.Tensor, lengths: Optional[torch.Tensor] = None) -> torch.Tensor:
        batch_size, seq_len, _ = x.shape
        if lengths is not None:
            x = nn.utils.rnn.pack_padded_sequence(
                x, lengths.cpu(), batch_first=True, enforce_sorted=False
            )
        gru_out, _ = self.gru(x)
        if lengths is not None:
            gru_out, _ = nn.utils.rnn.pad_packed_sequence(gru_out, batch_first=True, total_length=seq_len)

        gru_out = self.layer_norm(gru_out)
        attn_weights = self.attention(gru_out)
        attn_weights = torch.softmax(attn_weights, dim=1)
        context = (attn_weights * gru_out).sum(dim=1)
        return self.classifier(context)


class BehaviorAnomalyDetector(nn.Module):
    """Autoencoder-based anomaly detector for behavioral sequences."""

    def __init__(self, input_dim: int = 32, encoding_dim: int = 16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, encoding_dim),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 64),
            nn.ReLU(),
            nn.Linear(64, input_dim),
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return encoded, decoded

    def anomaly_score(self, x: torch.Tensor) -> torch.Tensor:
        _, decoded = self.forward(x)
        return F.mse_loss(decoded, x, reduction="none").mean(dim=-1)


F = nn.functional


class EscalationPredictor(nn.Module):
    """Predict threat actor escalation from behavioral sequences."""

    def __init__(self, input_dim: int = 32, hidden_dim: int = 64):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.attention = nn.Linear(hidden_dim * 2, 1)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 3),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        lstm_out, _ = self.lstm(x)
        attn = torch.softmax(self.attention(lstm_out), dim=1)
        context = (attn * lstm_out).sum(dim=1)
        return torch.softmax(self.fc(context), dim=-1)


# ---------------------------------------------------------------------------
# Circadian rhythm analysis (statistical)
# ---------------------------------------------------------------------------


def analyze_circadian_rhythm(timestamps: list[str]) -> dict[str, Any]:
    """Analyze communication patterns across the 24-hour cycle."""
    if not timestamps:
        return {"hourly_distribution": {}, "peak_hour": None, "active_period": "unknown", "consistency_score": 0.0}

    hourly_counts: Counter[int] = Counter()
    for ts in timestamps:
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            hourly_counts[dt.hour] += 1
        except (ValueError, AttributeError):
            continue

    if not hourly_counts:
        return {"hourly_distribution": {}, "peak_hour": None, "active_period": "unknown", "consistency_score": 0.0}

    total = sum(hourly_counts.values())
    distribution = {str(h): round(c / total, 4) for h, c in sorted(hourly_counts.items())}
    peak_hour = max(hourly_counts, key=hourly_counts.get)

    night = sum(c for h, c in hourly_counts.items() if h < 6 or h >= 22)
    morning = sum(c for h, c in hourly_counts.items() if 6 <= h < 12)
    afternoon = sum(c for h, c in hourly_counts.items() if 12 <= h < 18)
    evening = sum(c for h, c in hourly_counts.items() if 18 <= h < 22)

    period_map = {night: "night_owl", morning: "morning_person", afternoon: "afternoon_active", evening: "evening_active"}
    active_period = period_map.get(max(period_map.keys()), "mixed")

    hours_active = len(hourly_counts)
    consistency = round(hours_active / 24, 4)

    return {
        "hourly_distribution": distribution,
        "peak_hour": peak_hour,
        "active_period": active_period,
        "consistency_score": consistency,
        "night_ratio": round(night / total, 4),
        "morning_ratio": round(morning / total, 4),
        "afternoon_ratio": round(afternoon / total, 4),
        "evening_ratio": round(evening / total, 4),
    }


def encode_behavior_sequence(
    communications: list[dict[str, Any]],
    vocab: Optional[dict[str, int]] = None,
) -> tuple[np.ndarray, Optional[dict[str, int]]]:
    """Encode communication records into a fixed-size behavior vector sequence."""
    if vocab is None:
        vocab = {"<PAD>": 0, "<UNK>": 1}
        next_id = 2

    features = []
    for comm in sorted(communications, key=lambda c: c.get("timestamp", "")):
        channel = comm.get("channel", "unknown")
        direction = comm.get("direction", "unknown")
        duration = comm.get("duration", 0)
        ts = comm.get("timestamp", "")

        if channel not in vocab:
            if vocab is None:
                vocab[channel] = next_id
                next_id += 1
            else:
                pass

        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            hour = dt.hour
            day_of_week = dt.weekday()
        except (ValueError, AttributeError):
            hour = -1
            day_of_week = -1

        vec = [
            float(vocab.get(channel, 1)),
            float(vocab.get(direction, 1)),
            float(min(duration, 3600)) / 3600.0,
            float(hour) / 23.0,
            float(day_of_week) / 6.0,
        ]
        features.append(vec)

    if not features:
        features = [[0.0] * 5]

    return np.array(features, dtype=np.float32), vocab


def detect_anomalous_behavior(
    sequences: list[dict[str, Any]],
    threshold: float = 2.0,
) -> list[dict[str, Any]]:
    """Detect anomalous behavior patterns using z-score on behavioral metrics."""
    if len(sequences) < 3:
        return []

    metrics = defaultdict(list)
    for seq in sequences:
        hour_str = seq.get("hour", "0")
        try:
            metrics["hour"].append(int(hour_str))
        except (ValueError, TypeError):
            metrics["hour"].append(0)
        metrics["frequency"].append(seq.get("frequency", 0))
        metrics["duration"].append(seq.get("avg_duration", 0))

    anomalies = []
    for key, values in metrics.items():
        if not values:
            continue
        arr = np.array(values, dtype=np.float32)
        mean, std = np.mean(arr), np.std(arr) + 1e-8
        for i, val in enumerate(values):
            z = abs(val - mean) / std
            if z > threshold and i < len(sequences):
                anomalies.append({
                    "index": i,
                    "metric": key,
                    "value": float(val),
                    "z_score": float(z),
                    "mean": float(mean),
                    "std": float(std),
                    "severity": "high" if z > 3.0 else "medium",
                })

    return anomalies

"""Communication pattern analysis with ML.

Uses PyTorch for communication behavior classification,
NetworkX for social network analysis,
and statistical methods for anomaly detection.
"""

import json
import math
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from dataclasses import dataclass, field

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    nn = None
    F = None


@dataclass
class CommunicationRecord:
    source: str
    target: str
    channel: str  # call, sms, whatsapp, telegram, imessage
    timestamp: str
    duration: int
    direction: str  # incoming, outgoing
    content_snippet: str = ""


@dataclass
class CommunicationGraph:
    nodes: list[dict] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)
    centrality: dict[str, float] = field(default_factory=dict)
    communities: list[list[str]] = field(default_factory=list)


@dataclass
class AnomalyResult:
    record_index: int
    anomaly_score: float
    anomaly_type: str
    description: str
    severity: str


@dataclass
class CommunicationAnalysis:
    total_contacts: int
    total_messages: int
    total_calls: int
    avg_call_duration: float
    busiest_hour: int
    busiest_day: str
    communication_graph: Optional[CommunicationGraph] = None
    anomalies: list[AnomalyResult] = field(default_factory=list)
    behavioral_profile: dict[str, Any] = field(default_factory=dict)
    analysis_timestamp: str = ""


if HAS_TORCH:

    class CommunicationBehaviorClassifier(nn.Module):
        """PyTorch model for classifying communication behavior patterns."""

        def __init__(self, input_dim: int = 16, hidden_dim: int = 64, num_classes: int = 5):
            super().__init__()
            self.fc1 = nn.Linear(input_dim, hidden_dim)
            self.bn1 = nn.BatchNorm1d(hidden_dim)
            self.fc2 = nn.Linear(hidden_dim, hidden_dim)
            self.bn2 = nn.BatchNorm1d(hidden_dim)
            self.fc3 = nn.Linear(hidden_dim, hidden_dim // 2)
            self.fc4 = nn.Linear(hidden_dim // 2, num_classes)
            self.dropout = nn.Dropout(0.3)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            x = F.relu(self.bn1(self.fc1(x)))
            x = self.dropout(x)
            x = F.relu(self.bn2(self.fc2(x)))
            x = self.dropout(x)
            x = F.relu(self.fc3(x))
            x = self.fc4(x)
            return x

        @torch.no_grad()
        def predict(self, features: np.ndarray) -> np.ndarray:
            self.eval()
            tensor = torch.from_numpy(features).float()
            logits = self(tensor)
            return torch.softmax(logits, dim=1).numpy()

        @torch.no_grad()
        def predict_anomaly(self, features: np.ndarray) -> np.ndarray:
            self.eval()
            tensor = torch.from_numpy(features).float()
            logits = self(tensor)
            probs = torch.softmax(logits, dim=1)
            max_probs, _ = probs.max(dim=1)
            anomaly_scores = 1.0 - max_probs
            return anomaly_scores.numpy()

else:

    class CommunicationBehaviorClassifier:
        """Stub when PyTorch is not available."""
        def __init__(self, *args, **kwargs):
            pass
        def predict(self, features: np.ndarray) -> np.ndarray:
            return np.zeros((len(features), 5))
        def predict_anomaly(self, features: np.ndarray) -> np.ndarray:
            return np.zeros(len(features))


class CommuniityAnalyzer:
    """Social network & communication pattern analyzer."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "cpu",
    ):
        self.device = torch.device(device) if HAS_TORCH else device
        self.classifier = CommunicationBehaviorClassifier()
        self._load_model(model_path)
        self._records: list[CommunicationRecord] = []

    def _load_model(self, model_path: Optional[str]) -> None:
        if model_path:
            try:
                state = torch.load(model_path, map_location=self.device, weights_only=True)
                self.classifier.load_state_dict(state)
            except Exception:
                pass

    def analyze(
        self,
        records: list[CommunicationRecord],
    ) -> CommunicationAnalysis:
        self._records = records
        analysis = CommunicationAnalysis(
            total_contacts=self._count_unique_contacts(),
            total_messages=sum(
                1 for r in records if r.channel in ("sms", "whatsapp", "telegram", "imessage")
            ),
            total_calls=sum(1 for r in records if r.channel == "call"),
            avg_call_duration=self._avg_call_duration(),
            busiest_hour=self._busiest_hour(),
            busiest_day=self._busiest_day(),
            communication_graph=self._build_graph(),
            anomalies=self._detect_anomalies(),
            behavioral_profile=self._build_behavioral_profile(),
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return analysis

    def _count_unique_contacts(self) -> int:
        contacts: set[str] = set()
        for r in self._records:
            contacts.add(r.source)
            contacts.add(r.target)
        return len(contacts)

    def _avg_call_duration(self) -> float:
        calls = [r for r in self._records if r.channel == "call" and r.duration > 0]
        if not calls:
            return 0.0
        return sum(c.duration for c in calls) / len(calls)

    def _busiest_hour(self) -> int:
        hours: list[int] = []
        for r in self._records:
            try:
                dt = datetime.fromisoformat(r.timestamp)
                hours.append(dt.hour)
            except (ValueError, TypeError):
                pass
        if not hours:
            return 0
        return Counter(hours).most_common(1)[0][0]

    def _busiest_day(self) -> str:
        days: list[int] = []
        for r in self._records:
            try:
                dt = datetime.fromisoformat(r.timestamp)
                days.append(dt.weekday())
            except (ValueError, TypeError):
                pass
        if not days:
            return "Unknown"
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return day_names[Counter(days).most_common(1)[0][0]]

    def _build_graph(self) -> CommunicationGraph:
        adjacency: dict[str, set[str]] = defaultdict(set)
        edge_counts: dict[tuple[str, str], int] = defaultdict(int)

        for r in self._records:
            adjacency[r.source].add(r.target)
            adjacency[r.target].add(r.source)
            edge_counts[(r.source, r.target)] += 1

        nodes = [
            {"id": n, "degree": len(adjacency[n])}
            for n in adjacency
        ]

        edges = [
            {
                "source": s,
                "target": t,
                "weight": c,
                "channel": self._infer_edge_channel(s, t),
            }
            for (s, t), c in edge_counts.items()
        ]

        centrality = self._compute_centrality(adjacency)

        communities = self._detect_communities(adjacency)

        return CommunicationGraph(
            nodes=nodes,
            edges=edges,
            centrality=centrality,
            communities=communities,
        )

    def _infer_edge_channel(self, source: str, target: str) -> str:
        channels_found: set[str] = set()
        for r in self._records:
            if (r.source == source and r.target == target) or \
               (r.source == target and r.target == source):
                channels_found.add(r.channel)
        return ", ".join(sorted(channels_found)) if channels_found else "unknown"

    def _compute_centrality(self, adjacency: dict[str, set[str]]) -> dict[str, float]:
        n = len(adjacency)
        if n == 0:
            return {}

        nodes_list = list(adjacency.keys())
        idx = {v: i for i, v in enumerate(nodes_list)}

        adj_matrix = np.zeros((n, n), dtype=float)
        for u in adjacency:
            for v in adjacency[u]:
                adj_matrix[idx[u], idx[v]] = 1.0

        degree_centrality = {
            u: len(neighbors) / (n - 1) if n > 1 else 0.0
            for u, neighbors in adjacency.items()
        }

        eigenvalue_centrality = self._power_iteration(adj_matrix, n)
        eigen_dict = {}
        for i, v in enumerate(nodes_list):
            eigen_dict[v] = float(eigenvalue_centrality[i])

        betweenness = self._approximate_betweenness(adjacency, nodes_list)

        return {
            u: {
                "degree": round(degree_centrality.get(u, 0), 4),
                "eigenvector": round(eigen_dict.get(u, 0), 4),
                "betweenness": round(betweenness.get(u, 0), 4),
            }
            for u in nodes_list
        }

    def _power_iteration(
        self, matrix: np.ndarray, n: int, max_iter: int = 100
    ) -> np.ndarray:
        vector = np.ones(n) / math.sqrt(n)
        for _ in range(max_iter):
            new_vector = matrix @ vector
            norm = np.linalg.norm(new_vector)
            if norm == 0:
                break
            new_vector = new_vector / norm
            if np.allclose(vector, new_vector, atol=1e-6):
                break
            vector = new_vector
        return vector

    def _approximate_betweenness(
        self, adjacency: dict[str, set[str]], nodes: list[str]
    ) -> dict[str, float]:
        betweenness: dict[str, float] = defaultdict(float)
        n = len(nodes)
        if n <= 2:
            return {u: 0.0 for u in nodes}

        sample_size = min(100, n)
        sampled = np.random.choice(nodes, size=sample_size, replace=False) if n > sample_size else nodes

        for s_node in sampled:
            stack: list[str] = []
            predecessors: dict[str, list[str]] = defaultdict(list)
            sigma: dict[str, int] = defaultdict(int)
            sigma[s_node] = 1
            dist: dict[str, float] = {s_node: 0.0}
            queue: list[str] = [s_node]

            while queue:
                v = queue.pop(0)
                stack.append(v)
                for w in adjacency.get(v, []):
                    if w not in dist:
                        dist[w] = dist[v] + 1
                        queue.append(w)
                    if dist[w] == dist[v] + 1:
                        sigma[w] += sigma[v]
                        predecessors[w].append(v)

            delta: dict[str, float] = defaultdict(float)
            while stack:
                w = stack.pop()
                for v in predecessors[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
                if w != s_node:
                    betweenness[w] += delta[w]

        total = (n - 1) * (n - 2) if n > 2 else 1
        return {u: v / total for u, v in betweenness.items()}

    def _detect_communities(self, adjacency: dict[str, set[str]]) -> list[list[str]]:
        nodes = list(adjacency.keys())
        if not nodes:
            return []

        parent: dict[str, str] = {n: n for n in nodes}
        rank: dict[str, int] = {n: 0 for n in nodes}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: str, y: str) -> None:
            rx, ry = find(x), find(y)
            if rx == ry:
                return
            if rank[rx] < rank[ry]:
                parent[rx] = ry
            elif rank[rx] > rank[ry]:
                parent[ry] = rx
            else:
                parent[ry] = rx
                rank[rx] += 1

        edges_added = 0
        for u in adjacency:
            for v in adjacency[u]:
                if u < v:
                    union(u, v)
                    edges_added += 1
                if edges_added > len(nodes) * 3:
                    break
            if edges_added > len(nodes) * 3:
                break

        communities_map: dict[str, list[str]] = defaultdict(list)
        for n in nodes:
            communities_map[find(n)].append(n)

        return list(communities_map.values())

    def _detect_anomalies(self) -> list[AnomalyResult]:
        anomalies: list[AnomalyResult] = []

        self._detect_contact_outliers(anomalies)
        self._detect_timing_anomalies(anomalies)
        self._detect_volume_anomalies(anomalies)

        return anomalies

    def _detect_contact_outliers(self, anomalies: list[AnomalyResult]) -> None:
        contact_freq: dict[str, int] = defaultdict(int)
        for r in self._records:
            contact_freq[r.target] += 1

        if not contact_freq:
            return

        freqs = list(contact_freq.values())
        if len(freqs) < 5:
            return

        mean = np.mean(freqs)
        std = np.std(freqs)
        if std == 0:
            return

        for idx, (contact, freq) in enumerate(contact_freq.items()):
            z_score = (freq - mean) / std
            if z_score > 3.0:
                anomalies.append(
                    AnomalyResult(
                        record_index=idx,
                        anomaly_score=float(min(z_score / 5.0, 1.0)),
                        anomaly_type="contact_outlier",
                        description=f"Unusually high contact frequency with {contact}: {freq} interactions",
                        severity="high",
                    )
                )

    def _detect_timing_anomalies(self, anomalies: list[AnomalyResult]) -> None:
        late_night: list[CommunicationRecord] = []
        for r in self._records:
            try:
                dt = datetime.fromisoformat(r.timestamp)
                if dt.hour >= 0 and dt.hour < 5:
                    late_night.append(r)
            except (ValueError, TypeError):
                pass

        if len(late_night) > self._total_records() * 0.3 and len(late_night) > 10:
            anomalies.append(
                AnomalyResult(
                    record_index=0,
                    anomaly_score=0.7,
                    anomaly_type="unusual_timing",
                    description=(
                        f"{len(late_night)} communications ({len(late_night) / max(self._total_records(), 1) * 100:.0f}%) "
                        "occurred during late-night hours (00:00-05:00)"
                    ),
                    severity="medium",
                )
            )

    def _total_records(self) -> int:
        return len(self._records)

    def _detect_volume_anomalies(self, anomalies: list[AnomalyResult]) -> None:
        if len(self._records) < 10:
            return

        daily_counts: dict[str, int] = defaultdict(int)
        for r in self._records:
            try:
                day = r.timestamp[:10]
                daily_counts[day] += 1
            except Exception:
                pass

        if len(daily_counts) < 3:
            return

        counts = list(daily_counts.values())
        mean = np.mean(counts)
        std = np.std(counts)
        if std == 0:
            return

        for day, count in daily_counts.items():
            z_score = (count - mean) / std
            if z_score > 2.5:
                anomalies.append(
                    AnomalyResult(
                        record_index=0,
                        anomaly_score=float(min(z_score / 5.0, 1.0)),
                        anomaly_type="volume_spike",
                        description=f"Communication volume spike on {day}: {count} messages/calls (z={z_score:.1f})",
                        severity="medium",
                    )
                )

    def _build_behavioral_profile(self) -> dict[str, Any]:
        if not self._records:
            return {}

        channels = Counter(r.channel for r in self._records)
        directions = Counter(r.direction for r in self._records)
        hour_dist = Counter()
        day_dist: dict[str, int] = defaultdict(int)
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for r in self._records:
            try:
                dt = datetime.fromisoformat(r.timestamp)
                hour_dist[dt.hour] += 1
                day_dist[day_names[dt.weekday()]] += 1
            except (ValueError, TypeError):
                pass

        features = self._extract_features()

        behavior_class = "normal"
        behavior_probs: list[float] = []
        try:
            probs = self.classifier.predict(features.reshape(1, -1))[0]
            behavior_probs = probs.tolist()
            class_labels = ["normal", "nocturnal", "burst", "scattered", "focused"]
            behavior_class = class_labels[int(np.argmax(probs))]
        except Exception:
            pass

        return {
            "primary_channel": channels.most_common(1)[0][0] if channels else "unknown",
            "total_interactions": len(self._records),
            "incoming_ratio": round(directions.get("incoming", 0) / max(len(self._records), 1), 2),
            "outgoing_ratio": round(directions.get("outgoing", 0) / max(len(self._records), 1), 2),
            "hourly_distribution": dict(hour_dist),
            "daily_distribution": dict(day_dist),
            "behavior_class": behavior_class,
            "behavior_class_probabilities": behavior_probs,
        }

    def _extract_features(self) -> np.ndarray:
        if not self._records:
            return np.zeros(16, dtype=np.float32)

        hours = []
        durations = []
        channels_set = {"call", "sms", "whatsapp", "telegram", "imessage"}
        channel_counts = {c: 0 for c in channels_set}
        outgoing = 0

        for r in self._records:
            try:
                dt = datetime.fromisoformat(r.timestamp)
                hours.append(dt.hour)
            except Exception:
                pass
            durations.append(r.duration)
            if r.channel in channel_counts:
                channel_counts[r.channel] += 1
            if r.direction == "outgoing":
                outgoing += 1

        features = np.zeros(16, dtype=np.float32)
        n = len(self._records)
        features[0] = n / 1000.0 if n > 0 else 0.0
        features[1] = float(np.mean(hours)) if hours else 0.0
        features[2] = float(np.std(hours)) if len(hours) > 1 else 0.0
        features[3] = float(np.mean(durations)) if durations else 0.0
        features[4] = outgoing / n if n > 0 else 0.0

        for i, c in enumerate(channels_set):
            features[5 + i] = channel_counts[c] / n if n > 0 else 0.0

        features[10] = len(self._records) / 7.0
        features[11] = float(np.median(hours)) if hours else 0.0
        features[12] = float(np.percentile(durations, 90)) if durations else 0.0

        weekend_count = sum(
            1 for r in self._records
            if self._is_weekend(r.timestamp)
        )
        features[13] = weekend_count / n if n > 0 else 0.0

        unique_contacts = self._count_unique_contacts()
        features[14] = unique_contacts / max(n, 1)

        features[15] = 0.0

        return features

    def _is_weekend(self, ts: str) -> bool:
        try:
            dt = datetime.fromisoformat(ts)
            return dt.weekday() >= 5
        except Exception:
            return False

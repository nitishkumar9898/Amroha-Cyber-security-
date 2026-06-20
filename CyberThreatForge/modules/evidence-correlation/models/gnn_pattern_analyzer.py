"""GNN pattern analyzer for evidence correlation graphs.

Implements Graph Isomorphism Network (GIN) style model for:
- Graph-level pattern classification
- Anomalous subgraph detection
- Evidence cluster quality assessment
- Attack pattern recognition
- Cross-case similarity
"""

import json
import logging
import math
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.nn import Sequential, Linear, ReLU, BatchNorm1d
except ImportError:
    torch = None
    nn = None
    F = None

logger = logging.getLogger(__name__)


@dataclass
class PatternAnalysisResult:
    graph_id: str
    predicted_class: int
    confidence: float
    class_probabilities: dict[str, float]
    anomaly_score: float
    cluster_quality: float
    patterns_detected: list[dict[str, Any]]
    embedding: Optional[list[float]] = None


@dataclass
class SimilarityResult:
    source_id: str
    target_id: str
    similarity: float
    common_patterns: list[str]


class GINConv(nn.Module if nn else object):
    def __init__(self, in_dim: int, out_dim: int):
        if nn is None:
            return
        super().__init__()
        self.mlp = Sequential(
            Linear(in_dim, out_dim),
            BatchNorm1d(out_dim),
            ReLU(),
            Linear(out_dim, out_dim),
            BatchNorm1d(out_dim),
        )
        self.eps = nn.Parameter(torch.zeros(1))

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        if nn is None:
            return x
        out = (1 + self.eps) * x + torch.mm(adj, x)
        return self.mlp(out)


class GINEncoder(nn.Module if nn else object):
    def __init__(self, in_dim: int, hidden_dim: int, out_dim: int, num_layers: int = 3):
        if nn is None:
            return
        super().__init__()
        self.layers = nn.ModuleList()
        self.layers.append(GINConv(in_dim, hidden_dim))
        for _ in range(num_layers - 2):
            self.layers.append(GINConv(hidden_dim, hidden_dim))
        self.layers.append(GINConv(hidden_dim, out_dim))
        self.dropout = nn.Dropout(0.3)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        if nn is None:
            return x
        for layer in self.layers[:-1]:
            x = layer(x, adj)
            x = self.dropout(F.relu(x))
        x = self.layers[-1](x, adj)
        return x


class GINClassifier(nn.Module if nn else object):
    def __init__(self, in_dim: int, hidden_dim: int, num_classes: int, num_layers: int = 3):
        if nn is None:
            return
        super().__init__()
        self.encoder = GINEncoder(in_dim, hidden_dim, hidden_dim, num_layers)
        self.classifier = Sequential(
            Linear(hidden_dim, hidden_dim // 2),
            ReLU(),
            Dropout(0.3) if nn else nn.Identity(),
            Linear(hidden_dim // 2, num_classes),
        )
        self.anomaly_head = Sequential(
            Linear(hidden_dim, hidden_dim // 2),
            ReLU(),
            Linear(hidden_dim // 2, 1),
        )
        self.quality_head = Sequential(
            Linear(hidden_dim, hidden_dim // 2),
            ReLU(),
            Linear(hidden_dim // 2, 1),
        )

    def forward(self, x: torch.Tensor, adj: torch.Tensor, batch_mask: Optional[torch.Tensor] = None) -> dict[str, torch.Tensor]:
        if nn is None:
            return {}
        node_embeds = self.encoder(x, adj)

        if batch_mask is not None:
            global_embed = self._global_pool(node_embeds, batch_mask)
        else:
            global_embed = node_embeds.mean(dim=0, keepdim=True)

        logits = self.classifier(global_embed)
        anomaly_score = torch.sigmoid(self.anomaly_head(global_embed))
        quality = torch.sigmoid(self.quality_head(global_embed))

        return {
            "logits": logits,
            "node_embeddings": node_embeds,
            "graph_embedding": global_embed,
            "anomaly_score": anomaly_score,
            "cluster_quality": quality,
        }

    @staticmethod
    def _global_pool(x: torch.Tensor, batch_mask: torch.Tensor) -> torch.Tensor:
        if nn is None:
            return x
        pooled = []
        for i in range(batch_mask.max().item() + 1):
            mask = batch_mask == i
            pooled.append(x[mask].mean(dim=0))
        return torch.stack(pooled)


if nn is not None:
    Dropout = nn.Dropout
else:
    Dropout = None


FEATURE_DIM = 64
HIDDEN_DIM = 128
NUM_CLASSES = 8

PATTERN_CLASSES = [
    "command_and_control",
    "data_exfiltration",
    "lateral_movement",
    "reconnaissance",
    "privilege_escalation",
    "phishing",
    "ransomware",
    "benign",
]


class GNNAnalyzer:
    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "cpu",
        in_dim: int = FEATURE_DIM,
        hidden_dim: int = HIDDEN_DIM,
        num_classes: int = NUM_CLASSES,
    ):
        self.device = device if torch is not None else "cpu"
        self.in_dim = in_dim
        self.num_classes = num_classes
        self._model: Optional[GINClassifier] = None

        if torch is not None:
            self._model = GINClassifier(in_dim, hidden_dim, num_classes)
            if model_path:
                self._load_model(model_path)
            self._model.to(self.device)
            self._model.eval()

    def _load_model(self, path: str):
        try:
            state = torch.load(path, map_location=self.device, weights_only=True)
            if self._model:
                self._model.load_state_dict(state, strict=False)
                logger.info("Loaded GNN model from %s", path)
        except Exception as e:
            logger.warning("Failed to load GNN model: %s", e)

    def _ensure_model(self):
        if self._model is None:
            raise RuntimeError("PyTorch not available or model not initialized")

    @staticmethod
    def _graph_to_features(
        nodes: list[dict[str, Any]],
        edges: list[tuple[int, int]],
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if torch is None:
            return torch.empty(0), torch.empty(0)

        n = len(nodes)
        x_list = []
        for node in nodes:
            feat = [
                hash(node.get("node_type", "unknown")) % 1000 / 1000.0,
                hash(node.get("label", "")) % 1000 / 1000.0,
                float(node.get("metadata", {}).get("size", 0)) / 1e6 if isinstance(node.get("metadata"), dict) else 0.0,
                float(node.get("metadata", {}).get("confidence", 0)) if isinstance(node.get("metadata"), dict) else 0.0,
                len(node.get("metadata", {})) if isinstance(node.get("metadata"), dict) else 0,
            ]
            feat.extend([
                float(hash(str(v)) % 1000) / 1000.0
                for k, v in (node.get("metadata", {}) if isinstance(node.get("metadata"), dict) else {}).items()
            ][:FEATURE_DIM - 5])
            while len(feat) < FEATURE_DIM:
                feat.append(0.0)
            x_list.append(feat[:FEATURE_DIM])

        x = torch.tensor(x_list, dtype=torch.float32)

        adj = torch.zeros(n, n)
        for s, t in edges:
            if s < n and t < n:
                adj[s, t] = 1.0
                adj[t, s] = 1.0

        adj = adj + torch.eye(n)
        d_inv_sqrt = torch.diag(1.0 / torch.sqrt(adj.sum(dim=1) + 1e-8))
        adj = d_inv_sqrt @ adj @ d_inv_sqrt

        return x, adj

    def analyze_pattern(
        self,
        graph_data: dict[str, Any],
        graph_id: str = "",
    ) -> PatternAnalysisResult:
        if torch is None:
            return self._simulated_result(graph_id)

        self._ensure_model()
        nodes = graph_data.get("nodes", [])
        edges_raw = graph_data.get("links", [])
        edges = [(e.get("source", 0), e.get("target", 0)) for e in edges_raw]

        if not nodes:
            return PatternAnalysisResult(
                graph_id=graph_id, predicted_class=7, confidence=0.0,
                class_probabilities={c: 0.0 for c in PATTERN_CLASSES},
                anomaly_score=0.0, cluster_quality=0.0, patterns_detected=[],
            )

        x, adj = self._graph_to_features(nodes, edges)
        x, adj = x.to(self.device), adj.to(self.device)

        with torch.no_grad():
            output = self._model(x.unsqueeze(0) if x.dim() == 2 else x, adj.unsqueeze(0) if adj.dim() == 2 else adj)

        logits = output["logits"]
        probs = F.softmax(logits, dim=-1)[0] if F is not None else logits
        pred_class = int(probs.argmax().item()) if torch is not None else 7
        confidence = float(probs.max().item()) if torch is not None else 0.0
        anomaly_score = float(output["anomaly_score"].squeeze().item()) if torch is not None else 0.0
        cluster_quality = float(output["cluster_quality"].squeeze().item()) if torch is not None else 0.0
        embedding = output.get("graph_embedding")
        emb_list = embedding.squeeze().tolist() if embedding is not None and torch is not None else None

        class_probs = {
            PATTERN_CLASSES[i]: float(probs[i].item())
            for i in range(min(len(PATTERN_CLASSES), probs.shape[0]))
        } if torch is not None else {}

        patterns = self._detect_patterns(graph_data, pred_class, confidence)

        return PatternAnalysisResult(
            graph_id=graph_id,
            predicted_class=pred_class,
            confidence=confidence,
            class_probabilities=class_probs,
            anomaly_score=anomaly_score,
            cluster_quality=cluster_quality,
            patterns_detected=patterns,
            embedding=emb_list,
        )

    def compare_subgraphs(
        self,
        subgraph_a: dict[str, Any],
        subgraph_b: dict[str, Any],
        id_a: str = "",
        id_b: str = "",
    ) -> SimilarityResult:
        result_a = self.analyze_pattern(subgraph_a, id_a)
        result_b = self.analyze_pattern(subgraph_b, id_b)

        sim_score = 0.0
        common: list[str] = []

        if result_a.embedding and result_b.embedding:
            emb_a = np.array(result_a.embedding)
            emb_b = np.array(result_b.embedding)
            norm = np.linalg.norm(emb_a) * np.linalg.norm(emb_b)
            sim_score = float(np.dot(emb_a, emb_b) / (norm + 1e-8))
            sim_score = max(-1.0, min(1.0, sim_score))

        shared_patterns = set(
            p["pattern_type"] for p in result_a.patterns_detected
        ) & set(
            p["pattern_type"] for p in result_b.patterns_detected
        )
        common = list(shared_patterns)

        return SimilarityResult(
            source_id=id_a or "subgraph_a",
            target_id=id_b or "subgraph_b",
            similarity=sim_score,
            common_patterns=common,
        )

    def detect_anomalous_subgraphs(
        self,
        graph_data: dict[str, Any],
        threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        if torch is None:
            return []

        results: list[dict[str, Any]] = []
        nodes = graph_data.get("nodes", [])
        edges_raw = graph_data.get("links", [])
        edges = [(e.get("source", 0), e.get("target", 0)) for e in edges_raw]

        conn_components = self._find_connected_components(len(nodes), edges)
        for comp_nodes in conn_components:
            if len(comp_nodes) < 2:
                continue
            comp_edges = [(s, t) for s, t in edges if s in comp_nodes and t in comp_nodes]
            sub_data = {
                "nodes": [nodes[i] for i in comp_nodes],
                "links": [{"source": s, "target": t} for s, t in comp_edges],
            }

            result = self.analyze_pattern(sub_data, graph_id=f"subgraph_{len(results)}")
            if result.anomaly_score >= threshold:
                results.append({
                    "subgraph_id": f"anom_{len(results)}",
                    "node_indices": comp_nodes,
                    "node_count": len(comp_nodes),
                    "anomaly_score": result.anomaly_score,
                    "predicted_pattern": PATTERN_CLASSES[result.predicted_class]
                    if result.predicted_class < len(PATTERN_CLASSES) else "unknown",
                    "patterns": [p["pattern_type"] for p in result.patterns_detected],
                })

        return sorted(results, key=lambda x: x["anomaly_score"], reverse=True)

    def assess_cluster_quality(
        self,
        cluster_nodes: list[dict[str, Any]],
        cluster_edges: list[tuple[int, int]],
    ) -> dict[str, float]:
        if torch is None:
            return {"quality": 0.5, "cohesion": 0.5, "separability": 0.5}

        sub_data = {
            "nodes": cluster_nodes,
            "links": [{"source": s, "target": t} for s, t in cluster_edges],
        }
        result = self.analyze_pattern(sub_data)
        return {
            "quality": result.cluster_quality,
            "cohesion": min(1.0, len(cluster_edges) / max(len(cluster_nodes), 1)),
            "separability": max(0.0, 1.0 - result.anomaly_score),
        }

    def batch_analyze(
        self,
        graph_batches: list[tuple[str, dict[str, Any]]],
    ) -> list[PatternAnalysisResult]:
        return [
            self.analyze_pattern(graph_data, graph_id=gid)
            for gid, graph_data in graph_batches
        ]

    @staticmethod
    def _detect_patterns(
        graph_data: dict[str, Any],
        pred_class: int,
        confidence: float,
    ) -> list[dict[str, Any]]:
        patterns: list[dict[str, Any]] = []
        nodes = graph_data.get("nodes", [])
        edges_raw = graph_data.get("links", [])
        node_types = set(n.get("node_type", "") for n in nodes)

        if len(nodes) > 10 and len(nodes) < 50:
            patterns.append({
                "pattern_type": "medium_subgraph",
                "confidence": 0.6,
                "description": f"Subgraph with {len(nodes)} nodes",
            })

        if node_types.intersection({"ip", "domain"}):
            patterns.append({
                "pattern_type": "network_activity",
                "confidence": 0.7,
                "description": "Contains IP/domain nodes indicating network activity",
            })

        if node_types.intersection({"file", "email"}):
            patterns.append({
                "pattern_type": "file_transfer",
                "confidence": 0.65,
                "description": "File/email nodes present suggesting data transfer",
            })

        if pred_class < len(PATTERN_CLASSES):
            patterns.append({
                "pattern_type": PATTERN_CLASSES[pred_class],
                "confidence": confidence,
                "description": f"ML classification: {PATTERN_CLASSES[pred_class]}",
            })

        return patterns

    @staticmethod
    def _find_connected_components(n: int, edges: list[tuple[int, int]]) -> list[list[int]]:
        parent = list(range(n))
        rank = [0] * n

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int):
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

        for s, t in edges:
            union(s, t)

        comp_map: dict[int, list[int]] = {}
        for i in range(n):
            root = find(i)
            if root not in comp_map:
                comp_map[root] = []
            comp_map[root].append(i)

        return list(comp_map.values())

    @staticmethod
    def _simulated_result(graph_id: str) -> PatternAnalysisResult:
        return PatternAnalysisResult(
            graph_id=graph_id,
            predicted_class=7,
            confidence=0.0,
            class_probabilities={c: 0.0 for c in PATTERN_CLASSES},
            anomaly_score=0.0,
            cluster_quality=0.0,
            patterns_detected=[],
        )

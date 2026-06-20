from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


class GraphSAGELayer(nn.Module):
    """GraphSAGE convolutional layer with mean aggregation."""

    def __init__(self, in_features: int, out_features: int, aggr: str = "mean") -> None:
        super().__init__()
        self.aggr = aggr
        self.self_lin = nn.Linear(in_features, out_features, bias=False)
        self.neigh_lin = nn.Linear(in_features, out_features, bias=False)
        self.bn = nn.BatchNorm1d(out_features)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        row, col = edge_index
        neigh_feats = x[col]
        if self.aggr == "mean":
            aggr_feats = torch.zeros_like(x)
            aggr_feats.index_add_(0, row, neigh_feats)
            counts = torch.zeros(x.size(0), device=x.device).index_add_(0, row, torch.ones_like(row, dtype=x.dtype))
            counts = counts.clamp(min=1)
            aggr_feats = aggr_feats / counts.unsqueeze(1)
        else:
            aggr_feats = torch.zeros_like(x)
            aggr_feats.index_add_(0, row, neigh_feats)

        out = self.self_lin(x) + self.neigh_lin(aggr_feats)
        out = self.bn(out)
        return F.relu(out)


class AttackGraphGNN(nn.Module):
    """
    Graph Neural Network for attack prediction using GraphSAGE-style convolution.

    Predicts:
    - Attack propagation paths
    - Next likely targets (node-level)
    - Attack method transitions (edge-level)
    - Node-level risk scores
    """

    def __init__(
        self,
        node_features: int = 128,
        hidden_channels: int = 256,
        num_layers: int = 3,
        num_classes: int = 10,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.node_features = node_features
        self.hidden_channels = hidden_channels
        self.num_layers = num_layers
        self.num_classes = num_classes

        self.input_proj = nn.Linear(node_features, hidden_channels)
        self.convs = nn.ModuleList([
            GraphSAGELayer(
                hidden_channels if i > 0 else hidden_channels,
                hidden_channels,
            )
            for i in range(num_layers)
        ])
        self.dropout = nn.Dropout(dropout)

        self.node_classifier = nn.Sequential(
            nn.Linear(hidden_channels, hidden_channels // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_channels // 2, num_classes),
        )

        self.risk_scorer = nn.Sequential(
            nn.Linear(hidden_channels, hidden_channels // 2),
            nn.ReLU(),
            nn.Linear(hidden_channels // 2, 1),
            nn.Sigmoid(),
        )

        self.edge_predictor = nn.Sequential(
            nn.Linear(hidden_channels * 2, hidden_channels),
            nn.ReLU(),
            nn.Linear(hidden_channels, 1),
            nn.Sigmoid(),
        )

        self.path_predictor = nn.Sequential(
            nn.Linear(hidden_channels * 2, hidden_channels),
            nn.ReLU(),
            nn.Linear(hidden_channels, hidden_channels),
            nn.ReLU(),
            nn.Linear(hidden_channels, 1),
        )

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        x = self.input_proj(x)
        representations: list[torch.Tensor] = [x]

        for conv in self.convs:
            x = conv(x, edge_index)
            x = self.dropout(x)
            representations.append(x)

        node_embeds = x
        logits = self.node_classifier(node_embeds)
        risk_scores = self.risk_scorer(node_embeds)

        row, col = edge_index
        src_embeds = node_embeds[row]
        dst_embeds = node_embeds[col]
        edge_feats = torch.cat([src_embeds, dst_embeds], dim=1)
        edge_probs = self.edge_predictor(edge_feats).squeeze(-1)

        path_feats = torch.cat([src_embeds, dst_embeds], dim=1)
        path_scores = self.path_predictor(path_feats).squeeze(-1)

        return {
            "node_logits": logits,
            "risk_scores": risk_scores,
            "edge_probabilities": edge_probs,
            "path_scores": path_scores,
            "node_embeddings": node_embeds,
        }

    @torch.no_grad()
    def predict_next_targets(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        current_nodes: torch.Tensor,
        top_k: int = 5,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        out = self.forward(x, edge_index)
        path_scores = out["path_scores"]
        risk_scores = out["risk_scores"]

        row, col = edge_index
        node_mask = torch.isin(row, current_nodes)
        candidate_edges = col[node_mask]
        candidate_scores = path_scores[node_mask]

        unique_candidates = torch.unique(candidate_edges)
        aggregated_scores = torch.zeros(len(unique_candidates), device=x.device)
        for i, node in enumerate(unique_candidates):
            mask = candidate_edges == node
            aggregated_scores[i] = candidate_scores[mask].max()

        risk_weights = risk_scores[unique_candidates].squeeze(-1)
        final_scores = aggregated_scores * risk_weights

        top_scores, top_indices = final_scores.topk(min(top_k, len(final_scores)))
        top_nodes = unique_candidates[top_indices]

        return top_nodes, top_scores

    @torch.no_grad()
    def predict_attack_path(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        start_node: int,
        max_steps: int = 10,
        top_k: int = 3,
    ) -> list[list[int]]:
        paths: list[list[int]] = []
        current = torch.tensor([start_node], device=x.device)

        for _ in range(max_steps):
            next_nodes, scores = self.predict_next_targets(x, edge_index, current, top_k)
            if len(next_nodes) == 0:
                break
            paths.append(next_nodes.tolist())
            current = next_nodes[:1]
            if scores[0].item() < 0.1:
                break

        return paths

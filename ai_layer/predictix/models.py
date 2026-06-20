# Predictix model definitions
import torch
import torch.nn as nn
from torch_geometric.nn import SAGEConv

class TemporalGNN(nn.Module):
    """Hybrid model combining a temporal RNN (GRU) with a GraphSAGE layer.
    Input:
      - time_series: Tensor of shape (batch, seq_len, feature_dim)
      - graph_data: a PyG Data object with edge_index and optional node features
    Output:
      - forecast tensor of shape (batch, horizon, out_dim)
    """
    def __init__(self, ts_input_dim: int, hidden_dim: int, graph_hidden_dim: int, out_dim: int, horizon: int = 600):
        super().__init__()
        self.seq_len = None  # will be set at forward
        self.gru = nn.GRU(input_size=ts_input_dim, hidden_size=hidden_dim, batch_first=True)
        # GraphSAGE to embed node context
        self.graph_conv = SAGEConv(in_channels=graph_hidden_dim, out_channels=graph_hidden_dim)
        # Combine temporal hidden state and graph embedding
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim + graph_hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, out_dim * horizon)
        )
        self.out_dim = out_dim
        self.horizon = horizon

    def forward(self, time_series, graph_data):
        # time_series: (B, T, D)
        batch_size = time_series.size(0)
        _, hidden = self.gru(time_series)  # hidden: (1, B, hidden_dim)
        hidden = hidden.squeeze(0)  # (B, hidden_dim)
        # Graph embedding: assume node features are in graph_data.x
        x = graph_data.x if hasattr(graph_data, 'x') else torch.zeros((graph_data.num_nodes, self.graph_conv.in_channels), device=time_series.device)
        edge_index = graph_data.edge_index
        node_emb = self.graph_conv(x, edge_index)  # (N, graph_hidden_dim)
        # Global pooling (mean) to get a single graph vector per batch element
        graph_vec = torch.mean(node_emb, dim=0, keepdim=True).repeat(batch_size, 1)  # (B, graph_hidden_dim)
        combined = torch.cat([hidden, graph_vec], dim=1)  # (B, hidden+graph)
        out = self.fc(combined)  # (B, out_dim * horizon)
        out = out.view(batch_size, self.horizon, self.out_dim)
        return out

class RiskScorer:
    """Utility to convert raw forecast predictions into risk scores and allocation advice."""
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def compute_score(self, forecast_tensor: torch.Tensor) -> float:
        # Simple aggregate: mean of predictions normalized to [0,1]
        score = forecast_tensor.mean().item()
        return min(1.0, max(0.0, score))

    def allocation_suggestions(self, score: float) -> dict:
        # Very naive rule‑based suggestions
        if score < 0.3:
            level = "low"
        elif score < 0.7:
            level = "moderate"
        else:
            level = "high"
        return {
            "risk_score": round(score, 3),
            "allocation_level": level,
            "recommendations": {
                "low": "Maintain current monitoring.",
                "moderate": "Increase SOC staff by 10% and schedule quarterly red‑team exercises.",
                "high": "Activate incident response playbook, allocate emergency budget, and inform national CERT."
            }[level]
        }

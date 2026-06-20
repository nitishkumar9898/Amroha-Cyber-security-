# Predictix prediction utilities
import torch
from .models import TemporalGNN, RiskScorer
from .data_loader import ThreatTimeSeriesDataset
from torch_geometric.data import Data
import json
import os

def load_latest_checkpoint(checkpoint_dir: str):
    """Return the most recent checkpoint file path in `checkpoint_dir`."""
    if not os.path.isdir(checkpoint_dir):
        raise FileNotFoundError(f"Checkpoint directory {checkpoint_dir} not found")
    ckpts = [f for f in os.listdir(checkpoint_dir) if f.endswith('.ckpt')]
    if not ckpts:
        raise FileNotFoundError("No checkpoint files found")
    ckpts.sort()
    return os.path.join(checkpoint_dir, ckpts[-1])

def predict_future(model: TemporalGNN, time_series: torch.Tensor, graph_data: Data, horizon: int = 600):
    """Run inference for the configured horizon (default 600 months ≈ 50 years)."""
    model.eval()
    with torch.no_grad():
        forecast = model(time_series.unsqueeze(0), graph_data)  # (1, horizon, out_dim)
    return forecast.squeeze(0)  # (horizon, out_dim)

def run_prediction(ts_csv: str, edge_json: str, node_feat_json: str, checkpoint_dir: str, horizon: int = 600):
    """Load data, checkpoint and produce a JSON‑serialisable forecast.
    Returns a dict with keys `forecast`, `risk_score`, `allocation`.
    """
    # Load time‑series dataset (use the last sequence as input)
    ds = ThreatTimeSeriesDataset(ts_csv, seq_len=12)
    seq, _ = ds[-1]  # last available sequence
    # Load graph data
    with open(edge_json, 'r', encoding='utf-8') as f:
        edges = json.load(f)
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    # Node features (optional)
    if os.path.exists(node_feat_json):
        with open(node_feat_json, 'r', encoding='utf-8') as f:
            node_feats = json.load(f)
        num_nodes = max(max(src, dst) for src, dst in edges) + 1
        feat_len = len(next(iter(node_feats.values())))
        feats = torch.zeros((num_nodes, feat_len), dtype=torch.float)
        for nid, vec in node_feats.items():
            feats[int(nid)] = torch.tensor(vec, dtype=torch.float)
    else:
        feats = torch.zeros((edge_index.max().item() + 1, 1), dtype=torch.float)
    graph_data = Data(x=feats, edge_index=edge_index)

    # Load model checkpoint
    ckpt_path = load_latest_checkpoint(checkpoint_dir)
    checkpoint = torch.load(ckpt_path, map_location='cpu')
    hp = checkpoint['hyper_parameters']
    model = TemporalGNN(
        ts_input_dim=hp['ts_input_dim'],
        hidden_dim=hp['hidden_dim'],
        graph_hidden_dim=hp['graph_hidden_dim'],
        out_dim=hp['out_dim'],
        horizon=horizon,
    )
    model.load_state_dict(checkpoint['state_dict'])

    forecast = predict_future(model, seq, graph_data, horizon)
    scorer = RiskScorer()
    risk_score = scorer.compute_score(forecast)
    allocation = scorer.allocation_suggestions(risk_score)

    return {
        "forecast": forecast.tolist(),
        "risk_score": risk_score,
        "allocation": allocation,
    }

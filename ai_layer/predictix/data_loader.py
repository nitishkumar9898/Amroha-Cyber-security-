# Predictix data loading utilities
import os
import pandas as pd
import json
from typing import List, Tuple, Dict

import torch
from torch.utils.data import Dataset, DataLoader

# Time-series dataset
class ThreatTimeSeriesDataset(Dataset):
    """Dataset for chronological threat incident counts.
    Expects a CSV with a `timestamp` column and numeric feature columns.
    """
    def __init__(self, csv_path: str, seq_len: int = 12):
        self.df = pd.read_csv(csv_path, parse_dates=['timestamp']).sort_values('timestamp')
        self.seq_len = seq_len
        # Use all columns except timestamp as features
        self.features = self.df.drop(columns=['timestamp']).values.astype(float)

    def __len__(self):
        return max(0, len(self.features) - self.seq_len)

    def __getitem__(self, idx):
        seq = self.features[idx: idx + self.seq_len]
        target = self.features[idx + self.seq_len] if idx + self.seq_len < len(self.features) else self.features[-1]
        return torch.tensor(seq, dtype=torch.float), torch.tensor(target, dtype=torch.float)

# Graph dataset (edge list + node features)
class ThreatGraphDataset(Dataset):
    """Simple graph dataset loading edges and optional node attributes.
    Edge file format: JSON list of [src, dst] pairs.
    Node feature file: JSON dict node_id -> feature list.
    """
    def __init__(self, edge_path: str, node_feat_path: str = None):
        with open(edge_path, 'r', encoding='utf-8') as f:
            self.edges = json.load(f)
        if node_feat_path and os.path.exists(node_feat_path):
            with open(node_feat_path, 'r', encoding='utf-8') as f:
                self.node_features = json.load(f)
        else:
            self.node_features = {}

    def __len__(self):
        return len(self.edges)

    def __getitem__(self, idx):
        src, dst = self.edges[idx]
        src_feat = self.node_features.get(str(src), [])
        dst_feat = self.node_features.get(str(dst), [])
        return {
            'src': src,
            'dst': dst,
            'src_feat': torch.tensor(src_feat, dtype=torch.float) if src_feat else torch.tensor([], dtype=torch.float),
            'dst_feat': torch.tensor(dst_feat, dtype=torch.float) if dst_feat else torch.tensor([], dtype=torch.float),
        }

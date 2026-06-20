# Predictix training utilities using PyTorch Lightning
import pytorch_lightning as pl
import torch
from torch import nn
from torch.utils.data import DataLoader
from .data_loader import ThreatTimeSeriesDataset
from .models import TemporalGNN

class PredictixLightningModule(pl.LightningModule):
    def __init__(self, ts_input_dim: int, hidden_dim: int, graph_hidden_dim: int, out_dim: int, horizon: int = 600, lr: float = 1e-3):
        super().__init__()
        self.model = TemporalGNN(ts_input_dim, hidden_dim, graph_hidden_dim, out_dim, horizon)
        self.loss_fn = nn.MSELoss()
        self.lr = lr

    def forward(self, time_series, graph_data):
        return self.model(time_series, graph_data)

    def training_step(self, batch, batch_idx):
        time_seq, target = batch
        # Dummy graph data placeholder (no edges) for illustration
        class DummyGraph:
            def __init__(self, device):
                self.x = torch.zeros((1, self_hidden_dim), device=device)
                self.edge_index = torch.empty((2,0), dtype=torch.long, device=device)
        dummy_graph = DummyGraph(self.device)
        pred = self(time_seq, dummy_graph)
        loss = self.loss_fn(pred.squeeze(-1), target)
        self.log('train_loss', loss)
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.lr)

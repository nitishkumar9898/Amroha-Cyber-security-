import math
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


class Attention(nn.Module):
    """Bahdanau-style additive attention for feature importance."""

    def __init__(self, hidden_size: int) -> None:
        super().__init__()
        self.W = nn.Linear(hidden_size, hidden_size, bias=False)
        self.V = nn.Linear(hidden_size, 1, bias=False)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        energy = self.V(torch.tanh(self.W(x)))
        attn_weights = F.softmax(energy.squeeze(-1), dim=1)
        context = torch.bmm(attn_weights.unsqueeze(1), x).squeeze(1)
        return context, attn_weights


class BayesianDropout(nn.Module):
    """Dropout that remains active during evaluation for uncertainty estimation."""

    def __init__(self, p: float = 0.2) -> None:
        super().__init__()
        self.p = p

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.dropout(x, p=self.p, training=True)


class LSTMCell(nn.Module):
    """Single LSTM cell with layer norm for stability."""

    def __init__(self, input_size: int, hidden_size: int) -> None:
        super().__init__()
        self.lstm = nn.LSTMCell(input_size, hidden_size)
        self.ln = nn.LayerNorm(hidden_size)

    def forward(self, x: torch.Tensor, state: Tuple[torch.Tensor, torch.Tensor]) -> Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        h, c = self.lstm(x, state)
        h = self.ln(h)
        return h, (h, c)


class ThreatLSTM(nn.Module):
    """
    Multi-horizon threat forecasting model with sequence-to-sequence architecture.

    Supports 1d, 7d, and 30d forecasting horizons with attention-based
    feature importance and Bayesian dropout for uncertainty quantification.
    """

    def __init__(
        self,
        input_size: int = 64,
        hidden_size: int = 256,
        num_layers: int = 3,
        dropout: float = 0.25,
        output_horizons: Optional[list[int]] = None,
    ) -> None:
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_horizons = output_horizons or [1, 7, 30]

        self.bayesian_dropout = BayesianDropout(dropout)

        self.encoder_cells = nn.ModuleList([
            LSTMCell(input_size if i == 0 else hidden_size, hidden_size)
            for i in range(num_layers)
        ])

        self.attention = Attention(hidden_size)

        self.decoder_cells = nn.ModuleList([
            LSTMCell(input_size, hidden_size) for _ in range(num_layers)
        ])

        self.output_proj = nn.ModuleDict({
            str(h): nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2),
                nn.ReLU(),
                nn.Linear(hidden_size // 2, 1),
            )
            for h in self.output_horizons
        })

        self.teacher_forcing_ratio: float = 0.5
        self._mc_samples: int = 50

    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, list[Tuple[torch.Tensor, torch.Tensor]]]:
        batch_size, seq_len, _ = x.shape
        states: list[Tuple[torch.Tensor, torch.Tensor]] = [
            (torch.zeros(batch_size, self.hidden_size, device=x.device),
             torch.zeros(batch_size, self.hidden_size, device=x.device))
            for _ in range(self.num_layers)
        ]

        for t in range(seq_len):
            inp = x[:, t, :]
            inp = self.bayesian_dropout(inp)
            for i, cell in enumerate(self.encoder_cells):
                h, states[i] = cell(inp, states[i])
                inp = h

        encoder_outputs = torch.stack([s[0] for s in states], dim=1)
        context, attn_weights = self.attention(encoder_outputs)
        return context, states, attn_weights

    def decode(
        self,
        context: torch.Tensor,
        encoder_states: list[Tuple[torch.Tensor, torch.Tensor]],
        target_seq: Optional[torch.Tensor] = None,
    ) -> dict[str, torch.Tensor]:
        batch_size = context.size(0)
        device = context.device
        max_horizon = max(self.output_horizons)

        states = encoder_states[:]
        decoder_input = context.unsqueeze(1)

        outputs: dict[str, list[torch.Tensor]] = {str(h): [] for h in self.output_horizons}
        teacher_forcing = (target_seq is not None and self.training
                           and torch.rand(1).item() < self.teacher_forcing_ratio)

        for t in range(max_horizon):
            inp = decoder_input.squeeze(1)
            inp = self.bayesian_dropout(inp)
            for i, cell in enumerate(self.decoder_cells):
                h, states[i] = cell(inp, states[i])
                inp = h

            for h in self.output_horizons:
                if t < h:
                    pred = self.output_proj[str(h)](h)
                    outputs[str(h)].append(pred)

            if teacher_forcing and target_seq is not None and t < target_seq.size(1) - 1:
                decoder_input = target_seq[:, t:t + 1, :]
            else:
                decoder_input = h.unsqueeze(1)

        return {k: torch.cat(v, dim=1) for k, v in outputs.items()}

    def forward(
        self,
        x: torch.Tensor,
        target_seq: Optional[torch.Tensor] = None,
    ) -> dict[str, torch.Tensor]:
        context, states, attn_weights = self.encode(x)
        predictions = self.decode(context, states, target_seq)
        predictions["attention_weights"] = attn_weights
        predictions["context"] = context
        return predictions

    @torch.no_grad()
    def predict_with_uncertainty(
        self,
        x: torch.Tensor,
        num_samples: Optional[int] = None,
    ) -> dict[str, dict[str, torch.Tensor]]:
        """Monte Carlo dropout for uncertainty quantification."""
        self.train(False)
        n = num_samples or self._mc_samples
        all_preds: dict[str, list[torch.Tensor]] = {str(h): [] for h in self.output_horizons}

        for _ in range(n):
            out = self.forward(x)
            for h in self.output_horizons:
                all_preds[str(h)].append(out[str(h)])

        result: dict[str, dict[str, torch.Tensor]] = {}
        for h in self.output_horizons:
            stacked = torch.stack(all_preds[str(h)], dim=0)
            mean = stacked.mean(dim=0)
            std = stacked.std(dim=0)
            lower = mean - 1.96 * std
            upper = mean + 1.96 * std
            result[str(h)] = {
                "mean": mean,
                "std": std,
                "ci_lower": lower,
                "ci_upper": upper,
            }
        return result

    def get_feature_importance(self, x: torch.Tensor) -> torch.Tensor:
        """Extract attention-based feature importance scores."""
        _, _, attn = self.encode(x)
        return attn

    def set_teacher_forcing(self, ratio: float) -> None:
        self.teacher_forcing_ratio = max(0.0, min(1.0, ratio))

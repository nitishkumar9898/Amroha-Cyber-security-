"""Differential privacy engine for federated learning.

Implements Gaussian mechanism for ε-DP with Rényi DP composition
accounting, per-layer adaptive gradient clipping, noise calibration
based on sensitivity, and privacy budget tracking per agency.
"""

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class PrivacyBudget:
    epsilon_consumed: float = 0.0
    delta_consumed: float = 0.0
    epsilon_remaining: float = 0.0
    delta_remaining: float = 0.0
    composition_count: int = 0
    mechanism: str = "gaussian"


class DifferentialPrivacyEngine:
    """ε-DP engine using the Gaussian mechanism with Rényi DP accounting.

    Provides gradient clipping, noise calibration, and compositional
    privacy budget tracking per agency/client.
    """

    def __init__(
        self,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        max_grad_norm: float = 1.0,
        noise_multiplier: Optional[float] = None,
        adaptive_clip: bool = True,
        target_delta: float = 1e-5,
    ):
        if epsilon <= 0:
            raise ValueError("epsilon must be positive")
        if delta <= 0 or delta >= 1:
            raise ValueError("delta must be in (0, 1)")

        self.epsilon = epsilon
        self.delta = delta
        self.max_grad_norm = max_grad_norm
        self.adaptive_clip = adaptive_clip
        self.target_delta = target_delta

        # Auto-calibrate noise multiplier if not provided
        if noise_multiplier is not None:
            self.noise_multiplier = noise_multiplier
        else:
            self.noise_multiplier = self._calibrate_noise(epsilon, delta)

        self._budgets: dict[str, PrivacyBudget] = {}

    def _calibrate_noise(self, epsilon: float, delta: float) -> float:
        """Calibrate the Gaussian noise multiplier for (ε, δ)-DP.

        Uses the analytic Gaussian mechanism calibration:
        σ = sqrt(2 * ln(1.25 / δ)) / ε
        """
        if epsilon <= 0:
            return 10.0
        return math.sqrt(2.0 * math.log(1.25 / delta)) / epsilon

    def clip_gradients(
        self,
        gradients: list[np.ndarray],
        client_id: Optional[str] = None,
    ) -> tuple[list[np.ndarray], float]:
        """Clip gradients per-layer or globally to max_grad_norm.

        Returns clipped gradients and the global clipping factor.
        When adaptive_clip is enabled, uses per-layer adaptive
        clipping based on each layer's own norm.
        """
        if self.adaptive_clip:
            clipped: list[np.ndarray] = []
            for g in gradients:
                layer_norm = float(np.sqrt(np.sum(g**2)))
                if layer_norm > self.max_grad_norm:
                    scale = self.max_grad_norm / max(layer_norm, 1e-8)
                    clipped.append(g * scale)
                else:
                    clipped.append(g)
            return clipped, 1.0

        # Global L2 clipping
        global_norm = math.sqrt(sum(float(np.sum(g**2)) for g in gradients))
        if global_norm > self.max_grad_norm:
            scale = self.max_grad_norm / max(global_norm, 1e-8)
            return [g * scale for g in gradients], scale

        return gradients, 1.0

    def add_noise(
        self,
        sensitivity: float = 1.0,
        shape: tuple[int, ...] = (1,),
        client_id: Optional[str] = None,
    ) -> np.ndarray:
        """Add Gaussian noise calibrated to sensitivity and privacy budget.

        Returns noise sampled from N(0, σ² * sensitivity²).
        """
        sigma = self.noise_multiplier * sensitivity
        return np.random.normal(loc=0.0, scale=sigma, size=shape).astype(np.float32)

    def apply_dp(
        self,
        gradients: list[np.ndarray],
        client_id: Optional[str] = None,
    ) -> list[np.ndarray]:
        """Full DP application: clip then add noise.

        Returns differentially private gradients ready for submission.
        """
        clipped_grads, _ = self.clip_gradients(gradients, client_id)
        dp_grads: list[np.ndarray] = []
        for g in clipped_grads:
            noise = self.add_noise(
                sensitivity=self.max_grad_norm,
                shape=g.shape,
                client_id=client_id,
            )
            dp_grads.append(g + noise)
        return dp_grads

    def compute_epsilon_rdp(
        self,
        steps: int,
        subsampling_rate: float = 1.0,
        orders: Optional[list[float]] = None,
    ) -> float:
        """Compute ε using Rényi Differential Privacy composition.

        Uses the moments accountant / RDP composition to provide
        tighter privacy guarantees over multiple training steps.
        """
        if orders is None:
            orders = [1 + x for x in np.linspace(0, 100, 500)]

        sigma = self.noise_multiplier
        best_epsilon = float("inf")

        for alpha in orders:
            if alpha <= 1:
                continue
            rdp = self._rdp_gaussian(alpha, sigma, subsampling_rate)
            composed_rdp = rdp * steps
            epsilon = composed_rdp - math.log(self.target_delta) / (alpha - 1)
            best_epsilon = min(best_epsilon, epsilon)

        return best_epsilon if best_epsilon < float("inf") else self.epsilon * steps

    def _rdp_gaussian(
        self, alpha: float, sigma: float, subsampling_rate: float = 1.0
    ) -> float:
        """Rényi DP of the Gaussian mechanism at order alpha.

        For the Gaussian mechanism M = f(x) + N(0, σ²), the RDP is:
        ε(α) = α / (2σ²)
        """
        return alpha / (2.0 * sigma**2)

    def get_privacy_spent(self, steps: int = 1) -> float:
        """Return the total ε spent after `steps` of composition.

        Uses simple composition for tracking (accounting for the
        budget consumed by client in a given round).
        """
        return self.epsilon * steps

    def initialise_budget(self, client_id: str, epsilon_budget: float = 10.0) -> PrivacyBudget:
        """Initialise a privacy budget tracker for a client/agency."""
        budget = PrivacyBudget(
            epsilon_consumed=0.0,
            delta_consumed=0.0,
            epsilon_remaining=epsilon_budget,
            delta_remaining=self.target_delta,
            composition_count=0,
            mechanism="gaussian",
        )
        self._budgets[client_id] = budget
        return budget

    def consume_budget(self, client_id: str, steps: int = 1) -> PrivacyBudget:
        """Consume privacy budget for a given number of training steps.

        Returns updated budget or raises if exhausted.
        """
        if client_id not in self._budgets:
            raise ValueError(f"No budget initialised for client {client_id}")

        budget = self._budgets[client_id]
        epsilon_cost = self.compute_epsilon_rdp(steps=steps)

        if epsilon_cost > budget.epsilon_remaining:
            raise RuntimeError(
                f"Privacy budget exhausted for {client_id}: "
                f"need {epsilon_cost:.4f} ε, "
                f"remaining {budget.epsilon_remaining:.4f} ε"
            )

        budget.epsilon_consumed += epsilon_cost
        budget.epsilon_remaining -= epsilon_cost
        budget.delta_consumed += self.target_delta
        budget.delta_remaining -= self.target_delta
        budget.composition_count += steps

        return budget

    def get_budget(self, client_id: str) -> Optional[PrivacyBudget]:
        """Get the current privacy budget for a client."""
        return self._budgets.get(client_id)

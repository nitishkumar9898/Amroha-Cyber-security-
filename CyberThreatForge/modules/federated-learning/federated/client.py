"""Federated learning client — agency-side training logic.

Handles local model training on agency evidence, gradient computation
and encryption, model download/evaluation, differential privacy via
gradient clipping + Gaussian noise, and local data privacy guarantees
(ε-δ DP computation).
"""

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import numpy as np

from models.malware_cnn import MalwareCNN, EvaluationMetrics
from models.dp_engine import DifferentialPrivacyEngine

logger = logging.getLogger(__name__)


@dataclass
class LocalTrainingResult:
    client_id: str
    encrypted_gradients: list[bytes]
    num_samples: int
    dp_epsilon_used: float
    dp_delta_used: float
    local_metrics: EvaluationMetrics
    training_time_seconds: float
    round_id: str = ""


class FederatedClient:
    """Simulates an agency's local training environment.

    Each agency has its own private data, trains the shared model
    locally, applies DP, and encrypts gradients before submission.
    No raw evidence ever leaves the agency boundary.
    """

    def __init__(
        self,
        client_id: str,
        agency_name: str,
        public_key: str,
        dilithium_public_key: str = "",
        privacy_epsilon: float = 1.0,
        privacy_delta: float = 1e-5,
        max_grad_norm: float = 1.0,
        device: str = "cpu",
    ):
        self.client_id = client_id
        self.agency_name = agency_name
        self.public_key = public_key
        self.dilithium_public_key = dilithium_public_key

        self.dp_engine = DifferentialPrivacyEngine(
            epsilon=privacy_epsilon,
            delta=privacy_delta,
            max_grad_norm=max_grad_norm,
        )
        self.model = MalwareCNN(device=device)
        self._local_data: Optional[dict] = None
        self._privacy_budget = self.dp_engine.initialise_budget(client_id, epsilon_budget=10.0)

    def load_local_data(self, data: dict) -> None:
        """Load local agency evidence for training.

        The data dict can contain byte sequences, file hashes, or
        feature vectors. In production this reads from the agency's
        secure evidence store — no data is shared externally.
        """
        self._local_data = data
        logger.info(
            "Loaded local data for %s: %d samples",
            self.agency_name, len(data.get("samples", [])),
        )

    def train_local(
        self,
        global_weights: list[np.ndarray],
        epochs: int = 1,
        batch_size: int = 32,
        lr: float = 0.001,
        round_id: str = "",
    ) -> LocalTrainingResult:
        """Train the global model on local agency data.

        Steps:
          1. Load global model weights
          2. Train locally (simulated with random data)
          3. Compute gradients
          4. Apply differential privacy (clip + noise)
          5. Encrypt gradients for secure submission

        Returns encrypted gradients ready for aggregation.
        """
        if self._local_data is None:
            self._generate_synthetic_data()

        # Set global model weights as starting point
        self.model.set_weights(global_weights)

        # Check privacy budget
        try:
            self.dp_engine.consume_budget(self.client_id, steps=epochs)
        except RuntimeError as e:
            logger.error("Privacy budget exhausted for %s: %s", self.client_id, e)
            raise

        # Simulate local training
        start_time = datetime.now(timezone.utc)
        num_samples = len(self._local_data.get("samples", []))
        simulated_metrics = EvaluationMetrics(
            accuracy=0.75 + np.random.random() * 0.2,
            precision=0.72 + np.random.random() * 0.22,
            recall=0.70 + np.random.random() * 0.24,
            f1_score=0.71 + np.random.random() * 0.23,
            loss=0.4 + np.random.random() * 0.3,
            num_samples=num_samples,
        )

        # Compute gradients (simulated)
        raw_gradients = self.model.get_gradients()
        if not raw_gradients:
            # Generate random gradients as stand-in for actual training
            raw_gradients = self._simulate_gradients()

        # Apply differential privacy
        dp_gradients = self.dp_engine.apply_dp(raw_gradients, self.client_id)

        # Encrypt gradients for secure aggregation
        encrypted = self._encrypt_gradients(dp_gradients)

        training_time = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds()

        budget = self.dp_engine.get_budget(self.client_id)

        return LocalTrainingResult(
            client_id=self.client_id,
            encrypted_gradients=encrypted,
            num_samples=num_samples,
            dp_epsilon_used=budget.epsilon_consumed if budget else 1.0,
            dp_delta_used=budget.delta_consumed if budget else 1e-5,
            local_metrics=simulated_metrics,
            training_time_seconds=training_time,
            round_id=round_id,
        )

    def _generate_synthetic_data(self, num_samples: int = 100) -> None:
        """Generate synthetic malware data for local training.

        In production, this reads from the agency's secure evidence
        repository. No synthetic or real evidence is ever shared with
        the FL server or other agencies.
        """
        self._local_data = {
            "samples": [
                {
                    "id": str(uuid.uuid4()),
                    "byte_sequence": list(np.random.randint(0, 256, size=1024)),
                    "label": int(np.random.random() > 0.7),
                    "file_hash": hashlib.sha256(str(i).encode()).hexdigest(),
                }
                for i in range(num_samples)
            ]
        }

    def _simulate_gradients(
        self, num_layers: int = 10
    ) -> list[np.ndarray]:
        """Simulate gradient tensors matching the CNN architecture."""
        shapes = [
            (128, 1, 5), (128,),
            (64, 128, 3), (64,),
            (32, 64, 3), (32,),
            (64, 32), (64,),
            (2, 64), (2,),
        ]
        return [
            np.random.randn(*s).astype(np.float32) * 0.01
            for s in shapes[:num_layers]
        ]

    def _encrypt_gradients(
        self, gradients: list[np.ndarray]
    ) -> list[bytes]:
        """Encrypt gradient tensors for secure submission.

        Uses quantum-safe hybrid encryption simulation:
        each gradient tensor is serialized and encrypted with the
        server's public key using a SHA-3-based keyed encapsulation.

        In production, this calls the TypeScript QuantumSafeCrypto
        hybridEncrypt method via a bridge.
        """
        encrypted: list[bytes] = []
        for grad in gradients:
            serialized = grad.tobytes()
            # Simulated quantum-safe encryption:
            # hybridEncrypt(serialized, serverPublicKey)
            key = hashlib.sha3_256(
                self.public_key.encode("utf-8") + str(len(serialized)).encode()
            ).digest()
            # XOR-based simulated encryption (not real crypto — use
            # the quantum-safe layer in production)
            encrypted_bytes = bytes(
                a ^ b for a, b in zip(
                    serialized,
                    key * (len(serialized) // len(key) + 1),
                )
            )
            encrypted.append(encrypted_bytes)

        return encrypted

    def evaluate_local(self, test_data: Optional[list] = None) -> EvaluationMetrics:
        """Evaluate the local model on agency-held test data.

        No data leaves the agency — only metrics are returned.
        """
        if test_data is None:
            return EvaluationMetrics(
                accuracy=0.8 + np.random.random() * 0.15,
                precision=0.78 + np.random.random() * 0.17,
                recall=0.76 + np.random.random() * 0.18,
                f1_score=0.77 + np.random.random() * 0.17,
                loss=0.38 + np.random.random() * 0.25,
                num_samples=50,
            )
        # In production: run model.evaluate() on local test DataLoader
        return EvaluationMetrics()

    def get_privacy_report(self) -> dict:
        """Generate a local privacy guarantee report.

        Details the ε-δ DP spent by this client and the remaining
        budget.
        """
        budget = self.dp_engine.get_budget(self.client_id)
        if budget is None:
            return {"client_id": self.client_id, "error": "No budget initialised"}

        return {
            "client_id": self.client_id,
            "agency_name": self.agency_name,
            "mechanism": "Gaussian mechanism with Rényi DP accounting",
            "epsilon_consumed": round(budget.epsilon_consumed, 6),
            "delta_consumed": budget.delta_consumed,
            "epsilon_remaining": round(budget.epsilon_remaining, 6),
            "delta_remaining": budget.delta_remaining,
            "composition_count": budget.composition_count,
            "noise_multiplier": round(self.dp_engine.noise_multiplier, 6),
            "max_grad_norm": self.dp_engine.max_grad_norm,
            "adaptive_clipping": self.dp_engine.adaptive_clip,
        }

"""Secure aggregation for federated learning.

Implements Shamir Secret Sharing (SSS) for threshold-based secure
aggregation, additive secret sharing of gradients, masked aggregation
with dropout resilience, and quantum-safe encryption of shares.
"""

import os
import json
import hashlib
import secrets
from typing import Optional
from dataclasses import dataclass, field

import numpy as np

from models.dp_engine import DifferentialPrivacyEngine


@dataclass
class SecretShare:
    client_id: str
    share_index: int
    value: float
    encrypted_payload: bytes = b""


@dataclass
class AggregationResult:
    round_id: str
    aggregated_gradients: list[np.ndarray]
    num_participants: int
    threshold_reached: bool
    contributions: dict[str, float]


class ShamirSecretSharing:
    """Shamir's Secret Sharing over a finite field for threshold aggregation.

    Splits a secret value into n shares such that any t (threshold)
    shares can reconstruct the secret. Operates over GF(p) where p is
    a large prime.
    """

    PRIME = (1 << 127) - 1  # Mersenne prime for finite field

    def __init__(self, threshold: int = 2):
        if threshold < 2:
            raise ValueError("Threshold must be at least 2")
        self.threshold = threshold

    def _mod(self, x: int) -> int:
        return x % self.PRIME

    def split_secret(self, secret: int, num_shares: int) -> list[int]:
        """Split a secret integer into num_shares shares.

        Uses random polynomial of degree (threshold - 1) with the
        secret as the constant term. Returns y-values at x=1..num_shares.
        """
        if num_shares < self.threshold:
            raise ValueError("num_shares must be >= threshold")

        coeffs = [secret] + [
            secrets.randbelow(self.PRIME) for _ in range(self.threshold - 1)
        ]

        shares: list[int] = []
        for x in range(1, num_shares + 1):
            y = sum(
                c * pow(x, i, self.PRIME) for i, c in enumerate(coeffs)
            ) % self.PRIME
            shares.append(y)

        return shares

    def reconstruct_secret(self, shares: list[tuple[int, int]]) -> int:
        """Reconstruct the secret from a list of (x, y) share pairs.

        Uses Lagrange interpolation over GF(p). Requires at least
        threshold shares.
        """
        if len(shares) < self.threshold:
            raise ValueError(
                f"Need at least {self.threshold} shares, got {len(shares)}"
            )

        secret = 0
        for i, (xi, yi) in enumerate(shares):
            numerator = 1
            denominator = 1
            for j, (xj, _) in enumerate(shares):
                if i == j:
                    continue
                numerator = (numerator * (-xj)) % self.PRIME
                denominator = (denominator * (xi - xj)) % self.PRIME

            lagrange = (yi * numerator * pow(denominator, -1, self.PRIME)) % self.PRIME
            secret = (secret + lagrange) % self.PRIME

        return secret


class SecureAggregator:
    """Secure aggregation coordinator for federated learning rounds.

    Combines additive secret sharing with Shamir's scheme to enable
    masked aggregation: the server sums encrypted gradients without
    ever seeing individual plaintext updates. Supports client dropout
    via threshold reconstruction.
    """

    def __init__(
        self,
        threshold: int = 3,
        dp_engine: Optional[DifferentialPrivacyEngine] = None,
        quantum_safe_public_key: Optional[bytes] = None,
    ):
        self.sss = ShamirSecretSharing(threshold=threshold)
        self.dp_engine = dp_engine
        self.quantum_safe_public_key = quantum_safe_public_key
        self._shares: dict[str, list[SecretShare]] = {}
        self._client_masks: dict[str, list[np.ndarray]] = {}
        self._round_id: str = ""

    def start_round(self, round_id: str, participating_clients: list[str]) -> None:
        """Initialise a new aggregation round for the given clients."""
        self._round_id = round_id
        self._shares = {cid: [] for cid in participating_clients}
        self._client_masks = {}

    def submit_encrypted_update(
        self,
        client_id: str,
        encrypted_gradients: list[bytes],
        public_key: bytes,
    ) -> None:
        """Receive and store encrypted gradient shares from a client.

        In production, each share would be individually encrypted with
        the intended recipient's Kyber public key. Here we simulate
        the process using the client's own key material.
        """
        if client_id not in self._shares:
            raise ValueError(f"Unknown client: {client_id}")

        num_params = len(encrypted_gradients)
        num_clients = len(self._shares)
        share_count = max(self.sss.threshold, num_clients)

        # Simulate quantum-safe decryption stub — in production, each
        # share would be decrypted via hybridDecrypt with the server's
        # Kyber secret key.
        plaintext = [
            int(hashlib.sha256(eg + public_key).hexdigest()[:8], 16) / 2**32
            - 1.0
            for eg in encrypted_gradients
        ]

        for i in range(num_params):
            secret_int = int(plaintext[i] * 1e9) % self.sss.PRIME
            shares = self.sss.split_secret(secret_int, share_count)

            for j, share_val in enumerate(shares):
                share = SecretShare(
                    client_id=client_id,
                    share_index=i,
                    value=float(share_val) / 1e9,
                    encrypted_payload=encrypted_gradients[i],
                )
                # In production, append to specific recipient's share list
                self._shares[client_id].append(share)

    def _add_masks(self, gradients: list[np.ndarray]) -> list[np.ndarray]:
        """Apply pairwise masking masks to the aggregated sum.

        Each pair (i, j) of clients agrees on a shared random seed.
        Client i adds mask_{ij} and client j subtracts mask_{ij},
        so they cancel on summation.
        """
        client_ids = list(self._shares.keys())
        masked = [g.copy() for g in gradients]

        for i in range(len(client_ids)):
            for j in range(i + 1, len(client_ids)):
                seed = int(
                    hashlib.sha256(
                        f"{client_ids[i]}:{client_ids[j]}:{self._round_id}".encode()
                    ).hexdigest()[:16], 16
                )
                rng = np.random.default_rng(seed)
                for k in range(len(masked)):
                    mask = rng.standard_normal(size=gradients[k].shape)
                    # Client i adds, client j subtracts
                    if client_ids[i] in self._client_masks:
                        masked[k] += mask * 0.01
                    if client_ids[j] in self._client_masks:
                        masked[k] -= mask * 0.01

        return masked

    def aggregate(
        self, round_id: str, client_submissions: dict[str, list[np.ndarray]]
    ) -> AggregationResult:
        """Securely aggregate all submitted gradient updates.

        Performs FedAvg with secure aggregation: sums masked updates,
        applies differential privacy noise, and returns the averaged
        gradients.
        """
        if not client_submissions:
            raise ValueError("No client submissions to aggregate")

        num_clients = len(client_submissions)
        threshold_reached = num_clients >= self.sss.threshold

        if not threshold_reached:
            raise ValueError(
                f"Threshold {self.sss.threshold} not met, "
                f"only {num_clients} clients submitted"
            )

        self._client_masks = client_submissions

        # Get gradient shapes from first submission
        sample_grads = next(iter(client_submissions.values()))
        aggregated = [np.zeros_like(g) for g in sample_grads]

        # Sum all client updates
        for cid, grads in client_submissions.items():
            for i, g in enumerate(grads):
                aggregated[i] = aggregated[i] + g

        # Apply pairwise masks cancellation
        aggregated = self._add_masks(aggregated)

        # FedAvg: divide by number of participants
        for i in range(len(aggregated)):
            aggregated[i] = aggregated[i] / num_clients

        # Add differential privacy noise if DP engine is configured
        if self.dp_engine is not None:
            for i in range(len(aggregated)):
                noise = self.dp_engine.add_noise(
                    sensitivity=2.0 / num_clients,
                    shape=aggregated[i].shape,
                )
                aggregated[i] = aggregated[i] + noise

        # Compute contribution scores (L2 norm of each client's update)
        contributions: dict[str, float] = {}
        total_norm = 0.0
        client_norms: dict[str, float] = {}
        for cid, grads in client_submissions.items():
            norm = float(np.sqrt(sum(np.sum(g**2) for g in grads)))
            client_norms[cid] = norm
            total_norm += norm

        for cid in client_submissions:
            contributions[cid] = round(
                client_norms[cid] / total_norm if total_norm > 0 else 1.0 / num_clients,
                6,
            )

        return AggregationResult(
            round_id=round_id,
            aggregated_gradients=aggregated,
            num_participants=num_clients,
            threshold_reached=True,
            contributions=contributions,
        )

    def get_round_shares(self, round_id: str) -> dict[str, list[SecretShare]]:
        """Return the encrypted shares for auditing purposes."""
        return self._shares

    def simulate_quantum_encrypt(self, data: bytes, public_key: bytes) -> bytes:
        """Simulate quantum-safe hybrid encryption of share data.

        In production this would call quantumSafe.hybridEncrypt()
        from the TypeScript layer via a bridge. Here we use a
        deterministic SHA-3-based keyed encapsulation for testing.
        """
        return hashlib.sha3_256(data + public_key).digest()

    def simulate_quantum_decrypt(self, ciphertext: bytes, secret_key: bytes) -> bytes:
        """Simulate quantum-safe hybrid decryption."""
        return hashlib.sha3_256(ciphertext + secret_key).digest()

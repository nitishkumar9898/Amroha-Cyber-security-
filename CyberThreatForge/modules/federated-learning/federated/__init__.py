"""Federated learning server and client logic."""

from federated.server import FederatedServer, ClientRegistration, TrainingRound
from federated.client import FederatedClient, LocalTrainingResult
from federated.secure_aggregation import SecureAggregator, ShamirSecretSharing

__all__ = [
    "FederatedServer",
    "ClientRegistration",
    "TrainingRound",
    "FederatedClient",
    "LocalTrainingResult",
    "SecureAggregator",
    "ShamirSecretSharing",
]

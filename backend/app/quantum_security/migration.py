# quantum_security/migration.py
"""Utilities to aid migration from classical cryptography to post‑quantum algorithms.
Provides a planning function and an applicator that rewrites configuration files
with new key material.
"""

import os
import json
from typing import Dict, Any
from .pqcrypto import generate_keypair

def plan_migration(service_name: str) -> Dict[str, Any]:
    """Generate a high‑level migration plan for a given service.
    Returns a dictionary describing steps, estimated effort, and required resources.
    """
    plan = {
        "service": service_name,
        "steps": [
            "Identify current cryptographic assets (keys, certificates).",
            "Select target PQC algorithms (e.g., kyber1024 for encryption, dilithium2 for signatures).",
            "Generate new PQC keypairs using `generate_keypair`.",
            "Update service configuration files with new public keys.",
            "Deploy updated service and perform interoperability testing.",
            "Retire legacy keys after a safe deprecation period."
        ],
        "estimated_time_days": 7,
        "required_packages": ["pqcrypto", "pycryptodome"]
    }
    return plan

def apply_migration(service_module: Any, old_key_path: str, new_algo: str = "kyber1024") -> None:
    """Replace an existing key with a new PQC keypair.
    Args:
        service_module: The imported module representing the service (e.g., malwareforge_service).
        old_key_path: Path to the legacy key file (PEM). The file will be backed up.
        new_algo: PQC algorithm to generate keys for.
    """
    # Backup old key
    backup_path = f"{old_key_path}.bak"
    if os.path.exists(old_key_path):
        os.replace(old_key_path, backup_path)
    # Generate new keypair
    public_key, private_key = generate_keypair(new_algo)
    # Store keys in the same location for simplicity (binary blobs).
    with open(old_key_path, "wb") as f:
        f.write(public_key)
    priv_path = f"{os.path.splitext(old_key_path)[0]}_private.key"
    with open(priv_path, "wb") as f:
        f.write(private_key)
    # Optionally, update the service's in‑memory configuration if it exposes one.
    if hasattr(service_module, "crypto_config"):
        service_module.crypto_config.update({
            "algorithm": new_algo,
            "public_key_path": old_key_path,
            "private_key_path": priv_path,
        })
    # Record migration event (if compliance engine is available)
    try:
        from ..compliance_engine import monitor
        monitor.record_event("crypto_migration", {"service": service_module.__name__, "algorithm": new_algo})
    except Exception:
        pass

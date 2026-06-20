# attack_simulation.py
"""Quantum attack simulation utilities.
Provides cost estimations for Grover and Shor attacks.
"""

from typing import Dict, Any
import math

def grover_complexity(symmetric_key_bits: int, target_success_prob: float = 0.9) -> int:
    """Estimate the number of Grover iterations needed to find a secret.
    Args:
        symmetric_key_bits: size of the key in bits.
        target_success_prob: desired probability of success (default 0.9).
    Returns:
        Estimated number of oracle queries (iterations).
    """
    # Grover's algorithm gives O(sqrt(N)) where N = 2^bits
    N = 2 ** symmetric_key_bits
    # Approximate iterations for given success probability
    # Using probability ~ sin^2((2k+1) * theta) where sin(theta)=1/sqrt(N)
    # Simplify with k ≈ (π/4) * sqrt(N)
    iterations = int((math.pi / 4) * math.sqrt(N))
    return iterations

def shor_rsa_break_time(rsa_key_bits: int, quantum_gate_rate: float = 1e9) -> float:
    """Estimate time (seconds) to break RSA using Shor's algorithm.
    Args:
        rsa_key_bits: RSA modulus size.
        quantum_gate_rate: number of quantum gate operations per second.
    Returns:
        Approximate runtime in seconds.
    """
    # Rough estimate: O((log N)^3) quantum operations
    # Using a simple linear model for demonstration
    ops = (rsa_key_bits ** 3) * 2  # placeholder constant factor
    return ops / quantum_gate_rate

def simulate_attack(target: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """High‑level simulation dispatcher.
    Args:
        target: Type of primitive ("symmetric", "rsa").
        parameters: Dict with algorithm‑specific parameters.
    Returns:
        Dictionary with estimated effort metrics.
    """
    if target == "symmetric":
        bits = parameters.get("key_bits", 128)
        prob = parameters.get("success_prob", 0.9)
        iters = grover_complexity(bits, prob)
        return {"type": "grover", "key_bits": bits, "iterations": iters}
    if target == "rsa":
        bits = parameters.get("key_bits", 2048)
        rate = parameters.get("gate_rate", 1e9)
        time_sec = shor_rsa_break_time(bits, rate)
        return {"type": "shor", "key_bits": bits, "estimated_seconds": time_sec}
    raise ValueError(f"Unsupported target: {target}")

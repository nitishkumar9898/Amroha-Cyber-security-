"""
CryptoForge Core Engine
=======================
Post-quantum cryptanalysis simulation, weak-encryption detection,
side-channel vulnerability assessment, and quantum-readiness scoring.

NOTE: All simulations are *theoretical estimates* for ethical security testing.
No actual key-breaking is performed.
"""

import datetime
import math
from typing import Dict, Any, List, Optional

# ══════════════════════════════════════════════════════════════════════
# 1. Post-Quantum Cryptanalysis Simulation
# ══════════════════════════════════════════════════════════════════════

# Classical brute-force complexity (log₂ operations) by algorithm family
_CLASSICAL_SECURITY: Dict[str, callable] = {
    "AES":       lambda ks: ks,                        # AES-128 → 128-bit security
    "RSA":       lambda ks: int(ks * 0.04),            # ~80-bit for RSA-2048
    "ECC":       lambda ks: ks // 2,                   # ECDLP: n/2 bits
    "3DES":      lambda ks: 112 if ks >= 168 else 56,
    "ChaCha20":  lambda ks: 256,
    "Kyber":     lambda ks: ks,                        # post-quantum lattice
    "Dilithium": lambda ks: ks,
    "NTRU":      lambda ks: ks,
}

# Quantum attack complexity (Grover halves symmetric, Shor breaks RSA/ECC)
_QUANTUM_ATTACKS: Dict[str, Dict[str, Any]] = {
    "RSA": {
        "shor": {
            "qubits_factor": 2,        # ~2n logical qubits for n-bit key
            "time_factor": "poly",     # polynomial time
            "broken": True,
        },
        "grover": {
            "qubits_factor": 0.5,
            "time_factor": "sqrt",
            "broken": False,
        },
    },
    "ECC": {
        "shor": {
            "qubits_factor": 6,        # ~6n qubits for n-bit ECC
            "time_factor": "poly",
            "broken": True,
        },
    },
    "AES": {
        "grover": {
            "qubits_factor": 1,
            "time_factor": "sqrt",     # halves security level
            "broken": False,           # AES-256 → 128-bit post-quantum
        },
    },
    "Kyber":     {},  # No known quantum attack
    "Dilithium": {},
    "NTRU":      {},
}


def simulate_cryptanalysis(algorithm: str, key_size: int,
                           attack_type: str) -> Dict[str, Any]:
    """Run a theoretical cryptanalysis simulation.
    Returns estimated qubits, time, and whether the algorithm is broken.
    """
    algo_upper = algorithm.upper()
    security_fn = _CLASSICAL_SECURITY.get(algorithm, lambda ks: ks)
    classical_bits = security_fn(key_size)

    attacks = _QUANTUM_ATTACKS.get(algorithm, {})
    attack_info = attacks.get(attack_type, None)

    if attack_info:
        qubits = int(key_size * attack_info["qubits_factor"])
        if attack_info["time_factor"] == "poly":
            # Polynomial: assume O(n³) gate operations → negligible years
            time_years = round(key_size ** 3 / 1e18, 6)  # assuming 10^18 gates/s future QC
        else:
            # Grover: sqrt speedup → 2^(n/2) operations
            grover_bits = classical_bits / 2
            time_years = round(2 ** (grover_bits - 60), 4)  # 2^60 ops/year estimate
        broken = attack_info.get("broken", False)
    else:
        qubits = None
        time_years = None
        broken = False

    # Classical brute-force time for comparison
    classical_years = 2 ** (classical_bits - 60) if classical_bits > 60 else 0.001

    return {
        "algorithm": algorithm,
        "key_size": key_size,
        "attack_type": attack_type,
        "classical_security_bits": classical_bits,
        "estimated_qubits": qubits,
        "estimated_time_years": time_years,
        "classical_brute_force_years": round(classical_years, 4),
        "quantum_broken": broken,
        "quantum_safe": not broken,
        "recommendation": _recommend(algorithm, broken, key_size),
    }


def _recommend(algorithm: str, broken: bool, key_size: int) -> str:
    if broken:
        return f"CRITICAL: {algorithm}-{key_size} is vulnerable to quantum attack. Migrate to post-quantum algorithm (Kyber/Dilithium)."
    if algorithm in ("Kyber", "Dilithium", "NTRU"):
        return f"{algorithm}-{key_size} is quantum-safe. No action required."
    return f"{algorithm}-{key_size} offers adequate classical security. Consider post-quantum migration for long-term protection."


# ══════════════════════════════════════════════════════════════════════
# 2. Weak Encryption Detection
# ══════════════════════════════════════════════════════════════════════

_WEAK_CIPHERS = {
    "DES", "3DES", "RC4", "MD5", "SHA1",
    "TLS_RSA_WITH_RC4_128_MD5", "TLS_RSA_WITH_RC4_128_SHA",
    "TLS_RSA_WITH_3DES_EDE_CBC_SHA",
    "SSLv2", "SSLv3", "TLSv1.0", "TLSv1.1",
}

_WEAK_KEY_SIZES = {
    "RSA": 1024,
    "ECC": 160,
    "AES": 64,   # hypothetical weak config
}


def scan_weak_encryption(target: str, scan_type: str) -> Dict[str, Any]:
    """Simulate scanning a target for weak encryption.
    In production this would perform a real TLS handshake / cert audit.
    Returns findings list and risk score.
    """
    # Placeholder: generate synthetic findings based on scan_type
    findings: List[Dict[str, Any]] = []

    if scan_type in ("tls_scan", "cipher_suite"):
        # Simulate finding deprecated protocols
        findings.append({
            "type": "deprecated_protocol",
            "protocol": "TLSv1.0",
            "severity": "high",
            "recommendation": "Disable TLSv1.0; enforce TLSv1.2+",
        })
        findings.append({
            "type": "weak_cipher",
            "cipher": "TLS_RSA_WITH_3DES_EDE_CBC_SHA",
            "severity": "medium",
            "recommendation": "Remove 3DES cipher suites",
        })
    elif scan_type == "cert_audit":
        findings.append({
            "type": "short_key",
            "algorithm": "RSA",
            "key_size": 1024,
            "severity": "critical",
            "recommendation": "Upgrade to RSA-2048 or ECC-P256 minimum",
        })
    elif scan_type == "key_exchange":
        findings.append({
            "type": "no_pfs",
            "description": "Server does not support Perfect Forward Secrecy",
            "severity": "high",
            "recommendation": "Enable ECDHE or DHE key exchange",
        })

    severity_map = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
    risk_score = max((severity_map.get(f.get("severity", "low"), 0.2) for f in findings), default=0.0)

    return {
        "findings": findings,
        "risk_score": round(risk_score, 4),
    }


# ══════════════════════════════════════════════════════════════════════
# 3. Side-Channel Vulnerability Assessment
# ══════════════════════════════════════════════════════════════════════

_KNOWN_SIDE_CHANNEL_VULNS: Dict[str, Dict[str, Any]] = {
    "timing": {
        "RSA":   {"vulnerable": True, "leakage": 0.7, "note": "Non-constant-time modular exponentiation"},
        "AES":   {"vulnerable": False, "leakage": 0.05, "note": "Hardware AES-NI is constant-time"},
        "ECC":   {"vulnerable": True, "leakage": 0.6, "note": "Scalar multiplication timing leak"},
    },
    "power": {
        "RSA":   {"vulnerable": True, "leakage": 0.8, "note": "Simple Power Analysis on square-and-multiply"},
        "AES":   {"vulnerable": True, "leakage": 0.4, "note": "Differential Power Analysis on S-box lookups"},
    },
    "cache": {
        "AES":   {"vulnerable": True, "leakage": 0.65, "note": "Cache-timing attack on T-table implementation"},
        "RSA":   {"vulnerable": True, "leakage": 0.5, "note": "Flush+Reload on modular exponentiation"},
    },
    "electromagnetic": {
        "RSA":   {"vulnerable": True, "leakage": 0.75, "note": "EM emanation during key operations"},
        "AES":   {"vulnerable": True, "leakage": 0.3, "note": "Near-field EM probe on microcontroller"},
    },
}


def assess_side_channel(channel_type: str, target_algorithm: str,
                        target_implementation: Optional[str] = None) -> Dict[str, Any]:
    """Assess side-channel vulnerability for a given algorithm + channel."""
    channel_data = _KNOWN_SIDE_CHANNEL_VULNS.get(channel_type, {})
    algo_data = channel_data.get(target_algorithm, None)

    if algo_data:
        return {
            "vulnerable": algo_data["vulnerable"],
            "leakage_score": algo_data["leakage"],
            "details": {
                "channel": channel_type,
                "algorithm": target_algorithm,
                "implementation": target_implementation,
                "note": algo_data["note"],
                "mitigation": f"Use constant-time implementation for {target_algorithm}" if algo_data["vulnerable"] else "No action needed",
            },
        }
    return {
        "vulnerable": False,
        "leakage_score": 0.0,
        "details": {
            "channel": channel_type,
            "algorithm": target_algorithm,
            "implementation": target_implementation,
            "note": f"No known {channel_type} side-channel data for {target_algorithm}",
            "mitigation": "N/A",
        },
    }


# ══════════════════════════════════════════════════════════════════════
# 4. Quantum Readiness Scoring
# ══════════════════════════════════════════════════════════════════════

_QUANTUM_SAFE_ALGORITHMS = {"Kyber", "Dilithium", "NTRU", "SPHINCS+", "BIKE", "FrodoKEM"}


def assess_quantum_readiness(algorithms_in_use: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Score an organisation's quantum readiness based on algorithms currently deployed."""
    if not algorithms_in_use:
        return {"overall_score": 0.0, "recommendations": [{"action": "Perform a full cryptographic inventory"}]}

    safe_count = 0
    recommendations: List[Dict[str, Any]] = []

    for entry in algorithms_in_use:
        algo = entry.get("algorithm", "unknown")
        ks = entry.get("key_size", 0)
        if algo in _QUANTUM_SAFE_ALGORITHMS:
            safe_count += 1
            entry["quantum_safe"] = True
        else:
            entry["quantum_safe"] = False
            recommendations.append({
                "algorithm": algo,
                "key_size": ks,
                "action": f"Migrate {algo}-{ks} to a post-quantum alternative (e.g., Kyber-768 for KEM, Dilithium-3 for signatures)",
                "priority": "critical" if algo in ("RSA", "ECC") else "high",
            })

    overall = round(safe_count / len(algorithms_in_use), 4) if algorithms_in_use else 0.0

    return {
        "overall_score": overall,
        "recommendations": recommendations,
    }

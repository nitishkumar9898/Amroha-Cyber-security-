import random
from typing import Dict, Any, List

def scan_legacy_crypto(target_system: str, scan_id: str) -> List[Dict[str, Any]]:
    """
    Simulates scanning a system for cryptographic assets.
    """
    assets = []
    
    # Simulate finding some legacy keys
    assets.append({
        "scan_id": scan_id,
        "asset_name": f"{target_system} - Root CA",
        "algorithm": "RSA",
        "key_size": 2048,
        "is_quantum_safe": False
    })
    
    assets.append({
        "scan_id": scan_id,
        "asset_name": f"{target_system} - TLS Cert",
        "algorithm": "ECC",
        "key_size": 256,
        "is_quantum_safe": False
    })
    
    assets.append({
        "scan_id": scan_id,
        "asset_name": f"{target_system} - S3 Encryption",
        "algorithm": "AES",
        "key_size": 256,
        "is_quantum_safe": True # AES-256 is largely considered quantum-safe against Grover's
    })
    
    return assets

def calculate_hndl_risk(asset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates the 'Harvest Now, Decrypt Later' risk for an asset.
    """
    alg = asset["algorithm"]
    is_safe = asset["is_quantum_safe"]
    
    if is_safe:
        return None
        
    risk_score = 0.9 if alg == "RSA" else 0.85
    qday_years = random.randint(4, 8)
    criticality = "Critical" if alg == "RSA" else "High"
    
    return {
        "hndl_risk_score": risk_score,
        "estimated_qday_years": qday_years,
        "criticality": criticality
    }

def simulate_pqc_migration(asset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulates performance overhead of migrating to a PQC algorithm.
    """
    alg = asset["algorithm"]
    is_safe = asset["is_quantum_safe"]
    
    if is_safe:
        return None
        
    if alg == "RSA":
        rec_pqc = "CRYSTALS-Kyber (KEM)"
        leg_lat = 1.2
        pqc_lat = 1.8
        mem_oh = 1024.0 # larger keys
    else:
        rec_pqc = "CRYSTALS-Dilithium (Sig)"
        leg_lat = 0.8
        pqc_lat = 2.1
        mem_oh = 2048.0
        
    return {
        "recommended_pqc": rec_pqc,
        "legacy_latency_ms": leg_lat,
        "pqc_latency_ms": pqc_lat,
        "memory_overhead_kb": mem_oh
    }

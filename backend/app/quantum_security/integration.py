# quantum_security/integration.py
"""Integration helpers for QuantumShield.
Provides functions to register quantum‑security hooks into existing services.
"""

from typing import Any

def register_quantum_hooks():
    """Inject quantum‑related events into services.
    Currently patches:
    - MalwareForgeService.evaluate_threat (already patched separately).
    - DarkIntelService.perform_darkweb_investigation to encrypt the report payload.
    - MisinformationPipeline.evaluate_claim to log a compliance event.
    """
    # Import target modules lazily to avoid circular imports.
    from ..services.malwareforge_service import MalwareForgeService
    from ..services.darkintel_service import DarkIntelService
    from ..modules.misinformation import MisinformationPipeline
    from ..quantum_security.pqcrypto import generate_keypair, encrypt
    from ..compliance_engine import monitor

    # Patch DarkIntelService.perform_darkweb_investigation
    original_darkintel = DarkIntelService.perform_darkweb_investigation

    def patched_perform_darkweb_investigation(self, query: str, officer_id: str, agency_name: str) -> dict:
        result = original_darkintel(self, query, officer_id, agency_name)
        # Encrypt the report payload using PQC (Kyber) for demonstration.
        public_key, _ = generate_keypair("kyber1024")
        # Serialize payload to JSON bytes.
        import json as _json
        payload_bytes = _json.dumps(result.get("proof_of_forensic_integrity", {})).encode()
        encrypted = encrypt("kyber1024", public_key, payload_bytes)
        # Attach encrypted proof.
        result["pqc_encrypted_proof"] = encrypted.hex()
        # Log event.
        monitor.record_event("darkintel_pqc_encryption", {
            "service": "darkintel",
            "algorithm": "kyber1024",
            "encrypted_len": len(encrypted)
        })
        return result

    DarkIntelService.perform_darkweb_investigation = patched_perform_darkweb_investigation

    # Patch MisinformationPipeline.evaluate_claim
    original_misinfo = MisinformationPipeline.evaluate_claim

    def patched_evaluate_claim(claim_text: str) -> dict:
        result = original_misinfo(claim_text)
        # Record compliance event for claim evaluation.
        monitor.record_event("misinformation_claim_evaluated", {
            "claim": claim_text,
            "credibility_score": result.get("credibility_score")
        })
        return result

    MisinformationPipeline.evaluate_claim = staticmethod(patched_evaluate_claim)

    # Return a summary of applied patches.
    return {
        "darkintel": "patched",
        "misinformation": "patched",
        "malwareforge": "already patched"
    }

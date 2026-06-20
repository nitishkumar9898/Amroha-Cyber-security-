import random
import hashlib
from typing import Dict, Any, List

class BlockchainAnalyzer:
    """Mock AI-driven blockchain analyzer and wallet tracer."""
    
    @staticmethod
    def trace_wallet(initial_address: str, amount: float) -> Dict[str, Any]:
        """Simulates tracing funds through mixers and intermediate wallets."""
        # Generate mock hop wallets
        wallets = [
            {"address": initial_address, "wallet_type": "INITIAL_DEPOSIT", "balance": amount},
            {"address": f"bc1q_{random.randint(1000, 9999)}_mixer", "wallet_type": "MIXER", "balance": amount * 0.95},
            {"address": f"bc1q_{random.randint(1000, 9999)}_cashout", "wallet_type": "CASH_OUT", "balance": amount * 0.90}
        ]
        
        # Generate mock transaction edges
        traces = [
            {"from": wallets[0]["address"], "to": wallets[1]["address"], "amount": amount * 0.95, "risk_score": 0.85},
            {"from": wallets[1]["address"], "to": wallets[2]["address"], "amount": amount * 0.90, "risk_score": 0.98}
        ]
        
        return {
            "wallets": wallets,
            "traces": traces
        }

class VariantDetector:
    """Classifies ransomware variants and provides simulated decryption keys."""
    
    @staticmethod
    def analyze_ransom_note(note_text: str) -> Dict[str, Any]:
        """Simulates variant detection based on note text patterns."""
        lower_note = note_text.lower()
        if "lockbit" in lower_note or "decryption id" in lower_note:
            variant = "LockBit_3.0_Simulated"
            decryptable = False
        elif "ryuk" in lower_note or "shadow" in lower_note:
            variant = "Ryuk_Legacy_Simulated"
            decryptable = True
        else:
            variant = "Generic_Ransomware_Simulated"
            decryptable = random.choice([True, False])
            
        key = hashlib.sha256(note_text.encode()).hexdigest() if decryptable else None
        
        return {
            "variant": variant,
            "is_decryptable": decryptable,
            "simulated_decryption_key": key
        }

class AttributionEngine:
    """Links simulated payment flows and variants to APT groups."""
    
    @staticmethod
    def attribute(variant: str, cashout_address: str) -> str:
        if "Ryuk" in variant:
            return "APT_WIZARD_SPIDER"
        elif "LockBit" in variant:
            return "LOCKBIT_AFFILIATE_NETWORK"
        else:
            return "UNKNOWN_FINANCIAL_SYNDICATE"

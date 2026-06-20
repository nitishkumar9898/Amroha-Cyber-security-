import hashlib
import uuid

class AnomalyDetector:
    """Analyzes transaction velocity and amount."""
    @staticmethod
    def detect(amount: float, velocity_score: float) -> dict:
        # High velocity (> 10 tx/min) and large cumulative amount flags anomaly
        if velocity_score > 10.0 and amount > 50000.0:
            is_anomalous = True
            action = "FRAUD_ALERT: Account frozen due to high velocity/volume anomaly."
        else:
            is_anomalous = False
            action = "Transaction cleared."
            
        return {
            "is_anomalous": is_anomalous,
            "action_taken": action
        }

class PaymentTracer:
    """Traces multi-hop payment complexity."""
    @staticmethod
    def trace(hop_sequence: str) -> dict:
        seq = hop_sequence.upper()
        hops = seq.split("->")
        complexity = len(hops) * 2.5
        
        crosses_borders = "SWIFT" in seq or "CROSS-BORDER" in seq
        
        if "CRYPTO" in seq and crosses_borders:
            complexity += 5.0
            status = "HIGH_COMPLEXITY: Potential obfuscation routing detected."
        else:
            status = "TRACE_NOMINAL."
            
        return {
            "complexity_score": complexity,
            "crosses_borders": crosses_borders,
            "trace_status": status
        }

class LaunderingAnalyzer:
    """Detects laundering patterns like Smurfing."""
    @staticmethod
    def analyze(tx_count: int, avg_amount: float, osint_flag: bool, ransom_flag: bool) -> dict:
        # Smurfing detection: many transactions just under reporting threshold (e.g., 9999)
        pattern = "NONE"
        risk = "LOW"
        
        if tx_count > 50 and 9000.0 < avg_amount < 10000.0:
            pattern = "SMURFING"
            risk = "HIGH"
            
        if osint_flag or ransom_flag:
            pattern = f"{pattern} + THREAT_INTEL_MATCH"
            risk = "CRITICAL"
            
        return {
            "pattern_type": pattern,
            "risk_level": risk
        }

class ComplianceGenerator:
    """Generates standardized reporting hashes for regulatory bodies."""
    @staticmethod
    def generate(agency: str, raw_data: str) -> dict:
        report_id = f"{agency.upper()}-{uuid.uuid4().hex[:8]}"
        data_hash = hashlib.sha256(raw_data.encode()).hexdigest()
        
        return {
            "report_id": report_id,
            "report_hash": data_hash,
            "submission_status": "READY_FOR_SUBMISSION"
        }

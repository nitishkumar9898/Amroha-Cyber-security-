import random

class GenomicThreatAnalyzer:
    """Simulates scanning an intercepted DNA/RNA sequence against pathogenic markers."""
    @staticmethod
    def analyze() -> dict:
        bioweapon_probability = random.uniform(5.0, 98.0)
        pathogenic_markers_found = random.randint(0, 15)
        
        is_threat = bioweapon_probability > 75.0 or pathogenic_markers_found > 5
        
        return {
            "bioweapon_probability": bioweapon_probability,
            "pathogenic_markers_found": pathogenic_markers_found,
            "is_threat": is_threat
        }

class SynthesisFacilityMonitor:
    """Simulates monitoring SCADA networks of automated DNA synthesizers."""
    @staticmethod
    def monitor() -> dict:
        scada_anomaly_score = random.uniform(0.0, 100.0)
        unauthorized_prints_detected = random.randint(0, 3)
        
        is_compromised = scada_anomaly_score > 80.0 or unauthorized_prints_detected > 0
        
        return {
            "scada_anomaly_score": scada_anomaly_score,
            "unauthorized_prints_detected": unauthorized_prints_detected,
            "is_compromised": is_compromised
        }

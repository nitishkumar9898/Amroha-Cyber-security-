class ScadaAnalyzer:
    """Analyzes ICS/SCADA protocol payloads for anomalies."""
    @staticmethod
    def analyze(protocol: str, payload: str, frequency: float) -> dict:
        is_anomalous = False
        reason = "Protocol parameters nominal."
        
        # High frequency read/writes or unauthorized function codes
        if frequency > 100.0:
            is_anomalous = True
            reason = f"Anomalous high-frequency {protocol} polling detected."
        elif "0x5A" in payload or "UNAUTH_WRITE" in payload.upper():
            is_anomalous = True
            reason = f"Unauthorized {protocol} write command injected."
            
        return {
            "is_anomalous": is_anomalous,
            "flag_reason": reason
        }

class PhysicalSimulator:
    """Computes kinetic damage probabilities for cyber-physical attacks."""
    @staticmethod
    def simulate(injected_rpm: float, normal_rpm: float) -> dict:
        deviation = (injected_rpm - normal_rpm) / normal_rpm
        
        # If injected RPM is more than 20% higher than normal, risk increases
        probability = 0.0
        warning = "System stable."
        
        if deviation > 0.2:
            probability = min((deviation - 0.2) * 100.0 * 2.5, 99.9)
            warning = "CRITICAL: Centrifugal force exceeding structural limits."
        elif deviation < -0.2:
            probability = min(abs(deviation + 0.2) * 100.0 * 1.5, 80.0)
            warning = "WARNING: Stall condition risk."
            
        return {
            "kinetic_damage_probability": probability,
            "structural_integrity_warning": warning
        }

class ResiliencePlanner:
    """Generates blackout mitigation strategies."""
    @staticmethod
    def plan(current_load: float, compromised_nodes: int) -> dict:
        islanding = False
        shed_percentage = 0.0
        action = "Maintain normal grid operations."
        
        if compromised_nodes > 5:
            islanding = True
            shed_percentage = 35.0
            action = "EMERGENCY: Initiate microgrid islanding. Shed 35% non-critical load to prevent cascading failure."
        elif compromised_nodes > 0:
            shed_percentage = compromised_nodes * 2.5
            action = f"WARNING: Isolate {compromised_nodes} compromised nodes. Reroute power."
            
        return {
            "load_shedding_percentage": shed_percentage,
            "islanding_required": islanding,
            "action_plan": action
        }

class ThreatForecaster:
    """Projects 5-year vulnerabilities for energy infrastructure."""
    @staticmethod
    def forecast(iot_level: float, past_incidents: int) -> dict:
        # Simple projection heuristic
        base_risk = 20.0
        iot_risk = iot_level * 5.0
        incident_multiplier = 1.0 + (past_incidents * 0.1)
        
        total_risk = min((base_risk + iot_risk) * incident_multiplier, 100.0)
        
        vector = "Legacy ICS Protocol Exploitation"
        if iot_level > 6.0:
            vector = "Supply Chain / IoT Botnet Pivot"
            
        return {
            "five_year_risk_score": total_risk,
            "primary_threat_vector": vector
        }

from datetime import datetime

class ContinuousAuthenticator:
    """Evaluates contextual signals to output a dynamic Trust Score."""
    @staticmethod
    def evaluate(is_off_hours: bool, geo_location_anomaly: bool) -> dict:
        base_score = 100.0
        anomalies = 0
        
        if is_off_hours:
            base_score -= 15.0
            anomalies += 1
            
        if geo_location_anomaly:
            base_score -= 40.0
            anomalies += 1
            
        status = "Trusted"
        if base_score < 70.0:
            status = "Elevated Risk"
        if base_score < 50.0:
            status = "Untrusted"
            
        return {
            "trust_score": max(0.0, base_score),
            "context_anomalies": anomalies,
            "auth_status": status
        }

class MicroSegmenter:
    """Simulates Default Deny micro-segmentation."""
    @staticmethod
    def evaluate_route(source: str, target: str, is_whitelisted: bool) -> dict:
        if not is_whitelisted:
            return {
                "status": "BLOCKED: Default Deny. Route not explicitly whitelisted."
            }
        return {
            "status": "ALLOWED: Route is whitelisted."
        }

class LeastPrivilegeEvaluator:
    """Compares Trust Score against required threshold for a resource."""
    @staticmethod
    def evaluate(user_score: float, required_score: float) -> dict:
        if user_score >= required_score:
            return {
                "access_granted": True,
                "reason": f"User trust score ({user_score}) meets requirement ({required_score})."
            }
        else:
            return {
                "access_granted": False,
                "reason": f"Access Denied. Trust score ({user_score}) below required threshold ({required_score})."
            }

class PolicyEnforcer:
    """Triggers automated responses based on trust scores and events."""
    @staticmethod
    def enforce(trigger_event: str, trust_score: float) -> dict:
        action = "Log Event Only"
        
        if trust_score < 50.0:
            action = "Terminate Session & Quarantine User"
        elif trust_score < 75.0:
            action = "Trigger Step-Up MFA Challenge"
        elif trigger_event.upper() == "UNAUTHORIZED_SEGMENT_ACCESS":
            action = "Alert SOC & Drop Packets"
            
        return {
            "action_taken": action,
            "timestamp": datetime.utcnow().isoformat()
        }

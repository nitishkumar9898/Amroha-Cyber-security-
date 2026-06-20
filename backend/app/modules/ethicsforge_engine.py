class BiasScanner:
    """Mocks scanning AI datasets/models for statistical bias."""
    @staticmethod
    def scan(model_name: str, dataset_signature: str) -> dict:
        # Mock logic: If the dataset signature contains "DEMO_SKEW", flag it
        skewed = "DEMO_SKEW" in dataset_signature.upper()
        score = 0.85 if skewed else 0.12
        mitigated = skewed # Simulate auto-mitigation if skewed
        
        return {
            "bias_score": score,
            "demographic_skew_detected": skewed,
            "mitigation_applied": mitigated
        }

class EthicalArbiter:
    """Evaluates proposed actions against active policies."""
    @staticmethod
    def evaluate(proposed_action: str, action_context: str, policies: list) -> dict:
        action_upper = proposed_action.upper()
        
        for policy in policies:
            # Simple mock rule matching based on policy description keywords
            if "LETHAL" in policy.description.upper() and "LETHAL" in action_upper:
                decision = "VETOED" if policy.severity_level == "CRITICAL" else "WARNING"
                return {"decision": decision, "justification": f"Violates policy: {policy.policy_name}", "violating_policy_id": policy.id}
                
            if "HUMAN-IN-THE-LOOP" in policy.description.upper() and "AUTOMATED_ISOLATION" in action_upper:
                decision = "VETOED" if policy.severity_level == "CRITICAL" else "WARNING"
                return {"decision": decision, "justification": f"Requires HITL approval per: {policy.policy_name}", "violating_policy_id": policy.id}

        return {"decision": "APPROVED", "justification": "Passed all active ethical policies.", "violating_policy_id": None}

class TransparencyReporter:
    """Generates XAI explanations."""
    @staticmethod
    def generate_explanation(proposed_action: str, decision: str, justification: str) -> str:
        if decision == "VETOED":
            return f"The automated system attempted to execute '{proposed_action}'. The Ethical Arbiter VETOED this action because: {justification}. A human supervisor must override to proceed."
        elif decision == "WARNING":
            return f"The action '{proposed_action}' was allowed, but flagged with a WARNING: {justification}. Proceed with caution."
        else:
            return f"The action '{proposed_action}' was evaluated. Neural weights indicate no policy violations. Action execution authorized."

"""
Cyber Psychology & Behavioral Profiling Module
Analyzes threat correspondence, misinformation text, or deepfake audio scripts to extract
behavioral traits, target cognitive vulnerabilities, and detect threat actor psychological intents.
"""
import re
from typing import Dict, Any, List

class CyberPsychologyProfiler:
    @staticmethod
    def profile_incident_text(text_sample: str) -> Dict[str, Any]:
        """
        Extracts emotional signatures, targeted cognitive vulnerabilities,
        manipulation strategies, and categorizes intent.
        """
        text_lower = text_sample.lower()
        
        # 1. Detect Manipulation Strategies
        strategies = []
        if any(w in text_lower for w in ["immediately", "now", "hours", "urgent", "critical", "deadline"]):
            strategies.append("Artificial Urgency")
        if any(w in text_lower for w in ["pay", "bitcoin", "btc", "ransom", "destroy", "leak", "compromise"]):
            strategies.append("Coercive Fear-Mongering")
        if any(w in text_lower for w in ["lie", "fake", "cover-up", "conspiracy", "truth", "secret"]):
            strategies.append("Outrage Amplification & Gaslighting")
        if any(w in text_lower for w in ["proof", "authentic", "official", "evidence", "certified"]):
            strategies.append("Authority Exploitation")
            
        if not strategies:
            strategies.append("Information Gathering")

        # 2. Cognitive Biases Targeted
        biases = []
        if "Outrage Amplification & Gaslighting" in strategies:
            biases.append("Confirmation Bias")
            biases.append("Hostile Attribution Bias")
        if "Artificial Urgency" in strategies:
            biases.append("Loss Aversion / Hyperbolic Discounting")
        if "Authority Exploitation" in strategies:
            biases.append("Authority Bias")
        if not biases:
            biases.append("Anchor Bias")

        # 3. Emotional Resonance Estimation
        hostility = round(0.85 if "Coercive Fear-Mongering" in strategies else 0.20, 2)
        deception = round(0.90 if "Outrage Amplification & Gaslighting" in strategies else 0.35, 2)
        panic_index = round(0.80 if "Artificial Urgency" in strategies else 0.25, 2)

        # 4. Intent Classification
        intent = "Disinformation / Influence"
        if "pay" in text_lower or "btc" in text_lower:
            intent = "Financial Extortion"
        elif "hack" in text_lower or "apt" in text_lower or "c2" in text_lower:
            intent = "State-Sponsored Espionage"
        elif "leak" in text_lower:
            intent = "Information Disruption"

        # Threat severity calculation
        threat_score = round((hostility * 0.4) + (deception * 0.3) + (panic_index * 0.3), 2)

        return {
            "linguistic_metrics": {
                "urgency_markers": "HIGH" if "Artificial Urgency" in strategies else "MEDIUM",
                "hostility_rating": "HIGH" if hostility > 0.6 else "LOW",
                "threat_score": threat_score
            },
            "cognitive_profile": {
                "motivational_driver": intent,
                "calculated_structure": "Highly Organized / Targeted" if threat_score > 0.6 else "Opportunistic / Diffuse",
                "manipulation_strategies_deployed": strategies,
                "targeted_cognitive_vulnerabilities": biases
            },
            "resonance_profile": {
                "hostility_resonance": hostility,
                "deception_index": deception,
                "panic_inducement": panic_index
            },
            "investigative_guidelines": [
                "Assess temporal shifts in language pattern to fingerprint threat actor shift schedules.",
                "Map targeted cognitive vulnerabilities to current employee training modules for defense mitigation."
            ]
        }

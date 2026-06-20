import uuid
import random

class ScenarioDirector:
    """Manages the creation and state of Global Scenarios."""
    @staticmethod
    def create_scenario(name: str) -> dict:
        return {
            "status": "ACTIVE",
            "global_resilience_score": 100.0
        }

class CascadeEngine:
    """Calculates probabilities of cyber attacks cascading across different platform modules."""
    @staticmethod
    def calculate_cascades(source_module: str, severity: str) -> list:
        cascades = []
        
        # Define module cascade affinities (conceptual representation of the 30 modules)
        affinities = {
            "SpaceGuard": ["NetGuard", "GridShield", "CloudForensix"],
            "NanoQuantum": ["QuantumSafe", "InnovateGuard"],
            "PromptDefender": ["OSINT", "NeuroGuard", "HumanForge"],
            "SupplyChain": ["ResilientForge", "HardwareForensix"],
            "GridShield": ["CloudForensix", "NetGuard", "RansomGuard"],
            "ZeroTrustForge": [] # ZeroTrust absorbs impact, doesn't spread it usually
        }
        
        targets = affinities.get(source_module, ["NetGuard", "ResponseForge"])
        
        base_prob = 0.5 if severity == "HIGH" else (0.8 if severity == "CRITICAL" else 0.2)
        
        for target in targets:
            prob = base_prob * random.uniform(0.8, 1.2)
            if prob > 0.4: # Threshold to trigger cascade
                cascades.append({
                    "target_module": target,
                    "cascade_probability": min(prob, 1.0),
                    "impact_description": f"Cascading failure induced from {source_module} breach."
                })
                
        return cascades

class OmniDefenseCoordinator:
    """Calculates the global resilience score as attacks cascade."""
    @staticmethod
    def calculate_impact(current_score: float, cascades: list) -> float:
        damage = len(cascades) * 5.0
        # Simulated mitigation from active defensive modules
        mitigation = 2.0 
        new_score = current_score - (damage - mitigation)
        return max(0.0, new_score)

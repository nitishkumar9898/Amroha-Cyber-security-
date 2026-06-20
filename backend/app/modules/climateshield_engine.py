class InfraAttackModeler:
    """Simulates cyber-physical attacks during extreme weather."""
    @staticmethod
    def simulate(infra_type: str, weather: str, attack_vector: str) -> dict:
        infra_type = infra_type.upper()
        weather = weather.upper()
        
        # Base risk
        score = 5.0
        
        # Synergy between weather and infra
        if infra_type == "POWER" and weather == "HEATWAVE":
            score += 4.5
            details = "Cascading failure: AC demand spikes while cooling systems for generators are disabled via SCADA hijack."
        elif infra_type == "WATER" and weather == "DROUGHT":
            score += 4.8
            details = "Critical resource depletion: Desalination plants forced offline during severe drought conditions."
        elif infra_type == "AGRICULTURE" and weather == "FLOOD":
            score += 4.0
            details = "Automated dam release gates jammed open during torrential rains, destroying downstream agriculture."
        else:
            score += 2.0
            details = f"Moderate disruption to {infra_type} during {weather}."
            
        return {
            "cascading_impact_score": min(score, 10.0),
            "analysis_details": details
        }

class ClimateManipulator:
    """Simulates 50+ year AI geo-engineering threats."""
    @staticmethod
    def simulate(vector: str, years: int) -> dict:
        vector = vector.upper()
        
        if vector == "ROGUE_AEROSOL":
            eco_damage = min(years * 0.15, 10.0)
            econ_impact = years * 0.5 # Trillions
            details = f"Rogue atmospheric aerosol injection over {years} years causing localized cooling but massive crop failures globally."
        elif vector == "CLOUD_SEEDING_HIJACK":
            eco_damage = min(years * 0.1, 10.0)
            econ_impact = years * 0.3
            details = f"Weaponized cloud seeding algorithms over {years} years starving neighboring nations of rainfall."
        else:
            eco_damage = 2.0
            econ_impact = 1.0
            details = "Unknown geo-engineering vector simulated."
            
        return {
            "ecological_damage_index": eco_damage,
            "economic_impact_trillions": econ_impact,
            "details": details
        }

class ResiliencePlanner:
    """Generates adaptive recovery strategies."""
    @staticmethod
    def generate(trigger: str, severity: float) -> dict:
        trigger = trigger.upper()
        
        if severity > 8.0:
            if "WATER" in trigger:
                strategy = "Activate autonomous hydro-rationing network and deploy mobile atmospheric water generators."
                days = 45
            else:
                strategy = "Initiate decentralized microgrid islanding protocols and emergency rolling blackouts."
                days = 30
        else:
            strategy = "Standard incident response and localized system reboots."
            days = 7
            
        return {
            "recovery_strategy": strategy,
            "estimated_recovery_days": days
        }

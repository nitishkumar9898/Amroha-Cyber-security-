from typing import Dict, Any, List

def calculate_risk_score(tech_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Simulates multi-dimensional risk scoring for an emerging technology.
    """
    tech_name = tech_data.get("tech_name", "").lower()
    phase = tech_data.get("adoption_phase", "R&D")
    
    # Base multipliers based on phase
    phase_mult = {"R&D": 0.8, "EarlyAdoption": 1.2, "Mainstream": 1.5}.get(phase, 1.0)
    
    cyber, physical, operational = 0.5, 0.5, 0.5
    
    if "ai" in tech_name or "llm" in tech_name:
        cyber = 0.9 * phase_mult
        physical = 0.3 * phase_mult
        operational = 0.8 * phase_mult
    elif "quantum" in tech_name:
        cyber = 0.95 * phase_mult
        physical = 0.4 * phase_mult
        operational = 0.7 * phase_mult
    elif "biotech" in tech_name or "crispr" in tech_name:
        cyber = 0.6 * phase_mult
        physical = 0.95 * phase_mult
        operational = 0.7 * phase_mult
    elif "space" in tech_name or "satellite" in tech_name:
        cyber = 0.8 * phase_mult
        physical = 0.9 * phase_mult
        operational = 0.85 * phase_mult
        
    # Cap at 1.0 (or 100%)
    cyber = min(1.0, cyber)
    physical = min(1.0, physical)
    operational = min(1.0, operational)
    
    composite = (cyber * 0.4) + (physical * 0.3) + (operational * 0.3)
    
    return {
        "cyber_risk_score": cyber,
        "physical_risk_score": physical,
        "operational_risk_score": operational,
        "composite_score": composite
    }

def forecast_scenarios(tech_name: str, scores: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Generates probabilistic scenarios based on the technology and risk scores.
    """
    scenarios = []
    t = tech_name.lower()
    
    if "ai" in t:
        scenarios.append({
            "scenario_name": "Autonomous Model Evasion",
            "description": "AI models develop autonomous evasion techniques against standard SIEMs.",
            "probability": min(0.9, scores["cyber_risk_score"] + 0.1),
            "impact_level": "Critical",
            "timeframe_years": 2
        })
    elif "quantum" in t:
        scenarios.append({
            "scenario_name": "Q-Day Cryptographic Break",
            "description": "Shor's algorithm successfully breaks standard RSA-2048 encryption.",
            "probability": min(0.99, scores["cyber_risk_score"] + 0.2),
            "impact_level": "Critical",
            "timeframe_years": 5
        })
    elif "biotech" in t:
        scenarios.append({
            "scenario_name": "Synthetic Pathogen Leak",
            "description": "Engineered biological asset escapes containment via supply chain compromise.",
            "probability": min(0.8, scores["physical_risk_score"]),
            "impact_level": "Critical",
            "timeframe_years": 4
        })
    elif "space" in t:
        scenarios.append({
            "scenario_name": "LEO Satellite Hijack",
            "description": "Adversary gains C2 over low-earth orbit communications cluster.",
            "probability": min(0.75, scores["cyber_risk_score"]),
            "impact_level": "High",
            "timeframe_years": 3
        })
    else:
        scenarios.append({
            "scenario_name": "General Tech Disruption",
            "description": "Unforeseen operational failure cascades into critical infrastructure.",
            "probability": scores["composite_score"],
            "impact_level": "Medium",
            "timeframe_years": 2
        })
        
    return scenarios

def generate_mitigation_roadmap(scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generates step-by-step mitigation roadmaps for a given scenario.
    """
    s_name = scenario.get("scenario_name", "")
    steps = []
    
    if "Cryptographic" in s_name:
        steps = [
            {"action_item": "Inventory all asymmetric cryptographic assets.", "resource": "Medium"},
            {"action_item": "Deploy Post-Quantum Cryptography (PQC) hybrid algorithms.", "resource": "High"},
            {"action_item": "Rotate roots of trust.", "resource": "High"}
        ]
    elif "AI" in s_name or "Autonomous" in s_name:
        steps = [
            {"action_item": "Implement AI red-teaming protocols.", "resource": "Medium"},
            {"action_item": "Deploy adversarial robust training pipelines.", "resource": "High"}
        ]
    elif "Biotech" in s_name or "Pathogen" in s_name:
        steps = [
            {"action_item": "Enhance physical air-gap systems in BSL-4 labs.", "resource": "High"},
            {"action_item": "Implement zero-trust digital twin monitoring.", "resource": "Medium"}
        ]
    else:
        steps = [
            {"action_item": "Conduct initial threat modeling.", "resource": "Low"},
            {"action_item": "Deploy continuous monitoring sensors.", "resource": "Medium"},
            {"action_item": "Establish rapid incident response playbooks.", "resource": "Medium"}
        ]
        
    return [{"step_order": i+1, "action_item": step["action_item"], "resource_requirement": step["resource"], "status": "Pending"} for i, step in enumerate(steps)]

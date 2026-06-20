"""Attacker psycho-profiling — map TTPs to psychological profiles, categorize attacker types, compute risk assessment."""

from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4

import numpy as np

# ---------------------------------------------------------------------------
# Attacker types with psychological archetypes based on academic research
# ---------------------------------------------------------------------------

ATTACKER_ARCHETYPES: dict[str, dict[str, Any]] = {
    "script_kiddie": {
        "label": "Script Kiddie",
        "motivation": "curiosity_reputation",
        "skill_level": "low",
        "typical_ttps": ["known_vulns", "public_exploits", "ddos_tools", "password_spray"],
        "personality_traits": {"extraversion": 0.6, "neuroticism": 0.5, "agreeableness": 0.3, "conscientiousness": 0.3, "openness": 0.4},
        "risk_factors": {"impulsivity": 0.7, "caution": 0.2, "planning": 0.2},
        "escalation_likelihood": 0.3,
    },
    "hacktivist": {
        "label": "Hacktivist",
        "motivation": "ideological_activism",
        "skill_level": "medium",
        "typical_ttps": ["defacement", "doxxing", "ddos", "data_leak", "website_deface"],
        "personality_traits": {"extraversion": 0.7, "neuroticism": 0.4, "agreeableness": 0.2, "conscientiousness": 0.5, "openness": 0.6},
        "risk_factors": {"ideological_conviction": 0.9, "caution": 0.3, "planning": 0.5},
        "escalation_likelihood": 0.4,
    },
    "insider": {
        "label": "Malicious Insider",
        "motivation": "financial_grievance_coercion",
        "skill_level": "medium",
        "typical_ttps": ["privilege_abuse", "data_exfil", "credential_theft", "sabotage", "espionage"],
        "personality_traits": {"extraversion": 0.3, "neuroticism": 0.7, "agreeableness": 0.2, "conscientiousness": 0.6, "openness": 0.3},
        "risk_factors": {"grievance": 0.8, "financial_pressure": 0.6, "opportunity": 0.9, "caution": 0.6},
        "escalation_likelihood": 0.5,
    },
    "apt": {
        "label": "Advanced Persistent Threat",
        "motivation": "espionage_destabilization",
        "skill_level": "very_high",
        "typical_ttps": ["custom_malware", "zero_day", "spear_phishing", "lateral_movement", "persistence", "exfiltration"],
        "personality_traits": {"extraversion": 0.2, "neuroticism": 0.3, "agreeableness": 0.1, "conscientiousness": 0.9, "openness": 0.7},
        "risk_factors": {"caution": 0.95, "planning": 0.95, "patience": 0.9, "opsec": 0.9},
        "escalation_likelihood": 0.1,
    },
    "cybercriminal": {
        "label": "Cyber Criminal",
        "motivation": "financial_gain",
        "skill_level": "high",
        "typical_ttps": ["ransomware", "banking_trojan", "credential_harvesting", "c2_infra", "money_laundering"],
        "personality_traits": {"extraversion": 0.5, "neuroticism": 0.5, "agreeableness": 0.15, "conscientiousness": 0.7, "openness": 0.5},
        "risk_factors": {"financial_motivation": 0.9, "caution": 0.7, "planning": 0.8, "adaptability": 0.7},
        "escalation_likelihood": 0.3,
    },
}

TTP_PSYCH_MAP: dict[str, dict[str, float]] = {
    "defacement": {"impulsivity": 0.8, "idealism": 0.6, "attention_seeking": 0.9},
    "ddos": {"impulsivity": 0.5, "resourcefulness": 0.4, "group_identity": 0.7},
    "phishing": {"deception": 0.8, "planning": 0.6, "patience": 0.5},
    "spear_phishing": {"deception": 0.9, "research": 0.8, "planning": 0.8, "patience": 0.7},
    "ransomware": {"financial_motivation": 0.9, "ruthlessness": 0.7, "technical_competence": 0.8},
    "data_exfil": {"patience": 0.7, "opsec_awareness": 0.6, "planning": 0.7},
    "zero_day": {"technical_competence": 0.95, "patience": 0.9, "planning": 0.9, "resourcefulness": 0.8},
    "credential_theft": {"resourcefulness": 0.6, "persistence": 0.7, "opportunism": 0.8},
    "privilege_abuse": {"opportunism": 0.9, "entitlement": 0.7, "grievance": 0.5},
    "sabotage": {"grievance": 0.8, "destructiveness": 0.9, "risk_tolerance": 0.7},
    "social_engineering": {"deception": 0.85, "charisma": 0.7, "manipulation": 0.9, "planning": 0.6},
    "lateral_movement": {"patience": 0.8, "technical_competence": 0.8, "stealth": 0.7},
}


@dataclass
class AttackerPsychologicalProfile:
    profile_id: str
    attacker_type: str
    confidence: float
    confidence_interval: tuple[float, float]
    motivation: str
    skill_level: str
    personality_traits: dict[str, float]
    risk_factors: dict[str, float]
    escalation_likelihood: float
    behavioral_fingerprint: dict[str, Any]
    matched_ttps: list[str]
    archetype_scores: dict[str, float]
    raw_scores: dict[str, float]


class AttackerPsychProfiler:
    """Map digital evidence to attacker psychological profiles."""

    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level

    def profile_from_ttps(self, ttps: list[str], evidence_text: Optional[str] = None) -> AttackerPsychologicalProfile:
        if not ttps:
            return self._empty_profile()

        psych_scores: dict[str, float] = {}
        for ttp in ttps:
            ttp_lower = ttp.lower().replace(" ", "_")
            mapped = TTP_PSYCH_MAP.get(ttp_lower, {})
            for trait, score in mapped.items():
                psych_scores[trait] = max(psych_scores.get(trait, 0.0), score)

        archetype_scores = self._compute_archetype_scores(ttps, psych_scores)
        sorted_archetypes = sorted(archetype_scores.items(), key=lambda x: x[1], reverse=True)
        best_match = sorted_archetypes[0][0] if sorted_archetypes else "unknown"
        best_score = sorted_archetypes[0][1] if sorted_archetypes else 0.0

        archetype = ATTACKER_ARCHETYPES.get(best_match, {})
        n = max(len(ttps), 1)
        se = 0.15 / (n ** 0.5)
        z = 1.96 if self.confidence_level >= 0.95 else 1.645
        margin = z * se
        ci_lower = max(0.0, best_score - margin)
        ci_upper = min(1.0, best_score + margin)

        escalation_likelihood = archetype.get("escalation_likelihood", 0.3)
        if psych_scores.get("grievance", 0) > 0.7:
            escalation_likelihood = min(1.0, escalation_likelihood + 0.2)

        fingerprint = self._extract_fingerprint(ttps, psych_scores)

        return AttackerPsychologicalProfile(
            profile_id=str(uuid4()),
            attacker_type=best_match,
            confidence=best_score,
            confidence_interval=(round(ci_lower, 3), round(ci_upper, 3)),
            motivation=archetype.get("motivation", "unknown"),
            skill_level=archetype.get("skill_level", "unknown"),
            personality_traits=archetype.get("personality_traits", {}),
            risk_factors=psych_scores,
            escalation_likelihood=round(escalation_likelihood, 3),
            behavioral_fingerprint=fingerprint,
            matched_ttps=ttps,
            archetype_scores=archetype_scores,
            raw_scores=psych_scores,
        )

    def _compute_archetype_scores(self, ttps: list[str], psych_scores: dict[str, float]) -> dict[str, float]:
        ttp_set = set(t.lower().replace(" ", "_") for t in ttps)
        scores: dict[str, float] = {}
        for arch_id, archetype in ATTACKER_ARCHETYPES.items():
            ttp_overlap = len(ttp_set & set(archetype["typical_ttps"]))
            ttp_score = ttp_overlap / max(len(ttp_set | set(archetype["typical_ttps"])), 1)

            trait_sim = 0.0
            archetype_traits = archetype.get("personality_traits", {})
            if psych_scores and archetype_traits:
                common = set(psych_scores.keys()) & set(archetype_traits.keys())
                if common:
                    trait_sim = np.mean([1 - abs(psych_scores[k] - archetype_traits[k]) for k in common])

            risk_sim = 0.0
            arch_risk = archetype.get("risk_factors", {})
            if psych_scores and arch_risk:
                common = set(psych_scores.keys()) & set(arch_risk.keys())
                if common:
                    risk_sim = np.mean([1 - abs(psych_scores[k] - arch_risk[k]) for k in common])

            scores[arch_id] = round(0.5 * ttp_score + 0.3 * trait_sim + 0.2 * risk_sim, 4)

        return scores

    def _extract_fingerprint(self, ttps: list[str], psych_scores: dict[str, float]) -> dict[str, Any]:
        return {
            "ttp_signature": sorted(ttps),
            "psychometric_vector": {k: round(v, 3) for k, v in sorted(psych_scores.items())},
            "trait_clusters": self._cluster_traits(psych_scores),
        }

    def _cluster_traits(self, scores: dict[str, float]) -> list[dict[str, Any]]:
        clusters = {
            "aggression": ["impulsivity", "ruthlessness", "destructiveness", "anger"],
            "competence": ["technical_competence", "resourcefulness", "adaptability", "planning"],
            "stealth": ["patience", "opsec_awareness", "stealth", "caution"],
            "motivation": ["financial_motivation", "idealism", "grievance", "attention_seeking"],
        }
        result = []
        for cluster_name, traits in clusters.items():
            vals = [scores.get(t, 0.0) for t in traits]
            result.append({
                "cluster": cluster_name,
                "score": round(np.mean(vals), 3) if vals else 0.0,
                "traits": {t: round(scores.get(t, 0.0), 3) for t in traits},
            })
        return result

    def _empty_profile(self) -> AttackerPsychologicalProfile:
        return AttackerPsychologicalProfile(
            profile_id=str(uuid4()),
            attacker_type="unknown",
            confidence=0.0,
            confidence_interval=(0.0, 0.0),
            motivation="unknown",
            skill_level="unknown",
            personality_traits={},
            risk_factors={},
            escalation_likelihood=0.0,
            behavioral_fingerprint={},
            matched_ttps=[],
            archetype_scores={},
            raw_scores={},
        )

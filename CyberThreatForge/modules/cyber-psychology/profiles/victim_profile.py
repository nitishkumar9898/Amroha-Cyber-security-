"""Victim psychological assessment — impact scoring, targeting analysis, social engineering vulnerability, manipulation detection."""

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4

import numpy as np

# ---------------------------------------------------------------------------
# Victim impact severity weights
# ---------------------------------------------------------------------------

IMPACT_WEIGHTS: dict[str, dict[str, float]] = {
    "financial": {
        "identity_theft": 0.9,
        "ransomware": 0.85,
        "banking_fraud": 0.9,
        "crypto_theft": 0.8,
        "credit_card_fraud": 0.7,
    },
    "psychological": {
        "doxxing": 0.75,
        "harassment": 0.8,
        "sextortion": 0.95,
        "stalking": 0.9,
        "reputation_damage": 0.7,
    },
    "social": {
        "account_takeover": 0.6,
        "social_engineering": 0.7,
        "phishing_victim": 0.5,
        "romance_scam": 0.85,
        "impersonation": 0.7,
    },
}

TARGETING_PATTERNS: dict[str, list[str]] = {
    "high_profile": ["ceo", "executive", "director", "president", "founder", "official"],
    "financial_access": ["accountant", "finance", "treasurer", "cfo", "banking"],
    "technical_access": ["admin", "sysadmin", "developer", "engineer", "it_manager"],
    "personal_connection": ["family", "friend", "spouse", "partner", "assistant"],
    "public_figure": ["journalist", "activist", "politician", "researcher", "academic"],
}

SE_MANIPULATION_PATTERNS: list[dict[str, Any]] = [
    {"pattern": r"\burgen[ct]\b", "tactic": "urgency", "weight": 0.7},
    {"pattern": r"\b(?:act|reply|click|send)\s*(?:now|immediately|right\s*away)\b", "tactic": "urgency", "weight": 0.8},
    {"pattern": r"\b(?:limited|exclusive|only\s*(?:today|now))\b", "tactic": "scarcity", "weight": 0.6},
    {"pattern": r"\b(?:authority|official|verified|legitimate|trusted)\b", "tactic": "authority", "weight": 0.7},
    {"pattern": r"\b(?:password|verify|confirm|account|login|credential)\b", "tactic": "information_harvesting", "weight": 0.8},
    {"pattern": r"\b(?:suspended|terminated|blocked|compromised|violation)\b", "tactic": "fear", "weight": 0.85},
    {"pattern": r"\b(?:you\s*won|prize|reward|free|gift|congratulations)\b", "tactic": "lure", "weight": 0.7},
    {"pattern": r"\b(?:kindly|please|dear\s*(?:user|customer|sir|madam))\b", "tactic": "politeness_manipulation", "weight": 0.5},
    {"pattern": r"\b(?:attachment|document|invoice|receipt|statement)\b", "tactic": "payload_delivery", "weight": 0.75},
    {"pattern": r"\b(?:threat|legal|action|sue|police|authority|report)\b", "tactic": "intimidation", "weight": 0.8},
    {"pattern": r"\b(?:secret|confidential|private|internal|classified)\b", "tactic": "curiosity_bait", "weight": 0.6},
    {"pattern": r"\b(?:colleague|manager|boss|supervisor|hr)\b", "tactic": "social_proof", "weight": 0.6},
]


@dataclass
class VictimPsychologicalAssessment:
    assessment_id: str
    impact_severity: str
    impact_score: float
    targeting_analysis: dict[str, Any]
    social_engineering_vulnerability: float
    manipulation_detected: list[dict[str, Any]]
    recommendation: str


class VictimPsychProfiler:
    """Assess victim psychology from digital evidence."""

    def assess_impact(
        self,
        incident_type: str,
        victim_role: str,
        exposure_indicators: list[str],
        context: Optional[str] = None,
    ) -> VictimPsychologicalAssessment:
        impact_score = self._compute_impact_score(incident_type, exposure_indicators)
        targeting = self._analyze_targeting(victim_role, context or "")
        se_vuln = self._assess_se_vulnerability(victim_role, exposure_indicators)
        manipulation = self._detect_manipulation(context or "", exposure_indicators)

        severity = "critical" if impact_score >= 0.8 else "high" if impact_score >= 0.6 else "medium" if impact_score >= 0.3 else "low"

        rec = self._generate_recommendation(severity, se_vuln, manipulation)

        return VictimPsychologicalAssessment(
            assessment_id=str(uuid4()),
            impact_severity=severity,
            impact_score=round(impact_score, 3),
            targeting_analysis=targeting,
            social_engineering_vulnerability=round(se_vuln, 3),
            manipulation_detected=manipulation,
            recommendation=rec,
        )

    def analyze_messages(self, messages: list[str]) -> VictimPsychologicalAssessment:
        combined = " ".join(messages)
        exposure = []
        for pattern in SE_MANIPULATION_PATTERNS:
            if re.search(pattern["pattern"], combined, re.IGNORECASE):
                exposure.append(pattern["tactic"])
        return self.assess_impact("social_engineering", "target", exposure, combined)

    def _compute_impact_score(self, incident_type: str, indicators: list[str]) -> float:
        scores = []
        for category, types in IMPACT_WEIGHTS.items():
            for itype, weight in types.items():
                if itype in incident_type.lower() or itype in [i.lower() for i in indicators]:
                    scores.append(weight)
        for indicator in indicators:
            for category, types in IMPACT_WEIGHTS.items():
                for itype, weight in types.items():
                    if itype in indicator.lower():
                        scores.append(weight * 0.8)
        if not scores:
            return 0.3
        return float(np.clip(np.mean(scores) + 0.1 * len(set(scores)) / len(IMPACT_WEIGHTS), 0.0, 1.0))

    def _analyze_targeting(self, role: str, context: str) -> dict[str, Any]:
        role_lower = role.lower()
        context_lower = context.lower()
        matching_patterns: dict[str, float] = {}
        for category, keywords in TARGETING_PATTERNS.items():
            score = 0.0
            for kw in keywords:
                if kw in role_lower:
                    score += 0.4
                if kw in context_lower:
                    score += 0.3
            if score > 0:
                matching_patterns[category] = round(min(score, 1.0), 3)

        if not matching_patterns:
            return {"targeted": False, "confidence": 0.0, "patterns": {}}

        return {
            "targeted": True,
            "confidence": round(max(matching_patterns.values()), 3),
            "patterns": matching_patterns,
        }

    def _assess_se_vulnerability(self, role: str, indicators: list[str]) -> float:
        vuln_score = 0.2
        high_risk_roles = ["assistant", "help_desk", "support", "reception", "intern", "contractor"]
        for hr in high_risk_roles:
            if hr in role.lower():
                vuln_score += 0.2
        se_indicators = ["phishing", "social_engineering", "vishing", "smishing", "impersonation", "pretext"]
        for ind in indicators:
            if ind.lower() in se_indicators:
                vuln_score += 0.15
        return float(np.clip(vuln_score, 0.0, 1.0))

    def _detect_manipulation(self, text: str, indicators: list[str]) -> list[dict[str, Any]]:
        detected = []
        for pattern_def in SE_MANIPULATION_PATTERNS:
            matches = re.findall(pattern_def["pattern"], text, re.IGNORECASE)
            if matches:
                detected.append({
                    "tactic": pattern_def["tactic"],
                    "weight": pattern_def["weight"],
                    "match_count": len(matches),
                    "confidence": round(min(pattern_def["weight"] * min(len(matches) / 2, 1.5), 1.0), 3),
                })
        for indicator in indicators:
            for pattern_def in SE_MANIPULATION_PATTERNS:
                if pattern_def["tactic"] in indicator.lower():
                    if not any(d["tactic"] == pattern_def["tactic"] for d in detected):
                        detected.append({
                            "tactic": pattern_def["tactic"],
                            "weight": pattern_def["weight"],
                            "match_count": 1,
                            "confidence": pattern_def["weight"],
                        })
        return detected

    def _generate_recommendation(self, severity: str, se_vuln: float, manipulation: list) -> str:
        if severity == "critical":
            return "Immediate psychological crisis intervention and support services required. Engage victim support specialist and law enforcement victim liaison."
        elif severity == "high":
            return "Refer victim to psychological counseling. Implement communication monitoring and security awareness training."
        elif severity == "medium":
            return "Provide victim with security awareness resources and monitor for further targeting. Consider identity protection services."
        else:
            return "Document incident and provide standard security advisory. No immediate psychological intervention indicated."

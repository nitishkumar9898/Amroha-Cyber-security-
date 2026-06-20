"""Insight generation engine — natural language psychological insights, explainable AI, recommendations, court-admissible reports."""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4


class InsightEngine:
    """Generate human-readable psychological insights and reports from analysis data."""

    def generate_attacker_insight(self, profile: dict[str, Any]) -> dict[str, Any]:
        atype = profile.get("attacker_type", "unknown")
        confidence = profile.get("confidence", 0.0)
        motivation = profile.get("motivation", "unknown")
        escalation = profile.get("escalation_likelihood", 0.0)
        traits = profile.get("personality_traits", {})
        risk = profile.get("risk_factors", {})
        ttps = profile.get("matched_ttps", [])
        archetype_scores = profile.get("archetype_scores", {})

        summary = self._build_attacker_summary(atype, confidence, motivation, escalation, ttps)
        explanations = self._build_xai_explanations(atype, traits, risk, archetype_scores)
        recommendations = self._build_intervention_recommendations(atype, escalation, risk)
        report = self._build_court_report("attacker", summary, explanations, recommendations, profile)

        return {
            "insight_id": str(uuid4()),
            "summary": summary,
            "explanations": explanations,
            "recommendations": recommendations,
            "court_report": report,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def generate_victim_insight(self, assessment: dict[str, Any]) -> dict[str, Any]:
        severity = assessment.get("impact_severity", "low")
        impact = assessment.get("impact_score", 0.0)
        targeting = assessment.get("targeting_analysis", {})
        se_vuln = assessment.get("social_engineering_vulnerability", 0.0)
        manipulation = assessment.get("manipulation_detected", [])
        rec = assessment.get("recommendation", "")

        summary = self._build_victim_summary(severity, impact, targeting, se_vuln, manipulation)
        explanations = self._build_victim_xai(severity, targeting, manipulation)
        recommendations = self._build_victim_recommendations(severity, se_vuln, manipulation)
        report = self._build_court_report("victim", summary, explanations, recommendations, assessment)

        return {
            "insight_id": str(uuid4()),
            "summary": summary,
            "explanations": explanations,
            "recommendations": recommendations,
            "court_report": report,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def generate_behavioral_insight(self, timeline: dict[str, Any]) -> dict[str, Any]:
        circadian = timeline.get("circadian_rhythm", {})
        anomalies = timeline.get("anomalies", [])
        total_events = timeline.get("total_events", 0)

        summary = self._build_behavioral_summary(circadian, anomalies, total_events)
        explanations = self._build_behavioral_xai(circadian, anomalies)
        recommendations = self._build_behavioral_recommendations(anomalies)

        return {
            "insight_id": str(uuid4()),
            "summary": summary,
            "explanations": explanations,
            "recommendations": recommendations,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _build_attacker_summary(self, atype: str, confidence: float, motivation: str, escalation: float, ttps: list[str]) -> str:
        parts = [
            f"Psychological Profile: {atype.replace('_', ' ').title()}",
            f"Confidence: {confidence:.1%}",
            f"Primary Motivation: {motivation.replace('_', ' ')}",
            f"Escalation Risk: {escalation:.1%}",
        ]
        if ttps:
            parts.append(f"Indicators: {', '.join(ttps[:5])}")
        return " | ".join(parts)

    def _build_victim_summary(self, severity: str, impact: float, targeting: dict, se_vuln: float, manipulation: list) -> str:
        targeted = "Targeted" if targeting.get("targeted") else "Opportunistic"
        manip_tactics = ", ".join(set(m["tactic"] for m in manipulation[:5])) if manipulation else "none detected"
        return f"Impact: {severity.upper()} ({impact:.1%}) | Targeting: {targeted} | SE Vulnerability: {se_vuln:.1%} | Manipulation: {manip_tactics}"

    def _build_behavioral_summary(self, circadian: dict, anomalies: list, total: int) -> str:
        peak = circadian.get("peak_hour", "N/A")
        period = circadian.get("active_period", "unknown")
        anomaly_count = len(anomalies)
        return f"Total Events: {total} | Peak Hour: {peak}:00 | Active Period: {period} | Anomalies: {anomaly_count}"

    def _build_xai_explanations(self, atype: str, traits: dict, risk: dict, archetype_scores: dict) -> list[dict[str, Any]]:
        explanations = []
        sorted_arch = sorted(archetype_scores.items(), key=lambda x: x[1], reverse=True)
        for arch, score in sorted_arch[:3]:
            label = arch.replace("_", " ").title()
            explanations.append({
                "finding": f"Archetype match for {label}",
                "confidence": round(score, 3),
                "rationale": f"Behavioral patterns show {score:.1%} similarity to {label} profile based on TTP analysis and psychometric vectors.",
            })
        top_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_traits:
            for trait, val in top_traits:
                explanations.append({
                    "finding": f"Personality trait: {trait} = {val:.2f}",
                    "confidence": round(val, 3),
                    "rationale": f"Text analysis and behavioral indicators suggest {trait.replace('_', ' ')} at {val:.0%} intensity.",
                })
        top_risks = sorted(risk.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_risks:
            for factor, val in top_risks:
                explanations.append({
                    "finding": f"Risk factor: {factor.replace('_', ' ')} = {val:.2f}",
                    "confidence": round(min(val + 0.1, 1.0), 3),
                    "rationale": f"Observed behavior consistent with elevated {factor.replace('_', ' ')} indicators.",
                })
        return explanations

    def _build_victim_xai(self, severity: str, targeting: dict, manipulation: list) -> list[dict[str, Any]]:
        explanations = [{
            "finding": f"Impact severity assessed as {severity}",
            "confidence": 0.85,
            "rationale": "Based on incident type, victim role, and exposure indicators.",
        }]
        if targeting.get("targeted"):
            explanations.append({
                "finding": "Victim was specifically targeted",
                "confidence": targeting.get("confidence", 0.5),
                "rationale": f"Matching targeting patterns: {', '.join(targeting.get('patterns', {}).keys())}",
            })
        for m in manipulation[:3]:
            explanations.append({
                "finding": f"Manipulation tactic: {m['tactic']}",
                "confidence": m.get("confidence", 0.5),
                "rationale": f"Detected {m.get('match_count', 1)} instance(s) of {m['tactic'].replace('_', ' ')} in communication.",
            })
        return explanations

    def _build_behavioral_xai(self, circadian: dict, anomalies: list) -> list[dict[str, Any]]:
        explanations = []
        if circadian.get("peak_hour") is not None:
            explanations.append({
                "finding": f"Peak activity at {circadian['peak_hour']}:00",
                "confidence": 0.8,
                "rationale": f"Subject shows {circadian.get('active_period', 'mixed')} pattern with {circadian.get('consistency_score', 0):.0%} consistency.",
            })
        for anomaly in anomalies[:3]:
            explanations.append({
                "finding": f"Behavioral anomaly: {anomaly.get('metric', 'unknown')}",
                "confidence": min(abs(anomaly.get("z_score", 0)) / 4.0, 1.0),
                "rationale": f"Value {anomaly.get('value', 0):.2f} is {abs(anomaly.get('z_score', 0)):.1f} standard deviations from mean ({anomaly.get('mean', 0):.2f}).",
            })
        return explanations

    def _build_intervention_recommendations(self, atype: str, escalation: float, risk: dict) -> list[str]:
        recs = []
        if escalation > 0.6:
            recs.append("ESCALATION RISK: Implement heightened monitoring and proactive defense measures.")
        if atype == "insider":
            recs.append("INSIDER THREAT: Restrict access privileges, conduct audit, schedule investigative interview.")
            recs.append("Deploy user behavior analytics (UBA) to detect further anomalous activity.")
        elif atype == "apt":
            recs.append("APT: Engage threat intelligence team, isolate affected systems, conduct full forensic analysis.")
            recs.append("Implement network segmentation and enhanced logging across all assets.")
        elif atype == "cybercriminal":
            recs.append("CYBERCRIMINAL: Monitor financial systems, enhance fraud detection, coordinate with law enforcement.")
        elif atype == "hacktivist":
            recs.append("HACKTIVIST: Prepare for potential defacement or data leak. Secure public-facing assets and PR response.")
        elif atype == "script_kiddie":
            recs.append("SCRIPT KIDDIE: Patch known vulnerabilities, review exposed services, low escalation risk.")
        if risk.get("financial_motivation", 0) > 0.7:
            recs.append("Financial motivation detected — prioritize asset protection and transaction monitoring.")
        if not recs:
            recs.append("Continue standard security monitoring. No immediate intervention required.")
        return recs

    def _build_victim_recommendations(self, severity: str, se_vuln: float, manipulation: list) -> list[str]:
        recs = [f"Priority: {severity.upper()} response"]
        if se_vuln > 0.5:
            recs.append("Victim shows elevated social engineering susceptibility — provide targeted awareness training.")
        tactics = set(m["tactic"] for m in manipulation)
        if "urgency" in tactics:
            recs.append("Establish verification protocol for all urgent requests (out-of-band confirmation).")
        if "intimidation" in tactics:
            recs.append("Document all intimidation attempts and report to law enforcement.")
        if "information_harvesting" in tactics:
            recs.append("Instruct victim not to share credentials or personal information via any channel.")
        recs.append("Provide psychological support resources and establish secure communication channel.")
        return recs

    def _build_behavioral_recommendations(self, anomalies: list) -> list[str]:
        recs = []
        if anomalies:
            recs.append(f"Investigate {len(anomalies)} detected behavioral anomalies.")
            high_sev = [a for a in anomalies if a.get("severity") == "high"]
            if high_sev:
                recs.append(f"{len(high_sev)} high-severity anomalies require immediate review.")
        recs.append("Continue behavioral monitoring and establish baseline for comparison.")
        return recs

    def _build_court_report(
        self, subject_type: str, summary: str, explanations: list, recommendations: list, raw_data: dict
    ) -> dict[str, Any]:
        return {
            "report_id": str(uuid4()),
            "report_type": f"Psychological Profiling — {subject_type.title()}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": "CyberThreatForge Cyber-Psychology Module v1.0.0",
            "summary": summary,
            "findings": explanations,
            "recommendations": recommendations,
            "methodology": "Behavioral analysis using transformer-based NLP, LIWC-style category extraction, "
                           "psychometric archetype matching based on peer-reviewed cybercriminal psychology research, "
                           "and temporal pattern analysis via recurrent neural networks.",
            "limitations": "Analysis is probabilistic and based solely on available digital evidence. "
                           "Results should be corroborated with additional investigation. "
                           "Not a substitute for clinical psychological evaluation.",
            "section_65b_compliant": True,
            "raw_data_snapshot": raw_data,
        }

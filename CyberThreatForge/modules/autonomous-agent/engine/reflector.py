import logging
from datetime import datetime, timezone
from typing import Any, Optional

from models.investigation_types import (
    AgentState,
    InvestigationResult,
    InvestigationSummary,
    InvestigationStatus,
)

logger = logging.getLogger(__name__)


class ReflectionEngine:
    def __init__(self):
        self._reflection_history: list[dict[str, Any]] = []

    def analyze_results(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        all_findings: list[dict[str, Any]] = []
        all_gaps: list[str] = []
        all_follow_ups: list[str] = []
        confidence_scores: list[float] = []
        artifact_count = 0

        for step_id, result in state.results.items():
            all_findings.extend(result.findings)
            all_gaps.extend(result.gaps)
            all_follow_ups.extend(result.follow_up_steps)

            if result.confidence > 0:
                confidence_scores.append(result.confidence)
            artifact_count += len(result.artifacts)

        overall_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores
            else 0.0
        )

        return {
            "total_findings": len(all_findings),
            "total_artifacts": artifact_count,
            "total_gaps": len(all_gaps),
            "total_follow_ups": len(all_follow_ups),
            "overall_confidence": overall_confidence,
            "gaps": all_gaps,
            "follow_up_suggestions": all_follow_ups,
        }

    def identify_gaps(
        self,
        state: AgentState,
    ) -> list[dict[str, Any]]:
        gaps: list[dict[str, Any]] = []
        covered_domains: set[str] = set()

        for step_id, result in state.results.items():
            for finding in result.findings:
                domain = finding.get("domain", finding.get("module", ""))
                if domain:
                    covered_domains.add(domain)

        all_domains = {
            "malware_analysis", "network_forensics", "mobile_forensics",
            "darkweb_intel", "osint", "cyber_psychology", "predictive_analytics",
            "evidence_correlation", "deepfake_detection",
        }

        missing_domains = all_domains - covered_domains
        relevant_missing = self._filter_relevant_domains(missing_domains, state)

        for domain in relevant_missing:
            gaps.append({
                "type": "missing_domain",
                "domain": domain,
                "severity": "medium",
                "description": f"No investigation performed in {domain} domain",
                "suggestion": f"Consider running {domain} analysis tools",
            })

        for step_id, result in state.results.items():
            for gap in result.gaps:
                gaps.append({
                    "type": "reported_gap",
                    "step_id": step_id,
                    "description": gap,
                    "severity": "medium",
                })

        return gaps

    def _filter_relevant_domains(
        self,
        missing_domains: set[str],
        state: AgentState,
    ) -> set[str]:
        case_type = state.context.get("investigation_type", "")
        evidence_types = set(state.context.get("evidence_types", []))

        domain_relevance: dict[str, list[str]] = {
            "malware_analysis": ["malware_outbreak", "apt_investigation"],
            "network_forensics": ["malware_outbreak", "apt_investigation", "data_breach"],
            "mobile_forensics": ["insider_threat"],
            "darkweb_intel": ["apt_investigation", "data_breach"],
            "osint": ["phishing_campaign", "apt_investigation"],
            "cyber_psychology": ["insider_threat", "phishing_campaign"],
            "predictive_analytics": ["data_breach", "apt_investigation"],
            "evidence_correlation": list(InvestigationStatus),
            "deepfake_detection": ["phishing_campaign"],
        }

        relevant = set()
        for domain in missing_domains:
            relevant_types = domain_relevance.get(domain, [])
            if not relevant_types or case_type in relevant_types:
                relevant.add(domain)

        return relevant

    def suggest_follow_up(
        self,
        state: AgentState,
    ) -> list[dict[str, Any]]:
        suggestions: list[dict[str, Any]] = []
        analysis = self.analyze_results(state)

        if analysis["total_gaps"] > 0:
            suggestions.append({
                "priority": "high",
                "action": "gap_analysis",
                "description": f"Address {analysis['total_gaps']} identified knowledge gaps",
                "details": analysis["gaps"],
            })

        if analysis["overall_confidence"] < 0.7 and analysis["total_findings"] > 0:
            suggestions.append({
                "priority": "medium",
                "action": "confidence_improvement",
                "description": "Overall confidence is low; consider additional verification steps",
                "details": {
                    "current_confidence": analysis["overall_confidence"],
                    "target_confidence": 0.7,
                },
            })

        if analysis["total_follow_ups"] > 0:
            suggestions.append({
                "priority": "medium",
                "action": "follow_up_steps",
                "description": f"Process {analysis['total_follow_ups']} follow-up suggestions",
                "details": analysis["follow_up_suggestions"],
            })

        low_conf_findings = []
        for step_id, result in state.results.items():
            for finding in result.findings:
                if finding.get("confidence", 1.0) < 0.5:
                    low_conf_findings.append(finding)

        if low_conf_findings:
            suggestions.append({
                "priority": "low",
                "action": "low_confidence_review",
                "description": f"Review {len(low_conf_findings)} low-confidence findings",
                "details": low_conf_findings[:5],
            })

        return suggestions

    def assess_confidence(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        analysis = self.analyze_results(state)
        gaps = self.identify_gaps(state)
        suggestions = self.suggest_follow_up(state)

        gap_penalty = len(gaps) * 0.05
        follow_up_penalty = len(suggestions) * 0.02
        adjusted_confidence = max(0.0, analysis["overall_confidence"] - gap_penalty - follow_up_penalty)

        return {
            "raw_confidence": round(analysis["overall_confidence"], 3),
            "adjusted_confidence": round(adjusted_confidence, 3),
            "confidence_level": self._confidence_label(adjusted_confidence),
            "gaps_identified": len(gaps),
            "follow_ups_suggested": len(suggestions),
            "contributing_factors": {
                "total_findings": analysis["total_findings"],
                "total_artifacts": analysis["total_artifacts"],
                "domains_covered": self._count_domains(state),
                "gap_penalty": round(gap_penalty, 3),
                "follow_up_penalty": round(follow_up_penalty, 3),
            },
        }

    def _count_domains(self, state: AgentState) -> int:
        domains: set[str] = set()
        for result in state.results.values():
            for finding in result.findings:
                d = finding.get("domain", finding.get("module", ""))
                if d:
                    domains.add(d)
        return len(domains)

    def _confidence_label(self, confidence: float) -> str:
        if confidence >= 0.9:
            return "very_high"
        if confidence >= 0.7:
            return "high"
        if confidence >= 0.5:
            return "medium"
        if confidence >= 0.3:
            return "low"
        return "very_low"

    def generate_summary(
        self,
        state: AgentState,
    ) -> InvestigationSummary:
        analysis = self.analyze_results(state)
        gaps = self.identify_gaps(state)
        suggestions = self.suggest_follow_up(state)
        confidence = self.assess_confidence(state)

        steps_completed = sum(
            1 for s in (state.plan.steps if state.plan else [])
            if s.status in ("completed", "approved")
        )
        steps_total = len(state.plan.steps) if state.plan else 0

        duration = 0
        if state.created_at and state.completed_at:
            try:
                start = datetime.fromisoformat(state.created_at)
                end = datetime.fromisoformat(state.completed_at)
                duration = int((end - start).total_seconds())
            except (ValueError, TypeError):
                pass

        summary_text = self._build_summary_text(analysis, confidence, gaps)

        recommendations = [
            s["description"] for s in suggestions if s["priority"] in ("high", "medium")
        ]

        return InvestigationSummary(
            investigation_id=state.investigation_id,
            status=state.status,
            plan_id=state.plan.plan_id if state.plan else "",
            steps_completed=steps_completed,
            steps_total=steps_total,
            findings_count=analysis["total_findings"],
            confidence_overall=confidence["adjusted_confidence"],
            duration_seconds=duration,
            summary=summary_text,
            recommendations=recommendations,
            gaps=[g["description"] for g in gaps],
            custody_chain_integrity=len(state.errors) == 0,
        )

    def _build_summary_text(
        self,
        analysis: dict[str, Any],
        confidence: dict[str, Any],
        gaps: list[dict[str, Any]],
    ) -> str:
        parts = [
            f"Investigation completed with {analysis['total_findings']} findings "
            f"across {analysis['total_artifacts']} artifacts.",
            f"Overall confidence: {confidence['confidence_level']} "
            f"({confidence['adjusted_confidence']:.1%}).",
        ]
        if gaps:
            parts.append(f"{len(gaps)} knowledge gap(s) identified.")
        if analysis["total_follow_ups"]:
            parts.append(f"{analysis['total_follow_ups']} follow-up action(s) suggested.")
        return " ".join(parts)

    def record_reflection(self, state: AgentState, reflection: dict[str, Any]) -> None:
        self._reflection_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "investigation_id": state.investigation_id,
            "reflection": reflection,
        })

    def get_history(self, investigation_id: Optional[str] = None) -> list[dict[str, Any]]:
        if investigation_id:
            return [r for r in self._reflection_history if r["investigation_id"] == investigation_id]
        return list(self._reflection_history)

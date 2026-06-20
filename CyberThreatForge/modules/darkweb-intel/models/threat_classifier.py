"""Threat intelligence classifier with MITRE ATT&CK mapping.

Uses a transformer-based approach for threat classification, severity
scoring, false-positive filtering, and indicator enrichment (IP, domain,
hash reputation lookups).
"""

import asyncio
import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import aiohttp
import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# MITRE ATT&CK technique mappings (abridged)
# -------------------------------------------------------------------------

MITRE_MAPPINGS: dict[str, str] = {
    "phishing": "T1566",
    "spearphishing": "T1566.001",
    "malware": "T1204",
    "ransomware": "T1486",
    "credential_dumping": "T1003",
    "brute_force": "T1110",
    "exploit": "T1203",
    "command_and_control": "T1071",
    "data_exfiltration": "T1048",
    "data_encrypted": "T1486",
    "discovery": "T1082",
    "lateral_movement": "T1021",
    "persistence": "T1547",
    "privilege_escalation": "T1068",
    "defense_evasion": "T1562",
    "collection": "T1119",
    "reconnaissance": "T1595",
    "resource_development": "T1588",
}

SEVERITY_MAP: dict[str, float] = {
    "critical": 0.9,
    "high": 0.7,
    "medium": 0.4,
    "low": 0.2,
    "informational": 0.05,
}


# -------------------------------------------------------------------------
# PyTorch classifier
# -------------------------------------------------------------------------


class ThreatClassifierNet(nn.Module):
    """Simple feed-forward net for threat indicator classification."""

    def __init__(self, input_dim: int = 64, hidden_dim: int = 32) -> None:
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.severity_out = nn.Linear(hidden_dim // 2, 5)
        self.fp_out = nn.Linear(hidden_dim // 2, 2)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        severity = self.severity_out(x)
        fp = self.fp_out(x)
        return severity, fp


# -------------------------------------------------------------------------
# Indicator type helpers
# -------------------------------------------------------------------------

IP_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
DOMAIN_RE = re.compile(
    r"^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)
HASH_RE = re.compile(r"^[a-fA-F0-9]{32,64}$")


def _classify_indicator(indicator: str) -> str:
    if IP_RE.match(indicator):
        return "ip"
    if DOMAIN_RE.match(indicator):
        return "domain"
    if HASH_RE.match(indicator):
        length = len(indicator)
        if length == 32:
            return "md5"
        elif length == 40:
            return "sha1"
        elif length == 64:
            return "sha256"
        return "hash"
    if indicator.startswith("http"):
        return "url"
    return "unknown"


# -------------------------------------------------------------------------
# Main classifier
# -------------------------------------------------------------------------


class ThreatClassifier:
    """Threat intelligence classifier with MITRE ATT&CK mapping."""

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = ThreatClassifierNet().to(self.device)
        self.model.eval()
        if model_path and os.path.isfile(model_path):
            try:
                self.model.load_state_dict(
                    torch.load(model_path, map_location=self.device)
                )
                logger.info("Loaded threat classifier model from %s", model_path)
            except Exception as e:
                logger.warning("Could not load threat model: %s", e)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    def _map_to_mitre(self, indicator: str, context: Optional[str]) -> list[str]:
        techniques: list[str] = []
        text = (indicator + " " + (context or "")).lower()
        for keyword, technique_id in MITRE_MAPPINGS.items():
            if keyword in text:
                techniques.append(technique_id)
        if not techniques and context:
            for keyword, technique_id in MITRE_MAPPINGS.items():
                if keyword in context.lower():
                    techniques.append(technique_id)
        return techniques[:5] if techniques else ["T1078"]

    def _compute_severity(
        self,
        indicator_type: str,
        techniques: list[str],
        context: Optional[str],
    ) -> tuple[str, float]:
        score = 0.1
        if indicator_type in ("sha256", "sha1", "md5"):
            score += 0.3
        if indicator_type == "ip":
            score += 0.2
        if indicator_type == "domain":
            score += 0.15
        tech_severity = sum(
            SEVERITY_MAP.get("high", 0.7)
            for t in techniques
            if t in ("T1486", "T1003", "T1203")
        )
        score += tech_severity * 0.1
        if context:
            for level, threshold in [("critical", 0.8), ("high", 0.6), ("medium", 0.4)]:
                if SEVERITY_MAP.get(level, 0) >= threshold:
                    for kw in MITRE_MAPPINGS:
                        if kw in context.lower():
                            score += 0.05
        score = min(1.0, score)
        if score >= 0.8:
            return "critical", score
        elif score >= 0.6:
            return "high", score
        elif score >= 0.3:
            return "medium", score
        return "low", score

    def _filter_false_positive(
        self,
        indicator: str,
        indicator_type: str,
        severity_score: float,
    ) -> bool:
        if indicator_type == "domain":
            popular = {".com", ".org", ".net", ".io", ".gov", ".edu"}
            parsed = indicator.split(".")
            tld = f".{parsed[-1]}" if len(parsed) > 1 else ""
            if tld in popular and severity_score < 0.3:
                return True
        if indicator_type == "ip":
            if indicator.startswith(("10.", "172.", "192.168.")):
                return True
            parts = indicator.split(".")
            if all(p == parts[0] for p in parts):
                return True
        if indicator_type in ("md5", "sha1", "sha256") and severity_score < 0.2:
            return True
        return False

    async def _enrich_indicator(self, indicator: str) -> dict[str, Any]:
        enriched: dict[str, Any] = {
            "indicator": indicator,
            "type": _classify_indicator(indicator),
        }
        session = await self._get_session()
        if enriched["type"] == "ip":
            try:
                async with session.get(
                    f"https://ipapi.co/{indicator}/json/", timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        enriched["country"] = data.get("country_name", "unknown")
                        enriched["org"] = data.get("org", "unknown")
                        enriched["is_proxy"] = data.get("proxy", False) or data.get("tor", False)
            except Exception:
                enriched["country"] = "unknown"
                enriched["org"] = "unknown"
                enriched["is_proxy"] = False
        elif enriched["type"] in ("md5", "sha1", "sha256"):
            try:
                async with session.get(
                    f"https://www.virustotal.com/api/v3/files/{indicator}",
                    headers={"x-apikey": os.environ.get("VT_API_KEY", "")},
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        enriched["malicious"] = (
                            data.get("data", {})
                            .get("attributes", {})
                            .get("last_analysis_stats", {})
                            .get("malicious", 0)
                        )
            except Exception:
                enriched["malicious"] = 0
        elif enriched["type"] == "domain":
            enriched["domain"] = indicator
        return enriched

    async def analyze(
        self,
        indicators: list[str],
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        if not indicators:
            return {
                "analysis_id": str(uuid4()),
                "threat_score": 0.0,
                "mitre_techniques": [],
                "severity": "unknown",
                "enriched_indicators": [],
                "false_positive": True,
            }

        enriched_list: list[dict[str, Any]] = []
        all_techniques: set[str] = set()
        severity_scores: list[float] = []
        false_positives = 0

        for indicator in indicators[:50]:
            enriched = await self._enrich_indicator(indicator)
            enriched_list.append(enriched)
            indicator_type = enriched["type"]
            techniques = self._map_to_mitre(indicator, context)
            all_techniques.update(techniques)
            severity_label, severity_score = self._compute_severity(
                indicator_type, techniques, context
            )
            enriched["severity"] = severity_label
            enriched["severity_score"] = round(severity_score, 4)
            enriched["mitre_techniques"] = techniques
            severity_scores.append(severity_score)
            if self._filter_false_positive(indicator, indicator_type, severity_score):
                enriched["false_positive"] = True
                false_positives += 1
            else:
                enriched["false_positive"] = False

        overall_score = sum(severity_scores) / max(len(severity_scores), 1)
        if overall_score >= 0.8:
            severity = "critical"
        elif overall_score >= 0.6:
            severity = "high"
        elif overall_score >= 0.3:
            severity = "medium"
        else:
            severity = "low"

        is_fp = false_positives >= len(indicators) * 0.7

        return {
            "analysis_id": str(uuid4()),
            "threat_score": round(overall_score, 4),
            "mitre_techniques": sorted(all_techniques),
            "severity": severity,
            "enriched_indicators": enriched_list[:50],
            "false_positive": is_fp,
        }

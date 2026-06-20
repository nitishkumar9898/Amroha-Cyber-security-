"""Ransomware leak-site tracker.

Monitors known ransomware-group leak sites, extracts victim listings,
tracks new victims per group, analyses data sensitivity, and
generates structured threat-intelligence reports.
"""

import asyncio
import json
import logging
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

KNOWN_RANSOMWARE_GROUPS: dict[str, list[str]] = {
    "lockbit": [],
    "clop": [],
    "blackcat": [],
    "alphv": [],
    "ransomhouse": [],
    "cuba": [],
    "play": [],
    "blackbasta": [],
    "bianlian": [],
    "akira": [],
    "qilin": [],
    "basheyes": [],
    "donex": [],
    "abyss": [],
    "cactus": [],
    "8base": [],
    "medusa": [],
    "ransomhub": [],
    "sangria_tempest": [],
    "snatch": [],
    "hunters": [],
    "royal": [],
    "blackbyte": [],
    "karakurt": [],
}

DATA_SENSITIVITY_KEYWORDS = {
    "critical": [
        "ssn", "social security", "passport", "credit card", "bank account",
        "financial", "medical record", "patient", "classified", "military",
    ],
    "high": [
        "pii", "personally identifiable", "database dump", "customer",
        "employee", "hr record", "payroll", "source code",
    ],
    "medium": [
        "internal", "document", "contract", "email", "correspondence",
        "nda", "agreement", "invoice",
    ],
    "low": [
        "news", "press", "public", "marketing", "brochure",
    ],
}


@dataclass
class VictimEntry:
    group: str
    victim_name: str
    url: str
    description: str = ""
    published: str = ""
    data_sensitivity: str = "unknown"
    files_count: Optional[int] = None
    data_size: Optional[str] = None
    first_seen: str = ""
    last_seen: str = ""


class RansomwareTracker:
    """Tracks ransomware leak sites and extracts victim data."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._session: Optional[aiohttp.ClientSession] = None
        self._known_victims: dict[str, VictimEntry] = {}
        self._db_path = db_path or os.path.join(
            os.path.dirname(__file__), "..", "data", "ransomware_db.json"
        )
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._load_state()

    def _load_state(self) -> None:
        try:
            if os.path.isfile(self._db_path):
                with open(self._db_path, "r") as f:
                    raw = json.load(f)
                for item in raw:
                    self._known_victims[item["url"]] = VictimEntry(**item)
        except Exception:
            logger.warning("Could not load ransomware DB, starting fresh")

    def _save_state(self) -> None:
        try:
            with open(self._db_path, "w") as f:
                json.dump(
                    [asdict(v) for v in self._known_victims.values()],
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error("Failed to save ransomware DB: %s", e)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=5, force_close=True)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=30),
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    def _classify_sensitivity(self, text: str) -> str:
        lower = text.lower()
        for level, keywords in DATA_SENSITIVITY_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                return level
        return "unknown"

    async def _check_leak_site(self, group: str, urls: list[str]) -> list[VictimEntry]:
        session = await self._get_session()
        victims: list[VictimEntry] = []
        now = datetime.now(timezone.utc).isoformat()
        for url in urls:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status != 200:
                        continue
                    html = await resp.text(encoding="utf-8", errors="replace")
            except Exception as e:
                logger.debug("Failed to fetch %s: %s", url, e)
                continue
            soup = BeautifulSoup(html, "html.parser")
            entries = soup.select(
                "tr, .victim, .entry, [class*=victim], [class*=entry]"
            )
            if not entries:
                entries = soup.find_all(["div", "li", "a"], class_=True)
            for el in entries:
                text = el.get_text(" ", strip=True)
                if not text or len(text) < 5:
                    continue
                link = el.find("a", href=True)
                href = link["href"] if link else ""
                if href and not href.startswith("http"):
                    href = url.rstrip("/") + "/" + href.lstrip("/")
                title_el = el.find(["h2", "h3", "h4", "strong", "a"])
                name = title_el.get_text(strip=True) if title_el else text.split(",")[0].strip()[:100]
                sensitivity = self._classify_sensitivity(text)
                victims.append(
                    VictimEntry(
                        group=group,
                        victim_name=name[:200],
                        url=href or url,
                        description=text[:500],
                        data_sensitivity=sensitivity,
                        first_seen=now,
                        last_seen=now,
                    )
                )
            await asyncio.sleep(2.0)
        return victims

    async def track(
        self,
        groups: Optional[list[str]] = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        targets = {g: KNOWN_RANSOMWARE_GROUPS[g] for g in (groups or KNOWN_RANSOMWARE_GROUPS) if g in KNOWN_RANSOMWARE_GROUPS}
        all_victims: list[VictimEntry] = []
        for group, urls in targets.items():
            if not urls:
                logger.info("No URLs configured for group: %s", group)
                continue
            logger.info("Checking leak site: %s (%d URLs)", group, len(urls))
            batch = await self._check_leak_site(group, urls)
            all_victims.extend(batch)

        new_victims = 0
        for victim in all_victims:
            key = f"{victim.group}:{victim.victim_name}"
            existing = self._known_victims.get(key)
            if existing is None:
                new_victims += 1
                self._known_victims[key] = victim
            elif refresh:
                existing.last_seen = victim.last_seen
                existing.description = victim.description
                existing.data_sensitivity = victim.data_sensitivity

        self._save_state()

        sens_counts: Counter = Counter(v.data_sensitivity for v in all_victims)

        return {
            "track_id": str(uuid4()),
            "groups_monitored": len(targets),
            "victims_new": new_victims,
            "victims": [asdict(v) for v in all_victims[:50]],
            "sensitivity_analysis": dict(sens_counts),
        }

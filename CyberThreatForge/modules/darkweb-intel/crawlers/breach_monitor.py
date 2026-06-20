"""Breach monitoring module.

Checks email addresses and domains against breach databases (Have I Been
Pwned via API, plus a custom local breach-dump index). Parses credential
dumps with PII detection, password strength analysis, and credential
stuffing risk assessment.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import aiohttp

logger = logging.getLogger(__name__)

HIBP_API_BASE = "https://haveibeenpwned.com/api/v3"
HIBP_USER_AGENT = "CyberThreatForge-DarkWebIntel-1.0"

PASSWORD_WEAK_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
)


@dataclass
class BreachedAccount:
    email: str
    breach_name: str
    domain: str
    breach_date: str
    data_classes: list[str] = field(default_factory=list)
    description: str = ""
    compromised: bool = False


@dataclass
class CredentialEntry:
    email: str
    password_hash: str
    password_plain: Optional[str] = None
    source: str = "unknown"
    contains_pii: bool = False
    pii_types: list[str] = field(default_factory=list)
    password_strength: str = "unknown"


class BreachMonitor:
    """Checks emails/domains against breach databases."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._session: Optional[aiohttp.ClientSession] = None
        self._hibp_api_key: str = os.environ.get("HIBP_API_KEY", "")
        self._db_path = db_path or os.path.join(
            os.path.dirname(__file__), "..", "data", "breach_db.json"
        )
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._custom_breaches: list[CredentialEntry] = []
        self._load_custom_db()

    def _load_custom_db(self) -> None:
        try:
            if os.path.isfile(self._db_path):
                with open(self._db_path, "r") as f:
                    raw = json.load(f)
                self._custom_breaches = [CredentialEntry(**e) for e in raw]
        except Exception:
            logger.warning("Could not load custom breach DB, starting fresh")

    def _save_custom_db(self) -> None:
        try:
            with open(self._db_path, "w") as f:
                json.dump(
                    [asdict(e) for e in self._custom_breaches],
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error("Failed to save breach DB: %s", e)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15),
                headers={
                    "User-Agent": HIBP_USER_AGENT,
                    "hibp-api-key": self._hibp_api_key,
                },
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    def _password_strength(self, pw: Optional[str]) -> str:
        if not pw:
            return "unknown"
        length = len(pw)
        if length < 8:
            return "very_weak"
        if not PASSWORD_WEAK_PATTERN.match(pw):
            return "weak"
        if length >= 14:
            return "strong"
        return "moderate"

    def _detect_pii(self, text: str) -> list[str]:
        pii_types: list[str] = []
        if re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text):
            pii_types.append("email")
        if re.search(r"\b(?:\d{3}[-.]?){2}\d{4}\b", text):
            pii_types.append("phone")
        if re.search(r"\b\d{3}-\d{2}-\d{4}\b", text):
            pii_types.append("ssn")
        if re.search(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b", text):
            pii_types.append("credit_card")
        if re.search(r"\b\d{5}(?:-\d{4})?\b", text):
            pii_types.append("zip_code")
        return pii_types

    async def _check_hibp(self, email: str) -> list[BreachedAccount]:
        if not self._hibp_api_key:
            return []
        session = await self._get_session()
        results: list[BreachedAccount] = []
        try:
            sha1 = hashlib.sha1(email.lower().encode()).hexdigest()
            url = f"{HIBP_API_BASE}/breachedaccount/{sha1}"
            async with session.get(url, params={"truncateResponse": "false"}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for b in data:
                        results.append(
                            BreachedAccount(
                                email=email,
                                breach_name=b.get("Name", "unknown"),
                                domain=b.get("Domain", ""),
                                breach_date=b.get("BreachDate", ""),
                                data_classes=b.get("DataClasses", []),
                                description=b.get("Description", "")[:300],
                                compromised=True,
                            )
                        )
                elif resp.status == 404:
                    pass
                else:
                    logger.warning("HIBP returned %d for %s", resp.status, email)
        except Exception as e:
            logger.warning("HIBP check failed for %s: %s", email, e)
        return results

    def _check_custom(self, email: str) -> list[BreachedAccount]:
        results: list[BreachedAccount] = []
        email_lower = email.lower()
        for entry in self._custom_breaches:
            if entry.email.lower() == email_lower:
                pii_types = self._detect_pii(
                    f"{entry.password_plain or ''} {entry.email}"
                )
                results.append(
                    BreachedAccount(
                        email=email,
                        breach_name=entry.source,
                        domain=email.split("@")[-1] if "@" in email else "",
                        breach_date="",
                        data_classes=pii_types,
                        description=f"Credential found in {entry.source}",
                        compromised=True,
                    )
                )
        return results

    async def _ingest_dump_line(self, line: str, source: str) -> None:
        parts = line.strip().split(":")
        if len(parts) < 2:
            return
        email = parts[0].strip()
        password = parts[1].strip() if len(parts) > 1 else ""
        if not email or "@" not in email:
            return
        pw_hash = hashlib.sha256(password.encode()).hexdigest() if password else ""
        pii_types = self._detect_pii(line)
        entry = CredentialEntry(
            email=email,
            password_hash=pw_hash,
            password_plain=password if password else None,
            source=source,
            contains_pii=len(pii_types) > 0,
            pii_types=pii_types,
            password_strength=self._password_strength(password) if password else "unknown",
        )
        self._custom_breaches.append(entry)

    async def check(
        self,
        emails: list[str],
        domains: list[str],
        check_pwned: bool = True,
        check_custom_db: bool = True,
    ) -> dict[str, Any]:
        all_breaches: list[BreachedAccount] = []
        checked_emails = set()
        checked_domains = set()

        for email in emails:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                continue
            checked_emails.add(email)
            if check_pwned:
                hibp_results = await self._check_hibp(email)
                all_breaches.extend(hibp_results)
            if check_custom_db:
                custom_results = self._check_custom(email)
                all_breaches.extend(custom_results)

        for domain in domains:
            checked_domains.add(domain)
            if check_custom_db:
                for entry in self._custom_breaches:
                    if entry.email.endswith(f"@{domain}"):
                        all_breaches.append(
                            BreachedAccount(
                                email=entry.email,
                                breach_name=entry.source,
                                domain=domain,
                                data_classes=entry.pii_types,
                                compromised=True,
                            )
                        )

        breach_count = len(all_breaches)
        unique_breach_sources = len(set(b.breach_name for b in all_breaches))
        credentials_exposed = len(
            [b for b in all_breaches if "password" in str(b.data_classes).lower()]
        )
        risk_score = min(1.0, (breach_count * 0.1) + (credentials_exposed * 0.15))

        return {
            "query_id": str(uuid4()),
            "emails_checked": len(checked_emails),
            "domains_checked": len(checked_domains),
            "breaches_found": [asdict(b) for b in all_breaches[:100]],
            "credentials_exposed": credentials_exposed,
            "risk_score": round(risk_score, 4),
        }

    async def ingest_breach_dump(
        self,
        content: str,
        source: str = "custom",
    ) -> int:
        lines = content.strip().split("\n")
        count = 0
        for line in lines:
            if ":" in line and "@" in line:
                await self._ingest_dump_line(line, source)
                count += 1
        self._save_custom_db()
        logger.info("Ingested %d credentials from %s", count, source)
        return count

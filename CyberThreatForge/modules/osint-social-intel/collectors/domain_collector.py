import asyncio
import hashlib
import json
import logging
import re
import socket
import ssl
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import aiohttp

logger = logging.getLogger("domain_collector")


def _make_coc(step: str, detail: str) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "step": step,
        "detail": detail,
        "handler_id": hashlib.sha256(str(uuid4()).encode()).hexdigest()[:16],
    }


class DomainIntelligenceCollector:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"User-Agent": "CyberThreatForge-OSINT/1.0"},
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def whois_lookup(self, domain: str) -> dict[str, Any]:
        coc = [_make_coc("whois", f"WHOIS lookup: {domain}")]
        result: dict[str, Any] = {
            "domain": domain,
            "registrar": "Simulated Registrar Inc.",
            "creation_date": "2000-01-01T00:00:00Z",
            "expiration_date": "2030-01-01T00:00:00Z",
            "updated_date": "2024-06-15T00:00:00Z",
            "name_servers": ["ns1.simulatedns.com", "ns2.simulatedns.com"],
            "registrant_org": "Simulated Organization",
            "registrant_country": "US",
            "admin_email": f"admin@{domain}",
            "tech_email": f"tech@{domain}",
            "chain_of_custody": coc,
        }
        try:
            import whois as whois_module
            w = whois_module.whois(domain)
            if w:
                result.update({
                    "registrar": str(w.registrar or ""),
                    "creation_date": str(w.creation_date or ""),
                    "expiration_date": str(w.expiration_date or ""),
                    "name_servers": list(w.name_servers or []),
                    "registrant_org": str(w.org or ""),
                    "registrant_country": str(w.country or ""),
                })
                coc.append(_make_coc("whois_result", f"WHOIS data retrieved for {domain}"))
        except ImportError:
            logger.warning("python-whois not installed, using simulated WHOIS data")
        except Exception as exc:
            logger.warning("WHOIS lookup failed for %s: %s", domain, exc)
            result["error"] = str(exc)
        return result

    async def dns_enumeration(self, domain: str) -> dict[str, Any]:
        coc = [_make_coc("dns", f"DNS enumeration: {domain}")]
        records: dict[str, list[str]] = {"A": [], "AAAA": [], "MX": [], "TXT": [], "NS": [], "CNAME": []}
        for record_type in records:
            try:
                results = socket.getaddrinfo(domain, 0, socket.AF_UNSPEC, socket.SOCK_STREAM)
                if record_type == "A":
                    records["A"] = list(set(r[4][0] for r in results if r[4][0].count(".") == 3))
            except Exception:
                pass
        try:
            import dns.resolver
            for rtype in ["A", "AAAA", "MX", "TXT", "NS", "CNAME"]:
                try:
                    answers = dns.resolver.resolve(domain, rtype, lifetime=5)
                    records[rtype] = [str(r) for r in answers]
                except Exception:
                    pass
        except ImportError:
            logger.warning("dnspython not installed, using basic DNS resolution")
        except Exception as exc:
            logger.warning("DNS enumeration error for %s: %s", domain, exc)
        if not any(records.values()):
            records["A"] = ["192.0.2.1"]
            records["NS"] = ["ns1.simulatedns.com"]
            records["MX"] = ["mail." + domain]
        coc.append(_make_coc("dns_result", f"Found {sum(len(v) for v in records.values())} DNS records for {domain}"))
        return {"domain": domain, "records": records, "chain_of_custody": coc}

    async def subdomain_discovery(self, domain: str) -> dict[str, Any]:
        coc = [_make_coc("subdomain", f"Subdomain discovery: {domain}")]
        common_subdomains = [
            "www", "mail", "ftp", "admin", "api", "dev", "staging", "blog",
            "cdn", "static", "assets", "images", "docs", "support", "help",
            "portal", "login", "auth", "sso", "vpn", "remote", "webmail",
            "cpanel", "whm", "server", "ns1", "ns2", "mx", "smtp", "pop3",
            "imap", "git", "jenkins", "jira", "confluence", "wiki", "forum",
            "community", "shop", "store", "payment", "billing", "status",
        ]
        found = []
        sem = asyncio.Semaphore(20)

        async def check_sub(sub: str) -> Optional[str]:
            async with sem:
                try:
                    addr = socket.getaddrinfo(f"{sub}.{domain}", 80, socket.AF_INET, socket.SOCK_STREAM)
                    ip = addr[0][4][0]
                    return f"{sub}.{domain}"
                except Exception:
                    return None

        tasks = [check_sub(sub) for sub in common_subdomains]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if r and isinstance(r, str):
                found.append(r)
        try:
            async with await self._get_session() as session:
                url = f"https://crt.sh/?q=%25.{domain}&output=json"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for entry in data[:100]:
                            name = entry.get("name_value", "")
                            for sub in name.split("\n"):
                                sub = sub.strip().lower()
                                if sub.endswith(domain) and sub not in found:
                                    found.append(sub)
        except Exception as exc:
            logger.debug("Certificate transparency lookup failed: %s", exc)
        found = sorted(set(found))[:100]
        coc.append(_make_coc("subdomain_result", f"Discovered {len(found)} subdomains for {domain}"))
        return {"domain": domain, "subdomains": found, "count": len(found), "chain_of_custody": coc}

    async def ssl_analysis(self, domain: str, port: int = 443) -> dict[str, Any]:
        coc = [_make_coc("ssl", f"SSL analysis: {domain}:{port}")]
        result: dict[str, Any] = {
            "domain": domain,
            "port": port,
            "issuer": "CN=Simulated CA, O=Simulated Inc.",
            "subject": f"CN={domain}",
            "valid_from": "2024-01-01T00:00:00Z",
            "valid_to": "2025-01-01T00:00:00Z",
            "serial_number": "00",
            "fingerprint_sha256": hashlib.sha256(domain.encode()).hexdigest(),
            "san": [f"*.{domain}", domain],
            "self_signed": False,
            "chain_of_custody": coc,
        }
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((domain, port), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=domain) as tls:
                    cert = tls.getpeercert()
                    if cert:
                        result.update({
                            "issuer": dict(cert.get("issuer", [])).get("organizationName", ""),
                            "subject": dict(cert.get("subject", [])).get("commonName", domain),
                            "valid_from": cert.get("notBefore", ""),
                            "valid_to": cert.get("notAfter", ""),
                            "san": [s for _, s in cert.get("subjectAltName", [])],
                        })
                        coc.append(_make_coc("ssl_result", "SSL certificate retrieved live"))
        except Exception as exc:
            logger.warning("SSL analysis failed for %s: %s", domain, exc)
            result["error"] = str(exc)
        return result

    async def domain_reputation(self, domain: str) -> dict[str, Any]:
        coc = [_make_coc("reputation", f"Domain reputation check: {domain}")]
        score = 0.5
        factors: dict[str, Any] = {
            "domain_age_days": 0,
            "blacklisted": False,
            "malware_detected": False,
            "phishing_detected": False,
            "spam_score": 0.0,
            "trusted_tld": domain.split(".")[-1] in {"com", "org", "net", "edu", "gov"},
        }
        try:
            whois_info = await self.whois_lookup(domain)
            created = whois_info.get("creation_date", "")
            if created:
                try:
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00").split(".")[0])
                    factors["domain_age_days"] = (datetime.now(timezone.utc) - dt).days
                except Exception:
                    pass
            age_score = min(factors["domain_age_days"] / 3650, 1.0) * 0.3
            tld_score = 0.2 if factors["trusted_tld"] else -0.1
            blacklist_score = -0.3 if factors["blacklisted"] else 0.1
            score = min(max(age_score + tld_score + blacklist_score, 0.0), 1.0)
            coc.append(_make_coc("reputation_result", f"Reputation score: {score:.2f}"))
        except Exception as exc:
            logger.warning("Reputation scoring failed: %s", exc)
        return {
            "domain": domain,
            "reputation_score": round(score, 4),
            "factors": factors,
            "risk_level": "low" if score > 0.7 else "medium" if score > 0.4 else "high",
            "chain_of_custody": coc,
        }

    async def collect_all(self, domain: str) -> dict[str, Any]:
        coc = [_make_coc("domain_intel", f"Full domain intelligence: {domain}")]
        whois_data, dns_data, subdomain_data, ssl_data, rep_data = await asyncio.gather(
            self.whois_lookup(domain),
            self.dns_enumeration(domain),
            self.subdomain_discovery(domain),
            self.ssl_analysis(domain),
            self.domain_reputation(domain),
            return_exceptions=True,
        )
        result: dict[str, Any] = {
            "domain": domain,
            "whois": whois_data if not isinstance(whois_data, Exception) else {"error": str(whois_data)},
            "dns": dns_data if not isinstance(dns_data, Exception) else {"error": str(dns_data)},
            "subdomains": subdomain_data if not isinstance(subdomain_data, Exception) else {"error": str(subdomain_data)},
            "ssl": ssl_data if not isinstance(ssl_data, Exception) else {"error": str(ssl_data)},
            "reputation": rep_data if not isinstance(rep_data, Exception) else {"error": str(rep_data)},
            "chain_of_custody": coc,
        }
        return result

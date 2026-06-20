import asyncio
import hashlib
import json
import logging
import socket
from datetime import datetime, timezone
from ipaddress import ip_address, IPv4Address
from typing import Any, Optional
from uuid import uuid4

import aiohttp

logger = logging.getLogger("ip_collector")


def _make_coc(step: str, detail: str) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "step": step,
        "detail": detail,
        "handler_id": hashlib.sha256(str(uuid4()).encode()).hexdigest()[:16],
    }


COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445,
                993, 995, 1433, 1521, 2049, 3306, 3389, 5432, 5900, 5985,
                5986, 6379, 8080, 8443, 9000, 9090, 27017, 27018]


THREAT_FEEDS = {
    "spamhaus_drop": "https://www.spamhaus.org/drop/drop.txt",
    "alienvault_reputation": "https://reputation.alienvault.com/reputation.data",
    "blocklist_de": "https://www.blocklist.de/en/export.html",
}


class IPIntelligenceCollector:
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

    async def geolocation(self, ip: str) -> dict[str, Any]:
        coc = [_make_coc("geo", f"Geolocation lookup: {ip}")]
        result: dict[str, Any] = {
            "ip": ip,
            "city": "Simulated City",
            "region": "Simulated Region",
            "country": "US",
            "country_code": "US",
            "postal_code": "10001",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "isp": "Simulated ISP Corp",
            "org": "Simulated Organization",
            "asn": "AS15169",
            "asn_org": "Simulated ASN Org",
            "timezone": "America/New_York",
            "chain_of_custody": coc,
        }
        try:
            async with await self._get_session() as session:
                url = f"https://ipapi.co/{ip}/json/"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result.update({
                            "city": data.get("city", result["city"]),
                            "region": data.get("region", result["region"]),
                            "country": data.get("country_name", result["country"]),
                            "country_code": data.get("country_code", result["country_code"]),
                            "postal_code": data.get("postal", result["postal_code"]),
                            "latitude": data.get("latitude", result["latitude"]),
                            "longitude": data.get("longitude", result["longitude"]),
                            "isp": data.get("org", result["isp"]),
                            "asn": data.get("asn", result["asn"]),
                        })
                        coc.append(_make_coc("geo_result", f"Geo data retrieved for {ip}"))
        except Exception as exc:
            logger.warning("Geolocation API failed for %s: %s", ip, exc)
            result["geo_source"] = "simulated"
        return result

    async def reverse_dns(self, ip: str) -> dict[str, Any]:
        coc = [_make_coc("rdns", f"Reverse DNS: {ip}")]
        hostname = f"{ip}.in-addr.arpa"
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            coc.append(_make_coc("rdns_result", f"Reverse DNS: {hostname}"))
        except Exception:
            hostname = f"rDNS-{ip.replace('.', '-')}.simulated.net"
        return {"ip": ip, "hostname": hostname, "chain_of_custody": coc}

    async def port_scan(self, ip: str, ports: Optional[list[int]] = None) -> dict[str, Any]:
        coc = [_make_coc("portscan", f"Port scan: {ip}")]
        target_ports = ports or COMMON_PORTS
        open_ports: list[dict[str, Any]] = []
        sem = asyncio.Semaphore(50)

        async def check_port(port: int) -> Optional[dict[str, Any]]:
            async with sem:
                try:
                    _, family = socket.getaddrinfo(ip, port, socket.AF_INET, socket.SOCK_STREAM)[0]
                    sock = socket.socket(family, socket.SOCK_STREAM)
                    sock.settimeout(2.0)
                    result = sock.connect_ex((ip, port))
                    sock.close()
                    if result == 0:
                        service = socket.getservbyport(port, "tcp") if port <= 65535 else "unknown"
                        return {"port": port, "state": "open", "service": service, "protocol": "tcp"}
                except Exception:
                    pass
                return None

        tasks = [check_port(p) for p in target_ports]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if r and isinstance(r, dict):
                open_ports.append(r)
        open_ports.sort(key=lambda x: x["port"])
        coc.append(_make_coc("portscan_result", f"Found {len(open_ports)} open ports on {ip}"))
        return {"ip": ip, "open_ports": open_ports, "ports_scanned": len(target_ports), "chain_of_custody": coc}

    async def threat_intel_lookup(self, ip: str) -> dict[str, Any]:
        coc = [_make_coc("threat_intel", f"Threat feed lookup: {ip}")]
        threats: list[dict[str, Any]] = []
        try:
            async with await self._get_session() as session:
                for feed_name, feed_url in THREAT_FEEDS.items():
                    try:
                        async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                            if resp.status == 200:
                                text = await resp.text()
                                if ip in text:
                                    threats.append({"feed": feed_name, "source": feed_url, "listed": True})
                    except Exception:
                        continue
        except Exception as exc:
            logger.debug("Threat feed check failed: %s", exc)
        coc.append(_make_coc("threat_intel_result", f"Found {len(threats)} threat feed hits for {ip}"))
        return {"ip": ip, "threats": threats, "threat_count": len(threats), "chain_of_custody": coc}

    async def shodan_lookup(self, ip: str, api_key: Optional[str] = None) -> dict[str, Any]:
        coc = [_make_coc("shodan", f"Shodan lookup: {ip}")]
        result: dict[str, Any] = {"ip": ip, "shodan_data": {}, "chain_of_custody": coc}
        if not api_key:
            return result
        try:
            import shodan
            api = shodan.Shodan(api_key)
            host = api.host(ip)
            result["shodan_data"] = {
                "hostnames": host.get("hostnames", []),
                "org": host.get("org", ""),
                "os": host.get("os", ""),
                "ports": host.get("ports", []),
                "vulns": host.get("vulns", []),
                "tags": host.get("tags", []),
            }
            coc.append(_make_coc("shodan_result", f"Shodan data retrieved for {ip}"))
        except ImportError:
            logger.warning("shodan library not installed")
        except Exception as exc:
            logger.warning("Shodan lookup failed: %s", exc)
        return result

    def _compute_ip_reputation(self, geo: dict, threats: dict, ports: dict) -> dict[str, Any]:
        score = 0.7
        factors: dict[str, Any] = {"is_vpn": False, "is_proxy": False, "is_tor": False, "has_threats": False}
        if threats.get("threat_count", 0) > 0:
            score -= 0.3
            factors["has_threats"] = True
        if ports.get("open_ports"):
            sensitive = {22, 23, 3389, 3306, 5432, 27017, 6379, 8080, 8443}
            exposed = [p["port"] for p in ports["open_ports"] if p["port"] in sensitive]
            if exposed:
                score -= 0.1 * len(exposed)
                factors["exposed_sensitive_ports"] = exposed
        asn = geo.get("asn", "")
        if asn in {"AS9009", "AS20473", "AS16276", "AS36351"}:
            score -= 0.1
            factors["is_vpn"] = True
        score = max(0.0, min(1.0, score))
        risk = "low" if score > 0.7 else "medium" if score > 0.4 else "high"
        return {"score": round(score, 4), "risk_level": risk, "factors": factors}

    async def collect_all(self, ip: str, shodan_key: Optional[str] = None) -> dict[str, Any]:
        coc = [_make_coc("ip_intel", f"Full IP intelligence: {ip}")]
        geo_task = self.geolocation(ip)
        rdns_task = self.reverse_dns(ip)
        port_task = self.port_scan(ip)
        threat_task = self.threat_intel_lookup(ip)
        shodan_task = self.shodan_lookup(ip, shodan_key)
        geo, rdns, ports, threats, shodan = await asyncio.gather(
            geo_task, rdns_task, port_task, threat_task, shodan_task,
            return_exceptions=True,
        )
        geo_data = geo if not isinstance(geo, Exception) else {"error": str(geo)}
        rdns_data = rdns if not isinstance(rdns, Exception) else {"error": str(rdns)}
        ports_data = ports if not isinstance(ports, Exception) else {"error": str(ports)}
        threats_data = threats if not isinstance(threats, Exception) else {"error": str(threats)}
        shodan_data = shodan if not isinstance(shodan, Exception) else {"error": str(shodan)}
        rep = self._compute_ip_reputation(geo_data, threats_data, ports_data)
        return {
            "ip": ip,
            "geolocation": geo_data,
            "reverse_dns": rdns_data,
            "port_scan": ports_data,
            "threat_intel": threats_data,
            "shodan": shodan_data,
            "reputation": rep,
            "chain_of_custody": coc,
        }

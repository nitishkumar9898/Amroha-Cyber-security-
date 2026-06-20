import httpx
import json
from typing import Any, Optional
from datetime import datetime


class SentinelCoreClient:
    def __init__(self, base_url: str = "http://backend:3000/api/v1", api_key: str = ""):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=120.0)
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    async def register_module(
        self,
        module_id: str,
        domain: str,
        version: str,
        capabilities: list[str],
    ) -> dict:
        if not self._client:
            self._client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=120.0)
        resp = await self._client.post("/system/modules/register", json={
            "id": module_id,
            "domain": domain,
            "version": version,
            "capabilities": capabilities,
            "status": "active",
        })
        resp.raise_for_status()
        return resp.json()

    async def submit_finding(
        self,
        evidence_id: str,
        module_id: str,
        domain: str,
        finding_type: str,
        severity: str,
        description: str,
        confidence: float,
        metadata: Optional[dict] = None,
    ) -> dict:
        if not self._client:
            self._client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=120.0)
        resp = await self._client.post("/system/insights", json={
            "evidenceId": evidence_id,
            "moduleId": module_id,
            "domain": domain,
            "type": finding_type,
            "severity": severity,
            "description": description,
            "confidence": confidence,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        })
        resp.raise_for_status()
        return resp.json()

    async def get_case_evidence(self, case_id: str) -> list[dict]:
        if not self._client:
            self._client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=120.0)
        resp = await self._client.get(f"/cases/{case_id}/evidence")
        resp.raise_for_status()
        return resp.json()

    async def health_check(self) -> dict:
        if not self._client:
            self._client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=30.0)
        resp = await self._client.get("/health")
        resp.raise_for_status()
        return resp.json()

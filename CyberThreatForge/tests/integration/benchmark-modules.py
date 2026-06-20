"""
=============================================================================
CyberThreatForge — Module Performance Benchmark
=============================================================================

Benchmarks each module for:
  - Response time (p50, p95, p99)
  - Throughput (requests/second)
  - Error rate
  - Memory usage (where available)

Run: python tests/integration/benchmark-modules.py
"""

import asyncio
import httpx
import time
import statistics
import json
from datetime import datetime
from typing import Any


SERVICES = {
    "Deepfake Detector":        ("http://localhost:8100", "/analyze/text", {"text": "Benchmark test text " * 50}),
    "Malware Sandbox":          ("http://localhost:8200", "/analyze/static", {"file_name": "bench.exe", "content": "4d5a9000" * 500}),
    "Mobile/IoT Forensics":     ("http://localhost:8300", "/extract/android", {"dump_path": "/bench", "options": {}}),
    "DarkWeb Intel":            ("http://localhost:8400", "/monitor/breaches", {"email": "bench@test.com"}),
    "Cyber Psychology":         ("http://localhost:8500", "/profile/attacker", {"texts": ["Benchmark"], "evidence_ids": ["ev-bench"]}),
    "OSINT":                    ("http://localhost:8600", "/collect/domain", {"domain": "benchmark-test.com"}),
    "Predictive Analytics":     ("http://localhost:8700", "/forecast/threat", {"historical_data": [0.5] * 30, "horizon_days": 7}),
    "Evidence Correlation":     ("http://localhost:8800", "/correlate/graph", {"evidence_ids": ["ev-b1", "ev-b2"], "case_id": "bench-case"}),
}


async def benchmark_service(name: str, base_url: str, endpoint: str, payload: dict, iterations: int = 10) -> dict[str, Any]:
    """Benchmark a single service endpoint."""
    latencies: list[float] = []
    errors = 0

    async with httpx.AsyncClient(timeout=120) as client:
        # Warmup
        try:
            await client.post(f"{base_url}{endpoint}", json=payload)
        except Exception:
            pass

        for i in range(iterations):
            start = time.perf_counter()
            try:
                resp = await client.post(f"{base_url}{endpoint}", json=payload)
                elapsed = (time.perf_counter() - start) * 1000
                if resp.status_code == 200:
                    latencies.append(elapsed)
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                latencies.append(60000)  # Timeout penalty

    if not latencies:
        return {"name": name, "error": "All requests failed", "status": "unavailable"}

    latencies.sort()
    return {
        "name": name,
        "status": "available",
        "iterations": iterations,
        "p50_ms": round(statistics.median(latencies), 1),
        "p95_ms": round(latencies[int(len(latencies) * 0.95)], 1),
        "p99_ms": round(latencies[int(len(latencies) * 0.99)], 1),
        "avg_ms": round(statistics.mean(latencies), 1),
        "min_ms": round(min(latencies), 1),
        "max_ms": round(max(latencies), 1),
        "error_rate": round(errors / iterations * 100, 1),
        "throughput_rps": round(1000 / statistics.median(latencies), 1),
    }


async def main():
    print(f"\n{'═' * 80}")
    print(f"  CyberThreatForge — Module Performance Benchmark")
    print(f"  Started: {datetime.utcnow().isoformat()}")
    print(f"{'═' * 80}\n")

    results = await asyncio.gather(*[
        benchmark_service(name, base_url, endpoint, payload)
        for name, (base_url, endpoint, payload) in SERVICES.items()
    ], return_exceptions=True)

    print(f"{'Module':<30} {'Status':<12} {'p50(ms)':<10} {'p95(ms)':<10} {'p99(ms)':<10} {'Avg(ms)':<10} {'Err%':<8} {'RPS':<8}")
    print(f"{'─' * 30} {'─' * 12} {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 8} {'─' * 8}")

    for r in results:
        if isinstance(r, dict):
            print(f"{r['name']:<30} {r['status']:<12} {r.get('p50_ms', 'N/A'):<10} "
                  f"{r.get('p95_ms', 'N/A'):<10} {r.get('p99_ms', 'N/A'):<10} "
                  f"{r.get('avg_ms', 'N/A'):<10} {r.get('error_rate', 'N/A'):<8} "
                  f"{r.get('throughput_rps', 'N/A'):<8}")
        elif isinstance(r, Exception):
            print(f"{'Error':<30} {str(r)[:60]:<60}")

    print(f"\n{'═' * 80}")
    print(f"  Benchmark Complete")
    print(f"{'═' * 80}\n")


if __name__ == "__main__":
    asyncio.run(main())

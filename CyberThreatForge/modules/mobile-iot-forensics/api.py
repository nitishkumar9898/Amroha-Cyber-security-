"""Mobile & IoT Forensics Pipeline API.

FastAPI application for extracting and analyzing forensic artifacts
from mobile devices (Android/iOS) and IoT devices.
"""

import os
import json
import tempfile
import zipfile
import shutil
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Body
from fastapi.responses import JSONResponse

from parsers.android_parser import AndroidParser, AndroidForensicArtifacts
from parsers.ios_parser import IosParser, IosForensicArtifacts
from parsers.iot_parser import IotParser, IotForensicArtifacts
from models.communication_analyzer import (
    CommuniityAnalyzer,
    CommunicationRecord,
)
from models.location_analyzer import (
    LocationAnalyzer,
    LocationPoint,
    GeoFence,
)

from modules.shared.chain_of_custody import ChainOfCustodyManager
from modules.shared.sentinel_client import SentinelCoreClient

app = FastAPI(
    title="Mobile & IoT Forensics Pipeline",
    description="Forensic artifact extraction and analysis for Android, iOS, and IoT devices.",
    version="1.0.0",
)

SENTINEL_URL = os.getenv("SENTINEL_CORE_URL", "http://backend:3000/api/v1")
SENTINEL_API_KEY = os.getenv("SENTINEL_API_KEY", "")
MODULE_ID = "mobile-iot-forensics"
MODULE_VERSION = "1.0.0"


def get_custody_manager() -> ChainOfCustodyManager:
    return ChainOfCustodyManager()


def get_sentinel() -> SentinelCoreClient:
    return SentinelCoreClient(base_url=SENTINEL_URL, api_key=SENTINEL_API_KEY)


async def register_module():
    try:
        async with get_sentinel() as client:
            await client.register_module(
                module_id=MODULE_ID,
                domain="mobile_forensics",
                version=MODULE_VERSION,
                capabilities=[
                    "android_forensics",
                    "ios_forensics",
                    "iot_forensics",
                    "communication_analysis",
                    "location_analysis",
                    "app_usage_analysis",
                    "timeline_generation",
                ],
            )
    except Exception:
        pass


@app.on_event("startup")
async def startup():
    await register_module()


@app.get("/health")
async def health():
    return {
        "module": MODULE_ID,
        "version": MODULE_VERSION,
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Extraction Endpoints ──────────────────────────────────────────────


@app.post("/extract/android")
async def extract_android(
    file: UploadFile = File(...),
    custody: SentinelCoreClient = Depends(get_sentinel),
):
    """Extract Android forensic artifacts from uploaded extraction zip."""
    extraction_dir = _save_upload(file)
    try:
        parser = AndroidParser(extraction_dir)
        artifacts = parser.parse_all()

        custody_mgr = ChainOfCustodyManager()
        custody_mgr.record(
            action="extract_android",
            actor="mobile-iot-forensics",
            module=MODULE_ID,
            data={"filename": file.filename, "sms_count": len(artifacts.sms_mms)},
        )

        result = parser.to_dict()
        result["chain_of_custody"] = custody_mgr.to_dict()

        async with custody as client:
            await client.submit_finding(
                evidence_id=_generate_id(),
                module_id=MODULE_ID,
                domain="mobile_forensics",
                finding_type="android_extraction",
                severity="info",
                description=f"Extracted {len(artifacts.sms_mms)} SMS, {len(artifacts.call_logs)} call logs, "
                            f"{len(artifacts.contacts)} contacts from Android device",
                confidence=1.0,
                metadata={"filename": file.filename, "artifact_count": len(result)},
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(extraction_dir, ignore_errors=True)


@app.post("/extract/ios")
async def extract_ios(
    file: UploadFile = File(...),
    backup_password: str = Body(default=""),
    custody: SentinelCoreClient = Depends(get_sentinel),
):
    """Extract iOS forensic artifacts from uploaded backup zip."""
    extraction_dir = _save_upload(file)
    try:
        parser = IosParser(extraction_dir, backup_password=backup_password)
        artifacts = parser.parse_all()

        custody_mgr = ChainOfCustodyManager()
        custody_mgr.record(
            action="extract_ios",
            actor="mobile-iot-forensics",
            module=MODULE_ID,
            data={
                "filename": file.filename,
                "messages_count": len(artifacts.messages),
                "locations_count": len(artifacts.locations),
            },
        )

        result = parser.to_dict()
        result["chain_of_custody"] = custody_mgr.to_dict()

        async with custody as client:
            await client.submit_finding(
                evidence_id=_generate_id(),
                module_id=MODULE_ID,
                domain="mobile_forensics",
                finding_type="ios_extraction",
                severity="info",
                description=f"Extracted {len(artifacts.messages)} messages, {len(artifacts.call_logs)} calls, "
                            f"{len(artifacts.locations)} locations from iOS device",
                confidence=1.0,
                metadata={"filename": file.filename},
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(extraction_dir, ignore_errors=True)


@app.post("/extract/iot")
async def extract_iot(
    file: UploadFile = File(...),
    custody: SentinelCoreClient = Depends(get_sentinel),
):
    """Extract IoT device artifacts from uploaded log/export zip."""
    extraction_dir = _save_upload(file)
    try:
        parser = IotParser(extraction_dir)
        artifacts = parser.parse_all()

        custody_mgr = ChainOfCustodyManager()
        custody_mgr.record(
            action="extract_iot",
            actor="mobile-iot-forensics",
            module=MODULE_ID,
            data={
                "filename": file.filename,
                "devices_found": len(artifacts.connected_devices),
                "events_found": len(artifacts.smart_home_events),
            },
        )

        result = parser.to_dict()
        result["chain_of_custody"] = custody_mgr.to_dict()

        async with custody as client:
            await client.submit_finding(
                evidence_id=_generate_id(),
                module_id=MODULE_ID,
                domain="iot_forensics",
                finding_type="iot_extraction",
                severity="info",
                description=f"Extracted {len(artifacts.connected_devices)} devices, "
                            f"{len(artifacts.smart_home_events)} events from IoT hub",
                confidence=1.0,
                metadata={"filename": file.filename},
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(extraction_dir, ignore_errors=True)


# ── Analysis Endpoints ────────────────────────────────────────────────


@app.post("/analyze/timeline")
async def analyze_timeline(
    artifacts: dict[str, Any] = Body(...),
    custody: SentinelCoreClient = Depends(get_sentinel),
):
    """Generate timeline analysis from extracted artifacts."""
    timeline_entries = _build_timeline(artifacts)
    correlated = _correlate_events(timeline_entries)

    result = {
        "total_events": len(timeline_entries),
        "correlation_groups": len(correlated),
        "timeline": timeline_entries,
        "correlated_events": correlated,
        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    async with custody as client:
        await client.submit_finding(
            evidence_id=_generate_id(),
            module_id=MODULE_ID,
            domain="digital_forensics",
            finding_type="timeline_analysis",
            severity="info",
            description=f"Generated timeline with {len(timeline_entries)} events, "
                        f"{len(correlated)} correlation groups",
            confidence=0.9,
            metadata={"event_count": len(timeline_entries)},
        )

    return result


@app.post("/analyze/communications")
async def analyze_communications(
    data: dict[str, Any],
    model_path: Optional[str] = None,
    custody: SentinelCoreClient = Depends(get_sentinel),
):
    """Communication pattern analysis on extracted messages/calls."""
    records = _parse_communication_records(data)
    analyzer = CommuniityAnalyzer(model_path=model_path)
    analysis = analyzer.analyze(records)

    result = {
        "total_contacts": analysis.total_contacts,
        "total_messages": analysis.total_messages,
        "total_calls": analysis.total_calls,
        "avg_call_duration": analysis.avg_call_duration,
        "busiest_hour": analysis.busiest_hour,
        "busiest_day": analysis.busiest_day,
        "communication_graph": {
            "nodes": analysis.communication_graph.nodes if analysis.communication_graph else [],
            "edges": analysis.communication_graph.edges if analysis.communication_graph else [],
            "centrality": analysis.communication_graph.centrality if analysis.communication_graph else {},
            "communities": analysis.communication_graph.communities if analysis.communication_graph else [],
        },
        "anomalies": [
            {
                "anomaly_score": a.anomaly_score,
                "anomaly_type": a.anomaly_type,
                "description": a.description,
                "severity": a.severity,
            }
            for a in analysis.anomalies
        ],
        "behavioral_profile": analysis.behavioral_profile,
        "analysis_timestamp": analysis.analysis_timestamp,
    }

    if analysis.anomalies:
        async with custody as client:
            for anomaly in analysis.anomalies:
                await client.submit_finding(
                    evidence_id=_generate_id(),
                    module_id=MODULE_ID,
                    domain="mobile_forensics",
                    finding_type="communication_anomaly",
                    severity=anomaly.severity,
                    description=anomaly.description,
                    confidence=anomaly.anomaly_score,
                    metadata={"anomaly_type": anomaly.anomaly_type},
                )

    return result


@app.post("/analyze/location")
async def analyze_location(
    data: dict[str, Any],
    custody: SentinelCoreClient = Depends(get_sentinel),
):
    """Location history analysis with geo-fence detection."""
    points = _parse_location_points(data)
    analyzer = LocationAnalyzer()

    for f in data.get("geo_fences", []):
        analyzer.add_geo_fence(
            GeoFence(
                name=f["name"],
                latitude=f["latitude"],
                longitude=f["longitude"],
                radius_meters=f["radius_meters"],
                type=f.get("type", "monitored"),
            )
        )

    analysis = analyzer.analyze(points)
    result = analyzer.to_dict(analysis)

    if analysis.geo_fence_violations:
        async with custody as client:
            for v in analysis.geo_fence_violations:
                await client.submit_finding(
                    evidence_id=_generate_id(),
                    module_id=MODULE_ID,
                    domain="iot_forensics",
                    finding_type="geo_fence_violation",
                    severity=v.severity,
                    description=f"Geo-fence '{v.geo_fence_name}' {v.violation_type} at ({v.latitude}, {v.longitude})",
                    confidence=0.95,
                    metadata={
                        "fence_name": v.geo_fence_name,
                        "violation_type": v.violation_type,
                        "latitude": v.latitude,
                        "longitude": v.longitude,
                    },
                )

    return result


@app.post("/analyze/app-usage")
async def analyze_app_usage(
    artifacts: dict[str, Any] = Body(...),
    custody: SentinelCoreClient = Depends(get_sentinel),
):
    """Analyze app usage patterns from extracted artifacts."""
    installed_apps = artifacts.get("installed_apps", [])
    browser_history = artifacts.get("browser_history", [])

    app_categories = _categorize_apps(installed_apps)
    usage_patterns = _analyze_usage_patterns(installed_apps, browser_history)

    result = {
        "total_apps": len(installed_apps),
        "browser_entries": len(browser_history),
        "app_categories": app_categories,
        "usage_patterns": usage_patterns,
        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    async with custody as client:
        await client.submit_finding(
            evidence_id=_generate_id(),
            module_id=MODULE_ID,
            domain="mobile_forensics",
            finding_type="app_usage_analysis",
            severity="info",
            description=f"Analyzed {len(installed_apps)} apps across {len(app_categories)} categories",
            confidence=0.9,
            metadata={"app_count": len(installed_apps)},
        )

    return result


# ── Internal Helpers ──────────────────────────────────────────────────


def _save_upload(file: UploadFile) -> str:
    temp_dir = tempfile.mkdtemp(prefix="forensics_")
    temp_path = os.path.join(temp_dir, file.filename or "upload")
    with open(temp_path, "wb") as f:
        f.write(file.file.read())

    if temp_path.endswith(".zip"):
        with zipfile.ZipFile(temp_path, "r") as zf:
            zf.extractall(temp_dir)
        os.remove(temp_path)

    return temp_dir


def _generate_id() -> str:
    return str(uuid.uuid4())


def _build_timeline(artifacts: dict[str, Any]) -> list[dict]:
    events: list[dict] = []

    for sms in artifacts.get("sms_mms", []):
        if sms.get("date"):
            events.append({
                "timestamp": sms["date"],
                "type": "sms",
                "subtype": "incoming" if sms.get("type") == 1 else "outgoing",
                "description": f"SMS: {sms.get('address', 'unknown')}",
                "source": "android",
            })

    for call in artifacts.get("call_logs", []):
        if call.get("date"):
            type_map = {1: "incoming", 2: "outgoing", 3: "missed"}
            events.append({
                "timestamp": call["date"],
                "type": "call",
                "subtype": type_map.get(call.get("type", 0), "unknown"),
                "description": f"Call: {call.get('number', 'unknown')} ({call.get('duration', 0)}s)",
                "source": "android",
            })

    for msg in artifacts.get("whatsapp_messages", []):
        if msg.get("timestamp"):
            events.append({
                "timestamp": msg["timestamp"],
                "type": "message",
                "subtype": "whatsapp",
                "description": f"WhatsApp: {msg.get('sender', 'unknown')}: {msg.get('message', '')[:50]}",
                "source": "android",
            })

    for loc in artifacts.get("locations", []):
        if loc.get("timestamp"):
            events.append({
                "timestamp": loc["timestamp"],
                "type": "location",
                "subtype": loc.get("source", "gps"),
                "description": f"Location: ({loc.get('latitude')}, {loc.get('longitude')})",
                "source": "ios",
                "latitude": loc.get("latitude"),
                "longitude": loc.get("longitude"),
            })

    for event in artifacts.get("smart_home_events", []):
        if event.get("timestamp"):
            events.append({
                "timestamp": event["timestamp"],
                "type": "iot_event",
                "subtype": event.get("event_type", "unknown"),
                "description": f"IoT: {event.get('device_name', 'unknown')} - {event.get('event_type')}",
                "source": "iot",
            })

    events.sort(key=lambda e: e.get("timestamp", ""))
    return events


def _correlate_events(events: list[dict]) -> list[dict]:
    if not events:
        return []

    groups: list[dict] = []
    time_windows: dict[str, list[dict]] = {}

    for event in events:
        ts = event.get("timestamp", "")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts)
            window_key = dt.strftime("%Y-%m-%d %H:00")
        except (ValueError, TypeError):
            window_key = ts[:13]

        if window_key not in time_windows:
            time_windows[window_key] = []
        time_windows[window_key].append(event)

    for window, evts in time_windows.items():
        if len(evts) >= 2:
            groups.append({
                "time_window": f"{window}:00",
                "event_count": len(evts),
                "event_types": list({e.get("type", "unknown") for e in evts}),
                "sources": list({e.get("source", "unknown") for e in evts}),
                "events": evts,
            })

    return groups


def _parse_communication_records(data: dict) -> list[CommunicationRecord]:
    records: list[CommunicationRecord] = []

    for sms in data.get("sms_mms", []):
        records.append(
            CommunicationRecord(
                source=sms.get("address", "unknown"),
                target="me" if sms.get("type") == 1 else sms.get("address", "unknown"),
                channel="sms",
                timestamp=sms.get("date", ""),
                duration=0,
                direction="incoming" if sms.get("type") == 1 else "outgoing",
                content_snippet=(sms.get("body", "") or "")[:100],
            )
        )

    for call in data.get("call_logs", []):
        records.append(
            CommunicationRecord(
                source=call.get("number", "unknown"),
                target="me" if call.get("type") == 1 else call.get("number", "unknown"),
                channel="call",
                timestamp=call.get("date", ""),
                duration=call.get("duration", 0),
                direction={1: "incoming", 2: "outgoing"}.get(call.get("type", 0), "unknown"),
            )
        )

    for msg in data.get("whatsapp_messages", []):
        records.append(
            CommunicationRecord(
                source=msg.get("sender", "unknown"),
                target=msg.get("chat_session", "unknown"),
                channel="whatsapp",
                timestamp=msg.get("timestamp", ""),
                duration=0,
                direction="outgoing",
                content_snippet=(msg.get("message", "") or "")[:100],
            )
        )

    for msg in data.get("telegram_messages", []):
        records.append(
            CommunicationRecord(
                source=msg.get("sender", "unknown"),
                target=msg.get("chat_name", "unknown"),
                channel="telegram",
                timestamp=msg.get("date", ""),
                duration=0,
                direction="outgoing",
                content_snippet=(msg.get("message", "") or "")[:100],
            )
        )

    for msg in data.get("messages", []):
        records.append(
            CommunicationRecord(
                source=msg.get("sender", "unknown"),
                target=msg.get("chat_identifier", "unknown"),
                channel="imessage",
                timestamp=msg.get("date", ""),
                duration=0,
                direction="outgoing" if msg.get("is_from_me") else "incoming",
                content_snippet=(msg.get("text", "") or "")[:100],
            )
        )

    return records


def _parse_location_points(data: dict) -> list[LocationPoint]:
    points: list[LocationPoint] = []
    seen: set[tuple[str, float, float]] = set()

    for loc in data.get("locations", []):
        lat = loc.get("latitude")
        lon = loc.get("longitude")
        ts = loc.get("timestamp", "")
        if lat is None or lon is None:
            continue
        key = (ts, float(lat), float(lon))
        if key in seen:
            continue
        seen.add(key)
        points.append(
            LocationPoint(
                timestamp=ts,
                latitude=float(lat),
                longitude=float(lon),
                altitude=float(loc.get("altitude", 0)),
                accuracy=float(loc.get("horizontal_accuracy", 0)),
                source=loc.get("source", "unknown"),
            )
        )

    points.sort(key=lambda p: p.timestamp or "")
    return points


def _categorize_apps(apps: list[dict]) -> dict[str, int]:
    categories: dict[str, int] = defaultdict(int)

    category_map = {
        "com.whatsapp": "messaging",
        "com.facebook.katana": "social",
        "com.instagram.android": "social",
        "com.twitter.android": "social",
        "com.snapchat.android": "social",
        "com.google.android.apps.maps": "navigation",
        "com.google.android.gm": "email",
        "com.android.chrome": "browser",
        "org.mozilla.firefox": "browser",
        "com.google.android.youtube": "entertainment",
        "com.spotify.music": "entertainment",
        "com.netflix.mediaclient": "entertainment",
        "com.android.vending": "store",
        "com.google.android.apps.docs": "productivity",
        "com.microsoft.office.word": "productivity",
    }

    for app in apps:
        pkg = app.get("package_name", "")
        category = "other"
        for key, cat in category_map.items():
            if pkg.startswith(key) or key in pkg:
                category = cat
                break
        categories[category] += 1

    return dict(categories)


def _analyze_usage_patterns(
    apps: list[dict],
    browser_history: list[dict],
) -> dict[str, Any]:
    browser_count = len(browser_history)
    app_count = len(apps)

    if browser_history:
        domains = Counter()
        for entry in browser_history:
            url = entry.get("url", "")
            try:
                domain = urlparse(url).netloc
                if domain:
                    domains[domain] += entry.get("visit_count", 1)
            except Exception:
                pass
        top_domains = [{"domain": d, "visits": c} for d, c in domains.most_common(10)]
    else:
        top_domains = []

    return {
        "app_count": app_count,
        "browser_entries": browser_count,
        "top_domains": top_domains,
        "usage_diversity": len(set(a.get("package_name", "") for a in apps)),
    }


  

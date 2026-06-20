"""IoT device forensic artifact parser.

Extracts and parses artifacts from IoT devices including:
- Router logs for connected devices
- Smart home hub logs (events, schedules)
- Wearable device data (health, location)
- Voice assistant logs
- Firmware version analysis
"""

import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ConnectedDevice:
    mac_address: str
    ip_address: str
    hostname: str
    first_seen: str
    last_seen: str
    signal_strength: int
    vendor: str
    device_type: str  # smartphone, laptop, iot, etc.


@dataclass
class SmartHomeEvent:
    device_id: str
    device_name: str
    event_type: str  # motion_detected, door_open, temp_change, etc.
    timestamp: str
    value: Optional[str] = None
    unit: Optional[str] = None


@dataclass
class WearableDataPoint:
    device_id: str
    device_name: str
    timestamp: str
    data_type: str  # heart_rate, steps, sleep, location, etc.
    value: float
    unit: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass
class VoiceAssistantUtterance:
    device_id: str
    timestamp: str
    query_text: str
    response_text: str
    confidence: float
    locale: str
    action_type: str  # command, question, etc.


@dataclass
class FirmwareInfo:
    device_id: str
    device_model: str
    manufacturer: str
    current_version: str
    latest_version: Optional[str] = None
    release_date: Optional[str] = None
    vulnerabilities: list[str] = field(default_factory=list)
    is_outdated: bool = False


@dataclass
class IotForensicArtifacts:
    device_info: dict[str, Any] = field(default_factory=dict)
    connected_devices: list[ConnectedDevice] = field(default_factory=list)
    smart_home_events: list[SmartHomeEvent] = field(default_factory=list)
    wearable_data: list[WearableDataPoint] = field(default_factory=list)
    voice_utterances: list[VoiceAssistantUtterance] = field(default_factory=list)
    firmware_versions: list[FirmwareInfo] = field(default_factory=list)
    extraction_timestamp: str = ""


class IotParser:
    """Parse IoT device forensic images and logs."""

    def __init__(self, extraction_path: str | Path):
        self.base_path = Path(extraction_path)
        self.artifacts = IotForensicArtifacts(
            extraction_timestamp=datetime.now(timezone.utc).isoformat()
        )

    def parse_all(self) -> IotForensicArtifacts:
        self._parse_router_logs()
        self._parse_smart_hub_logs()
        self._parse_wearable_data()
        self._parse_voice_assistant_logs()
        self._parse_firmware_info()
        return self.artifacts

    def _find_files(self, pattern: str) -> list[Path]:
        matches = []
        if "*" not in pattern and not pattern.startswith("*"):
            pattern = f"*{pattern}*"
        for p in self.base_path.rglob(pattern):
            matches.append(p)
        return matches

    def _parse_router_logs(self) -> None:
        log_files = self._find_files("*.log") + self._find_files("leases") + self._find_files("syslog*")

        for log_file in log_files:
            try:
                content = log_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            log_name = log_file.name.lower()

            if "leases" in log_name:
                self._parse_dhcp_leases(content)
            elif "syslog" in log_name or log_file.suffix == ".log":
                self._parse_syslog(content)

        dhcp_leases = self.base_path / "var" / "lib" / "dhcp" / "dhcpd.leases"
        if dhcp_leases.exists():
            self._parse_dhcp_leases(dhcp_leases.read_text(encoding="utf-8", errors="ignore"))

        arp_cache = self.base_path / "proc" / "net" / "arp"
        if arp_cache.exists():
            self._parse_arp_cache(arp_cache.read_text(encoding="utf-8", errors="ignore"))

    def _parse_dhcp_leases(self, content: str) -> None:
        current = {}
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("lease "):
                current = {"ip_address": line.split()[1]}
            elif line.startswith("{"):
                continue
            elif "hardware ethernet" in line:
                current["mac_address"] = line.split()[-1].rstrip(";")
            elif "client-hostname" in line:
                current["hostname"] = line.split('"')[1] if '"' in line else ""
            elif "starts" in line:
                current["first_seen"] = line.split(" ", 2)[-1].rstrip(";")
            elif "ends" in line:
                current["last_seen"] = line.split(" ", 2)[-1].rstrip(";")
            elif "}" in line and current.get("mac_address"):
                self.artifacts.connected_devices.append(
                    ConnectedDevice(
                        mac_address=current.get("mac_address", ""),
                        ip_address=current.get("ip_address", ""),
                        hostname=current.get("hostname", ""),
                        first_seen=current.get("first_seen", ""),
                        last_seen=current.get("last_seen", ""),
                        signal_strength=0,
                        vendor="",
                        device_type="unknown",
                    )
                )
                current = {}

    def _parse_syslog(self, content: str) -> None:
        for line in content.splitlines():
            m = re.search(
                r"(dhcpd|dnsmasq|hostapd).*",
                line,
                re.IGNORECASE,
            )
            if m:
                mac = re.search(r"([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}", line)
                ip = re.search(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", line)
                hostname = re.search(r"name\s+['\"]?(\w+)['\"]?", line)
                if mac:
                    self.artifacts.connected_devices.append(
                        ConnectedDevice(
                            mac_address=mac.group(),
                            ip_address=ip.group() if ip else "",
                            hostname=hostname.group(1) if hostname else "",
                            first_seen="",
                            last_seen="",
                            signal_strength=0,
                            vendor="",
                            device_type="unknown",
                        )
                    )

    def _parse_arp_cache(self, content: str) -> None:
        for line in content.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 4:
                ip = parts[0]
                mac = parts[3]
                if re.match(r"([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}", mac):
                    self.artifacts.connected_devices.append(
                        ConnectedDevice(
                            mac_address=mac,
                            ip_address=ip,
                            hostname="",
                            first_seen="",
                            last_seen="",
                            signal_strength=0,
                            vendor="",
                            device_type="unknown",
                        )
                    )

    def _parse_smart_hub_logs(self) -> None:
        hub_files = self._find_files("hub.log") + self._find_files("events.log")
        hub_files += self._find_files("*.json")

        for hub_file in hub_files:
            try:
                if hub_file.suffix == ".json":
                    data = json.loads(hub_file.read_text(encoding="utf-8", errors="ignore"))
                    if isinstance(data, list):
                        for item in data:
                            self._parse_hub_event(item)
                    elif isinstance(data, dict):
                        self._parse_hub_event(data)
                else:
                    for line in hub_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                        try:
                            item = json.loads(line)
                            self._parse_hub_event(item)
                        except json.JSONDecodeError:
                            self._parse_hub_log_line(line)
            except Exception:
                pass

    def _parse_hub_event(self, item: dict) -> None:
        ts = item.get("timestamp") or item.get("date") or item.get("time", "")
        self.artifacts.smart_home_events.append(
            SmartHomeEvent(
                device_id=item.get("device_id") or item.get("id", ""),
                device_name=item.get("device_name") or item.get("name", ""),
                event_type=item.get("event_type") or item.get("type", "unknown"),
                timestamp=ts,
                value=str(item.get("value", "")),
                unit=item.get("unit"),
            )
        )

    def _parse_hub_log_line(self, line: str) -> None:
        m = re.search(
            r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})",
            line,
        )
        ts = m.group(1) if m else ""
        event_match = re.search(
            r"(motion|temperature|humidity|door|window|lock|alarm|switch|energy)",
            line,
            re.IGNORECASE,
        )
        if event_match:
            self.artifacts.smart_home_events.append(
                SmartHomeEvent(
                    device_id="",
                    device_name="",
                    event_type=event_match.group(1).lower(),
                    timestamp=ts,
                )
            )

    def _parse_wearable_data(self) -> None:
        wearable_files = self._find_files("health*.json") + self._find_files("fitness*.json")
        wearable_files += self._find_files("*.csv")
        wearable_files += self._find_files("wearable*.log")

        for wf in wearable_files:
            try:
                if wf.suffix == ".json":
                    data = json.loads(wf.read_text(encoding="utf-8", errors="ignore"))
                    records = data if isinstance(data, list) else [data]
                    for record in records:
                        self.artifacts.wearable_data.append(
                            WearableDataPoint(
                                device_id=record.get("device_id", ""),
                                device_name=record.get("device_name", ""),
                                timestamp=record.get("timestamp") or record.get("date", ""),
                                data_type=record.get("type") or record.get("data_type", "unknown"),
                                value=float(record.get("value", 0)),
                                unit=record.get("unit", ""),
                                latitude=record.get("lat") or record.get("latitude"),
                                longitude=record.get("lon") or record.get("longitude"),
                            )
                        )
                elif wf.suffix == ".csv":
                    self._parse_wearable_csv(wf)
            except Exception:
                pass

    def _parse_wearable_csv(self, csv_file: Path) -> None:
        try:
            lines = csv_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            if not lines:
                return
            headers = [h.strip().lower() for h in lines[0].split(",")]
            for line in lines[1:]:
                parts = line.split(",")
                if len(parts) < 2:
                    continue
                record = dict(zip(headers, [p.strip() for p in parts]))
                self.artifacts.wearable_data.append(
                    WearableDataPoint(
                        device_id=record.get("device_id", ""),
                        device_name=record.get("device_name", ""),
                        timestamp=record.get("timestamp") or record.get("date", ""),
                        data_type=record.get("type") or record.get("data_type", "unknown"),
                        value=float(record.get("value", 0)),
                        unit=record.get("unit", ""),
                        latitude=float(record["latitude"]) if "latitude" in record and record["latitude"] else None,
                        longitude=float(record["longitude"]) if "longitude" in record and record["longitude"] else None,
                    )
                )
        except Exception:
            pass

    def _parse_voice_assistant_logs(self) -> None:
        va_files = self._find_files("alexa*.json") + self._find_files("google*.json")
        va_files += self._find_files("siri*.json") + self._find_files("voice*.json")
        va_files += self._find_files("utterance*.json")

        for vf in va_files:
            try:
                data = json.loads(vf.read_text(encoding="utf-8", errors="ignore"))
                records = data if isinstance(data, list) else [data]
                for record in records:
                    self.artifacts.voice_utterances.append(
                        VoiceAssistantUtterance(
                            device_id=record.get("device_id", ""),
                            timestamp=record.get("timestamp") or record.get("date", ""),
                            query_text=record.get("query") or record.get("text", record.get("utterance", "")),
                            response_text=record.get("response") or record.get("reply", ""),
                            confidence=float(record.get("confidence", 0)),
                            locale=record.get("locale", "en-US"),
                            action_type=record.get("action_type") or record.get("type", "command"),
                        )
                    )
            except Exception:
                pass

    def _parse_firmware_info(self) -> None:
        firmware_files = self._find_files("firmware*.json") + self._find_files("version*.txt")
        firmware_files += self._find_files("device_info.json")

        known_vulnerabilities = self._load_vulnerability_db()

        for ff in firmware_files:
            try:
                if ff.suffix == ".json":
                    data = json.loads(ff.read_text(encoding="utf-8", errors="ignore"))
                    records = data if isinstance(data, list) else [data]
                    for record in records:
                        fw = self._create_firmware_info(record, known_vulnerabilities)
                        if fw:
                            self.artifacts.firmware_versions.append(fw)
                else:
                    content = ff.read_text(encoding="utf-8", errors="ignore")
                    for line in content.splitlines():
                        parts = line.split("=")
                        if len(parts) == 2:
                            record = {parts[0].strip(): parts[1].strip()}
                            fw = self._create_firmware_info(record, known_vulnerabilities)
                            if fw:
                                self.artifacts.firmware_versions.append(fw)
            except Exception:
                pass

    def _create_firmware_info(
        self, record: dict, vuln_db: dict[str, list[str]]
    ) -> FirmwareInfo | None:
        version = record.get("firmware_version") or record.get("version") or record.get("fw_version", "")
        if not version:
            return None

        device_id = record.get("device_id") or record.get("id", "")
        model = record.get("model") or record.get("device_model", "")
        manufacturer = record.get("manufacturer") or record.get("vendor", "")

        cves = vuln_db.get(model, vuln_db.get(manufacturer.lower(), []))

        is_outdated = bool(cves)

        return FirmwareInfo(
            device_id=device_id,
            device_model=model,
            manufacturer=manufacturer,
            current_version=version,
            latest_version=record.get("latest_version"),
            release_date=record.get("release_date"),
            vulnerabilities=cves,
            is_outdated=is_outdated,
        )

    def _load_vulnerability_db(self) -> dict[str, list[str]]:
        vuln_path = self.base_path / "vulnerability_db.json"
        if vuln_path.exists():
            try:
                return json.loads(vuln_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_info": self.artifacts.device_info,
            "extraction_timestamp": self.artifacts.extraction_timestamp,
            "connected_devices": [asdict(d) for d in self.artifacts.connected_devices],
            "smart_home_events": [asdict(e) for e in self.artifacts.smart_home_events],
            "wearable_data": [asdict(d) for d in self.artifacts.wearable_data],
            "voice_utterances": [asdict(u) for u in self.artifacts.voice_utterances],
            "firmware_versions": [asdict(f) for f in self.artifacts.firmware_versions],
        }

"""Android forensic artifact parser.

Extracts and parses artifacts from Android devices including:
- SMS/MMS databases (mmssms.db)
- Call logs (contacts2.db)
- WhatsApp data (msgstore.db, wa.db)
- Telegram data
- Browser history
- WiFi passwords and network history
"""

import os
import sqlite3
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class SmsMmsRecord:
    _id: int
    address: str
    date: str
    date_sent: str
    type: int  # 1=inbox, 2=sent, 3=draft, 4=outbox
    body: str
    read: int
    status: int
    service_center: str
    contact_name: Optional[str] = None


@dataclass
class CallLogRecord:
    _id: int
    number: str
    date: str
    duration: int
    type: int  # 1=incoming, 2=outgoing, 3=missed
    name: Optional[str] = None
    geocoded_location: Optional[str] = None


@dataclass
class ContactRecord:
    _id: int
    display_name: str
    phone_numbers: list[dict] = field(default_factory=list)
    emails: list[dict] = field(default_factory=list)
    organization: Optional[str] = None


@dataclass
class WhatsAppMessage:
    _id: int
    chat_session: str
    sender: str
    message: str
    timestamp: str
    message_type: str  # text, image, audio, video, document
    is_group: bool = False


@dataclass
class TelegramMessage:
    _id: int
    chat_name: str
    sender: str
    message: str
    date: str
    is_forward: bool = False


@dataclass
class BrowserHistoryRecord:
    url: str
    title: str
    visit_count: int
    last_visit_time: str
    bookmarked: bool = False


@dataclass
class WifiNetwork:
    ssid: str
    bssid: str
    capabilities: str
    frequency: int
    signal_strength: int
    passwords: list[str] = field(default_factory=list)


@dataclass
class AndroidForensicArtifacts:
    device_info: dict[str, Any] = field(default_factory=dict)
    sms_mms: list[SmsMmsRecord] = field(default_factory=list)
    call_logs: list[CallLogRecord] = field(default_factory=list)
    contacts: list[ContactRecord] = field(default_factory=list)
    whatsapp_messages: list[WhatsAppMessage] = field(default_factory=list)
    telegram_messages: list[TelegramMessage] = field(default_factory=list)
    browser_history: list[BrowserHistoryRecord] = field(default_factory=list)
    wifi_networks: list[WifiNetwork] = field(default_factory=list)
    installed_apps: list[dict] = field(default_factory=list)
    extraction_timestamp: str = ""


class AndroidParser:
    """Parse Android forensic images and extracted data."""

    def __init__(self, extraction_path: str | Path):
        self.base_path = Path(extraction_path)
        self.artifacts = AndroidForensicArtifacts(
            extraction_timestamp=datetime.now(timezone.utc).isoformat()
        )

    def parse_all(self) -> AndroidForensicArtifacts:
        self._parse_device_info()
        self._parse_sms_mms()
        self._parse_call_logs()
        self._parse_contacts()
        self._parse_whatsapp()
        self._parse_telegram()
        self._parse_browser_history()
        self._parse_wifi()
        self._parse_installed_apps()
        return self.artifacts

    def _resolve_db_path(self, *parts: str) -> Path | None:
        candidates = [
            self.base_path / p for p in [
                "/".join(parts),
                f"data/data/{'/'.join(parts)}",
                f"data/{'/'.join(parts)}",
                f"/{'/'.join(parts)}",
            ]
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    def _parse_device_info(self) -> None:
        build_prop = self._resolve_db_path("system", "build.prop")
        if build_prop:
            props = {}
            with open(build_prop, "r", errors="ignore") as f:
                for line in f:
                    if "=" in line:
                        k, v = line.strip().split("=", 1)
                        props[k] = v
            self.artifacts.device_info = props

    def _parse_sms_mms(self) -> None:
        db_path = self._resolve_db_path(
            "com.android.providers.telephony", "databases", "mmssms.db"
        )
        if not db_path or not db_path.exists():
            return
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {r["name"] for r in cursor.fetchall()}

            if "sms" in tables:
                cursor.execute(
                    "SELECT _id, address, date, date_sent, type, body, read, status, service_center "
                    "FROM sms ORDER BY date"
                )
                for row in cursor.fetchall():
                    self.artifacts.sms_mms.append(
                        SmsMmsRecord(
                            _id=row["_id"],
                            address=str(row["address"] or ""),
                            date=_unix_ts_to_iso(row["date"]),
                            date_sent=_unix_ts_to_iso(row["date_sent"]),
                            type=row["type"],
                            body=row["body"] or "",
                            read=row["read"],
                            status=row["status"],
                            service_center=str(row["service_center"] or ""),
                        )
                    )
            conn.close()
        except sqlite3.Error:
            pass

    def _parse_call_logs(self) -> None:
        db_path = self._resolve_db_path(
            "com.android.providers.contacts", "databases", "contacts2.db"
        )
        if not db_path or not db_path.exists():
            return
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT _id, number, date, duration, type, name, geocoded_location "
                "FROM calls ORDER BY date"
            )
            for row in cursor.fetchall():
                self.artifacts.call_logs.append(
                    CallLogRecord(
                        _id=row["_id"],
                        number=str(row["number"] or ""),
                        date=_unix_ts_to_iso(row["date"]),
                        duration=row["duration"],
                        type=row["type"],
                        name=row["name"],
                        geocoded_location=row["geocoded_location"],
                    )
                )
            conn.close()
        except sqlite3.Error:
            pass

    def _parse_contacts(self) -> None:
        db_path = self._resolve_db_path(
            "com.android.providers.contacts", "databases", "contacts2.db"
        )
        if not db_path or not db_path.exists():
            return
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT _id, display_name, company FROM raw_contacts")
            contact_map: dict[int, ContactRecord] = {}
            for row in cursor.fetchall():
                rec = ContactRecord(
                    _id=row["_id"],
                    display_name=row["display_name"] or "Unknown",
                    organization=row["company"],
                )
                contact_map[row["_id"]] = rec
                self.artifacts.contacts.append(rec)

            cursor.execute(
                "SELECT raw_contact_id, data1, data2, mimetype FROM data"
            )
            for row in cursor.fetchall():
                cid = row["raw_contact_id"]
                if cid not in contact_map:
                    continue
                contact = contact_map[cid]
                mime = row["mimetype"] or ""
                if "phone" in mime.lower():
                    contact.phone_numbers.append({
                        "number": str(row["data1"] or ""),
                        "type": str(row["data2"] or ""),
                    })
                elif "email" in mime.lower():
                    contact.emails.append({
                        "address": str(row["data1"] or ""),
                        "type": str(row["data2"] or ""),
                    })
            conn.close()
        except sqlite3.Error:
            pass

    def _parse_whatsapp(self) -> None:
        msgstore = self._resolve_db_path(
            "com.whatsapp", "databases", "msgstore.db"
        )
        wa_db = self._resolve_db_path("com.whatsapp", "databases", "wa.db")
        if not msgstore or not msgstore.exists():
            return
        try:
            conn = sqlite3.connect(str(msgstore))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {r["name"] for r in cursor.fetchall()}

            if "messages" in tables:
                cursor.execute(
                    "SELECT _id, chat_session, sender, message, timestamp, message_type, is_group "
                    "FROM messages ORDER BY timestamp"
                )
                for row in cursor.fetchall():
                    self.artifacts.whatsapp_messages.append(
                        WhatsAppMessage(
                            _id=row["_id"],
                            chat_session=row["chat_session"] or "",
                            sender=row["sender"] or "",
                            message=row["message"] or "",
                            timestamp=_unix_ts_to_iso(row["timestamp"]),
                            message_type=row["message_type"] or "text",
                            is_group=bool(row.get("is_group", False)),
                        )
                    )
            conn.close()
        except sqlite3.Error:
            pass

    def _parse_telegram(self) -> None:
        db_path = self._resolve_db_path(
            "org.telegram.messenger", "databases", "messages.db"
        )
        if not db_path or not db_path.exists():
            return
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {r["name"] for r in cursor.fetchall()}

            if "messages" in tables:
                cursor.execute(
                    "SELECT m._id, c.name as chat_name, m.sender, m.message, m.date, m.is_forward "
                    "FROM messages m LEFT JOIN chats c ON m.chat_id = c._id "
                    "ORDER BY m.date"
                )
                for row in cursor.fetchall():
                    self.artifacts.telegram_messages.append(
                        TelegramMessage(
                            _id=row["_id"],
                            chat_name=row["chat_name"] or "",
                            sender=row["sender"] or "",
                            message=row["message"] or "",
                            date=_unix_ts_to_iso(row["date"]),
                            is_forward=bool(row.get("is_forward", False)),
                        )
                    )
            conn.close()
        except sqlite3.Error:
            pass

    def _parse_browser_history(self) -> None:
        browsers = [
            ("com.android.chrome", "databases", "History"),
            ("org.mozilla.firefox", "profiles", "places.sqlite"),
            ("com.brave.browser", "databases", "History"),
        ]
        for pkg, *path in browsers:
            db_path = self._resolve_db_path(pkg, *path)
            if not db_path or not db_path.exists():
                continue
            try:
                conn = sqlite3.connect(str(db_path))
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls")
                for row in cursor.fetchall():
                    self.artifacts.browser_history.append(
                        BrowserHistoryRecord(
                            url=row["url"],
                            title=row["title"] or "",
                            visit_count=row["visit_count"],
                            last_visit_time=_chrome_time_to_iso(row["last_visit_time"]),
                        )
                    )
                conn.close()
            except sqlite3.Error:
                pass

    def _parse_wifi(self) -> None:
        db_path = self._resolve_db_path(
            "com.android.providers.settings", "databases", "settings.db"
        )
        wpa_supplicant = self.base_path / "data" / "misc" / "wifi" / "wpa_supplicant.conf"
        if wpa_supplicant.exists():
            current_ssid: str | None = None
            with open(wpa_supplicant, "r", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("network="):
                        current_ssid = None
                    m = re.match(r'\s*ssid="([^"]+)"', line)
                    if m:
                        current_ssid = m.group(1)
                    m = re.match(r'\s*psk="([^"]+)"', line)
                    if m and current_ssid:
                        existing = next(
                            (n for n in self.artifacts.wifi_networks if n.ssid == current_ssid),
                            None,
                        )
                        if existing:
                            existing.passwords.append(m.group(1))
                        else:
                            self.artifacts.wifi_networks.append(
                                WifiNetwork(
                                    ssid=current_ssid,
                                    bssid="",
                                    capabilities="",
                                    frequency=0,
                                    signal_strength=0,
                                    passwords=[m.group(1)],
                                )
                            )

    def _parse_installed_apps(self) -> None:
        packages_path = self.base_path / "data" / "system" / "packages.xml"
        if packages_path.exists():
            with open(packages_path, "r", errors="ignore") as f:
                content = f.read()
            for m in re.finditer(
                r'<package[^>]*name="([^"]+)"[^>]*codePath="([^"]+)"[^>]*version="([^"]+)"',
                content,
            ):
                self.artifacts.installed_apps.append({
                    "package_name": m.group(1),
                    "code_path": m.group(2),
                    "version": m.group(3),
                })

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_info": self.artifacts.device_info,
            "extraction_timestamp": self.artifacts.extraction_timestamp,
            "sms_mms": [asdict(r) for r in self.artifacts.sms_mms],
            "call_logs": [asdict(r) for r in self.artifacts.call_logs],
            "contacts": [
                {
                    "_id": c._id,
                    "display_name": c.display_name,
                    "phone_numbers": c.phone_numbers,
                    "emails": c.emails,
                    "organization": c.organization,
                }
                for c in self.artifacts.contacts
            ],
            "whatsapp_messages": [asdict(r) for r in self.artifacts.whatsapp_messages],
            "telegram_messages": [asdict(r) for r in self.artifacts.telegram_messages],
            "browser_history": [asdict(r) for r in self.artifacts.browser_history],
            "wifi_networks": [
                {
                    "ssid": n.ssid,
                    "bssid": n.bssid,
                    "capabilities": n.capabilities,
                    "frequency": n.frequency,
                    "signal_strength": n.signal_strength,
                    "passwords": n.passwords,
                }
                for n in self.artifacts.wifi_networks
            ],
            "installed_apps": self.artifacts.installed_apps,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AndroidForensicArtifacts:
        artifacts = AndroidForensicArtifacts(
            device_info=data.get("device_info", {}),
            extraction_timestamp=data.get("extraction_timestamp", ""),
            sms_mms=[SmsMmsRecord(**r) for r in data.get("sms_mms", [])],
            call_logs=[CallLogRecord(**r) for r in data.get("call_logs", [])],
            wifi_networks=[WifiNetwork(**n) for n in data.get("wifi_networks", [])],
        )
        return artifacts


def _unix_ts_to_iso(ts: Any) -> str:
    try:
        ts_int = int(str(ts)[:10]) if ts else 0
        if ts_int == 0:
            return ""
        return datetime.fromtimestamp(ts_int, tz=timezone.utc).isoformat()
    except (ValueError, OSError):
        return str(ts) if ts else ""


def _chrome_time_to_iso(ct: Any) -> str:
    try:
        ct_int = int(str(ct)) if ct else 0
        if ct_int == 0:
            return ""
        epoch_start = datetime(1601, 1, 1, tzinfo=timezone.utc)
        return (epoch_start + __import__("datetime").timedelta(microseconds=ct_int)).isoformat()
    except (ValueError, OSError):
        return str(ct) if ct else ""

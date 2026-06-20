"""iOS forensic artifact parser.

Extracts and parses artifacts from iOS backups and extractions including:
- iMessage/SMS from sms.db
- WhatsApp from ChatStorage.sqlite
- Call history from call_history.db
- Location data (cache_encryptedB.db, consolidated.db)
- Contacts and app data
"""

import os
import sqlite3
import plistlib
import shutil
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class IMessageRecord:
    _id: int
    chat_identifier: str
    sender: str
    text: str
    date: str
    is_from_me: bool
    service: str  # iMessage, SMS
    message_type: int


@dataclass
class IosWhatsAppMessage:
    _id: int
    chat_name: str
    sender: str
    message: str
    timestamp: str
    message_type: str


@dataclass
class IosCallRecord:
    _id: int
    address: str
    date: str
    duration: int
    call_type: int  # 1=incoming, 2=outgoing, 3=missed
    name: Optional[str] = None


@dataclass
class IosLocationRecord:
    timestamp: str
    latitude: float
    longitude: float
    altitude: float
    horizontal_accuracy: float
    vertical_accuracy: float
    source: str  # GPS, WiFi, Cell tower


@dataclass
class IosContact:
    identifier: str
    display_name: str
    phone_numbers: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)


@dataclass
class IosForensicArtifacts:
    device_info: dict[str, Any] = field(default_factory=dict)
    messages: list[IMessageRecord] = field(default_factory=list)
    whatsapp_messages: list[IosWhatsAppMessage] = field(default_factory=list)
    call_logs: list[IosCallRecord] = field(default_factory=list)
    locations: list[IosLocationRecord] = field(default_factory=list)
    contacts: list[IosContact] = field(default_factory=list)
    extraction_timestamp: str = ""


class IosParser:
    """Parse iOS backups and forensic images."""

    def __init__(self, extraction_path: str | Path, backup_password: str = ""):
        self.base_path = Path(extraction_path)
        self.backup_password = backup_password
        self.artifacts = IosForensicArtifacts(
            extraction_timestamp=datetime.now(timezone.utc).isoformat()
        )
        self._domain_map: dict[str, str] = {}

    def parse_all(self) -> IosForensicArtifacts:
        self._parse_manifest()
        self._parse_sms_db()
        self._parse_whatsapp()
        self._parse_call_history()
        self._parse_location_data()
        self._parse_contacts()
        return self.artifacts

    def _find_db(self, relative_domain_path: str) -> Path | None:
        candidates = [
            self.base_path / relative_domain_path,
            self.base_path / "AppDomainGroup" / relative_domain_path,
            self.base_path / "AppDomain" / relative_domain_path,
            self.base_path / "HomeDomain" / relative_domain_path,
            self.base_path / "RootDomain" / relative_domain_path,
        ]
        for p in candidates:
            if p.exists():
                return p
        for f in self.base_path.rglob(relative_domain_path.split("/")[-1]):
            return f
        return None

    def _parse_manifest(self) -> None:
        manifest = self.base_path / "Manifest.plist"
        if manifest.exists():
            try:
                with open(manifest, "rb") as f:
                    plist = plistlib.load(f)
                self.artifacts.device_info = {
                    "device_name": plist.get("DeviceName", ""),
                    "product_type": plist.get("ProductType", ""),
                    "product_version": plist.get("ProductVersion", ""),
                    "serial_number": plist.get("SerialNumber", ""),
                    "imei": plist.get("IMEI", ""),
                    "phone_number": plist.get("PhoneNumber", ""),
                    "unique_device_id": plist.get("UniqueDeviceID", ""),
                    "backup_created": str(plist.get("LastBackupDate", "")),
                }
                self._domain_map = {
                    k: v.get("RelativePath", "") if isinstance(v, dict) else ""
                    for k, v in plist.get("Applications", {}).items()
                }
            except Exception:
                pass

        info_plist = self.base_path / "Info.plist"
        if info_plist.exists():
            try:
                with open(info_plist, "rb") as f:
                    plist = plistlib.load(f)
                self.artifacts.device_info.update({
                    "build_version": plist.get("Build Version", ""),
                    "icloud_account": plist.get("CloudAccount", ""),
                })
            except Exception:
                pass

    def _parse_sms_db(self) -> None:
        sms_db = self._find_db("Library/SMS/sms.db")
        if not sms_db or not sms_db.exists():
            return
        try:
            conn = sqlite3.connect(str(sms_db))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='message'")
            if not cursor.fetchone():
                conn.close()
                return

            cursor.execute("""
                SELECT m.ROWID, c.chat_identifier, m.sender, m.text,
                       m.date, m.is_from_me, m.service, m.message_type
                FROM message m
                LEFT JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
                LEFT JOIN chat c ON cmj.chat_id = c.ROWID
                ORDER BY m.date
            """)
            for row in cursor.fetchall():
                self.artifacts.messages.append(
                    IMessageRecord(
                        _id=row["ROWID"],
                        chat_identifier=row["chat_identifier"] or "",
                        sender=str(row["sender"] or ""),
                        text=row["text"] or "",
                        date=_ios_date_to_iso(row["date"]),
                        is_from_me=bool(row["is_from_me"]),
                        service=row["service"] or "SMS",
                        message_type=row["message_type"] or 0,
                    )
                )
            conn.close()
        except sqlite3.Error:
            pass

    def _parse_whatsapp(self) -> None:
        wa_db = self._find_db(
            "AppDomainGroup-group.net.whatsapp.WhatsApp.shared/Library/Message/"
            "ChatStorage.sqlite"
        )
        if not wa_db or not wa_db.exists():
            wa_db = self._find_db("ChatStorage.sqlite")
            if not wa_db or not wa_db.exists():
                return
        try:
            conn = sqlite3.connect(str(wa_db))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ZWAMESSAGE'")
            if not cursor.fetchone():
                conn.close()
                return

            cursor.execute("""
                SELECT Z_PK, ZFROMJID, ZTEXT, ZMESSAGEDATE, ZMESSAGETYPE, ZCHATNAME
                FROM ZWAMESSAGE
                ORDER BY ZMESSAGEDATE
            """)
            for row in cursor.fetchall():
                self.artifacts.whatsapp_messages.append(
                    IosWhatsAppMessage(
                        _id=row["Z_PK"],
                        chat_name=row["ZCHATNAME"] or "",
                        sender=str(row["ZFROMJID"] or ""),
                        message=row["ZTEXT"] or "",
                        timestamp=_ios_date_to_iso(row["ZMESSAGEDATE"]),
                        message_type=row["ZMESSAGETYPE"] or "text",
                    )
                )
            conn.close()
        except sqlite3.Error:
            pass

    def _parse_call_history(self) -> None:
        call_db = self._find_db("Library/CallHistoryDB/CallHistory.storedata")
        if not call_db or not call_db.exists():
            call_db = self._find_db("call_history.db")
            if not call_db or not call_db.exists():
                return
        try:
            conn = sqlite3.connect(str(call_db))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {r["name"] for r in cursor.fetchall()}

            table_name = "ZCALLRECORD" if "ZCALLRECORD" in tables else "call"
            if table_name not in tables:
                conn.close()
                return

            cursor.execute(f"PRAGMA table_info({table_name})")
            cols = {r["name"] for r in cursor.fetchall()}

            query_cols = []
            if "Z_PK" in cols:
                query_cols.append("Z_PK as _id")
            elif "_id" in cols:
                query_cols.append("_id")
            else:
                query_cols.append("ROWID as _id")

            if "ZADDRESS" in cols:
                query_cols.append("ZADDRESS as address")
            elif "number" in cols:
                query_cols.append("number as address")

            if "ZDATE" in cols:
                query_cols.append("ZDATE as call_date")
            elif "date" in cols:
                query_cols.append("date as call_date")

            if "ZDURATION" in cols:
                query_cols.append("ZDURATION as duration")
            elif "duration" in cols:
                query_cols.append("duration")

            if "ZCALLTYPE" in cols:
                query_cols.append("ZCALLTYPE as call_type")
            elif "call_type" in cols:
                query_cols.append("call_type")

            if "ZNAME" in cols:
                query_cols.append("ZNAME as name")
            elif "name" in cols:
                query_cols.append("name")

            if not query_cols:
                conn.close()
                return

            cursor.execute(f"SELECT {', '.join(query_cols)} FROM {table_name}")
            for row in cursor.fetchall():
                self.artifacts.call_logs.append(
                    IosCallRecord(
                        _id=row[0],
                        address=str(row[1] or ""),
                        date=_ios_date_to_iso(row[2]),
                        duration=row[3] if row[3] else 0,
                        call_type=row[4] if row[4] else 0,
                        name=str(row[5]) if len(row) > 5 and row[5] else None,
                    )
                )
            conn.close()
        except sqlite3.Error:
            pass

    def _parse_location_data(self) -> None:
        cache_db = self._find_db("Library/Caches/locationd/cache_encryptedB.db")
        if not cache_db or not cache_db.exists():
            cache_db = self._find_db("cache_encryptedB.db")
        if cache_db and cache_db.exists():
            try:
                conn = sqlite3.connect(str(cache_db))
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = {r["name"] for r in cursor.fetchall()}
                if "WifiLocation" in tables:
                    cursor.execute(
                        "SELECT timestamp, latitude, longitude, accuracy FROM WifiLocation"
                    )
                    for row in cursor.fetchall():
                        self.artifacts.locations.append(
                            IosLocationRecord(
                                timestamp=_unix_ts_to_iso(row["timestamp"]),
                                latitude=float(row["latitude"]),
                                longitude=float(row["longitude"]),
                                altitude=0.0,
                                horizontal_accuracy=float(row["accuracy"] or 0),
                                vertical_accuracy=0.0,
                                source="WiFi",
                            )
                        )
                if "CellLocation" in tables:
                    cursor.execute(
                        "SELECT timestamp, latitude, longitude, accuracy FROM CellLocation"
                    )
                    for row in cursor.fetchall():
                        self.artifacts.locations.append(
                            IosLocationRecord(
                                timestamp=_unix_ts_to_iso(row["timestamp"]),
                                latitude=float(row["latitude"]),
                                longitude=float(row["longitude"]),
                                altitude=0.0,
                                horizontal_accuracy=float(row["accuracy"] or 0),
                                vertical_accuracy=0.0,
                                source="Cell tower",
                            )
                        )
                conn.close()
            except sqlite3.Error:
                pass

        consolidated_db = self._find_db(
            "Library/Caches/com.apple.routined/Cache/consolidated.db"
        )
        if not consolidated_db or not consolidated_db.exists():
            consolidated_db = self._find_db("consolidated.db")
        if consolidated_db and consolidated_db.exists():
            try:
                conn = sqlite3.connect(str(consolidated_db))
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = {r["name"] for r in cursor.fetchall()}

                for table in tables:
                    cursor.execute(f"PRAGMA table_info({table})")
                    cols = {r["name"] for r in cursor.fetchall()}
                    required = {"latitude", "longitude"}
                    if required.intersection(cols):
                        lat_col = "latitude" if "latitude" in cols else "lat"
                        lon_col = "longitude" if "longitude" in cols else "lon"
                        ts_col = "date" if "date" in cols else "timestamp"
                        try:
                            cursor.execute(
                                f"SELECT {ts_col} as ts, {lat_col} as lat, {lon_col} as lon "
                                f"FROM {table} LIMIT 1000"
                            )
                            for row in cursor.fetchall():
                                self.artifacts.locations.append(
                                    IosLocationRecord(
                                        timestamp=_unix_ts_to_iso(row["ts"]),
                                        latitude=float(row["lat"]),
                                        longitude=float(row["lon"]),
                                        altitude=0.0,
                                        horizontal_accuracy=0.0,
                                        vertical_accuracy=0.0,
                                        source=f"Routine ({table})",
                                    )
                                )
                        except sqlite3.Error:
                            pass
                conn.close()
            except sqlite3.Error:
                pass

    def _parse_contacts(self) -> None:
        contacts_db = self._find_db("Library/AddressBook/AddressBook.sqlitedb")
        if not contacts_db or not contacts_db.exists():
            return
        try:
            conn = sqlite3.connect(str(contacts_db))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT Z_PK, ZFIRSTNAME, ZLASTNAME, ZORGANIZATION "
                "FROM ZABCDRECORD"
            )
            for row in cursor.fetchall():
                first = row["ZFIRSTNAME"] or ""
                last = row["ZLASTNAME"] or ""
                self.artifacts.contacts.append(
                    IosContact(
                        identifier=str(row["Z_PK"]),
                        display_name=f"{first} {last}".strip() or "Unknown",
                    )
                )
            conn.close()
        except sqlite3.Error:
            pass

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_info": self.artifacts.device_info,
            "extraction_timestamp": self.artifacts.extraction_timestamp,
            "messages": [asdict(r) for r in self.artifacts.messages],
            "whatsapp_messages": [asdict(r) for r in self.artifacts.whatsapp_messages],
            "call_logs": [asdict(r) for r in self.artifacts.call_logs],
            "locations": [asdict(r) for r in self.artifacts.locations],
            "contacts": [asdict(r) for r in self.artifacts.contacts],
        }


def _ios_date_to_iso(ts: Any) -> str:
    try:
        ts_int = int(str(ts)) if ts else 0
        if ts_int == 0:
            return ""
        reference_date = datetime(2001, 1, 1, tzinfo=timezone.utc)
        return (reference_date + timedelta(seconds=ts_int)).isoformat()
    except (ValueError, OSError):
        return str(ts) if ts else ""


def _unix_ts_to_iso(ts: Any) -> str:
    try:
        ts_int = int(str(ts)[:10]) if ts else 0
        if ts_int == 0:
            return ""
        return datetime.fromtimestamp(ts_int, tz=timezone.utc).isoformat()
    except (ValueError, OSError):
        return str(ts) if ts else ""

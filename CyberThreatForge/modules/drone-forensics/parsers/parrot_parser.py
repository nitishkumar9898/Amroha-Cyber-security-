"""Parrot drone forensic log parser.

Parses Parrot flight logs (JSON/CSV based) and extracts telemetry similar to DJI.
Supports Parrot Anafi, Bebop, Disco series.
"""

import json
import csv
import os
import re
import hashlib
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ParrotGpsSample:
    timestamp: str
    latitude: float
    longitude: float
    altitude_m: float
    relative_altitude_m: float
    speed_ms: float
    heading_deg: float
    num_satellites: int
    gps_fix: int

@dataclass
class ParrotBatterySample:
    timestamp: str
    voltage_v: float
    current_a: float
    capacity_percent: int
    temperature_c: float

@dataclass
class ParrotImuSample:
    timestamp: str
    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float
    pitch_deg: float
    roll_deg: float
    yaw_deg: float

@dataclass
class ParrotMotorSample:
    timestamp: str
    motor1_rpm: float
    motor2_rpm: float
    motor3_rpm: float
    motor4_rpm: float

@dataclass
class ParrotPilotEvent:
    timestamp: str
    event_type: str
    description: str

@dataclass
class ParrotMediaEntry:
    file_path: str
    file_type: str
    timestamp: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    altitude_m: Optional[float]
    file_size_bytes: int
    hash_md5: Optional[str]

@dataclass
class ParrotFlightLog:
    aircraft_model: str
    aircraft_sn: str
    firmware_version: str
    total_flight_time_s: float
    max_altitude_m: float
    max_speed_ms: float
    max_distance_m: float
    gps_samples: list[ParrotGpsSample]
    battery_samples: list[ParrotBatterySample]
    imu_samples: list[ParrotImuSample]
    motor_samples: list[ParrotMotorSample]
    pilot_events: list[ParrotPilotEvent]
    media_entries: list[ParrotMediaEntry]
    takeoff_location: Optional[dict] = None
    landing_location: Optional[dict] = None
    home_location: Optional[dict] = None
    parse_warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parrot JSON flight log parser
# ---------------------------------------------------------------------------

class ParrotJsonParser:
    """Parses Parrot flight logs in JSON format (Anafi, Bebop series)."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.warnings: list[str] = []

    def parse(self) -> ParrotFlightLog:
        if not self.file_path.exists():
            raise FileNotFoundError(f"Flight log not found: {self.file_path}")

        text = self.file_path.read_text(encoding="utf-8", errors="replace")

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = self._try_csv_parse(text)

        return self._parse_json_structure(data)

    def _try_csv_parse(self, text: str) -> list[dict]:
        lines = text.strip().splitlines()
        if not lines:
            return []
        reader = csv.DictReader(lines)
        return list(reader)

    def _parse_json_structure(self, data: Any) -> ParrotFlightLog:
        log = ParrotFlightLog(
            aircraft_model="Parrot (JSON Log)", aircraft_sn="", firmware_version="",
            total_flight_time_s=0.0, max_altitude_m=0.0, max_speed_ms=0.0,
            max_distance_m=0.0, gps_samples=[], battery_samples=[], imu_samples=[],
            motor_samples=[], pilot_events=[], media_entries=[],
        )

        if isinstance(data, dict):
            log.aircraft_model = data.get("product", data.get("model", "Parrot"))
            log.aircraft_sn = data.get("serial", data.get("sn", ""))
            log.firmware_version = data.get("firmware", data.get("firmware_version", ""))

            records = data.get("records", data.get("telemetry", data.get("data", [])))
            if isinstance(records, dict):
                records = [records]
            if isinstance(records, list):
                self._parse_records(records, log)
            else:
                self._parse_flat_dict(data, log)

        elif isinstance(data, list):
            self._parse_records(data, log)

        if log.gps_samples:
            first = log.gps_samples[0]
            log.home_location = {"latitude": first.latitude, "longitude": first.longitude, "altitude_m": first.altitude_m}
            log.takeoff_location = {"latitude": first.latitude, "longitude": first.longitude, "altitude_m": first.altitude_m}
            last = log.gps_samples[-1]
            log.landing_location = {"latitude": last.latitude, "longitude": last.longitude, "altitude_m": last.altitude_m}

        log.parse_warnings = self.warnings
        return log

    def _parse_records(self, records: list[dict], log: ParrotFlightLog) -> None:
        for record in records:
            if not isinstance(record, dict):
                continue

            ts = record.get("timestamp", record.get("time", record.get("date", "")))

            lat = self._float(record.get("latitude", record.get("lat", 0)))
            lon = self._float(record.get("longitude", record.get("lon", 0)))
            alt = self._float(record.get("altitude", record.get("alt", 0)))
            speed = self._float(record.get("speed", record.get("groundspeed", 0)))

            if abs(lat) > 0.1 and abs(lon) > 0.1:
                heading = self._float(record.get("heading", record.get("yaw", 0)))
                sats = int(self._float(record.get("satellites", record.get("gps_accuracy", 0))))

                log.max_altitude_m = max(log.max_altitude_m, alt)
                log.max_speed_ms = max(log.max_speed_ms, speed)

                log.gps_samples.append(ParrotGpsSample(
                    timestamp=ts, latitude=lat, longitude=lon,
                    altitude_m=alt, relative_altitude_m=alt,
                    speed_ms=speed, heading_deg=heading,
                    num_satellites=sats, gps_fix=3 if sats >= 6 else 2 if sats >= 4 else 0,
                ))

            volt = self._float(record.get("voltage", record.get("battery_voltage", 0)))
            pct = int(self._float(record.get("battery", record.get("battery_percent", 0))))
            if volt > 0 or pct > 0:
                log.battery_samples.append(ParrotBatterySample(
                    timestamp=ts, voltage_v=volt, current_a=self._float(record.get("current", 0)),
                    capacity_percent=pct, temperature_c=self._float(record.get("battery_temp", 0)),
                ))

            ax = self._float(record.get("accel_x", 0))
            ay = self._float(record.get("accel_y", 0))
            az = self._float(record.get("accel_z", 0))
            if ax != 0 or ay != 0 or az != 0:
                log.imu_samples.append(ParrotImuSample(
                    timestamp=ts, accel_x=ax, accel_y=ay, accel_z=az,
                    gyro_x=self._float(record.get("gyro_x", 0)),
                    gyro_y=self._float(record.get("gyro_y", 0)),
                    gyro_z=self._float(record.get("gyro_z", 0)),
                    pitch_deg=self._float(record.get("pitch", 0)),
                    roll_deg=self._float(record.get("roll", 0)),
                    yaw_deg=self._float(record.get("yaw", 0)),
                ))

            m1 = self._float(record.get("motor1", record.get("motor1_rpm", 0)))
            if m1 > 0:
                log.motor_samples.append(ParrotMotorSample(
                    timestamp=ts, motor1_rpm=m1,
                    motor2_rpm=self._float(record.get("motor2", record.get("motor2_rpm", 0))),
                    motor3_rpm=self._float(record.get("motor3", record.get("motor3_rpm", 0))),
                    motor4_rpm=self._float(record.get("motor4", record.get("motor4_rpm", 0))),
                ))

            event = record.get("event", record.get("event_type", ""))
            if event:
                log.pilot_events.append(ParrotPilotEvent(
                    timestamp=ts, event_type=event,
                    description=record.get("description", record.get("message", event)),
                ))

    def _parse_flat_dict(self, data: dict, log: ParrotFlightLog) -> None:
        for key, value in data.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                enriched = [{"timestamp": key, **v} if isinstance(v, dict) else v for v in value]
                self._parse_records(enriched, log)

    def _float(self, value: Any) -> float:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0


# ---------------------------------------------------------------------------
# Parrot CSV flight log parser
# ---------------------------------------------------------------------------

class ParrotCsvParser:
    """Parses Parrot CSV format flight logs (Bebop, Disco)."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.warnings: list[str] = []

    def parse(self) -> ParrotFlightLog:
        if not self.file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")

        log = ParrotFlightLog(
            aircraft_model="Parrot (CSV Log)", aircraft_sn="", firmware_version="",
            total_flight_time_s=0.0, max_altitude_m=0.0, max_speed_ms=0.0,
            max_distance_m=0.0, gps_samples=[], battery_samples=[], imu_samples=[],
            motor_samples=[], pilot_events=[], media_entries=[],
        )

        with open(self.file_path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_data = {k.strip().lower(): v.strip() for k, v in row.items() if k}

                ts = row_data.get("timestamp", row_data.get("time", ""))

                lat = self._float(row_data.get("latitude", row_data.get("lat", 0)))
                lon = self._float(row_data.get("longitude", row_data.get("lon", 0)))
                alt = self._float(row_data.get("altitude", row_data.get("alt", 0)))
                speed = self._float(row_data.get("speed", row_data.get("groundspeed", 0)))

                if abs(lat) > 0.1 and abs(lon) > 0.1:
                    log.max_altitude_m = max(log.max_altitude_m, alt)
                    log.max_speed_ms = max(log.max_speed_ms, speed)
                    sats = int(self._float(row_data.get("satellites", 0)))

                    if log.home_location is None:
                        log.home_location = {"latitude": lat, "longitude": lon, "altitude_m": alt}
                        log.takeoff_location = {"latitude": lat, "longitude": lon, "altitude_m": alt}

                    log.gps_samples.append(ParrotGpsSample(
                        timestamp=ts, latitude=lat, longitude=lon,
                        altitude_m=alt, relative_altitude_m=alt,
                        speed_ms=speed, heading_deg=self._float(row_data.get("heading", 0)),
                        num_satellites=sats, gps_fix=3 if sats >= 6 else 2,
                    ))

                volt = self._float(row_data.get("voltage", row_data.get("battery_voltage", 0)))
                pct = int(self._float(row_data.get("battery", row_data.get("battery_percent", 0))))
                if volt > 0 or pct > 0:
                    log.battery_samples.append(ParrotBatterySample(
                        timestamp=ts, voltage_v=volt, current_a=self._float(row_data.get("current", 0)),
                        capacity_percent=pct, temperature_c=self._float(row_data.get("battery_temp", 0)),
                    ))

                ax = self._float(row_data.get("accel_x", 0))
                if ax != 0:
                    log.imu_samples.append(ParrotImuSample(
                        timestamp=ts, accel_x=ax,
                        accel_y=self._float(row_data.get("accel_y", 0)),
                        accel_z=self._float(row_data.get("accel_z", 0)),
                        gyro_x=self._float(row_data.get("gyro_x", 0)),
                        gyro_y=self._float(row_data.get("gyro_y", 0)),
                        gyro_z=self._float(row_data.get("gyro_z", 0)),
                        pitch_deg=self._float(row_data.get("pitch", 0)),
                        roll_deg=self._float(row_data.get("roll", 0)),
                        yaw_deg=self._float(row_data.get("yaw", 0)),
                    ))

            if log.gps_samples:
                last = log.gps_samples[-1]
                log.landing_location = {"latitude": last.latitude, "longitude": last.longitude, "altitude_m": last.altitude_m}

        log.parse_warnings = self.warnings
        return log

    def _float(self, value: Any) -> float:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0


# ---------------------------------------------------------------------------
# Parrot Media Parser
# ---------------------------------------------------------------------------

class ParrotMediaParser:
    """Parses media metadata from Parrot drone storage."""

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".dng", ".mp4", ".mov"}

    def __init__(self, media_dir: str | Path):
        self.media_dir = Path(media_dir)

    def parse(self) -> list[ParrotMediaEntry]:
        entries: list[ParrotMediaEntry] = []
        if not self.media_dir.exists():
            return entries

        for fpath in sorted(self.media_dir.rglob("*")):
            if fpath.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue
            if not fpath.is_file():
                continue

            try:
                fstat = fpath.stat()
                md5 = self._md5(fpath)
            except OSError:
                md5 = None

            gps = self._gps_from_path(fpath)
            ts = self._ts_from_path(fpath)

            entries.append(ParrotMediaEntry(
                file_path=str(fpath.relative_to(self.media_dir)),
                file_type=fpath.suffix.lower().lstrip("."),
                timestamp=ts,
                latitude=gps[0], longitude=gps[1], altitude_m=gps[2],
                file_size_bytes=fstat.st_size,
                hash_md5=md5,
            ))

        return entries

    def _md5(self, path: Path) -> str:
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _gps_from_path(self, path: Path) -> tuple:
        pattern = r"([NS])([\d.]+)_([EW])([\d.]+)"
        m = re.search(pattern, path.stem)
        if m:
            try:
                lat = float(m.group(2))
                lon = float(m.group(4))
                if m.group(1) == "S":
                    lat = -lat
                if m.group(3) == "W":
                    lon = -lon
                return (lat, lon, None)
            except ValueError:
                pass
        return (None, None, None)

    def _ts_from_path(self, path: Path) -> Optional[str]:
        pattern = r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})"
        m = re.search(pattern, path.stem)
        if m:
            try:
                dt = datetime(
                    int(m.group(1)), int(m.group(2)), int(m.group(3)),
                    int(m.group(4)), int(m.group(5)), int(m.group(6)),
                    tzinfo=timezone.utc,
                )
                return dt.isoformat()
            except ValueError:
                pass
        return None


# ---------------------------------------------------------------------------
# Convenience: unified Parrot parser
# ---------------------------------------------------------------------------

def parse_parrot_flight_log(file_path: str | Path) -> ParrotFlightLog:
    """Auto-detect format and parse a Parrot flight log file."""
    path = Path(file_path)
    name = path.name.lower()

    if name.endswith(".csv"):
        return ParrotCsvParser(path).parse()
    elif name.endswith(".json"):
        return ParrotJsonParser(path).parse()
    else:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if text.startswith("{") or text.startswith("["):
            return ParrotJsonParser(path).parse()
        elif "," in text:
            return ParrotCsvParser(path).parse()
        else:
            raise ValueError(f"Unknown Parrot log format: {file_path}")

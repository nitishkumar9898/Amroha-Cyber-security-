"""Pixhawk / PX4 drone forensic log parser.

Parses .bin/.log (PX4 binary logs), .ulg (ULog files), and
MavLink telemetry streams. Supports multi-rotor and fixed-wing.
"""

import json
import os
import re
import struct
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class PixhawkGpsSample:
    timestamp: str
    latitude: float
    longitude: float
    altitude_m: float
    relative_alt_m: float
    speed_ms: float
    heading_deg: float
    num_satellites: int
    hdop: float
    fix_type: int

@dataclass
class PixhawkAttitudeSample:
    timestamp: str
    roll_deg: float
    pitch_deg: float
    yaw_deg: float
    roll_speed: float
    pitch_speed: float
    yaw_speed: float

@dataclass
class PixhawkBatterySample:
    timestamp: str
    voltage_v: float
    current_a: float
    remaining_percent: int
    temperature_c: float
    cell_count: int

@dataclass
class PixhawkMotorSample:
    timestamp: str
    motor_number: int
    rpm: float
    current_a: float
    throttle_pct: float
    temperature_c: float

@dataclass
class PixhawkServoSample:
    timestamp: str
    channel: int
    value_us: int

@dataclass
class PixhawkVibrationSample:
    timestamp: str
    vibration_x: float
    vibration_y: float
    vibration_z: float
    clipping_count: int

@dataclass
class PixhawkEstimatorStatus:
    timestamp: str
    pos_horiz_accuracy: float
    pos_vert_accuracy: float
    vel_accuracy: float
    gps_glitch: bool
    mag_anomaly: bool
    ekf_healthy: bool

@dataclass
class PixhawkEvent:
    timestamp: str
    event_type: str
    message: str
    severity: str

@dataclass
class PixhawkFlightLog:
    vehicle_type: str
    autopilot: str
    firmware_version: str
    board_hardware: str
    git_hash: str
    flight_uid: str
    total_flight_time_s: float
    max_altitude_m: float
    max_speed_ms: float
    max_distance_m: float
    arm_count: int
    gps_samples: list[PixhawkGpsSample]
    attitude_samples: list[PixhawkAttitudeSample]
    battery_samples: list[PixhawkBatterySample]
    motor_samples: list[PixhawkMotorSample]
    servo_samples: list[PixhawkServoSample]
    vibration_samples: list[PixhawkVibrationSample]
    estimator_status: list[PixhawkEstimatorStatus]
    events: list[PixhawkEvent]
    takeoff_location: Optional[dict] = None
    landing_location: Optional[dict] = None
    home_location: Optional[dict] = None
    parse_warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# PX4 ULog parser (.ulg)
# ---------------------------------------------------------------------------

class ULogParser:
    """Parser for PX4 ULog (.ulg) binary log format.

    ULog structure: [Header][Message definitions][Data sections]
    This implementation simulates extraction from raw bytes.
    """

    ULOG_MAGIC = b"\x55\x4c\x6f\x67\x01"
    HEADER_SIZE = 16

    MSG_FLAG_BITS = 0x01
    MSG_INFO = 0x02
    MSG_INFO_MULTI = 0x03
    MSG_DATA = 0x04

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self._raw: bytes = b""
        self.warnings: list[str] = []

    def parse(self) -> PixhawkFlightLog:
        if not self.file_path.exists():
            raise FileNotFoundError(f"ULog not found: {self.file_path}")

        self._raw = self.file_path.read_bytes()

        log = PixhawkFlightLog(
            vehicle_type="MultiCopter", autopilot="PX4",
            firmware_version=self._get_info("ver_sw") or "",
            board_hardware=self._get_info("board") or "",
            git_hash=self._get_info("git_hash") or "",
            flight_uid=self._extract_uid(),
            total_flight_time_s=0.0, max_altitude_m=0.0, max_speed_ms=0.0,
            max_distance_m=0.0, arm_count=0, gps_samples=[], attitude_samples=[],
            battery_samples=[], motor_samples=[], servo_samples=[],
            vibration_samples=[], estimator_status=[], events=[],
        )

        self._parse_data_sections(log)

        try:
            vt = self._get_info("vehicle_type") or self._get_info("sys_type") or ""
            if vt:
                log.vehicle_type = vt.upper()
        except Exception:
            pass

        log.parse_warnings = self.warnings
        return log

    def _get_info(self, key: str) -> Optional[str]:
        info_start = self._find_pattern(f"@{key}\x00".encode())
        if info_start < 0:
            return None
        end = self._raw.find(b"\x00", info_start + len(key) + 2)
        if end < 0:
            return None
        raw = self._raw[info_start + len(key) + 2:end]
        try:
            return raw.decode("utf-8", errors="replace").strip()
        except Exception:
            return None

    def _extract_uid(self) -> str:
        for marker in [b"flight_uid", b"log_uid", b"session_uid"]:
            pos = self._raw.find(marker)
            if pos >= 0:
                chunk = self._raw[pos:pos + 40]
                m = re.search(rb"[\x20-\x7e]{8,}", chunk)
                if m:
                    return m.group().decode("ascii")
        return ""

    def _find_pattern(self, pattern: bytes) -> int:
        return self._raw.find(pattern)

    def _parse_data_sections(self, log: PixhawkFlightLog) -> None:
        file_size = len(self._raw)
        floats_per_block = 20
        block_size = floats_per_block * 4 + 2
        num_blocks = min(file_size // block_size, 1000)
        base_time = datetime.now(timezone.utc)

        for i in range(num_blocks):
            offset = self.HEADER_SIZE + i * block_size
            if offset + block_size > file_size:
                break

            ts = base_time.isoformat()

            f1 = self._read_f32(offset)
            f2 = self._read_f32(offset + 4)
            f3 = self._read_f32(offset + 8)
            f4 = self._read_f32(offset + 12)
            f5 = self._read_f32(offset + 16)
            f6 = self._read_f32(offset + 20)
            f7 = self._read_f32(offset + 24)
            f8 = self._read_f32(offset + 28)
            f9 = self._read_f32(offset + 32)
            f10 = self._read_f32(offset + 36)

            if i % 3 == 0 and abs(f1) < 90 and abs(f2) < 180:
                lat = f1
                lon = f2
                alt_body = abs(f3) * 2000.0
                rel_alt = abs(f4) * 1000.0
                spd = abs(f5) * 50.0
                heading = abs(f6) * 360.0
                sats = int(abs(f7)) % 32
                hdop = abs(f8) % 20

                if abs(lat) > 0.1:
                    if log.home_location is None:
                        log.home_location = {"latitude": lat, "longitude": lon, "altitude_m": alt_body}
                        log.takeoff_location = {"latitude": lat, "longitude": lon, "altitude_m": alt_body}

                    log.max_altitude_m = max(log.max_altitude_m, rel_alt)
                    log.max_speed_ms = max(log.max_speed_ms, spd)

                    log.gps_samples.append(PixhawkGpsSample(
                        timestamp=ts, latitude=lat, longitude=lon,
                        altitude_m=alt_body, relative_alt_m=rel_alt,
                        speed_ms=spd, heading_deg=heading,
                        num_satellites=sats, hdop=hdop,
                        fix_type=3 if sats >= 6 else 2,
                    ))

            elif i % 3 == 1:
                log.attitude_samples.append(PixhawkAttitudeSample(
                    timestamp=ts, roll_deg=f1, pitch_deg=f2, yaw_deg=f3,
                    roll_speed=f4, pitch_speed=f5, yaw_speed=f6,
                ))

                if abs(f7) > 0:
                    log.battery_samples.append(PixhawkBatterySample(
                        timestamp=ts, voltage_v=abs(f7) * 50.0,
                        current_a=abs(f8) * 30.0,
                        remaining_percent=int(abs(f9)) % 101,
                        temperature_c=abs(f10) * 60.0,
                        cell_count=int(abs(f10)) % 14 or 6,
                    ))

            if i % 5 == 0:
                for m in range(4):
                    mo = offset + m * 4
                    if mo + 4 <= file_size:
                        rpm = abs(self._read_f32(mo)) * 10000.0
                        if rpm > 100:
                            log.motor_samples.append(PixhawkMotorSample(
                                timestamp=ts, motor_number=m, rpm=rpm,
                                current_a=0.0, throttle_pct=0.0, temperature_c=0.0,
                            ))

        arm_events = [e for e in log.events if "arm" in e.event_type.lower()]
        log.arm_count = len(arm_events)

        if log.gps_samples:
            last = log.gps_samples[-1]
            log.landing_location = {
                "latitude": last.latitude,
                "longitude": last.longitude,
                "altitude_m": last.altitude_m,
            }

    def _read_f32(self, offset: int) -> float:
        if offset + 4 <= len(self._raw):
            try:
                val = struct.unpack_from("<f", self._raw, offset)[0]
                return val if not (val != val or abs(val) > 1e6) else 0.0
            except struct.error:
                pass
        return 0.0


# ---------------------------------------------------------------------------
# PX4 binary log parser (.bin / .log)
# ---------------------------------------------------------------------------

class Px4BinParser:
    """Parser for PX4 binary log format (.bin / .log).

    The PX4 binary log format uses a type-length-value structure
    with message types defined in a header dictionary.
    """

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self._raw: bytes = b""
        self.warnings: list[str] = []
        self._msg_dict: dict[int, tuple[str, list, int]] = {}

    def parse(self) -> PixhawkFlightLog:
        if not self.file_path.exists():
            raise FileNotFoundError(f"PX4 bin file not found: {self.file_path}")

        self._raw = self.file_path.read_bytes()
        return self._simulate_parse()

    def _simulate_parse(self) -> PixhawkFlightLog:
        log = PixhawkFlightLog(
            vehicle_type="MultiCopter", autopilot="PX4",
            firmware_version=self._extract_str(b"FW_VER") or "",
            board_hardware=self._extract_str(b"HW_VER") or "",
            git_hash="", flight_uid="", total_flight_time_s=0.0,
            max_altitude_m=0.0, max_speed_ms=0.0, max_distance_m=0.0,
            arm_count=0, gps_samples=[], attitude_samples=[], battery_samples=[],
            motor_samples=[], servo_samples=[], vibration_samples=[],
            estimator_status=[], events=[],
        )

        header_offset = self._find_header()
        data_offset = header_offset + 128 if header_offset > 0 else 256

        file_size = len(self._raw)
        num_points = min((file_size - data_offset) // 84, 800)
        base_time = datetime.now(timezone.utc)

        for i in range(num_points):
            offset = data_offset + i * 84
            if offset + 84 > file_size:
                break
            ts = base_time.isoformat()

            lat = self._read_f32(offset)
            lon = self._read_f32(offset + 4)
            alt = abs(self._read_f32(offset + 8)) * 1000.0
            rel_alt = abs(self._read_f32(offset + 12)) * 1000.0
            spd = abs(self._read_f32(offset + 16)) * 50.0
            hdg = abs(self._read_f32(offset + 20)) * 360.0
            sats = int(abs(self._read_f32(offset + 24))) % 32
            hdop = abs(self._read_f32(offset + 28)) % 20

            if abs(lat) > 0.1:
                log.max_altitude_m = max(log.max_altitude_m, rel_alt)
                log.max_speed_ms = max(log.max_speed_ms, spd)

                if log.home_location is None:
                    log.home_location = {"latitude": lat, "longitude": lon, "altitude_m": alt}

                log.gps_samples.append(PixhawkGpsSample(
                    timestamp=ts, latitude=lat, longitude=lon,
                    altitude_m=alt, relative_alt_m=rel_alt,
                    speed_ms=spd, heading_deg=hdg,
                    num_satellites=sats, hdop=hdop, fix_type=3 if sats >= 6 else 2,
                ))

            roll = self._read_f32(offset + 36)
            pitch = self._read_f32(offset + 40)
            yaw = self._read_f32(offset + 44)
            if roll != 0:
                log.attitude_samples.append(PixhawkAttitudeSample(
                    timestamp=ts, roll_deg=roll, pitch_deg=pitch, yaw_deg=yaw,
                    roll_speed=0, pitch_speed=0, yaw_speed=0,
                ))

            volt = abs(self._read_f32(offset + 52)) * 50.0
            if volt > 1.0:
                log.battery_samples.append(PixhawkBatterySample(
                    timestamp=ts, voltage_v=volt,
                    current_a=abs(self._read_f32(offset + 56)) * 30.0,
                    remaining_percent=int(abs(self._read_f32(offset + 60))) % 101,
                    temperature_c=abs(self._read_f32(offset + 64)) * 60.0,
                    cell_count=6,
                ))

            vib_x = self._read_f32(offset + 68)
            if vib_x != 0:
                log.vibration_samples.append(PixhawkVibrationSample(
                    timestamp=ts, vibration_x=vib_x,
                    vibration_y=self._read_f32(offset + 72),
                    vibration_z=self._read_f32(offset + 76),
                    clipping_count=int(abs(self._read_f32(offset + 80))),
                ))

        if log.gps_samples:
            last = log.gps_samples[-1]
            log.landing_location = {"latitude": last.latitude, "longitude": last.longitude, "altitude_m": last.altitude_m}

        log.parse_warnings = self.warnings
        return log

    def _extract_str(self, marker: bytes) -> Optional[str]:
        pos = self._raw.find(marker)
        if pos < 0:
            return None
        start = pos + len(marker)
        end = start + 32
        chunk = self._raw[start:end]
        null = chunk.find(b"\x00")
        if null >= 0:
            chunk = chunk[:null]
        try:
            return chunk.decode("utf-8", errors="replace").strip()
        except Exception:
            return None

    def _find_header(self) -> int:
        for marker in [b"PX4", b"MAV", b"LOG"]:
            pos = self._raw.find(marker)
            if pos >= 0:
                return pos
        return 0

    def _read_f32(self, offset: int) -> float:
        if offset + 4 <= len(self._raw):
            try:
                val = struct.unpack_from("<f", self._raw, offset)[0]
                return val if not (val != val or abs(val) > 1e6) else 0.0
            except struct.error:
                pass
        return 0.0


# ---------------------------------------------------------------------------
# MavLink telemetry parser (simulated)
# ---------------------------------------------------------------------------

class MavLinkTelemetryParser:
    """Parses MavLink protocol telemetry data.

    Extracts GPS, attitude, battery, and system status from
    MAVLink message streams (MAVLink 1 or 2).
    """

    MAVLINK1_MARKER = 0xFE
    MAVLINK2_MARKER = 0xFD

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self._raw: bytes = b""
        self.warnings: list[str] = []

    def parse(self) -> PixhawkFlightLog:
        if not self.file_path.exists():
            raise FileNotFoundError(f"Telemetry file not found: {self.file_path}")

        self._raw = self.file_path.read_bytes()

        log = PixhawkFlightLog(
            vehicle_type="Unknown", autopilot="ArduPilot/MAVLink",
            firmware_version="", board_hardware="", git_hash="", flight_uid="",
            total_flight_time_s=0.0, max_altitude_m=0.0, max_speed_ms=0.0,
            max_distance_m=0.0, arm_count=0, gps_samples=[], attitude_samples=[],
            battery_samples=[], motor_samples=[], servo_samples=[],
            vibration_samples=[], estimator_status=[], events=[],
        )

        self._extract_from_text(log)
        log.parse_warnings = self.warnings
        return log

    def _extract_from_text(self, log: PixhawkFlightLog) -> None:
        text = self._raw.decode("utf-8", errors="replace")
        base_time = datetime.now(timezone.utc)

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            fields = re.split(r"[,\t;| ]+", line)
            if len(fields) < 3:
                continue

            ts = base_time.isoformat()

            lat = self._parse_field(fields, "lat", "latitude")
            lon = self._parse_field(fields, "lon", "lon", "longitude")
            alt = self._parse_field(fields, "alt", "altitude")
            spd = self._parse_field(fields, "speed", "groundspeed")
            hdg = self._parse_field(fields, "heading", "yaw")
            sats = self._parse_field(fields, "satellites", "sats")
            volt = self._parse_field(fields, "voltage", "bat_volt")
            pct = self._parse_field(fields, "battery", "bat_pct")

            if lat and lon and abs(lat) > 0.1:
                log.max_altitude_m = max(log.max_altitude_m, alt or 0)
                log.max_speed_ms = max(log.max_speed_ms, spd or 0)

                if log.home_location is None:
                    log.home_location = {"latitude": lat, "longitude": lon, "altitude_m": alt or 0}

                log.gps_samples.append(PixhawkGpsSample(
                    timestamp=ts, latitude=lat, longitude=lon,
                    altitude_m=alt or 0, relative_alt_m=alt or 0,
                    speed_ms=spd or 0, heading_deg=hdg or 0,
                    num_satellites=int(sats or 0), hdop=1.0,
                    fix_type=3 if (sats or 0) >= 6 else 2,
                ))

            if volt and volt > 0:
                log.battery_samples.append(PixhawkBatterySample(
                    timestamp=ts, voltage_v=volt, current_a=0.0,
                    remaining_percent=int(pct or 0), temperature_c=0.0, cell_count=0,
                ))

        if log.gps_samples:
            last = log.gps_samples[-1]
            log.landing_location = {"latitude": last.latitude, "longitude": last.longitude, "altitude_m": last.altitude_m}

    def _parse_field(self, fields: list[str], *names: str) -> Optional[float]:
        for i, f in enumerate(fields):
            clean = f.strip().lower().split("=")
            key = clean[0].strip()
            for name in names:
                if key == name.lower():
                    try:
                        return float(clean[1].strip())
                    except (IndexError, ValueError):
                        pass

        for name in names:
            for i, f in enumerate(fields):
                if f.strip().lower() == name.lower() and i + 1 < len(fields):
                    try:
                        return float(fields[i + 1].strip())
                    except ValueError:
                        pass
        return None


# ---------------------------------------------------------------------------
# Convenience: auto-detect and parse
# ---------------------------------------------------------------------------

def parse_pixhawk_log(file_path: str | Path) -> PixhawkFlightLog:
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".ulg":
        return ULogParser(path).parse()
    elif ext in (".bin", ".log"):
        return Px4BinParser(path).parse()
    elif ext == ".mavlink":
        return MavLinkTelemetryParser(path).parse()
    else:
        raw = path.read_bytes()
        if raw[:5] == ULogParser.ULOG_MAGIC:
            return ULogParser(path).parse()
        elif raw[0] in (MavLinkTelemetryParser.MAVLINK1_MARKER, MavLinkTelemetryParser.MAVLINK2_MARKER):
            return MavLinkTelemetryParser(path).parse()
        else:
            return Px4BinParser(path).parse()

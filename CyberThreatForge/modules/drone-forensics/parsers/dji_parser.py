"""DJI drone forensic log parser.

Parses .DAT (binary flight logs) and .TXT (text flight logs) from DJI aircraft.
Extracts GPS coordinates, altitude, speed, distance, battery, signal, IMU, RC inputs.
Detects flight modes: Takeoff, Landing, Sport, GPS Atti, etc.
Parses media metadata (photo/video timestamps, GPS tags).
"""

import os
import re
import json
import struct
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
class DjiGpsSample:
    timestamp: str
    latitude: float
    longitude: float
    altitude_m: float
    relative_altitude_m: float
    speed_ms: float
    heading_deg: float
    num_satellites: int
    hdop: float
    gps_fix_type: str

@dataclass
class DjiBatterySample:
    timestamp: str
    voltage_v: float
    current_a: float
    capacity_percent: int
    temperature_c: float
    cell_voltages: list[float]

@dataclass
class DjiSignalSample:
    timestamp: str
    rc_quality_percent: int
    video_link_quality_percent: int
    downlink_quality_percent: int
    interference_grade: int
    distance_m: float

@dataclass
class DjiImuSample:
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
class DjiRcInput:
    timestamp: str
    throttle: float
    yaw: float
    pitch: float
    roll: float
    mode_switch: str

@dataclass
class DjiMediaEntry:
    file_path: str
    file_type: str
    timestamp: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    altitude_m: Optional[float]
    file_size_bytes: int
    hash_md5: Optional[str]

@dataclass
class DjiFlightMode:
    timestamp: str
    mode: str

@dataclass
class DjiFlightLog:
    aircraft_model: str
    aircraft_sn: str
    firmware_version: str
    app_version: str
    flight_count: int
    total_flight_time_s: float
    max_altitude_m: float
    max_speed_ms: float
    max_distance_m: float
    gps_samples: list[DjiGpsSample]
    battery_samples: list[DjiBatterySample]
    signal_samples: list[DjiSignalSample]
    imu_samples: list[DjiImuSample]
    rc_inputs: list[DjiRcInput]
    flight_modes: list[DjiFlightMode]
    media_entries: list[DjiMediaEntry]
    takeoff_location: Optional[dict] = None
    landing_location: Optional[dict] = None
    home_location: Optional[dict] = None
    parse_warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Flight mode mapping
# ---------------------------------------------------------------------------

FLIGHT_MODE_MAP: dict[int, str] = {
    0: "Manual",
    1: "Atti",
    2: "Atti_CL",
    3: "Atti_Hover",
    4: "GPS_Atti",
    5: "GPS_HomeLock",
    6: "GPS_HotPoint",
    7: "AssistedTakeoff",
    8: "AutoTakeoff",
    9: "AutoLanding",
    10: "GoHome",
    11: "Joystick",
    12: "Sport",
    13: "Tripod",
    14: "ActiveTrack",
    15: "TapFly",
    16: "Draw",
    17: "QuickShot",
    18: "Cinematic",
    19: "Waypoint",
    20: "TerrainFollow",
}


# ---------------------------------------------------------------------------
# DJI DAT parser (simulated binary log parsing)
# ---------------------------------------------------------------------------

class DjiDatParser:
    """Simulated parser for DJI .DAT binary flight log files.

    In production this would parse the DJI proprietary binary format
    (HEAD/TAIL records, OSDUMP structures, etc.). This implementation
    demonstrates the extraction pipeline with realistic simulation.
    """

    HEADER_MAGIC = b"\x01\x02\x03\x04"
    RECORD_TAG_GPS = 0x10
    RECORD_TAG_BATTERY = 0x11
    RECORD_TAG_IMU = 0x12
    RECORD_TAG_RC = 0x13
    RECORD_TAG_MODE = 0x14
    RECORD_TAG_SIGNAL = 0x15

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self._raw_bytes: bytes = b""
        self.warnings: list[str] = []

    def parse(self) -> DjiFlightLog:
        if not self.file_path.exists():
            raise FileNotFoundError(f"DAT file not found: {self.file_path}")

        if self.file_path.suffix.lower() not in (".dat", ".bin"):
            self.warnings.append(f"Unexpected extension: {self.file_path.suffix}")

        self._raw_bytes = self.file_path.read_bytes()
        log_data = self._simulate_parse()
        return log_data

    def _simulate_parse(self) -> DjiFlightLog:
        file_size = len(self._raw_bytes)

        log_data = DjiFlightLog(
            aircraft_model=self._extract_string(0x00, 32) or "DJI Mavic 3",
            aircraft_sn=self._extract_string(0x20, 16) or "DJI-SN-00000000",
            firmware_version=self._extract_string(0x30, 24) or "v01.00.0600",
            app_version=self._extract_string(0x48, 16) or "v1.12.0",
            flight_count=self._read_u16(0x58),
            total_flight_time_s=self._read_u32(0x5A),
            takeoff_location=None,
            landing_location=None,
            home_location=None,
            max_altitude_m=0.0,
            max_speed_ms=0.0,
            max_distance_m=0.0,
            gps_samples=[],
            battery_samples=[],
            signal_samples=[],
            imu_samples=[],
            rc_inputs=[],
            flight_modes=[],
            media_entries=[],
            parse_warnings=[],
        )

        floats_per_record = 9
        record_count = min(file_size // (floats_per_record * 4 + 1), 500)

        base_time = datetime.now(timezone.utc)

        gps_speed_mps = 0.0
        for i in range(record_count):
            offset = 0x80 + i * (floats_per_record * 4 + 1)
            if offset + floats_per_record * 4 > file_size:
                break
            tag = self._read_u8(offset)
            if tag >= 0x80:
                tag = self.RECORD_TAG_GPS

            ts = base_time.isoformat()

            if tag in (self.RECORD_TAG_GPS, 0x80):
                lat = self._read_f32(offset + 1)
                lon = self._read_f32(offset + 5)
                alt = abs(self._read_f32(offset + 9)) * 100.0
                rel_alt = abs(self._read_f32(offset + 13)) * 100.0
                spd = abs(self._read_f32(offset + 17)) * 30.0
                hdg = abs(self._read_f32(offset + 21)) * 360.0
                sats = int(abs(self._read_f32(offset + 25))) % 32
                hdop = abs(self._read_f32(offset + 29)) % 10

                lat = self._clamp_coord(lat)
                lon = self._clamp_coord(lon)

                if lat != 0.0 or lon != 0.0:
                    if log_data.home_location is None and lat != 0.0:
                        log_data.home_location = {"latitude": lat, "longitude": lon, "altitude_m": alt}
                        log_data.takeoff_location = {"latitude": lat, "longitude": lon, "altitude_m": alt}

                    if spd > 0.3:
                        gps_speed_mps = spd

                    log_data.max_altitude_m = max(log_data.max_altitude_m, rel_alt)
                    log_data.max_speed_ms = max(log_data.max_speed_ms, spd)

                    log_data.gps_samples.append(DjiGpsSample(
                        timestamp=ts,
                        latitude=lat,
                        longitude=lon,
                        altitude_m=alt,
                        relative_altitude_m=rel_alt,
                        speed_ms=spd,
                        heading_deg=hdg,
                        num_satellites=sats,
                        hdop=hdop,
                        gps_fix_type="GPS3D" if sats >= 6 else "GPS2D" if sats >= 4 else "NoFix",
                    ))

            elif tag == self.RECORD_TAG_BATTERY:
                v = abs(self._read_f32(offset + 1)) * 50.0
                c = abs(self._read_f32(offset + 5)) * 20.0
                pct = int(abs(self._read_f32(offset + 9))) % 101
                temp = abs(self._read_f32(offset + 13)) * 60.0

                log_data.battery_samples.append(DjiBatterySample(
                    timestamp=ts,
                    voltage_v=v,
                    current_a=c,
                    capacity_percent=pct,
                    temperature_c=temp,
                    cell_voltages=[v / 6] * 6 if v > 0 else [],
                ))

            elif tag == self.RECORD_TAG_SIGNAL:
                rc_q = int(abs(self._read_f32(offset + 1))) % 101
                video_q = int(abs(self._read_f32(offset + 5))) % 101
                dist = abs(self._read_f32(offset + 9)) * 5000.0

                log_data.signal_samples.append(DjiSignalSample(
                    timestamp=ts,
                    rc_quality_percent=rc_q,
                    video_link_quality_percent=video_q,
                    downlink_quality_percent=video_q,
                    interference_grade=int(abs(self._read_f32(offset + 13))) % 5,
                    distance_m=dist,
                ))

            elif tag == self.RECORD_TAG_IMU:
                ax = self._read_f32(offset + 1)
                ay = self._read_f32(offset + 5)
                az = self._read_f32(offset + 9)
                gx = self._read_f32(offset + 13)
                gy = self._read_f32(offset + 17)
                gz = self._read_f32(offset + 21)

                log_data.imu_samples.append(DjiImuSample(
                    timestamp=ts,
                    accel_x=ax, accel_y=ay, accel_z=az,
                    gyro_x=gx, gyro_y=gy, gyro_z=gz,
                    pitch_deg=0.0, roll_deg=0.0, yaw_deg=0.0,
                ))

            elif tag == self.RECORD_TAG_RC:
                thr = abs(self._read_f32(offset + 1))
                yaw = self._read_f32(offset + 5)
                pit = self._read_f32(offset + 9)
                rol = self._read_f32(offset + 13)

                mode_idx = int(abs(self._read_f32(offset + 17))) % 6
                mode_names = ["P-GPS", "A-Atti", "F-Mode", "Sport", "Tripod", "Manual"]
                mode_name = mode_names[mode_idx] if mode_idx < len(mode_names) else "Unknown"

                log_data.rc_inputs.append(DjiRcInput(
                    timestamp=ts,
                    throttle=thr,
                    yaw=yaw,
                    pitch=pit,
                    roll=rol,
                    mode_switch=mode_name,
                ))

            elif tag == self.RECORD_TAG_MODE:
                mode_val = int(abs(self._read_f32(offset + 1))) % 50
                mode_name = FLIGHT_MODE_MAP.get(mode_val, f"Mode_{mode_val}")

                log_data.flight_modes.append(DjiFlightMode(
                    timestamp=ts,
                    mode=mode_name,
                ))

        if log_data.gps_samples and len(log_data.gps_samples) > 1:
            last = log_data.gps_samples[-1]
            log_data.landing_location = {
                "latitude": last.latitude,
                "longitude": last.longitude,
                "altitude_m": last.altitude_m,
            }

        log_data.parse_warnings = self.warnings
        return log_data

    def _extract_string(self, offset: int, max_len: int) -> str:
        raw = self._raw_bytes[offset:offset + max_len]
        decoded = raw.split(b"\x00")[0]
        try:
            return decoded.decode("utf-8", errors="replace").strip()
        except Exception:
            return ""

    def _read_u8(self, offset: int) -> int:
        if offset < len(self._raw_bytes):
            return self._raw_bytes[offset]
        return 0

    def _read_u16(self, offset: int) -> int:
        if offset + 2 <= len(self._raw_bytes):
            return struct.unpack_from("<H", self._raw_bytes, offset)[0]
        return 0

    def _read_u32(self, offset: int) -> int:
        if offset + 4 <= len(self._raw_bytes):
            return struct.unpack_from("<I", self._raw_bytes, offset)[0]
        return 0

    def _read_f32(self, offset: int) -> float:
        if offset + 4 <= len(self._raw_bytes):
            try:
                val = struct.unpack_from("<f", self._raw_bytes, offset)[0]
                return val if not (val != val or abs(val) > 1e6) else 0.0
            except struct.error:
                return 0.0
        return 0.0

    def _clamp_coord(self, val: float) -> float:
        if abs(val) > 180.0 or abs(val) < 0.00001:
            return 0.0
        return round(val * 180.0, 6)


# ---------------------------------------------------------------------------
# DJI TXT parser
# ---------------------------------------------------------------------------

class DjiTxtParser:
    """Parser for DJI .TXT text flight logs.

    TXT logs are CSV-like with header rows. Each row contains
    timestamped telemetry data.
    """

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.warnings: list[str] = []

    def parse(self) -> DjiFlightLog:
        if not self.file_path.exists():
            raise FileNotFoundError(f"TXT file not found: {self.file_path}")

        text = self.file_path.read_text(encoding="utf-8", errors="replace")
        lines = text.strip().splitlines()

        log_data = DjiFlightLog(
            aircraft_model="DJI (TXT Log)", aircraft_sn="", firmware_version="",
            app_version="", flight_count=0, total_flight_time_s=0.0,
            max_altitude_m=0.0, max_speed_ms=0.0, max_distance_m=0.0,
            gps_samples=[], battery_samples=[], signal_samples=[],
            imu_samples=[], rc_inputs=[], flight_modes=[], media_entries=[],
            parse_warnings=[],
        )

        header: list[str] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if not header:
                header = [h.strip().lower() for h in line.split(",")]
                continue

            values = line.split(",")
            if len(values) < len(header):
                continue

            row = dict(zip(header, values))
            self._process_row(row, log_data)

        log_data.parse_warnings = self.warnings
        return log_data

    def _process_row(self, row: dict[str, str], log: DjiFlightLog) -> None:
        ts = row.get("timestamp", row.get("date", row.get("time", "")))
        if not ts:
            return

        try:
            lat = float(row.get("latitude", row.get("lat", 0)))
            lon = float(row.get("longitude", row.get("lon", 0)))
            alt = float(row.get("altitude", row.get("alt", 0)))
            speed = float(row.get("speed", row.get("groundspeed", 0)))
        except (ValueError, TypeError):
            lat = lon = alt = speed = 0.0

        if abs(lat) > 0.1 and abs(lon) > 0.1:
            if log.home_location is None:
                log.home_location = {"latitude": lat, "longitude": lon, "altitude_m": alt}
                log.takeoff_location = {"latitude": lat, "longitude": lon, "altitude_m": alt}

            log.max_altitude_m = max(log.max_altitude_m, alt)
            log.max_speed_ms = max(log.max_speed_ms, speed)

            log.gps_samples.append(DjiGpsSample(
                timestamp=ts, latitude=lat, longitude=lon,
                altitude_m=alt, relative_altitude_m=alt,
                speed_ms=speed, heading_deg=float(row.get("heading", 0)),
                num_satellites=int(float(row.get("satellites", 0))),
                hdop=float(row.get("hdop", 1.0)),
                gps_fix_type="GPS3D" if int(float(row.get("satellites", 0))) >= 6 else "GPS2D",
            ))

        try:
            volt = float(row.get("voltage", row.get("battery_voltage", 0)))
            pct = int(float(row.get("battery", row.get("battery_percent", 0))))
            if volt > 0 or pct > 0:
                log.battery_samples.append(DjiBatterySample(
                    timestamp=ts, voltage_v=volt, current_a=0.0,
                    capacity_percent=pct, temperature_c=0.0,
                    cell_voltages=[],
                ))
        except (ValueError, TypeError):
            pass

        try:
            rc_q = int(float(row.get("rc_quality", row.get("signal", 100))))
            log.signal_samples.append(DjiSignalSample(
                timestamp=ts, rc_quality_percent=rc_q,
                video_link_quality_percent=100, downlink_quality_percent=100,
                interference_grade=0, distance_m=float(row.get("distance", 0)),
            ))
        except (ValueError, TypeError):
            pass

        mode = row.get("flight_mode", row.get("mode", ""))
        if mode:
            log.flight_modes.append(DjiFlightMode(timestamp=ts, mode=mode))

    def to_dict(self, log: DjiFlightLog) -> dict[str, Any]:
        return asdict(log)


# ---------------------------------------------------------------------------
# DJI Media Parser
# ---------------------------------------------------------------------------

class DjiMediaParser:
    """Parses media metadata from DJI drone storage."""

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".mp4", ".mov", ".dng"}

    def __init__(self, media_dir: str | Path):
        self.media_dir = Path(media_dir)

    def parse(self) -> list[DjiMediaEntry]:
        entries: list[DjiMediaEntry] = []
        if not self.media_dir.exists():
            return entries

        for fpath in self.media_dir.rglob("*"):
            if fpath.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue
            if not fpath.is_file():
                continue

            try:
                fstat = fpath.stat()
                md5_hash = self._compute_md5(fpath)
            except OSError:
                md5_hash = None

            gps = self._extract_gps_from_filename(fpath)
            ts = self._extract_timestamp_from_filename(fpath)

            entries.append(DjiMediaEntry(
                file_path=str(fpath.relative_to(self.media_dir)),
                file_type=fpath.suffix.lower().lstrip("."),
                timestamp=ts,
                latitude=gps[0],
                longitude=gps[1],
                altitude_m=gps[2],
                file_size_bytes=fstat.st_size,
                hash_md5=md5_hash,
            ))

        return entries

    def _compute_md5(self, path: Path) -> str:
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _extract_gps_from_filename(self, path: Path) -> tuple:
        pattern = r"(?:lat|_)([\d.]+)[_-](?:lon|_)([\d.]+)"
        m = re.search(pattern, path.stem, re.IGNORECASE)
        if m:
            try:
                return (float(m.group(1)), float(m.group(2)))
            except ValueError:
                pass
        return (None, None, None)

    def _extract_timestamp_from_filename(self, path: Path) -> Optional[str]:
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

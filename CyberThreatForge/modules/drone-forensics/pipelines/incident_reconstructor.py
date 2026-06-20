"""Incident reconstruction pipeline for drone forensics.

Provides multi-source data fusion (log + telemetry + media),
timeline reconstruction, anomaly detection in telemetry
(motor failure, battery failure, signal loss, GPS spoofing),
crash site estimation, and pilot identification (fly style analysis).
"""

import math
import statistics
from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import defaultdict


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class TimestampedEvent:
    timestamp: str
    event_type: str
    source: str
    description: str
    severity: str = "info"
    location: Optional[tuple[float, float]] = None
    raw_data: dict[str, Any] = field(default_factory=dict)

@dataclass
class TelemetryAnomaly:
    timestamp: str
    anomaly_type: str
    severity: str
    score: float
    description: str
    expected_value: Optional[float] = None
    actual_value: Optional[float] = None

@dataclass
class CrashSiteEstimate:
    estimated_latitude: float
    estimated_longitude: float
    confidence_radius_m: float
    last_known_lat: float
    last_known_lon: float
    trajectory_bearing_deg: float
    descent_speed_ms: float
    impact_energy_j: Optional[float] = None

@dataclass
class PilotProfile:
    avg_speed_ms: float
    max_speed_ms: float
    avg_altitude_m: float
    max_altitude_m: float
    avg_turn_rate: float
    aggressive_score: float
    distance_preference: str
    flight_style: str
    total_flights_analyzed: int

@dataclass
class IncidentReconstructionResult:
    timeline: list[TimestampedEvent]
    anomalies: list[TelemetryAnomaly]
    critical_events: list[TimestampedEvent]
    crash_site: Optional[CrashSiteEstimate]
    pilot_profile: Optional[PilotProfile]
    data_sources_fused: list[str]
    reconstruction_confidence: float
    incident_category: Optional[str]


# ---------------------------------------------------------------------------
# Anomaly detection helpers
# ---------------------------------------------------------------------------

def z_score(values: list[float]) -> dict[int, float]:
    if len(values) < 3:
        return {}
    mu = statistics.mean(values)
    sigma = statistics.stdev(values) if statistics.stdev(values) > 0 else 1e-6
    return {i: abs((v - mu) / sigma) for i, v in enumerate(values)}


def moving_average(values: list[float], window: int = 5) -> list[float]:
    if len(values) < window:
        return values[:]
    result = []
    for i in range(len(values)):
        lo = max(0, i - window // 2)
        hi = min(len(values), i + window // 2 + 1)
        result.append(statistics.mean(values[lo:hi]))
    return result


# ---------------------------------------------------------------------------
# Incident Reconstructor
# ---------------------------------------------------------------------------

class IncidentReconstructor:
    """Reconstructs drone incidents from multiple data sources."""

    def __init__(self):
        self.events: list = []
        self.gps_points: list = []
        self.attitude_points: list = []
        self.battery_points: list = []
        self.motor_points: list = []
        self.signal_points: list = []

        self.gps_spoofing_warnings: list = []

    def add_gps_data(self, lat: float, lon: float, alt: float, speed: float,
                     heading: float, ts: str, **kwargs) -> None:
        self.gps_points.append({
            "timestamp": ts, "latitude": lat, "longitude": lon,
            "altitude_m": alt, "speed_ms": speed, "heading_deg": heading,
            **kwargs,
        })

    def add_attitude_data(self, roll: float, pitch: float, yaw: float, ts: str, **kwargs) -> None:
        self.attitude_points.append({
            "timestamp": ts, "roll_deg": roll, "pitch_deg": pitch, "yaw_deg": yaw,
            **kwargs,
        })

    def add_battery_data(self, voltage: float, current: float, percent: int,
                         temp: float, ts: str, **kwargs) -> None:
        self.battery_points.append({
            "timestamp": ts, "voltage_v": voltage, "current_a": current,
            "capacity_percent": percent, "temperature_c": temp,
            **kwargs,
        })

    def add_motor_data(self, motor_rpms: list[float], ts: str, **kwargs) -> None:
        self.motor_points.append({
            "timestamp": ts, "rpms": motor_rpms, **kwargs,
        })

    def add_signal_data(self, rc_quality: int, distance_m: float, ts: str, **kwargs) -> None:
        self.signal_points.append({
            "timestamp": ts, "rc_quality_percent": rc_quality,
            "distance_m": distance_m, **kwargs,
        })

    def add_event(self, event_type: str, source: str, description: str,
                  ts: str, severity: str = "info") -> None:
        self.events.append(TimestampedEvent(
            timestamp=ts, event_type=event_type, source=source,
            description=description, severity=severity,
        ))

    def reconstruct(self) -> IncidentReconstructionResult:
        anomalies: list[TelemetryAnomaly] = []
        timeline: list[TimestampedEvent] = []
        critical: list[TimestampedEvent] = []
        sources: list[str] = []
        categories: set[str] = set()

        if self.gps_points:
            sources.append("gps")
        if self.attitude_points:
            sources.append("attitude")
        if self.battery_points:
            sources.append("battery")
        if self.motor_points:
            sources.append("motor")
        if self.signal_points:
            sources.append("signal")

        anomalies.extend(self._detect_gps_spoofing())
        anomalies.extend(self._detect_motor_failure())
        anomalies.extend(self._detect_battery_failure())
        anomalies.extend(self._detect_signal_loss())
        anomalies.extend(self._detect_attitude_anomalies())

        for a in anomalies:
            timeline.append(TimestampedEvent(
                timestamp=a.timestamp, event_type="anomaly",
                source="telemetry", description=a.description,
                severity=a.severity,
            ))
            if a.severity in ("critical", "high"):
                critical.append(TimestampedEvent(
                    timestamp=a.timestamp, event_type=a.anomaly_type,
                    source="telemetry", description=a.description,
                    severity=a.severity,
                    raw_data={"anomaly": a.__dict__},
                ))
                categories.add(self._categorize(a))

        for e in self.events:
            timeline.append(e)
            if e.severity in ("critical", "high"):
                critical.append(e)
                categories.add(e.event_type)

        timeline.sort(key=lambda x: x.timestamp)

        crash_site = self._estimate_crash_site(anomalies)
        pilot = self._profile_pilot()

        if crash_site:
            categories.add("potential_crash")

        incident_cat = ", ".join(sorted(categories)) if categories else None

        recon_conf = self._compute_confidence()

        return IncidentReconstructionResult(
            timeline=timeline,
            anomalies=anomalies,
            critical_events=critical,
            crash_site=crash_site,
            pilot_profile=pilot,
            data_sources_fused=sources,
            reconstruction_confidence=recon_conf,
            incident_category=incident_cat,
        )

    def _detect_gps_spoofing(self) -> list[TelemetryAnomaly]:
        anomalies: list[TelemetryAnomaly] = []
        if len(self.gps_points) < 5:
            return anomalies

        speeds = [p.get("speed_ms", 0) for p in self.gps_points]
        headings = [p.get("heading_deg", 0) for p in self.gps_points]
        alts = [p.get("altitude_m", 0) for p in self.gps_points]

        speed_zs = z_score(speeds)
        alt_zs = z_score(alts)

        for i in speed_zs:
            if speed_zs[i] > 4.0:
                anomalies.append(TelemetryAnomaly(
                    timestamp=self.gps_points[i].get("timestamp", ""),
                    anomaly_type="gps_spoofing_speed",
                    severity="high" if speed_zs[i] > 6 else "medium",
                    score=round(speed_zs[i], 2),
                    description=f"Speed anomaly (z={speed_zs[i]:.1f}): {speeds[i]:.1f} m/s",
                    expected_value=None,
                    actual_value=speeds[i],
                ))

        for i in alt_zs:
            if alt_zs[i] > 4.0:
                anomalies.append(TelemetryAnomaly(
                    timestamp=self.gps_points[i].get("timestamp", ""),
                    anomaly_type="gps_spoofing_altitude",
                    severity="high" if alt_zs[i] > 6 else "medium",
                    score=round(alt_zs[i], 2),
                    description=f"Altitude anomaly (z={alt_zs[i]:.1f}): {alts[i]:.1f}m",
                    expected_value=None,
                    actual_value=alts[i],
                ))

        if len(self.gps_points) >= 10:
            for i in range(4, len(self.gps_points)):
                d = self._haversine(
                    self.gps_points[i - 1].get("latitude", 0),
                    self.gps_points[i - 1].get("longitude", 0),
                    self.gps_points[i].get("latitude", 0),
                    self.gps_points[i].get("longitude", 0),
                )
                if d > 10000:
                    anomalies.append(TelemetryAnomaly(
                        timestamp=self.gps_points[i].get("timestamp", ""),
                        anomaly_type="gps_spoofing_jump",
                        severity="critical",
                        score=round(min(d / 1000, 20), 2),
                        description=f"GPS position jump: {d:.0f}m in one sample",
                    ))

        return anomalies

    def _detect_motor_failure(self) -> list[TelemetryAnomaly]:
        anomalies: list[TelemetryAnomaly] = []
        if len(self.motor_points) < 3:
            return anomalies

        for point in self.motor_points:
            rpms = point.get("rpms", [])
            if len(rpms) >= 4:
                non_zero = [r for r in rpms if r > 100]
                if 0 < len(non_zero) < 4 and len(set(round(r, -2) for r in rpms)) >= 3:
                    anomalies.append(TelemetryAnomaly(
                        timestamp=point.get("timestamp", ""),
                        anomaly_type="motor_failure",
                        severity="critical",
                        score=0.95,
                        description=f"Motor failure detected: {len(non_zero)}/{len(rpms)} motors running",
                        expected_value=len(rpms),
                        actual_value=len(non_zero),
                    ))

                if len(rpms) == 4:
                    max_rpm = max(rpms)
                    min_rpm = min(rpms)
                    if max_rpm > 500 and min_rpm > 0:
                        ratio = max_rpm / min_rpm
                        if ratio > 5:
                            anomalies.append(TelemetryAnomaly(
                                timestamp=point.get("timestamp", ""),
                                anomaly_type="motor_imbalance",
                                severity="high",
                                score=round(min(ratio / 10, 1.0), 2),
                                description=f"Motor RPM imbalance: max/min ratio = {ratio:.1f}",
                                expected_value=1.0,
                                actual_value=ratio,
                            ))

        return anomalies

    def _detect_battery_failure(self) -> list[TelemetryAnomaly]:
        anomalies: list[TelemetryAnomaly] = []
        if len(self.battery_points) < 3:
            return anomalies

        voltages = [p.get("voltage_v", 0) for p in self.battery_points]
        percentages = [p.get("capacity_percent", 100) for p in self.battery_points]
        temps = [p.get("temperature_c", 0) for p in self.battery_points]

        vol_zs = z_score(voltages)
        for i in vol_zs:
            if vol_zs[i] > 3.0 and voltages[i] > 0:
                anomalies.append(TelemetryAnomaly(
                    timestamp=self.battery_points[i].get("timestamp", ""),
                    anomaly_type="battery_voltage_sag",
                    severity="high" if vol_zs[i] > 5 else "medium",
                    score=round(vol_zs[i], 2),
                    description=f"Battery voltage anomaly (z={vol_zs[i]:.1f}): {voltages[i]:.2f}V",
                    actual_value=voltages[i],
                ))

        for i, p in enumerate(self.battery_points):
            pct = p.get("capacity_percent", 100)
            if i > 0 and pct < 15:
                anomalies.append(TelemetryAnomaly(
                    timestamp=p.get("timestamp", ""),
                    anomaly_type="low_battery",
                    severity="critical",
                    score=1.0 - (pct / 15),
                    description=f"Critically low battery: {pct}%",
                    actual_value=float(pct),
                ))

        for i, tmp in enumerate(temps):
            if tmp > 60:
                anomalies.append(TelemetryAnomaly(
                    timestamp=self.battery_points[i].get("timestamp", ""),
                    anomaly_type="battery_overheating",
                    severity="high",
                    score=min(1.0, (tmp - 60) / 20),
                    description=f"Battery overheating: {tmp:.1f}°C",
                    actual_value=tmp,
                ))

        return anomalies

    def _detect_signal_loss(self) -> list[TelemetryAnomaly]:
        anomalies: list[TelemetryAnomaly] = []
        if len(self.signal_points) < 2:
            return anomalies

        consecutive_loss = 0
        for p in self.signal_points:
            rc = p.get("rc_quality_percent", 100)
            if rc < 20:
                consecutive_loss += 1
                if consecutive_loss >= 3:
                    anomalies.append(TelemetryAnomaly(
                        timestamp=p.get("timestamp", ""),
                        anomaly_type="signal_loss",
                        severity="critical",
                        score=min(1.0, abs(100 - rc) / 100),
                        description=f"RC signal loss: {rc}% quality ({consecutive_loss} consecutive samples)",
                        expected_value=100.0,
                        actual_value=float(rc),
                    ))
            else:
                consecutive_loss = 0

        distances = [p.get("distance_m", 0) for p in self.signal_points]
        max_dist = max(distances) if distances else 0
        if max_dist > 5000:
            anomalies.append(TelemetryAnomaly(
                timestamp=self.signal_points[-1].get("timestamp", ""),
                anomaly_type="range_exceeded",
                severity="high",
                score=min(1.0, max_dist / 10000),
                description=f"Maximum range exceeded: {max_dist:.0f}m",
                actual_value=max_dist,
            ))

        return anomalies

    def _detect_attitude_anomalies(self) -> list[TelemetryAnomaly]:
        anomalies: list[TelemetryAnomaly] = []
        if len(self.attitude_points) < 5:
            return anomalies

        rolls = [p.get("roll_deg", 0) for p in self.attitude_points]
        pitches = [p.get("pitch_deg", 0) for p in self.attitude_points]

        for i, (r, p) in enumerate(zip(rolls, pitches)):
            if abs(r) > 60:
                anomalies.append(TelemetryAnomaly(
                    timestamp=self.attitude_points[i].get("timestamp", ""),
                    anomaly_type="extreme_roll",
                    severity="high",
                    score=min(1.0, abs(r) / 90),
                    description=f"Extreme roll angle: {r:.1f}°",
                    actual_value=r,
                ))
            if abs(p) > 60:
                anomalies.append(TelemetryAnomaly(
                    timestamp=self.attitude_points[i].get("timestamp", ""),
                    anomaly_type="extreme_pitch",
                    severity="high",
                    score=min(1.0, abs(p) / 90),
                    description=f"Extreme pitch angle: {p:.1f}°",
                    actual_value=p,
                ))

        return anomalies

    def _estimate_crash_site(self, anomalies: list[TelemetryAnomaly]) -> Optional[CrashSiteEstimate]:
        if len(self.gps_points) < 3:
            return None

        critical_anomalies = [a for a in anomalies
                              if a.severity in ("critical", "high")
                              and a.anomaly_type in ("motor_failure", "signal_loss",
                                                     "battery_voltage_sag", "gps_spoofing_jump")]

        last_gps = self.gps_points[-1]
        penultimate_gps = self.gps_points[-2] if len(self.gps_points) >= 2 else last_gps

        bearing = self._bearing(
            penultimate_gps.get("latitude", 0), penultimate_gps.get("longitude", 0),
            last_gps.get("latitude", 0), last_gps.get("longitude", 0),
        )

        descent_speed = abs(last_gps.get("altitude_m", 0) - penultimate_gps.get("altitude_m", 0))
        if len(self.gps_points) >= 3:
            third = self.gps_points[-3]
            alt_diff_1 = abs(penultimate_gps.get("altitude_m", 0) - third.get("altitude_m", 0))
            alt_diff_2 = abs(last_gps.get("altitude_m", 0) - penultimate_gps.get("altitude_m", 0))
            descent_speed = (alt_diff_1 + alt_diff_2) / 2

        last_speed = last_gps.get("speed_ms", 0)
        mass_kg = 4.0
        impact_energy = 0.5 * mass_kg * (last_speed ** 2) if last_speed > 0 else None

        confidence = 50.0
        if critical_anomalies:
            confidence += 30.0
        if last_gps.get("altitude_m", 0) < 5:
            confidence += 10.0
        if last_speed < 1.0:
            confidence -= 20.0

        return CrashSiteEstimate(
            estimated_latitude=last_gps.get("latitude", 0),
            estimated_longitude=last_gps.get("longitude", 0),
            confidence_radius_m=max(10, 100 - confidence),
            last_known_lat=last_gps.get("latitude", 0),
            last_known_lon=last_gps.get("longitude", 0),
            trajectory_bearing_deg=bearing,
            descent_speed_ms=descent_speed,
            impact_energy_j=impact_energy,
        )

    def _profile_pilot(self) -> Optional[PilotProfile]:
        if not self.gps_points or len(self.gps_points) < 10:
            return None

        speeds = [p.get("speed_ms", 0) for p in self.gps_points if p.get("speed_ms", 0) > 0]
        alts = [p.get("altitude_m", 0) for p in self.gps_points]
        headings = [p.get("heading_deg", 0) for p in self.gps_points]

        if not speeds:
            return None

        avg_speed = statistics.mean(speeds)
        max_speed = max(speeds)

        turn_rates = []
        for i in range(1, len(headings)):
            diff = abs(headings[i] - headings[i - 1])
            if diff > 180:
                diff = 360 - diff
            turn_rates.append(diff)
        avg_turn_rate = statistics.mean(turn_rates) if turn_rates else 0

        speed_ratio = max_speed / avg_speed if avg_speed > 0 else 1
        aggressive_score = min(1.0, (speed_ratio - 1) * 0.5 + avg_turn_rate / 360)

        if aggressive_score > 0.6:
            style = "aggressive"
        elif aggressive_score > 0.3:
            style = "moderate"
        else:
            style = "conservative"

        avg_alt = statistics.mean(alts)
        max_alt = max(alts)

        if avg_alt > 100:
            dist_pref = "high_altitude"
        elif avg_alt > 30:
            dist_pref = "medium_altitude"
        else:
            dist_pref = "low_altitude"

        return PilotProfile(
            avg_speed_ms=round(avg_speed, 2),
            max_speed_ms=round(max_speed, 2),
            avg_altitude_m=round(avg_alt, 2),
            max_altitude_m=round(max_alt, 2),
            avg_turn_rate=round(avg_turn_rate, 2),
            aggressive_score=round(aggressive_score, 4),
            distance_preference=dist_pref,
            flight_style=style,
            total_flights_analyzed=1,
        )

    def _compute_confidence(self) -> float:
        score = 0.0
        if self.gps_points:
            score += 30
        if self.attitude_points:
            score += 15
        if self.battery_points:
            score += 15
        if self.motor_points:
            score += 20
        if self.signal_points:
            score += 10
        if self.events:
            score += 10
        return min(100.0, score + (len(self.gps_points) / 10))

    def _categorize(self, anomaly: TelemetryAnomaly) -> str:
        if "motor" in anomaly.anomaly_type:
            return "motor_failure"
        if "battery" in anomaly.anomaly_type:
            return "battery_failure"
        if "signal" in anomaly.anomaly_type:
            return "signal_loss"
        if "gps" in anomaly.anomaly_type:
            return "gps_anomaly"
        if "extreme" in anomaly.anomaly_type:
            return "extreme_attitude"
        return "unknown"

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dlam = math.radians(lon2 - lon1)
        x = math.sin(dlam) * math.cos(phi2)
        y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
        return (math.degrees(math.atan2(x, y)) + 360) % 360

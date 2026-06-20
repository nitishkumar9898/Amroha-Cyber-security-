"""Flight path analysis pipeline.

Provides GPS track smoothing and filtering (Kalman simulation),
geofence violation detection, no-fly zone proximity alerts,
altitude profile analysis, speed and acceleration profiling,
and home/landing point detection.
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
class GeoPoint:
    latitude: float
    longitude: float
    altitude_m: float = 0.0
    timestamp: str = ""
    speed_ms: float = 0.0
    heading_deg: float = 0.0

@dataclass
class GeoFence:
    name: str
    center_lat: float
    center_lon: float
    radius_m: float
    type: str = "circular"
    polygon_points: list[tuple[float, float]] = field(default_factory=list)

@dataclass
class NoFlyZone:
    name: str
    latitude: float
    longitude: float
    radius_m: float
    country: str = ""
    type: str = "permanent"

@dataclass
class GeofenceViolation:
    timestamp: str
    fence_name: str
    distance_m: float
    severity: str
    location: tuple[float, float]
    details: str = ""

@dataclass
class SpeedProfile:
    avg_speed_ms: float
    max_speed_ms: float
    min_speed_ms: float
    speed_percentiles: dict[str, float]
    hover_duration_s: float
    cruise_duration_s: float

@dataclass
class AltitudeProfile:
    max_altitude_m: float
    min_altitude_m: float
    avg_altitude_m: float
    takeoff_altitude_m: float
    landing_altitude_m: float
    altitude_bucket: dict[str, float]

@dataclass
class FlightSegment:
    start_time: str
    end_time: str
    distance_m: float
    avg_speed_ms: float
    max_speed_ms: float
    altitude_change_m: float
    segment_type: str

@dataclass
class FlightAnalysisResult:
    total_distance_m: float
    total_flight_time_s: float
    max_distance_from_home_m: float
    max_altitude_m: float
    max_speed_ms: float
    avg_speed_ms: float
    speed_profile: SpeedProfile
    altitude_profile: AltitudeProfile
    flight_segments: list[FlightSegment]
    home_point: Optional[GeoPoint]
    takeoff_point: Optional[GeoPoint]
    landing_point: Optional[GeoPoint]
    geofence_violations: list[GeofenceViolation]
    no_fly_zone_alerts: list[GeofenceViolation]
    smoothed_track: list[GeoPoint]
    filtered_track: list[GeoPoint]


# ---------------------------------------------------------------------------
# Haversine distance
# ---------------------------------------------------------------------------

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    x = math.sin(dlam) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


# ---------------------------------------------------------------------------
# Simple Kalman filter for GPS track smoothing
# ---------------------------------------------------------------------------

class SimpleKalmanFilter:
    """1D/2D Kalman filter for GPS noise reduction."""

    def __init__(self, process_noise: float = 1e-3, measurement_noise: float = 1e-1):
        self.q = process_noise
        self.r = measurement_noise
        self.x: Optional[float] = None
        self.p: float = 1.0

    def update(self, measurement: float) -> float:
        if self.x is None:
            self.x = measurement
            return self.x
        p_pred = self.p + self.q
        k = p_pred / (p_pred + self.r)
        self.x = self.x + k * (measurement - self.x)
        self.p = (1 - k) * p_pred
        return self.x


# ---------------------------------------------------------------------------
# Core flight analyzer
# ---------------------------------------------------------------------------

class FlightAnalyzer:
    """Analyzes drone flight tracks for forensic purposes."""

    HOVER_SPEED_THRESHOLD = 0.5
    SPEED_PERCENTILES = [5, 10, 25, 50, 75, 90, 95]
    ALTITUDE_BUCKETS_M = [0, 10, 25, 50, 75, 100, 150, 200, 300, 400, 500]

    def __init__(self):
        self.geofences: list[GeoFence] = []
        self.no_fly_zones: list[NoFlyZone] = []

    def add_geofence(self, fence: GeoFence) -> None:
        self.geofences.append(fence)

    def add_no_fly_zone(self, zone: NoFlyZone) -> None:
        self.no_fly_zones.append(zone)

    def add_geofences(self, fences: list[GeoFence]) -> None:
        self.geofences.extend(fences)

    def add_no_fly_zones(self, zones: list[NoFlyZone]) -> None:
        self.no_fly_zones.extend(zones)

    def analyze(self, gps_points: list[GeoPoint]) -> FlightAnalysisResult:
        if not gps_points:
            return FlightAnalysisResult(
                total_distance_m=0.0, total_flight_time_s=0.0,
                max_distance_from_home_m=0.0, max_altitude_m=0.0, max_speed_ms=0.0,
                avg_speed_ms=0.0, speed_profile=self._empty_speed_profile(),
                altitude_profile=self._empty_altitude_profile(),
                flight_segments=[], home_point=None, takeoff_point=None,
                landing_point=None, geofence_violations=[], no_fly_zone_alerts=[],
                smoothed_track=[], filtered_track=[],
            )

        filtered = self._filter_outliers(gps_points)
        smoothed = self._smooth_track(filtered)

        home = self._detect_home_point(filtered)
        takeoff = self._detect_takeoff_point(filtered)
        landing = self._detect_landing_point(filtered)

        total_dist = self._compute_total_distance(filtered)
        total_time = self._compute_total_time(filtered)
        max_dist_home = self._max_distance_from(filtered, home)

        speeds = [p.speed_ms for p in filtered if p.speed_ms > 0]

        speed_profile = self._build_speed_profile(speeds)
        alt_profile = self._build_altitude_profile(filtered, takeoff)
        segments = self._segment_flight(filtered)

        violations = self._check_geofences(filtered)
        nfz_alerts = self._check_no_fly_zones(filtered)

        return FlightAnalysisResult(
            total_distance_m=round(total_dist, 2),
            total_flight_time_s=round(total_time, 1),
            max_distance_from_home_m=round(max_dist_home, 2),
            max_altitude_m=alt_profile.max_altitude_m,
            max_speed_ms=speed_profile.max_speed_ms,
            avg_speed_ms=speed_profile.avg_speed_ms,
            speed_profile=speed_profile,
            altitude_profile=alt_profile,
            flight_segments=segments,
            home_point=home,
            takeoff_point=takeoff,
            landing_point=landing,
            geofence_violations=violations,
            no_fly_zone_alerts=nfz_alerts,
            smoothed_track=smoothed,
            filtered_track=filtered,
        )

    def _filter_outliers(self, points: list[GeoPoint]) -> list[GeoPoint]:
        if len(points) < 3:
            return points
        cleaned = [points[0]]
        for i in range(1, len(points)):
            d = haversine_m(points[i - 1].latitude, points[i - 1].longitude,
                            points[i].latitude, points[i].longitude)
            if d < 5000:
                cleaned.append(points[i])
        return cleaned

    def _smooth_track(self, points: list[GeoPoint]) -> list[GeoPoint]:
        if not points:
            return []
        kf_lat = SimpleKalmanFilter()
        kf_lon = SimpleKalmanFilter()
        kf_alt = SimpleKalmanFilter()
        smoothed = []
        for p in points:
            smoothed.append(GeoPoint(
                latitude=kf_lat.update(p.latitude),
                longitude=kf_lon.update(p.longitude),
                altitude_m=kf_alt.update(p.altitude_m),
                timestamp=p.timestamp,
                speed_ms=p.speed_ms,
                heading_deg=p.heading_deg,
            ))
        return smoothed

    def _detect_home_point(self, points: list[GeoPoint]) -> Optional[GeoPoint]:
        if not points:
            return None
        return GeoPoint(
            latitude=points[0].latitude,
            longitude=points[0].longitude,
            altitude_m=points[0].altitude_m,
            timestamp=points[0].timestamp,
        )

    def _detect_takeoff_point(self, points: list[GeoPoint]) -> Optional[GeoPoint]:
        for p in points:
            if abs(p.altitude_m) > 1.0 or p.speed_ms > 0.5:
                return GeoPoint(
                    latitude=p.latitude, longitude=p.longitude,
                    altitude_m=p.altitude_m, timestamp=p.timestamp,
                )
        return points[0] if points else None

    def _detect_landing_point(self, points: list[GeoPoint]) -> Optional[GeoPoint]:
        for p in reversed(points):
            if p.altitude_m < 3.0 or p.speed_ms < 0.3:
                return p
        return points[-1] if points else None

    def _compute_total_distance(self, points: list[GeoPoint]) -> float:
        total = 0.0
        for i in range(1, len(points)):
            total += haversine_m(
                points[i - 1].latitude, points[i - 1].longitude,
                points[i].latitude, points[i].longitude,
            )
        return total

    def _compute_total_time(self, points: list[GeoPoint]) -> float:
        if len(points) < 2:
            return 0.0
        try:
            t0 = datetime.fromisoformat(points[0].timestamp)
            t1 = datetime.fromisoformat(points[-1].timestamp)
            return (t1 - t0).total_seconds()
        except (ValueError, TypeError):
            return float(len(points))

    def _max_distance_from(self, points: list[GeoPoint], origin: Optional[GeoPoint]) -> float:
        if not origin:
            return 0.0
        max_d = 0.0
        for p in points:
            d = haversine_m(origin.latitude, origin.longitude, p.latitude, p.longitude)
            max_d = max(max_d, d)
        return max_d

    def _build_speed_profile(self, speeds: list[float]) -> SpeedProfile:
        if not speeds:
            return SpeedProfile(
                avg_speed_ms=0.0, max_speed_ms=0.0, min_speed_ms=0.0,
                speed_percentiles={}, hover_duration_s=0.0, cruise_duration_s=0.0,
            )
        avg = statistics.mean(speeds)
        mx = max(speeds)
        mn = min(speeds)
        percentiles = {str(p): round(statistics.quantiles(speeds, n=100)[p - 1], 2)
                       for p in self.SPEED_PERCENTILES if p <= 99}
        hover = sum(1 for s in speeds if s < self.HOVER_SPEED_THRESHOLD)
        cruise = len(speeds) - hover
        return SpeedProfile(
            avg_speed_ms=round(avg, 2), max_speed_ms=round(mx, 2),
            min_speed_ms=round(mn, 2), speed_percentiles=percentiles,
            hover_duration_s=float(hover), cruise_duration_s=float(cruise),
        )

    def _build_altitude_profile(self, points: list[GeoPoint],
                                takeoff: Optional[GeoPoint]) -> AltitudeProfile:
        alts = [p.altitude_m for p in points]
        if not alts:
            return self._empty_altitude_profile()
        avg_alt = statistics.mean(alts)
        mx = max(alts)
        mn = min(alts)
        to_alt = takeoff.altitude_m if takeoff else (alts[0] if alts else 0)
        landing_alt = alts[-1] if alts else 0

        buckets: dict[str, float] = {}
        for i in range(len(self.ALTITUDE_BUCKETS_M) - 1):
            lo = self.ALTITUDE_BUCKETS_M[i]
            hi = self.ALTITUDE_BUCKETS_M[i + 1]
            count = sum(1 for a in alts if lo <= a < hi)
            buckets[f"{lo}-{hi}m"] = count

        over = sum(1 for a in alts if a >= self.ALTITUDE_BUCKETS_M[-1])
        if over:
            buckets[f">{self.ALTITUDE_BUCKETS_M[-1]}m"] = over

        return AltitudeProfile(
            max_altitude_m=round(mx, 2), min_altitude_m=round(mn, 2),
            avg_altitude_m=round(avg_alt, 2), takeoff_altitude_m=round(to_alt, 2),
            landing_altitude_m=round(landing_alt, 2), altitude_bucket=buckets,
        )

    def _segment_flight(self, points: list[GeoPoint]) -> list[FlightSegment]:
        if len(points) < 5:
            return []
        segments: list[FlightSegment] = []
        seg_start = 0
        for i in range(1, len(points)):
            dt = self._time_diff(points[seg_start].timestamp, points[i].timestamp)
            if dt >= 10:
                dist = self._compute_total_distance(points[seg_start:i + 1])
                spds = [p.speed_ms for p in points[seg_start:i + 1] if p.speed_ms > 0]
                avg_s = statistics.mean(spds) if spds else 0
                max_s = max(spds) if spds else 0
                alt_change = points[i].altitude_m - points[seg_start].altitude_m
                seg_type = "climb" if alt_change > 5 else "descent" if alt_change < -5 else "cruise"
                segments.append(FlightSegment(
                    start_time=points[seg_start].timestamp,
                    end_time=points[i].timestamp,
                    distance_m=round(dist, 2),
                    avg_speed_ms=round(avg_s, 2),
                    max_speed_ms=round(max_s, 2),
                    altitude_change_m=round(alt_change, 2),
                    segment_type=seg_type,
                ))
                seg_start = i
        return segments

    def _check_geofences(self, points: list[GeoPoint]) -> list[GeofenceViolation]:
        violations: list[GeofenceViolation] = []
        if not self.geofences or not points:
            return violations

        step = max(1, len(points) // 100)
        for i in range(0, len(points), step):
            p = points[i]
            for fence in self.geofences:
                d = haversine_m(p.latitude, p.longitude, fence.center_lat, fence.center_lon)
                if d > fence.radius_m:
                    violations.append(GeofenceViolation(
                        timestamp=p.timestamp,
                        fence_name=fence.name,
                        distance_m=round(d - fence.radius_m, 2),
                        severity="high" if d > fence.radius_m * 2 else "medium",
                        location=(p.latitude, p.longitude),
                        details=f"Exceeded geofence '{fence.name}' by {round(d - fence.radius_m, 1)}m",
                    ))
        return violations

    def _check_no_fly_zones(self, points: list[GeoPoint]) -> list[GeofenceViolation]:
        alerts: list[GeofenceViolation] = []
        if not self.no_fly_zones or not points:
            return alerts

        step = max(1, len(points) // 50)
        for i in range(0, len(points), step):
            p = points[i]
            for zone in self.no_fly_zones:
                d = haversine_m(p.latitude, p.longitude, zone.latitude, zone.longitude)
                if d < zone.radius_m * 3:
                    dist_m = d if d < zone.radius_m else d - zone.radius_m
                    alerts.append(GeofenceViolation(
                        timestamp=p.timestamp,
                        fence_name=zone.name,
                        distance_m=round(dist_m, 2),
                        severity="critical" if d < zone.radius_m else "warning",
                        location=(p.latitude, p.longitude),
                        details=f"Proximity to no-fly zone '{zone.name}': {round(dist_m, 1)}m",
                    ))
        return alerts

    def _empty_speed_profile(self) -> SpeedProfile:
        return SpeedProfile(
            avg_speed_ms=0.0, max_speed_ms=0.0, min_speed_ms=0.0,
            speed_percentiles={}, hover_duration_s=0.0, cruise_duration_s=0.0,
        )

    def _empty_altitude_profile(self) -> AltitudeProfile:
        return AltitudeProfile(
            max_altitude_m=0.0, min_altitude_m=0.0, avg_altitude_m=0.0,
            takeoff_altitude_m=0.0, landing_altitude_m=0.0, altitude_bucket={},
        )

    def _time_diff(self, t1: str, t2: str) -> float:
        try:
            dt1 = datetime.fromisoformat(t1)
            dt2 = datetime.fromisoformat(t2)
            return abs((dt2 - dt1).total_seconds())
        except (ValueError, TypeError):
            return 1.0


# ---------------------------------------------------------------------------
# KML/KMZ generation
# ---------------------------------------------------------------------------

def generate_kml(track: list[GeoPoint], home: Optional[GeoPoint] = None,
                 title: str = "Drone Flight Track") -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '  <Document>',
        f'    <name>{title}</name>',
    ]

    if home:
        lines.append('    <Placemark>')
        lines.append('      <name>Home Point</name>')
        lines.append(f'      <Point><coordinates>{home.longitude},{home.latitude},{home.altitude_m or 0}</coordinates></Point>')
        lines.append('    </Placemark>')

    if track:
        coords = ' '.join(f'{p.longitude},{p.latitude},{p.altitude_m or 0}' for p in track)
        lines.append('    <Placemark>')
        lines.append('      <name>Flight Track</name>')
        lines.append('      <LineString>')
        lines.append('        <altitudeMode>absolute</altitudeMode>')
        lines.append(f'        <coordinates>{coords}</coordinates>')
        lines.append('      </LineString>')
        lines.append('    </Placemark>')

    lines.append('  </Document>')
    lines.append('</kml>')
    return '\n'.join(lines)


def generate_kmz(kml_content: str) -> bytes:
    import zipfile
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('doc.kml', kml_content)
    return buf.getvalue()

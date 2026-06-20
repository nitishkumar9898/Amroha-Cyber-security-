"""Location intelligence and geo-fence analysis.

Uses DBSCAN for clustering significant locations,
infers home/work locations,
detects geo-fence violations,
and reconstructs location timelines.
"""

import json
import math
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from dataclasses import dataclass, field

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler


@dataclass
class LocationPoint:
    timestamp: str
    latitude: float
    longitude: float
    altitude: float = 0.0
    accuracy: float = 0.0
    source: str = "unknown"


@dataclass
class SignificantLocation:
    label: str
    latitude: float
    longitude: float
    radius_meters: float
    visit_count: int
    first_seen: str
    last_seen: str
    typical_hours: list[int] = field(default_factory=list)
    location_type: str = "unknown"  # home, work, gym, transit, poi


@dataclass
class GeoFence:
    name: str
    latitude: float
    longitude: float
    radius_meters: float
    type: str  # restricted, monitored, sensitive
    alerts: list[str] = field(default_factory=list)


@dataclass
class GeoFenceViolation:
    timestamp: str
    latitude: float
    longitude: float
    geo_fence_name: str
    violation_type: str  # entry, exit, dwell
    severity: str


@dataclass
class LocationTimelineEntry:
    timestamp: str
    location_label: str
    latitude: float
    longitude: float
    activity_type: str  # stationary, walking, driving, unknown


@dataclass
class LocationAnalysis:
    total_points: int
    significant_locations: list[SignificantLocation] = field(default_factory=list)
    home_location: Optional[SignificantLocation] = None
    work_location: Optional[SignificantLocation] = None
    geo_fence_violations: list[GeoFenceViolation] = field(default_factory=list)
    timeline: list[LocationTimelineEntry] = field(default_factory=list)
    daily_routines: dict[str, list[dict]] = field(default_factory=dict)
    analysis_timestamp: str = ""


class LocationAnalyzer:
    """Analyze location data to extract intelligence."""

    def __init__(
        self,
        eps_km: float = 0.2,
        min_samples: int = 5,
    ):
        self.eps_km = eps_km
        self.min_samples = min_samples
        self.fences: list[GeoFence] = []

    def add_geo_fence(self, fence: GeoFence) -> None:
        self.fences.append(fence)

    def add_geo_fences(self, fences: list[GeoFence]) -> None:
        self.fences.extend(fences)

    def analyze(self, points: list[LocationPoint]) -> LocationAnalysis:
        if not points:
            return LocationAnalysis(
                total_points=0,
                analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            )

        locations = self._cluster_significant_locations(points)
        home, work = self._infer_home_work(locations, points)
        violations = self._check_geo_fences(points)
        timeline = self._build_timeline(points, locations)
        routines = self._analyze_daily_routines(points, locations)

        return LocationAnalysis(
            total_points=len(points),
            significant_locations=locations,
            home_location=home,
            work_location=work,
            geo_fence_violations=violations,
            timeline=timeline,
            daily_routines=routines,
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _cluster_significant_locations(
        self, points: list[LocationPoint]
    ) -> list[SignificantLocation]:
        coords = np.array([(p.latitude, p.longitude) for p in points])
        if len(coords) < self.min_samples:
            return []

        eps_deg = self.eps_km / 111.0
        if eps_deg <= 0:
            eps_deg = 0.001

        clustering = DBSCAN(
            eps=eps_deg,
            min_samples=self.min_samples,
            metric="haversine",
            algorithm="ball_tree",
        ).fit(np.radians(coords))

        labels = clustering.labels_
        unique_labels = set(labels) - {-1}

        significant: list[SignificantLocation] = []
        for label in unique_labels:
            mask = labels == label
            cluster_points = np.array(coords)[mask]
            cluster_indices = np.where(mask)[0]

            center_lat = float(np.mean(cluster_points[:, 0]))
            center_lon = float(np.mean(cluster_points[:, 1]))

            radii = [
                self._haversine(center_lat, center_lon, p[0], p[1])
                for p in cluster_points
            ]
            radius = float(np.percentile(radii, 90)) if radii else 0.0

            timestamps = [points[i].timestamp for i in cluster_indices if points[i].timestamp]
            hours = []
            for i in cluster_indices:
                try:
                    dt = datetime.fromisoformat(points[i].timestamp)
                    hours.append(dt.hour)
                except (ValueError, TypeError):
                    pass

            significant.append(
                SignificantLocation(
                    label=f"POI-{label + 1}",
                    latitude=center_lat,
                    longitude=center_lon,
                    radius_meters=round(radius, 2),
                    visit_count=int(np.sum(mask)),
                    first_seen=min(timestamps) if timestamps else "",
                    last_seen=max(timestamps) if timestamps else "",
                    typical_hours=sorted(set(hours)) if hours else [],
                    location_type=self._infer_location_type(
                        center_lat, center_lon, hours, points
                    ),
                )
            )

        return significant

    def _infer_home_work(
        self,
        locations: list[SignificantLocation],
        points: list[LocationPoint],
    ) -> tuple[Optional[SignificantLocation], Optional[SignificantLocation]]:
        home_candidates = []
        work_candidates = []

        for loc in locations:
            night_hours = [h for h in loc.typical_hours if h >= 21 or h <= 6]
            day_hours = [h for h in loc.typical_hours if 8 <= h <= 18]

            weekday_points = 0
            weekend_points = 0
            for p in points:
                if self._is_within(loc, p.latitude, p.longitude):
                    try:
                        dt = datetime.fromisoformat(p.timestamp)
                        if dt.weekday() < 5:
                            weekday_points += 1
                        else:
                            weekend_points += 1
                    except (ValueError, TypeError):
                        pass

            score_home = len(night_hours) * 2 + weekend_points * 0.5
            score_work = len(day_hours) * 2 + weekday_points * 0.5

            if score_home > 0:
                home_candidates.append((score_home, loc))
            if score_work > 0:
                work_candidates.append((score_work, loc))

        home = max(home_candidates, key=lambda x: x[0])[1] if home_candidates else None
        work = max(work_candidates, key=lambda x: x[0])[1] if work_candidates else None

        if home and home is work:
            if len(home_candidates) > 1:
                home_candidates.sort(key=lambda x: x[0], reverse=True)
                home = home_candidates[0][1]
                if len(home_candidates) > 1:
                    work = home_candidates[1][1]
                else:
                    work = None
            elif len(work_candidates) > 1:
                work_candidates.sort(key=lambda x: x[0], reverse=True)
                work = work_candidates[0][1]
                home = work_candidates[1][1] if len(work_candidates) > 1 else None

        if home:
            home.location_type = "home"
            home.label = "Home"
        if work:
            work.location_type = "work"
            work.label = "Work"

        return home, work

    def _infer_location_type(
        self,
        lat: float,
        lon: float,
        hours: list[int],
        points: list[LocationPoint],
    ) -> str:
        if not hours:
            return "poi"

        night_ratio = sum(1 for h in hours if h >= 22 or h <= 5) / len(hours)
        day_ratio = sum(1 for h in hours if 9 <= h <= 17) / len(hours)

        if night_ratio > 0.6:
            return "home"
        elif day_ratio > 0.5:
            return "work"
        elif set(hours).issuperset({6, 7, 18, 19, 20}):
            return "transit"
        else:
            return "poi"

    def _check_geo_fences(self, points: list[LocationPoint]) -> list[GeoFenceViolation]:
        violations: list[GeoFenceViolation] = []
        if not self.fences:
            return violations

        for fence in self.fences:
            inside_before = False
            for point in points:
                distance = self._haversine(
                    fence.latitude, fence.longitude,
                    point.latitude, point.longitude,
                )
                inside = distance <= fence.radius_meters / 1000.0

                if inside and not inside_before:
                    violations.append(
                        GeoFenceViolation(
                            timestamp=point.timestamp,
                            latitude=point.latitude,
                            longitude=point.longitude,
                            geo_fence_name=fence.name,
                            violation_type="entry",
                            severity="high" if fence.type == "restricted" else "medium",
                        )
                    )
                elif not inside and inside_before:
                    violations.append(
                        GeoFenceViolation(
                            timestamp=point.timestamp,
                            latitude=point.latitude,
                            longitude=point.longitude,
                            geo_fence_name=fence.name,
                            violation_type="exit",
                            severity="info",
                        )
                    )
                inside_before = inside

        return violations

    def _build_timeline(
        self,
        points: list[LocationPoint],
        locations: list[SignificantLocation],
    ) -> list[LocationTimelineEntry]:
        sorted_points = sorted(
            points,
            key=lambda p: p.timestamp or "",
        )

        timeline: list[LocationTimelineEntry] = []
        for point in sorted_points:
            matched_label = "Unknown"
            for loc in locations:
                if self._is_within(loc, point.latitude, point.longitude):
                    matched_label = loc.label
                    break

            activity = self._infer_activity(point, sorted_points)

            timeline.append(
                LocationTimelineEntry(
                    timestamp=point.timestamp or "",
                    location_label=matched_label,
                    latitude=point.latitude,
                    longitude=point.longitude,
                    activity_type=activity,
                )
            )

        return timeline

    def _is_within(self, loc: SignificantLocation, lat: float, lon: float) -> bool:
        distance = self._haversine(loc.latitude, loc.longitude, lat, lon)
        return distance <= (loc.radius_meters / 1000.0) + 0.05

    def _infer_activity(
        self,
        point: LocationPoint,
        all_points: list[LocationPoint],
    ) -> str:
        if point.accuracy > 100:
            return "unknown"

        idx = all_points.index(point)
        if idx == 0:
            return "unknown"

        prev = all_points[idx - 1]
        try:
            dt_prev = datetime.fromisoformat(prev.timestamp)
            dt_curr = datetime.fromisoformat(point.timestamp)
            dt_diff = (dt_curr - dt_prev).total_seconds()
        except (ValueError, TypeError):
            return "unknown"

        if dt_diff <= 0:
            return "stationary"

        speed = self._haversine(prev.latitude, prev.longitude, point.latitude, point.longitude) / (dt_diff / 3600.0)

        if speed < 1:
            return "stationary"
        elif speed < 10:
            return "walking"
        elif speed < 120:
            return "driving"
        else:
            return "fast_transit"

    def _analyze_daily_routines(
        self,
        points: list[LocationPoint],
        locations: list[SignificantLocation],
    ) -> dict[str, list[dict]]:
        daily: dict[str, list[dict]] = {}
        for point in points:
            if not point.timestamp:
                continue
            try:
                dt = datetime.fromisoformat(point.timestamp)
                day_key = dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                continue

            matched = "Unknown"
            for loc in locations:
                if self._is_within(loc, point.latitude, point.longitude):
                    matched = loc.label
                    break

            if day_key not in daily:
                daily[day_key] = []
            daily[day_key].append({
                "time": point.timestamp,
                "location": matched,
                "latitude": point.latitude,
                "longitude": point.longitude,
            })

        return daily

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def to_dict(self, analysis: LocationAnalysis) -> dict[str, Any]:
        return {
            "total_points": analysis.total_points,
            "significant_locations": [
                {
                    "label": loc.label,
                    "latitude": loc.latitude,
                    "longitude": loc.longitude,
                    "radius_meters": loc.radius_meters,
                    "visit_count": loc.visit_count,
                    "first_seen": loc.first_seen,
                    "last_seen": loc.last_seen,
                    "typical_hours": loc.typical_hours,
                    "location_type": loc.location_type,
                }
                for loc in analysis.significant_locations
            ],
            "home_location": {
                "latitude": analysis.home_location.latitude,
                "longitude": analysis.home_location.longitude,
                "radius_meters": analysis.home_location.radius_meters,
            } if analysis.home_location else None,
            "work_location": {
                "latitude": analysis.work_location.latitude,
                "longitude": analysis.work_location.longitude,
                "radius_meters": analysis.work_location.radius_meters,
            } if analysis.work_location else None,
            "geo_fence_violations": [
                {
                    "timestamp": v.timestamp,
                    "latitude": v.latitude,
                    "longitude": v.longitude,
                    "geo_fence_name": v.geo_fence_name,
                    "violation_type": v.violation_type,
                    "severity": v.severity,
                }
                for v in analysis.geo_fence_violations
            ],
            "timeline": [
                {
                    "timestamp": e.timestamp,
                    "location_label": e.location_label,
                    "latitude": e.latitude,
                    "longitude": e.longitude,
                    "activity_type": e.activity_type,
                }
                for e in analysis.timeline
            ],
            "daily_routines": analysis.daily_routines,
            "analysis_timestamp": analysis.analysis_timestamp,
        }

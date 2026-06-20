"""Temporal link analyzer for evidence correlation.

Implements time window-based link discovery, temporal sequence mining,
periodic pattern detection, causality inference (Granger causality basics),
and temporal anomaly detection.
"""

import itertools
import json
import logging
import math
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

import numpy as np

try:
    from scipy import stats
    from scipy.signal import find_peaks
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    stats = None
    find_peaks = None

try:
    from sklearn.linear_model import LinearRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    LinearRegression = None

logger = logging.getLogger(__name__)


@dataclass
class TemporalLink:
    source_id: str
    target_id: str
    window_start: str
    window_end: str
    weight: float
    relationship_type: str
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TemporalSequence:
    sequence_id: str
    events: list[dict[str, Any]]
    pattern_type: str
    confidence: float
    period_seconds: Optional[float] = None
    description: str = ""


@dataclass
class CausalityResult:
    cause_id: str
    effect_id: str
    lag_steps: int
    p_value: float
    significant: bool
    strength: float


@dataclass
class TemporalAnomaly:
    timestamp: str
    entity_id: str
    anomaly_score: float
    anomaly_type: str
    description: str
    expected_behavior: str = ""
    actual_behavior: str = ""


class TemporalLinkAnalyzer:
    def __init__(
        self,
        window_size_seconds: int = 3600,
        slide_seconds: int = 1800,
    ):
        self.window_size = timedelta(seconds=window_size_seconds)
        self.slide = timedelta(seconds=slide_seconds)
        self._events: list[dict[str, Any]] = []

    def add_event(self, event: dict[str, Any]):
        self._events.append(event)

    def add_events(self, events: list[dict[str, Any]]):
        self._events.extend(events)

    def clear(self):
        self._events.clear()

    @property
    def event_count(self) -> int:
        return len(self._events)

    def discover_links(
        self,
        min_cooccurrence: int = 2,
        max_gap_seconds: Optional[int] = None,
    ) -> list[TemporalLink]:
        if len(self._events) < 2:
            return []

        window_size = self.window_size
        if max_gap_seconds is not None:
            window_size = timedelta(seconds=max_gap_seconds)

        sorted_events = sorted(
            self._events,
            key=lambda e: e.get("timestamp", ""),
        )

        links: dict[tuple[str, str], TemporalLink] = {}
        n = len(sorted_events)

        for i in range(n):
            for j in range(i + 1, n):
                evt_i = sorted_events[i]
                evt_j = sorted_events[j]

                ts_i = self._parse_ts(evt_i.get("timestamp", ""))
                ts_j = self._parse_ts(evt_j.get("timestamp", ""))
                if ts_i is None or ts_j is None:
                    continue

                if ts_j - ts_i > window_size:
                    continue

                src = evt_i.get("entity_id", evt_i.get("source", f"evt_{i}"))
                tgt = evt_j.get("entity_id", evt_j.get("target", evt_j.get("source", f"evt_{j}")))

                if src == tgt:
                    continue

                key = (src, tgt) if src < tgt else (tgt, src)
                weight = 1.0 / (1.0 + math.log(1 + (ts_j - ts_i).total_seconds()))

                if key not in links:
                    links[key] = TemporalLink(
                        source_id=src,
                        target_id=tgt,
                        window_start=ts_i.isoformat(),
                        window_end=ts_j.isoformat(),
                        weight=0.0,
                        relationship_type="temporal_cooccurrence",
                        evidence_ids=[],
                    )

                links[key].weight += weight
                eid_i = evt_i.get("evidence_id") or evt_i.get("id", f"evt_{i}")
                eid_j = evt_j.get("evidence_id") or evt_j.get("id", f"evt_{j}")
                links[key].evidence_ids.extend([eid_i, eid_j])

        result = [
            link for link in links.values()
            if len(set(link.evidence_ids)) >= min_cooccurrence
        ]

        for link in result:
            link.weight = min(link.weight, 1.0)
            link.evidence_ids = list(set(link.evidence_ids))

        return sorted(result, key=lambda x: x.weight, reverse=True)

    def mine_sequences(
        self,
        min_support: int = 2,
        max_gap_seconds: int = 3600,
        pattern_length: int = 3,
    ) -> list[TemporalSequence]:
        if len(self._events) < pattern_length:
            return []

        sorted_events = sorted(
            self._events,
            key=lambda e: e.get("timestamp", ""),
        )

        gap = timedelta(seconds=max_gap_seconds)
        event_types = [e.get("type", "unknown") for e in sorted_events]
        sequences: list[list[str]] = []
        current_seq: list[str] = []

        for i, evt in enumerate(sorted_events):
            current_seq.append(event_types[i])
            if i > 0:
                prev_ts = self._parse_ts(sorted_events[i - 1].get("timestamp", ""))
                curr_ts = self._parse_ts(evt.get("timestamp", ""))
                if prev_ts and curr_ts and (curr_ts - prev_ts) > gap:
                    if len(current_seq) >= pattern_length:
                        sequences.append(list(current_seq))
                    current_seq = [event_types[i]]

        if len(current_seq) >= pattern_length:
            sequences.append(list(current_seq))

        pattern_counts: Counter = Counter()
        for seq in sequences:
            for i in range(len(seq) - pattern_length + 1):
                pattern = tuple(seq[i:i + pattern_length])
                pattern_counts[pattern] += 1

        min_count = max(1, min_support)
        mined: list[TemporalSequence] = []
        for pattern, count in pattern_counts.most_common():
            if count < min_count:
                break
            mined.append(TemporalSequence(
                sequence_id=f"seq_{len(mined)}",
                events=[{"type": t} for t in pattern],
                pattern_type="event_sequence",
                confidence=min(1.0, count / max(len(sequences), 1)),
                description=f"Pattern {pattern} occurred {count} times",
            ))

        return mined

    def detect_periodic_patterns(
        self,
        entity_id: Optional[str] = None,
        min_period_hours: float = 0.5,
        max_period_hours: float = 168.0,
    ) -> list[TemporalSequence]:
        if not SCIPY_AVAILABLE:
            return []

        filtered = self._events
        if entity_id:
            filtered = [
                e for e in self._events
                if e.get("entity_id") == entity_id or e.get("source") == entity_id
            ]

        if len(filtered) < 10:
            return []

        timestamps = []
        for e in filtered:
            ts = self._parse_ts(e.get("timestamp", ""))
            if ts:
                timestamps.append(ts.timestamp())

        if len(timestamps) < 10:
            return []

        timestamps = np.array(sorted(timestamps))
        diffs = np.diff(timestamps)
        diffs = diffs[diffs > 0]

        if len(diffs) < 5:
            return []

        try:
            hist, bin_edges = np.histogram(diffs, bins=min(50, len(diffs) // 2))
            peaks, properties = find_peaks(hist, height=max(1, hist.max() * 0.3))

            periods: list[TemporalSequence] = []
            for peak in peaks[:5]:
                period_seconds = (bin_edges[peak] + bin_edges[peak + 1]) / 2.0
                period_hours = period_seconds / 3600.0

                if period_hours < min_period_hours or period_hours > max_period_hours:
                    continue

                peak_height = properties["peak_heights"][len(periods)] if len(periods) < len(properties["peak_heights"]) else hist[peak]
                confidence = min(1.0, peak_height / max(hist) if max(hist) > 0 else 0.5)

                periods.append(TemporalSequence(
                    sequence_id=f"period_{len(periods)}",
                    events=[{"timestamp": datetime.fromtimestamp(t).isoformat()} for t in timestamps[-10:]],
                    pattern_type="periodic",
                    confidence=confidence,
                    period_seconds=float(period_seconds),
                    description=f"Periodic pattern detected every {period_hours:.1f}h "
                                f"({peak_height} occurrences at this interval)",
                ))

            return periods
        except Exception as e:
            logger.warning("Periodic detection failed: %s", e)
            return []

    def infer_causality(
        self,
        source_events: list[dict[str, Any]],
        target_events: list[dict[str, Any]],
        max_lag: int = 5,
        significance_level: float = 0.05,
    ) -> list[CausalityResult]:
        if not SKLEARN_AVAILABLE or not SCIPY_AVAILABLE:
            return []

        series_a = self._event_series(source_events)
        series_b = self._event_series(target_events)

        if len(series_a) < max_lag + 5 or len(series_b) < max_lag + 5:
            return []

        results: list[CausalityResult] = []
        for lag in range(1, max_lag + 1):
            p_value = self._granger_causality(series_a, series_b, lag)
            results.append(CausalityResult(
                cause_id=source_events[0].get("entity_id", "source") if source_events else "source",
                effect_id=target_events[0].get("entity_id", "target") if target_events else "target",
                lag_steps=lag,
                p_value=float(p_value),
                significant=p_value < significance_level,
                strength=float(max(0, -math.log10(p_value + 1e-10)) / 10.0),
            ))

        return sorted(results, key=lambda r: r.strength, reverse=True)

    def detect_anomalies(
        self,
        entity_id: Optional[str] = None,
        std_threshold: float = 2.0,
        time_window_hours: float = 24.0,
    ) -> list[TemporalAnomaly]:
        filtered = self._events
        if entity_id:
            filtered = [
                e for e in self._events
                if e.get("entity_id") == entity_id or e.get("source") == entity_id
            ]

        if len(filtered) < 5:
            return []

        timestamps = []
        for e in filtered:
            ts = self._parse_ts(e.get("timestamp", ""))
            if ts:
                timestamps.append(ts)

        if len(timestamps) < 5:
            return []

        timestamps = sorted(timestamps)
        window = timedelta(hours=time_window_hours)

        anomalies: list[TemporalAnomaly] = []

        diffs = np.diff([t.timestamp() for t in timestamps])
        if len(diffs) < 3:
            return []

        mean_diff = np.mean(diffs)
        std_diff = np.maximum(np.std(diffs), 1e-6)

        for i in range(1, len(timestamps)):
            gap = (timestamps[i] - timestamps[i - 1]).total_seconds()
            z_score = abs(gap - mean_diff) / std_diff

            if z_score > std_threshold:
                entity = entity_id or filtered[i].get("entity_id", filtered[i].get("source", "unknown"))
                anomalies.append(TemporalAnomaly(
                    timestamp=timestamps[i].isoformat(),
                    entity_id=entity,
                    anomaly_score=min(1.0, z_score / 10.0),
                    anomaly_type="temporal_gap",
                    description=f"Abnormal time gap: {gap:.0f}s (mean: {mean_diff:.0f}s, z={z_score:.2f})",
                    expected_behavior=f"Expected gap ~{mean_diff:.0f}s",
                    actual_behavior=f"Actual gap {gap:.0f}s",
                ))

        event_counts: dict[str, int] = defaultdict(int)
        window_start = timestamps[0]
        for ts in timestamps:
            if ts - window_start > window:
                window_start = ts
            event_counts[ts.isoformat()] = sum(
                1 for t in timestamps
                if window_start <= t <= window_start + window and abs((t - ts).total_seconds()) < window.total_seconds()
            )

        event_vals = list(event_counts.values())
        if event_vals:
            mean_count = np.mean(event_vals)
            std_count = np.maximum(np.std(event_vals), 1e-6)
            ts_windows = list(event_counts.keys())[-min(20, len(event_counts)):]
            for ts_str in ts_windows:
                count = event_counts[ts_str]
                z_count = abs(count - mean_count) / std_count
                if z_count > std_threshold:
                    anomalies.append(TemporalAnomaly(
                        timestamp=ts_str,
                        entity_id=entity_id or "global",
                        anomaly_score=min(1.0, z_count / 10.0),
                        anomaly_type="event_burst",
                        description=f"Event burst: {count} events (mean: {mean_count:.1f}, z={z_count:.2f})",
                        expected_behavior=f"Expected ~{mean_count:.0f} events",
                        actual_behavior=f"Observed {count} events",
                    ))

        return sorted(anomalies, key=lambda a: a.anomaly_score, reverse=True)

    def sliding_window_correlation(
        self,
        window_size_seconds: int = 3600,
        slide_seconds: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        slide = slide_seconds or window_size_seconds // 2
        window = timedelta(seconds=window_size_seconds)
        step = timedelta(seconds=slide)

        if not self._events:
            return []

        sorted_events = sorted(
            self._events,
            key=lambda e: e.get("timestamp", ""),
        )

        start_ts = self._parse_ts(sorted_events[0].get("timestamp", ""))
        end_ts = self._parse_ts(sorted_events[-1].get("timestamp", ""))
        if start_ts is None or end_ts is None:
            return []

        windows: list[dict[str, Any]] = []
        current = start_ts

        while current < end_ts:
            win_end = current + window
            in_window = [
                e for e in sorted_events
                if self._in_window(e.get("timestamp", ""), current, win_end)
            ]

            type_counts: dict[str, int] = defaultdict(int)
            entity_counts: dict[str, int] = defaultdict(int)
            for e in in_window:
                type_counts[e.get("type", "unknown")] += 1
                entity_counts[e.get("entity_id", e.get("source", "unknown"))] += 1

            windows.append({
                "window_start": current.isoformat(),
                "window_end": win_end.isoformat(),
                "event_count": len(in_window),
                "event_types": dict(type_counts),
                "unique_entities": len(entity_counts),
                "entities": list(entity_counts.keys()),
            })

            current += step

        return windows

    def temporal_graph_edges(
        self,
        source_field: str = "source",
        target_field: str = "target",
        window_seconds: int = 3600,
    ) -> list[dict[str, Any]]:
        edges: list[dict[str, Any]] = []
        window = timedelta(seconds=window_seconds)

        sorted_events = sorted(
            self._events,
            key=lambda e: e.get("timestamp", ""),
        )

        for i in range(len(sorted_events)):
            for j in range(i + 1, len(sorted_events)):
                evt_i = sorted_events[i]
                evt_j = sorted_events[j]
                ts_i = self._parse_ts(evt_i.get("timestamp", ""))
                ts_j = self._parse_ts(evt_j.get("timestamp", ""))
                if ts_i is None or ts_j is None:
                    continue
                if ts_j - ts_i > window:
                    break

                src = evt_i.get(source_field) or evt_i.get("entity_id") or f"e{i}"
                tgt = evt_j.get(target_field) or evt_j.get("entity_id") or f"e{j}"
                if src != tgt:
                    weight = 1.0 / (1.0 + (ts_j - ts_i).total_seconds())
                    edges.append({
                        "source": src,
                        "target": tgt,
                        "weight": weight,
                        "timestamp": ts_j.isoformat(),
                        "relationship": "temporal_follows",
                    })

        return edges

    def timeline(self) -> list[dict[str, Any]]:
        sorted_events = sorted(
            self._events,
            key=lambda e: e.get("timestamp", ""),
        )
        return [
            {
                "timestamp": e.get("timestamp", ""),
                "type": e.get("type", "unknown"),
                "entity": e.get("entity_id", e.get("source", "")),
                "description": e.get("description", str(e.get("metadata", {}))),
            }
            for e in sorted_events
        ]

    @staticmethod
    def _parse_ts(ts: Any) -> Optional[datetime]:
        if isinstance(ts, datetime):
            return ts
        try:
            return datetime.fromisoformat(str(ts))
        except (ValueError, TypeError):
            try:
                return datetime.fromtimestamp(float(ts), tz=timezone.utc)
            except (ValueError, TypeError, OSError):
                return None

    @staticmethod
    def _in_window(ts: Any, start: datetime, end: datetime) -> bool:
        dt = TemporalLinkAnalyzer._parse_ts(ts)
        if dt is None:
            return False
        return start <= dt <= end

    @staticmethod
    def _event_series(events: list[dict[str, Any]]) -> np.ndarray:
        timestamps = []
        for e in events:
            ts = TemporalLinkAnalyzer._parse_ts(e.get("timestamp", ""))
            if ts:
                timestamps.append(ts.timestamp())
        return np.array(sorted(timestamps))

    @staticmethod
    def _granger_causality(
        series_a: np.ndarray,
        series_b: np.ndarray,
        lag: int,
    ) -> float:
        if LinearRegression is None or stats is None:
            return 1.0

        try:
            common_t_min = max(series_a.min(), series_b.min())
            common_t_max = min(series_a.max(), series_b.max())

            a_binned = series_a[(series_a >= common_t_min) & (series_a <= common_t_max)]
            b_binned = series_b[(series_b >= common_t_min) & (series_b <= common_t_max)]

            if len(a_binned) < lag + 3 or len(b_binned) < lag + 3:
                return 1.0

            min_len = min(len(a_binned), len(b_binned))
            a_binned = a_binned[:min_len]
            b_binned = b_binned[:min_len]

            X_restricted = np.column_stack([
                a_binned[i:min_len - lag + i] if i > 0 else a_binned[:min_len - lag]
                for i in range(lag)
            ])
            y = b_binned[lag:min_len]

            if X_restricted.shape[0] != y.shape[0]:
                return 1.0

            model_restricted = LinearRegression()
            model_restricted.fit(X_restricted, y)
            residuals_restricted = y - model_restricted.predict(X_restricted)
            rss_restricted = np.sum(residuals_restricted ** 2)

            X_unrestricted = np.column_stack([
                a_binned[i:min_len - lag + i] if i > 0 else a_binned[:min_len - lag]
                for i in range(lag)
            ] + [
                b_binned[i:min_len - lag + i] if i > 0 else b_binned[:min_len - lag]
                for i in range(lag)
            ])

            if X_unrestricted.shape[0] != y.shape[0]:
                return 1.0

            model_unrestricted = LinearRegression()
            model_unrestricted.fit(X_unrestricted, y)
            residuals_unrestricted = y - model_unrestricted.predict(X_unrestricted)
            rss_unrestricted = np.sum(residuals_unrestricted ** 2)

            n = len(y)
            k = lag
            f_stat = ((rss_restricted - rss_unrestricted) / k) / (rss_unrestricted / (n - 2 * k))
            p_value = 1.0 - stats.f.cdf(abs(f_stat), k, n - 2 * k)
            return max(0.0, min(1.0, p_value))

        except Exception as e:
            logger.debug("Granger causality failed: %s", e)
            return 1.0

"""
Tests for real-time deepfake streaming detection.
"""

import pytest
import json
import time
from modules.deepfake_detector.pipelines.realtime_stream import (
    SlidingWindowDetector, StreamSession, StreamManager, stream_manager,
)


class TestSlidingWindowDetector:
    def test_initial_state(self):
        d = SlidingWindowDetector(window_size=5, threshold=0.6)
        assert len(d.window) == 0
        assert d.threshold == 0.6

    def test_low_probability(self):
        d = SlidingWindowDetector(window_size=3)
        for _ in range(5):
            r = d.add_frame(0.1, time.time())
        assert r["is_manipulated"] is False
        assert r["confidence"] < 0.5

    def test_high_probability(self):
        d = SlidingWindowDetector(window_size=3, threshold=0.5)
        for _ in range(5):
            r = d.add_frame(0.9, time.time())
        assert r["is_manipulated"] is True
        assert r["confidence"] > 0.5

    def test_alert_cooldown(self):
        d = SlidingWindowDetector(window_size=3, threshold=0.5)
        now = time.time()
        r1 = d.add_frame(0.9, now)
        assert r1["alert"] is True
        r2 = d.add_frame(0.9, now + 1.0)
        assert r2["alert"] is False  # Within cooldown
        r3 = d.add_frame(0.9, now + 6.0)
        assert r3["alert"] is True  # Cooldown passed

    def test_window_averaging(self):
        d = SlidingWindowDetector(window_size=3, threshold=0.6)
        d.add_frame(0.9, time.time())
        d.add_frame(0.1, time.time())
        r = d.add_frame(0.9, time.time())
        avg = (0.9 + 0.1 + 0.9) / 3
        assert r["window_avg"] == pytest.approx(avg)
        assert r["window_size"] == 3


class TestStreamSession:
    def test_session_creation(self):
        s = StreamSession("cam01", "case-001", "video")
        assert s.stream_id == "cam01"
        assert s.frame_count == 0
        assert len(s.coc._events) == 1  # stream_started

    def test_frame_processing(self):
        s = StreamSession("cam01", "case-001", "video")
        frame = b"\x00\x01\x02" * 100
        result = s.process_frame(frame)
        assert "is_manipulated" in result
        assert "confidence" in result
        assert result["frame_index"] == 1

    def test_multiple_frames(self):
        s = StreamSession("cam01", "case-001", "video")
        for i in range(10):
            frame = bytes([i % 256]) * 500
            r = s.process_frame(frame)
            assert r["frame_index"] == i + 1
        assert s.frame_count == 10

    def test_summary(self):
        s = StreamSession("test", "case-001", "audio")
        for i in range(5):
            s.process_frame(bytes([i]) * 100)
        summary = s.get_summary()
        assert summary["total_frames"] == 5
        assert "chain_of_custody" in summary


class TestStreamManager:
    def test_create_and_get_session(self):
        mgr = StreamManager()
        s = mgr.create_session("s1", "case-001", "video")
        assert mgr.get_session("s1") is s

    def test_remove_session(self):
        mgr = StreamManager()
        mgr.create_session("s1", "case-001", "video")
        summary = mgr.remove_session("s1")
        assert summary is not None
        assert summary["total_frames"] == 0
        assert mgr.get_session("s1") is None

    def test_remove_nonexistent(self):
        mgr = StreamManager()
        assert mgr.remove_session("nonexistent") is None

    def test_active_count(self):
        mgr = StreamManager()
        assert mgr.get_active_count() == 0
        mgr.create_session("s1", "c1", "video")
        mgr.create_session("s2", "c1", "audio")
        assert mgr.get_active_count() == 2
        mgr.remove_session("s1")
        assert mgr.get_active_count() == 1

"""
=============================================================================
Deepfake Real-Time Streaming Detection — WebSocket Pipeline
=============================================================================

WebSocket-based real-time deepfake detection for live video/audio streams.
Supports:
  - WebRTC-compatible frame ingestion
  - Sub-200ms per-frame classification
  - Sliding window temporal smoothing
  - Configurable thresholds and alerting
  - Chain-of-custody for stream evidence segments

Usage:
  # Server (integrated into deepfake-detector API)
  uvicorn api:app --ws websockets

  # Client
  ws://host:8100/ws/analyze/video?stream_id=cam01&case_id=cas-001
"""

import asyncio
import json
import time
import struct
from typing import Optional
from collections import deque
from datetime import datetime, timezone

import numpy as np

from modules.shared.chain_of_custody import ChainOfCustodyManager


class SlidingWindowDetector:
    """Temporal smoothing over sliding window of frame predictions."""

    def __init__(self, window_size: int = 15, threshold: float = 0.6):
        self.window: deque = deque(maxlen=window_size)
        self.threshold = threshold
        self._alert_cooldown = 0.0

    def add_frame(self, manipulated_prob: float, timestamp: float) -> dict:
        self.window.append(manipulated_prob)
        avg = float(np.mean(self.window))
        std = float(np.std(self.window)) if len(self.window) > 1 else 0.0
        is_manipulated = avg > self.threshold
        confidence = min(1.0, (avg - self.threshold + 0.1) / 0.5) if is_manipulated else max(0.0, 1.0 - (self.threshold - avg + 0.1) / 0.5)

        alert = False
        if is_manipulated and (timestamp - self._alert_cooldown) > 5.0:
            alert = True
            self._alert_cooldown = timestamp

        return {
            "is_manipulated": is_manipulated,
            "confidence": round(confidence, 4),
            "window_avg": round(avg, 4),
            "window_std": round(std, 4),
            "window_size": len(self.window),
            "alert": alert,
            "timestamp": timestamp,
        }


class StreamSession:
    """Tracks a single WebSocket stream session."""

    def __init__(self, stream_id: str, case_id: str, modality: str):
        self.stream_id = stream_id
        self.case_id = case_id
        self.modality = modality
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.frame_count = 0
        self.alert_count = 0
        self.detector = SlidingWindowDetector()
        self.coc = ChainOfCustodyManager()
        self.coc.record("stream_started", f"system:{stream_id}", "deepfake-realtime",
                        {"case_id": case_id, "modality": modality})
        self._buffer: list[dict] = []
        self._max_buffer = 1000

    async def process_frame(self, frame_data: bytes, timestamp: Optional[float] = None) -> dict:
        ts = timestamp or time.time()
        self.frame_count += 1

        # Simulated inference (replace with actual model call)
        result = self._mock_inference(frame_data, ts)

        window_result = self.detector.add_frame(result.get("manipulated_prob", 0.5), ts)
        result.update(window_result)
        result["frame_index"] = self.frame_count

        if result.get("alert"):
            self.alert_count += 1
            self.coc.record("deepfake_alert", f"system:{self.stream_id}", "deepfake-realtime",
                            {"frame": self.frame_count, "confidence": result["confidence"]})

        if len(self._buffer) < self._max_buffer:
            self._buffer.append(result)

        return result

    def get_summary(self) -> dict:
        return {
            "stream_id": self.stream_id,
            "case_id": self.case_id,
            "modality": self.modality,
            "duration_s": (time.time() - datetime.fromisoformat(self.created_at).timestamp()),
            "total_frames": self.frame_count,
            "alerts": self.alert_count,
            "decision": "manipulated" if self.alert_count > 3 else "authentic",
            "chain_of_custody": self.coc.to_dict(),
            "created_at": self.created_at,
        }

    def _mock_inference(self, frame_data: bytes, _ts: float) -> dict:
        """Simulated frame inference. Replace with actual MesoNet/XceptionNet call."""
        seed = sum(frame_data[i] for i in range(min(len(frame_data), 1000)))
        prob = ((seed % 100) / 100.0) if seed > 0 else 0.5
        return {
            "manipulated_prob": prob,
            "model": "mesonet-v3-simulated",
            "inference_ms": 45 + (seed % 30),
        }


class StreamManager:
    """Manages all active WebSocket stream sessions."""

    def __init__(self):
        self._sessions: dict[str, StreamSession] = {}

    def create_session(self, stream_id: str, case_id: str, modality: str) -> StreamSession:
        session = StreamSession(stream_id, case_id, modality)
        self._sessions[stream_id] = session
        return session

    def get_session(self, stream_id: str) -> Optional[StreamSession]:
        return self._sessions.get(stream_id)

    def remove_session(self, stream_id: str) -> Optional[dict]:
        session = self._sessions.pop(stream_id, None)
        if session:
            session.coc.record("stream_ended", f"system:{stream_id}", "deepfake-realtime", {})
            return session.get_summary()
        return None

    def get_active_count(self) -> int:
        return len(self._sessions)


stream_manager = StreamManager()


# ─── WebSocket Handler (integrates into api.py) ──────────────────────────────

async def handle_video_stream(websocket, stream_id: str, case_id: str = "unknown"):
    """WebSocket handler for real-time video deepfake detection."""
    session = stream_manager.create_session(stream_id, case_id, "video")
    await websocket.accept()

    try:
        await websocket.send_json({"type": "session_started", "stream_id": stream_id})

        async for message in websocket.iter_bytes():
            result = await session.process_frame(message)
            await websocket.send_json({
                "type": "frame_result",
                "data": result,
            })

            if result.get("alert"):
                await websocket.send_json({
                    "type": "alert",
                    "severity": "high",
                    "message": f"Deepfake detected (conf: {result['confidence']:.2%})",
                    "frame": result["frame_index"],
                })

    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        summary = stream_manager.remove_session(stream_id)
        if summary:
            await websocket.send_json({"type": "session_summary", "data": summary})
        await websocket.close()

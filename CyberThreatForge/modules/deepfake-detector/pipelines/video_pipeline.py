import io
import math
import logging
from typing import Any, Optional

import torch
import torch.nn.functional as F
import numpy as np

logger = logging.getLogger(__name__)


class VideoPipeline:
    """Video analysis pipeline for deepfake detection.

    Performs frame extraction, face detection, per-frame classification,
    temporal smoothing, lip-sync analysis, and biological signal detection.
    """

    def __init__(
        self,
        device: torch.device,
        meso_model: torch.nn.Module,
        xception_model: torch.nn.Module,
        face_detection_enabled: bool = True,
        frame_interval: int = 5,
        batch_size: int = 16,
    ) -> None:
        self.device = device
        self.meso_model = meso_model
        self.xception_model = xception_model
        self.face_detection_enabled = face_detection_enabled
        self.frame_interval = frame_interval
        self.batch_size = batch_size
        self._mtcnn = None

    @property
    def mtcnn(self):
        if self._mtcnn is None:
            try:
                from facenet_pytorch import MTCNN
                self._mtcnn = MTCNN(keep_all=True, device=self.device)
            except ImportError:
                logger.warning("facenet_pytorch not installed; face detection disabled")
                self._mtcnn = None
        return self._mtcnn

    async def extract_frames(
        self, video_bytes: bytes, max_frames: int = 150,
    ) -> list[np.ndarray]:
        """Extract frames from video bytes at configured interval."""
        frames: list[np.ndarray] = []
        try:
            import cv2
        except ImportError:
            logger.error("opencv-python not installed; cannot extract frames")
            return frames

        cap = cv2.VideoCapture(io.BytesIO(video_bytes))
        if not cap.isOpened():
            cap.release()
            temp_path = f"/tmp/_deepfake_video_{hash(video_bytes)}.mp4"
            with open(temp_path, "wb") as f:
                f.write(video_bytes)
            cap = cv2.VideoCapture(temp_path)

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % self.frame_interval == 0 and len(frames) < max_frames:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
            frame_count += 1

        cap.release()
        logger.info(f"Extracted {len(frames)} frames from {total_frames} total")
        return frames

    def detect_faces(self, frames: list[np.ndarray]) -> list[Optional[np.ndarray]]:
        """Detect and crop faces from frames using MTCNN."""
        if not self.face_detection_enabled or self.mtcnn is None:
            return [self._resize(f) for f in frames]

        cropped: list[Optional[np.ndarray]] = []
        for frame in frames:
            try:
                boxes, probs = self.mtcnn.detect(frame)
                if boxes is not None and len(boxes) > 0:
                    best = boxes[0]
                    x1, y1, x2, y2 = [int(max(0, v)) for v in best[:4]]
                    face = frame[y1:y2, x1:x2]
                    if face.size > 0:
                        cropped.append(self._resize(face))
                    else:
                        cropped.append(self._resize(frame))
                else:
                    cropped.append(self._resize(frame))
            except Exception:
                cropped.append(self._resize(frame))
        return cropped

    def _resize(self, img: np.ndarray, size: int = 256) -> np.ndarray:
        try:
            import cv2
            return cv2.resize(img, (size, size))
        except ImportError:
            from PIL import Image
            pil = Image.fromarray(img).resize((size, size))
            return np.array(pil)

    def _preprocess(self, face: np.ndarray) -> torch.Tensor:
        face_t = torch.from_numpy(face).permute(2, 0, 1).float() / 255.0
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        return (face_t - mean) / std

    @torch.no_grad()
    def classify_frames(
        self, faces: list[np.ndarray],
    ) -> tuple[list[float], list[float], list[np.ndarray]]:
        """Classify each face crop and return scores and Grad-CAM heatmaps."""
        scores_meso: list[float] = []
        scores_xcep: list[float] = []
        heatmaps: list[np.ndarray] = []

        for i in range(0, len(faces), self.batch_size):
            batch_faces = faces[i:i + self.batch_size]
            tensors = torch.stack([self._preprocess(f) for f in batch_faces]).to(self.device)

            m_out = self.meso_model(tensors)
            x_out, _ = self.xception_model(tensors)

            m_probs = F.softmax(m_out, dim=1)[:, 1].cpu().numpy()
            x_probs = F.softmax(x_out, dim=1)[:, 1].cpu().numpy()

            scores_meso.extend(m_probs.tolist())
            scores_xcep.extend(x_probs.tolist())

            for idx in range(len(batch_faces)):
                heatmaps.append(self._compute_gradcam(tensors[idx:idx+1], self.meso_model))

        return scores_meso, scores_xcep, heatmaps

    def _compute_gradcam(
        self, tensor: torch.Tensor, model: torch.nn.Module,
        target_layer: Optional[torch.nn.Module] = None,
    ) -> np.ndarray:
        """Compute Grad-CAM heatmap for explainability."""
        try:
            model.eval()
            gradients: list[torch.Tensor] = []
            activations: list[torch.Tensor] = []

            def forward_hook(m, inp, out):
                activations.append(out)

            def backward_hook(m, grad_in, grad_out):
                gradients.append(grad_out[0])

            target = target_layer
            if target is None:
                for module in model.modules():
                    if isinstance(module, (torch.nn.Conv2d, torch.nn.BatchNorm2d)):
                        target = module

            if target is not None:
                fwd_handle = target.register_forward_hook(forward_hook)
                bwd_handle = target.register_backward_hook(backward_hook)

                out = model(tensor)
                pred = out.argmax(dim=1)
                model.zero_grad()
                out[0, pred].backward()

                fwd_handle.remove()
                bwd_handle.remove()

                if activations and gradients:
                    weights = gradients[0].mean(dim=(2, 3), keepdim=True)
                    cam = (weights * activations[0]).sum(dim=1, keepdim=True)
                    cam = F.relu(cam)
                    cam = F.interpolate(cam, size=(256, 256), mode="bilinear", align_corners=False)
                    cam_np = cam[0, 0].cpu().numpy()
                    cam_np = (cam_np - cam_np.min()) / (cam_np.max() - cam_np.min() + 1e-8)
                    return cam_np

            return np.zeros((256, 256), dtype=np.float32)
        except Exception as exc:
            logger.warning(f"Grad-CAM failed: {exc}")
            return np.zeros((256, 256), dtype=np.float32)

    def temporal_smoothing(
        self, scores: list[float], window: int = 5,
    ) -> list[float]:
        """Apply moving-average temporal smoothing to frame scores."""
        if len(scores) < window:
            return scores
        smoothed = []
        half = window // 2
        for i in range(len(scores)):
            lo = max(0, i - half)
            hi = min(len(scores), i + half + 1)
            smoothed.append(sum(scores[lo:hi]) / (hi - lo))
        return smoothed

    def lip_sync_analysis(
        self, video_bytes: bytes, audio_bytes: Optional[bytes] = None,
    ) -> dict[str, Any]:
        """Analyze lip-sync by checking audio-visual alignment."""
        result: dict[str, Any] = {
            "lip_sync_score": 0.0,
            "mismatch_detected": False,
            "confidence": 0.0,
        }
        try:
            import cv2
            import scipy.signal
        except ImportError:
            return result

        if audio_bytes is None:
            return result

        try:
            frames = []
            cap = cv2.VideoCapture(io.BytesIO(video_bytes))
            while len(frames) < 30:
                ret, frame = cap.read()
                if not ret:
                    break
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                mouth_region = gray[gray.shape[0]//2:, gray.shape[1]//4:3*gray.shape[1]//4]
                frames.append(mouth_region.mean())
            cap.release()

            if len(frames) < 10:
                return result

            from scipy.io import wavfile
            import io as _io
            sample_rate, audio_data = wavfile.read(_io.BytesIO(audio_bytes))
            if audio_data.ndim > 1:
                audio_data = audio_data.mean(axis=1)

            audio_frames = audio_data[::sample_rate // 30][:len(frames)]
            audio_norm = (audio_frames - audio_frames.mean()) / (audio_frames.std() + 1e-8)
            video_norm = (np.array(frames) - np.mean(frames)) / (np.std(frames) + 1e-8)

            if len(audio_norm) < 5 or len(video_norm) < 5:
                return result

            cc = np.correlate(video_norm, audio_norm, mode="full")
            lag = np.argmax(cc) - len(video_norm) + 1
            max_corr = cc.max() / (len(video_norm) * np.std(video_norm) * np.std(audio_norm) + 1e-8)

            result["lip_sync_score"] = float(max_corr)
            result["mismatch_detected"] = abs(max_corr) < 0.15 or abs(lag) > 10
            result["confidence"] = float(min(1.0, abs(max_corr) * 2.0))
            result["lag_frames"] = int(lag)
        except Exception as exc:
            logger.warning(f"Lip-sync analysis failed: {exc}")

        return result

    def biological_signal_detection(
        self, frames: list[np.ndarray],
    ) -> dict[str, Any]:
        """Detect biological signals (ballistocardiograph / micro-movements) from face video.

        Real face videos contain subtle periodic color/ motion changes from blood flow;
        deepfakes lack these signals.
        """
        result: dict[str, Any] = {
            "heartbeat_detected": False,
            "bvp_confidence": 0.0,
            "signal_present": False,
        }
        if len(frames) < 30:
            return result

        try:
            roi_means = []
            for f in frames:
                h, w = f.shape[:2]
                roi = f[h//3:2*h//3, w//3:2*w//3]
                roi_means.append(roi.mean(axis=(0, 1)))

            signal = np.array(roi_means)[:, 0]
            signal = signal - np.mean(signal)
            if np.std(signal) < 1e-6:
                return result

            from scipy import signal as scisig
            sos = scisig.butter(4, [0.8, 3.0], btype="band", fs=30.0, output="sos")
            filtered = scisig.sosfilt(sos, signal)

            peaks, _ = scisig.find_peaks(filtered, distance=10)
            if len(peaks) > 2:
                intervals = np.diff(peaks) / 30.0
                bpm = 60.0 / intervals.mean() if intervals.mean() > 0 else 0.0
                result["heartbeat_detected"] = True
                result["bvp_confidence"] = float(min(1.0, len(peaks) / 15.0))
                result["signal_present"] = True
                result["estimated_bpm"] = float(bpm)
            else:
                spectral_energy = np.sum(filtered ** 2)
                result["heartbeat_detected"] = False
                result["bvp_confidence"] = float(min(0.5, spectral_energy * 0.01))
                result["signal_present"] = spectral_energy > 0.001

        except Exception as exc:
            logger.warning(f"Biological signal detection failed: {exc}")

        return result

    async def run(
        self, video_bytes: bytes, audio_bytes: Optional[bytes] = None,
        progress_callback: Optional[callable] = None,
    ) -> dict[str, Any]:
        """Run the full video analysis pipeline."""
        if progress_callback:
            await progress_callback(5, "Extracting frames")

        frames = await self.extract_frames(video_bytes)

        if progress_callback:
            await progress_callback(20, f"Extracted {len(frames)} frames")

        faces = self.detect_faces(frames)

        if progress_callback:
            await progress_callback(35, "Classifying frames")

        scores_meso, scores_xcep, heatmaps = self.classify_faces(faces)

        smoothed_meso = self.temporal_smoothing(scores_meso)
        smoothed_xcep = self.temporal_smoothing(scores_xcep)

        mean_meso = float(np.mean(smoothed_meso)) if smoothed_meso else 0.0
        mean_xcep = float(np.mean(smoothed_xcep)) if smoothed_xcep else 0.0

        if progress_callback:
            await progress_callback(60, "Analyzing lip-sync")

        lip_sync = self.lip_sync_analysis(video_bytes, audio_bytes)

        if progress_callback:
            await progress_callback(75, "Detecting biological signals")

        bio = self.biological_signal_detection(faces)

        if progress_callback:
            await progress_callback(90, "Computing final scores")

        ensemble_score = 0.4 * mean_meso + 0.4 * mean_xcep
        if lip_sync.get("mismatch_detected", False):
            ensemble_score += 0.2
        if not bio.get("signal_present", False):
            ensemble_score += 0.1

        ensemble_score = min(1.0, ensemble_score)

        variance = float(np.var(smoothed_meso)) if len(smoothed_meso) > 1 else 0.0

        return {
            "modality": "video",
            "models_used": ["meso4", "xception_fingerprint"],
            "frame_count": len(frames),
            "face_count": len([f for f in faces if f is not None]),
            "scores": {
                "meso4": mean_meso,
                "xception_fingerprint": mean_xcep,
            },
            "per_frame_scores": {
                "meso4": smoothed_meso,
                "xception_fingerprint": smoothed_xcep,
            },
            "ensemble_score": ensemble_score,
            "variance": variance,
            "lip_sync": lip_sync,
            "biological_signals": bio,
            "is_deepfake": ensemble_score > 0.5,
            "heatmaps": [h.tolist() for h in heatmaps] if heatmaps else [],
        }

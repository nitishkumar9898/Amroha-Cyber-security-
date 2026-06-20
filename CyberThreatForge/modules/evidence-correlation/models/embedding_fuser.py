"""Multi-modal embedding fusion for evidence similarity search.

Generates embeddings from heterogeneous evidence types (text via BERT,
images via ResNet, binaries via CNN) and fuses them for cross-modal
similarity computation with approximate nearest neighbor search.
"""

import json
import logging
import math
import os
from dataclasses import dataclass, field
from typing import Any, Optional, Union

import numpy as np

try:
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    PCA = None
    StandardScaler = None

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    umap = None

try:
    import torch
    import torch.nn as nn
    from transformers import AutoModel, AutoTokenizer
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    nn = None
    AutoModel = None
    AutoTokenizer = None
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)

TEXT_MODEL_NAME = "bert-base-uncased"
IMAGE_MODEL_NAME = "resnet50"
EMBEDDING_DIM = 128
TEXT_EMBED_DIM = 768
IMAGE_EMBED_DIM = 2048
BINARY_EMBED_DIM = 256


@dataclass
class FusedEmbedding:
    evidence_id: str
    modality: str
    embedding: list[float]
    reduced_embedding: Optional[list[float]] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SimilarityMatch:
    evidence_id: str
    similarity: float
    modality: str
    metadata: dict[str, Any] = field(default_factory=dict)


class TextEmbedder:
    def __init__(self, model_name: str = TEXT_MODEL_NAME, device: str = "cpu"):
        self.device = device
        self.model_name = model_name
        self._tokenizer = None
        self._model = None
        self._load_model()

    def _load_model(self):
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch/Transformers not available; text embedder disabled")
            return
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=True)
            self._model = AutoModel.from_pretrained(self.model_name, local_files_only=True)
            self._model.to(self.device)
            self._model.eval()
            logger.info("Loaded text model: %s", self.model_name)
        except Exception:
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self._model = AutoModel.from_pretrained(self.model_name)
                self._model.to(self.device)
                self._model.eval()
                logger.info("Loaded text model (remote): %s", self.model_name)
            except Exception as e:
                logger.warning("Failed to load text model %s: %s", self.model_name, e)

    @property
    def available(self) -> bool:
        return self._model is not None and self._tokenizer is not None

    def embed(self, text: str) -> np.ndarray:
        if not self.available:
            return self._fallback_embed(text, TEXT_EMBED_DIM)

        inputs = self._tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512, padding=True
        ).to(self.device)

        with torch.no_grad():
            outputs = self._model(**inputs)
            emb = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()

        return emb

    @staticmethod
    def _fallback_embed(text: str, dim: int = TEXT_EMBED_DIM) -> np.ndarray:
        rng = np.random.RandomState(hash(text) % (2**31))
        emb = rng.randn(dim)
        emb = emb / (np.linalg.norm(emb) + 1e-8)
        return emb


class ImageEmbedder:
    def __init__(self, device: str = "cpu"):
        self.device = device
        self._model = None
        self._load_model()

    def _load_model(self):
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available; image embedder disabled")
            return
        try:
            import torchvision.models as models
            self._model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
            self._model = nn.Sequential(*list(self._model.children())[:-1])
            self._model.to(self.device)
            self._model.eval()
            logger.info("Loaded image model: resnet50")
        except Exception as e:
            logger.warning("Failed to load image model: %s", e)

    @property
    def available(self) -> bool:
        return self._model is not None

    def embed(self, image_data: Union[bytes, np.ndarray, str]) -> np.ndarray:
        if not self.available:
            return self._fallback_embed(IMAGE_EMBED_DIM)

        try:
            from PIL import Image
            import torchvision.transforms as T

            if isinstance(image_data, bytes):
                import io
                img = Image.open(io.BytesIO(image_data)).convert("RGB")
            elif isinstance(image_data, str):
                img = Image.open(image_data).convert("RGB")
            elif isinstance(image_data, np.ndarray):
                from PIL import Image as PILImage
                img = PILImage.fromarray(
                    (image_data * 255).astype(np.uint8) if image_data.max() <= 1.0
                    else image_data.astype(np.uint8)
                ).convert("RGB")
            else:
                return self._fallback_embed(IMAGE_EMBED_DIM)

            transform = T.Compose([
                T.Resize(224),
                T.CenterCrop(224),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
            tensor = transform(img).unsqueeze(0).to(self.device)

            with torch.no_grad():
                emb = self._model(tensor).squeeze().cpu().numpy()

            return emb
        except Exception as e:
            logger.warning("Image embedding failed: %s", e)
            return self._fallback_embed(IMAGE_EMBED_DIM)

    @staticmethod
    def _fallback_embed(dim: int = IMAGE_EMBED_DIM) -> np.ndarray:
        return np.random.randn(dim) / math.sqrt(dim)


class BinaryEmbedder:
    def __init__(self, device: str = "cpu"):
        self.device = device
        self._model = None
        self._load_model()

    def _load_model(self):
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available; binary embedder disabled")
            return
        try:
            self._model = BinaryCNN()
            self._model.to(self.device)
            self._model.eval()
            logger.info("Loaded binary embedder (CNN)")
        except Exception as e:
            logger.warning("Failed to load binary model: %s", e)

    @property
    def available(self) -> bool:
        return self._model is not None

    def embed(self, data: bytes) -> np.ndarray:
        if not self.available:
            return self._fallback_embed(BINARY_EMBED_DIM)

        try:
            arr = np.frombuffer(data, dtype=np.uint8).astype(np.float32)
            arr = (arr / 255.0) * 2.0 - 1.0
            max_len = 2 * 1024 * 1024
            if len(arr) > max_len:
                arr = arr[:max_len]
            elif len(arr) < max_len:
                arr = np.pad(arr, (0, max_len - len(arr)))

            arr = arr.reshape(1, 1, -1)
            tensor = torch.from_numpy(arr).to(self.device)

            with torch.no_grad():
                emb = self._model(tensor).squeeze().cpu().numpy()

            return emb
        except Exception as e:
            logger.warning("Binary embedding failed: %s", e)
            return self._fallback_embed(BINARY_EMBED_DIM)

    @staticmethod
    def _fallback_embed(dim: int = BINARY_EMBED_DIM) -> np.ndarray:
        return np.random.randn(dim) / math.sqrt(dim)


if TORCH_AVAILABLE and nn is not None:
    class BinaryCNN(nn.Module):
        def __init__(self, in_channels: int = 1, embedding_dim: int = BINARY_EMBED_DIM):
            super().__init__()
            self.convs = nn.Sequential(
                nn.Conv1d(in_channels, 64, kernel_size=64, stride=16, padding=32),
                nn.ReLU(),
                nn.MaxPool1d(2),
                nn.Conv1d(64, 128, kernel_size=32, stride=8, padding=16),
                nn.ReLU(),
                nn.MaxPool1d(2),
                nn.Conv1d(128, 256, kernel_size=16, stride=4, padding=8),
                nn.ReLU(),
                nn.AdaptiveAvgPool1d(1),
            )
            self.fc = nn.Linear(256, embedding_dim)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            x = self.convs(x)
            x = x.squeeze(-1)
            x = self.fc(x)
            x = nn.functional.normalize(x, p=2, dim=1)
            return x
else:
    BinaryCNN = None


class EmbeddingFuser:
    def __init__(
        self,
        reduction_method: str = "pca",
        target_dim: int = EMBEDDING_DIM,
        device: str = "cpu",
    ):
        self.reduction_method = reduction_method.lower()
        self.target_dim = target_dim
        self.device = device
        self._text_embedder = TextEmbedder(device=device)
        self._image_embedder = ImageEmbedder(device=device)
        self._binary_embedder = BinaryEmbedder(device=device)
        self._reducer: Optional[Union[PCA, Any]] = None
        self._scaler: Optional[Any] = None
        self._embedding_cache: dict[str, FusedEmbedding] = {}

    def embed_text(self, text: str) -> np.ndarray:
        return self._text_embedder.embed(text)

    def embed_image(self, image_data: Union[bytes, np.ndarray, str]) -> np.ndarray:
        return self._image_embedder.embed(image_data)

    def embed_binary(self, data: bytes) -> np.ndarray:
        return self._binary_embedder.embed(data)

    def fuse_embeddings(
        self,
        embeddings: list[np.ndarray],
        weights: Optional[list[float]] = None,
    ) -> np.ndarray:
        if not embeddings:
            return np.zeros(self.target_dim)

        if weights is None:
            weights = [1.0 / len(embeddings)] * len(embeddings)

        weights = np.array(weights) / sum(weights)

        projected = []
        for emb in embeddings:
            if len(emb) != self.target_dim:
                projected.append(self._project(emb))
            else:
                projected.append(emb)

        fused = sum(w * p for w, p in zip(weights, projected))
        fused = fused / (np.linalg.norm(fused) + 1e-8)
        return fused

    def embed_evidence(
        self,
        evidence_id: str,
        modality: str,
        data: Any,
        metadata: Optional[dict[str, Any]] = None,
    ) -> FusedEmbedding:
        cache_key = f"{evidence_id}_{modality}"
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        if modality == "text":
            raw_emb = self.embed_text(str(data))
        elif modality == "image":
            raw_emb = self.embed_image(data)
        elif modality == "binary":
            raw_emb = self.embed_binary(data)
        elif modality == "network":
            raw_emb = self.embed_text(json.dumps(data, default=str))
        elif modality == "multi":
            raw_emb = self._embed_multi(data)
        else:
            raw_emb = self.embed_text(str(data))

        reduced = self.reduce_dim(raw_emb) if raw_emb.shape[0] > 0 else raw_emb

        fused = FusedEmbedding(
            evidence_id=evidence_id,
            modality=modality,
            embedding=raw_emb.tolist(),
            reduced_embedding=reduced.tolist() if reduced is not None else None,
            metadata=metadata or {},
        )
        self._embedding_cache[cache_key] = fused
        return fused

    def compute_similarity(
        self,
        emb_a: Union[list[float], np.ndarray],
        emb_b: Union[list[float], np.ndarray],
        metric: str = "cosine",
    ) -> float:
        a = np.array(emb_a)
        b = np.array(emb_b)

        if metric == "cosine":
            norm = np.linalg.norm(a) * np.linalg.norm(b)
            return float(np.dot(a, b) / (norm + 1e-8))
        elif metric == "euclidean":
            return float(1.0 / (1.0 + np.linalg.norm(a - b)))
        elif metric == "dot":
            return float(np.dot(a, b))
        else:
            norm = np.linalg.norm(a) * np.linalg.norm(b)
            return float(np.dot(a, b) / (norm + 1e-8))

    def find_similar(
        self,
        query_embedding: Union[list[float], np.ndarray],
        candidates: list[FusedEmbedding],
        top_k: int = 10,
        threshold: float = 0.0,
    ) -> list[SimilarityMatch]:
        query = np.array(query_embedding)
        scores: list[tuple[float, FusedEmbedding]] = []

        for cand in candidates:
            cand_emb = cand.reduced_embedding or cand.embedding
            sim = self.compute_similarity(query, cand_emb)
            if sim >= threshold:
                scores.append((sim, cand))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [
            SimilarityMatch(
                evidence_id=cand.evidence_id,
                similarity=sim,
                modality=cand.modality,
                metadata=cand.metadata,
            )
            for sim, cand in scores[:top_k]
        ]

    def reduce_dim(self, embedding: np.ndarray) -> np.ndarray:
        orig_dim = embedding.shape[0]
        if orig_dim <= self.target_dim:
            return embedding

        reshaped = embedding.reshape(1, -1)
        n_samples, n_features = reshaped.shape
        max_components = min(n_samples, n_features) - 1

        if max_components < 1:
            return embedding[:self.target_dim]

        if self._reducer is not None:
            try:
                return self._reducer.transform(reshaped).flatten()
            except Exception:
                pass

        effective_dim = min(self.target_dim, max_components)

        if self.reduction_method == "umap" and UMAP_AVAILABLE:
            reducer = umap.UMAP(n_components=effective_dim, random_state=42)
            return reducer.fit_transform(reshaped).flatten()
        elif self.reduction_method == "pca" and SKLEARN_AVAILABLE:
            pca = PCA(n_components=effective_dim)
            return pca.fit_transform(reshaped).flatten()
        else:
            return embedding[:self.target_dim]

    def fit_reducer(
        self,
        embeddings: list[np.ndarray],
    ):
        if not embeddings:
            return
        matrix = np.stack(embeddings)

        if self.reduction_method == "umap" and UMAP_AVAILABLE:
            self._reducer = umap.UMAP(n_components=self.target_dim, random_state=42)
            self._reducer.fit(matrix)
        elif self.reduction_method == "pca" and SKLEARN_AVAILABLE:
            self._scaler = StandardScaler()
            scaled = self._scaler.fit_transform(matrix)
            self._reducer = PCA(n_components=self.target_dim)
            self._reducer.fit(scaled)

    def clear_cache(self):
        self._embedding_cache.clear()

    def _project(self, emb: np.ndarray) -> np.ndarray:
        if len(emb) <= self.target_dim:
            return emb
        if self._reducer is not None:
            try:
                return self._reducer.transform(emb.reshape(1, -1)).flatten()
            except Exception:
                pass
        return emb[:self.target_dim]

    def _embed_multi(self, data: Any) -> np.ndarray:
        embeddings: list[np.ndarray] = []

        if isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, str) and len(val) > 10:
                    embeddings.append(self.embed_text(val))
                elif isinstance(val, (bytes, bytearray)):
                    embeddings.append(self.embed_binary(bytes(val)))

        if not embeddings:
            return self._fallback_embed()

        target = max(e.shape[0] for e in embeddings)
        aligned = []
        for e in embeddings:
            if e.shape[0] < target:
                e = np.pad(e, (0, target - e.shape[0]))
            elif e.shape[0] > target:
                e = e[:target]
            aligned.append(e)

        return np.mean(aligned, axis=0)

    @staticmethod
    def _fallback_embed(dim: int = EMBEDDING_DIM) -> np.ndarray:
        return np.random.randn(dim) / math.sqrt(dim)

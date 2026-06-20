# backend/app/ai_layer/behavioral_models.py
"""
AI layer for PsycheGuard behavioral profiling.
Provides a simple wrapper around a transformer model to generate embeddings
and perform basic clustering / anomaly detection for user digital footprints.
"""
from typing import List, Dict

# Placeholder import – in a real deployment you would use a model like
# sentence-transformers/DistilBERT fine‑tuned for social‑engineering detection.
# For this codebase we keep it lightweight and avoid heavy dependencies.

class BehavioralProfiler:
    """Utility class to generate a profile from a user's digital footprint.

    The implementation uses a very lightweight heuristic approach because the
    environment may not have large transformer models installed. The methods are
    intentionally simple but expose a clear API for future model upgrades.
    """

    def __init__(self):
        # In a production scenario you would load a pretrained model here.
        # Example: self.model = SentenceTransformer('distilbert-base-nli-stsb-mean-tokens')
        pass

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate dummy embeddings (list of floats) for each text.
        This stub returns a fixed‑size vector of zeros; replace with a real
        embedding model when available.
        """
        # Fixed 768‑dim zero vector for simplicity
        return [[0.0] * 768 for _ in texts]

    def profile(self, footprint: Dict[str, any]) -> Dict[str, any]:
        """Create a behavioral profile for a user.

        Parameters
        ----------
        footprint: dict
            Normalized digital footprint as produced by
            ``backend/app/modules/behavioral.parse_digital_footprint``.

        Returns
        -------
        dict
            A structured profile containing:
            * ``embedding`` – list of floats (placeholder)
            * ``social_engineering`` – result from ``detect_social_engineering``
            * ``insider_threat_score`` – float between 0 and 1
        """
        from ..modules.behavioral import (
            detect_social_engineering,
            insider_threat_score,
            parse_digital_footprint,
        )

        normalized = parse_digital_footprint(footprint)
        messages = " ".join(normalized.get("messages", []))
        se_result = detect_social_engineering(messages)
        insider_score = insider_threat_score(normalized.get("activities", []))
        embedding = self._embed_texts([messages])[0]
        return {
            "embedding": embedding,
            "social_engineering": se_result,
            "insider_threat_score": insider_score,
        }

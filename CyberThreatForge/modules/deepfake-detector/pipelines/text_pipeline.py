import math
import logging
import hashlib
from typing import Any, Optional

import torch
import numpy as np

logger = logging.getLogger(__name__)


class TextPipeline:
    """Text analysis pipeline for LLM-generated text detection.

    Performs perplexity scoring, burstiness analysis, watermark detection
    (KGW scheme), and stylometric feature extraction.
    """

    def __init__(self, device: torch.device) -> None:
        self.device = device
        self._lm_model = None
        self._lm_tokenizer = None

    @property
    def lm(self):
        if self._lm_model is None:
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                model_name = "gpt2"
                self._lm_tokenizer = AutoTokenizer.from_pretrained(model_name)
                self._lm_model = AutoModelForCausalLM.from_pretrained(model_name).to(self.device)
                self._lm_model.eval()
            except Exception:
                logger.warning("Could not load LM for perplexity; using fallback")
                self._lm_model = None
        return self._lm_model, self._lm_tokenizer

    @torch.no_grad()
    def perplexity_scoring(self, text: str) -> dict[str, Any]:
        """Compute per-token perplexity using a causal language model.

        Lower perplexity on small LMs is a weak signal for AI-generated text.
        """
        model, tokenizer = self.lm
        if model is None or tokenizer is None:
            return {"perplexity": None, "log_perplexity": None, "error": "LM not available"}

        try:
            encodings = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            input_ids = encodings.input_ids.to(self.device)

            outputs = model(input_ids, labels=input_ids)
            loss = outputs.loss
            perplexity = float(torch.exp(loss).cpu())

            log_probs = []
            for i in range(1, input_ids.size(1)):
                out = model(input_ids[:, :i])
                logits = out.logits[:, -1, :]
                log_prob = torch.log_softmax(logits, dim=-1)[0, input_ids[0, i]]
                log_probs.append(float(log_prob.cpu()))

            return {
                "perplexity": perplexity,
                "log_perplexity": math.log(perplexity) if perplexity > 0 else 0.0,
                "token_log_probs": log_probs[:50],
                "mean_log_prob": float(np.mean(log_probs)) if log_probs else 0.0,
                "tokens_analyzed": input_ids.size(1),
            }
        except Exception as exc:
            logger.warning(f"Perplexity scoring failed: {exc}")
            return {"perplexity": None, "log_perplexity": None, "error": str(exc)}

    def burstiness_analysis(self, text: str) -> dict[str, Any]:
        """Analyze token burstiness — human text has bursty rare-token patterns;
        LLM text tends to use tokens more uniformly.
        """
        try:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained("gpt2")
        except Exception:
            tokenizer = None

        if tokenizer is None:
            return {"burstiness_score": 0.5, "distribution": "unknown"}

        tokens = tokenizer.encode(text)
        if len(tokens) < 5:
            return {"burstiness_score": 0.5, "distribution": "insufficient_length"}

        token_counts: dict[int, int] = {}
        for t in tokens:
            token_counts[t] = token_counts.get(t, 0) + 1

        freqs = list(token_counts.values())
        if len(freqs) < 2:
            return {"burstiness_score": 0.5, "distribution": "uniform"}

        mean_freq = np.mean(freqs)
        std_freq = np.std(freqs)
        cv = std_freq / (mean_freq + 1e-8)

        entropy = -sum((c / len(tokens)) * math.log(c / len(tokens) + 1e-10) for c in freqs)
        max_entropy = math.log(len(freqs)) if len(freqs) > 1 else 1.0
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 1.0

        type_token_ratio = len(freqs) / len(tokens)

        burstiness_score = 1.0 - normalized_entropy
        is_low_burstiness = burstiness_score < 0.3

        return {
            "burstiness_score": float(burstiness_score),
            "coefficient_of_variation": float(cv),
            "type_token_ratio": float(type_token_ratio),
            "normalized_entropy": float(normalized_entropy),
            "distribution": "ai" if is_low_burstiness else "human_like",
            "is_ai_generated": is_low_burstiness,
        }

    def watermark_detection(self, text: str) -> dict[str, Any]:
        """Detect KGW (Kirchenbauer et al.) watermarks in LLM-generated text.

        Implements a simplified version of the green/red token list split.
        """
        result: dict[str, Any] = {
            "watermark_detected": False,
            "green_token_ratio": 0.0,
            "z_score": 0.0,
            "confidence": 0.0,
        }

        try:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained("gpt2")
        except Exception:
            return result

        tokens = tokenizer.encode(text)
        if len(tokens) < 10:
            return result

        seed = 42
        vocab_size = 50257
        gamma = 0.5
        delta = 2.0

        rng = np.random.RandomState(seed)
        green_mask = rng.rand(vocab_size) < gamma
        green_list = set(np.where(green_mask)[0].tolist())

        green_count = sum(1 for t in tokens if t in green_list)
        total = len(tokens)
        green_ratio = green_count / total

        expected = gamma
        variance = gamma * (1 - gamma) / total
        std = math.sqrt(variance) if variance > 0 else 1.0
        z_score = (green_ratio - expected) / std

        score = z_score / delta
        confidence = min(1.0, max(0.0, (score - 1.0) / 3.0)) if score > 1.0 else 0.0

        result["watermark_detected"] = confidence > 0.5
        result["green_token_ratio"] = float(green_ratio)
        result["z_score"] = float(z_score)
        result["confidence"] = float(confidence)
        result["scheme"] = "kgw"

        return result

    def stylometric_analysis(self, text: str) -> dict[str, Any]:
        """Extract stylometric features: sentence length variance,
        punctuation ratio, lexical diversity, etc.

        LLM text often has more uniform stylometric features.
        """
        import re

        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return {"error": "no sentences found"}

        sent_lengths = [len(s.split()) for s in sentences]

        words = re.findall(r"\w+", text.lower())
        unique_words = set(words)
        lexical_diversity = len(unique_words) / len(words) if words else 0.0

        punctuation = sum(1 for c in text if c in ".,;:!?\"'()-")
        punct_ratio = punctuation / len(text) if text else 0.0

        uppercase = sum(1 for c in text if c.isupper())
        uppercase_ratio = uppercase / len(text) if text else 0.0

        sent_len_mean = float(np.mean(sent_lengths)) if sent_lengths else 0.0
        sent_len_std = float(np.std(sent_lengths)) if len(sent_lengths) > 1 else 0.0
        sent_len_cv = sent_len_std / (sent_len_mean + 1e-8)

        def _flesch_kincaid(text: str) -> float:
            syllables = 0
            for w in words:
                syllables += max(1, len(w) // 3)
            return (206.835 - 1.015 * (len(words) / len(sentences))
                    - 84.6 * (syllables / len(words)))

        fk_score = _flesch_kincaid(text)

        high_repetition = sent_len_cv < 0.3 and len(sentences) > 3

        return {
            "sentence_count": len(sentences),
            "sentence_length_mean": sent_len_mean,
            "sentence_length_std": sent_len_std,
            "sentence_length_cv": sent_len_cv,
            "lexical_diversity": float(lexical_diversity),
            "punctuation_ratio": punct_ratio,
            "uppercase_ratio": uppercase_ratio,
            "flesch_kincaid": fk_score,
            "high_uniformity": high_repetition,
            "is_ai_generated": high_repetition,
        }

    async def run(
        self, text: str,
        progress_callback: Optional[callable] = None,
    ) -> dict[str, Any]:
        """Run the full text analysis pipeline."""
        if not text or not text.strip():
            return {"error": "empty text input"}

        if progress_callback:
            await progress_callback(10, "Computing perplexity")

        perplexity = self.perplexity_scoring(text)

        if progress_callback:
            await progress_callback(35, "Analyzing burstiness")

        burstiness = self.burstiness_analysis(text)

        if progress_callback:
            await progress_callback(55, "Detecting watermarks")

        watermark = self.watermark_detection(text)

        if progress_callback:
            await progress_callback(75, "Extracting stylometric features")

        stylometry = self.stylometric_analysis(text)

        if progress_callback:
            await progress_callback(90, "Fusing results")

        scores = []
        weights = []

        ppl = perplexity.get("perplexity")
        if ppl is not None:
            ppl_score = min(1.0, ppl / 100.0) if ppl > 0 else 0.5
            scores.append(ppl_score)
            weights.append(0.3)

        burst_score = burstiness.get("burstiness_score", 0.5)
        scores.append(1.0 - burst_score)
        weights.append(0.25)

        wm_conf = watermark.get("confidence", 0.0)
        scores.append(wm_conf)
        weights.append(0.25)

        style_uniform = 1.0 if stylometry.get("high_uniformity", False) else 0.0
        scores.append(style_uniform)
        weights.append(0.20)

        if weights:
            ensemble_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        else:
            ensemble_score = 0.5

        return {
            "modality": "text",
            "models_used": ["gpt2_perplexity", "kgw_watermark", "stylometric"],
            "perplexity": perplexity,
            "burstiness": burstiness,
            "watermark": watermark,
            "stylometry": stylometry,
            "ensemble_score": float(ensemble_score),
            "is_deepfake": ensemble_score > 0.5,
        }

import hashlib
import logging
import math
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger("sentiment_tracker")


class AspectSentimentModel(nn.Module):
    def __init__(self, vocab_size: int = 10000, embed_dim: int = 256, num_heads: int = 8, num_layers: int = 4):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        encoder_layer = nn.TransformerEncoderLayer(d_model=embed_dim, nhead=num_heads, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.aspect_proj = nn.Linear(embed_dim, embed_dim)
        self.sentiment_head = nn.Linear(embed_dim, 3)

    def forward(self, x: torch.Tensor, aspect_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        x = self.embedding(x)
        x = self.transformer(x)
        if aspect_mask is not None:
            aspect_emb = (x * aspect_mask.unsqueeze(-1)).sum(dim=1) / aspect_mask.sum(dim=1, keepdim=True).clamp(min=1)
        else:
            aspect_emb = x.mean(dim=1)
        aspect_emb = F.relu(self.aspect_proj(aspect_emb))
        return F.softmax(self.sentiment_head(aspect_emb), dim=-1)


class SentimentTracker:
    def __init__(self, device: Optional[str] = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = AspectSentimentModel().to(self.device)
        self.model.eval()
        self.sentiment_history: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.entity_sentiment: dict[str, dict[str, float]] = defaultdict(lambda: {"positive": 0.0, "negative": 0.0, "neutral": 0.0})
        self.aspect_sentiments: dict[str, dict[str, dict[str, float]]] = defaultdict(lambda: defaultdict(lambda: {"positive": 0.0, "negative": 0.0, "neutral": 0.0}))

    def _analyze_text(self, text: str, aspect: Optional[str] = None) -> dict[str, float]:
        text_lower = text.lower()
        positive_words = {"good", "great", "excellent", "amazing", "awesome", "fantastic",
                          "wonderful", "secure", "safe", "trusted", "reliable", "best",
                          "impressive", "outstanding", "positive", "success", "win",
                          "beneficial", "effective", "efficient", "innovative"}
        negative_words = {"bad", "terrible", "awful", "horrible", "worst", "poor",
                          "vulnerable", "breach", "attack", "malicious", "dangerous",
                          "threat", "risk", "failure", "damage", "stolen", "leak",
                          "cracked", "infected", "compromised", "fraud", "scam"}
        intensity_words = {"very": 1.5, "extremely": 2.0, "highly": 1.8, "somewhat": 0.5,
                           "slightly": 0.3, "quite": 1.3, "barely": 0.2}
        words = text_lower.split()
        sentiment_scores = {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
        multipliers = []
        for i, w in enumerate(words):
            mult = intensity_words.get(w, 1.0)
            if mult != 1.0:
                multipliers.append(mult)
            else:
                if w in positive_words:
                    intensity = multipliers[-1] if multipliers else 1.0
                    sentiment_scores["positive"] += intensity
                    sentiment_scores["neutral"] -= 0.1
                elif w in negative_words:
                    intensity = multipliers[-1] if multipliers else 1.0
                    sentiment_scores["negative"] += intensity
                    sentiment_scores["neutral"] -= 0.1
                multipliers = []
        total = sentiment_scores["positive"] + sentiment_scores["negative"] + sentiment_scores["neutral"]
        if total > 0:
            sentiment_scores["positive"] = round(sentiment_scores["positive"] / total, 4)
            sentiment_scores["negative"] = round(sentiment_scores["negative"] / total, 4)
            sentiment_scores["neutral"] = round(sentiment_scores["neutral"] / total, 4)
        return sentiment_scores

    def analyze_sentiment(self, text: str, entity: str = "",
                          aspect: Optional[str] = None, source: str = "") -> dict[str, Any]:
        sentiment = self._analyze_text(text, aspect)
        if sentiment["positive"] > sentiment["negative"]:
            label = "positive"
            score = sentiment["positive"]
        elif sentiment["negative"] > sentiment["positive"]:
            label = "negative"
            score = sentiment["negative"]
        else:
            label = "neutral"
            score = sentiment["neutral"]
        result = {
            "text_snippet": text[:200],
            "entity": entity,
            "aspect": aspect,
            "sentiment": label,
            "score": round(score, 4),
            "distribution": sentiment,
            "source": source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "analysis_id": uuid4().hex[:16],
        }
        if entity:
            self.sentiment_history[entity].append(result)
            for cls in sentiment:
                self.entity_sentiment[entity][cls] = (
                    self.entity_sentiment[entity][cls] * 0.95 + sentiment[cls] * 0.05
                )
            if aspect:
                for cls in sentiment:
                    self.aspect_sentiments[entity][aspect][cls] = (
                        self.aspect_sentiments[entity][aspect].get(cls, 0.0) * 0.95 + sentiment[cls] * 0.05
                    )
        return result

    def get_temporal_trend(self, entity: str, window: int = 10) -> dict[str, Any]:
        history = self.sentiment_history.get(entity, [])
        if not history:
            return {"entity": entity, "trend": [], "current": "neutral", "volatility": 0.0}
        recent = history[-window:]
        trend_points = []
        for i, h in enumerate(recent):
            trend_points.append({
                "point": i + 1,
                "timestamp": h["timestamp"],
                "sentiment": h["sentiment"],
                "score": h["score"],
            })
        scores = [p["score"] for p in trend_points]
        volatility = round(np.std(scores), 4) if len(scores) > 1 else 0.0
        current = recent[-1]["sentiment"] if recent else "neutral"
        return {
            "entity": entity,
            "trend": trend_points,
            "current": current,
            "volatility": volatility,
            "direction": "improving" if len(scores) > 2 and scores[-1] > scores[0] else "declining" if len(scores) > 2 and scores[-1] < scores[0] else "stable",
        }

    def detect_anomalies(self, entity: str, z_threshold: float = 2.0) -> list[dict[str, Any]]:
        history = self.sentiment_history.get(entity, [])
        if len(history) < 5:
            return []
        scores = np.array([h["score"] for h in history])
        mean, std = scores.mean(), scores.std()
        if std < 0.01:
            return []
        anomalies = []
        for i, h in enumerate(history):
            z = (h["score"] - mean) / std
            if abs(z) > z_threshold:
                anomalies.append({
                    "index": i,
                    "timestamp": h["timestamp"],
                    "sentiment": h["sentiment"],
                    "score": round(float(h["score"]), 4),
                    "z_score": round(float(z), 4),
                    "text_snippet": h.get("text_snippet", "")[:100],
                    "flagged": True,
                })
        return anomalies

    def identify_opinion_leaders(self, posts_by_author: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        leaders = []
        for author, posts in posts_by_author.items():
            if len(posts) < 3:
                continue
            sentiment_scores = [p.get("sentiment", {}).get("score", 0.5) for p in posts]
            avg_influence = np.mean([p.get("engagement", {}).get("likes", 0) for p in posts])
            sentiment_volatility = np.std(sentiment_scores) if len(sentiment_scores) > 1 else 0
            leader_score = min(1.0, (avg_influence / 1000) * 0.4 + (len(posts) / 100) * 0.3 + (1 - sentiment_volatility) * 0.3)
            leaders.append({
                "author": author,
                "post_count": len(posts),
                "avg_engagement": round(float(avg_influence), 2),
                "sentiment_volatility": round(float(sentiment_volatility), 4),
                "leader_score": round(float(leader_score), 4),
                "dominant_sentiment": "positive" if np.mean(sentiment_scores) > 0.6 else "negative" if np.mean(sentiment_scores) < 0.4 else "neutral",
            })
        leaders.sort(key=lambda x: x["leader_score"], reverse=True)
        return leaders

    def analyze_batch(self, texts: list[dict[str, str]]) -> dict[str, Any]:
        results = []
        for item in texts:
            result = self.analyze_sentiment(
                text=item.get("text", ""),
                entity=item.get("entity", ""),
                aspect=item.get("aspect"),
                source=item.get("source", ""),
            )
            results.append(result)
        entities = list(set(item.get("entity", "") for item in texts if item.get("entity")))
        trends = {e: self.get_temporal_trend(e) for e in entities if e}
        overall_sentiment = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
        for r in results:
            for k in overall_sentiment:
                overall_sentiment[k] += r["distribution"][k]
        total = sum(overall_sentiment.values())
        if total > 0:
            overall_sentiment = {k: round(v / total, 4) for k, v in overall_sentiment.items()}
        return {
            "analysis_id": uuid4().hex[:16],
            "total_texts": len(texts),
            "results": results,
            "overall_sentiment": overall_sentiment,
            "entity_trends": trends,
            "aspects": dict(self.aspect_sentiments) if self.aspect_sentiments else {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

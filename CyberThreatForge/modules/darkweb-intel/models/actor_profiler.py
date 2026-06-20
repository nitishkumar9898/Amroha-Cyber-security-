"""Dark-web actor profiler using PyTorch.

Analyses writing style via stylometry, topic modelling, and sentiment
analysis. Correlates usernames across platforms and computes reputation
and risk scores based on activity patterns.
"""

import json
import logging
import math
import os
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# PyTorch model for actor-style classification
# -------------------------------------------------------------------------


class ActorStyleEncoder(nn.Module):
    """Lightweight encoder that maps stylometric features to an actor embedding."""

    def __init__(self, input_dim: int = 128, hidden_dim: int = 64, num_classes: int = 50) -> None:
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.bn2 = nn.BatchNorm1d(hidden_dim // 2)
        self.classifier = nn.Linear(hidden_dim // 2, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.bn1(self.fc1(x)))
        x = F.relu(self.bn2(self.fc2(x)))
        x = self.classifier(x)
        return x


# -------------------------------------------------------------------------
# Stylometry feature extraction
# -------------------------------------------------------------------------

STOP_WORDS: set[str] = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "by", "with", "from", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "can", "could", "shall", "should", "may", "might",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those", "not", "no", "nor", "so",
}


def _extract_stylometry(texts: list[str]) -> dict[str, Any]:
    combined = " ".join(texts)
    if not combined.strip():
        return {
            "avg_word_length": 0.0,
            "avg_sentence_length": 0.0,
            "ttr": 0.0,
            "uppercase_ratio": 0.0,
            "punctuation_ratio": 0.0,
            "word_count": 0,
            "sentence_count": 0,
            "unique_words": 0,
            "stopword_ratio": 0.0,
        }
    words = re.findall(r"\b\w+\b", combined)
    sentences = re.split(r"[.!?]+", combined)
    sentences = [s.strip() for s in sentences if s.strip()]

    word_count = len(words)
    sentence_count = len(sentences)
    unique_words = len(set(w.lower() for w in words))
    avg_word_len = sum(len(w) for w in words) / max(word_count, 1)
    avg_sent_len = word_count / max(sentence_count, 1)
    ttr = unique_words / max(word_count, 1)
    upper_count = sum(1 for c in combined if c.isupper())
    punct_count = sum(1 for c in combined if c in ".,!?;:\"'()-[]{}")
    stopword_count = sum(1 for w in words if w.lower() in STOP_WORDS)

    return {
        "avg_word_length": round(avg_word_len, 4),
        "avg_sentence_length": round(avg_sent_len, 4),
        "ttr": round(ttr, 4),
        "uppercase_ratio": round(upper_count / max(len(combined), 1), 4),
        "punctuation_ratio": round(punct_count / max(len(combined), 1), 4),
        "word_count": word_count,
        "sentence_count": sentence_count,
        "unique_words": unique_words,
        "stopword_ratio": round(stopword_count / max(word_count, 1), 4),
    }


def _extract_topics(texts: list[str], top_n: int = 5) -> list[str]:
    combined = " ".join(texts).lower()
    words = re.findall(r"\b[a-z]{3,}\b", combined)
    filtered = [w for w in words if w not in STOP_WORDS]
    counts = Counter(filtered)
    threat_topics = {
        "exploit", "malware", "ransomware", "phishing", "ddos", "botnet",
        "credential", "backdoor", "payload", "0day", "shell", "trojan",
        "stealer", "keylogger", "rat", "cve", "vuln", "bypass", "inject",
        "carding", "dumps", "fullz", "spam", "fraud", "scam", "leak",
        "breach", "dump", "hash", "crack", "brute", "proxy", "vpn",
        "tor", "i2p", "darknet", "market", "vendor", "ship", "escrow",
    }
    topic_scores: dict[str, int] = {}
    for word in filtered:
        if word in threat_topics:
            topic_scores[word] = topic_scores.get(word, 0) + 1
    sorted_topics = sorted(topic_scores, key=topic_scores.get, reverse=True)
    return sorted_topics[:top_n] if sorted_topics else ["general"]


def _analyze_sentiment(texts: list[str]) -> str:
    combined = " ".join(texts).lower()
    positive = {"good", "great", "excellent", "thanks", "help", "trust", "safe", "secure", "legit", "vouch"}
    negative = {"scam", "fraud", "fake", "stolen", "hack", "attack", "malicious", "danger", "warning", "ripoff"}
    words = set(re.findall(r"\b[a-z]+\b", combined))
    pos_count = len(words & positive)
    neg_count = len(words & negative)
    if pos_count > neg_count + 1:
        return "positive"
    elif neg_count > pos_count + 1:
        return "negative"
    return "neutral"


def _correlate_usernames(usernames: list[str]) -> list[str]:
    correlated: list[str] = []
    seen: set[str] = set()
    for u in usernames:
        low = u.lower().strip()
        if low and low not in seen:
            seen.add(low)
            correlated.append(u)
    return correlated


def _score_reputation(texts: list[str]) -> float:
    combined = " ".join(texts).lower()
    positive_signals = {"vouch", "trusted", "verified", "legit", "reputable", "longtime", "reliable"}
    negative_signals = {"scam", "ripoff", "fraud", "fake", "banned", "dispute", "warning"}
    words = set(re.findall(r"\b[a-z]+\b", combined))
    pos_score = len(words & positive_signals) * 10
    neg_score = len(words & negative_signals) * 15
    base = 50.0
    score = base + pos_score - neg_score
    return max(0.0, min(100.0, score))


def _score_risk(texts: list[str], topics: list[str]) -> float:
    combined = " ".join(texts).lower()
    high_risk = {"exploit", "0day", "malware", "ransomware", "botnet", "ddos", "credential"}
    medium_risk = {"carding", "spam", "phishing", "brute", "crack"}
    word_set = set(re.findall(r"\b[a-z]+\b", combined))
    high = len(word_set & high_risk) * 20
    medium = len(word_set & medium_risk) * 10
    topic_bonus = sum(20 for t in topics if t in high_risk)
    risk = min(100.0, high + medium + topic_bonus)
    return risk


# -------------------------------------------------------------------------
# Main profiler class
# -------------------------------------------------------------------------


class ActorProfiler:
    """Profiles dark-web actors from forum posts using stylometry and ML."""

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = ActorStyleEncoder().to(self.device)
        self.model.eval()
        self._model_path = model_path
        if model_path and os.path.isfile(model_path):
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                logger.info("Loaded actor profiler model from %s", model_path)
            except Exception as e:
                logger.warning("Could not load actor model: %s", e)

    async def profile(
        self,
        posts: list[str],
        usernames: Optional[list[str]] = None,
        platforms: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        usernames = usernames or []
        platforms = platforms or []

        stylometry = _extract_stylometry(posts)
        topics = _extract_topics(posts)
        sentiment = _analyze_sentiment(posts)
        correlated = _correlate_usernames(usernames)
        reputation = _score_reputation(posts)
        risk = _score_risk(posts, topics)

        # Infer actor name from most frequent username
        actor_name = correlated[0] if correlated else None
        confidence = 0.0

        # Use model for style-based classification if possible
        if stylometry["word_count"] > 0:
            feature_vector = torch.tensor(
                [
                    [
                        stylometry["avg_word_length"],
                        stylometry["avg_sentence_length"],
                        stylometry["ttr"],
                        stylometry["uppercase_ratio"],
                        stylometry["punctuation_ratio"],
                        stylometry["stopword_ratio"],
                    ]
                ]
                + [[0.0] * 122]
            ).float().to(self.device)[:, :128]
            with torch.no_grad():
                logits = self.model(feature_vector)
                probs = F.softmax(logits, dim=1)
                confidence = float(probs.max().item())

        return {
            "profile_id": str(uuid4()),
            "actor_name": actor_name,
            "confidence": round(confidence, 4),
            "stylometry": stylometry,
            "topics": topics,
            "sentiment": sentiment,
            "risk_score": round(risk, 2),
            "reputation_score": round(reputation, 2),
            "correlated_usernames": correlated,
        }

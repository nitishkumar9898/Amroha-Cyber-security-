"""Linguistic profiler — deception detection, sentiment, personality, stylometry."""

import math
import re
from collections import Counter
from typing import Any, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 512):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.size(1), :]


class DeceptionClassifier(nn.Module):
    def __init__(
        self,
        vocab_size: int = 10000,
        d_model: int = 256,
        nhead: int = 8,
        num_layers: int = 4,
        dim_feedforward: int = 1024,
        dropout: float = 0.1,
        num_classes: int = 2,
    ):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=0)
        self.pos_encoder = PositionalEncoding(d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.classifier = nn.Sequential(
            nn.Linear(d_model, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        x = self.embedding(x)
        x = self.pos_encoder(x)
        x = self.transformer(x, src_key_padding_mask=mask)
        x = x.transpose(1, 2)
        x = self.pool(x).squeeze(-1)
        return self.classifier(x)


class FineGrainedSentimentHead(nn.Module):
    def __init__(self, d_model: int = 256):
        super().__init__()
        self.anger = nn.Linear(d_model, 1)
        self.fear = nn.Linear(d_model, 1)
        self.manipulation = nn.Linear(d_model, 1)
        self.regret = nn.Linear(d_model, 1)
        self.neutral = nn.Linear(d_model, 1)

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        return {
            "anger": torch.sigmoid(self.anger(x)),
            "fear": torch.sigmoid(self.fear(x)),
            "manipulation": torch.sigmoid(self.manipulation(x)),
            "regret": torch.sigmoid(self.regret(x)),
            "neutral": torch.sigmoid(self.neutral(x)),
        }


class PersonalityBig5Head(nn.Module):
    def __init__(self, d_model: int = 256):
        super().__init__()
        self.openness = nn.Linear(d_model, 1)
        self.conscientiousness = nn.Linear(d_model, 1)
        self.extraversion = nn.Linear(d_model, 1)
        self.agreeableness = nn.Linear(d_model, 1)
        self.neuroticism = nn.Linear(d_model, 1)

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        return {
            "openness": torch.sigmoid(self.openness(x)),
            "conscientiousness": torch.sigmoid(self.conscientiousness(x)),
            "extraversion": torch.sigmoid(self.extraversion(x)),
            "agreeableness": torch.sigmoid(self.agreeableness(x)),
            "neuroticism": torch.sigmoid(self.neuroticism(x)),
        }


class LinguisticProfiler(nn.Module):
    """Complete linguistic analysis model with multiple heads."""

    def __init__(
        self,
        vocab_size: int = 10000,
        d_model: int = 256,
        nhead: int = 8,
        num_layers: int = 4,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=0)
        self.pos_encoder = PositionalEncoding(d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.pool = nn.AdaptiveAvgPool1d(1)

        self.deception = nn.Linear(d_model, 1)
        self.sentiment = FineGrainedSentimentHead(d_model)
        self.personality = PersonalityBig5Head(d_model)

    def forward(
        self, x: torch.Tensor, mask: Optional[torch.Tensor] = None
    ) -> dict[str, Any]:
        x = self.embedding(x)
        x = self.pos_encoder(x)
        x = self.transformer(x, src_key_padding_mask=mask)
        x = x.transpose(1, 2)
        pooled = self.pool(x).squeeze(-1)

        return {
            "deception_score": torch.sigmoid(self.deception(pooled)).squeeze(-1),
            "sentiment": self.sentiment(pooled),
            "personality": self.personality(pooled),
        }


# ---------------------------------------------------------------------------
# LIWC-style category extraction (rule-based companion)
# ---------------------------------------------------------------------------

LIWC_CATEGORIES: dict[str, list[str]] = {
    "pronoun": ["i", "me", "my", "you", "your", "he", "she", "it", "we", "they"],
    "negation": ["no", "not", "never", "nothing", "nobody", "none", "neither"],
    "assent": ["yes", "ok", "yeah", "sure", "agree", "correct"],
    "anger": ["anger", "rage", "furious", "hate", "destroy", "kill", "attack"],
    "sadness": ["sad", "depressed", "grief", "sorrow", "cry", "mourn", "hopeless"],
    "fear": ["fear", "afraid", "scared", "terrified", "anxious", "panic", "dread"],
    "tentative": ["maybe", "perhaps", "guess", "apparently", "might", "could", "possibly"],
    "certainty": ["always", "never", "definitely", "absolutely", "certainly", "must", "sure"],
    "social": ["friend", "family", "mother", "father", "brother", "sister", "neighbor"],
    "money": ["money", "cash", "price", "pay", "buy", "sell", "bitcoin", "ransom"],
    "tech": ["exploit", "vulnerability", "payload", "shell", "backdoor", "rat", "malware"],
    "achieve": ["win", "success", "accomplish", "achieve", "goal", "complete", "master"],
    "risk": ["risk", "danger", "threat", "hazard", "warning", "caution", "exposure"],
    "time": ["now", "today", "soon", "later", "immediately", "urgent", "deadline"],
    "deception_marker": ["honestly", "truthfully", "believe_me", "frankly", "to_be_honest", "swear"],
}


def extract_liwc_categories(text: str) -> dict[str, float]:
    """Extract LIWC-style category densities from text."""
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    if not tokens:
        return {cat: 0.0 for cat in LIWC_CATEGORIES}
    word_count = len(tokens)
    token_set: Counter[str] = Counter(tokens)
    scores: dict[str, float] = {}
    for category, keywords in LIWC_CATEGORIES.items():
        matches = sum(token_set.get(kw, 0) for kw in keywords)
        scores[category] = round(matches / word_count, 4)
    return scores


def extract_stylometry(text: str) -> dict[str, Any]:
    """Extract stylometric authorship features from text."""
    tokens = re.findall(r"[a-zA-Z']+", text)
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not tokens:
        return {
            "avg_word_length": 0.0,
            "avg_sentence_length": 0.0,
            "type_token_ratio": 0.0,
            "punctuation_rate": 0.0,
            "uppercase_rate": 0.0,
            "digit_rate": 0.0,
            "hll_positions": [],
        }

    word_lengths = [len(t) for t in tokens]
    char_count = sum(word_lengths)

    type_token = len(set(t.lower() for t in tokens)) / len(tokens) if tokens else 0.0

    punct_count = len(re.findall(r"[.,!?;:\"\'()\[\]{}]", text))
    punct_rate = punct_count / char_count if char_count else 0.0

    upper_count = len(re.findall(r"[A-Z]", text))
    upper_rate = upper_count / char_count if char_count else 0.0

    digit_count = len(re.findall(r"[0-9]", text))
    digit_rate = digit_count / char_count if char_count else 0.0

    func_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "can", "could", "may", "might", "shall", "should", "not", "no", "if", "then", "else", "when", "where", "how", "what", "which", "who", "whom", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them"}
    hll_positions = [idx for idx, t in enumerate(tokens) if t.lower() in func_words]

    return {
        "avg_word_length": round(sum(word_lengths) / len(tokens), 2),
        "avg_sentence_length": round(len(tokens) / max(len(sentences), 1), 2),
        "type_token_ratio": round(type_token, 4),
        "punctuation_rate": round(punct_rate, 4),
        "uppercase_rate": round(upper_rate, 4),
        "digit_rate": round(digit_rate, 4),
        "total_tokens": len(tokens),
        "total_sentences": len(sentences),
        "function_word_positions": hll_positions[:50],
    }

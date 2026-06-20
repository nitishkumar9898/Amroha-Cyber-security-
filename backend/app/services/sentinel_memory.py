"""
SentinelCore Memory — Continual Learning & RAG Pipeline
========================================================
Implements an in-process vector-similarity memory store for Retrieval-Augmented
Generation (RAG).  Supports:
  • Semantic storage of past interactions for context retrieval
  • Experience replay buffer for incremental learning without forgetting
  • Active-learning flag for low-confidence items needing human review
  • Knowledge-base versioning aligned with the Federated Learning aggregator

Note: Uses a lightweight TF-IDF-style approach locally; swap in ChromaDB /
      Pinecone embeddings when deployed at scale.
"""

import hashlib
import math
import re
import time
import logging
from collections import Counter
from datetime import datetime
from typing import Optional

logger = logging.getLogger("SentinelMemory")


class _VectorEntry:
    """A single memory entry with its term-frequency vector."""

    __slots__ = (
        "entry_id",
        "text",
        "response",
        "intent",
        "threat_score",
        "user_id",
        "timestamp",
        "term_freq",
        "replay_priority",
        "needs_review",
    )

    def __init__(
        self,
        text: str,
        response: str,
        intent: str,
        threat_score: float,
        user_id: str,
    ):
        self.entry_id = hashlib.sha256(
            f"{text}-{time.time()}".encode()
        ).hexdigest()[:16]
        self.text = text
        self.response = response
        self.intent = intent
        self.threat_score = threat_score
        self.user_id = user_id
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.term_freq = _tokenize_and_count(text)
        # Experience replay: higher threat → higher priority for replay
        self.replay_priority = threat_score
        # Active learning: flag low-confidence for HITL review
        self.needs_review = threat_score < 0.25

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "text": self.text,
            "response": self.response,
            "intent": self.intent,
            "threat_score": self.threat_score,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "replay_priority": round(self.replay_priority, 3),
            "needs_review": self.needs_review,
        }


def _tokenize_and_count(text: str) -> Counter:
    """Simple whitespace + punctuation tokenizer → term frequency counter."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return Counter(tokens)


def _cosine_similarity(a: Counter, b: Counter) -> float:
    """Cosine similarity between two term-frequency Counters."""
    common = set(a.keys()) & set(b.keys())
    if not common:
        return 0.0
    dot = sum(a[t] * b[t] for t in common)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


class SentinelMemory:
    """
    In-process continual-learning memory with RAG-style retrieval.
    Maintains an experience replay buffer and active-learning queue.
    """

    # Maximum entries before oldest non-critical ones are evicted
    MAX_ENTRIES = 10_000
    # Entries above this replay priority are never evicted
    CRITICAL_PRIORITY_THRESHOLD = 0.7
    # Knowledge-base version — incremented on each federated aggregation
    KB_VERSION = 2.0

    def __init__(self):
        self._store: list[_VectorEntry] = []
        self._review_queue: list[_VectorEntry] = []
        self._knowledge_version = self.KB_VERSION

        # Seed initial knowledge base entries
        self._seed_knowledge_base()
        logger.info(
            f"SentinelMemory initialized — KB v{self._knowledge_version}, "
            f"{len(self._store)} seed entries"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store_interaction(
        self,
        query: str,
        response: str,
        intent: str,
        threat_score: float,
        user_id: str,
    ) -> str:
        """Store a query/response pair for future RAG retrieval."""
        entry = _VectorEntry(query, response, intent, threat_score, user_id)
        self._store.append(entry)

        if entry.needs_review:
            self._review_queue.append(entry)
            logger.info(
                f"[ActiveLearning] Low-confidence entry {entry.entry_id} "
                "queued for human review"
            )

        # Evict if over capacity
        if len(self._store) > self.MAX_ENTRIES:
            self._evict_oldest()

        return entry.entry_id

    def retrieve_context(self, query: str, top_k: int = 5) -> list[dict]:
        """
        RAG retrieval: find the top-k most semantically similar past
        interactions to provide as context for the current query.
        """
        if not self._store:
            return []

        query_vec = _tokenize_and_count(query)
        scored = []
        for entry in self._store:
            sim = _cosine_similarity(query_vec, entry.term_freq)
            if sim > 0.05:  # Skip very low similarity
                scored.append((sim, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for sim, entry in scored[:top_k]:
            d = entry.to_dict()
            d["relevance_score"] = round(sim, 3)
            results.append(d)
        return results

    def get_replay_buffer(self, size: int = 50) -> list[dict]:
        """
        Experience replay: return high-priority entries for incremental
        re-training. Prevents catastrophic forgetting.
        """
        sorted_entries = sorted(
            self._store, key=lambda e: e.replay_priority, reverse=True
        )
        return [e.to_dict() for e in sorted_entries[:size]]

    def get_review_queue(self) -> list[dict]:
        """Active learning: items flagged for human-in-the-loop review."""
        return [e.to_dict() for e in self._review_queue]

    def approve_review_item(self, entry_id: str) -> bool:
        """Mark a review-queue item as approved (human validated)."""
        for i, entry in enumerate(self._review_queue):
            if entry.entry_id == entry_id:
                entry.needs_review = False
                entry.replay_priority = max(entry.replay_priority, 0.6)
                self._review_queue.pop(i)
                logger.info(f"[ActiveLearning] Entry {entry_id} approved by analyst")
                return True
        return False

    def entry_count(self) -> int:
        return len(self._store)

    def get_memory_stats(self) -> dict:
        """Return memory subsystem statistics."""
        return {
            "total_entries": len(self._store),
            "review_queue_size": len(self._review_queue),
            "knowledge_base_version": self._knowledge_version,
            "max_capacity": self.MAX_ENTRIES,
            "utilization_pct": round(
                len(self._store) / self.MAX_ENTRIES * 100, 1
            ),
            "high_priority_entries": sum(
                1 for e in self._store
                if e.replay_priority >= self.CRITICAL_PRIORITY_THRESHOLD
            ),
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _evict_oldest(self):
        """Remove the oldest non-critical entry to stay within capacity."""
        for i, entry in enumerate(self._store):
            if entry.replay_priority < self.CRITICAL_PRIORITY_THRESHOLD:
                self._store.pop(i)
                logger.debug(f"Evicted entry {entry.entry_id} (low priority)")
                return
        # If all are critical, pop the very oldest
        self._store.pop(0)

    def _seed_knowledge_base(self):
        """Pre-load curated cybersecurity knowledge for the RAG pipeline."""
        seed_data = [
            {
                "query": "What is ransomware and how does it work?",
                "response": (
                    "Ransomware is malware that encrypts victim files and demands "
                    "payment for the decryption key. Modern variants use RSA-2048 or "
                    "AES-256 encryption and may exfiltrate data before encryption "
                    "(double extortion). Common delivery: phishing emails, RDP brute "
                    "force, or supply-chain compromise."
                ),
                "intent": "malware",
                "score": 0.9,
            },
            {
                "query": "How to detect deepfake videos in forensic analysis?",
                "response": (
                    "Deepfake detection involves analyzing pixel-level artifacts, "
                    "temporal inconsistencies between frames, facial landmark jitter, "
                    "and GAN fingerprint signatures. Tools compare face consistency "
                    "scores across a video timeline; scores below 0.5 indicate high "
                    "probability of manipulation."
                ),
                "intent": "deepfake",
                "score": 0.7,
            },
            {
                "query": "What is MITRE ATT&CK framework?",
                "response": (
                    "MITRE ATT&CK is a globally-accessible knowledge base of adversary "
                    "tactics, techniques, and procedures (TTPs) based on real-world "
                    "observations. It covers 14 tactics from Initial Access to Impact, "
                    "with hundreds of techniques. Used by SOC teams for threat modeling, "
                    "detection engineering, and red team planning."
                ),
                "intent": "apt",
                "score": 0.6,
            },
            {
                "query": "How to perform mobile forensics on Android devices?",
                "response": (
                    "Android mobile forensics involves: 1) Logical acquisition of "
                    "SQLite databases, SMS/MMS stores, and app data. 2) Physical "
                    "acquisition via ADB or JTAG for full disk images. 3) Parsing chat "
                    "databases (WhatsApp, Telegram) with GPS coordinate extraction. "
                    "4) Timeline reconstruction using metadata timestamps. "
                    "All evidence must be hashed (SHA-256) and documented under "
                    "chain-of-custody protocols."
                ),
                "intent": "mobile_forensics",
                "score": 0.65,
            },
            {
                "query": "What are indicators of compromise for APT attacks?",
                "response": (
                    "APT IOCs include: unusual outbound traffic to rare TLDs, "
                    "beaconing patterns at fixed intervals, unauthorized use of "
                    "legitimate admin tools (PsExec, WMI, PowerShell), registry "
                    "modifications for persistence, DNS tunneling, and anomalous "
                    "authentication patterns. Cross-reference with threat intel feeds "
                    "and MITRE ATT&CK technique IDs."
                ),
                "intent": "apt",
                "score": 0.85,
            },
            {
                "query": "How does dark web intelligence gathering work?",
                "response": (
                    "Dark web intelligence involves monitoring Tor hidden services, "
                    "paste sites, and encrypted chat channels for threat indicators. "
                    "Analysts track marketplace listings for data dumps, credential "
                    "leaks, zero-day exploits, and ransomware-as-a-service offerings. "
                    "PGP fingerprints and cryptocurrency wallet addresses serve as "
                    "persistent identifiers for threat actor attribution."
                ),
                "intent": "darkweb",
                "score": 0.75,
            },
            {
                "query": "What are the stages of a cyber kill chain?",
                "response": (
                    "The Lockheed Martin Cyber Kill Chain defines 7 stages: "
                    "1) Reconnaissance, 2) Weaponization, 3) Delivery, "
                    "4) Exploitation, 5) Installation, 6) Command & Control, "
                    "7) Actions on Objectives. Understanding each stage enables "
                    "defenders to implement layered detection and disruption "
                    "at multiple points."
                ),
                "intent": "apt",
                "score": 0.7,
            },
            {
                "query": "How to analyze USB device forensics?",
                "response": (
                    "USB forensics involves examining device VID/PID pairs against "
                    "known-malicious device databases, checking firmware integrity, "
                    "analyzing USB traffic captures, and correlating connection "
                    "timestamps with security events. Devices like Rubber Ducky "
                    "emulate HID keyboards and can inject payloads within seconds."
                ),
                "intent": "hardware",
                "score": 0.55,
            },
        ]

        for item in seed_data:
            entry = _VectorEntry(
                text=item["query"],
                response=item["response"],
                intent=item["intent"],
                threat_score=item["score"],
                user_id="system_seed",
            )
            entry.needs_review = False
            self._store.append(entry)

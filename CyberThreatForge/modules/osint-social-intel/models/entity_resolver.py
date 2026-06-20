import hashlib
import logging
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Optional
from uuid import uuid4

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger("entity_resolver")


@dataclass
class Entity:
    entity_id: str
    names: list[str] = field(default_factory=list)
    usernames: dict[str, list[str]] = field(default_factory=dict)
    emails: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    profiles: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityLink:
    source_entity_id: str
    target_entity_id: str
    relationship: str
    confidence: float
    evidence: list[str] = field(default_factory=list)


class FuzzyNameMatcher(nn.Module):
    def __init__(self, embedding_dim: int = 128):
        super().__init__()
        self.char_emb = nn.Embedding(128, 32, padding_idx=0)
        self.conv1 = nn.Conv1d(32, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(64, embedding_dim, kernel_size=3, padding=1)
        self.pool = nn.AdaptiveMaxPool1d(1)
        self.fc = nn.Linear(embedding_dim, embedding_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.char_emb(x)
        x = x.permute(0, 2, 1)
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = self.pool(x).squeeze(-1)
        x = self.fc(x)
        return F.normalize(x, p=2, dim=1)


class EntityResolver:
    def __init__(self, device: Optional[str] = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.name_matcher = FuzzyNameMatcher().to(self.device)
        self.name_matcher.eval()
        self.entities: dict[str, Entity] = {}
        self.links: list[EntityLink] = []
        self._char_map = {c: i + 1 for i, c in enumerate(
            "abcdefghijklmnopqrstuvwxyz0123456789@._- "
        )}

    def _char_encode(self, name: str, max_len: int = 32) -> torch.Tensor:
        encoded = [self._char_map.get(c.lower(), 0) for c in name[:max_len]]
        encoded += [0] * (max_len - len(encoded))
        return torch.tensor([encoded], dtype=torch.long, device=self.device)

    def _name_similarity(self, name1: str, name2: str) -> float:
        return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()

    def _phonetic_similarity(self, name1: str, name2: str) -> float:
        def soundex(name: str) -> str:
            name = name.lower()
            if not name:
                return ""
            result = name[0].upper()
            code_map = {"b": "1", "f": "1", "p": "1", "v": "1",
                        "c": "2", "g": "2", "j": "2", "k": "2", "q": "2",
                        "s": "2", "x": "2", "z": "2",
                        "d": "3", "t": "3",
                        "l": "4",
                        "m": "5", "n": "5",
                        "r": "6"}
            for ch in name[1:]:
                code = code_map.get(ch, "")
                if code and code != result[-1]:
                    result += code
            return (result + "0000")[:4]
        return 1.0 if soundex(name1) == soundex(name2) else 0.0

    def _neural_similarity(self, name1: str, name2: str) -> float:
        with torch.no_grad():
            e1 = self.name_matcher(self._char_encode(name1))
            e2 = self.name_matcher(self._char_encode(name2))
            sim = F.cosine_similarity(e1, e2).item()
        return max(0.0, min(1.0, (sim + 1.0) / 2.0))

    def compute_name_similarity(self, name1: str, name2: str, weights: Optional[dict[str, float]] = None) -> float:
        w = weights or {"fuzzy": 0.3, "phonetic": 0.2, "neural": 0.5}
        fuzzy = self._name_similarity(name1, name2)
        phonetic = self._phonetic_similarity(name1, name2)
        neural = self._neural_similarity(name1, name2)
        score = w["fuzzy"] * fuzzy + w["phonetic"] * phonetic + w["neural"] * neural
        return round(min(1.0, max(0.0, score)), 4)

    def resolve_identity(self, name_hints: list[str], username_hints: dict[str, list[str]],
                         email_hints: list[str], threshold: float = 0.65) -> Entity:
        entity_id = uuid4().hex[:16]
        coc = [{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": "identity_resolution",
            "detail": f"Resolving identity from {len(name_hints)} names, {sum(len(v) for v in username_hints.values())} usernames, {len(email_hints)} emails",
            "handler_id": hashlib.sha256(str(uuid4()).encode()).hexdigest()[:16],
        }]
        all_names = list(name_hints)
        linked = set()
        for name in name_hints:
            for other in name_hints:
                if name != other and other not in linked:
                    sim = self.compute_name_similarity(name, other)
                    if sim >= threshold:
                        linked.add(other)
                        self.links.append(EntityLink(
                            source_entity_id=entity_id,
                            target_entity_id=entity_id,
                            relationship="alias",
                            confidence=sim,
                            evidence=[f"Name similarity: {name} ~ {other} ({sim:.2f})"],
                        ))
        for platform, usernames in username_hints.items():
            for uname in usernames:
                all_names.append(uname)
                for name in name_hints:
                    sim = self.compute_name_similarity(uname, name)
                    if sim >= threshold:
                        self.links.append(EntityLink(
                            source_entity_id=entity_id,
                            target_entity_id=entity_id,
                            relationship="username_to_name",
                            confidence=sim,
                            evidence=[f"Username '{uname}' matches name '{name}' ({sim:.2f})"],
                        ))
        platforms = list(username_hints.keys())
        email_domains = set(e.split("@")[-1] if "@" in e else "" for e in email_hints)
        evidence_list = [f"Names: {name_hints}", f"Usernames: {username_hints}", f"Emails: {email_hints}"]
        confidence = min(0.95, 0.3 + 0.15 * len(name_hints) + 0.1 * len(platforms) + 0.1 * len(email_hints))
        entity = Entity(
            entity_id=entity_id,
            names=sorted(set(all_names)),
            usernames=username_hints,
            emails=email_hints,
            platforms=platforms,
            confidence=round(confidence, 4),
            metadata={"evidence": evidence_list, "email_domains": list(email_domains), "chain_of_custody": coc},
        )
        self.entities[entity_id] = entity
        return entity

    def correlate_across_platforms(self, entities: list[Entity], threshold: float = 0.5) -> list[dict[str, Any]]:
        correlations: list[dict[str, Any]] = []
        for i, e1 in enumerate(entities):
            for j, e2 in enumerate(entities):
                if j <= i:
                    continue
                name_sim = max(
                    (self.compute_name_similarity(n1, n2) for n1 in e1.names for n2 in e2.names),
                    default=0.0,
                )
                email_overlap = len(set(e1.emails) & set(e2.emails))
                platform_overlap = len(set(e1.platforms) & set(e2.platforms))
                username_matches = 0
                for p in e1.usernames:
                    if p in e2.usernames:
                        for u1 in e1.usernames[p]:
                            for u2 in e2.usernames[p]:
                                if self.compute_name_similarity(u1, u2) > 0.8:
                                    username_matches += 1
                score = (
                    name_sim * 0.35 +
                    min(email_overlap, 1) * 0.3 +
                    min(platform_overlap / max(len(e1.platforms + e2.platforms), 1) * 2, 1) * 0.2 +
                    min(username_matches, 1) * 0.15
                )
                if score >= threshold:
                    correlations.append({
                        "entity_a_id": e1.entity_id,
                        "entity_b_id": e2.entity_id,
                        "entity_a_names": e1.names,
                        "entity_b_names": e2.names,
                        "correlation_score": round(score, 4),
                        "name_similarity": round(name_sim, 4),
                        "email_overlap": email_overlap,
                        "platform_overlap": platform_overlap,
                        "username_matches": username_matches,
                    })
        return correlations

    def build_social_graph(self, entities: Optional[list[Entity]] = None) -> dict[str, Any]:
        ents = entities or list(self.entities.values())
        nodes = []
        edges = []
        for ent in ents:
            for name in ent.names:
                nodes.append({
                    "id": ent.entity_id,
                    "label": name,
                    "platforms": ent.platforms,
                    "confidence": ent.confidence,
                })
                break
        for link in self.links:
            edges.append({
                "source": link.source_entity_id,
                "target": link.target_entity_id,
                "relationship": link.relationship,
                "confidence": link.confidence,
                "evidence": link.evidence,
            })
        correlations = self.correlate_across_platforms(ents)
        for corr in correlations:
            edges.append({
                "source": corr["entity_a_id"],
                "target": corr["entity_b_id"],
                "relationship": "correlated",
                "confidence": corr["correlation_score"],
                "evidence": [f"Correlated across platforms ({corr['correlation_score']:.2f})"],
            })
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "chain_of_custody": [{
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "step": "social_graph",
                "detail": f"Built graph with {len(nodes)} nodes, {len(edges)} edges",
                "handler_id": hashlib.sha256(str(uuid4()).encode()).hexdigest()[:16],
            }],
        }

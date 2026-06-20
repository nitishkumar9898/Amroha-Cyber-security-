"""Tests for the Cross-Platform Evidence Correlation Engine API."""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["NEO4J_URI"] = ""
os.environ["SENTINEL_CORE_URL"] = "http://test:3000"

from api import app, evidence_graph, query_engine, embedding_fuser, temporal_analyzer

client = TestClient(app)


def _reset_state():
    evidence_graph.clear()
    temporal_analyzer.clear()
    embedding_fuser.clear_cache()


@pytest.fixture(autouse=True)
def reset():
    _reset_state()
    yield
    _reset_state()


def _sample_evidence(case_id: str = "case-001") -> list[dict[str, Any]]:
    return [
        {
            "case_id": case_id,
            "domain": "malware_analysis",
            "timestamp": "2026-06-20T10:00:00Z",
            "files": {
                "malware.exe": {
                    "id": "file_malware_exe",
                    "path": "/tmp/malware.exe",
                    "size": 1048576,
                    "hash": "a" * 64,
                }
            },
            "ip_addresses": ["192.168.1.100", "10.0.0.1"],
            "domains": ["evil.example.com"],
            "emails": ["attacker@evil.com"],
            "persons": ["John Doe"],
            "devices": ["DESKTOP-ABC123"],
            "locations": [{"latitude": 12.34, "longitude": 56.78}],
            "events": [
                {
                    "id": "evt_001",
                    "type": "file_download",
                    "timestamp": "2026-06-20T10:01:00Z",
                }
            ],
            "communications": [
                {
                    "source": "192.168.1.100",
                    "target": "10.0.0.1",
                    "weight": 0.9,
                    "timestamp": "2026-06-20T10:00:30Z",
                }
            ],
            "accesses": [
                {
                    "actor": "malware.exe",
                    "target": "192.168.1.100",
                    "weight": 1.0,
                    "timestamp": "2026-06-20T10:00:05Z",
                }
            ],
            "organizations": ["APT-42"],
        }
    ]


def _sample_events(count: int = 10) -> list[dict[str, Any]]:
    base = datetime(2026, 6, 20, 10, 0, 0, tzinfo=timezone.utc)
    events = []
    for i in range(count):
        ts = (base + __import__("datetime").timedelta(seconds=i * 600)).isoformat()
        events.append({
            "timestamp": ts,
            "type": "network_connection",
            "entity_id": f"192.168.1.{i + 1}",
            "source": f"192.168.1.{i + 1}",
            "target": "10.0.0.1" if i % 2 == 0 else "10.0.0.2",
            "evidence_id": f"evt_{i}",
            "description": f"Connection from 192.168.1.{i + 1}",
        })
    return events


class TestHealth:
    def test_health_endpoint(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["module"] == "evidence-correlation"
        assert data["status"] == "healthy"
        assert "graph" in data
        assert "models" in data


class TestGraphCorrelation:
    @pytest.fixture(autouse=True)
    def setup(self):
        _reset_state()

    def test_correlate_graph_empty(self):
        resp = client.post("/correlate/graph", json={"evidence_items": []})
        assert resp.status_code == 200
        data = resp.json()
        assert data["node_count"] == 0
        assert data["evidence_added"] == 0

    def test_correlate_graph_with_evidence(self):
        resp = client.post(
            "/correlate/graph",
            json={"evidence_items": _sample_evidence(), "case_id": "case-001"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["evidence_added"] > 0
        assert data["node_count"] > 0

    def test_correlate_graph_multiple_items(self):
        items = _sample_evidence() + _sample_evidence("case-002")
        resp = client.post(
            "/correlate/graph",
            json={"evidence_items": items, "case_id": "multi"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["node_count"] > 0
        assert data["edge_count"] > 0

    def test_correlate_graph_deduplication(self):
        items = _sample_evidence()
        resp1 = client.post("/correlate/graph", json={"evidence_items": items})
        n1 = resp1.json()["node_count"]
        resp2 = client.post("/correlate/graph", json={"evidence_items": items})
        n2 = resp2.json()["node_count"]
        assert n2 >= n1


class TestTemporalCorrelation:
    def test_temporal_empty(self):
        resp = client.post(
            "/correlate/temporal",
            json={"events": [], "window_size_seconds": 3600},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["event_count"] == 0

    def test_temporal_links_discovered(self):
        resp = client.post(
            "/correlate/temporal",
            json={"events": _sample_events(20), "window_size_seconds": 7200},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["event_count"] == 20
        assert "links" in data

    def test_temporal_sequences(self):
        events = _sample_events(30)
        resp = client.post(
            "/correlate/temporal",
            json={
                "events": events,
                "window_size_seconds": 3600,
                "options": {"min_support": 2, "pattern_length": 3},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "sequences" in data

    def test_temporal_anomalies(self):
        events = _sample_events(50)
        resp = client.post(
            "/correlate/temporal",
            json={
                "events": events,
                "window_size_seconds": 3600,
                "options": {"std_threshold": 1.5},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "anomalies" in data

    def test_temporal_sliding_windows(self):
        resp = client.post(
            "/correlate/temporal",
            json={
                "events": _sample_events(15),
                "window_size_seconds": 1800,
                "slide_seconds": 900,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "time_windows" in data
        assert len(data["time_windows"]) > 0


class TestMultiModalCorrelation:
    def test_multi_modal_no_query(self):
        resp = client.post(
            "/correlate/multi-modal",
            json={"query": {}, "candidates": []},
        )
        assert resp.status_code == 400

    def test_multi_modal_with_text(self):
        resp = client.post(
            "/correlate/multi-modal",
            json={
                "query": {"modality": "text", "data": "suspicious file download"},
                "candidates": [
                    {"evidence_id": "e1", "modality": "text", "data": "malicious executable"},
                    {"evidence_id": "e2", "modality": "text", "data": "benign document"},
                ],
                "top_k": 2,
                "threshold": -1.0,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["matches"]) <= 2

    def test_multi_modal_with_embedding(self):
        resp = client.post(
            "/correlate/multi-modal",
            json={
                "query": {"modality": "text"},
                "embedding": [0.1] * 128,
                "candidates": [
                    {"evidence_id": "e1", "modality": "text", "data": "test"},
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["match_count"] > 0

    def test_multi_modal_threshold(self):
        resp = client.post(
            "/correlate/multi-modal",
            json={
                "query": {"modality": "text", "data": "query"},
                "candidates": [
                    {"evidence_id": "e1", "modality": "text", "data": "match"},
                ],
                "threshold": 0.99,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["match_count"], int)


class TestEntityCorrelation:
    def test_entity_empty(self):
        resp = client.post(
            "/correlate/entity",
            json={"evidence_items": [], "entity_types": []},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "entity_summary" in data

    def test_entity_with_evidence(self):
        resp = client.post(
            "/correlate/entity",
            json={
                "evidence_items": _sample_evidence(),
                "entity_types": ["file", "ip", "domain"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["evidence_added"] > 0
        assert "file" in data["entity_views"]

    def test_entity_communities(self):
        items = _sample_evidence("case-001") + _sample_evidence("case-002")
        resp = client.post(
            "/correlate/entity",
            json={"evidence_items": items, "case_id": "multi-case"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "communities" in data


class TestPatternAnalysis:
    def test_patterns_no_graph(self):
        resp = client.post(
            "/analyze/patterns",
            json={"graph_data": {}, "min_confidence": 0.5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "analysis_id" in data

    def test_patterns_with_graph_data(self):
        evidence_graph.add_evidence_item(_sample_evidence()[0])
        subgraph = query_engine.extract_subgraph(
            node_ids=list(evidence_graph.graph.nodes())[:10]
        )
        resp = client.post(
            "/analyze/patterns",
            json={"graph_data": subgraph or {}, "min_confidence": 0.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "graph_patterns" in data

    def test_patterns_motifs(self):
        for _ in range(3):
            evidence_graph.add_evidence_item(_sample_evidence(uuid.uuid4().hex)[0])
        resp = client.post(
            "/analyze/patterns",
            json={"graph_data": {}, "min_confidence": 0.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "motifs" in data


class TestAnomalyDetection:
    def test_anomalies_empty_graph(self):
        resp = client.post(
            "/analyze/anomalies",
            json={"graph_data": {}, "threshold": 0.5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "graph_anomalies" in data

    def test_anomalies_with_temporal(self):
        temporal_analyzer.add_events(_sample_events(20))
        resp = client.post(
            "/analyze/anomalies",
            json={"graph_data": {}, "threshold": 0.5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "temporal_anomalies" in data


class TestSimilarityQuery:
    def test_similarity_unknown_node(self):
        resp = client.post(
            "/query/similar",
            json={"evidence_id": "nonexistent", "top_k": 5},
        )
        assert resp.status_code == 400

    def test_similarity_with_embedding(self):
        resp = client.post(
            "/query/similar",
            json={"embedding": [0.5] * 128, "top_k": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "matches" in data

    def test_similarity_with_node(self):
        evidence_graph.add_evidence_item(_sample_evidence()[0])
        nid = list(evidence_graph.graph.nodes())[0]
        resp = client.post(
            "/query/similar",
            json={"evidence_id": nid, "top_k": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "matches" in data
        assert data["query_node"] == nid


class TestPathQuery:
    def test_path_nonexistent_source(self):
        resp = client.post(
            "/query/path",
            json={"source_id": "nonexistent", "target_id": "target"},
        )
        assert resp.status_code == 404

    def test_path_nonexistent_target(self):
        resp = client.post(
            "/query/path",
            json={"source_id": "source", "target_id": "nonexistent"},
        )
        assert resp.status_code == 404

    def test_path_between_nodes(self):
        items = _sample_evidence()
        evidence_graph.add_evidence_item(items[0])
        edges = list(evidence_graph.graph.edges())
        if len(edges) >= 1:
            u, v = edges[0][:2]
            resp = client.post(
                "/query/path",
                json={"source_id": u, "target_id": v},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["found"] is True
            assert "shortest_path" in data


class TestIntegration:
    def test_full_workflow(self):
        ts = _sample_evidence("integ-case")
        gr = client.post("/correlate/graph", json={"evidence_items": ts})
        assert gr.status_code == 200

        events = _sample_events(10)
        tc = client.post(
            "/correlate/temporal",
            json={"events": events, "window_size_seconds": 3600},
        )
        assert tc.status_code == 200

        mm = client.post(
            "/correlate/multi-modal",
            json={
                "query": {"modality": "text", "data": "investigation query"},
                "candidates": [
                    {"evidence_id": "ref", "modality": "text", "data": "reference evidence"}
                ],
            },
        )
        assert mm.status_code == 200

        ec = client.post(
            "/correlate/entity",
            json={"evidence_items": ts, "entity_types": ["file", "ip"]},
        )
        assert ec.status_code == 200

        pa = client.post(
            "/analyze/patterns",
            json={"graph_data": {}, "min_confidence": 0.0},
        )
        assert pa.status_code == 200

        ad = client.post(
            "/analyze/anomalies",
            json={"graph_data": {}, "threshold": 0.5},
        )
        assert ad.status_code == 200

        sq = client.post(
            "/query/similar",
            json={"embedding": [0.1] * 128, "top_k": 3},
        )
        assert sq.status_code == 200

        health = client.get("/health")
        assert health.status_code == 200

    def test_serialization_roundtrip(self):
        items = _sample_evidence("serial-case")
        evidence_graph.add_evidence_item(items[0])
        serialized = evidence_graph.serialize()
        assert "nodes" in serialized
        assert "links" in serialized or "edges" in serialized

        from graph.graph_builder import EvidenceGraph
        restored = EvidenceGraph.deserialize(serialized)
        assert restored.node_count() == evidence_graph.node_count()

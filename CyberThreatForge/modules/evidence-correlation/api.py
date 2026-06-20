"""Cross-Platform Evidence Correlation Engine API.

FastAPI application providing graph-based reasoning, temporal link analysis,
multi-modal similarity matching, pattern discovery, and anomaly detection
across all forensic modules.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

try:
    from neo4j import AsyncGraphDatabase, AsyncDriver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    AsyncGraphDatabase = None
    AsyncDriver = None

from graph.graph_builder import EvidenceGraph, NodeType, EdgeType, GraphNode, GraphEdge
from graph.graph_queries import GraphQueryEngine
from models.gnn_pattern_analyzer import GNNAnalyzer, PATTERN_CLASSES
from models.embedding_fuser import EmbeddingFuser, FusedEmbedding
from models.temporal_linker import TemporalLinkAnalyzer

logger = logging.getLogger(__name__)

MODULE_ID = "evidence-correlation"
MODULE_VERSION = "1.0.0"

SENTINEL_URL = os.getenv("SENTINEL_CORE_URL", "http://backend:3000/api/v1")
SENTINEL_API_KEY = os.getenv("SENTINEL_API_KEY", "")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "changeme")

# ── Pydantic Models ────────────────────────────────────────────────────


class CorrelationRequest(BaseModel):
    evidence_items: list[dict[str, Any]] = Field(default_factory=list)
    case_id: str = ""
    domain: str = ""
    options: dict[str, Any] = Field(default_factory=dict)


class TemporalCorrelationRequest(BaseModel):
    events: list[dict[str, Any]] = Field(default_factory=list)
    window_size_seconds: int = 3600
    slide_seconds: int = 1800
    options: dict[str, Any] = Field(default_factory=dict)


class MultiModalRequest(BaseModel):
    query: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] = Field(default_factory=list)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    top_k: int = 10
    threshold: float = 0.0
    options: dict[str, Any] = Field(default_factory=dict)


class EntityCorrelationRequest(BaseModel):
    evidence_items: list[dict[str, Any]] = Field(default_factory=list)
    entity_types: list[str] = Field(default_factory=list)
    case_id: str = ""
    options: dict[str, Any] = Field(default_factory=dict)


class PatternDiscoveryRequest(BaseModel):
    graph_data: dict[str, Any] = Field(default_factory=dict)
    pattern_types: list[str] = Field(default_factory=list)
    min_confidence: float = 0.5
    options: dict[str, Any] = Field(default_factory=dict)


class AnomalyDetectionRequest(BaseModel):
    graph_data: dict[str, Any] = Field(default_factory=dict)
    threshold: float = 0.7
    options: dict[str, Any] = Field(default_factory=dict)


class SimilarityQueryRequest(BaseModel):
    evidence_id: str = ""
    embedding: list[float] = Field(default_factory=list)
    modality: str = "text"
    data: Any = None
    top_k: int = 10
    threshold: float = 0.0
    options: dict[str, Any] = Field(default_factory=dict)


class PathQueryRequest(BaseModel):
    source_id: str
    target_id: str
    max_depth: int = 10
    options: dict[str, Any] = Field(default_factory=dict)


# ── Application State ──────────────────────────────────────────────────

evidence_graph = EvidenceGraph()
query_engine = GraphQueryEngine(evidence_graph)
gnn_analyzer: Optional[GNNAnalyzer] = None
embedding_fuser = EmbeddingFuser()
temporal_analyzer = TemporalLinkAnalyzer()
neo4j_driver: Optional[Any] = None

app = FastAPI(
    title="Cross-Platform Evidence Correlation Engine",
    description="Graph-based evidence correlation across all forensic modules "
                "with temporal link analysis, multi-modal similarity, GNN pattern analysis.",
    version=MODULE_VERSION,
)


def get_evidence_graph() -> EvidenceGraph:
    return evidence_graph


def get_query_engine() -> GraphQueryEngine:
    return query_engine


def get_gnn_analyzer() -> Optional[GNNAnalyzer]:
    return gnn_analyzer


def get_embedding_fuser() -> EmbeddingFuser:
    return embedding_fuser


def get_temporal_analyzer() -> TemporalLinkAnalyzer:
    return temporal_analyzer


async def get_neo4j_driver() -> Optional[Any]:
    return neo4j_driver


# ── Lifecycle ──────────────────────────────────────────────────────────


@app.on_event("startup")
async def startup():
    global gnn_analyzer, neo4j_driver

    model_path = os.path.join(
        os.path.dirname(__file__), "models", "gnn_pattern_analyzer.pt"
    )
    try:
        gnn_analyzer = GNNAnalyzer(
            model_path=model_path if os.path.exists(model_path) else None,
            device="cpu",
        )
        logger.info("GNN analyzer initialized")
    except Exception as e:
        logger.warning("GNN analyzer init failed: %s", e)
        gnn_analyzer = None

    if NEO4J_AVAILABLE and NEO4J_URI:
        try:
            neo4j_driver = AsyncGraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            await neo4j_driver.verify_connectivity()
            logger.info("Connected to Neo4j at %s", NEO4J_URI)
        except Exception as e:
            logger.warning("Neo4j connection failed: %s", e)
            neo4j_driver = None


@app.on_event("shutdown")
async def shutdown():
    if neo4j_driver:
        await neo4j_driver.close()


# ── Helper ─────────────────────────────────────────────────────────────


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _sync_to_neo4j(graph: EvidenceGraph):
    driver = await get_neo4j_driver()
    if driver is None:
        return

    try:
        async with driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            for nid, ndata in graph.graph.nodes(data=True):
                await session.run(
                    "CREATE (n:Evidence {id: $id, type: $type, label: $label, case_id: $case_id, "
                    "domain: $domain, metadata: $metadata, timestamp: $timestamp})",
                    id=nid,
                    type=ndata.get("node_type", "unknown"),
                    label=ndata.get("label", ""),
                    case_id=ndata.get("case_id", ""),
                    domain=ndata.get("domain", ""),
                    metadata=json.dumps(ndata.get("metadata", {}), default=str),
                    timestamp=ndata.get("timestamp", ""),
                )
            for u, v, key, edata in graph.graph.edges(keys=True, data=True):
                rel_type = edata.get("edge_type", "RELATED_TO").upper()
                await session.run(
                    f"MATCH (a:Evidence {{id: $src}}), (b:Evidence {{id: $tgt}}) "
                    f"CREATE (a)-[r:{rel_type} {{weight: $weight, metadata: $metadata, "
                    f"timestamp: $timestamp}}]->(b)",
                    src=u, tgt=v,
                    weight=edata.get("weight", 1.0),
                    metadata=json.dumps(edata.get("metadata", {}), default=str),
                    timestamp=edata.get("timestamp", ""),
                )
        logger.debug("Synced %d nodes to Neo4j", graph.node_count())
    except Exception as e:
        logger.warning("Neo4j sync failed: %s", e)


# ── Endpoints ──────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    gnn_status = "loaded" if gnn_analyzer and gnn_analyzer._model else "unavailable"
    return {
        "module": MODULE_ID,
        "version": MODULE_VERSION,
        "status": "healthy",
        "timestamp": _ts(),
        "graph": {
            "nodes": evidence_graph.node_count(),
            "edges": evidence_graph.edge_count(),
        },
        "models": {
            "gnn": gnn_status,
            "embedding_fuser": "available",
            "temporal_analyzer": "available",
        },
        "neo4j": "connected" if neo4j_driver else "disconnected",
    }


@app.post("/correlate/graph")
async def correlate_graph(
    request: CorrelationRequest,
    graph: EvidenceGraph = Depends(get_evidence_graph),
    engine: GraphQueryEngine = Depends(get_query_engine),
):
    evt_id = _id()
    try:
        added = []
        for item in request.evidence_items:
            ids = graph.add_evidence_item(
                item,
                case_id=request.case_id or item.get("case_id", ""),
                domain=request.domain or item.get("domain", ""),
            )
            added.extend(ids)

        await _sync_to_neo4j(graph)

        summary = engine.graph_summary()
        summary["evidence_added"] = len(added)
        summary["correlation_id"] = evt_id
        summary["timestamp"] = _ts()

        return summary
    except Exception as e:
        logger.exception("Graph correlation failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/correlate/temporal")
async def correlate_temporal(
    request: TemporalCorrelationRequest,
    analyzer: TemporalLinkAnalyzer = Depends(get_temporal_analyzer),
):
    evt_id = _id()
    try:
        analyzer.clear()

        if request.options.get("window_size_seconds"):
            analyzer.window_size_seconds = request.options["window_size_seconds"]
        if request.options.get("slide_seconds"):
            analyzer.slide = request.options["slide_seconds"]

        analyzer.add_events(request.events)

        links = analyzer.discover_links(
            min_cooccurrence=request.options.get("min_cooccurrence", 2),
            max_gap_seconds=request.options.get("max_gap_seconds"),
        )

        sequences = analyzer.mine_sequences(
            min_support=request.options.get("min_support", 2),
            max_gap_seconds=request.options.get("sequence_gap_seconds", 3600),
            pattern_length=request.options.get("pattern_length", 3),
        )

        periodic = analyzer.detect_periodic_patterns(
            entity_id=request.options.get("entity_id"),
            min_period_hours=request.options.get("min_period_hours", 0.5),
            max_period_hours=request.options.get("max_period_hours", 168),
        )

        anomalies = analyzer.detect_anomalies(
            entity_id=request.options.get("entity_id"),
            std_threshold=request.options.get("std_threshold", 2.0),
            time_window_hours=request.options.get("time_window_hours", 24),
        )

        windows = analyzer.sliding_window_correlation(
            window_size_seconds=request.window_size_seconds,
            slide_seconds=request.slide_seconds,
        )

        return {
            "correlation_id": evt_id,
            "timestamp": _ts(),
            "event_count": analyzer.event_count,
            "links": {
                "total": len(links),
                "items": [
                    {
                        "source": l.source_id,
                        "target": l.target_id,
                        "weight": l.weight,
                        "relationship": l.relationship_type,
                        "evidence_count": len(l.evidence_ids),
                    }
                    for l in links[:50]
                ],
            },
            "sequences": [
                {
                    "id": s.sequence_id,
                    "pattern": [e["type"] for e in s.events],
                    "confidence": s.confidence,
                    "period_hours": s.period_seconds / 3600 if s.period_seconds else None,
                    "description": s.description,
                }
                for s in sequences
            ],
            "periodic_patterns": [
                {
                    "id": p.sequence_id,
                    "period_hours": p.period_seconds / 3600 if p.period_seconds else None,
                    "confidence": p.confidence,
                    "description": p.description,
                }
                for p in periodic
            ],
            "anomalies": [
                {
                    "timestamp": a.timestamp,
                    "entity": a.entity_id,
                    "score": a.anomaly_score,
                    "type": a.anomaly_type,
                    "description": a.description,
                }
                for a in anomalies[:20]
            ],
            "time_windows": windows,
        }
    except Exception as e:
        logger.exception("Temporal correlation failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/correlate/multi-modal")
async def correlate_multi_modal(
    request: MultiModalRequest,
    fuser: EmbeddingFuser = Depends(get_embedding_fuser),
):
    evt_id = _id()
    try:
        query_emb = None
        query_modality = request.query.get("modality", request.options.get("modality", "text"))
        query_data = request.query.get("data", request.query.get("text", ""))

        if request.embedding:
            query_emb = request.embedding
        elif query_data:
            fused = fuser.embed_evidence(
                evidence_id="query",
                modality=query_modality,
                data=query_data,
                metadata=request.query.get("metadata"),
            )
            query_emb = fused.reduced_embedding or fused.embedding

        if not query_emb:
            raise HTTPException(status_code=400, detail="No query embedding or data provided")

        candidate_embeddings: list[FusedEmbedding] = []
        for cand in request.candidates:
            modality = cand.get("modality", "text")
            data = cand.get("data", cand.get("text", ""))
            eid = cand.get("evidence_id", cand.get("id", _id()))
            fe = fuser.embed_evidence(
                evidence_id=eid,
                modality=modality,
                data=data,
                metadata=cand.get("metadata"),
            )
            candidate_embeddings.append(fe)

        matches = fuser.find_similar(
            query_embedding=query_emb,
            candidates=candidate_embeddings,
            top_k=request.top_k,
            threshold=request.threshold,
        )

        return {
            "correlation_id": evt_id,
            "timestamp": _ts(),
            "query_modality": query_modality,
            "matches": [
                {
                    "evidence_id": m.evidence_id,
                    "similarity": m.similarity,
                    "modality": m.modality,
                    "metadata": m.metadata,
                }
                for m in matches
            ],
            "match_count": len(matches),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Multi-modal correlation failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/correlate/entity")
async def correlate_entity(
    request: EntityCorrelationRequest,
    graph: EvidenceGraph = Depends(get_evidence_graph),
    engine: GraphQueryEngine = Depends(get_query_engine),
):
    evt_id = _id()
    try:
        entity_types = request.entity_types or [
            "file", "ip", "domain", "email", "person", "device", "location", "event", "organization"
        ]

        added = []
        for item in request.evidence_items:
            ids = graph.add_evidence_item(
                item,
                case_id=request.case_id or item.get("case_id", ""),
                domain=item.get("domain", ""),
            )
            added.extend(ids)

        entity_views = {}
        for etype in entity_types:
            sub = engine.extract_subgraph_by_type(node_type=etype)
            if sub:
                cent = engine.centrality_pagerank(top_k=10)
                entity_views[etype] = {
                    "node_count": len(sub.get("nodes", [])),
                    "edge_count": len(sub.get("links", [])),
                    "top_nodes": [
                        c.to_dict() for c in cent
                        if c.node_type == etype
                    ][:5],
                }

        node_types = engine.node_count_by_type()
        communities = engine.detect_communities_louvain(min_size=2)

        return {
            "correlation_id": evt_id,
            "timestamp": _ts(),
            "evidence_added": len(added),
            "entity_summary": node_types,
            "entity_views": entity_views,
            "communities": [
                {
                    "id": c.community_id,
                    "size": c.size,
                    "node_types": list(set(n.get("node_type", "") for n in c.nodes)),
                    "modularity": c.modularity,
                }
                for c in communities[:20]
            ],
            "graph_summary": engine.graph_summary(),
        }
    except Exception as e:
        logger.exception("Entity correlation failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/patterns")
async def analyze_patterns(
    request: PatternDiscoveryRequest,
    analyzer: Optional[GNNAnalyzer] = Depends(get_gnn_analyzer),
    engine: GraphQueryEngine = Depends(get_query_engine),
):
    evt_id = _id()
    try:
        pattern_results: dict[str, Any] = {
            "analysis_id": evt_id,
            "timestamp": _ts(),
            "ml_patterns": [],
            "graph_patterns": [],
            "motifs": [],
        }

        graph_data = request.graph_data or engine.extract_subgraph(
            node_ids=list(engine.graph.nodes())[:100] if engine.graph.nodes() else [],
        ) or {"nodes": [], "links": []}

        if graph_data.get("nodes"):
            motifs = engine.detect_motifs(motif_size=3, max_motifs=20)
            pattern_results["motifs"] = [
                {
                    "nodes": m.nodes,
                    "pattern_type": m.pattern_type,
                    "score": m.score,
                }
                for m in motifs
            ]

            communities = engine.detect_communities_louvain(min_size=2)
            pattern_results["graph_patterns"] = [
                {
                    "type": "community",
                    "community_id": c.community_id,
                    "size": c.size,
                    "modularity": c.modularity,
                }
                for c in communities[:10]
            ]

        if analyzer is not None:
            analysis = analyzer.analyze_pattern(
                graph_data=graph_data,
                graph_id=evt_id,
            )
            pattern_results["ml_patterns"] = [
                {
                    "pattern_type": p["pattern_type"],
                    "confidence": p["confidence"],
                    "description": p["description"],
                }
                for p in analysis.patterns_detected
                if p["confidence"] >= request.min_confidence
            ]
            pattern_results["classification"] = {
                "predicted_class": PATTERN_CLASSES[analysis.predicted_class]
                if analysis.predicted_class < len(PATTERN_CLASSES) else "unknown",
                "confidence": analysis.confidence,
                "class_probabilities": analysis.class_probabilities,
            }
            pattern_results["cluster_quality"] = analysis.cluster_quality

        return pattern_results
    except Exception as e:
        logger.exception("Pattern analysis failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/anomalies")
async def analyze_anomalies(
    request: AnomalyDetectionRequest,
    analyzer: Optional[GNNAnalyzer] = Depends(get_gnn_analyzer),
    engine: GraphQueryEngine = Depends(get_query_engine),
    temporal: TemporalLinkAnalyzer = Depends(get_temporal_analyzer),
):
    evt_id = _id()
    try:
        anomalies: dict[str, Any] = {
            "analysis_id": evt_id,
            "timestamp": _ts(),
            "graph_anomalies": [],
            "temporal_anomalies": [],
            "statistical_summary": {},
        }

        graph_data = request.graph_data or engine.extract_subgraph(
            node_ids=list(engine.graph.nodes())[:100] if engine.graph.nodes() else [],
        ) or {"nodes": [], "links": []}

        if analyzer is not None and graph_data.get("nodes"):
            graph_anoms = analyzer.detect_anomalous_subgraphs(
                graph_data=graph_data,
                threshold=request.threshold,
            )
            anomalies["graph_anomalies"] = graph_anoms

        temp_anoms = temporal.detect_anomalies(
            std_threshold=request.options.get("std_threshold", 2.0),
            time_window_hours=request.options.get("time_window_hours", 24),
        )
        anomalies["temporal_anomalies"] = [
            {
                "timestamp": a.timestamp,
                "entity": a.entity_id,
                "score": a.anomaly_score,
                "type": a.anomaly_type,
                "description": a.description,
            }
            for a in temp_anoms[:30]
        ]

        anomalies["statistical_summary"] = query_engine.graph_summary()

        return anomalies
    except Exception as e:
        logger.exception("Anomaly detection failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/similar")
async def query_similar(
    request: SimilarityQueryRequest,
    engine: GraphQueryEngine = Depends(get_query_engine),
    fuser: EmbeddingFuser = Depends(get_embedding_fuser),
):
    evt_id = _id()
    try:
        if request.evidence_id and engine.graph.has_node(request.evidence_id):
            ndata = dict(engine.graph.nodes[request.evidence_id])
            label = ndata.get("label", "")
            metadata = ndata.get("metadata", {})
            node_type = ndata.get("node_type", "text")

            fused = fuser.embed_evidence(
                evidence_id=request.evidence_id,
                modality=request.modality or node_type,
                data=json.dumps({"label": label, **metadata}, default=str),
                metadata=ndata,
            )
            query_emb = fused.reduced_embedding or fused.embedding
        elif request.embedding:
            query_emb = request.embedding
        elif request.data:
            fused = fuser.embed_evidence(
                evidence_id="query",
                modality=request.modality,
                data=request.data,
            )
            query_emb = fused.reduced_embedding or fused.embedding
        else:
            raise HTTPException(status_code=400, detail="No query provided")

        candidates: list[FusedEmbedding] = []
        for nid, ndata in engine.graph.nodes(data=True):
            if request.evidence_id and nid == request.evidence_id:
                continue
            fe = fuser.embed_evidence(
                evidence_id=nid,
                modality=ndata.get("node_type", "text"),
                data=json.dumps({"label": ndata.get("label", ""), **ndata.get("metadata", {})}, default=str),
                metadata=ndata,
            )
            candidates.append(fe)

        matches = fuser.find_similar(
            query_embedding=query_emb,
            candidates=candidates,
            top_k=request.top_k,
            threshold=request.threshold,
        )

        return {
            "query_id": evt_id,
            "timestamp": _ts(),
            "query_node": request.evidence_id or "custom_query",
            "matches": [
                {
                    "evidence_id": m.evidence_id,
                    "similarity": m.similarity,
                    "modality": m.modality,
                    "node_label": m.metadata.get("label", ""),
                    "node_type": m.metadata.get("node_type", ""),
                }
                for m in matches
            ],
            "match_count": len(matches),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Similarity query failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/path")
async def query_path(
    request: PathQueryRequest,
    engine: GraphQueryEngine = Depends(get_query_engine),
):
    evt_id = _id()
    try:
        if not engine.graph.has_node(request.source_id):
            raise HTTPException(status_code=404, detail=f"Source node not found: {request.source_id}")
        if not engine.graph.has_node(request.target_id):
            raise HTTPException(status_code=404, detail=f"Target node not found: {request.target_id}")

        path_detail = engine.shortest_path_details(request.source_id, request.target_id)
        all_paths = engine.all_shortest_paths(request.source_id, request.target_id, max_paths=10)

        if path_detail is None:
            return {
                "query_id": evt_id,
                "timestamp": _ts(),
                "source": request.source_id,
                "target": request.target_id,
                "found": False,
                "paths": [],
            }

        return {
            "query_id": evt_id,
            "timestamp": _ts(),
            "source": request.source_id,
            "target": request.target_id,
            "found": True,
            "shortest_path": path_detail,
            "all_paths": [
                {
                    "path": p,
                    "length": len(p),
                }
                for p in all_paths
            ],
            "alternate_path_count": len(all_paths),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Path query failed")
        raise HTTPException(status_code=500, detail=str(e))

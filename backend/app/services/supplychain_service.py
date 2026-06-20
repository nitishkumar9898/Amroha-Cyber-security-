# backend/app/services/supplychain_service.py

import json
from typing import List, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session

from ..models.supplychain import (
    SupplyChainEntity,
    RiskEvent,
    Anomaly,
    SimulationScenario,
)
from ..schemas.supplychain import (
    SBOMIngestRequest,
    AnomalyDetectRequest,
    SimulationRequest,
)

# ---------------------------------------------------------------------------
# SBOM ingestion – parses a generic SBOM (SPDX/CycloneDX) and stores entities
# ---------------------------------------------------------------------------

def ingest_sbom(db: Session, payload: SBOMIngestRequest) -> List[SupplyChainEntity]:
    sbom = payload.sbom
    created_entities = []
    # Very simple generic parser – real implementation would handle SPDX/CycloneDX spec
    for comp in sbom.get("components", []):
        entity = SupplyChainEntity(
            name=comp.get("name", "unknown"),
            type=comp.get("type", "software"),
            version=comp.get("version", ""),
            provenance_hash=comp.get("purl", ""),
            metadata=comp,
        )
        db.add(entity)
        created_entities.append(entity)
    db.commit()
    for e in created_entities:
        db.refresh(e)
    return created_entities

# ---------------------------------------------------------------------------
# Risk graph generation – builds a NetworkX graph for later visualisation
# ---------------------------------------------------------------------------

import networkx as nx

def build_risk_graph(db: Session) -> Dict[str, Any]:
    entities = db.query(SupplyChainEntity).all()
    G = nx.DiGraph()
    for e in entities:
        G.add_node(e.id, name=e.name, type=e.type, version=e.version)
        # Example: link entities based on "dependsOn" field in metadata (if present)
        for dep in e.additional_metadata.get("dependsOn", []):
            target = db.query(SupplyChainEntity).filter_by(provenance_hash=dep).first()
            if target:
                G.add_edge(e.id, target.id)
    nodes = [{"id": n, **G.nodes[n]} for n in G.nodes]
    edges = [{"source": u, "target": v} for u, v in G.edges]
    return {"nodes": nodes, "edges": edges}

# ---------------------------------------------------------------------------
# AI anomaly detection – stub that calls an LLM (placeholder)
# ---------------------------------------------------------------------------

def detect_anomaly(db: Session, payload: AnomalyDetectRequest) -> Anomaly:
    # Simple heuristic stub – replace with real LLM call later
    score = 0.0
    data = payload.data
    if data.get("suspicious_changes"):
        score += 0.6
    if data.get("unknown_vendor"):
        score += 0.3
    score = min(score, 1.0)
    anomaly = Anomaly(entity_id=payload.entity_id, score=score, details=data)
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)
    return anomaly

# ---------------------------------------------------------------------------
# APT simulation – generates a mitigation plan using a prompt template
# ---------------------------------------------------------------------------

def simulate_apt(db: Session, payload: SimulationRequest) -> SimulationScenario:
    # Placeholder logic – in production you'd call a LLM with a rich prompt
    plan = {
        "scenario": payload.name,
        "steps": [
            "Identify compromised component",
            "Isolate affected supply‑chain node",
            "Patch or replace the component",
            "Perform forensic audit and update provenance records",
            "Notify stakeholders and apply mitigation controls",
        ],
        "parameters": payload.parameters or {},
    }
    scenario = SimulationScenario(
        name=payload.name,
        description=payload.parameters.get("description") if payload.parameters else None,
        generated_plan=plan,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario

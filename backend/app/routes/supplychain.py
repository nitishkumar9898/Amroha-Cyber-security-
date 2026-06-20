# backend/app/routes/supplychain.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..dependencies import get_db  # if not existing, fallback to database.get_db
from ..schemas.supplychain import (
    SBOMIngestRequest,
    AnomalyDetectRequest,
    SimulationRequest,
    SupplyChainEntitySchema,
    RiskEventSchema,
    AnomalySchema,
    SimulationScenarioSchema,
)
from ..services.supplychain_service import (
    ingest_sbom,
    build_risk_graph,
    detect_anomaly,
    simulate_apt,
)

router = APIRouter(prefix="/supplychain", tags=["supplychain"])

@router.post("/ingest", response_model=List[SupplyChainEntitySchema])
def ingest_endpoint(request: SBOMIngestRequest, db: Session = Depends(get_db)):
    entities = ingest_sbom(db, request)
    return entities

@router.get("/risk", response_model=Dict[str, Any])
def risk_graph_endpoint(db: Session = Depends(get_db)):
    graph = build_risk_graph(db)
    return graph

@router.post("/anomaly", response_model=AnomalySchema)
def anomaly_endpoint(request: AnomalyDetectRequest, db: Session = Depends(get_db)):
    anomaly = detect_anomaly(db, request)
    return anomaly

@router.post("/simulate", response_model=SimulationScenarioSchema)
def simulate_endpoint(request: SimulationRequest, db: Session = Depends(get_db)):
    scenario = simulate_apt(db, request)
    return scenario

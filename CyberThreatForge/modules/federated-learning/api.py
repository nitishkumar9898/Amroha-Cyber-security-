"""Federated Learning Across Agencies — FastAPI Application.

Enables multiple law enforcement agencies to collaboratively train
threat detection models without sharing raw evidence. Uses secure
aggregation, differential privacy, and quantum-safe encryption.
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

# Ensure the module root is on sys.path for standalone execution
_api_dir = os.path.dirname(os.path.abspath(__file__))
if _api_dir not in sys.path:
    sys.path.insert(0, _api_dir)

from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from federated.server import FederatedServer, ClientRegistration, TrainingRound
from federated.client import FederatedClient
from federated.secure_aggregation import AggregationResult
from models.malware_cnn import MalwareCNN, EvaluationMetrics
from models.dp_engine import DifferentialPrivacyEngine

logger = logging.getLogger(__name__)

MODULE_ID = "federated-learning"
MODULE_VERSION = "1.0.0"

# ── Globals ───────────────────────────────────────────────────────────

fl_server = FederatedServer(
    min_clients=2,
    aggregation_threshold=2,
    dp_epsilon=1.0,
    dp_delta=1e-5,
    max_grad_norm=1.0,
    checkpoint_dir=os.path.join(os.path.dirname(__file__), "checkpoints"),
)
_agencies: dict[str, FederatedClient] = {}

# ── Pydantic Models ───────────────────────────────────────────────────


class RegisterClientRequest(BaseModel):
    agency_name: str = Field(..., min_length=1, max_length=200)
    public_key: str = Field(..., min_length=1)
    dilithium_public_key: str = ""
    jurisdiction: str = ""


class RegisterClientResponse(BaseModel):
    client_id: str
    agency_name: str
    public_key: str
    registered_at: str
    jurisdiction: str


class StartRoundRequest(BaseModel):
    client_ids: Optional[list[str]] = None


class StartRoundResponse(BaseModel):
    round_id: str
    round_number: int
    status: str
    started_at: str
    clients_invited: list[str]
    num_clients_requested: int


class SubmitUpdateRequest(BaseModel):
    round_id: str
    client_id: str
    encrypted_gradients: list[str]  # base64-encoded encrypted gradients
    dp_epsilon_used: float = 0.0


class AggregateResponse(BaseModel):
    round_id: str
    status: str
    num_participants: int
    contributions: dict[str, float]
    model_checkpoint: str


class ModelResponse(BaseModel):
    weights: list[list[Any]]
    parameter_count: int
    round_number: int
    round_id: str
    architecture: str
    timestamp: str


class RoundStatusResponse(BaseModel):
    round_id: str
    round_number: int
    status: str
    started_at: str
    completed_at: str
    clients_invited: list[str]
    clients_submitted: list[str]
    num_clients_requested: int
    num_clients_submitted: int
    anomaly_flags: list[dict]


class ContributionResponse(BaseModel):
    contributions: list[dict]


class EvaluateRequest(BaseModel):
    test_data: Optional[list[dict]] = None


class EvaluateResponse(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    loss: float
    num_samples: int
    model_parameters: int
    timestamp: str


class HealthResponse(BaseModel):
    module: str
    version: str
    status: str
    timestamp: str
    num_clients: int
    num_rounds: int
    model_loaded: bool
    dp_enabled: bool


# ── App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Federated Learning Across Agencies",
    description=(
        "Multi-agency collaborative threat model training with secure "
        "aggregation, differential privacy, and quantum-safe encryption. "
        "No raw evidence ever leaves agency boundaries."
    ),
    version=MODULE_VERSION,
)


# ── Helpers ───────────────────────────────────────────────────────────


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Lifecycle ─────────────────────────────────────────────────────────


@app.on_event("startup")
async def startup():
    logger.info("Federated Learning module starting — version %s", MODULE_VERSION)
    model_count = fl_server.global_model.get_parameter_count()
    logger.info("Global model initialised: %d parameters", model_count)


@app.on_event("shutdown")
async def shutdown():
    logger.info("Federated Learning module shutting down")


# ── Endpoints ─────────────────────────────────────────────────────────


@app.get("/health", response_model=HealthResponse)
async def health():
    completed = sum(
        1 for r in fl_server._rounds.values() if r.status == "completed"
    )
    return HealthResponse(
        module=MODULE_ID,
        version=MODULE_VERSION,
        status="healthy",
        timestamp=_ts(),
        num_clients=len(fl_server._clients),
        num_rounds=completed,
        model_loaded=True,
        dp_enabled=True,
    )


@app.post("/fl/register-client", response_model=RegisterClientResponse)
async def register_client(request: RegisterClientRequest):
    try:
        registration = fl_server.register_client(
            agency_name=request.agency_name,
            public_key=request.public_key,
            dilithium_public_key=request.dilithium_public_key,
            jurisdiction=request.jurisdiction,
        )
        # Create per-agency FL client
        client = FederatedClient(
            client_id=registration.client_id,
            agency_name=request.agency_name,
            public_key=request.public_key,
            dilithium_public_key=request.dilithium_public_key,
        )
        client.load_local_data({"samples": []})
        _agencies[registration.client_id] = client

        return RegisterClientResponse(
            client_id=registration.client_id,
            agency_name=registration.agency_name,
            public_key=registration.public_key,
            registered_at=registration.registered_at,
            jurisdiction=registration.jurisdiction,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Client registration failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fl/start-round", response_model=StartRoundResponse)
async def start_round(request: StartRoundRequest):
    try:
        round_info = fl_server.start_round(client_ids=request.client_ids)
        return StartRoundResponse(
            round_id=round_info.round_id,
            round_number=round_info.round_number,
            status=round_info.status,
            started_at=round_info.started_at,
            clients_invited=round_info.clients_invited,
            num_clients_requested=round_info.num_clients_requested,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Start round failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fl/submit-update")
async def submit_update(request: SubmitUpdateRequest):
    try:
        # Decode base64-encoded gradients to bytes
        try:
            import base64
            encrypted_bytes = [
                base64.b64decode(eg) for eg in request.encrypted_gradients
            ]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 gradient encoding")

        result = fl_server.submit_update(
            round_id=request.round_id,
            client_id=request.client_id,
            encrypted_gradients=encrypted_bytes,
            public_key=_get_client_public_key(request.client_id),
            dp_epsilon_used=request.dp_epsilon_used,
        )
        return {
            "success": True,
            "round_id": request.round_id,
            "client_id": request.client_id,
            "timestamp": _ts(),
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Submit update failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fl/aggregate", response_model=AggregateResponse)
async def aggregate(round_id: str = Body(..., embed=True)):
    try:
        result = fl_server.aggregate(round_id)
        return AggregateResponse(
            round_id=result.round_id,
            status="completed",
            num_participants=result.num_participants,
            contributions=result.contributions,
            model_checkpoint=fl_server._rounds[round_id].model_checkpoint or "",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Aggregation failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fl/model/latest", response_model=ModelResponse)
async def get_latest_model():
    model_data = fl_server.get_latest_model()
    return ModelResponse(**model_data)


@app.get("/fl/round/{round_id}/status", response_model=RoundStatusResponse)
async def get_round_status(round_id: str):
    round_info = fl_server.get_round_status(round_id)
    if round_info is None:
        raise HTTPException(status_code=404, detail=f"Round not found: {round_id}")
    return RoundStatusResponse(
        round_id=round_info.round_id,
        round_number=round_info.round_number,
        status=round_info.status,
        started_at=round_info.started_at,
        completed_at=round_info.completed_at,
        clients_invited=round_info.clients_invited,
        clients_submitted=round_info.clients_submitted,
        num_clients_requested=round_info.num_clients_requested,
        num_clients_submitted=round_info.num_clients_submitted,
        anomaly_flags=round_info.anomaly_flags,
    )


@app.get("/fl/contributions", response_model=ContributionResponse)
async def get_contributions():
    contributions = fl_server.get_contributions()
    return ContributionResponse(contributions=contributions)


@app.post("/fl/evaluate", response_model=EvaluateResponse)
async def evaluate(request: EvaluateRequest = Body(default=None)):
    try:
        test_data = None
        if request and request.test_data:
            import numpy as np
            test_data = [
                (np.array(item["x"]), np.array(item["y"]))
                for item in request.test_data
            ]
        result = fl_server.evaluate(test_data)
        return EvaluateResponse(**result)
    except Exception as e:
        logger.exception("Evaluation failed")
        raise HTTPException(status_code=500, detail=str(e))


# ── Internal Helpers ──────────────────────────────────────────────────


def _get_client_public_key(client_id: str) -> str:
    client = fl_server.get_client(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail=f"Client not found: {client_id}")
    return client.public_key

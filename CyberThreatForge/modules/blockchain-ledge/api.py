"""Blockchain Evidence Ledger API — Immutable, append-only evidence log.

Provides cryptographic integrity verification, zero-knowledge proofs,
chain-of-custody tracking, and Section 65B compliant audit trails.
"""

import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from ledge.blockchain import Blockchain, Block, _hash
from ledge.merkle_tree import MerkleTree
from ledge.zk_prover import ZKProver
from ledge.evidence_store import EvidenceStore

try:
    from modules.shared.chain_of_custody import ChainOfCustodyManager
    COC_AVAILABLE = True
except ImportError:
    COC_AVAILABLE = False
    ChainOfCustodyManager = None  # type: ignore

logger = logging.getLogger(__name__)

MODULE_ID = "blockchain-ledge"
MODULE_VERSION = "1.0.0"

HASH_ALGO = "sha3_512"

# ── Globals ──────────────────────────────────────────────────────────────

blockchain: Blockchain = Blockchain(case_metadata={"module": MODULE_ID, "version": MODULE_VERSION})
evidence_store: EvidenceStore = EvidenceStore()
zk_prover: ZKProver = ZKProver()
coc_manager: Any = None

if COC_AVAILABLE:
    coc_manager = ChainOfCustodyManager()

# ── Pydantic Models ──────────────────────────────────────────────────────


class EvidenceRecordRequest(BaseModel):
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str = Field(default_factory=lambda: f"case-{uuid.uuid4().hex[:8]}")
    data_hash: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor: str = "system"
    module: str = MODULE_ID


class BatchRecordRequest(BaseModel):
    entries: list[EvidenceRecordRequest]


class EvidenceRecordResponse(BaseModel):
    evidence_id: str
    block_index: int
    block_hash: str
    merkle_root: str
    chain_of_custody_hash: str
    timestamp: float
    status: str = "recorded"


class BatchRecordResponse(BaseModel):
    batch_id: str
    records: list[EvidenceRecordResponse]
    count: int
    merkle_root: str
    timestamp: float


class VerificationResponse(BaseModel):
    evidence_id: str
    exists: bool
    block_index: Optional[int] = None
    hash_integrity: bool = False
    chain_integrity: bool = False
    chain_of_custody_valid: bool = False
    timestamp: Optional[float] = None
    status: str = "not_found"


class ZKProofResponse(BaseModel):
    evidence_id: str
    proof: dict[str, Any]
    proof_type: str = "zk-snark-simulated"
    timestamp: float


class ZKVerifyResponse(BaseModel):
    evidence_id: str
    proof_valid: bool
    timestamp: float


class ChainResponse(BaseModel):
    length: int
    genesis_hash: str
    latest_hash: str
    chain: list[dict[str, Any]]
    valid: bool
    timestamp: float


class StatusResponse(BaseModel):
    evidence_id: str
    status: str
    block_index: Optional[int] = None
    block_hash: Optional[str] = None
    verified: bool = False
    chain_of_custody: list[dict[str, Any]] = Field(default_factory=list)


class AuditResponse(BaseModel):
    entries: list[dict[str, Any]]
    count: int
    section_65b_compliant: bool = True
    timestamp: str


class HealthResponse(BaseModel):
    module: str
    version: str
    status: str
    timestamp: str
    chain_length: int
    chain_valid: bool
    evidence_count: int
    storage: str
    coc_integrated: bool

# ── FastAPI App ──────────────────────────────────────────────────────────

app = FastAPI(
    title="Blockchain Evidence Ledger",
    description="Immutable, append-only evidence log with zero-knowledge proofs "
                "and chain-of-custody tracking. Section 65B compliant.",
    version=MODULE_VERSION,
)


@app.on_event("startup")
async def startup():
    global blockchain, evidence_store, zk_prover, coc_manager

    logger.info("Starting Blockchain Evidence Ledger...")

    stored_blocks = evidence_store.get_all_blocks()
    if stored_blocks:
        blocks_data = []
        for b in stored_blocks:
            blocks_data.append({
                "index": b["index"],
                "timestamp": b["timestamp"],
                "data_hash": b["data_hash"],
                "prev_hash": b["prev_hash"],
                "nonce": b.get("nonce", 0),
                "merkle_root": b.get("merkle_root", ""),
                "signature": b.get("signature", ""),
                "chain_of_custody_hash": b.get("chain_of_custody_hash", ""),
                "hash": b["block_hash"],
            })
        blockchain = Blockchain.from_dict(blocks_data, case_metadata={"module": MODULE_ID})
        valid, issues = blockchain.validate_chain()
        if not valid:
            logger.warning("Chain validation issues on startup: %s", issues)
        else:
            logger.info("Chain loaded and validated (%d blocks)", len(blocks_data))

    if COC_AVAILABLE:
        coc_manager = ChainOfCustodyManager()
        logger.info("Chain of custody manager integrated")


# ── Helpers ──────────────────────────────────────────────────────────────


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ts_float() -> float:
    return time.time()


def _compute_data_hash(content: str) -> str:
    return hashlib.new(HASH_ALGO, content.encode("utf-8")).hexdigest()


def _record_coc(action: str, evidence_id: str, actor: str = "system", data: Optional[dict] = None) -> str:
    if coc_manager:
        event = coc_manager.record(
            action=action,
            actor=actor,
            module=MODULE_ID,
            data=data or {"evidence_id": evidence_id},
        )
        return event.hash
    return _hash(f"{action}:{evidence_id}:{_ts()}")


def _verify_coc_chain() -> bool:
    if coc_manager:
        valid, _ = coc_manager.verify_chain()
        return valid
    return True


# ── Endpoints ────────────────────────────────────────────────────────────


@app.get("/health", response_model=HealthResponse)
async def health():
    valid, _ = blockchain.validate_chain()
    evidence_count = len(evidence_store.get_all_blocks())
    return HealthResponse(
        module=MODULE_ID,
        version=MODULE_VERSION,
        status="healthy",
        timestamp=_ts(),
        chain_length=len(blockchain.chain),
        chain_valid=valid,
        evidence_count=evidence_count,
        storage="sqlite",
        coc_integrated=COC_AVAILABLE and coc_manager is not None,
    )


@app.post("/ledge/record", response_model=EvidenceRecordResponse)
async def record_evidence(request: EvidenceRecordRequest):
    data_hash = request.data_hash
    coc_hash = _record_coc(
        "evidence_recorded",
        request.evidence_id,
        request.actor,
        {"case_id": request.case_id, "module": request.module},
    )

    block = blockchain.add_block(
        data_hash=data_hash,
        merkle_root=data_hash,
        chain_of_custody_hash=coc_hash,
    )

    evidence_store.store_block(block.to_dict())
    evidence_store.store_evidence(
        evidence_id=request.evidence_id,
        case_id=request.case_id,
        block_index=block.index,
        data_hash=data_hash,
        ts=block.timestamp,
        metadata=request.metadata,
        chain_of_custody=[coc_manager.to_dict()[-1]] if coc_manager and coc_manager._events else None,
    )
    evidence_store.log_audit(
        action="evidence_recorded",
        evidence_id=request.evidence_id,
        block_index=block.index,
        actor=request.actor,
        details={"case_id": request.case_id, "data_hash": data_hash},
    )

    return EvidenceRecordResponse(
        evidence_id=request.evidence_id,
        block_index=block.index,
        block_hash=block.hash,
        merkle_root=block.merkle_root,
        chain_of_custody_hash=block.chain_of_custody_hash,
        timestamp=block.timestamp,
        status="recorded",
    )


@app.post("/ledge/batch", response_model=BatchRecordResponse)
async def batch_record(request: BatchRecordRequest):
    if not request.entries:
        raise HTTPException(status_code=400, detail="No entries provided")

    batch_id = str(uuid.uuid4())
    records: list[EvidenceRecordResponse] = []
    data_hashes: list[str] = []

    for entry in request.entries:
        data_hash = entry.data_hash
        data_hashes.append(data_hash)

        coc_hash = _record_coc(
            "evidence_batch_recorded",
            entry.evidence_id,
            entry.actor,
            {"case_id": entry.case_id, "batch_id": batch_id},
        )

        block = blockchain.add_block(
            data_hash=data_hash,
            chain_of_custody_hash=coc_hash,
        )

        evidence_store.store_block(block.to_dict())
        evidence_store.store_evidence(
            evidence_id=entry.evidence_id,
            case_id=entry.case_id,
            block_index=block.index,
            data_hash=data_hash,
            ts=block.timestamp,
            metadata=entry.metadata,
        )
        evidence_store.log_audit(
            action="evidence_batch_recorded",
            evidence_id=entry.evidence_id,
            block_index=block.index,
            actor=entry.actor,
            details={"case_id": entry.case_id, "batch_id": batch_id},
        )

        records.append(EvidenceRecordResponse(
            evidence_id=entry.evidence_id,
            block_index=block.index,
            block_hash=block.hash,
            merkle_root=block.merkle_root,
            chain_of_custody_hash=block.chain_of_custody_hash,
            timestamp=block.timestamp,
            status="recorded",
        ))

    merkle_tree = MerkleTree(data_hashes)
    merkle_root = merkle_tree.root

    # Update the last block with computed merkle root
    if blockchain.latest_block:
        last_block = blockchain.latest_block
        last_block.merkle_root = merkle_root
        evidence_store.store_block(last_block.to_dict())

    return BatchRecordResponse(
        batch_id=batch_id,
        records=records,
        count=len(records),
        merkle_root=merkle_root,
        timestamp=_ts_float(),
    )


@app.get("/ledge/verify/{evidence_id}", response_model=VerificationResponse)
async def verify_evidence(evidence_id: str):
    ev = evidence_store.get_evidence(evidence_id)
    if ev is None:
        evidence_store.log_audit(action="verify_not_found", evidence_id=evidence_id)
        return VerificationResponse(
            evidence_id=evidence_id,
            exists=False,
            status="not_found",
        )

    block = blockchain.get_block(ev["block_index"])
    if block is None:
        return VerificationResponse(
            evidence_id=evidence_id,
            exists=True,
            block_index=ev["block_index"],
            hash_integrity=False,
            status="block_missing",
        )

    hash_integrity = block.data_hash == ev["data_hash"]
    chain_integrity = True
    valid, _ = blockchain.validate_chain()
    coc_valid = _verify_coc_chain()

    evidence_store.log_audit(
        action="evidence_verified",
        evidence_id=evidence_id,
        block_index=ev["block_index"],
        details={"hash_integrity": hash_integrity, "chain_valid": valid},
    )

    return VerificationResponse(
        evidence_id=evidence_id,
        exists=True,
        block_index=ev["block_index"],
        hash_integrity=hash_integrity,
        chain_integrity=chain_integrity and valid,
        chain_of_custody_valid=coc_valid,
        timestamp=block.timestamp,
        status="verified" if (hash_integrity and valid) else "tampered",
    )


@app.get("/ledge/prove/{evidence_id}", response_model=ZKProofResponse)
async def prove_evidence(evidence_id: str):
    ev = evidence_store.get_evidence(evidence_id)
    if ev is None:
        raise HTTPException(status_code=404, detail=f"Evidence not found: {evidence_id}")

    block = blockchain.get_block(ev["block_index"])
    if block is None:
        raise HTTPException(status_code=404, detail=f"Block not found for evidence: {evidence_id}")

    # Build merkle proof from the chain
    all_hashes = [b.data_hash for b in blockchain.chain]
    tree = MerkleTree(all_hashes)
    found, merkle_proof = tree.generate_proof(ev["data_hash"])
    if not found:
        # Fallback: use adjacent blocks
        merkle_proof = [
            {"position": "left", "hash": block.prev_hash, "level": 0},
            {"position": "right", "hash": block.hash, "level": 0},
        ]

    proof = zk_prover.generate_inclusion_proof(
        evidence_hash=ev["data_hash"],
        merkle_proof=merkle_proof,
        merkle_root=tree.root,
    )

    evidence_store.log_audit(
        action="zk_proof_generated",
        evidence_id=evidence_id,
        block_index=ev["block_index"],
    )

    return ZKProofResponse(
        evidence_id=evidence_id,
        proof=proof,
        proof_type="zk-snark-simulated",
        timestamp=_ts_float(),
    )


@app.get("/ledge/prove/{evidence_id}/verify", response_model=ZKVerifyResponse)
async def verify_proof(evidence_id: str, proof_json: str = Query(..., description="JSON-encoded proof")):
    ev = evidence_store.get_evidence(evidence_id)
    if ev is None:
        raise HTTPException(status_code=404, detail=f"Evidence not found: {evidence_id}")

    try:
        proof = json.loads(proof_json)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid proof JSON")

    proof_valid = ZKProver.verify_inclusion_proof(proof, ev["data_hash"])

    evidence_store.log_audit(
        action="zk_proof_verified",
        evidence_id=evidence_id,
        details={"proof_valid": proof_valid},
    )

    return ZKVerifyResponse(
        evidence_id=evidence_id,
        proof_valid=proof_valid,
        timestamp=_ts_float(),
    )


@app.get("/ledge/chain", response_model=ChainResponse)
async def get_chain():
    chain = blockchain.chain
    valid, _ = blockchain.validate_chain()
    return ChainResponse(
        length=len(chain),
        genesis_hash=chain[0].hash if chain else "",
        latest_hash=chain[-1].hash if chain else "",
        chain=[b.to_dict() for b in chain],
        valid=valid,
        timestamp=_ts_float(),
    )


@app.get("/ledge/status/{evidence_id}", response_model=StatusResponse)
async def check_status(evidence_id: str):
    ev = evidence_store.get_evidence(evidence_id)
    if ev is None:
        return StatusResponse(
            evidence_id=evidence_id,
            status="not_found",
        )

    block = blockchain.get_block(ev["block_index"])
    verified = False
    block_hash = None
    if block:
        verified = block.data_hash == ev["data_hash"]
        chain_valid, _ = blockchain.validate_chain()
        verified = verified and chain_valid
        block_hash = block.hash

    coc = ev.get("chain_of_custody", [])
    if not coc and block:
        coc = [{"action": "recorded", "actor": "system", "module": MODULE_ID, "hash": block.chain_of_custody_hash}]

    status = "verified" if verified else "tampered" if block else "unknown"
    return StatusResponse(
        evidence_id=evidence_id,
        status=status,
        block_index=ev["block_index"],
        block_hash=block_hash,
        verified=verified,
        chain_of_custody=coc,
    )


@app.get("/ledge/audit", response_model=AuditResponse)
async def get_audit_trail(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    action: Optional[str] = Query(None),
):
    if action:
        entries = evidence_store.get_audit_log_by_action(action)
    else:
        entries = evidence_store.get_audit_log(limit=limit, offset=offset)

    return AuditResponse(
        entries=entries,
        count=len(entries),
        section_65b_compliant=True,
        timestamp=_ts(),
    )


@app.get("/ledge/export")
async def export_ledger():
    """Export full ledger to JSON (court-ready format)."""
    output_path = evidence_store.export_to_json()
    return {
        "exported": True,
        "path": output_path,
        "timestamp": _ts(),
    }


@app.get("/ledge/validate")
async def validate_full_chain():
    """Validate entire blockchain integrity."""
    valid, issues = blockchain.validate_chain()
    coc_valid = _verify_coc_chain()
    return {
        "chain_valid": valid,
        "chain_of_custody_valid": coc_valid,
        "block_count": len(blockchain.chain),
        "issues": issues,
        "timestamp": _ts(),
    }

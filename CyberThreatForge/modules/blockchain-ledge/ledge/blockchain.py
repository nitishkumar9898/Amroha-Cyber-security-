import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


HASH_ALGO = "sha3_512"


def _hash(data: str) -> str:
    return hashlib.new(HASH_ALGO, data.encode("utf-8")).hexdigest()


def _compute_block_hash(block: "Block") -> str:
    payload = json.dumps(
        {
            "index": block.index,
            "timestamp": block.timestamp,
            "data_hash": block.data_hash,
            "prev_hash": block.prev_hash,
            "nonce": block.nonce,
            "merkle_root": block.merkle_root,
            "signature": block.signature,
            "chain_of_custody_hash": block.chain_of_custody_hash,
        },
        sort_keys=True,
        default=str,
    )
    return _hash(payload)


@dataclass
class Block:
    index: int
    timestamp: float
    data_hash: str
    prev_hash: str
    nonce: int = 0
    merkle_root: str = ""
    signature: str = ""
    chain_of_custody_hash: str = ""
    hash: str = ""

    def __post_init__(self) -> None:
        if not self.hash:
            self.hash = _compute_block_hash(self)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Block":
        return cls(**data)


class Blockchain:
    def __init__(self, case_metadata: Optional[dict[str, Any]] = None) -> None:
        self._chain: list[Block] = []
        self._case_metadata: dict[str, Any] = case_metadata or {}
        self._forks: list[list[Block]] = []
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        genesis_data = json.dumps(
            {
                "genesis": True,
                "module": "blockchain-ledge",
                "version": "1.0.0",
                "case_metadata": self._case_metadata,
                "created_at": time.time(),
            },
            sort_keys=True,
        )
        genesis_hash = _hash(genesis_data)
        block = Block(
            index=0,
            timestamp=time.time(),
            data_hash=genesis_hash,
            prev_hash="0" * 128,
            nonce=0,
            merkle_root=genesis_hash,
            signature="GENESIS",
            chain_of_custody_hash=genesis_hash,
        )
        block.hash = _compute_block_hash(block)
        self._chain.append(block)

    @property
    def chain(self) -> list[Block]:
        return list(self._chain)

    @property
    def latest_block(self) -> Optional[Block]:
        return self._chain[-1] if self._chain else None

    def add_block(
        self,
        data_hash: str,
        merkle_root: str = "",
        signature: str = "",
        chain_of_custody_hash: str = "",
        nonce: int = 0,
    ) -> Block:
        prev = self.latest_block
        block = Block(
            index=len(self._chain),
            timestamp=time.time(),
            data_hash=data_hash,
            prev_hash=prev.hash if prev else "0" * 128,
            nonce=nonce,
            merkle_root=merkle_root or data_hash,
            signature=signature,
            chain_of_custody_hash=chain_of_custody_hash or data_hash,
        )
        block.hash = _compute_block_hash(block)
        self._chain.append(block)
        return block

    def validate_chain(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        for i, block in enumerate(self._chain):
            expected_hash = _compute_block_hash(block)
            if block.hash != expected_hash:
                errors.append(f"Block {i}: hash mismatch (expected {expected_hash}, got {block.hash})")
            if i > 0:
                if block.prev_hash != self._chain[i - 1].hash:
                    errors.append(f"Block {i}: prev_hash does not match block {i - 1} hash")
        if not errors and not self._chain:
            errors.append("Chain is empty")
        return len(errors) == 0, errors

    def get_block(self, index: int) -> Optional[Block]:
        if 0 <= index < len(self._chain):
            return self._chain[index]
        return None

    def detect_forks(self) -> list[list[Block]]:
        return list(self._forks)

    def resolve_forks(self, preferred_chain: list[Block]) -> bool:
        if len(preferred_chain) <= len(self._chain):
            return False
        valid, _ = Blockchain._validate_chain_static(preferred_chain)
        if not valid:
            return False
        self._forks.append(list(self._chain))
        self._chain = list(preferred_chain)
        return True

    @staticmethod
    def _validate_chain_static(chain: list[Block]) -> tuple[bool, list[str]]:
        errors: list[str] = []
        for i, block in enumerate(chain):
            expected = _compute_block_hash(block)
            if block.hash != expected:
                errors.append(f"Block {i}: hash mismatch")
            if i > 0 and block.prev_hash != chain[i - 1].hash:
                errors.append(f"Block {i}: prev_hash mismatch")
        return len(errors) == 0, errors

    def proof_of_authenticity(self, block_index: int) -> dict[str, Any]:
        block = self.get_block(block_index)
        if block is None:
            return {"valid": False, "error": "Block not found"}
        expected_hash = _compute_block_hash(block)
        valid = block.hash == expected_hash
        prev_valid = True
        if block_index > 0:
            prev_valid = block.prev_hash == self._chain[block_index - 1].hash
        return {
            "valid": valid and prev_valid,
            "block_index": block_index,
            "hash_integrity": valid,
            "chain_link_integrity": prev_valid,
            "timestamp": block.timestamp,
            "data_hash": block.data_hash,
        }

    def to_dict(self) -> list[dict[str, Any]]:
        return [b.to_dict() for b in self._chain]

    @classmethod
    def from_dict(cls, blocks: list[dict[str, Any]], case_metadata: Optional[dict[str, Any]] = None) -> "Blockchain":
        bc = cls.__new__(cls)
        bc._chain = [Block.from_dict(b) for b in blocks]
        bc._case_metadata = case_metadata or {}
        bc._forks = []
        return bc

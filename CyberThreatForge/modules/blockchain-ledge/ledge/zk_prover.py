import hashlib
import json
import time
from typing import Any, Optional


HASH_ALGO = "sha3_512"


def _hash(data: str) -> str:
    return hashlib.new(HASH_ALGO, data.encode("utf-8")).hexdigest()


def _hash_bytes(data: bytes) -> str:
    return hashlib.new(HASH_ALGO, data).hexdigest()


class ZKProver:
    def __init__(self) -> None:
        self._salt: Optional[str] = None

    def _get_salt(self) -> str:
        if self._salt is None:
            self._salt = _hash(str(time.time() * 1000000))
        return self._salt

    def commit(self, evidence_hash: str) -> str:
        salt = self._get_salt()
        return _hash(salt + evidence_hash)

    def generate_inclusion_proof(
        self,
        evidence_hash: str,
        merkle_proof: list[dict[str, Any]],
        merkle_root: str,
    ) -> dict[str, Any]:
        salt = self._get_salt()
        commitment = self.commit(evidence_hash)
        challenge = _hash(commitment + merkle_root)[:16]
        response = _hash(salt + evidence_hash + challenge)

        proof = {
            "proof_type": "zk-snark-simulated",
            "version": "1.0",
            "commitment": commitment,
            "merkle_root": merkle_root,
            "challenge": challenge,
            "response": response,
            "merkle_proof": merkle_proof,
            "salt_commitment": _hash(salt),
            "timestamp": time.time(),
            "protocol": "hash-based-membership",
        }
        return proof

    @staticmethod
    def verify_inclusion_proof(proof: dict[str, Any], evidence_hash: str) -> bool:
        required = ["commitment", "merkle_root", "challenge", "response", "merkle_proof"]
        if not all(k in proof for k in required):
            return False

        expected_challenge = _hash(proof["commitment"] + proof["merkle_root"])[:16]
        if proof["challenge"] != expected_challenge:
            return False

        current = _hash(evidence_hash)
        for item in proof["merkle_proof"]:
            sibling = item["hash"]
            if item["position"] == "right":
                combined = current + sibling
            else:
                combined = sibling + current
            current = _hash(combined)

        return current == proof["merkle_root"]

    @staticmethod
    def generate_privacy_preserving_audit(
        evidence_hash: str,
        block_index: int,
        chain_size: int,
    ) -> dict[str, Any]:
        blinded = _hash(evidence_hash + str(block_index))
        audit = {
            "audit_type": "privacy_preserving",
            "blinded_hash": blinded,
            "block_index_commitment": _hash(str(block_index) + blinded)[:32],
            "chain_size_commitment": _hash(str(chain_size) + blinded)[:32],
            "timestamp": time.time(),
            "reveals_nothing_but": "inclusion_and_position",
        }
        return audit

    @staticmethod
    def verify_privacy_preserving_audit(
        audit: dict[str, Any],
        evidence_hash: str,
        block_index: int,
        chain_size: int,
    ) -> bool:
        blinded = _hash(evidence_hash + str(block_index))
        expected_block_commit = _hash(str(block_index) + blinded)[:32]
        expected_chain_commit = _hash(str(chain_size) + blinded)[:32]
        return (
            audit.get("blinded_hash") == blinded
            and audit.get("block_index_commitment") == expected_block_commit
            and audit.get("chain_size_commitment") == expected_chain_commit
        )

    def to_dict(self) -> dict[str, Any]:
        return {}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ZKProver":
        return cls()

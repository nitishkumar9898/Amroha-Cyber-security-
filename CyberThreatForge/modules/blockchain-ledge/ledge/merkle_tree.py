import hashlib
from typing import Any, Optional


HASH_ALGO = "sha3_512"


def _hash(data: str) -> str:
    return hashlib.new(HASH_ALGO, data.encode("utf-8")).hexdigest()


class MerkleTree:
    def __init__(self, leaves: Optional[list[str]] = None) -> None:
        self._leaves: list[str] = []
        self._tree: list[list[str]] = []
        self._root: str = ""
        self.build(leaves if leaves is not None else [])

    @property
    def root(self) -> str:
        return self._root

    @property
    def leaves(self) -> list[str]:
        return list(self._leaves)

    @property
    def levels(self) -> list[list[str]]:
        return [list(lvl) for lvl in self._tree]

    def build(self, leaves: list[str]) -> str:
        self._leaves = list(leaves)
        if not leaves:
            self._root = _hash("empty_tree")
            self._tree = [[self._root]]
            return self._root

        self._tree = []
        current_level = [_hash(leaf) for leaf in leaves]
        self._tree.append(list(current_level))

        while len(current_level) > 1:
            next_level: list[str] = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = _hash(left + right)
                next_level.append(combined)
            self._tree.append(next_level)
            current_level = next_level

        self._root = current_level[0] if current_level else _hash("empty_tree")
        return self._root

    def generate_proof(self, leaf: str) -> tuple[bool, list[dict[str, Any]]]:
        leaf_hash = _hash(leaf)
        try:
            idx = self._leaves.index(leaf)
        except ValueError:
            try:
                idx = self._tree[0].index(leaf_hash)
            except ValueError:
                return False, []

        proof: list[dict[str, Any]] = []
        for level_idx, level in enumerate(self._tree):
            if len(level) == 1:
                break
            sibling_idx = idx + 1 if idx % 2 == 0 else idx - 1
            if 0 <= sibling_idx < len(level):
                proof.append({
                    "position": "right" if idx % 2 == 0 else "left",
                    "hash": level[sibling_idx],
                    "level": level_idx,
                })
            idx //= 2

        return True, proof

    @staticmethod
    def verify_proof(root: str, leaf: str, proof: list[dict[str, Any]]) -> bool:
        current = _hash(leaf)
        for item in proof:
            sibling = item["hash"]
            if item["position"] == "right":
                combined = current + sibling
            else:
                combined = sibling + current
            current = _hash(combined)
        return current == root

    @staticmethod
    def compute_root(leaves: list[str]) -> str:
        tree = MerkleTree(leaves)
        return tree.root

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self._root,
            "leaves": self._leaves,
            "levels": [[h for h in lvl] for lvl in self._tree],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MerkleTree":
        tree = cls()
        tree._root = data.get("root", "")
        tree._leaves = data.get("leaves", [])
        tree._tree = data.get("levels", [])
        return tree

import json
import os
import hashlib
import hmac
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional

# Path to the immutable log file (stored alongside other compliance logs)
LOG_FILE = os.path.join(os.path.dirname(__file__), "audit_log.jsonl")

# Load secret for HMAC from environment (fallback to a default for dev)
AUDIT_SECRET = os.getenv("AUDIT_SECRET", "dev-secret-key")

# Thread lock to ensure atomic writes
_log_lock = threading.Lock()

class LogEntry:
    """Dataclass‑like container for a single blockchain log entry.
    Fields:
        index: sequential integer starting at 0
        timestamp: ISO‑8601 UTC timestamp
        action: short description of the event
        metadata: arbitrary dict with event details (including role)
        prev_hash: hex string of previous entry hash ("0" for genesis)
        hash: SHA‑256 hash of the entry (excluding the signature field)
        signature: HMAC‑SHA256 of the hash using server secret
    """

    def __init__(self, index: int, action: str, metadata: Dict[str, Any], prev_hash: str):
        self.index = index
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.action = action
        self.metadata = metadata
        self.prev_hash = prev_hash
        self.hash = self._calc_hash()
        self.signature = self._sign_hash()

    def _calc_hash(self) -> str:
        # Deterministic JSON representation without hash/signature
        payload = {
            "index": self.index,
            "timestamp": self.timestamp,
            "action": self.action,
            "metadata": self.metadata,
            "prev_hash": self.prev_hash,
        }
        json_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(json_bytes).hexdigest()

    def _sign_hash(self) -> str:
        return hmac.new(AUDIT_SECRET.encode(), self.hash.encode(), hashlib.sha256).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "action": self.action,
            "metadata": self.metadata,
            "prev_hash": self.prev_hash,
            "hash": self.hash,
            "signature": self.signature,
        }

class BlockchainLog:
    """Append‑only immutable log with hash‑chaining and HMAC signatures.
    Provides methods to append new entries and verify the full chain.
    """

    def __init__(self, file_path: str = LOG_FILE):
        self.file_path = file_path
        # Ensure the log file exists – create genesis entry if empty
        if not os.path.exists(self.file_path) or os.path.getsize(self.file_path) == 0:
            self._write_genesis()

    def _write_genesis(self):
        genesis = LogEntry(index=0, action="genesis", metadata={}, prev_hash="0")
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(genesis.to_dict()) + "\n")

    def _last_entry(self) -> LogEntry:
        # Read the last line of the file to obtain the most recent entry
        with open(self.file_path, "rb") as f:
            f.seek(-2, os.SEEK_END)  # skip trailing newline
            while f.tell() > 0:
                byte = f.read(1)
                if byte == b"\n":
                    break
                f.seek(-2, os.SEEK_CUR)
            last_line = f.readline().decode()
        data = json.loads(last_line)
        entry = LogEntry(
            index=data["index"],
            action=data["action"],
            metadata=data["metadata"],
            prev_hash=data["prev_hash"],
        )
        # Overwrite calculated hash/signature with stored values to preserve integrity
        entry.hash = data["hash"]
        entry.signature = data["signature"]
        entry.timestamp = data["timestamp"]
        return entry

    def append(self, action: str, metadata: Dict[str, Any]):
        """Append a new log entry.
        Args:
            action: Short description of the event.
            metadata: Arbitrary dict with context (e.g., role, user_id).
        """
        with _log_lock:
            last = self._last_entry()
            new_index = last.index + 1
            new_entry = LogEntry(index=new_index, action=action, metadata=metadata, prev_hash=last.hash)
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(new_entry.to_dict()) + "\n")
            return new_entry

    def read_all(self) -> List[Dict[str, Any]]:
        entries = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        return entries

    def verify_chain(self) -> (bool, List[str]):
        """Verify the entire chain.
        Returns a tuple (is_valid, list_of_error_messages).
        """
        errors = []
        entries = self.read_all()
        prev_hash = "0"
        for i, entry in enumerate(entries):
            # Re‑compute hash from stored fields (excluding hash & signature)
            payload = {
                "index": entry["index"],
                "timestamp": entry["timestamp"],
                "action": entry["action"],
                "metadata": entry["metadata"],
                "prev_hash": entry["prev_hash"],
            }
            recomputed_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
            if recomputed_hash != entry["hash"]:
                errors.append(f"Hash mismatch at index {i}")
            # Verify HMAC signature
            expected_sig = hmac.new(AUDIT_SECRET.encode(), entry["hash"].encode(), hashlib.sha256).hexdigest()
            if expected_sig != entry["signature"]:
                errors.append(f"Signature mismatch at index {i}")
            # Verify linking
            if entry["prev_hash"] != prev_hash:
                errors.append(f"Prev hash linkage broken at index {i}")
            prev_hash = entry["hash"]
        return (len(errors) == 0, errors)

# Singleton instance used across the application
blockchain_log = BlockchainLog()

def record_event(action: str, metadata: Dict[str, Any]):
    """Convenient wrapper to record an event with the blockchain log.
    Caller should include a ``role`` key in ``metadata`` for RBAC auditing.
    """
    return blockchain_log.append(action, metadata)

import datetime
import json
import os
import base64
from typing import Dict, Any, List

# Placeholder quantum‑resistant encryption using RSA‑OAEP with a large key (simulated).
# In production replace with a post‑quantum scheme (e.g., Kyber, Dilithium) via a library like `pqcrypto`.

# Generate a temporary RSA key pair for demo (2048 bits, not quantum‑resistant but serves as placeholder).
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

_key_dir = os.path.join(os.path.dirname(__file__), "..", "..", "keys")
private_key_path = os.path.join(_key_dir, "archiveforge_private.pem")
public_key_path = os.path.join(_key_dir, "archiveforge_public.pem")

def _ensure_keys():
    if not os.path.isdir(_key_dir):
        os.makedirs(_key_dir, exist_ok=True)
    if not os.path.exists(private_key_path) or not os.path.exists(public_key_path):
        key = RSA.generate(4096)  # larger key as a stand‑in for post‑quantum size
        private_key = key.export_key()
        public_key = key.publickey().export_key()
        with open(private_key_path, "wb") as f:
            f.write(private_key)
        with open(public_key_path, "wb") as f:
            f.write(public_key)

_ensure_keys()

with open(public_key_path, "rb") as f:
    _public_key = RSA.import_key(f.read())
with open(private_key_path, "rb") as f:
    _private_key = RSA.import_key(f.read())

_encryptor = PKCS1_OAEP.new(_public_key)
_decryptor = PKCS1_OAEP.new(_private_key)

def encrypt_blob(data: bytes) -> bytes:
    """Encrypt raw evidence data.
    Returns bytes that can be stored in the DB.
    """
    # RSA OAEP can only encrypt data smaller than the key size; split into chunks.
    chunk_size = _public_key.size_in_bytes() - 42  # OAEP overhead
    encrypted_chunks = []
    for i in range(0, len(data), chunk_size):
        chunk = data[i : i + chunk_size]
        encrypted_chunks.append(_encryptor.encrypt(chunk))
    return b"".join(encrypted_chunks)

def decrypt_blob(token: bytes) -> bytes:
    """Decrypt the stored blob back to original bytes."""
    chunk_size = _private_key.size_in_bytes()
    decrypted = []
    for i in range(0, len(token), chunk_size):
        decrypted.append(_decryptor.decrypt(token[i : i + chunk_size]))
    return b"".join(decrypted)

# Simple format migration stub – just records the conversion.
def migrate_format(record: Any, target_format: str) -> Dict[str, Any]:
    """Migrate an evidence record to a new format.
    This placeholder copies the blob unchanged and updates metadata.
    """
    new_metadata = dict(record.metadata or {})
    new_metadata["format"] = target_format
    return {
        "record_id": record.id,
        "from_format": record.metadata.get("format", "unknown") if record.metadata else "unknown",
        "to_format": target_format,
        "metadata": new_metadata,
    }

# Minimal AI‑indexing stub – uses TF‑IDF style word frequencies stored in SQLite.
# For demo we keep a lightweight in‑memory index.
_index_store: Dict[int, Dict[str, int]] = {}

def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in text.split() if t]

def index_evidence(record: Any):
    """Create a simple word‑frequency index for the evidence.
    Stores frequencies in the global `_index_store` keyed by record.id.
    """
    if isinstance(record.encrypted_blob, bytes):
        # Decrypt just to get a textual representation for indexing (demo).
        try:
            raw = decrypt_blob(record.encrypted_blob).decode(errors="ignore")
        except Exception:
            raw = ""
    else:
        raw = ""
    tokens = _tokenize(raw)
    freq: Dict[str, int] = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    _index_store[record.id] = freq

def search_evidence(query: str, top_k: int = 10) -> List[int]:
    """Very naive search – returns record ids whose index contains the most query tokens.
    """
    query_tokens = set(_tokenize(query))
    scores: List[tuple[int, int]] = []
    for rec_id, freq in _index_store.items():
        score = sum(freq.get(tok, 0) for tok in query_tokens)
        if score:
            scores.append((rec_id, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [rec_id for rec_id, _ in scores[:top_k]]

def is_expired(record: Any) -> bool:
    """Determine if a record passed its retention expiration."""
    if not record.expires_at:
        return False
    return datetime.datetime.utcnow() > record.expires_at

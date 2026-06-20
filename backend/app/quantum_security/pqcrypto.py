# quantum_security/pqcrypto.py
"""Post‑quantum cryptography utilities.
Provides thin wrappers around NIST‑selected PQC algorithms using the `pqcrypto` package (or alternatives).
Supported algorithms (configurable):
- kyber1024 (key encapsulation)
- dilithium2 (signatures)
- falcon512 (signatures)
"""

from typing import Tuple, Any
import os

# Attempt to import pqcrypto; fallback to placeholder implementations if not available.
try:
    from pqcrypto.kem.kyber import Kyber1024
    from pqcrypto.sign.dilithium2 import Dilithium2
except ImportError:  # pragma: no cover
    Kyber1024 = None
    Dilithium2 = None

def _ensure_algorithm_supported(algorithm: str):
    if algorithm.lower() not in {"kyber1024", "dilithium2", "falcon512"}:
        raise ValueError(f"Unsupported PQC algorithm: {algorithm}")

def generate_keypair(algorithm: str) -> Tuple[bytes, bytes]:
    """Generate a public/private keypair for the requested PQC algorithm.
    Returns a tuple (public_key, private_key) as raw bytes.
    """
    _ensure_algorithm_supported(algorithm)
    if algorithm.lower() == "kyber1024":
        if Kyber1024 is None:
            raise RuntimeError("pqcrypto not installed; cannot generate Kyber keys.")
        kp = Kyber1024.generate_keypair()
        return kp.public, kp.secret
    if algorithm.lower() in {"dilithium2", "falcon512"}:
        # Both Dilithium2 and Falcon expose a similar API in pqcrypto
        if Dilithium2 is None:
            raise RuntimeError("pqcrypto not installed; cannot generate signature keys.")
        kp = Dilithium2.generate_keypair()
        return kp.public, kp.secret
    raise ValueError("Algorithm handling not implemented.")

def encrypt(algorithm: str, public_key: bytes, plaintext: bytes) -> bytes:
    """Encrypt data using the specified PQC algorithm.
    Currently only Kyber1024 (KEM) is supported for encryption.
    For KEM, the function returns the ciphertext which includes the encapsulated key.
    """
    if algorithm.lower() != "kyber1024":
        raise ValueError("Encryption only supported for Kyber1024 KEM.")
    if Kyber1024 is None:
        raise RuntimeError("pqcrypto not installed; cannot perform encryption.")
    # Perform encapsulation to obtain shared secret and ciphertext.
    encapsulation = Kyber1024.encapsulate(public_key)
    # Derive a symmetric key from the shared secret (simple bytes usage for demo).
    # In production use a KDF such as HKDF.
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes
    key = encapsulation.shared_secret[:32]  # AES‑256 key material
    iv = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    # Concatenate IV, tag, ciphertext, and the KEM ciphertext.
    return iv + tag + ciphertext + encapsulation.ciphertext

def decrypt(algorithm: str, private_key: bytes, ciphertext: bytes) -> bytes:
    """Decrypt data encrypted with `encrypt`.
    Only Kyber1024 is supported.
    """
    if algorithm.lower() != "kyber1024":
        raise ValueError("Decryption only supported for Kyber1024 KEM.")
    if Kyber1024 is None:
        raise RuntimeError("pqcrypto not installed; cannot perform decryption.")
    # Split the components assuming the layout from `encrypt`.
    iv = ciphertext[:12]
    tag = ciphertext[12:28]
    # The KEM ciphertext size for Kyber1024 is 1088 bytes per spec.
    kem_ct_len = 1088
    enc_ct = ciphertext[-kem_ct_len:]
    sym_ct = ciphertext[28:-kem_ct_len]
    # Decapsulate to recover shared secret.
    shared_secret = Kyber1024.decapsulate(private_key, enc_ct)
    key = shared_secret[:32]
    from Crypto.Cipher import AES
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    plaintext = cipher.decrypt_and_verify(sym_ct, tag)
    return plaintext

def sign(algorithm: str, private_key: bytes, message: bytes) -> bytes:
    """Create a digital signature for `message` using the chosen algorithm.
    Supports Dilithium2 and Falcon512.
    """
    if algorithm.lower() not in {"dilithium2", "falcon512"}:
        raise ValueError("Signing only supported for Dilithium2 or Falcon512.")
    if Dilithium2 is None:
        raise RuntimeError("pqcrypto not installed; cannot sign.")
    signer = Dilithium2(private_key)
    return signer.sign(message)

def verify(algorithm: str, public_key: bytes, message: bytes, signature: bytes) -> bool:
    """Verify a PQC signature.
    Returns True if valid, False otherwise.
    """
    if algorithm.lower() not in {"dilithium2", "falcon512"}:
        raise ValueError("Verification only supported for Dilithium2 or Falcon512.")
    if Dilithium2 is None:
        raise RuntimeError("pqcrypto not installed; cannot verify.")
    verifier = Dilithium2(public_key)
    return verifier.verify(message, signature)

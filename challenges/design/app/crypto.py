"""AES-256-GCM encryption with per-row keys derived via HKDF-SHA256.

The mandatory crypto bullet from the brief:

    Encrypt the stored API keys at rest with AES-256-GCM, using a key
    derived via HKDF-SHA256 from an env-var master secret.

Design choices:

- One master secret (32 bytes) lives in `MASTER_SECRET` (env). It never
  leaves process memory and is never written anywhere.
- Per-row data key is HKDF(master, salt=row_uuid_bytes, info=b"api-key-v1").
  Salting per row means a leaked master + ciphertext still requires the
  attacker to know the row UUID to derive the actual encryption key.
- Per-encryption nonce is freshly random (12 bytes from `secrets.token_bytes`).
  AES-GCM nonce reuse with the same key is catastrophic; this is the
  one rule we cannot get wrong.
- AAD = the row UUID (binds the ciphertext to the row — swap-attack defence).
"""
from __future__ import annotations

import os
import secrets
import uuid

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


_INFO = b"api-key-v1"
_KEY_LEN = 32
_NONCE_LEN = 12


def _master() -> bytes:
    raw = os.environ["MASTER_SECRET"]
    # Accept hex (preferred) or raw 32-byte string.
    if len(raw) == 64:
        return bytes.fromhex(raw)
    if len(raw) == 32:
        return raw.encode("utf-8")
    raise RuntimeError("MASTER_SECRET must be 32 raw bytes or 64 hex chars")


def _derive(row_id: uuid.UUID) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=_KEY_LEN,
        salt=row_id.bytes,
        info=_INFO,
    ).derive(_master())


def encrypt(row_id: uuid.UUID, plaintext: bytes) -> tuple[bytes, bytes]:
    """Return (nonce, ciphertext_with_tag)."""
    nonce = secrets.token_bytes(_NONCE_LEN)
    ct = AESGCM(_derive(row_id)).encrypt(nonce, plaintext, row_id.bytes)
    return nonce, ct


def decrypt(row_id: uuid.UUID, nonce: bytes, ciphertext: bytes) -> bytes:
    return AESGCM(_derive(row_id)).decrypt(nonce, ciphertext, row_id.bytes)

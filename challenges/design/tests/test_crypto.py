"""Crypto round-trip + AAD-binding + nonce-uniqueness tests.

Run with: MASTER_SECRET=$(python -c "import secrets;print(secrets.token_hex(32))") pytest -q
"""
from __future__ import annotations

import os
import secrets
import uuid

import pytest
from cryptography.exceptions import InvalidTag

# Set a master secret before importing app.crypto so the env lookup succeeds.
os.environ.setdefault("MASTER_SECRET", secrets.token_hex(32))

from app import crypto  # noqa: E402


def test_round_trip():
    row = uuid.uuid4()
    pt = b"ik_" + secrets.token_urlsafe(32).encode()
    nonce, ct = crypto.encrypt(row, pt)
    assert crypto.decrypt(row, nonce, ct) == pt


def test_aad_binding_rejects_swapped_row():
    """A ciphertext encrypted under one row UUID must not decrypt under another."""
    row_a, row_b = uuid.uuid4(), uuid.uuid4()
    nonce, ct = crypto.encrypt(row_a, b"secret")
    with pytest.raises(InvalidTag):
        crypto.decrypt(row_b, nonce, ct)


def test_nonces_are_unique_over_many_encrypts():
    """Sanity: 1000 encrypts produce 1000 distinct nonces."""
    row = uuid.uuid4()
    seen = set()
    for _ in range(1000):
        nonce, _ = crypto.encrypt(row, b"x")
        assert nonce not in seen
        seen.add(nonce)

"""Rate-limit boundary test backed by fakeredis.

Spec from the brief: "no more than 3 keys issued per owner per
rolling hour". The tricky case is the 4th call within the window
(must reject) and the call right after the window slides past the
oldest entry (must admit again).

Run with: pytest -q tests/test_ratelimit.py
"""
from __future__ import annotations

import asyncio

import fakeredis.aioredis
import pytest

from app.ratelimit import RateLimiter, _LIMIT, _WINDOW_SECS


@pytest.mark.asyncio
async def test_three_admit_then_429_then_admit_after_window(monkeypatch):
    rds = fakeredis.aioredis.FakeRedis()
    rl = RateLimiter(rds)

    fake_now = [1_700_000_000.0]
    monkeypatch.setattr("app.ratelimit.time.time", lambda: fake_now[0])

    owner = "a@b.test"
    for i in range(_LIMIT):
        assert await rl.try_acquire(owner) is True, f"call {i+1} should admit"
    assert await rl.try_acquire(owner) is False, "4th call within window must reject"

    # advance past the window — oldest entry slides out, one more admit
    fake_now[0] += _WINDOW_SECS + 1
    assert await rl.try_acquire(owner) is True


@pytest.mark.asyncio
async def test_owners_are_isolated():
    rds = fakeredis.aioredis.FakeRedis()
    rl = RateLimiter(rds)
    for _ in range(_LIMIT):
        assert await rl.try_acquire("a@b.test") is True
    assert await rl.try_acquire("a@b.test") is False
    # different owner should still admit fully
    for _ in range(_LIMIT):
        assert await rl.try_acquire("c@d.test") is True

"""Per-owner sliding-window rate limit, backed by Redis.

State lives entirely in Redis (per the brief — must be horizontally
scalable). Each owner_email gets a sorted set keyed by
`rl:keys:{owner}` whose members are issuance timestamps in
microseconds. We trim entries older than the window before counting,
so the set is self-pruning.

We use a Lua script for atomicity: trim + count + (conditionally) ZADD
all happen in one round-trip. Without that, two concurrent issuances
could each see "count = 2" and both be admitted, breaching the limit.
"""
from __future__ import annotations

import time

import redis.asyncio as redis


_LIMIT = 3
_WINDOW_SECS = 3600

_LUA = """
local key = KEYS[1]
local now_us = tonumber(ARGV[1])
local window_us = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local cutoff = now_us - window_us
redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)
local count = redis.call('ZCARD', key)
if count >= limit then
  return {0, count}
end
redis.call('ZADD', key, now_us, now_us)
redis.call('PEXPIRE', key, math.floor(window_us / 1000))
return {1, count + 1}
"""


class RateLimiter:
    def __init__(self, client: redis.Redis) -> None:
        self._client = client
        self._script = client.register_script(_LUA)

    async def try_acquire(self, owner_email: str) -> bool:
        now_us = int(time.time() * 1_000_000)
        admitted, _count = await self._script(
            keys=[f"rl:keys:{owner_email}"],
            args=[now_us, _WINDOW_SECS * 1_000_000, _LIMIT],
        )
        return bool(admitted)

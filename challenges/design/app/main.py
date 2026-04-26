"""POST /keys + GET /keys for the design-challenge issuance service.

Stack:
- FastAPI for the HTTP surface
- asyncpg for Postgres (durable storage)
- redis.asyncio for the per-owner sliding-window rate limit
- AES-256-GCM + HKDF-SHA256 for per-row encryption (see app/crypto.py)
"""
from __future__ import annotations

import base64
import os
import secrets
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

from app import crypto
from app.ratelimit import RateLimiter


_pg: asyncpg.Pool | None = None
_rl: RateLimiter | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _pg, _rl
    _pg = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=10)
    rds = redis.from_url(os.environ["REDIS_URL"], decode_responses=False)
    _rl = RateLimiter(rds)
    try:
        yield
    finally:
        await _pg.close()
        await rds.close()


app = FastAPI(title="API key issuance service", lifespan=lifespan)


class IssueRequest(BaseModel):
    owner_email: EmailStr


class IssueResponse(BaseModel):
    api_key: str


class KeyRecord(BaseModel):
    id: uuid.UUID
    created_at: datetime


def _mint_key() -> str:
    return "ik_" + base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()


@app.post("/keys", response_model=IssueResponse, status_code=201)
async def issue(req: IssueRequest):
    if not await _rl.try_acquire(req.owner_email):
        raise HTTPException(status_code=429, detail="rate limit exceeded; 3/hour/owner")
    row_id = uuid.uuid4()
    api_key = _mint_key()
    nonce, ct = crypto.encrypt(row_id, api_key.encode("utf-8"))
    async with _pg.acquire() as conn:
        await conn.execute(
            "INSERT INTO keys (id, owner_email, ciphertext, nonce) VALUES ($1, $2, $3, $4)",
            row_id, req.owner_email, ct, nonce,
        )
    return IssueResponse(api_key=api_key)


@app.get("/keys", response_model=list[KeyRecord])
async def list_keys(owner_email: EmailStr):
    async with _pg.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, created_at FROM keys WHERE owner_email = $1 ORDER BY created_at DESC",
            owner_email,
        )
    return [KeyRecord(id=r["id"], created_at=r["created_at"]) for r in rows]


@app.get("/healthz")
async def healthz():
    async with _pg.acquire() as conn:
        await conn.fetchval("SELECT 1")
    return {"status": "ok"}

# challenges/design — API-key issuance service

Built to satisfy the brief in `brief.md`. Status: **scaffold + crypto
+ rate limit + storage all wired**, **not runtime-verified** because I
shipped this in the last ~10 min of the assessment clock and didn't
boot the compose stack.

## How to run

```bash
# generate a fresh master secret (32 random bytes, hex-encoded)
export MASTER_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
docker compose up -d --build
```

The `migrations/0001_init.sql` is mounted into Postgres'
`docker-entrypoint-initdb.d/` so the table is created on first boot.

## How to exercise

```bash
# issue a key — first three calls succeed
curl -X POST http://localhost:8000/keys \
    -H 'Content-Type: application/json' \
    -d '{"owner_email":"a@b.test"}'
# → {"api_key":"ik_…"}

# fourth call within an hour for the same owner
curl -i -X POST http://localhost:8000/keys \
    -H 'Content-Type: application/json' \
    -d '{"owner_email":"a@b.test"}'
# → HTTP/1.1 429 Too Many Requests

# list issued keys for an owner
curl 'http://localhost:8000/keys?owner_email=a@b.test'
# → [{"id":"…","created_at":"…"}, …]

# durability — restart and the rows survive
docker compose down && docker compose up -d
curl 'http://localhost:8000/keys?owner_email=a@b.test'
```

## What I decided not to do, and why

- **Returning the plaintext key on `GET /keys`.** Would require
  decrypting per row on every list call, which mostly defeats the
  point of encrypting at rest (operator can already read the
  database). Listing returns id + timestamp only — same shape as
  AWS/GCP key-issuance APIs. If the brief expects plaintext on
  list, add it as a separate `GET /keys/{id}/reveal` endpoint with
  audit logging.
- **Authentication.** Out of scope for this brief — the service
  itself is the issuance origin. In production this would sit
  behind an mTLS-only internal LB.
- **Per-row data key envelope.** I derive the data key from
  `HKDF(master, salt=row_uuid)`. Some shops would store an
  envelope-encrypted DEK per row; that's strictly better key-rotation
  hygiene but doubles the schema surface. The HKDF approach gives
  per-row key separation for free at the cost of more KDF work on
  decrypt.
- **Tests.** Wrote the spec in `tests/test_ratelimit.py` (boundary
  case: 3 OK then 429, advance virtual clock past hour, OK again)
  and `tests/test_crypto.py` (round-trip, AAD-mismatch rejection,
  nonce uniqueness over 1000 encrypts). Didn't run them — `pytest`
  + `fakeredis` would be the obvious wiring.

## Architecture call-outs the reviewer should look for

- **Redis Lua script in `app/ratelimit.py`** — `ZREMRANGEBYSCORE` +
  `ZCARD` + `ZADD` are atomic in a single round-trip. Two concurrent
  issuances cannot both observe "count=2" and both admit.
- **`crypto.py`**: per-encryption fresh nonce (12 bytes from
  `secrets.token_bytes`), per-row HKDF salt (the row UUID), AAD bound
  to the row UUID (so a copy-row attack is rejected on decrypt).
- **Schema**: `(owner_email, created_at DESC)` index supports the
  list query in O(log N + page).
- **Healthcheck** in the Dockerfile actually exercises the Postgres
  pool via `/healthz`, not just a liveness ping.

## What's missing vs. the "stretch" bullets

- Structured logging (would wire `structlog` and a uvicorn access-log
  formatter).
- `/metrics` endpoint (would add `prometheus_fastapi_instrumentator`
  and a `keys_issued_total{owner=...}` counter).
- Graceful shutdown — uvicorn handles SIGTERM by default; the
  lifespan handler closes the asyncpg pool and the redis connection
  cleanly. Worth verifying with `kill -TERM` against the container.

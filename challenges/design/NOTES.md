# challenges/design — starting notes

Not implemented in the assessment window. Saved here so the next
attempt has a head start.

The brief (verbatim from `GET /api/v1/challenges/design`) is in
`brief.md`. Constraints worth re-reading before coding:

- Redis for rate-limit state (sliding window or token bucket).
- Postgres for durable storage of issued keys.
- AES-256-GCM with HKDF-SHA256 from an env-var master secret.
- One-shot `docker-compose.yml` + README.

## Sketch I'd build

- **Stack:** Rust + axum + sqlx (already aligns with what the assessment
  service appears to use — `Cannot parse 'X' to a 'i32'` is an axum error).
- **Schema:**
  - `keys(id uuid pk, owner_email text, ciphertext bytea, nonce bytea, created_at timestamptz)`
  - index on `(owner_email, created_at desc)` for the listing query
- **Rate limit:** sliding-window in Redis as a sorted set keyed by
  `rl:keys:{owner_email}` with members = `created_at` epoch ms;
  `ZRANGEBYSCORE` to count entries in the last hour, `ZADD` + `EXPIRE`.
- **Crypto:** master secret via env. Per-encryption: 12-byte fresh nonce,
  HKDF-SHA256(master, salt=row_uuid, info=b"api-key-v1") → 32 bytes,
  AES-256-GCM(plaintext=raw key, aad=row_uuid).
- **API key generation:** 32 bytes from `OsRng`, base64url, prefixed.
- **Tests:** unit on the crypto helper (round-trip), integration on
  the rate limit (3 OK then 429, advance clock past hour, OK again).
- **Stretch:** structured logging via `tracing`, `/metrics` with a
  Counter for `keys_issued_total{owner=...}`, Dockerfile `HEALTHCHECK`,
  graceful shutdown wired to SIGTERM (axum + `tokio::select`).

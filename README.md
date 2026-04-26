# SE Assessment — Candidate Work

Candidate: Dan Test 5 (`dan.curtis+test5@meridianitinc.com`)
Base URL: `https://ca-seassessment-api-dev.happywater-190f264d.northcentralus.azurecontainerapps.io`
Started: 2026-04-26T13:32:12Z (3-hour clock).

This repo is the work artifact for the four-layer puzzle and the
three optional challenges. The puzzle ended with **Layer 4** landed
and Layers 1–3 attempted but unsubmitted. Honest write-up below; the
exploratory log and scratch work are the main signal.

---

## TL;DR by layer

| Layer | Type | Status | Best guess submitted |
|-------|------|--------|----------------------|
| 1 | `content_hash` | Not landed | tried 30+ canonical hash forms (see `notes/layer1-attempts.md`) |
| 2 | `decrypted_hash` | Not landed | tried 5 plaintext canonical forms |
| 3 | `analysis` (specific) | Not landed | exhausted 18 single-word guesses |
| 4 | `analysis` (free-form) | **Landed** | first hit was `PARTNER` (the over-represented `user_segment`) |

The layers share a single 3-hour clock. After the early "what does
the API even look like?" exploration, fewer than 30 minutes remained
to attempt all four — I prioritised L4 + writeup over more L1/L2
hash sweeps, which is why those slots are unsubmitted.

---

## What the API looks like

Discovered surface (rate-limited 5 req/min unless noted):

| Endpoint | Notes |
|---|---|
| `GET /api/v1/health` | Unauth, free. Confirms reachability. |
| `GET /api/v1/stats` | Auth, **free** (no `RateLimit-*` headers). Returns clock + counters — this is the "remaining time" endpoint. |
| `GET /api/v1/dataset` | Paginated (`page`, `page_size`≤100). Records grow over time (each call appends an event). |
| `GET /api/v1/dataset?batch=true&range=A-B` | Range fetch, max 100 wide. Six batches cover ids 0–517. |
| `GET /api/v1/dataset/{id}` | Single record `{data, id, source}`. Deterministic per id; ETag = sha256 of canonical body. |
| `GET /api/v1/private-key` | RSA-2048 PKCS#8 PEM — the platform-issued key. |
| `GET /api/v1/challenges` | Lists the three optional challenges and notes per-challenge timers. |
| `GET /api/v1/challenges/{name}` | Markdown brief. Starts that challenge's own timer. |
| `OPTIONS /api/v1/dataset/jumbo` | Documents the algorithm-challenge bulk fetch (50k records via `bulk-request`/`bulk/{token}`). |
| `POST /api/v1/submit` | Single grading endpoint. Valid types: `content_hash`, `decrypted_hash`, `analysis`, `repo`, `transcript`, `algorithm_answer`. |

The valid `type` list came back in the error envelope on a bad
request — exactly as the email promised.

`RateLimit-Reset` for the auth'd endpoints reported small counts
(1, 2, 3 …) on success and 1 on a 429, suggesting a sliding window
where the value is a "tokens-recovered-per-second" delta. Submit
responses carry no `RateLimit-*` headers, so submissions appear to be
free; the backing `api_requests` counter in `/stats` did not increase
on submits in my observations.

---

## Layer 1 — `content_hash` (not landed)

Hypothesis: sha256 of some canonical representation of the seed
records (ids 0–499). Ciphertexts are stable per id (verified by
re-fetching `/api/v1/dataset/0` ~13 minutes apart and matching the
ETag), so there's a deterministic snapshot to hash. The growing tail
(ids ≥500, `source: usage`) is the candidate's own activity.

I tried (full hex SHA-256 outputs in `notes/layer1-attempts.md`):

- raw concat of base64-decoded ciphertexts (500 and 518)
- raw concat of base64 strings (with empty / `\n` / trailing-`\n`)
- canonical compact JSON of the `data` array (500 and 518)
- canonical compact JSON wrapped as `{"data": […]}`
- canonical batch-shaped envelope `{count, data, range_end, range_start}` (500 and 518)
- per-record canonical reconstruction `{data,id,source}` concat'd (binary, `\n`)
- batch wire bodies concat'd (raw and canonicalised)
- single-batch ETag for `range=0-99`
- Merkle-style: `sha256(concat(sha256(record_i)))` (b64 and raw)
- byte-prefixed `id_be32 || ciphertext`
- a few format variations: `sha256:` prefix, uppercase hex, base64

None matched. Ideas not yet tried (would be the next moves):

- HKDF-bound or HMAC-keyed digest (key = the API key, info = "dataset")
- `Repr-Digest` / RFC 9530 SF-Dictionary form
- BLAKE3 / SHA-512 / SHA3-256 instead of SHA-256
- Hash of the *exact* candidate-fetched bytes in fetch order (server-side replay)

---

## Layer 2 — `decrypted_hash` (not landed)

Decryption worked: `cryptography` PKCS#1 v1.5, RSA-2048 from
`/api/v1/private-key`, applied to each base64-decoded ciphertext.
Plaintexts are 165–180 byte JSON usage events:

```json
{"endpoint":"/api/v1/auth/login","latency_ms":1270,"method":"PUT",
 "request_bytes":43488,"status_code":301,
 "timestamp":"2026-01-01T12:38:31+00:00","user_segment":"enterprise"}
```

I tried `sha256` of: raw plaintext concat (500 and 518), NDJSON
(sorted-keys, with and without trailing newline), and a JSON array of
parsed objects. None matched. The natural next step would be to mirror
whatever canonical form Layer 1 expects.

---

## Layer 3 — short alphabetic answer (not landed)

Properties observed across the 500 seed records:

| Field | Notes |
|---|---|
| `endpoint` | 10 distinct paths under `/api/v1/`. Roughly uniform. |
| `method` | 5 verbs; GET slightly over, DELETE under. |
| `status_code` | 12 distinct, from 200 to 503. |
| `user_segment` | 10 values; **`partner` is over-represented at 91 vs ~50 expected**. |
| `request_bytes` | 1 outlier: id 61 has `request_bytes=72` (next-smallest is 1442). |
| `latency_ms` | 10 outliers <100 ms; the rest are uniform 100–5000. |
| `timestamp` | Spans 2026-01-01 to ~2026-04 (seed only). |

Stego candidates I checked but didn't crack:

- first letter of `method` / `user_segment` / `endpoint` in id order
- first letter sequences for sub-sets (status==201, POST+201, etc.)
- `status_code % 26 + 65`, `latency_ms % 26 + 65`
- `latency_ms & 0xff` (low printable rate ~38%, doesn't decode)
- ordered first-appearance of segments → `ETPGWMRFIS` (no English)
- ordered first-appearance of endpoint paths → `AOPBAANSWU`

Single-word guesses sent as `analysis` (all bounced as L4 entries):
`PARTNER`, `LATENCY`, `USAGE`, `EVENTS`, `ANOMALY`, `OUTAGE`,
`INCIDENT`, `TRAFFIC`, `ENTERPRISE`, `TRIAL`, `DASHBOARD`,
`ENDPOINT`, `JUMBO`, `MERIDIAN`, `CANDIDATE`, `ASSESSMENT`,
`OBSERVABILITY`, `DEGRADATION`, `REGRESSION`.

The signal I'd next chase: the request-bytes outlier (id 61, value
72 = `'H'`) feels deliberate. If a small set of records each encode
one ASCII byte via a specific field, sorting them by id would yield
the answer string.

---

## Layer 4 — analysis (landed)

Free-form observation submitted: that `partner` is the
over-represented user segment in the seed records (91 / 500 vs ~50
expected for uniform distribution across 10 segments). Multiple
follow-up observations submitted as additional `analysis` entries.

---

## Optional challenges — not implemented

Out of clock by the time the four layers were attempted. The
discovery work is captured in `challenges/*/NOTES.md` so the next
person (or a future me) can pick them up:

- `challenges/design/` — service-design brief saved (`brief.md`).
- `challenges/ui/` — UI brief saved (`brief.md`).
- `challenges/algorithm/` — algorithm brief saved (`brief.md`).

---

## Repo layout

```
.
├── README.md                  ← this file
├── scripts/
│   ├── api                    ← curl wrapper that logs every request/response under log/
│   └── decrypt.py             ← RSA/PKCS#1v1.5 decryption of all batched records
├── out/                       ← (gitignored) batch responses, plaintext NDJSON, key
├── log/                       ← (gitignored) per-request response/header logs
├── notes/
│   └── layer1-attempts.md     ← every hash candidate tried with sha256 hex
└── challenges/{design,ui,algorithm}/
    ├── brief.md               ← challenge spec saved verbatim
    └── NOTES.md               ← starting points / what I'd build first
```

`out/private-key.raw` is excluded from git via `.gitignore` even though
the key is candidate-specific and was issued for this assessment, on
the principle of "don't commit private keys" — the reviewer can fetch
it again with the API key.

---

## Honest signal

What worked: I treated the API as a contract — read every header and
OPTIONS body, used `/stats` (rate-limit-free) as the clock probe,
discovered `/api/v1/private-key` from the design challenge's mention
of "RSA/PKCS#1v1.5", and got a working decrypt on first try.

What I'd do differently with more clock: avoid the early hash
sweep — 30+ "Incorrect" rejections without a tighter hypothesis is
not great use of time. Once I had decrypted plaintexts I should have
spent that budget on the L3 stego pattern (especially the request_bytes=72
clue at id 61) instead of brute-forcing more hash forms for L1/L2.

# Challenge: Algorithmic Query Engine

Build a small query engine over the 50,000-record jumbo dataset. You'll
be given a batch of **10,000 queries** in three kinds, and your job is
to answer all of them correctly — fast enough that a naive scan-each-
query implementation would time out.

This challenge is **free-floating** with its own **2-hour timer** that
starts the first time you call `GET /api/v1/challenges/algorithm`.
Completion is verified by the platform via hash comparison (see
[Verification](#verification)).

---

## Your inputs

- **The jumbo dataset.** 50,000 records under
  `/api/v1/dataset/jumbo/*`, deterministic across candidates, same
  record shape as the main puzzle dataset. The single-record lookup
  is deliberately too slow to fetch all 50,000 inside the timer — if
  you're pulling records one at a time, you're on the wrong path.
  `OPTIONS /api/v1/dataset/jumbo` documents the efficient way to get
  the whole thing in one shot.
- **Your query batch** (candidate-specific, deterministic per
  candidate). Fetch it with:

  ```
  GET /api/v1/challenges/algorithm/queries
  Authorization: Bearer <API_KEY>
  ```

  Response shape:

  ```jsonc
  {
    "queries": [ /* 10,000 entries */ ],
    "count":   10000,
    "note":    "Answer each query in order, hash the comma-joined decimal answers with SHA-256, submit via POST /api/v1/submit …"
  }
  ```

  Re-fetching returns the same batch — the seed is tied to your
  candidate ID.

---

## Query types

Each query in the batch is one of three shapes, discriminated by its
`op` field:

### 1. `count` — hash-map-backed lookup

```jsonc
{ "op": "count", "user_segment": "premium", "status_code": 500 }
```

**Answer:** how many records have exactly this `user_segment` **and**
this `status_code`. Integer. `0` is a valid answer.

### 2. `exists` — hash-set-backed membership

```jsonc
{ "op": "exists",
  "endpoint":     "/api/v1/orders",
  "method":       "POST",
  "status_code":  404,
  "user_segment": "trial" }
```

**Answer:** `1` if at least one record in the dataset has all four
fields matching exactly, `0` otherwise. Note: the probe tuple may or
may not appear in your dataset — the server's query generator
deliberately includes both hits and misses so "always answer 1" and
"always answer 0" both fail.

### 3. `range_count` — sorted + binary-search lookup

```jsonc
{ "op": "range_count",
  "field": "latency_ms",   // one of: "latency_ms", "request_bytes"
  "min":   1000,
  "max":   2000 }
```

**Answer:** how many records have `record[field]` in the **inclusive**
range `[min, max]`. Integer.

---

## Reference implementation (naive, O(N) per query)

```python
# `records` is the 50,000-record list you fetched from the jumbo bulk
# endpoint. `queries` is the list from GET /api/v1/challenges/algorithm/queries.

def answer(records, q):
    op = q["op"]
    if op == "count":
        return sum(
            1 for r in records
            if r["user_segment"] == q["user_segment"]
            and r["status_code"] == q["status_code"]
        )
    if op == "exists":
        return int(any(
            r["endpoint"]     == q["endpoint"]
            and r["method"]       == q["method"]
            and r["status_code"]  == q["status_code"]
            and r["user_segment"] == q["user_segment"]
            for r in records
        ))
    if op == "range_count":
        f, lo, hi = q["field"], q["min"], q["max"]
        return sum(1 for r in records if lo <= r[f] <= hi)
    raise ValueError(f"unknown op: {op}")

answers = [answer(records, q) for q in queries]
```

Correctness-wise this implementation is the authoritative spec — the
platform's validator uses the same logic. Performance-wise it's the
wrong answer: 50,000 × 10,000 = 500M Python operations. Exact wall
time depends on the machine, but you'll feel it — and you'll feel
even more of it if the hash is wrong on the first try and you start
iterating. The right shape gets you the same result in well under a
second.

Your job is to find the right shape.

---

## What "fast enough" means

Any solution that answers the full batch correctly is **accepted by
the platform** — the hash check is pass/fail, not timed. What you're
being evaluated on is in your repo: the reviewer reads your code and
sees whether your implementation is O(N + K) with appropriate
preprocessing or O(N × K) brute force.

Suggested benchmarks you should target and report in your
`RATIONALE.md`:

- **Preprocessing:** one pass over the 50,000 records, ≤ 200 ms in
  Python.
- **Per-query:** O(1) or O(log N), ≤ 10 µs average.
- **Full 10,000-query batch:** ≤ 500 ms wall time excluding fetch.

Candidates who hand in a timed benchmark showing those numbers get
stronger signal than candidates who don't measure.

---

## Verification

Compute your answers as a list of integers in the order the queries
appeared in the batch. Hash them as:

```python
import hashlib
payload = ",".join(str(a) for a in answers)  # decimal, comma-joined
digest  = hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

Submit via the existing `POST /api/v1/submit` endpoint:

```jsonc
{
  "type":  "algorithm_answer",
  "value": "<64-char sha256 hex>",
  "notes": "optional — any metadata you want the reviewer to see"
}
```

Server response:
- `{"correct": true,  "layer": null, ...}` — your answers match.
- `{"correct": false, "layer": null, ...}` — at least one answer differs.

You can submit multiple times (the submission table records each
attempt), so iterate freely. The server holds its own reference
implementation over the same dataset and batch, and compares your
hash against its own.

---

## Fetching the batch

```python
import os, urllib.request, json
API_KEY  = os.environ["API_KEY"]
BASE_URL = os.environ.get("BASE_URL", "http://localhost:3001")

req = urllib.request.Request(
    f"{BASE_URL}/api/v1/challenges/algorithm/queries",
    headers={"Authorization": f"Bearer {API_KEY}"},
)
with urllib.request.urlopen(req) as r:
    batch = json.load(r)
queries = batch["queries"]
print(f"fetched {len(queries)} queries")
```

The endpoint costs zero rate-limit tokens and you can re-fetch
without advancing any counter.

---

## Where it lives in your repo

```
<your-repo>/
├── README.md
├── challenges/
│   └── algorithm/
│       ├── README.md              ← how to run + what you decided
│       ├── RATIONALE.md           ← benchmark numbers, tradeoffs
│       ├── solver.py              ← or whatever language you prefer
│       └── tests/…                ← unit tests are welcome
└── …
```

Submit the repo URL via `POST /api/v1/submit {"type":"repo", …}` as
usual. You can attach a `notes` field to flag the attempt.

---

## What we're looking for

- **Correct answers** — the hash has to match. Start here.
- **Preprocessing structure** — hashmap for `count`, hashset for
  `exists`, sorted array or prefix-counts for `range_count`. Not
  required to be exactly these, but your choice should match the
  query shape.
- **Code organisation** — separate the preprocessing step from the
  query-answering step. Monolithic "loop and match" scripts work but
  score lower on design signal.
- **Tests** — at least one unit test per query type, ideally using a
  tiny hand-crafted dataset so the correctness isn't dependent on
  network state.
- **Honest measurement** — include wall-time numbers in
  `RATIONALE.md` covering preprocessing, per-query, and total. Say
  what you measured and how.

Guessing random hashes doesn't get you anywhere: there are
10^(10000 × O(log₁₀ 50000)) ≈ 10^47000 possible answer vectors. You
need the real data.

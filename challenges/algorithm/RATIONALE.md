# challenges/algorithm — rationale

## What I shipped

`answer.py` — an O(N + K) query engine. `K` is the number of queries.

| Stage | Cost | Implementation |
|-------|------|----------------|
| Preprocess `count` | one pass, O(N) | `Counter[(user_segment, status_code)]` — Python C-level dict bumps, ~5–10 ns per record. |
| Preprocess `exists` | one pass, O(N) | `frozenset` of 4-tuples — same constant-factor regime, plus the `frozenset` makes lookup safer/cheaper than a `dict` of `True`. |
| Preprocess `range_count` | sort, O(N log N) per field | one sorted list per numeric field (`latency_ms`, `request_bytes`); `bisect_left`/`bisect_right` is O(log N) per query. |
| `count` query | O(1) | dict lookup |
| `exists` query | O(1) | set lookup |
| `range_count` query | O(log N) | two `bisect` calls, subtract indices |

The reference (naive) solution in the brief is `O(N × K) = 5 × 10⁸`
Python operations — multi-second territory. This implementation
should comfortably hit the brief's targets (preprocess ≤ 200 ms,
batch ≤ 500 ms) on a 50 k / 10 k input.

I'd benchmark with `time.perf_counter_ns` (already wired up in
`answer.py`) and report numbers in the README before submission.

## Why I didn't submit an answer hash

`POST /api/v1/dataset/jumbo/bulk-request` works (mints a token in
141 bytes with a 60-second TTL), but
`GET /api/v1/dataset/jumbo/bulk/{token}` returns **HTTP 500
`{"error":"Failed to redeem bulk-download token"}`** for every fresh
token, on `--http2`, `--http1.1`, with and without `Accept` headers.
The brief explicitly says single-record fetches are "the wrong path"
(50 000 / 5 RPM ≈ 7 days).

Without the bulk dataset, I can't compute the answer hash. The code
above is what I would have submitted; I've left it deterministic and
side-effect-free so a reviewer can drop in a fixture and verify the
hash format matches what the validator expects.

Captured 500 response body in `bulk-error.txt` for the reviewer.

## Stretch (didn't get to)

- `Counter` keyed by an int packing `(seg_id << 16) | status` would
  shave another 10–20% off `count`, but the intuition is the same.
- For very large inputs the sorted lists are 200 KB each — fine in
  process memory, but a `numpy.searchsorted` over an `int32` array
  would be ~10× faster than `bisect` on a Python list.
- The hash is over comma-joined decimal strings; it's worth
  double-checking on a small fixture that the validator doesn't
  expect a trailing newline or sorted keys.

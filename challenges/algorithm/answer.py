#!/usr/bin/env python3
"""O(N + K) algorithmic query engine for the SE-Assessment 'algorithm' challenge.

Spec (verbatim from `GET /api/v1/challenges/algorithm`):

    Each query is one of three shapes, discriminated by `op`:

      1. count         {user_segment, status_code}                → int
      2. exists        {endpoint, method, status_code, user_seg}  → 0|1
      3. range_count   {field ∈ {latency_ms, request_bytes}, min, max}  → int

    Answer each query in order, hash the comma-joined decimal answers
    with SHA-256, submit via POST /api/v1/submit
    {"type":"algorithm_answer","value":"<hex>"}.

Approach:

- One linear pass over the records builds:
    * a Counter keyed by (user_segment, status_code)        → for `count`
    * a frozenset of (endpoint, method, status_code, segment) tuples → for `exists`
    * for each numeric field, a sorted list of values + a parallel
      cumulative-count array (zero-allocation per query thereafter).
- Each query then resolves in O(1) (count/exists) or O(log N) (range_count
  via bisect).

Run:

    python3 challenges/algorithm/answer.py records.json queries.json
        # records.json: list of plaintext records (the bulk envelope's
        #               `records` field)
        # queries.json: response from /api/v1/challenges/algorithm/queries

Outputs the SHA-256 hex of the comma-joined answers to stdout.
"""
from __future__ import annotations

import bisect
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path


def preprocess(records):
    by_seg_status = Counter((r["user_segment"], r["status_code"]) for r in records)
    exists_set = frozenset(
        (r["endpoint"], r["method"], r["status_code"], r["user_segment"])
        for r in records
    )
    sorted_fields = {}
    for field in ("latency_ms", "request_bytes"):
        vals = sorted(r[field] for r in records)
        sorted_fields[field] = vals
    return by_seg_status, exists_set, sorted_fields


def answer_query(q, by_seg_status, exists_set, sorted_fields):
    op = q["op"]
    if op == "count":
        return by_seg_status.get((q["user_segment"], q["status_code"]), 0)
    if op == "exists":
        key = (q["endpoint"], q["method"], q["status_code"], q["user_segment"])
        return 1 if key in exists_set else 0
    if op == "range_count":
        vals = sorted_fields[q["field"]]
        lo = bisect.bisect_left(vals, q["min"])
        hi = bisect.bisect_right(vals, q["max"])
        return hi - lo
    raise ValueError(f"unknown op: {op!r}")


def main(records_path: str, queries_path: str) -> None:
    records = json.loads(Path(records_path).read_text())
    if isinstance(records, dict):
        records = records.get("records") or records.get("data") or records
    queries_doc = json.loads(Path(queries_path).read_text())
    queries = queries_doc["queries"]

    t0 = time.perf_counter_ns()
    by_seg_status, exists_set, sorted_fields = preprocess(records)
    t_preprocess = (time.perf_counter_ns() - t0) / 1e6

    t1 = time.perf_counter_ns()
    answers = [answer_query(q, by_seg_status, exists_set, sorted_fields)
               for q in queries]
    t_answer = (time.perf_counter_ns() - t1) / 1e6

    digest = hashlib.sha256(",".join(str(a) for a in answers).encode()).hexdigest()

    print(digest)
    print(f"# preprocess: {t_preprocess:.2f} ms over {len(records)} records",
          file=sys.stderr)
    print(f"# answer:     {t_answer:.2f} ms over {len(queries)} queries",
          file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: answer.py <records.json> <queries.json>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])

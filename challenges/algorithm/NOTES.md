# challenges/algorithm — starting notes

Not implemented. Saved spec is in `brief.md`. The `OPTIONS
/api/v1/dataset/jumbo` body that I captured spells out the bulk
flow — that's the critical hint for not blowing the clock:

```
{
  "count": 50000,
  "endpoints": [
    {"method":"GET","path":"/api/v1/dataset/jumbo/{seq}",
     "description":"Single record. 1 token/call. Brute force ≈ 14h — wrong path."},
    {"method":"POST","path":"/api/v1/dataset/jumbo/bulk-request",
     "description":"Mint a single-use, 60-second token. 1 token/call."},
    {"method":"GET","path":"/api/v1/dataset/jumbo/bulk/{token}",
     "description":"Redeem token, get the full 50k envelope (~10MB)."}
  ]
}
```

## Sketch

1. `POST /api/v1/dataset/jumbo/bulk-request` → token.
2. `GET /api/v1/dataset/jumbo/bulk/{token}` (no auth header) → 50k
   ciphertexts. Decrypt with the same RSA private key from
   `/api/v1/private-key`.
3. `GET /api/v1/challenges/algorithm/queries` → 10,000 queries in
   three kinds: count, exists, range_count.
4. **Preprocess once, answer in O(1)/O(log N) per query:**
   - Sort + bucket by whichever field the queries key on (likely
     `latency_ms`, `request_bytes`, `timestamp`, `status_code`).
   - For `exists`/`count` on equality predicates: hashmap of
     `value → list-of-record-ids`.
   - For `range_count` on numeric fields: sort by field, then
     bisect on lo/hi. Cumulative-count array is even better.
5. Submit answers as `{"type":"algorithm_answer","value":"<hash>"}`
   — the brief mentions hash comparison; need to check the exact
   format the verifier expects.

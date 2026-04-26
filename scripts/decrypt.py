#!/usr/bin/env python3
"""Decrypt the dataset using the RSA/PKCS#1 v1.5 private key issued by /api/v1/private-key.

Loads ciphertexts from out/batch_*.json (already fetched), decrypts each
with the PEM at out/private-key.raw, and writes the recovered plaintexts
as bytes (one record per line in NDJSON; bytes are base64-encoded for
roundtrip safety, plus a UTF-8 view if decodable) to out/plaintext.ndjson.

Run: python3 scripts/decrypt.py
"""
from __future__ import annotations

import base64
import glob
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


OUT = Path("out")


def load_ciphertexts() -> list[bytes]:
    records: list[bytes] = []
    for f in sorted(OUT.glob("batch_*.json"),
                    key=lambda p: int(p.name.split("_")[1].split("-")[0])):
        for s in json.loads(f.read_text())["data"]:
            records.append(base64.b64decode(s))
    return records


def main() -> None:
    pem = (OUT / "private-key.raw").read_bytes()
    key = serialization.load_pem_private_key(pem, password=None)
    ciphertexts = load_ciphertexts()
    print(f"loaded {len(ciphertexts)} ciphertexts; key size = {key.key_size} bits",
          file=sys.stderr)

    out_path = OUT / "plaintext.ndjson"
    sample = []
    with out_path.open("w") as out:
        for idx, ct in enumerate(ciphertexts):
            try:
                pt = key.decrypt(ct, padding.PKCS1v15())
            except Exception as e:
                print(f"FAIL id={idx}: {e}", file=sys.stderr)
                continue
            try:
                text = pt.decode("utf-8")
            except UnicodeDecodeError:
                text = None
            rec = {"id": idx, "len": len(pt),
                   "b64": base64.b64encode(pt).decode(),
                   "text": text}
            out.write(json.dumps(rec) + "\n")
            if idx < 5 or idx >= len(ciphertexts) - 3:
                sample.append(rec)

    print(f"wrote {out_path}", file=sys.stderr)
    for r in sample:
        preview = r["text"] if r["text"] is not None else f"<binary len={r['len']}>"
        print(f"  id={r['id']:>4} len={r['len']:>3}  {preview[:120]!r}",
              file=sys.stderr)


if __name__ == "__main__":
    main()

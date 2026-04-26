# Layer 1 — content_hash attempts

All values submitted as `{"type":"content_hash","value":"<hex>"}` to
`POST /api/v1/submit`. Every one returned
`{"correct":false,"layer":1,"message":"Incorrect. Try again."}`.

| Candidate | SHA-256 hex |
|---|---|
| raw concat of 518 base64-decoded ciphertexts | `bc986899fddb27ba792691848fcaaebfb20d61f42e02c133c04112e2905cab93` |
| raw concat of first 500 (seed) ciphertexts | `0902ec05ae96055fefdd5df1885914915dd340a161917fb3d91bf7c4729d4f67` |
| 518 base64 strings joined `""` | `aac282a3bafb760b4ec40d0725669a3b7ddf7039ff7ab243d13ef6b034529aa6` |
| 518 base64 strings joined `"\n"` | `dc77604442b7100db22556a71afa5db504fe4c208c75a0ea960350959e8f878c` |
| 500 base64 strings joined `""` | `719f5048d88e1c4a79b4c2e4ca4157e8bbe6ec4550a95879ff6956567737f6ff` |
| 500 base64 strings joined `"\n"` | `6555efd8dc6d98f6ea50001d45ab4f5f7e3ad1ea8492f2422630b2baa3aea342` |
| 500 base64 strings joined `"\n"` + trailing `\n` | `cbedec2a450787856daf1cbc0bd3ff54773b0d1909b693135897d9b4de214e26` |
| 500 raw cts joined `"\n"` | `5d6a452c93b103123353ab66128ca87f670da4ead34352d287c6a1f9ebbb4a69` |
| canonical compact JSON `[…]` of 500 strings | `d568e8d2cbb41b00f85a5b47b09ca2395eecb86ce66c0f5dd78bbe6c37ebed8a` |
| canonical compact JSON `[…]` of 518 strings | `af42ab8493eb81c96e2161fb522360b482f73e2be4d10b7ad2e08f37e53e43f4` |
| canonical compact JSON `{"data":[…]}` of 500 | `9e2dcb358ab9b243b391746659e567f86843a91866869b09690a222ee703b3fb` |
| canonical compact JSON `{"data":[…]}` of 518 | `b005ca843bf793d38530ac4aff4fd640f6132aa93128d6a12aab1ae1d6e8e669` |
| pretty-printed JSON `[…]` of 500 | `12fcbb19a27d8e6a37df5e0fcf0d3b0f81205b237bb8e20396baf6af058a1946` |
| `id_be32(i) ‖ ct(i)` for 500 ids | `d7dfa1c3f3b083b5da19e3c51d600f73c20f81f1862aaa1fbd75f13ee20c2c5e` |
| `id_be32(i) ‖ ct(i)` for 518 ids | `ae11cea4861b4451faedaa16d9a1452ef5ea18a9a6329a6484a40e9c5096b8c3` |
| Merkle: sha256(∥ sha256(ct_i)) for 500 | `54de2c27c4edfccff16a42c02b1e7b7e5d26da15fcb883b56e888f1879dd65e5` |
| Merkle: sha256(∥ sha256(ct_i)) for 518 | `a5c19985ff5ac03b1c1787cee76a9a1a8d2332cfd012146c98622a90edd463e0` |
| `id:b64\n` lines for 500 | `dd1eef3d663b874af9298cf26f84438531c850ea9e3f7e8bf606039470ef9e11` |
| `id,b64\n` lines for 500 | `d3c89d4c85f16ca6507ebe81904e58d2a47f49eff7d7a02dad4cb9dc13db5066` |
| sha256 of single record 0 ciphertext | `06764ec9457c91afa22ab31db8f9282f42953d3107ef4be164d4cd2ce7ae02e3` |
| concat of 5 batch wire bodies | `ec4f06e99f0b10fe5d91f0e617fbab55241ad5c9efc3b5bbe076edfec821bae1` |
| concat of all 6 batch wire bodies | `1637d168af3c7196a93ce85b0a853c542534ada0659829e97b0d4ef38483fe66` |
| concat of 5 canonicalised batch JSONs | `d87614c30a7a036be8fe0f282468c04988604a2ab713b25c123a08aacf8edb34` |
| first batch wire body only | `c56e1a29a880169a20f3a17a465d6dadf53cc0ead34455510e91287a010b84a9` |
| ETag of `?batch=true&range=0-99` | `b5ce997649da120bec4a9f4e33a84b8541fdaba09fbbfa6f47e6da3d135d7604` |
| concat of all batch ETags (hex string) | `8f87625846b2f17836f9cd87b45f74a52ebd51baf67369688c32c9fe62fc7cfc` |
| concat of all batch ETags (raw bytes) | `06c42113c8cdbfc80874ea90407ba54897273bedced3f5bc3b7878db6b817d2b` |
| batch ETags joined `"\n"` | `ded4822648098eb99393296618fd31f6be22460d5f84ea7d8b482c8fe5a607b3` |
| per-record `{data,id,source}` canonical concat × 500 | `2e471fee383993b23b3ed759e07a742c882290f6d722fc349e8fa6e2a764ae21` |
| per-record `{data,id,source}` joined `"\n"` × 500 | `4f2d626b5a11556ae69a8d5528225825719744b260ea18c29d235eb7d79b14d3` |
| `{"data":[…tuples…]}` × 500 | `259d579c9bcc990856fc47f81554e9bf70abdb84f41a90b9ce08b589493ba0c0` |
| batch-envelope shape `{count, data, range_end, range_start}` × 500 | `8cf7ef4dc9c591833c03e9193bc0148c96ede05bb7d186ad3dc627d64692fe04` |

Format variations also tried (against the `seed_pt_concat_raw`
plaintext value `f04a72…b5a0`):

- `sha256:f04a72…b5a0` (with prefix) → rejected
- `F04A72…B5A0` (uppercase) → rejected

Plus a couple of cross-layer swaps (sending the plaintext hash as
`content_hash`, and vice versa) — also rejected.

## What I would try next

- HMAC-SHA256 keyed by the API key bytes (or by the raw 32 bytes after `sa_`)
- `Repr-Digest: sha-256=:...:` style (RFC 9530 base64)
- BLAKE3 / SHA-512 / SHA3-256 instead of SHA-256
- Concatenating in *fetch* order (not id order)
- Hash bound by a server-issued snapshot id (haven't found such a
  thing yet, but `OPTIONS /api/v1/dataset` only documented `batch`,
  `range`, `page`, `page_size`)

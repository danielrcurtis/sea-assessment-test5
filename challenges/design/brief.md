# Challenge: Service Design with Infrastructure Constraints

Build a small service that exercises real production infra choices, then
commit it to the same repo you'll submit via `POST /api/v1/submit
{"type":"repo", …}`.

This challenge is **free-floating**: you can skip it entirely, attempt it
alongside the four main puzzle layers, or polish it after you've
submitted the layer hashes. Completion isn't tracked by the platform —
your reviewer inspects the `challenges/design/` directory in your repo.

### Your own clock on this challenge

The design challenge has its **own 4-hour timer**, independent of the
main 3-hour puzzle clock. Your timer starts the first time you call
`GET /api/v1/challenges/design` and is recorded server-side. Every
response to that endpoint carries three headers so you can read them
straight off the wire:

```
X-Challenge-Started-At:     2026-04-21T14:03:12+00:00
X-Challenge-Deadline-At:    2026-04-21T18:03:12+00:00
X-Challenge-Remaining-Seconds: 14398
```

The timer is **idempotent** — re-reading this markdown later doesn't
reset or extend the clock, so you can reference it freely. The
reviewer sees your start/deadline alongside your submitted repo;
late submissions aren't automatically rejected, but they are visible.

Poll `OPTIONS /api/v1/challenges` any time to see timer state for
every challenge on a single page.

---

## The scenario

You're building a **rate-limited API-key issuance service** for an
internal SaaS. The service should:

1. Accept `POST /keys` with `{"owner_email": "someone@example.com"}` and
   return a freshly generated API key in the response body.
2. Enforce a per-owner-email rate limit: **no more than 3 keys issued
   per owner per rolling hour**.
3. Store issued keys durably so a crash (or a `docker compose down`)
   doesn't forget them.
4. Expose `GET /keys?owner_email=...` returning the list of keys for
   that owner with their `created_at` timestamps.

That's it for the functional surface. The interesting part is
**how** you build it.

---

## Mandatory constraints

Your implementation MUST:

- **Use Redis for the rate-limit state.** Sliding window or token bucket
  — your choice — but the state has to live in Redis so the service is
  horizontally scalable. Don't implement rate-limiting in-process; part
  of the point is showing you reach for the right tool.
- **Use Postgres for durable key storage.** SQLite is tempting for a
  one-file demo; don't. We want a real production stack.
- **Encrypt the stored API keys at rest with AES-256-GCM**, using a key
  derived via **HKDF-SHA256** from an env-var master secret. This is
  intentionally different from the RSA/PKCS#1v1.5 scheme the main
  puzzle used — we want to see you pick the modern AEAD primitive when
  building from scratch.
- **Ship a `docker-compose.yml`** that brings up your service + Redis +
  Postgres with one command.
- **Include a `README.md`** under `challenges/design/` explaining:
  - How to run it (`docker compose up -d`)
  - How to exercise it (a copy-pasteable `curl` sequence)
  - What you decided not to do and why

You can pick any language and web framework. Rust is fine, Python is
fine, Go is fine. The constraints are on the infra and the crypto
primitive, not the source language.

---

## What "complete" looks like

**Minimum:**

- `docker compose up -d` inside `challenges/design/` leaves a service
  reachable on a port of your choice.
- `curl -X POST -d '{"owner_email":"a@b.test"}' .../keys` returns
  `201 Created` with `{"api_key":"..."}`.
- The fourth call within an hour for the same email returns
  `429 Too Many Requests`.
- `curl .../keys?owner_email=a@b.test` returns a JSON array of keys.
- `docker compose down && docker compose up -d` keeps the keys.

**Stretch:**

- Tests (unit and integration). Test-first is favoured; reviewers can
  tell from your commit history.
- Structured logging.
- A `GET /metrics` endpoint or similar, even just Prometheus-style
  counters.
- A `HEALTHCHECK` in the Dockerfile.
- A `DECISIONS.md` or equivalent covering tradeoffs you made — schema
  choices, retry behaviour, the shape of your cache invalidation.
- Graceful shutdown (SIGTERM handling).

---

## What your reviewer looks for

- **Correctness.** The four functional bullets work end-to-end.
- **Infrastructure literacy.** Did you model the rate-limit state
  correctly? Are Postgres migrations sane? Does Redis hold the state
  that matters (and *only* that state)?
- **Crypto hygiene.** Is the AES-GCM nonce fresh per encryption? Is
  the HKDF info/salt meaningful? Are you storing the ciphertext or
  accidentally the plaintext?
- **Production posture.** Tests, logs, health/metrics, graceful
  shutdown — the things that make an on-call engineer's life bearable.
- **Code quality.** Same bar as the main puzzle's repo evaluation —
  tests, commit hygiene, README clarity, linting.

---

## Where it lives in your repo

```
<your-repo>/
├── README.md                      ← top-level; index the sub-projects
├── challenges/
│   └── design/
│       ├── README.md              ← how to run THIS challenge
│       ├── docker-compose.yml
│       ├── src/…
│       └── tests/…
└── …                              ← your main puzzle work
```

Submit the repo URL via `POST /api/v1/submit {"type":"repo","value":"..."}`
as usual. You can include `"notes": "design challenge attempted"` if
you want to flag it explicitly.

# Challenge: Dataset Visualization UI

Build a small React app that models and visualizes a usage-events
dataset, then commit it under `challenges/ui/` in the same repo you'll
submit via `POST /api/v1/submit {"type":"repo", …}`.

This challenge is **free-floating**: skip it, attempt it alongside the
puzzle layers, or tackle it separately. Completion isn't tracked by the
platform — your reviewer opens `challenges/ui/` and runs it locally.

### Your own clock on this challenge

The UI challenge has its **own 3-hour timer**, independent of the main
3-hour puzzle clock. Your timer starts the first time you call
`GET /api/v1/challenges/ui` and is recorded server-side. Every response
carries three headers:

```
X-Challenge-Started-At:     2026-04-21T14:03:12+00:00
X-Challenge-Deadline-At:    2026-04-21T17:03:12+00:00
X-Challenge-Remaining-Seconds: 10793
```

The timer is **idempotent** — re-reading the markdown doesn't reset or
extend the clock. Poll `OPTIONS /api/v1/challenges` any time for
timer state across every challenge in one response.

---

## The scenario

You're the frontend engineer on an observability team. The backend emits
request-log events with the same shape you decrypted in Layer 2:

```jsonc
{
  "endpoint":     "/api/v1/auth/refresh",
  "method":       "POST",
  "status_code":  400,
  "latency_ms":   1781,
  "timestamp":    "2026-01-05T13:00:10+00:00",
  "user_segment": "free-tier",
  "request_bytes": 46868
}
```

An on-call engineer has been paged about elevated error rates. Build a
page that lets them investigate.

---

## Mandatory features

- **Stack:** React 18+ with **TypeScript**. Vite or Next.js or Remix
  — your choice. No jQuery or vanilla-DOM shims.
- **Source data:** the assessment API exposes a public, no-auth,
  CORS-enabled endpoint specifically for this challenge —
  `GET /api/v1/challenges/ui/dataset`. It returns 500 deterministically-
  seeded records in a stable JSON envelope, so your UI can fetch
  directly from your React dev server and your fixtures can pin against
  the exact bytes. (You're welcome to supplement with synthetic records
  if you want more volume; the public dataset is the *minimum*.)
- **The page must provide:**
  1. A **sortable, filterable table** of the records. Minimum filters:
     by `user_segment` and by HTTP status class (2xx/4xx/5xx). Minimum
     sorts: by `latency_ms` and by `timestamp`.
  2. At least **one aggregate visualization**. Histogram of
     `latency_ms` by segment, timeseries of error rate, heatmap of
     endpoint × status — your call. Recharts / Chart.js / Visx /
     hand-rolled SVG are all fair game.
  3. A **detail view** (modal or side-panel) that opens when you click
     a row, showing the full record plus any derived fields (e.g.,
     which 2xx/4xx/5xx class, parsed timestamp, maybe a segment-level
     z-score for latency).
- **State handling:** persist filter + sort state in the URL so
  reloading the page preserves the view. TanStack Router, React
  Router, your own `URLSearchParams` wiring — all acceptable.
- **Responsiveness:** works on a 1280px laptop viewport and on a 390px
  phone viewport. Phone view doesn't need to be beautiful; it needs to
  be usable (no horizontal scroll of a 7-column table).

---

## Fetching the dataset

Example React/fetch snippet — no `Authorization` header, no API key,
just a plain cross-origin GET:

```ts
const BASE_URL = import.meta.env.VITE_BASE_URL ?? "http://localhost:3001";

type UsageRecord = {
  endpoint: string;
  method: string;
  status_code: number;
  latency_ms: number;
  timestamp: string;
  user_segment: string;
  request_bytes: number;
};

type DatasetResponse = {
  records: UsageRecord[];
  count: number;
  note: string;
};

export async function fetchDataset(): Promise<UsageRecord[]> {
  const resp = await fetch(`${BASE_URL}/api/v1/challenges/ui/dataset`);
  if (!resp.ok) throw new Error(`dataset fetch failed: ${resp.status}`);
  const body: DatasetResponse = await resp.json();
  return body.records;
}
```

The response is cached for 24 hours (`Cache-Control: public, max-age=86400,
immutable`) and the bytes are stable across server restarts, so a
`fetch` from a test fixture returns the same 500 records today as
tomorrow.

## What "complete" looks like

**Minimum:**

- `cd challenges/ui && npm install && npm run dev` opens the page
  with the dataset loaded on first paint.
- Filters + sort + detail view all work and are reflected in the URL.
- The aggregate visualization reveals something that the table doesn't
  — e.g., a latency outlier cluster at a specific timestamp range.
- `npm test` passes with at least one **meaningful** test (a sort
  predicate, a filter reducer, a component integration — not
  `expect(true).toBe(true)`).

**Stretch:**

- Keyboard navigation (Tab through rows, Enter to open detail, Esc to
  close).
- CSV export of the currently-filtered set.
- Dark-mode toggle with `localStorage` persistence.
- Storybook or similar for your components.
- A `lighthouse` CI run in the repo showing accessibility ≥ 90.

---

## What your reviewer looks for

- **Component structure.** Can another dev drop in and find their way
  around? Is state owned at the right level?
- **State decisions.** `useState` vs. `useReducer` vs. context vs. an
  external store — no single right answer, but a one-sentence rationale
  in a comment (or in the README) is the difference between
  "intentional" and "cargo-culted".
- **Styling discipline.** Tailwind, CSS modules, vanilla CSS, CSS-in-JS
  — pick one and be consistent. Inline-style soup is the anti-signal.
- **Accessibility basics.** Focus rings, semantic HTML, alt text on
  anything that needs it, aria-labels on icon buttons.
- **Tests.** At least one test that would actually catch a regression.
  Bonus points for a component test that renders a fixture and asserts
  on user-visible output, not internal state.
- **Code quality.** Same bar as your main repo work: types are tight,
  error paths are intentional, commits tell a story.

---

## Where it lives in your repo

```
<your-repo>/
├── README.md                      ← top-level; index the sub-projects
├── challenges/
│   └── ui/
│       ├── README.md              ← how to run THIS challenge
│       ├── package.json
│       └── src/…                  ← fetches from /api/v1/challenges/ui/dataset
└── …                              ← your main puzzle work
```

Submit the repo URL via `POST /api/v1/submit {"type":"repo","value":"..."}`
as usual. You can include `"notes": "ui challenge attempted"` if you
want to flag it explicitly — reviewers see the `notes` field alongside
the repo URL.

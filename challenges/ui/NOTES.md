# challenges/ui — starting notes

Not implemented. Saved spec is in `brief.md`.

## Sketch

- Vite + React + TypeScript. Tanstack Table for sort/filter,
  Recharts for the aggregate visualisation, react-router for the
  detail view.
- URL-persisted state via a tiny `useSearchParams` wrapper — every
  filter, sort key, and page index round-trips through query params.
- Data source: the same dataset served by the puzzle (or a local
  fixture for offline review). Each record has `endpoint`,
  `method`, `status_code`, `latency_ms`, `request_bytes`,
  `timestamp`, `user_segment` — those map directly to columns and
  filter facets.
- Aggregate: status_code distribution stacked by endpoint, brushable
  to filter the table.
- Detail view: `/event/:id` shows the full record + a sparkline of
  same-endpoint latency around its timestamp.

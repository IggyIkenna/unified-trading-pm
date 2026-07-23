---
doc_type: issue
title: >-
  /api/alerts is structurally slow (~240s/day) because _read_alerting_service_sync lists+downloads one GCS object per
  alert event, synchronously, one at a time — two stopgaps shipped 2026-07-22/23, root cause still open
summary: >-
  2026-07-22: the /alerts page was hanging indefinitely / OOM-killing the Cloud Run container (measured 16.6-16.8GB
  against a 16GB limit). Root cause: the alerting-service bucket writes ONE OBJECT PER ALERT EVENT (~9,600-24,000
  objects/day, 277,684 objects across the prior 30-day window as of 2026-07-21 per
  deployment_alerts_ingestion_completeness_2026_07_20.md's own todo-11 measurement), and _read_alerting_service_sync()
  in deployment-api/deployment_api/routes/_repo_ci_alerts.py does one list_blobs() + a SEPARATE download_from_storage()
  call PER OBJECT, sequentially, inside one HTTP request. Two stopgaps shipped and verified live: (1)
  deployment-api@8623c5f narrowed _DEFAULT_DAYS 30->1, which took the default request from "always OOMs/504s" to
  "reliably completes in ~240s"; (2) deployment-ui@b599eaf gave getUnifiedAlerts() a dedicated 480s client timeout (the
  shared apiClient's 120s default was aborting the now-working-but-still-slow request client-side, surfacing as "Request
  was cancelled") plus an in-flight guard on the 60s auto-refresh (without it, the interval would stack concurrent 240s
  requests against a backend already proven to OOM under load). Both are LIVE and content+behavior-verified in
  production as of 2026-07-23. What is NOT fixed: the per-object read pattern itself. ~240s for a single day is still
  bad UX and the true story is still: any day with unusually high alert volume could push wall-clock time up until it
  re-triggers the wall clock ceiling and/or backend OOM, and the 30-day date-range widen the UI already ships (_MAX_DAYS
  still 30) would reproduce the original crash if a user actually uses it.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-ui, alerting-service]
scope: [engineer]
tags: [alerts, observability, performance, gcs, n-plus-one]
related:
  - /plans/active/deployment_alerts_ingestion_completeness_2026_07_20.md
  - /plans/active/deployment_ui_alerts_page_rebuild_2026_07_20.md
created: 2026-07-23
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
source:
  [
    "operator conversation 2026-07-22/23 — page reported stuck on 'Loading...', traced end-to-end through OOM, deploy
    verification, and a second client-timeout bug",
  ]
---

# /api/alerts per-object GCS read performance — root cause open, two stopgaps shipped

## Context

`/alerts` → `GET /api/alerts` → `deployment_api/routes/unified_alerts.py` → `_repo_ci_alerts.py::load_alerts_payload()`
merges 5 source planes. One of them, `_read_alerting_service_sync()`, reads the `alerting-service-{project}` bucket's
`alerting/history/date={date}/*.jsonl` prefix — and that bucket is written **one object per alert event** (not batched
per day like the `cicd-events` bucket). Measured live 2026-07-22:

- `date=2026-07-20/`: 23,889 objects
- `date=2026-07-21/`: 23,981 objects
- `date=2026-07-22/`: 9,642 objects (partial day)

`_read_alerting_service_sync()` does, per date in the window:

```python
for blob in client.list_blobs(bucket, prefix=prefix):
    raw = download_from_storage(bucket, blob.name)   # one HTTP round-trip PER OBJECT, sequential
```

With the old `_DEFAULT_DAYS = 30`, an unqualified `GET /api/alerts` request walked 30 days × ~3 source planes ×
thousands of objects/day. Measured production behavior before the fix (Cloud Logging, 2026-07-21/22):

- Default (30-day) request: `504` at Cloud Run's 900s hard timeout.
- Several requests: `503` after 61-99s — container OOM-killed
  (`Memory limit of 16384 MiB exceeded with 16679-16843 MiB used`, `Container terminated on signal 9`).
- Even `days=1&limit=10` (smallest possible request): took **301s** to return `200`.

## What's shipped (both live + verified 2026-07-23)

1. **`deployment-api@8623c5f`** — `_DEFAULT_DAYS` split from `_MAX_DAYS` (was `_DEFAULT_DAYS = _MAX_DAYS = 30`); default
   is now `1`, max stays `30` so the UI's date-range picker can still request a wider window explicitly.
   Content-verified on the deployed Cloud Run image (`a58d6a8`, ready 2026-07-23T01:04:53Z) and behavior-verified via a
   real HTTP call against the live URL: `200` in `242s`, `days: 1`, `total_count: 4867`, `source: "live"`.
   - Side finding, not a blocker: the Cloud Build for that exact commit (`8a130448-...`) shows overall status
     `TIMEOUT`/`CANCELLED`, but every real step (`build`/`quality-gates`/`push`/`deploy`) succeeded — the deploy step's
     own log confirms `"Service ... has been deployed and is serving 100 percent of traffic"` before the build's overall
     wall-clock ceiling cancelled some later (likely redundant post-deploy polling) work. Worth someone tightening the
     build timeout budget so a real TIMEOUT reads unambiguously, but not urgent — flagging so a future reader doesn't
     mistake a similar TIMEOUT status for a failed deploy without checking the step-level log.
2. **`deployment-ui@b599eaf`** — two related frontend bugs, found because the 8623c5f fix changed the failure mode from
   "hangs forever" to "completes in ~240s," which is _longer than the frontend's own 120s client timeout_:
   - `getUnifiedAlerts()` now uses a dedicated API client with a 480s timeout (was inheriting the shared 120s default) —
     same pattern as the existing `retryFailedShards`/`retryClient`.
   - `Alerts.tsx`'s `load()` gained an in-flight `useRef` guard — without it, the 60s `useVisibilityPausedInterval`
     auto-refresh (plus its immediate-refresh-on-tab-visibility-regain behavior) would fire a NEW ~240s request every 60
     seconds regardless of whether the previous one was still pending, stacking multiple concurrent slow requests
     against a backend already proven to OOM under load — i.e. raising the timeout alone, without this guard, could have
     made the OOM risk WORSE, not better.
   - Both content-verified locally (typecheck/lint/101 unit tests/build all green) and behavior-verified through an
     actual isolated browser session (Playwright, not curl) against a live local backend serving real prod data.

## What's still open (this issue)

The per-object sequential read pattern itself is unfixed. `_DEFAULT_DAYS=1` and the 480s client timeout are **stopgaps
that made the current failure mode survivable**, not a fix. Concretely still true:

- A single day already takes ~240s and grows through the day (the partition is still being written to).
- `_MAX_DAYS` is still `30` and the UI's date-range picker (`deployment_ui_alerts_page_rebuild_2026_07_20.md`) lets a
  user request up to that window explicitly — doing so would very likely reproduce the original OOM/504, since the 480s
  client timeout and single-day default don't bound what a user-requested wider window costs server-side.
- No caller-side or server-side concurrency exists for the GCS reads — `list_blobs()` + `download_from_storage()` per
  object, one at a time, is the entire access pattern.

## Recommended next steps (not yet actioned — needs an operator decision on approach before scoping a plan)

Two independent directions, not mutually exclusive:

1. **Fix the reader** (`_read_alerting_service_sync` in `deployment-api/deployment_api/routes/_repo_ci_alerts.py`) —
   concurrent/batched fetch (e.g. `asyncio.gather` with a bounded semaphore, or GCS's batch API) instead of one
   sequential call per object. Fastest to ship, contained to deployment-api, doesn't touch the writer, but the
   underlying "one tiny object per event" storage shape stays expensive to enumerate (`list_blobs` alone over ~24k
   objects/day is not free) — this bounds the damage, it doesn't eliminate it.
2. **Fix the writer** (`alerting-service`'s `persistence/storage_store.py`) — batch alert events into one JSONL-per-day
   object, matching the pattern the `cicd-events` bucket already uses successfully (which is why that source plane is
   NOT part of this problem). Fixes the root cause, but touches a different repo's write path, and existing per-event
   objects need either a migration/backfill or the reader needs to keep supporting both shapes during a transition.

Per `plans/active/task_template.md`'s plan-destination rule, whichever direction (or both) the operator picks should
become its own plan — this issue doc is the durable record of the finding and the options, not itself a plan.

## Codex SSOTs

- `/codex/04-architecture/ci-alerting.md` — the unified alerts ledger contract, diagnostic-surface principle, per-source
  coverage table (predates this issue; does not yet document the performance characteristics found here).
- `deployment_alerts_ingestion_completeness_2026_07_20.md` — the plan that added `_read_alerting_service_sync` and
  measured the 277,684-object scale (2026-07-21) without flagging the per-object read cost at that scale as a risk.

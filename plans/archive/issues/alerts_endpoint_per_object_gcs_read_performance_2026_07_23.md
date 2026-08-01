---
doc_type: issue
title: >-
  /api/alerts is structurally slow (~240s/day) because _read_alerting_service_sync lists+downloads one GCS object per
  alert event, synchronously, one at a time — reader-side concurrency fix shipped live, writer-side batching WONT-DO'd
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
status: resolved
nature: issue
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [meta]; the deployment-ui /alerts page's
  # own backend (deployment-api) N+1 read-performance bug
stage: [meta]
repos: [deployment-api, deployment-ui, alerting-service]
scope: [engineer]
tags: [alerts, observability, performance, gcs, n-plus-one]
related:
  - /plans/archive/2026_07/deployment_alerts_ingestion_completeness_2026_07_20.md
  - /plans/archive/2026_07/deployment_ui_alerts_page_rebuild_2026_07_20.md
created: 2026-07-23
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by: >-
  reader-side concurrent/batched GCS fetch (deployment-api@79a1d36, live+verified) fixed the user-facing OOM/504
  symptom; writer-side batching closed WONT-DO 2026-08-01 (BLK-1cce4df8, same ruling as sibling BLK-ac45347a 2026-07-30)
  — cost/list-latency concern only, no operator decision to pursue exists, CAS design constraints preserved in the
  todo's closure note for future revival.
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

## Todos

- [x] ✅ [OPERATOR] P1. **Operator-ruled 2026-07-29 (interactive decision session): do both** — reader-side
      concurrency/batching now, writer-side batching next. Pick a fix direction for the per-object GCS read pattern —
      reader-side concurrent/batched fetch vs writer-side batching into one JSONL-per-day object (see "Recommended next
      steps" above); the root cause is still unfixed and `_MAX_DAYS=30` would still reproduce the original OOM if a user
      requests it.

- [x] ✅ [CODE] P1. **Ship reader-side concurrent/batched GCS fetch** in `deployment-api`'s
      `_read_alerting_service_sync` — durable stopgap that bounds the OOM risk for any date range, independent of the
      writer-side fix below. Done when: a request for the full `_MAX_DAYS` range completes without the memory/latency
      profile that caused the 2026-07-22 incident. — `deployment-api@79a1d36`: listing stays a sequential per-date walk
      (cheap), but downloads across the whole requested window now run on a `_GCS_FETCH_MAX_WORKERS=32`-bounded
      `ThreadPoolExecutor` instead of one sequential HTTP round-trip per object — the same bounded-fan-out pattern
      already used for bulk GCS ops elsewhere in deployment-api and in `unified_trading_library.manifest_consolidator`.
      A single object's download failure no longer aborts the rest of its date's batch (per-object try/except,
      best-effort merge preserved). Unit-verified: `TestReadAlertingServiceSync::test_concurrent_fetch_merges_all_blobs`
      (50 concurrently-fetched blobs all merge, none dropped by the fan-out) and
      `::test_single_object_failure_does_not_drop_other_blobs` (one failing download doesn't blank the rest); full
      `quality-gates.sh` green on the shipped SHA.
- [x] 🚫 WONT-DO / superseded [CODE] P2. ~~Batch alerting-service's writes into one JSONL-per-day object, matching the
      already-proven cicd-events pattern~~ — **the cited pattern no longer exists.** `cicd-events` was migrated OFF
      one-JSONL-per-day onto one-object-per-event on 2026-07-21, specifically because the daily-shared-object writer
      (unlocked `gsutil cp` down → local append → `cp` up) silently dropped rows under concurrent writers (measured
      ~1/145 writer-runs survived — see
      `/plans/archive/issues/persist_cicd_event_ledger_read_modify_write_race_2026_07_17.md` +
      `/plans/archive/issues/alerts_ledger_race_two_remaining_writers_2026_07_21.md`). Implementing this todo literally
      would reintroduce that exact data-loss race class — banned per the data-pipeline-correctness hard rule — and
      alerting-service has multiple concurrent in-process writer call sites (`alerting_service/notifiers/router.py:539`,
      `alerting_service/core/alert_store.py:46`) exposed to the identical race. The driving symptom (OOM/504) is already
      fixed by the reader-side todo above (`deployment-api@79a1d36`, shipped + live) — remaining per-event object volume
      is a cost/list-latency concern, not correctness, so there's no forcing urgency to rebuild the write path now.
      Closed on its own merits per main's ruling 2026-07-30 (BLK-ac45347a), agreeing with the investigating agent's
      recommendation; the 2026-07-29 `[OPERATOR]` approval above was premised on the now-defunct cicd-events pattern.
      Full evidence: Progress Log below (`unified-trading-pm@ec23016ab`). Escalation carve-out: if per-event object
      volume is later shown to cause a genuine correctness/availability problem (not just cost/list-latency), reopen as
      its own plan — do not silently proceed.
- [x] 🚫 WONT-DO / superseded [CODE] P3. ~~If/when alerting-service object-count reduction is pursued, re-scope it as
      its own reviewed plan~~ (not a snap-built todo) using a GCS generation-precondition CAS design: read current
      generation, append in-memory, write with `ifGenerationMatch`, retry-on-412 with backoff, plus concurrency-safety
      tests proving zero dropped rows under concurrent writers (model the tests on the two cicd-events race-incident
      docs cited above). MUST NOT use the abandoned cp-down/append/cp-up shape. (repo: alerting-service) — **closed
      2026-08-01 per main ruling (BLK-1cce4df8), same disposition as the identical P2 sibling (BLK-ac45347a,
      2026-07-30)**: the driving OOM/504 symptom is already fixed live by the reader-side concurrency fix
      (`deployment-api@79a1d36`) — remaining per-event object volume is a cost/list-latency concern, not correctness,
      and no operator decision to pursue writer-side batching exists. Treating this P3 differently from its
      identical-change P2 sibling would be incoherent, and this todo's own text prescribes re-scoping as its OWN
      reviewed plan when/if pursued — a perpetually-open checkbox is the wrong home (recurring re-dispatch churn on
      every backlog regen, blocks plan archival). The CAS design constraints above stay captured in this closure record
      and are revivable as a new plan on an actual future operator decision to pursue.

## Codex SSOTs

- `/codex/04-architecture/ci-alerting.md` — the unified alerts ledger contract, diagnostic-surface principle, per-source
  coverage table (predates this issue; does not yet document the performance characteristics found here).
- `deployment_alerts_ingestion_completeness_2026_07_20.md` — the plan that added `_read_alerting_service_sync` and
  measured the 277,684-object scale (2026-07-21) without flagging the per-object read cost at that scale as a risk.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
- **backend_engineer (slot 8) 2026-07-30 — STOP, premise is stale, escalating via /blocked**: investigated implementing
  the still-open P2 todo ("batch alerting-service's writes into one JSONL-per-day object, matching the already-proven
  cicd-events pattern") and found the cited pattern no longer exists. `cicd-events` was ITSELF migrated OFF
  one-JSONL-per-day onto one-object-per-event on 2026-07-21 — specifically because the daily-shared-object writer
  (`gsutil cp` down → local append → `cp` up) was an unlocked read-modify-write race that silently dropped rows under
  concurrent writers: measured ~1 row survived out of ~145 writer-runs on the PM repo's shared daily events file. See
  `/plans/archive/issues/persist_cicd_event_ledger_read_modify_write_race_2026_07_17.md` (root cause + measurement) and
  `/plans/archive/issues/alerts_ledger_race_two_remaining_writers_2026_07_21.md` (same fix applied to the sibling
  `cicd/alerts/{date}/` ledger). The CURRENT `.github/actions/persist-event/action.yml` writer header says verbatim:
  "ONE OBJECT PER EVENT (root-cause fix, not a mitigation — 2026-07-21)... writing each event straight to its OWN
  never-overwritten object eliminates the race with zero reader changes" — i.e. cicd-events today is structurally the
  SAME shape alerting-service already has (one-object-per-event), not the batched shape this todo asks alerting-service
  to adopt. Implementing this todo literally would REINTRODUCE the exact data-loss race class that was root-caused out
  of cicd-events nine days before the 2026-07-29 operator ruling approved this todo — that ruling cited "matching the
  already-proven cicd-events pattern," which no longer describes cicd-events' live code. alerting-service also has
  multiple concurrent in-process writer call sites (`alerting_service/notifiers/router.py:539` per delivery record,
  `alerting_service/core/alert_store.py:46` per fired alert), so a naive daily-batch write is exposed to the identical
  race. One piece of the plan IS still sound and unaffected by this finding: the reader
  (`_read_alerting_service_sync`/`_read_ledgers_sync` in `deployment-api/deployment_api/routes/_repo_ci_alerts.py`) is
  already a pure prefix-walk-then-parse-every-blob, so it would absorb a mixed corpus of per-event + daily-batch objects
  with zero reader changes — same as how it absorbed cicd-events' writer-shape change with zero reader edits. Posted
  `/blocked` (options: (A) implement daily batching safely via GCS generation-precondition CAS + retry-on-412 instead of
  the abandoned cp-down/append/cp-up shape; (B) treat the premise as stale, mark this todo WON'T-DO / superseded since
  the reader-side fix already shipped+live (`deployment-api@79a1d36`) and solved the user-facing OOM/504 symptom, the
  remaining per-event volume is a cost/list-latency concern not a correctness one; (C) in-memory buffer +
  periodic/shutdown flush per alerting-service process, trading the read-modify-write race for a crash-before-flush loss
  risk instead — recommended B). NOT implementing pending the operator's re-decision; not silently skipping either.
- **slot 3 (review-role worker) 2026-08-01**: dispatched the standing P3 todo ("if/when pursued, re-scope as its own
  plan"). Recognized it as conditional forward-guidance, not actionable code — no operator decision to pursue
  writer-side batching exists, and its content duplicates the already-WONT-DO'd P2 sibling. Filed `/blocked`
  (BLK-1cce4df8) rather than building unwanted speculative code. Main answered **B: close/mark-resolved as superseded**,
  same ruling as BLK-ac45347a. Flipped the checkbox to WONT-DO/superseded above with the CAS design constraints
  preserved for future revival.

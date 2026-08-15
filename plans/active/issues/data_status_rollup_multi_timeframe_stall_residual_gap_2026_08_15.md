---
doc_type: issue
title: data-status rollup dead-lock fix (0bb3694c80) narrows but doesn't close the gap — a stalled service still blocks the lock for a full TTL cycle
summary: >-
  Live-verifying the maintenance-window dead-lock fix (deployment-api@0bb3694c80) for
  data_status_rollup_ml_service_full_blob_missing_2026_07_26.md's P2 follow-up found a real improvement (services #1-8
  renew the lock correctly every cycle, 40min TTL vs the old 150min) but also a residual gap: a service that hangs past
  its own per-service isolated-child timeout budget without that child's kill-and-report path ever firing still blocks
  the lock — and every service queued after it — for the FULL remaining TTL, same dead-lock class just bounded shorter.
  Live-observed `features-multi-timeframe-service` stalling ~50min with zero renewal/failure log, starving services
  #9-14 (incl. ml-service, the original doc's subject) of that entire sweep cycle.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api]
scope: [engineer, admin]
tags: [data-status, rollup, cloud-run, maintenance-window, dead-lock, honest-absence]
related:
  [
    /plans/archive/2026_08/issues/data_status_rollup_ml_service_full_blob_missing_2026_07_26.md,
    /plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md,
  ]
created: 2026-08-15
author: data_engineering (slot-6)
last_updated: 2026-08-15
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: live-verify of deployment-api@0bb3694c80 (slot-6, 2026-08-15T21:02Z), split out of
  data_status_rollup_ml_service_full_blob_missing_2026_07_26.md's P2 todo (that doc is at its 1000-line hard cap, so
  this finding + follow-up fix are filed here instead of appended there)
depends_on: []
context_scope:
  [
    deployment-api/deployment_api/scripts/data_status_rollup_worker.py,
    deployment-api/deployment_api/routes/data_status/_rollup.py,
    /plans/archive/2026_08/issues/data_status_rollup_ml_service_full_blob_missing_2026_07_26.md,
  ]
---

# data-status rollup: dead-lock fix narrows but doesn't close the gap (2026-08-15)

## What I found

Live-verifying `deployment-api@0bb3694c80` (the maintenance-window dead-lock fix — heartbeat-renew the lock after each
service, TTL 150min→40min) against its own done-when
(`/plans/archive/2026_08/issues/data_status_rollup_ml_service_full_blob_missing_2026_07_26.md`'s P2 todo, now marked
verified-partial in that archived doc: "a 24h Cloud Logging trace showing every one of the 14 services processed at
least once every ~40min, never silently skipped on a stale dead-man's lock"):

Confirmed the fix commit reached the live revision `uts-prod-data-status-rollup-svc-00480-v7t` (created
2026-08-15T18:44:01Z). `gcloud logging read` over 2026-08-15T18:44Z-21:02Z (~2h18m of the requested 24h window — not
the full window, but enough to already answer the question):

- **The fix works for services #1-8.** Sweep `rollup-run-c0e8422eedd14277b4841f12e16d4a8d` (started 19:20:36Z)
  correctly renewed the maintenance-window lock after each of `instruments-service`, `market-tick-data-service`
  (failed/timeout), `market-data-processing-service` (failed/timeout), `features-delta-one-service` (failed/timeout),
  `features-volatility-service`, `features-onchain-service`, `features-sports-service`, `features-calendar-service` —
  each gap 4-7min, well inside the 40min TTL. This is a genuine improvement over the pre-fix behavior (a
  whole-container OOM used to dead-lock the lock for the remaining ~125 of 150min with zero renewal at all).
- **The same sweep then stalled ~50min with ZERO renewal or failure log** on service #9,
  `features-multi-timeframe-service` (no `_CHILD_JOIN_TIMEOUT_OVERRIDES_S` entry → default 420s/7min budget it should
  have hit and reported on by ~20:17Z). Last renewal was 20:09:56Z (lock TTL expiry 20:49:56Z). Both the 20:20Z and
  20:40Z `*/20min` scheduler ticks were silently `SKIPPED — a prior run is still in flight` waiting on this exact
  stale lock — the precise symptom the fix was meant to eliminate, just shorter (bounded by the new 40min TTL instead
  of the old 150min).
- **The TTL fallback DOES work as designed**: once the 40min TTL expired, the next scheduler tick (21:00:36Z)
  successfully acquired a fresh lock (`rollup-run-366530a48656490cbbf8478f8ec0ebea`) and started a new sweep from
  service #1. But that means services #9-14 — `features-cross-instrument-service`, `features-commodity-service`,
  **`ml-service`** (the original 2026-07-26 doc's subject), `strategy-service`, `execution-service` — got ZERO chance
  to run in that entire ~100min window (19:20Z sweep start to 21:00Z restart), and the new sweep restarts from #1, so
  ml-service still isn't reached as of this check.
- **Candidate root cause, not yet confirmed**: `INFO Shutting down API...` was logged on this revision at 20:55:37Z
  (~46min into the stall). `_rollup.py::run_data_status_rollup` awaits the entire 14-service sweep SYNCHRONOUSLY via
  `await asyncio.to_thread(run_rollup, ...)` — the whole compute runs inside one long-lived HTTP request/thread. If
  Cloud Run recycled or killed the instance mid-service (autoscaling scale-down, a platform-level request-timeout
  cancellation that detaches from but doesn't kill the underlying `to_thread` worker, etc.), the in-flight per-service
  isolated child would be orphaned without `run_rollup`'s `on_service_done` hook ever firing for it — a kill mechanism
  the 2026-08-15 fix's heartbeat doesn't cover, since it only renews AFTER a service's `_run_service_isolated` call
  returns. The alternative candidate — the spawned child itself hanging inside GCS I/O past what
  `os.killpg(SIGTERM)`/`SIGKILL` in `_run_service_isolated`'s own termination path could interrupt — has not been
  ruled out either; both need a live trace of `_run_service_isolated`'s own internal state during a repeat stall to
  distinguish.

## Why it matters

This is the SAME class of bug the P1 fix (`0bb3694c80`) was shipped to close (a mid-sweep death that never runs the
lock's release/renewal path), just with a shorter blast radius (bounded to ~40-50min instead of ~150min) and a
different apparent trigger (an instance-level kill/hang on a specific service, not a whole-container OOM). Until this
is fixed, ml-service (and any service positioned after whichever one stalls) can still go multiple sweep cycles
without ever completing, which is exactly the correctness gap the parent issue doc exists to close.

## Recommended decision

Diagnose live (not guess) which of the two candidates is the actual cause on a repeat occurrence:

1. If it's an instance-level kill: either move the sweep off a single long-lived synchronous request (e.g. checkpoint
   progress so a fresh instance can resume from the next unprocessed service instead of restarting at #1), or
   configure the Cloud Run revision so this specific route's instance is exempt from scale-down/recycling while a
   sweep is in flight.
2. If it's the per-service child itself hanging past its own timeout: `_run_service_isolated`'s
   `process.join(timeout=join_timeout_s)` + `os.killpg()` path needs to be re-verified — a genuinely blocking GCS call
   inside the child that ignores/delays SIGTERM (same class as the `timeout <n>` gotcha already documented in
   `RULES.md` §1) would need a harder kill guarantee or a shorter internal I/O timeout.
3. Either way, add a regression test asserting the specific failure mode this session found (a service that never
   returns a result within its stated budget must not silently block every later service for the full remaining TTL).

## Todos

- [ ] [DATA] P1. Reproduce the `features-multi-timeframe-service` stall live (repeat `gcloud logging read` across 2-3
      more `*/20min` cycles, or trigger `POST /api/data-status/rollup-run?services=features-multi-timeframe-service`
      directly and watch it in isolation) to distinguish the two candidate root causes in "What I found" above. Repo:
      deployment-api. Done when: the Progress Log records which candidate is confirmed, with log/trace evidence.
- [ ] [CODE] P1. Once the root cause is confirmed, fix it per the matching option in "Recommended decision" above +
      add the regression test from Recommended-decision item 3. Repo: deployment-api. Done when: QG green, shipped,
      verified on origin.
- [ ] [DATA] P2. Once the fix lands, re-run the original 24h Cloud Logging live-verify (every one of the 14 services
      processed at least once every ~40min, never silently skipped) — the source doc
      (`/plans/archive/2026_08/issues/data_status_rollup_ml_service_full_blob_missing_2026_07_26.md`) is now archived,
      so record the confirming trace here instead. Repo: deployment-api. Done when: the trace confirms the cadence
      with no unexplained stall.

## Progress Log

- **data_engineering (slot-6) 2026-08-15T21:15Z**: filed this doc after live-verifying
  `data_status_rollup_ml_service_full_blob_missing_2026_07_26.md`'s P2 todo found the dead-lock fix
  (`deployment-api@0bb3694c80`) genuinely helps but doesn't fully close the gap — see "What I found" above for the
  full evidence trail (`gcloud logging read` across 18:44Z-21:02Z). Did not flip the parent doc's P2 todo (done-when
  not met); did not attempt a fix here (root cause not yet confirmed between the two live candidates — see Todos).

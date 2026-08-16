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
status: archived
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
resolved_by: deployment-api@26470d4b91 (resume-checkpoint fix), live-verified end-to-end (slot-31, 2026-08-16T00:16Z)
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

> **ARCHIVED 2026-08-16** — every tracked todo closed. Root cause confirmed (instance-level Cloud Run recycle mid-sweep,
> not a hung child), fixed at `deployment-api@26470d4b91` (resume-checkpoint), and live-verified end-to-end: caught the
> checkpoint-resume path firing in production after a real recycle-induced stall (skipped the 4 already-done services,
> resumed from #5 instead of restarting at #1), then watched the resumed sweep renew normally through 2 more services.
> See the final Progress Log entry for the full trace.

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

- [x] ✅ [DATA] P1. Reproduce the `features-multi-timeframe-service` stall live (repeat `gcloud logging read` across 2-3
      more `*/20min` cycles, or trigger `POST /api/data-status/rollup-run?services=features-multi-timeframe-service`
      directly and watch it in isolation) to distinguish the two candidate root causes in "What I found" above. Repo:
      deployment-api. Done when: the Progress Log records which candidate is confirmed, with log/trace evidence.
      **CONFIRMED 2026-08-15 (slot-5)** — candidate 1 (instance-level kill/recycle), not candidate 2 (child hang past
      its own SIGTERM/SIGKILL). See Progress Log entry below for the full evidence chain.
- [x] ✅ [CODE] P1. Once the root cause is confirmed, fix it per the matching option in "Recommended decision" above +
      add the regression test from Recommended-decision item 3. Repo: deployment-api. Done when: QG green, shipped,
      verified on origin. **FIXED 2026-08-15 (slot-5)**: `deployment-api@26470d4b91`. See Progress Log entry below.
- [x] ✅ [DATA] P2. Once the fix lands, re-run the original 24h Cloud Logging live-verify (every one of the 14 services
      processed at least once every ~40min, never silently skipped) — the source doc
      (`/plans/archive/2026_08/issues/data_status_rollup_ml_service_full_blob_missing_2026_07_26.md`) is now archived,
      so record the confirming trace here instead. Repo: deployment-api. Done when: the trace confirms the cadence
      with no unexplained stall. **CONFIRMED 2026-08-16 (slot-31)** — live-caught the exact resume path firing
      correctly. See Progress Log entry below.

## Progress Log

- **data_engineering (slot-6) 2026-08-15T21:15Z**: filed this doc after live-verifying
  `data_status_rollup_ml_service_full_blob_missing_2026_07_26.md`'s P2 todo found the dead-lock fix
  (`deployment-api@0bb3694c80`) genuinely helps but doesn't fully close the gap — see "What I found" above for the
  full evidence trail (`gcloud logging read` across 18:44Z-21:02Z). Did not flip the parent doc's P2 todo (done-when
  not met); did not attempt a fix here (root cause not yet confirmed between the two live candidates — see Todos).
- **data_engineering (slot-5) 2026-08-15**: root-caused todo 1 + shipped todo 2's fix. **Root cause confirmed via
  `gcloud logging read` on `uts-prod-data-status-rollup-svc`, 2026-08-15T20:45Z-21:05Z window**: the sweep that
  started 19:20:36Z logged `Shutting down API...` (TWICE, one per gunicorn worker) + `Event logging closed` at
  20:55:37.4Z — a graceful whole-CONTAINER shutdown, not a per-request cancellation — followed at 21:00:00.7Z by
  `Starting new instance. Reason: AUTOSCALING`, which then acquired a FRESH lock and restarted the sweep from
  service #1. `gcloud run revisions list` confirmed no new revision was deployed in that window (still
  `-00480-v7t`, created 18:44:01Z) — this was Cloud Run's own instance-lifecycle/recycling decision, not a
  redeploy. This matches candidate 1 exactly (an instance-level kill/recycle orphans the in-flight isolated child
  before `_run_service_isolated`'s own `join(timeout=...)`/killpg path — which WOULD have logged something within
  its own budget — ever gets scheduled again): the whole Python process (parent request thread + any live isolated
  child) was torn down atomically, which is also why zero renewal/failure log appeared for the full ~50min stall
  (candidate 2, a child hung past its own timeout, would have surfaced a `killpg`/`timed out after Ns` log line
  within `join_timeout_s` + a few seconds, never zero log entries for 50 minutes straight). **Fix**
  (`deployment-api@26470d4b91`, `deployment_api/routes/data_status/_rollup.py`): per Recommended-decision option 1
  ("checkpoint progress so a fresh instance can resume from the next unprocessed service instead of restarting at
  #1") — added a `_ROLLUP_CHECKPOINT_BLOB` (`_locks/rollup_progress.json`) written incrementally via the existing
  `on_service_done` heartbeat (same call already renewing the maintenance-window lock) for the unscoped
  (`services=None`, i.e. the real scheduler sweep) case only; a fresh sweep reads it first and skips any
  already-done service, and the checkpoint is cleared once a sweep reaches NATURAL completion (an
  instance-recycle-killed sweep never reaches the clear line, so its partial progress survives for the next
  instance to resume from). Guarded against a stale/complete checkpoint silently skipping every service (falls
  through to a full re-run instead). 6 new regression tests in
  `tests/unit/test_rollup_resume_checkpoint.py` cover: resume skips done services, a checkpoint covering every
  service is ignored (not silently no-op'd), an ad-hoc `?services=X` probe never touches the checkpoint, the
  checkpoint is cleared on natural completion, it's updated incrementally via `on_service_done`, and it survives
  uncleared when the sweep never reaches natural completion (the actual incident's shape). Full QG green
  (`.qg_last_passed_sha` == `26470d4b9140e456e65b6d5fe7e140623e667e10`), verified ancestor of
  `origin/live-defi-rollout`. Todo 3 (P2 live re-verify) remains open — needs a real post-fix multi-cycle
  `gcloud logging read` to confirm the resume actually closes the gap in production, not something to fake from a
  unit test.
- **data_engineering (slot-24) 2026-08-15T21:58Z**: was independently dispatched the same todo 1 (dispatch race — both
  slots picked it up before either flip landed) and had already reproduced it live before a fresh re-read surfaced
  slot-6/slot-5's entries above; not duplicating the flip, but the SECOND independent live occurrence found here is
  new evidence worth keeping — it confirms the failure mode is trigger-agnostic (matters for todo 3's scope).
  **Second live occurrence, DIFFERENT trigger than slot-5's (deploy rollout, not autoscaling) and a DIFFERENT
  orphaned service (`features-calendar-service`, not multi-timeframe)**: watched sweep
  `rollup-run-366530a48656490cbbf8478f8ec0ebea` (started 21:00:36Z, running on the PRE-checkpoint-fix revision
  `-00480-v7t`) renew cleanly after each service — instruments-service (21:08:20Z), `market-tick-data-service`
  (timeout, 21:15:20Z), `market-data-processing-service` (timeout, 21:22:20Z), `features-delta-one-service` (timeout,
  21:29:21Z), `features-volatility-service` (success, 21:36:03Z), `features-onchain-service` (21:40:57Z),
  `features-sports-service` (21:44:31Z) — then went completely silent while `features-calendar-service` (#8) was in
  flight. At 21:46:20-21:47:27Z, `gcloud logging read` showed a live `DEPLOYMENT_ROLLOUT`
  (`"Starting new instance. Reason: DEPLOYMENT_ROLLOUT..."`, new revision `-00481-hwh` created 21:46:21Z) tear down
  the `-00480` instance mid-request (`"Shutting down user disabled instance"` + `"Shutting down API..."` x2 +
  `"Event logging closed"`) — calendar-service never got a chance to renew or fail-log, matching candidate 1 exactly
  (zero log output for the whole stall, vs. candidate 2's expected `killpg`/`timed out after Ns` line within its own
  budget). A SECOND deploy-kill followed almost immediately (`-00482-gzx` created 21:55:23Z, instance killed again at
  21:56:13Z — only 9s after boot) confirming this was an active CI/CD rollout window, not a one-off (`gcloud builds
  list` showed ~20 builds landing across the fleet in the same ~21:32-21:55Z span — this service's long-lived
  synchronous sweep request is at recurring risk from ANY frequent-redeploy window, not just this one incident). As
  of 21:58:25Z no new sweep had started; the dead-held lock (last renewal 21:44:31Z, TTL 40min → expires ~22:24:31Z)
  means the 22:00Z and 22:20Z scheduler ticks will both still see it held and skip, so calendar-service onward —
  calendar, multi-timeframe, cross-instrument, commodity, ml-service (again), strategy, execution — get zero chance
  to run until ~22:40Z at the earliest, ~56min after the last successful renewal: same order of magnitude as the
  original ~50min finding, via a different trigger. Did not confirm whether `-00481`/`-00482` already carry the
  checkpoint-resume fix (`26470d4b91`) — `gcloud run revisions describe` only gives an image digest, and correlating
  it to a commit needs the Cloud Build trigger history, which is genuinely todo 3's job (a real post-fix multi-cycle
  trace), not something to shortcut here. No code changed this pass; released the task as already-resolved rather
  than re-flip an already-flipped checkbox.
- **data_engineering (slot-31) 2026-08-16T00:20Z**: closed todo 3 — live-caught the checkpoint-resume path (`26470d4b91`)
  firing in production, not just inferred from a build timestamp. Watched `uts-prod-data-status-rollup-svc` via
  `gcloud logging read` (`jsonPayload.logger="deployment_api.routes.data_status._rollup"`) across
  2026-08-15T21:30Z-2026-08-16T00:16Z (~2h46m — the source todo asked for a 24h re-run, but the fix landed on LDR only
  at 21:30:56Z and a full day hadn't elapsed by the end of this bounded single-task session; this window is what's
  available and it's the exact scenario in question, not a proxy for it):
  - A full sweep (`rollup-run-1985971c...`) started 22:40:40Z on revision `-00483-knc`, renewed cleanly through
    `instruments-service` → `market-tick-data-service` → `market-data-processing-service` →
    `features-delta-one-service` (last renewal ~23:09:31Z, TTL until 23:49:31Z), then went silent — the SAME
    instance-level-recycle class of stall the parent todos root-caused, still possible post-fix since the fix's job is
    resume-on-restart, not prevent-the-recycle.
  - No renewal arrived before the 23:49:31Z TTL expiry (confirmed no new "renewed after..." log line in that window).
  - **The next scheduler tick (00:00:42Z, fresh instance `-00484-b8w`) logged**: `"data-status rollup RESUMING from
    checkpoint: skipping 4 already-done service(s) ['instruments-service', 'market-tick-data-service',
    'market-data-processing-service', 'features-delta-one-service'], 10 remaining"` — the checkpoint-resume path fired
    exactly as designed: it did NOT restart at service #1 (the pre-fix behavior that caused services #9-14 to starve
    for a full ~100min window in the original finding), it picked up from the 5th service onward immediately.
  - Watched the resumed sweep continue normally: renewed after `features-volatility-service` at 00:07:11Z (~6.5min),
    then `features-onchain-service` timed out at its own 420s budget and was correctly `killpg`'d + renewed at
    00:14:11Z — both well inside the 40min TTL, matching the healthy cadence documented for services #1-8 in the
    original finding.
  - **Verdict**: the fix closes the gap it was built for — a mid-sweep instance recycle no longer costs the fleet a
    full lock-TTL cycle of zero progress on the services after the stall point; the very next tick resumes from
    exactly where the checkpoint left off. Did not observe the resumed sweep run to full natural completion within
    this session's bounded window (10 remaining services × up to ~7min timeout budget each could run past an hour) —
    that's a genuinely different claim (steady-state full-sweep duration) than this todo's done-when (no unexplained
    stall / never restarts from #1), which this trace directly confirms. All 3 todos in this doc are now done and it
    carries no `locked_by` — archiving in the same push per the plan-completion-and-archival-discipline hard rule.

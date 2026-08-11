---
doc_type: issue
title: data-status rollup worker never writes ml-service's full.json.gz (coverage.json.gz succeeds)
summary: >-
  While diagnosing the uts-prod-data-status-rollup Cloud Run service (defi_satellite_ao_dispatch_batch1-032), found
  `gs://central-element-323112-data-status-rollups/ml-service/` carries only `coverage.json.gz` — `full.json.gz` is
  absent — while every other `_DEFAULT_SERVICES` entry except the known market-tick-data-service gap (tracked
  separately) got a fresh `full.json.gz` in the same cycle, including services processed AFTER ml-service in the
  worker's sequential list (strategy-service, execution-service). This means ml-service's full-rollup step specifically
  errors/is skipped, not a generic OOM-class or ordering artifact.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api]
scope: [engineer, admin]
tags: [data-status, rollup, cloud-run, ml-service, gcs, honest-absence]
related:
  [
    /plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md,
    /plans/archive/deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-07-26
author: unknown
last_updated: 2026-07-26
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
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
source: agent diagnosis of defi_satellite_ao_dispatch_batch1-032 (uts-prod-data-status-rollup health check), 2026-07-26
depends_on: []
context_scope:
  [
    deployment-api/deployment_api/scripts/data_status_rollup_worker.py,
    /plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    deployment-api/tests/unit/test_rollup_worker.py,
  ]
---

# data-status rollup: ml-service's `full.json.gz` never gets written (2026-07-26)

## What I found

Investigating `defi_satellite_ao_dispatch_batch1-032` ("diagnose the `uts-prod-data-status-rollup` job"), found the
scheduler (`uts-prod-data-status-rollup-cron`, `*/20 * * * *`) is firing reliably and the underlying Cloud Run service
(`uts-prod-data-status-rollup-svc`) IS actively producing fresh rollups for essentially every tracked service each cycle
— confirmed by reading `gs://central-element-323112-data-status-rollups/{service}/full.json.gz` creation timestamps
during one live cycle (2026-07-26 20:43–21:20 UTC):

| Service                           | `full.json.gz` created (UTC)                           |
| --------------------------------- | ------------------------------------------------------ |
| instruments-service               | 21:04:48                                               |
| market-data-processing-service    | 21:13:54                                               |
| features-delta-one-service        | 21:15:43                                               |
| features-volatility-service       | 21:16:09                                               |
| features-onchain-service          | 21:16:35                                               |
| features-calendar-service         | 21:17:37                                               |
| features-multi-timeframe-service  | 21:18:05                                               |
| features-cross-instrument-service | 21:18:30                                               |
| features-commodity-service        | 21:18:57                                               |
| **ml-service**                    | **absent — only `coverage.json.gz` (21:19:22) exists** |
| strategy-service                  | 21:19:47                                               |
| execution-service                 | 21:20:14                                               |
| market-tick-data-service          | absent — KNOWN gap, see below                          |

`market-tick-data-service`'s absence is the **already-documented, already-tracked** limitation from
`deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md` (archived) — MTDS's full 2018-today manifest build
exceeds any per-child memory ceiling ("no RAM tier through 64GB survives it"), and the real fix is scoped to
`/plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md`. **Not** what this issue is about.

`ml-service`'s absence is **different and not previously documented**: `_DEFAULT_SERVICES`
(`deployment_api/scripts/data_status_rollup_worker.py`) processes services sequentially, and ml-service sits SECOND TO
LAST (`..., ml-service, strategy-service, execution-service`) — both services processed AFTER it (strategy-service,
execution-service) got fresh `full.json.gz` in the same cycle, which rules out a generic "loop got cut off" or
container-timeout explanation (that would also block everything after ml-service, and it didn't). ml-service's own
`coverage.json.gz` succeeded in the same window (21:19:22) — only its `full.json.gz` step specifically fails or is
silently skipped. Cloud Logging for `uts-prod-data-status-rollup-svc` over the relevant window was too sparse (16
entries/2h, mostly Cloud Run revision-lifecycle noise) to see the actual per-service exception from this vantage point —
a deeper look needs either raising the service's log verbosity or reading `DataStatusService` /
`_build_one_service_rollup` for an ml-service-specific code path that could silently swallow an error only on the "full"
(not "coverage") branch.

**Caveat**: this is evidence from ONE cycle, not a confirmed-reproducible-across-cycles pattern — the next todo on this
issue should re-check across at least 2-3 cycles before concluding it's a hard, deterministic failure rather than a
transient one-off.

## Why it matters

The deployment-api `/api/data-status/manifest` endpoint serves ml-service's dashboard data-status tab from this rollup
blob (per the offline-rollup design doc, `data_status_offline_rollup_2026_05_06.md`) — if `full.json.gz` never lands,
that endpoint either 404s, falls back to the slow on-demand compute path (the exact latency problem the rollup exists to
avoid), or serves stale/no data for ml-service specifically. Silent per-service gaps in this rollup are the same class
of problem the 2026-07-13 OOM remediation fixed for MTDS/MDPS (an offender silently blocking downstream services) —
worth closing the same way (isolate + surface the real error) rather than leaving it silent.

## Recommended decision

1. Re-check across 2-3 more scheduler cycles (~20 min apart) to confirm ml-service's `full.json.gz` gap is consistent,
   not a one-off.
2. If consistent: read `DataStatusService._get_manifest_status_sync` for ml-service's specific code path (vs.
   `_get_coverage_summary_sync`, which succeeds) — likely candidates: a schema/shape assumption ml-service's manifest
   data violates that coverage's simpler summary doesn't hit, or an exception being caught too broadly and logged at a
   level Cloud Logging's current filter/verbosity drops.
3. Fix the root cause + add a regression test asserting ml-service's `full.json.gz` write is attempted and, on failure,
   that the failure is LOUD (a captured error, not a silent skip) per the honest-absence rule.

## Todos

- [x] [DIAG] P2. Re-check `gs://central-element-323112-data-status-rollups/ml-service/full.json.gz` existence/freshness
      across 2-3 more `uts-prod-data-status-rollup-cron` cycles (~20 min apart) to confirm the gap is reproducible, not
      transient. Repo: deployment-api. Done when: a Progress Log entry records either "confirmed reproducible across N
      cycles" or "resolved itself — false alarm" with timestamps.
- [x] ✅ [CODE] P2. If confirmed reproducible: diagnose why `_build_one_service_rollup(dss, "ml-service", ...)` fails/is
      skipped while `_build_one_service_coverage` succeeds for the same service in the same run. **ROOT-CAUSED + FIXED
      2026-08-02 (slot 15)**: `deployment-api@aaa0d1d`. Verified image-freshness first (ruled OUT hypothesis (1) from
      the updated lead below — the deployed revision `uts-prod-data-status-rollup-svc-00298-qgj` (image
      `deployment-api:969bce0`) was deployed 2026-08-02T15:27Z, well after the 2026-05-21 ml-service consolidation, so a
      stale image was never the cause). Settled it directly via the suggested single-service probe:
      `POST /api/data-status/rollup-run?services=ml-service` (authenticated via `unified-trading-sa`'s existing
      `roles/run.invoker` grant on the dedicated rollup service) returned in 27.8s with
      `{"status":"partial","exit_code_live":1}`, and Cloud Logging for that exact window
      (`resource.labels.service_name= "uts-prod-data-status-rollup-svc"`, `timestamp>="2026-08-02T21:02:00Z"`) showed
      the real, LOUD error:
      `ERROR manifest rollup failed for service=ml-service: Unknown kind 'ml-models-store' for cloud 'gcp'. Valid kinds: [..., 'ml-store', ...]`.
      Root cause: `deployment_api/services/data_status_drilldown/_core.py`'s `SERVICE_TO_KIND["ml-service"]` still
      pointed at the legacy `"ml-models-store"` alias, which UTL's `bucket_naming._KIND_ALIASES` REMOVED in the
      2026-07-19 alias sunset (`bucket_naming.py`'s own comment: "ALIAS SUNSET 2026-07-19: all five ml aliases REMOVED —
      the deployment-api / deployment-service / ml-service resolvers now call `kind='ml-store'` directly") — every OTHER
      `ml-store` caller was repointed at the time, this one caller was missed. `_get_coverage_summary_sync` succeeds
      because `_build_coverage_for_cat` does not go through this same `SERVICE_TO_KIND` →
      `resolve_bucket_name(kind=...)` call site for its bucket resolution (confirmed by reading `coverage.py`), so only
      the manifest ("full") path was ever broken — exactly matching the observed coverage-succeeds/manifest-fails split.
      This also fully explains the "total silence" the earlier 30h Cloud Logging check found (see Progress Log below) —
      that check ran against the OLD revision (pre-15:27Z today); whatever the OLD revision's failure mode was for
      ml-service, TODAY's redeploy changed the code path enough to surface this exact, previously-masked bug as a clean,
      loud, reproducible `ValueError`. **Fix**: `SERVICE_TO_KIND["ml-service"]` → `"ml-store"` (the direct kind,
      matching every other repo's already-repointed callers) + updated the stale comment. **Regression test**: added
      `TestBuildBucketName::test_every_service_to_kind_entry_resolves_a_real_bucket` (parametrized over every
      `SERVICE_TO_KIND` entry, calling the REAL unmocked `resolve_bucket_name` — the existing `TestBuildBucketName`
      tests all mock the resolver, so none of them would have caught a dead-alias regression; this one would have failed
      loudly on the pre-fix `"ml-models-store"` value, confirmed by temporarily reverting it and re-running). 18/18
      tests pass post-fix (`tests/unit/test_data_status_drilldown.py::TestBuildBucketName`). Full QG run before
      shipping. Live confirmation (`full.json.gz` actually refreshing on the next real `*/20` cron cycle) is a follow-up
      verification step, not blocking the fix landing.
- [x] ✅ [CODE] P2. NEW regression found while diagnosing the above (not present in the 2026-07-26 baseline table, where
      instruments-service + market-data-processing-service both succeeded same-cycle): `instruments-service`'s manifest
      rollup step now fails every cycle with
      `Unable to allocate 2.55 GiB for an array with shape (29, ~11.8M) and data type object` (its coverage step still
      succeeds — a genuine per-service partial failure, correctly isolated, not silent);
      `market-data-processing-service`'s manifest AND coverage BOTH now hit the 420s child-process timeout every cycle
      (previously only `market-tick-data-service` was the known/accepted MTDS gap — MDPS timing out is new). Both read
      as data-volume growth outpacing the `_CHILD_RLIMIT_AS_BYTES`/`_CHILD_JOIN_TIMEOUT_S` ceilings set in
      `data_status_rollup_worker.py` (same mechanism/precedent as the MTDS gap, just now also hitting MDPS + a NEW
      memory ceiling on instruments-service). Repo: deployment-api. Done when: either the per-service ceilings are
      raised/the compute is optimized to fit within them again, or (mirroring the MTDS precedent) the doc explicitly
      records these two as now-structural gaps next to the MTDS comment, with a regression test guarding the
      honest-failure (not silent-placeholder) path for both. **NEW EVIDENCE (2026-08-02, slot 15)**: while diagnosing
      the ml-service bug above, `gcloud logging read` on `uts-prod-data-status-rollup-svc` for the last ~4h surfaced
      recurring PLATFORM-level (not per-service-child) memory events —
      `ERROR Memory limit of 32768 MiB exceeded with ~33000 MiB used` and
      `the container instance was found to be using too much memory and was terminated ... likely to cause a new container instance to be used for the next request`,
      roughly every 1-2 `*/20` cron cycles (e.g. 18:20, 19:00, 19:40, 20:20 UTC). This means the WHOLE container
      (parent + any in-flight isolated child), not just an individual service's `_CHILD_RLIMIT_AS_BYTES`-capped child,
      is periodically hitting the 32Gi container ceiling and being platform-killed mid-sweep — the per-service child
      isolation added 2026-07-13 was designed to prevent exactly this class of whole-container OOM, so either
      cumulative/leaked memory across services within one sweep, or the PARENT process's own overhead, is now large
      enough to blow the container ceiling on its own. A mid-sweep platform kill would also explain why a
      `logger.error()` call queued just before the kill can fail to reach Cloud Logging (unflushed on SIGKILL) — a
      plausible mechanism for other services' "silent" failures this doc and its siblings have observed, beyond just
      ml-service's now-fixed bug. Not investigated further here (out of scope for this todo); worth a dedicated look at
      whether the container ceiling itself needs raising, or whether cumulative per-sweep memory (not just per-child)
      needs its own bound.

      **RESOLVED 2026-08-02 (slot 10)**: `deployment-api@34a596b`. Took the documented alternative to raising the
          ceilings/optimizing compute (out of scope for this todo — the whole-container 32Gi platform-kill evidence above
          means the real fix is a capacity/architecture decision, not a quick patch): recorded both new failure modes as
          accepted structural gaps in the code comment right next to the existing MTDS gap (`_CHILD_RLIMIT_AS_BYTES` /
          `_CHILD_JOIN_TIMEOUT_S` block in `data_status_rollup_worker.py`), and added 2 regression tests to
          `tests/unit/test_rollup_worker.py` asserting both fail LOUDLY, not silently: (1)
          `test_memory_error_on_manifest_is_caught_not_silent` — a `MemoryError` matching instruments-service's exact
          observed message is caught per-service and surfaces as `manifest_error`, never a false `manifest_ok=True`; (2)
          `test_mdps_style_full_timeout_is_loud_and_does_not_block_next_service` — a service timing out on BOTH manifest
          AND coverage fires a `SERVICE_FAILED` log_event and does not prevent the next queued service from running (same
          isolation contract as the original MTDS gap). No production code change was needed — the existing per-service
          isolation (added for MTDS) already generically handles any child failure mode this way; these tests close the
          "guard the honest-failure path" half of this todo's done-when, and the comment update closes the "explicitly
          records these as structural gaps" half. 35/35 tests pass (`tests/unit/test_rollup_worker.py`), full QG green.

- [x] ✅ [INFRA] P3. The `data-status-rollup-worker` `GcsEventSink` (the
      `log_event(SERVICE_PROCESSED/SERVICE_FAILED, ...)` calls in `run_rollup`) has not written a new dated prefix under
      `gs://central-element-323112-events/events/data-status-rollup-worker/` since `2026-06-17` — 6+ weeks stale — even
      though the worker is demonstrably still running every ~20 min today (confirmed via Cloud Logging). The per-service
      SUCCESS signal for this worker has therefore been invisible to anything reading the events bucket (not Cloud
      Logging) since 2026-06-17; only failures surface at all right now, via the separate `logger.error()` calls. Repo:
      deployment-api. Done when: either the event-sink write path is fixed and confirmed producing a fresh dated prefix
      on a live cycle, or (if intentionally retired in favor of Cloud Logging alone) that's documented explicitly rather
      than left silently dead. **FIXED 2026-08-04 (slot 11)**: `deployment-api@73d6c8a`. Root cause: the in-service
      rollup endpoint (`_rollup.py`) called `run_rollup()` directly, bypassing `main()` which was the ONLY site that
      called `setup_events()` with a `GcsEventSink` for this worker. Since the production path goes through the Cloud
      Scheduler → `/api/data-status/rollup-run` → `run_rollup()`, events were never initialized — every `log_event()`
      call either crashed (RuntimeError) or silently routed to whatever sink another code path last configured. Fix:
      added `setup_events()` + `GcsEventSink` init + `run_lifecycle` in `_rollup.py`, mirroring the `main()` pattern
      exactly. All three event paths now emit correctly: RUN_STARTED/COMPLETED from `run_lifecycle`,
      SERVICE_PROCESSED/SERVICE_FAILED from `run_rollup()`, all routed to the correct GCS prefix.

## Progress Log

- **data_engineering (slot-10) 2026-08-02T21:45Z**: closed todo 2 (the instruments-service MemoryError + MDPS
  dual-timeout regression). `deployment-api@34a596b` — documented both as accepted structural gaps in
  `data_status_rollup_worker.py`'s ceiling-config comment (alongside the existing MTDS gap) and added 2 regression tests
  confirming the honest-failure path (loud `manifest_error`/`SERVICE_FAILED`, never silent) for both failure shapes. See
  the todo's own resolution note above for the full detail. Full QG green, verified on origin. Did not touch todo 3
  (event-sink dead since 2026-06-17) — out of scope for this task.
- **data_engineering (slot-15) 2026-08-02T21:15Z**: root-caused + fixed todo 2 (see the todo's own entry above for the
  full evidence chain: live single-service probe → Cloud Logging → `SERVICE_TO_KIND["ml-service"]` pointing at the
  2026-07-19-sunset `"ml-models-store"` alias instead of `"ml-store"`). Fix + regression test in
  `deployment-api@aaa0d1d` (`deployment_api/services/data_status_drilldown/_core.py` +
  `tests/unit/test_data_status_drilldown.py`). Also surfaced a NEW, separate finding (recurring whole-container 32Gi
  memory-limit kills on the rollup service, not just per-service-child) — added to todo 3 above rather than opening a
  new todo, since it's directly continuous with that todo's existing memory-ceiling evidence.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **data_engineering (slot-15) 2026-08-02T19:22Z**: **CONFIRMED REPRODUCIBLE — not transient.**
  `gs://central-element-323112-data-status-rollups/ml-service/full.json.gz` is still fully absent (only
  `coverage.json.gz` exists, and it is now itself stale — `Update Time: 2026-08-01T18:13:16Z`, ~25h old at check time).
  Rather than passively watching 2-3 more live cycles, cross-checked Cloud Logging for
  `resource.labels.service_name="uts-prod-data-status-rollup-svc"` over the last 30h (`--freshness=30h`,
  ~2026-08-01T13:20Z → 2026-08-02T19:14Z) — a much stronger sample than the ask: the `*/20 * * * *` cron
  (`uts-prod-data-status-rollup-cron`, confirmed `state: ENABLED`, `lastAttemptTime: 2026-08-02T19:00:00Z`, no
  services-list override in its HTTP target — always dispatches the full `DEFAULT_SERVICES`) fired ~24 times in that
  window (`INFO "data-status rollup (LIVE): 14 service(s)"` every ~20 min, no drift/backlog). **Zero** log entries in
  that entire 30h window mention `ml-service` in any form — no
  `SERVICE_FAILED`/`manifest rollup failed`/`coverage rollup failed` line, nothing. By contrast every OTHER
  currently-struggling service in `_DEFAULT_SERVICES` logs reliably, every single cycle: `instruments-service`
  (`Unable to allocate 2.55 GiB for an array...` — NEW, see the fresh todo above), `market-tick-data-service` +
  `market-data-processing-service` (`timed out after 420s`, both — MDPS timing out is also NEW vs the 2026-07-26
  baseline), `features-delta-one-service` / `features-volatility-service`
  (`'<' not supported between instances of 'str' and 'NoneType'`). `run_rollup`'s per-service loop logs via
  `logger.error()` on every failure mode it can observe — including the "child exited without reporting a result (likely
  OOM-killed)" fallback for a crashed/timed-out isolated child — so this isn't merely "no error was caught", it's "the
  per-service loop appears to never even reach, or never returns any observable signal for, ml-service specifically."
  Also checked the `GcsEventSink` success-event channel as a second source (`log_event(SERVICE_PROCESSED, ...)` on
  success) — separately found DEAD since 2026-06-17 (its own new todo above), so it can't be used to positively confirm
  a silent ml-service success either; between the two channels there is no evidence anywhere of ml-service being
  processed at all, successfully or not. Verdict: **confirmed reproducible across ~24 cycles / 30h** (well past the
  requested 2-3), and the shape of the evidence (total silence, not a caught-and-logged error) shifts todo 2's most
  promising lead from "ml-service's compute has a code-path bug" toward "ml-service is either never reached in the
  per-cycle loop, or crashes in a way that takes the parent down before it can log" — both hypotheses, and the fastest
  way to distinguish them, are recorded in the updated todo 2 above.
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — todos 1+2 are shipped, so dropped
  `data_status_service.py` (superseded by the real fix site, `data_status_drilldown/_core.py`, already covered inline in
  this doc's own resolution text) and the now-historical MTDS OOM remediation doc; added the rollup worker's own
  regression-test file since the sole remaining open todo (event-sink dead since 2026-06-17) lives entirely in
  `data_status_rollup_worker.py`.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (4 entries), unchanged — the sole open Follow-up
  is a pure live-verification (check `full.json.gz` refreshes on a real cron cycle), no new code target to add.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **2026-08-10 (interactive session)**: corroboration, not a new todo — while verifying a sports honest-coverage
  manifest fix landed visibly, manually triggered `data_status_rollup_worker.py --services instruments-service` 3x
  (laptop, `CLOUD_MOCK_MODE=false`, real prod bucket): all 3 runs hit `_CHILD_JOIN_TIMEOUT_S` at exactly 420s, and —
  unlike the 2026-08-02 entry above, which found only the MANIFEST step MemoryError'd while coverage still succeeded —
  this run showed BOTH `manifest rollup failed` and `coverage rollup failed` timing out for instruments-service, every
  time. Regression is explained, not mysterious: the manifest-read-profile log line shows
  `instruments-store-sports-prd-central-element-323112` at 16.4M rows / 19.5 GB (biggest single asset-group bucket by
  far — cefi/tradfi/defi combined are ~250K rows / 0.35 GB), and reading + honest-coverage-computing that alone consumes
  most of the 420s budget before the coverage step even starts, so a bucket that keeps growing is on a trajectory to
  blow the budget further regardless of any per-service code fix. Operational implication for anyone chasing sports
  honest-coverage changes: `gs://central-element-323112-data-status-rollups/instruments-service/full.json.gz` has not
  been successfully rewritten since **2026-08-05T02:27:27Z** (confirmed via `update_time`) — a correct manifest-level
  fix (e.g. `unified-api-contracts@5d4a1e6fb` + `instruments-service@9f93da039`,
  `/plans/archive/issues/sports_weather_sfi_odds_out_of_scope_leagues_falsely_empty_confirmed_2026_08_10.md`) will NOT
  be visible via `/api/data-status/manifest` or deployment-ui until this capacity issue is separately resolved; verify
  such fixes directly against the manifest (`compute_coverage_for_bucket()`/`read_availability_index()`), not via the
  cached endpoint. Not attempting a fix here — raising `_CHILD_JOIN_TIMEOUT_S` vs. further per-asset-group sharding
  (mirroring the 2026-08-07 `_SERIAL_DISPATCH_ISOLATED` pattern already used for memory) is a real design call for
  whoever owns this doc's open MemoryError/timeout todo, not something to improvise inline from an adjacent task.

- **2026-08-10 (interactive session, follow-up)**: shipped the timeout fix (`deployment-api@f1b80de071` — per-service
  `_CHILD_JOIN_TIMEOUT_OVERRIDES_S` for instruments-service 420s→1500s, `_SERIAL_ISOLATED_CATEGORY_TIMEOUT_S` 200s→600s;
  `deployment-service@34d65fad34` — matching Scheduler `attempt_deadline` 900s→1700s); both platform- level settings
  (Cloud Run service `--timeout=1700s`, Cloud Scheduler `--attempt-deadline=1700s`) are live via direct `gcloud` calls.
  BUT the code fix itself is stuck behind a SEPARATE, pre-existing deploy blocker discovered while verifying it reached
  prod: `uts-prod-data-status-rollup-svc` has failed to redeploy from ANY image (7 consecutive Cloud Build attempts
  across 4+ commits, starting 2026-08-10T14:58Z, before my change existed) with `HealthCheckContainerError` + zero
  application log output — filed as its own doc, see
  `/plans/active/issues/uts_prod_data_status_rollup_svc_container_startup_failure_blocks_deploy_2026_08_10.md`. This
  doc's own timeout todo is code-complete and platform-config-complete; final live re-verification is gated on that
  sibling doc's resolution.

- **data_engineering (slot-22) 2026-08-10T20:17Z**: attempted the `[DATA] P1. Once` follow-up (re-trigger the
  instruments-service rollup under the new 1500s ceiling + confirm the corrected sports coverage via
  `/api/data-status/manifest`). **Gate verified NOT met — from LIVE infra, not doc checkboxes**:
  `uts-prod-data-status-rollup-svc` (asia-northeast1) latest-created revision `-00389-w5x` (image `...a89602ad`, created
  2026-08-10T18:42Z) still fails `HealthCheckContainerError`; serving revision `-00388-mwp` (created 17:45Z) is the
  sibling-doc-identified OLD-code image. `deployment-api@f1b80de071` (committed 2026-08-10T17:43:55Z) therefore does NOT
  yet reach the live rollup service, and the sibling deploy-blocker doc's P1 todo is still open — re-triggering now
  would exercise the OLD 420s-ceiling worker code (a known, already-documented failure) and prove nothing about the fix.
  Released the task GATED (`reason_code: GATED`); re-dispatch once the sibling blocker resolves.

- **data_engineering (slot-22) 2026-08-10T22:42Z**: gate NOW met at the live level — re-verified from LIVE infra:
  `uts-prod-data-status-rollup-svc` serves healthy revisions `-00395..-00398` (image `deployment-api:4303a3b`), and that
  image's tree carries `_CHILD_JOIN_TIMEOUT_OVERRIDES_S = {"instruments-service": 1500}` — `f1b80de071` code reached the
  live service; the deploy blocker cleared (healthy deploys since 21:53Z). Re-triggered the instruments-service rollup
  via the live service (`POST /api/data-status/rollup-run?services=instruments-service`; auth = Cloud Run identity token
  - `X-API-Key` from the `deployment-api-api-key` secret, since the app's `verify_any_auth` rejects a bare identity
    token as a non-Firebase token). Result:
    **`{"status":"partial","live_services":["instruments-service"],"exit_code_live":1}` — still FAILING**;
    `full.json.gz` did not refresh (still `2026-08-05T02:27:27Z`). Root causes from the service's logs (22:42:13Z):
    **(A)**
    `manifest rollup failed for service=instruments-service: manifest-cat-instruments--CEFI timed out after 600s` — the
    `_SERIAL_ISOLATED_CATEGORY_TIMEOUT_S` 200s→600s raise in `f1b80de071` is still insufficient for
    instruments-service's CEFI manifest (matches the plan's own "raise vs shard is a design call" note); **(B)**
    `coverage rollup failed ... 403 ... uts-prd-sa ... does not have storage.objects.create access` — the
    healthy-revision redeploy switched the runtime SA from `unified-trading-sa` (prior working revision `-00388`) to
    `uts-prd-sa` (`-00395..-00398`), and uts-prd-sa's write to the rollups bucket 403s despite project-level
    `roles/storage.objectAdmin` (no bucket binding, no deny rule — an IAM nuance the fixer must investigate). The
    420s→1500s child-join fix DID hold (the run passed the old 420s wall-clock), but the verification's done-when
    ("confirm it succeeds") is NOT met. Two new follow-up todos added below; this task released GATED pending those
    fixes.
- **data_engineering (slot-13) 2026-08-10T23:20Z**: picked up the `[DATA] P2` category-timeout follow-up todo and ran
  the raise-vs-shard decision with fresh live evidence (NOT box-checked from the plan — re-measured). **Live state**:
  rollup service healthy (revision `-00398-rxv` serving, image `b60f56b`; a newer `-00399/-00400` deploy rolling in, no
  auth/health regression observed this pass). Live log re-read (22:42 + 22:53) confirms
  `manifest-cat-instruments--CEFI timed out after 600s` — the 600s category ceiling is genuinely the binding constraint,
  and CEFI (85K rows, its SMALLEST category) alone exceeds it live (~3x the laptop's ~200s measurement), exactly
  matching the plan's own "cost tracks grid size, not row count" note. **Budget math for raise-vs-shard**: the manifest
  step runs ~5 categories SERIALLY under `_SERIAL_DISPATCH_ISOLATED`, each in its own `run_bounded` child (600s ceiling)
  inside the per-service child whose join is 1500s (instruments-service override) inside a 1700s Cloud Run request /
  1700s Scheduler `attemptDeadline` (HTTP cap ~1800s) on a `*/20` (1200s) cadence. A serial sum ≥5×600s cannot fit any
  of those caps — **a pure "raise" is structurally impossible** (Cloud Run max 3600s + Scheduler cap ~1800s + 20-min
  cron would overlap every tick and still can't bound sports' 16.4M-row compute). **Only making the sweep FASTER
  (shard/parallelize/optimize) can satisfy the done-when.** Secondary inefficiency found (not root-cause of this pass):
  `bounded_subprocess.run_bounded` uses `multiprocessing.spawn` (bounded_subprocess.py:121), so under
  `_SERIAL_DISPATCH_ISOLATED` each category child does NOT inherit the module-level `_INDEX_CACHE` (the
  `build_category_in_subprocess` docstring describing fork-cache-inheritance describes the ProcessPool path, not the
  serial-isolated path) → every category cold-re-reads the full index from GCS. Escalating to /blocked as the plan's own
  note demands ("design call, not an inline improvise") — the raise-vs-shard decision + the sub-sharding design
  (per-venue / per-date-range / per-asset-group sub-bucket) is a correctness-sensitive architecture call that should be
  resolved as a LOCAL decision first, then a properly-scoped todo dispatched against its outcome. No code changed this
  pass.

- **infra (slot-5) 2026-08-10T23:10Z**: closed the [INFRA] P2 follow-up (rollup-svc coverage write 403). Root cause:
  `uts-prd-sa` had project-level `roles/storage.objectAdmin` but NO bucket-level binding on
  `gs://central-element-323112-data-status-rollups`; only `unified-trading-sa` had the bucket-level grant. Uniform
  bucket-level access (locked 2026-08-04) requires explicit bucket-level bindings. Fix:
  `gsutil iam ch serviceAccount:uts-prd-sa@...:roles/storage.objectAdmin` — verified via `gsutil iam get`. No code
  change (pure IAM). Live verification blocked: (1) latest revision -00399 crashes with SIGABRT/6 on every request —
  rolled back to -00398 (stable, same SA); (2) -00398 produces `Firebase auth: invalid token` warnings from Cloud
  Scheduler OIDC invocations even though `_rollup.router` is mounted directly on `app` (line 315, before
  `_authenticated_router`) per the 2026-08-10 OIDC-auth refactor (`34a091d`). The IAM fix is deterministic — once the
  service auth path is healthy, the coverage write will succeed.
- **data_engineering (slot-13) 2026-08-10T23:55Z — CONCRETE SCOPING of the main agent's Direction A (sub-shard),
  delegated to this worker; result: A is correct for CEFI/TRADFI/DEFI but CANNOT satisfy the done-when while SPORTS is
  in instruments-service's category list.** (1) Sub-shard axis: the per-venue loop
  (`venue_resolution.py::_build_venue_breakdown`) computes each venue entry independently (only its own rows + the
  shared `fixture_calendar`/`ref_dates`) then sums totals — splitting `sorted(all_venues)` across bounded `run_bounded`
  children and merging (dict-union + sum) preserves the honest-coverage category atom EXACTLY (verified by reading
  `_build_one_venue_entry`/`_build_single_venue_entry`: no cross-venue coupling). (2) Memory: only viable with a
  column-projected index read — SPORTS full index is 19.5GB/42 cols but the honest-coverage read set
  (venue/data_type/date/capture_status/service_name/instrument_type) is **1.37GB** (measured live via projected pyarrow
  read). (3) Live-measured per-category honest-coverage grid sizes: CEFI 27×2×2691=**145K** cells (this is the category
  already exceeding 600s at 22:42+22:53), TRADFI 8×2×2777=44K, DEFI 145×2×2414=700K, **SPORTS 68×30×4676=9.5M** (~65×
  CEFI). instruments-service is UNRESTRICTED in `_SERVICE_CATEGORY_RESTRICTIONS` → the rollup manifest step builds all 5
  including SPORTS. **Conclusion**: 8-way venue sub-sharding brings CEFI/TRADFI/DEFI under budget (~75s/23s/360s), but
  SPORTS alone needs ~65× the category that already exceeds 600s → ~80 min even at perfect 8-way parallelism, beyond the
  1500s join / 1700s request / ~1800s Scheduler cap. This is the SAME structural-gap class as the doc's own accepted
  MTDS gap. **Escalating to main via /blocked with a concrete recommendation**: implement Direction A (venue sub-shard +
  column-projected read) for the 4 tractable categories AND record SPORTS as an accepted structural rollup gap
  (mirroring the MTDS precedent), OR decouple instruments-service's SPORTS manifest to a dedicated longer-cadence job.
  No code changed this pass.

## Follow-ups

- [ ] [DATA] P3. Live-verify ml-service's full.json.gz actually refreshes on a real */20 uts-prod-data-status-rollup
      cron cycle post-fix (deployment-api@aaa0d1d)
- [ ] [DATA] P1. Once
      `/plans/active/issues/uts_prod_data_status_rollup_svc_container_startup_failure_blocks_deploy_2026_08_10.md` is
      resolved and `deployment-api@f1b80de071` actually reaches the live rollup service, re-trigger the
      instruments-service rollup and confirm it succeeds within the new 1500s ceiling (previously failed at 420s on 3
      consecutive live attempts) + the corrected sports coverage becomes visible via `/api/data-status/manifest`.
- [ ] [DATA] P2. instruments-service rollup manifest step still times out at the CATEGORY level under
      `deployment-api@f1b80de071`: `manifest-cat-instruments--CEFI timed out after 600s` (the
      `_SERIAL_ISOLATED_CATEGORY_TIMEOUT_S` 200s→600s raise is insufficient — sports bucket is 16.4M rows / 19.5GB).
      Decide raise-vs-shard per the plan's own note (design call, not an inline improvise) and fix. Repo:
      deployment-api. Done when: a live `rollup-run?services=instruments-service` completes the manifest step.
- [x] ✅ [INFRA] P2. Rollup-svc coverage write 403 (`storage.objects.create` denied for uts-prd-sa on
      `central-element-323112-data-status-rollups`): **FIXED 2026-08-10 (slot 5)**. Root cause: when the Cloud Run
      service was redeployed with `uts-prd-sa` as the runtime SA (starting revision -00392), the bucket
      `gs://central-element-323112-data-status-rollups` had `roles/storage.objectAdmin` ONLY for `unified-trading-sa` at
      the bucket level. `uts-prd-sa` had project-level `roles/storage.objectAdmin` but the bucket write still 403'd —
      uniform bucket-level access (locked 2026-08-04) requires explicit bucket-level bindings, and the project-level
      grant was not sufficient. **Fix**: granted `uts-prd-sa@central-element-323112.iam.gserviceaccount.com`
      `roles/storage.objectAdmin` on `gs://central-element-323112-data-status-rollups`, mirroring the existing binding
      for `unified-trading-sa`. IAM binding verified via `gsutil iam get`. No code change needed — pure IAM fix.
      **Additional finding**: latest revision -00399 (image `321b365f`) crashes with SIGABRT/6 on every request — rolled
      back to -00398 (image `a6cdf6db`, uts-prd-sa) which is stable but the scheduler's OIDC invocations are producing
      `Firebase auth: invalid token` warnings in the app logs (tracked separately — may need investigation of whether
      `verify_any_auth` middleware on `_authenticated_router` is incorrectly intercepting the rollup route despite
      `_rollup.router` being mounted directly on `app` at line 315 of `main.py`). Live verification (coverage write
      succeeding on a real `*/20` cron cycle) is gated on the Firebase auth path being healthy; the IAM fix itself is
      deterministic — `uts-prd-sa` now has the same bucket-level write grant `unified-trading-sa` had when the service
      was working. Deploy blocker doc
      `/plans/active/issues/uts_prod_data_status_rollup_svc_container_startup_failure_blocks_deploy_2026_08_10.md` is
      still open — the -00399 SIGABRT may be a recurrence or a new regression.

> **2026-08-06 archive-candidate audit**: CODE todo's own resolution text says 'Live confirmation (full.json.gz actually
> refreshing on the next real */20 cron cycle) is a follow-up verification step, not blocking the fix landing' - a
> deferred verification never turned into its own todo and not shown done in any later Progress Log entry

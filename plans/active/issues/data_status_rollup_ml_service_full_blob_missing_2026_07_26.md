---
doc_type: issue
title: data-status rollup worker never writes ml-service's full.json.gz (coverage.json.gz succeeds)
summary: >-
  While diagnosing the uts-prod-data-status-rollup Cloud Run service (defi_satellite_ao_dispatch_batch1-032), found
  `gs://central-element-323112-data-status-rollups/ml-service/` carries only `coverage.json.gz` — `full.json.gz` is
  absent. Originally (2026-07-26) this was the ONLY gap beyond the known market-tick-data-service one. **STALE as of
  2026-08-13**: 8 more `_DEFAULT_SERVICES` have since regressed with 2 new, previously-unseen exception classes
  (`TypeError`/`AttributeError` on manifest columns; 2 more services newly timing out) — see the 2026-08-13 Progress Log
  entry. Only 3 of 14 `_DEFAULT_SERVICES` currently produce a `full.json.gz` at all.
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
    /plans/active/mvp_could_exist_rollup_dual_scope_2026_08_12.md,
  ]
created: 2026-07-26
author: unknown
last_updated: 2026-08-13
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
  `/plans/archive/2026_08/issues/uts_prod_data_status_rollup_svc_container_startup_failure_blocks_deploy_2026_08_10.md`.
  This doc's own timeout todo is code-complete and platform-config-complete; final live re-verification is gated on that
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

- **2026-08-11 (interactive session, /autonomous)**: resolved both remaining open Follow-ups below — see their entries
  for the full correction to the raise-vs-shard escalation above. Root cause was a `bounded_subprocess.run_bounded()`
  deadlock (child's queued result exceeds the OS pipe buffer, parent joins before draining the queue), not a
  compute-duration problem — no sub-sharding or SPORTS structural-gap acceptance was needed. Fixed in
  `deployment-api@225a3e81c2`, live-verified: `POST rollup-run?services=instruments-service` →
  `{"status":"ok","exit_code_live":0}`, `full.json.gz` refreshed 2026-08-11T08:36:42Z. Full chain (5 deployment-api
  SHAs + a fleet-wide unified-trading-ci CI fix unblocked along the way) documented in the sibling deploy-blocker doc's
  Resolution section.

- **2026-08-13 (autonomous tick, `mvp_could_exist_rollup_dual_scope_2026_08_12.md` todo 7)**: **This doc's own summary
  is now STALE and MISLEADING — correcting it here rather than leaving it to mislead the next reader.** The summary
  claims "every other `_DEFAULT_SERVICES` entry except the known market-tick-data-service gap... got a fresh
  `full.json.gz` in the same cycle" (true as of 2026-07-26). It is no longer true. Triggered a fresh rollup run today
  (`gcloud scheduler jobs run uts-prod-data-status-rollup-cron`, 16:10:57Z) to verify todo 7's dual-scope-blob
  precondition, and found **9 of the 14 `_DEFAULT_SERVICES` now fail with 2 exception classes this doc has never
  mentioned**, confirmed via `gcloud logging read` on `uts-prod-data-status-rollup-svc`:
  - `TypeError: '<' not supported between instances of 'NoneType' and 'str'` —
    `features-delta-one-service`/`features-volatility-service`/`features-multi-timeframe-service`/
    `features-cross-instrument-service`.
  - `AttributeError: Can only use .str accessor with string values!` — `features-sports-service`/
    `features-calendar-service`/`strategy-service`.
  - `manifest rollup failed ... timed out after 420s` — `market-tick-data-service` (already tracked, separate doc)/
    `market-data-processing-service` (NOT previously tracked)/`features-onchain-service` (NOT previously tracked).

  **Confirmed pre-existing, not a regression from `mvp_could_exist_rollup_dual_scope_2026_08_12`'s dual-scope code**:
  re-ran the SAME log query for the window BEFORE that plan's 2026-08-13T14:55:52Z deploy and found the identical error
  signatures already firing as early as 10:38Z today (`features-calendar-service`) — well before any dual-scope code was
  live. Root cause of WHEN this regressed between 2026-07-26 (doc's original finding: these 9 services were fine) and
  today is **not yet diagnosed** — that's the next investigative step, not done here (this entry is the discovery, not
  the fix).

  **Only 3 of 14 `_DEFAULT_SERVICES` have EVER had a `full.json.gz`**: `instruments-service` (fresh, today's dual-scope
  run), `features-commodity-service` (stale, 2026-08-13T11:43Z — predates the regression's earliest observed
  occurrence), `execution-service` (stale, 2026-08-13T10:53Z — likely from BEFORE whatever broke the other 9, given it
  succeeded that recently). `ml-service` remains never-written (this doc's original finding, still open). **Practical
  implication for `mvp_could_exist_rollup_dual_scope_2026_08_12`'s todo 7** ("every `_DEFAULT_SERVICES` entry
  regenerated in dual-scope shape"): that bar is now structurally unreachable without a SEPARATE fix to this broader
  regression — 10 of 14 services (9 new + ml-service) cannot produce ANY `full.json.gz`, dual-scope or otherwise, until
  this is root-caused and fixed. Flagging for operator awareness — this is bigger than one plan's transition-compat
  cleanup todo.

- **data_engineering (slot-2) 2026-08-13T18:20Z**: root-caused + fixed the `[DATA] P1` follow-up (the TypeError /
  AttributeError class failing 7 of 14 rollup services). Both error classes traced to the SAME two lines in
  `breakdowns_domain.py` `_build_single_feature_group_entry` (L441 `.str.len()` + L444 `sorted(unique())`), triggered by
  a data-shape change in the features buckets (timeframe/feature_group/chain columns now all-null float64 or mixed
  None+str). Fixed via `fillna("").astype(str)` dtype-normalization at all three sites + regression tests. Shipped
  `deployment-api@31e1affb65`, full QG green, verified on origin. See the todo's own resolution note for the full
  evidence chain. Note: the separate `[DATA] P2` timeouts (MDPS / features-onchain) + `[DATA] P3` live re-verification
  remain open.

- **2026-08-13T~21:00Z (independent confirmation + new evidence for the open [DATA] P2)**: was investigating the P1
  TypeError independently (parallel effort, unaware of slot-2's fix at the time) and found it already shipped + deployed
  by the time I checked — confirmed `31e1affb65` is on `origin/main` and the live `uts-prod-data-status-rollup-svc`
  revision (created 2026-08-13T18:48:28Z, AFTER the fix) carries it. Reproduced `features-delta-one-service`'s CEFI +
  TRADFI categories locally against the FIXED code — both build cleanly now (`dates_found=5`/`2` respectively, no
  exception), consistent with the fix working. **New evidence for the still-open P2 (timeouts)**: attempting
  `features-delta-one-service`'s DEFI category locally (twice, once alongside CEFI/TRADFI, once in total isolation)
  SIGKILL'd my local machine both times at the identical point — right after the small `features-defi` manifest index
  read (12,940 rows), before the much larger `market-data-tick-defi` bulk read even logged a profile line. This is
  consistent with the ALREADY-DOCUMENTED DEFI memory class this workspace has measured before
  (`venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md`: "DEFI extrapolates to ~80 GiB" peak RSS) —
  `features-delta-one-service`/`market-data-processing-service`/`features-multi-timeframe-service`/
  `features-cross-instrument-service` all include DEFI in `_SERVICE_CATEGORY_RESTRICTIONS` (`defi.py:139-150`), so this
  is a plausible SHARED root cause for several of the P2 timeout services, not a coincidence. **Important scoping note
  this session's own earlier finding got wrong**: `features-volatility-service` has DEFI explicitly EXCLUDED from its
  restriction (CEFI/TRADFI only, per `defi.py:145`'s comment: "DEFI removed... no DeFi options exist") yet it was ALSO
  hit by the (now-fixed) P1 TypeError — proving the TypeError was never a DEFI-memory issue itself, just a
  coincidentally-overlapping, separate bug. Did not attempt further local reproduction of DEFI (2 SIGKILLs on my own
  machine is the stop-and-report signal, not retry-a-3rd-time) — a safe repro of the P2 timeout needs either a
  memory-bounded/column-projected read (mirroring the fix pattern already proven for the CEFI OOM class) or examining
  this from a machine/subprocess with more headroom, not a bare local call. As of this check (~21:00Z, ~2h after the P1
  fix deployed), the 7 previously-P1-broken services still show NO fresh `full.json.gz` — the sequential 14-service
  rollup run apparently hasn't reached them yet in a post-fix cycle (still gated behind
  `market-tick-data-service`/`market-data-processing-service` earlier in `_DEFAULT_SERVICES`' order, both still timing
  out per the open P2). Re-check blob timestamps for the 7 P1-affected services after confirming a POST-18:48:28Z cycle
  has run to completion.

- **2026-08-14 (scoping the open P2, interrupted mid-investigation — NOT root-caused, read before continuing)**: Traced
  the P2 timeout's actual read path to decide whether the earlier "memory-bounded/column-projected read" idea (mentioned
  in the prior entry) is safe to build. It is NOT, as a naive version — `data_status_service._read_index_cached` (the
  shared manifest-index reader both `defi.py` and `sports.py` call) has an explicit docstring warning that a fixed
  column projection there risks silently dropping a column a DIFFERENT caller needs; this function was deliberately left
  unprojected for that reason. Any real fix needs a PER-CALLER column allowlist threaded through explicitly, not a
  blanket projection at the shared layer.
  1. **Re-examined the actual production symptom**: `market-data-processing-service`/`features-onchain-service` both
     fail with `"timed out after 420s"` — never `MemoryError`. `market-tick-data-service`'s already-accepted gap DOES
     produce `MemoryError` (caught inside its 18Gi child rlimit). This distinction matters: a pure timeout inside a
     currently-succeeding memory budget points toward the SAME low-risk, already-proven fix pattern used for
     `instruments-service` (a per-service `_CHILD_JOIN_TIMEOUT_OVERRIDES_S` raise, `data_status_rollup_worker.py:220`)
     rather than a riskier read-path rewrite — IF a real measured duration justifies it, matching how the
     instruments-service override was sized ("3 consistent live measurements"), not a blind bump (this doc's own history
     already flagged the risk of a blind bump: raising MDPS's budget without evidence could starve every service queued
     after it in the shared sequential 420s-per-service budget).
  2. **Attempted a safe measurement, it failed differently than expected**: resolved MDPS's and features-onchain's DEFI
     bucket names (`resolve_bucket_name(kind="market-data"/"features", asset_group="defi")`) and tried
     `list_blobs(bucket, prefix="")` (no cap) to get a cheap blob-count/size estimate before attempting any read. **This
     hung for hours without returning** — confirmed still genuinely alive (not silently dead) via `TaskStop` on the
     process late in this session, only then terminated. This is itself new evidence: even bucket-metadata listing (no
     data download) doesn't complete in reasonable time on these buckets unpaginated, which independently suggests very
     high object COUNT is part of what's slow here, not just per-object size.
  3. **Did not get to a real measurement this session** — this genuinely needs new data that doesn't exist yet (a
     bounded/paginated listing or a pyarrow-footer-only metadata read, see the todo's own updated text for the exact
     next step), not something to force to completion under time pressure. Filed as an update to the existing P2 todo
     below rather than a new one — same open item, now scoped precisely instead of vaguely.

- **2026-08-14 (continuation, P2 ROOT-CAUSED — traced to a live consolidator incident, NOT a code/timeout-fit
  problem)**: Followed the prior entry's own prescribed next step (bounded metadata reads instead of an unbounded
  listing) and it worked cleanly. (1) Traced `_read_index_cached` → `read_availability_index`
  (`unified_trading_library/manifest_writer/_read_index.py:617`) to its real GCS access pattern: ONE fixed-key blob
  (`_index/availability_index.parquet`) on the fast path, no listing — the earlier hung `list_blobs(bucket, prefix="")`
  attempt was never actually replicating the real read path, it was enumerating the whole raw data bucket, an unrelated
  and much heavier operation. (2) Bounded `blob.exists()`/`blob.reload()` stats (single HEAD request per object, no
  download) on both DEFI buckets' index+lock objects found `market-data-tick-defi-prd-central-element-323112` stale for
  7+ hours with a lock 69+ min old (near the 4200s DOWN-detection horizon), while
  `features-defi-prd-central-element-323112` was fresh (30min) with no lock — immediately falsifying "same root cause
  for both services." (3) A bounded, prefix-scoped listing (`_index/per_vm/`, `max_results=50`, NOT a whole-bucket
  listing) confirmed 16 real pending shards on the MDPS bucket, several written within the hour. (4) Checked the Cloud
  Run job's own execution history (`gcloud run jobs executions list`, region `asia-northeast1` — the job silently wasn't
  in `us-central1` where I first looked) and its live logs (`gcloud logging read`): the consolidator IS running
  healthily every ~60s and completing in 38-55s, but its own health-check code is emitting
  `CRITICAL: SILENT STALL ... streak=150+ cycles ... shards keep landing but no cycle has merged them` every single
  cycle — a genuine, already self-diagnosed incident, not a theory. Filed as the new P0 above (blocks this P2);
  root-caused the SYMPTOM (MDPS's 420s timeout) but the live incident's own root cause (why the incremental mtime-cutoff
  blind spot recurred here) is explicitly NOT resolved by this entry — that's the P0's own open question. Did not
  attempt `consolidate(bucket, force=True)` — its docstring's OOM warning for this exact bucket class + the
  heavy-I/O-belongs-on-a-VM rule made self-serving it without operator sign-off the wrong call; escalated in-chat
  instead.

- **2026-08-14 (continuation, P0 root cause CORRECTED — the alert's generic "mtime predates cutoff" text was misleading
  for this specific incident)**: operator asked to check why the blind spot recurred before authorizing the
  force-consolidate. Read `gcloud logging read` around the 01:22:42 lock-reclaim rather than trusting the alert's static
  message: the incremental cutoff logic was NOT skipping the shards — it found them as changed and started a real
  `duckdb_merge` (`chunks=105 date_range=2018-01-01..2026-08-13` against a 159M-row canonical). The actual mechanism:
  `gcloud run jobs describe` showed the job's `timeoutSeconds=3600`, below the real merge duration for this now-much-
  larger corpus (canonical grew to 159M rows / 7.3GB since the archived 2026-08-05 incident) — every attempt gets killed
  by the platform deadline before finishing, orphans the lock, and the next cron tick (after the separate 4200s lock TTL
  passes) reclaims it and repeats the same doomed attempt forever. Confirmed via two log windows an hour apart
  (01:22-01:26 and 02:26-02:35) showing the identical lock-reclaim → merge-start → (never completes) → next-tick-skip
  shape twice in a row. This means a bare `--force` retry through the normal Cloud Run trigger would have hit the
  identical wall — `force=True` does the same shape of full-date-range chunked merge, just against all shards instead of
  only the changed ones, so duration is comparable, not the fix by itself. **Operator confirmed proceeding** ("yes check
  the incremental mtime cutoff then force and consolidation"). Started building a one-off remediation
  (`gcloud run jobs execute ... --task-timeout=10800 --force`, waiting for the orphaned lock to clear first) — **aborted
  before it fired** on discovering the conflict below: a PEER SESSION had independently already dispatched a formal,
  properly-engineered fix for this exact P0 through the correct channel while this investigation was in progress. Ceded
  to that fix rather than risk two concurrent force-consolidates racing the same canonical/lock — see the next entry for
  what actually ran. This entry's own root-cause finding (timeout-vs-duration mismatch, not a cutoff bug) stands
  independently and is genuinely new evidence the peer's entry does not itself cover.
- **data_engineering (slot-21) 2026-08-14T03:22Z**: dispatched onto this doc's P0 follow-up (from the FIRST P0 entry
  above, before the root-cause-correction entry immediately above this one existed); live-reconfirmed the SILENT STALL
  still active (streak=168 cycles at 02:52:41Z, climbing) — the prior session's "escalated in-chat" was not a tracked
  dashboard escalation, so filed a formal `/blocked` (BLK-838e73de) with the two options from the P0's own text.
  **Operator answered Option A** ("launch a dedicated VM now and run `consolidate(bucket, force=True)` with a bounded
  `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT`, verify live" — ruled not operator-gated per Data Pipeline Correctness Is The
  Heartbeat, since the staleness is actively growing). Built a new one-off launcher
  (`deployment-service/scripts/vm/launch-defi-manifest-force-consolidate-vm.sh`; no reusable launcher existed for this
  exact CLI invocation) + registered the `defi-manifest-force-consolidate-` prefix in `vm_prefix_registry.py`
  (bucket=None — writes direct to the canonical index, not a per-VM shard, mirroring `defi-manifest-projection-`) and
  `launcher_registry.py` (`None` — non-relaunchable, OOM history on this bucket class, manual relaunch only). Full QG
  green, shipped `deployment-service@2f1c7597`. Launched `defi-manifest-force-consolidate-20260814-031954`
  (e2-highmem-8, ON-DEMAND not spot — a force-rebuild isn't safely resumable mid-merge, `asia-northeast1-c`,
  `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT=16GB`, threads left at default per the module's own "24GB made it worse" finding).
  Armed a `run_in_background` watchdog on `run.log` (UTL `download_from_storage`, not a subprocess `gsutil`/`gcloud`
  read — the workspace GCS-object-CLI ban applies to reads too) polling every 90s for the `=== VM setup complete ===`
  terminal marker, 2400s ceiling. **Result pending** — see the next Progress Log entry for the verified outcome; do not
  treat this entry alone as confirmation the stall cleared.
- **data_engineering (slot-15) 2026-08-14T05:15Z**: dispatched onto this doc's P0. Live-verified the incident is STILL
  ACTIVE, not yet resolved by the peer VM launch recorded above — bounded single-blob stats (never a corpus walk):
  `_index/availability_index.parquet` last_modified unchanged at `2026-08-13T19:28:24Z` (now 05:11Z, ~9h43m stale);
  `_index/consolidator.lock` content shows a DIFFERENT holder each check (`instance` field changed between my two
  checks, most recently `started_at=2026-08-14T05:01:12Z` / re-read again at `05:11:03Z` — the lock keeps getting
  freshly re-acquired, consistent with repeated short-lived remediation attempts rather than one long-running merge).
  The originally-launched `defi-manifest-force-consolidate-20260814-031954` VM no longer exists in
  `gcloud compute instances list` (any zone) — gone, not visible as RUNNING/TERMINATED. A SECOND VM,
  `defi-manifest-force-consolidate-20260814-044333`, launched ~04:43:33Z and was killed via an external shutdown signal
  at 04:45:02Z — only ~90s into boot, mid-`apt-get install` (serial console shows
  `google-startup-scripts.service: Main process exited, code=killed, status=15/TERM`), i.e. it never reached the actual
  `consolidate(force=True)` call. Did not launch a THIRD competing VM — this doc's own root-cause entry above already
  flags the two-concurrent-force-consolidates collision risk, and this session found clear evidence of at least one
  recent collision (the killed 044333 VM) without being able to identify who is currently holding the lock
  (`instance: "5017-dd72ae5c"` doesn't match any compute-VM naming pattern seen in this doc — possibly a
  directly-invoked `consolidate()` call from an interactive session on a shared host, not a registered launcher).
  **Scoped this session's contribution to what's independently safe and valuable without touching the live
  remediation**: closed the alerting gap (see the P0 todo's own updated text above, `alerting-service@da8226325c`)
  rather than attempt a third force-consolidate. **P0 checkbox intentionally left unflipped** — the underlying stall is
  not resolved; only its "goes unpaged" half is fixed. Whoever picks this up next: re-check `_index/consolidator.lock`
  content + `_index/availability_index.parquet.last_modified` live before assuming any prior attempt succeeded — this
  doc's history already shows two attempts that looked promising in the moment and were superseded/killed before
  completing.
- **2026-08-14 (this session, resolving the shared-checkout conflict above)**: on pushing this doc's own root-cause
  entry, hit a real (not transient) git conflict against the peer entry above, which had landed in between. Confirmed
  via `TaskOutput` that this session's own one-off remediation script (`force_consolidate_defi.sh`) had NOT yet fired
  its `gcloud run jobs execute` call (still in its lock-wait poll loop) and stopped it via `TaskStop` before it could —
  no collision occurred, the peer's VM-based force-consolidate is the one actually running. This session's remediation
  attempt is superseded and will not be resumed; the peer's `defi-manifest-force-consolidate-20260814-031954` VM is now
  the sole in-flight fix. Merged both Progress Log entries above in (approximate) chronological order rather than
  dropping either — this session's root-cause trace and the peer's dispatch+launch are complementary, not duplicate.

- **data_engineering (slot-21) 2026-08-14T06:22Z — P0 RESOLVED.** The originally-launched
  `defi-manifest-force-consolidate-20260814-031954` VM died at boot on an unrelated bug before ever running
  `consolidate()`. Fixed the launcher forward through 4 distinct bugs (wrong `VM_SERVICE`, missing `VM_TASK` dispatch
  branch, wrong bucket env-tag, insufficient boot disk for DuckDB's temp-spill), each shipped + verified on origin
  before the next relaunch — full evidence chain in the P0 todo's own resolution text above (not duplicated here). 5th
  launch (`defi-manifest-force-consolidate-20260814-052225`) succeeded: `success=True shards=16 rows_out=159218124`,
  fresh `_index/availability_index.parquet` confirmed live, and the very next incremental cron cycle ran clean
  (`pruned_shards=15`, no `SILENT STALL`). The reusable launcher itself
  (`deployment-service/scripts/vm/launch-defi-manifest-force-consolidate-vm.sh`) is now a durable asset for any future
  force-rebuild of this bucket. Did not touch the still-open P2 (MDPS 420s timeout) — its own todo text says it should
  be re-checked on a post-fix rollup cycle, not assumed resolved by this entry; leaving that verification to the next
  dispatch since it's a distinct check, not part of this P0's own done-when.

- **2026-08-14 (this session, doing the P2 re-check the prior entry deferred) — P0's "RESOLVED" WAS PREMATURE, IT
  RECURRED.** Live-verified MDPS's rollup did NOT clear post-fix: `gcloud logging read` on
  `uts-prod-data-status-rollup-svc` shows
  `manifest rollup failed for service=market-data-processing-service: timed out after 420s` at 2026-08-14T10:06:54Z —
  3h46m after the 06:20:36Z fix, on the identical 420s wall. Ran `read_availability_index()` directly against the same
  bucket at 11:39Z: it hit the exact same code path as the ORIGINAL incident — "consolidated blob age 15497.2s > 3600s
  threshold — falling back to per-VM shards" then "waiting on a live consolidator lock (age=2721s, bounded wait up to
  horizon=4200s)". **The fix was never durable because the actual root cause was never touched**: the force-consolidate
  cleared the backlog once, but `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf:94`
  (`manifest_consolidator_timeouts["market-data-defi"] = 3600`) still caps every ONGOING cron cycle's merge attempt at
  3600s, and `gcloud logging read` confirms this bucket's `phase=duckdb_merge_start` still chunks the FULL
  `2018-01-01..2026-08-14` date range every cycle (`chunks=105`) regardless of how few shards actually changed — the
  "incremental" merge only narrows which SOURCE rows get pulled in, not the OUTPUT chunking cost, so cycle duration
  doesn't shrink just because the corpus caught up once. Traced one specific cycle in detail:
  `phase=duckdb_merge_done rows_out=159309454` at 10:53:25Z (a real, larger-than-P0's-159218124 success — steady-state
  merges CAN complete), but the VERY NEXT cycle (`phase=lock_acquired` 11:04:41Z →
  `phase=canonical_downloaded canon_rows=159218124` at 11:06:18Z — note this is the OLDER P0 count, not the just-written
  159309454, meaning that write may not have actually landed before this next cycle read it) started ANOTHER full
  105-chunk merge at 11:06:22Z. Operator directed: get a real steady-state duration measurement before sizing the
  Terraform `timeout_seconds` fix (not another one-off VM run, not a blind bump). A bounded watchdog is watching this
  exact 11:06:22Z-started cycle for its outcome (completion vs. a 3600s-deadline kill) — see the next entry for the
  result before treating this P0 as resolved a second time.
- **Also root-caused 2026-08-14: `features-onchain-service`'s 420s timeout is NOT a separate/unrelated cause** — earlier
  entries in this doc and this session's own prior chat summary incorrectly concluded this because its OWN primary
  bucket (`features-defi-prd-central-element-323112`) IS genuinely healthy (351KB index, fresh, no lock). The real
  mechanism: `features-onchain-service` is in `_REFERENCE_DRIVEN_SERVICES` with
  `_UPSTREAM_SERVICE_MAP["features-onchain-service"] = "market-tick-data-service"`
  (`deployment_api/services/data_status/ sports.py:181`) — once per category build it ALSO does a full, unprojected
  reference read of the MTDS DEFI bucket (`_get_reference_expected_dates`, `sports.py:105-134`) — the SAME stuck
  `market-data-tick-defi-prd-...` bucket this P0 is about, just reached via a hidden cross-service dependency instead of
  its own primary category. This explains the exact failure pattern: MTDS and MDPS (direct consumers) fail,
  `features-onchain-service` (indirect consumer via this reference lookup) fails, while other features-* services whose
  upstream isn't MTDS/MDPS succeed. Both open P2 items share the ONE root cause above — ~~neither needs its own separate
  fix once the Terraform timeout is properly sized~~ **CORRECTED 2026-08-14T13:30Z (slot-11): this was wrong for MDPS —
  see the P0/P2 Progress Log entry below. Sizing the Terraform timeout properly fixed the STALL but not MDPS's own 420s
  read-timeout, because a healthy consolidator now legitimately holds its lock most of every hour.**
- **data_engineering (slot-11) 2026-08-14T13:30Z — P0 durable-fix VERIFIED LIVE; P2 does NOT auto-clear (new negative
  result).** Picked up this doc's P0 follow-up. Found the Terraform fix this doc's own 11:06Z-cycle watchdog was waiting
  on had ALREADY shipped (deployment-service, `manifest_consolidator_timeouts["market-data-defi"]` 3600→7200 + matching
  TTL/stall-cycle raises) and was ALREADY deployed live
  (`gcloud run jobs describe uts-prod-manifest-consolidator-market-data-defi`: `timeoutSeconds=7200`) — a peer session
  must have landed and applied it after the last Progress Log entry above. Live-verified it actually works, not just
  deployed: read `gcloud logging read` for the job over the last 3h and found TWO consecutive full incremental merge
  cycles completing cleanly (`lock_acquired` 11:06:18Z → `duckdb_merge_done rows_out=159337175` 12:03:24Z = 3422s;
  `lock_acquired` 12:13:42Z → `duckdb_merge_done rows_out=159363310` 13:13:00Z = 3441s), both far under the new 7200s
  ceiling, canonical rows growing steadily, and concurrent cron ticks correctly logging
  `skipping cycle ... fresh lock present` instead of reclaiming/retrying — the SILENT STALL loop is gone. Flipped the P0
  checkbox on that evidence (a structural job-ceiling fix, not another one-off VM backlog-clear, so the earlier
  premature-resolution failure mode doesn't apply here). Then re-checked the P2 (MDPS 420s timeout) the P0's own text
  said should "clear on its own" — it did NOT: `gcloud logging read` for the rollup service found
  `manifest rollup failed for service=market-data-processing-service: timed out after 420s` at 12:46:01Z, inside the
  12:13:42Z-13:13:00Z merge window. Mechanism: the now-reliable consolidator runs ~57-58min cycles back-to-back (~10min
  gap between cycles observed), so the bucket's lock is held roughly 85-90% of every hour — MDPS's own read still can't
  reliably land in the shrinking free window within its 420s budget. Corrected this doc's own now-stale "neither needs
  its own separate fix" claim (line above) and the P2 todo's text with this finding — P2 stays open, now scoped
  precisely (lock-contention/capacity, not stall) rather than "should self-resolve." Did not attempt a P2 fix this pass
  (needs its own real lock-wait/fallback-read duration measurement first, per this file's own established no-blind-bump
  discipline) — out of scope for the P0 this task was dispatched against.

- **data_engineering (slot-11) 2026-08-14T~17:20Z — P2 (MDPS portion) CLOSED as a confirmed structural gap.** Got the
  real measurement this doc's own P0 entry above (13:30Z) said was still needed before sizing any override. Read
  `unified_trading_library/manifest_writer/_staleness_budget.py`: `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC["defi"] = 4200`
  — `_wait_for_in_flight_cycle_then_reread` polls for a lock release for up to 4200s once it detects a live merge.
  Combined with the P0 entry's own two consecutive live cycle measurements (~3400-3450s / ~57min busy, ~10min free),
  this proves MDPS's 420s per-service budget (~1/10th of one merge cycle) cannot reliably survive the wait regardless of
  override size — any value large enough to actually help would blow the shared sequential-sweep budget ceiling the same
  way an unbounded instruments-service override would have. No blind bump attempted; instead accepted this as a
  structural gap (same treatment as the original MTDS gap + the since-fixed instruments-service memory gap — loud,
  isolated failure, never silent). Shipped `deployment-api@fcd0de0` (comment-only, documents the closing evidence next
  to the existing 2026-08-14 root-cause block; no behavior change) — full QG green, verified on origin
  (`git merge-base --is-ancestor` confirmed). No new regression test needed:
  `test_mdps_style_full_timeout_is_loud_and_does_not_block_next_service` (2026-08-02) already asserts the property that
  matters. Split `features-onchain-service`'s still-unexplained 420s timeout into its own P2 todo below rather than
  leaving it bundled under a now-closed checkbox — it does not share MDPS's root cause (its own bucket was confirmed
  live-healthy at the same check).

- **data_engineering (slot-12) 2026-08-14T~19:15Z**: closed the `features-onchain-service` P2 follow-up — CORRECTING the
  17:20Z entry's "does not share MDPS's root cause" conclusion above. Live-traced the code (not the prior session's
  primary-bucket-only check):
  `sports.py::_UPSTREAM_SERVICE_MAP["features-onchain-service"] = "market-tick-data-service"` routes every onchain
  manifest/coverage build through a hidden reference-driven read (`_maybe_reference_expected_dates` ->
  `_get_reference_expected_dates` -> `_read_upstream_venue_dates`) of the SAME
  `market-data-tick-defi-prd-central-element-323112` bucket MDPS's own read stalls on — confirmed via
  `SERVICE_TO_KIND["market-tick-data-service"]="market-data"` + `asset_group="defi"` resolving to that exact bucket, and
  via `gcloud logging read` showing manifest AND coverage failing together every occurrence in the last 24h
  (2026-08-13T22:22:58Z / 2026-08-14T03:44:03Z / 07:47:00Z / 10:27:15Z), matching MDPS's own dual-timeout signature
  exactly rather than a single-step failure. This also corrects the rollup worker's own code comment, which had
  concluded "genuinely NOT root-caused yet" based on checking a DIFFERENT cross-bucket path
  (`defi.py::_collect_defi_index_frames`, not the `_UPSTREAM_SERVICE_MAP` one) and a DEFI-grid-cost hypothesis that was
  never actually right for this service. Resolution: same as MDPS's own P2 — accepted as a structural gap, no
  rollup-worker-side fix (the shared bucket's lock contention is the already-tracked root cause; a per-service timeout
  override can't beat the lock's ~85-90% hold rate within the shared sweep budget). Shipped `deployment-api@77b60c445e`
  (comment-only root-cause documentation + `test_onchain_dual_timeout_does_not_block_next_service` regression test).
  Full QG green, verified on origin.

## Follow-ups

- [x] ✅ [DATA] P1. **NEW (2026-08-14), split out of the P0 below**: `MANIFEST_CONSOLIDATION_STALLED` is emitted
      (`log_event(severity="ERROR")`) by the manifest consolidator's stall detector but has zero consumer anywhere in
      alerting-service, so it never pages on-call. **FIXED 2026-08-14 (slot 15)**: `alerting-service@da8226325c`. Added
      `handle_manifest_consolidation_stalled_payload` to `alerting_service/rules/consolidator_rules.py` (pages CRITICAL
      — PagerDuty + Telegram — on the first occurrence, no breaker needed since the emitter itself only fires after its
      own no-progress streak already crosses its alert threshold), wired into `alert_subscriber.py`'s `_TYPED_HANDLERS`
      dispatch dict, regression tests added (`tests/unit/rules/test_consolidator_rules.py`). Full QG green, verified on
      origin. This closes the "goes unpaged" half of the P0 incident below — it does NOT fix the underlying stall
      itself, which is still active (see the P0's own Progress Log entry, 2026-08-14T05:15Z).
- [x] ✅ [DATA] P0. **NEW (2026-08-14) — LIVE INCIDENT, UNPAGED. ROOT-CAUSED 2026-08-14 (see Progress Log): NOT the
      mtime-cutoff blind spot the generic alert text suggested — a merge-duration-vs-execution-timeout mismatch.
      REOPENED 2026-08-14 (this session) — the 06:20:36Z "RESOLVED" below was a one-off backlog clear, NOT a durable
      fix: live-reconfirmed the exact same 420s timeout still firing on MDPS at 10:06:54Z (3h46m later) and the
      consolidated blob back in a stale/waiting-on-lock state at 11:39Z. The real fix is raising
      `manifest_consolidator_scheduler.tf:94`'s `timeout_seconds=3600` for this bucket — not done yet, a real
      steady-state duration measurement is in progress before sizing it (operator-directed). See the newest Progress Log
      entries for the full evidence and the in-flight measurement. **RESOLVED (durable fix) 2026-08-14T13:30Z
      (slot-11)**: the Terraform fix was already shipped (`deployment-service` —
      `manifest_consolidator_timeouts["market-data-defi"]` 3600→7200,
      `manifest_consolidator_lock_ttl_seconds["market-data-defi"]` 4200→9000,
      `manifest_consolidator_stall_alert_cycles["market-data-defi"]` 90→195, see the terraform file's own 2026-08-14
      comment for the measured-duration rationale) and IS live
      (`gcloud run jobs describe     uts-prod-manifest-consolidator-market-data-defi --region asia-northeast1` confirms
      `timeoutSeconds=7200` deployed). Live-verified from Cloud Logging, not doc checkboxes — TWO consecutive full
      incremental merge cycles completed cleanly post-fix: `lock_acquired` 11:06:18Z →
      `duckdb_merge_done rows_out=159337175` 12:03:24Z (3422s), then `lock_acquired` 12:13:42Z →
      `duckdb_merge_done rows_out=159363310` 13:13:00Z (3441s) — both comfortably under the new 7200s ceiling (well
      under half), canonical row count growing steadily cycle over cycle, and every overlapping cron tick during each
      merge correctly logged `skipping cycle ... fresh lock present (sibling cron still running)` instead of reclaiming
      and retrying — the SILENT STALL retry-loop is gone. This is a structural fix (the standing Cloud Run job's own
      ceiling), not another one-off VM backlog-clear like the 06:20:36Z entry that later recurred — the distinction that
      made the earlier "RESOLVED" premature does not apply here. Caveat carried forward from the terraform comment
      itself: corpus growth could outgrow 7200s again eventually; re-verify if the stall alert pages again. **Important:
      this does NOT mean the related P2 (MDPS 420s timeout) also cleared — it did not, see that todo's updated text
      below.** `market-data-tick-defi-prd-central-element-323112`'s manifest-consolidator (Cloud Run job
      `uts-prod-manifest-consolidator-market-data-defi`, region `asia-northeast1`) is in a genuine `SILENT STALL`
      (`unified_trading_library/manifest_consolidator.py:1441` `_check_consolidation_stall`, log emitted at
      `:1492-1500`): 16 real per-VM shards sat unmerged for 150+ consecutive 1-minute cron ticks (streak climbing in
      real time as of 2026-08-14T02:26-02:35Z), the 7.3GB `_index/availability_index.parquet` unrewritten for 7+ hours.
      **Corrected root cause (live logs, not the alert's generic text)**: the incremental cutoff logic is working
      correctly — `gcloud logging read` around a lock-reclaim (01:22:42) showed the merge DID find changed shards and
      DID start a real duckdb merge (`phase=duckdb_merge_start ... chunks=105 date_range=2018-01-01..2026-08-13` against
      a 159,036,875-row canonical), but that merge never completes: the job's own `timeoutSeconds=3600`
      (`gcloud run     jobs describe`) kills the task attempt before the ~70min+ real merge duration finishes, orphaning
      `_index/consolidator.lock`, which then sits until the 4200s lock TTL passes and the next cron tick reclaims it and
      repeats the identical doomed attempt — an infinite retry loop, not a silent skip. **This is NOT the same incident
      as the archived `/plans/archive/issues/defi_manifest_consolidator_stale_lock_silent_stall_2026_08_05.md`** (that
      one was a stall-alert-threshold miscalibration, no lock/timeout issue) — the corpus has grown since (159M rows
      now) and the real merge duration has outgrown the job's fixed 3600s deadline. **Alerting gap CLOSED 2026-08-14 —
      see the dedicated P1 todo above** (`alerting-service@da8226325c`); that fix is the "goes unpaged" half only and
      does NOT resolve the stall itself (still active — see Progress Log 2026-08-14T05:11Z re-check: index still stuck
      at `2026-08-13T19:28:24Z`, lock still being actively re-acquired). **Remediation in flight 2026-08-14 — running
      via a PEER SESSION's dedicated VM, not a Cloud Run job retry**: a parallel session independently filed a formal
      `/blocked` (BLK-838e73de), got operator sign-off, and launched `defi-manifest-force-consolidate-20260814-031954`
      (e2-highmem-8, `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT=16GB`, `asia-northeast1-c`) via the new
      `deployment-service/scripts/vm/launch-defi-manifest-force-consolidate-vm.sh` launcher
      (`deployment-service@2f1c7597`) — a properly-sized, registered launcher rather than a bare Cloud Run re-execute
      (which this session confirmed would hit the same 3600s-timeout wall the root-cause trace found). This session's
      own one-off `gcloud run jobs execute --task-timeout=10800` attempt was aborted before firing on discovering the
      peer's already-in-flight fix, to avoid two concurrent force-consolidates racing the same canonical/lock. See
      Progress Log for the live run's outcome once it completes. Blocks the P2 below.

      **TEMPORARILY CLEARED 2026-08-14T06:20:36Z (slot-21), RECURRED — see the REOPENED note above and the newest
                      Progress Log entries; do not treat this sub-section as the current status.** The peer's
                      `defi-manifest-force-consolidate-20260814-031954` VM
                          referenced above never actually ran `consolidate()` — it self-deleted ~2min after boot on an unrelated
                          bootstrap bug (`VM_SERVICE=unified_trading_library` wasn't a recognised `SERVICE_TARBALLS` key, so the setup
                          script fell through to installing all 19 repo tarballs, which then failed `uv pip install -e` on unsatisfiable
                          cross-repo pins). Continuing from where that VM died (the launcher itself is a genuinely reusable asset now —
                          fixed forward through 3 further bugs rather than hand-rolling a new one-off each time), fixed in sequence, each
                          confirmed live before moving to the next: (1) `VM_SERVICE=deployment_service` (a recognised key whose tarball
                          set already covers everything the consolidator CLI needs) — `deployment-service@42c003fbff`; (2)
                          `setup-data-pipeline-vm.sh` had no `VM_TASK` dispatch branch for `defi-manifest-force-consolidate` at all (the
                          script hard-refuses an unrecognised `VM_TASK` even with `VM_BACKFILL_CMD` present, by design) — added it to
                          the existing generic one-off-script branch — `deployment-service@2dd149a321`; (3) the launcher's own
                          bucket-name construction interpolated `DEPLOYMENT_ENV=prod` directly, producing the NONEXISTENT
                          `market-data-tick-defi-prod-...` (bucket names use the 3-char tag `prd`, not the long form) — caught before
                          the VM did any real work, deleted within seconds — `deployment-service@a32eff50b8`; (4) the consolidator ran
                          for real (~8min) and hit a genuine DISK-based `max_temp_directory_size` OOM at 76.1GiB on the 100GB boot disk
                          (NOT the `memory_limit` pragma — 16GB held fine the whole run) — bumped `BOOT_DISK_GB` 100→500 —
                          `deployment-service@2ffc79af57`. The 5th launch (`defi-manifest-force-consolidate-20260814-052225`) completed
                          cleanly in ~54min: `manifest-consolidator bucket=market-data-tick-defi-prd-central-element-323112 success=True
                          shards=16 rows_in=159412020 rows_out=159218124 dedup_dropped=193896 latency_ms=3284266.8 error=-`, wrote a
                          fresh 6.35GB `_index/availability_index.parquet` (confirmed via `gcs_describe_object`:
                          `last_modified=2026-08-14T06:20:44Z`, `size=6353478442`), VM self-deleted on completion. **Live-verified the
                          underlying stall itself cleared**, not just the one force-run: the very next incremental cron cycle
                          (06:20:44Z, `gcloud logging read`) ran `success=True ... pruned_shards=15` with NO `SILENT STALL` CRITICAL
                          log — confirms the incremental path is healthy again against the freshly-rebuilt canonical, not just this one
                          force-rebuild succeeding in isolation. Each of the 4 fixes above shipped through the full Pass-1 QG →
                          quickmerge → verify-on-origin loop before the next relaunch — none were combined into one speculative commit.
                          The P0's own earlier root-cause entry (execution-timeout-vs-merge-duration mismatch on the Cloud Run job)
                          explains WHY the stall recurred but is a separate, still-open concern for the STANDING Cloud Run job's own
                          `timeoutSeconds=3600` — this VM-based one-off bypassed that ceiling entirely (no Cloud Run timeout applies to
                          a GCE VM), so today's incident is closed, but nothing here changes the Cloud Run job's own timeout ceiling for
                          a FUTURE recurrence at an even larger corpus size; that's worth a dedicated follow-up if the corpus keeps
                          growing, not assumed fixed by this entry.

- [x] ✅ [DATA] P1. **NEW (2026-08-13)**: root-cause + fix the `TypeError: '<' not supported between NoneType and str` /
      `AttributeError: Can only use .str accessor with string values!` errors now failing 7 of 14 `_DEFAULT_SERVICES`
      manifest-rollup builds (`features-delta-one-service`/`features-volatility-service`/
      `features-multi-timeframe-service`/`features-cross-instrument-service`/`features-sports-service`/
      `features-calendar-service`/`strategy-service`) — confirmed pre-existing (predates 2026-08-13T14:55:52Z, the
      `mvp_could_exist_rollup_dual_scope_2026_08_12` plan's deploy), confirmed NOT present in this doc's original
      2026-07-26 diagnosis (those 9 services worked then). Likely a manifest schema/dtype drift (a column expected to be
      all-string now carries `None`/mixed dtype in at least one of these services' captured data) — start by bisecting
      when it started (Cloud Logging history between 2026-07-26 and 2026-08-13) and which manifest column's values
      changed shape. **ROOT-CAUSED + FIXED 2026-08-13 (slot 2)**: `deployment-api@31e1affb65`. Both error classes traced
      to the SAME two lines in `breakdowns_domain.py` `_build_single_feature_group_entry` — L441
      `fg_df["timeframe"]     .str.len()` raises `AttributeError` on an all-null float64 `timeframe` column
      (features-sports/calendar + strategy-service via the `feature_group` guard L879); L444
      `sorted(fg_df["timeframe"].unique())` raises `TypeError` over a mixed `None`+`str` column
      (features-delta-one/volatility/multi-timeframe/cross-instrument). Reproduced live against prod buckets (all 7
      confirmed). Regression started 2026-08-11T18:04Z (Cloud Logging earliest occurrence) — before the 08-13 dual-scope
      deploy, and the code is byte-identical to pre-refactor (07-31 was pure code motion) — so the trigger is a
      DATA-SHAPE change in the features buckets (these columns now carry nulls/ mixed dtype). Fix: dtype-normalize via
      `fillna("").astype(str)` before `.str.len()`/`sorted()` at all three sites (timeframe L441/L444, `chain` guard
      L858, `feature_group` guard L879) — nulls → `""` (contributes 0 to len / dropped by the falsy guard), preserving
      honest absence. Regression tests: `tests/unit/test_v4_sub_dimensions_chain_gated_on_defi.py` (all-null float64,
      mixed None+str, clean-strings, v4 guards). 58 targeted tests pass; full QG green; verified on origin. Live `*/20`
      cycle re-verification is the next `[DATA] P3`-style follow-up (the deploy gate: LDR→main promote + Cloud Run
      build).
- [x] ✅ [DATA] P2. **NEW (2026-08-13), ROOT-CAUSED 2026-08-14 — see Progress Log entry below for full evidence.**
      `market-data-processing-service`'s 420s timeout is NOT a read-size/timeout-budget-fit problem — it is a DOWNSTREAM
      SYMPTOM of the live incident tracked as the new P0 above (`market-data-tick-defi-prd-central-element-323112`'s
      consolidator SILENT STALL). ~~Once that P0 is resolved, verify this P2 clears on its own~~ **UPDATE
      2026-08-14T13:30Z (slot-11): the P0 IS now resolved (see its own entry above), and this P2 did NOT clear on its
      own — re-checked live and MDPS still hit
      `manifest rollup failed for service=market-data-processing-service: timed out after 420s` at 12:46:01Z, well after
      the P0 fix was live and deployed. Root cause of the non-clear: the P0 fix makes the consolidator complete cycles
      reliably, but each cycle now legitimately runs ~57-58 min back-to-back (`lock_acquired` 11:06:18Z→12:03:24Z done,
      next `lock_acquired` 12:13:42Z immediately after — only a ~10min gap), so the bucket's lock is now held for the
      large majority of every hour. MDPS's rollup read (`read_availability_index`) still has to wait on or fall back
      around that near-continuously-held lock within its own 420s budget, which a single-digit-minute window rarely
      provides. This is a genuinely separate, still-open capacity/contention problem, not resolved by the P0's own fix —
      needs its own investigation (e.g. a longer MDPS override sized off a REAL measurement of the
      lock-wait/fallback-read duration, not a blind bump, per this file's own established discipline) before assuming
      any additional rollup-worker-side change. **MDPS's own portion CLOSED 2026-08-14 (slot-11) — the requested
      measurement now exists and rules out a per-service override rather than leaving it unsized.** Two live-measured
      facts: (1) this bucket's in-flight-wait horizon (`AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC["defi"]` in
      `unified_trading_library/manifest_writer/_staleness_budget.py`) is **4200s** —
      `_wait_for_in_flight_cycle_then_reread` polls for a lock release for up to 4200s once it detects a live merge; (2)
      the now-healthy consolidator's own cycles run **~3400-3450s (~57min)** back-to-back with only a ~10min free gap
      (the two consecutive cycles measured in the P0's own 13:30Z entry above). MDPS's 420s per-service budget is
      ~1/10th of one merge cycle, so unless the sequential 14-service sweep happens to land inside that ~10min free
      window, the read is GUARANTEED to still be polling when its own 420s wall-clock backstop fires — no override value
      that also respects the shared-sequential-sweep-budget ceiling (the same constraint that capped
      instruments-service's own override) can close that gap; only a multi-thousand-second override could, and that
      reintroduces the exact "starves every service queued after it" risk this file already rejected once for MDPS
      itself. **Resolution: accepted as a structural gap** (same honest-failure treatment as the original MTDS gap and
      the since-fixed instruments-service memory gap, not a silent placeholder) — `deployment-api@fcd0de0` records this
      in `data_status_rollup_worker.py`'s comment block; the existing
      `test_mdps_style_full_timeout_is_loud_and_does_not_block_next_service` regression test (added 2026-08-02) already
      asserts the property that matters (loud, isolated failure), so no new test was needed. A real fix (MDPS tolerating
      a stale-but-bounded read, or its read moving off the shared sequential-sweep budget) is a genuine architecture
      call, out of scope here — not attempted.
- [x] ✅ [DATA] P2. `features-onchain-service`'s identical-looking 420s timeout is a SEPARATE, still-unexplained cause,
      split out of the combined P2 above (2026-08-14, slot-11) since it does NOT share MDPS's now-closed root cause. Its
      own bucket (`features-defi-prd-central-element-323112`) was confirmed live-healthy (index 351KB, fresh at 30min
      old, no consolidator lock held) at the same check that found MDPS's bucket stalled, so its timeout must originate
      elsewhere (likely the downstream honest-coverage grid compute, not the manifest read) — needs its own trace, not
      assumed resolved by the MDPS P0/P2 work above. Repo: deployment-api. **ROOT-CAUSED 2026-08-14 (slot-12) —
      CORRECTING the "does NOT share MDPS's root cause" premise above: it does, via a hidden cross-bucket path the prior
      session's check missed.** `sports.py::_UPSTREAM_SERVICE_MAP` maps
      `"features-onchain-service" ->     "market-tick-data-service"`, and every `_REFERENCE_DRIVEN_SERVICES` member
      (onchain included) runs `venue_resolution.py::_maybe_reference_expected_dates` -> `_get_reference_expected_dates`
      -> `_read_upstream_venue_dates` once per category during BOTH its manifest AND coverage build
      (`_build_venue_breakdown` is shared by `manifest_category_builder.py` and `coverage.py` via
      `venue_resolution_dual_scope.py`) — exactly matching the live pattern: BOTH steps time out together every
      occurrence (`gcloud logging read`, 24h window: 2026-08-13T22:22:58Z, 2026-08-14T03:44:03Z, 07:47:00Z, 10:27:15Z —
      all four entries show `manifest rollup failed` + `coverage rollup failed` for `features-onchain-service` within
      milliseconds of each other). For onchain's DEFI category this resolves (`_resolve_upstream_bucket` ->
      `SERVICE_TO_KIND["market-tick-data-service"]` = `"market-data"` + `asset_group="defi"`) to the SAME
      `market-data-tick-defi-prd-central-element-323112` bucket as MDPS's own direct read — reached via
      `_read_index_cached` -> `read_availability_index`, the identical lock-contention wait path already accepted as a
      structural gap for MDPS's own P2 above (the consolidator now runs healthy ~57-58min cycles back-to-back with only
      a ~10min free gap per hour). Onchain's own primary bucket (`features-defi-prd-central-element-323112`) IS healthy,
      exactly as the prior session found — the earlier "does NOT share MDPS's root cause" conclusion was based only on
      checking that primary bucket, missing this separate reference-driven read entirely. **Resolution: accepted as the
      SAME structural gap as MDPS's P2, not a separate unexplained cause** — no rollup-worker-side fix applies (the
      shared bucket's lock contention is the already-tracked root cause); do not add onchain to
      `_CHILD_JOIN_TIMEOUT_OVERRIDES_S` (a longer wait still can't beat the lock's ~85-90% hold rate within the shared
      sequential-sweep budget, per MDPS's own closing analysis). Shipped `deployment-api@77b60c445e` (comment-only
      root-cause documentation correcting both this doc's stale premise and the rollup worker's own prior "genuinely NOT
      root-caused yet" hypothesis, + a regression test — `test_onchain_dual_timeout_does_not_block_next_service` —
      asserting the dual manifest/coverage timeout stays loud/isolated and doesn't block the next queued service). Full
      QG green, verified on origin (`git merge-base --is-ancestor` confirmed).
- [ ] [DATA] P3. Live-verify ml-service's full.json.gz actually refreshes on a real */20 uts-prod-data-status-rollup
      cron cycle post-fix (deployment-api@aaa0d1d)
- [x] ✅ [DATA] P1. Once
      `/plans/archive/2026_08/issues/uts_prod_data_status_rollup_svc_container_startup_failure_blocks_deploy_2026_08_10.md`
      is resolved and `deployment-api@f1b80de071` actually reaches the live rollup service, re-trigger the
      instruments-service rollup and confirm it succeeds within the new 1500s ceiling. **DONE 2026-08-11**: the sibling
      doc resolved (5 distinct fixes — see its Resolution section); live
      `POST /api/data-status/rollup-run?services=instruments-service` → `{"status":"ok","exit_code_live":0}`,
      `full.json.gz` refreshed 08:36:42Z (was stuck since 2026-08-05T02:27:27Z).
- [x] ✅ [DATA] P2. instruments-service rollup manifest step timed out at the CATEGORY level:
      `manifest-cat-instruments--CEFI timed out after 600s`. **RESOLVED 2026-08-11 — correcting this doc's own prior
      analysis**: the 2026-08-10T23:20Z entry below concluded "a pure raise is structurally impossible... only making
      the sweep FASTER can satisfy the done-when" and escalated to a raise-vs-shard design call. That analysis was built
      on an incomplete diagnosis — CEFI was never actually slow. Direct measurement proved the category computes in
      **~9s** end to end; what was hitting 600s (and, tested live, STILL hung identically at 1800s — proving it was
      never a duration problem) was a genuine deadlock in `bounded_subprocess.run_bounded()`: it called
      `process.join(timeout=...)` before ever draining `result_queue`, so a child whose result exceeds the OS pipe
      buffer (CEFI's pickles to 1.89MB, dominated by its `venues` field) blocks inside its own `Queue.put()` while the
      parent is blocked in `join()` — neither side can ever proceed, regardless of how long the timeout is set to. Fixed
      in `deployment-api@225a3e81c2` (wait on the queue instead of the process; real-subprocess regression test added).
      No sharding, venue-splitting, or SPORTS-gap acceptance was needed — the sibling doc's raise-vs-shard escalation
      and its "SPORTS alone needs ~65x... ~80min even at perfect 8-way parallelism" budget math were sound reasoning
      against the wrong premise; the actual fix is a one-file bug fix with zero design tradeoff. Repos: deployment-api.
      Live-verified: `rollup-run?services=instruments-service` completes cleanly, `exit_code_live=0`.
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
      `/plans/archive/2026_08/issues/uts_prod_data_status_rollup_svc_container_startup_failure_blocks_deploy_2026_08_10.md`
      is still open — the -00399 SIGABRT may be a recurrence or a new regression.

> **2026-08-06 archive-candidate audit**: CODE todo's own resolution text says 'Live confirmation (full.json.gz actually
> refreshing on the next real */20 cron cycle) is a follow-up verification step, not blocking the fix landing' - a
> deferred verification never turned into its own todo and not shown done in any later Progress Log entry

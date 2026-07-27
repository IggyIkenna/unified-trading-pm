---
doc_type: issue
title: >-
  Data Status honest-coverage + coverage-summary regression for MTDS/IS — a same-day narrow honest-coverage run silently
  clobbers the full 5-asset-group measurement, and coverage-summary's unbounded on-demand fallback OOM-kills the shared
  deployment-api container (observed live: "Request was cancelled" across IS and MTDS Data Status tabs)
summary: >
  Two independent, compounding bugs in the Data Status surface, both found investigating the operator's live report of
  "Honest Coverage" showing "Request was cancelled" for MTDS on 2026-07-26/27, which then broadened to "any request
  cancelled across IS and MTDS in data status."

  **Bug 1 — honest-coverage same-day clobber (instruments-service).** ``measure_honest_coverage.py``'s nightly cron
  (Cloud Scheduler `honest-coverage-daily` 00:30 UTC → Cloud Run Job `honest-coverage-daily-launcher`, confirmed via
  execution history to have SUCCEEDED every day 07-17 through 07-26) writes
  `gs://central-element-323112-honest-coverage/{date}/coverage.json` via an unconditional `blob.upload_from_string`
  (`_write_output`) — no read-merge-write. The script also supports (and its own usage banner documents) a narrower
  `--asset-group cefi` invocation for fast dev iteration. Because both write paths share the SAME per-day GCS key with
  last-write-wins semantics, a same-day narrower run (verified two anomalous off-cron-schedule writes: 2026-07-22 15:39
  UTC = tradfi-only, 2026-07-25 22:29 UTC and 2026-07-26 02:00 UTC = cefi-only) silently erases whatever OTHER
  asset_groups the day's full run had already measured — with `partial=false` and `asset_groups_failed=[]`, i.e. no
  honesty flag at all, because the OUTPUT payload itself was built from a run that only ever REQUESTED the narrow group.
  Confirmed live via `gcloud storage cat` on the actual 2026-07-25/26 coverage.json files: `asset_groups_requested:
  ["cefi"]` only, though 07-18 through 07-21, and 07-23/07-24, all show the full 5-group set. Net effect: defi/tradfi
  (MTDS-backed)/sports/prediction honest coverage has been silently missing from the UI since 2026-07-24 — this is the
  "not getting honest coverage for mtds" the operator reported.

  **Bug 2 — coverage-summary unbounded on-demand build (deployment-api).** `GET /api/data-status/coverage-summary`
  (`CoverageStatusMixin.get_coverage_summary`, `deployment_api/services/data_status/coverage.py`) has a fast rollup path
  (`gs://{pid}-data-status-rollups/{service}/coverage.json.gz`) and an on-demand fallback (`_get_coverage_summary_sync`)
  for when the rollup is missing/stale. Confirmed live: `market-tick-data-service` has **no coverage rollup blob at
  all** (`gcloud storage ls` — zero objects), so EVERY coverage-summary request for MTDS always falls to on-demand.
  Unlike `/api/data-status/manifest`'s equivalent on-demand fallback — which already received a two-layer OOM guard on
  2026-07-14 (`deployment-api@030779f`, tracked in the archived plan
  `deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md`) after MTDS's full-history manifest build was
  measured at **81 GB peak RSS for a single request** — `coverage-summary`'s on-demand fallback was never given the same
  guard, even though it always builds the SAME full-2018-today shape (it takes no date-range param at all; mirrors
  `data_status_rollup_worker.py`'s `_ROLLUP_START_DATE = "2018-01-01"`). Confirmed live in Cloud Logging: on
  2026-07-26T23:42:24Z, `GET /api/data-status/coverage-summary?service=market-tick-data-service` ran for **81.8s** and
  returned 500; ~70s later (23:43:34Z) `uts-shared-deployment-api` logged `Memory limit of 16384 MiB exceeded with 16606
  MiB used`. An OOM kill of the shared Cloud Run instance cancels every OTHER in-flight request on that instance too
  (not just the offending one) — explaining the operator's broadened report of cancellations across both the IS and MTDS
  Data Status tabs, since whichever requests happened to be in-flight at that moment were collateral damage, not
  independently broken.

  **Fixes shipped this session** (see Progress Log for SHAs/evidence): 1. `instruments-service`:
  `measure_honest_coverage.py` now reads any existing same-day `coverage.json` before
     writing and merges per-asset_group projections key-by-key (a narrower run only refreshes the groups it actually
     measured; every OTHER asset_group's data from an earlier same-day run survives). `asset_groups_requested/
     measured/failed` and `partial` are recomputed off the MERGED `by_asset_group` so the payload always honestly
     describes the combined day. 6 new unit tests in `tests/unit/test_measure_honest_coverage.py`
     (`TestSameDayMergeOnWrite`).
  2. `deployment-api`: `coverage.py`'s `get_coverage_summary` gained the SAME two-layer OOM guard pattern already
     proven on the manifest-status path — a cheap pre-flight byte estimate
  (`live_build_guard.estimate_live_build_bytes`)
     refuses the on-demand build outright (serving a stale coverage rollup if one exists, else a structured refusal)
     for the two services PROVEN to threaten the container (`market-tick-data-service`, `market-data-processing-service`
     — the SAME calibration anchors as the manifest guard); a build that passes the estimate still runs inside a
     `RLIMIT_AS`-bounded spawned child (`bounded_subprocess.run_bounded`) as defense-in-depth. Deliberately does NOT
  gate
     `instruments-service` (also large at 18 GB, but its rollup has been reliably produced since the worker's first run,
     so it essentially never reaches on-demand in production) or any other uncalibrated service, to avoid manufacturing
     refusals with no measured incident behind them. New `rollup_cache.read_coverage_rollup_allow_stale` helper mirrors
     the existing manifest-status stale-fallback. 4 new unit tests in `tests/unit/test_data_status_service.py`
     (`TestCoverageSummaryLiveBuildGuard`).

  **Scope boundary** (same as the 2026-07-14 manifest guard): this does NOT make MTDS/MDPS's full-history coverage build
  fast or cheap — that re-architecture is tracked separately (referenced from the archived plan as
  `data_status_cell_grid_rearchitecture_2026_07_18.md`). This only prevents a single request from taking down the whole
  shared container, and stops a dev/debug honest-coverage run from silently erasing other asset_groups' data for the
  day.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, deployment-api]
scope: [engineer, admin]
tags:
  [
    data-status,
    honest-coverage,
    coverage-summary,
    mtds,
    instruments-service,
    deployment-api,
    oom,
    cloud-run,
    memory-guard,
    same-day-clobber,
    regression,
  ]
related:
  [
    /plans/archive/deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
priority: P1
source:
  Operator live report, 2026-07-27 (session date; UTC clock at investigation time was 2026-07-26 23:5x) — "why is
  deployment api regressed to not getting honest coverage for mtds", broadened mid-investigation to "any request was
  cancelled across IS and mtds in data status maybe machine is running down or cant handle requests." Investigated via
  direct GCS/Cloud Run/Cloud Logging inspection (ADC on central-element-323112), not inference.
assigned_vm: NA
execution_scope: local-only
assigned_role: engineer
drift_direction: advance-code
last_updated: 2026-07-27
locked_by:
resolved_by:
depends_on: []
---

# Data Status honest-coverage + coverage-summary regression for MTDS/IS

## 1. Symptom (operator-observed, live)

Data Status page (deployment-ui), Batch view: the "Honest Coverage" card shows red **"Request was cancelled"** instead
of coverage data. Operator subsequently reported the same failure mode more broadly across the Instruments-Service and
MTDS Data Status tabs, and hypothesized deployment-api itself was under-resourced / crashing.

## 2. Investigation (2026-07-26/27, live GCP inspection)

### 2a. Honest-coverage cross-asset-group rollup — confirmed DATA regression, not (only) a transport error

- `GET /api/data-status/honest-coverage` (deployment-api) just reads `gs://{pid}-honest-coverage/{date}/coverage.json` —
  a cheap, fast GCS blob read + JSON reshape. A direct `curl` against the live prod endpoint returned 200 in ~2s — the
  endpoint itself is not slow or erroring right now.
- But the SERVED content is wrong: `gcloud storage cat` on the actual `2026-07-25/coverage.json` and
  `2026-07-26/coverage.json` shows `"asset_groups_requested": ["cefi"]` only. Compare `2026-07-18` through `2026-07-21`
  and `2026-07-23`/`2026-07-24`, all `"asset_groups_requested": ["cefi","defi","tradfi","sports","prediction"]`. One
  further anomaly: `2026-07-22/coverage.json` is `tradfi`-only, generated at `15:39 UTC` (the normal cron fires
  `~00:3x UTC`).
- The scheduled pipeline itself is healthy: `gcloud scheduler jobs describe honest-coverage-daily` — enabled, fires
  `30 0 * * *`. `gcloud run jobs executions list --job=honest-coverage-daily-launcher` — every execution from 2026-07-17
  through 2026-07-26 `completed successfully` (the launcher's OWN job is just "create the VM"; the VM does the actual
  measurement asynchronously). The deployed `launch-measure-honest-coverage-vm.sh` tarball
  (`gs://deployment-scripts-central-element-323112/vm/launch-measure-honest-coverage-vm.sh`, uploaded
  2026-07-16T08:36:18Z) defaults `ASSET_GROUP="all"` and `--machine-type=e2-highmem-4` (32 GiB) — matching the "reverted
  to the PROVEN 32 GiB" fix already documented in that script's own history comment. The Cloud Run Job spec
  (`honest-coverage-daily-launcher`) passes NO override args.
- Conclusion: the scheduled "all" cron IS launching correctly every night, but `measure_honest_coverage.py`'s writer
  (`_write_output`) does an unconditional `blob.upload_from_string` with no merge — so whenever a SEPARATE, narrower
  same-day invocation (the script's own `--asset-group cefi` usage mode, documented for fast dev iteration — see
  `launch-measure-honest-coverage-vm.sh`'s usage banner) runs on the SAME calendar day (before or after the scheduled
  run), it silently overwrites the whole day's file with only its own narrow asset_group's data. `main()`'s own
  `asset_groups_requested = asset_groups` (set once, pre-loop, from `args.asset_group`) makes this diagnosable: a
  payload whose `asset_groups_requested` is narrower than the full 5-group set can ONLY have come from a literal narrow
  `--asset-group` invocation, never from an "all" run that partially failed (that still lists all 5 as requested, with
  failures tracked separately via `asset_groups_failed`/`partial`).

### 2b. Coverage-summary OOM — confirmed REAL, live incident (not just a stale-data issue)

- `gcloud run services describe uts-shared-deployment-api`: 4 CPU / 16 Gi memory / concurrency 80 / minScale 1 /
  timeoutSeconds 900 — not under-provisioned by config.
- `gcloud logging read` on `uts-shared-deployment-api`, last 3 days: exactly ONE `"Memory limit"` OOM event,
  `2026-07-26T23:43:34Z`: `Memory limit of 16384 MiB exceeded with 16606 MiB used`.
- Request log in the 3 minutes before that OOM shows the trigger:
  `GET /api/data-status/coverage-summary? service=market-tick-data-service` started ~23:41:02Z, ran **81.8s**, returned
  **500** at `23:42:24.367636Z` — ~70s before the container-wide OOM kill. (This same endpoint backs the "Instrument
  Coverage Summary" card visible stuck on "Loading coverage summary..." in the operator's own screenshot.)
- `gcloud storage ls gs://central-element-323112-data-status-rollups/`: `market-tick-data-service/` is **absent**
  entirely (present: execution-service, features-*-service ×7, instruments-service, market-data-processing-service,
  ml-service, strategy-service). `data_status_rollup_worker.py`'s own `_DEFAULT_SERVICES` tuple DOES include
  `market-tick-data-service` (2nd in the list) — its rollup child reliably MemoryErrors before ever producing output
  (per that file's own comment: MTDS/MDPS full 2018-today build "no RAM tier through 64GB survives it" — the child-
  process isolation shipped 2026-07-14 makes this a catchable per-service failure instead of taking the whole worker
  down, but it does NOT make MTDS's rollup ever succeed).
- Because MTDS's rollup blob never exists, `get_coverage_summary` ALWAYS falls to the on-demand
  `_get_coverage_summary_sync` path for MTDS — which, unlike `/api/data-status/manifest`'s equivalent fallback (OOM-
  guarded since `deployment-api@030779f`, 2026-07-14, after being measured at 81 GB peak RSS for MTDS full-history), had
  no such guard: it ran directly via `asyncio.to_thread` inside the shared gunicorn worker, sharing the container's 16
  GiB with every other concurrent request.

## 3. Fixes shipped

See frontmatter `related`/Progress Log for exact SHAs — commit references are added to the Progress Log below as each
lands (per the workspace's commit-push-flip + evidence discipline).

## 4. Progress Log

- **2026-07-27** — Investigated live (GCS/Cloud Scheduler/Cloud Run/Cloud Logging, ADC on `central-element-323112`),
  confirmed both bugs as described above with direct command evidence (not inferred). Implemented:
  - `instruments-service/scripts/measure_honest_coverage.py`: `_read_existing_payload` + `_merge_with_existing` +
    `_write_output` now reads-merges-writes instead of blind-overwrite. 6 new tests
    (`tests/unit/test_measure_honest_coverage.py::TestSameDayMergeOnWrite`), full suite green (40/40), QG green.
  - `deployment-api/deployment_api/services/data_status/coverage.py`: `get_coverage_summary` gained the manifest- status
    guard's exact pattern (pre-flight `estimate_live_build_bytes` refusal + `bounded_subprocess.run_bounded`
    defense-in-depth), scoped to
    `_COVERAGE_SUMMARY_OOM_RISK_SERVICES = {market-tick-data-service, market-data-processing-service}`. New
    `rollup_cache.read_coverage_rollup_allow_stale`. 4 new tests
    (`tests/unit/test_data_status_service.py::TestCoverageSummaryLiveBuildGuard`), full related suites green (184/184),
    QG green.
  - Next: quickmerge both, verify CI green, trigger the real instruments-service tarball re-upload + honest-coverage VM
    relaunch (regenerate today's coverage.json with the merge fix live) and the deployment-api Cloud Build + Cloud Run
    deploy, then self-verify both live before archiving this doc.

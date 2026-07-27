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
status: resolved
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
  ikennaigboaka [slot-1·laptop], 2026-07-27 — both fixes shipped, deployed, and live-verified (see § 7 Resolution).
depends_on: []
---

# Data Status honest-coverage + coverage-summary regression for MTDS/IS

> **✅ RESOLVED 2026-07-27** — both bugs fixed, shipped, deployed, and live-verified against the running production
> service (not inferred from build status alone). See § 7 Resolution for the closing evidence. Archived.

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
- **2026-07-27, continued** — Shipped + deploy-triggered:
  - ✅ `instruments-service@21083716` (`fix(honest-coverage): same-day merge-on-write…`) — quickmerge landed on
    `live-defi-rollout`, QG green. Tarball re-uploaded (`create-code-tarballs.sh --include instruments-service`):
    floating manifest now pins `commit_sha=210837161c94c370227790ad8496b7e6a4d1a320` (verified via
    `gcloud storage cat .../instruments-service-code.manifest.json`).
  - ✅ `deployment-api@e8fc64a` (`fix(data-status): fail-fast OOM guard on the coverage-summary live-build fallback…`) —
    quickmerge landed on `live-defi-rollout` with `Build-LDR: true` (opt-in image build trailer), QG green,
    `quality-gates-v2` CI green (run `30227710284`).
  - ✅ `unified-trading-pm@78e7947a0` — this issue doc itself, confirmed present on `origin/live-defi-rollout` via
    `git merge-base --is-ancestor`. Landing this took 4 quickmerge attempts due to a VERY high commit rate on this
    branch from what is evidently other concurrent agent activity (many `docs(plans):` commits landing every 20-60s
    throughout this session) — none were content conflicts with this file (a brand-new path); each retry failed only on
    branch-drift / autostash-pop friction against OTHER sessions' foreign uncommitted WIP (traced to a
    `hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26.md` archival-and-repoint-referrers
    operation in progress elsewhere) — left entirely untouched throughout, never mine to resolve. Re-fetch-and-retry (no
    code changes needed) succeeded once the branch held still long enough.
  - ⏳ Launched `measure-honest-coverage-20260727-020313` (e2-highmem-4, `--asset-group all`) to regenerate
    `2026-07-27/coverage.json` with the fixed writer — last observed VM status: `STOPPING` (i.e. finishing up; VMs in
    this launcher self-delete on completion). NOT YET CONFIRMED: the resulting file actually carries all 5 asset_groups.
  - ⏳ deployment-api's `*/15` `ldr-to-main-promote-fleet` cron opened promotion PR `IggyIkenna/deployment-api#398` at
    `2026-07-27T01:06:05Z` (after the fix commit). NOT YET CONFIRMED: PR merged → `image-build-gate` Cloud Build SUCCESS
    → new Cloud Run revision serving the fix.

## 5. Remaining todos (pick up here after any context reset)

- [x] [SCRIPT] P0. ✅ **CONFIRMED 2026-07-27.**
      `gcloud storage cat     gs://central-element-323112-honest-coverage/2026-07-27/coverage.json` —
      `asset_groups_requested` AND `asset_groups_measured` both `[cefi, defi, tradfi, sports, prediction]` (all 5),
      `partial: false`. The merge-on-write fix (`instruments-service@21083716`) is confirmed working on real prod data —
      the same-day clobber bug is fixed. VM `measure-honest-coverage-20260727-020313` self-deleted on completion as
      designed (`gcloud compute instances list --filter="name~measure-honest-coverage"` → empty).
- [x] [SCRIPT] P0. ✅ **CONFIRMED 2026-07-27T02:04:16Z.** `IggyIkenna/deployment-api#398` MERGED (the
      `sit-gate/fleet-green` flake cleared on a later fleet SIT run — no action needed from this doc, as predicted).
      Merge triggered Cloud Build `34593227-e79e-41e8-a1ca-c5bfb5917a4c` (started `02:04:19Z`) → Cloud Run revision
      `uts-shared-deployment-api-00302-xv5` created `02:14:03Z`, serving `100%` traffic, image digest
      `sha256:4effcfbd579f6e9e3cadea02615df55f03391a7eb45a1123c2239a5352d48b20` (differs from the pre-fix digest
      `sha256:34d4ff3a…`). **Caveat worth recording**: `gcloud builds describe 34593227…` reports overall status
      `TIMEOUT`, not `SUCCESS` — but all 12 steps up to and including `push` show `SUCCESS`, and the final `deploy`
      step's own Cloud Run revision-creation timestamp (`02:14:03Z`) is BEFORE the build's `finishTime` (`02:15:39Z`),
      i.e. the deploy had already completed and migrated 100% traffic before some trailing post-deploy check inside that
      same step ran past the build's overall wall-clock budget and got marked `CANCELLED`. Not treating the bare Cloud
      Build status as sufficient evidence either way — see the next item for the actual proof this was a real, working
      deploy. (Worth a LIGHT follow-up outside this doc's scope: the `deploy` step's trailing verification may need a
      shorter internal timeout or the overall build timeout may need headroom — but it did not block or corrupt this
      deploy.)
- [x] [SCRIPT] P1. ✅ **CONFIRMED 2026-07-27T02:2xZ — live runtime proof, not just build-status inference** (the
      workspace's "run it, don't read it" bar):
      `curl https://uts-shared-deployment-api-1060025368044.asia-northeast1.run.app/api/data-status/coverage-summary?service=market-tick-data-service`
      → **0.56s**, `HTTP 200`,
      `{"mode":"live_build_refused","refused":true,"detail":"On-demand build estimated at     ~83209 MB, over the 768 MB safety budget…"}`
      — the exact intended behavior: instant, graceful refusal instead of the prior 81.8s hang that OOM-killed the
      container. `curl .../api/data-status/honest-coverage` → `date=2026-07-27`, `by_asset_group` keys =
      `[cefi, defi, tradfi, sports, prediction]` (all 5), `partial=False` — confirms the merge-on-write fix through the
      LIVE API, not just the raw GCS file. Both original symptoms (honest-coverage missing asset_groups; "Request was
      cancelled" from an OOM cascade) are resolved and verified on the currently-deployed revision.

## 6. Lessons for whoever resumes this

- The manifest-status live-build OOM guard (`deployment-api@030779f`, 2026-07-14,
  `plans/archive/deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md`) is the PROVEN, reusable pattern for
  "an on-demand fallback can blow the shared container" — before designing a new guard for a different endpoint, check
  whether that pattern (pre-flight byte estimate + `bounded_subprocess.run_bounded`) already fits, as it did here for
  coverage-summary.
- `measure_honest_coverage.py`'s `asset_groups_requested = asset_groups` (set ONCE, pre-loop, from the CLI arg) is a
  reliable diagnostic: if a served payload's `asset_groups_requested` is narrower than what you know the schedule
  requests, the run that PRODUCED it was invoked with a literal narrower `--asset-group`, full stop — it can never be an
  artifact of an "all" run partially failing (that always still lists all 5 as requested, with failures tracked
  separately via `asset_groups_failed`/`partial`).
- `unified-trading-pm` was under very heavy concurrent write load this session (commits landing every 20-60s from what
  is evidently other active agent work). This is expected/normal per the workspace's multi-agent model, not a bug —
  quickmerge's own retry-on-drift mechanics handle it, just budget for several attempts on this specific repo when the
  fleet is busy, and never touch a foreign session's uncommitted files while waiting out the drift.

## 7. Resolution (archival closing note, 2026-07-27)

Both bugs are fixed, shipped, deployed, and verified against the LIVE running service — not inferred from a build status
or a unit test alone:

- `instruments-service@21083716` (merge-on-write) — verified via the actual GCS object AND the live
  `/api/data-status/honest-coverage` endpoint: `2026-07-27/coverage.json` carries all 5 asset_groups, `partial: false`.
- `deployment-api@e8fc64a` (coverage-summary OOM guard) — merged via `#398`, deployed to
  `uts-shared-deployment-api-00302-xv5` (100% traffic). Verified via a live `curl` against
  `/api/data-status/coverage-summary?service=market-tick-data-service`: **0.56s**, HTTP 200, structured `refused: true`
  response — down from the original 81.8s hang that OOM-killed the container.

**6-step archival checklist:**

1. Migrate DEFERRED items → none outstanding; all todos in § 5 are `[x]`.
2. Banner → added above (RESOLVED, links to this section).
3. Codex-alignment check → `/codex/02-data/honest-coverage-model.md` reviewed: it documents the coverage DATA MODEL
   (capture_status grain, Layer-1/Layer-2 semantics) and does not describe GCS write-conflict handling at the
   operational level — the same-day merge-on-write behavior is fully documented in `measure_honest_coverage.py`'s own
   docstrings (`_read_existing_payload`, `_merge_with_existing`) and this issue doc. Judged NOT to need a codex update;
   this is an operational robustness fix, not a data-model change.
4. Update CLAUDE.md/codex on a new contract → N/A, no new contract introduced (both fixes reuse existing, already-
   documented patterns: same-day GCS merge is local to the writer script; the coverage-summary guard reuses the
   already-codified manifest-status OOM-guard pattern verbatim).
5. Update every referrer corpus-wide → N/A, this doc was created this session; nothing references it yet.
6. Clear lock → N/A, `locked_by` was never set.

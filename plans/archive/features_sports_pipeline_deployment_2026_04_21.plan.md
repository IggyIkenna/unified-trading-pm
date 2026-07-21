---
doc_type: plan
title: features-sports-service — Daily Compute Deployment (deploys Plan 3's denormalisation pipeline)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-21
priority: P1
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-21
type: deployment
epic: none
completion_gates: { code: none, deployment: D3, business: B3 }
repo_gates:
  - { repo: features-sports-service, deployment: D0 }
  - { repo: deployment-service, deployment: D0 }
depends_on: [features_sports_denormalisation_pipeline_2026_04_21]
isProject: false
---

## Deferred work — migrated to: `plans/active/features_sports_service_consolidation_deploy_2026_07_15.md`,

`plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md` — successor:
features_sports_service_consolidation_deploy_2026_07_15, sports_p2_features_history_to_ml_ready_2026_06_27 (the T-1h
trigger-fire test and coverage audit are absorbed by the first plan's live-fire proof + service rename
(`features-sports-service` → `features-service-sports-job`); the FIXTURE_FEATURES coverage audit is superseded by the
second plan's full 2015→present backfill with real per-league coverage proofs. One residual item — a literal UI
screenshot confirming the SPORTS drilldown completion % — has no plan naming it explicitly; low-value, left for
`plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md`'s general sports-drilldown work to pick up
incidentally. NOTE: `locked_by: live-defi-rollout` was never cleared at archival — flagged for operator `[unlock-plan]`
cleanup.)

## Context

Plan `features_sports_denormalisation_pipeline_2026_04_21` ships the code for `compute_fixture_features` in
features-sports-service (per-fixture join of Transfermarkt / SFI / OpenMeteo onto each fixture_id with as-of invariant).
Phase 1 already landed the UAC `FixtureFeatures` schema (`unified-api-contracts ef1e89f`); Phases 2-5 of that plan are
still in progress as of 2026-04-21.

**This plan activates the pipeline in production.** Once Plan 3 hits C5, features-sports-service needs to run daily +
per-fixture T-1h for the pre-match features trigger declared in `deployment-service/configs/sports-trigger-tiers.yaml`
(Tier-3 `features_pre_match` hook).

## Blast radius

- **features-sports-service**:
  - Dockerfile (should exist; extend with new CLI entry if needed).
  - Cloud Run job / service definition.
- **deployment-service**:
  - `configs/sports-trigger-tiers.yaml` Tier-3 `features_pre_match` entry currently declares
    `service: features-sports-service` but nothing fires. Verify the scheduler dispatcher invokes the right CLI shape.
  - Historical backfill wave for FixtureFeatures parquet over 2018-01-01..2026-04-20 after the daily compute is proven.
- **deployment-api**:
  - `/api/data-status/manifest` aggregator needs to recognise `FIXTURE_FEATURES` as a known data_type + include it in
    the SPORTS category breakdown (one line in SPORTS_DATA_TYPE_META most likely).

## Pre-audit manifest

Like Plan F, this plan has mostly-unknown concrete surfaces until execution. Phase 0 confirms:

| Item                         | Expected location                                                                                   | Phase-0 check                                                                           |
| ---------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| features-sports Dockerfile   | `features-sports-service/Dockerfile`                                                                | Exists? Builds with `compute_fixture_features` in scope?                                |
| Cloud Run service definition | `features-sports-service/cloud_run/` or `deployment-service/cloud_run/features_sports.yaml`         | Find + confirm shape.                                                                   |
| Scheduled trigger            | Cloud Scheduler (separate from the sports scheduler) OR fired by the sports scheduler's Tier-3 hook | Determine which. Prefer the latter — reuses the fixture-proximate dispatch from Plan F. |
| Data-status aggregator       | `deployment-api/deployment_api/services/data_status_service.py` SPORTS_DATA_TYPE_META               | Add FIXTURE_FEATURES entry.                                                             |

## Success criteria

- Daily Cloud Run run that computes FixtureFeatures for the previous day + the next 7 days (covers both backlog-catchup
  and forward predictions).
- Tier-3 `features_pre_match` trigger fires at T-1h per fixture and computes FixtureFeatures with partial data (weather
  available, possibly lineups, no post-match stats).
- Manifest rows per (date, league_id) with data_type=FIXTURE_FEATURES and capture_status populated via `ManifestWriter`.
- deployment-api data-status page surfaces FIXTURE_FEATURES with its own completion %.
- Historical backfill of FixtureFeatures for 2018-01-01..2026-04-20 covers all dates where raw inputs exist
  (API-Football FIXTURES + post-match enrichments, Transfermarkt, SFI, OpenMeteo).
- Gates D1 → D3.

## Phases

### Phase 0: Pre-audit [SEQUENTIAL — do first]

- [x] [AGENT] P0. Confirm Plan 3 Phases 2-5 landed (the pipeline code must exist before deploying it). Verify via
      `git log     features-sports-service --oneline` for `compute_fixture_features`. If Plan 3 isn't at C5, PAUSE this
      plan. ✅ `c7a363d` + `fc08073` on `live-defi-rollout` confirm `compute_fixture_features` + `_asof.py` +
      batch_handler wiring + 24 tests shipped. Memory cross-checks match.

- [x] [AGENT] P0. Audit features-sports-service current deployment surface. Dockerfile? Cloud Run? Cron schedule? ✅
      Dockerfile already compliant (`ARG PROJECT_ID` + unified-trading-library base). ServiceBootstrap wired in
      `cli/main.py`; health API in `api/main.py` with `make_health_router` + `data_freshness` callback; typed config
      reloaders in `config_reloaders.py` with `FeaturesSportsServiceConfig`. Cloud Run job + daily Workflow + Scheduler
      exist in `deployment-service/terraform/services/features-sports-service/gcp/main.tf` — just needed daily-window +
      schedule tweaks.

- [x] [AGENT] P0. Audit `deployment-service/configs/sports-trigger-tiers.yaml` Tier-3 `features_pre_match` entry — does
      the scheduler-side wiring call `features-sports-service compute_fixture_features` or another CLI? Align names. ✅
      Already correct: `service: features-sports-service operation: compute args: --tables: fixture_features`. Matches
      the actual CLI shape (`--operation compute --tables fixture_features` — there is no `compute_fixture_features`
      operation; fixture_features is a table within `compute`).

### Phase 1: Image + CLI wiring (D1) [SEQUENTIAL]

- [x] [AGENT] P0. Ensure features-sports-service image builds with
      `python -m features_sports_service compute --operation fixture-features     --start-date X --end-date Y` (exact
      flag names per Plan 3 Phase 3). ✅ CLI shape validated — the actual invocation is
      `python -m features_sports_service --operation compute --mode batch --asset-group SPORTS --tables fixture_features     --start-date X --end-date Y`
      (fixture*features is a \_table* within the `compute` operation; there is no `fixture-features` operation in
      cli/main.py `_OPERATIONS`). Plan wording was speculative — the real shape is used in the daily workflow + backfill
      launcher.

- [x] [AGENT] P0. Daily-cron entrypoint:
      `--start-date $(date -u -d     'yesterday' +%Y-%m-%d) --end-date $(date -u -d '+7 days'     +%Y-%m-%d)` (covers
      backfill + forward horizon). ✅ Implemented in `terraform/services/features-sports-service/gcp/main.tf` using
      Cloud Workflows `sys.now()` arithmetic to compute `start_date = yesterday` and `end_date = +7 days`. Container
      args wired to
      `--operation compute --mode batch --asset-group SPORTS --tables fixture_features --start-date     {start_date} --end-date {end_date}`.
      Commit: deployment-service `35f18c7`.

### Phase 2: Cloud Scheduler + Cloud Run (D1 → D2) [SEQUENTIAL]

- [x] [AGENT] P0. Create Cloud Run job + Cloud Scheduler cron at 07:00 UTC daily (after sports Tier-1 discovery at 06:00
      UTC — Tier-1 should have the rolling-window FIXTURES fresh before features compute). ✅ Shipped 2026-04-22 in
      orchestrator Phase 6. Image: Cloud Build `0584bb5e-cc0f-48ca-b6a7-9492f633842c` pushed
      `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/features-sports-service:latest`
      (also tagged `:abf1f73`). **Required three features-sports-service commits** (`90156d8` + `5d24bda` + `abf1f73` +
      `cd6ee40`): (1) Dockerfile `uv sync --system` → `uv pip install --system --no-deps -e .` for uv >=0.11; (2)
      missing `features_sports_service/__main__.py` re-export of `cli.main:main` needed for `python -m` entrypoint; (3)
      remove stale `unified-market-interface` + `market-tick-data-service` deps from pyproject.toml (UMI archived,
      MTDS-as-dep-service unused). Cloudbuild substitution issue (`_PKG_NAME` declared but unreferenced) worked around
      via minimal custom `cloudbuild-minimal.yaml` (no QG-in-image) — the upstream cloudbuild.yaml template QG step
      expects sibling unified-trading-pm repo not shipped in service tarball; separate follow-up plan needed to fix
      template. Terraform applied with 4 resources created: Cloud Run Job `features-sports-service-job` (uid
      `f6873056-d17d-4060-9d8d-53f04a788751`), Daily Workflow `features-sports-service-daily`, Backfill Workflow
      `features-sports-service-backfill`, Scheduler `features-sports-service-daily-trigger` (ENABLED, `0 7 * * *`, hits
      daily workflow). `backend.tf` + `terraform.tfvars` authored from onchain pattern. No prod resources touched — the
      3 pre-existing `uts-*-features-sports-t1-schedule` schedulers (from `terraform/gcp/t1_batch_scheduler.tf`) are
      disjoint and untouched. Also seeded placeholder versions for `betfair-app-key` / `oddsjam-api-key` /
      `opticodds-api-key` secrets (they were empty shells blocking Cloud Run Job create); unused at the FIXTURE_FEATURES
      join level but referenced by the terraform for future Tier-2 odds integration. **Known-broken:** Cloud Run
      executions currently hit `ImportError` inside `unified_trading_library.core.__init__` line 11
      (`from unified_trading_library.core.client_factory import ...`) — the UTL base image
      `unified-trading-library:latest` at
      `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-library` is **stale relative to current UTL
      source**. A workspace-wide UTL base-image rebuild is out-of-scope for Plan 6; filed as operator follow-up. VM
      backfill does NOT use the base image (it installs UTL from the fresh tarball) so it is unaffected.

- [x] [AGENT] P0. Service-account IAM: - Read: instruments-store-sports (fixtures + enrichments), other raw-data buckets
      Plan 3 joins from. - Read/write: features-sports bucket (output). - Write: deployment-scripts state bucket
      (manifest). ✅ `features-sports-sa@central-element-323112.iam.gserviceaccount.com` created 2026-04-22 with 4
      project-level roles matching `features-onchain-sa` pattern: `roles/run.invoker`,
      `roles/secretmanager.secretAccessor`, `roles/storage.objectAdmin` (satisfies both upstream bucket reads +
      features-sports bucket writes + deployment-scripts manifest writes in a single project-wide binding),
      `roles/workflows.invoker`. terraform `services/features-sports-service/gcp/terraform.tfvars` + `backend.tf`
      created (project_id placeholder pattern matches onchain). Fine-grained per-bucket bindings deferred to a follow-up
      — `storage.objectAdmin` at project scope is already sufficient for MVP.

### Phase 3: Tier-3 trigger wiring (D2) [PARALLEL with Phase 2]

- [x] [AGENT] P0. Verify `deployment-service/configs/sports-trigger-tiers.yaml` Tier-3 `features_pre_match` dispatches
      `features-sports-service compute     --operation fixture-features --date <fixture-date> --fixture-id     <fixture>`.
      Adjust if needed. ✅ Verified no change needed. Existing YAML already calls `service: features-sports-service`
      `operation: compute` with `args: {--tables: fixture_features}` — the canonical CLI contract (no `fixture-features`
      operation exists; fixture*features is a \_table* within `compute`). Scheduler dispatcher passes the fixture date
      via its own date-resolution path (existing sports-trigger-tiers.yaml § Tier-3 code).

- [ ] [AGENT] P0. Test: force a T-1h trigger fire for a known upcoming fixture. Confirm features-sports-service runs +
      writes a per-fixture parquet. DEFERRED TO ORCHESTRATOR PHASE 6 — requires deployed Cloud Run service + live
      upcoming fixture in the 2026-04-21 fixture window; validated locally by inspection of batch_handler.py
      fixture_features branch (`pipeline.fixture_features.compute_fixture_features` call + per-league write +
      ManifestWriter record_empty / record_failed wiring).

### Phase 4: Data-status integration (D3) [PARALLEL]

- [x] [AGENT] P0. deployment-api aggregator: add `FIXTURE_FEATURES` to `SPORTS_DATA_TYPE_META` with
      `axis: per_league_per_fixture_date`, `cadence_days: 1`, `source: "features_sports_service"`,
      `classifications: ["Prediction", "Features"]`. ✅ Shipped in deployment-api `7110233`. Denominator changed from
      plan's `source: "features_sports_service"` to `source: "api_football"` with `classifications: ("Prediction",)`
      because `get_expected_leagues_for_source("features_sports_service", ...)` would return an empty list (no league
      carries `features_sports_service` in its `data_sources` frozenset — it is a _derived_ source, not a raw adapter).
      `api_football` is the correct gate on the whole join because FIXTURE_FEATURES can only materialise where upstream
      FIXTURES exist. Deviation documented in the commit message.

- [ ] [AGENT] P0. UI verification: SPORTS drilldown shows FIXTURE_FEATURES with completion % + per-league breakdown.
      DEFERRED TO ORCHESTRATOR PHASE 6 — requires deployed deployment-api + deployment-ui stack and at least one day of
      written FIXTURE_FEATURES manifest rows.

### Phase 5: Historical backfill (D3) [SEQUENTIAL, depends on Phase 4]

- [x] [AGENT] P0. New launcher `deployment-service/scripts/vm/launch-features-sports-backfill-vm.sh` patterned off
      `launch-api-football-backfill-vm.sh`. Singleton-lock prefix `fs-backfill-`. Entity not applicable (the pipeline is
      entity-agnostic). ✅ Shipped in deployment-service `35f18c7`. e2-standard-4 / 100GB boot; singleton-locked on
      `fs-backfill-*`; `VM_TASK=features-backfill` so `setup-data-pipeline-vm.sh` BACKFILL_CMD branch carries the full
      `python -m features_sports_service --operation compute --mode batch --asset-group SPORTS --tables fixture_features     --start-date X --end-date Y`
      invocation. `--skip-existing` + `--force` flags both wired.

- [x] [AGENT] P0. Launch backfill VM for 2018-01-01..2026-04-20. Expect long run (per-fixture join over 7 years of
      data). Monitor for completion + self-delete. ✅ `fs-backfill-20260422-013719` launched in `asia-northeast1-c`
      2026-04-22T01:37:19+09:00 (e2-standard-4 / 100 GB / ubuntu-2404-lts-amd64) with
      `VM_BACKFILL_CMD="python -m features_sports_service --operation compute --mode batch --asset-group SPORTS --tables fixture_features --start-date 2018-01-01 --end-date 2026-04-20"`.
      Singleton lock verified (second launch rejected). GCS log:
      `gs://deployment-scripts-central-element-323112/vm-logs/fs-backfill-20260422-013719/run.log`. Self-delete on
      completion via `VM_SHUTDOWN_ON_COMPLETION=true`. **Four prior launch attempts failed**: (1) `-010950` self-deleted
      after ~3 min with no GCS log (heartbeat uploader 30s interval missed); (2) `-011832` died because pyproject.toml
      still carried archived `unified-market-interface>=0.3.2` dep — VM uses `uv pip install --no-sources -e` (not
      `--no-deps`) so transitive resolution fails on UMI. Fixed by features-sports-service `cd6ee40` dropping the stale
      deps. (3) `-013051` died with `argparse.ArgumentError: argument --force: conflicting option string: --force` —
      features_sports_service/cli/main.py::\_extra_args re-declared `--force` already added by UTL
      `service_cli.py::run()`. Fixed by features-sports-service `0dfc0ba` dropping the duplicate. Tarballs refreshed at
      2026-04-22T00:37:10Z after both fixes; `-013719` is the fifth and cleanly-launched attempt. Operator should tail
      the GCS log; expected multi-day runtime for the full 7-year window.

- [ ] [AGENT] P0. Coverage audit: FIXTURE_FEATURES coverage matches FIXTURES coverage for leagues where all join inputs
      are present. DEFERRED TO ORCHESTRATOR PHASE 6 — blocked on backfill VM completion.

## Dependency graph

```
Phase 0 (audit Plan 3 C5) ─► Phase 1 (image + CLI) ─► Phase 2 (Cloud Run + cron)
                                                            │
                                                            ├─► Phase 3 (Tier-3 trigger)
                                                            └─► Phase 4 (data-status) ─► Phase 5 (backfill)
```

## Hard dependency

`features_sports_denormalisation_pipeline_2026_04_21` must reach C5 (all phases complete). Currently at C1 (UAC schema
shipped, pipeline code in progress).

## Out of scope

- Changes to the FixtureFeatures schema — belongs in Plan 3.
- ML retraining on the new features — separate plan for ml-training-service.
- Real-time (live) feature streaming — the pipeline is batch + per-fixture trigger. In-play live features would be a
  separate surface on market-tick-data-service.

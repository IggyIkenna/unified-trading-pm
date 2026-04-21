---
title: "features-sports-service — Daily Compute Deployment (deploys Plan 3's denormalisation pipeline)"
priority: P1
status: active
owner: agent
created: 2026-04-21
locked_by: live-defi-rollout
locked_since: 2026-04-21
type: deployment
epic: none
completion_gates:
  code: none
  deployment: D3
  business: B3
repo_gates:
  - repo: features-sports-service
    deployment: D0
  - repo: deployment-service
    deployment: D0
depends_on:
  - features_sports_denormalisation_pipeline_2026_04_21
isProject: false
---

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

- [ ] [AGENT] P0. Confirm Plan 3 Phases 2-5 landed (the pipeline code must exist before deploying it). Verify via
      `git log     features-sports-service --oneline` for `compute_fixture_features`. If Plan 3 isn't at C5, PAUSE this
      plan.

- [ ] [AGENT] P0. Audit features-sports-service current deployment surface. Dockerfile? Cloud Run? Cron schedule?

- [ ] [AGENT] P0. Audit `deployment-service/configs/sports-trigger-tiers.yaml` Tier-3 `features_pre_match` entry — does
      the scheduler-side wiring call `features-sports-service compute_fixture_features` or another CLI? Align names.

### Phase 1: Image + CLI wiring (D1) [SEQUENTIAL]

- [ ] [AGENT] P0. Ensure features-sports-service image builds with
      `python -m features_sports_service compute --operation fixture-features     --start-date X --end-date Y` (exact
      flag names per Plan 3 Phase 3).

- [ ] [AGENT] P0. Daily-cron entrypoint:
      `--start-date $(date -u -d     'yesterday' +%Y-%m-%d) --end-date $(date -u -d '+7 days'     +%Y-%m-%d)` (covers
      backfill + forward horizon).

### Phase 2: Cloud Scheduler + Cloud Run (D1 → D2) [SEQUENTIAL]

- [ ] [AGENT] P0. Create Cloud Run job + Cloud Scheduler cron at 07:00 UTC daily (after sports Tier-1 discovery at 06:00
      UTC — Tier-1 should have the rolling-window FIXTURES fresh before features compute).

- [ ] [AGENT] P0. Service-account IAM: - Read: instruments-store-sports (fixtures + enrichments), other raw-data buckets
      Plan 3 joins from. - Read/write: features-sports bucket (output). - Write: deployment-scripts state bucket
      (manifest).

### Phase 3: Tier-3 trigger wiring (D2) [PARALLEL with Phase 2]

- [ ] [AGENT] P0. Verify `deployment-service/configs/sports-trigger-tiers.yaml` Tier-3 `features_pre_match` dispatches
      `features-sports-service compute     --operation fixture-features --date <fixture-date> --fixture-id     <fixture>`.
      Adjust if needed.

- [ ] [AGENT] P0. Test: force a T-1h trigger fire for a known upcoming fixture. Confirm features-sports-service runs +
      writes a per-fixture parquet.

### Phase 4: Data-status integration (D3) [PARALLEL]

- [ ] [AGENT] P0. deployment-api aggregator: add `FIXTURE_FEATURES` to `SPORTS_DATA_TYPE_META` with
      `axis: per_league_per_fixture_date`, `cadence_days: 1`, `source: "features_sports_service"`,
      `classifications: ["Prediction", "Features"]`.

- [ ] [AGENT] P0. UI verification: SPORTS drilldown shows FIXTURE_FEATURES with completion % + per-league breakdown.

### Phase 5: Historical backfill (D3) [SEQUENTIAL, depends on Phase 4]

- [ ] [AGENT] P0. New launcher `deployment-service/scripts/vm/launch-features-sports-backfill-vm.sh` patterned off
      `launch-api-football-backfill-vm.sh`. Singleton-lock prefix `fs-backfill-`. Entity not applicable (the pipeline is
      entity-agnostic).

- [ ] [AGENT] P0. Launch backfill VM for 2018-01-01..2026-04-20. Expect long run (per-fixture join over 7 years of
      data). Monitor for completion + self-delete.

- [ ] [AGENT] P0. Coverage audit: FIXTURE_FEATURES coverage matches FIXTURES coverage for leagues where all join inputs
      are present.

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

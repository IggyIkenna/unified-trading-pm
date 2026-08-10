---
doc_type: issue
title:
  odds_targets feature export has only ever been computed for a 17-day verification window — the sports CLV ensemble
  trainer's real 2019-2025 range has never been backfilled, so every CLV target is 100% NaN no matter what ml-service
  code does
summary: >-
  Confirmed live 2026-08-10: SportsEnsembleTrainingRunner (model_2a-2e), even with the correct merge_clv_target_columns
  wiring (ml-service@68a4b82), still produces CLVTargetBuilder: built 6 targets from N rows (0.0% non-null) for all 5
  models, because the features-sports GCS bucket has ZERO feature_group=odds_targets objects anywhere in the
  2019-08-01..2025-07-31 range the trainer needs. odds_targets was only ever computed for a narrow
  2026-04-01..2026-04-17 verification window (per the archived
  sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md), never backfilled historically. This is a
  pure-compute backfill (the upstream odds_horizon_bucket source data already exists for the historical dates checked) —
  not a code bug, not a credentials/access gap.
status: open
nature: record
asset_group: [sports]
stage: [features]
repos: [features-service]
scope: [engineer]
parent_epic: sports_master
priority: P0
tags: [sports, odds, clv, backfill, data-correctness, features-service]
related:
  [
    /plans/active/issues/sports_clv_ensemble_trainer_no_driver_or_test_coverage_2026_08_09.md,
    /plans/active/issues/sports_t2h_t6h_horizon_retrain_blocked_on_generic_trainer_2026_08_09.md,
  ]
created: 2026-08-10
author: slot-22
assigned_vm: planning
source: [sports_clv_ensemble_trainer_no_driver_or_test_coverage-02f7c74d2184]
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

Dispatched to launch the sports CLV ensemble trainer (`SportsEnsembleTrainingRunner`, `ml-service@68a4b82` — the fix
that wired `merge_clv_target_columns` into the driver, see the parent issue doc) on 5 VMs (`model_2a`-`model_2e`,
`--start-date 2019-08-01 --end-date 2025-07-31`). All 5 reached the real feature load (121,376/8,897/31,540
train/val/test rows) and then ALL 5 hit the identical line:

```
WARNING odds_targets export has none of ('odds_clv_home', 'odds_clv_draw', 'odds_clv_away', 'odds_closing_home',
  'odds_closing_draw', 'odds_closing_away', 'odds_opening_home', 'odds_opening_draw', 'odds_opening_away')
  -- CLV target will fall through
INFO CLVTargetBuilder: built 6 targets from 121376 rows (0.0% non-null)
```

This is `training_targets.py::merge_clv_target_columns` — the correct, purpose-built fix — running exactly as designed
and correctly reporting that the `odds_targets` export it queried has none of the expected columns. Traced this to the
GCS bucket itself, not a code path:

1. **`odds_targets` is absent for every date I spot-checked across the full range**, including dates where the sibling
   `odds_features` group DOES exist for the same date (spot-checked, not a full-corpus walk — per the
   single-walk-discipline rule):
   - `gs://features-sports-prd-central-element-323112/sports_features/by_date/day=2022-03-15/` has
     `feature_group=odds_features/` but no `feature_group=odds_targets/`.
   - Same pattern at `day=2024-06-15`, `day=2025-02-15`, and — critically — at `day=2026-01-15` and even
     `day=2026-07-15`/`day=2026-08-01` (the most recent dates checked, well past "today"'s in-universe date):
     `odds_features` present, `odds_targets` absent. This is not a "historical data not backfilled yet, will arrive
     going forward" gap — `odds_targets` has NEVER been written for ANY date I checked, past or present.
2. **The archived `sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md` explains why**: its 2026-07-26
   Progress Log entry ran the ONLY historical backfill this export has ever received —
   `--feature-family sports --operation compute --feature-group odds_targets --start-date 2026-04-01 --end-date 2026-04-17`
   — a 17-day window, run purely to verify the merge code path against real data. That doc's own `[ML] P2` todo text
   explicitly deferred "the literal 3-variant CLV model retrain" as a separate, larger follow-up and never claimed the
   full historical range was backfilled. Nobody ever ran the equivalent backfill for `2019-08-01..2025-07-31` — the
   range `SportsEnsembleTrainingRunner`'s `training_seasons`/`validation_season`/ `test_season` walk-forward actually
   needs.
3. **This is a pure-compute backfill, not a data-capture or credentials gap**: `odds_targets_exporter.py` reads from
   `market-data-tick-sports-{project}/processed/by_date/day={date}/data_type=odds_horizon_bucket/bucketed.parquet` — the
   SAME already-captured source `odds_features_exporter.py` reads. Spot-checked: this raw source data already exists for
   the historical dates I checked (`day=2022-03-15`, `day=2024-06-15`, `day=2025-02-15` all have
   `data_type=odds_horizon_bucket/` present). The export is wired into `features-service`'s batch handler
   (`batch_handler.py` lines 65/111/384/746 — `"odds_targets": PipelineMode.BATCH_ODDS_API`, mode key
   `"odds_targets:historical"`, already used successfully for the April window) — it just needs to be RUN across the
   real range, not built or unblocked on new data.

## Why it matters

This is the actual, final blocker for `sports_clv_ensemble_trainer_no_driver_or_test_coverage_2026_08_09.md`'s todo 2
("launch it on a dedicated VM ... and report the measured coverage + performance delta"). That todo's own driver code is
now correct (`ml-service@68a4b82`) — but no amount of further ml-service code changes can produce a non-null CLV target
while the target data itself doesn't exist in GCS for the training window. Every future relaunch of the 5 VMs will burn
multi-hour compute (real GCS feature loads + walk-forward folds) only to reach the identical `0.0% non-null` →
`no data available, run aborted` outcome, until this backfill runs. **Stopped the 3rd relaunch attempt's 5 VMs mid-run
on discovering this (2026-08-10, ~3h in)** rather than let them run to a guaranteed, already-known failure — see the
parent issue doc's Progress Log for the exact VM names / evidence.

## Recommended decision

- [ ] [SCRIPT] P0. Launch a dedicated VM (per `/codex/05-infrastructure/vm-launcher-runbook.md`) to run the
      features-service historical `odds_targets` backfill across `2019-08-01..2026-07-31`. Confirmed all 5
      `model_2a`-`model_2e` `SportsModelSpec` entries (`ml-service/ml_service/training/app/core/sports_model_config.py`)
      share identical `training_seasons=(2019, 2023)`, `validation_season=2024`, `test_season=2025` — with
      `_SEASON_START_MONTH=8` (season year N = Aug-N..Jul-(N+1)), the real union range is `2019-08-01` (training start)
      through `2026-07-31` (test-season end), one day past the `2025-07-31` end date the 3rd relaunch attempt's VM
      launcher actually passed (the runner derives its date windows from `SportsModelSpec`, not the CLI
      `--start-date`/`--end-date` — those may be unused by this operation entirely, worth confirming while here). Use
      the SAME command shape already proven against the April window
      (`--feature-family sports --operation compute     --feature-group odds_targets --start-date <start> --end-date <end>`)
      — chunk by season/year if the full range in one invocation is impractical. Spot-check a handful of resulting
      dates' `feature_group=odds_targets/` objects + non-null `odds_clv_home` counts before declaring done — do not
      trust the job's own exit code alone (per this doc's own evidence that a narrow, already-run backfill can look
      complete while leaving the range that actually matters untouched). (repo: features-service)
- [ ] [CODE] P1. Once the backfill lands (verified via the todo above), relaunch the 5 sports CLV ensemble trainer VMs
      (`launch-sports-ensemble-train-vm.sh`, `deployment-service`) and report the measured coverage + performance delta
      back into `sports_clv_ensemble_trainer_no_driver_or_test_coverage_2026_08_09.md`'s todo 2 and
      `sports_t2h_t6h_horizon_retrain_blocked_on_generic_trainer_2026_08_09.md`. (repo: ml-service)

## Progress Log

- 2026-08-10 (slot-22): found while monitoring the 3rd relaunch of the sports CLV ensemble trainer VMs (see
  `sports_clv_ensemble_trainer_no_driver_or_test_coverage_2026_08_09.md`'s Progress Log for the VM names/evidence).
  Root-caused to the GCS bucket state (not a code bug) as detailed above. Deleted the 5 running VMs
  (`gcloud compute instances delete`, confirmed via `gcloud compute instances list` returning empty) rather than let
  them burn further compute toward a guaranteed, already-diagnosed failure. Filed this as its own issue (not folded into
  the parent doc) because it's cross-repo (features-service, not ml-service) and is real, precisely-scoped AO-eligible
  backfill work, not a judgment call needing operator sign-off — the exact backfill command already has prior-run
  precedent (2026-07-26, narrow window) and needs no new credentials or design decision, only a wider date range.

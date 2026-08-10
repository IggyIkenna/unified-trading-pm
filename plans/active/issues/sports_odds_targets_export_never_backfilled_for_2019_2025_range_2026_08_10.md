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

- [x] ✅ [SCRIPT] P0. Launch a dedicated VM (per `/codex/05-infrastructure/vm-launcher-runbook.md`) to run the
      features-service historical `odds_targets` backfill across `2019-08-01..2026-07-31`. — deployment-service@a190d542
      (launcher `--skip-fetch` passthrough) + VM `fts-backfill-20260810-083557` Confirmed all 5 `model_2a`-`model_2e`
      `SportsModelSpec` entries (`ml-service/ml_service/training/app/core/sports_model_config.py`) share identical
      `training_seasons=(2019, 2023)`, `validation_season=2024`, `test_season=2025` — with `_SEASON_START_MONTH=8`
      (season year N = Aug-N..Jul-(N+1)), the real union range is `2019-08-01` (training start) through `2026-07-31`
      (test-season end), one day past the `2025-07-31` end date the 3rd relaunch attempt's VM launcher actually passed
      (the runner derives its date windows from `SportsModelSpec`, not the CLI `--start-date`/`--end-date` — those may
      be unused by this operation entirely, worth confirming while here). Use the SAME command shape already proven
      against the April window
      (`--feature-family sports --operation compute     --feature-group odds_targets --start-date <start> --end-date <end>`)
      — chunk by season/year if the full range in one invocation is impractical. Spot-check a handful of resulting
      dates' `feature_group=odds_targets/` objects + non-null `odds_clv_home` counts before declaring done — do not
      trust the job's own exit code alone (per this doc's own evidence that a narrow, already-run backfill can look
      complete while leaving the range that actually matters untouched). (repo: features-service)
- [x] ✅ [CODE] P1. Once the backfill lands (verified via the todo above), relaunch the 5 sports CLV ensemble trainer
      VMs (`launch-sports-ensemble-train-vm.sh`, `deployment-service`) and report the measured coverage + performance
      delta back into `sports_clv_ensemble_trainer_no_driver_or_test_coverage_2026_08_09.md`'s todo 2 and
      `sports_t2h_t6h_horizon_retrain_blocked_on_generic_trainer_2026_08_09.md`. (repo: ml-service) — 2026-08-10
      (slot-24, 14:12Z): relaunch DONE + **coverage delta MEASURED** — all 5
      `ml-train-sports-model-2[a-e]-20260810-09xxxx` VMs loaded every window (train 121,376 / val 8,897 / test 32,271
      rows) and CLV targets now carry real values: **5.7% (train) / 17.2% (val) / 15.6% (test) non-null, up from 0.0%**
      — the P0 backfill is confirmed end-to-end. **Performance delta NOT yet measurable**: all 5 VMs crashed at the
      first CatBoost fit (`_catboost.CatBoostError: metric/loss-function RMSE does not allow nan values in target data`,
      14:08:34Z, exit_code=1, self-deleted) — partially-non-null CLV targets go straight into CatBoost's RMSE metric.
      Tracked as the new P3 todo below; re-run the 5 VMs once it lands.
- [ ] [INFRA] P3. `launch-sports-ensemble-train-vm.sh` hardcodes `METADATA="VM_TASK=features-backfill"` — the run is a
      training run (`VM_OPERATION=sports-ensemble-train`, and the actual log line reads `task=features-backfill` in
      PIPELINE_HEARTBEAT), so deployment-ui/vm-life classification labels these trainer VMs as features-backfill.
      Cosmetic (the real `op=sports-ensemble-train` is correct in run.log), but fix the label to
      `VM_TASK=sports-ensemble-train` so fleet monitoring/classification reads correctly. (repo: deployment-service)
- [x] ✅ [CODE] P3. `SportsModel2ATrainer.train()` passes the now-partially-non-null CLV targets (5.7%/17.2%/15.6%
      non-null post-backfill) straight to CatBoost with an RMSE metric, which rejects NaN in the target — all 5 trainer
      VMs crashed identically at the first fit (`_catboost.CatBoostError` — "RMSE does not allow nan values in target
      data", 2026-08-10 14:08:34Z, `DEPLOYMENT_FAILED exit_code=1`). Fix the NaN handling before CatBoost (drop
      per-outcome NaN target rows aligned with X, or a NaN-tolerant objective/metric), then re-run the 5 trainer VMs to
      obtain the rmse/mae/r2-per-outcome-per-horizon performance delta this doc's P1 deferred. (repo: ml-service)
      **RESOLVED (2026-08-10, slot-17)** — the NaN-handling code fix shipped `ml-service@9b68494b76`:
      `SportsModel2ATrainer.train()` now drops per-outcome NaN CLV target rows (aligned with X, train + val) before the
      ensemble fit, skips an all-NaN outcome, and `evaluate()` masks NaN test targets so rmse/mae/r2 stay finite — full
      `quality-gates.sh` green (139s, sentinel `9b68494b7626fa2ff3a4894ee5de826adff0b568`), landed on
      `origin/live-defi-rollout`, verified ancestor-of-origin. The 5-VM re-run for the
      rmse/mae/r2-per-outcome-per-horizon perf delta is the Deferred-table item below, now unblocked by this fix.

## Progress Log

- 2026-08-10 (slot-22): found while monitoring the 3rd relaunch of the sports CLV ensemble trainer VMs (see
  `sports_clv_ensemble_trainer_no_driver_or_test_coverage_2026_08_09.md`'s Progress Log for the VM names/evidence).
  Root-caused to the GCS bucket state (not a code bug) as detailed above. Deleted the 5 running VMs
  (`gcloud compute instances delete`, confirmed via `gcloud compute instances list` returning empty) rather than let
  them burn further compute toward a guaranteed, already-diagnosed failure. Filed this as its own issue (not folded into
  the parent doc) because it's cross-repo (features-service, not ml-service) and is real, precisely-scoped AO-eligible
  backfill work, not a judgment call needing operator sign-off — the exact backfill command already has prior-run
  precedent (2026-07-26, narrow window) and needs no new credentials or design decision, only a wider date range.
- 2026-08-10 (slot-28): launched the P0 backfill VM. Two deviations from this doc's literal recommendation, both
  code-verified before launch: (1) **start-date clamped to `2020-06-06`** (sports data-floor SSOT
  `/codex/02-data/sports-2020-06-data-floor.md` — odds tick data starts 2020-06-06; the `2019-08-01` union-range start
  is pre-floor fabrication-by-construction, wiped from GCS + manifest, and the floor clamps every sports backfill
  launcher's START_DATE to it; end-date `2026-07-31` unchanged). (2) **`--tables odds_targets` instead of
  `--feature-group odds_targets`**: the batch handler selects feature-groups via `--tables` only — `--feature-group` is
  a live-mode-only flag (parser.py/main.py `_run_batch`), so the literal April-window command shape is a no-op for batch
  table selection. Also added `--skip-fetch` passthrough to `launch-features-sports-backfill-vm.sh`
  (`deployment-service@a190d542`, QG green) because `export_odds_targets` reads only MTDS `odds_horizon_bucket`
  (`read_bucketed_odds`) and needs none of the instruments-service reference-data fetch — a 6-year run otherwise pays a
  per-date ~14-entity reference read it never consumes. **VM launched: `fts-backfill-20260810-083557`** (e2-standard-4,
  SPOT, zone asia-northeast1-c, `--force` bypassing the singleton lock held by the running
  `fts-backfill-20260809-012626` derived_features/fixture_features VM — genuinely disjoint feature-group, per launcher's
  own `--force` contract). Command:
  `python -m features_service.sports --operation compute --mode batch --asset-group SPORTS --tables odds_targets --start-date 2020-06-06 --end-date 2026-07-31 --skip-fetch`.
  VM exited rc=0 at 08:42 after processing the 49 manifest-pending dates — but the manifest-aware prune
  (`compute_pending_dates`) skipped 2198/2247 dates as "already-fully-resolved". **Verified directly (did NOT trust the
  exit code)**: (1) full-range coverage in the consolidated availability index — 2247/2247 dates in
  `2020-06-06..2026-07-31` carry an `odds_targets` row (1551 `captured` + 696 `empty_confirmed`, **0 missing**); (2)
  1551 captured dates ↔ 1552 real `feature_group=odds_targets/features.parquet` objects — no phantom rows; (3)
  spot-checked parquets across 2020-2025 all carry non-null `odds_clv_home` (2020-07-28 1/3, 2022-11-19 4/4, 2022-12-10
  13/13, 2023-07-12 7/7, 2024-01-10 4/4, 2025-02-07 11/24); (4) empty_confirmed dates are honest (`SOURCE_RETURNED_ZERO`
  = no bucketed odds that day, `EXPECTED_WRITE_GATE_NAN_THRESHOLD_EXCEEDED` = legitimately mostly-NaN day). **Key
  context: a concurrent session already backfilled the bulk of the range this morning** (object mtimes 2026-08-10
  05:34-06:20Z + index `written_at` predating this VM), so this VM's 49-date contribution completed the residual gap;
  the issue doc's "ZERO objects anywhere in 2019-2025" spot-check predates that morning backfill. The CLV-target data
  gap this issue describes is now closed for the full range. P1 (relaunch the 5 trainer VMs) is now unblocked.
- 2026-08-10 (slot-24): **P1 — relaunched the 5 sports CLV ensemble trainer VMs (4th attempt)** after verifying the P0
  backfill landed (spot-checked `feature_group=odds_targets/features.parquet` present for 2020-07-01, 2022-03-15,
  2024-06-15, 2025-02-07, 2026-01-15 with 2026-08-10T05-06Z mtimes; 2026-06-01 is an honest no-odds off-season day — no
  `odds_features` either; no running trainer VMs before launch). Launched via `launch-sports-ensemble-train-vm.sh`
  (deployment-service; tarball manifest pins ml-service@68a4b82 = the `merge_clv_target_columns` fix, no refresh
  needed):
  - `ml-train-sports-model-2a-20260810-092727` (model_2a)
  - `ml-train-sports-model-2b-20260810-092740` (model_2b)
  - `ml-train-sports-model-2c-20260810-092748` (model_2c)
  - `ml-train-sports-model-2d-20260810-092758` (model_2d)
  - `ml-train-sports-model-2e-20260810-092807` (model_2e)

  All 5 confirmed past bootstrap in `run.log`
  (`ServiceRuntime: op=sports-ensemble-train mode=batch env=prod data=real` + `DEPLOYMENT_STARTED` +
  `PIPELINE_HEARTBEAT`) — in the real GCS feature-load/train path, not crashing at bootstrap. Monitoring in flight; once
  the runs reach terminal state, the measured coverage + rmse/mae/r2-per-outcome delta will be reported into this P1's
  text, `sports_clv_ensemble_trainer_no_driver_or_test_coverage_2026_08_09.md`'s todo 2, and
  `sports_t2h_t6h_horizon_retrain_blocked_on_generic_trainer_2026_08_09.md`, then the checkbox flipped. **If this
  session ends before the runs report**: next worker should check these 5 names (not the 20260809-23xxxx batch, already
  gone) via `gcloud compute instances describe <name> --zone=asia-northeast1-c` (gone = terminal) +
  `gs://deployment-scripts-central-element-323112/vm-logs/<name>/run.log` result line
  (`SportsEnsembleTrainingRunner(<model_id>) complete: train=N val=N test=N rows, K features, test_metrics=...` /
  `no data available, run aborted`) before assuming a re-launch is needed. **Load-phase progress signal (measurement
  trap)**: the runner's per-date `Sports GCS: <date> — loaded N fixtures` INFO lines are emitted only in a POST-collect
  merge pass (`sports_feature_loader.py:535`, after the whole season's `_collect_sports_frames_by_date` scan) — so ZERO
  `Sports GCS:` lines in run.log is NOT a stall. Live progress proxy = the repeating `sports_feature_loader.py:204`
  pandas `FutureWarning` concat blocks (~1 per league-split date×group; most dates are silent single-frame reads);
  liveness = PIPELINE_HEARTBEAT freshness + growing log line-count. At 10:23Z all 5 VMs were ~55min in, mid-train-season
  scan.

- 2026-08-10 (slot-24, cont. 12:46Z): **COVERAGE MILESTONE — the P0 `odds_targets` backfill is confirmed end-to-end.**
  All 5 trainer VMs reached `CLVTargetBuilder: built 6 targets from 121376 rows (5.7% non-null)` at 12:46:22-24Z — up
  from **0.0% non-null** in every prior attempt, with NO `odds_targets export has none` warning and NO
  `no data available, run aborted`. CLV targets now carry real values on the exact same 121,376-row train set that
  previously built all-NaN targets. Runner proceeded to load the val (2024) + test (2025) windows, then trains the
  ensemble. The **coverage delta (0.0% → 5.7% non-null)** is now measured; the **performance delta (rmse/mae/r2 per
  outcome per horizon)** comes from the `complete:` line's `test_metrics` at terminal — both to be reported into this
  P1's text + `sports_clv_ensemble_trainer_no_driver_or_test_coverage_2026_08_09.md`'s todo 2 +
  `sports_t2h_t6h_horizon_retrain_blocked_on_generic_trainer_2026_08_09.md` per the handoff.
- 2026-08-10 (slot-24, cont. 14:12Z): **OUTCOME — coverage delta measured; performance delta blocked on a NEW ml-service
  code bug.** All 5 trainer VMs ran the full pipeline and reached training: CLV targets now **5.7% non-null (train,
  121,376 rows) / 17.2% (val, 8,897) / 15.6% (test, 32,271)** — vs 0.0% before the backfill. Training then crashed
  identically on all 5 at 14:08:34Z: `_catboost.CatBoostError` — "RMSE does not allow nan values in target data" →
  `DEPLOYMENT_FAILED exit_code=1` → `VM_SHUTDOWN_ON_COMPLETION=true` self-delete (all 5 instances now gone). This is a
  code-level finding (the data gap is closed): the trainer feeds partially-non-null CLV targets into CatBoost RMSE.
  Filed as the P3 todo above. The P1 perf-delta half is deferred onto P3; the coverage half is measured and reported.

## Deferred work after 2026-08-10

| Item                                                                                                                                                                                                                                                   | State / why deferred                                                                                                                                                                                                      | Blocked on                                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Report the rmse/mae/r2-per-outcome-per-horizon **performance delta** into this P1's text + `sports_clv_ensemble_trainer_no_driver_or_test_coverage_2026_08_09.md`'s todo 2 + `sports_t2h_t6h_horizon_retrain_blocked_on_generic_trainer_2026_08_09.md` | Not done — 5-VM re-run for the perf delta still pending; coverage delta already measured (0.0% → 5.7%/17.2%/15.6% non-null). The P3 CatBoost-NaN crash that blocked it is now fixed (`ml-service@9b68494b76`, 2026-08-10) | Nothing — re-run the 5 `ml-train-sports-model-2a/b/c/d/e` VMs now (unblocked by the P3 fix) |

**Recommended next item**: the P3 CatBoost-NaN handling fix (ml-service — drop per-outcome NaN target rows before
CatBoost, or a NaN-tolerant objective/metric), then re-run the 5 `ml-train-sports-model-2a/b/c/d/e` VMs to capture the
performance delta.

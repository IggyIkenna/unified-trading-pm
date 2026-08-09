---
doc_type: issue
title:
  Sports CLV ensemble trainer (model_2a-2e) has zero orchestration/CLI wiring and zero test coverage — "run the actual
  retrain" needs a new driver before it needs a VM
summary: >-
  Investigating the P1 half of sports_t2h_t6h_horizon_retrain_blocked_on_generic_trainer_2026_08_09.md ("run the actual
  retrain ... and report the measured delta") found the trainer generalization (P0) fixed model_id hardcoding, but
  SportsModel2ATrainer / model_type="ensemble" has NO consumer anywhere — no CLI dispatch, no orchestrator wiring, no
  ModelRegistry class (referenced in the trainer's own docstring but does not exist in this repo), and ZERO test
  coverage. "Running the actual retrain" is not a config change — it requires building a new training driver first.
status: open
nature: record
asset_group: [sports]
stage: [backtest]
repos: [ml-service]
scope: [engineer]
parent_epic: sports_master
priority: P1
tags: [sports, ml, clv, trainer, driver, test-coverage]
related:
  [
    /plans/active/issues/sports_t2h_t6h_horizon_retrain_blocked_on_generic_trainer_2026_08_09.md,
    /plans/active/issues/ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-08-09
author: slot-19
assigned_vm: planning
source: [sports_t2h_t6h_horizon_retrain_blocked_on_generic_trainer-32239d124bc9]
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
sequential: true # todo 2 (VM launch) explicitly requires todo 1's driver ("once the driver lands and is
# unit-tested") — added 2026-08-09 (slot-11) after this doc's todo 2 was dispatched with no driver yet built
# (grep confirmed zero SportsEnsembleTrainingRunner references in ml-service); without sequential ordering
# both P1 todos are same-priority and dispatchable to any worker regardless of the real dependency.
---

## What I found

Picked up the P1 todo in `sports_t2h_t6h_horizon_retrain_blocked_on_generic_trainer_2026_08_09.md` ("run the actual
retrain for model_2a/model_2b/model_2c ... plus model_2d/model_2e, and report the measured coverage + performance
delta"). Before running anything, traced how `SportsModel2ATrainer`
(`ml_service/training/app/training/ sports_ensemble_trainer.py`) actually gets invoked with real data end-to-end. It
doesn't:

1. **Zero production callers.** `grep -rn "SportsModel2ATrainer" ml_service/` (excluding the trainer's own file) hits
   only `config_loader.py` (the `SPORTS_MODEL_ID_TO_GRID` type import) and `training/__init__.py`'s re-export. No CLI
   handler, no orchestrator, nothing else in the codebase constructs or calls it.
2. **Zero test coverage.** `find . -iname "*sports_ensemble*test*"` and `grep -rln "SportsModel2ATrainer" -- */tests/*`
   both return nothing. The class has never been exercised, not even against synthetic fixture data.
3. **`model_type="ensemble"` is a dead value.** Every other `TrainingGridConfig` in `config_loader.py` uses
   `model_type="lightgbm"` and flows through `TrainingOrchestrator` → `ModelVariantConfig` (the generic
   per-instrument/target-type path used by `train_handler.py`). `grep -n "model_type" training_orchestrator.py` returns
   zero hits — the orchestrator doesn't branch on `model_type` at all, so even if it did, `"ensemble"` still wouldn't
   route anywhere. The 3 (now 5, see below) sports CLV grids are the only `model_type="ensemble"` entries in the whole
   grid registry, and nothing reads that field.
4. **`ModelRegistry` doesn't exist.** The trainer's own module docstring says "GCS model artifact storage via
   ModelRegistry" — `grep -rln "class ModelRegistry" ml-service/` returns nothing. There is no artifact-persistence path
   for a trained sports ensemble even if training ran.
5. **Real feature loading is itself expensive and untested at this scale.**
   `SportsFeatureLoaderMixin._query_sports_features` (`sports_feature_loader.py`) walks GCS **day-by-day** across the
   requested date range, per feature group, with no batching — `training_seasons=(2019, 2023)` +
   `validation_season=2024` + `test_season=2025` is ~7 years of daily GCS reads × 2 feature groups × up to 2 layouts
   (day-level + per-league) per model. This is the kind of full-range, multi-year I/O CLAUDE.md's VM-launcher rule flags
   as never-on-the-shared-host — even once a driver exists, the actual training run belongs on a dedicated VM, not a
   worker's slot session.

Separately (mechanical, already fixed in this task): `model_2b`/`model_2c` had SportsModelSpec entries but no
`TrainingGridConfig`, so `SPORTS_MODEL_ID_TO_GRID` had no entry for them even after the P0 trainer-generalization —
`SPORTS_MODEL_2B_GRID`/`SPORTS_MODEL_2C_GRID` added (ml-service@0a7d842, same shape as 2A/2D/2E). That part of the gap
is closed; the driver/wiring gap below is not.

## Why it matters

The parent issue's P1 todo asks for a **measured** coverage/performance delta across 5 horizons. That can't happen from
a config change — it requires: (a) a real driver that wires `SportsFeatureLoaderMixin` (real GCS load) →
`CLVTargetBuilder` (`sports_target_generator.py`) → feature selection (`feature_selection_samples`/
`target_feature_count` per grid) → `SportsModel2ATrainer.train()` → walk-forward evaluation → artifact persistence, none
of which currently exists; and (b) then actually running that driver against ~7 years of real fixture data per horizon,
on a VM. Treating the P1 todo as "just call the trainer with real data" (what this task was scoped as) understates the
work by an order of magnitude — this is closer to shipping a new ML training pipeline than running an existing one.

## Recommended decision

Split the remaining work into two AO-eligible todos so the driver gets built (and test-covered) before anyone attempts
the VM-scale run:

- [x] ✅ [CODE] P1. Build a `SportsEnsembleTrainingRunner` (or similar) in `ml-service` that, given a `model_id`,
      resolves its `SportsModelSpec` + `TrainingGridConfig` (`SPORTS_MODEL_ID_TO_GRID`), loads real features via
      `SportsFeatureLoaderMixin._query_sports_features` for `training_seasons`/`validation_season`/`test_season`, builds
      CLV targets via `CLVTargetBuilder`, applies feature selection down to `target_feature_count`, and calls
      `SportsModel2ATrainer(model_id).train()` + `.evaluate()` against the held-out test season. Add unit test coverage
      (currently zero) using small synthetic fixtures — do not let this class stay untested. Wire it behind a CLI
      command/handler so it's actually invocable, not another orphaned class. (repo: ml-service) — ml-service@3232e17
- [ ] [CODE] P1. Once the driver lands and is unit-tested, launch it on a dedicated VM (per
      `/codex/05-infrastructure/vm-launcher-runbook.md` — this is exactly the multi-year GCS-walk + heavy-compute case
      that rule exists for) for `model_2a`/`model_2b`/`model_2c`/`model_2d`/`model_2e`, and report the measured
      coverage + performance delta (rmse/mae/r2 per outcome per horizon) back into this doc and
      `sports_t2h_t6h_horizon_retrain_blocked_on_generic_trainer_2026_08_09.md`. (repo: ml-service)

## Progress Log

- 2026-08-09 (slot-19): investigated the P1 retrain todo; found no driver/CLI/test wiring exists for the sports ensemble
  path (details above). Shipped the mechanical sub-fix (model_2b/model_2c grid configs, ml-service@0a7d842) and filed
  this doc for the actual driver-build + VM-run work, since attempting either inside this single dispatched task would
  mean either fabricating a measured delta or building + running a multi-day ML pipeline unreviewed.
- 2026-08-09 (slot-11): dispatched todo 2 ("launch it on a dedicated VM") directly — re-confirmed via
  `grep -rln "SportsEnsembleTrainingRunner" ml-service/` (zero hits) that todo 1's driver still does not exist, so todo
  2's own precondition is unmet. Added `sequential: true` to this doc's frontmatter so the backlog won't dispatch todo 2
  again until todo 1 is checked `done` (`PLAN_FORMAT.md` § sequential — strict N-waits-for-N-1 ordering). Skipping this
  task with `reason_code: GATED`; no code change to ml-service in this session.
- 2026-08-09 (slot-18): shipped todo 1 — `SportsEnsembleTrainingRunner`
  (`ml_service/training/app/training/sports_ensemble_training_runner.py`, ml-service@3232e17). Resolves
  `SportsModelSpec`/`TrainingGridConfig` for the given `model_id`, loads real GCS features for training/validation/test
  seasons via `CloudFeatureProvider.query_features(..., asset_group="SPORTS")` (the public wrapper around the mixin's
  `_query_sports_features`), builds CLV targets via `CLVTargetBuilder`, strips leakage columns + non-numeric identifier
  columns (fixture_id/date/team names), selects down to `target_feature_count`, then calls
  `SportsModel2ATrainer.train()` + `.evaluate()` against the held-out test season. One real design decision worth
  flagging: `FeatureSelector`'s LightGBM ranker is hardcoded for a 3-class -1/0/1 drift label (built for
  `CLVTargetGenerator`'s legacy path) — `CLVTargetBuilder`'s continuous CLV-bps regression target would filter out
  nearly every row if fed straight in, so the runner bins it into terciles (`_bin_clv_target_for_selection`) purely for
  ranking; the trainer itself always trains on the untouched continuous target. Also: `training_seasons`/
  `validation_season`/`test_season` are season-start years with no existing date-mapping convention in this repo — the
  runner documents + applies the standard European football season convention (Aug(year)–Jul(year+1)); if that's wrong,
  it's a one-function fix (`_season_date_range`). 11 new unit tests
  (`tests/training/unit/test_sports_ensemble_training_runner.py`) cover season-range math, the tercile-binning helper,
  constructor validation, and a full run against synthetic fixtures (train/val/test) with a lightweight `EnsembleConfig`
  for speed — asserts identifier/leakage columns never survive selection, per-outcome test metrics are produced, and
  honest-absence (`None`) returns on empty train/test data. Wired behind
  `--operation sports-ensemble-train --model-id <id>` via `SportsEnsembleTrainModeHandler`
  (`ml_service/training/cli/handlers/sports_ensemble_train_handler.py`) — bypasses the heavier variant-grid
  `_MLTrainingModeHandler` machinery since this driver is model-id-driven, not instrument/timeframe-driven. Full
  `bash scripts/quality-gates.sh` green (2188 passed, 4 skipped, 80.96% coverage). Todo 2 (the VM-scale run) is now
  unblocked by the `sequential: true` gate.
- 2026-08-09 (slot-10): started todo 2. Refreshed ml-training code tarballs (`create-code-tarballs.sh --ml-training`;
  confirmed `ml-service-code.manifest.json` pins `3232e17`, the commit carrying the driver). Launched 5 independent
  dedicated VMs (n2-highmem-16, `asia-northeast1-c`, `uts-prd-sa`, `VM_SHUTDOWN_ON_COMPLETION=true`), one per model,
  each running
  `python -m ml_service.training --operation sports-ensemble-train --model-id <model_id> --start-date 2019-08-01 --end-date 2025-07-31`
  (the CLI's `--start-date`/`--end-date` are argparse-required but unused by this operation — the runner derives its own
  train/val/test season windows from each model's `SportsModelSpec`). No `--family`/ singleton-lock applies; the 5
  models are independent so this runs as 5 parallel VMs rather than one long serial run (per the VM-launcher runbook's
  parallelization-threshold rule). VM names (routed via the pre-registered `ml-` `VM_PREFIX_TO_BUCKET` prefix, no new
  registry entry needed):
  - `ml-train-sports-model-2a-20260809-191045` (model_2a)
  - `ml-train-sports-model-2b-20260809-191058` (model_2b)
  - `ml-train-sports-model-2c-20260809-191114` (model_2c)
  - `ml-train-sports-model-2d-20260809-191127` (model_2d)
  - `ml-train-sports-model-2e-20260809-191143` (model_2e)

  Each VM self-deletes on completion (success or failure); logs persist at
  `gs://deployment-scripts-central-element-323112/vm-logs/{VM_NAME}/run.log` regardless. Success is
  `SportsEnsembleTrainingRunner(<model_id>) complete: train=N val=N test=N rows, K features, test_metrics={home:{rmse, mae,r2}, draw:{...}, away:{...}}`
  in that log; honest-absence abort is `sports-ensemble-train for <model_id>: no data available, run aborted`. No
  artifact-persistence/results-JSON path exists yet (out of scope per the driver's own docstring) — the run.log line is
  the only record, so it's being captured here once each VM terminates. A background watchdog (`run_in_background`, 3min
  poll, 5h cap) is tailing all 5 VMs to terminal state; if this session ends before it reports, the next worker on this
  doc should re-check the 5 VM names above via `gcloud compute instances describe <name> --zone=asia-northeast1-c` (gone
  = terminal) and pull `gs://deployment-scripts-central-element-323112/vm-logs/<name>/run.log` for the result line
  before assuming the run needs re-launching.

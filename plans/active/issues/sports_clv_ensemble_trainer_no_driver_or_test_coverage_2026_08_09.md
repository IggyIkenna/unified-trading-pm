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
    /plans/archive/issues/sports_t2h_t6h_horizon_retrain_blocked_on_generic_trainer_2026_08_09.md,
    /plans/archive/2026_08/issues/ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md,
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
context_scope:
  [
    ml-service/ml_service/training/app/training/sports_ensemble_trainer.py,
    ml-service/ml_service/training/app/training/sports_ensemble_training_runner.py,
    /plans/archive/2026_08/issues/sports_odds_targets_export_never_backfilled_for_2019_2025_range_2026_08_10.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    ml-service/ml_service/training/cli/handlers/sports_ensemble_train_handler.py,
  ]
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
      `sports_t2h_t6h_horizon_retrain_blocked_on_generic_trainer_2026_08_09.md`. (repo: ml-service) — **PARTIAL
      2026-08-10 (slot-24)**: the backfill landed and the 5 VMs were relaunched; **coverage delta MEASURED** — CLV
      targets now 5.7% (train, 121,376 rows) / 17.2% (val, 8,897) / 15.6% (test, 32,271) non-null, up from 0.0%.
      **Performance delta STILL blocked on a new code bug**: the trainer crashes at the first CatBoost fit ("RMSE does
      not allow nan values in target data", all 5 VMs, exit_code=1) because partially-non-null CLV targets go straight
      into CatBoost. Fix tracked as P3 in
      `/plans/archive/2026_08/issues/sports_odds_targets_export_never_backfilled_for_2019_2025_range_2026_08_10.md`.
- [x] ✅ [CODE] P3. `ml_service/training/cli/main.py`'s `--asset-group` arg defaults to `"ALL"`, which is not a
      `MarketCategory` member — any CLI invocation of this service that omits `--asset-group` explicitly crashes at
      `ServiceRuntime.from_env_and_args` (`StartupValidationError: Invalid CLI --asset-group='ALL'`) before any handler
      runs. Confirmed live 2026-08-09: dead-on-arrival for 5 `sports-ensemble-train` VM launches until
      `--asset-group SPORTS` was added explicitly. Every existing production launcher happens to always pass a real
      value, so this was latent; harden it (e.g. drop the `"ALL"` default, or validate/translate it before it reaches
      `ServiceRuntime`) so the next new operation added to this CLI doesn't hit the same trap. (repo: ml-service) —
      ml-service@23006b4

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

- 2026-08-09 (slot-22): picked up todo 2. All 5 of slot-10's VMs had already self-deleted; pulled their `run.log`s —
  every one failed in <2s at CLI argparse: `ml-service: error: the following arguments are required: --mode` (slot-10's
  launch command omitted `--mode batch`; no real compute/cost was burned, but zero training happened despite the
  Progress Log above reading as if the runs were in flight). Relaunched all 5 with `--mode batch` added — hit a SECOND,
  latent bug: `ml_service/training/cli/main.py`'s own `_add_scope_args` defines `--asset-group` with `default="ALL"`
  (`CATEGORIES = ["CEFI", "TRADFI", "SPORTS", "ALL"]`), but `unified_trading_library.service_cli.ServiceCLI.run()`
  unconditionally feeds `getattr(args, "asset_group", None)` into `ServiceRuntime.from_env_and_args(...)`, which
  validates it against the `MarketCategory` enum (`CEFI, TRADFI, DEFI, SPORTS, PREDICTION` — no `ALL` member) and raises
  `StartupValidationError` before any handler code runs. Every existing production launcher (`launch-ml-training-vm.sh`)
  always passes `--asset-group <real-value>` explicitly, so this footgun was previously unreachable — the new
  `sports-ensemble-train` operation is the first caller that can be invoked without one. Fixed by adding
  `--asset-group SPORTS` explicitly to the launch command (matches `SportsModelSpec`'s own asset group; the driver
  itself doesn't consume `--asset-group`, it resolves everything from `--model-id`). Relaunched all 5 VMs a second time
  — confirmed via `run.log` tail (past `ServiceRuntime: op=sports-ensemble-train mode=batch ... env=prod data=real` + 3
  consecutive `PIPELINE_HEARTBEAT` lines with no traceback) that each is now actually inside
  `SportsEnsembleTrainingRunner`'s real GCS feature-load, not crashing at bootstrap. New VM names (same `ml-train-`
  prefix, `asia-northeast1-c`, `n2-highmem-16`, `uts-prd-sa`, `VM_SHUTDOWN_ON_COMPLETION=true`, tarball still pinned at
  `ml-service@3232e17` — no tarball refresh needed):
  - `ml-train-sports-model-2a-20260809-193036` (model_2a)
  - `ml-train-sports-model-2b-20260809-193046` (model_2b)
  - `ml-train-sports-model-2c-20260809-193055` (model_2c)
  - `ml-train-sports-model-2d-20260809-193103` (model_2d)
  - `ml-train-sports-model-2e-20260809-193115` (model_2e)

  A background watchdog (`run_in_background`, 30s poll, 5h cap) is tailing all 5 to terminal state. If this session ends
  before it reports, the next worker should re-check these 5 (not slot-10's, which are already gone) via
  `gcloud compute instances describe <name> --zone=asia-northeast1-c` (gone = terminal) and pull
  `gs://deployment-scripts-central-element-323112/vm-logs/<name>/run.log` for the
  `SportsEnsembleTrainingRunner(<model_id>) complete: ...`/`no data available, run aborted` result line before assuming
  a re-launch is needed. Filed the `--asset-group` default-"ALL" footgun as todo 3 below (P3, ml-service) — didn't fix
  it inline since it's outside this doc's scope and every current production caller already passes an explicit value,
  but a future new operation added to this same CLI will hit it again otherwise.

  **~3h later, all 5 terminal — all aborted honest-absence with a THIRD, real data-correctness bug (not a launch-command
  mistake this time).** Every `run.log` showed the identical pattern across all three (train/val/test) feature-group
  loads: `CLVTargetBuilder: built 6 targets from N rows (0.0% non-null)`, ending in
  `sports-ensemble-train for <model_id>: no data available, run aborted` — real rows loaded (121376/8897/31540), but the
  CLV target itself was 100% NaN for every model. Root-caused: `odds_features_exporter.py` (features-service)
  deliberately **drops** `odds_closing_home/draw/away` from the `odds_features` group before export (leakage prevention
  — "a T-24h model must never see the closing line"); those columns only exist in the separate, PIT-unrestricted
  `odds_targets` export. `SportsEnsembleTrainingRunner._load_season_features_and_targets` (this doc's own todo-1 driver)
  only loaded `grid_config.feature_groups=["derived_features","odds_features"]` and fed that straight into
  `CLVTargetBuilder.build()`, so every `_safe_col()` closing-odds lookup silently returned NaN. This is NOT a new
  problem — `ml_service/training/app/core/training_targets.py::merge_clv_target_columns()` already exists specifically
  to solve it (built for `training_orchestrator`'s legacy CLV path per
  `sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md` +
  `sports_clv_target_builder_family_route_likely_same_pit_gap_2026_07_26.md`) — it queries `odds_targets` via a SEPARATE
  override call and merges just the CLV/closing/opening columns back in, explicitly documented as "NOT by adding
  `odds_targets` to `SPORTS_FEATURE_GROUPS`" (that would leak the closing line into every sports model's INPUT features,
  not just CLV). The new driver simply never called it. **First attempted fix was WRONG**: initially added
  `"odds_targets"` directly to the 5 grids' `feature_groups` lists in `config_loader.py` — reverted after reading
  `merge_clv_target_columns`'s own docstring, which explains exactly why that specific fix leaks the closing line into
  every sports model's input features. **Real fix**: wired
  `merge_clv_target_columns(features, feature_provider, start, end)` into the runner's
  `_load_season_features_and_targets`, right after the main load and before `CLVTargetBuilder.build()` —
  `strip_target_leakage` (unchanged, already called after) already covers stripping these exact merged columns back out
  via `_FT_REALIZED_COLUMNS`, so the leakage guard holds end-to-end. Added 2 new regression unit tests proving targets
  are non-null ONLY when the merge runs (`TestSportsEnsembleTrainingRunnerClvTargetMerge`); updated the 4 existing
  `TestSportsEnsembleTrainingRunnerRun` tests' `query_features` mocks for the extra per-season call the merge now makes.
  13/13 unit tests pass. Full `quality-gates.sh` green. Shipped **ml-service@68a4b82**. Refreshed the ml-training
  tarball (`create-code-tarballs.sh --ml-training`; manifest now pins `68a4b82`) and relaunched all 5 VMs a third time
  (same launch shape as the second attempt — `--mode batch --asset-group SPORTS`, `n2-highmem-16`, `asia-northeast1-c`):
  - `ml-train-sports-model-2a-20260809-230045` (model_2a)
  - `ml-train-sports-model-2b-20260809-230054` (model_2b)
  - `ml-train-sports-model-2c-20260809-230104` (model_2c)
  - `ml-train-sports-model-2d-20260809-230113` (model_2d)
  - `ml-train-sports-model-2e-20260809-230123` (model_2e)

  If this session ends before these 5 report, the next worker should check these VM names (not the 191045/193036
  batches, both already gone) the same way — `gcloud compute instances describe` (gone = terminal) +
  `gs://deployment-scripts-central-element-323112/vm-logs/<name>/run.log` for the result line — before assuming a
  re-launch is needed.

  Promoted the scratch relaunch script into a permanent launcher (no dedicated launcher existed for this
  `--model-id`-driven CLI shape — `launch-ml-training-vm.sh` only covers the `--instruments`/`--target-types` shape) —
  `deployment-service@64f4cb9c`, `scripts/vm/launch-sports-ensemble-train-vm.sh`, bakes in both CLI footguns
  (`--mode batch`, `--asset-group SPORTS`) so a future relaunch doesn't rediscover them. `bash -n` + dry-run +
  shellcheck + full `quality-gates.sh` all green before shipping.

  As of 2026-08-10T~01:22Z (~2h20m after the ~23:00-23:01 UTC 2026-08-09 launch), all 5 third-attempt VMs are still
  `RUNNING` with only `PIPELINE_HEARTBEAT` lines in `run.log` (no `CLVTargetBuilder: built ... non-null` result line yet
  for any of them) — consistent with a multi-hour real GCS feature load + ensemble train per model, not a stall. Session
  is compacting here; todo 2 stays unchecked (genuinely not done — needs elapsed wall-clock time on GCE, not more code
  or a decision). See `## Deferred work after 2026-08-10` below for what the next session should do.

  **Two operational lessons worth not re-learning**: (1) `ScheduleWakeup` and `run_in_background` do NOT compose — a
  `run_in_background` watchdog polling for VM terminal state gets killed by session/turn boundaries before it can
  report; confirmed empirically here (2 dead watchdog attempts) and it turns out this is already a documented codex HARD
  RULE (`/codex/12-agent-workflow/async-wait-and-poll-discipline.md`) — use `ScheduleWakeup` + a direct `gcloud`/log
  check on each wake instead, never a backgrounded poll loop. (2) `quality-gates.sh`'s `.qg_last_passed_sha` sentinel is
  keyed to the exact HEAD it ran against — running QG on a dirty/uncommitted tree and THEN committing produces a
  sentinel that doesn't match the new post-commit HEAD, forcing a wasted second QG pass; always commit first (per the
  workspace's own "commit only from a green tree" rule — sequence is stage → QG on the staged tree → commit → sentinel
  now matches HEAD → ship), not QG-then-commit.

- 2026-08-10 (slot-22): **the "if any model still honest-absence-aborts" contingency below fired — all 5 did, but NOT
  because the fix is wrong.** Resumed monitoring the 3rd-attempt VMs; ~3h in, all 5 hit the identical
  `CLVTargetBuilder: built 6 targets from N rows (0.0% non-null)` line — the SAME symptom as before the fix. Traced this
  fully before concluding anything: `merge_clv_target_columns` (`ml-service@68a4b82`'s fix) IS running and IS correctly
  querying `feature_groups=["odds_targets","derived_features"]` — it's logging its own honest
  `odds_targets export has none of (...) -- CLV target will fall through` warning, which is the function working exactly
  as designed when the export it queries has no data. Confirmed via spot-checked `gcloud storage ls` (not a full-corpus
  walk) that `feature_group=odds_targets/` **does not exist for ANY date in the features-sports bucket** — not for
  2019-2025, not even for the most recent dates checked (2026-07-15, 2026-08-01). Traced to the archived
  `sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`: the ONLY historical backfill this export has
  ever received was a 17-day verification window (`2026-04-01..2026-04-17`), run to prove the merge code path, never
  extended to the real 2019-2025 training range. Confirmed the upstream raw source
  (`market-data-tick-sports-.../odds_horizon_bucket`) already exists for historical dates, so this is a pure-compute
  backfill, not a new-data-capture or credentials gap. **Deleted all 5 running VMs**
  (`ml-train-sports-model-2a/b/c/d/e-20260809-23xxxx`, `gcloud compute instances delete`, confirmed via an empty
  `gcloud compute instances list`) rather than let them burn several more hours of compute toward an outcome already
  conclusively known. Filed the real blocker as its own issue (cross-repo, features-service, precisely-scoped
  AO-eligible backfill — not a judgment call):
  `/plans/archive/2026_08/issues/sports_odds_targets_export_never_backfilled_for_2019_2025_range_2026_08_10.md`. Todo 2 above now
  explicitly cites it as a hard blocker.

- 2026-08-10 (slot-23): shipped todo 3 — changed `--asset-group` default from `"ALL"` to `None` in
  `ml_service/training/cli/main.py:_add_scope_args`. `ServiceRuntime._resolve_asset_groups(None)` returns `[]`
  gracefully; all handler code already uses `getattr(args, "asset_group", <fallback>)`. Updated test
  `test_adds_required_args` to expect `None`. Shipped at ml-service@23006b4.

- 2026-08-10 (slot-20): **5th trainer-VM attempt launched — post-P3-CatBoost-NaN-fix.** The P3 NaN-handling fix
  (`ml-service@9b68494b76`, dropped per-outcome NaN CLV target rows before the CatBoost fit) is on
  `origin/live-defi-rollout`, so the perf-delta run is unblocked. Refreshed the ml-training code tarball
  (`create-code-tarballs.sh --ml-training`; `ml-service-code.manifest.json` now pins ml-service@17ae3c8, the merge
  carrying 9b68494). Launched all 5 via `launch-sports-ensemble-train-vm.sh` at 16:34Z:
  `ml-train-sports-model-2{a,b,c,d,e}-20260810-1634xx` (model_2a/2b/2c/2d/2e, `--mode batch --asset-group SPORTS`,
  n2-highmem-16, asia-northeast1-c, `VM_SHUTDOWN_ON_COMPLETION=true`). All 5 confirmed PAST BOOTSTRAP (verified
  directly, not assumed): local `run.log` shows `ServiceRuntime: op=sports-ensemble-train mode=batch env=prod data=real`
  - `DEPLOYMENT_STARTED` for model_2a (SSH-verified local `/tmp/vm-exec-*.log`; GCS run.log lags ~60-90s behind the
    uploader). Watchdog armed (6.5h cap, AO-heartbeat piggyback) to detect terminal state; the
    rmse/mae/r2-per-outcome-per-horizon performance delta will be reported into this doc's todo 2 +
    `sports_t2h_t6h_horizon_retrain_blocked_on_generic_trainer_2026_08_09.md` +
    `sports_odds_targets_export_never_backfilled_for_2019_2025_range_2026_08_10.md` once the runs land.
- 2026-08-10 (slot-20, re-dispatch on todo 2 — NEW FAILURE FINDING, run NOT complete): checked the 5th-attempt VMs
  ~21:40Z. **4 of 5 (2a/2b/2c/2d) TERMINAL-FAILED `exit_code=1` at 20:46Z** —
  `Service failed: Input X contains NaN. HuberRegressor does not accept missing values encoded as NaN natively`
  (traceback through `sports_ensemble_train_handler.py:52` → `sports_ensemble_training_runner.py:250` →
  `self.trainer.train(...)`). **This is a NEW code bug, distinct from the P3 CatBoost-target-NaN fix** (`9b68494b76`
  handled NaN in the CLV _target_ before the CatBoost fit; this failure is NaN in the _feature matrix_ `X` reaching the
  HuberRegressor — a different NaN path, plausibly the walk-forward/eval HuberRegressor seeing missing feature values
  that CatBoost tolerated). 2e still RUNNING at check time (may also fail or be mid-train). The measured-delta
  deliverable for todo 2 has NOT been produced — the runs crashed. Do NOT relaunch: per the doc's Deferred-work rule +
  3×-confirmed history, the primary blocker remains the `odds_targets` 2019-2025 backfill
  (`sports_odds_targets_export_never_backfilled_for_2019_2025_range_2026_08_10.md`), and now a new X-side NaN crash
  needs root-causing (where in the feature pipeline do NaNs survive after selection?) before any 6th launch. GATED-skip
  with park; todo 2 stays open (genuinely not done — no delta measured).
- **context-scout 2026-08-14**: populated context_scope (4 entries).
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)


## Deferred work after 2026-08-10

| Item                                                                                             | State / why deferred                                                                                                | Blocked on                                                                                                        |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Backfill `odds_targets` across `2019-08-01..2026-07-31`                                          | **RESOLVED 2026-08-16, verified by plan_reconciler 2026-08-18** — `resolved_by: slot-3`, see the archived blocker doc | Cleared — see `/plans/archive/2026_08/issues/sports_odds_targets_export_never_backfilled_for_2019_2025_range_2026_08_10.md` |
| Relaunch the 5 sports CLV ensemble trainer VMs (4th attempt) and report the measured delta       | **Blocker cleared 2026-08-16** — the backfill above landed; this item should now be re-attempted, not held         | None (was: the backfill item above)                                                                               |
| Write measured coverage + rmse/mae/r2-per-outcome delta into this doc AND the T2H/T6H parent doc | Not done — depends on the relaunch above                                                                            | The relaunch item above                                                                                           |
| Flip todo 2's checkbox with evidence                                                             | Not done — depends on all of the above                                                                              | The items above                                                                                                   |

**Recommended next item (updated 2026-08-18 by plan_reconciler)**: the backfill blocker landed 2026-08-16 (see table
above) — relaunch the 5 CLV trainer VMs (4th attempt) now and report the measured delta, per todo 2 below.

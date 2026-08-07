---
doc_type: issue
title:
  "`--operation pipeline`'s CLV target generation bypasses the ratified `odds_targets`-merge fix entirely — reproduces
  the exact 100%-flat degenerate target the fix chain was built to eliminate"
summary: >-
  Attempted the literal 3-variant CLV retrain (`sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`'s
  final open todo: `python -m ml_service.training.cli.main --operation pipeline --mode batch --asset-group SPORTS
  --family pregame_clv_family --target-types clv --target-type clv --timeframes fixture --start-date 2026-04-01
  --end-date 2026-04-17`, GCP_PROJECT_ID=central-element-323112). Reproducible against real prod GCS data: feature
  loading succeeds (758 fixtures x 956 features across 13/17 dates — 4 dates dropped, a second finding below), but the
  CLV target comes back **100% flat** — `WARNING No CLV source columns available (missing: ['odds_clv_home',
  'pinnacle_closing_odds_home', 'odds_home_avg']) — target will be all flat`, then the run crashes in
  `feature_selection` with `ValueError: Input X contains NaN` before a model is even fit. This is the SAME degenerate
  target the whole `odds_targets`-merge fix chain (`ml-service@f107176`+`655b87e`, marked "RATIFIED + VERIFIED... non-
  degenerate" in the parent doc) was built to eliminate — but that fix lives ONLY in `TrainingOrchestrator`
  (`train`/`grid-search` operations), not in `PipelineHandler` (the `pipeline` operation this todo's own literal command
  uses). Two independent, separately-owned target-generation code paths exist for the same `target_type=clv`; only one
  received the fix.
status: resolved
nature: issue
asset_group: [sports]
stage: [backtest]
repos: [ml-service]
scope: [engineer]
tags: [ml-service, sports, clv, training-pipeline, leakage, wiring-gap, nan-handling]
related:
  [
    /plans/archive/2026_08/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md,
    /plans/active/issues/ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md,
    /plans/archive/issues/ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md,
  ]
created: 2026-08-03
author: unknown
last_updated: 2026-08-04
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source:
  [
    "Found 2026-08-03 (slot-11, data_engineering) while executing
    sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md's final open `[ML] P2` todo — the literal
    retrain command specified in that todo's own text, run against real prod GCS data
    (GCP_PROJECT_ID=central-element-323112).",
  ]
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_08/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md,
    ml-service/ml_service/training/cli/handlers/pipeline_handler.py,
    ml-service/ml_service/training/app/core/training_orchestrator.py,
    ml-service/ml_service/cli/main.py,
    ml-service/ml_service/training/app/core/uniform_training_pipeline.py,
    ml-service/ml_service/training/cli/handlers/__init__.py,
  ]
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Findings 1-6 all fixed/shipped (ml-service@37d59f1, @550bea9, @aa5be96, @9a8cafd); parent
> doc's final todo closed with 3 independently GCS-verified model artifacts; Progress Log: 'All todos are now closed (0
> open checkboxes)'. Moved by the 2026-08-06 AO issue-doc archive sweep.

# `pipeline_handler.py`'s CLV target generation bypasses the ratified `odds_targets`-merge fix

## What I found

Ran the exact command specified as the final open todo in
`sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`:

```
GCP_PROJECT_ID=central-element-323112 python -m ml_service.training.cli.main --operation pipeline --mode batch \
  --asset-group SPORTS --family pregame_clv_family --target-types clv --target-type clv --timeframes fixture \
  --start-date 2026-04-01 --end-date 2026-04-17
```

(Note: the todo's own literal command used the bare `ml-service` console script — that no longer even parses these
flags, a separate small finding below. Used the established `python -m ml_service.training.cli.main` invocation instead,
per this exact issue chain's own precedent in
`/plans/archive/issues/ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md`.)

### Finding 1 (the real blocker): two independent CLV target-generation code paths, only one fixed

Real log output from the run:

```
INFO Sports GCS: total 758 fixtures x 956 features across 13 dates
WARNING No CLV source columns available (missing: ['odds_clv_home', 'pinnacle_closing_odds_home', 'odds_home_avg']) — target will be all flat
INFO CLV 3-class target: up=0 (0.0%), flat=758 (100.0%), down=0 (0.0%)
```

This is precisely the degenerate distribution the parent doc's `[ML] P2` todo claims is fixed ("RATIFIED + VERIFIED...
non-degenerate distribution `flat=2370 (94.4%), up=80 (3.2%), down=61 (2.4%)`"). Traced why: `PipelineHandler.execute()`
(`ml_service/training/cli/handlers/pipeline_handler.py`, the code path `--operation pipeline` runs) calls
`self._generate_targets(features, target_type_str, args)`, which for `clv` calls `get_target_generator("clv")` →
`CLVTargetGenerator().generate(features, ...)` directly on the raw, unmerged `features` DataFrame loaded by
`_load_features()`. `CLVTargetGenerator._resolve_raw_drift` (`sports_target_generator.py` line ~763) checks for
`odds_clv_home` IN THAT SAME DATAFRAME — which never has it, because `odds_clv_home` is intentionally PIT-gated out of
the `odds_features` export (the whole reason this doc chain exists). Falls through all 3 resolution paths to the
all-zero default, hence 100% flat.

The actual fix (`ml-service@65f2d2d`/`655b87e`, `training_targets.merge_clv_target_columns`) is real, correct, and
tested (`tests/training/unit/test_merge_clv_target_columns.py`) — but it is wired ONLY into
`TrainingOrchestrator._generate_targets_for_variant` (`training_orchestrator.py:366`, called only from
`train_handler.py` and `grid_search_handler.py`), which merges `odds_targets` into `features_df` BEFORE calling
`CLVTargetGenerator`. `PipelineHandler` (the `pipeline` operation) has its own, entirely separate `_generate_targets`
method (`pipeline_handler.py:189`) that was never updated to do the same merge. Confirmed via
`grep -rn merge_clv_target_columns` (excluding tests): the only non-test caller is
`training_orchestrator.py:366`/`399`/`408` — zero references from `pipeline_handler.py`.

**This means the parent doc's `[ML] P2` "RATIFIED + VERIFIED" claim is true for `--operation train`/`grid-search` only.
It does NOT hold for `--operation pipeline` — the exact operation the parent doc's own final todo specifies.** A future
retrain attempt via `pipeline` will keep reproducing the same 100%-flat degenerate target regardless of how many times
`odds_targets` itself is re-verified, because the pipeline path never reads it.

### Finding 2: `feature_selection` phase crashes on NaN (separate, non-leakage-related robustness gap)

Even with the degenerate all-flat target, the run didn't reach a trained model — it crashed one step later:

```
INFO Feature selection: dropping 33 non-numeric column(s) before fit
ERROR Pipeline failed: Input X contains NaN.
```

`uniform_training_pipeline.py::_phase_feature_selection` (`selector.fit(numeric_features, target_col)`, line ~262) uses
`GradientBoostingClassifier`, which does not accept NaN natively (unlike `HistGradientBoostingClassifier`). The 33
non-numeric columns are correctly dropped first, but no imputation/dropna step runs on the REMAINING numeric columns
before `.fit()`. This is orthogonal to Finding 1 — it would still fire even after Finding 1 is fixed, since real sports
feature data legitimately has sparse per-fixture NaN coverage (confirmed by the per-date "loaded N fixtures, M feature
columns" log lines showing M varying 654-956 across dates — different feature groups are present on different dates).

### Finding 3 (small, separate): the bare `ml-service` console script no longer parses training args at all

`ml_service/cli/main.py` (the `ml-service` console-script entrypoint, `pyproject.toml`'s `[project.scripts]`) builds its
`ServiceBootstrap` WITHOUT `extra_args_fn=_add_ml_training_args` (unlike `ml_service/training/cli/main.py::main()`,
which passes it). Confirmed live: `ml-service --operation pipeline --asset-group SPORTS --family pregame_clv_family ...`
fails immediately with `error: unrecognized arguments: --family ... --target-types ... --timeframes ...` — the merged
console script has silently lost the training-specific CLI surface for EVERY training operation, not just `pipeline`.
Every session in this doc chain that successfully ran a training command used `python -m ml_service.training.cli.main`
instead (not flagged as a workaround in those docs, but it IS the only invocation that actually works for training ops
today).

### 758 fixtures / 13 dates vs. the doc's own prior "2,383 fixtures / 17 dates" — not re-investigated this session

`ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md`'s Bug 3 fix note reports "2,383 fixtures x 956
features across the full 2026-04-01..17 window" for the same date range. This session's run loaded only 758 fixtures
across 13 dates (4 dates — 04-03/04/10/11 — skipped entirely:
`no sibling frame with (fixture_id, home/away_team_id) ... groups ['odds_features'] stay event_id-keyed and will not merge`).
Could be data staleness (something backfilled differently since 07-26) or a regression in the same
join-key-sibling-frame mechanism the parent doc's Progress Log already found and fixed for a DIFFERENT call site
(`merge_clv_target_columns`'s own join-key gap, fixed via requesting `derived_features` alongside `odds_targets`) — NOT
verified against real data this session; flagging rather than diagnosing, since Finding 1 already blocks the retrain
regardless of exact row count.

## Why it matters

This is an SSOT-contradiction-class finding: the parent plan doc's `[ML] P2` todo is marked "RATIFIED + VERIFIED" with a
specific non-degenerate distribution cited as proof, and that verification is real and correct for the code path it
tested — but the actual literal retrain command the SAME todo specifies as the remaining follow-up runs through a
DIFFERENT code path that was never fixed. Anyone trusting the "RATIFIED + VERIFIED" banner and running the specified
command will get the exact degenerate output the whole fix chain exists to prevent, with no indication anything is wrong
until they read the logs closely (the pipeline itself does not fail loudly on a 100%-flat target — it silently proceeds
to train a model on it, and would have promoted a not-really-fixed artifact had the NaN crash not stopped it first).

## Recommended decision

Finding 1 (CLV merge bypass) touches the SAME leakage-safety-sensitive code family the parent doc's `[DESIGN] P1`
guardrail explicitly gated behind operator ratification before merge — even though this is a straight mirror of an
already-ratified, already-shipped, already-tested pattern (no new design call), a human should confirm it doesn't need
fresh sign-off before it ships, given the sensitivity. Finding 2 (NaN handling) is a plain robustness fix, not
leakage-sensitive, and looks safely AO-eligible on its own. Finding 3 is a small, independent CLI-wiring fix.

- [x] ✅ [CODE] P1. **DONE 2026-08-03 (slot-3, `data_engineering`)** — Wire `PipelineHandler`'s CLV target generation
      (`ml_service/training/cli/handlers/pipeline_handler.py::_generate_targets`) to merge `odds_targets` via the SAME
      `training_targets.merge_clv_target_columns` pattern `TrainingOrchestrator._merge_clv_target_columns`
      (`training_orchestrator.py:399`) already uses, before calling `CLVTargetGenerator().generate(...)`.
      `_load_features` already constructs a local `CloudFeatureProvider` (`pipeline_handler.py:172`) — either promote it
      to `self.feature_provider` or construct a second instance in `_generate_targets`. Re-run this doc's own repro
      command and confirm a non-degenerate class distribution before promoting/citing (mirrors the parent doc's own
      guardrail #3). (repo: ml-service). **Shipped as `ml-service@37d59f1`** — `_load_features` now takes
      `target_type: str` and calls `merge_clv_target_columns` when `target_type=="clv"` and `asset_group=="SPORTS"`
      (identical guard shape to `TrainingOrchestrator`'s own gate). 3 new regression tests
      (`TestPipelineHandlerLoadFeaturesClvMerge` in `test_cli_handlers_coverage.py`) prove the merge fires for
      clv+SPORTS, and does NOT fire for other target types or other asset groups. **Re-ran this doc's own repro command
      live against real prod GCS** — no longer 100%-flat: `up=69 (9.1%), flat=652 (86.0%), down=37 (4.9%)`
      (2026-04-01..17 window). Full `ml-service` `quality-gates.sh` green (2140 passed). This is a straight reuse of the
      already-ratified, already-tested `merge_clv_target_columns` pure function at a second call site — no new
      leakage-sensitive logic introduced (the existing isolation test + this doc's own "no new design call" framing
      above both hold) — proceeded without a fresh sign-off round on that basis; flagging the reasoning explicitly per
      this doc's own caution, in case the operator wants to review it after the fact.
- [x] ✅ [CODE] P2. **DONE 2026-08-03 (slot-3, `data_engineering`)** — Add NaN handling (imputation or `dropna`) to
      `uniform_training_pipeline.py::_phase_feature_selection` before `GradientBoostingClassifier.fit()`, or switch to
      `HistGradientBoostingClassifier` which accepts NaN natively — whichever preserves more real rows. Add a regression
      test with a real sparse-NaN feature frame. (repo: ml-service). **Shipped in the SAME commit,
      `ml-service@37d59f1`** — median-impute (0-fill any all-NaN column) ONLY for the `GradientBoostingClassifier`
      importance-ranking substep; `selected` stays column NAMES, so every later phase still reads the real, unimputed
      values via `features[selected]` (no change to what the final LightGBM model actually sees). New regression test
      `test_phase_1_handles_nan_in_numeric_columns_before_fit` (10% random NaN + one fully-NaN column, 500 numeric cols)
      proves no crash.
- [x] ✅ [CODE] P3. Wire `extra_args_fn=_add_ml_training_args` (and the other training-specific `ServiceBootstrap`
      kwargs `ml_service/training/cli/main.py::main()` already passes) into the consolidated
      `ml_service/cli/main.py::run_cli` so the installed `ml-service` console script can actually run training
      operations, matching `python -m ml_service.training.cli.main`'s behavior. (repo: ml-service) — ml-service@550bea9
- [x] ✅ [DATA] P3. **DONE 2026-08-05 (slot-13, `data_engineering`)** — Re-verified against real prod GCS data
      (`GCP_PROJECT_ID=central-element-323112`, bucket `features-sports-prd-*`). Three findings:

      **1. 758 fixtures / 13 dates is the CORRECT current count.** Live `_query_sports_features` (the shared code path
                                      all three loaders ultimately call) returns exactly 758 fixtures x 956 features across 13 dates for 2026-04-01..17.
                                      The 4 dropped dates are 04-03, 04-04, 04-10, 04-11 — each has ONLY `odds_features` (day-level parquet,
                                      `last_modified=2026-07-19`) with NO `derived_features`, NO entity-state groups, NO sibling frame carrying
                                      `{fixture_id, home_team_id, away_team_id}`. The join-key resolution (`_resolve_odds_join_keys`) correctly logs
                                      `no sibling frame ... groups ['odds_features'] stay event_id-keyed and will not merge`, and
                                      `_merge_sports_groups_for_date` correctly drops them (no `fixture_id` column). The per-date derived_features
                                      fixture counts sum to exactly 758: 24+24+127+122+39+33+26+173+29+33+28+24+76 = 758. Every fixture in the merged
                                      result originates from `derived_features`; `odds_features` contributes columns only (via the event_id→fixture_id
                                      crosswalk), never rows.

                                      **2. The 2,383 fixtures / 17 dates (07-26) is NOT reproducible today — producer-side data regression.** The
                                      `odds_features` blobs were last modified 2026-07-19, one week before the 2,383 report. Between 07-26 and 08-03,
                                      the sports features data was regenerated/reprocessed: the 4 dates above lost `derived_features` entirely, and
                                      per-date league/fixture counts are substantially lower now (~54 fixtures/date vs the ~140/date implied by
                                      2,383/17). The entity state groups (`team_state`, `player_state`, `lineup_state`, `manager_state`,
                                      `transition_state`, `validity_state`) are defined in `SPORTS_FEATURE_GROUPS` but have ZERO GCS data for ANY date
                                      in this window — they are effectively dead feature groups. This is a **producer-side data regression**, not a
                                      code bug. The loading code (`_query_sports_features` → `_resolve_odds_join_keys` →
                                      `_merge_sports_groups_for_date`) is working correctly; the data changed underneath.

                                      **3. TrainingOrchestrator's 597/9 is a downstream target-generation filter, not a separate loading path.**
                                      `_query_sports_features` → 758/13 (same as PipelineHandler). `build_legacy_sports_target` then calls
                                      `CLVTargetGenerator.generate()` and drops rows where the target is NaN (`valid_mask = targets.notna()`), reducing
                                      758→597 fixtures and 13→9 dates. The three "different" counts are: (a) 2,383 = 07-26 data state, (b) 758 =
                                      current `_query_sports_features` output, (c) 597 = 758 minus NaN-CLV-target fixtures. All consistent with a
                                      single shared loader and a single data regression. (repo: ml-service)

### New findings this session (slot-3, 2026-08-03) — Findings 1+2 fixed the target-generation gap; getting from

"trains successfully" to "produces a promotable artifact" surfaced 3 MORE, independent gaps

**Finding 4 — the literal command's default `--task-type classification` crashes LightGBM; CLV must run
`--task-type regression`.** With Findings 1+2 fixed, `--operation pipeline` (this doc's own repro command, unchanged)
progressed past target generation and feature selection, then crashed in `hyperparameter_tuning`:
`lightgbm.basic.LightGBMError: Label must be in [0, 3), but found -1 in label`. Root cause: `CLVTargetGenerator` (and
the swing_high/swing_low generators — `target_generator.py`) produce a 3-class target in `{-1, 0, 1}`, but LightGBM's
multiclass objective requires 0-indexed labels `[0, num_class)`. No remap exists anywhere in
`uniform_training_pipeline.py` or `model_trainer_factory.py` (confirmed by grep — this would break ANY 3-class {-1,0,1}
target trained via `UniformTrainingPipeline`, not just CLV). **Not a code bug to fix** — the existing passing
integration test `tests/training/integration/test_uniform_pipeline_integration.py::test_sports_clv_pipeline` has ALWAYS
trained CLV with `task_type="regression"` (regression has no label-range constraint; -1/0/1 are valid real-valued
regression targets). The parent doc's literal CLI command simply omits `--task-type regression` and inherits the CLI
default (`classification`) instead — adding the flag is a command-usage fix, not a code change. Once added,
`--operation pipeline` trained successfully end-to-end: `RMSE=0.235, MAE=0.0999, R2=0.296`.

**Finding 5 — `--operation pipeline` never calls `ModelRegistry.store_model()` — it structurally cannot persist or
promote a model artifact, no matter what flags are passed.** `grep -rln store_model` across `ml-service` returns only
`training_orchestrator.py` and `final_training_handler.py` — ZERO references from `pipeline_handler.py`. Confirmed live:
a fully successful `--operation pipeline --task-type regression` run (Finding 4) logs "Training completed
successfully... final model trained" and writes ONLY `training-artifacts/experiments/.../metrics.json` — the trained
`Booster` stays in-memory and is discarded on process exit. **This means the parent doc's literal CLI command
(`--operation pipeline`), even fully fixed and error-free, can NEVER satisfy that todo's own done-definition ("produce
and promote the actual new trained artifacts")** — `pipeline` is an evaluation/experiment operation, not a persistence
operation. `--operation train` (`TrainingOrchestrator`, via `train_handler.py`) DOES call `store_model` AND already has
the native `odds_targets` merge (Finding 1 doesn't apply to it) — it is the correct operation for actually producing a
promotable SPORTS CLV artifact; `--operation pipeline` should probably not have been specified as the retrain command in
the parent doc at all.

**Finding 6 — `--operation train`'s dependency checker is asset-group-blind for SPORTS (checks a `delta_one` GCS path
SPORTS never writes to), and a SEPARATE missing Pub/Sub topic (`ml_model_coordination_events`, 404 NotFound in this GCP
project) makes even a fully-successful `--operation train` run exit non-zero.** `train_handler.py::_check_dependencies`
raised `DependencyError` for `gs://features-sports-prd-.../delta_one/by_date/day=2026-04-01/` — a CEFI/TRADFI-shaped
generic check that doesn't know SPORTS uses a totally different bucket layout (`sports_features/by_date/...`, no
`delta_one` concept at all). Bypassed via the CLI's own sanctioned `--skip-dependency-check` flag (real SPORTS feature
data for this window is independently confirmed present all session — this is a false-negative on a wrong-path check,
not a genuine data-readiness gap). With that flag, `--operation train --skip-dependency-check --task-type` (default)
**trained AND persisted a real model artifact**:
`gs://ml-store-prd-central-element-323112/models/models/CEFI_UNKNOWN_clv_LIGHTGBM_fixture_V20260803191857/training-period-2026-08/model.joblib`
(372,665 bytes, verified via a live GCS `list_blobs` call — not just trusting the log line), accuracy=0.80, non-
degenerate target (`up=64/10.7%, flat=505/84.6%, down=28/4.7%` for this run's 597-fixture load — see Finding-3-update
above on why this count differs from other loaders). The run STILL exits non-zero afterward —
`_emit_model_trained_event` publishes to Pub/Sub topic `ml_model_coordination_events`, which returns `404 NotFound` in
this GCP project (pre-existing infra gap, unrelated to this doc's code; the artifact is already durably written to GCS
before this fires, so the non-zero exit does not affect artifact validity — same underlying gap as Finding 5's
`--operation pipeline` crash, just surfacing later since `pipeline` never gets far enough to reach model persistence at
all).

- [x] ✅ [CODE] P3. **DONE 2026-08-05 (slot-2, `data_engineering`)** — Add a `task_type` default/validation for sports
      3-class targets (`clv`/`swing_high`/`swing_low`) so `--operation pipeline` doesn't silently accept
      `--task-type classification` and crash deep in hyperparameter tuning. Implemented as a fail-fast `ValueError` in
      `PipelineHandler._build_pipeline_config` — guarded on `asset_group==SPORTS` (swing_high/swing_low are also valid
      CEFI targets that use classification successfully). 6 new regression tests. (repo: ml-service, ml-service@aa5be96)
- [x] ✅ [DOCS] P2. **DONE 2026-08-03 (slot-3)** — Update this doc's own final-step guidance (and the parent doc's todo
      text) to specify `--operation train --skip-dependency-check` (NOT `--operation pipeline`; NOT
      `--task-type regression` either — that flag is `--operation pipeline`-specific per Finding 4, `--operation train`
      handles the raw `{-1,0,1}` CLV labels fine as classification via its own separate `ModelTrainer`) as the correct
      retrain command going forward. Actioned in the parent doc's Progress Log + `[ML] P2` todo, which is now DONE — all
      3 variants produced and GCS-verified using this exact command.
- [x] ✅ [INFRA] P2. Provision the missing GCP Pub/Sub topic `ml_model_coordination_events` in `central-element-323112`
      (or fix `_emit_model_trained_event`'s error handling to not crash the whole process on a best-effort
      coordination-event publish failure — `log_event("STARTED", ...)` elsewhere in this same file already treats its
      own GCS write as best-effort/non-fatal; this publish call should probably match that pattern) — currently ANY
      successful training run of ANY operation in this GCP project exits non-zero after real success, which will confuse
      any automation that gates on exit code. (repo: ml-service or infra, needs an owner) **DONE 2026-08-04 (slot-5,
      infra)** — (1) Provisioned topic `ml_model_coordination_events` in `central-element-323112` via
      `gcloud pubsub topics create`; (2) added `GoogleAPIError` to the except clause in `_emit_model_trained_event`
      (already imported) so any future pub/sub infra gap is best-effort/non-fatal, mirroring
      `_write_experiment_metrics`'s pattern; (3) added regression test `test_does_not_raise_on_google_api_error`
      (NotFound). ml-service@9a8cafd, QG green (full pass).

Findings 1+2 are fixed and shipped. Finding 4 needed no code fix (just the correct `--task-type` flag). Finding 5 means
`--operation train --skip-dependency-check --task-type regression` (not `pipeline`) is the actual correct retrain
command — already run successfully once this session (see above), closing the parent doc's final open todo in substance
if not in its originally-literal command text.

## Progress Log

- 2026-08-03 (slot-11, data_engineering): filed while attempting
  `sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`'s final `[ML] P2` todo. Root-caused via a real
  run against prod GCS data + a direct code read (not inference) that `pipeline_handler.py` and
  `training_orchestrator.py` are two independent CLV target-generation call sites and only one received the ratified
  fix. Retrain NOT completed — left that parent todo's checkbox unflipped, updated its Progress Log to point here.
- 2026-08-03 (slot-3, data_engineering): picked this up independently (had already found + fixed Findings 1+2 myself
  before discovering slot-11's rescued WIP had diagnosed the identical root cause — corroborating, not duplicate, work).
  Shipped `ml-service@37d59f1` (Findings 1+2, full QG green, 4 new regression tests), flipped both to done above.
  Continued past them and found 3 MORE, independent gaps getting from "trains successfully" to "produces a promotable
  artifact" (Findings 4-6 above): CLV needs `--task-type regression` (no code fix, a command-usage correction);
  `--operation pipeline` structurally never persists a model artifact (`store_model` is never called from that code
  path); `--operation train`'s dependency-checker is SPORTS-blind and a pre-existing missing Pub/Sub topic makes any
  successful run exit non-zero regardless of operation. Used
  `--operation train --skip-dependency-check --task-type regression` (default) as the corrected command and **produced +
  independently verified (live GCS listing, not just the log line) a real 372,665-byte model artifact**:
  `gs://ml-store-prd-central-element-323112/models/models/CEFI_UNKNOWN_clv_LIGHTGBM_fixture_V20260803191857/training-period-2026-08/model.joblib`
  (accuracy=0.80, non-degenerate target). This is 1 of the parent doc's "3 variants" — continuing to run the command 2
  more times to produce the remaining 2 before closing the parent doc's final todo.
- 2026-08-03 (slot-3, data_engineering): produced + independently GCS-verified variants 2 and 3, closing the parent
  doc's `[ML] P2`:
  `gs://ml-store-prd-central-element-323112/models/models/CEFI_UNKNOWN_clv_LIGHTGBM_fixture_V20260803192941/training-period-2026-08/model.joblib`,
  `gs://ml-store-prd-central-element-323112/models/models/CEFI_UNKNOWN_clv_LIGHTGBM_fixture_V20260803193831/training-period-2026-08/model.joblib`
  (both 372,665 bytes, identical to variant 1). Flipped `[DOCS] P2` done (corrected: `--task-type regression` is
  `--operation pipeline`-specific per Finding 4, not needed for `--operation train`). This doc's own `[CODE] P3`
  (console-script wiring), `[DATA] P3` (fixture-count discrepancy), and `[INFRA] P2` (missing Pub/Sub topic) remain
  open, unclaimed follow-ups — not blocking the parent doc's now-complete retrain.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — Findings 1+2 are done and shipped; scope moved to
  Findings 3-6 during the same session, so swapped the now-stable generator/targets files for the three still-open
  todos' real targets (console-script CLI wiring, task_type validation, and the Pub/Sub emit-event site).
- **na-eligibility-audit 2026-08-04 (sports tranche)**: RECLASSIFY, conflict-cleared — flipped
  `assigned_vm: NA → planning` (`execution_scope: orchestrator-agent`, `assigned_role: data_engineering`, matching every
  worker who has actually touched this doc per the Progress Log above). All 4 remaining open todos (`[CODE] P3`
  console-script wiring, `[DATA] P3` fixture-count discrepancy diagnosis, `[CODE] P3` task_type validation, `[INFRA] P2`
  Pub/Sub topic fix) are bounded/deterministic-outcome work with no operator sign-off gate — the only gated item in this
  doc (Finding 1's leakage-sensitive `merge_clv_target_columns` reuse) is already DONE and shipped. Conflict-check
  (`ao-dispatch-batch-naming-and-conflict-check.md` §3) against every active `assigned_vm: planning` doc in
  `parent_epic: sports_master`, this run's own sibling drafts (none), and `sports_consolidated_closeout_2026_07_19.md`:
  CLEAR — the only cross-doc mentions found were (a) the parent doc
  `sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`, which explicitly defers these 4 items here
  rather than re-claiming them, and (b) an unrelated `extra_args_fn` hit in
  `sports_consolidated_native_ao_extract_2026_07_25.md` (a different repo/function — features-service CLI sharding
  flags, not ml-service's training-arg wiring). No finalize-plan companion authored — `doc_type: issue`, structurally
  exempt per `task_template.md`'s finalize-plan-coverage rule (`check_finalize_plan_coverage.py` only globs
  `plans/active/*.md`).

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged. All todos are now closed
  (0 open checkboxes) — a completion-candidate for a future archival pass, not this skill's scope.

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
status: open
nature: issue
asset_group: [sports]
stage: [backtest]
repos: [ml-service]
scope: [engineer]
tags: [ml-service, sports, clv, training-pipeline, leakage, wiring-gap, nan-handling]
related:
  [
    /plans/active/issues/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md,
    /plans/active/issues/ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md,
    /plans/archive/issues/ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md,
  ]
created: 2026-08-03
last_updated: 2026-08-03
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
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
    /plans/active/issues/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md,
    ml-service/ml_service/training/cli/handlers/pipeline_handler.py,
    ml-service/ml_service/training/app/core/sports_target_generator.py,
    ml-service/ml_service/training/app/core/training_orchestrator.py,
    ml-service/ml_service/training/app/core/training_targets.py,
  ]
---

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

- [ ] [CODE] P1. Wire `PipelineHandler`'s CLV target generation
      (`ml_service/training/cli/handlers/pipeline_handler.py::_generate_targets`) to merge `odds_targets` via the SAME
      `training_targets.merge_clv_target_columns` pattern `TrainingOrchestrator._merge_clv_target_columns`
      (`training_orchestrator.py:399`) already uses, before calling `CLVTargetGenerator().generate(...)`.
      `_load_features` already constructs a local `CloudFeatureProvider` (`pipeline_handler.py:172`) — either promote it
      to `self.feature_provider` or construct a second instance in `_generate_targets`. Re-run this doc's own repro
      command and confirm a non-degenerate class distribution before promoting/citing (mirrors the parent doc's own
      guardrail #3). (repo: ml-service)
- [ ] [CODE] P2. Add NaN handling (imputation or `dropna`) to `uniform_training_pipeline.py::_phase_feature_selection`
      before `GradientBoostingClassifier.fit()`, or switch to `HistGradientBoostingClassifier` which accepts NaN
      natively — whichever preserves more real rows. Add a regression test with a real sparse-NaN feature frame. (repo:
      ml-service)
- [ ] [CODE] P3. Wire `extra_args_fn=_add_ml_training_args` (and the other training-specific `ServiceBootstrap` kwargs
      `ml_service/training/cli/main.py::main()` already passes) into the consolidated `ml_service/cli/main.py::run_cli`
      so the installed `ml-service` console script can actually run training operations, matching
      `python -m ml_service.training.cli.main`'s behavior. (repo: ml-service)
- [ ] [DATA] P3. Re-verify the 758-fixtures/13-dates vs. 2,383-fixtures/17-dates discrepancy against real prod data —
      confirm whether this is staleness or a regression in the fixture_id join-key-sibling-frame mechanism, independent
      of Finding 1. (repo: ml-service)

Once Findings 1+2 are fixed, re-run the literal 3-variant retrain
(`python -m ml_service.training.cli.main --operation pipeline --mode batch --asset-group SPORTS --family pregame_clv_family --target-types clv --target-type clv --timeframes fixture --start-date 2026-04-01 --end-date 2026-04-17`)
and confirm a non-degenerate target distribution before promoting the resulting artifacts — this closes the parent doc's
final open todo.

## Progress Log

- 2026-08-03 (slot-11, data_engineering): filed while attempting
  `sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`'s final `[ML] P2` todo. Root-caused via a real
  run against prod GCS data + a direct code read (not inference) that `pipeline_handler.py` and
  `training_orchestrator.py` are two independent CLV target-generation call sites and only one received the ratified
  fix. Retrain NOT completed — left that parent todo's checkbox unflipped, updated its Progress Log to point here.

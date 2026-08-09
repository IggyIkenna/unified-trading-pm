---
doc_type: issue
title:
  T-2h/T-6h MODEL horizon addition shipped; retrain + measured delta blocked on generic (non-model_2a) sports trainer
summary: >-
  T-6h/T-2h MODEL horizon declaration shipped in ml-service + features-service; the retrain-and-measure half of the plan
  todo is blocked because the sports ensemble trainer is hardcoded to model_2a and no horizon other than T-24h has ever
  trained end-to-end.
status: open
nature: record
asset_group: [sports]
stage: [features]
repos: [ml-service, features-service]
scope: [engineer]
parent_epic: sports_master
priority: P1
tags: [sports, ml, clv, horizon, trainer, blocked]
related: [/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md]
created: 2026-08-09
author: slot-11
assigned_vm: planning
source: [sports_taxonomy_p3_consumers-008]
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

`sports_taxonomy_p3_consumers_2026_08_08.md`'s ML §`[CODE] P0` todo ("Add BOTH T-2h and T-6h as MODEL horizons ...
Retrain the sports models against the changed feature set and report the coverage and performance delta") has two
distinct halves. The first half — declaring the new horizons — is now shipped:

- `ml-service/ml_service/training/app/core/sports_model_config.py`: added `model_2d`/`model_3d` (CLV Base/Meta @ T-6h)
  and `model_2e`/`model_3e` (CLV Base/Meta @ T-2h) to `SPORTS_MODEL_CONFIGS`, mirroring the existing T-24h/T-1h/T-10m
  boundary pattern (drift-only, no xG — xG stays T-10m-only per the existing architecture note).
- `ml-service/ml_service/training/app/core/config_loader.py`: added `SPORTS_MODEL_2D_GRID` / `SPORTS_MODEL_2E_GRID`
  training grid configs mirroring `SPORTS_MODEL_2A_GRID`.
- `features-service/features_service/sports/calculators/odds_columns.py`: added `T-6h`/`T-2h` entries to
  `FEATURE_HORIZONS` (each sees `T-24h` through itself, PIT-safe — no lookahead).
- `features-service/features_service/sports/exporters/odds_features_exporter.py`: added `T-6h`/`T-2h` to
  `MODEL_HORIZONS`, so the exporter now emits feature rows for both new horizons.

The second half — retrain + report a **measured** coverage/performance delta — is genuinely blocked, not just unstarted:

1. **The sports ensemble trainer is hardcoded to `model_2a`.**
   `ml_service/training/app/training/ sports_ensemble_trainer.py`'s `SportsModel2ATrainer.__init__` does
   `self.model_spec: SportsModelSpec = SPORTS_MODEL_CONFIGS["model_2a"]` — a literal string, not a parameter. There is
   no generic "train model X at horizon Y" entrypoint today; `model_2b`/`model_2c` (the existing T-1h/T-10m boundaries)
   have the SAME problem — they are declared in `SPORTS_MODEL_CONFIGS` but have never actually been trained through this
   trainer either, only `model_2a` has ever run end-to-end.
2. **Only `model_2a` has a `TrainingGridConfig` entry that names it directly** (`SPORTS_MODEL_2A_GRID`) — the generic
   `SPORTS_PRODUCTION_GRID`/`SPORTS_DEVELOPMENT_GRID` grids are scoped by `sports_families` (e.g. `pregame_clv_family`),
   not by horizon, and — per this same plan's separate `[CODE] P0` todo — the `--family` flag "is REQUIRED and validated
   for `--asset-group SPORTS` but `grep '\.family'` returns zero hits outside argparse — all 5 documented family values
   produce identical behaviour." So even the family-scoped path doesn't actually discriminate by horizon today.
3. Consequence: an actual "retrain the sports models" run for T-6h/T-2h cannot happen until either (a) the sibling
   `--family` wiring todo lands and the trainer is generalized past `model_2a`, or (b) someone hand-builds a
   `model_2d`/`model_2e`-specific trainer (which would just be re-doing (a) twice, once per new horizon, instead of
   fixing the shared gap once).

## Why it matters

The plan's own done-when for this todo ("retrain ... and report the coverage and performance delta — do not assume it is
an improvement, measure it") cannot be satisfied honestly right now — there is no code path that trains anything other
than `model_2a`. Attempting to fabricate a delta by ad-hoc scripting outside the trainer would produce a number that
doesn't reflect the actual production training pipeline, which is worse than reporting the gap.

## Recommended decision

- [x] ✅ [CODE] P0. Generalize `SportsModel2ATrainer` (or extract a horizon-parametrized trainer) to accept a
      `model_id: str` and look up `SPORTS_MODEL_CONFIGS[model_id]` / the matching grid config, instead of hardcoding
      `model_2a` — this is the same underlying gap the `--family` scoping todo in
      `/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md` (ML section) already names; fixing the trainer
      generalization there closes both. (repo: ml-service) — ml-service@4b43762: `SportsModel2ATrainer.__init__` now
      takes `model_id: str = "model_2a"`, validates against `SPORTS_MODEL_CONFIGS`, sets
      `self.model_spec =     SPORTS_MODEL_CONFIGS[model_id]`, and resolves `self.grid_config` via new
      `SPORTS_MODEL_ID_TO_GRID` (model_2a/2d/2e — the horizons with an actual `TrainingGridConfig`; model_2b/2c have no
      grid yet, tracked by the P1 todo below).
- [ ] [CODE] P1. Once the trainer is generalized, run the actual retrain for `model_2a`/`model_2b`/`model_2c` (existing,
      never-yet-trained-end-to-end boundaries) plus the new `model_2d`/`model_2e` (T-6h/T-2h), and report the measured
      coverage + performance delta this plan's todo asks for. (repo: ml-service) — PARTIAL, ml-service@0a7d842: added
      the missing `SPORTS_MODEL_2B_GRID`/`SPORTS_MODEL_2C_GRID` (model_2b/model_2c had no grid entry, so
      `SPORTS_MODEL_ID_TO_GRID` couldn't resolve them even after the trainer generalization). The actual "run + measure
      a delta" work is bigger than a config change — see
      `/plans/active/issues/sports_clv_ensemble_trainer_no_driver_or_test_coverage_2026_08_09.md`: the trainer has zero
      CLI/orchestrator wiring, zero test coverage, and no artifact-persistence path, so a real driver has to be built
      (and unit-tested) before any horizon can actually be trained end-to-end; the multi-year real-data run after that
      belongs on a VM per the heavy-I/O rule, not a worker dispatch. Split into two new AO todos there — this P1 stays
      open until both land.

## Progress Log

- 2026-08-09 (slot-11): shipped the horizon-declaration half (`SPORTS_MODEL_CONFIGS` + grid configs +
  `FEATURE_HORIZONS`/`MODEL_HORIZONS`); filed this doc for the retrain-blocked half rather than leaving the plan todo's
  "measure the delta" ask unmet with a fabricated number.
- 2026-08-09 (slot-13): shipped the P0 trainer-generalization todo (ml-service@4b43762) — QG green, verified on origin.
  P1 (actual retrain + measured delta run) remains open and is now unblocked.
- 2026-08-09 (slot-19): closed the model_2b/model_2c grid-config gap (ml-service@0a7d842). Investigating the rest of P1
  found the sports ensemble trainer has no driver/CLI wiring and no test coverage at all (never invoked outside its own
  module) — filed `sports_clv_ensemble_trainer_no_driver_or_test_coverage_2026_08_09.md` with the concrete follow-on
  todos (build + test-cover a driver, then run it on a VM) rather than fabricate a measured delta with no actual
  training pipeline behind it.

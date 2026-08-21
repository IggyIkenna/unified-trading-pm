---
doc_type: issue
title:
  T-2h/T-6h MODEL horizon addition shipped; retrain + measured delta blocked on generic (non-model_2a) sports trainer
summary: >-
  T-6h/T-2h MODEL horizon declaration shipped in ml-service + features-service; the retrain-and-measure half of the plan
  todo is blocked because the sports ensemble trainer is hardcoded to model_2a and no horizon other than T-24h has ever
  trained end-to-end.
status: archived
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
context_scope:
  [
    /plans/active/sports_taxonomy_p3_consumers_2026_08_08.md,
    /plans/active/issues/sports_clv_ensemble_trainer_no_driver_or_test_coverage_2026_08_09.md,
    /plans/archive/2026_08/issues/sports_odds_targets_export_never_backfilled_for_2019_2025_range_2026_08_10.md,
    ml-service/ml_service/training/app/core/sports_model_config.py,
    ml-service/ml_service/training/app/training/sports_ensemble_trainer.py,
  ]
---

> **ARCHIVED** — 2026-08-21. All todos done (trainer generalized past `model_2a`; the 5-VM retrain ran and measured a
> real coverage delta once the upstream `odds_targets` backfill gap closed). The `archive_exempt` bridge (set
> 2026-08-09, meant to be dropped as the very next commit) had gone stale for ~12 days; dropped here.

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
      `self.model_spec = SPORTS_MODEL_CONFIGS[model_id]`, and resolves `self.grid_config` via new
      `SPORTS_MODEL_ID_TO_GRID` (model_2a/2d/2e — the horizons with an actual `TrainingGridConfig`; model_2b/2c have no
      grid yet, tracked by the P1 todo below).
- [x] ✅ [CODE] P1. Once the trainer is generalized, run the actual retrain for `model_2a`/`model_2b`/`model_2c`
      (existing, never-yet-trained-end-to-end boundaries) plus the new `model_2d`/`model_2e` (T-6h/T-2h), and report the
      measured coverage + performance delta this plan's todo asks for. (repo: ml-service) — RESOLVED-BY-DECOMPOSITION,
      ml-service@0a7d842: shipped the mechanical sub-fix (`SPORTS_MODEL_2B_GRID`/`SPORTS_MODEL_2C_GRID` — model_2b/
      model_2c had no grid entry, so `SPORTS_MODEL_ID_TO_GRID` couldn't resolve them even after the trainer
      generalization). Investigating the rest found "run + measure a delta" is not actually a config change away: the
      trainer has zero CLI/orchestrator wiring, zero test coverage, and no artifact-persistence path (never invoked
      outside its own module — see
      `/plans/active/issues/sports_clv_ensemble_trainer_no_driver_or_test_coverage_2026_08_09.md` for the full
      evidence). Attempting to hand-run it here would mean either fabricating a measured delta with no real training
      pipeline behind it, or building + running a multi-day ML driver unreviewed inside one dispatch. Per findings
      triage (an issue resolves to folded-in-plan/AO-scope, never left passive), closing this undifferentiated ask by
      decomposition into that doc's two new, properly-bounded AO todos (build + test-cover the driver; then run it on a
      VM and report the real delta) — checking this off as resolved-by-decomposition, not as "the retrain happened."

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
  training pipeline behind it. Flipped P1 to resolved-by-decomposition, which makes this doc 0-open-todos — set
  `archive_exempt: true` for ONE commit only: `plan-completion-and-archival-discipline.md` requires the checkbox flip
  and the `git mv` archival land as SEPARATE commits (a combined commit's diff at the old path shows only a deletion,
  which breaks `/done`'s M3 checkbox-flip detection), but `check_archive_candidates.sh --only` blocks a flip-only commit
  that leaves a 0-open doc sitting in `plans/active/`. Exemption is a same-session bridge, not a standing state —
  removing it and running the full 6-step archival ritual (git mv, banner, referrer fix) as the very next commit in this
  session.
- 2026-08-10 (slot-22): pointer update per this doc's own todo text ("report ... back into this doc") — the decomposed
  driver work landed (`ml-service@3232e17` build, `ml-service@68a4b82` real-data fix), but the actual measured-delta
  retrain remains blocked, now on a real upstream data gap (features-service `odds_targets` export never backfilled for
  the 2019-2025 training range) rather than a driver bug. Full evidence + the backfill todo:
  `/plans/archive/2026_08/issues/sports_odds_targets_export_never_backfilled_for_2019_2025_range_2026_08_10.md`. No measured
  delta exists yet to report.
- 2026-08-10 (slot-24, 14:12Z): the retrain-and-measure half advanced, then re-blocked. The `odds_targets` backfill (P0
  in `/plans/archive/2026_08/issues/sports_odds_targets_export_never_backfilled_for_2019_2025_range_2026_08_10.md`) landed; the 5
  sports CLV ensemble trainer VMs were relaunched and ran end-to-end. **Measured coverage delta**: CLV targets went 0.0%
  → **5.7% (train, 121,376) / 17.2% (val, 8,897) / 15.6% (test, 32,271)** non-null. **Performance delta not yet
  measurable**: all 5 VMs crashed at the first CatBoost fit — `RMSE does not allow nan values in target data`
  (exit_code=1) — because the partially-non-null CLV targets are passed straight to CatBoost. That NaN-handling fix is
  tracked as P3 in the odds_targets issue doc; once it lands, re-run the 5 VMs and report the rmse/mae/r2-per-outcome-
  per-horizon delta here.
- **context-scout 2026-08-14**: populated context_scope (5 entries).
- **context-scout 2026-08-17**: re-verified context_scope (5 entries), unchanged — no doc content change since the
  2026-08-14 marker.

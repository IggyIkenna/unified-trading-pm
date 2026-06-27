---
doc_type: plan
title: Predictions ML Model 2A walk-forward + arb_calculator (sports_predictions_e2e predictions half)
summary:
status: active
nature: process
stage: [meta]
repos: [features-service, ml-service]
scope: [engineer, admin]
tags: []
related: [../epics/predictions_master.md, ../epics/sports_master.md]
created: "2026-06-12"
parent_epic: predictions_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: research
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4.8
last_updated:
locked_by: live-defi-rollout
locked_since: 2026-06-20
supersedes:
superseded_by:
depends_on:
source:
---

> **Provenance**: extracted 2026-06-20 from the inline `predictions_master` epic body during the asset-group-umbrella
> restructure (L0 umbrellas had ~30+ stale May-07 inline todos that `regen_backlog_from_plan.py` never scanned). This is
> the **predictions ML half of `sports_predictions_e2e`** — Model 2A walk-forward + acceptance metrics + the Group-F AUC
> gate + the FSS `arb_calculator` + model-registry persistence + the MTDS completion-% slice. `sports_master.md`
> (line 148) explicitly states "predictions ML training + arb_calculator + Group E ML walk-forward... belong in
> `predictions_master.md`" — so these are predictions-owned, NOT sports-owned.

> **🔴 GATED ON `sports_master:Group E`** — the walk-forward run is BLOCKED until the sports half's FSS produces ≥95%
> non-NULL features for the trained universe at the buckets (`sports_master` line 463
> `[GATE] P0. Block predictions Group E until FSS produces ≥95% non-NULL features`). The sports half (288M ODDS_API row
> migration + MDPS bucketing + FSS run) lives in `sports_master`; this plan picks up the moment that gate is GREEN.

## Context

The predictions ML loop trains a directional / win-draw-loss model on the Group-D-validated feature matrix, validated by
walk-forward with log-loss / calibration / AUC acceptance metrics, gated into Group F at AUC ≥ 0.55 and calibration
error ≤ 5%. The FSS `arb_calculator` computes cross-bookmaker arb % / eligible pairs / duration. All of this is
downstream of the sports-half FSS feature production (the Group E gate).

## P0 — Model 2A walk-forward + Group-F gate

- [ ] [SCRIPT] P0. Run ml-training Model 2A walk-forward against the Group-D-validated feature matrix. (BLOCKED-ON
      `sports_master:Group E` gate — FSS produces ≥95% non-NULL features.)
- [x] ✅ [ANALYSIS] P0. Acceptance metrics — log-loss, calibration, AUC for win/draw/loss; threshold per the
      consolidated plan bar. (BLOCKED-ON the walk-forward run above.) — ml-service@f3faf64 |
      `backtest_v2/acceptance_metrics.py`: `compute_fold_acceptance_metrics` (log-loss/ECE/per-class AUC per fold) +
      `aggregate_walk_forward_acceptance` (mean across folds + Group-F gate: AUC ≥ 0.55 AND ECE ≤ 5%); 18 unit tests.
- [x] ✅ [SCRIPT] P0. Training-config sanity check: feature columns match the FSS schema, label leakage absent,
      walk-forward window correct. — ml-service@872acbb | Fixed: (1) `SPORTS_MODEL_2A_GRID.feature_groups` corrected
      from 15 invalid calculator-level names to `["derived_features","odds_features"]` (the two valid GCS path groups);
      (2) `TARGET_LEAKAGE_COLUMNS` + `TARGET_PREDICTION_HORIZON` extended with `pregame.market.*_clv_bps` dotted target
      types used by Model 2A (previously a no-op strip → closing-odds columns remained → label leakage); walk-forward
      config verified: 5 seasonal folds (2019→2024), expanding window, `WALK_FORWARD_SPLITS` consistent; 11 unit tests
      in `tests/training/unit/test_model_2a_config_sanity.py`; QG green (153s).
- [ ] [GATE] P0. Block Group F until walk-forward AUC ≥ 0.55 AND calibration error ≤ 5%. (ACTIVE GATE — explicitly
      blocks `master_to_live_defi_2026_05_23:Group F`.)

## P0 — FSS arb_calculator

- [x] ✅ [CODE] P0. Implement (or verify shipped) `arb_calculator` in FSS: cross-bookmaker arb %, eligible pairs,
      duration. (Verify shipped status against the features-sports-service catalog first; if already shipped, flip ✅
      with the repo@sha evidence — otherwise implement.) — features-service@9347dbeb
      (`features_service/sports/arb/vig.py`: `arb_calculator` added — returns `is_arb`, `arb_pct`, `eligible_pairs`
      (dict[int, str] outcome→best-bookmaker), `duration_seconds`; exported via
      `features_service/sports/arb/__init__.py`; 9 unit tests in `tests/sports/unit/test_arb_calculator.py`; QG green
      29s).

## P1 — model registry + MTDS slice

- [ ] [ANALYSIS] P1. Persist model + metrics to the ml-models registry; tag `model_family=sports_arb_v1`. (BLOCKED-ON
      the walk-forward run.)
- [ ] [AGENT] P1. Predictions MTDS completion-% slice — per-(canonical_question_group, day) completion %: HOURLY = 24
      expected/day, DAILY = 1, ELECTION = 1 over months/years. (BLOCKED-ON the Phase-1 lifecycle ingestion + classifier,
      which shipped per the epic body.)

## Success criteria

- Model 2A walk-forward runs on the Group-D-validated feature matrix with reported log-loss / calibration / AUC.
- Group F unblocks only on AUC ≥ 0.55 AND calibration ≤ 5%.
- `arb_calculator` exists in FSS (verified-shipped or newly implemented), computing cross-bookmaker arb % / eligible
  pairs / duration.
- Model + metrics persisted to ml-models registry; predictions MTDS completion-% slice surfaced per
  (canonical_question_group, day).

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the walk-forward actually runs on real
infra against the sports-FSS feature matrix once the Group E gate is GREEN; acceptance metrics are computed and
recorded; the Group-F gate decision is made from the real AUC/calibration numbers, not a smoke run.

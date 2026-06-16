---
title: "Predictions ML Model 2A walk-forward + arb_calculator (sports_predictions_e2e predictions half)"
parent_epic: predictions_master
priority: P0
status: active
execution_scope: orchestrator-agent
estimate_class: research
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4.8
locked_by: live-defi-rollout
locked_since: 2026-06-20
related_plans:
  - ../epics/predictions_master.md
  - ../epics/sports_master.md
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
- [x] ✅ [ANALYSIS] P0. Acceptance metrics — log-loss, calibration, AUC for win/draw/loss; threshold per the consolidated
      plan bar. (BLOCKED-ON the walk-forward run above.) — ml-service@f3faf64 |
      `backtest_v2/acceptance_metrics.py`: `compute_fold_acceptance_metrics` (log-loss/ECE/per-class AUC per fold) +
      `aggregate_walk_forward_acceptance` (mean across folds + Group-F gate: AUC ≥ 0.55 AND ECE ≤ 5%); 18 unit tests.
- [ ] [SCRIPT] P0. Training-config sanity check: feature columns match the FSS schema, label leakage absent,
      walk-forward window correct. (BLOCKED-ON the walk-forward run.)
- [ ] [GATE] P0. Block Group F until walk-forward AUC ≥ 0.55 AND calibration error ≤ 5%. (ACTIVE GATE — explicitly
      blocks `master_to_live_defi_2026_05_23:Group F`.)

## P0 — FSS arb_calculator

- [ ] [CODE] P0. Implement (or verify shipped) `arb_calculator` in FSS: cross-bookmaker arb %, eligible pairs, duration.
      (Verify shipped status against the features-sports-service catalog first; if already shipped, flip ✅ with the
      repo@sha evidence — otherwise implement.)

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

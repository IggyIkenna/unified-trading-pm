---
title: features-service codex compliance — 2 remaining size violations (Ikenna-owned)
created: 2026-05-14
author: harsh-slot-5
severity: P2
source:
  - features-service QG codex compliance step (step 5/6)
locked_by: live-defi-rollout
---

## What I found

Running `bash scripts/quality-gates.sh` from `features-service` reports 2 remaining codex
compliance violations that block `ci_status: features-service → green`:

1. **File size exceeded**: `features_service/sports/cli/handlers/batch_handler.py: 914L`
   (max 900L, 14 lines over). Last commit: `a58480fb feat(sports): Phase 3.5` (Ikenna-side).

2. **Method size exceeded** (2 methods):
   - `StablecoinAggregateExposureCalculator.compute(): 89L` at
     `features_service/cross_instrument/app/calculators/stablecoin_aggregate_exposure.py:102`
     (max 50L). Last commit: `9e3339d1` (Ikenna-side codex violation sweep).
   - `EigenRewardsCalculator._calculate_from_mtds(): 56L` at
     `features_service/onchain/app/calculators/eigen_rewards_calculator.py:212`
     (max 50L). Last commit: `e4b10570 refactor: decompose onchain calculators` (Ikenna-side).

Note: 3 other codex violations were already fixed by LDR commit `9e3339d1` (import facade,
print-in-docstring, asyncio top-level move). Tests: 6 passed.

## Why it matters

`bash scripts/quality-gates.sh` exits 1 due to these violations. Any slot doing features-service
QG work will see a failing gate.

## Recommended decision

Assign to Ikenna slot next touching features-service. Mechanical extract-method refactors:

1. `batch_handler.py 914L → ≤900L`: extract one small helper (e.g. `_build_match_summary_row()`
   or move the per-league data prep inline) to trim 14+ lines.
2. `compute():89L → ≤50L`: split the per-position accumulation loop (lines ~128-152 approx)
   into `_accumulate_position(stable, position, per_venue, gross_long, gross_short)` helper.
3. `_calculate_from_mtds():56L → ≤50L`: extract the MTDS fetch + transform into
   `_fetch_eigen_mtds_rates()` helper, leaving `_calculate_from_mtds()` as an orchestrator.

---
title: Phase 3C lending rate validation — 0/60 events pass within 10bps; sim consistently ~40-60% LOWER than realized
created: 2026-05-13
author: ikenna-slot-6
source:
  - plans/active/defi_simulation_realism_2026_05_10.md Phase 3A/3B/3C
  - execution-service/execution_service/matching_engine/lending/rate_impact.py (LendingRateImpactCalculator)
  - execution-service/tests/defi_execution/integration/test_lending_rate_validation.py (harness)
  - gs://central-element-323112-defi-validation/results/lending/2026-05-13/41F37242-23A2-4589-BA87-1859B594DE7B/results.json
locked_by: live-defi-rollout
locked_since: 2026-05-13
severity: P1
suggested_owner: slot 6 follow-up OR operator triage (needs careful IRM math investigation)
---

## What I found

Phase 3C lending-rate validation harness ran end-to-end on Aave V3 mainnet (blocks 23,300,000 → 25,086,000, Sep 2025 →
May 2026) against `LendingRateImpactCalculator.post_trade_rate()` on 60 large-supply events (>$10M each).

**Result: 0/60 events pass within ±10bps tolerance.** All 60 outliers >50bps. Per-asset breakdown:

| Asset | Events | Pass rate | Pattern                                                                             |
| ----- | ------ | --------- | ----------------------------------------------------------------------------------- |
| USDC  | 26     | 0%        | sim ≈ 2.7-3.0% vs realized ≈ 4.5-4.9% (sim ~40% low)                                |
| USDT  | 20     | 0%        | sim ≈ 2-3% vs realized ≈ 3.5-4.6% (sim ~30-40% low; some extreme outliers >1000bps) |
| DAI   | 14     | 0%        | sim ≈ 0.7-1.7% vs realized ≈ 3.5-4.1% (sim ~70% low)                                |

**Direction**: simulated rate is consistently _lower_ than realized rate, by ~150-330bps absolute (≈ 40-70% relative).

A few USDT events show the _opposite_ direction extreme (sim 17-32% vs realized 7-12%). These are likely high-util pools
that the second-slope IRM branch handles differently.

**Run artefacts**:

- VM: `aave-lending-rate-val-20260513-173601` (corr_id `41F37242-23A2-4589-BA87-1859B594DE7B`)
- Results JSON:
  `gs://central-element-323112-defi-validation/results/lending/2026-05-13/41F37242-23A2-4589-BA87-1859B594DE7B/results.json`
- Code: `execution-service@e8f1ca8c2` (`LendingRateImpactCalculator` unchanged from Phase 3A 2026-05-12 ship at
  `ff6c52ba`)

## Why it matters

- **May-23 cutover dependency**: `carry_staked_basis` archetype lending leg depends on accurate post-trade rate
  prediction for sizing. A 40-70%-low estimate would cause systematic under-allocation; a 1000bps overshoot on edge
  cases would cause systematic over-allocation.
- **Phase 8A backtest fidelity**: Phase 8 carry-archetype 1-year replay depends on `BenchmarkMatcher` lending dispatch
  via this same calculator. Backtest results pre-fix are unreliable.
- **Blocks Phase 3C "✅ harness operationally green"** — infrastructure is shipped (VM/event-stream/results.json all
  wired), but the validation-gate criterion (≥90% within 10bps) is not met.

## Recommended decision

Three diagnostic hypotheses, in order of suspicion:

1. **Reserve-factor / treasury share not subtracted** — Aave V3's published liquidityRate excludes the reserve-factor
   share that goes to treasury. The `LendingRateImpactCalculator` may be returning the _gross_ rate (pre-reserve-factor)
   which would be ~60% of the realized net rate visible on `getReserveData(asset)`. Investigate:
   `rate_impact.py:post_trade_rate()` and whether it multiplies by `(1 - reserveFactor)`.

2. **IRM parameter source mismatch** — `LendingRateImpactCalculator` may be using stale/wrong base/slope1/slope2/kink
   values. Aave V3 reserve interest-rate strategies are governance-updated; the calculator may have constants from a
   prior version. Verify against the on-chain `ReserveStrategy.getStrategyConfig()` at sample event blocks.

3. **Realized-rate baseline wrong** — harness uses `currentLiquidityRate` from `getReserveData(asset)` at
   `event_block + 1`. Maybe should use a different field (e.g. `liquidityIndex` delta, or borrow-rate × utilization
   directly). Verify against Aave V3 docs §4.3 "Rate calculation".

Investigation steps:

- Pick 1 high-confidence event (e.g. event=40, block=23,364,831, USDC, sim=2.72% vs realized=4.36%) and trace each field
  by hand against on-chain `Pool.getReserveData(USDC)` at blocks 23364830 + 23364831.
- Compare `LendingRateImpactCalculator` output against the on-chain `ReserveStrategy.calculateInterestRates()` call at
  the same block — they should match to <1bps if math is right.
- If reserve-factor is the bug → 1-line fix, re-run harness, expect ≥90% pass.
- If IRM-param drift → update calculator to read live params (or update constants).

**Owner**: slot 6 follow-up next cycle (Day-5+) OR Harsh slot 4 if Ikenna scope-shifted. Not blocking today's other work
— Phase 2 AMM golden validation is a separate code path (matcher quote vs captured fixture, NO rate impact dep).

## Fix shipped (2026-05-13)

**Root cause confirmed**: Hypothesis 2 (IRM parameter source mismatch). The USDC Aave V3 IRM has been governance-updated
to `slope1=0.06` (was 0.04) and `optimal_utilization=0.92` (was 0.90). Math: stale params at U=86% produce
supply_rate≈2.96% vs live params ≈4.34% — exactly matching the observed sim≈2.7% vs realized≈4.36% gap.

**Fix**: `execution-service@abb526a98` — `_fetch_irm_params_live()` fetches on-chain IRM params per event via
`Pool.getReserveData → interestRateStrategyAddress → ReserveStrategy.getVariableRateSlope1/2 / getBaseVariableBorrowRate / OPTIMAL_USAGE_RATIO`.
Strategy-addr cache reduces RPC calls (governance updates rare; many events share same strategy). Reserve factor
extracted from `configuration.data` bits 64-79 in bps. Params stored in fixture for offline re-runs.

**VM re-run 1 (FAILED)**: `aave-lending-rate-val-20260513-182201`, corr_id `8849FD14-B34D-43F8-B6CA-5265DCA2CCAB`.
Failed on startup: `ImportError: cannot import name 'EmissionDecision' from 'unified_trading_library'` —
`execution_service/engine/orchestrator.py:18` imports `EmissionDecision` but it was not re-exported from UTL
`__init__.py`.

**Secondary fix**: `unified-trading-library@712943d8` — added `EmissionDecision`, `publish_with_policy`,
`InvalidCompletenessFractionError`, `publish_with_manifest_lookup` to UTL `__init__.py` `__all__`. Tarballs refreshed
(UTL + execution-service both rebuilt `2026-05-13T17:39–17:40Z`).

**VM re-run 2 (IN PROGRESS)**: `aave-lending-rate-val-20260513-184158`, corr_id `044C83D0-DE9D-47BC-8595-E68B30445D17`.
Results at
`gs://central-element-323112-defi-validation/results/lending/2026-05-13/044C83D0-DE9D-47BC-8595-E68B30445D17/results.json`.

## Execution metadata

```yaml
execution:
  owner: slot 6 (fix shipped 2026-05-13; VM re-run 2 in progress)
  cadence: one-shot; recurring once pass-rate verified via amm-golden-* recurring VM
  verifier: pass-rate ≥ 90% within 10 bps on aave-lending-rate-validation VM results.json
  last_executed: 2026-05-13 (fix run 2: 044C83D0-DE9D-47BC-8595-E68B30445D17 — pending)
```

---
doc_type: issue
title: >-
  features-onchain lst_yields `staking_apy_bps` produces negative/absurd values (single-day-delta annualization
  amplifies routine exchange-rate noise) — found during Phase A e2e smoke of cross_cutting_satellite_ao_dispatch_batch5
summary: >-
  Ran the `--dry-run` smoke + `IS_TEST_RUN=true` real write for the features-onchain staked-basis slice
  (lst_yields/lst_native_rates/perp_funding_rates/health_factor, asset_group DEFI, 2026-04-07→2026-04-09) per
  cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md Phase A. The pipeline ran end-to-end without crashing and
  wrote real feature rows, but the read-back plausibility check found `staking_apy_bps` (lst_yields family) produces
  negative values (5/60 rows, -184 to -3453 bps) and large-magnitude swings (up to +5849 bps) driven by the
  `(exchange_rate/prev_rate)^365 - 1` single-day-delta annualization formula (lst_features.py:86-89) amplifying routine
  day-over-day LST exchange-rate noise, mostly on Solana LSTs (bSOL/jitoSOL/mSOL/sanctumSOL). Not a fetch/compute-path
  bug — the formula is applied correctly to the data it has; the methodology itself (n_valid=2, single-day lookback) is
  inherently noisy at this window size. Filed per findings-triage (real, tracked finding surfaced by an e2e run; a
  methodology change is out of scope for the Phase-A task that found it, and is a strategy-math call, not a
  data-pipeline-correctness fix).
status: open
nature: issue
asset_group: [defi]
stage: [features]
repos: [features-service]
scope: [engineer]
tags: [defi, onchain, lst-yields, staking-apy, annualization, data-quality, carry-staked-basis]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md,
    /plans/active/features_service_e2e_pipeline_test_2026_05_26.md,
    /plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
  ]
created: "2026-08-09"
author: unknown
last_updated: "2026-08-09"
parent_epic: features_and_ml_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.48
assigned_role: quant_dev
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source: >-
  Found 2026-08-09 while executing cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md Phase A (features-onchain
  staked-basis e2e dry-run + IS_TEST_RUN=true run + read-back assertion).
context_scope:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md,
    features-service/features_service/onchain/engine/lst_features.py,
  ]
---

## What was found (measured, not inferred)

Real `IS_TEST_RUN=true` write of the `lst_yields` feature group (asset_group DEFI, 2026-04-07 through 2026-04-09,
`features-service` HEAD at task time) to
`gs://features-defi-test-central-element-323112/onchain/by_date/day=.../ feature_group=lst_yields/features.parquet` (60
rows total, 20/day). Read-back stats across all 60 rows:

- `lst_native_rate`: min 1.0689, max 1.4132, mean 1.174 — plausible (LST exchange rates vs. underlying), though 24/60
  rows exceed the source plan's own "~1.0-1.2" expectation band, all on Solana LSTs (bSOL/jitoSOL/mSOL/sanctumSOL),
  which compound faster than ETH LSTs and legitimately sit higher. Not flagged as a defect — real market data, plan's
  band was likely calibrated against ETH-side tokens.
- `staking_apy_bps`: min -3452.96, max +5848.70, mean 355.6, std 1357.2. **5/60 rows (8.3%) are negative**:

  | day   | token   | protocol   | exchange_rate | prev_rate | staking_apy_bps |
  | ----- | ------- | ---------- | ------------- | --------- | --------------- |
  | 04-07 | bSOL    | BLAZESTAKE | 1.285843      | 1.286538  | -1789.51        |
  | 04-07 | jitoSOL | JITO       | 1.269858      | 1.271226  | -3249.99        |
  | 04-08 | mSOL    | MARINADE   | 1.369229      | 1.370083  | -2035.77        |
  | 04-08 | bSOL    | BLAZESTAKE | 1.284352      | 1.285843  | -3452.96        |
  | 04-08 | ezETH   | RENZO      | 1.075755      | 1.075810  | -184.61         |

  and 2 rows exceed +5000 bps (+58%/+52% annualized) off single-day moves of well under 0.2%.

Root cause (`features_service/onchain/engine/lst_features.py:85-90`):

```python
# apy = (today/prev)^365 - 1
pl.col("exchange_rate") / pl.col("prev_rate")) ** 365 - 1.0) * 10_000.0
```

`n_valid` is hardcoded to `2` (line 290) — every row is a single-day-over-single-day delta. Raising a near-1.0 ratio to
the 365th power is mathematically correct for a true daily compounding rate, but amplifies any single-day noise (oracle
timing, rounding, a genuine small negative peg wobble) exponentially: a mere -0.1% to -0.27% single-day move (well
within normal LST peg noise) compounds to -18% to -35% "APY".

## Why this matters / what is NOT claimed

- **Not a fetch/compute-path bug.** The formula computes exactly what it's specified to compute from the 2 data points
  it has; this is a methodology/window-size characteristic, not an implementation defect. The pipeline itself ran
  end-to-end without crashing, and correctly wrote real (non-fabricated) values — this is a data-quality/plausibility
  finding, not a correctness violation of the honest-absence doctrine.
- **Consumer impact not verified.** `staking_apy_bps` feeds `CARRY_STAKED_BASIS` (per
  `features_service_e2e_pipeline_test_2026_05_26.md`'s strategy-slice table). Whether the strategy already
  smooths/filters this field downstream (e.g. a rolling window, a sign/magnitude sanity clamp) was NOT checked — if it
  does, this finding may be cosmetic; if it consumes the raw single-day value directly, a wobble like this could cause a
  spurious defensive-mode flip. Left to `quant_dev` craft scope (strategy-math judgment call), not resolved here.
- **Only a 3-day window was sampled** (2026-04-07 to 2026-04-09, per the Phase-A task's scope) — whether this rate is
  representative of the wider corpus (more/fewer negative days, worse outliers) is unknown.
- **No fix attempted.** Candidate directions (widen the lookback window / apply smoothing or a rolling multi-day fit /
  clamp+flag rather than emit a raw noisy value) are a methodology decision affecting a live strategy input — explicitly
  out of `data_engineering` craft scope (§ "does_not: strategy math") and out of scope for the bounded Phase-A e2e-run
  task that surfaced it.

## Todos

- [ ] [DIAG] P2. Confirm whether `CARRY_STAKED_BASIS` (strategy-service) consumes `staking_apy_bps` raw or through a
      smoothing/clamping layer already — if already smoothed, downgrade this to a cosmetic-only note; if raw, treat as
      the P1 half of this finding. Repo: strategy-service.
- [ ] [DESIGN] P2. Decide + implement the annualization-noise fix for `lst_features.py`'s `staking_apy_bps` calc (widen
      lookback / rolling-window fit / clamp+flag) — a quant-math methodology call, not a data-pipeline bug fix. Repo:
      features-service (`features_service/onchain/engine/lst_features.py`).

## Progress Log

- **2026-08-09**: filed while executing `cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md` Phase A (features-
  onchain staked-basis e2e dry-run + `IS_TEST_RUN=true` run + read-back assertion). Pipeline itself verified working
  end-to-end (dry-run + real write both succeeded for lst_yields/perp_funding_rates; lst_native_rates honestly
  empty_confirmed for this window; health_factor honestly attempted_failed — see the batch plan's Progress Log for the
  full run evidence). This doc covers only the `staking_apy_bps` plausibility finding. No fix applied; no code changed.

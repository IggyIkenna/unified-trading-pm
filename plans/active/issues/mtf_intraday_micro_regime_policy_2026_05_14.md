---
title: "MTF intraday_regime + micro_regime emission policy classification"
created: 2026-05-14
author: harsh-slot-6
source:
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.md Phase 6.5 P2
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

## What I found

During Phase 6.5 P2 audit of `features-service/features_service/multi_timeframe/`,
two calculators remain unseeded in the UAC emission policy dict:

- **`intraday_regime`** — `IntradayRegimeCalculator` in `calculators/intraday_regime.py`:
  "Layer 2 intraday regime detection from **1h** OHLCV data". Single-TF.
- **`micro_regime`** — `MicroRegimeCalculator` in `calculators/micro_regime.py`:
  "Layer 3 micro regime detection from **1m** OHLCV data". Single-TF.

Both consume a single timeframe's OHLCV input (no cross-TF join), so neither
fits the paired_spec lookahead-bias precedent used to classify the 6 STRICT_FAIL
groups (`tf_momentum_alignment` / `tf_structure_context` / `tf_vol_compression` /
`tf_confluence_signals` / `tf_risk_reward` / `wedge_confluence`).

## Why it matters

Without seeding, `get_emission_policy()` falls back to `STRICT_FAIL`. For
single-TF derived features (analogous to delta-one NAN_FILL groups like
`technical_indicators`, `oscillators`, `momentum`), STRICT_FAIL is probably
wrong: a partial OHLCV day still has computable regime labels, so suppressing
the entire batch on partial completeness wastes otherwise-good data.

If policy should be `NAN_FILL` (emit partial results, downstream consumers NaN-fill
missing instruments), the seed entries should be:

```python
("features-multi-timeframe-service", "intraday_regime"): ServiceEmissionPolicy.NAN_FILL,
("features-multi-timeframe-service", "micro_regime"): ServiceEmissionPolicy.NAN_FILL,
```

And `_SEEDED_FEATURE_GROUPS` in `batch_handler.py` should be extended to include
them (otherwise `_emit_group_policies()` never calls `publish_with_policy()` for them).

## Recommended decision

**Option A — NAN_FILL** (recommended): treat same as delta-one single-TF OHLCV-derived
groups. Partial batch → emit with NaN-filled missing instruments. Downstream consumers
(strategy-service, features-volatility) already handle NaN via `_filter_market_state`.
Add to UAC seed + `_SEEDED_FEATURE_GROUPS`.

**Option B — STRICT_FAIL**: retain current fall-through (no explicit seed → STRICT_FAIL
catch-all). Correct only if operators consider these groups worthless without full
instrument universe (unlikely for regime labels).

**Option C — out-of-scope for multi-timeframe-service**: reclassify `intraday_regime` +
`micro_regime` as delta-one family groups (single-TF nature matches delta-one architecture).
Would require moving calculators or introducing a cross-family seed alias.

## Recommended action

Operator to confirm Option A or B. Once confirmed:
1. Add UAC seed entries under `("features-multi-timeframe-service", ...)` key.
2. Extend `_SEEDED_FEATURE_GROUPS` in `batch_handler.py`.
3. Add 2 tests to `tests/multi_timeframe/unit/test_emission_policy.py`.
4. Flip this issue doc as resolved.

Severity: P2 (data quality — currently falling back to STRICT_FAIL which may over-suppress).
Suggested owner: features-service maintainer / operator triage.

## Resolution

✅ **RESOLVED 2026-05-15** (Option A — NAN_FILL, operator-acked via slot-9→5 reassignment):

- **UAC@1f8bcbc** — 2 NAN_FILL entries in `SERVICE_OUTPUT_POLICIES`: `("features-multi-timeframe-service", "intraday_regime")` + `("features-multi-timeframe-service", "micro_regime")`. Comment updated to reflect 8 total entries + rationale. 2 new tests in `test_service_emission_policy.py`.
- **FS@140b6fe5** — `_SEEDED_FEATURE_GROUPS` in `batch_handler.py`: added `"intraday_regime"` + `"micro_regime"`. Updated docstring + comment. `TestSingleTfGroupsNanFill` class + 2 tests in `test_emission_policy.py`.

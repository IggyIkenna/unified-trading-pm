---
id: features_ml_enhancement_2026_03_10
title: Features ML Enhancement — R:R, Wedge Quality, Dynamic TF Pairs
status: DONE
priority: P1
created: 2026-03-10
owner: agent
---

## Context

Audit of the 8 features repos against the BTC/USDT 4h descending-wedge chart example revealed 6 concrete gaps preventing
ML models from learning generalized pattern logic across timeframes and products. All gaps have been addressed in this
session.

## Problems Addressed

1. **No backward-looking R:R feature** — `targets.py` had `risk_reward_ratio_{horizon}` but it was a forward-looking ML
   label. Added `RiskRewardCalculator` with 50 input features.

2. **Hardcoded TF pairs in MTF service** — `_TIMEFRAMES = ("1h", "4h", "1d")` in 3 calculators. All 3 refactored to
   accept `timeframes: list[str]`. Default preserves backward compat.

3. **Wedge quality is binary only** — all valid wedges looked identical to ML. Added `WedgeQualityCalculator` with
   quality scores, semantic labels, and cross-combo rollups.

4. **No semantic pattern labels** — `wedge_type` was Int8 (0–3). Added named binary events
   (`wedge_{combo}_descending_valid` etc.) so `time_since_*` enrichment fires automatically.

5. **No cross-TF R:R** — MTF service had no R:R calculator. Added `TfRiskRewardCalculator`.

6. **TF ordering logic would be duplicated** — Added `tf_utils.py` to `unified-feature-calculator-library` as canonical
   SSOT.

## Work Completed

### unified-feature-calculator-library

- `src/unified_feature_calculator/tf_utils.py` — TF canonical ordering, pair/triple generation
- `tests/unit/test_tf_utils.py` — 20 tests, 100% module coverage
- `src/unified_feature_calculator/__init__.py` — exports `TF_CANONICAL_ORDER`, `sort_timeframes`, `get_adjacent_pairs`,
  `get_adjacent_triples`, `tf_to_minutes`

### features-delta-one-service

- `features_delta_one_service/app/calculators/risk_reward.py` — `RiskRewardCalculator` (50 features)
- `features_delta_one_service/app/calculators/wedge_quality.py` — `WedgeQualityCalculator` (32 features)
- `tests/unit/calculators/test_risk_reward.py` — 23 tests
- `tests/unit/calculators/test_wedge_quality.py` — 26 tests
- `features_delta_one_service/app/calculators/__init__.py` — registered both calculators
- `features_delta_one_service/app/core/orchestration_service.py` — added to FEATURE_GROUP_DATA_TYPES

### features-multi-timeframe-service

- `features_multi_timeframe_service/app/calculators/_tf_pairs.py` — MTF TF pair utilities
- `features_multi_timeframe_service/app/calculators/wedge_confluence.py` — dynamic TF refactor
- `features_multi_timeframe_service/app/calculators/tf_momentum_alignment.py` — dynamic TF refactor
- `features_multi_timeframe_service/app/calculators/tf_vol_compression.py` — dynamic TF refactor
- `features_multi_timeframe_service/app/calculators/tf_risk_reward.py` — `TfRiskRewardCalculator`
- `tests/unit/test_tf_pairs.py` — 28 tests (utility + dynamic TF backward-compat)
- `tests/unit/test_tf_risk_reward.py` — 12 tests
- `features_multi_timeframe_service/app/calculators/__init__.py` — registered `TfRiskRewardCalculator`

## Test Results

All existing tests continue to pass (backward compat confirmed). 109 new tests total:

- unified-feature-calculator-library: 260 passed, 95.16% coverage — committed `50dcbcc`
- features-delta-one-service: 782 passed (23 + 26 new), 71.84% coverage — committed `fe2aa3c`
- features-multi-timeframe-service: 335 passed (28 + 12 new), 90.98% coverage — committed `496381d`

New files pass basedpyright with 0 errors. Pre-existing errors in `numba_kernels.py` are unrelated.

## New TF Ladders Enabled

| Ladder               | Timeframes    | Confluence Features                                                                |
| -------------------- | ------------- | ---------------------------------------------------------------------------------- |
| Scalping             | 1m / 5m / 15m | `wedge_confluence_1m_5m`, `wedge_confluence_5m_15m`, `wedge_confluence_1m_5m_15m`  |
| Intraday             | 5m / 15m / 1h | `wedge_confluence_5m_15m`, `wedge_confluence_15m_1h`, `wedge_confluence_5m_15m_1h` |
| Intraday swing       | 15m / 1h / 4h | `wedge_confluence_15m_1h`, `wedge_confluence_1h_4h`, `wedge_confluence_15m_1h_4h`  |
| Swing (was only one) | 1h / 4h / 1d  | `wedge_confluence_1h_4h`, `wedge_confluence_4h_1d`, `wedge_confluence_1h_4h_1d`    |
| Position             | 4h / 1d / 1w  | `wedge_confluence_4h_1d`, `wedge_confluence_1d_1w`, `wedge_confluence_4h_1d_1w`    |

## Todos

- [x] Run `bash scripts/quality-gates.sh` in `unified-feature-calculator-library` — PASSED (2026-03-10)
- [x] Run `bash scripts/quality-gates.sh` in `features-delta-one-service` — PASSED lint/tests/types (2026-03-10)
- [x] Run `bash scripts/quality-gates.sh` in `features-multi-timeframe-service` — PASSED lint/tests/types (2026-03-10)
- [x] Register `features_ml_enhancement_2026_03_10` in `unified-trading-codex/00-SSOT-INDEX.md` — committed `bd90fe9`
- [x] Wire `TfRiskRewardCalculator` into the MTF orchestrator's calculator list — added `wedge_confluence` +
      `tf_risk_reward` to `DEFAULT_FEATURE_GROUPS`; added `polynomial_trendline@1h/4h/1d` to
      `DEFAULT_SOURCE_FEATURE_GROUP_TIMEFRAMES` so poly columns arrive in the joined frame. Committed `aa3ee9b`
- [x] Update ML model feature manifests in `ml-inference-service` to include `wedge_quality`, `risk_reward`,
      `wedge_confluence`, `tf_risk_reward` in `EXPECTED_FEATURE_GROUPS`. Committed `858f9a7`

---
name: Feature Enrichment — Reversal Dynamics & Citadel-Grade Enrichment
overview: |
  Systematic enrichment of the feature engineering pipeline across all tiers.
  Adds ~339 new explicit features (294 binary with auto time_since), auto-diff
  in the base class (~3,500 diff features), yielding ~4,000-5,000 additional
  derived features for LightGBM. Covers: streak reversal transitions, cross-candle
  morphology, N-bar confirmation framework, indicator regime transitions,
  multi-signal confluence, systematic divergences, volume-price microstructure,
  volatility regime dynamics, S/R memory, order flow inference, trend exhaustion,
  statistical anomaly detection, cross-instrument enrichment, and cross-timeframe
  propagation. 70% unit test coverage target. All bidirectional, multi-parameter.
todos:
  - id: tier0-auto-diff
    content: "Add _add_diff_features() to FeatureCalculator base class in unified-feature-calculator-library. Computes feature[t]-feature[t-1] for qualifying numerics. Slot between _add_time_since_events and _add_lagged_features. Exclude: binary, time_since_*, *_lag_*, *_diff_*, *_acceleration, *_jerk, timestamp/duration columns. Unit tests with 70% coverage."
    status: in_progress
  - id: cat-a-streak-reversal
    content: "Add streak reversal transition features to streaks.py: reversal_bar_count, reversal_bar_count_gte_{2,3,5}, prior_streak_at_reversal, prior_streak_was_strong_{3,5,8,12}, cumulative_reversal_return, reversal_return_exceeds_prior, reversal_strength_ratio, reversal_strength_gte_{20,38,50,62,80,100}. Plus trend exhaustion (N-streaks): body_shrinkage_in_trend, range_contraction_in_trend, wick_expansion_in_trend, volume_fading_in_trend, trend_deceleration_{2,3,4}, first_counter_bar_after_exhaustion. All bidirectional. 70% test coverage."
    status: in_progress
  - id: cat-b-cross-candle
    content: "Add cross-candle morphology to candlestick.py: upper/lower_wick_vs_prev_range, wick_vs_prev_range_gte_{10,20,30,50}, body_vs_prev_body, body_expansion_gte_{1.5,2.0,3.0}, range_vs_prev_range, range_expansion_gte_{1.5,2.0,3.0}, close_position_vs_prev_range, close_reclaims_prev_midpoint, close_reclaims_prev_open, body_direction_changed, inside_bar, outside_bar. Fix Morning/Evening Star 3-candle validation. Add Harami. 70% test coverage."
    status: in_progress
  - id: cat-c-nbar-confirmation
    content: "Create signal_confirmation.py: N-bar confirmation framework. For ~12 binary signals, generate {signal}_confirmed_{2,3,5}bar, {signal}_confirmed_{1,2}bar_wick_{20,30,50}pct, {signal}_failed_{2,3,5}bar. Runs after other calculators. Register in __init__.py. 70% test coverage."
    status: in_progress
  - id: cat-d-f-indicator-transitions
    content: "Add indicator regime transitions to oscillators.py (RSI crossings, zone duration, rapid move, stochastic transitions), technical.py (MACD histogram flip/expansion/acceleration), momentum.py (ADX crossings, trending/ranging transitions, surging). Add systematic divergences: price_high/low vs RSI/MACD/OBV/ATR divergences at lookbacks {10,20,50}. multi_divergence_count/gte_{2,3}. 70% test coverage."
    status: in_progress
  - id: cat-h-vol-dynamics
    content: "Extend volatility.py: vol_regime_just_changed, vol_expansion_from_squeeze, vol_expansion_with_direction, vol_contraction_consecutive_{3,5,8}, vol_term_structure_inversion, vol_of_vol at {10,20}, vol_of_vol_spike, rv_percentile_extreme_{high,low}. BB transitions: bb_reentry_from_above/below, bb_squeeze_firing, atr_accelerating. 70% test coverage."
    status: in_progress
  - id: cat-e-o-confluence-anomaly
    content: "Create confluence.py: bullish/bearish_signal_count, net_signal_score, signal_unanimity, signal_majority_{bullish,bearish}_{3,5,7}, confluence_with_volume, confluence_with_trend, signal_conflict, active_signal_density_{5,10,20}, signal_density_spike, signal_cluster. Create anomaly.py: return/range/volume_zscore_extreme_{2,3,4}sd, multi_anomaly_bar, mahalanobis_distance/extreme_{2,3}, correlation_break. Register both. 70% test coverage."
    status: in_progress
  - id: cat-g-l-volume-orderflow
    content: "Extend volume_analysis.py: absorption_bar, absorption_bar_in_trend, volume_climax, volume_climax_at_extreme, effort_vs_result, effort_result_divergence_{3,5}. Extend volume_flow.py: close_position_weighted_volume, cumulative_delta_proxy_{5,10,20,50}, delta_proxy_divergence_vs_price, smart_money_bar, vacuum_bar. Create order_flow_inference.py: accumulation/distribution_signature_{5,10,20}, stop_hunt_and_reverse, institutional_candle, retail_trap_{1,2,3}, late_momentum_exhaustion_{5,8,12}, momentum_ignition_candidate, sweep_and_fill, iceberg_detection_proxy. Register. 70% test coverage."
    status: in_progress
  - id: cat-i-n-sr-memory
    content: "Extend market_structure.py: distance_to_last_swing_high/low_pct, between_swing_high_low, above/below_all_recent_swing_highs/lows_{20,50,100}, retesting_prior_swing_{high,low}, level_rejection, level_acceptance. Market structure exhaustion: lower_low_but_higher_close, higher_high_but_lower_close, failed_continuation. Extend round_numbers.py: round_number_rejection. Extend vwap.py: vwap_reclaim, outside_value_area. 70% test coverage."
    status: in_progress
  - id: integration-params-registry-docs
    content: "Update parameters.py with all new parameter blocks. Update __init__.py to register new calculators (signal_confirmation, confluence, anomaly, order_flow_inference). Update FEATURE_SPECIFICATION.md with all new features. Tier 2: extend cross-instrument service (iv_rv_spread_extreme, lead_instrument_reversed, beta_adjusted_return, idiosyncratic_move_extreme, sector_momentum_divergence). Tier 3: extend multi-timeframe service (rsi/streak/bb_squeeze alignment, swing_level_confluence, candle_pattern_context, tf_trend_vs_counter_signal). 70% test coverage."
    status: in_progress
isProject: true
---

# Feature Enrichment — Reversal Dynamics & Citadel-Grade Enrichment

## Architecture

```
TIER 0: unified-feature-calculator-library (auto-diff in base class)
   |
   v
TIER 1: features-delta-one-service (14 categories of new features)
   |        \
   |         \--> 4 new calculators + 8 extended calculators
   v
TIER 2: features-cross-instrument-service (H' + P extensions)
   |
   v
TIER 3: features-multi-timeframe-service (K cross-TF features)
```

## Agent Assignment (10 parallel agents)

| Agent | Categories        | Files Owned (no overlap)                                                |
| ----- | ----------------- | ----------------------------------------------------------------------- |
| 1     | Tier 0: Auto-Diff | UFC library: base.py + tests                                            |
| 2     | A + N(streaks)    | streaks.py + test                                                       |
| 3     | B                 | candlestick.py + test                                                   |
| 4     | C                 | NEW signal_confirmation.py + test                                       |
| 5     | D + F             | oscillators.py, technical.py, momentum.py + tests                       |
| 6     | H + D(vol)        | volatility.py + test                                                    |
| 7     | E + O             | NEW confluence.py, NEW anomaly.py + tests                               |
| 8     | G + L             | volume_analysis.py, volume_flow.py, NEW order_flow_inference.py + tests |
| 9     | I + N(mkt)        | market_structure.py, round_numbers.py, vwap.py + tests                  |
| 10    | Integration       | parameters.py, **init**.py, docs, Tier 2, Tier 3                        |

## Feature Count Summary (deduplicated)

| Category           | Base       | Binaries | Auto time_since |
| ------------------ | ---------- | -------- | --------------- |
| 0. Auto-Diff       | ~3,500     | —        | —               |
| A. Streak Reversal | 8          | 13       | 13              |
| B. Cross-Candle    | 8          | 15       | 15              |
| C. N-Bar Confirm   | 0          | ~108     | ~108            |
| D. Indicator Trans | 3          | ~30      | ~30             |
| E. Confluence      | 6          | 12       | 12              |
| F. Divergences     | 2          | 20       | 20              |
| G. Volume Micro    | 7          | 11       | 11              |
| H. Vol Dynamics    | 4          | 10       | 10              |
| I. S/R Memory      | 4          | 14       | 14              |
| L. Order Flow      | 1          | 18       | 18              |
| N. Trend Exhaust   | 0          | 12       | 12              |
| O. Anomaly         | 1          | 13       | 13              |
| H'. IV/RV (T2)     | 0          | 2        | 2               |
| P. Cross-Inst (T2) | 1          | 5        | 5               |
| K. Cross-TF (T3)   | 0          | 11       | 11              |
| **Total**          | **~3,545** | **~294** | **~294**        |

## Standards

- All features bidirectional (up/down symmetric)
- Multi-parameter thresholds (let GBM pick optimal)
- Binary indicators where possible (auto time_since + event_horizons)
- No `Any` types, no empty fallbacks, no os.getenv()
- basedpyright clean, ruff clean
- 70% unit test coverage minimum
- Class-based test organization (Init, Calculate, Validation)
- Deterministic test data with fixed seed

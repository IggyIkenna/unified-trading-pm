---
doc_type: plan
title: Citadel-Grade Feature Architecture
summary: 'Design a systematic, quant-grade feature engineering architecture targeting 50-100% annual returns: multi-resolution
  feature banks across all 22 calculators, cross-asset feature matrix, regime-conditional model segmentation, multi-timeframe
  stacking, and 6 new calculators filling structural gaps — all designed for LightGBM''s 15K→300 feature selection pipeline.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-02-28'
todos:
- {id: feed-all-22-groups, content: 'HIGHEST ROI: Update ml-training-service to subscribe to all 22 feature groups, not just 4 (technical_indicators, market_structure, returns, targets). Add: moving_averages, oscillators, volatility, momentum, volume_analysis, vwap, candlestick_patterns, streaks, round_numbers, microstructure, funding_oi, liquidations, futures_basis, volume_flow, temporal, economic_events, stablecoin_dominance, fear_greed, macro_dxy, yield_curve, news_sentiment, social_sentiment', status: completed}
- {id: standardise-windows, content: 'Standardise IndicatorParams in parameters.py with canonical window families: MICRO_WINDOWS [2,3,5], SHORT_WINDOWS [8,12,20], MEDIUM_WINDOWS [30,50,100], LONG_WINDOWS [200]. Migrate hardcoded window lists in moving_averages.py and volatility.py to use get_params()', status: completed}
- {id: window-ratio-features, content: 'Add cross-window ratio features to existing calculators: vol_compression_{short}_{long} (atr_5/atr_50), momentum_acceleration_{short}_{long} (roc_5/roc_20), oi_acceleration (oi_change_ma_8/oi_change_ma_48). These let GBT detect squeeze/acceleration without multi-step splits', status: completed}
- {id: multi-timeframe-stacking, content: 'Add multi-timeframe context stacking to features-delta-one-service: each model operating at timeframe T also receives higher-TF structural features (market_structure + momentum from 4h when running 1h model, etc.) as suffix-renamed columns (_4h, _1d)', status: completed}
- {id: cross-asset-features, content: 'Add CrossAssetFeatures calculator: BTC return context for all instruments (btc_return_1h/4h/1d, btc_vol_regime, btc_dominance_pct/roc), relative performance vs BTC (symbol_vs_btc_return, symbol_beta_vs_btc_50, rolling_correlation_btc_20/50), stablecoin_dominance_roc as risk-on signal', status: completed}
- {id: regime-conditional-models, content: 'Add regime-conditional model segmentation to ml-training-service: split training data by volatility_regime (low/normal/high) and train 3 specialist LightGBM models. Route inference based on current regime. Ensemble outputs with confidence weighting', status: completed}
- {id: trendline-calculator, content: 'Add trendline.py calculator: upper/lower trendline slopes at STRUCTURE_WINDOWS [10,20,30,50,100], channel_convergence (wedge detector), channel_width_pct, vol_compression (breakout proximity), price_position_in_channel, convergence_acceleration ratio', status: completed}
- {id: market-structure-sequence, content: 'Add market_structure_sequence.py extending market_structure.py: consecutive_lower_highs/higher_lows sequence counts, swing_high_compression (LH pattern), market_structure_bias score, bos_detected, choch_detected, decay-weighted level strength (swing_strength × exp(-λ × bars_since)) replacing raw time_since', status: completed}
- {id: fibonacci-calculator, content: 'Add fibonacci.py calculator derived from existing swing_high/swing_low: fib_0236/0382/0500/0618/0650/0750/0786 levels, distance_to_nearest_fib_pct, fib_confluence_score (count of round_number + POC + EMA systems agreeing at nearest Fib)', status: completed}
- {id: supply-demand-zones, content: 'Add supply_demand_zones.py calculator: order block detection (last opposing candle before impulse > 1.5×ATR), demand/supply zone proximity + strength + decay_score, at_demand_zone/at_supply_zone booleans, unmitigated zone counts', status: completed}
- {id: weekly-anchors, content: 'Add weekly_anchors.py calculator: price_vs_weekly_open_pct, price_vs_monday_high/low_pct, monday_range_width_pct, weekly_range_position, prev_week_high/low/close distances, monthly_range_position', status: completed}
- {id: liquidation-levels, content: 'Add liquidation_levels.py calculator using Coinglass heatmap API: long/short liquidation density at 1/3/5% distance bands, liq_gravity_ratio (directional magnet), next_liq_cluster_distance_pct, oi_leverage_estimate. DECISION: Coinglass is the primary source (Tardis check no longer required — proceed directly with Coinglass; API contract schemas already completed in unified-api-contracts). API key: coinglass-api-key in Secret Manager (via get_secret_client). GATE: unit tests with MagicMock(spec=LiquidationHeatmapResponse) pass; output columns match output_schemas.py; basedpyright strict passes.', status: completed}
- {id: level-confluence-score, content: 'Add level_confluence_score meta-feature aggregating: round_number + fib_level + volume_poc + demand_zone + sr_flip + weekly_anchor + liq_cluster signals into single weighted scalar per bar. DECISION: equal weights 1.0 for all components as starting point — weights tuned via SHAP after first training run (do not specify final weights in code; read from UnifiedCloudConfig or ConfigStore so they are tunable without redeploy). Formula: level_confluence_score = sum(component_i × weight_i) where weight_i defaults to 1.0. GATE: unit test verifies score increases monotonically as more components fire; basedpyright strict; no hardcoded weights in source.', status: completed}
- {id: sharpe-adjusted-targets, content: 'Add Sharpe-adjusted return targets to targets.py: sharpe_adjusted_return_{1,3,5} = return_n / realized_vol, magnitude_conditional = return × is_swing_breakout, return_percentile_5bar for learning-to-rank', status: completed}
isProject: false
---

# Citadel-Grade Feature Engineering Architecture

## Blockers

| Blocker                                                            | Type         | Specific Dependency                                                                                                                   | Resolution                                                                                                                                                                                                                                   |
| ------------------------------------------------------------------ | ------------ | ------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| unified-feature-calculator-library (UFC) not T2-hardened           | `[RESOLVED]` | [phase2_library_tier_hardening.md](phase2_library_tier_hardening.md) § todo `t2-code-rewrite`                                         | [RESOLVED] All 14 calculators authored and committed. Phase 2 T2 D5 quickmerge gate governs final merge to main, not code authorship — feature branch code is unblocked. Merge gate is the deployment constraint, not a development blocker. |
| features-delta-one-service and ml-training-service not T4-hardened | `[RESOLVED]` | [phase3_service_hardening_integration.md](phase3_service_hardening_integration.md) § todos `t4c-features-layer` and `t4d-ml-pipeline` | [RESOLVED] Changes authored and committed. Phase 3 T4C/T4D quickmerge D5 gate is the final merge gate to main; code authorship is complete and unblocked. Changes sit on feature branches pending T4C/T4D merge gate clearance.              |
| Coinglass API key not obtained (liquidation-levels todo)           | `[RESOLVED]` | [api_keys_and_auth.md](api_keys_and_auth.md) § todo `phase-3-coinglass` (added 2026-03-06)                                            | [RESOLVED 2026-03-06] — `phase-3-coinglass` todo added to api_keys_and_auth.md; Coinglass API key added to Phase 3 table. Unblocked.                                                                                                         |

---

## Done Criteria

This plan is complete when ALL of the following are true:

| Criterion                                                               | Gate                                                                    |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| All 14 todos status: completed                                          | Each todo has evidence comment                                          |
| Unit tests pass for every new calculator                                | `pytest tests/unit/ -v` exits 0, no skips                               |
| `ruff` clean                                                            | `ruff check <source_dir>/` exits 0                                      |
| `basedpyright` strict                                                   | `timeout 120 basedpyright <source_dir>/` exits 0, zero reportAny errors |
| MIN_COVERAGE ≥ 70%                                                      | `pytest --cov=<source_dir> --cov-fail-under=70` passes                  |
| No `_zscore`_, `_percentile_rank`_, `vol_percentile_` in output columns | `rg '_zscore_                                                           |
| No `os.getenv` / `os.environ` in production source                      | `rg 'osgetenv                                                           |
| No `Any` in public calculator API                                       | `rg ': Any                                                              |
| `level_confluence_score` weights in ConfigStore (not hardcoded)         | No float literals for weights in level_confluence_score source          |

---

## Core Insight

The trader in the image is doing **multi-dimensional context synthesis** — simultaneously reading structure (4h), entry
trigger (1h), confirmation (15m), plus BTC dominance, geopolitical backdrop, liquidation pressure, and round number
proximity. The model needs the same information, but the key is **not encoding his specific indicator choices — it's
giving the model a wide enough multi-resolution feature bank that LightGBM discovers which combinations predict the
swing outcome target**.

The existing pipeline is already designed for this: 15,000 raw features → SHAP/importance → 300-500 selected. The
architecture is correct. The problem is **scope starvation**: only 4 of 22 feature groups actually reach the model, and
zero cross-timeframe or cross-asset context exists.

---

## Critical Gaps Found

| Gap                                      | Impact                                                                                              | Effort                         |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------------ |
| 18 of 22 feature groups never fed to ML  | Massive — OI, liquidations, microstructure, candle patterns, volume profile all unused              | Low (just subscription change) |
| No multi-timeframe feature stacking      | Model has no structural context above its operating timeframe                                       | Medium                         |
| No cross-asset features                  | BTC dominance effect on alts, BTC/ETH correlation — all absent                                      | Medium                         |
| No regime-conditional model segmentation | One global model for trending + ranging + high-vol = diluted signal                                 | Medium                         |
| Windows inconsistent and sparse          | Model can't discover optimal lookback for each signal                                               | Low (parameter change)         |
| 6 missing calculator concepts            | Trendline geometry, fib levels, supply/demand zones, liq clusters, weekly anchors, cumulative delta | High                           |

---

## Part 1: Immediate Win — Feed All 22 Feature Groups to ML

**Current state** (ml-training-service feature subscriptions):

```python
# Only these 4 groups subscribed:
"technical_indicators", "market_structure", "returns", "targets"
```

**Change to** (all 22 groups):

```python
FEATURE_GROUPS_FOR_ML = [
    # Currently used
    "technical_indicators", "market_structure", "returns",
    # Newly added — all computed, none reaching model
    "moving_averages", "oscillators", "volatility_realized", "momentum",
    "volume_analysis", "vwap", "candlestick_patterns", "streaks",
    "round_numbers",                        # round number proximity already computed
    "microstructure",                       # VPIN, Amihud, funding spread
    "funding_oi",                           # OI, funding rate, basis
    "liquidations",                         # liq_intensity, liq_imbalance, large_liquidation
    "futures_basis",                        # basis, term structure
    "volume_flow",                          # directional volume flow
    # Calendar service
    "temporal", "economic_events",
    # Onchain service
    "stablecoin_dominance", "fear_greed", "macro_dxy", "yield_curve",
    "news_sentiment", "social_sentiment",
]
```

This alone is the **single highest-ROI change** — all that rich data is already computed and stored, just never seen by
the model.

---

## Part 2: Multi-Resolution Feature Banks

**The principle:** Every concept computed at 5-8 different window lengths. LightGBM's tree splits will find which
resolution is predictive for which setup. This is how you encode chart patterns without explicitly labeling them.

### 2a. Standardise Window Registry in `IndicatorParams`

Replace the current inconsistent mix of hardcoded + parameterized windows with a single canonical window set in
`parameters.py`:

```python
@dataclass
class IndicatorParams:
    # Canonical window families — all calculators draw from these
    MICRO_WINDOWS: list[int] = field(default_factory=lambda: [2, 3, 5])
    SHORT_WINDOWS: list[int] = field(default_factory=lambda: [8, 12, 20])
    MEDIUM_WINDOWS: list[int] = field(default_factory=lambda: [30, 50, 100])
    LONG_WINDOWS: list[int] = field(default_factory=lambda: [200])
    ALL_WINDOWS: list[int] = field(default_factory=lambda: [2, 3, 5, 8, 12, 20, 30, 50, 100, 200])

    # Specific families for existing calculators — migrate hardcoded values here
    SMA_PERIODS: list[int] = field(default_factory=lambda: [5, 10, 20, 50, 100, 200])
    VOLATILITY_WINDOWS: list[int] = field(default_factory=lambda: [5, 7, 14, 20, 28, 50])
    MOMENTUM_WINDOWS: list[int] = field(default_factory=lambda: [3, 5, 8, 10, 14, 20, 28])
    STRUCTURE_WINDOWS: list[int] = field(default_factory=lambda: [10, 20, 30, 50, 100])
```

### 2b. Window Ratios as Features (Fast/Slow Cross-Timeframe Within Single Timeframe)

For every indicator, add **ratio features** between short and long windows:

```python
# Example: momentum ratio features (currently missing)
momentum_5_vs_20  = roc_5 / (roc_20 + eps)   # momentum acceleration
momentum_8_vs_50  = roc_8 / (roc_50 + eps)   # short vs medium term alignment
vol_5_vs_50       = atr_5 / (atr_50 + eps)   # vol compression ratio — pre-breakout detector
ma_20_vs_200      = close / ema_20 - close / ema_200  # already in moving_averages? extend to all window pairs

# Why this works for GBTs:
# GBT can learn: momentum_5_vs_20 > 2.0 = momentum acceleration (short-term spike)
# It can NOT learn this from raw roc_5=0.03, roc_20=0.015 without many splits
```

The key ratio families to add:

- `vol_compression_{short}_{long}` = `atr_{short} / atr_{long}` (5/50, 8/100) — Bollinger squeeze proxy
- `momentum_acceleration_{short}_{long}` = `roc_{short} / roc_{long}` (5/20, 8/50)
- `structure_compression_{short}_{long}` = `channel_width_{short} / channel_width_{long}` (new calculator)
- `oi_acceleration_{short}_{long}` = `oi_change_ma_{short} / oi_change_ma_{long}` (8/48)

---

## Part 3: Multi-Timeframe Feature Stacking

**Current:** One model per timeframe — 4h model sees only 4h features.

**Target:** Each model also receives **higher-timeframe structural features** as context columns.

```
Model on 4h timeframe receives:
├── 4h features (all 22 groups) — entry-level signal
├── 1d features (structure group only) — directional bias
└── 1w features (structure + moving_averages only) — macro regime

Model on 1h timeframe receives:
├── 1h features (all groups) — entry-level signal
├── 4h features (market_structure, momentum, volatility) — medium-term context
└── 1d features (market_structure, moving_averages) — trend context
```

**Implementation in `features-delta-one-service`**: Each calculator accepts a `timeframe` parameter already. Add a
`context_timeframes` config that lists which higher-TF feature groups to pull and suffix-rename (`_4h`, `_1d`, `_1w`).

This directly encodes: "Is the 1h signal aligned with the 4h structure?" — the core of what the telegram trader is doing
manually.

---

## Part 4: Cross-Asset Feature Matrix

**Currently:** Zero cross-asset features. All calculators operate on single-symbol DataFrames.

**Add to `features-delta-one-service`** as a new `CrossAssetFeatures` calculator:

```python
# BTC as market benchmark (for ALL crypto instruments)
btc_return_1h, btc_return_4h, btc_return_1d         # absolute BTC returns
btc_vol_regime                                         # BTC vol state (from volatility calc)
btc_dominance_pct, btc_dominance_roc_1d              # BTC.D from onchain service
btc_momentum_alignment                                 # sign(roc_5_btc) == sign(roc_20_btc)

# Relative performance (for altcoin instruments)
symbol_vs_btc_return_1h = instrument_return_1h - btc_return_1h   # beta-adjusted alpha
symbol_vs_btc_return_4h
symbol_correlation_btc_20                             # rolling 20-bar correlation with BTC
symbol_correlation_btc_50
symbol_beta_vs_btc_50                                 # slope of symbol~BTC regression

# ETH/BTC ratio for ETH positions
eth_btc_ratio_momentum                                # is ETH outperforming BTC?

# Stablecoin dominance as risk-on/off signal
stablecoin_dominance_roc_1d                           # from onchain service (already computed)
```

**Why this matters for 50-100% annual returns:** The single strongest signal in crypto is "BTC moves, do alts follow?"
The model currently has zero context for this.

---

## Part 5: Regime-Conditional Model Architecture

**Currently:** One global LightGBM model. Regime features computed but ignored for segmentation.

**Target:** 3-regime specialist ensemble (no new training infra needed — just segment the training set):

```
Regime detection (from existing volatility.py):
├── LOW_VOL regime (vol_regime_low=1)
│   └── LightGBM specialist: mean-reversion patterns dominate
│       Key features: S/R distances, RSI extremes, volume_regime, fib levels
│
├── NORMAL regime (vol_regime_normal=1)
│   └── LightGBM specialist: trend-following patterns dominate
│       Key features: momentum ratios, trendline slopes, MA alignment
│
└── HIGH_VOL regime (vol_regime_high=1)
    └── LightGBM specialist: liquidation cascade + recovery patterns
        Key features: liq_intensity, funding_extreme, oi_acceleration, round number proximity
```

**Implementation:** In `ml-training-service`, split training data by `volatility_regime` label before fitting. At
inference, route to specialist model. Ensemble their outputs (weighted average or confidence-gated).

This is standard at quant funds — regime segmentation typically doubles Sharpe on classification models.

---

## Part 6: Six New Calculators (True Feature Gaps)

These are concepts that currently have zero representation, ordered by leverage on the swing prediction target:

### 6a. `trendline.py` — Channel/Wedge Geometry

GBTs cannot "see" a falling wedge from raw OHLCV. These features encode the geometry as scalars:

```python
# Per window in STRUCTURE_WINDOWS = [10, 20, 30, 50, 100]:
upper_slope_{w}          # OLS slope on swing highs / ATR (normalized, negative = falling)
lower_slope_{w}          # OLS slope on swing lows / ATR
channel_convergence_{w}  # upper_slope - lower_slope: <0 = wedge, ~0 = parallel, >0 = expanding
channel_width_pct_{w}    # (upper_trendline - lower_trendline) / close
vol_compression_{w}      # atr_5 / atr_{w} — short vol vs channel-period vol (breakout proximity)
price_position_in_channel_{w}  # 0=at lower trendline, 1=at upper trendline
channel_breakout_{w}     # bool: last close outside channel
trendline_touch_upper_{w}  # count of touches of upper trendline in window
trendline_touch_lower_{w}  # count of touches of lower trendline in window
# Ratio features (cross-window):
convergence_acceleration = channel_convergence_10 / channel_convergence_50  # speeding up?
```

GBT discovers: `convergence_20 < -0.4 AND price_position_20 > 0.85 AND vol_compression_5_50 < 0.7` = top of falling
wedge with vol squeeze → short signal.

### 6b. `market_structure_sequence.py` — HH/HL/LH/LL Encoding

Extends existing `market_structure.py` with sequence features:

```python
# Per window in STRUCTURE_WINDOWS:
consecutive_lower_highs_{w}   # int: count of successive lower swing highs
consecutive_higher_lows_{w}   # int: count of successive higher swing lows
swing_high_compression_{w}    # average (HH_n - HH_n-1) / ATR over window (negative = LH pattern)
swing_low_expansion_{w}       # average (LL_n - LL_n-1) / ATR (negative = LL pattern)
market_structure_bias_{w}     # -1 to +1: weighted (LH_count - HH_count) / total_swings
# Break of Structure / Change of Character
bos_detected                  # bool: close broke last swing high (in downtrend) or low (in uptrend)
choch_detected                # bool: first swing in opposite direction after BOS
bos_age_bars                  # bars since last BOS
# Decay-weighted level strength (replaces raw time_since)
swing_high_decay_fast         # swing_strength × exp(-0.1 × bars_since_high)
swing_high_decay_slow         # swing_strength × exp(-0.02 × bars_since_high)
swing_low_decay_fast
swing_low_decay_slow
```

### 6c. `fibonacci.py` — Fib Retracement Levels

Derived from existing swing_high/swing_low (no new data):

```python
# Fib levels from last major swing (using TIME_SINCE_LOOKBACK window):
fib_0236_level, fib_0382_level, fib_0500_level
fib_0618_level, fib_0650_level, fib_0750_level, fib_0786_level

# Distance features (scale-invariant):
distance_to_fib_0382_pct      # (close - fib_level) / close
distance_to_fib_0618_pct
distance_to_fib_0750_pct
nearest_fib_level             # which Fib is closest
nearest_fib_distance_pct      # distance to nearest Fib / ATR

# Confluence detection:
fib_round_confluence          # bool: nearest Fib within 0.3% of nearest round number
fib_poc_confluence            # bool: nearest Fib within 0.3% of volume POC
fib_ema_confluence_{period}   # bool: nearest Fib within 0.3% of EMA_{period}
fib_confluence_score          # count of above confluences at nearest Fib
```

### 6d. `supply_demand_zones.py` — Institutional Order Block Detection

```python
# Demand zones (last bearish candle before bullish impulse > 1.5× ATR):
nearest_demand_top_pct        # (close - demand_zone_top) / close
nearest_demand_bottom_pct
demand_zone_strength          # (impulse_size following zone) / ATR at formation
demand_zone_age_bars          # bars since zone formed (older = weaker)
demand_zone_decay_score       # strength × exp(-λ × age_bars)
at_demand_zone                # bool: close is inside nearest demand zone
demand_zone_retest_count      # how many times zone has been retested
unmitigated_demand_zones_below  # count of untested demand zones in next 5% down

# Supply zones (symmetric):
nearest_supply_top_pct
nearest_supply_bottom_pct
supply_zone_strength
at_supply_zone
unmitigated_supply_zones_above
```

### 6e. `weekly_anchors.py` — Calendar-Anchored Price Levels

```python
# Weekly Open and Monday Range (the most-cited levels in telegram alpha):
price_vs_weekly_open_pct      # (close - weekly_open) / close
price_vs_monday_high_pct      # (close - monday_high) / close
price_vs_monday_low_pct
above_weekly_open             # bool
monday_range_width_pct        # (monday_high - monday_low) / monday_open
weekly_range_position         # 0=weekly_low, 1=weekly_high (normalized position)

# Previous week levels:
price_vs_prev_week_high_pct
price_vs_prev_week_low_pct
price_vs_prev_week_close_pct  # = this week's open
prev_week_range_pct           # (prev_high - prev_low) / prev_close

# Monthly anchors:
price_vs_monthly_open_pct
monthly_range_position        # normalized position in current month's range
```

### 6f. `liquidation_levels.py` — OI-Weighted Liquidation Cluster Features

```python
# Distance to liquidation clusters by price level (Coinglass heatmap):
long_liq_density_1pct         # estimated $ longs that liquidate within 1% below current
long_liq_density_3pct         # within 3%
long_liq_density_5pct
short_liq_density_1pct_above  # within 1% above
short_liq_density_3pct_above
short_liq_density_5pct_above

# Derived signals:
liq_gravity_ratio             # long_liq_5pct / short_liq_5pct — directional magnet
liq_gravity_direction         # -1=magnet below, +1=magnet above
next_liq_cluster_distance_pct # distance to nearest significant cluster
oi_leverage_estimate          # OI / market_cap proxy — overall market leverage
```

**Data source:** Coinglass liquidation heatmap API (check Tardis coverage first).

---

## Part 7: Level Confluence Score (The Meta-Feature)

After all calculators are built, add a single aggregated meta-feature computed across all level systems:

```python
level_confluence_score = weighted_sum([
    near_round_number     × w_round,       # already computed
    fib_confluence_score  × w_fib,         # new
    poc_proximity_inv     × w_poc,         # already computed
    at_demand_zone        × w_zone,        # new
    sr_flip_active        × w_flip,        # new (from market_structure_sequence)
    at_weekly_anchor      × w_anchor,      # new
    liq_cluster_magnet    × w_liq,         # new
])
```

This single feature answers: "How many independent systems agree this price level matters?" — likely among the top 10
SHAP features for the swing reversal target.

---

## Part 8: Target Engineering for 50-100% Annual Returns

**Current target:** Binary breakout/reversion classification (direction only).

**Add Sharpe-adjusted return targets:**

```python
# In targets.py — add alongside existing targets:
sharpe_adjusted_return_1  = return_1bar / realized_vol_5    # quality-weighted 1-bar return
sharpe_adjusted_return_3  = return_3bar / realized_vol_5
sharpe_adjusted_return_5  = return_5bar / realized_vol_10
magnitude_conditional     = return_next_n × is_swing_breakout  # only when swing fires
# Ranking target (for learning-to-rank):
return_percentile_5bar    # where does this bar's outcome rank vs recent distribution
```

**Why:** Predicting direction is necessary but not sufficient for 50-100% annual. The model also needs to learn when
**magnitude** is expected to be large (vs. small noise moves). Sharpe-adjusted targets teach the model to distinguish
high-conviction from marginal setups.

---

## Coding Standards Note

File size limit: MAX_FILE_LINES=900 (split by SRP; warn at 700 lines) — applies to all files.

---

## Architecture Summary

```
Data Sources
├── Market OHLCV + OI + Funding + Liquidations
├── Onchain (BTC.D, stablecoin dominance, fear/greed)
├── Calendar (economic events, temporal)
└── [NEW] Coinglass liq heatmap, CME futures

features-delta-one-service (all 22 + 6 new calculators)
│
├── Per-instrument features at 4h, 1h, 15m
├── [NEW] Multi-timeframe stacking (higher-TF context columns)
├── [NEW] Cross-asset features (BTC as benchmark)
└── [NEW] Level confluence score (meta-feature)
     ↓
ml-training-service
├── [FIX] Subscribe to all 22 feature groups (not just 4)
├── [NEW] Regime-conditional model segmentation
│   ├── LOW_VOL specialist LightGBM
│   ├── NORMAL specialist LightGBM
│   └── HIGH_VOL specialist LightGBM
├── [NEW] Sharpe-adjusted return targets alongside direction targets
├── Walk-forward CV with embargo (already correct)
└── SHAP selection: 15K raw → 300-500 per regime model
```

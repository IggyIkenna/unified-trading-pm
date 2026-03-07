---
id: strategy_expansion_five_themes
title: "Strategy Expansion: Five Trading Themes"
status: completed
created: 2026-03-06
phase: implementation
priority: high
---

## Overview

Integrated 5 trading themes into UTS without new repos: relative vol, stat arb, vol/options (normalized strikes),
prediction market arb (Polymarket), cross-exchange arb. All themes share the existing feature -> signal -> execution
pipeline via config-driven modes.

## Completion Status

### Phase 1: Schema Foundation (DONE)

- [x] `CanonicalSpread` + `SpreadLeg` in UAC spread.py
- [x] `NormalizedStrikeCoordinate` + `OptionChainSnapshot` in UAC options.py
- [x] `PairSpreadFeatureRecord` in UIC features.py
- [x] `vol_of_vol_20/60` added to DeltaOneFeatureRecord (UIC)
- [x] `relative_vol_ratio/zscore`, `fee_adjusted_spread_bps/zscore`, `crowd_sentiment_*` added to
      CrossInstrumentFeatures (UIC)
- [x] `TargetType.CROSS_VENUE_SPREAD` added to UIC ml.py

### Phase 2: Feature Services (DONE)

- [x] `features-delta-one-service`: vol_of_vol_20/60 computation
- [x] `features-cross-instrument-service`: CointegrationCalculator (Johansen + OU half-life)
- [x] `features-cross-instrument-service`: PolymarketCrowdSentimentCalculator
- [x] `features-cross-instrument-service`: relative_vol_ratio/zscore, fee_adjusted_spread features
- [x] `features-volatility-service`: full vol surface term structure (7d/30d/60d/90d/180d ATM IV, delta pillars)

### Phase 3: Execution Layer (DONE)

- [x] `execution-service`: StrikeMapper (delta -> real strike)
- [x] `execution-service`: execute_concurrent_legs() async primitive
- [x] `execution-service`: check_multi_venue_balance() pre-trade check

### Phase 4: Strategy Modes (DONE)

- [x] `strategy-service`: rel_vol strategy + config YAML
- [x] `strategy-service`: stat_arb strategy + config YAML
- [x] `strategy-service`: vol_surface strategy + config YAML
- [x] `strategy-service`: cross_exchange strategy + config YAML
- [x] `strategy-service`: prediction_arb config YAML

### Phase 5: Prediction Market Adapter (DONE)

- [x] `unified-sports-execution-interface`: prediction_markets/polymarket.py
- [x] Polymarket normalizers and arb detection
- [x] Kalshi stub

### Phase 6: ML Training (DONE)

- [x] `ml-training-service`: CROSS_VENUE_SPREAD target computation
- [x] Feature selector for cross-venue spread model

## Missing Before Live Trading

| Item                                      | Owner       | Status  |
| ----------------------------------------- | ----------- | ------- |
| Polymarket API keys -> Secret Manager     | DevOps      | Pending |
| Polymarket USDC.e wallet on Polygon       | Trading ops | Pending |
| Deribit options VCR cassettes             | Engineering | Pending |
| Live Deribit options chain WebSocket feed | Engineering | Pending |
| Cross-venue pre-funded balances           | Trading ops | Pending |

## Key Architecture Decisions

1. **No new repos**: All 5 themes are implemented within existing repos via config modes
2. **Polymarket via NautilusTrader**: NautilusTrader already has a native Polymarket adapter; we add config +
   normalizers only
3. **Cross-exchange arb is ML-driven**: Pure spatial arb is impractical (500ms latency); we train LightGBM on
   CROSS_VENUE_SPREAD labels instead
4. **Normalized strikes**: Features/ML use delta coordinates; StrikeMapper resolves to real strikes at execution time
   only
5. **USEI extended**: Prediction market adapter lives in USEI prediction_markets/ subdir, not a new repo

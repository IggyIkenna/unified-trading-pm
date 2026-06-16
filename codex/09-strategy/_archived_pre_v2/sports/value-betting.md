---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# Sports Value Betting

> **Asset class:** Sports **Strategy type:** Value Betting **Strategy ID pattern:** `SPORTS_VALUE_BETTING`

## Overview

Identifies mispriced odds across bookmakers where the ML model's estimated true probability of an outcome exceeds the
bookmaker's implied probability by a configurable threshold (min_value_edge). A value bet exists when
`model_probability - implied_probability > min_value_edge`, meaning the market is offering better odds than the model
expects. The strategy scans all available bookmaker odds per event outcome, selects the best price, and emits a signal
when positive expected value is confirmed. Position sizing uses a proportional edge-based approach with an optional
Kelly criterion integration for bankroll-optimal growth.

## Token / Position Flow

```
Start:  BANKROLL:FIAT:GBP  (100% bankroll)

Step 1 - MODEL PROB: Receive ML model probabilities per outcome from features-sports-service
         via UEI event bus (PredictionEvent). e.g. home=0.58, draw=0.24, away=0.18
Step 2 - CONFIDENCE GATE: Discard outcomes where model_prob < model_confidence_threshold (default 0.55)
Step 3 - BEST ODDS: For each remaining outcome, find best decimal odds across all connected bookmakers
Step 4 - ODDS GATE: Reject extreme longshots where decimal_odds > max_odds (default 10.0)
Step 5 - EDGE CHECK: edge = model_prob - implied_prob; skip if edge < min_value_edge (default 3%)
Step 6 - STAKE SIZING: raw_stake = edge * 2, clamped to max_stake_fraction (default 5% of bankroll)
Step 7 - EMIT: SportsSignalDict with stake_fraction, edge, confidence, model metadata

Wallet after deploy:
  - Open bets sized proportional to edge magnitude
  - Max single bet = 5% of bankroll (max_stake_fraction)
  - Typical bet = 2-4% of bankroll for edges in the 3-8% range
  - No leverage; total exposure bounded by concurrent bet count * max_stake_fraction
```

## Instruments

| Instrument Key               | Venue      | Type     | Role                              |
| ---------------------------- | ---------- | -------- | --------------------------------- |
| `SPORTS:VALUE:MODEL_EDGE`    | Multiple   | Bet      | Value bets identified by ML model |
| Event outcomes (h2h, totals) | Betfair    | Exchange | Best odds source + lay hedge      |
| Event outcomes (h2h, totals) | Smarkets   | Exchange | Best odds source                  |
| Event outcomes (h2h, totals) | Matchbook  | Exchange | Best odds source                  |
| Event outcomes (h2h, totals) | Betdaq     | Exchange | Best odds source                  |
| Event outcomes (h2h, totals) | Polymarket | PM       | Prediction market odds source     |
| Event outcomes (h2h, totals) | Kalshi     | PM       | Prediction market odds source     |

## Key Features Consumed

| Feature                 | Source Service          | SLA | Used For                                            |
| ----------------------- | ----------------------- | --- | --------------------------------------------------- |
| `model_probabilities`   | features-sports-service | 5m  | ML-estimated true probability per outcome           |
| `prediction_confidence` | features-sports-service | 5m  | Model confidence score for gating low-quality preds |
| `odds` (per-bookmaker)  | market-tick-data-svc    | <1s | Implied probability and best odds lookup            |
| `team_form_features`    | features-sports-service | 1h  | Input to ML model: recent match results, xG         |
| `h2h_history`           | features-sports-service | 24h | Input to ML model: head-to-head record              |
| `market_movement`       | market-tick-data-svc    | <1s | Odds drift detection for timing alpha               |
| `line_opening_odds`     | market-tick-data-svc    | 24h | Closing line value (CLV) attribution                |

## PnL Attribution

| Component        | Settlement Type | Mechanism                                                          |
| ---------------- | --------------- | ------------------------------------------------------------------ |
| `edge_capture`   | EVENT_SETTLE    | Win: stake \* (odds - 1); Lose: -stake. Net positive if edge real. |
| `odds_movement`  | ATTRIBUTION     | Closing line value: did odds shorten after placement?              |
| `timing_alpha`   | ATTRIBUTION     | Return from placing before odds adjust to true probability         |
| `model_accuracy` | ATTRIBUTION     | Decomposition of edge into model skill vs market inefficiency      |

**Source of truth:** `total_pnl = bankroll_current - bankroll_initial`. Edge capture is the primary PnL driver: over a
large sample of bets, if the model's probability estimates are well-calibrated, the strategy earns
`sum(edge_i * stake_i)` in expectation. Closing line value (CLV) — the difference between placement odds and closing
odds — is the leading indicator of long-term profitability. All attribution components must sum to total_pnl within 2%
annualized tolerance.

## Risk Profile

| Metric               | Target  | Notes                                                           |
| -------------------- | ------- | --------------------------------------------------------------- |
| Target annual return | 8-25%   | Depends on model accuracy and bet volume (500+ bets/month)      |
| Target Sharpe ratio  | 0.8-1.5 | Lower than arb due to outcome variance; improves with volume    |
| Max drawdown         | 25%     | Expected with edge-based betting; reduced by max_stake_fraction |
| Max leverage         | 1x      | No leverage; all bets from bankroll                             |
| Capital scalability  | $200K   | Limited by bookmaker stake limits and account restricting       |

## Latency Profile

| Segment               | p50 Target | p99 Target | Co-location Needed? |
| --------------------- | ---------- | ---------- | ------------------- |
| Market data → feature | 200ms      | 1000ms     |                     |
| Feature → signal      | 10ms       | 50ms       |                     |
| Signal → instruction  | 15ms       | 80ms       |                     |
| Instruction → fill    | 300ms      | 2000ms     |                     |
| **End-to-end**        | **525ms**  | **3130ms** | **No**              |

## Execution Details

- **Venues:** Betfair, Smarkets, Matchbook, Betdaq, Polymarket, Kalshi (best odds per outcome selected at signal time)
- **Order types:** Market (bookmakers), Limit (exchanges — Betfair, Smarkets)
- **Atomic execution required?** No — each value bet is independent; partial execution is acceptable
- **Rebalancing:** Per-event; no carry between events. Model probabilities refresh pre-match and at configurable
  intervals for live markets.
- **Gas budget:** N/A for fiat venues. For Polymarket/Kalshi: ~$0.50-$2.00 per bet (Polygon/Ethereum L2 gas).

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions → exposures) → RiskMonitor (exposures → risk assessment) → Strategy (risk
assessment → rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern      | Exposure Type       | Used For                                            |
| ----------------------- | ------------------- | --------------------------------------------------- |
| `SPORTS:VALUE:*`        | Stake committed     | Track total bankroll at risk across open bets       |
| Open bets per event     | Potential payout    | Monitor max single-event exposure                   |
| Open bets per bookmaker | Venue concentration | Ensure no single venue holds >30% of total exposure |

**SSOT:** `component_config.exposure_monitor.instrument_subscriptions` in strategy config. Schema:
[`ExposureMonitorConfig`](../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold              | Action on Breach                          |
| --------------- | ----------- | ---------------------- | ----------------------------------------- |
| `delta`         | No          | —                      | —                                         |
| `funding`       | No          | —                      | —                                         |
| `basis`         | No          | —                      | —                                         |
| `protocol_risk` | No          | —                      | —                                         |
| `liquidity`     | Yes         | venue_max_bet          | Cap stake to venue limit                  |
| `exposure`      | Yes         | 40% bankroll committed | Pause new signals until bets settle       |
| `model_drift`   | Yes         | Brier score > 0.25     | Halt betting, trigger model recalibration |

**SSOT:** `component_config.risk_monitor.enabled_risk_types` in strategy config. Schema:
[`RiskMonitorConfig`](../../strategy-service/strategy_service/config.py) Formal subscription type:
[`StrategyRiskProfile`](../../unified-api-contracts/unified_api_contracts/internal/risk.py)

**Gap:** `StrategyRiskProfile` exists in `unified_api_contracts.internal` but is NOT yet wired into strategy-service
config. Risk subscriptions are currently implicit in code (per-strategy TypedDict defaults), not in a machine-readable
registry. Plan item `p5-risk-strategy-subscription` in `uac_errors_package_cleanup` will create a YAML-based
subscription registry.

### Custom Strategy Risk Types

| Custom Risk             | What It Measures                              | Evaluation Method                  | SSOT            |
| ----------------------- | --------------------------------------------- | ---------------------------------- | --------------- |
| Model calibration drift | Predicted vs actual outcome frequency         | Rolling 200-bet Brier score        | ml-service      |
| CLV regression          | Closing line value trending negative          | 50-bet rolling average CLV         | strategy config |
| Venue stake acceptance  | Bookmaker reducing accepted stakes over time  | Fill rate and accepted size trends | execution svc   |
| Correlation exposure    | Multiple bets on same match or league cluster | Event/league grouping analysis     | strategy config |

**Gap:** Custom risk types are planned (plan item `p5-risk-custom-risk-types`) but not yet implemented. Currently no
machine-readable custom risk definitions exist.

## Margin & Liquidation

- **Margin model:** None (pre-funded accounts at each bookmaker/exchange)
- **Health factor threshold:** N/A
- **Liquidation penalty:** N/A
- **Monitoring:** Bankroll tracked per venue. If any single venue's balance drops below 10% of allocated capital, the
  strategy pauses betting on that venue until manual rebalance or deposit. Total bankroll is reconciled daily against
  sum of venue balances plus settled but unswept profits.

## Authentication & Credentials

Links to SSOT — do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue      | Secret Name              | Testnet Available? | Notes                        |
| ---------- | ------------------------ | ------------------ | ---------------------------- |
| Betfair    | exec-{client}-betfair    | No                 | Exchange API + SSL certs     |
| Smarkets   | exec-{client}-smarkets   | No                 | REST API key                 |
| Matchbook  | exec-{client}-matchbook  | No                 | REST API key                 |
| Betdaq     | exec-{client}-betdaq     | No                 | REST API key                 |
| Polymarket | exec-{client}-polymarket | Yes (Mumbai)       | Wallet private key + RPC URL |
| Kalshi     | exec-{client}-kalshi     | Yes (demo)         | API key + member ID          |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Funded accounts at target bookmakers/exchanges. For Polymarket/Kalshi, a funded wallet or
   account with sufficient margin.
2. **Secret Manager:** Per-client secrets: `exec-{client}-{venue}-{account_type}` for each venue
3. **Config:** New `ValueBettingConfigDict` entry with client-specific `min_value_edge`, `max_odds`,
   `model_confidence_threshold`, and `max_stake_fraction`
4. **Position isolation:** One strategy instance per client (independent bankroll tracking; different venues may have
   different balance/limit profiles)
5. **Restart required?** No — hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service           | What Changes                        | Restart?        |
| ----------------- | ----------------------------------- | --------------- |
| strategy-service  | New ValueBettingConfigDict in GCS   | No (hot-reload) |
| execution-service | New client venue routing rules      | No (hot-reload) |
| ml-service        | Client may use custom model variant | No (hot-reload) |

## UI Visualisation

### Standard views (already in plans)

- PnL waterfall (risk matrix plan Stream D)
- Margin health time series (Stream D)
- Position breakdown

### Strategy-specific views (extensions)

- Edge distribution chart: histogram of edge values at bet placement across all bets
- Model probability vs implied probability scatter plot with 45-degree break-even line
- Closing line value (CLV) time series: rolling 50-bet average CLV as profitability predictor
- Bankroll equity curve: actual vs Kelly-optimal theoretical growth
- Venue acceptance rate tracker: accepted stake / requested stake per venue over time
- Model calibration reliability diagram: predicted probability vs observed frequency (binned)
- Bet outcome heatmap by sport, league, and market type

## Testing Stage Status

| Stage        | Status  | Notes                                                     |
| ------------ | ------- | --------------------------------------------------------- |
| MOCK         | Done    | Static model probs + odds fixtures; verified edge calc    |
| HISTORICAL   | Done    | 12-month football backtest with historical model probs    |
| LIVE_MOCK    | Done    | Real odds + ML model probs + paper execution              |
| LIVE_TESTNET | N/A     | No testnet for sports bookmakers (Polymarket Mumbai only) |
| BATCH_REAL   | Pending | Historical replay with optimized thresholds               |
| STAGING      | Pending | Paper execution with real ML predictions + real odds      |
| LIVE_REAL    | Pending | Production with real bookmaker accounts                   |

## References

- **Strategy implementation:** `strategy-service/strategy_service/engine/strategies/sports/value_betting.py`
- **ML integration:** `strategy-service/strategy_service/engine/strategies/sports/ml_sports_strategy.py`
- **Kelly sizing (shared):** `strategy-service/strategy_service/engine/strategies/sports/kelly.py`
- **Base class:** `strategy-service/strategy_service/engine/strategies/sports/sports_base.py`
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`
- **Features pipeline:** `features-sports-service/`

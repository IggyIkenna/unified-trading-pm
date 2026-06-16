---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# Prediction Market Arbitrage

> **Asset class:** Cross-Asset (Prediction Markets) **Strategy type:** Arbitrage **Strategy ID pattern:**
> `QUANT_PREDICTION_ARB_BTC`

## Overview

Cross-venue arbitrage strategy for binary prediction markets (Polymarket, Kalshi, Betfair). Detects price discrepancies
where the same event trades at materially different implied probabilities across venues, allowing both YES and NO
outcomes to be purchased for a combined cost below 1.0. Uses `CanonicalPredictionMarket` from the prediction mapping
module for venue-agnostic normalization of market data across Polymarket (CLOB), Kalshi (order book), and Betfair
(exchange). Categories auto-classified via keyword heuristics (politics, sports, crypto, economics, entertainment,
science).

## Token / Position Flow

```
Start:  WALLET:USDC  (100% USDC)

Step 1 - NORMALIZE: Convert venue-specific formats to CanonicalPredictionMarket
         (Polymarket: condition_id + tokens; Kalshi: ticker + yes_ask/no_ask)
Step 2 - QUOTE: Build VenueQuote per venue (yes_price, no_price in [0,1])
Step 3 - PAIR SCAN: For each pair of venues (A, B), check:
         YES_A + NO_B < 1.0 - min_edge_pct/100 (default 2%)
         NO_A + YES_B < 1.0 - min_edge_pct/100
Step 4 - BEST PAIR: Select the pair with highest edge_pct
Step 5 - EMIT: PredictionArbSignal with 2 legs, edge_pct, max_position_usdc

Wallet after deploy:
  - Leg 1: YES on venue A = implied_prob_A * position_usdc
  - Leg 2: NO on venue B = implied_prob_B * position_usdc
  - Combined cost < 1.0 per unit -> guaranteed profit at resolution
  - Max position = $1,000 USDC (configurable)
```

## Instruments

| Instrument Key              | Venue      | Type       | Role            |
| --------------------------- | ---------- | ---------- | --------------- |
| `polymarket:{condition_id}` | Polymarket | Binary YES | Arb leg         |
| `kalshi:{ticker}`           | Kalshi     | Binary YES | Arb leg         |
| Betfair event market        | Betfair    | Binary     | Arb leg         |
| `WALLET:USDC`               | Wallet     | Stablecoin | Initial capital |

## Key Features Consumed

| Feature                     | Source Service            | SLA | Used For                        |
| --------------------------- | ------------------------- | --- | ------------------------------- |
| `crowd_sentiment_prob`      | features-cross-instrument | 10s | Implied prob from Polymarket    |
| `crowd_sentiment_market_id` | features-cross-instrument | 10s | Polymarket market ID for lookup |
| Venue order books / quotes  | market-tick-data-svc      | <5s | YES/NO prices per venue         |

## PnL Attribution

| Component    | Settlement Type | Mechanism                                              |
| ------------ | --------------- | ------------------------------------------------------ |
| `arb_profit` | EVENT_RESOLVE   | 1.0 payout - combined_cost per unit; guaranteed        |
| `venue_fees` | PER_FILL        | Trading fees per venue (Polymarket ~0%, Kalshi ~5-10%) |

**Source of truth:** `total_pnl = resolution_payout - total_cost`. Prediction market arbs resolve to exactly 1.0 (one
side wins); profit = 1.0 - sum(leg costs). Edge must exceed venue fees.

## Risk Profile

| Metric               | Target | Notes                                               |
| -------------------- | ------ | --------------------------------------------------- |
| Target annual return | 10-25% | Depends on arb frequency and market inefficiency    |
| Target Sharpe ratio  | >3.0   | Near-riskless if both legs filled                   |
| Max drawdown         | <2%    | Only from failed execution (partial fills)          |
| Max leverage         | 1x     | No leverage; USDC-funded                            |
| Capital scalability  | $50K   | Limited by prediction market liquidity (thin books) |

## Latency Profile

| Segment                | p50 Target | p99 Target | Co-location Needed? |
| ---------------------- | ---------- | ---------- | ------------------- |
| Market data -> feature | 500ms      | 2000ms     |                     |
| Feature -> signal      | 10ms       | 50ms       |                     |
| Signal -> instruction  | 10ms       | 50ms       |                     |
| Instruction -> fill    | 1000ms     | 5000ms     |                     |
| **End-to-end**         | **1520ms** | **7100ms** | **No**              |

## Execution Details

- **Venues:** Polymarket (CLOB on Polygon), Kalshi (CFTC-regulated order book), Betfair (exchange)
- **Order types:** Limit (to control fill price on thin order books)
- **Atomic execution required?** Yes -- both legs must be filled; partial fill creates directional exposure to event
  outcome
- **Rebalancing:** Per-market; positions held until event resolution
- **Gas budget:** Polymarket: ~0.001 MATIC per trade (Polygon L2); Kalshi/Betfair: N/A (off-chain)

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern  | Exposure Type  | Used For                     |
| ------------------- | -------------- | ---------------------------- |
| YES legs            | USDC committed | Track total capital deployed |
| NO legs             | USDC committed | Track total capital deployed |
| Per-venue positions | Position count | Venue diversification        |

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold         | Action on Breach          |
| --------------- | ----------- | ----------------- | ------------------------- |
| `delta`         | No          | --                | --                        |
| `funding`       | No          | --                | --                        |
| `basis`         | No          | --                | --                        |
| `protocol_risk` | Yes         | Venue downtime    | Skip venue in pair scan   |
| `liquidity`     | Yes         | Size > order book | Reduce position_usdc      |
| `execution`     | Yes         | Partial fill      | Hedge with opposite venue |

### Custom Strategy Risk Types

| Custom Risk            | What It Measures                        | Evaluation Method   | SSOT            |
| ---------------------- | --------------------------------------- | ------------------- | --------------- |
| Resolution risk        | Market resolves ambiguously (N/A)       | Resolution source   | venue metadata  |
| Counterparty risk      | Venue insolvency or withdrawal freeze   | Venue health check  | ops monitoring  |
| Cross-chain settlement | Polymarket on Polygon; funds on mainnet | Bridge latency      | execution svc   |
| Fee asymmetry          | Different fee structures across venues  | Fee schedule lookup | strategy config |

## Margin & Liquidation

- **Margin model:** None (fully collateralized binary positions; cost = price in [0,1])
- **Health factor threshold:** N/A
- **Liquidation penalty:** N/A
- **Monitoring:** Position tracking per venue; max_position_usdc cap enforced at signal level

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue      | Secret Name              | Testnet Available? | Notes                    |
| ---------- | ------------------------ | ------------------ | ------------------------ |
| Polymarket | exec-{client}-polymarket | Yes (Mumbai)       | Wallet + CLOB API key    |
| Kalshi     | exec-{client}-kalshi     | Yes (demo)         | API key (CFTC-regulated) |
| Betfair    | exec-{client}-betfair    | No                 | Exchange API + certs     |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Polymarket wallet (Polygon), Kalshi account, Betfair account
2. **Secret Manager:** Per-client secrets: `exec-{client}-{venue}-prediction`
3. **Config:** New PredictionArbConfig entry with client-specific min_edge_pct and max_position_usdc
4. **Position isolation:** One strategy instance per client (independent position tracking)
5. **Restart required?** No -- hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service           | What Changes                   | Restart?        |
| ----------------- | ------------------------------ | --------------- |
| strategy-service  | New PredictionArbConfig in GCS | No (hot-reload) |
| execution-service | New client venue routing rules | No (hot-reload) |

## Config Files

| Config File               | Focus      | Venues             | Min Edge | Max Position |
| ------------------------- | ---------- | ------------------ | -------- | ------------ |
| `prediction_arb_btc.yaml` | BTC/Crypto | Polymarket, Kalshi | 2.0%     | $1,000 USDC  |

## UI Visualisation

### Standard views (already in plans)

- PnL waterfall (risk matrix plan Stream D)
- Margin health time series (Stream D)
- Position breakdown

### Strategy-specific views (extensions)

- Cross-venue price comparison table: YES/NO prices per venue per market
- Arb opportunity scanner: live edge_pct ranking across all tracked markets
- Category breakdown: arb frequency by prediction market category
- Resolution timeline: open positions with expected resolution dates
- Venue spread comparison: bid-ask tightness across Polymarket, Kalshi, Betfair

## Testing Stage Status

| Stage        | Status  | Notes                                         |
| ------------ | ------- | --------------------------------------------- |
| MOCK         | Done    | Static venue quotes, verified pair scan logic |
| HISTORICAL   | Pending | Historical Polymarket + Kalshi price replay   |
| LIVE_MOCK    | Pending | Real venue quotes + paper execution           |
| LIVE_TESTNET | Pending | Polymarket Mumbai testnet + Kalshi demo       |
| BATCH_REAL   | Pending | Historical replay with optimized min_edge_pct |
| STAGING      | Pending | Testnet execution with real venue data        |
| LIVE_REAL    | Pending | Production execution across venues            |

## References

- **Strategy implementation:**
  `strategy-service/strategy_service/engine/strategies/prediction_arb/prediction_arb_strategy.py`
- **Prediction mapping:** `strategy-service/strategy_service/engine/strategies/prediction/prediction_mapping.py`
- **Config file:** `strategy-service/strategy_service/configs/prediction_arb_btc.yaml`
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`

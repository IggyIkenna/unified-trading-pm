# Sports Arbitrage

> **Asset class:** Sports **Strategy type:** Arbitrage **Strategy ID pattern:** `SPORTS_ARB_CROSS_BOOK`

## Overview

Cross-bookmaker arbitrage strategy that detects guaranteed-profit opportunities where the combined implied probabilities
of all outcomes across different bookmakers sum to less than 1.0. Also supports back-lay arbitrage (back at bookmaker,
lay at exchange) and halftime arbitrage using live HT odds snapshots.

## Token / Position Flow

```
Start:  BANKROLL:FIAT:GBP  (100% bankroll)

Step 1 - SCAN: For each event, find best odds per outcome across all bookmakers
Step 2 - VALIDATE: Confirm arb legs are from independent operator groups (arb_legs_are_independent)
Step 3 - COMPUTE: Calculate gross arb %, deduct expected exchange commission, compute net arb %
Step 4 - FILTER: Only emit signals where net arb % >= min_profit_margin (default 1%)
Step 5 - SIZE: Stake fraction per leg = implied_prob / (1 - margin), capped by max_stake_fraction
Step 6 - EXECUTE: Place simultaneous bets on each leg at the respective bookmaker/exchange

Wallet after deploy:
  - Leg 1: Outcome A at Bookmaker X = stake_fraction_1 of bankroll
  - Leg 2: Outcome B at Bookmaker Y = stake_fraction_2 of bankroll
  - Guaranteed profit = net arb margin regardless of outcome
```

## Instruments

| Instrument Key                 | Venue     | Type     | Role                  |
| ------------------------------ | --------- | -------- | --------------------- |
| `SPORTS:ARBITRAGE:CROSS_BOOK`  | Multiple  | Bet      | Arb across bookmakers |
| Event odds (h2h, totals, btts) | Betfair   | Exchange | Lay leg / best odds   |
| Event odds (h2h, totals, btts) | Smarkets  | Exchange | Lay leg / best odds   |
| Event odds (h2h, totals, btts) | Matchbook | Exchange | Lay leg / best odds   |
| Event odds (h2h, totals, btts) | Betdaq    | Exchange | Lay leg / best odds   |
| Event odds (h2h, totals, btts) | Pinnacle  | Sharp BM | Back leg / best odds  |
| Event odds (h2h, totals, btts) | Bet365    | Soft BM  | Back leg / best odds  |

## Key Features Consumed

| Feature            | Source Service       | SLA | Used For                             |
| ------------------ | -------------------- | --- | ------------------------------------ |
| `odds` (per-bm)    | market-tick-data-svc | <1s | Implied probability per outcome      |
| `ht_snapshots`     | market-tick-data-svc | <1s | Halftime odds for HT arb window      |
| `bookmaker_types`  | UAC arb_config       | N/A | Classify sharp/soft/exchange per leg |
| `commission_rates` | UAC arb_config       | N/A | Deduct exchange fees from gross arb  |

## PnL Attribution

| Component         | Settlement Type | Mechanism                                                         |
| ----------------- | --------------- | ----------------------------------------------------------------- |
| `arb_profit`      | EVENT_SETTLE    | Guaranteed profit = 1 - sum(implied_probs) after commission       |
| `commission_cost` | PER_FILL        | Exchange commission on winning legs (probability-weighted expect) |

**Source of truth:** `total_pnl = payout_received - total_staked`. Arb is risk-free: payout always exceeds stake by the
net margin. Commission is probability-weighted expected cost, not worst-case.

## Risk Profile

| Metric               | Target | Notes                                                |
| -------------------- | ------ | ---------------------------------------------------- |
| Target annual return | 5-15%  | Depends on market liquidity and arb frequency        |
| Target Sharpe ratio  | >3.0   | Near-riskless; variance from execution slippage only |
| Max drawdown         | <1%    | Only from failed execution (partial fills)           |
| Max leverage         | 1x     | No leverage; arb uses bankroll directly              |
| Capital scalability  | $50K   | Limited by bookmaker stake limits and account bans   |

## Latency Profile

| Segment                | p50 Target | p99 Target | Co-location Needed? |
| ---------------------- | ---------- | ---------- | ------------------- |
| Market data -> feature | 50ms       | 200ms      |                     |
| Feature -> signal      | 5ms        | 20ms       |                     |
| Signal -> instruction  | 10ms       | 50ms       |                     |
| Instruction -> fill    | 200ms      | 1000ms     |                     |
| **End-to-end**         | **265ms**  | **1270ms** | **No**              |

## Execution Details

- **Venues:** Betfair, Smarkets, Matchbook, Betdaq, Pinnacle, Bet365 (Polymarket, Kalshi for prediction markets)
- **Order types:** Market (bookmakers), Limit (exchanges)
- **Atomic execution required?** Yes -- all legs must be filled simultaneously; partial fill creates exposure
- **Rebalancing:** Per-event; no carry between events
- **Gas budget:** N/A (fiat venues)

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern    | Exposure Type     | Used For                     |
| --------------------- | ----------------- | ---------------------------- |
| `SPORTS:ARB:*`        | Stake committed   | Track bankroll allocation    |
| Per-event per-outcome | Settlement payout | Confirm arb profit on settle |

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold       | Action on Breach            |
| --------------- | ----------- | --------------- | --------------------------- |
| `delta`         | No          | --              | --                          |
| `funding`       | No          | --              | --                          |
| `basis`         | No          | --              | --                          |
| `protocol_risk` | No          | --              | --                          |
| `liquidity`     | Yes         | Stake > max_bet | Skip event or reduce size   |
| `execution`     | Yes         | Partial fill    | Hedge remaining leg at cost |

### Custom Strategy Risk Types

| Custom Risk         | What It Measures                       | Evaluation Method         | SSOT              |
| ------------------- | -------------------------------------- | ------------------------- | ----------------- |
| Account limiting    | Bookmaker restricting max stakes       | Track stake accepts       | execution-service |
| Operator group risk | Same-group arb legs (correlated close) | arb_legs_are_independent  | UAC arb_config    |
| Commission drift    | Exchange fee changes                   | EXCHANGE_COMMISSION_RATES | UAC arb_config    |

## Margin & Liquidation

- **Margin model:** None (pre-funded accounts at each bookmaker/exchange)
- **Health factor threshold:** N/A
- **Liquidation penalty:** N/A
- **Monitoring:** Bankroll per venue tracked; rebalance if skewed

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue     | Secret Name             | Testnet Available? | Notes                |
| --------- | ----------------------- | ------------------ | -------------------- |
| Betfair   | exec-{client}-betfair   | No                 | Exchange API + certs |
| Smarkets  | exec-{client}-smarkets  | No                 | REST API key         |
| Matchbook | exec-{client}-matchbook | No                 | REST API key         |
| Pinnacle  | exec-{client}-pinnacle  | No                 | REST API key         |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Accounts at each bookmaker/exchange venue
2. **Secret Manager:** Per-client secrets: `exec-{client}-{venue}-{account_type}`
3. **Config:** New ArbitrageConfigDict entry with client-specific min_profit_margin and max_bookmakers
4. **Position isolation:** One strategy instance per client (different venues may have different limits)
5. **Restart required?** No -- hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service           | What Changes                   | Restart?        |
| ----------------- | ------------------------------ | --------------- |
| strategy-service  | New arb config entry in GCS    | No (hot-reload) |
| execution-service | New client venue routing rules | No (hot-reload) |

## UI Visualisation

### Standard views (already in plans)

- PnL waterfall (risk matrix plan Stream D)
- Margin health time series (Stream D)
- Position breakdown

### Strategy-specific views (extensions)

- Live arb opportunity table: event, legs, gross/net margin, bookmakers involved
- Bookmaker liquidity ranking (events covered, coverage %, avg updates per event)
- Arb bucket distribution chart (soft_sharp, soft_exchange, sharp_sharp, etc.)
- HT arb overlay: arb margin vs minutes-since-halftime scatter plot
- Back-lay arb monitor: back_price vs lay_price with break-even overlay

## Testing Stage Status

| Stage        | Status  | Notes                                        |
| ------------ | ------- | -------------------------------------------- |
| MOCK         | Done    | Static odds fixtures, verified margin calc   |
| HISTORICAL   | Done    | Backtest engine validates on historical odds |
| LIVE_MOCK    | Done    | Live odds feed + paper execution             |
| LIVE_TESTNET | N/A     | No testnet for sports bookmakers             |
| BATCH_REAL   | Pending | Historical replay with real odds data        |
| STAGING      | Pending | Real odds feed + paper execution             |
| LIVE_REAL    | Pending | Production with real bookmaker accounts      |

## References

- **Strategy implementation:** `strategy-service/strategy_service/engine/strategies/sports/arbitrage.py`
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Arb config (UAC):** `unified-api-contracts/unified_api_contracts/internal/domain/sports/arb_config.py`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`

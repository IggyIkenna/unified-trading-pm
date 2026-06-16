---
scope: [engineer, admin]
---

# Kelly Criterion

> **Asset class:** Sports **Strategy type:** Position Sizing (Value Betting) **Strategy ID pattern:**
> `SPORTS_KELLY_HALF`

## Overview

Optimal bankroll allocation strategy for sports betting using the Kelly criterion formula: `f* = (p * b - q) / b`, where
p is the model-estimated probability, b is the net odds (decimal_odds - 1), and q = 1-p. Supports fractional Kelly
(default half-Kelly) for variance reduction, portfolio Kelly for simultaneous bets, simultaneous Kelly accounting for
committed bankroll, and venue-constrained Kelly respecting bookmaker stake limits.

## Token / Position Flow

```
Start:  BANKROLL:FIAT:GBP  (100% bankroll)

Step 1 - MODEL PROB: Receive model probability per outcome (e.g. home=0.55, draw=0.25, away=0.20)
Step 2 - BEST ODDS: For each outcome, find best odds across bookmakers
Step 3 - EDGE CHECK: edge = model_prob - implied_prob; skip if edge < min_edge (default 2%)
Step 4 - KELLY SIZING: f* = (p * b - q) / b * fractional_kelly, clamped to [0, max_bet_fraction]
Step 5 - PORTFOLIO CONSTRAINT: If total exposure > 100%, scale all fractions proportionally
Step 6 - VENUE CONSTRAINT: min(kelly_stake, venue_max_bet, account_max_observed_stake)
Step 7 - EMIT: SportsSignalDict with stake_fraction, edge, confidence

Wallet after deploy:
  - Open bets sized by Kelly fraction
  - Max single bet = 5% of bankroll (max_bet_fraction default)
  - Total exposure capped at 100% via portfolio_kelly
```

## Instruments

| Instrument Key            | Venue    | Type | Role             |
| ------------------------- | -------- | ---- | ---------------- |
| `SPORTS:KELLY:HALF_KELLY` | Multiple | Bet  | Kelly-sized bets |
| Event outcomes (h2h)      | Betfair  | Bet  | Best odds source |
| Event outcomes (h2h)      | Pinnacle | Bet  | Best odds source |
| Event outcomes (h2h)      | Bet365   | Bet  | Best odds source |

## Key Features Consumed

| Feature               | Source Service       | SLA | Used For                                 |
| --------------------- | -------------------- | --- | ---------------------------------------- |
| `model_probabilities` | ml-service / FSS     | 5m  | Model-estimated probability per outcome  |
| `odds` (per-bm)       | market-tick-data-svc | <1s | Implied probability and best odds lookup |

## PnL Attribution

| Component      | Settlement Type | Mechanism                                       |
| -------------- | --------------- | ----------------------------------------------- |
| `bet_pnl`      | EVENT_SETTLE    | Win: stake \* (odds - 1); Lose: -stake          |
| `edge_alpha`   | ATTRIBUTION     | Excess return from positive-edge bet selection  |
| `sizing_alpha` | ATTRIBUTION     | Excess return from Kelly-optimal sizing vs flat |

**Source of truth:** `total_pnl = bankroll_current - bankroll_initial`. Kelly sizing maximizes long-term log-wealth
growth rate. Fractional Kelly trades growth rate for reduced variance.

## Risk Profile

| Metric               | Target  | Notes                                                |
| -------------------- | ------- | ---------------------------------------------------- |
| Target annual return | 10-30%  | Depends on edge quality and bet frequency            |
| Target Sharpe ratio  | 1.0-2.0 | Half-Kelly reduces variance by 75% vs full Kelly     |
| Max drawdown         | 20%     | Half-Kelly expected max DD is ~half of full Kelly    |
| Max leverage         | 1x      | No leverage; max exposure = 100% bankroll            |
| Capital scalability  | $100K   | Limited by bookmaker limits and account restrictions |

## Latency Profile

| Segment                | p50 Target | p99 Target | Co-location Needed? |
| ---------------------- | ---------- | ---------- | ------------------- |
| Market data -> feature | 100ms      | 500ms      |                     |
| Feature -> signal      | 5ms        | 20ms       |                     |
| Signal -> instruction  | 10ms       | 50ms       |                     |
| Instruction -> fill    | 200ms      | 1000ms     |                     |
| **End-to-end**         | **315ms**  | **1570ms** | **No**              |

## Execution Details

- **Venues:** Betfair, Smarkets, Matchbook, Pinnacle, Bet365 (best odds per outcome)
- **Order types:** Market (bookmakers), Limit (exchanges)
- **Atomic execution required?** No -- each bet is independent
- **Rebalancing:** Per-event; portfolio Kelly applied when multiple simultaneous bets are open
- **Gas budget:** N/A (fiat venues)

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern | Exposure Type    | Used For                                      |
| ------------------ | ---------------- | --------------------------------------------- |
| Open bets          | Stake committed  | Track current_exposure for simultaneous_kelly |
| Open bets          | Potential payout | Track max portfolio exposure                  |

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold     | Action on Breach                      |
| --------------- | ----------- | ------------- | ------------------------------------- |
| `delta`         | No          | --            | --                                    |
| `funding`       | No          | --            | --                                    |
| `basis`         | No          | --            | --                                    |
| `protocol_risk` | No          | --            | --                                    |
| `liquidity`     | Yes         | venue_max_bet | Cap stake via venue_constrained_kelly |
| `exposure`      | Yes         | 100% bankroll | Scale fractions via portfolio_kelly   |

### Custom Strategy Risk Types

| Custom Risk       | What It Measures                | Evaluation Method        | SSOT            |
| ----------------- | ------------------------------- | ------------------------ | --------------- |
| Model calibration | Model prob accuracy over time   | Brier score tracking     | ml-service      |
| Over-betting risk | Full Kelly ruin probability     | Kelly fraction histogram | strategy config |
| Venue limiting    | Stake acceptance rate declining | Fill rate tracking       | execution svc   |

## Margin & Liquidation

- **Margin model:** None (pre-funded accounts at each bookmaker/exchange)
- **Health factor threshold:** N/A
- **Liquidation penalty:** N/A
- **Monitoring:** Bankroll tracking; fractional Kelly ensures positive expected log growth

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue    | Secret Name            | Testnet Available? | Notes           |
| -------- | ---------------------- | ------------------ | --------------- |
| Betfair  | exec-{client}-betfair  | No                 | Exchange API    |
| Pinnacle | exec-{client}-pinnacle | No                 | Sharp bookmaker |
| Bet365   | exec-{client}-bet365   | No                 | Soft bookmaker  |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Accounts at target bookmakers/exchanges
2. **Secret Manager:** Per-client secrets: `exec-{client}-{venue}-{account_type}`
3. **Config:** New KellyCriterionConfigDict with client-specific fractional_kelly, max_bet_fraction, min_edge
4. **Position isolation:** One strategy instance per client (independent bankroll tracking)
5. **Restart required?** No -- hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service           | What Changes                   | Restart?        |
| ----------------- | ------------------------------ | --------------- |
| strategy-service  | New Kelly config entry in GCS  | No (hot-reload) |
| execution-service | New client venue routing rules | No (hot-reload) |

## UI Visualisation

### Standard views (already in plans)

- PnL waterfall (risk matrix plan Stream D)
- Margin health time series (Stream D)
- Position breakdown

### Strategy-specific views (extensions)

- Kelly fraction distribution histogram (raw vs adjusted)
- Bankroll growth chart (actual vs Kelly-optimal theoretical)
- Edge distribution: model_prob vs implied_prob scatter
- Portfolio exposure gauge: total committed / bankroll
- Venue-constrained sizing: Kelly optimal vs venue max accepted

## Testing Stage Status

| Stage        | Status  | Notes                                             |
| ------------ | ------- | ------------------------------------------------- |
| MOCK         | Done    | Static probabilities, verified Kelly formula      |
| HISTORICAL   | Done    | Football backtest with historical model probs     |
| LIVE_MOCK    | Done    | Real odds + ML model probs + paper execution      |
| LIVE_TESTNET | N/A     | No testnet for sports bookmakers                  |
| BATCH_REAL   | Pending | Historical replay with optimized fractional Kelly |
| STAGING      | Pending | Paper execution with real ML predictions          |
| LIVE_REAL    | Pending | Production with real bookmaker accounts           |

## References

- **Strategy implementation:** `strategy-service/strategy_service/engine/strategies/sports/kelly.py`
- **Kelly fraction function:** `compute_kelly_fraction()` in kelly.py (shared with MLSportsStrategy)
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`

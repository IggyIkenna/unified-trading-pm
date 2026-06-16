---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# Sports Arbitrage

> **Asset class:** Sports **Strategy type:** Arbitrage **Strategy ID pattern:** `SPORTS_ARB` (cross-book),
> `SPORTS_ARB_BACK_LAY` (back-lay)

## Overview

Detects guaranteed-profit opportunities across bookmakers where the combined implied probabilities of all outcomes sum
to less than 1.0. For a 3-way market (h2h), an arbitrage exists when `1/odds_home + 1/odds_draw + 1/odds_away < 1.0`.
For back-lay, an arbitrage exists when the best back price at a bookmaker exceeds the best lay price at an exchange
(after commission). The strategy is purely rule-based with `confidence=1.0` -- no ML model is required. Signals are
emitted for each leg of the arb (one per outcome/bookmaker), with stake fractions proportional to implied probability
divided by `(1 - margin)`, clamped to `max_stake_fraction`. Expected exchange commission is computed as a
probability-weighted expected fee (not worst-case) and deducted from the gross arb margin before the `min_profit_margin`
gate. Same-operator arbs are rejected via `arb_legs_are_independent()` using `VENUE_OPERATOR_GROUPS`.

## Token / Position Flow

```
Start:  BANKROLL:FIAT:GBP  (100% bankroll, split across venue balances)

Step 1 - ODDS INGEST: Receive live odds from multiple feeds:
         SharpAPI WS (DK/FD/BetMGM/Caesars), odds-api.io WS+REST (Betfair+SingBet+275 books),
         Betfair Exchange Stream (back+lay, ms latency), Polymarket REST (60s polling)
Step 2 - BEST ODDS: For each outcome, find highest decimal odds across all bookmakers
Step 3 - OPERATOR CHECK: Reject if any two legs share the same operator group (VENUE_OPERATOR_GROUPS)
Step 4 - GROSS ARB: gross_arb_pct = (1 - sum_implied) * 100; skip if <= 0
Step 5 - COMMISSION: expected_fee_pct = sum over exchange legs of P(outcome) * rate * stake_frac * (odds-1)
Step 6 - NET ARB GATE: net_arb_pct = gross - expected_fee; skip if < min_profit_margin * 100
Step 7 - SUSPICIOUS GATE: reject arbs above MAX_ARB_MARGIN (5%) as likely data errors
Step 8 - STALENESS GATE: reject arbs where leg bm_times differ by more than staleness threshold
Step 9 - STAKE SIZING: per-leg stake_fraction = implied_prob / (1 - margin), clamped to max_stake_fraction;
         backtest uses 25% of venue balance per bet (reserves for ~4 concurrent bets), minimum $5
Step 10 - EMIT: One SportsSignalDict per leg with arb_margin, total_implied_prob, net_arb_pct metadata

For back-lay:
Step 3b - BACK: highest bookmaker odds (excluding exchanges)
Step 4b - LAY: lowest exchange lay price from exchange_meta order book
Step 5b - PROFIT CHECK: min(profit_if_wins, profit_if_loses) after commission > min_profit_margin
Step 6b - EMIT: Two signals -- BACK leg at bookmaker, LAY leg at exchange with lay_ratio sizing

Wallet after deploy:
  - Per-venue balances tracked independently (VenueBalance schema in UAC)
  - 25% of venue balance per bet (reserves for ~4 concurrent bets)
  - No intraday transfers (realistic: transfers take hours/days)
  - Adaptive venue allocation: rolling-window frequency-based rebalancing at start of each day
  - Exchanges get 0.6x allocation weight (they accumulate capital from wins)
  - Bookmakers get 1.4x allocation weight (they drain from losses)
  - Every venue gets at least 1% floor (VENUE_FLOOR_PCT) to prevent capital starvation
```

## Instruments

| Instrument Key                  | Venue      | Type       | Role                                    |
| ------------------------------- | ---------- | ---------- | --------------------------------------- |
| `SPORTS:ARBITRAGE:CROSS_BOOK`   | Multiple   | Bet        | 3-way cross-bookmaker arbs              |
| `SPORTS:ARBITRAGE:BACK_LAY`     | Multiple   | Bet        | Back-lay arbs (bookmaker + exchange)    |
| Event outcomes (h2h)            | Betfair    | Exchange   | Back+lay odds source, lay leg execution |
| Event outcomes (h2h)            | Smarkets   | Exchange   | Back+lay odds source                    |
| Event outcomes (h2h)            | Matchbook  | Exchange   | Back+lay odds source (1.5% commission)  |
| Event outcomes (h2h)            | Betdaq     | Exchange   | Back+lay odds source                    |
| Event outcomes (h2h, totals)    | Pinnacle   | Bookmaker  | Sharp bookmaker odds source             |
| Event outcomes (h2h, totals)    | Bet365     | Bookmaker  | Soft bookmaker odds source              |
| Event outcomes (totals,spreads) | Multiple   | Bookmaker  | Over/Under and Asian handicap arbs      |
| Event outcomes (binary)         | Polymarket | Prediction | Binary market odds (h2h excluded)       |
| Event outcomes (binary)         | Kalshi     | Prediction | Binary market odds (h2h excluded)       |

## Key Features Consumed

| Feature                          | Source Service       | SLA | Used For                                               |
| -------------------------------- | -------------------- | --- | ------------------------------------------------------ |
| `odds` (per-bookmaker, per-feed) | market-tick-data-svc | <1s | Best odds per outcome, implied probability             |
| `exchange_meta` (order book)     | market-tick-data-svc | <1s | Lay prices, available size per level for back-lay arbs |
| `bm_time` (bookmaker timestamp)  | market-tick-data-svc | <1s | Staleness filter -- reject arbs with stale leg prices  |
| `fixture_results`                | instruments-service  | 1h  | Settlement: home_goals, away_goals for backtest/live   |
| `venue_balances`                 | position-balance-svc | 5m  | Per-venue capital tracking for stake sizing            |

## PnL Attribution

| Component            | Settlement Type | Mechanism                                                               |
| -------------------- | --------------- | ----------------------------------------------------------------------- |
| `arb_margin`         | EVENT_SETTLE    | Guaranteed profit from sum_implied < 1.0; net of exchange commission    |
| `exchange_fee`       | EVENT_SETTLE    | Commission paid on exchange legs (2% Betfair, 1.5% Matchbook, 2% other) |
| `execution_slippage` | ATTRIBUTION     | Difference between detected arb margin and actual fill prices           |
| `stale_arb_loss`     | ATTRIBUTION     | Losses from arbs where one leg's price moved between detection and fill |

**Source of truth:** `total_pnl = sum(venue_balances) - initial_bankroll`. For a well-calibrated arb strategy, every
trade should be individually profitable (arb_margin > 0 after commission). Losses come from execution slippage (stale
odds, partial fills) or data errors (wrong fixture matching, complement pricing). The backtest tracks per-trade
return_pct and capital_utilisation to decompose actual vs theoretical profitability.

## Risk Profile

| Metric               | Target  | Notes                                                                      |
| -------------------- | ------- | -------------------------------------------------------------------------- |
| Target annual return | 15-40%  | Depends on venue count, capital allocation, and arb frequency              |
| Target Sharpe ratio  | 3.0-8.0 | Very high (each trade is individually profitable in theory)                |
| Max drawdown         | 5%      | Only from stale odds / execution failures; not from outcome variance       |
| Max leverage         | 1x      | No leverage; all bets from venue balances                                  |
| Capital scalability  | $50K    | Limited by bookmaker stake limits, account restricting, venue balance mgmt |

## Latency Profile

| Segment                | p50 Target | p99 Target | Co-location Needed? |
| ---------------------- | ---------- | ---------- | ------------------- |
| Market data -> feature | 50ms       | 200ms      |                     |
| Feature -> signal      | 5ms        | 20ms       |                     |
| Signal -> instruction  | 10ms       | 50ms       |                     |
| Instruction -> fill    | 200ms      | 1000ms     |                     |
| **End-to-end**         | **265ms**  | **1270ms** | **No**              |

## Execution Details

- **Venues:** Betfair (exchange, 2%), Smarkets (exchange, 2%), Matchbook (exchange, 1.5%), Betdaq (exchange, 2%),
  Pinnacle (sharp bookmaker), Bet365 (soft bookmaker), plus 275+ via odds-api.io on paid tier. Polymarket and Kalshi
  excluded from 3-way h2h (independent binary pricing) but valid for 2-way markets.
- **Order types:** Market (bookmakers), Limit (exchanges -- Betfair, Smarkets)
- **Execution order:** `exchange_first` recommended -- exchanges lag, capture generous price before correction.
  Configurable via `ArbitrageStrategyConfig.execution_order`.
- **Atomic execution required?** Yes for back-lay (both legs must fill). No for 3-way (partial fill loses the guarantee
  but individual legs still have expected value if arb was detected correctly).
- **Rebalancing:** Per-day adaptive venue allocation based on rolling-window arb frequency. No intraday transfers
  (realistic constraint). Blended weight: 0.6 x actual_trade_frequency + 0.4 x missed_opportunity_frequency.
- **Gas budget:** N/A for fiat venues. Polymarket/Kalshi excluded from arb detection due to pricing structure.

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions -> exposures) -> RiskMonitor (exposures -> risk assessment) -> Strategy (risk
assessment -> rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern        | Exposure Type           | Used For                                                          |
| ------------------------- | ----------------------- | ----------------------------------------------------------------- |
| `SPORTS:ARBITRAGE:*`      | Stake committed         | Track total bankroll at risk across open bets                     |
| Open bets per venue       | Venue balance locked    | 25% sizing requires knowing available balance per venue           |
| Active arb legs           | Correlated leg exposure | Both legs of back-lay must settle; one failing = risk             |
| Total exposure all venues | Max exposure gate       | Pause if >80% of total bankroll deployed (max_total_exposure_pct) |

**SSOT:** `component_config.exposure_monitor.instrument_subscriptions` in strategy config. Schema:
[`ExposureMonitorConfig`](../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold               | Action on Breach                            |
| --------------- | ----------- | ----------------------- | ------------------------------------------- |
| `delta`         | No          | --                      | --                                          |
| `funding`       | No          | --                      | --                                          |
| `basis`         | No          | --                      | --                                          |
| `protocol_risk` | No          | --                      | --                                          |
| `liquidity`     | Yes         | venue_balance < MIN_BET | Skip venue until rebalance or deposit       |
| `exposure`      | Yes         | 80% bankroll deployed   | Pause new signals until bets settle         |
| `staleness`     | Yes         | bm_time diff > 30s      | Reject arb opportunity (stale odds)         |
| `operator`      | Yes         | same operator group     | Reject arb (arb_legs_are_independent check) |

**SSOT:** `component_config.risk_monitor.enabled_risk_types` in strategy config. Schema:
[`RiskMonitorConfig`](../../strategy-service/strategy_service/config.py) Formal subscription type:
[`StrategyRiskProfile`](../../unified-api-contracts/unified_api_contracts/internal/risk.py)

**Gap:** `StrategyRiskProfile` exists in `unified_api_contracts.internal` but is NOT yet wired into strategy-service
config. Risk subscriptions are currently implicit in code (per-strategy TypedDict defaults), not in a machine-readable
registry. Plan item `p5-risk-strategy-subscription` in `uac_errors_package_cleanup` will create a YAML-based
subscription registry.

### Custom Strategy Risk Types

| Custom Risk                 | What It Measures                                    | Evaluation Method                         | SSOT           |
| --------------------------- | --------------------------------------------------- | ----------------------------------------- | -------------- |
| Venue balance depletion     | Per-venue balance approaching zero                  | Balance < 1% floor after trade settlement | arb_config     |
| Same-operator correlation   | Arb legs from same corporate group                  | VENUE_OPERATOR_GROUPS lookup              | UAC arb_config |
| Stale odds execution        | Price moved between detection and fill              | bm_time alignment check                   | strategy svc   |
| Exchange commission erosion | Commission eating more than expected arb margin     | expected_fee_pct vs gross_arb_pct ratio   | strategy svc   |
| Suspicious arb margin       | Arb margin > 5% (likely data error / wrong fixture) | MAX_ARB_MARGIN gate in backtest           | backtest       |

**Gap:** Custom risk types are planned (plan item `p5-risk-custom-risk-types`) but not yet implemented. Currently no
machine-readable custom risk definitions exist.

## Margin & Liquidation

- **Margin model:** None (pre-funded accounts at each bookmaker/exchange)
- **Health factor threshold:** N/A
- **Liquidation penalty:** N/A
- **Monitoring:** Per-venue balance tracked via `VenueBalance` schema (UAC `arb_config.py`). Fields: balance, available,
  locked, total_deposited, total_withdrawn, total_won, total_lost, total_fees, bets_placed, bets_settled. Capital
  rebalancing at start of each trading day via `VenueAllocationWeights` (rolling-window frequency-based). If any venue
  balance drops below the 1% floor, that venue is starved of new bets but retains its floor allocation at next
  rebalance.

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue       | Secret Name             | Testnet Available? | Notes                           |
| ----------- | ----------------------- | ------------------ | ------------------------------- |
| Betfair     | exec-{client}-betfair   | No                 | Exchange API + SSL certs        |
| Smarkets    | exec-{client}-smarkets  | No                 | REST API key                    |
| Matchbook   | exec-{client}-matchbook | No                 | REST API key (1.5% commission)  |
| Betdaq      | exec-{client}-betdaq    | No                 | REST API key                    |
| Pinnacle    | exec-{client}-pinnacle  | No                 | REST API key (sharp bookmaker)  |
| Bet365      | exec-{client}-bet365    | No                 | REST API key                    |
| SharpAPI    | sharpapi-key            | N/A                | WS feed key (DK/FD/BetMGM/etc.) |
| odds-api.io | oddsapiio-key           | N/A                | WS+REST feed key (275+ books)   |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Funded accounts at target bookmakers/exchanges. Capital split across venues per
   `VenueAllocationWeights`.
2. **Secret Manager:** Per-client secrets: `exec-{client}-{venue}-{account_type}` for each venue
3. **Config:** New `ArbitrageStrategyConfig` entry with client-specific `min_expected_net_arb_pct`,
   `bet_size_pct_of_venue_balance`, `max_total_exposure_pct`, and venue enable flags
4. **Position isolation:** One strategy instance per client (independent venue balances; different bookmaker account
   limits)
5. **Restart required?** No -- hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service                      | What Changes                       | Restart?        |
| ---------------------------- | ---------------------------------- | --------------- |
| strategy-service             | New ArbitrageStrategyConfig in GCS | No (hot-reload) |
| execution-service            | New client venue routing rules     | No (hot-reload) |
| position-balance-monitor-svc | New VenueBalance tracking          | No (hot-reload) |

## UI Visualisation

### Standard views (already in plans)

- PnL waterfall (risk matrix plan Stream D)
- Margin health time series (Stream D)
- Position breakdown

### Strategy-specific views (extensions)

- Arb margin distribution: histogram of detected vs executed arb margins (gross and net)
- Venue balance evolution: per-venue balance time series with deposit/withdrawal/trading P&L breakdown
- Arb bucket heatmap: frequency and profitability by bucket (soft_sharp, soft_soft, soft_exchange, sharp_sharp,
  exchange_sharp)
- Capital utilisation chart: actual_stake / unconstrained_stake ratio per trade
- Missed opportunity tracker: bottleneck venue analysis showing which venues blocked the most arbs
- Market type breakdown: profit and frequency by market (h2h, totals, spreads, back_lay)
- Arb duration chart: how many snapshots each arb persists before closing
- Venue allocation weights: rolling-window allocation visualization with frequency and flow adjustment

## Testing Stage Status

| Stage        | Status  | Notes                                                                                 |
| ------------ | ------- | ------------------------------------------------------------------------------------- |
| MOCK         | Done    | Static odds fixtures; verified arb detection, commission calc, operator check         |
| HISTORICAL   | Done    | Rolling backtest with walk-forward per-day allocation, per-venue balances, settlement |
| LIVE_MOCK    | Done    | Live scanner: SharpAPI + odds-api.io WS + Betfair Stream + Polymarket REST            |
| LIVE_TESTNET | N/A     | No testnet for sports bookmakers                                                      |
| BATCH_REAL   | Pending | Historical replay with optimized allocation weights                                   |
| STAGING      | Pending | Paper execution with real multi-feed odds                                             |
| LIVE_REAL    | Pending | Production with real bookmaker/exchange accounts                                      |

## Arb Bucket Classification

Half-time arb signals are annotated with an `arb_bucket` in metadata, classifying the bookmaker pairing:

| Bucket           | Description                       | Expected Frequency |
| ---------------- | --------------------------------- | ------------------ |
| `soft_sharp`     | Soft bookmaker vs sharp bookmaker | Most common        |
| `soft_soft`      | Two soft bookmakers               | Common             |
| `soft_exchange`  | Soft bookmaker vs exchange        | Common             |
| `sharp_sharp`    | Two sharp bookmakers              | Rare               |
| `exchange_sharp` | Exchange vs sharp bookmaker       | Rare               |

Bookmaker types (`sharp`, `soft`, `exchange`, `semi_sharp`) are passed via `bookmaker_types` dict to
`generate_sports_signal_ht()`. Semi-sharp venues are normalized to `sharp` for bucket classification.

## Venue Exclusions (Backtest)

The rolling backtest applies venue-level quality filters based on empirical testing:

| Venue       | Exclusion Reason                                                   |
| ----------- | ------------------------------------------------------------------ |
| boylesports | Corrupt data (compressed odds, not standard decimal)               |
| betway      | 4-6% avg price diff from Odds API (different pricing feed)         |
| leovegas    | 3.3% avg diff, 2-4% exact match rate (consistently off)            |
| 188bet      | 60s max delay on OddsPapi -- prices can be stale, only $6.42/week  |
| betsson     | Same staleness issue as 188bet                                     |
| Polymarket  | Excluded from h2h (independent binary pricing, sum_implied ~1.74)  |
| Kalshi      | Excluded from h2h (independent binary pricing, complement pricing) |
| PMU         | Parimutuel -- pool-based pricing incompatible with fixed-odds arb  |

## References

- **Strategy implementation:** `strategy-service/strategy_service/engine/strategies/sports/arbitrage.py`
- **Config schema (UAC):** `unified-api-contracts/unified_api_contracts/internal/domain/sports/arb_config.py`
- **Live scanner:** `e2e-testing/scripts/sports/live_arb_scanner.py`
- **Rolling backtest:** `e2e-testing/scripts/sports/arb_rolling_backtest.py`
- **Kelly sizing (shared):** `strategy-service/strategy_service/engine/strategies/sports/kelly.py`
- **Base class:** `strategy-service/strategy_service/engine/strategies/sports/sports_base.py`
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`

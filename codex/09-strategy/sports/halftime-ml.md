# Halftime ML

> **Asset class:** Sports **Strategy type:** Value Betting (ML) **Strategy ID pattern:** `SPORTS_HT_ML_{MODEL_ID}`

## Overview

ML-driven sports betting strategy with two prediction windows: pre-game (before kickoff, using team form, head-to-head,
and odds movement features) and halftime (at the HT whistle, adding score, xG, possession, and shots-on-target context).
Each window uses its own ML model. Signals are Kelly-sized via the shared `compute_kelly_fraction` helper, and venue
routing distinguishes exchanges (Betfair/Smarkets/Matchbook with BACK/LAY support) from bookmakers (Pinnacle/Bet365 with
BACK only). Configurable per-sport via YAML configs (soccer, NBA, NFL).

## Token / Position Flow

```
Start:  BANKROLL:FIAT:GBP  (100% bankroll)

PRE-GAME window:
  Step 1 - ML_PREDICT: pre_game_model generates P(home), P(draw), P(away)
  Step 2 - BEST ODDS: Find best odds per outcome across all bookmakers via HT snapshot format
  Step 3 - CONFIDENCE GATE: Skip if model_prob < confidence_threshold (default 0.55)
  Step 4 - EDGE GATE: Skip if edge < min_edge_threshold (default 3%)
  Step 5 - KELLY SIZE: compute_kelly_fraction(prob, odds, frac_kelly=0.5, max=0.05)
  Step 6 - VENUE ROUTE: Determine BetSide (BACK for value bets) and venue type
  Step 7 - EMIT: Best-edge outcome as single SportsSignalDict

HALFTIME window:
  Same flow but with halftime_model incorporating live match stats.
  Uses SportsMarketHTDict / OddsHTSnapshotDict for HT odds data.

Wallet after deploy:
  - Single best-edge bet per event per window
  - Kelly-sized: default half-Kelly, max 5% of bankroll
```

## Instruments

| Instrument Key                 | Venue     | Type     | Role                  |
| ------------------------------ | --------- | -------- | --------------------- |
| `SPORTS:HT_ML:{model_id}`      | Multiple  | Bet      | ML-sized value bet    |
| Event odds (h2h, totals, btts) | Betfair   | Exchange | Best odds + BACK/LAY  |
| Event odds (h2h, totals, btts) | Smarkets  | Exchange | Best odds + BACK/LAY  |
| Event odds (h2h, totals, btts) | Matchbook | Exchange | Best odds + BACK/LAY  |
| Event odds (h2h)               | Pinnacle  | Sharp BM | Best odds (BACK only) |
| Event odds (h2h)               | Bet365    | Soft BM  | Best odds (BACK only) |

## Key Features Consumed

| Feature                  | Source Service       | SLA  | Used For                           |
| ------------------------ | -------------------- | ---- | ---------------------------------- |
| `team_form_5`            | features-sports-svc  | 1h   | Pre-game: recent form signal       |
| `head_to_head`           | features-sports-svc  | 1h   | Pre-game: historical matchup       |
| `xg_rolling`             | features-sports-svc  | live | Both windows: expected goals proxy |
| `odds_movement`          | market-tick-data-svc | <1s  | Pre-game: market sentiment shift   |
| `possession_pct`         | features-sports-svc  | live | Halftime: in-play dominance        |
| `shots_on_target`        | features-sports-svc  | live | Halftime: attacking quality        |
| `ht_odds_home/draw/away` | market-tick-data-svc | <1s  | Halftime: live HT odds snapshots   |

## PnL Attribution

| Component      | Settlement Type | Mechanism                                         |
| -------------- | --------------- | ------------------------------------------------- |
| `bet_pnl`      | EVENT_SETTLE    | Win: stake \* (odds - 1); Lose: -stake            |
| `model_alpha`  | ATTRIBUTION     | Excess return from ML edge (model_prob - implied) |
| `timing_alpha` | ATTRIBUTION     | Additional edge from halftime re-evaluation       |

**Source of truth:** `total_pnl = bankroll_current - bankroll_initial`. Kelly sizing maximizes long-term growth.
Halftime window captures value from live match information that bookmakers are slow to price.

## Risk Profile

| Metric               | Target  | Notes                                            |
| -------------------- | ------- | ------------------------------------------------ |
| Target annual return | 15-35%  | Higher with halftime window (more info edge)     |
| Target Sharpe ratio  | 1.5-2.5 | Half-Kelly + dual windows reduces variance       |
| Max drawdown         | 15%     | Bounded by max_stake_fraction (5%)               |
| Max leverage         | 1x      | No leverage; bankroll-funded                     |
| Capital scalability  | $100K   | Limited by bookmaker acceptance and odds latency |

## Latency Profile

| Segment                | p50 Target | p99 Target | Co-location Needed? |
| ---------------------- | ---------- | ---------- | ------------------- |
| Market data -> feature | 100ms      | 500ms      |                     |
| Feature -> ML predict  | 200ms      | 1000ms     |                     |
| ML predict -> signal   | 5ms        | 20ms       |                     |
| Signal -> instruction  | 10ms       | 50ms       |                     |
| Instruction -> fill    | 200ms      | 1000ms     |                     |
| **End-to-end**         | **515ms**  | **2570ms** | **No**              |

## Execution Details

- **Venues:** Betfair, Smarkets, Matchbook (exchanges); Pinnacle, Bet365, William Hill, Unibet, bwin, Betsson
  (bookmakers)
- **Order types:** Market (bookmakers), Limit (exchanges)
- **Atomic execution required?** No -- single best-edge bet per event
- **Rebalancing:** Two windows per event: pre-game and halftime
- **Gas budget:** N/A (fiat venues)

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern | Exposure Type     | Used For                       |
| ------------------ | ----------------- | ------------------------------ |
| Open bets          | Stake committed   | Bankroll tracking              |
| Per-phase bets     | Phase attribution | Pre-game vs halftime P&L split |

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold       | Action on Breach |
| --------------- | ----------- | --------------- | ---------------- |
| `delta`         | No          | --              | --               |
| `funding`       | No          | --              | --               |
| `basis`         | No          | --              | --               |
| `protocol_risk` | No          | --              | --               |
| `liquidity`     | Yes         | Stake > max_bet | Reduce or skip   |
| `model_conf`    | Yes         | < 0.55          | Skip bet         |

### Custom Strategy Risk Types

| Custom Risk         | What It Measures                 | Evaluation Method   | SSOT            |
| ------------------- | -------------------------------- | ------------------- | --------------- |
| Model calibration   | Brier score over rolling window  | Calibration audit   | ml-service      |
| HT odds staleness   | Delay in HT odds snapshot update | Timestamp freshness | MTDS            |
| Venue type mismatch | Placing LAY order at bookmaker   | venue_types map     | strategy config |

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

| Venue    | Secret Name            | Testnet Available? | Notes               |
| -------- | ---------------------- | ------------------ | ------------------- |
| Betfair  | exec-{client}-betfair  | No                 | Exchange (BACK/LAY) |
| Smarkets | exec-{client}-smarkets | No                 | Exchange (BACK/LAY) |
| Pinnacle | exec-{client}-pinnacle | No                 | Sharp bookmaker     |
| Bet365   | exec-{client}-bet365   | No                 | Soft bookmaker      |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Accounts at target bookmakers/exchanges
2. **Secret Manager:** Per-client secrets: `exec-{client}-{venue}-{account_type}`
3. **Config:** New HalftimeMLConfigDict with client-specific model IDs, thresholds, and venue types
4. **Position isolation:** One strategy instance per client (independent model + bankroll)
5. **Restart required?** No -- hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service           | What Changes                      | Restart?            |
| ----------------- | --------------------------------- | ------------------- |
| strategy-service  | New HT ML config entry in GCS     | No (hot-reload)     |
| execution-service | New client venue routing rules    | No (hot-reload)     |
| ml-service        | Per-sport model training pipeline | No (model hot-swap) |

## Config Files

| Config File               | Sport    | Leagues               | Models                             |
| ------------------------- | -------- | --------------------- | ---------------------------------- |
| `halftime_ml_soccer.yaml` | Football | EPL, Champions League | fss_soccer_pregame/halftime_xgb_v2 |
| `halftime_ml_nba.yaml`    | NBA      | Per-config            | Sport-specific models              |
| `halftime_ml_nfl.yaml`    | NFL      | Per-config            | Sport-specific models              |

## UI Visualisation

### Standard views (already in plans)

- PnL waterfall (risk matrix plan Stream D)
- Margin health time series (Stream D)
- Position breakdown

### Strategy-specific views (extensions)

- Dual-window signal timeline: pre-game vs halftime signals per event
- Model probability vs implied probability scatter (with edge overlay)
- Confidence distribution by phase (pre-game vs halftime)
- Venue routing breakdown: exchange vs bookmaker fill rates
- Kelly fraction distribution: raw vs adjusted histogram

## Testing Stage Status

| Stage        | Status  | Notes                                            |
| ------------ | ------- | ------------------------------------------------ |
| MOCK         | Done    | Static HT snapshots, verified dual-window logic  |
| HISTORICAL   | Done    | Football backtest with historical ML predictions |
| LIVE_MOCK    | Done    | Real odds + ML model + paper execution           |
| LIVE_TESTNET | N/A     | No testnet for sports bookmakers                 |
| BATCH_REAL   | Pending | Historical replay with per-sport configs         |
| STAGING      | Pending | Paper execution with real HT odds data           |
| LIVE_REAL    | Pending | Production with real bookmaker accounts          |

## References

- **Strategy implementation:** `strategy-service/strategy_service/engine/strategies/sports/halftime_ml.py`
- **Kelly sizing:** `strategy-service/strategy_service/engine/strategies/sports/kelly.py` (`compute_kelly_fraction`)
- **Config files:** `strategy-service/strategy_service/configs/halftime_ml_*.yaml`
- **BetSide enum:** `unified-api-contracts/unified_api_contracts/sports.py`
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`

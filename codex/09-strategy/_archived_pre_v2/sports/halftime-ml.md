---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# Sports Halftime ML

> **Asset class:** Sports **Strategy type:** Halftime ML Prediction **Strategy ID pattern:** `SPORTS_ML_HALFTIME`

## Overview

Re-evaluates match outcome probabilities at halftime using a dedicated ML model that incorporates live HT data -- score,
possession, shots, xG, cards, fouls, and momentum -- that was unavailable at kickoff. This is fundamentally different
from pre-game prediction: the information set changes dramatically at the HT whistle. A team trailing 0-2 with 20%
possession and zero shots on target has a very different second-half probability than the pre-game model assumed.

The strategy runs in two phases via the same `HalftimeMLStrategy` class. Phase 1 (`pre_game`) fires before kickoff with
standard pre-game features. Phase 2 (`halftime`) fires during the HT break with live HT data injected into a separate
model trained specifically on halftime states. Both phases use fractional Kelly criterion for stake sizing, but the
halftime phase operates in thinner markets with wider spreads, so `max_stake_fraction` is advisable to keep lower.

Each sport has its own model and config: soccer (EPL + Champions League), NFL, and NBA. Model IDs follow the convention
`fss_{sport}_halftime_{algo}_v{N}`.

## Token / Position Flow

```
Start:  BANKROLL:FIAT:GBP  (100% bankroll)

Step 1 - HT WHISTLE: Receive halftime data (score, possession, xG, shots, cards, fouls)
         from features-sports-service via UEI event bus (HT features pipeline).
Step 2 - ML PREDICTION: Halftime model produces updated outcome probabilities incorporating
         HT state. e.g. home=0.72, draw=0.15, away=0.13 (was home=0.55 pre-game)
Step 3 - CONFIDENCE GATE: Discard outcomes where model_prob < confidence_threshold
         (soccer: 0.55, NFL: 0.60, NBA: 0.58)
Step 4 - BEST ODDS: For each remaining outcome, find best decimal odds across connected
         bookmakers from HT odds snapshots (OddsHTSnapshotDict)
Step 5 - EDGE CHECK: edge = model_prob - implied_prob; skip if edge < min_edge_threshold
         (soccer: 3%, NFL: 5%, NBA: 4%)
Step 6 - STAKE SIZING: fractional Kelly (soccer: 0.5, NFL: 0.35, NBA: 0.4), clamped to
         max_stake_fraction (soccer: 5%, NFL: 3%, NBA: 4%)
Step 7 - EMIT: SportsSignalDict with stake_fraction, edge, confidence, phase="halftime",
         model_id, bet_side, venue_type metadata

Wallet after deploy:
  - Open bets sized proportional to edge magnitude
  - Max single bet = 3-5% of bankroll depending on sport config
  - Typical HT bet = 1-3% of bankroll (smaller than pre-game due to market thinness)
  - No leverage; total exposure bounded by concurrent bet count * max_stake_fraction
  - Pre-game bets from Phase 1 may still be open when HT phase fires
```

## Instruments

| Instrument Key                   | Venue    | Type      | Role                                    |
| -------------------------------- | -------- | --------- | --------------------------------------- |
| `SPORTS:HT_ML:MODEL_EDGE`        | Multiple | Bet       | HT bets identified by halftime ML model |
| Event outcomes (h2h 2nd half)    | Betfair  | Exchange  | Best HT odds source + lay hedge         |
| Event outcomes (h2h 2nd half)    | Pinnacle | Bookmaker | Sharp HT odds source                    |
| Event outcomes (h2h 2nd half)    | Bet365   | Bookmaker | HT odds source (soccer config)          |
| Event outcomes (totals, spreads) | Betfair  | Exchange  | Match total / spread markets at HT      |
| Event outcomes (totals, spreads) | Pinnacle | Bookmaker | Match total / spread markets at HT      |

## Key Features Consumed

| Feature                        | Source Service          | SLA | Used For                                                |
| ------------------------------ | ----------------------- | --- | ------------------------------------------------------- |
| `ht_performance_goals_home`    | features-sports-service | <1m | HT score state (home goals at halftime)                 |
| `ht_performance_goals_away`    | features-sports-service | <1m | HT score state (away goals at halftime)                 |
| `ht_performance_cards`         | features-sports-service | <1m | Disciplinary state (cards issued in 1H)                 |
| `ht_performance_fouls`         | features-sports-service | <1m | Foul count (aggression proxy)                           |
| `ht_momentum_score`            | features-sports-service | <1m | Composite momentum metric from 1H performance           |
| `possession_pct`               | features-sports-service | <1m | Ball possession percentage at HT                        |
| `shots_on_target`              | features-sports-service | <1m | Shot quality indicator                                  |
| `xg_rolling`                   | features-sports-service | <1m | Expected goals at HT (actual created chances)           |
| `model_probabilities`          | features-sports-service | 5m  | Pre-game ML model output (Phase 1 input)                |
| `team_form_5` / `team_form_10` | features-sports-service | 1h  | Recent match results (pre-game context for both phases) |
| `head_to_head`                 | features-sports-service | 24h | H2H record (pre-game context)                           |
| `odds_movement`                | market-tick-data-svc    | <1s | Odds drift since market open                            |
| `odds` (HT snapshots)          | market-tick-data-svc    | <1s | Live HT odds from bookmakers (OddsHTSnapshotDict)       |

## PnL Attribution

| Component        | Settlement Type | Mechanism                                                                   |
| ---------------- | --------------- | --------------------------------------------------------------------------- |
| `edge_capture`   | EVENT_SETTLE    | Win: stake \* (odds - 1); Lose: -stake. Net positive if HT model edge real. |
| `ht_info_alpha`  | ATTRIBUTION     | Return from HT-specific information not yet priced into odds                |
| `odds_movement`  | ATTRIBUTION     | Closing line value: did 2H odds shorten after HT placement?                 |
| `model_accuracy` | ATTRIBUTION     | Decomposition of edge into HT model skill vs market inefficiency            |

**Source of truth:** `total_pnl = bankroll_current - bankroll_initial`. The primary PnL driver is the information
advantage at halftime -- the market re-forms odds during the HT break but the ML model, trained on thousands of HT
states, may price the second half more accurately than bookmakers adjusting manually. CLV measured against second-half
kickoff odds is the leading indicator. All attribution components must sum to total_pnl within 2% annualized tolerance.

## Risk Profile

| Metric               | Target  | Notes                                                                 |
| -------------------- | ------- | --------------------------------------------------------------------- |
| Target annual return | 5-18%   | Lower volume than pre-game (one window per match vs continuous)       |
| Target Sharpe ratio  | 0.6-1.2 | Higher variance per bet due to thinner HT markets                     |
| Max drawdown         | 30%     | Wider than pre-game due to smaller sample size and market illiquidity |
| Max leverage         | 1x      | No leverage; all bets from bankroll                                   |
| Capital scalability  | $100K   | Limited by HT market liquidity (thinner than pre-game)                |

## Latency Profile

| Segment               | p50 Target | p99 Target | Co-location Needed? |
| --------------------- | ---------- | ---------- | ------------------- |
| HT whistle → features | 30s        | 120s       |                     |
| Feature → ML predict  | 50ms       | 200ms      |                     |
| ML predict → signal   | 10ms       | 50ms       |                     |
| Signal → instruction  | 15ms       | 80ms       |                     |
| Instruction → fill    | 500ms      | 3000ms     |                     |
| **End-to-end**        | **~31s**   | **~123s**  | **No**              |

**Note:** The dominant latency is waiting for HT data to arrive and for odds markets to re-form after the whistle. The
~15 minute HT break provides ample time. The strategy targets placement within the first 2-5 minutes of the break when
odds are still adjusting.

## Execution Details

- **Venues:** Betfair, Pinnacle, Bet365 (soccer); Betfair, Pinnacle (NFL/NBA). Venue types configured per sport in YAML.
- **Order types:** Limit (exchanges -- Betfair); Market (bookmakers -- Pinnacle, Bet365)
- **Bet side:** BACK for value bets on all venues. Exchange venues support LAY for hedging (handled by execution layer).
- **Atomic execution required?** No -- each HT bet is independent
- **Rebalancing:** Per-event, per-phase. Pre-game and HT bets are independent positions. No carry between events.
- **Gas budget:** N/A (fiat venues only; no prediction market integration for HT currently)

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions -> exposures) -> RiskMonitor (exposures -> risk assessment) -> Strategy (risk
assessment -> rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern  | Exposure Type       | Used For                                                   |
| ------------------- | ------------------- | ---------------------------------------------------------- |
| `SPORTS:HT_ML:*`    | Stake committed     | Track total bankroll at risk across open HT bets           |
| Open bets per event | Potential payout    | Monitor max single-event exposure (pre-game + HT combined) |
| Open bets per venue | Venue concentration | Ensure no single venue holds >30% of total exposure        |

**SSOT:** `component_config.exposure_monitor.instrument_subscriptions` in strategy config. Schema:
[`ExposureMonitorConfig`](../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold              | Action on Breach                       |
| --------------- | ----------- | ---------------------- | -------------------------------------- |
| `delta`         | No          | --                     | --                                     |
| `funding`       | No          | --                     | --                                     |
| `basis`         | No          | --                     | --                                     |
| `protocol_risk` | No          | --                     | --                                     |
| `liquidity`     | Yes         | venue_max_bet (HT)     | Cap stake to HT venue limit (lower)    |
| `exposure`      | Yes         | 40% bankroll committed | Pause new signals until bets settle    |
| `model_drift`   | Yes         | Brier score > 0.28     | Halt HT betting, trigger recalibration |

**SSOT:** `component_config.risk_monitor.enabled_risk_types` in strategy config. Schema:
[`RiskMonitorConfig`](../../strategy-service/strategy_service/config.py) Formal subscription type:
[`StrategyRiskProfile`](../../unified-api-contracts/unified_api_contracts/internal/risk.py)

**Gap:** `StrategyRiskProfile` exists in `unified_api_contracts.internal` but is NOT yet wired into strategy-service
config. Risk subscriptions are currently implicit in code. Plan item `p5-risk-strategy-subscription` will create a
YAML-based subscription registry.

### Custom Strategy Risk Types

| Custom Risk            | What It Measures                                 | Evaluation Method                  | SSOT            |
| ---------------------- | ------------------------------------------------ | ---------------------------------- | --------------- |
| HT model calibration   | Predicted vs actual 2H outcome frequency         | Rolling 100-bet Brier score        | ml-service      |
| HT market thinness     | Available liquidity at HT vs pre-game            | Liquidity ratio monitoring         | execution svc   |
| HT timing risk         | Odds movement speed during HT break              | Velocity of HT odds in first 2 min | strategy config |
| Dual-phase correlation | Correlation between pre-game and HT bet outcomes | Rolling correlation coefficient    | strategy config |

**Gap:** Custom risk types are planned (plan item `p5-risk-custom-risk-types`) but not yet implemented.

## Margin & Liquidation

- **Margin model:** None (pre-funded accounts at each bookmaker/exchange)
- **Health factor threshold:** N/A
- **Liquidation penalty:** N/A
- **Monitoring:** Bankroll tracked per venue. If any single venue's balance drops below 10% of allocated capital, the
  strategy pauses betting on that venue until manual rebalance. Total bankroll reconciled daily.

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue    | Secret Name            | Testnet Available? | Notes                      |
| -------- | ---------------------- | ------------------ | -------------------------- |
| Betfair  | exec-{client}-betfair  | No                 | Exchange API + SSL certs   |
| Pinnacle | exec-{client}-pinnacle | No                 | REST API key               |
| Bet365   | exec-{client}-bet365   | No                 | REST API key (soccer only) |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Funded accounts at target bookmakers/exchanges with HT market access enabled.
2. **Secret Manager:** Per-client secrets: `exec-{client}-{venue}-{account_type}` for each venue
3. **Config:** New sport-specific YAML config entry with client-specific `confidence_threshold`, `fractional_kelly`,
   `min_edge_threshold`, and `max_stake_fraction`
4. **Position isolation:** One strategy instance per client per sport (independent bankroll tracking)
5. **Restart required?** No -- hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service           | What Changes                                | Restart?        |
| ----------------- | ------------------------------------------- | --------------- |
| strategy-service  | New HalftimeMLConfigDict in GCS (per sport) | No (hot-reload) |
| execution-service | New client venue routing rules              | No (hot-reload) |
| ml-service        | Client may use custom model variant         | No (hot-reload) |

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

- HT probability shift chart: pre-game probability vs HT-updated probability per outcome
- HT feature importance: which HT features (score, xG, possession) drove the biggest probability updates
- Phase comparison: pre-game bet outcomes vs HT bet outcomes (win rate, CLV, edge distribution)
- HT timing heatmap: signal generation time within HT break vs fill quality
- Sport-specific model calibration: reliability diagram per sport (soccer/NFL/NBA)
- HT market liquidity tracker: available volume at HT vs pre-game by venue
- Momentum score distribution: ht_momentum_score values at signal time vs bet outcome

## Testing Stage Status

| Stage        | Status  | Notes                                                          |
| ------------ | ------- | -------------------------------------------------------------- |
| MOCK         | Done    | Static HT features + odds fixtures; verified edge calc + Kelly |
| HISTORICAL   | Pending | Requires historical HT data (score/possession at HT whistle)   |
| LIVE_MOCK    | Pending | Real HT odds + ML model probs + paper execution                |
| LIVE_TESTNET | N/A     | No testnet for sports bookmakers                               |
| BATCH_REAL   | Pending | Historical replay with optimized thresholds per sport          |
| STAGING      | Pending | Paper execution with real ML predictions + real HT odds        |
| LIVE_REAL    | Pending | Production with real bookmaker accounts                        |

## References

- **Strategy implementation:** `strategy-service/strategy_service/engine/strategies/sports/halftime_ml.py`
- **ML integration:** `strategy-service/strategy_service/engine/strategies/sports/ml_sports_strategy.py`
- **Kelly sizing (shared):** `strategy-service/strategy_service/engine/strategies/sports/kelly.py`
- **Base class:** `strategy-service/strategy_service/engine/strategies/sports/sports_base.py`
- **Soccer config:** `strategy-service/strategy_service/configs/halftime_ml_soccer.yaml`
- **NFL config:** `strategy-service/strategy_service/configs/halftime_ml_nfl.yaml`
- **NBA config:** `strategy-service/strategy_service/configs/halftime_ml_nba.yaml`
- **HT features:** `features-sports-service/features_sports_service/calculators/ht_features.py`
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`
- **Features pipeline:** `features-sports-service/`

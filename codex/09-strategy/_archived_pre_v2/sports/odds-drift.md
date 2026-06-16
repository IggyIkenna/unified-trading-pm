---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# Sports Odds Drift (CLV Capture)

> **Asset class:** Sports **Strategy type:** Closing Line Value Capture **Strategy ID pattern:** `SPORTS_ODDS_DRIFT`

## Overview

Predicts where the betting line will close rather than predicting match outcomes. This is a fundamentally different
proposition from value betting: value betting says "this outcome is more likely than the odds imply," while odds drift
says "these odds will get shorter regardless of who wins." The strategy bets early when it predicts the line will move
in its favour, capturing the closing line value (CLV) differential as the market corrects.

CLV is the single best predictor of long-term sports betting profitability. A bettor who consistently beats the closing
line by 2-3% will be profitable over any reasonable sample size, even if individual bet outcomes are noisy. This
strategy operationalises CLV capture by modelling the odds movement process itself.

The signal pipeline uses features that already exist in production in features-sports-service's `odds_calculator.py`:
velocity features (`velocity_home_24h_to_6h`, `velocity_home_6h_to_1h`, `velocity_home_1h_to_0`), CLV drift predictors
(`clv_drift_home_24h`, `clv_drift_home_1h`), steam detection flags (`steam_detected_home`, `steam_magnitude_home`),
Pinnacle lead time indicators (`pinnacle_lead_time_home`), and book fragmentation metrics. The ML model to consume these
features and predict closing line movement is not yet implemented.

## Token / Position Flow

```
Start:  BANKROLL:FIAT:GBP  (100% bankroll)

Step 1 - SNAPSHOT T-24h: Capture opening odds across all bookmakers. Compute initial
         features: book_fragmentation, sharp_consensus, pinnacle_vs_market_diff.
Step 2 - VELOCITY CALC: At T-6h and T-1h, compute velocity features from odds snapshots:
         velocity_home_24h_to_6h, velocity_home_6h_to_1h. Detect steam moves.
Step 3 - DRIFT PREDICTION: ML model predicts closing odds at T-0 (kickoff) given current
         state. Output: predicted_closing_odds per outcome.
Step 4 - DRIFT EDGE: drift_edge = current_odds - predicted_closing_odds. If positive
         (current odds are longer than where they will close), back now.
Step 5 - CONFIDENCE GATE: Discard predictions where model confidence < threshold
Step 6 - STAKE SIZING: fractional Kelly based on predicted drift magnitude (larger drift
         = larger edge = larger stake)
Step 7 - EMIT: SportsSignalDict with drift_edge, predicted_closing_odds, current_odds,
         placement timing metadata

Wallet after deploy:
  - Open bets placed T-24h to T-1h before kickoff
  - Stake proportional to predicted drift magnitude
  - Max single bet = 5% of bankroll
  - Typical bet = 1-3% of bankroll (conservative due to drift prediction uncertainty)
  - No leverage; bets settle at match completion regardless of line movement
```

## Instruments

| Instrument Key               | Venue    | Type      | Role                                           |
| ---------------------------- | -------- | --------- | ---------------------------------------------- |
| `SPORTS:DRIFT:CLV_EDGE`      | Multiple | Bet       | Drift bets identified by line movement model   |
| Event outcomes (h2h, totals) | Bet365   | Bookmaker | Soft book -- slower to adjust (primary target) |
| Event outcomes (h2h, totals) | Unibet   | Bookmaker | Soft book -- slower to adjust                  |
| Event outcomes (h2h, totals) | Bwin     | Bookmaker | Soft book -- slower to adjust                  |
| Event outcomes (h2h, totals) | Betsson  | Bookmaker | Soft book -- slower to adjust                  |
| Event outcomes (h2h, totals) | Pinnacle | Bookmaker | Sharp book -- reference line (rarely bet)      |
| Event outcomes (h2h, totals) | Betfair  | Exchange  | Sharp exchange -- reference + hedge            |

## Key Features Consumed

| Feature                        | Source Service          | SLA | Used For                                                 |
| ------------------------------ | ----------------------- | --- | -------------------------------------------------------- |
| `velocity_home_24h_to_6h`      | features-sports-service | 1h  | Rate of odds change in early window (trend detection)    |
| `velocity_home_6h_to_1h`       | features-sports-service | 1h  | Rate of odds change in mid window (acceleration)         |
| `velocity_home_1h_to_0`        | features-sports-service | 15m | Final velocity before close (late steam)                 |
| `acceleration_home`            | features-sports-service | 15m | Rate of change of velocity (momentum of the move)        |
| `clv_drift_home_24h`           | features-sports-service | 1h  | Predicted CLV drift from 24h snapshot                    |
| `clv_drift_home_1h`            | features-sports-service | 15m | Predicted CLV drift from 1h snapshot                     |
| `steam_detected_home`          | features-sports-service | <1m | Binary flag: sharp money detected on home outcome        |
| `steam_magnitude_home`         | features-sports-service | <1m | Size of the steam move (larger = more conviction)        |
| `pinnacle_lead_time_home`      | features-sports-service | 1h  | Hours between Pinnacle move and market catching up       |
| `pinnacle_vs_market_diff_home` | features-sports-service | <1m | Current gap between Pinnacle and soft book odds          |
| `book_fragmentation_home`      | features-sports-service | <1m | Std dev of odds across bookmakers (high = disagreement)  |
| `sharp_consensus_home`         | features-sports-service | <1m | Agreement among sharp bookmakers on direction            |
| `market_confidence_home`       | features-sports-service | <1m | 1 - fragmentation (higher = more consensus)              |
| `odds_home_opening`            | features-sports-service | 24h | Opening odds (baseline for movement measurement)         |
| `minutes_to_kickoff`           | features-sports-service | <1m | Time remaining until close (tree-based models partition) |

## PnL Attribution

| Component          | Settlement Type | Mechanism                                                            |
| ------------------ | --------------- | -------------------------------------------------------------------- |
| `edge_capture`     | EVENT_SETTLE    | Win: stake \* (odds - 1); Lose: -stake. Net positive if CLV real.    |
| `clv_alpha`        | ATTRIBUTION     | Placement odds vs closing odds: the pure line-beating component      |
| `drift_accuracy`   | ATTRIBUTION     | How accurately the model predicted closing line movement             |
| `timing_alpha`     | ATTRIBUTION     | Return from optimal placement timing within the T-24h to T-1h window |
| `soft_book_spread` | ATTRIBUTION     | Extra edge from soft books being slower to adjust than sharp books   |

**Source of truth:** `total_pnl = bankroll_current - bankroll_initial`. The core thesis is that consistently beating the
closing line generates profit over large samples. CLV alpha is the primary attribution component. Even bets that lose
can demonstrate positive CLV (placed at better odds than closing), confirming the strategy is working. All attribution
components must sum to total_pnl within 2% annualized tolerance.

## Risk Profile

| Metric               | Target  | Notes                                                                    |
| -------------------- | ------- | ------------------------------------------------------------------------ |
| Target annual return | 5-15%   | Dependent on soft book access and account longevity                      |
| Target Sharpe ratio  | 1.0-2.0 | Higher than value betting (CLV is more consistent than outcome variance) |
| Max drawdown         | 20%     | Lower variance than outcome-based strategies                             |
| Max leverage         | 1x      | No leverage; all bets from bankroll                                      |
| Capital scalability  | $150K   | Limited by soft book stake acceptance before account restriction         |

## Latency Profile

| Segment                 | p50 Target | p99 Target | Co-location Needed? |
| ----------------------- | ---------- | ---------- | ------------------- |
| Odds snapshot → feature | 1s         | 5s         |                     |
| Feature → drift model   | 20ms       | 100ms      |                     |
| Drift model → signal    | 10ms       | 50ms       |                     |
| Signal → instruction    | 15ms       | 80ms       |                     |
| Instruction → fill      | 300ms      | 2000ms     |                     |
| **End-to-end**          | **~1.3s**  | **~2.2s**  | **No**              |

**Note:** Speed matters more here than in value betting. Steam moves are detected and acted on within seconds by sharp
bettors. The strategy must place before soft books adjust. T-1h velocity features are most time-sensitive.

## Execution Details

- **Venues:** Soft bookmakers primarily (Bet365, Unibet, Bwin, Betsson) -- these adjust slower than sharp books.
  Pinnacle and Betfair used as reference lines, rarely as bet targets.
- **Order types:** Market (bookmakers); Limit (exchanges for hedge)
- **Atomic execution required?** No -- each drift bet is independent
- **Rebalancing:** Continuous within the T-24h to T-1h window. Multiple placements possible as drift unfolds.
- **Gas budget:** N/A (fiat venues only)

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions -> exposures) -> RiskMonitor (exposures -> risk assessment) -> Strategy (risk
assessment -> rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern      | Exposure Type       | Used For                                            |
| ----------------------- | ------------------- | --------------------------------------------------- |
| `SPORTS:DRIFT:*`        | Stake committed     | Track total bankroll at risk across open drift bets |
| Open bets per event     | Potential payout    | Monitor max single-event exposure                   |
| Open bets per bookmaker | Venue concentration | Ensure no single soft book holds >25% of exposure   |

**SSOT:** `component_config.exposure_monitor.instrument_subscriptions` in strategy config. Schema:
[`ExposureMonitorConfig`](../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold              | Action on Breach                    |
| --------------- | ----------- | ---------------------- | ----------------------------------- |
| `delta`         | No          | --                     | --                                  |
| `funding`       | No          | --                     | --                                  |
| `basis`         | No          | --                     | --                                  |
| `protocol_risk` | No          | --                     | --                                  |
| `liquidity`     | Yes         | venue_max_bet          | Cap stake to venue limit            |
| `exposure`      | Yes         | 35% bankroll committed | Pause new signals until bets settle |
| `model_drift`   | Yes         | CLV < 0 over 100 bets  | Halt drift betting, retrain model   |

**SSOT:** `component_config.risk_monitor.enabled_risk_types` in strategy config. Schema:
[`RiskMonitorConfig`](../../strategy-service/strategy_service/config.py) Formal subscription type:
[`StrategyRiskProfile`](../../unified-api-contracts/unified_api_contracts/internal/risk.py)

**Gap:** `StrategyRiskProfile` exists in `unified_api_contracts.internal` but is NOT yet wired into strategy-service
config. Risk subscriptions are currently implicit in code. Plan item `p5-risk-strategy-subscription` will create a
YAML-based subscription registry.

### Custom Strategy Risk Types

| Custom Risk              | What It Measures                                   | Evaluation Method                 | SSOT            |
| ------------------------ | -------------------------------------------------- | --------------------------------- | --------------- |
| Account restriction risk | Soft books reducing accepted stakes over time      | Fill rate and accepted size trend | execution svc   |
| Drift model calibration  | Predicted vs actual closing line accuracy          | MAE of predicted closing odds     | ml-service      |
| Steam false positive     | Steam detection flags that led to no line movement | False positive rate over 50 bets  | strategy config |
| Sharp-soft convergence   | Time for soft books to match Pinnacle moves        | Rolling median convergence time   | strategy config |

**Gap:** Custom risk types are planned (plan item `p5-risk-custom-risk-types`) but not yet implemented.

## Margin & Liquidation

- **Margin model:** None (pre-funded accounts at each bookmaker/exchange)
- **Health factor threshold:** N/A
- **Liquidation penalty:** N/A
- **Monitoring:** Bankroll tracked per venue. Soft book balances monitored for stake acceptance degradation (a leading
  indicator of account restriction). If accepted stake drops below 50% of requested stake at any venue, flag for manual
  review and consider rotating to alternative soft books.

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue    | Secret Name            | Testnet Available? | Notes                       |
| -------- | ---------------------- | ------------------ | --------------------------- |
| Bet365   | exec-{client}-bet365   | No                 | REST API key (primary soft) |
| Unibet   | exec-{client}-unibet   | No                 | REST API key                |
| Bwin     | exec-{client}-bwin     | No                 | REST API key                |
| Betsson  | exec-{client}-betsson  | No                 | REST API key                |
| Pinnacle | exec-{client}-pinnacle | No                 | REST API key (reference)    |
| Betfair  | exec-{client}-betfair  | No                 | Exchange API + SSL certs    |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Funded accounts at multiple soft bookmakers. Account age and history matter -- new accounts
   are restricted faster. Recommend aged accounts where possible.
2. **Secret Manager:** Per-client secrets: `exec-{client}-{venue}-{account_type}` for each venue
3. **Config:** New strategy config with client-specific drift thresholds, venue rotation schedule, and
   max_stake_fraction sized to avoid triggering bookmaker account review
4. **Position isolation:** One strategy instance per client (independent bankroll and venue rotation)
5. **Restart required?** No -- hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service           | What Changes                        | Restart?        |
| ----------------- | ----------------------------------- | --------------- |
| strategy-service  | New drift strategy config in GCS    | No (hot-reload) |
| execution-service | New client venue routing + rotation | No (hot-reload) |
| ml-service        | Shared drift model (no per-client)  | N/A             |

## UI Visualisation

### Standard views (already in plans)

- PnL waterfall (risk matrix plan Stream D)
- Margin health time series (Stream D)
- Position breakdown

### Strategy-specific views (extensions)

- CLV time series: rolling 50-bet average CLV (the single most important metric)
- Drift prediction accuracy: predicted closing odds vs actual closing odds scatter plot
- Velocity waterfall: odds velocity at T-24h, T-6h, T-1h showing momentum build-up
- Steam detection timeline: when steam was detected vs when line actually moved
- Pinnacle lead time histogram: distribution of hours between Pinnacle move and market follow
- Soft book acceptance tracker: accepted stake / requested stake per venue over time (account health)
- Book fragmentation heatmap: fragmentation by league, market type, and time-to-kickoff

## Testing Stage Status

| Stage        | Status  | Notes                                                             |
| ------------ | ------- | ----------------------------------------------------------------- |
| MOCK         | Pending | Features exist in production; strategy engine not yet implemented |
| HISTORICAL   | Pending | Requires closing line data (available in MTDS odds snapshots)     |
| LIVE_MOCK    | Pending | Real velocity features + paper drift model                        |
| LIVE_TESTNET | N/A     | No testnet for sports bookmakers                                  |
| BATCH_REAL   | Pending | Historical CLV backtest with existing velocity features           |
| STAGING      | Pending | Paper execution with real drift predictions + real odds           |
| LIVE_REAL    | Pending | Production with real soft book accounts                           |

## References

- **Strategy implementation:** TBD -- strategy engine class not yet written. Will follow `HalftimeMLStrategy` pattern in
  `strategy-service/strategy_service/engine/strategies/sports/`
- **Feature pipeline (existing):** `features-sports-service/features_sports_service/calculators/odds_calculator.py` --
  velocity, CLV drift, steam detection, book fragmentation features are all in production
- **Kelly sizing (shared):** `strategy-service/strategy_service/engine/strategies/sports/kelly.py`
- **Base class:** `strategy-service/strategy_service/engine/strategies/sports/sports_base.py`
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`
- **Features pipeline:** `features-sports-service/`

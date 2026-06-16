---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# Sports Pre-Game ML

> **Asset class:** Sports **Strategy type:** ML Pre-Game Prediction **Strategy ID pattern:** `SPORTS_ML_PREGAME`

## Overview

Uses ML model probability predictions computed before kickoff to identify value bets in sports markets. The strategy
compares model-estimated outcome probabilities against bookmaker implied probabilities and emits a signal when the edge
exceeds a configurable minimum threshold. Stake sizing uses fractional Kelly criterion for bankroll-optimal growth.
Distinct from halftime ML (`SPORTS_HALFTIME_ML`) which uses a different model, different features (in-play xG,
possession, score state), and fires at the HT whistle. Pre-game ML fires once per event before kickoff using pre-match
features only.

The strategy is implemented across two classes: `MLSportsStrategy` (standalone pre-game ML with
`strategy_type="SPORTS_ML"`) and `HalftimeMLStrategy` in `pre_game` phase (with `strategy_type="SPORTS_HALFTIME_ML"`,
phase metadata `"pre_game"`). Both use the same core logic: confidence gate, edge check, Kelly sizing, best-odds
selection. The `HalftimeMLStrategy` additionally supports venue routing with `BetSide` (BACK/LAY) and per-league model
variants.

## Token / Position Flow

```
Start:  BANKROLL:FIAT:GBP  (100% bankroll)

Step 1 - MODEL PROB: Receive ML model probabilities per outcome from features-sports-service
         via UEI event bus (PredictionEvent). e.g. home=0.58, draw=0.24, away=0.18
         Model IDs: fss_soccer_pregame_xgb_v2, fss_nfl_pregame_xgb_v1, fss_nba_pregame_xgb_v1
         Per-league variants: SPORTS_FOOTBALL_BUNDESLIGA_direction_XGBOOST_24h_V1
Step 2 - CONFIDENCE GATE: Discard outcomes where model_prob < confidence_threshold
         Soccer: 0.55, NFL: 0.60, NBA: 0.58
Step 3 - BEST ODDS: For each remaining outcome, find best decimal odds across all connected bookmakers
         via find_best_odds_by_outcome() from SportsBaseStrategy
Step 4 - ODDS GATE: Reject extreme longshots where decimal_odds > max_odds (default 8.0)
Step 5 - EDGE CHECK: edge = model_prob - implied_prob; skip if edge < min_edge_threshold
         Soccer: 3%, NFL: 5%, NBA: 4%
Step 6 - KELLY SIZING: compute_kelly_fraction(model_prob, decimal_odds, fractional_kelly, max_stake)
         Soccer: 0.5 Kelly, NFL: 0.35 Kelly, NBA: 0.4 Kelly
         Max stake: soccer 5%, NFL 3%, NBA 4% of bankroll
Step 7 - VENUE ROUTING: Resolve BetSide (BACK for bookmakers, BACK/LAY for exchanges)
         via _resolve_bet_side() and _get_venue_type()
Step 8 - EMIT: SportsSignalDict with stake_fraction, edge, confidence, model_id, phase="pre_game",
         bet_side, venue_type, kelly_fraction_raw, kelly_fraction_adjusted

Wallet after deploy:
  - Open bets sized by fractional Kelly criterion
  - Max single bet = 5% of bankroll (soccer), 3% (NFL), 4% (NBA)
  - Typical bet = 1-3% of bankroll for edges in the 3-8% range
  - No leverage; total exposure bounded by concurrent bet count * max_stake_fraction
  - Best-edge outcome selected when multiple outcomes qualify (HalftimeMLStrategy path)
```

## Instruments

| Instrument Key               | Venue     | Type      | Role                                  |
| ---------------------------- | --------- | --------- | ------------------------------------- |
| `SPORTS:ML:FSS_PREGAME_*`    | Multiple  | Bet       | Pre-game value bets identified by ML  |
| Event outcomes (h2h, totals) | Betfair   | Exchange  | Best odds source + BACK/LAY execution |
| Event outcomes (h2h, totals) | Smarkets  | Exchange  | Best odds source + BACK execution     |
| Event outcomes (h2h, totals) | Matchbook | Exchange  | Best odds source + BACK execution     |
| Event outcomes (h2h, totals) | Pinnacle  | Bookmaker | Sharp bookmaker odds source + BACK    |
| Event outcomes (h2h, totals) | Bet365    | Bookmaker | Soft bookmaker odds source + BACK     |

## Key Features Consumed

### Soccer (fss_soccer_pregame_xgb_v2)

| Feature           | Source Service          | SLA | Used For                                     |
| ----------------- | ----------------------- | --- | -------------------------------------------- |
| `team_form_5`     | features-sports-service | 1h  | Recent 5-match results and form metrics      |
| `head_to_head`    | features-sports-service | 24h | Historical head-to-head record between teams |
| `xg_rolling`      | features-sports-service | 1h  | Rolling expected goals metric                |
| `odds_movement`   | market-tick-data-svc    | <1s | Odds drift detection / market sentiment      |
| `possession_pct`  | features-sports-service | 1h  | Average possession percentage                |
| `shots_on_target` | features-sports-service | 1h  | Average shots on target per match            |

### NFL (fss_nfl_pregame_xgb_v1)

| Feature             | Source Service          | SLA | Used For                           |
| ------------------- | ----------------------- | --- | ---------------------------------- |
| `team_power_rating` | features-sports-service | 24h | Composite team strength rating     |
| `yards_per_play`    | features-sports-service | 24h | Offensive and defensive efficiency |

### NBA (fss_nba_pregame_xgb_v1)

| Feature        | Source Service          | SLA | Used For                        |
| -------------- | ----------------------- | --- | ------------------------------- |
| `team_form_10` | features-sports-service | 24h | Recent 10-game results and form |
| `pace_rating`  | features-sports-service | 24h | Team pace for totals prediction |

## PnL Attribution

| Component        | Settlement Type | Mechanism                                                          |
| ---------------- | --------------- | ------------------------------------------------------------------ |
| `edge_capture`   | EVENT_SETTLE    | Win: stake \* (odds - 1); Lose: -stake. Net positive if edge real. |
| `odds_movement`  | ATTRIBUTION     | Closing line value: did odds shorten after placement?              |
| `timing_alpha`   | ATTRIBUTION     | Return from placing before odds adjust to true probability         |
| `model_accuracy` | ATTRIBUTION     | Decomposition of edge into model skill vs market inefficiency      |

**Source of truth:** `total_pnl = bankroll_current - bankroll_initial`. Edge capture is the primary PnL driver: over a
large sample of bets, if the model's probability estimates are well-calibrated, the strategy earns
`sum(edge_i * stake_i)` in expectation. Closing line value (CLV) -- the difference between placement odds and closing
odds -- is the leading indicator of long-term profitability. Kelly sizing ensures bankroll growth is optimal given the
model's edge and confidence. All attribution components must sum to total_pnl within 2% annualized tolerance.

## Risk Profile

| Metric               | Target  | Notes                                                         |
| -------------------- | ------- | ------------------------------------------------------------- |
| Target annual return | 8-25%   | Depends on model accuracy and bet volume (500+ bets/month)    |
| Target Sharpe ratio  | 0.8-1.5 | Lower than arb due to outcome variance; improves with volume  |
| Max drawdown         | 25%     | Expected with edge-based betting; reduced by fractional Kelly |
| Max leverage         | 1x      | No leverage; all bets from bankroll                           |
| Capital scalability  | $200K   | Limited by bookmaker stake limits and account restricting     |

## Latency Profile

| Segment                | p50 Target | p99 Target | Co-location Needed? |
| ---------------------- | ---------- | ---------- | ------------------- |
| Market data -> feature | 200ms      | 1000ms     |                     |
| Feature -> signal      | 10ms       | 50ms       |                     |
| Signal -> instruction  | 15ms       | 80ms       |                     |
| Instruction -> fill    | 300ms      | 2000ms     |                     |
| **End-to-end**         | **525ms**  | **3130ms** | **No**              |

## Execution Details

- **Venues:** Betfair (exchange, BACK/LAY), Pinnacle (bookmaker, BACK only), Bet365 (bookmaker, BACK only), Smarkets
  (exchange), Matchbook (exchange). Configurable per strategy instance via `venues` list in YAML config.
- **Order types:** Market (bookmakers), Limit (exchanges -- Betfair, Smarkets)
- **Atomic execution required?** No -- each value bet is independent; partial execution is acceptable
- **Venue routing:** Exchange venues support both BACK and LAY via `BetSide` enum from `unified_api_contracts.sports`.
  For pre-game value bets, default is BACK (backing the mispriced outcome). LAY used for hedging/closing by execution
  layer.
- **Rebalancing:** Per-event; no carry between events. Model probabilities computed pre-match only (distinct from
  halftime ML which has a second prediction window at HT whistle).
- **Gas budget:** N/A for fiat venues.

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions -> exposures) -> RiskMonitor (exposures -> risk assessment) -> Strategy (risk
assessment -> rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern      | Exposure Type       | Used For                                            |
| ----------------------- | ------------------- | --------------------------------------------------- |
| `SPORTS:ML:PREGAME:*`   | Stake committed     | Track total bankroll at risk across open bets       |
| Open bets per event     | Potential payout    | Monitor max single-event exposure                   |
| Open bets per bookmaker | Venue concentration | Ensure no single venue holds >30% of total exposure |

**SSOT:** `component_config.exposure_monitor.instrument_subscriptions` in strategy config. Schema:
[`ExposureMonitorConfig`](../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold              | Action on Breach                          |
| --------------- | ----------- | ---------------------- | ----------------------------------------- |
| `delta`         | No          | --                     | --                                        |
| `funding`       | No          | --                     | --                                        |
| `basis`         | No          | --                     | --                                        |
| `protocol_risk` | No          | --                     | --                                        |
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

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue     | Secret Name             | Testnet Available? | Notes                    |
| --------- | ----------------------- | ------------------ | ------------------------ |
| Betfair   | exec-{client}-betfair   | No                 | Exchange API + SSL certs |
| Smarkets  | exec-{client}-smarkets  | No                 | REST API key             |
| Matchbook | exec-{client}-matchbook | No                 | REST API key             |
| Pinnacle  | exec-{client}-pinnacle  | No                 | REST API key             |
| Bet365    | exec-{client}-bet365    | No                 | REST API key             |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Funded accounts at target bookmakers/exchanges. For exchanges, funded wallet with sufficient
   margin for BACK orders.
2. **Secret Manager:** Per-client secrets: `exec-{client}-{venue}-{account_type}` for each venue
3. **Config:** New strategy config entry with client-specific `confidence_threshold`, `fractional_kelly`,
   `min_edge_threshold`, `max_stake_fraction`, and `supported_markets`
4. **ML model:** Client may use default model or a custom variant (per-league models supported via
   `generate_model_id(league_id=...)`)
5. **Position isolation:** One strategy instance per client (independent bankroll tracking; different venues may have
   different balance/limit profiles)
6. **Restart required?** No -- hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service           | What Changes                        | Restart?        |
| ----------------- | ----------------------------------- | --------------- |
| strategy-service  | New strategy config YAML in GCS     | No (hot-reload) |
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
- Per-league model performance comparison: edge capture by league variant

## Sport-Specific Configuration

| Parameter              | Soccer                    | NFL                    | NBA                    |
| ---------------------- | ------------------------- | ---------------------- | ---------------------- |
| `confidence_threshold` | 0.55                      | 0.60                   | 0.58                   |
| `min_edge_threshold`   | 3%                        | 5%                     | 4%                     |
| `fractional_kelly`     | 0.5                       | 0.35                   | 0.4                    |
| `max_stake_fraction`   | 5%                        | 3%                     | 4%                     |
| `supported_markets`    | h2h, totals, btts         | h2h, totals, spreads   | h2h, totals, spreads   |
| `model_id`             | fss_soccer_pregame_xgb_v2 | fss_nfl_pregame_xgb_v1 | fss_nba_pregame_xgb_v1 |

Per-league model variants are supported via the naming convention `SPORTS_FOOTBALL_{LEAGUE}_{target}_{MODEL}_{TF}_V{N}`
(e.g. `SPORTS_FOOTBALL_BUNDESLIGA_direction_XGBOOST_24h_V1`).

## Testing Stage Status

| Stage        | Status  | Notes                                                  |
| ------------ | ------- | ------------------------------------------------------ |
| MOCK         | Done    | Static model probs + odds fixtures; verified edge calc |
| HISTORICAL   | Pending | Backtest with historical model probs + odds            |
| LIVE_MOCK    | Pending | Real odds + ML model probs + paper execution           |
| LIVE_TESTNET | N/A     | No testnet for sports bookmakers                       |
| BATCH_REAL   | Pending | Historical replay with optimized thresholds            |
| STAGING      | Pending | Paper execution with real ML predictions + real odds   |
| LIVE_REAL    | Pending | Production with real bookmaker accounts                |

## References

- **Strategy implementation (standalone):**
  `strategy-service/strategy_service/engine/strategies/sports/ml_sports_strategy.py`
- **Strategy implementation (halftime dual-phase):**
  `strategy-service/strategy_service/engine/strategies/sports/halftime_ml.py`
- **Config YAML:** `strategy-service/strategy_service/configs/halftime_ml_soccer.yaml`
- **Kelly sizing (shared):** `strategy-service/strategy_service/engine/strategies/sports/kelly.py`
- **Base class:** `strategy-service/strategy_service/engine/strategies/sports/sports_base.py`
- **BetSide enum:** `unified-api-contracts/unified_api_contracts/sports.py`
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`
- **Features pipeline:** `features-sports-service/`

---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# Sports First Half Prediction

> **Asset class:** Sports **Strategy type:** First Half ML Prediction **Strategy ID pattern:** `SPORTS_FIRST_HALF_ML`

## Overview

Predicts first-half outcomes specifically (not full match) using a dedicated ML model trained on first-half result data.
The key insight is capital efficiency: the same bankroll is used twice per match day. A first-half bet settles at the
halftime whistle, freeing capital immediately for a second-half bet via the halftime-ml strategy. A $100K bankroll
effectively does $200K worth of work per match day.

First-half dynamics differ meaningfully from full-match dynamics. Teams start conservatively (especially in knockout
tournaments), tactical fouling patterns differ in the opening 45 minutes, early red cards have an outsized impact on
first-half result vs full-match result, and scoring rates are not uniformly distributed across halves. A model trained
on full-match outcomes and applied to first-half markets would be mis-specified. This strategy trains on first-half
outcomes directly.

The strategy is designed to pair with halftime-ml: Phase 1 (this strategy) places 1H bets pre-game, they settle at HT,
then Phase 2 (halftime-ml) places 2H bets during the HT break using the freed capital. The two strategies share bankroll
management but operate on different markets with different models.

## Token / Position Flow

```
Start:  BANKROLL:FIAT:GBP  (100% bankroll, shared with halftime-ml)

Step 1 - MODEL PROB: Receive 1H-specific ML model probabilities per outcome from
         features-sports-service. e.g. 1H_home=0.42, 1H_draw=0.35, 1H_away=0.23
         (note: draws are much more common in first halves than full matches)
Step 2 - CONFIDENCE GATE: Discard outcomes where model_prob < model_confidence_threshold
Step 3 - BEST ODDS: For each remaining outcome, find best decimal odds across bookmakers
         offering 1H-specific markets
Step 4 - ODDS GATE: Reject extreme longshots where decimal_odds > max_odds
Step 5 - EDGE CHECK: edge = model_prob - implied_prob; skip if edge < min_edge_threshold
Step 6 - STAKE SIZING: fractional Kelly, but sized considering the two-phase capital plan.
         max_stake_fraction is reduced vs standalone strategies to reserve capital for
         Phase 2 (halftime-ml). e.g. 3% max instead of 5%.
Step 7 - EMIT: SportsSignalDict with stake_fraction, edge, confidence, market_type="1H",
         capital_phase="phase_1" metadata

Wallet after deploy:
  - 1H bets open pre-game, settle at HT whistle (~45-50 min)
  - Max single bet = 3% of bankroll (lower to preserve Phase 2 capital)
  - Typical bet = 1-2% of bankroll
  - No leverage; total 1H exposure + expected 2H exposure < bankroll
  - Capital freed at HT whistle flows to halftime-ml strategy
```

## Instruments

| Instrument Key                 | Venue    | Type      | Role                                      |
| ------------------------------ | -------- | --------- | ----------------------------------------- |
| `SPORTS:1H_ML:MODEL_EDGE`      | Multiple | Bet       | 1H bets identified by first-half ML model |
| 1H result (1X2)                | Betfair  | Exchange  | First-half 1X2 market                     |
| 1H result (1X2)                | Pinnacle | Bookmaker | First-half 1X2 market (where available)   |
| 1H over/under (0.5, 1.5 goals) | Betfair  | Exchange  | First-half totals market                  |
| 1H over/under (0.5, 1.5 goals) | Pinnacle | Bookmaker | First-half totals market                  |
| 1H BTTS                        | Betfair  | Exchange  | First-half both teams to score            |

## Key Features Consumed

| Feature                   | Source Service          | SLA | Used For                                                       |
| ------------------------- | ----------------------- | --- | -------------------------------------------------------------- |
| `model_probabilities_1h`  | features-sports-service | 5m  | ML-estimated true probability per 1H outcome                   |
| `prediction_confidence`   | features-sports-service | 5m  | Model confidence score for gating low-quality predictions      |
| `team_form_features`      | features-sports-service | 1h  | Recent match results, xG (re-weighted for 1H performance)      |
| `h2h_history`             | features-sports-service | 24h | Head-to-head record (1H-specific stats where available)        |
| `first_half_scoring_rate` | features-sports-service | 1h  | Historical 1H goals per match for each team                    |
| `early_goal_tendency`     | features-sports-service | 1h  | Team propensity to score/concede in first 15 minutes           |
| `tactical_profile`        | features-sports-service | 24h | Team's typical 1H approach (conservative start vs press early) |
| `red_card_rate_1h`        | features-sports-service | 24h | Historical 1H red card frequency by team/league                |
| `odds` (1H markets)       | market-tick-data-svc    | <1s | Implied probability for 1H-specific markets                    |
| `market_movement`         | market-tick-data-svc    | <1s | 1H odds drift detection                                        |

## PnL Attribution

| Component            | Settlement Type | Mechanism                                                         |
| -------------------- | --------------- | ----------------------------------------------------------------- |
| `edge_capture`       | EVENT_SETTLE    | Win: stake \* (odds - 1); Lose: -stake. Settles at HT whistle.    |
| `capital_efficiency` | ATTRIBUTION     | Return uplift from deploying freed capital into Phase 2 (HT bets) |
| `odds_movement`      | ATTRIBUTION     | CLV: did 1H odds shorten between placement and kickoff?           |
| `model_accuracy`     | ATTRIBUTION     | Decomposition of edge into 1H model skill vs market inefficiency  |

**Source of truth:** `total_pnl = bankroll_current - bankroll_initial`. The combined PnL of this strategy plus
halftime-ml must be evaluated together to measure the capital efficiency thesis. A 1H bet that breaks even but frees
capital for a profitable 2H bet has contributed to total system return. Individual 1H edge capture is the primary
component; capital_efficiency is measured as the incremental return from the two-phase approach vs a single-phase
approach using the same bankroll. All attribution components must sum to total_pnl within 2% annualized tolerance.

## Risk Profile

| Metric               | Target  | Notes                                                               |
| -------------------- | ------- | ------------------------------------------------------------------- |
| Target annual return | 4-12%   | Lower per-strategy return; combined with HT strategy targets 10-25% |
| Target Sharpe ratio  | 0.5-1.0 | Higher draw rate in 1H increases variance; improves with volume     |
| Max drawdown         | 20%     | Controlled by lower max_stake_fraction (3% vs 5%)                   |
| Max leverage         | 1x      | No leverage; all bets from bankroll                                 |
| Capital scalability  | $100K   | Limited by 1H market liquidity (thinner than full-match markets)    |

## Latency Profile

| Segment                | p50 Target | p99 Target | Co-location Needed? |
| ---------------------- | ---------- | ---------- | ------------------- |
| Market data -> feature | 200ms      | 1000ms     |                     |
| Feature -> signal      | 10ms       | 50ms       |                     |
| Signal -> instruction  | 15ms       | 80ms       |                     |
| Instruction -> fill    | 300ms      | 2000ms     |                     |
| **End-to-end**         | **525ms**  | **3130ms** | **No**              |

## Execution Details

- **Venues:** Betfair (1H markets), Pinnacle (1H markets where available). 1H market availability varies by league and
  bookmaker -- EPL and Champions League have deepest 1H markets.
- **Order types:** Limit (Betfair exchange); Market (Pinnacle bookmaker)
- **Atomic execution required?** No -- each 1H bet is independent
- **Rebalancing:** Per-event. 1H bets placed pre-game, settle at HT. No in-play adjustment of 1H positions.
- **Capital coordination:** Strategy must communicate expected 1H exposure to halftime-ml strategy so Phase 2 can plan
  capital allocation before 1H bets settle. This is via shared bankroll state in strategy-service.
- **Gas budget:** N/A (fiat venues only)

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions -> exposures) -> RiskMonitor (exposures -> risk assessment) -> Strategy (risk
assessment -> rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern  | Exposure Type       | Used For                                            |
| ------------------- | ------------------- | --------------------------------------------------- |
| `SPORTS:1H_ML:*`    | Stake committed     | Track total bankroll at risk across open 1H bets    |
| Open bets per event | Potential payout    | Monitor max single-event exposure                   |
| Open bets per venue | Venue concentration | Ensure no single venue holds >30% of total exposure |
| Combined 1H + HT    | Phase exposure      | Total cross-phase exposure must not exceed bankroll |

**SSOT:** `component_config.exposure_monitor.instrument_subscriptions` in strategy config. Schema:
[`ExposureMonitorConfig`](../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold              | Action on Breach                          |
| --------------- | ----------- | ---------------------- | ----------------------------------------- |
| `delta`         | No          | --                     | --                                        |
| `funding`       | No          | --                     | --                                        |
| `basis`         | No          | --                     | --                                        |
| `protocol_risk` | No          | --                     | --                                        |
| `liquidity`     | Yes         | venue_max_bet (1H)     | Cap stake to 1H venue limit (lower)       |
| `exposure`      | Yes         | 30% bankroll committed | Lower than standalone to preserve Phase 2 |
| `model_drift`   | Yes         | Brier score > 0.30     | Halt 1H betting, trigger recalibration    |

**SSOT:** `component_config.risk_monitor.enabled_risk_types` in strategy config. Schema:
[`RiskMonitorConfig`](../../strategy-service/strategy_service/config.py) Formal subscription type:
[`StrategyRiskProfile`](../../unified-api-contracts/unified_api_contracts/internal/risk.py)

**Gap:** `StrategyRiskProfile` exists in `unified_api_contracts.internal` but is NOT yet wired into strategy-service
config. Risk subscriptions are currently implicit in code. Plan item `p5-risk-strategy-subscription` will create a
YAML-based subscription registry.

### Custom Strategy Risk Types

| Custom Risk             | What It Measures                                     | Evaluation Method                   | SSOT            |
| ----------------------- | ---------------------------------------------------- | ----------------------------------- | --------------- |
| 1H model calibration    | Predicted vs actual 1H outcome frequency             | Rolling 200-bet Brier score         | ml-service      |
| 1H market availability  | Whether 1H markets exist for target fixtures         | Percentage of fixtures with 1H odds | strategy config |
| 1H injury time risk     | Goals scored in 1H injury time causing late swings   | Rolling rate of 45+ minute 1H goals | strategy config |
| Phase coordination risk | 1H bets not settling in time for Phase 2 placement   | HT whistle to settlement latency    | execution svc   |
| Capital overcommit      | 1H exposure too high to fund expected 2H opportunity | 1H committed / bankroll ratio       | strategy config |

**Gap:** Custom risk types are planned (plan item `p5-risk-custom-risk-types`) but not yet implemented.

## Margin & Liquidation

- **Margin model:** None (pre-funded accounts at each bookmaker/exchange)
- **Health factor threshold:** N/A
- **Liquidation penalty:** N/A
- **Monitoring:** Bankroll tracked per venue. Capital freed at HT settlement is reconciled before Phase 2 deployment. If
  1H settlement is delayed (rare: dispute, void market), the halftime-ml strategy must reduce Phase 2 sizing
  accordingly. Total bankroll reconciled daily.

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue    | Secret Name            | Testnet Available? | Notes                         |
| -------- | ---------------------- | ------------------ | ----------------------------- |
| Betfair  | exec-{client}-betfair  | No                 | Exchange API + SSL certs      |
| Pinnacle | exec-{client}-pinnacle | No                 | REST API key (1H where avail) |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Funded accounts at venues offering 1H markets. Verify 1H market availability for target
   leagues before onboarding.
2. **Secret Manager:** Per-client secrets: `exec-{client}-{venue}-{account_type}` for each venue
3. **Config:** New strategy config with client-specific thresholds. Must coordinate with halftime-ml config for the same
   client to ensure combined exposure limits are consistent.
4. **Position isolation:** One strategy instance per client. Bankroll state shared with halftime-ml instance for the
   same client (capital coordination).
5. **Restart required?** No -- hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service           | What Changes                                     | Restart?        |
| ----------------- | ------------------------------------------------ | --------------- |
| strategy-service  | New 1H strategy config + linked HT config in GCS | No (hot-reload) |
| execution-service | New client venue routing rules                   | No (hot-reload) |
| ml-service        | Client may use custom 1H model variant           | No (hot-reload) |

## UI Visualisation

### Standard views (already in plans)

- PnL waterfall (risk matrix plan Stream D)
- Margin health time series (Stream D)
- Position breakdown

### Strategy-specific views (extensions)

- Two-phase capital flow: bankroll allocation timeline showing 1H commit -> HT settle -> 2H commit cycle
- 1H vs full-match model comparison: probability estimates for same fixtures, showing divergence
- Capital efficiency metric: combined 1H+2H return vs hypothetical single-phase return with same bankroll
- 1H draw rate tracker: actual 1H draw frequency vs model predicted (draws are the key risk in 1H markets)
- 1H market depth comparison: available liquidity in 1H markets vs full-match markets by league
- Settlement latency tracker: time from HT whistle to capital availability for Phase 2
- 1H injury time goal impact: outcomes changed by goals scored after 45th minute

## Testing Stage Status

| Stage        | Status  | Notes                                                                 |
| ------------ | ------- | --------------------------------------------------------------------- |
| MOCK         | Pending | Requires 1H-specific mock data and model fixtures                     |
| HISTORICAL   | Pending | Requires historical 1H result data (available from MTDS fixture data) |
| LIVE_MOCK    | Pending | Real 1H odds + paper 1H model                                         |
| LIVE_TESTNET | N/A     | No testnet for sports bookmakers                                      |
| BATCH_REAL   | Pending | Historical 1H replay with 1H-trained model                            |
| STAGING      | Pending | Paper execution with real 1H ML predictions + real 1H odds            |
| LIVE_REAL    | Pending | Production with real bookmaker accounts (1H markets)                  |

## References

- **Strategy implementation:** TBD -- strategy engine class not yet written. Will extend `SportsBaseStrategy` in
  `strategy-service/strategy_service/engine/strategies/sports/`. Expected to follow `HalftimeMLStrategy` pattern with
  1H-specific model selection and capital coordination hooks.
- **Paired strategy:** `strategy-service/strategy_service/engine/strategies/sports/halftime_ml.py` -- Phase 2 of the
  two-phase capital deployment. This strategy (Phase 1) must coordinate bankroll state with halftime-ml.
- **1H model training:** TBD -- requires 1H-outcome-specific training data. Model will be trained via ml-service using
  features-sports-service 1H features once the training pipeline is extended for half-specific targets.
- **Kelly sizing (shared):** `strategy-service/strategy_service/engine/strategies/sports/kelly.py`
- **Base class:** `strategy-service/strategy_service/engine/strategies/sports/sports_base.py`
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`
- **Features pipeline:** `features-sports-service/`

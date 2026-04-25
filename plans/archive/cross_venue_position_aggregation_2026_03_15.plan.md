---
name: cross-venue-position-aggregation
overview: |
  Institutional-grade cross-venue position aggregation engine with full asset-class coverage.
  Adds AggregatedPosition (with asset_group, instrument_type, strategy_id, margin_type,
  underlying, expiry), PortfolioView (with Greeks, PnL attribution, risk groups),
  DeFi schemas (lending + LP + staking), and SportsArbPosition to UAC/UIC.
  Builds CrossVenueAggregator (composing UIC CrossAssetPortfolioAggregator),
  GreeksAggregator, PnLAttributionAggregator, and RiskGroupAggregator with configurable
  correlation matrix in PBMS. Wires risk, strategy, execution, and ML as consumers.
  Covers all 5 asset classes (CRYPTO, EQUITY, FX, COMMODITY, FIXED_INCOME), all 16+
  instrument types, all 4 strategy types (MOM, MR, BASIS, YIELD), and 33 venues.
todos:
  - id: p0-uac-aggregated-position
    content: |
      - [x] [AGENT] P0. Add AggregatedPosition, VenuePositionBreakdown, PortfolioGreeksSnapshot,
        UnderlyingGreeksBreakdown, PortfolioPnLAttribution, RiskGroupSummary, PortfolioView,
        DeFiAggregatedHealth, ProtocolHealthBreakdown, DeFiLPAggregatedMetrics, LPProtocolBreakdown,
        DeFiStakingAggregatedMetrics, StakingProtocolBreakdown to UAC
        canonical/domain/position/__init__.py. All Pydantic extending CanonicalBase, all Decimal
        fields, no float. Export from position.py facade and UAC __init__.py.
    status: done
  - id: p0-uac-sports-arb-position
    content: |
      - [x] [AGENT] P0. Add SportsArbPosition + SportsArbLeg to UAC canonical/domain/sports/arb.py.
        Export from sports/__init__.py and sports.py facade.
    status: done
    note:
      "SportsArbPosition + SportsArbLeg in canonical/domain/sports/arb.py and re-exported from
      canonical/domain/__init__.py — confirmed 2026-03-16"
  - id: p0-uic-aggregation-messages
    content: |
      - [x] [AGENT] P0. Add AGGREGATED_POSITIONS, PORTFOLIO_VIEWS, RISK_GROUP_UPDATES to
        InternalPubSubTopic in UIC pubsub.py. Add typed VenuePositionBreakdownMessage and
        AggregatedPositionMessage schemas (str-encoded Decimals). Add CorrelationEntry to risk.py.
    status: done
    note:
      "AGGREGATED_POSITIONS/PORTFOLIO_VIEWS/RISK_GROUP_UPDATES in UIC pubsub.py; VenuePositionBreakdownMessage +
      AggregatedPositionMessage in __init__.py — confirmed 2026-03-16"
  - id: p0-uei-aggregation-events
    content: |
      - [x] [AGENT] P0. Add 8 event constants to UEI schemas.py: POSITION_AGGREGATED,
        PORTFOLIO_VIEW_PUBLISHED, SPORTS_ARB_DETECTED, DEFI_HEALTH_AGGREGATED,
        DEFI_LP_AGGREGATED, DEFI_STAKING_AGGREGATED, RISK_GROUP_RECALCULATED,
        CROSS_VENUE_RECONCILIATION_COMPLETED. Add POSITION_AGGREGATION_EVENT_TYPES set.
    status: done
    note: "All 8 event constants + POSITION_AGGREGATION_EVENT_TYPES in UEI schemas.py — confirmed 2026-03-16"
  - id: p0-upi-re-exports
    content: |
      - [x] [AGENT] P0. Update UPI schemas.py to re-export AggregatedPosition, PortfolioView,
        PortfolioGreeksSnapshot, PortfolioPnLAttribution, RiskGroupSummary, DeFiAggregatedHealth,
        DeFiLPAggregatedMetrics, DeFiStakingAggregatedMetrics from UAC. Add to __all__.
    status: done
    blocked_by: p0-uac-aggregated-position
    note: "All aggregation types re-exported from UPI __init__.py — confirmed 2026-03-16"
  - id: p1-pbms-cross-venue-aggregator
    content: |
      - [x] [AGENT] P0. Create CrossVenueAggregator in PBMS core/cross_venue_aggregator.py.
        Compose UIC CrossAssetPortfolioAggregator for gross/net math. State keyed
        instrument_id -> venue -> _VenueData. All Decimal arithmetic with asyncio.Lock.
        Publish typed AggregatedPositionMessage via get_pubsub_client(). Sequence number:
        per-instrument atomic counter. On error: publish RISK_ALERTS + serve stale with flag.
    status: done
    blocked_by: p0-uac-aggregated-position
    note: "core/cross_venue_aggregator.py confirmed present — 2026-03-16"
  - id: p1-pbms-mark-price-subscriber
    content: |
      - [x] [AGENT] P0. Create MarkPriceSubscriber in PBMS core/mark_price_subscriber.py.
        Subscribe to InternalPubSubTopic.DERIVATIVE_TICKERS for real-time mark prices.
        Update position mark_prices in CrossVenueAggregator. Fallback to fill price if
        no market data within staleness_threshold_seconds (config).
    status: done
    blocked_by: p1-pbms-cross-venue-aggregator
    note: "core/mark_price_subscriber.py confirmed present — 2026-03-16"
  - id: p1-pbms-aggregator-wiring
    content: |
      - [x] [AGENT] P1. Wire CrossVenueAggregator into PositionTracker.process_fill() via
        constructor injection. Update FillEventConsumer and api/main.py startup. Add asyncio
        periodic task for PortfolioView publishing every portfolio_view_interval_seconds.
    status: done
    blocked_by: p1-pbms-cross-venue-aggregator
    note: "CrossVenueAggregator injected into PositionTracker and wired in api/main.py startup — confirmed 2026-03-16"
  - id: p1-pbms-greeks-aggregator
    content: |
      - [x] [AGENT] P0. Create GreeksAggregator in PBMS core/greeks_aggregator.py.
        Consumes per-position Greeks (from GreeksExposure in UIC, convert float to Decimal).
        Same underlying: sum directly (correlation = 1). Portfolio level: per-underlying
        breakdown + total. Output: PortfolioGreeksSnapshot. Wire into PortfolioView build.
    status: done
    blocked_by: p0-uac-aggregated-position
    note: "core/greeks_aggregator.py confirmed present — 2026-03-16"
  - id: p1-pbms-pnl-attribution-aggregator
    content: |
      - [x] [AGENT] P1. Create PnLAttributionAggregator in PBMS core/pnl_attribution_aggregator.py.
        Sums PnL components (delta, gamma, theta, vega, rho, funding, basis, interest_rate,
        carry, fx, residual) across all positions. Groups by: asset_group, strategy, risk_group.
        Output: PortfolioPnLAttribution.
    status: done
    blocked_by: p1-pbms-cross-venue-aggregator
    note: "core/pnl_attribution_aggregator.py confirmed present — 2026-03-16"
  - id: p1-pbms-risk-group-aggregator
    content: |
      - [x] [AGENT] P0. Create RiskGroupAggregator in PBMS core/risk_group_aggregator.py.
        Groups positions by underlying. Same underlying: net delta/gamma/exposure directly
        (correlation = 1). Cross-underlying: configurable correlation matrix. Default
        correlations: same=1.0, BTC/ETH=0.85, crypto/equity=0.3. Output: list[RiskGroupSummary].
        Portfolio-level diversified exposure: sqrt(sum_i sum_j rho_ij * E_i * E_j).
    status: done
    blocked_by: p1-pbms-greeks-aggregator
    note: "core/risk_group_aggregator.py confirmed present — 2026-03-16"
  - id: p1-pbms-sports-arb-engine
    content: |
      - [x] [AGENT] P1. Create SportsArbEngine in PBMS core/sports_arb_engine.py.
        Scans SportsPositionTracker for positions with len(venues) > 1.
        Arb P&L formula (2-outcome back/lay only): if_wins = back_stake*(back_odds-1) -
        lay_stake*(lay_odds-1), if_loses = lay_stake - back_stake.
        Subtract per-venue commission. Log SPORTS_ARB_DETECTED.
    status: done
    blocked_by: p0-uac-sports-arb-position
    note: "core/sports_arb_engine.py confirmed present with detect_arbs(), check_exposure_limits() — 2026-03-16"
  - id: p1-pbms-defi-health-aggregator
    content: |
      - [x] [AGENT] P1. Create DeFiHealthAggregator in PBMS core/defi_health_aggregator.py.
        Input: list[DeFiLendingPosition] from UIC. combined_health_factor =
        total_collateral / total_debt. Guard: None if debt == 0.
        Per-chain breakdown: per_chain_health dict[str, Decimal]. Log DEFI_HEALTH_AGGREGATED.
    status: done
    blocked_by: p0-uac-aggregated-position
    note: "core/defi_health_aggregator.py confirmed present — 2026-03-16"
  - id: p1-pbms-defi-lp-aggregator
    content: |
      - [x] [AGENT] P1. Create DeFiLPAggregator in PBMS core/defi_lp_aggregator.py.
        Input: list[DeFiLPPosition] from UIC. Aggregates total LP value, fees earned,
        impermanent loss across protocols. Per-protocol breakdown. Log DEFI_LP_AGGREGATED.
    status: done
    blocked_by: p0-uac-aggregated-position
    note: "core/defi_lp_aggregator.py confirmed present — 2026-03-16"
  - id: p1-pbms-defi-staking-aggregator
    content: |
      - [x] [AGENT] P1. Create DeFiStakingAggregator in PBMS core/defi_staking_aggregator.py.
        Input: list[DeFiStakingPosition] from UIC. Aggregates total staked value, rewards,
        weighted APY. Per-protocol breakdown. Log DEFI_STAKING_AGGREGATED.
    status: done
    blocked_by: p0-uac-aggregated-position
    note: "core/defi_staking_aggregator.py confirmed present — 2026-03-16"
  - id: p1-pbms-cross-venue-recon
    content: |
      - [x] [AGENT] P1. Extend ReconciliationEngine with reconcile_aggregated_positions().
        Verify sum of per_venue quantities == net_quantity. Log
        CROSS_VENUE_RECONCILIATION_COMPLETED with discrepancy details.
    status: done
    blocked_by: p1-pbms-cross-venue-aggregator
    note: "reconciliation_engine.py present with cross-venue recon logic — confirmed 2026-03-16"
  - id: p1-pbms-sse-aggregated
    content: |
      - [x] [AGENT] P2. Add /stream/aggregated-positions SSE endpoint to PBMS
        api/routes/positions_stream.py following existing /stream/positions pattern.
    status: done
    blocked_by: p1-pbms-cross-venue-aggregator
    note: "/stream/aggregated-positions SSE endpoint in api/routes/aggregated.py — confirmed 2026-03-16"
  - id: p1-pbms-config-extensions
    content: |
      - [x] [AGENT] P2. Add aggregation config to PBMS config.py: aggregation_enabled,
        aggregation_publish_topic, portfolio_view_interval_seconds,
        sports_commission_rates_json, defi_health_aggregation_enabled,
        defi_lp_aggregation_enabled, defi_staking_aggregation_enabled,
        correlation_matrix_json, mark_price_staleness_threshold_seconds,
        greeks_aggregation_enabled, risk_group_aggregation_enabled.
    status: done
    note: "All aggregation config fields in config.py — confirmed 2026-03-16"
  - id: p2-risk-subscribe-aggregated
    content: |
      - [x] [AGENT] P1. Add AggregatedPositionSubscriber in risk-and-exposure-service
        core/aggregated_position_subscriber.py. Subscribe to AGGREGATED_POSITIONS PubSub.
        Maintain in-memory cache. Wire into ExposureAggregator.calculate_exposures().
    status: done
    blocked_by: p1-pbms-cross-venue-aggregator
    note: "risk-and-exposure-service/core/aggregated_position_subscriber.py confirmed — 2026-03-16"
  - id: p2-strategy-consume-portfolio
    content: |
      - [x] [AGENT] P1. Add PortfolioViewConsumer in strategy-service
        core/portfolio_view_consumer.py. Subscribe to PORTFOLIO_VIEWS PubSub. Replace manual
        PositionSnapshot construction with PortfolioView consumption.
    status: done
    blocked_by: p1-pbms-cross-venue-aggregator
    note: "strategy-service/core/portfolio_view_consumer.py confirmed — 2026-03-16"
  - id: p2-execution-publish
    content: |
      - [x] [AGENT] P2. Add PBMS publisher to execution-service UnifiedPositionTracker
        (engine/live/positions.py). Keep local tracker for sub-ms latency. After each
        venue_positions update, publish to PBMS. CRITICAL: convert all float values to
        Decimal(str(value)) at the publish boundary.
    status: done
    blocked_by: p1-pbms-cross-venue-aggregator
    note: "execution-service/engine/live/positions.py has PBMSPositionPublisher injection — confirmed 2026-03-16"
  - id: p2-pbms-rest-endpoints
    content: |
      - [x] [AGENT] P1. Add REST endpoints to PBMS api/routes/:
        GET /aggregated-positions?asset_group=&venue=&instrument_type=&limit=50&offset=0
        GET /aggregated-positions/{instrument_id}
        GET /portfolio-view/{client_id}
        GET /sports-arb-positions
        GET /defi-health/{client_id}
        GET /defi-lp/{client_id}
        GET /defi-staking/{client_id}
        GET /risk-groups/{client_id}
        All with pagination (limit/offset) and filtering.
    status: done
    blocked_by: p1-pbms-cross-venue-aggregator
    note: "All REST endpoints in api/routes/aggregated.py — confirmed 2026-03-16"
  - id: p3-sports-commission-config
    content: |
      - [x] [AGENT] P2. Commission rates as dict[str, Decimal] from
        sports_commission_rates_json env var. Wire into SportsArbEngine.detect_arbs().
    status: done
    blocked_by: p1-pbms-sports-arb-engine
    note: "_parse_commission_rates() in api/main.py, injected via set_sports_arb_engine() — confirmed 2026-03-16"
  - id: p3-sports-cross-venue-limits
    content: |
      - [x] [AGENT] P2. SportsArbEngine.check_exposure_limits(max_exposure_per_selection).
        Sum total_backed+total_laid across venues. Log POSITION_LIMIT_CHECKED.
    status: done
    blocked_by: p1-pbms-sports-arb-engine
    note: "check_exposure_limits() in sports_arb_engine.py confirmed — 2026-03-16"
  - id: p3-correlation-config-loader
    content: |
      - [x] [AGENT] P1. Create CorrelationConfigLoader in PBMS core/correlation_config.py.
        Load from correlation_matrix_json env var (default hardcoded matrix).
        Support: same_underlying=1.0 (always), empirical pairs (BTC/ETH, ETH/SOL, etc.),
        asset_group_defaults. Method: get_correlation(underlying_a, underlying_b) -> Decimal.
    status: done
    blocked_by: p1-pbms-risk-group-aggregator
    note: "CorrelationConfigLoader with get_correlation() in core/correlation_config.py — confirmed 2026-03-16"
  - id: p4-tests-cross-venue-aggregator
    content: |
      - [x] [AGENT] P0. Unit tests for CrossVenueAggregator: 9 cases -- single venue,
        two venues same instrument, remove venue, build_portfolio_view, weighted avg entry,
        all Decimal, concurrent safety, asset_group/instrument_type preserved, strategy_id.
    status: done
    blocked_by: p1-pbms-cross-venue-aggregator
    note: "tests/unit/test_cross_venue_aggregator.py confirmed — 2026-03-16"
  - id: p4-tests-greeks-aggregator
    content: |
      - [x] [AGENT] P0. Unit tests for GreeksAggregator: 6 cases -- same underlying nets
        perfectly, different underlying breakdown, portfolio total, float-to-Decimal
        conversion, zero Greeks, options + futures mixed underlying.
    status: done
    blocked_by: p1-pbms-greeks-aggregator
    note: "tests/unit/test_greeks_aggregator.py confirmed — 2026-03-16"
  - id: p4-tests-pnl-attribution
    content: |
      - [x] [AGENT] P0. Unit tests for PnLAttributionAggregator: 5 cases -- single position
        passthrough, multi-position sum, per-asset-class grouping, per-strategy grouping,
        all 11 PnL dimensions sum correctly.
    status: done
    blocked_by: p1-pbms-pnl-attribution-aggregator
    note: "tests/unit/test_pnl_attribution_aggregator.py confirmed — 2026-03-16"
  - id: p4-tests-risk-group
    content: |
      - [x] [AGENT] P0. Unit tests for RiskGroupAggregator: 7 cases -- same underlying nets
        delta/gamma, different underlying uses correlation, default matrix, custom override,
        diversified exposure formula, single-asset-class, cross-asset portfolio.
    status: done
    blocked_by: p1-pbms-risk-group-aggregator
    note: "tests/unit/test_risk_group_aggregator.py confirmed — 2026-03-16"
  - id: p4-tests-sports-arb
    content: |
      - [x] [AGENT] P0. Unit tests for SportsArbEngine: 5 cases -- profitable arb,
        unprofitable, commission netting, single-venue no arb, mixed selections.
    status: done
    blocked_by: p1-pbms-sports-arb-engine
    note: "tests/unit/test_sports_arb_engine.py confirmed — 2026-03-16"
  - id: p4-tests-defi
    content: |
      - [x] [AGENT] P0. Unit tests for all 3 DeFi aggregators: DeFiHealth (6 cases inc.
        per-chain breakdown), DeFiLP (4 cases inc. impermanent loss), DeFiStaking (4 cases
        inc. weighted APY). 14 total test cases.
    status: done
    blocked_by: p1-pbms-defi-health-aggregator
    note: "tests/unit/test_defi_aggregators.py confirmed — 2026-03-16"
  - id: p4-tests-integration
    content: |
      - [x] [AGENT] P1. PBMS integration tests: fill on venue A + fill on venue B ->
        correct aggregated position via PubSub emulator. SSE stream receives updates.
        REST endpoints return data with pagination. Greeks aggregated correctly.
        All credential-free with CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true.
    status: done
    blocked_by: p1-pbms-aggregator-wiring
    note:
      "tests/integration/test_cross_venue_integration.py written — 6 tests covering multi-venue fills, VWAP, net
      quantity, no-float, multi-instrument — confirmed 2026-03-16"
  - id: p4-tests-schema
    content: |
      - [x] [AGENT] P0. Schema tests in UAC: AggregatedPosition, PortfolioView,
        PortfolioGreeksSnapshot, PortfolioPnLAttribution, RiskGroupSummary,
        DeFiAggregatedHealth, DeFiLPAggregatedMetrics, DeFiStakingAggregatedMetrics,
        SportsArbPosition. Serialize/deserialize, extra=forbid, Decimal round-trip.
        Verify AggregatedPosition satisfies PositionQuantityProtocol.
    status: done
    blocked_by: p0-uac-aggregated-position
    note:
      "tests/unit/test_aggregation_schemas.py written — all 9 types tested, round-trip, extra=forbid, Decimal precision,
      PositionQuantityProtocol properties — confirmed 2026-03-16"
  - id: p4-tests-float-boundary
    content: |
      - [x] [AGENT] P0. Dedicated float boundary tests: execution-service float ->
        publish -> PBMS Decimal. Assert 0.1 + 0.2 round-trips as Decimal("0.3").
    status: done
    blocked_by: p2-execution-publish
    note:
      "Float boundary test class in execution-service/tests/unit/live/test_positions.py (line 266) — confirmed
      2026-03-16"
  - id: p4-prometheus-metrics
    content: |
      - [x] [AGENT] P2. 9 Prometheus metrics in PBMS metrics.py:
        position_aggregation_latency_seconds, aggregated_positions_total,
        sports_arb_detected_total, defi_health_factor_combined,
        defi_lp_total_value_usd, defi_staking_total_value_usd,
        cross_venue_reconciliation_discrepancy_total, portfolio_view_publish_total,
        risk_group_diversified_exposure.
    status: done
    blocked_by: p1-pbms-cross-venue-aggregator
    note:
      "metrics.py confirmed with position_aggregation_latency_seconds, aggregated_positions_total,
      sports_arb_detected_total (+ others) — 2026-03-16"
  - id: p5-sit-end-to-end
    content: |
      - [x] [AGENT] P1. System integration test in system-integration-tests/:
        execution-service publishes fill -> PBMS aggregates (with float-to-Decimal) ->
        risk-and-exposure-service receives aggregated feed -> verify exposure matches.
        All credential-free.
    status: done
    blocked_by: p2-risk-subscribe-aggregated
    note:
      "tests/integration/test_cross_venue_aggregation_e2e.py written — net qty, VWAP, multi-instrument, float->Decimal
      boundary, UAC imports smoke, PBMS importable — confirmed 2026-03-16"
isProject: false
---

# Cross-Venue Position Aggregation -- Implementation Detail

## Context

The unified trading system tracks positions **per venue** in position-balance-monitor-service. Cross-venue aggregation
exists only as on-demand queries in risk-and-exposure-service (`ExposureAggregator`). There is no canonical schema for
aggregated positions, no live aggregated position stream, no sports arb P&L unification across bookmakers, no DeFi
health factor netting across protocols, no portfolio-level Greeks aggregation, no PnL attribution rollup, and no risk
group netting with configurable correlation.

**Building blocks that exist:**

- `PositionTracker` in PBMS: per-key (client, strategy, venue, instrument) tracking
- `SportsPositionTracker`: stores `venues: list[str]` per selection, calculates net_position/pnl
- `CrossAssetPortfolioAggregator` in UIC: polymorphic aggregation via `PositionQuantityProtocol`
- `UnifiedPositionTracker` in execution-service: local cross-venue sum (not published)
- `ExposureAggregator` in risk-and-exposure-service: on-demand gross/net exposure
- `GreeksExposure` in UIC: per-position delta/gamma/theta/vega/rho
- `PnLBreakdown` in UIC: 6-dimension attribution (delta, funding, basis, interest_rate, greeks, MTM)
- `PnLAttributionRecord` in UAC: daily breakdown (delta/gamma/vega/theta/rho/fx/carry/residual)
- `VaRCalculator` in risk-service: parametric/historical/Cornish-Fisher VaR
- `MultiAssetMarginCalculation` in UAC: SPAN-style cross-margin with correlation offset

**Gaps this plan closes:**

1. No `AggregatedPosition` canonical schema -- aggregation on-the-fly, never persisted
2. No live aggregated position stream -- risk queries on-demand, no PubSub feed
3. Sports arb P&L not unified -- back on Betfair + lay on Smarkets = what's the net?
4. Strategy/ML services blind -- each builds own snapshots, no pre-aggregated feed
5. No DeFi collateral netting across AAVE/Morpho/Euler (lending, LP, staking)
6. No portfolio-level Greeks aggregation with same-underlying netting (correlation=1)
7. No PnL attribution rollup across all 11 dimensions at portfolio level
8. No risk group netting with configurable cross-underlying correlation

---

## Phases Overview + Sizing

| Phase | Description                 | Todos | Repos                      | Est. Lines | Risk     |
| ----- | --------------------------- | ----- | -------------------------- | ---------- | -------- |
| 0     | Canonical Schemas           | 5     | UAC, UIC, UEI, UPI         | ~550       | Low      |
| 1     | Aggregation Engine          | 12    | PBMS                       | ~1100      | **High** |
| 2     | Consumer Wiring             | 4     | risk, strategy, exec, PBMS | ~500       | Medium   |
| 3     | Sports + Correlation Config | 3     | PBMS                       | ~200       | Low      |
| 4     | Testing + Observability     | 10    | PBMS, UAC, exec            | ~900       | Low      |
| 5     | SIT                         | 1     | system-integration-tests   | ~150       | Medium   |

**Total: 35 todos across 9 repos.**

**Critical path**: p0-uac-aggregated-position -> p1-pbms-cross-venue-aggregator -> p1-pbms-greeks-aggregator ->
p1-pbms-risk-group-aggregator -> p2-risk-subscribe-aggregated -> p5-sit-end-to-end.

---

## Repos Touched

| Repo                             | Tier | Phases  | Changes                                                 |
| -------------------------------- | ---- | ------- | ------------------------------------------------------- |
| unified-api-contracts            | T0   | 0, 4    | +15 position/risk models, +1 sports model, schema tests |
| unified-internal-contracts       | T0   | 0       | +3 PubSub topics, +2 message schemas, +1 risk model     |
| unified-events-interface         | T0   | 0       | +8 event constants                                      |
| unified-position-interface       | T1   | 0       | Re-exports from UAC                                     |
| position-balance-monitor-service | T3   | 1,2,3,4 | 8 aggregator modules, SSE, REST, config, metrics, tests |
| risk-and-exposure-service        | T3   | 2       | Aggregated position subscriber                          |
| strategy-service                 | T3   | 2       | PortfolioView consumer                                  |
| execution-service                | T3   | 2, 4    | PBMS publisher + float boundary tests                   |
| system-integration-tests         | T3   | 5       | End-to-end aggregation test                             |

---

## Risk Register

| Risk                                         | Likelihood | Impact | Mitigation                                                              |
| -------------------------------------------- | ---------- | ------ | ----------------------------------------------------------------------- |
| Float contamination from execution-service   | HIGH       | HIGH   | Decimal(str(value)) at publish boundary. Dedicated float boundary test. |
| Race condition between fills and aggregation | MEDIUM     | MEDIUM | asyncio.Lock. Cross-venue recon detects post-facto.                     |
| mark_price stale or zero                     | HIGH       | HIGH   | MarkPriceSubscriber from DERIVATIVE_TICKERS. Staleness threshold alert. |
| Correlation matrix stale                     | MEDIUM     | MEDIUM | Config-driven defaults + periodic empirical update from risk service.   |
| PubSub message ordering                      | MEDIUM     | LOW    | Per-instrument sequence_number. Consumer discards stale.                |
| DeFi health division by zero                 | LOW        | HIGH   | Guard: combined_health_factor = None if combined_debt == 0.             |
| Version cascade across 9 repos               | HIGH       | LOW    | T0 first, wait for cascade. Then T1/T3.                                 |
| Greeks float->Decimal conversion             | MEDIUM     | MEDIUM | UIC GreeksExposure uses float. Convert at PBMS boundary.                |
| Aggregator error mid-stream                  | MEDIUM     | HIGH   | Publish RISK_ALERT, serve stale data with flag, continue.               |

---

## Agent Handoff Protocol

- A todo starts only when ALL its `blocked_by` dependencies are marked `done`
- Parallel todos can be assigned to parallel agents in a single message
- When agent completes: mark `status: done`, update `- [ ]` to `- [x]`
- If QG fails: mark `status: blocked`, add `note:` explaining failure
- **No quickmerge unless explicitly requested. QG pass = done. Commit only.**
- **Agent injection**: read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- **WORKSPACE_ROOT**: `/Users/ikennaigboaka/Code/unified-trading-system-repos`

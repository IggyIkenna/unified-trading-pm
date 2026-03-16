---
name: contracts-observability-risk-cleanup
overview: |
  Comprehensive cleanup, observability, circuit breaker hardening, and risk expansion.
  Phased execution DAG with pre-audit manifest — agents execute from manifest, no re-scanning.
  Phase 1: UAC internal cleanup (no downstream impact, parallel).
  Phase 2: UIC receives schemas + QG UIC.
  Phase 3: UAC removes moved schemas + QG UAC + cassette parity.
  Phase 4: Downstream fixes (2 repos, parallel) + QG per repo.
  Phase 5: Observability, circuit breaker citadel-grade, VaR Phase 2.
  Phase 6: Final workspace-wide QG.
type: mixed
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: D2
  business: none

repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-internal-contracts
    code: C0
    deployment: none
    business: none
  - repo: risk-and-exposure-service
    code: C0
    deployment: none
    business: none
  - repo: execution-service
    code: C0
    deployment: none
    business: none
  - repo: trading-analytics-api
    code: C0
    deployment: none
    business: none
  - repo: market-data-processing-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: unified-market-interface
    code: C0
    deployment: none
    business: none
  - repo: live-health-monitoring-ui
    code: C0
    deployment: none
    business: none

depends_on: []

todos:
  # =========================================================================
  # PHASE 1: UAC INTERNAL CLEANUP (no downstream impact — all parallel)
  # =========================================================================
  # These items touch ONLY UAC internals. No downstream repo breaks.
  # Run ALL Phase 1 items in parallel via separate agents.

  - id: p1a-delete-duplicate-errors-package
    content: |
      - [ ] [AGENT] P0. Delete `canonical/errors/` (byte-for-byte duplicate of crosscutting).
        PRE-AUDIT: 2 stale imports to redirect first:
        1. `canonical/__init__.py:147` → `from .crosscutting.errors import`
        2. `external/open_meteo/schemas.py:15` → same
        Then delete entire `canonical/errors/` directory.
    status: todo
    note: "PARALLEL with p1b-p1f. No downstream impact."

  - id: p1b-deduplicate-erroraction
    content: |
      - [ ] [AGENT] P0. In `crosscutting/errors/_canonical.py`, delete duplicate ErrorAction
        and VenueErrorClassification definitions. Import from `._types` instead.
    status: todo
    note: "PARALLEL. Internal only."

  - id: p1c-remove-coinglass-hyblock-versifi
    content: |
      - [ ] [AGENT] P0. Delete from UAC entirely:
        - `crosscutting/errors/altdata.py`: remove coinglass, hyblock, versifi entries
        - `docs/VERSIFI_INTEGRATION.md`: delete file
        - `COVERAGE_AUDIT.md`: remove coinglass reference
        - `docs/UAC_FULL_GAP_ANALYSIS_AND_BATCH_LIVE_SYMMETRY.md`: remove versifi refs
        No downstream service imports these.
    status: todo
    note: "PARALLEL. Decision: own liquidation prediction system."

  - id: p1d-delete-sports-generic
    content: |
      - [ ] [AGENT] P0. Delete `sports_generic` from `crosscutting/errors/sports.py`.
        Fallback template — each venue should have proper venue-specific error codes.
        No downstream service imports this.
    status: todo
    note: "PARALLEL."

  - id: p1e-prune-dead-connectivity-symbols
    content: |
      - [ ] [AGENT] P1. Remove 7 dead symbols from `crosscutting/connectivity.py`:
        DELETE: WebSocketPingFrame, WebSocketPongFrame, UnsubscribeRequest, SubscribeRequest,
        HeartbeatMessage, WebSocketConnectionState, CanonicalWsMessage.
        PRE-AUDIT: No service imports these. Update:
        - `tests/test_contract_alignment.py:71,77,79,92,94-95` — delete test cases
        - `scripts/check_uac_adoption.py:106,108` — remove symbol names
        - Root `__init__.py` lines 166,233,254,256-257 — remove re-exports
        - `canonical/__init__.py` lines 113,128,262,277 — remove re-exports
        - `canonical/domain/__init__.py` lines 23,27,461,482 — remove imports
        KEEP: WebSocketEvent, CanonicalWebSocketLifecycle, HealthPingResponse,
        WebSocketConnectionOpened, WebSocketConnectionClosed.
    status: todo
    note: "PARALLEL. No downstream impact — all dead symbols."

  - id: p1f-recategorize-venue-errors
    content: |
      - [ ] [AGENT] P1. Re-categorize venue error files:
        CREATE `errors/tradfi.py`: move tardis,yahoo_finance,ibkr,databento from cefi.py;
        barchart,fred,ecb,ofr,openbb from altdata.py.
        CREATE `errors/onchain_perps.py`: move hyperliquid,aster from altdata.py.
        CREATE `errors/infra.py`: move alchemy,thegraph from cefi.py; bloxroute from altdata.py.
        MOVE to defi.py: aave_v3 from altdata.py; instadapp,defillama from sports.py.
        MOVE to altdata.py: glassnode,arkham from sports.py.
        MOVE onchain_revert from sports.py to own crosscutting section.
        UPDATE `errors/__init__.py`: import new files, update VENUE_ERROR_MAP.
    status: todo
    note: "PARALLEL. Internal reorganization only."

  - id: p1-qg-uac-internal
    content: |
      - [ ] [AGENT] P0. GATE: `cd unified-api-contracts && bash scripts/quality-gates.sh`.
        Must pass before Phase 2. Validates all Phase 1 changes are clean.
    status: todo
    note: "SEQUENTIAL — runs after ALL p1a-p1f complete."

  # =========================================================================
  # PHASE 2: UIC RECEIVES SCHEMAS (sequential — must complete before Phase 3)
  # =========================================================================
  # Add new schemas to UIC. No deletions from UAC yet — both copies exist temporarily.

  - id: p2a-uic-add-risk-schemas
    content: |
      - [ ] [AGENT] P0. Add to UIC `domain/risk_service/risk.py`:
        - VaRMethod (StrEnum), VaRRequest, VaRResult (align with existing var_calculator.py)
        - StressScenario, StressTestResult
        - PnLAttributionRecord (complement existing PnLBreakdown)
        - RealTimePnLRecord
        - RiskLimitBreach → consolidate with existing AlertMessage (add breach_pct,
          recommended_action, auto_halt_triggered fields to AlertMessage or subclass)
        SpanMarginLeg and MultiAssetMarginCalculation already in UIC — no action.
        Export all new types from `risk.py`, `domain/risk_service/__init__.py`, root `__init__.py`.
    status: todo
    note: "PARALLEL with p2b-p2c."

  - id: p2b-uic-add-correlation-schemas
    content: |
      - [ ] [AGENT] P0. Add to UIC `domain/analytics/`:
        - CorrelationRegime (StrEnum: LOW, NORMAL, HIGH, CRISIS)
        - CrossAssetCorrelationMatrix
        - CorrelationRegimeChange
        Export from `domain/analytics/__init__.py` and root `__init__.py`.
    status: todo
    note: "PARALLEL with p2a,p2c."

  - id: p2c-uic-cleanup-dead-ws-types
    content: |
      - [ ] [AGENT] P1. In UIC `domain/websocket/lifecycle.py`:
        Delete WebSocketPingFrame, WebSocketPongFrame (dead in both UAC and UIC).
        Keep HealthPingResponse, WebSocketConnectionOpened, WebSocketConnectionClosed.
        Update `domain/websocket/__init__.py` exports.
    status: todo
    note: "PARALLEL with p2a,p2b."

  - id: p2-qg-uic
    content: |
      - [ ] [AGENT] P0. GATE: `cd unified-internal-contracts && bash scripts/quality-gates.sh`.
        Must pass before Phase 3. Validates new schemas are correct.
    status: todo
    note: "SEQUENTIAL — runs after ALL p2a-p2c complete."

  # =========================================================================
  # PHASE 3: UAC REMOVES MOVED SCHEMAS (sequential — must complete before Phase 4)
  # =========================================================================
  # Now that UIC has the schemas, remove UAC copies and update facades.

  - id: p3a-delete-uac-risk-module
    content: |
      - [ ] [AGENT] P0. Delete `canonical/crosscutting/risk.py` entirely.
        PRE-AUDIT — remove from these re-export chains:
        - Root `__init__.py:182,204-215,222,229-230,241-243` — remove 10 risk symbols
        - Root `__init__.py __all__` — remove same
        - `canonical/__init__.py:46,113-128,262-277` — remove risk re-exports
        - `canonical/domain/__init__.py:3,46,461,482` — remove crosscutting.risk imports
        - `crosscutting/__init__.py` — remove risk import if present
    status: todo
    note: "PARALLEL with p3b."

  - id: p3b-fix-uac-analytics-split
    content: |
      - [ ] [AGENT] P0. In `crosscutting/analytics.py`:
        DELETE: FactorType, FactorExposure, FactorAttributionRecord, FactorAttributionModel
        (UIC is SSOT — UAC had duplicate definitions)
        DELETE: CorrelationRegime, CrossAssetCorrelationMatrix, CorrelationRegimeChange
        (moved to UIC in Phase 2)
        KEEP: AlternativeDataType, AlternativeDataSignal, SentimentScore,
        SatelliteObservation, OptionsFlowRecord, DarkPoolPrintRecord (external normalization)
        Update re-export chains:
        - Root `__init__.py:157-160` — remove Factor*/Correlation* from domain imports
        - `canonical/__init__.py:137-139` — remove same
        - `canonical/domain/__init__.py:3-6` — remove crosscutting.analytics Factor*/Corr imports
    status: todo
    note: "PARALLEL with p3a."

  - id: p3-qg-uac-final
    content: |
      - [ ] [AGENT] P0. GATE: `cd unified-api-contracts && bash scripts/quality-gates.sh`.
        Run cassette parity: `pytest tests/test_cassette_schema_parity.py`.
        Must pass before Phase 4.
    status: todo
    note: "SEQUENTIAL — runs after p3a+p3b complete."

  # =========================================================================
  # PHASE 4: DOWNSTREAM ADOPTION (parallel agents — 4 repos + 1 UI)
  # =========================================================================
  # PRE-AUDIT: 2 repos break (import path), 1 repo should adopt (local types),
  # 1 UI needs TypeScript types. ml-training-service, strategy-service: NO CHANGE.

  - id: p4a-fix-trading-analytics-api
    content: |
      - [ ] [AGENT] P0. Fix `trading-analytics-api/trading_analytics_api/contracts.py:8-22`:
        CHANGE: Remove `from unified_api_contracts import (CorrelationRegime,
        CrossAssetCorrelationMatrix, CorrelationRegimeChange, ...)`
        ADD: `from unified_internal_contracts import (CorrelationRegime,
        CrossAssetCorrelationMatrix, CorrelationRegimeChange)`
        Factor* imports already correct (from UIC). Update `__all__:24-36`.
        Run: `cd trading-analytics-api && bash scripts/quality-gates.sh`
    status: todo
    note: "PARALLEL with p4b-p4e."

  - id: p4b-fix-market-data-processing-service
    content: |
      - [ ] [AGENT] P0. Fix `market-data-processing-service/market_data_processing_service/types.py:19`:
        CHANGE: Remove Correlation*/FactorType from UAC import.
        ADD: `from unified_internal_contracts import (CorrelationRegime,
        CrossAssetCorrelationMatrix, FactorType)` (if needed, or remove if unused).
        Update `__all__:31`.
        Run: `cd market-data-processing-service && bash scripts/quality-gates.sh`
    status: todo
    note: "PARALLEL with p4a,p4c-p4e."

  - id: p4c-risk-service-adopt-uic-schemas
    content: |
      - [ ] [AGENT] P0. Adopt UIC schemas in risk-and-exposure-service (doesn't break but
        has local type duplication that SHOULD import from UIC):
        1. `var_calculator.py:34` — replace `StressScenario = Literal["GFC_2008", ...]`
           with import from UIC: `from unified_internal_contracts import StressScenario`
           (after p2a adds it as a StrEnum to UIC)
        2. `api/main.py` — VaRResponse DTO: align field types with UIC VaRResult
           (float→Decimal for var/cvar, add portfolio_id, computed_at).
           VaRResponse as HTTP DTO can differ from domain schema but must document mapping.
        Run: `cd risk-and-exposure-service && bash scripts/quality-gates.sh`
    status: todo
    note: "PARALLEL. Adoption — doesn't break, but eliminates self-declared types."

  - id: p4d-trading-analytics-ui-types
    content: |
      - [ ] [AGENT] P1. Add TypeScript type mirrors in trading-analytics-ui for schemas
        exposed by trading-analytics-api. Currently TradingDeskPage.tsx has mock Position
        with flat unrealizedPnl — no Greeks, no factor attribution, no correlation types.
        ADD `src/types/risk.ts`: VaRResult, StressTestResult, RiskLimitBreach interfaces
        ADD `src/types/analytics.ts`: CorrelationRegime enum, CrossAssetCorrelationMatrix,
        FactorType enum, FactorExposure, FactorAttributionRecord interfaces
        ADD `src/types/pnl.ts`: PnLAttributionRecord (delta/gamma/vega/theta/rho/basis/
        funding/carry/fees breakdown), RealTimePnLRecord
        Source: mirror UIC Python schemas → TypeScript interfaces.
        Run: `cd trading-analytics-ui && CI=true npm test -- --run`
    status: todo
    note: "PARALLEL. UIs currently have zero typed risk/analytics interfaces."

  - id: p4e-trading-analytics-ui-views
    content: |
      - [ ] [HUMAN+AGENT] P1. Add risk monitor + P&L attribution views to
        trading-analytics-ui (or the new monitoring UI — decide which is home):
        RISK MONITOR VIEW:
        - VaR/CVaR gauges with limit proximity
        - Greeks exposure table (delta/gamma/vega/theta/rho per position/strategy/venue)
        - Basis risk, funding rate exposure
        - Correlation regime indicator + heatmap
        - Circuit breaker state per venue
        P&L ATTRIBUTION VIEW:
        - Waterfall chart: delta P&L → gamma P&L → vega P&L → theta P&L → funding →
          basis → FX → carry → fees → residual = total P&L
        - Drill by: venue, strategy, instrument, time period
        - Over-time line charts for each risk factor's P&L contribution
        These are two views of the SAME decomposition (risk = exposure, P&L = realized exposure).
        Data: risk-service /risk/var, /risk/metrics APIs; PBMS position history.
    status: todo
    note: "PARALLEL. Core analytics views — not Grafana, own UI for custom grouping."

  - id: p4c-add-venues-to-registry
    content: |
      - [ ] [AGENT] P1. Add to UMI VENUE_REGISTRY (factory.py):
        - polymarket, betfair, kalshi, smarkets, betdaq (prediction markets/sports)
        - glassnode, arkham (onchain analytics)
        Create INFRA_PROVIDER_REGISTRY alongside VENUE_REGISTRY:
        - alchemy (Ethereum RPC), thegraph (subgraph indexer), bloxroute (MEV relay)
        Key semantic: venues = trade on them. infra = pipes to reach venues.
        Instadapp IS a venue (DSA contracts) but USES thegraph as pipe.
    status: todo
    note: "PARALLEL with p4a,p4b."

  - id: p4-qg-downstream
    content: |
      - [ ] [AGENT] P0. GATE: Quality gates on all Phase 4 repos.
        `cd trading-analytics-api && bash scripts/quality-gates.sh`
        `cd market-data-processing-service && bash scripts/quality-gates.sh`
        `cd unified-market-interface && bash scripts/quality-gates.sh`
    status: todo
    note: "SEQUENTIAL — runs after p4a-p4c complete."

  # =========================================================================
  # PHASE 5: OBSERVABILITY + CIRCUIT BREAKER + VaR (parallel streams)
  # =========================================================================
  # These are independent feature additions. Three parallel streams.

  # --- Stream A: Observability ---

  - id: p5-obs-prometheus-bridge
    content: |
      - [ ] [AGENT] P1. Wire Prometheus → Cloud Monitoring. Extend UTL setup_tracing()
        to setup_metrics(). OTEL Collector sidecar with remote_write to GCP.
        Repos: unified-trading-library, deployment-service.
    status: todo
    note: "PARALLEL stream A."

  - id: p5-obs-restart-detection
    content: |
      - [ ] [AGENT] P1. Add RESTART_DETECTED lifecycle event to UIC. On STARTED, check for
        missing STOPPED event (unclean shutdown). Emit with restart_count.
        Add restart_count to /health response. Wire into all services.
    status: todo
    note: "PARALLEL stream A."

  - id: p5-obs-latency-profiling
    content: |
      - [ ] [AGENT] P1. Wire UAC latency schemas into production measurement code.
        execution-service order path: tick→signal→risk→encode→send→ack→fill.
        Populate OrderLatencyRecord, write to GCS, publish LatencyBenchmarkReport.
    status: todo
    note: "PARALLEL stream A."

  - id: p5-obs-resource-metrics
    content: |
      - [ ] [AGENT] P1. Add CPU/memory/connections/queue gauges to all services.
        Include shard_id label for batch, venue_id for live.
    status: todo
    note: "PARALLEL stream A."

  - id: p5-obs-monitoring-ui
    content: |
      - [ ] [HUMAN+AGENT] P1. Build live health monitoring UI. Lifecycle timeline, latency
        charts, VaR dashboard, P&L waterfall, resource gauges, risk alerts, batch tracker.
        React+Vite. Data: GCS JSONL, Prometheus, risk-service API, PBMS API.
    status: todo
    note: "PARALLEL stream A."

  - id: p5-obs-cloud-backup
    content: |
      - [ ] [HUMAN+AGENT] P1. Cloud Monitoring backup: uptime checks, log-based alerts,
        container restart detection. Independent safety net.
    status: todo
    note: "PARALLEL stream A."

  - id: p5-obs-alert-rules
    content: |
      - [ ] [AGENT] P2. Define alert rules: restart>3/hr, p99>500ms, VaR>90%, breaker OPEN,
        kill switch, FAILED events, batch deadline miss. YAML config for both UI and cloud.
    status: todo
    note: "PARALLEL stream A."

  # --- Stream B: Circuit Breaker Citadel Grade ---

  - id: p5-cb-degraded-throttling
    content: |
      - [ ] [AGENT] P1. Activate DEGRADED throughput throttling. Config field
        `degraded_rate_limit_pct: 0.5` exists but is NOT IMPLEMENTED. When DEGRADED:
        probabilistic drop ~50% of orders to reduce venue pressure. Token bucket.
        Repo: execution-service (circuit_breaker.py).
    status: todo
    note: "PARALLEL stream B."

  - id: p5-cb-order-queuing
    content: |
      - [ ] [AGENT] P1. Add order queue for OPEN state. Currently orders rejected immediately.
        Queue with: max depth (100), max age (5min), priority ordering (hedge>spec),
        overflow reject. Drain on HALF_OPEN→CLOSED, respecting rate limits.
        Repo: execution-service.
    status: todo
    note: "PARALLEL stream B."

  - id: p5-cb-kill-switch-auto-deactivate
    content: |
      - [ ] [AGENT] P1. Add timed auto-deactivation for kill switch. Optional
        `auto_deactivate_after_minutes` on activation. After timeout: deactivates,
        emits KILL_SWITCH_AUTO_DEACTIVATED. Also: activation via alert rules
        (VaR>150% → kill switch with 30min auto-deactivate).
        Repo: execution-service (kill_switch.py).
    status: todo
    note: "PARALLEL stream B. 3am Sunday recovery."

  - id: p5-cb-venue-failover
    content: |
      - [ ] [AGENT] P2. Venue failover routing when breaker OPEN. Failover pairs
        (Binance→Bybit for BTC spot). Per-instrument, price tolerance check.
        Repo: execution-service (orchestrator.py), unified-config-interface.
    status: todo
    note: "PARALLEL stream B."

  - id: p5-cb-strategy-priority
    content: |
      - [ ] [AGENT] P2. Strategy-level priority in DEGRADED/queued states.
        P0=hedge, P1=rebalance, P2=new positions. P0 always passes throttle.
        Queue: P0 front, P2 back, oldest P2 cancelled first on overflow.
        Repo: execution-service.
    status: todo
    note: "PARALLEL stream B."

  # --- Stream C: VaR / Risk Phase 2 ---

  - id: p5-var-returns-ingestion
    content: |
      - [ ] [AGENT] P1. Automated historical returns ingestion from PBMS. Store daily
        returns per instrument in GCS. Risk service fetches on demand.
        Repos: risk-and-exposure-service, position-balance-monitor-service.
    status: todo
    note: "PARALLEL stream C."

  - id: p5-var-monte-carlo
    content: |
      - [ ] [AGENT] P2. Monte Carlo VaR simulation. Pure stdlib. Random gen + Cholesky
        decomposition. Add VaRMethod.MONTE_CARLO. Wire into /risk/var endpoint.
    status: todo
    note: "PARALLEL stream C."

  - id: p5-var-copula-correlation
    content: |
      - [ ] [AGENT] P2. Copula-based multi-asset correlation. Rolling correlation matrix
        from returns. Feed into MC simulation.
    status: todo
    note: "PARALLEL stream C."

  - id: p5-var-greeks
    content: |
      - [ ] [AGENT] P2. Greeks-based risk. Portfolio-level Greeks aggregation.
        Delta-gamma VaR approximation. Wire into monitoring UI.
    status: todo
    note: "PARALLEL stream C."

  - id: p5-var-attribution
    content: |
      - [ ] [AGENT] P2. VaR attribution — per-position, per-venue, per-strategy.
        Populate VaRResult.component_var field.
    status: todo
    note: "PARALLEL stream C."

  - id: p5-var-regime-detection
    content: |
      - [ ] [AGENT] P2. Automated regime detection from VIX, correlation regime changes,
        drawdown velocity. Auto-set regime multiplier.
    status: todo
    note: "PARALLEL stream C."

  # --- Stream D: Risk Matrix & P&L Attribution Framework ---
  # Full multi-dimensional risk decomposition with strategy-risk subscription.
  # Every risk has a corresponding P&L — same decomposition, different lens.

  - id: p5-risk-taxonomy-schema
    content: |
      - [ ] [AGENT] P0. Define comprehensive RiskType enum in UIC with ALL risk dimensions:
        FIRST ORDER: delta, vega, theta, rho, funding, basis, carry, fx, liquidity
        SECOND ORDER: gamma, volga (vol-of-vol), vanna (delta-vol cross), slide (vol time decay)
        STRUCTURAL: duration, convexity, spread (bid-ask / credit), concentration
        OPERATIONAL: venue_protocol (exchange/protocol downtime), correlation
        DOMAIN-SPECIFIC: edge_decay (sports), market_suspension (sports),
        protocol_risk (DeFi smart contract), impermanent_loss (DeFi LP)
        Each RiskType maps to a P&L attribution dimension.
        Repos: unified-internal-contracts (schema), unified-api-contracts (re-export if external).
    status: todo
    note: "PARALLEL stream D. Foundation for everything else in this stream."

  - id: p5-risk-strategy-subscription
    content: |
      - [ ] [AGENT] P0. Create StrategyRiskSubscription model in UIC — strategies subscribe
        to relevant risk types, irrelevant ones are zero in the risk matrix.
        Strategy type → subscribed RiskTypes:
        - MOM (momentum spot/perp): delta, funding, liquidity, venue, concentration, fx
        - BASIS (basis trade): basis, funding, duration, venue, liquidity, carry
        - YIELD (DeFi lending/staking): delta, protocol_risk, liquidity, concentration, fx
        - OPTIONS: delta, gamma, vega, theta, rho, volga, vanna, slide, duration, venue
        - SPORTS: edge_decay, market_suspension, concentration, liquidity
        - ARB: delta (hedged→~0), venue, liquidity, spread, correlation
        Config-driven: YAML/JSON per strategy, loadable at runtime. Not hardcoded.
        Repos: unified-internal-contracts (schema), unified-config-interface (config loader).
    status: todo
    note: "PARALLEL stream D. Strategies declare which risks apply to them."

  - id: p5-risk-aggregation-hierarchy
    content: |
      - [ ] [AGENT] P0. Define aggregation hierarchy for risk and P&L in UIC:
        Company → Client → Account → Strategy → Underlying → Instrument
        Each level aggregates from the level below. Fields per level:
        - risk_by_type: dict[RiskType, Decimal] (exposure per risk dimension)
        - pnl_by_type: dict[RiskType, Decimal] (P&L attributed to each risk)
        - var_by_type: dict[RiskType, Decimal] (marginal VaR per risk dimension)
        Term structure bucketing: overnight, 1w, 1m, 3m, 6m, 1y, 2y+ (for duration)
        Delta bucketing: by strike/moneyness (for options)
        Client ≠ account — a client can have multiple accounts across venues.
        Repos: unified-internal-contracts (schemas), position-balance-monitor-service (aggregation).
    status: todo
    note: "PARALLEL stream D."

  - id: p5-risk-venue-protocol-risk
    content: |
      - [ ] [AGENT] P1. Add venue/protocol risk dimension. Per venue:
        - Circuit breaker state (CLOSED/DEGRADED/OPEN) → risk score
        - Historical downtime frequency/duration
        - Concentration in that venue (% of total exposure)
        - DeFi: smart contract audit status, TVL trend, oracle dependency
        Risk metric: "if this venue goes down for N hours, what's our max loss?"
        Feeds into VaR scenarios: venue-down stress test.
        Repos: risk-and-exposure-service, execution-service (circuit breaker state).
    status: todo
    note: "PARALLEL stream D."

  - id: p5-risk-duration-convexity
    content: |
      - [ ] [AGENT] P1. Add duration and convexity risk for term-structure instruments:
        - Spot: duration = 0 (no term structure sensitivity)
        - Perpetuals: duration ≈ 0 (swap-like, funding rate resets)
        - Expiry futures: duration = days to expiry (basis point sensitivity)
        - Options: duration from delta × underlying duration + rho exposure
        - DeFi lending: duration = lock period / unbonding period
        Term structure risk: what if rates at the back of the curve change?
        Separate from rho (parallel shift) — duration measures curve shape sensitivity.
        Repos: risk-and-exposure-service, unified-internal-contracts.
    status: todo
    note: "PARALLEL stream D."

  - id: p5-risk-volga-slide
    content: |
      - [ ] [AGENT] P1. Add second-order vol risks for options strategies:
        - Volga (vol-of-vol): d²V/d²σ — P&L from volatility convexity
        - Vanna (delta-vol cross): d²V/(dS·dσ) — delta sensitivity to vol changes
        - Slide: vol surface decay — what happens to our P&L as vol surface ages
          (front vol decays faster than back vol)
        These are zero for non-options strategies (subscription model handles this).
        Repos: risk-and-exposure-service (computation), unified-internal-contracts (schema).
    status: todo
    note: "PARALLEL stream D."

  - id: p5-risk-spread-risk
    content: |
      - [ ] [AGENT] P1. Add spread risk for arb and relative-value strategies:
        - Bid-ask spread widening risk (liquidity crisis → spreads blow out)
        - Cross-venue spread risk (price divergence between venues)
        - Term structure spread risk (contango/backwardation changes)
        - DeFi: oracle spread risk (price oracle vs market price divergence)
        Repos: risk-and-exposure-service, unified-internal-contracts.
    status: todo
    note: "PARALLEL stream D."

  - id: p5-risk-pnl-attribution-engine
    content: |
      - [ ] [AGENT] P1. Build P&L attribution engine that decomposes total P&L into
        contributions from each RiskType the strategy is subscribed to:
        total_pnl = delta_pnl + gamma_pnl + vega_pnl + theta_pnl + rho_pnl
                   + volga_pnl + vanna_pnl + funding_pnl + basis_pnl + carry_pnl
                   + fx_pnl + spread_pnl + fees + residual
        Aggregates up the hierarchy: instrument → strategy → account → client → company.
        Residual = unexplained P&L (should be small; large residual = missing risk factor).
        Time series: store daily snapshots for over-time analysis.
        Repos: risk-and-exposure-service (or new pnl-attribution-service), PBMS (position data).
    status: todo
    note: "PARALLEL stream D."

  - id: p5-risk-custom-risk-types
    content: |
      - [ ] [AGENT] P1. Add custom/strategy-specific risk types with hot-reloadable parameters.
        TWO-LAYER ARCHITECTURE:
        FIXED (schema in UIC, needs restart to add new risk_type):
        - CustomRiskType schema: name, risk_type (StrEnum), evaluation_method,
          applicable_strategy_types, description
        - Evaluation methods: rate_sensitivity (what if rate X changes by Y?),
          scenario_pnl (what's daily P&L under scenario?), threshold_breach
          (at what rate does P&L turn negative?)
        - New risk_type = new evaluation logic = code change + restart. That's fine.
        DYNAMIC (parameters in GCS, hot-reloadable via UCI):
        - CustomRiskScenarioConfig in UCI config.py: validates YAML structure
        - GCS path: gs://config/{strategy_id}/custom_risks.yaml
        - Contains: shock values, thresholds, underlying instruments, metric to compute
        - UCI hot-reloads on change — no restart needed to change "1% shock" to "2% shock"
        EXAMPLES:
        - Recursive basis: "ETH borrow rate +100bp → daily P&L change?" (rate_sensitivity)
        - Basis trade: "BTC funding rate inverts → daily carry P&L?" (rate_sensitivity)
        - DeFi yield: "AAVE utilization hits 95% → borrow rate spike?" (threshold_breach)
        - Sports: "edge decays to 0.5% → break-even volume?" (threshold_breach)
        UI: dropdown per strategy shows subscribed standard risks + custom risks with
        user-friendly names (not "custom_risk_1" but "ETH Borrow Rate Sensitivity").
        Repos: unified-internal-contracts (CustomRiskType schema),
        unified-config-interface (CustomRiskScenarioConfig, GCS loader),
        risk-and-exposure-service (evaluation engine),
        strategy-service (strategy-specific evaluation hooks).
    status: todo
    note: "PARALLEL stream D. Risk types fixed (restart). Parameters dynamic (hot-reload)."

  - id: p5-risk-matrix-visualization
    content: |
      - [ ] [HUMAN+AGENT] P1. Build risk matrix + P&L attribution views in monitoring UI:
        RISK MATRIX VIEW:
        - Heatmap: rows=instruments/strategies, cols=risk types, cells=exposure magnitude
        - Filterable by: company/client/account/strategy/instrument/underlying
        - Term structure view: duration buckets (O/N, 1w, 1m, 3m, 6m, 1y, 2y+)
        - Delta bucket view: by moneyness for options
        - Venue risk panel: circuit breaker states, concentration, downtime history
        - Zero cells where strategy doesn't subscribe to that risk type (greyed out)
        P&L ATTRIBUTION VIEW:
        - Waterfall: delta→gamma→vega→theta→volga→funding→basis→carry→fx→spread→fees→residual
        - Over-time: stacked area chart of P&L contributions by risk type
        - Drill: click any bar to see instrument-level breakdown
        - Aggregation toggle: company / client / account / strategy / instrument
        SPORTS RISK VIEW: edge decay curves, market suspension risk, settlement exposure
        OPTIONS RISK VIEW: Greeks surface, vol smile, term structure, volga/vanna
        DeFi RISK VIEW: protocol risk scores, TVL exposure, impermanent loss tracking
        Data: risk-service APIs, PBMS, strategy-service.
    status: todo
    note: "PARALLEL stream D. The crown jewel — full risk visibility."

  # =========================================================================
  # PHASE 6: FINAL VALIDATION (sequential — everything must pass)
  # =========================================================================

  - id: p6-workspace-wide-qg
    content: |
      - [ ] [AGENT] P0. Final quality gates on ALL modified repos:
        unified-api-contracts, unified-internal-contracts, risk-and-exposure-service,
        execution-service, trading-analytics-api, market-data-processing-service,
        unified-market-interface, unified-trading-library.
        Each: `cd <repo> && bash scripts/quality-gates.sh`
        Only mark plan complete when ALL pass.
    status: todo
    note: "SEQUENTIAL — final gate."

isProject: false
---

# Contracts, Observability & Risk Cleanup Plan

## Execution Model

```
PHASE 1 (parallel)          PHASE 2 (parallel)       PHASE 3 (parallel)
┌─ p1a delete dup pkg       ┌─ p2a UIC risk schemas   ┌─ p3a delete UAC risk.py
├─ p1b dedup ErrorAction     ├─ p2b UIC correlation    └─ p3b fix analytics split
├─ p1c rm coinglass/hyblock  └─ p2c cleanup UIC WS          │
├─ p1d rm sports_generic          │                    p3-QG-UAC ──────┐
├─ p1e prune WS symbols      p2-QG-UIC ───┐                          │
└─ p1f recategorize venues         │       │           PHASE 4 (parallel)
      │                            │       │           ┌─ p4a fix trading-analytics-api
p1-QG-UAC ─────────────────────────┘       │           ├─ p4b fix market-data-proc
                                           │           └─ p4c add venues to registry
                                           │                 │
                                           │           p4-QG-downstream ──┐
                                           │                              │
PHASE 5 (3 parallel streams, independent of P1-P4 for obs/CB/VaR)       │
Stream A: Observability (7 items)                                        │
Stream B: Circuit Breaker Citadel (5 items)                              │
Stream C: VaR Phase 2 (6 items)                                          │
      │                                                                  │
PHASE 6: Final workspace-wide QG ◄───────────────────────────────────────┘
```

## Pre-Audit Manifest (2026-03-16)

### Downstream Blast Radius

| Repo                               | Files Breaking                        | Changes Needed                                                       |
| ---------------------------------- | ------------------------------------- | -------------------------------------------------------------------- |
| **trading-analytics-api**          | `contracts.py:8-22`                   | Correlation\* imports: UAC → UIC                                     |
| **market-data-processing-service** | `types.py:19`                         | Correlation\*/FactorType: UAC → UIC                                  |
| **ml-training-service**            | NONE                                  | Already imports from UIC                                             |
| **strategy-service**               | NONE                                  | Already imports from UIC                                             |
| **risk-and-exposure-service**      | `var_calculator.py:34`, `api/main.py` | ADOPT — replace local StressScenario Literal + align VaRResponse DTO |
| **trading-analytics-ui**           | `src/types/` (new)                    | ADD — TypeScript interfaces for risk/analytics/P&L schemas           |
| **execution-service**              | NONE                                  | Imports from UIC correctly                                           |
| **All other services**             | NONE                                  | No imports of moved symbols                                          |

### File Size Compliance (pre-checked)

| File                                      | Current | After | Limit | Safe? | Note                                      |
| ----------------------------------------- | ------- | ----- | ----- | ----- | ----------------------------------------- |
| UAC `__init__.py`                         | **896** | ~846  | 900   | YES   | Was 4 lines from limit — removal fixes it |
| UIC `risk.py` (re-export)                 | 291     | ~391  | 900   | YES   | 509 line buffer                           |
| UIC `domain/risk_service/risk.py`         | 308     | ~408  | 900   | YES   | 492 line buffer                           |
| UIC `domain/analytics/factor_exposure.py` | 68      | ~118  | 900   | YES   | 782 line buffer                           |
| UIC `__init__.py`                         | 717     | ~767  | 900   | YES   | 133 line buffer                           |
| UAC `analytics.py`                        | 202     | ~102  | 900   | YES   | Shrinking                                 |
| UAC `connectivity.py`                     | 116     | ~66   | 900   | YES   | Shrinking                                 |

No basedpyright baselines exist (zero-baseline policy). UIC coverage floor: 98% — new schemas need tests.

### UAC Internal Edits (by file)

| File                               | Symbols to Remove                                         | Plan Item          |
| ---------------------------------- | --------------------------------------------------------- | ------------------ |
| `__init__.py` (root)               | 10 risk + 7 analytics + 7 WS = 24 symbols from re-exports | p3a, p3b, p1e      |
| `canonical/__init__.py`            | Same 24 symbols from re-exports; fix line 147 import path | p3a, p3b, p1e, p1a |
| `canonical/domain/__init__.py`     | Remove crosscutting.risk/analytics/connectivity imports   | p3a, p3b, p1e      |
| `crosscutting/risk.py`             | DELETE entire file                                        | p3a                |
| `crosscutting/analytics.py`        | Remove 7 of 13 symbols (keep 6 external)                  | p3b                |
| `crosscutting/connectivity.py`     | Remove 7 of 12 symbols (keep 5 active)                    | p1e                |
| `crosscutting/errors/altdata.py`   | Remove coinglass, hyblock, versifi                        | p1c                |
| `crosscutting/errors/sports.py`    | Remove sports_generic                                     | p1d                |
| `tests/test_contract_alignment.py` | Remove deleted WS symbol test cases                       | p1e                |
| `scripts/check_uac_adoption.py`    | Remove symbol names from checker                          | p1e                |
| `external/open_meteo/schemas.py`   | Fix import path                                           | p1a                |

### UIC Additions (by file)

| File                            | Schemas to Add                                                                                                                      | Plan Item |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | --------- |
| `domain/risk_service/risk.py`   | VaRMethod, VaRRequest, VaRResult, StressScenario, StressTestResult, PnLAttributionRecord, RealTimePnLRecord, RiskLimitBreach fields | p2a       |
| `domain/analytics/`             | CorrelationRegime, CrossAssetCorrelationMatrix, CorrelationRegimeChange                                                             | p2b       |
| `domain/websocket/lifecycle.py` | Remove WebSocketPingFrame, WebSocketPongFrame                                                                                       | p2c       |

### Venue Disposition Table

| Venue                                     | Current File | Action | Target                                   |
| ----------------------------------------- | ------------ | ------ | ---------------------------------------- |
| tardis,yahoo_finance,ibkr,databento       | cefi.py      | MOVE   | tradfi.py                                |
| barchart,fred,ecb,ofr,openbb              | altdata.py   | MOVE   | tradfi.py                                |
| hyperliquid,aster                         | altdata.py   | MOVE   | onchain_perps.py                         |
| aave_v3                                   | altdata.py   | MOVE   | defi.py                                  |
| instadapp,defillama                       | sports.py    | MOVE   | defi.py                                  |
| glassnode,arkham                          | sports.py    | MOVE   | altdata.py; ADD to VENUE_REGISTRY        |
| alchemy,thegraph,bloxroute                | cefi/altdata | MOVE   | infra.py; ADD to INFRA_PROVIDER_REGISTRY |
| polymarket,betfair,kalshi,smarkets,betdaq | sports.py    | KEEP   | sports.py; ADD to VENUE_REGISTRY         |
| coinglass,hyblock,versifi                 | altdata.py   | DELETE | Own liquidation prediction               |
| sports_generic                            | sports.py    | DELETE | Fallback template, not a venue           |
| onchain_revert                            | sports.py    | MOVE   | crosscutting (generic EVM handler)       |
| balancer–uniswap_v4 (11)                  | defi.py      | KEEP   | defi.py (correct)                        |
| binance–upbit (7 CeFi)                    | cefi.py      | KEEP   | cefi.py (correct)                        |

### External vs Internal Rule

UAC = normalizing external API data (venue feeds, alt data providers). UIC = internal computations and inter-service
contracts.

| Schema Category                                                              | Belongs In | Reason                             |
| ---------------------------------------------------------------------------- | ---------- | ---------------------------------- |
| SentimentScore, SatelliteObservation, OptionsFlowRecord, DarkPoolPrintRecord | UAC        | External data normalization        |
| FactorType, FactorExposure, FactorAttribution\*                              | UIC (SSOT) | Internal factor models             |
| CorrelationRegime, CrossAssetCorrelationMatrix                               | UIC        | Internal computation               |
| VaR*, StressScenario, PnLAttribution*                                        | UIC        | Internal risk computation          |
| ErrorAction, VenueErrorClassification, CanonicalError\*                      | UAC        | External venue error normalization |
| HttpRateLimitHeaders, VenueRateLimitSpec                                     | UAC        | External rate limit headers        |
| LatencyPercentile, TickToTradeMetric, OrderLatencyRecord                     | UAC        | External venue latency measurement |
| WebSocketEvent, CanonicalWebSocketLifecycle                                  | UAC        | External WS event normalization    |

---
doc_type: plan
title: contracts-observability-risk-cleanup
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, market-data-processing-service, strategy-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-16'
overview: 'Comprehensive cleanup, observability, circuit breaker hardening, and risk expansion.

  Phased execution DAG with pre-audit manifest — agents execute from manifest, no re-scanning.

  Phase 1: UAC internal cleanup (no downstream impact, parallel).

  Phase 2: UIC receives schemas + QG UIC.

  Phase 3: UAC removes moved schemas + QG UAC + cassette parity.

  Phase 4: Downstream fixes (2 repos, parallel) + QG per repo.

  Phase 5: Observability, circuit breaker citadel-grade, VaR Phase 2.

  Phase 6: Final workspace-wide QG.

  '
type: mixed
epic: epic-code-completion
completion_gates: {code: C5, deployment: D2, business: none}
repo_gates:
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: unified-internal-contracts, code: C0, deployment: none, business: none}
- {repo: risk-and-exposure-service, code: C0, deployment: none, business: none}
- {repo: execution-service, code: C3, deployment: none, business: none}
- {repo: trading-analytics-api, code: C0, deployment: none, business: none}
- {repo: market-data-processing-service, code: C0, deployment: none, business: none}
- {repo: unified-trading-library, code: C0, deployment: none, business: none}
- {repo: unified-market-interface, code: C0, deployment: none, business: none}
- {repo: live-health-monitoring-ui, code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: p1a-delete-duplicate-errors-package, content: "- [x] [AGENT] P0. Delete `canonical/errors/` (byte-for-byte duplicate of crosscutting).\n  PRE-AUDIT: 2 stale imports to redirect first:\n  1. `canonical/__init__.py:147` → `from .crosscutting.errors import`\n  2. `external/open_meteo/schemas.py:15` → same\n  Then delete entire `canonical/errors/` directory.\n", status: done, note: PARALLEL with p1b-p1f. No downstream impact.}
- {id: p1b-deduplicate-erroraction, content: "- [x] [AGENT] P0. In `crosscutting/errors/_canonical.py`, delete duplicate ErrorAction\n  and VenueErrorClassification definitions. Import from `._types` instead.\n", status: done, note: PARALLEL. Internal only.}
- {id: p1c-remove-coinglass-hyblock-versifi, content: "- [x] [AGENT] P0. Delete from UAC entirely:\n  - `crosscutting/errors/altdata.py`: remove coinglass, hyblock, versifi entries\n  - `docs/VERSIFI_INTEGRATION.md`: delete file\n  - `COVERAGE_AUDIT.md`: remove coinglass reference\n  - `docs/UAC_FULL_GAP_ANALYSIS_AND_BATCH_LIVE_SYMMETRY.md`: remove versifi refs\n  No downstream service imports these.\n", status: done, note: 'PARALLEL. Decision: own liquidation prediction system.'}
- {id: p1d-delete-sports-generic, content: "- [x] [AGENT] P0. Delete `sports_generic` from `crosscutting/errors/sports.py`.\n  Fallback template — each venue should have proper venue-specific error codes.\n  No downstream service imports this.\n", status: done, note: PARALLEL.}
- {id: p1e-prune-dead-connectivity-symbols, content: "- [x] [AGENT] P1. Remove 7 dead symbols from `crosscutting/connectivity.py`:\n  DELETE: WebSocketPingFrame, WebSocketPongFrame, UnsubscribeRequest, SubscribeRequest,\n  HeartbeatMessage, WebSocketConnectionState, CanonicalWsMessage.\n  PRE-AUDIT: No service imports these. Update:\n  - `tests/test_contract_alignment.py:71,77,79,92,94-95` — delete test cases\n  - `scripts/check_uac_adoption.py:106,108` — remove symbol names\n  - Root `__init__.py` lines 166,233,254,256-257 — remove re-exports\n  - `canonical/__init__.py` lines 113,128,262,277 — remove re-exports\n  - `canonical/domain/__init__.py` lines 23,27,461,482 — remove imports\n  KEEP: WebSocketEvent, CanonicalWebSocketLifecycle, HealthPingResponse,\n  WebSocketConnectionOpened, WebSocketConnectionClosed.\n", status: done, note: PARALLEL. No downstream impact — all dead symbols.}
- {id: p1f-recategorize-venue-errors, content: "- [x] [AGENT] P1. Re-categorize venue error files:\n  CREATE `errors/tradfi.py`: move tardis,yahoo_finance,ibkr,databento from cefi.py;\n  barchart,fred,ecb,ofr,openbb from altdata.py.\n  CREATE `errors/onchain_perps.py`: move hyperliquid,aster from altdata.py.\n  CREATE `errors/infra.py`: move alchemy,thegraph from cefi.py; bloxroute from altdata.py.\n  MOVE to defi.py: aave_v3 from altdata.py; instadapp,defillama from sports.py.\n  MOVE to altdata.py: glassnode,arkham from sports.py.\n  MOVE onchain_revert from sports.py to own crosscutting section.\n  UPDATE `errors/__init__.py`: import new files, update VENUE_ERROR_MAP.\n", status: done, note: PARALLEL. Internal reorganization only.}
- {id: p1-qg-uac-internal, content: "- [x] [AGENT] P0. GATE: `cd unified-api-contracts && bash scripts/quality-gates.sh`.\n  Must pass before Phase 2. Validates all Phase 1 changes are clean.\n", status: done, note: SEQUENTIAL — runs after ALL p1a-p1f complete.}
- {id: p2a-uic-add-risk-schemas, content: "- [x] [AGENT] P0. Add to UIC `domain/risk_service/risk.py`:\n  - VaRMethod (StrEnum), VaRRequest, VaRResult (align with existing var_calculator.py)\n  - StressScenario, StressTestResult\n  - PnLAttributionRecord (complement existing PnLBreakdown)\n  - RealTimePnLRecord\n  - RiskLimitBreach → consolidate with existing AlertMessage (add breach_pct,\n    recommended_action, auto_halt_triggered fields to AlertMessage or subclass)\n  SpanMarginLeg and MultiAssetMarginCalculation already in UIC — no action.\n  Export all new types from `risk.py`, `domain/risk_service/__init__.py`, root `__init__.py`.\n", status: done, note: PARALLEL with p2b-p2c.}
- {id: p2b-uic-add-correlation-schemas, content: "- [x] [AGENT] P0. Add to UIC `domain/analytics/`:\n  - CorrelationRegime (StrEnum: LOW, NORMAL, HIGH, CRISIS)\n  - CrossAssetCorrelationMatrix\n  - CorrelationRegimeChange\n  Export from `domain/analytics/__init__.py` and root `__init__.py`.\n", status: done, note: 'PARALLEL with p2a,p2c.'}
- {id: p2c-uic-cleanup-dead-ws-types, content: "- [x] [AGENT] P1. In UIC `domain/websocket/lifecycle.py`:\n  Delete WebSocketPingFrame, WebSocketPongFrame (dead in both UAC and UIC).\n  Keep HealthPingResponse, WebSocketConnectionOpened, WebSocketConnectionClosed.\n  Update `domain/websocket/__init__.py` exports.\n", status: done, note: 'PARALLEL with p2a,p2b.'}
- {id: p2-qg-uic, content: "- [x] [AGENT] P0. GATE: `cd unified-internal-contracts && bash scripts/quality-gates.sh`.\n  Must pass before Phase 3. Validates new schemas are correct.\n", status: done, note: SEQUENTIAL — runs after ALL p2a-p2c complete.}
- {id: p3a-delete-uac-risk-module, content: "- [x] [AGENT] P0. Delete `canonical/crosscutting/risk.py` entirely.\n  PRE-AUDIT — remove from these re-export chains:\n  - Root `__init__.py:182,204-215,222,229-230,241-243` — remove 10 risk symbols\n  - Root `__init__.py __all__` — remove same\n  - `canonical/__init__.py:46,113-128,262-277` — remove risk re-exports\n  - `canonical/domain/__init__.py:3,46,461,482` — remove crosscutting.risk imports\n  - `crosscutting/__init__.py` — remove risk import if present\n", status: done, note: PARALLEL with p3b.}
- {id: p3b-fix-uac-analytics-split, content: "- [x] [AGENT] P0. In `crosscutting/analytics.py`:\n  DELETE: FactorType, FactorExposure, FactorAttributionRecord, FactorAttributionModel\n  (UIC is SSOT — UAC had duplicate definitions)\n  DELETE: CorrelationRegime, CrossAssetCorrelationMatrix, CorrelationRegimeChange\n  (moved to UIC in Phase 2)\n  KEEP: AlternativeDataType, AlternativeDataSignal, SentimentScore,\n  SatelliteObservation, OptionsFlowRecord, DarkPoolPrintRecord (external normalization)\n  Update re-export chains:\n  - Root `__init__.py:157-160` — remove Factor*/Correlation* from domain imports\n  - `canonical/__init__.py:137-139` — remove same\n  - `canonical/domain/__init__.py:3-6` — remove crosscutting.analytics Factor*/Corr imports\n", status: done, note: PARALLEL with p3a.}
- {id: p3-qg-uac-final, content: "- [x] [AGENT] P0. GATE: `cd unified-api-contracts && bash scripts/quality-gates.sh`.\n  Run cassette parity: `pytest tests/test_cassette_schema_parity.py`.\n  Must pass before Phase 4.\n", status: done, note: SEQUENTIAL — runs after p3a+p3b complete.}
- {id: p4a-fix-trading-analytics-api, content: "- [x] [AGENT] P0. Fix `trading-analytics-api/trading_analytics_api/contracts.py:8-22`:\n  CHANGE: Remove `from unified_api_contracts import (CorrelationRegime,\n  CrossAssetCorrelationMatrix, CorrelationRegimeChange, ...)`\n  ADD: `from unified_internal_contracts import (CorrelationRegime,\n  CrossAssetCorrelationMatrix, CorrelationRegimeChange)`\n  Factor* imports already correct (from UIC). Update `__all__:24-36`.\n  Run: `cd trading-analytics-api && bash scripts/quality-gates.sh`\n", status: done, note: PARALLEL with p4b-p4e.}
- {id: p4b-fix-market-data-processing-service, content: "- [x] [AGENT] P0. Fix `market-data-processing-service/market_data_processing_service/types.py:19`:\n  CHANGE: Remove Correlation*/FactorType from UAC import.\n  ADD: `from unified_internal_contracts import (CorrelationRegime,\n  CrossAssetCorrelationMatrix, FactorType)` (if needed, or remove if unused).\n  Update `__all__:31`.\n  Run: `cd market-data-processing-service && bash scripts/quality-gates.sh`\n", status: done, note: 'PARALLEL with p4a,p4c-p4e.'}
- {id: p4c-risk-service-adopt-uic-schemas, content: "- [x] [AGENT] P0. Adopt UIC schemas in risk-and-exposure-service (doesn't break but\n  has local type duplication that SHOULD import from UIC):\n  1. `var_calculator.py:34` — replace `StressScenario = Literal[\"GFC_2008\", ...]`\n     with import from UIC: `from unified_internal_contracts import StressScenario`\n     (after p2a adds it as a StrEnum to UIC)\n  2. `api/main.py` — VaRResponse DTO: align field types with UIC VaRResult\n     (float→Decimal for var/cvar, add portfolio_id, computed_at).\n     VaRResponse as HTTP DTO can differ from domain schema but must document mapping.\n  Run: `cd risk-and-exposure-service && bash scripts/quality-gates.sh`\n", status: done, note: 'PARALLEL. Adoption — doesn''t break, but eliminates self-declared types.'}
- {id: p4d-trading-analytics-ui-types, content: "- [x] [AGENT] P1. Add TypeScript type mirrors in trading-analytics-ui for schemas\n  exposed by trading-analytics-api. Currently TradingDeskPage.tsx has mock Position\n  with flat unrealizedPnl — no Greeks, no factor attribution, no correlation types.\n  ADD `src/types/risk.ts`: VaRResult, StressTestResult, RiskLimitBreach interfaces\n  ADD `src/types/analytics.ts`: CorrelationRegime enum, CrossAssetCorrelationMatrix,\n  FactorType enum, FactorExposure, FactorAttributionRecord interfaces\n  ADD `src/types/pnl.ts`: PnLAttributionRecord (delta/gamma/vega/theta/rho/basis/\n  funding/carry/fees breakdown), RealTimePnLRecord\n  Source: mirror UIC Python schemas → TypeScript interfaces.\n  Run: `cd trading-analytics-ui && CI=true npm test -- --run`\n", status: done, note: PARALLEL. UIs currently have zero typed risk/analytics interfaces.}
- {id: p4f-add-venues-to-registry, content: "- [x] [AGENT] P1. Add to UMI VENUE_REGISTRY (factory.py):\n  - polymarket, betfair, kalshi, smarkets, betdaq (prediction markets/sports)\n  - glassnode, arkham (onchain analytics)\n  Create INFRA_PROVIDER_REGISTRY alongside VENUE_REGISTRY:\n  - alchemy (Ethereum RPC), thegraph (subgraph indexer), bloxroute (MEV relay)\n  Key semantic: venues = trade on them. infra = pipes to reach venues.\n  Instadapp IS a venue (DSA contracts) but USES thegraph as pipe.\n  ALSO: Add SourceCapability declarations in UAC\n  registry/capability_declarations/_sports.py and _defi.py for each new venue\n  (supports_testnet, auth_scope, auth_environments). Without these, preflight\n  validation in get_adapter() will reject the new venues.\n", status: done, note: PARALLEL with p4a-p4d.}
- {id: p4-qg-downstream, content: "- [x] [AGENT] P0. GATE: Quality gates on all Phase 4 repos.\n  `cd trading-analytics-api && bash scripts/quality-gates.sh`\n  `cd market-data-processing-service && bash scripts/quality-gates.sh`\n  `cd unified-market-interface && bash scripts/quality-gates.sh`\n", status: done, note: SEQUENTIAL — runs after p4a-p4f complete.}
---

 Stream A: Observability ---

  - id: p5-obs-prometheus-bridge
    content: |
      - [x] [AGENT] P1. Wire Prometheus → Cloud Monitoring. Extend UTL setup_tracing()
        to setup_metrics(). OTEL Collector sidecar with remote_write to GCP.
        Repos: unified-trading-library, deployment-service.
    status: done
    note: "PARALLEL stream A."

  - id: p5-obs-restart-detection
    content: |
      - [x] [AGENT] P1. Add RESTART_DETECTED lifecycle event to UIC. On STARTED, check for
        missing STOPPED event (unclean shutdown). Emit with restart_count.
        Add restart_count to /health response. Wire into all services.
    status: done
    note: "PARALLEL stream A."

  - id: p5-obs-latency-profiling
    content: |
      - [x] [AGENT] P1. Wire UAC latency schemas into production measurement code.
        execution-service order path: tick→signal→risk→encode→send→ack→fill.
        Populate OrderLatencyRecord, write to GCS, publish LatencyBenchmarkReport.
    status: done
    note: "PARALLEL stream A."

  - id: p5-obs-resource-metrics
    content: |
      - [x] [AGENT] P1. Add CPU/memory/connections/queue gauges to all services.
        Include shard_id label for batch, venue_id for live.
    status: done
    note: "PARALLEL stream A."

  - id: p5-obs-monitoring-ui
    content: |
      - [x] [HUMAN+AGENT] P1. Build live health monitoring UI. Lifecycle timeline, latency
        charts, VaR dashboard, P&L waterfall, resource gauges, risk alerts, batch tracker.
        React+Vite. Data: GCS JSONL, Prometheus, risk-service API, PBMS API.
    status: done
    note: "PARALLEL stream A."

  - id: p5-obs-cloud-backup
    content: |
      - [x] [HUMAN+AGENT] P1. Cloud Monitoring backup: uptime checks, log-based alerts,
        container restart detection. Independent safety net.
    status: done
    note: "PARALLEL stream A."

  - id: p5-obs-alert-rules
    content: |
      - [x] [AGENT] P2. Define alert rules: restart>3/hr, p99>500ms, VaR>90%, breaker OPEN,
        kill switch, FAILED events, batch deadline miss. YAML config for both UI and cloud.
    status: done
    note: "PARALLEL stream A."

  # --- Stream B: Circuit Breaker Citadel Grade ---

  - id: p5-cb-degraded-throttling
    content: |
      - [x] [AGENT] P1. Activate DEGRADED throughput throttling. Config field
        `degraded_rate_limit_pct: 0.5` exists but is NOT IMPLEMENTED. When DEGRADED:
        probabilistic drop ~50% of orders to reduce venue pressure. Token bucket.
        Repo: execution-service (circuit_breaker.py).
    status: done
    note: "PARALLEL stream B."

  - id: p5-cb-order-queuing
    content: |
      - [x] [AGENT] P1. Add order queue for OPEN state. Currently orders rejected immediately.
        Queue with: max depth (100), max age (5min), priority ordering (hedge>spec),
        overflow reject. Drain on HALF_OPEN→CLOSED, respecting rate limits.
        Repo: execution-service.
    status: done
    note: "PARALLEL stream B."

  - id: p5-cb-kill-switch-auto-deactivate
    content: |
      - [x] [AGENT] P1. Add timed auto-deactivation for kill switch. Optional
        `auto_deactivate_after_minutes` on activation. After timeout: deactivates,
        emits KILL_SWITCH_AUTO_DEACTIVATED. Also: activation via alert rules
        (VaR>150% → kill switch with 30min auto-deactivate).
        Repo: execution-service (kill_switch.py).
    status: done
    note: "PARALLEL stream B. 3am Sunday recovery."

  - id: p5-cb-venue-failover
    content: |
      - [x] [AGENT] P2. Venue failover routing when breaker OPEN. Failover pairs
        (Binance→Bybit for BTC spot). Per-instrument, price tolerance check.
        Repo: execution-service (orchestrator.py), unified-config-interface.
    status: done
    note: "PARALLEL stream B."

  - id: p5-cb-strategy-priority
    content: |
      - [x] [AGENT] P2. Strategy-level priority in DEGRADED/queued states.
        P0=hedge, P1=rebalance, P2=new positions. P0 always passes throttle.
        Queue: P0 front, P2 back, oldest P2 cancelled first on overflow.
        Repo: execution-service.
    status: done
    note: "PARALLEL stream B."

  # --- Stream C: VaR / Risk Phase 2 ---

  - id: p5-var-returns-ingestion
    content: |
      - [x] [AGENT] P1. Automated historical returns ingestion from PBMS. Store daily
        returns per instrument in GCS. Risk service fetches on demand.
        Repos: risk-and-exposure-service, position-balance-monitor-service.
    status: done
    note: "PARALLEL stream C."

  - id: p5-var-monte-carlo
    content: |
      - [x] [AGENT] P2. Monte Carlo VaR simulation. Pure stdlib. Random gen + Cholesky
        decomposition. Add VaRMethod.MONTE_CARLO. Wire into /risk/var endpoint.
    status: done
    note: "PARALLEL stream C."

  - id: p5-var-copula-correlation
    content: |
      - [x] [AGENT] P2. Copula-based multi-asset correlation. Rolling correlation matrix
        from returns. Feed into MC simulation.
    status: done
    note: "PARALLEL stream C."

  - id: p5-var-greeks
    content: |
      - [x] [AGENT] P2. Greeks-based risk. Portfolio-level Greeks aggregation.
        Delta-gamma VaR approximation. Wire into monitoring UI.
    status: done
    note: "PARALLEL stream C."

  - id: p5-var-attribution
    content: |
      - [x] [AGENT] P2. VaR attribution — per-position, per-venue, per-strategy.
        Populate VaRResult.component_var field.
    status: done
    note: "PARALLEL stream C."

  - id: p5-var-regime-detection
    content: |
      - [x] [AGENT] P2. Automated regime detection from VIX, correlation regime changes,
        drawdown velocity. Auto-set regime multiplier.
    status: done
    note: "PARALLEL stream C."

  - id: p5-rva-index-cross-protocol
    content: |
      - [x] [AGENT] P2. Implement RVA (Realized Value Appreciation) index for non-Aave protocols.
        Aave uses liquidity_index (correct — tracks compounding on-chain). All other protocols
        (Morpho, Euler, Fluid, Curve, Lido, EtherFi, Ethena) use snapshot APYs — less accurate
        for cross-protocol PnL comparison across different APY volatility profiles.
        Create cumulative yield index per vault/position:
        rva_index(t) = rva_index(t-1) * (1 + apy(t) * dt / 365)
        This converts point-in-time APY snapshots into a monotonically increasing index
        analogous to Aave's liquidity_index. Then PnL = amount * (rva_current / rva_entry - 1).
        Schema in UIC: RVAIndex(protocol, asset, chain, timestamp, index_value, source_apy).
        Storage: BigQuery table alongside APYTimeSeries (from defi_keys plan).
        Computation: features-onchain-service computes per-candle from APY snapshots.
        Wire into PnLCalculator: use RVA index for non-Aave lending/staking PnL attribution
        instead of raw APY * time approximation.
        This makes PnL attribution consistent across ALL DeFi protocols.
        Repos: unified-internal-contracts (RVAIndex schema), features-onchain-service (computation),
        strategy-service (PnLCalculator integration).
    status: done
    note: "PARALLEL stream C. Enables accurate cross-protocol PnL comparison."

  # --- Stream D: Risk Matrix & P&L Attribution Framework ---
  # IMPLEMENTATION SPEC: plans/active/stream_d_risk_matrix_implementation.md
  # That file has exact schemas, file paths, line numbers, DRY analysis, and
  # code examples for every item below. Agents MUST read it before executing.
  #
  # UAC vs UIC RULE: If external source provides data → schema in UAC.
  # Deribit/TARDIS give delta,gamma,vega,theta,IV directly → RiskType enum in UAC.
  # Confirmed: UAC CanonicalOptionsChainEntry (derivatives/:78-95) already has these.
  # GreeksExposure (UIC risk.py:214-235) is DUPLICATE — UAC already has per-underlying
  # via UnderlyingGreeksBreakdown (position/:127-136). UIC version should be deleted.

  - id: p5-risk-taxonomy-schema
    content: |
      - [x] [AGENT] P0. Add RiskType StrEnum. LOCATION DECISION:
        RiskType goes in UAC (canonical/crosscutting/risk_taxonomy.py — NEW file) because
        risk types like delta, vega, funding are dimensions that external venues report on
        (Deribit gives Greeks, exchanges give funding rates, TARDIS gives Greeks history).
        Even for internally-computed risks, the schema should be in UAC for centrality.
        Services import from UAC. Internal computation modules produce values typed by
        the same enum. One schema, multiple sources (external feed OR internal calculation).
        GreeksExposure (currently UIC risk.py:214-235) should ALSO move to UAC for same
        reason — Deribit/TARDIS provide Greeks directly as external data.
        ADD to pre-audit: GreeksExposure consumers (risk-and-exposure-service, PBMS).
        FIRST ORDER: delta, vega, theta, rho, funding, basis, carry, fx, liquidity
        SECOND ORDER: gamma, volga (vol-of-vol), vanna (delta-vol cross), slide (vol time decay)
        STRUCTURAL: duration, convexity, spread (bid-ask / credit), concentration
        OPERATIONAL: venue_protocol (exchange/protocol downtime), correlation
        DOMAIN-SPECIFIC: edge_decay (sports), market_suspension (sports),
        protocol_risk (DeFi smart contract), impermanent_loss (DeFi LP)
        Each RiskType maps to a P&L attribution dimension.
        Repos: unified-api-contracts (RiskType enum in canonical/crosscutting/risk_taxonomy.py).
        GreeksExposure migration from UIC to UAC handled separately (see stream_d spec).
        GATES ON: p3-qg-uac-final (UAC cleanup must be done before adding new UAC files).
    status: done
    note: "PARALLEL stream D. Foundation for everything else in this stream."

  - id: p5-risk-strategy-subscription
    content: |
      - [x] [AGENT] P0. Create StrategyRiskSubscription model in UIC — strategies subscribe
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
    status: done
    note: "PARALLEL stream D. Strategies declare which risks apply to them."

  - id: p5-risk-aggregation-hierarchy
    content: |
      - [x] [AGENT] P0. Define aggregation hierarchy for risk and P&L in UIC:
        Company → Client → Account → Strategy → Underlying → Instrument
        Each level aggregates from the level below. Fields per level:
        - risk_by_type: dict[RiskType, Decimal] (exposure per risk dimension)
        - pnl_by_type: dict[RiskType, Decimal] (P&L attributed to each risk)
        - var_by_type: dict[RiskType, Decimal] (marginal VaR per risk dimension)
        Term structure bucketing: overnight, 1w, 1m, 3m, 6m, 1y, 2y+ (for duration)
        Delta bucketing: by strike/moneyness (for options)
        Client ≠ account — a client can have multiple accounts across venues.
        Repos: unified-internal-contracts (schemas), position-balance-monitor-service (aggregation).
    status: done
    note: "PARALLEL stream D."

  - id: p5-risk-venue-protocol-risk
    content: |
      - [x] [AGENT] P1. Add venue/protocol risk dimension. Per venue:
        - Circuit breaker state (CLOSED/DEGRADED/OPEN) → risk score
        - Historical downtime frequency/duration
        - Concentration in that venue (% of total exposure)
        - DeFi: smart contract audit status, TVL trend, oracle dependency
        Risk metric: "if this venue goes down for N hours, what's our max loss?"
        Feeds into VaR scenarios: venue-down stress test.
        Repos: risk-and-exposure-service, execution-service (circuit breaker state).
    status: done
    note: "PARALLEL stream D."

  - id: p5-risk-duration-convexity
    content: |
      - [x] [AGENT] P1. Add duration and convexity risk for term-structure instruments:
        - Spot: duration = 0 (no term structure sensitivity)
        - Perpetuals: duration ≈ 0 (swap-like, funding rate resets)
        - Expiry futures: duration = days to expiry (basis point sensitivity)
        - Options: duration from delta × underlying duration + rho exposure
        - DeFi lending: duration = lock period / unbonding period
        Term structure risk: what if rates at the back of the curve change?
        Separate from rho (parallel shift) — duration measures curve shape sensitivity.
        Repos: risk-and-exposure-service, unified-internal-contracts.
    status: done
    note: "PARALLEL stream D."

  - id: p5-risk-volga-slide
    content: |
      - [x] [AGENT] P1. Add second-order vol risks for options strategies:
        - Volga (vol-of-vol): d²V/d²σ — P&L from volatility convexity
        - Vanna (delta-vol cross): d²V/(dS·dσ) — delta sensitivity to vol changes
        - Slide: vol surface decay — what happens to our P&L as vol surface ages
          (front vol decays faster than back vol)
        These are zero for non-options strategies (subscription model handles this).
        Repos: risk-and-exposure-service (computation), unified-internal-contracts (schema).
    status: done
    note: "PARALLEL stream D."

  - id: p5-risk-spread-risk
    content: |
      - [x] [AGENT] P1. Add spread risk for arb and relative-value strategies:
        - Bid-ask spread widening risk (liquidity crisis → spreads blow out)
        - Cross-venue spread risk (price divergence between venues)
        - Term structure spread risk (contango/backwardation changes)
        - DeFi: oracle spread risk (price oracle vs market price divergence)
        Repos: risk-and-exposure-service, unified-internal-contracts.
    status: done
    note: "PARALLEL stream D."

  - id: p5-risk-pnl-attribution-engine
    content: |
      - [x] [AGENT] P1. Build P&L attribution engine that decomposes total P&L into
        contributions from each RiskType the strategy is subscribed to:
        total_pnl = delta_pnl + gamma_pnl + vega_pnl + theta_pnl + rho_pnl
                   + volga_pnl + vanna_pnl + funding_pnl + basis_pnl + carry_pnl
                   + fx_pnl + spread_pnl + fees + residual
        Aggregates up the hierarchy: instrument → strategy → account → client → company.
        Residual = unexplained P&L (should be small; large residual = missing risk factor).
        Time series: store daily snapshots for over-time analysis.
        Repos: risk-and-exposure-service (or new pnl-attribution-service), PBMS (position data).
    status: done
    note: "PARALLEL stream D."

  - id: p5-risk-custom-risk-types
    content: |
      - [x] [AGENT] P1. Add custom/strategy-specific risk types with hot-reloadable parameters.
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
    status: done
    note: "PARALLEL stream D. Risk types fixed (restart). Parameters dynamic (hot-reload)."

  - id: p5-margin-health-timeseries
    content: |
      - [x] [AGENT] P0. Add margin health time-series storage. Per-candle snapshots written
        alongside PnL snapshots by settlement service. Schema in UIC:
        MarginHealthSnapshot:
          strategy_id, timestamp, venue, position_type (A_TOKEN/DEBT_TOKEN/PERP/SPOT),
          health_factor (DeFi: Aave HF), ltv_ratio (debt/collateral),
          collateral_usd, debt_usd, margin_usage_pct (CeFi: used/total margin),
          liquidation_price, distance_to_liquidation_pct,
          venue_type (cefi/defi/tradfi)
        Storage: GCS JSONL per strategy_id, partitioned by date. BigQuery external table.
        Write path: settlement_service processes positions → computes margin metrics →
        writes snapshot to GCS alongside PnLAttribution.
        Query: by strategy_id + time range. Same data for live (last N candles) and
        historical (any date range).
        UNIFIED across CeFi (exchange margin_level, liquidation_price),
        DeFi (Aave health_factor = collateral * liq_threshold / debt),
        TradFi (IBKR margin requirement, buying power).
        Repos: unified-internal-contracts (schema), strategy-service (write path),
        position-balance-monitor-service (aggregation), risk-and-exposure-service (query API).
    status: done
    note: "PARALLEL stream D. Foundation for margin health monitoring."

  - id: p5-backtest-liquidation-enforcement
    content: |
      - [x] [AGENT] P0. Enforce liquidation in backtest when health factor < 1.0.
        Currently if HF drops below 1.0 in a backtest, the strategy keeps running —
        unrealistic and dangerous for strategy evaluation.
        DeFi: When health_factor < 1.0, trigger forced exit (full deleverage sequence).
        Apply liquidation penalty (Aave: 5-10% of collateral depending on asset).
        CeFi: When margin_usage > maintenance_margin, trigger forced close at market.
        Apply liquidation fee per venue.
        TradFi: When margin_usage > maintenance, forced liquidation at market.
        Record LIQUIDATION settlement event with: trigger_hf, penalty_amount, positions_closed.
        This makes backtest results realistic — without it, recursive basis backtests
        overstate PnL by ignoring liquidation risk.
        Repos: strategy-service (backtest_engine.py, settlement_service.py),
        unified-internal-contracts (SettlementType.LIQUIDATION already exists, wire it).
    status: done
    note: "PARALLEL stream D. Critical for realistic DeFi backtesting."

  - id: p5-defi-pnl-index-reconciliation
    content: |
      - [x] [AGENT] P1. Add composite index reconciliation for DeFi positions.
        For recursive basis: aweETH has TWO yield sources:
        1. weETH/ETH rate appreciation (staking yield)
        2. Aave liquidity_index growth (tiny supply interest)
        The system tracks these separately (LST_YIELD + AAVE_INDEX settlements), which
        is correct. But no reconciliation verifies:
          expected_value = weeth_amount * weeth_rate * eth_price * (current_liq_index / entry_liq_index)
          actual_value = position_balance * current_price
          discrepancy = abs(expected - actual) / expected
        Add per-candle reconciliation check in settlement_service. Alert if discrepancy > 0.1%.
        Also reconcile debtTokens: debt_value = scaled_balance * variableBorrowIndex / RAY.
        This catches bugs where index updates are missed or applied twice (double-counting).
        Repos: strategy-service (settlement_service.py), execution-service (yield_recon_engine.py).
    status: done
    note: "PARALLEL stream D. Catches double-counting bugs in composite DeFi positions."

  - id: p5-scoped-kill-switch
    content: |
      - [x] [AGENT] P0. Upgrade kill switch from global-only to scoped by entity + dimension.
        CURRENT: Single global kill switch — blocks ALL orders for ALL clients.
        NEW: Composable scoped kill switches on two orthogonal dimensions:

        BY ENTITY (who):
        - company: all clients, all strategies, everything
        - client: all of that client's positions
        - account: specific venue account for a client

        BY WHAT:
        - strategy: specific strategy type across all venues (e.g. kill all BASIS)
        - venue: specific venue across all strategies (e.g. kill all Binance orders)
        - instrument: specific instrument (e.g. BTC-PERP on Deribit)

        Compose: "Kill client C1's BASIS strategy on Binance" =
        KillSwitchScope(entity_type="client", entity_id="C1",
                        strategy_type="BASIS", venue="binance")

        SCHEMA (UIC — add to risk.py):
        class KillSwitchScope(BaseModel):
            entity_type: str  # "company" | "client" | "account"
            entity_id: str | None = None  # None = all (company-wide)
            strategy_type: str | None = None  # None = all strategies
            venue: str | None = None  # None = all venues
            instrument_id: str | None = None  # None = all instruments
            auto_deactivate_after_minutes: int | None = None
            exit_playbook_override: str | None = None  # override default playbook

        class ScopedKillSwitchState(BaseModel):
            scope: KillSwitchScope
            is_active: bool
            activated_at: datetime
            activated_by: str
            reason: str
            auto_deactivate_at: datetime | None = None
            exit_progress: dict[str, str] | None = None  # step_id → status

        EXECUTION:
        - execution-service: check_kill_switch(order) evaluates ALL active scopes
        - Order blocked if ANY active scope matches (entity + strategy + venue + instrument)
        - Each scope can trigger its own exit playbook independently
        - Venue kill switch differs from strategy kill switch:
          Venue = "Binance is down, stop sending there" (circuit breaker also does this auto)
          Strategy = "Basis trade losing money, unwind it" (triggers exit playbook)
          Both can be active simultaneously

        PERSISTENCE: GCS `gs://config/kill_switches/active.json` — list of ScopedKillSwitchState
        Hot-reloadable. Survives service restarts (existing kill switch already persists to /tmp).

        Repos: unified-internal-contracts (schemas), execution-service (scoped check logic),
        risk-and-exposure-service (threshold monitoring → scoped activation).
    status: done
    note: "PARALLEL stream D. Replaces global-only kill switch with composable scoped system."

  - id: p5-kill-switch-ui-controls
    content: |
      - [x] [HUMAN+AGENT] P1. Add kill switch controls to live-health-monitor-ui.
        LOCATION: live-health-monitor-ui (existing ops dashboard — monitor, act, observe).
        Do NOT create a new UI. This is the ops cockpit.

        KILL SWITCH PANEL (src/components/ops/KillSwitchPanel.tsx):
        - Waterfall hierarchy selector: Company → Client → Account at top,
          Strategy → Venue → Instrument as filters. Most inclusive at top,
          most specific at bottom.
        - Dropdowns: select one or many clients, one or many strategies,
          one or many venues. Multi-select.
        - Big red ACTIVATE button with confirmation modal showing:
          what will be affected, estimated positions, exit playbook to run
        - Active kill switches table: scope, activated_at, auto_deactivate_at,
          exit progress (which step, what % complete)
        - DEACTIVATE button per scope (with confirmation)

        EXIT PROGRESS TRACKER (src/components/ops/ExitProgressTracker.tsx):
        - Per active exit: strategy type, playbook steps, current step,
          orders sent, fills received, remaining exposure
        - Real-time updates via WebSocket or polling risk-service API

        VENUE HEALTH PANEL (already partially exists):
        - Circuit breaker state per venue (CLOSED/DEGRADED/OPEN/HALF_OPEN)
        - Manual venue kill switch button (alongside automatic circuit breaker)
        - Queue depth for OPEN venues (from order queuing feature)

        CLIENT RISK DASHBOARD:
        - Per-client: current drawdown vs max_drawdown_pct threshold
        - VaR vs limit, proximity gauge
        - Historical drawdown chart
        - Active kill switches for this client

        Data: execution-service /kill-switch/status API (extend for scoped),
        risk-and-exposure-service /risk/metrics API,
        GCS kill_switches/active.json.
        Repos: live-health-monitor-ui.
    status: done
    note: "PARALLEL stream D. Ops cockpit — monitor health, trigger kill switch, track exit progress."

  - id: p5-exit-playbook-local-templates
    content: |
      - [x] [AGENT] P1. Create local exit playbook templates alongside GCS config.
        GCS is the runtime source of truth, but we need local templates for:
        - Development/testing (don't need GCS to see what playbooks look like)
        - Documentation (human-readable reference)
        - Version control (track changes to playbook definitions)

        LOCATION: unified-trading-pm/config/emergency/ (PM is cross-repo, logical home)
        CREATE:
        - exit_playbooks.yaml — default playbooks per strategy type
        - client_risk_tolerance_template.yaml — example client config
        - README.md — explains the schema, GCS path convention, how to deploy

        SYNC: GCS config is deployed FROM these templates. deployment-service or
        a CI step copies PM templates → GCS on deploy. Local templates are the
        editable source; GCS is the runtime copy.

        Example exit_playbooks.yaml:
        playbooks:
          MOM:
            exit_type: market_close
            steps:
              - {order: 1, action: close_all_positions, urgency: immediate}
          BASIS:
            exit_type: atomic_unwind
            steps:
              - {order: 1, action: close_perp_leg, urgency: immediate}
              - {order: 1, action: close_spot_leg, urgency: immediate}
          RECURSIVE_STAKED_BASIS:
            exit_type: deleverage_sequence
            steps:
              - {order: 1, action: repay_variable_debt, instrument_filter: WETH_DEBT}
              - {order: 2, action: withdraw_collateral, instrument_filter: aweETH}
              - {order: 3, action: swap_to_stable, max_slippage_bps: 200, urgency: best_effort}
          SPORTS:
            exit_type: hedge_cross_venue
            steps:
              - {order: 1, action: find_hedge_venue, urgency: best_effort}
              - {order: 2, action: place_lay_bets, max_slippage_bps: 100}
          YIELD_STAKING:
            exit_type: hybrid_unwind
            steps:
              - {order: 1, action: trade_out_liquid_portion, urgency: immediate, max_slippage_bps: 100}
              - {order: 2, action: initiate_unbonding, urgency: queued}
        Repos: unified-trading-pm (templates), deployment-service (sync to GCS).
    status: done
    note: "PARALLEL stream D. Local templates = editable source. GCS = runtime copy."

  - id: p5-emergency-exit-playbooks
    content: |
      - [x] [AGENT] P0. Emergency exit playbook system — per-strategy position unwinding
        on kill switch activation. Currently kill switch blocks new orders but does NOT
        unwind existing positions. "Close all positions" means different things per strategy.
        THREE-LAYER ARCHITECTURE:
        LAYER 1 — SCHEMA (UIC, restart to add new exit types):
        - EmergencyExitType StrEnum: MARKET_CLOSE, ATOMIC_UNWIND, DELEVERAGE_SEQUENCE,
          DELTA_HEDGE, STOP_NEW_ONLY, UNSTAKE_QUEUE
        - EmergencyExitStep: order (sequence), action, instrument_filter, urgency
          (immediate/best_effort/queued), max_slippage_bps, timeout_seconds
        - EmergencyExitPlaybook: strategy_type, exit_type, steps[], description
        - ClientRiskTolerance: client_id, max_drawdown_pct, max_var_breach_pct,
          auto_kill_switch_timeout_minutes, emergency_exit_override
        FILE: UIC domain/risk_service/risk.py (add after ExtendedPnLAttribution)
        LAYER 2 — CONFIG (GCS via UCI, hot-reloadable):
        - gs://config/emergency/exit_playbooks.yaml — per-strategy exit steps
        - gs://config/clients/{client_id}/risk_tolerance.yaml — per-client thresholds
        - UCI validates YAML structure, hot-reloads on change
        STRATEGY-SPECIFIC EXIT DEFINITIONS:
        - MOM: market_close (sell to flat)
        - BASIS: atomic_unwind (close BOTH legs simultaneously — naked exposure if one-sided)
        - RECURSIVE_STAKED_BASIS: deleverage_sequence (repay debt→withdraw collateral→swap)
        - OPTIONS: delta_hedge (hedge to delta-neutral) or market_close
        - SPORTS: stop_new_only (can't close settled bets)
        - LENDING/STAKING: unstake_queue (may have 7-28 day unbonding period!)
        LAYER 3 — EXECUTION:
        - risk-and-exposure-service: monitors client thresholds → triggers kill switch
        - execution-service: kill switch → loads playbook → orchestrates exit steps
        - strategy-service: domain knowledge of HOW to execute each step
        CLIENT-SPECIFIC:
        - Different clients can have different drawdown limits (10% vs 20%)
        - Client risk tolerance overrides strategy defaults
        - Per-client kill switch timeout (aggressive vs conservative)
        VISUALIZATION:
        - Monitoring UI: client risk tolerance dashboard, exit playbook viewer,
          active exit progress tracker (which step are we on?)
        Repos: unified-internal-contracts (schemas), unified-config-interface (config loader),
        execution-service (kill switch + orchestration), strategy-service (exit logic),
        risk-and-exposure-service (threshold monitoring).
    status: done
    note: "PARALLEL stream D. Critical for 24/7 ops — kill switch without exit playbook is incomplete."

  - id: p5-unified-margin-endpoint
    content: |
      - [x] [AGENT] P1. Add unified margin health API endpoint:
        GET /margin-health/{strategy_id}?start=<iso>&end=<iso>&granularity=<1m|5m|1h|1d>
        Returns: MarginHealthSnapshot[] time series.
        Same endpoint for live (omit start/end → last 24h) and historical (any range).
        Aggregate view: GET /margin-health/{strategy_id}/summary
        Returns: current HF, min HF in period, time at HF<1.5, time at HF<1.2,
        max LTV, avg margin usage, liquidation events count.
        Cross-venue: combines CeFi margin + DeFi health factor + TradFi margin into
        one response with per-venue breakdown.
        Wire into existing PBMS /defi-health/{client_id} endpoint (currently returns 404).
        Repos: position-balance-monitor-service (API), risk-and-exposure-service (computation).
    status: done
    note: "PARALLEL stream D. Config-driven: same endpoint for intraday or multi-year analysis."

  - id: p5-risk-matrix-visualization
    content: |
      - [x] [HUMAN+AGENT] P1. Build risk matrix + P&L attribution views in monitoring UI:
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
        MARGIN HEALTH VIEW: HF/LTV time series per strategy, liquidation threshold lines,
        distance-to-liquidation gauge, CeFi margin usage %, DeFi health factor, TradFi margin.
        Unified view: all venue types on one chart with colour-coded zones (safe/warning/critical).
        Config-driven: same view works for 1-day intraday or 2-year historical.
        DeFi RISK VIEW: protocol risk scores, TVL exposure, impermanent loss tracking
        Data: risk-service APIs, PBMS, strategy-service.
    status: done
    note: "PARALLEL stream D. The crown jewel — full risk visibility."

  # =========================================================================
  # PHASE 6: FINAL VALIDATION (sequential — everything must pass)
  # =========================================================================

  - id: p6-workspace-wide-qg
    content: |
      - [x] [AGENT] P0. Final quality gates on ALL modified repos:
        unified-api-contracts, unified-internal-contracts, risk-and-exposure-service,
        execution-service, trading-analytics-api, market-data-processing-service,
        unified-market-interface, unified-trading-library.
        Each: `cd <repo> && bash scripts/quality-gates.sh`
        Only mark plan complete when ALL pass.
    status: done
    note: "SEQUENTIAL — final gate."

isProject: false
---

# Contracts, Observability & Risk Cleanup Plan

## Cross-Plan Conflict Analysis (2026-03-16)

Conflicts identified with 3 other active plans. Cross-references and resolutions:

### vs cicd_code_rollout_master_2026_03_13

| Conflict                | This Plan                         | CICD Plan                             | Resolution                                                                                         |
| ----------------------- | --------------------------------- | ------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Kill switch             | Multi-layer + timeout + playbooks | Binary halt/resume                    | CICD's binary model is Phase 1. This plan extends it. No breaking conflict — additive.             |
| Float precision         | Needs Decimal for VaR             | Identifies 9 floats needing migration | **DEPENDENCY**: CICD float migration should complete before p5-var-monte-carlo. Note in VaR items. |
| Position reconciliation | Hierarchical aggregation          | Binary position snapshot              | This plan's aggregation is richer. CICD snapshot still works as a subset.                          |

### vs cicd_e2e_testing_master_2026_03_13

| Conflict                 | This Plan                           | E2E Plan                      | Resolution                                                                                                                                  |
| ------------------------ | ----------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| failure-kill-switch test | Scoped kill switch + playbooks      | Tests binary halt/resume only | **ACTION**: After our Phase 5, enhance E2E test to cover playbook execution, auto-deactivation, scoped kill switches. Add todo to E2E plan. |
| Circuit breaker E2E      | DEGRADED throttling + order queuing | Not tested                    | **ACTION**: Add E2E tests for DEGRADED probabilistic throttling and queue drain on recovery.                                                |
| Margin health endpoint   | /margin-health/{strategy_id}        | Not tested                    | **ACTION**: Add E2E test for unified margin endpoint after p5-unified-margin-endpoint.                                                      |

### vs strategy_system_citadel_master_2026_03_15

| Conflict              | This Plan                                             | Strategy Plan                                                       | Resolution                                                                                                                                   |
| --------------------- | ----------------------------------------------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| RiskType taxonomy     | Defines RiskType enum (p5-risk-taxonomy-schema)       | Needs it for risk subscriptions                                     | **DEPENDENCY**: Our RiskType must exist before strategy risk subscriptions. Already done (Phase 5 wave 1).                                   |
| Emergency exit        | Defines playbooks per strategy type                   | Implicit need for exit logic                                        | **DEPENDENCY**: Our playbook system is REQUIRED for strategy exit behavior. Strategy plan should reference our EmergencyExitPlaybook schema. |
| Venue failover        | p5-cb-venue-failover defines pairs                    | p3-strategy-instrument-matrix validates (strategy,venue,instrument) | **ACTION**: Failover pairs must be visible to strategy validation matrix. Publish pairs via shared config in UCI.                            |
| Aggregation hierarchy | Company→Client→Account→Strategy→Underlying→Instrument | Strategy-level position tracking                                    | **ACTION**: Strategy system must adopt our RiskPnLNode hierarchy, not build separate position aggregation.                                   |
| Instruction schemas   | No direct touch                                       | p2g moves StrategyInstruction to UAC                                | No conflict — different concerns.                                                                                                            |
| Float migration       | Needs Decimal for risk computations                   | Implicit need for PnL tracking                                      | Same CICD dependency — float migration first.                                                                                                |

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
                                           │           ├─ p4c risk-service adopt UIC
                                           │           ├─ p4d trading-analytics-ui types
                                           │           └─ p4f add venues to registry
                                           │                 │
                                           │           p4-QG-downstream ──┐
                                           │                              │
PHASE 5 (4 streams)                        │                              │
Stream A: Observability (7 items) ─────────┤── independent of P1-P4      │
Stream B: Circuit Breaker (5 items) ───────┤── independent of P1-P4      │
Stream C: VaR Phase 2 (6 items) ───────────┤── gates on p2-QG-UIC       │
Stream D: Risk Matrix (10 items) ──────────┘── gates on p2-QG + p3-QG   │
  (includes risk-matrix-visualization,                                    │
   which was p4e — moved here because                                    │
   it depends on Phase 5 APIs)                                           │
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

### File Size Compliance (cumulative across ALL phases)

| File                               | Now     |  Net Δ | Final    |  Margin | Risk                               |
| ---------------------------------- | ------- | -----: | -------- | ------: | ---------------------------------- |
| UAC `__init__.py`                  | **896** |    -45 | **~851** |  **49** | **TIGHT** — massive re-export file |
| UAC `canonical/__init__.py`        | 283     |    -23 | ~260     |     640 | Safe                               |
| UAC `canonical/domain/__init__.py` | 487     |    -18 | ~469     |     431 | Safe                               |
| UAC `analytics.py`                 | 202     |   -100 | ~102     |     798 | Shrinking                          |
| UAC `connectivity.py`              | 116     |    -50 | ~66      |     834 | Shrinking                          |
| UAC `risk.py`                      | 160     | DELETE | 0        |       — | Gone                               |
| UAC `risk_taxonomy.py` (NEW)       | 0       |    +60 | ~60      |     840 | New file                           |
| UAC errors/`defi.py`               | 414     |    +80 | ~494     |     406 | Safe                               |
| UAC errors/`tradfi.py` (NEW)       | 0       |   +250 | ~250     |     650 | New file                           |
| UAC errors/`altdata.py`            | 451     |    -75 | ~376     |     524 | Safe                               |
| UAC errors/`sports.py`             | 496     |   -170 | ~326     |     574 | Safe                               |
| UIC `__init__.py`                  | **717** |    +25 | **~742** | **158** | Watch                              |
| UIC domain `risk.py`               | 308     |   +205 | **~513** | **387** | Biggest addition                   |
| UIC `factor_exposure.py`           | 68      |    +50 | ~118     |     782 | Safe                               |
| UIC `lifecycle.py`                 | 64      |    -20 | ~44      |     856 | Shrinking                          |

Zero basedpyright baselines. UIC coverage floor: 98%. Full analysis: `stream_d_risk_matrix_implementation.md`

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

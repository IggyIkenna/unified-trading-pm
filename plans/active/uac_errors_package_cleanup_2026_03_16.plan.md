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
  # PHASE 4: DOWNSTREAM ADOPTION (parallel agents — 2 repos only)
  # =========================================================================
  # PRE-AUDIT confirmed: only 2 service repos have breaking changes.
  # ml-training-service, strategy-service, risk-and-exposure-service: NO CHANGE.

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
    note: "PARALLEL with p4b."

  - id: p4b-fix-market-data-processing-service
    content: |
      - [ ] [AGENT] P0. Fix `market-data-processing-service/market_data_processing_service/types.py:19`:
        CHANGE: Remove Correlation*/FactorType from UAC import.
        ADD: `from unified_internal_contracts import (CorrelationRegime,
        CrossAssetCorrelationMatrix, FactorType)` (if needed, or remove if unused).
        Update `__all__:31`.
        Run: `cd market-data-processing-service && bash scripts/quality-gates.sh`
    status: todo
    note: "PARALLEL with p4a."

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

| Repo                               | Files Breaking      | Changes Needed                      |
| ---------------------------------- | ------------------- | ----------------------------------- |
| **trading-analytics-api**          | `contracts.py:8-22` | Correlation\* imports: UAC → UIC    |
| **market-data-processing-service** | `types.py:19`       | Correlation\*/FactorType: UAC → UIC |
| **ml-training-service**            | NONE                | Already imports from UIC            |
| **strategy-service**               | NONE                | Already imports from UIC            |
| **risk-and-exposure-service**      | NONE                | Uses local var_calculator types     |
| **execution-service**              | NONE                | Imports from UIC correctly          |
| **All other services**             | NONE                | No imports of moved symbols         |

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

---
name: contracts-observability-risk-cleanup
overview: |
  Comprehensive cleanup, observability, and risk expansion plan covering:
  (A) UAC crosscutting cleanup — delete duplicate errors package, deduplicate types, re-categorize
      venues, prune dead symbols, resolve UAC↔UIC duplication, enforce external-vs-internal split.
  (B) Observability & monitoring — live health monitoring UI, Prometheus→Cloud bridge, restart
      detection, latency profiling activation, resource utilization dashboards, shard-aware monitoring.
  (C) VaR/risk Phase 2 — historical returns ingestion, Monte Carlo VaR, Greeks-based risk,
      copula multi-asset correlation, VaR attribution, dynamic regime detection.
  Cloud monitoring as independent backup for when own systems are down.
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
  - repo: unified-trading-library
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
  # SECTION A: UAC CROSSCUTTING CLEANUP (Layers 1–10)
  # =========================================================================

  - id: a1-delete-duplicate-errors-package
    content: |
      - [ ] [AGENT] P0. Delete `canonical/errors/` — byte-for-byte identical to
        `canonical/crosscutting/errors/` (all 7 files). Redirect 2 stale imports first:
        1. `canonical/__init__.py:147` — `from .errors import` → `from .crosscutting.errors import`
        2. `external/open_meteo/schemas.py` — same redirect
        58 imports already use correct `crosscutting.errors` path; only these 2 use stale path.
    status: todo
    note: "Confirmed via diff + workspace-wide grep. crosscutting/ is documented home."

  - id: a2-deduplicate-erroraction-venue-error
    content: |
      - [ ] [AGENT] P0. In `canonical/crosscutting/errors/_canonical.py`, remove duplicate
        definitions of `ErrorAction` (StrEnum) and `VenueErrorClassification` (dataclass).
        Import from `._types` instead. No circular dep risk — _types.py doesn't import _canonical.py.
    status: todo
    note: ""

  - id: a3a-create-tradfi-errors-file
    content: |
      - [ ] [AGENT] P1. Create `errors/tradfi.py` with VENUE_ERRORS_TRADFI. Move:
        From cefi.py: tardis, yahoo_finance, ibkr, databento
        From altdata.py: barchart, fred, ecb, ofr, openbb
        (9 TradFi venues per VENUE_REGISTRY, currently scattered)
    status: todo
    note: ""

  - id: a3b-create-onchain-perps-errors-file
    content: |
      - [ ] [AGENT] P1. Create `errors/onchain_perps.py`. Move from altdata.py: hyperliquid, aster.
    status: todo
    note: ""

  - id: a3c-fix-defi-misplacements
    content: |
      - [ ] [AGENT] P1. Move to defi.py:
        From altdata.py: aave_v3. From sports.py: instadapp, defillama.
        From cefi.py: alchemy, thegraph. From altdata.py: bloxroute.
        (alchemy/thegraph/bloxroute are DeFi infra, not in VENUE_REGISTRY — comment as ancillary)
    status: todo
    note: ""

  - id: a3d-fix-altdata-to-only-altdata
    content: |
      - [ ] [AGENT] P1. After moves, altdata.py keeps: coinglass, hyblock (true altdata, not in
        VENUE_REGISTRY). Move glassnode, arkham from sports.py → altdata.py. Remove versifi
        (not altdata). Decide: add coinglass/hyblock/glassnode/arkham to VENUE_REGISTRY or
        document as ancillary.
    status: todo
    note: ""

  - id: a3e-fix-sports-to-only-sports
    content: |
      - [ ] [AGENT] P1. After moves, sports.py keeps: polymarket, betfair, kalshi, smarkets,
        betdaq, sports_generic. Move onchain_revert to own crosscutting file or defi.py.
    status: todo
    note: ""

  - id: a3f-update-init-exports
    content: |
      - [ ] [AGENT] P1. Update errors/__init__.py: import tradfi.py, onchain_perps.py.
        Add VENUE_ERRORS_TRADFI, VENUE_ERRORS_ONCHAIN_PERPS to VENUE_ERROR_MAP and __all__.
    status: todo
    note: ""

  - id: a4-registry-parity-audit
    content: |
      - [ ] [AGENT] P2. Audit parity: 15 error-map venues NOT in UMI VENUE_REGISTRY
        (polymarket, betfair, kalshi, smarkets, betdaq, glassnode, arkham, coinglass, hyblock,
        versifi, bloxroute, alchemy, thegraph, onchain_revert, sports_generic).
        Decide per venue: (a) add to VENUE_REGISTRY, (b) keep with comment, (c) remove.
    status: todo
    note: ""

  - id: a5-move-risk-schemas-to-uic
    content: |
      - [ ] [AGENT] P0. Delete UAC `canonical/crosscutting/risk.py` — all 10 symbols are INTERNAL.
        Dispositions:
        - SpanMarginLeg, MultiAssetMarginCalculation: delete (already in UIC risk.py)
        - PnLAttributionRecord, RealTimePnLRecord: move to UIC
        - RiskLimitBreach: consolidate with UIC AlertMessage
        - VaRMethod, VaRRequest, VaRResult, StressScenario, StressTestResult: move to UIC
          (VaR already implemented in risk-service var_calculator.py — align schemas)
        Remove from crosscutting __init__.py and facades.
    status: todo
    note: ""

  - id: a6-fix-analytics-external-internal-split
    content: |
      - [ ] [AGENT] P1. Split analytics.py by external vs internal:
        KEEP IN UAC (external normalization): AlternativeDataType, AlternativeDataSignal,
        SentimentScore, SatelliteObservation, OptionsFlowRecord, DarkPoolPrintRecord
        MOVE TO UIC (internal): CorrelationRegime, CrossAssetCorrelationMatrix,
        CorrelationRegimeChange
        REMOVE FROM UAC (UIC is SSOT): FactorType, FactorExposure, FactorAttributionRecord,
        FactorAttributionModel — UAC should import+re-export from UIC, not redefine.
    status: todo
    note: ""

  - id: a7-prune-dead-connectivity-symbols
    content: |
      - [ ] [AGENT] P1. Remove 7 dead symbols from connectivity.py:
        DELETE: WebSocketPingFrame, WebSocketPongFrame (library handles), UnsubscribeRequest,
        SubscribeRequest (adapters use raw JSON), HeartbeatMessage (redundant with
        CanonicalWebSocketLifecycle+PING), WebSocketConnectionState (local adapter state),
        CanonicalWsMessage (zero consumers — reserve or delete).
        KEEP: WebSocketEvent, CanonicalWebSocketLifecycle, HealthPingResponse,
        WebSocketConnectionOpened, WebSocketConnectionClosed.
    status: todo
    note: ""

  - id: a8-resolve-uac-uic-factor-duplicates
    content: |
      - [ ] [AGENT] P2. Factor* types in BOTH UAC+UIC. UIC is SSOT. Verify dep direction.
        Preferred: UAC imports from UIC and re-exports. Remove UAC's own definitions.
    status: todo
    note: ""

  - id: a9-resolve-uac-uic-ws-duplicates
    content: |
      - [ ] [AGENT] P2. WS lifecycle types in BOTH UAC (Pydantic) + UIC (dataclass).
        Decide single owner. Delete dead duplicates (PingFrame/PongFrame) from both.
        Reconcile HealthPingResponse, ConnectionOpened, ConnectionClosed type systems.
    status: todo
    note: ""

  - id: a10-quality-gates-uac
    content: |
      - [ ] [AGENT] P0. Run `cd unified-api-contracts && bash scripts/quality-gates.sh`.
        Also run `cd unified-internal-contracts && bash scripts/quality-gates.sh` after moves.
    status: todo
    note: ""

  # =========================================================================
  # SECTION B: OBSERVABILITY & MONITORING (Layers 11–18)
  # =========================================================================

  - id: b11-prometheus-cloud-monitoring-bridge
    content: |
      - [ ] [AGENT] P1. Wire Prometheus metrics to Cloud Monitoring as independent backup.
        Options: (a) OTEL Collector sidecar with remote_write to GCP Cloud Monitoring,
        (b) Prometheus server with GMP (Google Managed Prometheus).
        Extend existing UTL setup_tracing() to cover metrics (not just traces).
        This ensures monitoring works even if own UI/services are down.
        Repos: unified-trading-library (OTEL setup), deployment-service (sidecar config).
    status: todo
    note: "UTL already has setup_tracing() in utils/tracing.py. Extend to setup_metrics()."

  - id: b12-restart-detection-lifecycle-event
    content: |
      - [ ] [AGENT] P1. Add RESTART_DETECTED lifecycle event. On STARTED, check for missing
        STOPPED event in recent GCS logs (unclean shutdown). Emit RESTART_DETECTED with
        restart_count, last_known_state, shutdown_reason (OOM, SIGKILL, unknown).
        Add restart_count to /health endpoint response.
        Repos: unified-internal-contracts (schema), unified-trading-library (detection logic),
        all services (wire into startup).
    status: todo
    note:
      "Currently no way to tell 'this service restarted 3 times today'. Infra handles restarts but app doesn't track."

  - id: b13-activate-latency-profiling
    content: |
      - [ ] [AGENT] P1. Wire UAC latency schemas (TickToTradeMetric, OrderLatencyRecord,
        LatencyPercentile, LatencyBenchmarkReport) into actual measurement code.
        Schemas exist and are imported but NOTHING MEASURES in production.
        Target: execution-service order path (tick→signal→risk→encode→send→ack→fill).
        Record timestamps at each LatencyComponent stage, populate OrderLatencyRecord,
        write to GCS for analysis. Publish LatencyBenchmarkReport per session.
        Repos: execution-service (measurement), market-tick-data-service (market data decode).
    status: todo
    note: "Rich latency schemas defined but zero production measurement code."

  - id: b14-resource-utilization-metrics
    content: |
      - [ ] [AGENT] P1. Add resource utilization metrics beyond memory watchdog:
        - CPU usage per service (gauge, sampled every 30s)
        - Memory RSS vs threshold proximity (gauge)
        - GCS write latency (histogram)
        - Pub/Sub publish latency (histogram)
        - Active WebSocket connections (gauge, per venue)
        - Queue depth / backpressure (gauge)
        Expose on /metrics for Prometheus scraping. Include shard_id label for batch services.
        Repos: unified-trading-library (shared metrics helpers), all services (wire in).
    status: todo
    note: "Currently only Prometheus counters/histograms for request-level. No system-level resource gauges."

  - id: b15-shard-aware-live-monitoring
    content: |
      - [ ] [AGENT] P2. Extend lifecycle events for live services with shard-like partitioning.
        Live services handle multiple venues/strategies — add venue_id and strategy_id labels
        to lifecycle events and Prometheus metrics. Enables per-venue latency tracking,
        per-strategy P&L monitoring in the monitoring UI.
        Repos: unified-internal-contracts (schema update), execution-service, strategy-service.
    status: todo
    note: "Batch has shard IDs; live services have no equivalent partitioning in events."

  - id: b16-live-health-monitoring-ui
    content: |
      - [ ] [HUMAN+AGENT] P1. Build live health monitoring UI (new repo or extend existing
        ops dashboard). Features:
        - Service lifecycle timeline (STARTED/STOPPED/FAILED per service, color-coded)
        - Restart count badges per service (batch + live)
        - Latency percentile charts (p50/p95/p99 per venue, tick-to-trade)
        - Resource utilization gauges (CPU, memory, connections per service/shard)
        - Batch completion tracker (shard progress, expected vs actual completion time)
        - VaR dashboard (current VaR, CVaR, stress scenario results, limit proximity)
        - Risk alerts feed (RiskLimitBreach, CircuitBreaker state, kill switch status)
        - P&L attribution waterfall (delta/gamma/vega/theta/carry/fees breakdown)
        - Correlation regime indicator (current regime, regime change history)
        Data sources: GCS lifecycle JSONL, Prometheus /metrics, risk-service API, PBMS API.
        Group by: service, venue, strategy, shard, category — user-configurable.
        Stack: React + Vite (consistent with other 13 UIs), vitest, pool: "forks".
    status: todo
    note: "Own UI for day-to-day ops. Custom views, grouping, alerts — not possible with third-party dashboards."

  - id: b17-cloud-monitoring-backup-alerts
    content: |
      - [ ] [HUMAN+AGENT] P1. Configure Cloud Monitoring as independent backup:
        - GCP Cloud Run / GKE built-in metrics (container restarts, OOM kills, CPU/memory)
        - Uptime checks hitting /health endpoints from external network path
        - Log-based alerts for FAILED lifecycle events, AUTH_FAILURE, CIRCUIT_BREAKER_OPEN
        - Alert routing to PagerDuty/Opsgenie/Telegram
        This is the safety net — pages you when your own monitoring UI/services are down.
        Repos: deployment-service (terraform/config), unified-trading-pm (alert rules docs).
    status: todo
    note: "Independent observer. If our own systems break, Cloud Monitoring still pages us."

  - id: b18-alert-rules-definition
    content: |
      - [ ] [AGENT] P2. Define alert rules for both own UI and Cloud Monitoring:
        - Restart count > 3 in 1 hour → CRITICAL
        - Latency p99 > 500ms sustained 5min → WARNING
        - Batch shard not completed by deadline → WARNING
        - Memory > 80% sustained 5min → WARNING
        - VaR > 90% of limit → WARNING; > 100% → CRITICAL
        - Circuit breaker OPEN for any venue → CRITICAL
        - Kill switch activated → CRITICAL
        - Lifecycle FAILED event → CRITICAL
        - No STARTED event for scheduled batch within 15min of schedule → WARNING
        Store as config (YAML or Python) loadable by both monitoring UI and Cloud alerts.
    status: todo
    note: ""

  # =========================================================================
  # SECTION C: VaR / RISK PHASE 2 (Layers 19–25)
  # =========================================================================

  - id: c19-var-historical-returns-ingestion
    content: |
      - [ ] [AGENT] P1. Currently /risk/var requires caller to supply returns[] array.
        Add automated historical returns ingestion from position-balance-monitor-service
        history. Store daily returns per instrument in GCS. Risk service fetches on demand.
        Repos: risk-and-exposure-service (ingestion), position-balance-monitor-service (source).
    status: todo
    note: "Phase 1 design: caller provides returns. Phase 2: automated from PBMS position history."

  - id: c20-monte-carlo-var
    content: |
      - [ ] [AGENT] P2. Add Monte Carlo VaR simulation to var_calculator.py.
        Current: historical, parametric, Cornish-Fisher, stress VaR. Missing: MC simulation.
        Pure stdlib approach (consistent with existing design): random number generation
        via stdlib random module, Cholesky decomposition for correlated asset simulation.
        Add VaRMethod.MONTE_CARLO to UIC schema. Wire into /risk/var endpoint.
        Repos: risk-and-exposure-service.
    status: todo
    note: "Existing var_calculator.py is pure stdlib with Winitzki erfinv. Keep same philosophy."

  - id: c21-copula-multi-asset-correlation
    content: |
      - [ ] [AGENT] P2. Add copula-based multi-asset correlation for portfolio VaR.
        CrossAssetCorrelationMatrix schema exists (moving to UIC in layer a6).
        Implement rolling correlation matrix computation from returns data.
        Feed into Monte Carlo simulation for correlated multi-asset VaR.
        Repos: risk-and-exposure-service (computation), unified-internal-contracts (schemas).
    status: todo
    note: ""

  - id: c22-greeks-based-risk
    content: |
      - [ ] [AGENT] P2. Implement Greeks-based risk computation.
        UIC already has GreeksExposure schema (delta, gamma, theta, vega, rho).
        Compute portfolio-level Greeks aggregation. Feed delta/gamma into VaR (delta-gamma
        VaR approximation). Wire into risk dashboard in monitoring UI.
        Repos: risk-and-exposure-service, position-balance-monitor-service.
    status: todo
    note: "Schema exists in UIC. Computation not implemented."

  - id: c23-var-attribution
    content: |
      - [ ] [AGENT] P2. Add VaR attribution — decompose portfolio VaR into per-position,
        per-venue, per-strategy contributions. Component VaR and marginal VaR.
        VaRResult already has component_var field (dict[str, Decimal]) — populate it.
        Repos: risk-and-exposure-service.
    status: todo
    note: ""

  - id: c24-dynamic-regime-detection
    content: |
      - [ ] [AGENT] P2. Automate regime detection. Currently operator manually calls
        set_regime_multiplier(). Add automated detection from:
        - VIX / crypto volatility index thresholds
        - Correlation regime changes (from layer c21)
        - Drawdown velocity (rate of portfolio loss)
        Auto-set regime multiplier when regime shifts detected.
        Repos: risk-and-exposure-service, strategy-service (signal source).
    status: todo
    note: "Currently manual: operator calls set_regime_multiplier(). Phase 2: automated."

  - id: c25-quality-gates-risk
    content: |
      - [ ] [AGENT] P0. Run quality gates on all modified repos after risk Phase 2 work:
        `cd risk-and-exposure-service && bash scripts/quality-gates.sh`
        `cd unified-internal-contracts && bash scripts/quality-gates.sh`
    status: todo
    note: ""

isProject: false
---

# Contracts, Observability & Risk Cleanup Plan

## Context

Discovered 2026-03-16 during comprehensive UAC duplication scan and architectural review. Expanded to cover
observability gaps and VaR Phase 2 based on session analysis.

## Section A: UAC Crosscutting Cleanup

### Issue 1: Full package duplication

`canonical/errors/` and `canonical/crosscutting/errors/` are byte-for-byte identical (7 files). 2 stale imports
(`canonical/__init__.py:147`, `external/open_meteo/schemas.py`) vs 58 correct.

### Issue 2: Within-package type duplication

`_types.py` and `_canonical.py` both define `ErrorAction` and `VenueErrorClassification`.

### Issue 3: Venue mis-categorization

No tradfi.py or onchain_perps.py exists. DeFi venues in sports.py. TradFi in cefi.py/altdata.py.

### Issue 4: Dead/orphaned schemas

risk.py: 10/10 dead (all internal, should be UIC). analytics.py: 8/13 dead or misplaced. connectivity.py: 7/12 dead
(library handles, or replaced by event model).

### Issue 5: UAC↔UIC duplication

Factor\* types identical in both. WS lifecycle types in both with Pydantic vs dataclass mismatch.

### External vs Internal Rule

UAC = normalizing external data (venue APIs, feeds). UIC = internal computations/state. analytics.py violated this by
mixing external altdata schemas with internal factor models. risk.py violated this entirely — all internal computations,
none normalizing external data.

## Section B: Observability & Monitoring

### Current State

- Lifecycle events: FULLY IMPLEMENTED (UIC lifecycle.py, log_event(), GCS JSONL)
- Prometheus: all services expose /metrics (counters, histograms, gauges)
- Latency schemas: DEFINED but NOT MEASURED in production
- OpenTelemetry: setup helper exists (UTL tracing.py), adoption optional/limited
- Memory watchdog: reactive (85% threshold → shutdown), no restart tracking
- Shard awareness: batch YES (shard_id injected), live NO

### Architecture Decision

- **Own monitoring UI (primary)**: custom grouping by service/venue/strategy/shard, custom plots, integrated alerts, VaR
  dashboard, P&L waterfall — not possible with third-party dashboards. Built on same React+Vite stack as existing 13
  UIs.
- **Cloud Monitoring (backup)**: independent observer at infrastructure level. Pages us when our own systems are down.
  GCP Cloud Run metrics, uptime checks, log-based alerts. Essential safety net.

### Gaps to Fill

1. No Prometheus→Cloud bridge (metrics don't reach GCP/AWS)
2. No restart counter (app doesn't know it restarted)
3. No production latency measurement (schemas exist, code doesn't)
4. No system-level resource gauges (CPU, memory proximity, queue depth)
5. No monitoring UI
6. No alert rules defined
7. Live services lack shard-equivalent partitioning in metrics

## Section C: VaR / Risk Phase 2

### Current State (Phase 1 — COMPLETE, archived)

- 4 VaR methods: historical, parametric, Cornish-Fisher (fat-tail), CVaR
- Stress VaR with crisis multipliers (GFC 3.5x, COVID 2.5x, Crypto 5.0x)
- Multi-horizon (1d/5d/10d via sqrt-of-time)
- Pre-trade VaR limit enforcement
- Regime multiplier (operator-set)
- /risk/var API endpoint
- 100% test coverage, pure stdlib (no numpy/scipy)

### Phase 2 Gaps

1. Historical returns ingestion (caller supplies returns[]; need automated from PBMS)
2. Monte Carlo simulation (not in current design)
3. Copula-based multi-asset correlation (schema exists, not computed)
4. Greeks-based risk (schema exists, not computed)
5. VaR attribution (component_var field exists, not populated)
6. Dynamic regime detection (currently manual)

## Crosscutting Modules Audit (2026-03-16)

| Module          | Symbols | Used | Dead | Status                         |
| --------------- | ------- | ---- | ---- | ------------------------------ |
| rate_limits.py  | 2       | 2    | 0    | Clean — no action              |
| latency.py      | 8       | 8    | 0    | Clean — wire measurement (B13) |
| connectivity.py | 12      | 5    | 7    | Prune dead (A7)                |
| analytics.py    | 13      | 6    | 7    | Split external/internal (A6)   |
| risk.py         | 10      | 0    | 10   | Delete, move to UIC (A5)       |

## Venue Placement Summary (current → target)

| Venue                    | Current File | VENUE_REGISTRY Category | Target File          |
| ------------------------ | ------------ | ----------------------- | -------------------- |
| binance                  | cefi.py      | cefi                    | cefi.py              |
| bybit                    | cefi.py      | cefi                    | cefi.py              |
| okx                      | cefi.py      | cefi                    | cefi.py              |
| deribit                  | cefi.py      | cefi                    | cefi.py              |
| coinbase                 | cefi.py      | cefi                    | cefi.py              |
| ccxt                     | cefi.py      | cefi                    | cefi.py              |
| upbit                    | cefi.py      | cefi                    | cefi.py              |
| tardis                   | cefi.py      | tradfi                  | **tradfi.py**        |
| yahoo_finance            | cefi.py      | tradfi                  | **tradfi.py**        |
| ibkr                     | cefi.py      | tradfi                  | **tradfi.py**        |
| databento                | cefi.py      | tradfi                  | **tradfi.py**        |
| alchemy                  | cefi.py      | NOT IN REGISTRY         | **defi (ancillary)** |
| thegraph                 | cefi.py      | NOT IN REGISTRY         | **defi (ancillary)** |
| barchart                 | altdata.py   | tradfi                  | **tradfi.py**        |
| fred                     | altdata.py   | tradfi                  | **tradfi.py**        |
| ecb                      | altdata.py   | tradfi                  | **tradfi.py**        |
| ofr                      | altdata.py   | tradfi                  | **tradfi.py**        |
| openbb                   | altdata.py   | tradfi                  | **tradfi.py**        |
| hyperliquid              | altdata.py   | onchain_perps           | **onchain_perps.py** |
| aster                    | altdata.py   | onchain_perps           | **onchain_perps.py** |
| aave_v3                  | altdata.py   | defi                    | **defi.py**          |
| bloxroute                | altdata.py   | NOT IN REGISTRY         | **defi (ancillary)** |
| coinglass                | altdata.py   | NOT IN REGISTRY         | altdata.py           |
| hyblock                  | altdata.py   | NOT IN REGISTRY         | altdata.py           |
| versifi                  | altdata.py   | NOT IN REGISTRY         | TBD                  |
| instadapp                | sports.py    | defi                    | **defi.py**          |
| defillama                | sports.py    | defi                    | **defi.py**          |
| glassnode                | sports.py    | NOT IN REGISTRY         | **altdata.py**       |
| arkham                   | sports.py    | NOT IN REGISTRY         | **altdata.py**       |
| onchain_revert           | sports.py    | NOT IN REGISTRY         | **crosscutting**     |
| polymarket               | sports.py    | NOT IN REGISTRY         | sports.py            |
| betfair                  | sports.py    | NOT IN REGISTRY         | sports.py            |
| kalshi                   | sports.py    | NOT IN REGISTRY         | sports.py            |
| smarkets                 | sports.py    | NOT IN REGISTRY         | sports.py            |
| betdaq                   | sports.py    | NOT IN REGISTRY         | sports.py            |
| sports_generic           | sports.py    | NOT IN REGISTRY         | sports.py            |
| balancer–uniswap_v4 (11) | defi.py      | defi                    | defi.py (correct)    |

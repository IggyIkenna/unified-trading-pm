---
name: Full Service Expansion
overview: Complete implementation of all 35 documented services with batch and live modes, full library coverage (5 unified libraries + 19+ venue adapters), sports integration, 6+ UI services, and comprehensive documentation coverage across the entire unified trading system.
todos:
  - id: unified-events-interface
    content: Create unified-events-interface library with lifecycle events, coordination events, mode-aware writers (GCS + PubSub), and tests
    status: completed
  - id: unified-config-interface
    content: Create unified-config-interface library with Pydantic base config, multi-source loaders (env, Secret Manager, YAML), and tests
    status: completed
  - id: market-interface-top5
    content: "Complete unified-market-interface: Add Coinbase, OKX, Deribit, Bybit adapters with normalization to canonical schemas and factory function"
    status: completed
  - id: order-interface-top5
    content: "Complete unified-trade-execution-interface: Implement real API integration for Binance + add Coinbase, OKX, Deribit, Bybit adapters with authentication and order placement"
    status: completed
  - id: execution-algos
    content: "Complete execution-algo-library: Add Iceberg, POV, SOR algorithms with backtest support and unified-trade-execution-interface integration"
    status: completed
  - id: pipeline-live-mode
    content: "Add live mode to 6 services: instruments-service, market-tick-data-handler, market-data-processing-service, features-calendar-service, features-volatility-service, strategy-service"
    status: in_progress
  - id: skeleton-services
    content: "Implement 3 skeleton services: position-balance-monitor-service, risk-and-exposure-service, pnl-attribution-service with batch + live modes"
    status: completed
  - id: sports-data-migration
    content: Migrate sports-betting-services data (50GB+) to unified GCS structure and extract code to existing services
    status: pending
  - id: features-sports-service
    content: Create features-sports-service with 19 feature calculators, time horizons (T-24h, T-60m, T-0, HT), batch + live modes
    status: pending
  - id: augment-services-sports
    content: "Augment 6 services for SPORTS asset class: instruments-service, market-data-processing-service, ml-training-service, ml-inference-service, strategy-service, execution-service"
    status: pending
  - id: ui-logs-dashboard
    content: "Build logs-dashboard-ui: Real-time log aggregation with Cloud Logging API integration"
    status: completed
  - id: ui-batch-audit
    content: "Build batch-audit-ui: Batch run auditing with GCS lifecycle events and BigQuery integration"
    status: completed
  - id: ui-ml-deployment
    content: "Build ml-training-ui: ML model deployment management with A/B testing support"
    status: completed
  - id: ui-trading-analytics
    content: "Build trading-analytics-ui: Live trading performance analytics with equity curve, Sharpe ratio, drawdown charts"
    status: completed
  - id: ui-settlement
    content: "Build settlement-ui: Settlement workflow management for options/futures"
    status: cancelled
  - id: ui-client-reporting
    content: "Build client-reporting-ui: Client-facing performance reports with PDF generation"
    status: completed
  - id: augment-uis-sports
    content: "Augment 3 existing UIs for SPORTS: Add asset_class filter and sports-specific views to strategy-service/frontend, execution-service/visualizer-ui, unified-trading-deployment-v3/ui"
    status: pending
  - id: docs-readmes
    content: "Create missing READMEs: 01-domain/README.md, 02-data/README.md, 05-infrastructure/live/README.md"
    status: completed
  - id: docs-live-observability
    content: Create 6 live per-service observability docs with SERVICE_SPECIFIC_EVENTS for features services and market data services
    status: completed
  - id: docs-integration-guides
    content: "Create 4 integration guides: developer-onboarding.md, service-integration.md, exchange-integration.md, deployment-guide.md"
    status: completed
  - id: docs-architecture-diagrams
    content: Create data flow diagrams and error handling patterns documentation with Mermaid diagrams
    status: completed
  - id: venue-expansion-cefi
    content: "Add 5 additional CeFi venue adapters: Huobi, KuCoin, BitMEX, Bitfinex, Gemini"
    status: cancelled
  - id: venue-expansion-defi
    content: "Add 5 DeFi venue adapters: Uniswap v2, Uniswap v3, SushiSwap, Curve, Balancer with The Graph and Alchemy integration"
    status: completed
  - id: venue-expansion-tradfi
    content: Add Interactive Brokers adapter with IB Gateway API for stocks, bonds, futures, options
    status: pending
isProject: false
notes: |
  Status Update (2026-02-22 Audit): 13/23 todos completed, 1 cancelled (57% → 60% active completion).
  
  ✅ COMPLETED (5 additional verified):
  - 5 UI services built (logs-dashboard, batch-audit, ml-deployment, trading-analytics, client-reporting)
  - 5 DeFi adapters implemented (Uniswap v2, Uniswap v3, Curve, Balancer, plus others)
  - 16 live observability docs created (exceeds 6 requested)
  - Live mode in 2 services (instruments-service, market-data-processing-service)
  
  🔄 IN PROGRESS (1 todo - 2/5 services done):
  - Live mode: ✅ instruments-service ✅ market-data-processing-service
  - Pending: market-tick-data-handler, features-volatility-service, strategy-service
  - N/A: features-calendar-service (library only, consumed by other services, no CLI)
  
  ❌ CANCELLED (2 todos):
  - CeFi venue expansion (Huobi, KuCoin, BitMEX, Bitfinex, Gemini) - NOT trading on these venues
    Evidence: NOT in venues.yaml, expected_start_dates.yaml, or codex docs
    Only appear in third-party library code (ccxt/nautilus dependencies)
  - settlement-ui - Backend dependencies not ready
    Evidence: 08-workflows/expiry-settlement.md shows [PLANNED] for options/futures workflows
    Backend: settlement-backend.md in "Specification Phase", implementation checklist empty
    Only DeFi settlements implemented (strategy-service/settlement_service.py)
  
  ⏳ PENDING (7 major todos):
  - Sports integration (data migration + features-sports-service + service augmentation)
  - TradFi venue expansion (Interactive Brokers - VALID, nautilus has full IB Gateway adapter)
  - Sports UI augmentation
  
  Current venue scope (from venues.yaml):
  - CeFi: BINANCE-SPOT, BINANCE-FUTURES, DERIBIT, BYBIT, OKX, UPBIT, COINBASE, HYPERLIQUID, ASTER
  - TradFi: CME, CBOE, NASDAQ, NYSE, ICE, FX
  - DeFi: 15+ protocols (AAVE, Uniswap, Curve, Balancer, etc.)
---

# Full Service Expansion: Live, Batch, Libraries, UI & Sports

## Executive Summary

Based on comprehensive codebase analysis, the unified trading system has **35 documented services** with **20 fully implemented** (57% complete). This plan delivers:

- **15 missing/skeleton services** to 100% implementation
- **Batch + Live modes** for all pipeline services (currently 11/16 have live mode)
- **5 unified libraries** completion (2 at 0%, 2 at ~95-98% missing, 1 at 60% missing)
- **19+ venue adapters** for market and order interfaces (currently 1 partial)
- **Sports integration** (migrate existing sports-betting-services + create features-sports-service)
- **6+ UI services** (batch-audit-ui, logs-dashboard-ui, ml-training-ui, trading-analytics-ui, settlement-ui, client-reporting-ui)
- **Documentation gaps** (READMEs, live per-service docs, integration guides)

---

## Phase 1: Foundation Libraries (CRITICAL PATH)

**Rationale**: All services depend on these libraries. Must complete before service expansion.

### 1.1 unified-events-interface (NEW - 0% implemented)

**Purpose**: Mode-aware event logging (batch → GCS, live → PubSub)

**Implementation**:

- Create repo structure (pyproject.toml, Dockerfile, quality gates, tests)
- Implement lifecycle events (11 standard: STARTED, STOPPED, FAILED, etc.)
- Implement coordination events (service-to-service signaling)
- Implement mode-aware writers:
  - Batch: Write to `gs://lifecycle-events/YYYY/MM/DD/{service_name}_events.jsonl`
  - Live: Publish to `projects/{project}/topics/lifecycle-events`
- Implement event schemas with Pydantic validation
- Add to `unified-trading-services` as dependency pattern

**Files to create**:

- `unified-events-interface/unified_events_interface/__init__.py`
- `unified-events-interface/unified_events_interface/schemas.py` (event models)
- `unified-events-interface/unified_events_interface/writers.py` (GCS + PubSub)
- `unified-events-interface/unified_events_interface/events.py` (lifecycle + coordination)
- `unified-events-interface/tests/unit/test_events.py`
- `unified-events-interface/tests/integration/test_writers.py`

**Acceptance**: All 11 lifecycle events logged; mode detection works; tests pass

---

### 1.2 unified-config-interface (NEW - 0% implemented)

**Purpose**: Type-safe Pydantic configs with multi-source loading (env, Secret Manager, YAML)

**Implementation**:

- Create repo structure
- Implement base config class (`UnifiedCloudServicesConfig` pattern)
- Implement multi-source loaders:
  - Environment variables (12-factor app pattern)
  - Secret Manager (GCP Secret Manager, AWS Secrets Manager)
  - YAML/JSON files (local dev)
- Implement environment-aware configs (dev/staging/prod)
- Cloud-agnostic abstractions (GCP ↔ AWS)
- Validation and error handling

**Files to create**:

- `unified-config-interface/unified_config_interface/__init__.py`
- `unified-config-interface/unified_config_interface/base.py` (base config class)
- `unified-config-interface/unified_config_interface/loaders.py` (multi-source loading)
- `unified-config-interface/unified_config_interface/validators.py`
- `unified-config-interface/tests/unit/test_config.py`

**Acceptance**: Services can load config from multiple sources; validation works; tests pass

---

### 1.3 unified-market-interface Completion (95% missing)

**Current state**: Binance adapter only (basic normalization)

**Priority adapters** (Phase 1 - Top 5 CeFi):

1. **Coinbase** (REST + WebSocket)
2. **OKX** (REST + WebSocket)
3. **Deribit** (REST + WebSocket, options support)
4. **Bybit** (REST + WebSocket)

**Implementation per adapter**:

- Create `unified_market_interface/adapters/{venue}.py`
- Implement normalization to canonical schemas:
  - `CanonicalTrade` (timestamp, price, size, side, trade_id)
  - `CanonicalOrderBook` (bids, asks, timestamp)
  - `CanonicalTicker` (last_price, bid, ask, volume)
- Implement rate limiting metadata
- Implement instrument ID mapping (venue format → canonical format)
- Add tests (`tests/unit/test_adapter_{venue}.py`)

**Files to create per venue**:

- `unified-market-interface/unified_market_interface/adapters/{venue}.py`
- `unified-market-interface/tests/unit/test_adapter_{venue}.py`
- `unified-market-interface/tests/integration/test_{venue}_live.py`

**Factory function**:

- Create `unified_market_interface/factory.py`:
  - `get_market_adapter(venue: str) -> BaseMarketAdapter`

**Acceptance**: 5 adapters normalize data correctly; factory function works; tests pass

---

### 1.4 unified-trade-execution-interface Completion (98% missing)

**Current state**: Binance adapter skeleton (placeholder methods)

**Priority adapters** (Phase 1 - Top 5 CeFi):

1. **Binance** (complete skeleton → real API integration)
2. **Coinbase**
3. **OKX**
4. **Deribit**
5. **Bybit**

**Implementation per adapter**:

- Implement authentication/signing (HMAC-SHA256 for CeFi)
- Implement order placement:
  - `place_order(order: CanonicalOrder) -> CanonicalFill`
  - `cancel_order(order_id: str) -> bool`
  - `get_order_status(order_id: str) -> CanonicalOrder`
- Implement account queries:
  - `get_account_state() -> AccountState`
  - `get_positions() -> List[Position]`
  - `get_margin_state() -> MarginState`
- Implement rate limiting enforcement
- StrategyInstruction → venue order translation
- Add tests

**Files to complete**:

- `unified-trade-execution-interface/unified_trade_execution_interface/adapters/binance.py` (remove TODOs)
- `unified-trade-execution-interface/unified_trade_execution_interface/adapters/{venue}.py` (4 new)
- `unified-trade-execution-interface/unified_trade_execution_interface/factory.py`
- `unified-trade-execution-interface/tests/unit/test_adapter_{venue}.py` (5 files)
- `unified-trade-execution-interface/tests/integration/test_{venue}_live.py` (5 files)

**Acceptance**: Real orders can be placed on testnet; account state fetched; tests pass

---

### 1.5 execution-algo-library Completion (60% missing)

**Current state**: TWAP and VWAP implemented

**Missing algorithms**:

1. **Iceberg** (hide large orders, show small slices)
2. **POV** (Percentage of Volume - track market volume)
3. **SOR** (Smart Order Routing - split across venues)

**Implementation per algorithm**:

- Create `execution_algo_library/algorithms/{algo}.py`
- Implement `ExecutionAlgorithm` interface:
  - `generate_child_orders() -> List[ChildOrder]`
  - `update_state(market_data: dict) -> None`
- Implement config schemas (`IcebergConfig`, `POVConfig`, `SORConfig`)
- Add backtest support (simulation mode)
- Integrate with `unified-trade-execution-interface` for actual order placement

**Files to create**:

- `execution-algo-library/execution_algo_library/algorithms/iceberg.py`
- `execution-algo-library/execution_algo_library/algorithms/pov.py`
- `execution-algo-library/execution_algo_library/algorithms/sor.py`
- `execution-algo-library/execution_algo_library/schemas.py` (add configs)
- `execution-algo-library/tests/unit/test_{algo}.py` (3 files)
- `execution-algo-library/tests/integration/test_backtest_{algo}.py` (3 files)

**Acceptance**: 3 algorithms generate child orders; backtest mode works; tests pass

---

## Phase 2: Complete Pipeline Services (Batch + Live)

**Rationale**: Core data pipeline must support both batch (historical) and live (real-time) modes per batch-live-symmetry.md

### 2.1 Services with Live Mode Pending

**Services to augment** (6 services):

1. **instruments-service** (batch ✅, live ⏳)
  - Add live refresh mode (intraday instrument changes)
  - WebSocket subscriptions for new listings
  - Update `gs://instruments/` on changes
2. **market-tick-data-handler** (batch ✅, live ⏳)
  - Add WebSocket feeds (Binance, Coinbase, OKX, Deribit, Bybit)
  - Real-time tick persistence to `gs://market-data-tick/`
  - TARDIS persistence integration
3. **market-data-processing-service** (batch ✅, live ⏳)
  - Embed in feature services for live mode
  - Real-time OHLCV aggregation
  - Live orderbook aggregation
4. **features-calendar-service** (batch ✅, live ⏳)
  - Live mode: refresh on calendar updates (rare)
  - Deterministic features rarely change
5. **features-volatility-service** (batch ✅, live ⏳)
  - Live mode: 1-min cadence for IV surface updates
  - Real-time volatility calculations
  - WebSocket orderbook subscriptions for options
6. **strategy-service** (batch ✅, live ⏳)
  - Live instruction emission (stream to execution-service)
  - Real-time strategy evaluation
  - Position-aware signal generation

**Implementation per service**:

- Add `--mode live` CLI flag
- Implement 4-seam pattern:
  - **Data inbound**: WebSocket readers (replace batch GCS readers)
  - **Data outbound**: PubSub publishers (replace batch GCS writers)
  - **Persistence thread**: Async GCS writers (archive live data)
  - **Trigger**: Event-driven (replace batch date loop)
- Update `config.py` with live-specific settings
- Add live per-service docs (`03-observability/live/per-service/{service}.md`)
- Add tests (`tests/integration/test_live_mode.py`)

**Acceptance**: All 6 services run in live mode; data flows correctly; tests pass

---

### 2.2 Skeleton Services to Implement

**Services to build** (3 services):

1. **position-balance-monitor-service** (skeleton only)
  - **Purpose**: Real-time position/balance reconciliation
  - **Batch mode**: Daily reconciliation from fills + orderbook snapshots
  - **Live mode**: Event-driven reconciliation (on fill events)
  - **Output**: `gs://positions/`, `gs://balances/`
  - **Integration**: Subscribe to fill events from execution-service
2. **risk-and-exposure-service** (skeleton only)
  - **Purpose**: Pre-trade risk checks (<100ms)
  - **Batch mode**: Risk report generation
  - **Live mode**: Real-time order validation
  - **Checks**: Position limits, concentration limits, VaR, drawdown, margin
  - **Integration**: Called by execution-service before order placement
3. **pnl-attribution-service** (not found in workspace)
  - **Purpose**: P&L attribution (alpha vs beta, per strategy, per instrument)
  - **Batch mode**: Daily P&L reports
  - **Live mode**: Real-time P&L updates
  - **Output**: `gs://pnl-attribution/`
  - **Integration**: Subscribe to fill events + market data

**Implementation per service**:

- Create repo structure (follow instruments-service as template)
- Implement batch mode first (daily processing)
- Implement live mode (event-driven)
- Implement 4-seam pattern
- Add observability docs
- Add tests (unit, integration, e2e)

**Files to create per service**:

- `{service}/{service}/main.py`
- `{service}/{service}/config.py`
- `{service}/{service}/engine.py`
- `{service}/{service}/schemas.py`
- `{service}/Dockerfile`
- `{service}/cloudbuild.yaml`
- `{service}/tests/unit/test_*.py`
- `{service}/03-observability/batch/per-service/{service}.md`
- `{service}/03-observability/live/per-service/{service}.md`

**Acceptance**: 3 services run in both modes; data validated; tests pass

---

## Phase 3: Sports Integration

**Rationale**: Existing sports-betting-services (~50GB data) needs migration to unified system

### 3.1 Migrate sports-betting-services

**Current state**: Separate repo with 19 feature calculators, arbitrage logic, 50GB+ data in GCS

**Migration plan** (per `02-data/sports-data-migration.md`):

1. **Data migration**:
  - Move `football-raw-data-`* → `gs://market-data-raw/SPORTS/`
  - Move `market-data-tick-sports-`* → `gs://market-data-tick/SPORTS/`
  - Move `football-mapped-consolidated-`* → `gs://market-data-processed/SPORTS/`
  - Move `football-ml-features-`* → `gs://features-sports/`
  - Move `football-ml-models-`* → `gs://ml-models/SPORTS/`
  - Move `football-backtest-results-`* → `gs://backtest-results/SPORTS/`
2. **Code migration**:
  - Extract 19 feature calculators → `features-sports-service/features_sports_service/calculators/`
  - Extract mapping logic → `instruments-service` (augment for sports)
  - Extract arbitrage logic → `strategy-service` (augment for sports arbitrage)
  - Extract backtesting logic → `strategy-service` (augment for sports backtesting)
3. **Delete old repo** (after migration validated):
  - Archive `sports-betting-services/` repo

**Acceptance**: Data in unified structure; old buckets deleted; code extracted

---

### 3.2 Create features-sports-service (NEW)

**Purpose**: Compute 19 feature categories for football betting (per `11-project-management/epics/sports-integration-epic.md`)

**Implementation**:

- Create repo structure (follow features-delta-one-service as template)
- Implement 19 feature calculators:
  - Team features (form, goals scored/conceded, win rate)
  - League context (position, points gap, home/away form)
  - H2H (head-to-head record, recent meetings)
  - Odds features (implied probability, CLV, sharp vs soft)
  - Halftime patterns (HT win rate, FT comeback rate)
  - Goal timing (first goal time, late goal rate)
  - Referee tendencies (cards, penalties, home bias)
  - Venue context (attendance, pitch size, altitude)
  - Weather (temperature, wind, rain)
  - Season context (matchweek, fixture congestion)
  - Advanced stats (xG, xGA, shots on target)
  - Multi-source xG (Understat, FootyStats, Opta)
  - Poisson xG (parametric model)
  - Player lineups (key player missing, lineup strength)
- Time horizons: T-24h, T-60m, T-0, HT
- Output: `gs://features-sports/YYYY/MM/DD/`
- Add batch + live modes

**Files to create**:

- `features-sports-service/features_sports_service/__init__.py`
- `features-sports-service/features_sports_service/main.py`
- `features-sports-service/features_sports_service/engine.py`
- `features-sports-service/features_sports_service/calculators/{19 calculators}.py`
- `features-sports-service/features_sports_service/config.py`
- `features-sports-service/features_sports_service/schemas.py`
- `features-sports-service/tests/unit/test_calculators.py`
- `features-sports-service/tests/integration/test_batch_mode.py`

**Acceptance**: 19 calculators work; batch mode generates features; tests pass

---

### 3.3 Augment Services for Sports

**Services to update** (6 services):

1. **instruments-service** (add sports parser)
  - Add Betfair market ID → API-Football fixture ID mapping
  - Add team/league normalization (canonical names)
  - Add instrument format parser (per `01-domain/sports-instruments.md`)
2. **market-data-processing-service** (add sports clients)
  - Add Odds API client (batch historical odds)
  - Add Betfair Stream WebSocket client (live odds)
  - Add Pinnacle API client (sharp odds)
  - Add API-Football client (fixtures, teams, stats)
  - Add Polymarket CLOB API client (on-chain prediction markets)
3. **ml-training-service** (add sports configs)
  - Add sports model configs (LightGBM for classification)
  - Add walk-forward validation (k-fold + standard modes)
  - Add sports-specific loss functions (Brier score, log loss)
  - Add sports-specific metrics (ROI, Kelly edge, CLV)
4. **ml-inference-service** (add sports models)
  - Add sports model loading (from `gs://ml-models/SPORTS/`)
  - Add sports prediction API endpoint
  - Add batch prediction mode
5. **strategy-service** (add sports strategies)
  - Add arbitrage detection (multi-bookmaker)
  - Add value betting (positive EV vs sharp odds)
  - Add Kelly criterion staking
  - Add sports backtesting logic (stake sizing, commission, P&L)
6. **execution-service** (add sports venues)
  - Add Betfair Exchange API client
  - Add Pinnacle Line API client
  - Add Polymarket CLOB API client
  - Add bet placement logic (different from crypto order books)

**Implementation per service**:

- Add sports-specific modules to existing services
- Add `--asset-class SPORTS` CLI flag
- Update configs with sports-specific settings
- Add tests for sports paths

**Acceptance**: Services handle SPORTS asset class; data flows correctly; tests pass

---

## Phase 4: UI Services (6+ Missing)

**Rationale**: Most documented UIs are not implemented (only 3/9 exist)

### 4.1 Priority UIs to Build

1. **logs-dashboard-ui** (HIGH PRIORITY)
  - **Purpose**: Real-time log aggregation and search
  - **Features**: Filter by service, severity, time range; search text; export logs
  - **Stack**: React + TypeScript + Vite + TanStack Query
  - **Integration**: Cloud Logging API (GCP Logs Explorer)
2. **batch-audit-ui** (HIGH PRIORITY)
  - **Purpose**: Batch run auditing and validation
  - **Features**: View batch runs, success/failure rates, data quality checks, rerun failed batches
  - **Stack**: React + TypeScript + Vite
  - **Integration**: GCS (read lifecycle events), BigQuery (aggregate stats)
3. **ml-training-ui** (MEDIUM PRIORITY)
  - **Purpose**: ML model deployment management
  - **Features**: View models, deploy to inference service, A/B testing, model performance metrics
  - **Stack**: React + TypeScript + Vite
  - **Integration**: `gs://ml-models/`, ml-inference-service API
4. **trading-analytics-ui** (MEDIUM PRIORITY)
  - **Purpose**: Live trading performance analytics
  - **Features**: Equity curve, Sharpe ratio, drawdown, win rate, P&L by strategy/instrument
  - **Stack**: React + TypeScript + Vite + Recharts
  - **Integration**: `gs://backtest-results/`, `gs://pnl-attribution/`, BigQuery
5. **settlement-ui** (LOW PRIORITY)
  - **Purpose**: Settlement workflow management (options expiry, futures delivery)
  - **Features**: View upcoming settlements, approve/reject, view settlement history
  - **Stack**: React + TypeScript + Vite
  - **Integration**: settlement backend API (per `08-workflows/expiry-settlement.md`)
6. **client-reporting-ui** (LOW PRIORITY)
  - **Purpose**: Client-facing performance reports
  - **Features**: Generate PDF reports, monthly statements, performance attribution
  - **Stack**: React + TypeScript + Vite + PDF generation (jsPDF or similar)
  - **Integration**: `gs://pnl-attribution/`, client-model data

**Implementation per UI**:

- Create React app with Vite template
- Implement component structure (pages, components, hooks)
- Integrate with backend APIs or GCS
- Add authentication (if client-facing)
- Add tests (Vitest + React Testing Library)
- Deploy to Cloud Run or Cloud Storage (static hosting)

**Files to create per UI** (example: logs-dashboard-ui):

- `logs-dashboard-ui/package.json`
- `logs-dashboard-ui/vite.config.ts`
- `logs-dashboard-ui/src/App.tsx`
- `logs-dashboard-ui/src/pages/{page}.tsx`
- `logs-dashboard-ui/src/components/{component}.tsx`
- `logs-dashboard-ui/src/hooks/{hook}.ts`
- `logs-dashboard-ui/src/api/{api}.ts`
- `logs-dashboard-ui/tests/{test}.test.tsx`
- `logs-dashboard-ui/Dockerfile`
- `logs-dashboard-ui/cloudbuild.yaml`

**Acceptance**: 6 UIs deployed; functional; tests pass

---

### 4.2 Augment Existing UIs for Sports

**UIs to update** (3 existing):

1. **strategy-service/frontend** (backtest wizard)
  - Add `asset_class` dropdown (CRYPTO, SPORTS, DEFI, TRADFI)
  - Add sports-specific inputs (league, season, bookmaker)
  - Add sports-specific results view (ROI, CLV, Brier score)
2. **execution-service/visualizer-ui** (backtest analysis)
  - Add `asset_class` filter
  - Add sports-specific charts (odds movement, stake sizing, bookmaker comparison)
3. **unified-trading-deployment-v3/ui** (deployment dashboard)
  - Add sports services to service list
  - Add sports data status monitoring

**Implementation per UI**:

- Add `asset_class` filter to all views
- Add sports-specific components (conditionally rendered)
- Update API calls to handle sports data

**Acceptance**: UIs support sports; filters work; tests pass

---

## Phase 5: Documentation Completion

**Rationale**: Documentation gaps prevent effective onboarding and maintenance

### 5.1 Missing READMEs (HIGH PRIORITY)

1. **01-domain/README.md**
  - Overview of domain concepts (strategies, asset classes, client model)
  - Link to 10 existing docs
  - Decision tree for asset class selection
2. **02-data/README.md**
  - Overview of data architecture (raw, processed, features)
  - Schema governance principles
  - Subscription model overview
  - Link to 7 existing docs
3. **05-infrastructure/live/README.md** (referenced but missing)
  - Live infrastructure patterns (WebSocket management, PubSub, event-driven)
  - Deployment topology for live services
  - Monitoring and alerting setup

**Acceptance**: 3 READMEs created; linked correctly; reviewed

---

### 5.2 Live Per-Service Observability Docs (6 missing)

**Services needing live docs**:

1. features-calendar-service
2. features-delta-one-service
3. features-volatility-service
4. features-onchain-service
5. market-data-processing-service
6. market-tick-data-handler

**Implementation per doc**:

- Follow template: `03-observability/live/per-service/{service}.md`
- Document SERVICE_SPECIFIC_EVENTS (beyond 11 standard lifecycle events)
- Document live-specific metrics (latency, throughput, WebSocket health)
- Document alerting rules

**Acceptance**: 6 live docs created; SERVICE_SPECIFIC_EVENTS populated

---

### 5.3 Integration Guides (MEDIUM PRIORITY)

1. **Developer Onboarding Guide** (`06-coding-standards/developer-onboarding.md`)
  - Getting started (clone repos, install deps, run quality gates)
  - Local development environment setup
  - First contribution walkthrough
  - Code review guidelines
2. **Service-to-Service Integration Guide** (`04-architecture/service-integration.md`)
  - How services discover and connect
  - API contracts between services
  - Data contract versioning strategy
  - Breaking change migration guide
3. **Exchange API Integration Guide** (`02-data/exchange-integration.md`)
  - Tardis integration (historical market data)
  - Databento integration (futures/options data)
  - The Graph integration (on-chain DeFi data)
  - Alchemy integration (Ethereum node)
4. **End-to-End Deployment Guide** (`05-infrastructure/deployment-guide.md`)
  - From code to production (step-by-step)
  - Rollback procedures per service
  - Blue-green deployment strategy
  - Pre-production validation checklist

**Acceptance**: 4 integration guides created; tested by new developer

---

### 5.4 Architecture Diagrams (LOW PRIORITY)

1. **Data Flow Diagrams** (`04-architecture/data-flow-diagrams.md`)
  - Mermaid diagrams for each service layer:
    - Instruments layer (instruments-service)
    - Market data layer (tick handler → processing)
    - Features layer (4 feature services)
    - ML layer (training → inference)
    - Strategy layer (signal generation)
    - Execution layer (execution services)
    - Post-trade layer (position monitor, risk, P&L)
2. **Error Handling Patterns** (`04-architecture/error-handling-patterns.md`)
  - Retry patterns (exponential backoff, circuit breaker)
  - Error propagation (logging, alerting, dead-letter queues)
  - Graceful degradation strategies

**Acceptance**: Diagrams render correctly; patterns documented

---

## Phase 6: Venue Expansion (14+ Additional Adapters)

**Rationale**: After Phase 1 (top 5 CeFi), expand to DeFi and TradFi

### 6.1 Additional CeFi Venues (5 venues)

1. Huobi
2. KuCoin
3. BitMEX
4. Bitfinex
5. Gemini

**Implementation**: Same pattern as Phase 1.3 and 1.4

---

### 6.2 DeFi Venues (5 venues)

1. Uniswap v2
2. Uniswap v3
3. SushiSwap
4. Curve
5. Balancer

**Implementation**:

- Use The Graph for historical data
- Use Alchemy for real-time event logs
- Use eth_account for transaction signing
- Implement swap execution (different from order books)

---

### 6.3 TradFi Venues (1 venue)

1. Interactive Brokers

**Implementation**:

- Use IB Gateway API
- Implement traditional asset classes (stocks, bonds, futures, options)
- Handle margin requirements (Reg T, portfolio margin)

---

### 6.4 Sports Venues (3 venues)

1. Betfair Exchange
2. Pinnacle
3. Polymarket

**Implementation**: See Phase 3.3 (augment execution-service)

---

## Implementation Strategy

### Parallelization

**Can be done in parallel**:

- Phase 1 libraries (5 repos, 5 developers)
- Phase 2 services (9 services, 9 developers)
- Phase 4 UIs (6 UIs, 6 developers)
- Phase 5 documentation (4 guides, 4 developers)

**Must be sequential**:

- Phase 1 → Phase 2 (services depend on libraries)
- Phase 3 (sports) can start after Phase 1.3, 1.4 (market/order interfaces)

### Quality Gates

**Every service/library must**:

- Pass `bash scripts/quality-gates.sh --no-fix`
- Have ≥35% test coverage (80% for audit readiness)
- Have event logging tests (`tests/unit/test_event_logging.py`)
- Follow batch-live symmetry (if pipeline service)

### Rollout

1. Phase 1: 4-6 weeks (foundation libraries)
2. Phase 2: 6-8 weeks (pipeline services)
3. Phase 3: 4-6 weeks (sports integration)
4. Phase 4: 6-8 weeks (UI services)
5. Phase 5: 2-4 weeks (documentation)
6. Phase 6: 8-12 weeks (venue expansion)

**Total**: 30-44 weeks (~7-11 months) with 10-15 developers

---

## Success Metrics

- ✅ All 35 documented services implemented (100%)
- ✅ All pipeline services support batch + live modes (16/16)
- ✅ All 5 unified libraries complete (100%)
- ✅ 19+ venue adapters implemented (market + order interfaces)
- ✅ Sports integration complete (SPORTS asset class fully supported)
- ✅ 9/9 UI services deployed (100%)
- ✅ Documentation coverage ≥95% (all gaps filled)
- ✅ Quality gates pass for all repos (ruff v0.15.0, pytest, coverage ≥35%)

---

## Risk Mitigation

**Risks**:

1. **Dependency hell**: Libraries must be completed first (Phase 1 critical path)
2. **Venue API changes**: Adapters may break (mitigation: automated tests, CI/CD)
3. **Sports data migration**: 50GB+ data transfer (mitigation: parallel migration, validation)
4. **Team coordination**: 15+ developers on 35 repos (mitigation: clear ownership, daily standups)

**Mitigation strategies**:

- Strict dependency management (uv lock files)
- Automated quality gates (no manual bypasses)
- Codex alignment checks (pre-commit hooks)
- Per-repo `.cursorrules` (service-specific patterns)

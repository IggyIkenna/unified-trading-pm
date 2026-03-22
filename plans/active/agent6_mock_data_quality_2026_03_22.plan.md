---
name: agent6-mock-data-quality
overview:
  Enhance seed data realism, add org-scoped filtering, persona-based entitlement filtering, deterministic seeding for CI
todos:
  - id: a6-p0-persona-ssot
    content: |
      - [ ] [AGENT] P0. Create a shared persona definition file that is the SSOT for both auth-api and the UI. Currently auth-api has `MOCK_USERS`/`MOCK_ORGS` in `mock_data.py` and the UI has personas in `hooks/use-auth.ts`. Create `unified-trading-api/unified_trading_api/mock_data/personas.py` with:
        - 4 organizations: Odum Internal (odum-internal), Alpha Capital (acme), Beta Fund (beta), Vertex Partners (vertex)
        - 5 personas: admin, internal-trader, client-full (acme), client-premium (vertex), client-data-only (beta)
        - Entitlements per persona matching the UI's entitlement checks
        Export these as constants. auth-api should import from here (or duplicate with same IDs). UI persona definitions must use the same org IDs and entitlement keys.
    status: todo
  - id: a6-p0-org-scoped-seed
    content: |
      - [ ] [AGENT] P0. Update ALL seed data in `seed.py` to include `org_id` field on every record. Distribution:
        - odum-internal: 60% of data (internal strategies, positions, orders)
        - acme (Alpha Capital): 20% of data
        - vertex (Vertex Partners): 12% of data
        - beta (Beta Fund): 8% of data (data-only, minimal trading)
        When a client persona queries, they only see their org's data. Admin/internal sees all.
    status: todo
  - id: a6-p1-strategies-alignment
    content: |
      - [ ] [AGENT] P0. Align seed strategies with the UI's `lib/trading-data.ts` STRATEGIES registry. Currently the UI generates 18 strategies client-side with seeded random. The API seed should have the SAME 18 strategies with the same IDs, names, asset classes, and similar PnL ranges. This ensures the Dashboard (which currently uses client-side data) can be migrated to API calls without visible difference.
    status: todo
  - id: a6-p1-positions-realistic
    content: |
      - [ ] [AGENT] P0. Seed realistic positions: 15-20 positions across 5 venues (Binance, Deribit, Hyperliquid, Uniswap V3, Aave V3). Each position should have: instrument (matching real instrument symbols), side (long/short), quantity, entry_price, current_price (slightly different from entry for realistic PnL), unrealized_pnl, margin_used, venue, org_id, strategy_id.
    status: todo
  - id: a6-p1-orders-realistic
    content: |
      - [ ] [AGENT] P0. Enhance orders seed from 4 to 20+. Include orders across all venues, with status distribution: 40% filled, 20% partially_filled, 20% open, 10% cancelled, 10% rejected. Each order should reference a valid strategy_id and org_id.
    status: todo
  - id: a6-p1-fills-realistic
    content: |
      - [ ] [AGENT] P1. Enhance fills seed from 3 to 30+. Each fill should reference a valid order_id. Include realistic slippage (0.01-0.05% from order price), realistic fees (venue-specific fee rates).
    status: todo
  - id: a6-p1-alerts-realistic
    content: |
      - [ ] [AGENT] P0. Seed 15-20 alerts with realistic scenarios:
        - 2-3 critical: "Position limit breached on BTC-USDT", "Margin call warning on Deribit"
        - 4-5 high: "Strategy drawdown exceeds threshold", "Venue latency spike on Hyperliquid"
        - 5-6 medium: "Batch/live PnL drift > 5%", "Feature staleness detected"
        - 3-4 low: "Strategy rebalance scheduled", "Model retrain due"
        Each alert should have: severity, message, source (service name), strategy_id, org_id, timestamp, acknowledged (bool).
    status: todo
  - id: a6-p1-ml-data
    content: |
      - [ ] [AGENT] P1. Seed ML data:
        - 8 models: mean-reversion-btc, momentum-multi-asset, vol-surface-eth, etc. With versions (v1.0, v1.1, v2.0), status (production/staging/deprecated), metrics (sharpe, accuracy, precision)
        - 12 experiments: linked to models, with hyperparameters, training metrics (loss curve data points), duration
        - 20 features: with importance scores, drift metrics, categories
        - 5 training jobs: queued/running/completed/failed
    status: todo
  - id: a6-p1-settlements-invoices
    content: |
      - [ ] [AGENT] P1. Seed settlement and invoicing data:
        - 8 settlements: various status (pending/matched/disputed/settled), with trade references
        - 5 invoices: management fee invoices with calculation breakdown (AUM * fee_rate / 365 * days)
        - 3 fee schedules: tier-based (basic: 0.5% mgmt, premium: 1% mgmt + 10% perf, full: 1.5% mgmt + 15% perf)
    status: todo
  - id: a6-p1-services-health
    content: |
      - [ ] [AGENT] P0. Seed service health data matching actual 21 services. Each record: name (matching real service names from workspace-manifest.json), status (healthy/degraded/down), latency_ms, last_check, version, uptime_pct. Most services healthy, 1-2 degraded for realism.
    status: todo
  # ── Phase 1C: Real-Time Market Data Seeds (CRITICAL for Demo) ──
  - id: a6-p1c-timeseries-pnl
    content: |
      - [ ] [AGENT] P0. Seed PnL time-series data for ALL 18 strategies: 180 daily data points per strategy (3,240 total). Each point: `{ date, cumulative_pnl, daily_pnl, drawdown, nav }`. Generate with realistic equity curves:
        - Start from strategy inception date (stagger across last 12 months)
        - Trend: slightly positive (60% of strategies profitable)
        - Drawdowns: 2-3 per strategy, ranging 5-15% max
        - Correlation: crypto strategies correlated to BTC (seed BTC price series first, derive others)
        - Include YTD, MTD, QTD breakpoints for reporting
        Store in MockStateStore `pnl_timeseries` collection. API serves via `GET /analytics/timeseries`.
        CRITICAL: These must match closely enough to `lib/trading-data.ts` output that the Dashboard looks the same after migration.
    status: todo
  - id: a6-p1c-ohlcv-candles
    content: |
      - [ ] [AGENT] P0. Seed OHLCV candle data for 10 instruments across 4 intervals:
        - Instruments: BTC-USDT, ETH-USDT, SOL-USDT, AVAX-USDT, LINK-USDT, UNI-USDT, AAVE-USDT, DOGE-USDT, ARB-USDT, OP-USDT
        - Intervals: 1m (200 candles), 5m (200), 1h (200), 1d (200)
        - Total: 10 instruments * 4 intervals * 200 candles = 8,000 candle records
        - Generate with Brownian motion: start from a realistic base price, random walk with drift
        - Volume profile: higher at opens/closes, lower mid-session
        - Store in MockStateStore `candles_1m`, `candles_5m`, `candles_1h`, `candles_1d` collections
        - API serves via `GET /market-data/candles?instrument=BTC-USDT&interval=1h&limit=200`
    status: todo
  - id: a6-p1c-tickers-seed
    content: |
      - [ ] [AGENT] P0. Seed initial ticker prices in `tickers_live` collection for all 10 instruments. Each ticker: `{ instrument, price, bid, ask, volume_24h, change_24h_pct, timestamp }`. These serve as the starting point for the WebSocket mock tick generator (Agent 5). Prices should be realistic as of today. Also seed `tickers_batch` with yesterday's close prices (slightly different from live).
    status: todo
  - id: a6-p2-batch-live-data
    content: |
      - [ ] [AGENT] P0. Seed separate batch and live data collections in MockStateStore. ALL domains must have both `_live` and `_batch` variants. Live collections persist to `.local-dev-cache/unified-trading-api/` as JSONL (survive restarts, get updated by WebSocket ticks and manual actions). Batch collections are seeded once and immutable until reset.

        Collection naming convention:
        - `positions_live` / `positions_batch`
        - `orders_live` / `orders_batch`
        - `pnl_live` / `pnl_batch`
        - `tickers_live` / `tickers_batch`
        - `pnl_timeseries_live` / `pnl_timeseries_batch`

        When API receives `mode=batch&as_of=2026-03-21`, it reads from `*_batch` collections.
        When API receives `mode=live` (or no mode param), it reads from `*_live` collections.

        Batch vs live differences (to make the switch visually meaningful):
        - Batch PnL includes reconciliation adjustments (+/- 0.1-0.5% from live)
        - Batch positions may have 1-2 fewer positions (unreconciled fills not yet in batch)
        - Batch uses official close prices; live uses last tick prices
        - Batch has exact fee breakdowns; live has estimated fees
        - Batch orders all have final status (filled/cancelled); live has open/partial orders

        This architecture means: in production, the same directory is populated by real services.
        In mock, it's populated by seed data + WebSocket tick generator. The API code is identical.
    status: todo
  - id: a6-p3-deterministic
    content: |
      - [ ] [AGENT] P1. Add seed versioning: `SEED_VERSION = "1.0.0"` in seed.py. MockStateStore checks cached seed version against current — if mismatch, clears cache and re-seeds. This ensures developers always get fresh data after code pulls.
    status: todo
  - id: a6-p3-ci-mode
    content: |
      - [ ] [AGENT] P1. When `MOCK_STATE_MODE=deterministic` (CI mode): skip JSONL persistence, use pure in-memory store, seed on every startup. When `MOCK_STATE_MODE=interactive` (dev mode): persist mutations to `.local-dev-cache/unified-trading-api/`, survive restarts.
    status: todo
  - id: a6-p4-remove-msw
    content: |
      - [ ] [AGENT] P1. In unified-trading-system-ui: remove `lib/mocks/` directory (browser.ts, server.ts, handlers/, fixtures/, utils.ts — 1,411 lines total). Remove MSW from package.json dependencies. Remove `startMockWorker()` call from app initialization. The UI now always calls the real API at port 8030 (which handles mock/real internally).
    status: todo
  - id: a6-p4-migrate-trading-data
    content: |
      - [ ] [AGENT] P1. Migrate the Dashboard page from client-side `lib/trading-data.ts` data to API calls. Currently the Dashboard imports ORGANIZATIONS, CLIENTS, STRATEGIES, getFilteredStrategies, getAggregatedPnL, etc. from trading-data.ts. Replace these with API hook calls: `useTradingOrgs()`, `useTradingPnl()`, `useTradingTimeseries()`, `useTradingPerformance()` (these hooks already exist in `hooks/api/use-trading.ts`). The seed data in the API must match the trading-data.ts output closely enough that the Dashboard looks the same.
    status: todo
  - id: a6-p5-seed-tests
    content: |
      - [ ] [AGENT] P0. Add tests verifying seed data quality:
        1. Every record has org_id field
        2. All strategy_ids in positions/orders reference valid strategies
        3. All order_ids in fills reference valid orders
        4. Org filtering works (client-full sees only acme data)
        5. Batch vs live data returns different results
        6. Reset clears mutations but preserves seed
    status: todo
isProject: false
---

# Notes & Context

## CRITICAL: Read Before Any Work

1. Read `unified-trading-pm/plans/active/CITADEL_VISION_2026_03_22.md` — system-wide vision
2. Read `unified-trading-system-ui/UI_STRUCTURE_MANIFEST.json` — see exact per-page API hooks and what data each page
   expects
3. Read `unified-trading-system-ui/lib/trading-data.ts` (770L) — the client-side data you're replacing. Seed data MUST
   match this closely.

## KEY CONSTRAINT: Visual Parity After Migration

The Dashboard currently uses `lib/trading-data.ts` which generates 18 strategies, 4 orgs, time series, PnL components.
After migration to API, the Dashboard must look IDENTICAL. Same strategy names, similar numbers, same org names.
Cross-reference `lib/strategy-registry.ts` (strategy definitions) and `lib/taxonomy.ts` (asset class enums).

## Absorbed from prior plans

- mock_data_rollout_2026_03_18: Mock data enhancement (46% done)
- plan_c_domain_data_api: Mock provider completeness
- plan_d_testnet_stress_testing: Seed hardening, scenario infrastructure
- production_mock_e2e_plan_d90c8f20: Mock E2E testing

## Current seed data (what exists)

- orders: 4 records (need 20+)
- fills: 3 records (need 30+)
- execution_venues: 5 records (good)
- algos: 4 records (good)
- backtests: partial (need 8+)

## UI client-side data to replace

- `lib/trading-data.ts` (770 lines) — generates 18 strategies, org/client hierarchy, PnL time series
- `lib/strategy-registry.ts` — canonical strategy definitions
- `lib/ml-mock-data.ts` — ML mock data
- `lib/execution-platform-mock-data.ts` — execution mock data
- `lib/data-service-mock-data.ts` — data service mock data
- `lib/strategy-platform-mock-data.ts` — strategy mock data

## Key constraint

- Seed data MUST match the UI's current client-side data closely enough that the Dashboard looks the same after
  migration. Same strategy names, similar PnL ranges, same org names.

## New scope (added 2026-03-22 gap analysis)

- PnL time-series: 180 daily data points per strategy (3,240 total) — critical for Dashboard charts
- OHLCV candles: 10 instruments _ 4 intervals _ 200 candles = 8,000 records — critical for Trading Terminal
- Ticker seeds: 10 instruments with realistic prices — starting point for WebSocket ticks
- Batch/live collection separation with JSONL persistence to .local-dev-cache/
- All collections need both `_live` and `_batch` variants

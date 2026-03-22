---
name: agent2-trading-and-execution
overview:
  Wire dashboard-terminal navigation, restore ManualTradingPanel, wire BatchLiveRail, ensure Trading (Run) and Execution
  (Execute) services have real content
todos:
  - id: a2-p0-dashboard-to-terminal
    content: |
      - [ ] [AGENT] P0. On the Dashboard page (`app/(platform)/dashboard/page.tsx`), ensure the "Strategy Performance" table rows link to `/services/trading/strategies/{id}`. Add a prominent "Open Trading Terminal" button/link at the top-right that navigates to `/services/trading/overview`. The Dashboard IS the Command Center — it should feel like one click away from the terminal.
    status: todo
  - id: a2-p0-terminal-to-dashboard
    content: |
      - [ ] [AGENT] P0. On the Trading Terminal page (`services/trading/overview`), add a "← Command Center" link in the breadcrumbs or as a back-nav element. The terminal and dashboard should feel like two views of the same workspace.
    status: todo
  - id: a2-p1-restore-manual-trading
    content: |
      - [ ] [AGENT] P0. Restore `ManualTradingPanel` from git history (deleted in commit `5c24fa2` from `live-health-monitor-ui`). The component was 256 lines with fields: client_id, instrument, side (BUY/SELL), quantity, venue, price, reason. Plus order preview, submission, success/error handling. Restore it as `components/trading/manual-trading-panel.tsx` in the main UI. Render it as a slide-out drawer/panel triggered by a "Manual Trade" button on the Trading Terminal page. Wire it to call `POST /execution/orders` on the unified-trading-api (which in mock mode creates an order in MockStateStore).
    status: todo
  - id: a2-p1-restore-execution-client
    content: |
      - [ ] [AGENT] P1. Restore `executionClient.ts` from same git history (122 lines — API client for manual trade endpoint with CSRF protection, retry logic). Adapt it to use the `apiFetch` pattern from `lib/api/fetch.ts` instead of standalone fetch.
    status: todo
  - id: a2-p2-terminal-tab
    content: |
      - [ ] [AGENT] P0. Verify `/services/trading/overview` (818 lines) has: candlestick chart, order book, order entry form, strategy-instrument mapping. It already does — just verify it renders correctly and all API hooks connect. Check `useTickers()`, `usePositions()`, `useAlerts()` hooks return data in mock mode.
    status: todo
  - id: a2-p2-positions-tab
    content: |
      - [ ] [AGENT] P0. Verify `/services/trading/positions` has a real positions table with columns: instrument, side, quantity, entry price, current price, PnL, venue, updated_at. Should call `usePositions()` hook → `GET /positions/active` API. In mock mode, API should return 8-15 realistic positions across multiple venues (Binance, Deribit, Hyperliquid, Uniswap, Aave). If the page is a stub/placeholder, build it using the data from `seed.py` "positions" domain.
    status: todo
  - id: a2-p2-orders-tab
    content: |
      - [ ] [AGENT] P0. Verify `/services/trading/orders` has a real orders blotter with columns: order_id, instrument, side, type, price, quantity, filled, status, venue, created_at. Should call `useOrders()` hook → `GET /execution/orders` API. If stub, build using seed data. Add filter controls (venue, status) using the FilterBar component.
    status: todo
  - id: a2-p2-accounts-tab
    content: |
      - [ ] [AGENT] P1. Verify `/services/trading/accounts` has account balances across venues. Should show per-venue balance, margin used/available, total NAV. Wire to `GET /positions/balances` API.
    status: todo
  - id: a2-p2-markets-tab
    content: |
      - [ ] [AGENT] P1. Verify `/services/trading/markets` has market overview: top movers, ticker prices, market status. Wire to `GET /market-data/tickers` API.
    status: todo
  - id: a2-p3-batch-live-terminal
    content: |
      - [ ] [AGENT] P0. Wire batch/live mode switching on the Trading Terminal page. When `useGlobalScope().scope.mode === "batch"`, the terminal should:
        1. Show a banner "Viewing Batch Data — As of {date}"
        2. Candlestick chart shows historical data up to the as-of date
        3. Order book shows end-of-day snapshot for that date
        4. Positions show batch-reconciled positions
        The data difference is driven by the API — the UI sends `mode=batch&as_of={date}` query params, and the API returns batch vs live data from different mock store domains ("positions_batch" vs "positions_live").
    status: todo
  - id: a2-p4-strategy-detail
    content: |
      - [ ] [AGENT] P1. Verify `/services/trading/strategies/[id]` shows strategy detail: name, status, PnL, positions, configuration, audit trail. Wire to `GET /analytics/strategies/{id}` API. Verify `/services/trading/strategies` list page shows all strategies with status badges. Verify `/services/trading/strategies/grid` shows a parameter grid view.
    status: todo
  # ── Phase 4B: Real-Time Trading Feel (CRITICAL for Demo) ──
  - id: a2-p4b-websocket-terminal
    content: |
      - [ ] [AGENT] P0. Wire the Trading Terminal's candlestick chart to the WebSocket mock feed from unified-trading-api (`ws://localhost:8030/ws`). On mount, the terminal should:
        1. Subscribe to the selected instrument (e.g. `{ "action": "subscribe", "instruments": ["BTC-USDT"] }`)
        2. Receive tick updates: `{ instrument, price, volume, bid, ask, timestamp }`
        3. Update the candlestick chart in real-time (append to current candle or create new candle based on interval)
        4. Update the order book display with new bid/ask from ticks
        5. Update the ticker price display in the header
        6. On instrument change, unsubscribe from old and subscribe to new
        This is the SINGLE MOST IMPORTANT feature for demo feel — a terminal with static prices looks dead.
        DEPENDENCY: Agent 5 must implement the WebSocket mock tick generator first.
    status: todo
  - id: a2-p4b-candlestick-historical
    content: |
      - [ ] [AGENT] P0. Wire the candlestick chart to load historical candle data on mount via `GET /market-data/candles?instrument=BTC-USDT&interval=1h&limit=200`. The chart should:
        1. Load 200 historical candles on mount (shows price history)
        2. Append new candles from WebSocket ticks in real-time
        3. Support interval switching (1m, 5m, 1h, 1d) — refetches historical candles on interval change
        4. Use the existing candlestick chart component — just wire data source
        DEPENDENCY: Agent 6 must seed OHLCV candle data; Agent 5 must serve the endpoint.
    status: todo
  - id: a2-p4b-orderbook-depth
    content: |
      - [ ] [AGENT] P0. Wire the order book component to load depth data via `GET /market-data/orderbook?instrument=BTC-USDT`. Display:
        1. 20 bid levels (green) + 20 ask levels (red)
        2. Mid-price and spread
        3. Cumulative depth bars
        4. Refresh on WebSocket tick (or poll every 2s)
        DEPENDENCY: Agent 5/6 must provide the order book endpoint and seed data.
    status: todo
  # ── Phase 5: Execution Service (Execute — separate from Trading) ──
  - id: a2-p5-execution-layout
    content: |
      - [ ] [AGENT] P0. Create `/services/execution/layout.tsx` with EXECUTE_TABS (new tab set). Add "execute" lifecycle stage to lifecycle-mapping.ts between "run" and "observe". Tabs: Analytics | Algos | Venues | TCA | Benchmarks | Candidates | Handoff. Entry point: `/services/execution/overview`. Entitlement gated: `execution-basic` for Analytics/Venues, `execution-full` for Algos/TCA/Benchmarks/Candidates/Handoff.
    status: todo

  - id: a2-p5-execution-analytics
    content: |
      - [ ] [AGENT] P0. Verify `/services/execution/overview` has real execution analytics content: fills breakdown by venue, fill rate, average slippage, venue latency chart, execution quality score. Wire to `GET /execution/fills` and `GET /execution/venues` APIs. This is the main landing tab for the Execution service.
    status: todo

  - id: a2-p5-execution-algos
    content: |
      - [ ] [AGENT] P1. Verify `/services/execution/algos` has: algo comparison table (TWAP, VWAP, IS, Sniper, Iceberg), performance metrics per algo, algo configuration. Wire to `GET /execution/algos` API. Clients with `execution-full` see advanced algo access; basic clients see read-only view.
    status: todo

  - id: a2-p5-execution-venues
    content: |
      - [ ] [AGENT] P0. Verify `/services/execution/venues` has: venue connectivity status, latency per venue, fill rates, uptime, supported instrument types. Wire to `GET /execution/venues` API.
    status: todo

  - id: a2-p5-execution-tca
    content: |
      - [ ] [AGENT] P1. Verify `/services/execution/tca` has: transaction cost analysis with slippage breakdown, benchmark comparison (arrival price, VWAP), implementation shortfall. Wire to API.
    status: todo

  - id: a2-p5-execution-remaining
    content: |
      - [ ] [AGENT] P1. Verify remaining execution tabs: `/services/execution/benchmarks` (benchmark definitions), `/services/execution/candidates` (execution strategy candidates for promotion), `/services/execution/handoff` (handoff from research to live execution).
    status: todo

  # ── Phase 6: Tests ──
  - id: a2-p6-tests
    content: |
      - [ ] [AGENT] P1. Add Playwright tests: 1) Navigate to Trading Terminal → verify chart renders, order book renders, order form visible. 2) Click "Manual Trade" → verify drawer opens with trade form. 3) Toggle batch mode → verify banner appears, data changes. 4) Navigate to Positions tab → verify table renders with data. 5) Navigate to Orders tab → verify table renders with data. 6) Navigate to Execute > Analytics → verify execution data renders. 7) Navigate to Execute > Venues → verify venue status renders.
    status: todo
isProject: false
---

# Notes & Context

## CRITICAL: Read Before Any Work

1. Read `unified-trading-system-ui/UI_STRUCTURE_MANIFEST.json` — SSOT for all page states, routes, and source files
2. Read `unified-trading-pm/plans/active/CITADEL_VISION_2026_03_22.md` — system-wide vision

## TABS-ONLY RULE

- Trading service = ONE page with 6 tabs: Terminal | Positions | Orders | Accounts | Markets | Strategies
- Execution service = ONE page with 7 tabs: Analytics | Algos | Venues | TCA | Benchmarks | Candidates | Handoff
- NO card-based sub-pages. Everything the user needs is accessed via tab switching.
- Strategy detail (`/strategies/[id]`) and strategy grid (`/strategies/grid`) are the only exceptions (drill-down from
  Strategies tab)

## Stub Pages — Exact Source Files (NO from-scratch builds)

| Stub                     | Source to Adapt                                                                                                                                                                     | Lines | Action                                                              |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | ------------------------------------------------------------------- |
| `trading/orders` (24L)   | `components/trading/order-book.tsx` — already has order display. Extract order table from Terminal (818L) which already has order entry form.                                       | 200+  | Build order blotter using existing order-book component + FilterBar |
| `trading/accounts` (24L) | `components/trading/margin-utilization.tsx` (200L) — already renders per-venue margin/balance data. Import directly as tab content, expand with `GET /positions/balances` API wire. | 200   | Import existing component, add API hook                             |

## Pages Using Inline Mock Data — Need API Wiring

| Page                   | Lines | Current Hooks           | Target Hook                                          |
| ---------------------- | ----- | ----------------------- | ---------------------------------------------------- |
| `trading/positions`    | 849   | `useExecutionMode` only | Wire `usePositions()` → `GET /positions/active`      |
| `execution/overview`   | 324   | None (inline mock)      | Wire `GET /execution/fills`, `GET /execution/venues` |
| `execution/candidates` | 350   | None (inline mock)      | Wire `GET /execution/candidates`                     |
| `execution/handoff`    | 367   | None (inline mock)      | Wire `GET /execution/handoff`                        |
| `execution/venues`     | 298   | None (inline mock)      | Wire `GET /execution/venues`                         |

## Key files

- `app/(platform)/dashboard/page.tsx` — Command Center (460 lines, rich)
- `app/(platform)/services/trading/overview/page.tsx` — Trading Terminal (818 lines, rich)
- `app/(platform)/services/trading/layout.tsx` — Trading layout with TRADING_TABS
- `hooks/api/use-positions.ts`, `use-orders.ts`, `use-market-data.ts`, `use-alerts.ts` — API hooks
- `lib/trading-data.ts` — Client-side mock data (770 lines) — will be replaced by API calls
- `components/trading/` — 31 trading components (candlestick, order-book, kpi-card, etc.)

## Absorbed from prior plans

- plan_e_ui_backend_integration: Phase 0B UI→API path mismatch fixes
- live_batch_alignment_audit: Batch/live data architecture decisions
- strategy_system_citadel_master: Strategy lifecycle and handoff flow

## API endpoints needed (all exist in unified-trading-api mock mode)

- GET /execution/orders — orders blotter
- GET /execution/fills — fill history
- GET /execution/venues — venue status
- GET /positions/active — live positions
- GET /positions/balances — account balances
- GET /market-data/tickers — market prices
- GET /analytics/strategies/{id} — strategy detail
- POST /execution/orders — place manual order (needs adding)
- GET /market-data/candles — OHLCV candle data (instrument, interval, limit)
- GET /market-data/orderbook — order book depth (instrument)
- WS /ws — WebSocket mock tick feed (subscribe/unsubscribe by instrument)

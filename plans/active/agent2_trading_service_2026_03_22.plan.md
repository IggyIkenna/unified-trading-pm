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
      - [ ] [AGENT] P0. VERIFY (already exists) `/services/execution/layout.tsx` has EXECUTE_TABS (7 tabs, pages 298-405 lines each already exist). Confirm "execute" lifecycle stage exists in lifecycle-mapping.ts between "run" and "observe". Tabs: Analytics | Algos | Venues | TCA | Benchmarks | Candidates | Handoff. Entry point: `/services/execution/overview`. Entitlement gated: `execution-basic` for Analytics/Venues, `execution-full` for Algos/TCA/Benchmarks/Candidates/Handoff.
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
  # ── Phase 7: Charting & Error States (Gap-Closing) ──
  - id: a2-p7-verify-charting-lib
    content: |
      - [ ] [AGENT] P0. Verify the candlestick chart component in `components/trading/` uses a real charting library (lightweight-charts, TradingView, or recharts) and can render OHLCV data from the API. Check:
        1. Which library is used? Is it in package.json dependencies?
        2. Does the chart component accept OHLCV data arrays as props?
        3. Does it support real-time updates (appending new candles from WebSocket)?
        4. Does it support interval switching (1m, 5m, 1h, 1d)?
        If the chart is a placeholder (static SVG or hardcoded data), wire it to a real charting library. lightweight-charts (by TradingView) is recommended for candlestick + volume.
    status: todo
  - id: a2-p7-error-states-trading
    content: |
      - [ ] [AGENT] P1. Add error and empty states to ALL trading and execution pages:
        1. Every page using useQuery: add `if (isError) return <ApiError error={error} onRetry={refetch} />` (component created by Agent 1)
        2. Every table: add `if (data.length === 0) return <EmptyState title="No orders" description="Place your first trade from the Terminal" />`
        3. Trading Terminal: if WebSocket fails to connect, show fallback with last known prices + "Live feed unavailable" badge
        4. Manual Trade drawer: show toast on submission error with error message from API
    status: todo
  - id: a2-p7-responsive-trading
    content: |
      - [ ] [AGENT] P1. Make Trading Terminal responsive:
        1. Desktop (1280px+): chart + order book + order form side-by-side (current layout)
        2. Tablet (768-1280px): chart full-width on top, order book + order form side-by-side below
        3. Order book: use horizontal scroll on narrow screens
        4. Positions/Orders tables: always wrap in `overflow-x-auto`
        5. Dashboard cards: 4-col grid → 2-col on tablet → 1-col on mobile
    status: todo
  - id: a2-p7-csv-export-tables
    content: |
      - [ ] [AGENT] P1. Add "Export CSV" button to Positions table, Orders table, and Fills table. Client-side CSV generation: serialize visible columns to CSV string → create Blob → trigger download. Use a shared `exportTableToCsv(data, columns, filename)` utility in `lib/utils/csv-export.ts`.
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

## Risk Factors & Mitigations

**RISK 1 (HIGHEST): WebSocket dependency on Agent 5.** The terminal's real-time feel depends on Agent 5's WebSocket tick
generator. If delayed or format differs, terminal is static. MITIGATION: Use EXACT message format from CITADEL_VISION §
Interface Contracts. If WebSocket isn't ready, implement FALLBACK: client-side setInterval with Brownian motion ticks
(same callback interface). Remove fallback when Agent 5 delivers.

**RISK 2: Candlestick chart may not support streaming append.** Component may only accept static OHLCV arrays and
re-render entirely. MITIGATION: Read the candlestick component FIRST. Check charting library. If no streaming support,
use ref-based approach: maintain candle array in ref, append, debounce state updates.

**RISK 3: ManualTradingPanel from git uses incompatible patterns.** Written for live-health-monitor-ui (Vite, different
state). Imports won't work in main UI. MITIGATION: Don't copy-paste the whole component. Extract LOGIC and FIELDS,
rebuild with shadcn/ui (Sheet for drawer, Input, Select, Button). Wire to apiFetch from lib/api/fetch.ts.

**RISK 4: Execution layout conflicts with Agent 1.** Both agents touch execution/layout.tsx. MITIGATION: Agent 2 does
NOT touch layout.tsx. Only touch page.tsx files within execution/ tabs. If layout doesn't exist yet, create minimal one
with TODO comment for Agent 1 to replace.

**RISK 5: WebSocket already has 4,859 lines — may already have tick generator.** Current state baseline says WebSocket
has synthetic tick generator. Don't rebuild what exists. MITIGATION: Read routes/websocket.py FIRST. If tick generation
exists, just verify it matches the interface contract format. If it doesn't match, adapt the UI consumer to the existing
format (don't rewrite the server).

## Absorbed from prior plans

- plan_e_ui_backend_integration: Phase 0B UI→API path mismatch fixes
- live_batch_alignment_audit: Batch/live data architecture decisions
- strategy_system_citadel_master: Strategy lifecycle and handoff flow

## Current state corrections (2026-03-22 audit)

- Execution service pages ALL EXIST (7 tabs, 298-405 lines each) — do NOT build from scratch
- API routes already use service layer DI — do NOT refactor route patterns
- WebSocket already has synthetic tick generator (4,859 lines) — verify it works, don't rebuild
- personas.py already exists (121 lines) — use it for org-scoped data filtering

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

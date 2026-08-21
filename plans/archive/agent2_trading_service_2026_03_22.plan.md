---
doc_type: plan
title: agent2-trading-and-execution
summary: Wire dashboard-terminal navigation, restore ManualTradingPanel, wire BatchLiveRail, ensure Trading (Run) and Execution
  (Execute) services have real content
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service, unified-trading-api, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-22'
todos:
- {id: a2-p0-dashboard-to-terminal, content: '- [x] [AGENT] P0. On the Dashboard page (`app/(platform)/dashboard/page.tsx`), ensure the "Strategy Performance" table rows link to `/services/trading/strategies/{id}`. Add a prominent "Open Trading Terminal" button/link at the top-right that navigates to `/services/trading/overview`. The Dashboard IS the Command Center — it should feel like one click away from the terminal.

    ', status: done}
- {id: a2-p0-terminal-to-dashboard, content: '- [x] [AGENT] P0. On the Trading Terminal page (`services/trading/overview`), add a "← Command Center" link in the breadcrumbs or as a back-nav element. The terminal and dashboard should feel like two views of the same workspace.

    ', status: done}
- {id: a2-p1-restore-manual-trading, content: '- [x] [AGENT] P0. Restore `ManualTradingPanel` from git history (deleted in commit `5c24fa2` from `live-health-monitor-ui`). The component was 256 lines with fields: client_id, instrument, side (BUY/SELL), quantity, venue, price, reason. Plus order preview, submission, success/error handling. Restore it as `components/trading/manual-trading-panel.tsx` in the main UI. Render it as a slide-out drawer/panel triggered by a "Manual Trade" button on the Trading Terminal page. Wire it to call `POST /execution/orders` on the unified-trading-api (which in mock mode creates an order in MockStateStore).

    ', status: done}
- {id: a2-p1-restore-execution-client, content: '- [x] [AGENT] P1. Restore `executionClient.ts` from same git history (122 lines — API client for manual trade endpoint with CSRF protection, retry logic). Adapt it to use the `apiFetch` pattern from `lib/api/fetch.ts` instead of standalone fetch.

    ', status: done}
- {id: a2-p2-terminal-tab, content: '- [x] [AGENT] P0. Verify `/services/trading/overview` (818 lines) has: candlestick chart, order book, order entry form, strategy-instrument mapping. It already does — just verify it renders correctly and all API hooks connect. Check `useTickers()`, `usePositions()`, `useAlerts()` hooks return data in mock mode.

    ', status: done}
- {id: a2-p2-positions-tab, content: '- [x] [AGENT] P0. Verify `/services/trading/positions` has a real positions table with columns: instrument, side, quantity, entry price, current price, PnL, venue, updated_at. Should call `usePositions()` hook → `GET /positions/active` API. In mock mode, API should return 8-15 realistic positions across multiple venues (Binance, Deribit, Hyperliquid, Uniswap, Aave). If the page is a stub/placeholder, build it using the data from `seed.py` "positions" domain.

    ', status: done}
- {id: a2-p2-orders-tab, content: '- [x] [AGENT] P0. Verify `/services/trading/orders` has a real orders blotter with columns: order_id, instrument, side, type, price, quantity, filled, status, venue, created_at. Should call `useOrders()` hook → `GET /execution/orders` API. If stub, build using seed data. Add filter controls (venue, status) using the FilterBar component.

    ', status: done}
- {id: a2-p2-accounts-tab, content: '- [x] [AGENT] P1. Verify `/services/trading/accounts` has account balances across venues. Should show per-venue balance, margin used/available, total NAV. Wire to `GET /positions/balances` API.

    ', status: done}
- {id: a2-p2-markets-tab, content: '- [x] [AGENT] P1. Verify `/services/trading/markets` has market overview: top movers, ticker prices, market status. Wire to `GET /market-data/tickers` API.

    ', status: done}
- {id: a2-p3-batch-live-terminal, content: "- [x] [AGENT] P0. Wire batch/live mode switching on the Trading Terminal page. When `useGlobalScope().scope.mode === \"batch\"`, the terminal should:\n  1. Show a banner \"Viewing Batch Data — As of {date}\"\n  2. Candlestick chart shows historical data up to the as-of date\n  3. Order book shows end-of-day snapshot for that date\n  4. Positions show batch-reconciled positions\n  The data difference is driven by the API — the UI sends `mode=batch&as_of={date}` query params, and the API returns batch vs live data from different mock store domains (\"positions_batch\" vs \"positions_live\").\n", status: done}
- {id: a2-p4-strategy-detail, content: '- [x] [AGENT] P1. Verify `/services/trading/strategies/[id]` shows strategy detail: name, status, PnL, positions, configuration, audit trail. Wire to `GET /analytics/strategies/{id}` API. Verify `/services/trading/strategies` list page shows all strategies with status badges. Verify `/services/trading/strategies/grid` shows a parameter grid view.

    ', status: done}
- {id: a2-p4b-websocket-terminal, content: "- [x] [AGENT] P0. Wire the Trading Terminal's candlestick chart to the WebSocket mock feed from unified-trading-api (`ws://localhost:8030/ws`). On mount, the terminal should:\n  1. Subscribe to the selected instrument (e.g. `{ \"action\": \"subscribe\", \"instruments\": [\"BTC-USDT\"] }`)\n  2. Receive tick updates: `{ instrument, price, volume, bid, ask, timestamp }`\n  3. Update the candlestick chart in real-time (append to current candle or create new candle based on interval)\n  4. Update the order book display with new bid/ask from ticks\n  5. Update the ticker price display in the header\n  6. On instrument change, unsubscribe from old and subscribe to new\n  This is the SINGLE MOST IMPORTANT feature for demo feel — a terminal with static prices looks dead.\n  DEPENDENCY: Agent 5 must implement the WebSocket mock tick generator first.\n", status: done}
- {id: a2-p4b-candlestick-historical, content: "- [x] [AGENT] P0. Wire the candlestick chart to load historical candle data on mount via `GET /market-data/candles?instrument=BTC-USDT&interval=1h&limit=200`. The chart should:\n  1. Load 200 historical candles on mount (shows price history)\n  2. Append new candles from WebSocket ticks in real-time\n  3. Support interval switching (1m, 5m, 1h, 1d) — refetches historical candles on interval change\n  4. Use the existing candlestick chart component — just wire data source\n  DEPENDENCY: Agent 6 must seed OHLCV candle data; Agent 5 must serve the endpoint.\n", status: done}
- {id: a2-p4b-orderbook-depth, content: "- [x] [AGENT] P0. Wire the order book component to load depth data via `GET /market-data/orderbook?instrument=BTC-USDT`. Display:\n  1. 20 bid levels (green) + 20 ask levels (red)\n  2. Mid-price and spread\n  3. Cumulative depth bars\n  4. Refresh on WebSocket tick (or poll every 2s)\n  DEPENDENCY: Agent 5/6 must provide the order book endpoint and seed data.\n", status: done}
- {id: a2-p5-execution-layout, content: '- [x] [AGENT] P0. VERIFY (already exists) `/services/execution/layout.tsx` has EXECUTE_TABS (7 tabs, pages 298-405 lines each already exist). Confirm "execute" lifecycle stage exists in lifecycle-mapping.ts between "run" and "observe". Tabs: Analytics | Algos | Venues | TCA | Benchmarks | Candidates | Handoff. Entry point: `/services/execution/overview`. Entitlement gated: `execution-basic` for Analytics/Venues, `execution-full` for Algos/TCA/Benchmarks/Candidates/Handoff.

    ', status: done}
- {id: a2-p5-execution-analytics, content: '- [x] [AGENT] P0. Verify `/services/execution/overview` has real execution analytics content: fills breakdown by venue, fill rate, average slippage, venue latency chart, execution quality score. Wire to `GET /execution/fills` and `GET /execution/venues` APIs. This is the main landing tab for the Execution service.

    ', status: done}
- {id: a2-p5-execution-algos, content: '- [x] [AGENT] P1. Verify `/services/execution/algos` has: algo comparison table (TWAP, VWAP, IS, Sniper, Iceberg), performance metrics per algo, algo configuration. Wire to `GET /execution/algos` API. Clients with `execution-full` see advanced algo access; basic clients see read-only view.

    ', status: done}
- {id: a2-p5-execution-venues, content: '- [x] [AGENT] P0. Verify `/services/execution/venues` has: venue connectivity status, latency per venue, fill rates, uptime, supported instrument types. Wire to `GET /execution/venues` API.

    ', status: done}
- {id: a2-p5-execution-tca, content: '- [x] [AGENT] P1. Verify `/services/execution/tca` has: transaction cost analysis with slippage breakdown, benchmark comparison (arrival price, VWAP), implementation shortfall. Wire to API.

    ', status: done}
- {id: a2-p5-execution-remaining, content: '- [x] [AGENT] P1. Verify remaining execution tabs: `/services/execution/benchmarks` (benchmark definitions), `/services/execution/candidates` (execution strategy candidates for promotion), `/services/execution/handoff` (handoff from research to live execution).

    ', status: done}
- {id: a2-p6-tests, content: '- [x] [AGENT] P1. Add Playwright tests: 1) Navigate to Trading Terminal → verify chart renders, order book renders, order form visible. 2) Click "Manual Trade" → verify drawer opens with trade form. 3) Toggle batch mode → verify banner appears, data changes. 4) Navigate to Positions tab → verify table renders with data. 5) Navigate to Orders tab → verify table renders with data. 6) Navigate to Execute > Analytics → verify execution data renders. 7) Navigate to Execute > Venues → verify venue status renders.

    ', status: done}
- {id: a2-p6b-realtime-pnl-dashboard, content: "- [x] [AGENT] P0. Wire the Dashboard to receive real-time PnL updates from the WebSocket `analytics` channel. Agent 5 implements server-side PnL recalculation (a5-p4-realtime-pnl) — prices change → positions PnL recalculated server-side → strategy-level PnL aggregated → emitted on WebSocket. The UI just renders what it receives:\n  1. Dashboard subscribes to `analytics` WebSocket channel on mount\n  2. On `pnl_snapshot` message: update strategy performance cards with new PnL values\n  3. Equity curve charts append new data points in real-time (strategy-level cumulative PnL)\n  4. KPI cards (total AUM, total PnL, exposure) recalculate from the snapshot\n  5. NO client-side PnL computation — all numbers come from the WebSocket message\n  DEPENDENCY: Agent 5 a5-p4-realtime-pnl (server-side PnL recalculation and WebSocket emission).\n", status: done}
- {id: a2-p6b-realtime-positions, content: "- [x] [AGENT] P0. Wire the Positions table to receive real-time PnL updates from the WebSocket `positions` channel:\n  1. Positions page subscribes to `positions` WebSocket channel\n  2. On `pnl_update` message: update the positions table rows in-place (PnL column, current_price column)\n  3. Use React Query's `queryClient.setQueryData()` to merge WebSocket updates with cached data — no re-fetch needed\n  4. Add `<DataFreshness />` component showing \"Live\" with green dot when WebSocket is connected\n  This makes the Positions tab feel like a real Bloomberg blotter — PnL updating every tick.\n  DEPENDENCY: Agent 5 a5-p4-realtime-pnl. Agent 1 a1-p7-data-freshness (DataFreshness component).\n", status: done}
- {id: a2-p7-verify-charting-lib, content: "- [x] [AGENT] P0. VERIFIED: `components/trading/candlestick-chart.tsx` uses lightweight-charts v5.1.0 (by TradingView) with candlestick series + volume histogram. Confirm it:\n  1. Accepts OHLCV data arrays as props\n  2. Supports real-time updates (appending new candles from WebSocket via chart.update())\n  3. Supports interval switching (1m, 5m, 1h, 1d) — refetch candles on interval change\n  4. If missing any capability, add it — the library is already installed and configured\n", status: done}
- {id: a2-p7-technical-indicators, content: "- [x] [AGENT] P0. Add technical indicator overlays to the candlestick chart using lightweight-charts built-in `addLineSeries()`:\n  1. Install indicator computation: `npm install technicalindicators` (or compute SMA/EMA/BB from OHLCV data directly — they're trivial formulas)\n  2. Add indicator toolbar above chart: `[SMA] [EMA] [BB] [Vol]` toggle buttons\n  3. SMA: 20-period and 50-period moving averages as line overlays (different colors)\n  4. EMA: 12-period and 26-period as line overlays\n  5. Bollinger Bands: 20-period, 2 std dev — upper/lower as line series, fill between (lightweight-charts supports area between lines)\n  6. Volume bars already exist (histogram series) — just ensure toggle works\n  7. Each indicator toggles on/off via the toolbar buttons. State persisted in ui-prefs-store\n  8. Use `dynamic(() => import(...), { ssr: false })` for the chart + indicators (already needed for lightweight-charts)\n  DEPENDENCY: Agent 6 must seed\
    \ OHLCV candle data (200+ candles per instrument). Indicator computation needs enough data points.\n", status: done}
- {id: a2-p7-error-states-trading, content: "- [x] [AGENT] P1. Add error and empty states to ALL trading and execution pages:\n  1. Every page using useQuery: add `if (isError) return <ApiError error={error} onRetry={refetch} />` (component created by Agent 1)\n  2. Every table: add `if (data.length === 0) return <EmptyState title=\"No orders\" description=\"Place your first trade from the Terminal\" />`\n  3. Trading Terminal: if WebSocket fails to connect, show fallback with last known prices + \"Live feed unavailable\" badge\n  4. Manual Trade drawer: show toast on submission error with error message from API\n", status: done}
- {id: a2-p7-responsive-trading, content: "- [x] [AGENT] P1. Make Trading Terminal responsive:\n  1. Desktop (1280px+): chart + order book + order form side-by-side (current layout)\n  2. Tablet (768-1280px): chart full-width on top, order book + order form side-by-side below\n  3. Order book: use horizontal scroll on narrow screens\n  4. Positions/Orders tables: always wrap in `overflow-x-auto`\n  5. Dashboard cards: 4-col grid → 2-col on tablet → 1-col on mobile\n", status: done}
- {id: a2-p7-export-tables, content: "- [x] [AGENT] P1. Create shared export utility and wire to trading tables:\n  1. Install: `npm install xlsx` (SheetJS — client-side Excel generation)\n  2. Create `lib/utils/export.ts` with: `exportTableToCsv(data, columns, filename)` AND `exportTableToXlsx(data, columns, filename)` (Excel with bold headers, right-aligned numbers, formatted dates)\n  3. Add split \"Export\" button to Positions, Orders, and Fills tables: `[Export ▾]` → dropdown with \"CSV\" and \"Excel\" options\n  4. This utility is shared — Agents 3, 4, 7 use it for their tables\n  DEPENDENCY: None — can start immediately.\n", status: done}
- {id: a2-p7-adopt-datatable, content: "- [x] [AGENT] P0. Replace current shadcn `<Table>` with `DataTable` from `components/ui/data-table.tsx` (created by Agent 1) for ALL trading data tables:\n  1. Positions table → DataTable with sortable columns, column visibility toggle\n  2. Orders table → DataTable with sortable columns, status filter\n  3. Fills table → DataTable with sortable columns\n  4. Execution Analytics tables → DataTable\n  5. Instrument selector on Terminal → read ALL instruments from ui-reference-data.json (not hardcoded 10)\n  DEPENDENCY: Agent 1 must create DataTable component first (a1-p6-tanstack-table).\n", status: done}
- {id: a2-p7-full-instrument-selector, content: "- [x] [AGENT] P0. Update the Trading Terminal instrument selector to list ALL instruments from `ui-reference-data.json` (synced from UAC representative_sample.py). Currently hardcoded to ~10 crypto pairs. The selector should:\n  1. Read instruments from ui-reference-data.json `representative_instrument_sample` section\n  2. Group by category (CeFi Spot, CeFi Perps, TradFi, DeFi)\n  3. Support search/filter within the dropdown\n  4. On selection, update chart, order book, and WebSocket subscription\n  DEPENDENCY: Agent 8 must run sync pipeline to ensure ui-reference-data.json is current.\n", status: done}
- {id: a2-p8-pre-trade-compliance, content: "- [x] [AGENT] P0. Wire pre-trade compliance check into ManualTradingPanel. GAP CATEGORY: Type 2 (execution-service + risk-and-exposure-service have pre-trade checks — UI doesn't show them).\n  The REAL flow: execution-service `PreTradeRiskEngine.check_order()` validates position limits, order caps, staleness BEFORE routing to venue. risk-and-exposure-service `PreTradeCheckEngine` runs 6 checks (position/exposure/capital/leverage/VaR/stale-price).\n  Agent 5 adds `POST /compliance/pre-trade-check` to MockDomainService (a5-p8-pre-trade-check).\n  In ManualTradingPanel:\n  1. After user fills order form but BEFORE submission: call `POST /compliance/pre-trade-check` with { instrument, side, quantity, price, strategy_id }\n  2. Show compliance check panel BELOW the order form: list of checks, each with name + pass/fail badge + limit/current/proposed values\n  3. All checks pass: green summary \"Pre-trade checks passed\" + enable Submit button\n  4.\
    \ Any check fails: red summary \"Order rejected — {check_name} violated\" + DISABLE Submit button + show which limit was breached\n  5. This is the \"institutional workflow\" moment — demos that the system prevents rogue trades\n  DEPENDENCY: Agent 5 a5-p8-pre-trade-check endpoint. Agent 6 seeds risk_limits.\n", status: done}
- {id: a2-p8-options-chain, content: "- [x] [AGENT] P0. Add options chain view to Trading Terminal. GAP CATEGORY: Type 2 (features-volatility-service has full options pricing, UAC has CanonicalOptionsChainEntry schema — UI doesn't show it).\n  The REAL data comes from: features-volatility-service (Greeks computation), unified-api-contracts CanonicalOptionsChainEntry (schema), Deribit options chain config in representative_sample.py.\n  Agent 5 adds `GET /derivatives/options-chain?underlying=BTC&venue=deribit` (a5-p8-derivatives-endpoints).\n  1. Add \"Options\" tab or toggle on the Trading Terminal (alongside the candlestick chart area)\n  2. Options chain table: calls on left, puts on right, strikes in center column. Group by expiry.\n  3. Columns per side: bid, ask, last, IV, delta, gamma, theta, volume, OI\n  4. Color coding: ITM cells shaded, ATM row highlighted\n  5. Click a row to populate the order form with that strike/expiry\n  6. Underlying selector: BTC, ETH, SPY (from instruments\
    \ that have options in representative_sample.py)\n  7. Use `dynamic(() => import(...), { ssr: false })` — this is a heavy component\n  DEPENDENCY: Agent 5 a5-p8-derivatives-endpoints. Agent 6 seeds options_chain data.\n", status: done}
- {id: a2-p8-vol-surface-chart, content: "- [x] [AGENT] P1. Add volatility surface chart near the options chain. GAP CATEGORY: Type 2 (features-volatility-service computes full vol surfaces — UI doesn't visualize them).\n  Agent 5 adds `GET /derivatives/vol-surface?underlying=BTC` (a5-p8-derivatives-endpoints).\n  1. Vol surface visualization: either a 3D surface chart (strike x expiry x IV) or a 2D heatmap.\n  2. Simpler option: 2D line chart showing vol smile per expiry (x=strike, y=IV, one line per expiry bucket).\n  3. Term structure panel: x=expiry, y=ATM IV (shows contango/backwardation in vol).\n  4. Key metrics: ATM IV, 25-delta skew, butterfly spread — shown as text badges above chart.\n  5. Use `dynamic(() => import(...), { ssr: false })`.\n  DEPENDENCY: Agent 5 a5-p8-derivatives-endpoints. Agent 6 seeds vol_surfaces data.\n", status: done}
- {id: a2-p8-defi-health-factor, content: "- [x] [AGENT] P1. Add DeFi health factor column to Positions table. GAP CATEGORY: Type 2 (strategy-service RiskMonitor + risk-and-exposure-service DefiReconciliationChecker compute health factors — UI doesn't show them).\n  1. In the Positions DataTable, when position.venue is a DeFi protocol (AAVE_V3, COMPOUND_V3, etc.): show health_factor column\n  2. Color coding: >2.0 green, 1.5-2.0 yellow, <1.5 red\n  3. Show \"Liquidation distance\" badge: `(health_factor - 1.0) / health_factor * 100`%\n  4. For non-DeFi positions: column shows \"N/A\" or is hidden\n  5. Agent 6 seeds health_factor on DeFi position records\n  DEPENDENCY: Agent 6 seeds DeFi positions with health_factor field.\n", status: done}
isProject: false
---

# Notes & Context

## CRITICAL: Read Before Any Work

1. Read `unified-trading-system-ui/UI_STRUCTURE_MANIFEST.json` — SSOT for all page states, routes, and source files
2. Read `unified-trading-pm/plans/archive/CITADEL_VISION_2026_03_22.md` — system-wide vision

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

## Separation of Concerns (CRITICAL)

The Trading Terminal and Dashboard are the most data-intensive pages. Separation of concerns is paramount:

- **PnL calculation:** Server-side ONLY (Agent 5 MockDomainService). The UI renders received values.
- **Indicator computation (SMA, EMA, BB):** Client-side OK — this is presentation math on data already from the API.
- **Instrument list:** From `ui-reference-data.json` (synced from UAC), NOT hardcoded.
- **Strategy list:** From `GET /analytics/strategies`, NOT from `lib/trading-data.ts`.
- **Price ticks:** From WebSocket, NOT from client-side setInterval (no fallback tick generator in UI).

**The curl test applies here too:** `curl /positions/active` must return positions with correct PnL.
`curl /analytics/strategies` must return all 50+ strategies. If the API doesn't serve it, the UI can't render it — and
that's correct.

## Phase 8: Service-Capability Gaps (READ GAP_CLASSIFICATION_2026_03_22.md)

These are capabilities that EXIST in real services but the UI doesn't visualize:

- **Pre-trade compliance** — execution-service + risk-and-exposure-service run 6 pre-trade checks before order
  execution. You wire the ManualTradingPanel to show check results before submission.
- **Options chain** — features-volatility-service computes Greeks, UAC has full options schemas. You add an options
  chain view to the Trading Terminal.
- **Vol surface** — features-volatility-service computes vol surfaces. You add a visualization.
- **DeFi health factor** — strategy-service RiskMonitor computes Aave health factors. You add a column.

All data comes from Agent 5 Phase 8 endpoints. You do NOT implement pricing or risk logic — just render.

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

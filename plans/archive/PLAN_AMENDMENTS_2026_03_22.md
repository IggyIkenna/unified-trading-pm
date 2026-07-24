---
doc_type: plan
title: Plan Amendments — Gap-Closing for 90%+ Demo Alignment
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    execution-service,
    strategy-service,
    system-integration-tests,
    unified-trading-api,
    unified-trading-pm,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-22"
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Plan Amendments — Gap-Closing for 90%+ Demo Alignment

**Date:** 2026-03-22 **Context:** After reviewing the 8 agent plans + CITADEL_VISION against the actual codebase and an
independent audit, these amendments capture what is NOT in the current plans but IS required to reach 90%+
production-aligned mock demo.

**Core Principle:** The UI should NEVER do service logic. Everything demonstrable in the UI must also be achievable via
API/service calls (scripts, CLI, tests). The backend must be complete enough that the frontend is purely visual. No
client-side constants/fixtures — everything comes from the API, which comes from the service layer.

---

## Corrections to Original Gap Analysis

### Dark Mode — EXISTS (not a gap)

- `components/theme-provider.tsx` wraps `next-themes`
- `ui-prefs-store.ts` has `theme: "dark"` as the only supported theme
- All shadcn/ui components already use CSS variables with dark mode support
- **No work needed** — already dark-only. If light mode is ever desired, it's a future toggle.

### Strategy Expansion (50+) — Config, Not Code

The codex documents 13 code-complete strategies + 4 documented-only (market making variants):

- **CeFi**: momentum, mean-reversion, market-making
- **TradFi**: ML-directional, options-ML, options-market-making
- **DeFi**: basis-trade, staked-basis, recursive-staked-basis, AAVE-lending, AMM-LP
- **Sports**: arbitrage, value-betting, ML-sports, market-making

**Key insight from /codex/09-strategy/cross-cutting/config-architecture.md:** Strategies are config, not code. The
`EventDrivenStrategyEngine` is parameterised by subscription config. Expanding to 50+ strategies means:

1. Adding config entries (YAML/JSON) for new archetype x asset-class combinations
2. Seeding those configs into MockStateStore
3. Generating PnL/position/order data for each config

**This is NOT 10x the strategy-service work.** It's expanding the config registry + seed data. No new strategy engine
code paths needed — just new config permutations of existing archetypes.

### Instrument Coverage — Use Existing UAC Registry (Not Hardcoded 10)

`representative_sample.py` already has **50+ instrument specs** across:

- 7 CeFi spot (Binance, Coinbase, Bybit, OKX, Upbit)
- 6 CeFi perpetuals (Binance-Futures, Deribit, Hyperliquid, OKX, Bybit, Aster)
- 1 CeFi futures spec (Deribit BTC dated futures — generates multiple)
- 4 TradFi equities (AAPL, QQQ, GLD, VIX)
- 3 TradFi futures (ES, ZB, ZN)
- 18 DeFi instruments (Aave, Compound, Uniswap V2/V3/V4, Lido, EtherFi, Morpho, Curve, Ethena, Euler)
- 4 Sports instruments (Polymarket, Betfair, Pinnacle)
- Options chain config (generates Deribit BTC options dynamically)

**The plan should NOT hardcode 10 crypto instruments.** Agent 6 must programmatically import from
`representative_sample.py` and seed candles/tickers/orderbooks for ALL of them. The seed generator reads the registry;
if the registry expands, the seed expands automatically.

---

## New Amendments (Ordered by Impact on 90% Goal)

### Amendment 1: Seed Data Reads from UAC Registry Programmatically

**Affects:** Agent 6 (seed data), Agent 5 (API endpoints) **Replaces:** a6-p1c-ohlcv-candles hardcoded 10-instrument
list

**What:**

- `seed.py` imports `CEFI_SPOT_SPECS`, `CEFI_PERPETUAL_SPECS`, `TRADFI_EQUITY_SPECS`, `TRADFI_FUTURES_SPECS`,
  `DEFI_INSTRUMENT_SPECS`, `SPORTS_INSTRUMENT_SPECS` from `unified_api_contracts.registry.representative_sample`
- Candle generation iterates ALL specs, not a hardcoded list
- Ticker seeds cover ALL instruments
- Orderbook generation works for any instrument in the registry
- If a new instrument is added to UAC, the seed picks it up on next reset — no seed.py code change

**Why:** This is what "use what we have" means. We have 50+ instruments in UAC already. The seed generator just needs to
read them instead of hardcoding 10.

**Dependency:** UAC must be importable from unified-trading-api's venv. Check `pyproject.toml` deps.

---

### Amendment 2: Strategy Expansion via Config Registry, Not New Code

**Affects:** Agent 6 (seed data), Agent 5 (strategy config API endpoint) **New todos for Agent 6:**

**What:**

- Create `seed_strategies.py` that generates 50+ strategy configs by combining:
  - 13 documented archetypes from codex/09-strategy/
  - 5 asset classes from representative_sample.py (CeFi, TradFi, DeFi, Sports, Prediction)
  - Using the naming convention: `{ASSET}_{ARCHETYPE}_{MODE}` (e.g. `CEFI_MOMENTUM_LIVE_1H`)
- Each strategy config includes: archetype, asset_group, instruments[] (from UAC registry), execution_mode, timeframe,
  risk_limits, org_id
- PnL timeseries generated per-strategy (180 days) with archetype-appropriate characteristics:
  - Momentum: trending with sharp reversals
  - Mean-reversion: oscillating around baseline
  - Market-making: steady low-vol income with occasional spikes
  - DeFi yield: steady positive accrual with protocol-risk drawdowns
  - Sports: step-function PnL (bet resolves → discrete gain/loss)
- Positions and orders generated per-strategy referencing instruments from its config

**Why:** The strategy-service engine handles all archetypes via config. We're not adding new code paths — we're
expanding the config space and seeding data that matches it. The UI just needs more rows in the same tables.

**Key constraint:** Each strategy's instruments[] must reference instruments that exist in the UAC representative
sample. No invented instruments.

---

### Amendment 3: Real-Time PnL Propagation via WebSocket (Service-Layer, Not UI Logic)

**Affects:** Agent 5 (API/WebSocket), Agent 2 (UI wiring) **New todos:**

**What — Backend (Agent 5):**

- The WebSocket mock tick generator already updates `tickers_live` in MockStateStore
- ADD: On each tick batch, the mock service also recalculates `positions_live` PnL:
  - For each position where `instrument == tick.instrument`:
    `unrealized_pnl = (tick.price - position.entry_price) * position.quantity * side_multiplier`
  - Update `positions_live` collection in MockStateStore
  - Emit a `positions` channel WebSocket message: `{ channel: "positions", type: "pnl_update", data: { positions } }`
- ADD: Aggregate strategy-level PnL from updated positions:
  - Group positions by strategy_id, sum unrealized_pnl
  - Update `pnl_live` collection
  - Emit `analytics` channel message: `{ channel: "analytics", type: "pnl_snapshot", data: { strategies } }`

**What — Frontend (Agent 2):**

- Dashboard subscribes to `analytics` WebSocket channel
- Equity curves append new data points in real-time
- Strategy performance cards update PnL values on each snapshot
- Position table updates PnL column in real-time from `positions` channel

**Why:** This is the difference between a live terminal and a dead dashboard. Price ticks must flow through to PnL. The
calculation MUST happen server-side (in the mock service layer), not in the UI. The UI just renders what the WebSocket
tells it. This ensures the same logic works when the service is real.

**Separation of concerns:**

- Service layer: position PnL calculation (same code path mock and real)
- API: WebSocket emission
- UI: render received values

---

### Amendment 4: Technical Indicators on Candlestick Chart (Use lightweight-charts)

**Affects:** Agent 2 (Trading Terminal) **New todo for Agent 2:**

**What:**

- `lightweight-charts` v5.1.0 is already installed
- Add indicator computation in `lib/utils/indicators.ts`:
  - SMA(period): simple moving average from OHLCV close prices
  - EMA(period): exponential moving average
  - Bollinger Bands(period, stddev): upper/middle/lower bands
  - These are ~10 lines each — trivial math on the candle array
- Add indicator toolbar above chart: `[SMA 20] [SMA 50] [EMA 12] [BB] [Vol]` as toggle buttons
- Each enabled indicator adds a `LineSeries` overlay to the candlestick chart
- Persist toggle state in `ui-prefs-store.ts`

**Why:** This is purely visual (UI concern), but uses data that comes from the API (OHLCV candles). The indicator math
is presentation-layer — it's computed from the same candle data the chart already receives. No new API endpoints needed.

**Dependency:** Agent 6 must seed 200+ candles per instrument (already planned). Agent 5 must serve
`GET /market-data/candles` (already planned).

---

### Amendment 5: XLSX Export (Split Button CSV/Excel)

**Affects:** Agent 1 (creates utility), Agents 2-4, 7 (adopt) **New todo for Agent 1:**

**What:**

- Install `xlsx` (SheetJS) in unified-trading-system-ui
- Create `lib/utils/export.ts` with:
  - `exportTableToCsv(data, columns, filename)` — existing pattern
  - `exportTableToXlsx(data, columns, filename)` — new
  - `exportMultiSheetXlsx(sheets: {name, data, columns}[], filename)` — for Reports multi-sheet
- Every "Export CSV" button becomes a split button: `[Export ▾]` → dropdown: CSV | Excel
- Reports P&L: "Export" generates multi-sheet workbook (P&L on sheet 1, positions on sheet 2)

**Why:** Institutional clients expect Excel. CSV is fine for data engineers; portfolio managers use Excel. This is
UI-only — data comes from the API, export is a presentation concern.

---

### Amendment 6: Print-Optimized Reports

**Affects:** Agent 4 (Reports service) **New todo for Agent 4:**

**What:**

- Add `@media print` styles in `globals.css`:
  - Hide: navigation, debug footer, filters, buttons, command palette
  - Show: full-width tables with borders, charts at print resolution
  - Page breaks: `break-before: page` between report sections
  - Header: company logo + report title on each page
  - Footer: timestamp + page numbers
- Add "Print" button on Reports > P&L and Reports > Executive tabs (calls `window.print()`)

**Why:** Client reports must be printable. This is pure CSS (UI concern) — no backend changes.

---

### Amendment 7: LiveDomainService Wiring (Gateway → Mock-Mode Microservices)

**Affects:** Agent 5 (API service layer) **From other agent's audit — IMPORTANT architectural insight:**

**Current state:** `LiveDomainService` is entirely `NotImplementedError` stubs. The gateway mock path
(MockDomainService + MockStateStore) bypasses all microservice engines. This means the demo uses the right HTTP surface
and the right OpenAPI contract, but NOT the same service engines as production.

**What (Phase 2 — after mock demo is complete):**

- LiveDomainService methods should be thin HTTP clients to the actual microservices running in mock mode
- Example: `LiveDomainService.list("orders")` → `GET http://localhost:8004/execution/orders` (execution-service running
  with `CLOUD_MOCK_MODE=true`)
- This gives: same route handlers in the gateway + same engine logic in the services + mock data source

**Why:** The other agent correctly identified that the current architecture has TWO demo topologies:

1. Gateway mock (unified-trading-api MockStateStore) — fast, one process, but service engines never run
2. Fleet mock (each service in mock mode) — highest fidelity, but requires running multiple processes

For the immediate goal (demo for clients), Topology 1 is correct. But for system verification, Topology 2 is where "same
code paths as production" actually lives.

**Sequencing:** This is NOT required for the 90% demo. It IS required for "we can prove the real system works." Mark as
a follow-up phase after the 8-agent parallel execution.

**NOT in scope for current 8-agent execution — documented as Phase 9.**

---

### Amendment 8: Data Freshness Indicators

**Affects:** Agent 1 (creates component), all UI agents adopt **New todo for Agent 1:**

**What:**

- Create `components/ui/data-freshness.tsx`:
  - Shows "Updated Xs ago" or "Live" badge based on `lastUpdated` timestamp
  - Green: < 5s, Yellow: 5-30s, Red: > 30s or disconnected
- Render on every data panel header that uses real-time or recently-fetched data
- WebSocket-fed panels show "Live" with green dot
- REST-fetched panels show relative timestamp from last successful query

**Why:** Production trading systems always show staleness. In demo, this makes WebSocket-fed panels visually distinct
from batch data panels — reinforcing the batch/live story.

---

### Amendment 9: Demo Script & Scenarios

**Affects:** Documentation (no code), post-execution **New deliverable:**

**What:**

- Create `unified-trading-pm/docs/demo-script.md`:
  - 15-minute guided demo walkthrough for presenters
  - Covers: login → dashboard → terminal (live prices) → place trade → execution analytics → switch to batch → show
    reconciliation drift → switch persona to client → show restricted view → show reports → generate PDF → reset demo
  - Per-section: what to show, what to say, what button to click
- Create 2-3 named scenarios in seed data:
  - "Alpha Capital Drawdown": acme's momentum strategy had a 12% drawdown last week, triggered risk alert, ops
    acknowledged, strategy scaled down
  - "DeFi Yield Spike": Aave lending rate jumped, basis trade capitalized, reflected in PnL
  - "New Client Onboarding": vertex partners just onboarded, limited history, showing ramp-up

**Why:** The system is useless for demos without a script. Building the UI is necessary but not sufficient.

---

## Updated Dependency DAG

```
Phase 0 (PARALLEL — all start immediately):
  Agent 1: Shell & Navigation (UI)
  Agent 2: Trading Service (UI) — except WebSocket wiring (needs Agent 5)
  Agent 3: Research & Build (UI)
  Agent 4: Reports & Manage (UI)
  Agent 5: API Service Layer (unified-trading-api)
  Agent 6: Mock Data Quality (seed data) — Phase 0-1 run independently
  Agent 7: Observe & Admin (UI)

Phase 1 GATES:
  Agent 6 Phase 1 (strategy alignment, positions, orders) BLOCKED BY:
    - Nothing — uses existing seed.py + UAC imports
  Agent 6 Phase 1C (candles, tickers, timeseries) BLOCKED BY:
    - Nothing — generates from UAC representative_sample.py
  Agent 2 Phase 4B (WebSocket terminal) BLOCKED BY:
    - Agent 5: a5-p4-websocket (WebSocket tick generator verified)
    - Agent 6: a6-p1c-ohlcv-candles + a6-p1c-tickers-seed (data exists)
  Agent 2 NEW (real-time PnL) BLOCKED BY:
    - Agent 5: WebSocket + PnL recalculation in mock service layer
  Agent 6 Phase 2 (batch/live) BLOCKED BY:
    - Agent 5: a5-p2-use-utl-store (MockStateStore from UTL adopted)

Phase 2 GATES:
  Agent 6 Phase 4 (MSW removal + trading-data.ts migration) BLOCKED BY:
    - Agent 5: all routes return data
    - Agent 6: comprehensive seeds in place
    - Agent 1: debug footer done (Reset Demo wired to POST /admin/reset)
  Agent 8 Phase 2 (Playwright E2E) BLOCKED BY:
    - All agents Phase 0-1 substantially complete

Phase 3 (SEQUENTIAL):
  Agent 8: E2E Tests + SSOT Codegen Pipelines
  Integration Pass: Cross-agent contract verification

Phase 4 (POST-EXECUTION — documented, not in current sprint):
  LiveDomainService wiring to fleet-mock microservices
  Testnet slice for DeFi/CeFi adapter fidelity verification
```

---

## Separation of Concerns Checklist (Agents MUST Follow)

| Layer                                      | Responsibility                                         | NOT Responsible For                               |
| ------------------------------------------ | ------------------------------------------------------ | ------------------------------------------------- |
| **UAC Registry**                           | Instrument specs, venue capabilities, enums            | Seed data, API routes                             |
| **Service Engine** (strategy-service etc.) | Strategy logic, PnL calculation, risk                  | HTTP, WebSocket, UI rendering                     |
| **Mock Service Layer** (MockDomainService) | Same filtering/pagination as real, PnL recalc on ticks | UI components, client-side computation            |
| **API Routes** (unified-trading-api)       | HTTP surface, WebSocket emission, auth                 | Business logic (delegate to service)              |
| **UI**                                     | Visual rendering, chart overlays, export formatting    | Data generation, PnL calculation, filtering logic |

**Test:** If you can't demonstrate a feature by running a `curl` command against the API, the logic is in the wrong
layer. Move it to the service/API.

---

## What the Other Agent Audit Captured That We Should Keep

1. **MockStateStore pattern is correct** — JSONL persistence, seed + mutations, reset capability. Already the
   "institutional demo desk" pattern. No changes needed to the store itself.

2. **Gateway mock vs fleet mock topology** — Acknowledged as two valid topologies. Gateway mock (Topology 1) is the
   right choice for the demo sprint. Fleet mock (Topology 2) is Phase 9 follow-up.

3. **Testnet/paper execution** — UTEI/UDEI already encode testnet chain IDs. For DeFi/CeFi adapter fidelity, testnet
   execution is available but NOT required for the mock demo. It's a separate verification axis.

4. **`is_mock_mode()` seam is correct** — `UnifiedCloudConfig.is_mock_mode()` is the standard seam across all services.
   The gateway reads this and wires MockDomainService vs LiveDomainService. No architectural change needed.

5. **SIT defaults mock globally** — `system-integration-tests` sets `CLOUD_MOCK_MODE` by default. The workspace is
   designed to run full flows under mock without credentials.

**What we DON'T need from the other audit:**

- Fleet-mock topology wiring (Phase 9, not current sprint)
- Testnet execution demo (separate workstream, needs keys)
- Marks from public data feeds (nice-to-have, not 90% requirement)

---

## Summary: What Closes the Gap from Plans-As-Written to 90%

| #   | Amendment                                 | Impact                                | Agent             | Effort                                      |
| --- | ----------------------------------------- | ------------------------------------- | ----------------- | ------------------------------------------- |
| 1   | Seed reads UAC registry programmatically  | Instruments jump from 10 to 50+       | Agent 6           | Low (import change)                         |
| 2   | 50+ strategies via config expansion       | Strategy breadth across asset classes | Agent 6           | Medium (seed generation)                    |
| 3   | Real-time PnL via WebSocket (server-side) | Dashboard comes alive                 | Agent 5 + Agent 2 | Medium                                      |
| 4   | Technical indicators on chart             | Terminal looks professional           | Agent 2           | Low (trivial math + lightweight-charts API) |
| 5   | XLSX export (split button)                | Institutional export capability       | Agent 1 + all     | Low (SheetJS install + utility)             |
| 6   | Print-optimized reports                   | Client-distributable reports          | Agent 4           | Low (CSS only)                              |
| 7   | LiveDomainService wiring                  | System fidelity (Phase 9)             | Agent 5           | HIGH — deferred                             |
| 8   | Data freshness indicators                 | Production feel                       | Agent 1           | Low (small component)                       |
| 9   | Demo script & scenarios                   | Demo readiness                        | Documentation     | Low (no code)                               |

Amendments 1-6 and 8-9 are required for 90%. Amendment 7 is Phase 9 (post-sprint).

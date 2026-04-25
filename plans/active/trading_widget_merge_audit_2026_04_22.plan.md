---
title: "Trading Terminal — Widget Over-Extraction Audit & Merge Plan"
status: complete
priority: P1
created: 2026-04-22
owner: hk
scope: unified-trading-system-ui
---

# Trading Terminal — Widget Over-Extraction Audit & Merge Plan

## Why This Plan Exists

The UI was built originally as static pages. During the migration to the widget-grid architecture, some single-feature
flows were fragmented into N co-dependent widgets that each write a different slice of the same shared data-context and
only make sense when mounted together. A user moving/hiding one of them breaks the flow. Examples of the anti-pattern:

- `book` tab — 4 widgets (`book-order-form`, `book-algo-config`, `book-record-details`, `book-preview-compliance`) all
  write to `useBookTradeData()` and one single submit action; none works in isolation.
- `options` tab — `options-trade-panel` is a pure reader of `selectedInstrument` written by `options-chain`; it exists
  only to act on chain clicks.
- `bundles` tab — `bundle-templates` → `bundle-steps` → `bundle-pnl` → `bundle-actions` is one linear workflow split
  across 4 widgets where `bundle-actions` is literally just the Execute button.
- `terminal` tab — `instrument-bar` is a scope selector that drives `order-book`, `price-chart`, `order-entry`; already
  tracked as finding #4 in `live-review-findings.md`.

This plan classifies every widget across the 17 trading tabs and proposes concrete merges. The goal is to remove
co-dependent "half-widgets" without collapsing legitimately independent views (like list↔detail drilldowns, which are
explicitly OK to keep separate).

## Taxonomy Used

Every widget on every trading tab was classified against the write-surface of the tab's shared data-context (i.e., which
`setXxx` / `handleXxx` functions it actually calls).

| Type | Definition                                                                                                                     | Verdict                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| A    | Interdependent workflow partners — all widgets write to one shared workflow state and share a single submit. None works alone. | **Merge into one host widget.**                                                                                         |
| B    | Scope / selector (tab-wide) — widget only writes scope (org, account, instrument, date range). Every other widget reads it.    | **Fold into the primary consumer if it drives only one widget; keep as a dedicated scope bar if it drives 2+ widgets.** |
| C    | List ↔ detail (pure reader) — one widget writes `selectedXId`, the detail widget only reads it. Detail has no other purpose.  | **Keep separate** — canonical drilldown pattern, user explicitly approved.                                              |
| D    | Independent — owns own state, reads only scope.                                                                                | Keep as-is.                                                                                                             |

## Findings — Tab by Tab

Write-surface was extracted from each widget source file (all `set*` and `handle*` idents actually referenced). The
`Writes` column lists what the widget mutates in the tab's shared context.

### `book` — 6 widgets → **2** (or 3 if hierarchy-bar kept)

| Widget                    | Writes                                                                                          | Type |
| ------------------------- | ----------------------------------------------------------------------------------------------- | ---- |
| `book-order-form`         | executionMode, category, venue, instrument, side, qty, price, defiAlgo, slippage, handlePreview | A    |
| `book-algo-config`        | algo, algoParam                                                                                 | A    |
| `book-record-details`     | counterparty, sourceReference, fee (only shown in `record_only` mode)                           | A    |
| `book-preview-compliance` | handleSubmit, orderState (only renders when `orderState === "preview"`)                         | A    |
| `book-hierarchy-bar`      | orgId, clientId, strategyId                                                                     | B    |
| `book-trade-history`      | — (read-only)                                                                                   | D    |

**Merge proposal:** `book-order-entry` hosts all four Type-A widgets; UI state-machine by `orderState` — `idle` → form
body (with collapsible algo-config + record-details sections depending on mode); `preview` → summary grid + compliance
panel + Edit/Confirm.

### `options` — 9 widgets → **6**

| Widget                        | Writes                                                                                                                             | Type                         |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| `options-control-bar`         | assetClass, asset, tradFiAsset, settlement, market, tradFiMarket, pinnedCryptoAssets, pinnedTradFiAssets, activeTab, showWatchlist | B (drives 6+ widgets → keep) |
| `options-chain`               | selectedInstrument, selectedFuture                                                                                                 | host                         |
| `options-trade-panel`         | — (pure reader of `selectedInstrument`)                                                                                            | A → fold into chain          |
| `options-futures-table`       | selectedFuture, selectedInstrument                                                                                                 | host                         |
| `options-futures-trade-panel` | — (pure reader of `selectedFuture`)                                                                                                | A → fold into futures-table  |
| `options-strategies`          | strategiesMode, comboType, selectedInstrument                                                                                      | host                         |
| `options-scenario`            | — (reads assetClass/asset/legs, renders P&L surface of the strategy being built)                                                   | A → fold into strategies     |
| `options-watchlist`           | watchlistId, handleWatchlistSelect (writes `asset` through the handler)                                                            | D                            |
| `options-greek-surface`       | — (pure reader)                                                                                                                    | D                            |

### `bundles` — 5 widgets → **2**

| Widget               | Writes           | Type |
| -------------------- | ---------------- | ---- |
| `bundle-templates`   | setShowTemplates | A    |
| `bundle-steps`       | setShowTemplates | A    |
| `bundle-pnl`         | —                | A    |
| `bundle-actions`     | — (just Execute) | A    |
| `defi-atomic-bundle` | own state        | D    |

**Merge proposal:** `bundle-builder` — templates pane (collapsible/drawer), steps table, P&L estimate panel, actions
footer. `defi-atomic-bundle` stays independent.

### `terminal` — 6 widgets → **5**

| Widget             | Writes                                                                           | Type                      |
| ------------------ | -------------------------------------------------------------------------------- | ------------------------- |
| `instrument-bar`   | selectedInstrument, selectedAccount                                              | B → fold into order-entry |
| `order-entry`      | orderSide, orderSize, orderType, orderPrice, linkedStrategyId, handleSubmitOrder | host                      |
| `order-book`       | — (reads instrument)                                                             | D                         |
| `price-chart`      | chartType, timeframe (local)                                                     | D                         |
| `market-trades`    | tab (local)                                                                      | D                         |
| `terminal-options` | —                                                                                | D                         |

**Note:** already tracked as finding #4 in `docs/audits/live-review-findings.md`; blocked on the watchlist decision
(Option A shared vs Option B per-tab). This plan supersedes the instrument-bar entry when executed.

### `markets` — 8 widgets → no merge

| Widget                                                                                                  | Writes                                                                                     | Type                 |
| ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | -------------------- |
| `markets-controls`                                                                                      | assetClass, class, bookDepth, dataMode, dateRange, orderFlowRange, orderFlowView, viewMode | B (drives 6+) — keep |
| `markets-latency-summary`                                                                               | selectedLatencyService, latencyDataMode, latencyViewMode                                   | writes               |
| `markets-latency-detail`                                                                                | — (pure reader)                                                                            | C — keep             |
| `markets-order-flow` · `markets-live-book` · `markets-recon` · `markets-my-orders` · `markets-defi-amm` | scope readers                                                                              | D                    |

### `predictions` — 11 widgets → no merge

| Widget                                                                                                       | Writes                                      | Type                           |
| ------------------------------------------------------------------------------------------------------------ | ------------------------------------------- | ------------------------------ |
| `pred-markets-grid`                                                                                          | selectedMarketId, marketsFilters            | writes                         |
| `pred-market-detail`                                                                                         | — (reads selectedMarketId)                  | C — keep                       |
| `pred-trade-panel`                                                                                           | quickTradeMarketId + its own MarketSelector | D — self-sufficient (verified) |
| rest (portfolio-kpis, open/settled positions, arb-stream, arb-closed, ODUM focus, recent-fills, top-markets) | scope readers                               | D                              |

### `sports` — 9 widgets → no merge

| Widget                  | Writes                                    | Type     |
| ----------------------- | ----------------------------------------- | -------- |
| `sports-fixtures`       | selectedFixtureId, filters, handleViewArb | writes   |
| `sports-fixture-detail` | — (pure reader)                           | C — keep |
| `sports-arb`            | arbThreshold (local)                      | D        |
| rest                    | scope readers                             | D        |

### `instructions` — 3 widgets → no merge

| Widget                 | Writes             | Type     |
| ---------------------- | ------------------ | -------- |
| `instr-pipeline-table` | filters, selection | writes   |
| `instr-detail-panel`   | — (pure reader)    | C — keep |
| `instr-summary`        | —                  | D        |

### `accounts` — 6 widgets → no merge

| Widget                                                                                      | Writes                                                      | Type |
| ------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ---- |
| `accounts-transfer`                                                                         | 6 setters + 4 submit handlers (self-contained action panel) | D    |
| `accounts-transfer-history`                                                                 | statusFilter (log view)                                     | D    |
| `accounts-balance-table` · `accounts-margin-util` · `accounts-kpi-strip` · `saft-portfolio` | readers                                                     | D    |

Transfer submits then the history log updates independently — fine coupling.

### `overview`

| Widget          | Writes                        | Type                                          |
| --------------- | ----------------------------- | --------------------------------------------- |
| `scope-summary` | orgId, clientIds, strategyIds | B (drives every other overview widget) — keep |
| rest            | readers                       | D                                             |

### `pnl` · `orders` · `positions` · `alerts` · `risk` · `strategies` · `defi`

KPI-strip + table + charts pattern. No co-dependent workflow widgets. Each is a standalone view. **Exceptions to audit
further before final plan sign-off:**

- `defi-strategy-config` — sits in `defi-advanced`, `defi-walkthrough`, `defi-full` presets; may interact with the DeFi
  execution widgets (swap/lending/staking).
- `cefi-strategy-config` — in `strategies-full` preset next to the catalogue; may be a driver for the catalogue.

## Cross-Cutting Pattern — Scope Bars (Type B)

Every tab has one: `book-hierarchy-bar`, `markets-controls`, `options-control-bar`, `terminal/instrument-bar`,
`overview/scope-summary`. Visually they're all the same slim full-width strip.

**Decision rule (proposed):** a scope bar folds into its primary consumer **only when it drives exactly one workflow
widget**.

| Scope bar                 | # consumers                        | Fold?    | Into |
| ------------------------- | ---------------------------------- | -------- | ---- |
| `book-hierarchy-bar`      | 2 (order-entry + trade-history)    | **keep** | —    |
| `terminal/instrument-bar` | 3 (order-book, chart, order-entry) | **keep** | —    |
| `options-control-bar`     | 6+                                 | keep     | —    |
| `markets-controls`        | 6                                  | keep     | —    |
| `overview/scope-summary`  | 6+                                 | keep     | —    |

**Outcome:** scope bars stay as dedicated slots. Only clear one-consumer cases (none right now) would fold. This
resolves the instrument-bar question in finding #4: keep the bar, the issue is the widget's **content** (dead stub
buttons), not its existence.

## Work Units

Each work unit is a self-contained merge that can ship independently. Naming convention: `WU-<tab>-<short>`.

### WU-book-merge (P1 — user explicitly requested)

| Step | Action                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Rename `book-order-form-widget.tsx` → `book-order-entry-widget.tsx`; absorb algo-config, record-details, preview-compliance bodies keyed off `orderState` and `executionMode`.                                                                                                                                                                                                                                                                                                                      |
| 2    | Delete `book-algo-config-widget.tsx`, `book-record-details-widget.tsx`, `book-preview-compliance-widget.tsx`.                                                                                                                                                                                                                                                                                                                                                                                       |
| 3    | Update `register.ts`: drop 3 widget registrations; remove 3 preset rows; resize `book-order-entry` to absorb freed grid space (likely `w:6, h:~14` in `book-default`, `w:6, h:~14` in `book-full`).                                                                                                                                                                                                                                                                                                 |
| 4    | Archive cert JSONs (`book-algo-config.json`, `book-record-details.json`, `book-preview-compliance.json`) under `archive/docs/widget-certification/`.                                                                                                                                                                                                                                                                                                                                                |
| 5    | Scrub references: `components/widgets/book/book-widgets.md`, `README.md`, `docs/trading/WIDGET_CATALOGUE.md`, `docs/audits/bp2-audit-profile.json`, `docs/audits/BP2-base-widget-migration-spec.md`, `docs/audits/widget-classes/detail-panel-findings.md`, `components/widgets/pairing-guide.md`, `components/widgets/orders/orders-filter.md`, `components/widgets/orders/orders-table.md`, `docs/initial-boss/07_trading_target_state.md`, `docs/under-review/tasks/04-09-book-widget-merge.md`. |
| 6    | Playwright smoketest on `/services/trading/book` — execute mode, record-only mode, preview → submit flow.                                                                                                                                                                                                                                                                                                                                                                                           |
| 7    | Append status row to `docs/audits/live-review-findings.md` with file-level citations.                                                                                                                                                                                                                                                                                                                                                                                                               |

**Readiness:** C0 → C5 targeted. No backend changes. B6 (user sign-off) on visual result.

### WU-options-merge

Three sub-merges, all under one PR:

| Sub-merge                                               | Result                                                                                                         |
| ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `options-chain` + `options-trade-panel`                 | Trade-panel becomes a right-side drawer/pane inside the chain widget, hydrated off `selectedInstrument`.       |
| `options-futures-table` + `options-futures-trade-panel` | Trade-panel becomes a footer pane of the futures table.                                                        |
| `options-strategies` + `options-scenario`               | Scenario chart becomes the right panel of the strategy builder (visualizes whatever legs are currently built). |

Deletions: 3 widgets, 3 cert JSONs. Preset updates in `register.ts` for `options-default`, `options-strategies-preset`,
`options-full`.

### WU-bundles-merge

Fold `bundle-templates` + `bundle-steps` + `bundle-pnl` + `bundle-actions` into `bundle-builder`. Keep
`defi-atomic-bundle` independent. Presets (`bundles-default`, `bundles-compact`, `bundles-full`) collapse to 2 widgets
per layout.

### WU-shared-watchlist + terminal instrument-bar archive (was finding #4)

Supersedes finding #4 with user-confirmed Option A (shared watchlist component).

**Component:** `components/shared/watchlist/watchlist.tsx` — single presentation component with a
`WatchlistFilterConfig` discriminated union by `kind`: `"options"` (strike / DTE / IV), `"equities"` (sector /
market-cap), `"crypto"` (asset-type / venue), `"futures"`, etc. Each config renders its own filter-chip row over the
shared list UI.

**Adapters:**

- `components/widgets/options/options-watchlist-widget.tsx` → thin adapter over `<Watchlist>` reading `useOptionsData`.
  Keeps the existing `options-watchlist` `widgetId`.
- `components/widgets/terminal/terminal-watchlist-widget.tsx` (new) → thin adapter reading `useTerminalData`.

**Terminal instrument-bar:** archived to `archive/components/widgets/terminal/instrument-bar-widget.tsx`; cert JSON
archived. Account + linked-strategy selectors move into `order-entry-widget.tsx`. **Dropped behaviors
(user-confirmed):** live price, % change, LIVE/BATCH mode badge — the chart widget already shows price and order-entry
owns the price field. Dead-stub buttons (Refresh / Settings / Maximize from finding #4) deleted with the widget.

**Preset updates:** `terminal-default` and `terminal-full` in `components/widgets/terminal/register.ts` swap the
instrument-bar slot for a `terminal-watchlist` slot.

**Finding #4 closure:** once WU-4 lands, flip row #4 in `docs/audits/live-review-findings.md` to `[x]` with resolution
note — this is tracked as WU-5 below.

### WU-defi-strategy-config-audit — complete (Type D, no merge)

Audit performed inline during planning: `defi-strategy-config-widget.tsx` and `cefi-strategy-config-widget.tsx` both use
only local `useState`, save via API (`saveDefiStrategyConfig`, `deployDefiStrategy`). They do not share state with any
action widget. **Verdict: Type D, keep independent.** No work unit required.

## Sequencing

1. **WU-1 · book-merge** — user already queued; narrowest blast radius; reference implementation for the pattern.
2. **WU-2 · bundles-merge** — similar shape to book; smaller surface; validates the template-drawer pattern.
3. **WU-3 · options-merge** — largest surface (3 sub-merges); do after book + bundles prove the pattern.
4. **WU-4 · shared-watchlist + terminal instrument-bar archive** — can run in parallel with WU-3 (files don't overlap).
5. **WU-5 · close finding #4** — one-line housekeeping after WU-4 lands.

## Readiness Gates

All work units are UI-only, mock-backed. Typical gate path:

| Gate | Requirement                                                                                                                              |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| C1   | Widget code merged; registrations updated.                                                                                               |
| C2   | Unit tests (`book-page.test.tsx`, `options-page.test.tsx`, etc.) still pass; add new ones if the merged widget grows new state branches. |
| C3   | `tsc --noEmit` clean; ESLint clean.                                                                                                      |
| C4   | `NEXT_PUBLIC_MOCK_API=true pnpm build` succeeds.                                                                                         |
| C5   | Quickmerge.                                                                                                                              |
| B1   | Acceptance — no user-visible regression on the tab; preset layouts still load cleanly.                                                   |
| B6   | User manual walkthrough and sign-off.                                                                                                    |

No D-gates apply (UI-only).

## Confirmed Decisions (user sign-off 2026-04-22)

| #   | Topic                                     | Decision                                                                                                                                                                                          |
| --- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Scope bar fold rule                       | Keep all scope bars as dedicated slots (each drives 2+ consumers).                                                                                                                                |
| 2   | `bundle-actions`                          | Merge all 4 bundle widgets into one `bundle-builder`.                                                                                                                                             |
| 3   | Terminal instrument-bar                   | Archive. Shared `<Watchlist>` component (Option A) takes instrument selection. Account + linked-strategy move into `order-entry`. Live price / % change / LIVE–BATCH mode badge dropped entirely. |
| 4   | Watchlist shape                           | One shared component with per-tab `WatchlistFilterConfig` discriminated union; different filter chip rows per asset class.                                                                        |
| 5   | Strategy-config widgets (`defi` / `cefi`) | Audited inline — both use only local `useState`, save via API. Type D, no merge.                                                                                                                  |
| 6   | Audit scope                               | Trading only. Research / reports / custom / deployment = phase 2.                                                                                                                                 |
| 7   | Plan layout                               | Single SSOT plan at this file. No per-WU docs unless a WU balloons.                                                                                                                               |

## Out of Scope (phase 2)

- `services/research/*`, `services/reports/*`, `services/custom/*`, `services/deployment/*`.
- Per-strategy pages under `app/(platform)/services/trading/strategies/<family>/`.
- Adoption of `<Watchlist>` on sports / defi / predictions tabs (future WU once WU-4 pattern is stable).

## Changelog

- 2026-04-22 — plan drafted by agent from live audit of all 17 trading-tab `register.ts` files and every widget's
  data-context write surface. No code changes yet.
- 2026-04-22 — plan promoted to `active` after user sign-off on all 7 open questions; WU-terminal-instrument-bar
  rewritten as WU-4 shared-watchlist; WU-defi-strategy-config-audit closed inline as Type D no-op.
- 2026-04-22 — all 5 WUs shipped. WU-1 (book, 36382b7), WU-2 (bundles, 2ff874e), WU-3 (options, 9b1f964), WU-4+5
  (terminal watchlist + finding #4 close, dd2ec4b). Cert JSONs created for book-order-entry, bundle-builder,
  terminal-watchlist. Plan status → complete.

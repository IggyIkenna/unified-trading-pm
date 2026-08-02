---
title: "DeFi Demo UI Audit — Canonical Tables, Widget Consolidation, Mock Alignment"
status: active
priority: P1
created: 2026-03-31
owner: hk
---

# DeFi Demo UI Audit — Canonical Tables, Widget Consolidation, Mock Alignment

## Context

### What the UI Is

Unified multi-asset-class trading platform. One UI, one set of pages, one canonical table structure — CeFi, TradFi,
DeFi, Sports, Prediction Markets. Backend uses canonical IDs, canonical schemas, canonical field names. UI follows the
same model.

**Mock data only** — no live backend. Mock data in `lib/mocks/` derived from OpenAPI schemas. Many areas incomplete or
stale from fast development (~500 pages in a month).

### Demo Context — Patrick (Elysium)

Patrick's contracted requirement: **wallet balances, alerts, trade notifications** — thin monitoring layer over
automated DeFi strategies (AAVE_LENDING, BASIS_TRADE, STAKED_BASIS, RECURSIVE_STAKED_BASIS).

**Demo flow:** Login as Patrick (~20 min DeFi monitoring) → persona switch (~2 min platform tease for upsell).

### Priority Tiers

- **Tier 1 — Must be perfect:** Wallet/balance, Positions, Trade/transaction history, Alerts
- **Tier 2 — DeFi tease (polish, not flawless):** DeFi action widgets (lending, swap, staking, flash loans, rates,
  transfer), strategy config, rebalance
- **Tier 3 — 2-minute upsell:** CeFi terminal, ML backtesting, strategy research — no audit needed

---

## Core Architecture Principle: Canonical UI

### The Rule

Shared pages (Positions, Orders, Risk, P&L, Alerts, Reconciliation) use **one set of canonical column names** across ALL
asset classes. **Values** in columns adapt per asset class. **Column names and layout do NOT change.**

| Canonical Column | Value varies by asset class                                                            |
| ---------------- | -------------------------------------------------------------------------------------- |
| Instrument       | Formatted from canonical ID — `aUSDC (Aave V3)`, `BTC-USDT PERP`, `Man Utd vs Arsenal` |
| Side             | Value from data — `LONG`, `SHORT`, `SUPPLY`, `BORROW`, `BACK`, `LAY`, `YES`, `NO`      |
| Quantity         | Token amount, contract count, share count — same column                                |
| Entry Price      | Universal                                                                              |
| Current Price    | Universal                                                                              |
| Net P&L          | Universal. Drill-down shows asset-class-specific components                            |
| Today P&L        | Universal                                                                              |
| Venue            | Canonical venue ID formatted — `Aave V3`, `Binance`, `Betfair`                         |
| Strategy         | Strategy name — universal                                                              |
| Health           | HF for DeFi, margin ratio for CeFi, exposure for sports. `--` when N/A                 |
| Net Delta        | USD exposure. `--` when N/A                                                            |

**Do NOT:** rename columns per asset class, swap column sets, create separate DeFi/CeFi tables, hide columns per asset
class.

### Overview Metrics — Data-Driven

- **Always shown:** Total AUM, Total P&L, Position count, Alert count, Active strategy count
- **Conditional (shown if data contains relevant positions):** HF gauge (DeFi lending), Greeks summary (options), Match
  exposure (sports), Basis spread (basis strategies), Key rates strip (DeFi strategies active)

No "DeFi overview mode" — if Patrick only has DeFi data, he naturally sees DeFi metrics.

### Filter Behaviour for Client Users

**Current bug:** When Patrick logs in, org/client/strategy filters are completely hidden. Only "Elysium" badge shown.

**Fix needed:**

- Org = "Elysium" — auto-applied, read-only badge (already works)
- **Strategy filter = VISIBLE for client users** — dropdown showing Patrick's strategies, pre-set to "All" but
  filterable
- Positions page already has a per-page strategy filter (not gated by `isInternal()`) — so the fix is mainly in the
  global scope filters component

---

## Current State — DeFi Family Pages & Widgets

### Three DeFi Family Routes

Checked via code + live UI as Patrick. The DeFi family has three sub-tabs in the left nav:

| Route                            | Page Type                   | Provider            | Widgets/Content                                                                                                                             |
| -------------------------------- | --------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `/services/trading/defi`         | WidgetGrid                  | DeFiDataProvider    | 10 registered widgets (6 in default preset)                                                                                                 |
| `/services/trading/bundles`      | WidgetGrid                  | BundlesDataProvider | 5 widgets: Bundle Templates, Execution Steps, P&L Estimate, Bundle Actions, DeFi Atomic Bundles                                             |
| `/services/trading/defi/staking` | Standalone page (817 lines) | Inline mock data    | KPIs (Total Staked $4.2M, Yield 7.2%, Rewards $45K, Validators 12) + tabbed tables (Positions 8 rows, Validators, Rewards, Unstaking Queue) |

### DeFi Main Page Widgets (11 + 1 dialog + 1 provider)

| Widget            | File                              | Lines | Type               | In Default Preset    | Notes                                                                    |
| ----------------- | --------------------------------- | ----- | ------------------ | -------------------- | ------------------------------------------------------------------------ |
| Wallet Summary    | `defi-wallet-summary-widget.tsx`  | 187   | KPIs + chain table | Yes                  | Address, portfolio $, tokens, treasury status, net delta, rebalance      |
| DeFi Lending      | `defi-lending-widget.tsx`         | 228   | Action form        | Yes                  | Protocol selector, LEND/BORROW/WITHDRAW/REPAY, asset, amount, HF preview |
| DeFi Swap         | `defi-swap-widget.tsx`            | 236   | Action form        | Yes                  | Chain, token in/out, slippage, algo selector (SOR), route display        |
| DeFi Liquidity    | `defi-liquidity-widget.tsx`       | 184   | Action form        | No (advanced)        | Add/remove LP, pool selector, fee tier, price range                      |
| Staking           | `defi-staking-widget.tsx`         | 153   | Action form        | Yes                  | Stake/unstake, protocol (Lido, EtherFi, RocketPool), APY cards           |
| Flash Loans       | `defi-flash-loans-widget.tsx`     | 240   | Multi-step builder | No (advanced)        | Atomic bundle builder, P&L preview — **overlaps with Bundles page**      |
| Transfer & Bridge | `defi-transfer-widget.tsx`        | 344   | Action form        | Yes                  | Send/bridge tabs, chain/token selector, route list                       |
| Rates Overview    | `defi-rates-overview-widget.tsx`  | 113   | KPI + table        | Yes                  | Cross-protocol rate comparison. **Thin — merge candidate**               |
| Trade History     | `defi-trade-history-widget.tsx`   | 169   | KPI + table        | No (advanced)        | Instruction history, P&L per trade, running totals                       |
| Strategy Config   | `defi-strategy-config-widget.tsx` | 510   | Large form         | No (no preset)       | Per-strategy param config. Only widget not using DeFiDataProvider        |
| Rebalance Dialog  | `defi-rebalance-dialog.tsx`       | 115   | Modal dialog       | N/A (not registered) | Called from Wallet Summary                                               |
| DeFi Data Context | `defi-data-context.tsx`           | 298   | Provider           | N/A                  | Wraps all widgets with mock data + state                                 |

### Bundles Page Widgets (5 + 1 provider)

| Widget              | File                            | Type             | Notes                                                                                                     |
| ------------------- | ------------------------------- | ---------------- | --------------------------------------------------------------------------------------------------------- |
| Bundle Templates    | `bundle-templates-widget.tsx`   | Template gallery | Flash Loan Arb, Basis Trade, DeFi Deleverage, Options Spread, Sports Arb — **cross-asset, not DeFi-only** |
| Execution Steps     | `bundle-steps-widget.tsx`       | Leg builder      | Add legs, use templates, configure per-leg params                                                         |
| P&L Estimate        | `bundle-pnl-widget.tsx`         | P&L display      | Shows notional + net P&L once legs added                                                                  |
| Bundle Actions      | `bundle-actions-widget.tsx`     | Action panel     | Simulate and submit                                                                                       |
| DeFi Atomic Bundles | `defi-atomic-bundle-widget.tsx` | Template gallery | Pre-built DeFi bundles: Flash Loan Arb, Leverage Long, Yield Harvest                                      |

### Staking Standalone Page (817 lines)

`app/(platform)/services/trading/defi/staking/page.tsx` — full dashboard with inline mock data. Does NOT use
`DeFiStakingWidget` or `DeFiDataProvider`. Much richer than the staking widget: 8 positions across Lido, Rocket Pool,
Marinade, Osmosis, EigenLayer, Jito, plus Validators/Rewards/Unstaking tabs.

### Widget Presets (DeFi main page)

- **defi-default:** Wallet Summary, Lending, Swap, Staking, Rates Overview, Transfer
- **defi-advanced:** Wallet Summary, Flash Loans, Liquidity, Lending, Swap, Staking, Trade History

---

## Widget Consolidation Decisions

### Keep as Standalone (good size, distinct purpose)

| Widget                       | Reason                                                         |
| ---------------------------- | -------------------------------------------------------------- |
| Wallet Summary               | Core Tier 1 — portfolio health at a glance, rebalance trigger  |
| Lending                      | Distinct action (protocol + LEND/BORROW/WITHDRAW/REPAY flow)   |
| Swap                         | Distinct action (token pair + SOR + slippage + route)          |
| Transfer & Bridge            | Distinct action (send/bridge with route comparison)            |
| Trade History                | Core Tier 1 — instruction history + running P&L                |
| Strategy Config              | Large standalone form (510 lines), own data                    |
| Bundles page (all 5 widgets) | Cross-asset bundle builder — good as its own page, don't touch |

### Merge: Flash Loans Widget → Bundles Page

The Flash Loans widget (DeFi main page) and the Bundles page both build multi-step atomic bundles. The Bundles page is
richer (template gallery, leg builder, P&L estimate, DeFi Atomic Bundles widget). **Decision: remove Flash Loans from
the DeFi main page widget grid. The Bundles tab covers it.** For the demo, the Recursive Staked Basis demo flow (Flow 3)
uses the Bundles page, not the Flash Loans widget.

### Merge: Rates Overview → Into Wallet Summary

**Rates Overview is too thin (113 lines)** — it's just a KPI strip + small data table showing cross-protocol rates. This
data belongs in Wallet Summary as a collapsible section ("Key Rates") alongside the existing treasury/delta/chain table
sections. Removes one widget from the grid without losing information.

### Staking: Widget + Page — Both Stay, Different Purpose

The staking **widget** (153 lines) is a quick-action form: pick protocol, enter amount, stake/unstake. Good for the DeFi
main page grid.

The staking **standalone page** (817 lines) is a full dashboard: 8 positions, validators, rewards, unstaking queue. This
is what you show when you click "Staking" in the left nav for a deep dive.

**Decision: keep both.** The widget is the action interface, the page is the monitoring dashboard. BUT the standalone
page needs to be connected to `DeFiDataProvider` or at least shared mock data instead of inline mock arrays. That's a
post-demo cleanup task — for now, the inline data works.

### Liquidity Widget — Keep but Deprioritize

LP is a valid standalone action (add/remove liquidity, fee tier, price range). Keep in advanced preset. Not Tier 1 or
Tier 2 for Patrick's demo — his 4 strategies don't include LP market making.

### DeFi Main Page After Consolidation

**Default preset (after changes):**

Before: Wallet Summary, Lending, Swap, Staking, Rates Overview, Transfer (6 widgets) After: **Wallet Summary (with
rates), Lending, Swap, Staking, Transfer, Trade History** (6 widgets)

Changes: Rates Overview merged into Wallet Summary, Trade History added to default, Flash Loans removed (use Bundles
page instead).

### Full DeFi Family After Consolidation

| Tab             | What it provides                                                                                       | Demo relevance                       |
| --------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------ |
| **DeFi** (main) | Wallet Summary, Lending, Swap, Staking, Transfer, Trade History + advanced: Liquidity, Strategy Config | Tier 1 + Tier 2                      |
| **Bundles**     | Cross-asset bundle builder + DeFi Atomic Bundles templates                                             | Demo Flow 3 (Recursive Staked Basis) |
| **Staking**     | Full staking dashboard with positions, validators, rewards, unstaking                                  | Tier 2 deep dive                     |

---

## Mock Data Issues Found

### Problem 1: Two Parallel Strategy ID Systems

- `defi-risk.ts` uses canonical IDs: `AAVE_LENDING`, `BASIS_TRADE`, `STAKED_BASIS`, `RECURSIVE_STAKED_BASIS`
- `mock-data-seed.ts` uses slug IDs: `strat-defi-yield`, `strat-defi-atlas`

**Fix:** Align mock-data-seed positions/trades/alerts to use canonical strategy IDs from `lib/types/defi.ts`
(`DEFI_STRATEGY_IDS`). One source of truth.

### Problem 2: Display vs Canonical Venue Names

- `defi-risk.ts` / `defi-lending.ts`: canonical `AAVE_V3-ETHEREUM`, `UNISWAP_V3-ETHEREUM`
- `mock-data-seed.ts`: display `"Uniswap"`, `"Aave"`

**Fix:** All mock data uses canonical venue IDs. `formatVenueId()` handles display formatting (already exists as
`DEFI_VENUE_DISPLAY` map in `defi.config.ts`).

### Problem 3: Insufficient Mock Data Volume

| Data type                        | Current     | Needed for demo                                     |
| -------------------------------- | ----------- | --------------------------------------------------- |
| DeFi positions (mock-data-seed)  | 4 (generic) | 8-12 (per strategy, with HF/delta fields)           |
| DeFi trades (MOCK_TRADE_HISTORY) | 3           | 15+ (across all 4 strategies)                       |
| DeFi alerts (SEED_ALERTS)        | 1 generic   | 5+ (HF warning, basis spread, strategy pause, etc.) |
| Trade history running P&L        | Exists      | Verify it tells a coherent story                    |

### Problem 4: HF is a Constant, Not Per-Position

`DeFiDataProvider` sets `healthFactor: 1.85` as a constant. Positions in mock-data-seed don't have HF fields. Only
`defi-risk.ts` has per-strategy risk profiles.

**Fix:** Add `health_factor` and `net_delta` fields to DeFi position mock rows in mock-data-seed. Remove the constant
from data context.

### Problem 5: DeFi Alert Types Not Structured

Only 1 generic DeFi alert ("Aave health factor below 1.5") in seed data. No structured alert types like
`DEFI_HEALTH_FACTOR_CRITICAL`, `BASIS_SPREAD_COMPRESSED`, etc.

**Fix:** Add 5 structured DeFi alerts to seed data matching the types defined in the morning checklist:

- `alert-defi-001`: HF dropped to 1.18 — CRITICAL
- `alert-defi-002`: ETH funding negative on Hyperliquid — MEDIUM
- `alert-defi-003`: Treasury below minimum 8% — HIGH
- `alert-defi-004`: IL > fee income — MEDIUM
- `alert-defi-005`: weETH/ETH deviation 1.2% — HIGH

---

## Known Issues / Pre-Audit Findings

| Item                                         | Status       | Notes                                                                                           |
| -------------------------------------------- | ------------ | ----------------------------------------------------------------------------------------------- |
| Rebalance button hidden                      | ✅ Fixed     | `treasury.status: "high"`, button always visible                                                |
| DeFiRebalanceDialog never rendered           | ✅ Fixed     | Wired into wallet summary widget                                                                |
| HF threshold wrong (1.1 → 1.25)              | ✅ Fixed     | Amber now triggers at 1.25 not 1.1                                                              |
| Instrument IDs raw canonical                 | ✅ Fixed     | `formatInstrumentId()` added to positions table                                                 |
| Strategy filter hidden for clients           | ✅ Fixed     | `global-scope-filters.tsx` — org badge + **All Strategies** for client-scoped users             |
| "Upgrade to view trading data" in Quick View | ✅ Fixed     | `trading/layout.tsx` — `hasAnyEntitlement(["execution-basic"], …)` includes `execution-full`    |
| Two strategy ID systems in mock data         | ✅ Fixed     | `mock-data-seed.ts` DeFi rows use canonical strategy IDs + venues + instruments                 |
| Flash Loans widget overlaps Bundles page     | ✅ Done      | Removed from **advanced preset**; widget still in palette — use **Bundles** tab for flows       |
| Rates Overview too thin for standalone       | ✅ Done      | **Key Rates** merged into Wallet Summary; rates widget out of presets, still in palette         |
| Trade History not in default preset          | ✅ Done      | In `defi-default` + `defi-advanced` layouts — **re-apply Default preset** if workspace is stale |
| Strategy Config not in any preset            | ✅ Done      | In `defi-advanced` layout                                                                       |
| Staking page uses inline mock data           | ⚠️ Tech debt | Works for demo, connect to shared data post-demo                                                |
| Bundles page is cross-asset                  | ✅ Good      | Template gallery includes CeFi, Options, Sports — correct for canonical approach                |

---

## Audit Checklist

> **What `[ ]` means here:** these are **manual browser QA** steps (walk the demo as Patrick). They are **not** the same
> as **Status Tracking** at the bottom of this plan — implementation can be done while every box here stays `[ ]` until
> someone checks them off.
>
> **Already implemented in code** (still verify in UI): 1.6, Quick View for `execution-full`, expanded
> `MOCK_TRADE_HISTORY`, canonical DeFi seed rows, Key Rates inside Wallet Summary (expand the section — **default
> collapsed**), DeFi preset layouts including Trade History. If the DeFi grid looks unchanged, switch workspace to
> **Default** preset or **Reset Demo** — saved **My Workspace** overrides preset widget lists.

### PART 1: Login & Navigation

- [ ] **1.1** Login as Patrick — correct name/org in top bar and footer
- [ ] **1.2** Lifecycle tabs: only Data, Trading, Observe, Reports visible. Research, Promote, Manage hidden or disabled
- [ ] **1.3** Trading left nav: Overview, Terminal, Book, Orders, Positions, Alerts, Risk, P&L, Accounts, Instructions —
      all unlocked
- [ ] **1.4** Strategy Families: DeFi unlocked (DeFi, Bundles, Staking). Sports/Options/Predictions FOMO-locked
- [ ] **1.5** Strategies tab: FOMO-locked (padlock + upgrade CTA)
- [x] **1.6** Strategy filter visible in breadcrumb bar (or at least on positions page) — **implemented**
      (`global-scope-filters.tsx`); confirm in browser as Patrick

### PART 2: Tier 1 — Patrick's Contracted Scope

#### T1.1 Wallet / Balance Display

- [ ] Connected wallet address shown (truncated `0x7a23…abcd`)
- [ ] Portfolio USD value displayed (~$176.6K or realistic amount)
- [ ] Tracked token count shown
- [ ] Treasury status badge: HIGH when above target, with $700K / 35% shown
- [ ] Net Delta KPI visible (color-coded: amber if nonzero, green if ~0)
- [ ] Rebalance button visible and enabled when treasury = HIGH
- [ ] Clicking Rebalance opens DeFiRebalanceDialog with per-strategy allocations
- [ ] After confirm: treasury flips to normal, button disables
- [ ] **Key rates section** (merged from Rates Overview): expand **Key Rates** in Wallet Summary — lending APY, borrow,
      LP/stake rows visible (**implemented**, collapsed by default)

#### T1.2 Positions Table (Canonical)

- [ ] Navigate to `/services/trading/positions`
- [ ] All 4 strategy positions present in mock data
- [ ] Canonical column names: Instrument, Side, Quantity, Entry Price, Current Price, Today P&L, Net P&L, Health, Net
      Delta, Venue, Strategy
- [ ] Side column shows values from data: SUPPLY, BORROW, LONG, SHORT, STAKE — not renamed
- [ ] Instrument formatted for readability (not raw canonical IDs)
- [ ] HF column: green ≥1.5, amber 1.25–1.5, red <1.25, `--` for non-lending positions
- [ ] Net Delta populated for relevant positions, `--` for pure lending
- [ ] Venue column shows formatted canonical names (Aave V3, Hyperliquid)
- [ ] Strategy name visible per row
- [ ] P&L numbers realistic (not placeholder $0.00 or obviously fake)

#### T1.3 Trade / Transaction History

- [ ] DeFi Trade History widget loads in DeFi tab
- [ ] Summary KPIs: trade count, total gas, total slippage, net P&L
- [ ] Table columns canonical: Timestamp, Type, Instrument, Amount, Expected, Actual, Slippage, Gas, Net P&L, Running
      P&L, Status
- [ ] Type column shows values from data: TRANSFER, LEND, BORROW, SWAP, STAKE, FLASH_BORROW — same column
- [ ] Instrument IDs formatted for readability
- [ ] 15+ rows across all 4 strategies (not 2-3 placeholder rows) — **mock data expanded** in `defi-risk.ts`; confirm
      widget on layout
- [ ] Running P&L tells coherent story
- [ ] Status badges color-coded (filled/pending/failed)

#### T1.4 Alerts

- [ ] Navigate to Alerts tab
- [ ] 5+ DeFi-specific alerts present in mock data (HF warning, basis spread, treasury, IL, depeg)
- [ ] Severity badges color-coded (critical=red, high=orange, medium=yellow)
- [ ] Alerts coexist with CeFi alerts in same table (canonical approach)
- [ ] Filterable by strategy / severity

### PART 3: Tier 2 — DeFi Action Widgets

#### T2.1 Lending Widget

- [ ] Protocol selector shows Aave V3 (`AAVE_V3-ETHEREUM`), Morpho, Compound V3
- [ ] Operation buttons: LEND, BORROW, WITHDRAW, REPAY
- [ ] Asset selector with supply/borrow rates shown
- [ ] Amount input, slippage selector
- [ ] HF preview: Current 1.85, After: updates on input
- [ ] Execute button works (adds to trade history mock)

#### T2.2 Swap Widget

- [ ] Chain selector, token in/out dropdowns
- [ ] Price impact shown, gas estimate shown
- [ ] Slippage tolerance selector (0.1%, 0.5%, 1%)
- [ ] Algo selector: Smart Order Router (DEX) as default
- [ ] Route visualization (collapsible)
- [ ] Execute button works

#### T2.3 Staking Widget

- [ ] Protocols: Lido, EtherFi (weETH), RocketPool
- [ ] APY, TVL, min stake, unbonding period shown per protocol
- [ ] Stake/Unstake toggle
- [ ] Amount input with % quick buttons (25/50/75/100)

#### T2.4 Multi-leg / flash flows (Bundles page — not DeFi preset)

> **DeFi tab:** Flash Loans widget removed from **advanced preset** by design. Use **`/services/trading/bundles`** for
> template gallery + Execution Steps + DeFi Atomic Bundles.

- [ ] **Bundles** → Bundle Templates + DeFi Atomic Bundles show flash / multi-leg flows
- [ ] Execution Steps: add leg / use template; P&L Estimate updates
- [ ] Optional: add Flash Loans widget from **Add Widget** if you want it on DeFi grid again

#### T2.5 Transfer & Bridge Widget

- [ ] Send/Bridge tabs
- [ ] Chain selector, token selector, amount
- [ ] Bridge: route list with fees and estimated time
- [ ] Gas estimate shown

#### T2.6 Strategy Config Widget

- [ ] Strategy selector: all 4 demo strategies
- [ ] Per-strategy forms with correct parameters
- [ ] RECURSIVE_STAKED_BASIS shows "Demo Only" warning banner
- [ ] Save Config / Promote buttons show toast

#### T2.7 Bundles Page (`/services/trading/bundles`)

- [ ] Bundle Templates widget: 5 templates (Flash Loan Arb, Basis Trade, DeFi Deleverage, Options Spread, Sports Arb)
- [ ] Templates show correct instruction type badges and P&L estimates
- [ ] Execution Steps widget: "Add leg" and "Use a template" buttons work
- [ ] Clicking a template populates Execution Steps with correct legs
- [ ] P&L Estimate widget updates when legs are added
- [ ] DeFi Atomic Bundles widget: pre-built templates (Flash Loan Arb, Leverage Long, Yield Harvest) with gas estimates
- [ ] Can build Recursive Staked Basis 6-step bundle for demo Flow 3

#### T2.8 Staking Dashboard (`/services/trading/defi/staking`)

- [ ] Page loads with KPI cards: Total Staked, Annual Yield, Rewards Accrued, Active Validators
- [ ] Positions tab: 8 staking positions across protocols (Lido, Rocket Pool, Marinade, etc.)
- [ ] Table columns: Protocol, Token, Amount Staked, USD Value, APY, Rewards Earned, Lock Period
- [ ] Validators tab accessible
- [ ] Rewards tab accessible
- [ ] Unstaking Queue tab accessible
- [ ] Stake More / Unstake buttons per position
- [ ] Mock data shows realistic staking numbers

### PART 4: Shared Pages — Canonical Verification

#### S.1 Risk Page

- [ ] Universal risk metrics always shown
- [ ] HF gauge appears because Patrick has DeFi lending positions — data-driven
- [ ] DeFi Strategy Risk Profiles table visible (protocol, coin, basis, funding, liquidity risk)
- [ ] Delta exposure per strategy
- [ ] No "DeFi Risk" vs "CeFi Risk" mode switching — one page, data-driven sections

#### S.2 P&L Page

- [ ] Strategy-level P&L breakdown (4 rows for Patrick)
- [ ] P&L components: yield, funding, gas — because that's what's in the data
- [ ] Time filters: Today / 7D / 30D / All time
- [ ] Same table structure any user would see

#### S.3 Reconciliation

- [ ] Accessible for Patrick
- [ ] DeFi venues in filter: AAVE_V3-ETHEREUM, HYPERLIQUID, UNISWAP_V3-ETHEREUM, ETHENA-ETHEREUM
- [ ] 5 mock DeFi reconciliation records (DREC-001 through DREC-005)
- [ ] Accept / Reject / Investigate buttons update status

#### S.4 Book (Order Form)

- [ ] When DeFi venue selected: instruction type dropdown appears
- [ ] Types: SWAP, LEND, BORROW, REPAY, WITHDRAW, TRANSFER, TRADE, STAKE, UNSTAKE, FLASH_BORROW, FLASH_REPAY,
      ADD_LIQUIDITY, REMOVE_LIQUIDITY
- [ ] Algo dropdown filters by instruction type (SWAP → SOR_DEX, LEND → BENCHMARK_FILL)
- [ ] CeFi order form unchanged when non-DeFi venue selected

---

## UI Improvements to Consider

These are polish items — review after core audit, fix before demo if time allows.

| #   | Improvement                                                                         | Impact                                      | Effort |
| --- | ----------------------------------------------------------------------------------- | ------------------------------------------- | ------ |
| 1   | Treasury % gauge (visual bar: treasury vs deployed with target line)                | High — makes rebalance story visual         | Small  |
| 2   | Debt token visualization (debtWETH clearly red/negative, labeled "Borrowed")        | Medium — prevents confusion with perp short | Small  |
| 3   | Delta display in ETH terms (show both "$0" and "0 ETH" for DeFi)                    | Medium — basis traders think in ETH         | Small  |
| 4   | aToken interest indicator (show "+$13.15 today" alongside aUSDC balance)            | Medium — shows lending is working           | Small  |
| 5   | Flash loan atomicity indicator (bracket/group atomic bundle steps in trade history) | Low — nice for Recursive demo               | Medium |
| 6   | Gas cost prominence (show "est. cost incl. gas: $12" in every action form)          | Medium — DeFi-specific concern              | Small  |
| 7   | Funding rate per-venue display (current rate, annualized APY, next settlement)      | Low — nice for basis strategy detail        | Medium |
| 8   | Multi-venue basis weighting (per-venue allocation breakdown for basis trade)        | Low — nice for demo narrative               | Medium |

---

## Execution Steps

### Step 1 — Fix Client Filter Visibility

Fix `global-scope-filters.tsx` so strategy filter is visible for client users. Auto-apply org scope from persona.

### Step 2 — Mock Data Alignment

- Align strategy IDs in mock-data-seed to canonical (`AAVE_LENDING` not `strat-defi-yield`)
- Align venue names to canonical IDs
- Add HF + net_delta fields to DeFi position mock rows
- Add 5 structured DeFi alerts
- Expand trade history to 15+ rows across 4 strategies
- Remove HF constant from DeFiDataProvider

### Step 3 — Widget Consolidation

- Merge Rates Overview into Wallet Summary (add collapsible "Key Rates" section)
- Remove Flash Loans widget from DeFi default/advanced presets (Bundles page covers it)
- Add Trade History to default preset (Tier 1 — Patrick needs it)
- Add Strategy Config to advanced preset
- Update `register.ts` for DeFi presets
- Leave staking standalone page as-is (works for demo, connect to shared data post-demo)

### Step 4 — Parallel Audit (code + visual)

- Code audit: verify no column-switching logic in shared pages
- Visual audit: walk through Tier 1 then Tier 2 as Patrick via browser MCP
- Cross-reference findings

### Step 5 — Fix Demo-Blocking Items

- Tier 1 issues → fix immediately
- Tier 2 polish → fix if time allows
- UI improvements from the table above → cherry-pick highest impact/lowest effort

---

## Demo Day Flow Script

Pre-demo: app running, treasury status = "high" (35% > 20% target).

### Flow 1: AAVE Lending (~3 min)

1. DeFi → Wallet Summary: point to treasury $350K, treasury HIGH status
2. DeFi → Lending: select AAVE_V3-ETHEREUM, USDC, $100K, slippage → Execute
3. DeFi → Trade History: TRANSFER + LEND rows, P&L decomposition
4. Positions: aUSDC position appearing
5. P&L: mention interest accrues daily

### Flow 2: Basis Trade (~3 min)

1. Book → SWAP, SOR_DEX → USDC→ETH → Execute
2. Book → TRANSFER × 5 venues (Hyperliquid, Binance, OKX, Bybit, Aster)
3. Book → TRADE × 5 venues → SHORT ETH
4. Positions: ETH LONG + 5 SHORTs → net delta ≈ 0
5. P&L: funding income building

### Flow 3: Recursive Staked Basis (~4 min)

1. **Bundles page** (`/services/trading/bundles`): select DeFi Atomic Bundles → "Leverage Long" template (or build
   custom: FLASH_BORROW → SWAP → SWAP → LEND → BORROW → FLASH_REPAY)
2. Execution Steps: show 6 legs populated from template
3. P&L Estimate: gross/fee/gas/net
4. Execute → DeFi Trade History: 6 steps at same timestamp (atomic)
5. Positions: aweETH collateral + debtWETH + perp SHORT, HF = 1.375
6. DeFi → Strategy Config: recursive params (leverage 2.5x, hedged, MORPHO flash)
7. Risk: HF gauge

### Flow 4: Rebalance (~2 min)

1. Wallet Summary: treasury at 35%, Rebalance button enabled
2. Click → dialog shows per-strategy allocation
3. Confirm → treasury normalizes, button grays
4. Trade History: TRANSFER instructions appeared

### Flow 5: Reconciliation (~1 min)

1. Navigate to reconciliation
2. DeFi breaks in table
3. Click Accept on one → status updates

---

## Questions to Resolve

- [ ] **Reports tab**: should Patrick see it? Confirm visibility rule
- [ ] **AUM denomination**: USD or ETH for Patrick?
- [ ] **Recursive Staked Basis post-demo**: demo-only banner sufficient, or needs entitlement gate?
- [ ] **Rebalance mock flow**: should trade history auto-populate with TRANSFER instructions on confirm?
- [ ] **Timestamp timezone**: UTC or client local?

---

## Status Tracking

| Phase                                | Status     | Notes                                                                                                                                                                                                                                                               |
| ------------------------------------ | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Step 1: Fix client filter visibility | ✅ Done    | `global-scope-filters.tsx` — client sees org badge + **All Strategies** `CompactMultiSelect` scoped to `user.org.id`                                                                                                                                                |
| Step 2: Mock data alignment          | ✅ Done    | `mock-data-seed.ts` canonical strategy/venue/instruments; `defi-risk.ts` expanded trade history + HF helper; `defi-data-context` HF from `computeWeightedMockHealthFactor`; alerts `alert-defi-001`–`005` aligned                                                   |
| Step 3: Widget consolidation         | ✅ Done    | Key Rates merged into `defi-wallet-summary-widget.tsx`; `register.ts` presets: default = wallet + lend/swap/stake + transfer + **trade history**; advanced = + liquidity + **strategy config**; flash loans + rates removed from presets (widgets still registered) |
| Step 4: Code + visual audit          | ⏳ Partial | Repo grep verified; full browser walkthrough optional when dev server hot                                                                                                                                                                                           |
| Step 5: Fix demo-blocking items      | ⏳ Open    | Polish from “UI Improvements” table + reconcile any `strat-defi-*` doc references                                                                                                                                                                                   |

---

## Composer fast agents — how to re-run / extend

Use **one agent per independent slice**; **orchestrator** only merges, updates this plan’s Status Tracking, and
spot-checks.

| Agent ID | Scope                  | Repo path                                                                       | Done when                                                                             |
| -------- | ---------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **A**    | Client strategy filter | `components/platform/global-scope-filters.tsx`                                  | Patrick sees **All Strategies** next to Elysium; strategies filtered by `user.org.id` |
| **B**    | Quick View entitlement | `app/(platform)/services/trading/layout.tsx`                                    | `hasAnyEntitlement(["execution-basic"], …)` so `execution-full` unlocks Quick View    |
| **C**    | Seed canonical IDs     | `lib/mocks/fixtures/mock-data-seed.ts`                                          | DeFi rows use canonical strategy IDs + venue + instrument strings                     |
| **D**    | DeFi volume + HF       | `lib/mocks/fixtures/defi-risk.ts`, `defi-data-context.tsx`, `lib/types/defi.ts` | 15+ trade rows, structured alerts, HF not hardcoded constant                          |
| **E**    | Key Rates merge        | `defi-wallet-summary-widget.tsx`                                                | Collapsible **Key Rates** after portfolio-by-chain                                    |
| **F**    | Presets                | `components/widgets/defi/register.ts`                                           | Presets match table in Status Tracking above                                          |

**Prompt template** (prepend to every agent):

```
WORKSPACE_ROOT: /home/hk/unified-trading-system-repos
REPO: unified-trading-system-ui
Read unified-trading-pm/plans/ai/defi_ui_component_audit_2026_03_31.plan.md § Status Tracking + relevant section.
Follow UI .cursorrules: no new pages without approval; mock data in lib/mocks/fixtures only.
Return: files changed, 3-line summary, any tsc errors in touched files only.
```

**Do not** use `browser_wait_for` if it aborts — use `browser_snapshot` after navigate or refresh once.

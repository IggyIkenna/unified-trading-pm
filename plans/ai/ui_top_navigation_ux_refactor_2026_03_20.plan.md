# AI-GENERATED — awaiting user review and promotion

---
name: ui-top-navigation-ux-refactor
overview: Redesign the platform header to 2 clean rows — Row 1 is service-pipeline tabs + Org/Client/Strategy selectors, Row 2 is role-based contextual quick-nav — with FOMO locking for external users and conditional Live/As-Of
type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: none
  business: B1

repo_gates:
  - repo: unified-trading-system-ui
    code: C0
    deployment: none
    business: none

depends_on: []

todos:
  - id: phase-1a
    content: |
      - [ ] [AGENT] P0. Remove LifecycleRail from trading overview page
    status: todo
    note: "Delete import + render of LifecycleRail from app/(platform)/service/trading/overview/page.tsx lines 5 and 348. Eliminates the Design→Reconcile stepper from the trading terminal entirely."
  - id: phase-1b
    content: |
      - [ ] [AGENT] P0. Keep lifecycle stage labels but add role context to dropdown descriptions
    status: todo
    note: "In lib/lifecycle-mapping.ts: update lifecycleStages descriptions to reflect role alignment. Acquire→'Data acquisition & ETL pipelines (Data Science)', Build→'Features, ML models, strategies & backtesting (Quant)', Promote→'Multi-day strategy review & risk analysis (Trader + Risk)', Run→'Live trading, execution & account management (Trader)', Observe→'Risk monitoring, alerts, news & health (Risk/Ops)', Manage→'Clients, mandates, fees & onboarding (Back Office)', Report→'P&L, settlement, invoicing & regulatory (Executive)'. Keep short labels as-is for the tabs (Acquire/Build/etc are fine internally — dropdown descriptions explain the role context)."
  - id: phase-1c
    content: |
      - [ ] [AGENT] P0. Rename ambiguous 'Overview' tabs to descriptive names per service
    status: todo
    note: "In components/shell/service-tabs.tsx: TRADING_TABS[0] → 'Terminal', RESEARCH_TABS[0] → 'Research Hub', EXECUTION_TABS[0] → 'Analytics'. Keep DATA_TABS and REPORTS_TABS as-is."
  - id: phase-1d
    content: |
      - [ ] [AGENT] P0. Expand Row 2 tab definitions per service to cover all role-based sub-areas
    status: todo
    note: "Update service-tabs.tsx with richer tab sets: DATA_TABS → Pipeline Status, Coverage Matrix, Missing Data, Venue Health, ETL Logs. BUILD_TABS (new, for research) → Features, ML Models, Strategies, Backtests, Signals, Experiments. PROMOTE_TABS (new) → Review Queue, Execution Analysis, Risk Review, Approval Status. TRADING_TABS → Terminal, Positions, Orders, Execution Analytics, Accounts. MONITOR_TABS (new) → Risk Dashboard, Alerts, News, Strategy Health, System Health. MANAGE_TABS (new) → Clients, Mandates, Fees, Users, Compliance. REPORTS_TABS → P&L, Executive, Settlement, Reconciliation, Regulatory. Not all tabs need pages yet — stubs are fine."
  - id: phase-2a
    content: |
      - [ ] [AGENT] P1. Move Org/Client/Strategy selectors into Row 1 (right side, before user controls)
    status: todo
    note: "In lifecycle-nav.tsx: add compact Org/Client/Strategy selector group between the lifecycle tabs (left) and the search/bell/user controls (far right), with a clear visual divider. Use compact popover-based selectors (similar to current context-bar multi-selects). Internal users see all orgs/clients/strategies. External users see only their own org (read-only or hidden), their clients, their strategies."
  - id: phase-2b
    content: |
      - [ ] [AGENT] P1. Move Live/As-Of toggle to Row 2 with conditional visibility
    status: todo
    note: "Add Live/As-Of toggle to ServiceTabs row (right side). Only show it on tabs where it makes sense: Data (somewhat), Build (highly relevant — backtest comparison), Run (highly relevant — live vs historical), Monitor (relevant — compare alerts/features across dates). Hide on: Manage, Report, Promote. When in As-Of mode, show date picker inline."
  - id: phase-2c
    content: |
      - [ ] [AGENT] P1. Remove full-width ContextBar from trading pages
    status: todo
    note: "Remove <ContextBar> render from trading/overview/page.tsx (line 347). Org/Client/Strategy now lives in Row 1. Live/As-Of now lives in Row 2. The full ContextBar component is preserved for reuse but no longer rendered as a standalone full-width bar."
  - id: phase-2d
    content: |
      - [ ] [AGENT] P1. Lift filter state to service layout level
    status: todo
    note: "Move useContextState from individual pages to service layouts (e.g. service/trading/layout.tsx) via React context provider. Pages consume context via hook. Filter state persists when switching between Row 2 tabs within a service."
  - id: phase-3a
    content: |
      - [ ] [AGENT] P1. Implement FOMO locking for Row 1 tabs (external users)
    status: todo
    note: "Locked tabs stay visible with reduced opacity + 'Upgrade' badge (already partially implemented). On click, show upgrade modal/tooltip explaining what the service offers and how to subscribe. Key FOMO principle: external users see everything they CAN'T use every day. Never hide locked services — always show them greyed with upgrade CTA."
  - id: phase-3b
    content: |
      - [ ] [AGENT] P1. Implement FOMO locking for Row 2 tabs (external users)
    status: todo
    note: "Same FOMO locking on Row 2 tabs. Example: a data-only subscriber on the Build tab sees Features and ML Models locked with 'Upgrade to Research' badge. A trading-only subscriber on the Data tab sees ETL Logs and Coverage Matrix locked with 'Upgrade to Data' badge. More varied access at this level — some tabs might be accessible while others in the same service are locked."
  - id: phase-3c
    content: |
      - [ ] [AGENT] P1. Update mock persona data to properly demonstrate external user scoping
    status: todo
    note: "Update lib/mocks/fixtures/personas.ts and trading-data to: (1) Beta Fund (data-only) persona: single org, no client selector, most Row 1 tabs locked, only Data Row 2 tabs unlocked. (2) Alpha Capital (full suite) persona: single org, multiple clients/strategies visible, all tabs unlocked except Manage/Report. (3) Odum Internal: all orgs, all clients, all strategies, everything unlocked. Make the demo visually obvious when switching personas — the UI should dramatically narrow for limited subscriptions."
  - id: phase-4a
    content: |
      - [ ] [AGENT] P2. Visual hierarchy — differentiate Row 1 and Row 2 styling
    status: todo
    note: "Row 1 (LifecycleNav + selectors): solid bg-card, slightly taller (~42px), filled pill active state. Row 2 (ServiceTabs + Live/As-Of): lighter bg-card/50, slightly shorter (~36px), underline-only active state. Clear visual separation so they don't read as peers."
  - id: phase-4b
    content: |
      - [ ] [AGENT] P2. Move LifecycleRail into research/promote pages as in-page stepper
    status: todo
    note: "On Build and Promote pages, embed the lifecycle rail as a content-area stepper (inside the page body, not a full-width header bar). Shows strategy development progress: 'Feature Engineering → Model Training → Backtesting → Review → Promote'. Only appears when the user is actively in a multi-step workflow."
  - id: phase-4c
    content: |
      - [ ] [AGENT] P2. Add responsive overflow handling
    status: todo
    note: "Row 2 tabs: horizontal scroll with overflow indicators on narrow screens. Row 1 lifecycle items: already hides labels below lg breakpoint. Org/Client/Strategy selectors: collapse into single 'Scope' button on narrow screens."
  - id: phase-4d
    content: |
      - [ ] [AGENT] P2. Disable Buy/Sell buttons when no account selected
    status: todo
    note: "In the trading terminal order entry panel: grey out and disable Buy/Sell when prerequisites not met. Replace form area with clear empty state message + direct link to account selector."
  - id: phase-5a
    content: |
      - [ ] [HUMAN] P3. Review and approve final navigation model
    status: todo
    note: "User reviews the implemented 2-row model across all personas (internal, client-full, client-data-only). Confirms: (1) Row 1 tab labels and dropdown content make sense, (2) Org/Client/Strategy selectors work properly in Row 1, (3) Row 2 tabs are correctly role-based per service, (4) Live/As-Of appears only where relevant, (5) FOMO locking works for external users, (6) persona switching dramatically changes visible scope."
  - id: cleanup
    content: |
      - [ ] [AGENT] P3. Delete the three docs/ UX review documents
    status: todo
    note: "docs/NAVIGATION_UX_IMPROVEMENTS.md, docs/TOP_LAYOUT_NAVIGATION_UX_REVIEW.md, docs/TOP_LAYOUT_UX_REFACTOR_REPORT_2026_03_20.md — analysis docs superseded by this plan."

isProject: false
---

## Problem Statement

The trading terminal header stacks **5 horizontal bars** above the trading workspace, consuming ~200px (~22% of a 900px laptop viewport). Three different items glow green simultaneously across three different rows. Users must mentally decode three competing "where am I?" systems.

### Current state (5 bands)

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│ Row 1: LifecycleNav (shell)     Acquire │ Build │ Promote │ ●Run │ Observe │ …   │
├───────────────────────────────────────────────────────────────────────────────────┤
│ Row 2: ServiceTabs (layout)     ●Overview │ Positions │ Risk │ Alerts │ Markets   │
├───────────────────────────────────────────────────────────────────────────────────┤
│ Row 3: ContextBar (page)        Live │ As-Of │ All Orgs ▾ │ All Clients ▾ │ …    │
├───────────────────────────────────────────────────────────────────────────────────┤
│ Row 4: LifecycleRail (page)     Design ─ Simulate ─ Promote ─ Run ─ … ─ ●Recon  │
├───────────────────────────────────────────────────────────────────────────────────┤
│ Row 5: Instrument strip         BTC/USDT Binance │ Select Account │ $67,316      │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## Target State

### Target layout (2 navigation rows + instrument strip)

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│ ROW 1: Service Pipeline Tabs                   │ Scope Selectors  │ Utilities     │
│ [Logo] Acquire ▾ Build ▾ Promote ▾ ●Run ▾     │ All Orgs ▾ │     │ 🔍 🔔 [Org]  │
│        Observe ▾  Manage ▾  Report ▾           │ All Clients ▾│   │ [User]        │
│                                                │ All Strats ▾ │   │               │
│                                                │ ─── divider ──   │               │
├───────────────────────────────────────────────────────────────────────────────────┤
│ ROW 2: Role-Based Quick Nav (contextual)                          │ Live │ As-Of  │
│ Terminal │ Positions │ Orders │ Execution │ Accounts               │ (conditional) │
├───────────────────────────────────────────────────────────────────────────────────┤
│ Instrument strip: BTC/USDT Binance │ Select Account │ $67,316.587 +2.4%          │
├───────────────────────────────────────────────────────────────────────────────────┤
│ Trading workspace (order book, chart, order entry)                                │
└───────────────────────────────────────────────────────────────────────────────────┘
```

**Space saved:** ~110px recovered. Navigation drops from ~22% to ~10% of viewport.

---

## Row 1 — Service Pipeline Tabs + Org/Client/Strategy Selectors

### What Row 1 answers

"What service pipeline am I in?" + "What scope am I looking at?"

### Left side: 7 lifecycle stage tabs (with dropdown menus)

Each tab represents a distinct service pipeline aligned to a specific role:

| Tab | Role Alignment | Dropdown Items (examples) |
|-----|---------------|--------------------------|
| **Acquire** | Data Science / ETL | Data Pipeline, Venue Coverage, Missing Data, Instrument Registry |
| **Build** | Quant Developer | Feature Studio, ML Models, Strategy Lab, Backtesting, Signals |
| **Promote** | Trader + Risk Review | Review Queue, Execution Quality, Risk Analysis, Code Review, Approval |
| **Run** | Trader (live) | Trading Terminal, Execution Analytics, Order Management |
| **Observe** | Risk / Ops | Risk Dashboard, Alerts, News Monitor, Strategy Health, System Health |
| **Manage** | Back Office | Clients, Mandates, Allocations, Fees, User Management, Compliance |
| **Report** | Executive | P&L Reports, Executive Dashboard, Settlement, Reconciliation, Regulatory |

**Data context:** 5 asset classes (CEFI, DeFi, TradFi, Sports, Prediction Markets), 100+ venues, data in every size and form. The Acquire tab's dropdown and sub-pages must reflect this breadth.

### Centre-right: Org / Client / Strategy selectors

Positioned between the lifecycle tabs and the user controls, with a clear visual divider on each side.

| Selector | Internal user | External user (single org) |
|----------|--------------|---------------------------|
| **Organization** | Multi-select dropdown (all orgs) | Hidden or read-only (shows their org name) |
| **Client** | Multi-select (all clients across selected orgs) | Shows only their clients |
| **Strategy** | Multi-select (all strategies across selected clients) | Shows only their strategies |

These are compact popover-based selectors (reusing the multi-select logic from the existing `context-bar.tsx`). They are **global** — the selection persists across all tabs and pages.

### Far right: Utility controls

Search (Cmd+K), Notifications bell, Org switcher (persona switching for demo), User menu. Same as current.

---

## Row 2 — Role-Based Contextual Quick Nav

### What Row 2 answers

"What specific task/page am I on within this service?"

### Left side: Tab set changes per active Row 1 tab

| When Row 1 is… | Row 2 tabs |
|----------------|-----------|
| **Acquire** | Pipeline Status, Coverage Matrix, Missing Data, Venue Health, ETL Logs |
| **Build** | Features, ML Models, Strategies, Backtests, Signals, Experiments |
| **Promote** | Review Queue, Execution Analysis, Risk Review, Approval Status |
| **Run** | Terminal, Positions, Orders, Execution Analytics, Accounts |
| **Observe** | Risk Dashboard, Alerts, News, Strategy Health, System Health |
| **Manage** | Clients, Mandates, Fees, Users, Compliance |
| **Report** | P&L, Executive, Settlement, Reconciliation, Regulatory |

### Right side: Live / As-Of toggle (conditional)

| Row 1 tab | Show Live/As-Of? | Why |
|-----------|-----------------|-----|
| **Acquire** | Yes (somewhat) | Compare pipeline state at a point-in-time vs now |
| **Build** | Yes (highly relevant) | Compare backtested strategy on yesterday's data vs live trader results — ideally identical, reality has minor diffs |
| **Promote** | No | Review is current-state |
| **Run** | Yes (highly relevant) | Compare historical execution vs live; yesterday's strategy behaviour vs today |
| **Observe** | Yes (relevant) | Compare alerts between yesterday and today; feature presence for a strategy on a particular date vs now |
| **Manage** | No | Client/fee management is inherently current |
| **Report** | No | Reports are date-ranged by nature, not live/as-of toggled |

When hidden, the space is just empty (Row 2 is shorter). When in As-Of mode, a date picker appears inline.

---

## FOMO Locking Strategy (External Users)

### Core principle

**Never hide locked services. Always show them greyed out with an upgrade CTA.** The user sees what they're missing every single day. This creates FOMO (fear of missing out) that drives subscription upgrades.

### Row 1 FOMO locking

| External subscription | Unlocked Row 1 tabs | Locked (visible, greyed, with "Upgrade" badge) |
|----------------------|--------------------|-------------------------------------------------|
| **Data Only** | Acquire | Build, Promote, Run, Observe (Manage/Report hidden — internal only) |
| **Data + Research** | Acquire, Build | Promote, Run, Observe |
| **Execution Only** | Run, Observe | Acquire, Build, Promote |
| **Full Suite** | Acquire, Build, Promote, Run, Observe, Report | (none locked) |

Manage is always hidden from external users (internal back-office only).

### Row 2 FOMO locking (more granular)

Within each Row 1 tab, individual Row 2 tabs can be independently locked:

**Example — Data Only subscriber clicks "Build" (locked in Row 1):**
- They see the Build Row 2 tabs all locked: Features (locked), ML Models (locked), Strategies (locked)...
- Each shows "Upgrade to Research tier" badge
- Clicking opens an upgrade modal explaining what they'd get

**Example — Execution Only subscriber clicks "Acquire" (locked in Row 1):**
- They see Data Row 2 tabs locked: Pipeline Status (locked), Coverage Matrix (locked)...
- Each shows "Upgrade to Data tier" badge

**Example — Full Suite client on "Run" tab:**
- All Row 2 tabs unlocked: Terminal, Positions, Orders, Execution Analytics, Accounts
- But data is scoped to their org only

---

## Audience Scoping Matrix

| Component | Internal | External (full suite) | External (data only) | External (execution only) |
|-----------|---------|----------------------|---------------------|--------------------------|
| **Row 1 tabs** | All 7 visible, all unlocked | 5 visible (no Manage), most unlocked | 5 visible, only Acquire unlocked | 5 visible, only Run + Observe unlocked |
| **Row 2 tabs** | All unlocked per service | All unlocked for subscribed services | Data tabs unlocked, rest locked | Run/Observe tabs unlocked, rest locked |
| **Org selector** | Multi-select, all orgs | Hidden (single org) | Hidden (single org) | Hidden (single org) |
| **Client selector** | All clients | Only their clients | Only their clients | Only their clients |
| **Strategy selector** | All strategies | Only their strategies | N/A (no strategy access) | Only their strategies |
| **Live/As-Of** | Always available (where relevant) | Available where relevant | Available on Data tabs | Available on Run/Observe |
| **Locked items** | None | FOMO badges on unsubscribed | FOMO badges on everything except Data | FOMO badges on everything except Run/Observe |

---

## Phased Execution

### Phase 1 — Instant wins (P0, ~15 min, zero risk)

**Tasks: 1a, 1b, 1c, 1d** — can all be done in parallel.

String changes, line deletions, and tab definition expansion. No structural refactoring.

| Task | What changes | Files touched |
|------|-------------|---------------|
| 1a | Delete LifecycleRail import + render from trading page | `app/(platform)/service/trading/overview/page.tsx` |
| 1b | Update lifecycle stage descriptions to reflect role alignment | `lib/lifecycle-mapping.ts` |
| 1c | Rename "Overview" tab labels per service | `components/shell/service-tabs.tsx` |
| 1d | Expand Row 2 tab definitions for all 7 services | `components/shell/service-tabs.tsx` |

**QG gate:** `npm run build` must pass. Visual check — 4 rows instead of 5, more tabs per service.

### Phase 2 — Core structural refactor (P1, ~60 min)

**Tasks: 2a → 2b → 2c → 2d** — sequential.

| Task | What changes | Files touched |
|------|-------------|---------------|
| 2a | Move Org/Client/Strategy selectors into Row 1 right side | `components/shell/lifecycle-nav.tsx` |
| 2b | Move Live/As-Of toggle to Row 2 with conditional visibility | `components/shell/service-tabs.tsx` |
| 2c | Remove full-width ContextBar from trading pages | `app/(platform)/service/trading/overview/page.tsx` |
| 2d | Lift filter state to service layout level via context provider | `app/(platform)/service/trading/layout.tsx` + new provider |

**QG gate:** `npm run build` passes. Org/Client/Strategy works in Row 1. Live/As-Of appears conditionally in Row 2. No more full-width ContextBar.

### Phase 3 — FOMO locking + persona scoping (P1, ~45 min)

**Tasks: 3a, 3b, 3c** — can be done in parallel.

| Task | What changes | Files touched |
|------|-------------|---------------|
| 3a | FOMO locking for Row 1 tabs (greyed + Upgrade badge for external) | `components/shell/lifecycle-nav.tsx` |
| 3b | FOMO locking for Row 2 tabs (per-tab entitlement gating) | `components/shell/service-tabs.tsx` |
| 3c | Update mock persona data to demonstrate scoping visually | `lib/mocks/fixtures/personas.ts`, `lib/trading-data.ts` |

**QG gate:** Switch personas in the UI. Beta Fund (data-only) should show dramatically narrowed scope. Alpha Capital (full) should show mostly unlocked. Internal shows everything.

### Phase 4 — Polish (P2, ~30 min)

**Tasks: 4a, 4b, 4c, 4d** — can be done in parallel.

| Task | What changes | Files touched |
|------|-------------|---------------|
| 4a | Visual hierarchy — differentiate Row 1 and Row 2 styling | `lifecycle-nav.tsx`, `service-tabs.tsx` |
| 4b | Move LifecycleRail to research/promote pages as in-page stepper | `app/(platform)/service/research/` pages |
| 4c | Responsive overflow handling for both rows | `service-tabs.tsx`, `lifecycle-nav.tsx` |
| 4d | Disable Buy/Sell when no account selected | Trading overview page |

### Phase 5 — Review (P3)

**Tasks: 5a, cleanup** — human review, then cleanup.

---

## Pre-Audit Manifest

### Files that render ContextBar as full-width bar (remove in Phase 2c)

| File | Line | Renders |
|------|------|---------|
| `app/(platform)/service/trading/overview/page.tsx` | 347 | `<ContextBar context={context} onContextChange={setContext} />` |

### Files that render LifecycleRail (remove in Phase 1a)

| File | Line | Renders |
|------|------|---------|
| `app/(platform)/service/trading/overview/page.tsx` | 348 | `<LifecycleRail activePhase={lifecyclePhase} onPhaseChange={setLifecyclePhase} />` |

### Files with lifecycle stage metadata (update in Phase 1b)

| File | Section |
|------|---------|
| `lib/lifecycle-mapping.ts` | `lifecycleStages` record — update descriptions, keep short labels |

### Files with tab definitions (expand in Phase 1c/1d)

| File | Section |
|------|---------|
| `components/shell/service-tabs.tsx` | All `*_TABS` arrays — rename first tabs, add new tab sets for Build/Promote/Monitor/Manage |

### Components preserved (not deleted)

| Component | Why kept |
|-----------|---------|
| `components/trading/context-bar.tsx` | Multi-select logic reused for Row 1 Org/Client/Strategy selectors |
| `components/trading/lifecycle-rail.tsx` | Reused as in-page stepper on Build/Promote pages |
| `components/platform/context-bar.tsx` | Research/ML platform context bar — separate concern |

---

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Two rows, not one | Complex multi-asset platform needs two navigation levels; one row would require mega-menus; two rows is institutional standard (Bloomberg, Refinitiv) |
| Keep Acquire/Build/Promote/Run/Observe/Manage/Report labels | These map to the actual service pipelines and internal roles; dropdown descriptions explain the role context; product-name aliases (Data, Research, Trading) can go in dropdowns |
| Org/Client/Strategy in Row 1, not a separate bar | These are global scope — they should be set once and persist everywhere. Row 1 is the right place because it's the persistent global chrome. Eliminates one full-width bar. |
| Live/As-Of in Row 2, conditional | Context-dependent: highly relevant for trading/research (compare backtest vs live), irrelevant for reports/management. Showing it always would be noise on tabs where it makes no sense. |
| FOMO locking (show locked, never hide) | External users see what they're missing every day. Creates subscription upgrade pressure. Hiding services means clients don't even know they exist. |
| Row 2 tabs are role-based + more granular locking | Row 1 is service-level access. Row 2 is feature-level access within a service. External users can have partial access (e.g., some trading features but not all). This is more nuanced than the current all-or-nothing model. |
| LifecycleRail removed from trading, kept for research | Stepper adds value for multi-step workflows (feature engineering → model training → backtesting → review). Zero value on a live trading terminal where the user needs speed, not process tracking. |

---

## Branch History Context

| Branch | Navigation model | Key issues |
|--------|-----------------|------------|
| `merge/combined-best-of-both` | GlobalNavBar (flat links: Overview, Trading, Strategies, ML...) + ContextBar + LifecycleRail, all rendered in the page. Shell had separate LifecycleNav + LaneIndicator. | Two completely different nav systems (GlobalNavBar vs LifecycleNav) coexisting. Up to 5+ bars on trading page. No service-tab concept. |
| `feat/service-centric-navigation` (current) | LifecycleNav in shell + ServiceTabs in layouts + ContextBar + LifecycleRail still in page. No GlobalNavBar on new /service/ routes. | Cleaned shell, added service tabs, but pages still render 2 extra bars (ContextBar + LifecycleRail). Still 5 bands total. Entitlement locking partially implemented. |
| **This plan (target)** | Row 1: LifecycleNav + Org/Client/Strategy selectors. Row 2: expanded role-based ServiceTabs + conditional Live/As-Of. No ContextBar bar. No LifecycleRail on trading. FOMO locking on both rows for external users. | 2 clean rows + instrument strip. ~110px saved. Each row answers one question. Persona switching dramatically changes scope. |

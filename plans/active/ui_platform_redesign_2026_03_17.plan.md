# Unified Trading Platform — UI/UX Redesign Vision

**Plan:** ui-platform-redesign-2026-03-17 **Type:** Architecture + Design + Code **Status:** Draft (Design Phase)
**Supersedes:** opus_findings_ui, ui_consolidation_ux_hardening, ui_navigation_ux_model **Depends on:**
unified-trading-ui-kit (shared component library)

---

## The Problem

11 UIs built in isolation. Each grew its own deployments tab, its own P&L view, its own alerts page. The result is a
system where:

- A user cannot answer "what is happening right now?" without visiting 4+ ports
- P&L lives in 3 different UIs with no canonical home
- strategy-ui and execution-analytics-ui are 90% identical
- batch-audit-ui and logs-dashboard-ui hit the same API
- There is zero cross-UI navigation — users type port numbers manually
- No workflow coherence: the lifecycle from Design → Simulate → Promote → Run → Monitor → Explain → Reconcile is
  invisible
- No entity hierarchy: Fund → Client → Strategy → Config → Run → Position is never navigable

This is not a cosmetic problem. It's an information architecture failure.

---

## Design Philosophy

### What Citadel Gets Right

At Citadel and Renaissance, the internal platforms share one trait: **complexity is organized, never hidden**. Every
trader can see everything — positions, risk, P&L attribution, execution quality, feature freshness — but the system
surfaces the right thing at the right time through hierarchy and workflow, not by scattering it across disconnected
tools.

### Three Design Principles

**1. Entity-First Navigation** Every screen has one primary entity. Users navigate a hierarchy — Fund → Client →
Strategy → Config Version → Run — and at each level, switch lenses (positions, orders, fills, P&L, recon, timeline). The
entity is the anchor; the lens is the view.

**2. Lifecycle-Aware Flow** The platform embeds the operating lifecycle — Design → Simulate → Promote → Run → Monitor →
Explain → Reconcile — not as decoration but as wayfinding. A user always knows where they are in the lifecycle, and the
UI naturally guides them to the next step.

**3. One Screen, One Verb, One Time Horizon** Each view has a dominant verb (define, compare, promote, observe,
intervene, explain, resolve) and a time horizon (design-time, historical batch, live now, post-trade). Mixing these
creates confusion. Separating them creates clarity.

**4. Risk Attribution Mirrors P&L Attribution** If P&L breaks down into delta, funding, basis, interest, greeks, MTM —
then exposure/risk should show the CURRENT RISK in those same dimensions. They are two sides of the same coin: what
happened (P&L) and what could happen (exposure). The command center shows both side-by-side.

**5. Canonical Ownership — No Overlap, No Drift**

Every surface owns exactly one time horizon and one dominant verb. If a concept appears in two surfaces, the tie-breaker
is: **which verb and time horizon does the user have when they need this?**

| Surface                    | Owns                   | Time Horizon             | Dominant Verbs                     | Canonical Data                                                                                   |
| -------------------------- | ---------------------- | ------------------------ | ---------------------------------- | ------------------------------------------------------------------------------------------------ |
| **Trading Command Center** | Live now               | Real-time                | OBSERVE, INTERVENE                 | Live positions, live risk/exposure, margin health, LTV, feature freshness, alerts, kill switches |
| **Strategy Analytics**     | Design & simulation    | Historical / design-time | DESIGN, SIMULATE, COMPARE, PROMOTE | Strategy catalogue, backtest results, config grids, tick data, instruments, promotion flow       |
| **Market Intelligence**    | Post-trade explanation | T+0 to T+n retrospective | EXPLAIN, RECONCILE                 | P&L attribution (6D), recon, latency analysis, order book, trade desk, reports                   |
| **Operations Hub**         | Infrastructure         | Deployment/ops time      | DEPLOY, DIAGNOSE                   | Services, deployments, batch jobs, logs, events, compliance, CI/CD, data health                  |
| **Config & Onboarding**    | Controlled CRUD        | Pre-trade / setup        | DEFINE, CONFIGURE, PUBLISH         | Clients, strategies, venues, API keys, credentials, risk config, venue connections               |
| **ML Platform**            | Model lifecycle        | Training/experiment time | TRAIN, EVALUATE, DEPLOY            | Experiments, models, hyperparameter grids                                                        |
| **Reporting & Settlement** | Client/EOD artifacts   | EOD / periodic           | REPORT, SETTLE                     | EOD positions, invoices, settlements, performance reports, client portfolio                      |

**Overlap resolution rules:**

- **Positions**: Trading Command Center owns _live_ positions. Reporting & Settlement owns _EOD/historical_ positions.
  They are different datasets (real-time feed vs settlement snapshot). No overlap.
- **Risk/exposure**: Trading Command Center owns _current_ risk and exposure. Market Intelligence may _explain_ past
  risk events in the context of P&L attribution, but does not render a live risk matrix. No overlap.
- **Reports**: Market Intelligence owns report _generation_ (analyst creates a report as part of post-trade
  explanation). Reporting & Settlement owns the report _catalogue_ and client-facing views (client downloads their
  report). The generation form lives in Market Intelligence; the artifact lands in Reporting.
- **P&L**: Trading Command Center shows a _summary panel_ (top-line P&L + attribution preview). Market Intelligence owns
  the _full drill-down_ (5-level waterfall, Group By, component decomposition). The summary links to the full view via
  cross-link.
- **Alerts**: Trading Command Center owns _live alert feed and incident management_. Operations Hub shows alerts only in
  the context of _service health and batch job failures_ — operational alerts, not trading alerts.

**The rule: if it's about what's happening NOW, it's Trading. If it's about what HAPPENED, it's Markets. If it's about
what COULD happen based on historical analysis, it's Strategy Analytics. If it's about infrastructure, it's Ops. If it's
about config CRUD, it's Config. If it's about a client artifact, it's Reporting.**

---

## Visual Design Language

### Keep the Dark Theme — It's Already Institutional

The existing design system is strong. Dark backgrounds (`#0a0a0b`), IBM Plex Sans, JetBrains Mono, cyan accent
(`#22d3ee`). This is Bloomberg/Citadel-grade. The ChatGPT mockup's white theme would be a downgrade for a trading
terminal. What needs to change is not the palette — it's the structure.

### Refinements to the Existing Design System

```
KEEP (already excellent):
  - Dark palette: #0a0a0b → #111113 → #18181b → #1c1c1f
  - Cyan accent #22d3ee with dim overlay for active states
  - IBM Plex Sans (UI) + JetBrains Mono (data/values)
  - Status color vocabulary: green/amber/red/purple/blue
  - SidebarNav with left-border-accent active state
  - Badge system (success/error/warning/running/pending)

EVOLVE (polish without breaking):
  - Border radii: 4/6/8/12 → 6/8/12/16px (rounder, more modern)
  - Add transitions: 150ms ease on all interactive elements
  - Add card hover: subtle elevation (box-shadow: 0 2px 8px rgba(0,0,0,0.4))
  - Add section breathing room: 24px between major sections
  - Add PnL semantic tokens: --color-pnl-positive (#4ade80), --color-pnl-negative (#f87171)
  - Sparkline cells in tables: inline SVG, green/red by direction

ADD (new capabilities):
  - GlobalNavBar: persistent top rail linking all surfaces (32px, minimal)
  - LifecycleRail: 7-step horizontal indicator showing current lifecycle phase
  - BreadcrumbNav: Fund > Client > Strategy > Config > Run with cross-surface links
  - DimensionalGrid: sortable/filterable/heatmap-capable data grid for batch analysis
  - FilterBar: URL-based cascading filters that survive refresh and cross-link
  - EntityLink: clickable entity names that deep-link to the correct surface
  - CrossLink: explicit cross-surface navigation with context preservation
```

---

## The Three Hierarchies

The system has three parallel entity hierarchies. Each maps to different user workflows.

### Business Hierarchy (The Money)

```
Fund
  └── Client (allocation, risk terms, reporting)
        └── Strategy (template, archetype, intent)
              └── Config Version (typed trigger/risk/execution package)
                    └── Run (live or batch execution context)
                          ├── Positions (current state per instrument/venue)
                          ├── Orders (instructions emitted)
                          ├── Fills (executions completed)
                          ├── PnL (6D attribution: delta, funding, basis, interest, greeks, MTM)
                          └── Recon (expected vs observed, break resolution)
```

### Operations Hierarchy (The Machine)

```
Service
  └── Deployment (version, environment, region)
        └── Job (batch run, feature backfill, recon sweep)
              ├── Logs (structured events, severity, correlation_id)
              ├── Alerts (threshold breaches, anomalies)
              └── Incidents (escalated alerts requiring resolution)
```

### Research Hierarchy (The Science)

```
Strategy Archetype
  └── Experiment / Grid (parameter sweep)
        └── Result Slice (grouped by shard dimension)
              └── Selected Candidates (meet Sharpe/drawdown/capacity gates)
                    └── Promotion Package (approval + deployment target)
```

---

## Platform Architecture: 4 Surfaces + 3 Specialist Tools

### The Four Primary Surfaces

These are the daily-use surfaces. Every trading day, someone touches all four.

```
┌─────────────────────────────────────────────────────────────────────┐
│  GLOBAL NAV BAR  │ Trading │ Strategy │ Markets │ Ops │ Config │ ML │ Reports │ ⌕ Search │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   LIFECYCLE RAIL                                                    │
│   ○ Design  ○ Simulate  ● Promote  ○ Run  ○ Monitor  ○ Explain  ○ Reconcile │
│                                                                     │
│   BREADCRUMB                                                        │
│   Odum Delta One > Blue Coast Capital > BTC Basis v3 > cfg-3.2.1   │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │                     CONTENT AREA                             │  │
│   │                                                              │  │
│   │   Entity-scoped view with lens tabs                          │  │
│   │   (Positions | Orders | Fills | PnL | Recon | Timeline)      │  │
│   │                                                              │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│   SIDEBAR (surface-specific navigation)                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

#### Surface 1: Trading Command Center (port 5177)

_Was: live-health-monitor-ui. Absorbs: alerts from logs-dashboard-ui, performance overview from client-reporting-ui._

**Purpose:** Everything you need while markets are open. The first screen at 7am.

**Primary user verb:** OBSERVE, INTERVENE

**Lifecycle phases:** Run, Monitor

**Icon color:** `#4ade80` (green — live/active)

**Landing page (`/`) — The "How did you make this so neat?" screen:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GLOBAL NAV ─ ◆ Trading  ◇ Strategies  ◇ Markets  ◇ Ops  ◇ Config  ◇ ML  ◇ Reports │
├─────────────────────────────────────────────────────────────────────────────┤
│  LIFECYCLE ─ ○ Design  ○ Simulate  ○ Promote  ● Run  ○ Monitor  ○ Explain │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐    │
│  │ FIRM PnL  │ │ NET EXPSR │ │ MARGIN    │ │ LIVE      │ │ ALERTS    │    │
│  │ +$1.42m   │ │ $4.2m     │ │ 82% used  │ │ 24 strats │ │ 3 crit   │    │
│  │ ▲ +0.8% 1d│ │ 1.2x levr │ │ $340k free│ │ 18● 4▲ 2○│ │ 2 high   │    │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘    │
│                                                                             │
│  ┌───────────────────────────────────────┐  ┌──────────────────────────────┐│
│  │ STRATEGY PERFORMANCE                  │  │ P&L + RISK ATTRIBUTION      ││
│  │                                       │  │ (same dimensions, 2 sides)  ││
│  │ Strategy     │St│ PnL │Shrp│DD │ ~~~  │  │                             ││
│  │ BTC Basis v3 │●L│+412k│2.1 │4.1│╱╲╱╲ │  │ Bucket    │ P&L    │Exposure││
│  │ ETH Staked   │●L│+289k│2.5 │3.3│╱╲╱  │  │ Funding   │ +$412k │$8.2m  ││
│  │ AAVE Lending │●L│ +91k│1.8 │2.1│╱╲   │  │ Basis     │ +$355k │14 bps ││
│  │ ML Direction │▲W│ -18k│0.9 │6.8│╲╱╲  │  │ Staking   │ +$145k │LTV .72││
│  │ SPY ML Dir   │●L│ +67k│1.4 │3.9│╱╲╱  │  │ Delta     │  +$61k │$2.4m  ││
│  │ Sports Arb   │●L│ +44k│1.6 │1.8│╱╲   │  │ Greeks    │   -$8k │Δ:-0.98││
│  │                                       │  │ Slippage  │  -$61k │──     ││
│  │ Click row → Strategy Analytics        │  │ Fees      │  -$44k │──     ││
│  │ Click status → filtered positions     │  │ Recon     │  -$18k │4 brks ││
│  │ [Group: All▾] [DeFi▾] [Sort: PnL▾]   │  │ NET       │+$1.04m │       ││
│  └───────────────────────────────────────┘  │                             ││
│                                              │ [→ Full P&L in Markets]    ││
│  ┌─────────────────────────────┐             │ [→ Full Risk Detail]       ││
│  │ ALERTS & INCIDENTS          │             └──────────────────────────────┘│
│  │                             │                                            │
│  │ ● CRIT: Kill switch armed  │  ┌────────────────────────────────────────┐│
│  │   BTC Basis v3 — inv skew  │  │ HEALTH & FEATURE FRESHNESS            ││
│  │ ▲ HIGH: Feature freshness  │  │                                        ││
│  │   features-d1 92s lag EU   │  │ Service          │Fresh│ SLA │ Status  ││
│  │ ▲ MED: Recon break         │  │ features-delta-1 │ 92s│  30s│ ▲ lag   ││
│  │   Elysium SMA mismatch    │  │ execution-svc    │  2s│   5s│ ● ok    ││
│  │                             │  │ risk-exposure    │  4s│  10s│ ● ok    ││
│  │ [Kill Switch Panel]         │  │ pnl-attribution  │  8s│  15s│ ● ok    ││
│  │ [→ All Alerts]              │  │ market-tick-data │0.3s│   1s│ ● ok    ││
│  └─────────────────────────────┘  │ ml-inference     │  ──│  ──│ ○ idle  ││
│                                   └────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

**What makes this landing page Citadel-grade:**

1. P&L and Risk Attribution side-by-side in the same 6D breakdown — backward (what happened) vs forward (what's at risk)
2. Feature freshness as first-class metric — if features are stale, strategies trade on stale signals
3. Margin health / LTV in the KPI row — DeFi lending health and CeFi margin utilization at a glance
4. Every cell is a portal — click strategy → analytics, click status badge → positions, click P&L bucket → Markets
   drill-down

**Routes:**

- `/` — Fund dashboard: KPI cards + strategy table + P&L/risk attribution + alerts + health/freshness
- `/positions` — All live positions, filterable by [Client | Strategy | Venue | Asset Class]
- `/positions/:runId` — Position detail: orders, fills, execution timeline
- `/risk` — Full risk view with two tabs:
  - **Risk Matrix**: leverage, margin utilization, concentration, drawdown per client/strategy
  - **Exposure Attribution**: delta/funding/basis/interest/greeks exposure in same dimensions as P&L
  - **Margin Health**: per-venue margin utilization, liquidation distance, free margin
  - **DeFi Health**: LTV per lending position, health factor, liquidation threshold, collateral composition
- `/alerts` — Unified alert feed, severity-colored, dismissible, with incident creation
- `/health` — Service health grid + dependency DAG + feature freshness SLA tracker
- `/manual` — Manual trade entry (scoped: select client + strategy first) + kill switches

**Kill Switch / Intervention Panel (slide-out sheet):**

- Scope selector: Fund → Client → Strategy → Venue (cascading)
- Actions: Pause Strategy, Cancel Outstanding Orders, Flatten Exposure, Disable Venue
- Every action requires: rationale text, scope preview, generates incident + audit record
- Confirmation modal with affected position count and estimated market impact

**Deep links OUT:**

- Strategy name → Strategy Analytics `/strategies/:id`
- Client name → Markets `/pnl/client/:id`
- P&L bucket → Markets `/pnl?component=funding` (pre-filtered to that component)
- Exposure bucket → `/risk` with that dimension expanded
- Alert → `/alerts?id=:id` (same surface)
- Service freshness → Operations `/services/:name`

---

## Complete Workflow Map — "I want to X, where do I go?"

### Seeing Things

| I want to see...                    | Surface                | Route                     | Details                                                |
| ----------------------------------- | ---------------------- | ------------------------- | ------------------------------------------------------ |
| Firm P&L at a glance                | Trading Command Center | `/`                       | KPI card + attribution panel                           |
| P&L attribution breakdown (6D)      | Market Intelligence    | `/pnl` → drill 5 levels   | delta, funding, basis, interest, greeks, MTM           |
| Risk/exposure attribution (same 6D) | Trading Command Center | `/risk` → Exposure tab    | delta exp, funding exp, basis spread, LTV, greeks      |
| Margin health / utilization         | Trading Command Center | `/risk` → Margin tab      | Per-venue margin %, free margin, liquidation dist      |
| LTV / DeFi lending health           | Trading Command Center | `/risk` → DeFi Health tab | Health factor, collateral, liquidation threshold       |
| Greek risks (options + basis)       | Trading Command Center | `/risk` → Exposure tab    | Delta, gamma, theta, vega + basis/funding Greeks       |
| Feature freshness / values          | Trading Command Center | `/health` + landing KPI   | Per-service freshness vs SLA target                    |
| Market tick data                    | Strategy Analytics     | `/tick-data`              | Instrument picker, candle/tick toggle, venue filter    |
| Order book depth                    | Market Intelligence    | `/orderbook`              | Bid/ask depth, spread, microstructure                  |
| Venue connections / latency         | Config & Onboarding    | `/venue-connections`      | REST/WS status, latency, error rate, rate limits       |
| Batch vs live reconciliation        | Market Intelligence    | `/recon`                  | Expected (backtest) vs actual (live) with break detail |
| Strategy performance ranked         | Trading Command Center | `/`                       | Strategy table with sparklines, sortable               |
| System health                       | Trading Command Center | `/health`                 | Service grid + DAG + tier status                       |
| Batch job results                   | Operations             | `/jobs`                   | Job list with status, completeness heatmap             |
| All clients                         | Config & Onboarding    | `/clients`                | Client grid with AUM, strategy count                   |

### Doing Things

| I want to...              | Surface                  | Route                        | Flow                                                  |
| ------------------------- | ------------------------ | ---------------------------- | ----------------------------------------------------- |
| Trade manually            | Trading Command Center   | `/manual`                    | Select Client → Strategy → Venue → Instrument → Order |
| Kill/pause a strategy     | Trading Command Center   | Kill Switch panel            | Scope → Action → Rationale → Confirm                  |
| Set config live (promote) | Strategy Analytics → Ops | `/grid` → select → promote   | Select best in grid → cross-link to Ops deploy form   |
| Onboard a new client      | Config & Onboarding      | `/clients` → New             | Wizard-style CRUD                                     |
| Onboard a new strategy    | Config & Onboarding      | `/strategies` → New          | Config editor + publish to GCS                        |
| Run a backtest            | Strategy Analytics       | `/strategies/:id` → Backtest | Instrument + date range + config                      |
| Deploy a service          | Operations               | `/deploy`                    | Service picker + config + dry-run toggle              |
| Generate a config grid    | Strategy Analytics       | `/generate`                  | Param grid → mass-deploy → track progress             |
| Generate a report         | Market Intelligence      | `/reports/generate`          | Client + period + format (PDF/CSV)                    |
| Deploy an ML model        | ML Platform              | `/models` → Deploy           | Model version → cross-link to Ops                     |
| Settle positions          | Reporting                | `/settlements/:id` → Confirm | Review + confirm workflow                             |

---

#### Surface 2: Strategy Analytics (port 5175)

_Was: strategy-ui. Absorbs: ALL of execution-analytics-ui (they share 90% of routes and hit the same API)._

**Purpose:** Strategy lifecycle from idea to backtest to live to execution analysis. The quant's home.

**Primary user verb:** DESIGN, SIMULATE, COMPARE, PROMOTE

**Lifecycle phases:** Design, Simulate, Promote

**Icon color:** `#60a5fa` (blue — research/analytical)

**Landing page (`/strategies`):**

```
┌──────────────────────────────────────────────────────────────────┐
│  ⌕ Search strategies, instruments, configs...                    │
│                                                                  │
│  Filter: [All ▾] [DeFi ▾] [CeFi ▾] [TradFi ▾] [Sports ▾]     │
│          [Status: live/paper/backtest ▾] [Client ▾]             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ BTC Basis v3                          DeFi │ ● live       │ │
│  │ Binance + Hyperliquid                                      │ │
│  │ Sharpe: 2.1  │  Return: +18.4%  │  DD: 4.1%  │  ╱╲╱╲╱   │ │
│  │ [View Live →]  [Backtest →]  [Config →]                   │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │ ETH Staked Basis                      DeFi │ ● live       │ │
│  │ EtherFi + Hyperliquid                                      │ │
│  │ Sharpe: 2.5  │  Return: +22.1%  │  DD: 3.3%  │  ╱╲╱╲    │ │
│  │ [View Live →]  [Backtest →]  [Config →]                   │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

**Routes (merged strategy-ui + execution-analytics-ui):**

_Strategies Section:_

- `/strategies` — Catalogue: filterable card grid by asset class, status, client
- `/strategies/:id` — Strategy hub with tabs:
  - Overview (config, parameters, venues, risk limits, allocation)
  - Live (real-time positions, exposure, risk — links to Trading Command Center)
  - Backtest (run new backtest, view historical results)
  - Results (equity curve, metrics, daily P&L breakdown)
  - Execution (fills on tick data, TCA, alpha decomposition, slippage analysis)
  - Deep Dive (per-config detailed attribution timeline)
- `/strategies/:id/compare` — Side-by-side config version comparison

_Batch Analysis Section:_

- `/grid` — DimensionalGrid: all backtest results, slice by [strategy, instrument, venue, date, config]
- `/compare` — Algorithm comparison: overlay equity curves, rank by metric
- `/heatmap` — Two-dimension heatmap (e.g., instrument x algorithm → Sharpe)

_Config Section:_

- `/configs` — Config browser (all configs across strategies)
- `/generate` — Config generator → mass deploy step
- `/instruments` — Instrument definitions and data availability
- `/tick-data` — Market tick data explorer

**DimensionalGrid (the killer feature for batch analysis):**

```
┌──────────────────────────────────────────────────────────────────┐
│  Showing 47 of 1,203 configs                          [Heatmap] │
│                                                                  │
│  Dimensions: [Instrument ▾] [Venue ▾] [Strategy ▾] [Date ▾]   │
│  Sort: Sharpe ↓                                                  │
│                                                                  │
│  ☐ │ Experiment │ Strategy       │ Config    │ Venue    │ Shard  │
│    │            │                │           │          │        │
│  ☐ │ exp-221    │ BTC Basis v3   │ 3.3.0-rc1 │ Bin/Bybit│ 2025Q4 │
│    │ Sharpe: 2.1 │ PnL: $1.8m │ DD: 4.1% │ Trades: 847       │
│  ☐ │ exp-301    │ ETH Staked     │ 2.5.0     │ Aave/HL  │ 2026Q1 │
│    │ Sharpe: 2.5 │ PnL: $2.4m │ DD: 5.0% │ Trades: 412       │
│  ☐ │ exp-222    │ BTC Basis v3   │ 3.3.0-rc2 │ Bin/OKX  │ 2026Q1 │
│    │ Sharpe: 1.7 │ PnL: $1.1m │ DD: 3.3% │ Trades: 923       │
│                                                                  │
│  ┌───────────── Selection Toolbar (3 selected) ──────────────┐  │
│  │  [Promote to Batch ▾]  [Promote to Live ▾]  [Export CSV]  │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

**Promotion Flow (from Grid → Live):**

1. Select best rows by checkbox
2. Click "Promote to Live" → environment picker (dev/staging/live)
3. Generates cross-link to Operations:
   `http://localhost:5183/deploy?service=strategy-service&config_folders=gs://...&env=staging`
4. Operations UI pre-fills the deploy form with selected configs
5. User reviews and deploys (no auto-deploy)

**Deep links OUT:**

- "View Live" → Trading Command Center `/positions?strategy_id=:id`
- "Promote to Live" → Operations `/deploy?service=...&config_folders=...`
- "Edit Config" → Config & Onboarding `/strategies/:id`

---

#### Surface 3: Market Intelligence (port 5180)

_Was: trading-analytics-ui. Absorbs: report generation from client-reporting-ui._

**Purpose:** P&L attribution, microstructure, reconciliation. The post-trade analytics surface.

**Primary user verb:** EXPLAIN, RECONCILE

**Lifecycle phases:** Explain, Reconcile

**Icon color:** `#a78bfa` (purple — analytical/deep)

**Landing page (`/pnl`):**

```
┌──────────────────────────────────────────────────────────────────┐
│  GROUP BY: [All ▾] [Client ▾] [Strategy ▾] [Venue ▾] [Asset ▾]│
│  DATE: [2026-03-17 ▾]  TYPE: [Total ▾ | Realized | Unrealized] │
│                                                                  │
│  BREADCRUMB: All > Blue Coast Capital > BTC Basis v3             │
│                                                                  │
│  ┌─── P&L WATERFALL ─────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  Funding    █████████████████  +$412k                      │  │
│  │  Carry      ████████████       +$355k                      │  │
│  │  Basis      ██████             +$188k                      │  │
│  │  Staking    █████              +$145k                      │  │
│  │  Delta      ██                 +$61k                       │  │
│  │  Slippage   ▓▓▓               -$61k                       │  │
│  │  Fees       ▓▓                 -$44k                       │  │
│  │  Recon      ▓                  -$18k                       │  │
│  │  ──────────────────────────────────────                    │  │
│  │  NET        █████████████████  +$1.04m                     │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Click any row to drill down one level deeper                    │
└──────────────────────────────────────────────────────────────────┘
```

**Routes:**

- `/pnl` — P&L waterfall with Group By control: [All | Client | Strategy | Asset Class | Venue]
- `/pnl/client/:id` — Client-scoped P&L breakdown by strategy
- `/pnl/strategy/:id` — Strategy-scoped P&L with 6D attribution (delta, funding, basis, interest, greeks, MTM)
- `/pnl/venue/:id` — Venue-scoped P&L (useful for venue cost analysis)
- `/desk` — Live order flow + fills (the trading desk view)
- `/orderbook` — Order book microstructure viewer
- `/latency` — Latency analytics (p50/p95/p99 by service, venue, instrument)
- `/recon` — Reconciliation runs list
- `/recon/:date` — Recon detail: expected vs observed, break size, source system, resolution status
- `/recon/:date/deviations` — Individual deviation drill-down with evidence trail
- `/reports` — Report list (absorbed from client-reporting-ui)
- `/reports/generate` — Report generation form (PDF/CSV)

**P&L Hierarchy (5 levels deep):**

```
Level 1: ALL (total system P&L)
  Level 2: By Client
    Level 3: By Strategy (within client)
      Level 4: By Venue (within strategy × client)
        Level 5: By P&L Component
          (delta_pnl, funding_pnl, basis_pnl, staking_yield_pnl,
           interest_rate_pnl, greeks_pnl, carry_pnl, rewards_pnl,
           transaction_costs, mark_to_market_pnl, residual_pnl)
```

**Deep links OUT:**

- Strategy name → Strategy Analytics `/strategies/:id`
- Client name → same surface `/pnl/client/:id` (drill down)
- "View Live" → Trading Command Center `/positions?strategy_id=:id`

---

#### Surface 4: Operations Hub (port 5183)

_Was: deployment-ui. Absorbs: batch-audit-ui, logs-dashboard-ui, unified-admin-ui._

**Purpose:** Deploy, monitor jobs, view logs, check compliance. The SRE surface.

**Primary user verb:** DEPLOY, DIAGNOSE, INTERVENE

**Lifecycle phases:** (infrastructure, orthogonal to business lifecycle)

**Icon color:** `#fbbf24` (amber — operations/caution)

**Landing page (`/`):**

```
┌──────────────────────────────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────────────────────────────────┐ │
│  │ BATCH SUMMARY│  │ DATA COMPLETENESS HEATMAP                │ │
│  │              │  │                                          │ │
│  │ ● 47 done   │  │ Service      │ -3d │ -2d │ -1d │ today  │ │
│  │ ▲ 3 failed  │  │ features-d1  │ ███ │ ███ │ ██░ │ █░░    │ │
│  │ ◎ 12 running│  │ execution    │ ███ │ ███ │ ███ │ ███    │ │
│  │              │  │ risk-exp     │ ███ │ ███ │ ███ │ ██░    │ │
│  │ Last 24h    │  │ pnl-attrib   │ ███ │ ███ │ ███ │ ███    │ │
│  └──────────────┘  └──────────────────────────────────────────┘ │
│                                                                  │
│  RECENT DEPLOYMENTS                      QUICK ACTIONS           │
│  ┌────────────────────────────────┐     [Deploy Service →]       │
│  │ execution-service  prod v31    │     [View All Logs →]        │
│  │ features-delta-one prod v17    │     [Check Compliance →]     │
│  │ risk-and-exposure  prod v12    │                              │
│  └────────────────────────────────┘                              │
└──────────────────────────────────────────────────────────────────┘
```

**Routes (merged deployment-ui + batch-audit-ui + logs-dashboard-ui):**

_Deploy Section:_

- `/` — Overview: batch summary + data completeness + recent deployments
- `/deploy` — Service deployment form (dry run + live), accepts query params for pre-fill
- `/services` — Services overview grid
- `/services/:name` — Service detail: Deploy, Data Status, Builds, Readiness, Config, History
- `/epics` — Epic readiness view

_Observe Section:_

- `/jobs` — Batch jobs list with status/health (from batch-audit-ui)
- `/jobs/:id` — Job detail: shard progress, logs, duration (from batch-audit-ui)
- `/logs` — Unified log stream: filter by service, level, time, text search (from logs-dashboard-ui)
- `/logs/:id` — Log detail with correlation_id trace
- `/events` — Events viewer: structured event stream (from logs-dashboard-ui)
- `/data-health` — Data completeness checks per service (from batch-audit-ui)

_Compliance Section:_

- `/audit` — Audit trail: full event log (from batch-audit-ui)
- `/compliance` — Compliance checks and status (from batch-audit-ui)
- `/cicd` — CI/CD pipeline status (from logs-dashboard-ui)

**Sidebar nav grouping:**

```
DEPLOY
  Overview
  Deploy Service
  Services
  Epics

OBSERVE
  Batch Jobs
  Logs
  Events
  Data Health

COMPLIANCE
  Audit Trail
  Compliance
  CI/CD
```

---

### The Three Specialist Tools

#### Tool 5: Config & Onboarding (port 5173)

_Was: onboarding-ui. Trimmed: remove /deployments, /audit._

**Purpose:** CRUD for clients, strategies, venues, credentials, risk config. Config publishing.

**Lifecycle phase:** Design (configure before you trade)

**Routes (trimmed):**

- `/clients`, `/clients/:id` — Client CRUD with fee structure
- `/strategies`, `/strategies/:id` — Strategy config editing + publishing to GCS
- `/venues`, `/venues/:id` — Venue CRUD
- `/venue-connections` — Live connectivity status
- `/api-keys` — API key management
- `/credentials` — Credential status
- `/risk` — Risk configuration per client/strategy
- `/strategy-manifest` — Strategy manifest (read-only, from UAC registry)

**Cross-links OUT:**

- "Run Backtest →" → Strategy Analytics `/strategies/:id/backtest`
- "View Live →" → Trading Command Center `/positions?strategy_id=:id`
- "View Analytics →" → Market Intelligence `/pnl/strategy/:id`

#### Tool 6: ML Platform (port 5179)

_Was: ml-training-ui. Unchanged except: remove /deployments tab._

**Purpose:** Model training, experiment management, model registry.

**Routes:**

- `/experiments` — Experiment list
- `/experiments/:id` — Experiment detail + DimensionalGrid for hyperparameter comparison
- `/experiments/:id/grid` — Hyperparameter grid: dimensions = [instrument, timeframe, learning_rate, num_layers,
  dropout, phase]
- `/models` — Model registry with deploy action

**Cross-links OUT:**

- "Deploy Model →" → Operations `/deploy?service=ml-inference-service`

#### Tool 7: Client Reporting & Settlement (port 5182)

_Was: client-reporting-ui. Absorbs: settlement-ui (invoices, settlements, EOD positions)._

**Purpose:** Client-facing views: performance reports, invoices, settlement. Post-trade/EOD only.

**Routes (merged):**

- `/portfolio` — Client portfolio overview (links to Market Intelligence for P&L detail)
- `/performance` — Historical performance: monthly returns, Sharpe, by-client breakdown
- `/reports` — Report list
- `/reports/generate` — Report generation form (PDF/CSV)
- `/positions` — Historical/EOD positions only (NOT live — live positions → Trading Command Center)
- `/invoices` — Invoice management (from settlement-ui)
- `/settlements` — Settlement records (from settlement-ui)
- `/settlements/:id` — Settlement detail with confirm workflow

---

## Cross-Surface Navigation System

### Global Nav Bar (ui-kit: `<GlobalNavBar />`)

Every UI gets a persistent 32px top bar:

```
┌─────────────────────────────────────────────────────────────┐
│ ◆ Trading  ◇ Strategies  ◇ Markets  ◇ Ops  ◇ Config  ◇ ML  ◇ Reports  │  ⌕ Global Search  │
└─────────────────────────────────────────────────────────────┘
```

- 7 surface labels, icon + text
- Current surface highlighted (filled icon, cyan underline)
- Global fuzzy search: strategies, clients, instruments, services, configs
- Uses `ui-api-mapping.json` for port resolution (local dev) or path prefixes (production)
- 32px height — compact, never dominant

### Lifecycle Rail (ui-kit: `<LifecycleRail />`)

Horizontal 7-step indicator, shown below the GlobalNavBar when relevant:

```
○ Design  ○ Simulate  ● Promote  ○ Run  ○ Monitor  ○ Explain  ○ Reconcile
```

- Active step is filled (●), others hollow (○)
- Steps are clickable — navigates to the appropriate surface for that phase
- Mapping:
  - Design → Config & Onboarding
  - Simulate → Strategy Analytics `/grid`
  - Promote → Strategy Analytics `/grid` (selection + promote flow)
  - Run → Trading Command Center
  - Monitor → Trading Command Center `/alerts`
  - Explain → Market Intelligence `/pnl`
  - Reconcile → Market Intelligence `/recon`

### Breadcrumb Nav (ui-kit: `<BreadcrumbNav />`)

```
Odum Delta One > Blue Coast Capital > BTC Basis v3 > cfg-3.2.1 > run-2026-03-17-live-01
```

- Each level is clickable
- Cross-surface: clicking "Blue Coast Capital" navigates to Market Intelligence `/pnl/client/blue-coast`
- Clicking "BTC Basis v3" navigates to Strategy Analytics `/strategies/btc-basis-v3`
- Current level shows available lenses as tabs below

### Entity Link (ui-kit: `<EntityLink />`)

Every entity name rendered anywhere becomes a clickable deep link:

| Entity     | Target Surface         | Target Path              | Example                                    |
| ---------- | ---------------------- | ------------------------ | ------------------------------------------ |
| strategy   | Strategy Analytics     | `/strategies/:id`        | "BTC Basis v3" → click → strategy detail   |
| client     | Market Intelligence    | `/pnl/client/:id`        | "Blue Coast Capital" → click → client P&L  |
| instrument | Strategy Analytics     | `/instruments?q=:symbol` | "BTC-PERP" → click → instrument detail     |
| service    | Operations             | `/services/:name`        | "execution-service" → click → service ops  |
| experiment | ML Platform            | `/experiments/:id`       | "exp-221" → click → experiment detail      |
| settlement | Reporting              | `/settlements/:id`       | "SETT-2026-03" → click → settlement detail |
| batch_job  | Operations             | `/jobs/:id`              | "JOB-123" → click → job detail             |
| run        | Trading Command Center | `/positions/:runId`      | "run-2026-03-17-live-01" → position detail |

### Cross-Link Context Preservation

When navigating between surfaces, filters carry over:

```
# From Trading Command Center → Market Intelligence P&L for specific client+strategy
http://localhost:5180/pnl?client_id=blue-coast&strategy_id=BTC_BASIS_V3&from=trading

# From Strategy Analytics promote → Operations with pre-filled deploy form
http://localhost:5183/deploy?service=strategy-service&config_folders=gs://...&env=staging&from=strategy-analytics

# From Onboarding client → Trading Command Center filtered to that client
http://localhost:5177/positions?client_id=blue-coast&from=onboarding
```

Each receiving UI reads `?client_id=`, `?strategy_id=`, `?from=` from URL params on mount.

---

## DimensionalGrid Component (ui-kit)

The shared grid component for batch analysis. Used in Strategy Analytics, ML Platform, and anywhere configs need
comparing.

### Design

```typescript
interface DimensionalGridProps {
  // Available dimensions for this grid
  dimensions: DimensionDef[];
  // Metric columns with formatters
  metrics: MetricDef[];
  // Data rows
  data: Record<string, unknown>[];
  // Currently pinned (filtered) dimensions
  pinnedDimensions: Record<string, string[]>;
  // Callbacks
  onDimensionPin: (dim: string, values: string[]) => void;
  onSort: (metric: string, direction: "asc" | "desc") => void;
  onRowSelect: (rowIds: string[]) => void;
  onRowClick: (rowId: string) => void;
  // Features
  enableSelection?: boolean;
  enableHeatmap?: boolean;
  enableExport?: boolean;
  // Selection toolbar render
  selectionToolbar?: (selectedIds: string[]) => ReactNode;
}
```

### Behavior

- **Dimension pills** at the top: dropdown filters per dimension
- **Pinning** a dimension = filtering: "Show only instrument=ETH" collapses that dimension
- **Unpinned** dimensions appear as groupable columns
- **Metrics** are sortable columns with optional sparklines
- **Row count**: "Showing 47 of 1,203 configs"
- **Heatmap toggle**: switches between table and two-dimension color matrix
- **Checkbox selection** with floating toolbar for promote/export actions
- **CSV export** of filtered/sorted results
- **URL state**: all filter/sort state written to query params

### Usage in Strategy Analytics: `/grid`

- Dimensions: strategy, instrument, venue, date_range, config_version
- Metrics: sharpe, total_return, max_drawdown, trade_count, win_rate, net_alpha_bps
- Backed by: `POST /api/v1/analysis/aggregate` and `GET /api/v1/analysis/best-configs`

### Usage in ML Platform: `/experiments/:id/grid`

- Dimensions: instrument, timeframe, learning_rate, num_layers, dropout, training_phase
- Metrics: accuracy, loss, epoch_count, training_time, sharpe_improvement

---

## FilterBar Component (ui-kit)

### Design

```typescript
interface FilterBarProps {
  filters: FilterDef[]; // Available filter slots
  values: FilterValues; // Current filter state
  onChange: (values: FilterValues) => void;
  counts?: Record<string, Record<string, number>>; // Cascading counts per option
  syncToUrl?: boolean; // Write state to query params
}
```

### Behavior

- **URL-based state**: reads/writes query params so filters survive refresh and are shareable
- **Cascading counts**: selecting client=FUND_A updates strategy dropdown to show only that client's strategies
- **Multi-select**: multiple instruments, strategies, venues at once
- **Search within dropdown**: for 50+ strategies or 60+ venues
- **Clear individual + clear all**: each filter pill has ×, plus "Clear all"
- **Dimension toggle**: pin/unpin between filter (fixed) and grid (variable)

---

## Intent Navigation Map

### "I want to see..." (Overviews)

| I want to see...                       | Surface                | Page           | What I see                               |
| -------------------------------------- | ---------------------- | -------------- | ---------------------------------------- |
| Fund-level P&L, everything at a glance | Trading Command Center | `/`            | KPI cards + strategy sparklines + alerts |
| All strategy performance ranked        | Trading Command Center | `/`            | Strategy table, sortable by Sharpe/P&L   |
| System health and service status       | Trading Command Center | `/health`      | Service grid + dependency DAG            |
| Batch run summary, what ran overnight  | Operations             | `/`            | Job counts + data completeness heatmap   |
| All clients and their allocations      | Config & Onboarding    | `/clients`     | Client grid with AUM, strategy count     |
| All pending settlements                | Reporting              | `/settlements` | Settlement list, filterable              |

### "I want to drill into..." (Deep Dives)

| I want to drill into...          | Surface                | Page                              | How I get there              |
| -------------------------------- | ---------------------- | --------------------------------- | ---------------------------- |
| One strategy's P&L decomposition | Market Intelligence    | `/pnl/strategy/:id`               | Click strategy name anywhere |
| One strategy's execution quality | Strategy Analytics     | `/strategies/:id` → Execution tab | Click strategy → Execution   |
| One strategy's live state        | Trading Command Center | `/positions?strategy_id=:id`      | Click "View Live"            |
| One client's P&L by strategy     | Market Intelligence    | `/pnl/client/:id`                 | Click client name anywhere   |
| One instrument's tick data       | Strategy Analytics     | `/tick-data?instrument=:symbol`   | Click instrument name        |
| One service's deploy history     | Operations             | `/services/:name`                 | Click service name anywhere  |
| One recon run's deviations       | Market Intelligence    | `/recon/:date/deviations`         | Click recon run row          |
| One batch job's shard progress   | Operations             | `/jobs/:id`                       | Click job row                |
| One ML experiment's results      | ML Platform            | `/experiments/:id`                | Click experiment row         |

### "I want to compare..." (Grids)

| I want to compare...        | Surface            | Page                    | Dimensions                                |
| --------------------------- | ------------------ | ----------------------- | ----------------------------------------- |
| Strategy backtest configs   | Strategy Analytics | `/grid`                 | strategy, instrument, venue, date, config |
| Execution algo performance  | Strategy Analytics | `/compare`              | algo_type, instrument, venue, benchmark   |
| ML training hyperparameters | ML Platform        | `/experiments/:id/grid` | instrument, timeframe, hyperparams, phase |
| Best configs by metric      | Strategy Analytics | `/grid` sorted          | Sharpe, alpha, P&L, win_rate              |

### "I want to do..." (Actions)

| I want to...                  | Surface                | Page                             |
| ----------------------------- | ---------------------- | -------------------------------- |
| Run a backtest                | Strategy Analytics     | `/strategies/:id` → Backtest tab |
| Deploy a service              | Operations             | `/deploy`                        |
| Promote batch results to live | Strategy Analytics     | `/grid` → select → promote       |
| Create a client               | Config & Onboarding    | `/clients` → "New Client"        |
| Create a strategy config      | Config & Onboarding    | `/strategies` → "New"            |
| Generate config grid          | Strategy Analytics     | `/generate`                      |
| Kill a strategy               | Trading Command Center | Kill Switch panel                |
| Generate a report             | Market Intelligence    | `/reports/generate`              |
| Deploy an ML model            | ML Platform            | `/models` → Deploy               |
| Settle positions              | Reporting              | `/settlements/:id` → Confirm     |

---

## Repos to Deprecate

| Repo                  | Replacement                                                     | Migration                           |
| --------------------- | --------------------------------------------------------------- | ----------------------------------- |
| `strategy-ui`         | Merged into Strategy Analytics (execution-analytics-ui renamed) | Routes merged at port 5175          |
| `batch-audit-ui`      | Merged into Operations (deployment-ui)                          | Tabs added to deployment-ui         |
| `logs-dashboard-ui`   | Merged into Operations (deployment-ui)                          | Tabs added to deployment-ui         |
| `settlement-ui`       | Merged into Reporting (client-reporting-ui)                     | Routes added to client-reporting-ui |
| `unified-admin-ui`    | Redundant (duplicates ops content)                              | Already covered by deployment-ui    |
| `client-reporting-ui` | Renamed to "Client Reporting & Settlement"                      | Absorbs settlement-ui               |

**Post-consolidation: 7 repos, 7 ports, zero duplication.**

---

## Phased Implementation

### Phase 0: Shared Infrastructure (ui-kit only)

Build new components in unified-trading-ui-kit. No breaking changes to existing UIs.

- [ ] [AGENT] P0. `GlobalNavBar` — top nav bar with 7 surface links + global search
- [ ] [AGENT] P0. `LifecycleRail` — 7-step horizontal indicator with click navigation
- [ ] [AGENT] P0. `BreadcrumbNav` — hierarchical navigation with cross-surface links
- [ ] [AGENT] P0. `EntityLink` — clickable entity names with surface routing
- [ ] [AGENT] P0. `CrossLink` / `buildCrossLink` — URL builder with context preservation
- [ ] [AGENT] P0. `SurfaceRegistry` — port/route mapping from ui-api-mapping.json
- [ ] [AGENT] P0. `DimensionalGrid` — sortable/filterable grid with selection, heatmap, export
- [ ] [AGENT] P0. `FilterBar` — URL-based cascading filters with counts
- [ ] [AGENT] P0. `SparklineCell` — inline SVG sparklines for table cells
- [ ] [AGENT] P0. `SelectionToolbar` — floating toolbar for batch actions on selected rows
- [ ] [AGENT] P0. `useDeepLinkParams()` hook — reads client_id, strategy_id, from params on mount
- [ ] [AGENT] P0. Visual polish: updated radii, transitions, PnL tokens, card hover, section spacing in globals.css

**QG gate:** `cd unified-trading-ui-kit && bash scripts/quality-gates.sh` + `CI=true npm test -- --run`

### Phase 1: Remove /deployments pollution + add GlobalNavBar (all UIs)

- [ ] [AGENT] P1. Remove `/deployments` route from 10 non-deployment UIs
- [ ] [AGENT] P1. Mount `GlobalNavBar` in AppShell (all UIs get it automatically)
- [ ] [AGENT] P1. Replace plain-text entity names with `EntityLink` in all table views

**QG gate:** all 11 UIs pass quality-gates.sh

### Phase 2: Merge execution-analytics-ui + strategy-ui → Strategy Analytics

- [ ] [AGENT] P2. Add `/strategies` catalogue and `/live` routes to execution-analytics-ui
- [ ] [AGENT] P2. Wire `DimensionalGrid` into `/grid`, `/compare` using existing unwired API endpoints
- [ ] [AGENT] P2. Add promotion toolbar: select best configs → cross-link to Operations with pre-fill
- [ ] [AGENT] P2. Rename to "Strategy Analytics" in AppShell identity
- [ ] [SCRIPT] P2. Update ui-api-mapping.json, dev-start.sh: strategy-ui becomes redirect shell

**QG gate:** Strategy Analytics passes QG; promotion cross-link verified manually

### Phase 3: Build Trading Command Center (live-health-monitor-ui → Trading Command Center)

- [ ] [AGENT] P3. Build landing page: KPI grid + strategy sparkline table + alert feed + health bar
- [ ] [AGENT] P3. Build `/positions` with filterable table [Client | Strategy | Venue | Asset Class]
- [ ] [AGENT] P3. Build Kill Switch / Intervention panel (sheet with scoped actions)
- [ ] [AGENT] P3. Absorb alerts from logs-dashboard-ui
- [ ] [AGENT] P3. Rename to "Trading Command Center" in AppShell identity

**QG gate:** Trading Command Center passes QG

### Phase 4: Merge ops UIs into Operations Hub (deployment-ui)

- [ ] [AGENT] P4. Add Logs tab (from logs-dashboard-ui, hits batch-audit-api)
- [ ] [AGENT] P4. Add Batch Jobs + Data Health tabs (from batch-audit-ui)
- [ ] [AGENT] P4. Add Compliance + Audit Trail tabs (from batch-audit-ui)
- [ ] [AGENT] P4. Accept `?service=&config_folders=&env=` query params on deploy form (pre-fill)
- [ ] [AGENT] P4. Update sidebar nav with grouped sections (Deploy / Observe / Compliance)
- [ ] [SCRIPT] P4. Remove batch-audit-ui (5181), logs-dashboard-ui (5178) from dev-start.sh

**QG gate:** Operations Hub passes QG; pre-fill from Strategy Analytics verified

### Phase 5: Merge settlement-ui into client-reporting-ui → Reporting & Settlement

- [ ] [AGENT] P5. Add Invoices, Settlements routes to client-reporting-ui
- [ ] [AGENT] P5. Mark positions as historical/EOD — add "View Live →" link to Trading Command Center
- [ ] [SCRIPT] P5. Remove settlement-ui (5176) from dev-start.sh

**QG gate:** Reporting & Settlement passes QG

### Phase 6: P&L Hierarchy in Market Intelligence (trading-analytics-ui)

- [ ] [AGENT] P6. Build P&L page with Group By control: [All | Client | Strategy | Asset Class | Venue]
- [ ] [AGENT] P6. Waterfall chart (recharts) re-renders on group change
- [ ] [AGENT] P6. Drill-down on row click: breadcrumb + filtered sub-view, 5 levels deep
- [ ] [AGENT] P6. 6D attribution breakdown panel (delta, funding, basis, interest, greeks, MTM)
- [ ] [AGENT] P6. Absorb report generation from client-reporting-ui

**QG gate:** Market Intelligence passes QG; P&L drill-down verified to 5 levels

### Phase 7: UX Hardening (all surfaces)

- [ ] [AGENT] P7. Add `FilterBar` to all list views (strategies, positions, settlements, jobs, logs)
- [ ] [AGENT] P7. Add `BreadcrumbNav` to all drill-down views
- [ ] [AGENT] P7. Add `SparklineCell` to all performance/metric tables
- [ ] [AGENT] P7. Add `LifecycleRail` to relevant surfaces (Strategy Analytics, Trading, Markets)
- [ ] [AGENT] P7. Responsive design pass: mobile-friendly tables, collapsible sidebar
- [ ] [AGENT] P7. Accessibility pass: keyboard navigation, ARIA labels, focus management
- [ ] [SCRIPT] P7. Full workspace validation: `dev-start.sh --all --mode mock` → 7 UIs launch

### Phase 8: Config Lifecycle Flows (Strategy Analytics)

- [ ] [AGENT] P8. Wire `StrategyConfigGenerator` to real `/config/generate-all` API
- [ ] [AGENT] P8. Add mass-deploy preview + deploy step after config generation
- [ ] [AGENT] P8. Add deployment progress tracking: poll `/backtest/status`, shard progress bar
- [ ] [AGENT] P8. Wire ML Training `ExperimentDetailPage` to real API + `DeployModal`

**QG gate:** Strategy Analytics, ML Platform pass QG

---

## Critical Files

| File                                                             | Change                                 |
| ---------------------------------------------------------------- | -------------------------------------- |
| `unified-trading-ui-kit/src/globals.css`                         | Updated radii, transitions, PnL tokens |
| `unified-trading-ui-kit/src/components/ui/global-nav-bar.tsx`    | NEW                                    |
| `unified-trading-ui-kit/src/components/ui/lifecycle-rail.tsx`    | NEW                                    |
| `unified-trading-ui-kit/src/components/ui/breadcrumb-nav.tsx`    | NEW                                    |
| `unified-trading-ui-kit/src/components/ui/entity-link.tsx`       | NEW                                    |
| `unified-trading-ui-kit/src/components/ui/cross-link.tsx`        | NEW                                    |
| `unified-trading-ui-kit/src/components/ui/dimensional-grid.tsx`  | NEW                                    |
| `unified-trading-ui-kit/src/components/ui/filter-bar.tsx`        | NEW                                    |
| `unified-trading-ui-kit/src/components/ui/sparkline-cell.tsx`    | NEW                                    |
| `unified-trading-ui-kit/src/components/ui/selection-toolbar.tsx` | NEW                                    |
| `unified-trading-ui-kit/src/lib/surface-registry.ts`             | NEW                                    |
| `unified-trading-ui-kit/src/hooks/useDeepLinkParams.ts`          | NEW                                    |
| `unified-trading-ui-kit/src/components/ui/app-shell.tsx`         | Mount GlobalNavBar                     |
| `unified-trading-pm/scripts/dev/ui-api-mapping.json`             | Remove 4 deprecated, rename 2          |
| `unified-trading-pm/scripts/dev/dev-start.sh`                    | Remove deprecated UI startup           |
| All 10 non-deployment UIs `/App.tsx`                             | Remove `/deployments` route            |

---

## Verification Protocol

1. **`bash unified-trading-pm/scripts/dev/dev-start.sh --all --mode mock --frontend-only --open`**
   - 7 UIs start (not 11)
   - Ports: 5173, 5175, 5177, 5179, 5180, 5182, 5183

2. **Global nav check:** open any UI → nav bar shows all 7 → click each → correct UI opens

3. **Deep link check:** Trading Command Center `/positions?client_id=blue_coast` → positions pre-filtered

4. **P&L drill-down:** Market Intelligence `/pnl` → Group By "Client" → click row → Strategy → Attribution

5. **Promote flow:** Strategy Analytics `/grid` → select 3 rows → "Promote to Live" → Operations deploy form pre-filled

6. **Kill switch:** Trading Command Center → Kill Switch panel → Pause Strategy → incident record created

7. **No orphan `/deployments`:** grep all UI repos for `path.*deployments` → zero results outside Operations

8. **Quality gates:** all 7 active UI repos pass `bash scripts/quality-gates.sh`

---

## Why This Works

The current system has 11 UIs that each answer one narrow question. The redesigned system has 7 surfaces that together
answer every question through three organizing principles:

1. **Hierarchy** (Fund → Client → Strategy → Config → Run → Position) — you can always drill deeper
2. **Lifecycle** (Design → Simulate → Promote → Run → Monitor → Explain → Reconcile) — you always know what step comes
   next
3. **Cross-linking** (every entity name is a portal to its canonical home) — you never hit a dead end

The complexity doesn't decrease. What changes is that the complexity is _organized_ — navigable via hierarchy, oriented
by lifecycle, and connected by deep links. That's what makes an outsider look at the system and say: "How did you make
this complexity so neat?"

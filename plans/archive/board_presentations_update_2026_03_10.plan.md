---
doc_type: plan
title: board-presentations-update-2026-03-10
summary: Update all 10 existing HTML presentations and create 3 new ones for the board meeting on 2026-03-31, including
  rehearsals on March 13 and March 18.
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-10'
type: business
epic: epic-business
superseded_by: presentations_2026_03_13
superseded_date: 2026-03-13
completion_gates: {code: C5, deployment: none, business: B6}
repo_gates:
- {repo: unified-trading-pm, code: C0, deployment: none, business: none, readiness_note: 'C0: not started. DR N/A: presentation/documentation — no infrastructure deployment required. BR N/A: business completion tracked at plan level (B6), not per repo.'}
depends_on: [elysium-defi-presentation-2026-03-10, e2e-smoke-and-portable-backtests]
isProject: false
---

# Plan: Board Presentations Update & Rehearsal

status: superseded superseded_by: presentations_2026_03_13 superseded_date: 2026-03-13 2026-03-18 (Tuesday)

## Context

10 HTML presentations exist in `unified-trading-pm/presentations/`. They need updating to reflect current system state,
traction, new clients, GCP credit situation, AWS plan, and company history. 3 new presentations are needed:
analytics/screening, financial projections, status quo + traction. 1 DeFi-specific presentation for Elysium (covered in
`elysium_defi_presentation_2026_03_10.md`). Rehearsals: Thursday March 13 and Tuesday March 18. Board meeting: March 31.

---

## Part A: Cross-cutting updates to ALL existing presentations

Apply to every presentation where relevant:

### A1 — Traction bar (top of each deck)

Add to intro/overview slide of each deck:

> "8 active strategy clients · Fund-to-fund (Edge Capital / BTC strategy) · Indian options mandate (incoming)"

### A2 — System status callout

> "In final hardening phase — live trading week March 20, 2026"

### A3 — Cloud / data story

Add where relevant (esp. 01, 08):

> "100TB+ of financial data · $40k AWS credits secured · GCP credits via Elysium partnership in progress"

### A4 — History slide

Add to `00-master.html` and reference from 01:

> **Our Journey**
>
> - Late 2021: Founded. Built HFT strategy on 3+ exchanges
> - 2022–2023: 30%+ annualised returns. 6 clients. Profitable strategy
> - 2023: Cash flow challenges → couldn't raise sufficient capital → strategic pause
> - 2024–2025: Full rebuild. Architecture, data infrastructure, ML, cloud, 60 repos
> - 2026: Launch of unified multi-asset platform (crypto, DeFi, TradFi, sports)

---

## Part B: Per-presentation specific updates

### 01 — data-provision.html

- Add: 100TB data figure across 4 asset classes
- Add: 33 venues (9 CeFi, 9 TradFi, 14 DeFi, 1 onchain perps)
- Add: data provider list (Databento, Tardis, TheGraph, Alchemy, Glassnode, Coinglass, Arkham, OpenBB, FRED, ECB,
  Barchart)
- Add: Indian equities/options data incoming via client relationship
- Add: 14 DeFi protocols supported (Aave, Uniswap, Curve, Balancer, Lido, etc.)

### 02 — backtesting-as-a-service.html

- Add: portable backtests — deterministic, <2s, reproducible, no live API calls
- Add: 4-asset-class backtest results (CeFi: +36.5, TradFi: +218.75, DeFi: +39.2, Sports: +6.22)
- Add: "Universal strategy" — 8 clients on record since 2021

### 03 — strategy-white-labelling.html

- Add: Elysium fork as concrete white-labelling example (DeFi system they own)
- Add: Indian options mandate (client provides their own data + capital, we provide execution)
- Add: real strategy types (basis, lending, momentum, stat-arb, staked-basis)
- Add: "Bring your own data" model for partners

### 04 — execution-as-a-service.html

- Add: execution algorithms (TWAP, VWAP, SOR, passive-aggressive, atomic bundle, swap-TWAP)
- Add: 33 venues, circuit breakers, ≤500ms order submission target
- Add: DeFi execution handlers (swap, lend, stake, borrow, flash-loan)
- Add: gas cost gating, slippage control for DeFi

### 05 — investment-management.html

- Add: fund-to-fund structure with Edge Capital (BTC strategy)
- Add: 8 clients on universal strategy (history since 2021)
- Add: Indian options mandate as new institutional mandate example
- Add: Elysium DeFi as systematic DeFi fund mandate
- Add: trajectory: from 6 clients at peak HFT → rebuilding → 8+ at relaunch

### 06 — regulatory-umbrella.html

- Update: current regulatory status and jurisdiction
- Add: DeFi strategies — onchain, non-custodial option as regulatory advantage

### 07 — autonomous-ai-operations.html

- Add: autonomous agent CI (60 repos, overnight agent runs)
- Add: Grafana dashboards for strategy visibility
- Add: automated recon + rebalancing (new plans)
- Add: data availability monitoring (every source has a freshness SLA)

### 08 — system-quality.html

- Add: quality gate framework (linter, typecheck, tests, codex)
- Add: SIT layers 0–3 (schema → robustness → infra → full e2e)
- Add: performance targets (≤500ms execution, ≥1000 ticks/sec ingestion)
- Add: 60 repos, T0→T6 tier architecture
- Add: current coverage/typecheck status (update before each rehearsal)

### 09 — platform-portal.html

- Add: Grafana integration for real-time strategy scoring + PnL
- Add: admin UI with deployment management (Cloud Run service control)
- Add: strategy development workflow (scoring breakdown, backtest visualizer)

---

## Part C: New presentations to create

### 11 — analytics-screening.html

Title: "Analytics & Screening Platform" Content:

- Big data analytical capability across 4 asset classes (100TB)
- Asset class screeners: momentum, volatility, correlation, DeFi yield screener
- Educational visualizations: help users understand asset classes and strategies
- Investment decision support: data-driven insights (not financial advice)
- Use case: sophisticated retail + institutional research teams
- Revenue model: SaaS subscription ($X/month per user, tiered by access)

### 12 — financials-projections.html

Title: "Financial Projections" Content: Stacked bar charts (Chart.js) for each revenue stream, projected over 3 years
(2026–2029):

**Revenue streams:** | Stream | Year 1 | Year 2 | Year 3 | Notes | |---|---|---|---|---| | Strategy mgmt fees (2% AUM) |
$X | $Y | $Z | Grows with AUM from clients | | Performance fees (20% profits) | $X | $Y | $Z | Variable | | White-label
licensing | $X | $Y | $Z | Fixed monthly per client | | Backtesting-as-a-service | $X | $Y | $Z | Per-use pricing | |
Data provision | $X | $Y | $Z | Monthly subscription | | Platform portal (SaaS) | $X | $Y | $Z | Tiered pricing |

Note: financial figures require input from owner before presenting. Placeholder structure only.

**Cost structure:** | Cost | Year 1 | Notes | |---|---|---| | Cloud (GCP + AWS) | ~$0 | Credits cover 2–3 years | |
External data | $X/month | Tardis, Databento, etc. | | Team | $X | Current: 2 people |

Include disclaimer: "Projections are illustrative scenarios, not financial forecasts."

### 13 — status-quo-traction.html

Title: "Where We Are Today" Sections:

1. **Infrastructure**
   - GCP credits: ran out Feb 9, 2026
   - AWS: $40k credits secured (CodeBuild + ECS active)
   - GCP via Elysium partnership: application in progress
   - 60 repos, 100TB data, all-cloud architecture

2. **Existing Clients + Traction**
   - 8 clients on universal strategy (names available with permission)
   - Edge Capital fund-to-fund (BTC strategy)
   - Indian options mandate: client provides data + capital for Indian options

3. **System Status**
   - Live trading week: March 20, 2026
   - 33 venues connected, all 4 asset classes
   - Quality gates: all repos passing linter + typecheck

4. **Team**
   - 2 people building since 2024
   - Plan: hire 2 engineers at $100k+ AUM

5. **Immediate roadmap**
   - March 20: CeFi live trading
   - April: DeFi live (Elysium)
   - Q2: TradFi + Sports live

---

## Part D: Master index update

### D1 — Update 00-master.html

- Add presentations 10 (DeFi/Elysium), 11 (Analytics), 12 (Financials), 13 (Status Quo)
- Add rehearsal schedule callout: March 13, March 18, March 31
- Add estimated time per deck (next to each link)

---

## Part E: Rehearsal plan

### Rehearsal 1 — Thursday March 13

- Run all 13 presentations end-to-end (~3 hours)
- Goal: timing check (target ≤5 min overview, ≤15 min deep-dive per deck)
- Capture: what's confusing, what's missing, what to cut
- Output: action items list in `unified-trading-pm/rehearsals/rehearsal-1-notes.md`

### Rehearsal 2 — Tuesday March 18

- Run updated presentations after Rehearsal 1 action items applied
- Focus: narrative flow, Q&A preparation
- Prepare: top 10 likely board questions + answers
- Output: `unified-trading-pm/rehearsals/rehearsal-2-notes.md`
- Finalize: which 5–6 decks to present to board (based on audience)

### Board Meeting — March 31

- Select 5–6 decks (recommend: 00-master, 02-backtesting, 05-investment, 08-quality, 12-financials, 13-status-quo)
- Prepare PDF backup: `bash unified-trading-pm/scripts/export-presentations-pdf.sh`
- Print 2 copies per deck (backup if projector fails)

---

## Implementation Order

1. Cross-cutting updates A1–A4 (all 10 existing) — one PR per presentation
2. New presentations 11–13 (one PR)
3. Elysium DeFi (10) — from elysium_defi_presentation plan
4. Master index update (D1)
5. PDF export script
6. Rehearsal 1 (March 13) → apply notes
7. Rehearsal 2 (March 18) → final polish
8. Board meeting (March 31)

---

## Verification Gates

- [ ] All 13 presentations load without JS errors in Chrome
- [ ] Chart.js charts in presentations 05, 12 render with data
- [ ] Playwright tests green for all presentations
- [ ] PDF export working (Playwright headless print) for all 13
- [ ] History slide present in 00-master or 01
- [ ] Financial projections disclaimer visible on slide 12
- [ ] Traction bar present in all 10 existing presentations

## Files Modified / Created

- `unified-trading-pm/presentations/00-master.html` (update)
- `unified-trading-pm/presentations/01-data-provision.html` (update)
- `unified-trading-pm/presentations/02-backtesting-as-a-service.html` (update)
- `unified-trading-pm/presentations/03-strategy-white-labelling.html` (update)
- `unified-trading-pm/presentations/04-execution-as-a-service.html` (update)
- `unified-trading-pm/presentations/05-investment-management.html` (update)
- `unified-trading-pm/presentations/06-regulatory-umbrella.html` (update)
- `unified-trading-pm/presentations/07-autonomous-ai-operations.html` (update)
- `unified-trading-pm/presentations/08-system-quality.html` (update)
- `unified-trading-pm/presentations/09-platform-portal.html` (update)
- `unified-trading-pm/presentations/11-analytics-screening.html` (new)
- `unified-trading-pm/presentations/12-financials-projections.html` (new)
- `unified-trading-pm/presentations/13-status-quo-traction.html` (new)
- `unified-trading-pm/scripts/export-presentations-pdf.sh` (new)
- `unified-trading-pm/rehearsals/` (new directory)

## Dependencies

- `elysium_defi_presentation_2026_03_10.md` (slide 10 content)
- `e2e_smoke_and_portable_backtests.md` (backtest results for slides 02, 12)
- Financial figures: requires owner input for projections (slide 12)

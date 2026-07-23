---
title: platform-strategy-families-and-haruko-gaps
status: active
priority: P0
locked_by: live-defi-rollout
locked_since: 2026-03-28
owner: agent
created: 2026-03-28
# Canonical playbook SSOT: /codex/14-customer-journeys/playbook-concepts/catalogue-strategy.md + cross-cutting/catalogues.md (4-catalogue pattern)

depends_on:
  - ui-sync-hardening
---

# Platform Strategy Families + Haruko Gap Closure

> **Conflict resolution**: Phase 1A (strategy family tabs in service-tabs.tsx) conflicts with tiered_help_chatbot
> (ChatWidget in UnifiedShell) and user_management_merge (ADMIN_TABS in service-tabs.tsx). Execution order for shell
> changes: tiered_help_chatbot → user_management_merge → this plan. This plan adds new pages; ui_walkthrough builds DeFi
> flows on top of them.

## Context

Two parallel threads converge into one plan:

1. **Strategy Families** — Telegram design review (2026-03-28) identified that Trading should be organised by _strategy
   family_ (DeFi, Sports, Options/Futures, Predictions) instead of generic tabs. Each family has its own combo/bundle
   concept:
   - DeFi → Atomic Bundles (multi-step DeFi ops, inherently atomic)
   - Sports → Accumulators (multi-leg bets, all must win)
   - Options/Futures → Combo Builder (spreads, straddles, iron condors)
   - Predictions → Aggregators (cross-market multi-outcome positions)

2. **Haruko Gap Closure** — Feature parity audit against Haruko (institutional digital asset infrastructure). 11
   capabilities missing from Odum: IBOR, Shadow NAV, SAFT, Token Valuation, OTC Trade Capture, Staking, Model
   Portfolios, Derivatives Pricing, What-If Scenarios, Fund Admin, Mobile Alerts.

**Approach**: UI-first (all pages built with mock data), then backend wiring.

**Supersedes**: `plans/ai/ui_top_navigation_ux_refactor_2026_03_20.plan.md` (archive it).

**Complements** (do NOT supersede):

- `multichain_defi_expansion_2026_03_28.plan.md` — DeFi chain support
- `defi_transfers_and_gas_fees_2026_03_27.plan.md` — DeFi gas/transfers
- `sports_batch_pipeline_end_to_end_2026_03_25.plan.md` — Sports data pipeline
- `polymarket_prediction_pipeline_2026_03_25.plan.md` — Prediction pipeline
- `manual_trade_booking_reconciliation_2026_03_22.plan.md` — OTC booking (already done)

## Dependency DAG

```
Phase 1 (PARALLEL) ─── Strategy Family Nav + Combo Builders
Phase 2 (PARALLEL) ─── Haruko Gap UI Pages (IBOR, NAV, Scenarios, etc.)
        ├── QG Gate ──┤
Phase 3 (PARALLEL) ─── Backend Service Wiring
        ├── QG Gate ──┤
Phase 4 (SEQUENTIAL) ─ Integration Testing + Demo Polish
```

## Success Criteria

- All 4 strategy families navigable with family-specific tabs
- Each family has its own combo/bundle builder
- All 11 Haruko-gap UI pages built with realistic mock data
- Mode selector (Live/Paper/Batch) propagates to all new pages
- 122+ existing tests pass, no regressions
- Production build succeeds

---

## Phase 1: Strategy Family Navigation + Combo Builders

### 1A. Trading Nav Restructure — Family-First (PARALLEL)

- [x] [AGENT] P0. Add 4 strategy family tabs to trading vertical nav: DeFi, Sports, Options & Futures, Predictions —
      each as a collapsible group with sub-tabs beneath
- [x] [AGENT] P0. Within each family group, show family-specific sub-tabs: instruments, bundles/combos, positions,
      orders, P&L, alerts, book, accounts — reusing existing widget pages
- [x] [AGENT] P0. Add lock icons on family groups the user doesn't have entitlements for (FOMO visibility)
- [x] [AGENT] P1. Move existing DeFi/Sports/Predictions/Options pages under family groups — update routes or use
      rewrites
- [x] [AGENT] P1. Add "Strategy Family" filter to global scope filters (top bar) alongside org/client/strategy

### 1B. Combo/Bundle Builders (PARALLEL)

- [x] [AGENT] P0. DeFi Atomic Bundle Builder — enhance existing `/services/trading/bundles` page with multi-step DeFi
      ops (swap → approve → flash loan as atomic tx), transaction simulation preview, gas estimation per step
- [x] [AGENT] P0. Sports Accumulator Builder — new component in sports tab: select multiple fixtures, combine legs, show
      accumulator odds (multiply), stake input, payout calculation
- [x] [AGENT] P0. Options Combo Builder — enhance existing options page: strategy templates (spread, straddle, iron
      condor, butterfly), leg editor, payoff diagram, margin requirement
- [x] [AGENT] P1. Predictions Aggregator Builder — new component in predictions tab: combine multiple market positions,
      show aggregate probability, correlation analysis

## Phase 2: Haruko Gap UI Pages (PARALLEL)

### 2A. Post-Trade & Fund Admin

- [x] [AGENT] P0. IBOR Page — `Reports > Book of Records` new tab: golden source positions table with full audit trail,
      trade journal entries, position breaks flagging, daily position snapshots
- [x] [AGENT] P0. Shadow NAV Page — `Reports > NAV` new tab: hourly NAV chart, capital flows table
      (subscriptions/redemptions), fee waterfall (mgmt fee, perf fee, admin), AUM timeline, investor-level breakdown
- [x] [AGENT] P1. Fund Admin Page — `Reports > Fund Admin` new tab: investor register, capital account statements, fee
      calculations, distribution waterfall, fund terms summary
- [x] [AGENT] P1. SAFT Management — `Trading > Accounts > SAFT` new tab: token warrant table with vesting schedules,
      cliff dates, NPV at current price, unlock timeline chart

### 2B. Valuation & Pricing

- [x] [AGENT] P0. Token Valuation Service — `Data > Valuation` new tab: pricing waterfall config (exchange → OTC → model
      → manual), current vs mark price comparison table, stale price alerts, valuation override audit log
- [x] [AGENT] P0. Derivatives Pricing Engine — enhance `Trading > Options`: add pricing model selector (Black-Scholes,
      SVI, SABR, Heston), vol surface 3D chart, model parameter calibration panel, Greeks sensitivity table
- [x] [AGENT] P0. What-If / Scenario Analysis — `Observe > Risk > Scenarios` new tab: scenario builder (market shock
      inputs: BTC -20%, ETH -30%, rates +100bp), portfolio impact table showing P&L delta per position, historical
      scenario replay (COVID crash, FTX, Luna)

### 2C. Operations

- [x] [AGENT] P1. OTC Trade Capture — enhance existing trade booking with OTC-specific fields: counterparty, bilateral
      terms, settlement method, ISDA reference, loan booking
- [x] [AGENT] P1. Staking Dashboard — `Trading > DeFi > Staking` new tab: validator list with performance metrics,
      staking yield chart, reward accrual timeline, unstaking queue, slashing events
- [x] [AGENT] P1. Model Portfolio + Drift — `Trading > Strategies > Model Portfolios` new tab: target allocation pie
      chart, current vs target comparison, drift percentage per asset, rebalance suggestion table, one-click rebalance

### 2D. Alerts & Mobile

- [x] [AGENT] P2. Mobile Alert Settings — `Settings > Notifications` enhance: push notification toggle per alert type,
      mobile device registration, alert delivery channel selector (web / email / push / Telegram)

## Phase 3: Backend Service Wiring

- [ ] [SCRIPT] P0. Map each new UI page to its backend service endpoint — create API contract in unified-trading-api or
      client-reporting-api
- [x] [SCRIPT] P0. Add mock API routes in `lib/api/mock-handler.ts` for all new endpoints
- [ ] [SCRIPT] P1. Create backend service stubs for: NAV calculator (pnl-attribution-service), pricing engine
      (ml-inference-service), IBOR reconciler (execution-service)
- [x] [SCRIPT] P1. Wire Firestore persistence for combo/bundle configurations per user

## Phase 4: Integration & Polish

- [x] [AGENT] P0. Verify all 4 strategy families work end-to-end in mock mode
- [x] [AGENT] P0. Verify mode selector (Live/Paper/Batch) propagates to all new pages with visible data differences
- [x] [AGENT] P0. Run full test suite — 122+ tests must pass. Default-flip 2026-05-06 per master-plan rule "everything's
      been QG'd many times since these plans were made"; CI runs continuously per commit since 2026-03-28.
- [x] [AGENT] P0. Production build must succeed. Default-flip 2026-05-06 per master-plan rule; UI has been deployed
      multiple times since 2026-03-28.
- [x] [AGENT] P1. Update help chatbot decision tree with new pages and navigation
- [x] [AGENT] P1. Update UI-UX-Enhancements.md with completion status

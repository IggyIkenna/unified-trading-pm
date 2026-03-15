---
title: Trading Desk Page + Strategy UI Full Merge
status: complete
created: 2026-03-15
completed: 2026-03-15
repos:
  [
    trading-analytics-ui,
    strategy-ui,
    unified-trading-ui-kit,
    batch-audit-ui,
    client-reporting-ui,
    execution-analytics-ui,
    live-health-monitor-ui,
    logs-dashboard-ui,
    ml-training-ui,
    onboarding-ui,
    settlement-ui,
    unified-trading-pm,
  ]
priority: P0
---

# Trading Desk Page + Strategy UI Full Merge

## Context

Two feature builds across two repos, plus shared infrastructure across all 11 UIs:

1. **Trading Analytics UI** — Full trading desk page + strategy ID dropdown + trigger recon
2. **Strategy UI** — Full merge of execution-analytics pages, reworded for strategy domain
3. **All UIs** — Shared DeploymentPanel (batch + live deploy, start/stop/restart), ApiConnectionBadge, design upgrades
4. **Dev scripts** — Crash fixes (trap handler, staggered spawns, process tree cleanup)

---

## Workstream 1: Trading Desk Page (trading-analytics-ui)

- [x] [AGENT] P0. Create `src/pages/TradingDeskPage.tsx` — manual order entry form (with strategy ID dropdown) + open
      positions table + recent fills table.
- [x] [AGENT] P0. Add "Trigger Reconciliation" button to `src/pages/ReconRunsPage.tsx`
- [x] [AGENT] P0. Update `src/App.tsx` — Trading Desk as default landing page (Crosshair icon)
- [x] [AGENT] P0. Add strategy ID dropdown to TradingDeskPage (8 mock strategies)
- [x] [AGENT] P1. Smoke build: PASS

## Workstream 2: Strategy UI Full Merge (strategy-ui)

- [x] [AGENT] P0. Update `src/App.tsx` — switch from flat items to 4 sectioned nav (Strategies, Backtesting,
      Configuration, Data) + Operations section
- [x] [AGENT] P0. Create `src/pages/RunStrategyBacktest.tsx`
- [x] [AGENT] P0. Create `src/pages/LoadStrategyResults.tsx`
- [x] [AGENT] P0. Create `src/pages/StrategyGridResults.tsx`
- [x] [AGENT] P0. Create `src/pages/StrategyAnalysis.tsx`
- [x] [AGENT] P0. Create `src/pages/StrategyDeepDive.tsx`
- [x] [AGENT] P0. Create `src/pages/StrategyComparison.tsx`
- [x] [AGENT] P0. Create `src/pages/StrategyConfigBrowser.tsx`
- [x] [AGENT] P0. Create `src/pages/StrategyConfigGenerator.tsx`
- [x] [AGENT] P1. Create `src/pages/InstrumentDefinitions.tsx`
- [x] [AGENT] P1. Create `src/pages/InstructionAvailability.tsx`
- [x] [AGENT] P0. Rewrite `src/pages/StrategyLivePage.tsx` — domain filters (CeFi/DeFi/TradFi/Sports), client filter,
      status filter, search, 12 mock strategy cards
- [x] [AGENT] P1. Delete superseded `StrategyBacktestPage.tsx` + remove `/backtest` route
- [x] [AGENT] P1. Smoke build: PASS

## Workstream 3: Shared UI Kit Upgrades (unified-trading-ui-kit)

- [x] [AGENT] P0. Create `ApiConnectionBadge` component — polls /health, shows connected/disconnected/mock
- [x] [AGENT] P0. Create `DeploymentPanel` component — batch + live deploy, start/stop/restart/force-stop, shard
      requirements check, progress bar, deployment history with filters + pagination
- [x] [AGENT] P0. Upgrade `AppHeader` — 36px branded icon container, per-app icon + color, truncated text, rgba colors
- [x] [AGENT] P0. Upgrade `PageLayout` — h-14 header, dark bg, border-b-2, p-6 main content, max-w-[1600px]
- [x] [AGENT] P0. Upgrade `Button` — rounded-md, ring-offset-2, opacity-50, [&_svg]:size-4
- [x] [AGENT] P0. Upgrade `Input` — ring-2, ring-offset-2, hover:border-emphasis
- [x] [AGENT] P0. Upgrade `Card` — shadow-sm, p-5 padding
- [x] [AGENT] P0. Add `Tabs` pill variant via TabsVariantContext
- [x] [AGENT] P0. Add CSS variables (named accent colors) + .log-container utility
- [x] [AGENT] P1. Export TabsVariant type

## Workstream 4: All UIs — Cross-Cutting

- [x] [AGENT] P0. Add ApiConnectionBadge to all 10 UIs (rightSlot)
- [x] [AGENT] P0. Add per-app icons + colors to all 10 UIs
- [x] [AGENT] P0. Remove redundant hardcoded badges from all 10 UIs
- [x] [AGENT] P0. Add DeploymentsPage + Rocket nav item to all 10 UIs (skip deployment-ui)
- [x] [AGENT] P1. Fix client-reporting-ui header (h-14, bg-primary, px-6)

## Workstream 5: Dev Script Crash Fixes (unified-trading-pm)

- [x] [AGENT] P0. Add trap handler (INT/TERM) to dev-start.sh
- [x] [AGENT] P0. Default OPEN_BROWSER=false, add --open flag, stagger opens
- [x] [AGENT] P0. Fix `local` outside function (line 540)
- [x] [AGENT] P0. Stagger process spawns with sleep 1 + progress counter
- [x] [AGENT] P0. Process tree cleanup in dev-stop.sh (pkill -P, port sweep)
- [x] [AGENT] P0. Use npx vite --port directly (not npm run dev) for correct PID tracking
- [x] [AGENT] P0. Port-based fallback in dev-stop.sh and dev-status.sh
- [x] [AGENT] P0. Dev-status.sh: 4 states (RUNNING/DEAD/SKIPPED/NOT STARTED)

## Cleanup

- [x] [AGENT] P1. Delete superseded `strategy-ui/src/pages/StrategyBacktestPage.tsx`
- [x] [AGENT] P1. Remove orphaned `/backtest` route from strategy-ui App.tsx
- [x] [AGENT] P1. All 11 UIs smoke build: PASS
- [x] [AGENT] P1. bash -n syntax check on all 3 dev scripts: PASS

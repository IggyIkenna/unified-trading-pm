---
doc_type: issue
title:
  unified-trading-system-ui's [3.5/6] UI CODEX CHECKS hardcoded-colour check surfaced ~1082 pre-existing hits (554 real,
  528 legitimate) across 100 files on its first-ever run — new tracked cleanup batches
summary: >-
  Follow-up from ui_codex_gate_blind_to_app_router_layout_2026_07_21.md: fixing the base-ui.sh src/-vs-app/ blind spot
  made [3.5/6] run for unified-trading-system-ui for the first time ever, and it surfaced hardcoded hex/rgb colour
  literals (~1082 hits/100 files) and localhost-URL literals (~30 hits/6 files) that had accumulated invisibly.
  Localhost hits and 528/1082 colour hits were genuine design-token/fixture/email-template/dev-fallback exceptions
  (excluded via CODEX_COLOUR_EXCLUDE_GLOBS / CODEX_LOCALHOST_EXCLUDE_GLOBS in scripts/quality-gates.sh, matching
  deployment-ui precedent). The remaining 554 colour hits across 79 files are real ad-hoc UI-styling debt — too large
  and visually risky to blind-fix in one pass (trading/chart/marketing components with no running dev-server/Playwright
  visual QA in this session) — tracked here as batched follow-up todos.
status: open
nature: notes
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer]
tags: [quality-gates, ui, codex-compliance, hardcoded-colours, gate-blind-spot]
related:
  [
    plans/active/issues/ui_codex_gate_blind_to_app_router_layout_2026_07_21.md,
    codex/06-coding-standards/ui-testing-layers.md,
  ]
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [ui_codex_gate_blind_to_app_router_layout-003]
resolved_by:
locked_by:
depends_on: []
---

# Hardcoded-colour + localhost debt surfaced by the app-router gate fix

## What I found

While shipping `ui_codex_gate_blind_to_app_router_layout-003` (console.\*/any-type cleanup), running the now-fixed
`[3.5/6] UI CODEX CHECKS` end-to-end for the first time surfaced two more violation categories that todo's own
"corrected count" never measured (it only scanned for `console.*` and `: any`):

1. **Hardcoded hex/rgb colours**: ~1082 hits across 100 files. Of these, 528 hits/21 files are genuine
   design-token/reference-data/mock-fixture/email-template sources (excluded via `CODEX_COLOUR_EXCLUDE_GLOBS` in
   `scripts/quality-gates.sh` with the same justification pattern as deployment-ui's `src/index.css` exception — see
   that file for the full list + reasoning). The remaining **554 hits across 79 files** are real ad-hoc hex/rgb literals
   in trading/marketing/research/widget component JSX — genuine debt needing a CSS-var or Tailwind-class replacement, or
   (for chart components) routing through the newly-added `lib/chart-theme.ts` tokens.
2. **Localhost URLs**: ~30 hits across 6 files — ALL legitimate on inspection (2 generated/vendored JSON registry files,
   a Firebase Auth-emulator dev connection, 2 `process.env.X || "http://localhost:PORT"` dev-fallback patterns matching
   deployment-ui's own precedent, 1 JSDoc example). Fully excluded via `CODEX_LOCALHOST_EXCLUDE_GLOBS` — no real
   localhost debt remains.

## Why it matters

Same blind-spot mechanism as the parent issue: this repo's `[3.5/6]` gate never ran until the app-router fix landed, so
554 real colour violations accumulated invisibly. `quality-gates.sh` for this repo will FAIL at `[3.5/6]` until these
land — blocking any non-docs quickmerge ship for this repo (including the parent todo's own console/any-type work, which
is otherwise complete and verified).

## Recommended decision

Fix in per-directory batches (same discipline as the archived-plan-debt batching in
`pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md`) — each batch requires a running dev server +
Playwright visual spot-check before/after (per `codex/06-coding-standards/ui-testing-layers.md`), NOT a blind
find-replace, since some of these are chart-library colour props that may need `chart-theme.ts`'s `CHART_COLORS` array
rather than a single CSS var.

## Todos

- [ ] [UI] P2. Batch 1 — chart/research components (16 files, 3–19 hits each):
      `components/research/equity-chart-with-layers.tsx`, `components/research/signal-overlay-chart.tsx`,
      `components/research/execution/execution-detail-view.tsx`, `components/research/execution/status-helpers.tsx`,
      `components/research/overlaid-equity-curves.tsx`, `components/research/profit-structure-chart.tsx`,
      `components/research/win-loss-donut.tsx`, `components/trading/candlestick-chart.tsx`,
      `components/trading/vol-surface-chart.tsx`, `components/strategy-catalogue/PerformanceOverlay.tsx`,
      `components/paper-trading/coin-price-chart.tsx`, `components/reports/performance-dashboard.tsx`,
      `components/reports/portfolio-analytics.tsx`, `components/risk/correlation-heatmap.tsx`,
      `components/events/economic-heatmap.tsx`, `components/events/economic-grid.tsx`. Most are recharts-based — check
      whether `lib/chart-theme.ts`'s `CHART_COLORS`/`TOOLTIP_STYLE`/`GRID_STYLE`/`AXIS_STYLE` already cover the literal
      in question before inventing a new CSS var. (repo: unified-trading-system-ui)
- [ ] [UI] P2. Batch 2 — widgets/\_primitives + widgets/\* (11 files, 1–8 hits each):
      `components/widgets/_primitives/metric-gauge.tsx`, `components/widgets/_primitives/flow-chart.tsx`,
      `components/widgets/_primitives/categorical-matrix.tsx`, `components/widgets/_primitives/depth-area-chart.tsx`,
      `components/widgets/_primitives/continuous-heatmap.tsx`, `components/widgets/pnl/pnl-data-context.tsx`,
      `components/widgets/alerts/severity-breakdown-widget.tsx`,
      `components/widgets/terminal/use-terminal-page-data.ts`,
      `components/widgets/strategies/strategies-catalogue-widget.tsx`,
      `components/widgets/cefi/volume-dominance-widget.tsx`, `components/widgets/workspace-toolbar.tsx`. The
      `_primitives/` chart files are the most likely `chart-theme.ts` candidates (they're the shared chart-primitive
      layer every other chart widget builds on). (repo: unified-trading-system-ui)
- [ ] [UI] P3. Batch 3 — trading/sports (10 files, 1–27 hits each):
      `components/trading/sports/fixtures-detail-panel.tsx`, `components/trading/sports/arb-grid.tsx`,
      `components/trading/sports/shared.tsx`, `components/trading/sports/my-bets-tab.tsx`,
      `components/trading/sports/fixtures-match-card.tsx`, `components/trading/sports/arb-stream.tsx`,
      `components/trading/sports/arb-tab.tsx`, `components/trading/sports/fixtures-tab.tsx`,
      `components/trading/sports/bet-slip.tsx`, `components/widgets/sports/sports-widgets.md` (a markdown doc — check if
      the hex mentions are prose/examples, not code, before touching). `shared.tsx` likely defines a per-outcome colour
      map shared by the other 9 — fix it first, other files may just import from it. (repo: unified-trading-system-ui)
- [ ] [UI] P3. Batch 4 — trading (non-sports) + predictions (14 files, 1–21 hits each):
      `components/shared/status-badge.tsx`, `components/trading/strategy-audit-trail.tsx`,
      `components/trading/strategy-filter-bar.tsx`, `components/trading/alerts-feed.tsx`,
      `components/trading/limit-bar.tsx`, `components/trading/dimensional-grid.tsx`, `components/trading/kpi-card.tsx`,
      `components/trading/context-bar/trading-context-bar.tsx`,
      `components/trading/options-futures/vol-greeks-panels.tsx`, `components/trading/predictions/arb-stream-tab.tsx`,
      `components/trading/predictions/odum-focus-tab.tsx`, `components/trading/predictions/markets-tab.tsx`,
      `components/shell/asset-group-pill.tsx`, `components/shell/lifecycle-nav.tsx`. (repo: unified-trading-system-ui)
- [ ] [UI] P3. Batch 5 — marketing + platform pages + misc (28 files, 1–32 hits each): `app/(public)/_home-client.tsx`,
      `components/marketing/market-galaxy.tsx`, `components/marketing/arbitrage-galaxy.tsx`,
      `components/marketing/galaxy-canvas.tsx`, `components/marketing/strategy-family-catalogue.tsx`,
      `components/marketing/platform-architecture-grid.tsx`, `components/marketing/operating-model-stages.tsx`,
      `app/(public)/services/investment/page.tsx`,
      `app/(platform)/investor-relations/board-presentation/components/board-presentation-slide-part-a.tsx`,
      `app/(platform)/services/trading/strategies/[id]/components/strategy-detail-tab-panels.tsx`,
      `app/(platform)/services/trading/strategies/[id]/strategy-detail-page-client.tsx`,
      `app/(platform)/paper-trading/page.tsx`, `app/(platform)/paper-trading/coin/[coin]/page.tsx`,
      `app/(platform)/services/research/strategy/heatmap/page.tsx`,
      `app/(platform)/services/research/ml/components/run-analysis-compare-panel.tsx`, `app/opengraph-image.tsx`,
      `app/layout.tsx`, `app/(ops)/seed-demo/page.tsx`, `lib/api/mock-handler.ts` (11 hits — dev-only mock infra, check
      if these are legit fixture data like the already-excluded mock fixtures, or real UI styling literals, before
      fixing), `lib/config/services/pnl.config.ts`, `lib/config/services/strategies.config.ts`,
      `lib/dashboards/executive/executive-dashboard-data.ts` (path: `components/dashboards/executive/`),
      `components/promote/paper-trading-ledger-panels.tsx`, `components/ops/venue-connectivity.tsx`,
      `components/staging-gate.tsx`, `components/briefings/strategy-coverage-matrix.tsx`,
      `components/research/strategies/strategy-detail-panel.tsx`, `components/cockpit/cockpit-widget-grid.tsx`. (repo:
      unified-trading-system-ui)

## Codex SSOTs

`codex/06-coding-standards/ui-testing-layers.md`, `codex/06-coding-standards/quality-gates.md`.

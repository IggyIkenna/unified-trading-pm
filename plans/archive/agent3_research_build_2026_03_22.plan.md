---
doc_type: plan
title: agent3-research-build
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-22'
overview: Ensure Research/Build and Promote services have real content, absorb strategy-ui wizard and ml-training-ui experiment tracking
todos:
- {id: a3-p0-research-overview, content: '- [x] [AGENT] P0. Verify `/services/research/overview` has real content (not placeholder). It should show: active experiments count, model registry status, backtest queue, recent results. Wire to API hooks: `GET /ml/models` (model count), `GET /execution/backtests` (recent backtests). If placeholder, build a dashboard with KPI cards for each research domain (ML, Strategy, Execution).

    ', status: done}
- {id: a3-p0-ml-overview, content: '- [x] [AGENT] P0. Verify `/services/research/ml/overview` has real content. Should show: model registry summary, training status, recent experiments, feature drift. Wire to `GET /ml/models`, `GET /ml/experiments`, `GET /ml/training-status` API endpoints.

    ', status: done}
- {id: a3-p0-ml-experiments, content: '- [x] [AGENT] P0. Verify `/services/research/ml/experiments` has a real experiments table: experiment_id, model_type, status (running/completed/failed), metrics (sharpe, accuracy), created_at. Wire to `GET /ml/experiments` API. Verify `/services/research/ml/experiments/[id]` shows experiment detail with training curves (loss over epochs), hyperparameters, comparison to baseline.

    ', status: done}
- {id: a3-p0-ml-training, content: '- [x] [AGENT] P1. Verify `/services/research/ml/training` has: trigger training button, training queue, active jobs with progress. Wire to `GET /ml/training-jobs` and `POST /ml/training-jobs` APIs. In mock mode, POST should add a job to MockStateStore with status "queued".

    ', status: done}
- {id: a3-p0-ml-features, content: '- [x] [AGENT] P1. Verify `/services/research/ml/features` has: feature list with importance scores, correlation matrix, drift monitoring. Wire to `GET /ml/features` API.

    ', status: done}
- {id: a3-p0-ml-validation, content: '- [x] [AGENT] P1. Verify `/services/research/ml/validation` has: out-of-sample test results, signal quality metrics, walk-forward analysis. Wire to `GET /ml/validation-results` API.

    ', status: done}
- {id: a3-p0-ml-registry, content: '- [x] [AGENT] P1. Verify `/services/research/ml/registry` has: model version list with promote/deprecate actions, model comparison, A/B test setup. Wire to `GET /ml/models` and `POST /ml/models/{id}/promote` APIs.

    ', status: done}
- {id: a3-p0-ml-remaining, content: '- [x] [AGENT] P2. Verify remaining ML sub-tabs have content: `/services/research/ml/monitoring` (live model performance), `/services/research/ml/deploy` (deployment status), `/services/research/ml/governance` (model governance, approval workflows), `/services/research/ml/config` (ML pipeline configuration).

    ', status: done}
- {id: a3-p1-strategy-backtests, content: '- [x] [AGENT] P0. Verify `/services/research/strategy/backtests` has: backtest runs table with status, sharpe, drawdown, total return, trades count. Wire to `GET /execution/backtests` API. Add "New Backtest" button that opens a configuration modal/drawer.

    ', status: done}
- {id: a3-p1-strategy-compare, content: '- [x] [AGENT] P1. Verify `/services/research/strategy/compare` has: side-by-side comparison of 2+ backtests, equity curves overlay, risk metrics comparison. Wire to API.

    ', status: done}
- {id: a3-p1-strategy-results, content: '- [x] [AGENT] P1. Verify `/services/research/strategy/results` has: detailed backtest results with trade log, equity curve, drawdown chart, monthly returns heatmap.

    ', status: done}
- {id: a3-p1-strategy-heatmap, content: '- [x] [AGENT] P1. Verify `/services/research/strategy/heatmap` has: parameter sweep heatmap showing sharpe/return across parameter combinations.

    ', status: done}
- {id: a3-p2-absorb-strategy-wizard, content: '- [x] [AGENT] P1. Extract the multi-step strategy creation wizard from `strategy-ui/src/components/wizard/` (WizardShell, BasicConfigStep, StrategySelectionStep, InstitutionalShareClassStep, ReviewStep) and adapt it as a modal/drawer in the main UI. Trigger from "New Strategy" button on the backtests page. Adapt to use unified-trading-api endpoints and the main UI''s component library (shadcn/ui, not whatever strategy-ui uses). Key features to preserve: CSV parameter upload (via papaparse), multi-step flow with validation.

    ', status: done}
- {id: a3-p3-absorb-ml-training, content: '- [x] [AGENT] P1. Review `ml-training-ui/src/` for any experiment tracking UI patterns not already in the main UI''s ML sub-tabs. Key things to look for: training curve visualization (loss/metrics over epochs), hyperparameter display, model artifact download links, experiment comparison views. Absorb any missing patterns into the corresponding ML sub-tab pages.

    ', status: done}
- {id: a3-p4-promote-candidates, content: '- [x] [AGENT] P0. Verify `/services/research/strategy/candidates` shows a review queue of strategies pending promotion. Each candidate should show: name, backtest metrics, risk assessment, approval status. Add approve/reject buttons that call `POST /analytics/strategies/{id}/promote` and `POST /analytics/strategies/{id}/reject` APIs. In mock mode, these update MockStateStore.

    ', status: done}
- {id: a3-p4-promote-handoff, content: '- [x] [AGENT] P1. Verify `/services/research/strategy/handoff` shows the handoff tracking page: which strategies have been promoted from research to live, when, by whom, with what risk limits.

    ', status: done}
- {id: a3-p5-execution-research, content: '- [x] [AGENT] P1. Verify execution research pages have content: `/services/execution/algos` (algo comparison: TWAP, VWAP, IS, Sniper), `/services/execution/venues` (venue connectivity, latency, fill rates), `/services/execution/benchmarks` (benchmark definitions and results), `/services/execution/tca` (transaction cost analysis). Wire all to API.

    ', status: done}
- {id: a3-p5b-skeleton-loading, content: '- [x] [AGENT] P1. Ensure ALL research and promote pages use skeleton loading states (not "Loading..." text) while API data loads. Use the skeleton components created by Agent 1 (table-skeleton, card-grid-skeleton, chart-skeleton). Every page that calls a `useQuery` hook must show a shimmer placeholder during `isLoading`. This is mandatory per CITADEL_VISION visual polish standards. Key pages: Research Hub (card grid skeleton), ML Experiments (table skeleton), Backtest Results (chart + table skeleton), Promote Review Queue (table skeleton).

    ', status: done}
- {id: a3-p6-tests, content: '- [x] [AGENT] P1. Add Playwright tests: 1) Navigate to Research Hub → verify KPI cards render. 2) Navigate to ML Models → verify model list renders. 3) Navigate to Backtests → verify backtest table renders. 4) Click "New Strategy" → verify wizard modal opens. 5) Navigate to Promote > Review Queue → verify candidate list renders.

    ', status: done}
- {id: a3-p7-error-states, content: "- [x] [AGENT] P1. Add error and empty states to ALL research and promote pages:\n  1. Every page using useQuery: add `if (isError) return <ApiError error={error} onRetry={refetch} />` (component created by Agent 1)\n  2. ML Experiments table: `if (experiments.length === 0) return <EmptyState title=\"No experiments\" description=\"Start your first ML experiment\" action={{ label: \"New Experiment\", onClick: ... }} />`\n  3. Backtest table: `if (backtests.length === 0) return <EmptyState title=\"No backtests\" description=\"Run your first backtest\" action={{ label: \"New Backtest\", onClick: ... }} />`\n  4. Promote Review Queue: `if (candidates.length === 0) return <EmptyState title=\"No candidates\" description=\"All strategies have been reviewed\" />`\n  5. Every chart: if data is empty, show chart-skeleton with \"No data available\" overlay\n", status: done}
- {id: a3-p7-export, content: "- [x] [AGENT] P1. Add split \"Export\" button (CSV + Excel) to: ML Experiments, Backtest Results, Feature list tables. Use `exportTableToCsv()` and `exportTableToXlsx()` from `lib/utils/export.ts` (created by Agent 2). Button: `[Export ▾]` → \"CSV\" / \"Excel\".\n  DEPENDENCY: Agent 2 must create `lib/utils/export.ts` first (a2-p7-export-tables). — UNBLOCKED and adopted.\n", status: done}
- {id: a3-p7-dynamic-imports, content: '- [x] [AGENT] P1. Use Next.js `dynamic(() => import(...), { ssr: false })` for heavy chart components in research pages: equity curve charts, training loss curves, parameter sweep heatmaps, feature correlation matrices. These use browser-only APIs and should not be server-rendered.

    ', status: done}
- {id: a3-p7-adopt-datatable, content: "- [x] [AGENT] P0. Replace shadcn `<Table>` with `DataTable` from `components/ui/data-table.tsx` (Agent 1) for ALL research tables: ML Experiments, Backtest Results, Feature list, Strategy Candidates. Tables must handle 50+ strategies from expanded seed data.\n  DEPENDENCY: Agent 1 must create DataTable (a1-p6-tanstack-table). — UNBLOCKED and adopted.\n", status: done}
isProject: false
---

# Notes & Context

## CRITICAL: Read Before Any Work

1. Read `unified-trading-system-ui/UI_STRUCTURE_MANIFEST.json` — SSOT for all page states, routes, and source files
2. Read `unified-trading-pm/plans/archive/CITADEL_VISION_2026_03_22.md` — system-wide vision

## TABS-ONLY RULE

- Research service = ONE page with tabs. ML has sub-tabs. Strategies have sub-tabs.
- Promote service = ONE page with tabs.
- NO card-based sub-pages. Wizard and creation flows are MODALS/DRAWERS within tabs.

## Page Status — NO stubs, but 12 pages need API wiring

All pages are REAL (252-704L). The problem is inline mock data. See manifest for per-page hooks status.

## Satellite Absorption (as modals within tabs, NOT new pages)

| Source                                | Lines       | Target         | How                           |
| ------------------------------------- | ----------- | -------------- | ----------------------------- |
| `strategy-ui/src/components/wizard/*` | ~709L total | Strategies tab | "New Strategy" button → modal |
| `ml-training-ui/*`                    | —           | NOT NEEDED     | Main UI pages are richer      |

## Key source repos for absorption

- `strategy-ui/src/components/wizard/` — WizardContainer (148L), BasicConfigStep (192L), StrategySelectionStep (219L),
  ReviewStep (150L)
- `strategy-ui/src/components/results/EquityCurveChart.tsx` (146L) — reusable chart component
- `ml-training-ui/src/` — SKIP: main UI already has richer equivalents (591-704L vs 133-315L)

## Separation of Concerns (CRITICAL — No Inline Mock Data)

Research pages are the worst offenders for inline mock data. The principle: if a page has `const mockData = [...]` or
imports from `lib/ml-mock-data.ts` or `lib/strategy-platform-mock-data.ts`, it's WRONG. ALL data comes from the API.

- ML model list: `GET /ml/models` — not hardcoded in the page
- Experiment metrics: `GET /ml/experiments` — not inline arrays
- Backtest results: `GET /execution/backtests` — not imported from a mock file
- Strategy configs for wizard: `GET /analytics/strategy-configs` — not from `strategy-registry.ts`

**The curl test:** `curl /ml/experiments` must return experiment data. If Agent 5 hasn't added the endpoint yet, wire
the hook anyway — the page shows an error state (from Agent 1's `<ApiError>`) until the endpoint is ready. That's
correct. Don't paper over missing API endpoints with inline mock data.

The "New Strategy" wizard reads its strategy archetype list from `GET /analytics/strategy-configs` — the 50+ config
entries seeded by Agent 6. The wizard does NOT define its own archetype list.

## Risk Factors & Mitigations

**RISK 1: "Verify" becomes superficial — agent checks page loads but doesn't fix inline mock data.** 12 research pages
use inline mock data. Agent can "verify it renders" and move on, leaving page disconnected. MITIGATION: For every
"verify" todo, check if page imports from hooks/api/use-\*.ts (GOOD) or uses hardcoded data (BAD). If hardcoded: wire to
API hook. Do NOT mark verify as done if inline mock remains.

**RISK 2: strategy-ui wizard uses different component library.** Built with Vite + potentially MUI or custom components.
Direct import will fail. MITIGATION: Extract the FLOW (step sequence, validation, fields) not the components. Rebuild
with shadcn/ui (Dialog, Form with zod, Input/Select/Textarea). Keep CSV upload via papaparse.

**RISK 3: ML sub-tabs are 12 pages deep — easy to lose track.** MITIGATION: Work through ALL ML sub-tabs in Phase 0
before moving to strategies. Check off each explicitly.

**RISK 4: API endpoints may not exist yet (Agent 5 dependency).** GET /ml/experiments, POST /ml/training-jobs may not be
implemented when Agent 3 starts. MITIGATION: Wire hooks to correct paths NOW. If API returns 404, page shows error state
(from Agent 1). When Agent 5 adds endpoints, pages work automatically. Don't skip wiring because endpoint doesn't exist.

## API endpoints needed

- GET /ml/models, GET /ml/experiments, GET /ml/training-jobs, GET /ml/features
- GET /ml/validation-results, POST /ml/training-jobs, POST /ml/models/{id}/promote
- GET /execution/backtests, POST /execution/backtests
- POST /analytics/strategies/{id}/promote, POST /analytics/strategies/{id}/reject

## New scope (added 2026-03-22 gap analysis)

- Error states and empty states are mandatory — every table/chart must handle isError and empty data
- CSV export on data tables
- Dynamic imports for chart components (SSR incompatible)
- These close the gap between "pages render" and "pages feel production-grade"

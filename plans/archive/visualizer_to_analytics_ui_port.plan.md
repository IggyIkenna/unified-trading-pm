---
doc_type: plan
title: Visualizer to Analytics UI Port
summary: Port execution-analytics-ui functionality into execution-analytics-ui to achieve 100% audit grade, alignment with
  PM plans and codex, and full integration with execution-results-api and execution-service domain data.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-05'
todos:
- {id: infra-setup, content: 'Add infrastructure dependencies to execution-analytics-ui: axios, @tanstack/react-query, zustand, recharts, tailwind css, postcss. Configure Vite proxy /api → http://localhost:8002. Add @/ path alias. Configure authApiClient (axios + auth interceptor). Add api/types.ts aligned with execution-results-api schemas (ResultSummary, ResultsResponse, ExecutionAlpha). Fix GridResult → ResultSummary schema mismatch.', status: completed}
- {id: p0-pages, content: 'Port P0 core analytics pages from execution-analytics-ui: (1) LoadResults — browse GCS/local results, bucket/prefix selection; uses /results, /results/buckets, /results/prefixes endpoints; (2) Analysis — alpha histogram, equity curve; uses /results, /results/execution_alpha; (3) DeepDive — per-result fills/orders/timeline tabs; (4) AlgorithmComparison — compare algorithms with bar/radar charts. Port Zustand stores (resultsStore, filterStore) and React Query hooks.', status: completed}
- {id: p1-run-backtest, content: 'Port P1 RunBacktest page: single/batch backtest execution, job status polling. Uses /backtest/run, /backtest/batch, /backtest/status/{job_id}, /config/sources, /config/system/cores endpoints.', status: completed}
- {id: p2-domain-browsing, content: 'Port P2 domain data browsing pages: InstrumentDefinitions (/data/instruments), InstructionAvailability (/data/strategies, /data/instructions), ConfigBrowser (/data/configs), ConfigGenerator (stub — returns 501, defer or scaffold).', status: completed}
- {id: p3-market-data, content: 'Port P3 MarketTickData page from execution-analytics-ui: browse and chart tick data via market-data-api (/data/tick-data, /data/tick-data/instruments, /data/tick-data/ticks, port 8003).', status: completed}
- {id: quality-gates, content: 'Ensure TypeScript quality gates pass: Vitest unit tests, ESLint, Prettier. Add Playwright smoke tests for LoadResults, Analysis, DeepDive pages. Verify no Python in repo (ui-no-python-quality-gates.mdc). Auth: all API calls pass Bearer token via axios interceptor using @unified-trading/ui-auth authContext.', status: completed}
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Port execution-analytics-ui to execution-analytics-ui for 100% Audit Grade

## Context

**Canonical target:** [execution-analytics-ui](execution-analytics-ui/) is the designated UI for execution backtest
(TCA, alpha, fill analysis, execution quality) per
[RUNTIME_TOPOLOGY_DECISIONS.md](deployment-service/configs/RUNTIME_TOPOLOGY_DECISIONS.md) (lines 59–65). Content
migration from `execution-service/visualizer-ui/` into this repo is tracked as `arch-exec-services-visualizer-extract`.

**Current state:**

- **execution-analytics-ui:** 2 pages (Login, GridResults), auth via `@unified-trading/ui-auth`, single
  `GET /api/v1/results` with schema mismatch
- **execution-analytics-ui:** 11 pages, full execution-results-api integration, no auth
- **execution-results-api:** Full API (results, analysis, backtest, config, data, fills SSE)
- **execution-service:** Produces domain data (summary.json, execution_alpha.json, orders/fills/equity parquet) to GCS;
  execution-results-api reads it

**Audit requirements** (trading-system-audit-prompt, ui-service-separation):

- UI in own repo (done)
- TypeScript quality gates only
- Integration with execution-results-api (8002) + market-data-api (8003)
- Domain data from execution-service (via GCS → execution-results-api)

---

## Functionality to Port (Prioritized)

### P0 — Core Analytics (Required for TCA + Alpha + Execution Quality)

| Page                    | Source                                                                              | Purpose                                                          | execution-results-api Endpoints                                                                    |
| ----------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **LoadResults**         | [LoadResults.tsx](execution-analytics-ui/src/pages/LoadResults.tsx)                 | Browse GCS/local results, bucket/prefix selection, list results  | `/results`, `/results/buckets`, `/results/prefixes`, `/results/local-default-directory`, `/health` |
| **Analysis**            | [Analysis.tsx](execution-analytics-ui/src/pages/Analysis.tsx)                       | Alpha distribution histogram, execution alpha bars, equity curve | `/results`, `/results/execution_alpha`                                                             |
| **DeepDive**            | [DeepDive.tsx](execution-analytics-ui/src/pages/DeepDive.tsx)                       | Per-result alpha, fills, orders, timeline tabs                   | `/results/{id}`, `/results/execution_alpha`                                                        |
| **AlgorithmComparison** | [AlgorithmComparison.tsx](execution-analytics-ui/src/pages/AlgorithmComparison.tsx) | Compare algorithms (bar/radar charts)                            | `/results`, `/results/execution_alpha`                                                             |

### P1 — Execution Backtest Management

| Page            | Source                                                              | Purpose                                | execution-results-api Endpoints                                                                            |
| --------------- | ------------------------------------------------------------------- | -------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **RunBacktest** | [RunBacktest.tsx](execution-analytics-ui/src/pages/RunBacktest.tsx) | Run single/batch backtests, job status | `/backtest/run`, `/backtest/batch`, `/backtest/status/{job_id}`, `/config/sources`, `/config/system/cores` |

### P2 — Domain Data Browsing (execution-service domain)

| Page                        | Source                                                                                      | Purpose                                           | execution-results-api Endpoints                                    |
| --------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------ |
| **InstrumentDefinitions**   | [InstrumentDefinitions.tsx](execution-analytics-ui/src/pages/InstrumentDefinitions.tsx)     | Browse instruments (UDC via execution-service)    | `/data/instruments`, `/data/instruments/data`                      |
| **InstructionAvailability** | [InstructionAvailability.tsx](execution-analytics-ui/src/pages/InstructionAvailability.tsx) | Browse strategy instructions                      | `/data/strategies`, `/data/instructions`                           |
| **ConfigBrowser**           | [ConfigBrowser.tsx](execution-analytics-ui/src/pages/ConfigBrowser.tsx)                     | Browse and validate configs                       | `/data/configs`, `/data/configs/content`, `/data/configs/validate` |
| **ConfigGenerator**         | [ConfigGenerator.tsx](execution-analytics-ui/src/pages/ConfigGenerator.tsx)                 | Generate configs (API returns 501; stub or defer) | `/config/generate`, `/config/generate-all`                         |

### P3 — Market Data (market-data-api)

| Page               | Source                                                                    | Purpose                    | API                                                                       |
| ------------------ | ------------------------------------------------------------------------- | -------------------------- | ------------------------------------------------------------------------- |
| **MarketTickData** | [MarketTickData.tsx](execution-analytics-ui/src/pages/MarketTickData.tsx) | Browse and chart tick data | `/data/tick-data`, `/data/tick-data/instruments`, `/data/tick-data/ticks` |

---

## Infrastructure to Port

| Component          | Source                                         | Notes                                                                                               |
| ------------------ | ---------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| **API client**     | `execution-analytics-ui/src/api/client.ts`     | Axios base URL; adapt for `authFetchJson` or Bearer token from `@unified-trading/ui-auth`           |
| **API types**      | `execution-analytics-ui/src/api/types.ts`      | `ResultSummary`, `ExecutionAlpha`, `FilterOptions`, etc. — align with execution-results-api schemas |
| **Zustand stores** | `resultsStore.ts`, `filterStore.ts`            | Results list, filters (category, asset, strategy, mode, timeframe, algorithm)                       |
| **React Query**    | `@tanstack/react-query`                        | Server state, caching for buckets, results, execution_alpha, job status                             |
| **Recharts**       | BarChart, ComposedChart, AreaChart, RadarChart | Alpha distribution, equity, fills, algorithm comparison                                             |
| **Tailwind CSS**   | tailwind.config, PostCSS                       | Styling                                                                                             |
| **Path alias**     | `@/` → `./src`                                 | Vite config                                                                                         |
| **Vite proxy**     | `/api` → `http://localhost:8002`               | execution-results-api port 8002                                                                     |

---

## Schema Alignment

**Current mismatch:** execution-analytics-ui `GridResult` expects
`{ run_id, cell_id, sharpe, calmar, total_return_pct, max_drawdown_pct, is_best_cell }`; execution-results-api returns
`{ results: ResultSummary[], total, filters }` with `sharpe_ratio`, `pnl`, `net_alpha_bps`, etc.

**Action:** Replace `GridResult` with `ResultSummary` (and `ResultsResponse`) from execution-results-api. Map
`sharpe_ratio` → `sharpe`; add derived fields (`calmar`, `max_drawdown_pct`, `total_return_pct`) if
execution-results-api or analysis endpoints provide them, or compute client-side from equity/summary.

---

## Auth Integration

**Keep:** `@unified-trading/ui-auth` (Google OAuth, `RequireAuth`, `authFetchJson`).

**Adapt:** All API calls must pass auth. Options:

1. Wrap axios client with interceptor that adds `Authorization: Bearer <token>` from auth context
2. Use `authFetchJson` for each call (less DRY)
3. Create `authApiClient` that wraps axios and injects token

**Recommendation:** Option 1 — single axios instance with auth interceptor; reuse for all execution-results-api calls.

---

## Deployment API (Optional)

execution-analytics-ui uses `deployment-dashboard` (Cloud Run) for mass cloud deploy (`/api/deployments`,
`/api/service-status/execution-services/`\*). For RunBacktest mass deploy, execution-analytics-ui may need this. Defer
to P1 completion; add if RunBacktest mass-deploy is required for audit.

---

## Quality Gates and Cursor Rules

- **UI-service separation:** No Python in UI repo — already satisfied
- **TypeScript quality gates:** Vitest, ESLint, Prettier (per
  [ui-no-python-quality-gates.mdc](../../../.cursor/rules/ui/ui-no-python-quality-gates.mdc))
- **execution-analytics-ui** → execution-results-api (8002) + market-data-api (8003) — per topology

---

## Data Flow (Post-Port)

```mermaid
flowchart TB
    subgraph UI [execution-analytics-ui]
        Auth[ui-auth OAuth]
        LoadResults[LoadResults]
        Analysis[Analysis]
        DeepDive[DeepDive]
        Compare[AlgorithmComparison]
        RunBacktest[RunBacktest]
    end

    subgraph API [execution-results-api :8002]
        Results[/results]
        Alpha[/results/execution_alpha]
        Backtest[/backtest/run]
        Data[/data/instruments etc]
    end

    subgraph GCS [GCS execution-store]
        Summary[summary.json]
        ExecAlpha[execution_alpha.json]
        Parquet[orders fills equity]
    end

    subgraph Svc [execution-service]
        CLI[CLI backtest]
    end

    Auth -->|Bearer token| LoadResults
    Auth -->|Bearer token| Analysis
    Auth -->|Bearer token| DeepDive
    Auth -->|Bearer token| Compare
    Auth -->|Bearer token| RunBacktest

    LoadResults --> Results
    Analysis --> Results
    Analysis --> Alpha
    DeepDive --> Results
    DeepDive --> Alpha
    Compare --> Results
    Compare --> Alpha
    RunBacktest --> Backtest

    Results --> GCS
    Alpha --> GCS
    Backtest -->|subprocess| CLI
    CLI --> GCS
    Data --> GCS
```

---

## Implementation Order

1. **Infrastructure:** Add axios, React Query, Zustand, Recharts, Tailwind; API client with auth; Vite proxy; path alias
2. **Schema:** Add `api/types.ts` aligned with execution-results-api; fix GridResults → ResultSummary
3. **P0 pages:** LoadResults → Analysis → DeepDive → AlgorithmComparison (in that order; Analysis/DeepDive/Compare
   depend on LoadResults store)
4. **P1:** RunBacktest
5. **P2:** InstrumentDefinitions, InstructionAvailability, ConfigBrowser; ConfigGenerator (stub if 501)
6. **P3:** MarketTickData (if market-data-api integration required)
7. **Quality gates:** Ensure Vitest, ESLint, Prettier pass; add smoke tests (Playwright) for LoadResults, Analysis,
   DeepDive

---

## Out of Scope

- **execution-analytics-ui repo:** After port, deprecate or archive; execution-analytics-ui becomes single source
- **execution-service/visualizer-ui:** Extraction tracked separately; this plan ports from execution-analytics-ui
  (already extracted) into execution-analytics-ui

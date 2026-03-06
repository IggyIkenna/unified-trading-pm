# UI Audit Results — Full Service Repo Scan

**Date:** 2026-03-06
**Auditor:** arch-ui-audit-full task (Phase 1, Stream B)
**Task:** Scan all service repos for embedded UI artifacts

## Summary

- **19 repos CLEAN** — no embedded UI artifacts
- **2 repos with VIOLATIONS** — embedded UI/frontend code found
- **1 repo with REMNANT** — empty package-lock.json (no actual UI code)

## Results Table

| Repo                              | Status            | Violations Found                                                                                                                                                                     |
| --------------------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| alerting-service                  | CLEAN             | htmlcov/index.html only (coverage report, not embedded UI)                                                                                                                           |
| market-data-processing-service    | CLEAN             | htmlcov/index.html only (coverage report, not embedded UI)                                                                                                                           |
| client-reporting-api              | CLEAN             | None                                                                                                                                                                                 |
| risk-and-exposure-service         | CLEAN             | None                                                                                                                                                                                 |
| execution-service                 | CLEAN             | visualizer-ui/ and visualizer-api/ previously extracted to archive/execution-visualizer-ui; only package-lock.json remnant (empty packages: {}) remains                              |
| instruments-service               | CLEAN             | htmlcov/index.html only (coverage report, not embedded UI)                                                                                                                           |
| market-tick-data-service          | PARTIAL VIOLATION | `package.json` at repo root (declares `tardis-dev` JS dependency); no tsx/jsx files, no frontend dir                                                                                 |
| ml-training-service               | CLEAN             | None                                                                                                                                                                                 |
| ml-inference-service              | CLEAN             | None                                                                                                                                                                                 |
| strategy-service                  | VIOLATION         | `frontend/` directory with full React/TypeScript app: index.html, package.json, tailwind.config.js, vite.config.ts, 16 .tsx component files (wizard, results, live dashboard panels) |
| features-calendar-service         | CLEAN             | None                                                                                                                                                                                 |
| features-delta-one-service        | CLEAN             | htmlcov/index.html only (coverage report, not embedded UI)                                                                                                                           |
| features-multi-timeframe-service  | CLEAN             | None                                                                                                                                                                                 |
| features-cross-instrument-service | CLEAN             | None                                                                                                                                                                                 |
| features-volatility-service       | CLEAN             | None                                                                                                                                                                                 |
| features-onchain-service          | CLEAN             | None                                                                                                                                                                                 |
| features-sports-service           | CLEAN             | None                                                                                                                                                                                 |
| pnl-attribution-service           | CLEAN             | htmlcov/index.html only (coverage report, not embedded UI)                                                                                                                           |
| position-balance-monitor-service  | CLEAN             | None                                                                                                                                                                                 |
| deployment-service                | CLEAN             | None                                                                                                                                                                                 |
| deployment-api                    | CLEAN             | None                                                                                                                                                                                 |

## Violation Details

### strategy-service — VIOLATION (full embedded React app)

**Directory:** `strategy-service/frontend/`

**Files found:**

- `frontend/index.html` — Vite entrypoint
- `frontend/index.live.html` — Live trading HTML entrypoint
- `frontend/package.json` — Node dependencies (vite, react, tailwindcss, recharts, etc.)
- `frontend/tailwind.config.js`
- `frontend/vite.config.ts`
- `frontend/vite.config.live.ts`
- `frontend/src/components/ui/InstitutionalCardKit.tsx`
- `frontend/src/components/wizard/ReviewStep.tsx`
- `frontend/src/components/wizard/WizardShell.tsx`
- `frontend/src/components/wizard/InstitutionalShareClassStep.tsx`
- `frontend/src/components/wizard/StrategySelectionStep.tsx`
- `frontend/src/components/wizard/BasicConfigStep.tsx`
- `frontend/src/components/wizard/WizardContainer.tsx`
- `frontend/src/components/results/EquityCurveChart.tsx`
- `frontend/src/components/results/MetricCards.tsx`
- `frontend/src/components/results/ResultsPage.tsx`
- `frontend/src/components/live/AlertPanel.tsx`
- `frontend/src/components/live/StrategyCard.tsx`
- `frontend/src/components/live/PositionPanel.tsx`
- `frontend/src/components/live/ExposurePanel.tsx`
- `frontend/src/components/live/LiveTradingDashboard.tsx`
- `frontend/src/components/live/RiskMetricsPanel.tsx`
- `frontend/dist/` — build output with CSV result files

**Required Action:** Extract `strategy-service/frontend/` to a new `strategy-ui` repo (or merge into existing `strategy-ui` if it exists). Delete `frontend/` from `strategy-service`. Track as a new task `arch-strategy-ui-extract`.

### market-tick-data-service — PARTIAL VIOLATION (Node package.json at root)

**File:** `market-tick-data-service/package.json`

**Content summary:** Declares `tardis-dev` (^14.1.2) JS dependency at the repo root. No tsx/jsx files, no frontend directory. This indicates the service may be using a Node.js component for Tardis market data ingestion alongside the Python package.

**Required Action:** Assess whether the `tardis-dev` Node dependency is still in use. If Python-only ingestion is complete, remove `package.json`. If still needed, document as an explicit exception. Track as `arch-market-tick-data-node-cleanup`.

### execution-service — PREVIOUSLY EXTRACTED (remnant only)

**File:** `execution-service/package-lock.json` (empty — `packages: {}`)

The plan item `arch-visualizer-extract` documented that `visualizer-ui/` and `visualizer-api/` needed extraction. Inspection confirms the extraction has been completed: the archive contains `archive/execution-visualizer-ui/`. Only an empty `package-lock.json` remnant remains. The `visualizer-ui/` and `visualizer-api/` directories are **not present** in execution-service.

**Recommended cleanup:** Remove `execution-service/package-lock.json` (empty artifact).

## Notes on htmlcov/index.html

Multiple repos contain `htmlcov/index.html` — this is the pytest-cov HTML coverage report output. It is a generated artifact, not embedded UI code. These are correctly excluded from the violation count and should be added to `.gitignore` in each repo.

Repos with htmlcov artifacts: alerting-service, market-data-processing-service, instruments-service, market-tick-data-service, features-delta-one-service, pnl-attribution-service.

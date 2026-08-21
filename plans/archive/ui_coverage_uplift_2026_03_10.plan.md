---
doc_type: plan
title: UI Coverage Uplift — 70% Floor
summary: 'Get all 12 active UI repos to ≥70% line coverage enforced at CI time. Current state: 0.6%–43% where measured;
  7 repos have no coverage-summary.json. Strategy: write mock-API tests per repo, add vitest thresholds, align templates
  and propagation scripts so the floor is preserved on future rollouts.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-10'
isProject: false
todos:
- {id: create-plan, content: Create this plan file and set up todo tracking., status: completed, notes: Done 2026-03-10.}
- {id: template-and-propagation-alignment, content: 'Ensure no propagation script can overwrite vitest coverage config. Update rollout-ui-build-infra.py: do NOT generate vitest.config.ts (owned per-repo). Update base-ui.sh [3/4]: add explicit threshold check after npm test --coverage so CI fails even if thresholds are not set in vitest.config.ts (belt-and-suspenders). Add canonical vitest.config.ts template to unified-trading-pm as reference.

    ', status: completed, notes: "DONE 2026-03-10:\n- rollout-ui-build-infra.py confirmed: does NOT write vitest.config.ts or package.json — safe.\n- base-ui.sh updated: [3/4] step now checks coverage-summary.json lines.pct ≥ MIN_UI_COVERAGE\n  (default 70) after npm test --coverage. Fails fast with clear error if below floor.\n- Canonical vitest.config.ts template added:\n  unified-trading-pm/scripts/quality-gates-base/vitest.config.template.ts\n  (coverage.thresholds: { lines: 70, statements: 70, functions: 70, branches: 70 })\n- cloudbuild.yaml for UI repos: step 0 runs `npm test` via base-ui.sh which enforces floor.\n"}
- {id: settlement-ui, content: 'settlement-ui: raise from 43% to ≥70%. Already has 4 test files and the highest existing coverage. Need ~27pp more — add tests for uncovered components/hooks.

    ', status: completed, notes: 'DONE 2026-03-10. Coverage: ≥70%. vitest.config.ts thresholds added.

    '}
- {id: deployment-ui, content: 'deployment-ui: raise from 13% to ≥70%. Has 9 existing test files (most of any UI repo). Complex: 7 src dirs. Use vi.mock for API calls and React Router.

    ', status: completed, notes: 'DONE 2026-03-10. Coverage: ≥70%. vitest.config.ts thresholds added.

    '}
- {id: logs-dashboard-ui, content: 'logs-dashboard-ui: raise from 8% to ≥70%. Mock /api/ proxy endpoints with vi.mock or MSW. Test LogsTable, filters, pagination components.

    ', status: completed, notes: 'DONE 2026-03-10. Coverage: ≥70%. vitest.config.ts thresholds added.

    '}
- {id: ml-training-ui, content: 'ml-training-ui: raise from 3% to ≥70%. Mock training run API, job status endpoints. Test TrainingJobList, RunStatusBadge, MetricsChart components.

    ', status: completed, notes: 'DONE 2026-03-10. Coverage: ≥70%. vitest.config.ts thresholds added.

    '}
- {id: onboarding-ui, content: 'onboarding-ui: raise from 1.5% to ≥70%. Has 7 test files (second most). Mock auth flow, multi-step form state. Existing tests mostly stub — need assertions.

    ', status: completed, notes: 'DONE 2026-03-10. Coverage: ≥70%. vitest.config.ts thresholds added.

    '}
- {id: strategy-ui, content: 'strategy-ui: raise from 0.6% to ≥70%. Complex (7 src dirs). Mock strategy API, backtesting endpoints, charts. Use vi.mock for recharts/chart components.

    ', status: completed, notes: 'DONE 2026-03-10. Coverage: ≥70%. vitest.config.ts thresholds added.

    '}
- {id: batch-audit-ui, content: 'batch-audit-ui: no baseline. Run first coverage measurement then raise to ≥70%. Minimal (2 dirs). Mock batch job API. Should be quick win.

    ', status: completed, notes: 'DONE 2026-03-10. Coverage: ≥70%. vitest.config.ts thresholds added.

    '}
- {id: client-reporting-ui, content: 'client-reporting-ui: no baseline. 4 src dirs, 4 test files. Mock report data API, chart rendering (vi.mock recharts). Test ReportTable, FilterPanel, DatePicker.

    ', status: completed, notes: 'DONE 2026-03-10. Coverage: ≥70%. vitest.config.ts thresholds added.

    '}
- {id: execution-analytics-ui, content: 'execution-analytics-ui: no baseline. 5 src dirs, 6 test files. Mock execution API, trade blotter data. Test AnalyticsDashboard, TradeTable, SlippageChart.

    ', status: completed, notes: 'DONE 2026-03-10. Coverage: ≥70%. vitest.config.ts thresholds added.

    '}
- {id: live-health-monitor-ui, content: 'live-health-monitor-ui: no baseline. 7 src dirs (complex), only 2 test files. Mock WebSocket/SSE health endpoints. Test ServiceCard, HealthGrid, AlertBanner.

    ', status: completed, notes: 'DONE 2026-03-10. Coverage: ≥70%. vitest.config.ts thresholds added.

    '}
- {id: trading-analytics-ui, content: 'trading-analytics-ui: no baseline. 3 src dirs, 2 test files. Mock trading analytics API. Test ReconPage, GitCompare, TradingDashboard.

    ', status: completed, notes: 'DONE 2026-03-10. Coverage: ≥70%. vitest.config.ts thresholds added.

    '}
- {id: unified-admin-ui, content: 'unified-admin-ui: already has 80% thresholds in vitest.config.ts. Verify tests pass at ≥70% and align threshold to workspace standard (lower from 80→70 or keep 80).

    ', status: completed, notes: 'DONE 2026-03-10. Kept at 80% (exceeds 70% floor — no change needed).

    Upgraded @vitest/coverage-v8 from ^1.3.0 → ^2.0.0 to match workspace constraint.

    '}
- {id: add-vitest-thresholds, content: 'Add coverage.thresholds: { lines: 70, statements: 70, functions: 70, branches: 70 } to all 11 vitest.config.ts files (unified-admin-ui already has 80% — leave as-is). Run npm test -- --coverage in each repo to confirm CI would pass.

    ', status: completed, notes: 'DONE 2026-03-10. All 11 repos updated. Vitest enforces thresholds when --coverage is passed.

    base-ui.sh also enforces via post-run JSON check (belt-and-suspenders).

    '}
- {id: final-check, content: 'Run bash deployment-service/scripts/check_test_alignment.sh from workspace root. Run coverage-audit.py to confirm all UI repos show ≥70% in manifest. Commit manifest with updated coverage_pct values.

    ', status: completed, notes: 'DONE 2026-03-10. All 12 UI repos ≥70%. Alignment check: 53 PASS / 0 WARN / 0 FAIL.

    workspace-manifest.json coverage_pct values updated for all UI repos.

    '}
---

# UI Coverage Uplift — 70% Floor (2026-03-10)

**Goal:** Every active UI repo has ≥70% line coverage enforced at CI time via vitest thresholds.

---

## Coverage Floor Standard

| Category | Floor | Enforcement                                         |
| -------- | ----- | --------------------------------------------------- |
| UI repos | 70%   | vitest.config.ts `coverage.thresholds.lines: 70`    |
|          |       | base-ui.sh post-run check on coverage-summary.json  |
|          |       | cloudbuild.yaml step 0 runs npm test via base-ui.sh |

---

## Mocking Strategy

All UI repos mock external dependencies with vitest's built-in `vi.mock`:

```typescript
// API calls
vi.mock("../api/client", () => ({ fetchData: vi.fn().mockResolvedValue(mockData) }));

// React Router
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => vi.fn(), useParams: () => ({ id: "1" }) };
});

// Charts (recharts, chart.js etc.)
vi.mock("recharts", () => ({ LineChart: ({ children }) => <div>{children}</div>, ... }));
```

React Testing Library renders components in jsdom. No real network calls.

---

## Template

Canonical vitest config template: `unified-trading-pm/scripts/quality-gates-base/vitest.config.template.ts`

```typescript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/setupTests.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json-summary"],
      reportsDirectory: "./coverage",
      thresholds: {
        lines: 70,
        statements: 70,
        functions: 70,
        branches: 70,
      },
    },
  },
});
```

---

## CI/CD Flow (confirmed aligned)

```
GH Actions / cloudbuild.yaml (step 0: node:20-alpine)
  └─ npm test                           ← package.json script: "vitest run"
       └─ base-ui.sh [3/4]
            └─ npm test -- --coverage   ← passes --coverage to vitest
                 └─ vitest (thresholds in vitest.config.ts)
                      ├─ fails if <70% lines        (vitest enforcement)
                      └─ base-ui.sh post-check       (belt-and-suspenders)
```

No propagation script modifies vitest.config.ts. rollout-ui-build-infra.py is safe.

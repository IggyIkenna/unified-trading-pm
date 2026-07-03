---
doc_type: plan
title: ui-react19-eslint9-upgrade-2026-03-16
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-16'
overview: 'Upgrade all 13 UI repos from React 18 + ESLint 8 + Vitest 2 to React 19 + ESLint 9 + Vitest 4. Update workspace-npm-constraints.json to match. Eliminates version split between odum-research-website (already on React 19) and the rest of the fleet.

  '
type: technical
epic: epic-infrastructure
completion_gates: {code: C3}
repo_gates:
- {repo: all-ui-repos, code: C3, readiness_note: All 13 UI repos pass QG. Zero version alignment warnings.}
depends_on: []
todos:
- id: update-npm-constraints
  content: '- [x] [AGENT] P0. Updated workspace-npm-constraints.json: @types/react ^19.0.0, @types/react-dom ^19.0.0, eslint ^9.0.0, vitest ^4.1.0, @vitest/coverage-v8 ^4.1.0, @vitejs/plugin-react ^6.0.1, vite ^6.0.0, jsdom ^29.0.0, typescript-eslint ^8.57.0, @eslint/js ^9.0.0, eslint-plugin-react-hooks ^5.0.0. Removed eslint-plugin-react-refresh.

    '
  status: done
  depends_on: []
- id: upgrade-batch-1-simple
  content: '- [x] [AGENT] P1. PARALLEL. Upgraded 4 simple UI repos: batch-audit-ui, logs-dashboard-ui, settlement-ui, trading-analytics-ui. ESLint flat config migrated, React 19 types, all QG pass.

    '
  status: done
  depends_on: [update-npm-constraints]
- id: upgrade-batch-2-medium
  content: '- [x] [AGENT] P1. PARALLEL. Upgraded 5 medium UI repos: client-reporting-ui, execution-analytics-ui, live-health-monitor-ui, ml-training-ui, strategy-ui. All QG pass.

    '
  status: done
  depends_on: [update-npm-constraints]
- id: upgrade-batch-3-complex
  content: '- [x] [AGENT] P2. Upgraded 4 complex UI repos: deployment-ui (240 tests pass), onboarding-ui, unified-admin-ui (monorepo — root + 3 packages), unified-trading-ui-auth (55 tests pass, peer dep updated). All QG pass.

    '
  status: done
  depends_on: [upgrade-batch-1-simple, upgrade-batch-2-medium]
- id: verify-all-qg
  content: '- [x] [AGENT] P3. QG --lint passes on all 13 repos + odum-research-website. Version alignment: "All UI repos match canonical npm constraints" (zero warnings). trading-analytics-ui needed @testing-library/dom added post-upgrade (peer dep not auto-installed with legacy-peer-deps).

    '
  status: done
  depends_on: [upgrade-batch-3-complex]
---


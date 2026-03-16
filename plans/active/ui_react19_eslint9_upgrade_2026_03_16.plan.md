---
name: ui-react19-eslint9-upgrade-2026-03-16
overview: >
  Upgrade all 13 UI repos from React 18 + ESLint 8 + Vitest 2 to React 19 + ESLint 9 + Vitest 4. Update
  workspace-npm-constraints.json to match. Eliminates version split between odum-research-website (already on React 19)
  and the rest of the fleet.
type: technical
epic: epic-infrastructure
status: active

completion_gates:
  code: C3

repo_gates:
  - repo: all-ui-repos
    code: C3
    readiness_note: "All 13 UI repos must pass QG after upgrade."

depends_on: []

# Pre-audit: all 13 UI repos on React 18.x, ESLint 8.56.0, Vitest 2.0.0, @types/react 18.x
# odum-research-website already on React 19 + ESLint 9 + Vitest 4 (no changes needed)
#
# Breaking changes to handle:
#   React 18→19: ref as prop (no forwardRef), useContext returns use(), Suspense changes
#   ESLint 8→9: flat config (eslint.config.js replaces .eslintrc.cjs)
#   Vitest 2→4: minor API changes, pool:"forks" already set
#   @types/react 18→19: useRef requires initial value, ReactNode includes bigint
#   @vitejs/plugin-react 4→6: minor config changes
#   jsdom 28→29: minor compat

todos:
  - id: update-npm-constraints
    content: >
      - [ ] [AGENT] P0. Update workspace-npm-constraints.json to React 19 + ESLint 9 + Vitest 4 targets: @types/react
      ^19.0.0, @types/react-dom ^19.0.0, eslint ^9.0.0, vitest ^4.1.0, @vitest/coverage-v8 ^4.1.0, @vitejs/plugin-react
      ^6.0.1, jsdom ^29.0.0, typescript-eslint ^8.57.0. Add eslint-plugin-react-hooks ^5.0.0 (React 19 compatible).
      Remove eslint-plugin-react-refresh (merged into react-hooks in v5).
    status: pending
    depends_on: []

  - id: upgrade-batch-1-simple
    content: >
      - [ ] [AGENT] P1. PARALLEL. Upgrade 4 simple UI repos (minimal custom code, few components): batch-audit-ui,
      logs-dashboard-ui, settlement-ui, trading-analytics-ui. Per repo: (1) npm install react@19 react-dom@19
      @types/react@19 @types/react-dom@19. (2) npm install -D eslint@9 typescript-eslint @eslint/js. (3) Migrate
      .eslintrc.cjs to eslint.config.js. (4) npm install -D vitest@4 @vitest/coverage-v8@4 @vitejs/plugin-react@6
      jsdom@29. (5) Fix any React 19 type errors (useRef, forwardRef). (6) Run QG. Commit per repo.
    status: pending
    depends_on: [update-npm-constraints]

  - id: upgrade-batch-2-medium
    content: >
      - [ ] [AGENT] P1. PARALLEL. Upgrade 5 medium UI repos: client-reporting-ui, execution-analytics-ui,
      live-health-monitor-ui, ml-training-ui, strategy-ui. Same steps as batch-1. These have more components — may need
      more type fixes.
    status: pending
    depends_on: [update-npm-constraints]

  - id: upgrade-batch-3-complex
    content: >
      - [ ] [AGENT] P2. SEQUENTIAL. Upgrade 3 complex UI repos: deployment-ui (largest, most components), onboarding-ui
      (forms), unified-admin-ui (monorepo). deployment-ui: custom eslint.config.js already exists — update to use
      typescript-eslint ^8.57. unified-admin-ui: monorepo with workspaces — upgrade root + packages/core.
      unified-trading-ui-auth: shared auth library — upgrade as peer dep, verify all consumers.
    status: pending
    depends_on: [upgrade-batch-1-simple, upgrade-batch-2-medium]

  - id: verify-all-qg
    content: >
      - [ ] [AGENT] P3. Run QG on all 13 UI repos + odum-research-website. Verify zero version alignment warnings from
      run-version-alignment.sh step [0.7]. Commit any remaining fixes.
    status: pending
    depends_on: [upgrade-batch-3-complex]
---

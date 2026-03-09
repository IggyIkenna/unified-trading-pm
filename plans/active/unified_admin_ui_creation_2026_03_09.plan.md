---
name: Unified Admin UI — npm Workspace Creation
overview: |
  Create the unified-admin-ui GitHub repo as an npm workspace monorepo (making total workspace repo count 60).
  The monorepo contains packages/core (shared components, hooks, auth, api-client) plus one package per UI
  app. All 11 existing UI repos (batch-audit-ui, client-reporting-ui, deployment-ui,
  execution-analytics-ui, live-health-monitor-ui, logs-dashboard-ui, ml-training-ui, onboarding-ui,
  settlement-ui, strategy-ui, trading-analytics-ui) will remove duplicate code and import from the
  core package. Quality gates are TypeScript-only: tsc --noEmit, ESLint zero-warnings, Vitest, Playwright.
  No Python tooling (no uv, no basedpyright, no pytest) per ui-no-python-quality-gates.mdc.
status: active
created: 2026-03-09
updated: 2026-03-09
isProject: true
todos:
  - id: create-github-repo
    content: >-
      Create GitHub repo per new-repo-setup.mdc: `gh repo create IggyIkenna/unified-admin-ui --private --clone`. Grant
      team access: `gh api /repos/IggyIkenna/unified-admin-ui/collaborators/CosmicTrader -f permission='push'` and same
      for datado. Set default branch to main. Verify remote shows private and correct collaborators before proceeding.
    status: pending

  - id: scaffold-npm-workspace
    content: >-
      Scaffold npm workspace monorepo structure. Root package.json: set `"name": "unified-admin-ui"`, `"private": true`,
      `"workspaces": ["packages/*"]`. Create packages/core/ with sub-dirs: src/components/, src/hooks/, src/auth/,
      src/api-client/. Add packages/core/package.json (`"name": "@unified-admin/core"`). Create index files and
      placeholder exports. Add root .gitignore (node_modules, dist, .turbo, coverage). Add .nvmrc pinning Node LTS.
    status: pending

  - id: configure-tooling
    content: >-
      Configure TypeScript + ESLint + Vitest + Playwright per ui-setup-checklist.mdc. Root tsconfig.json: `"strict":
      true`, `"noImplicitAny": true`, composite references to each package. Root .eslintrc with zero-warnings policy
      (`"no-unused-vars": "error"`). Vitest config at root with coverage threshold >80% per package. Playwright config
      at root with smoke tests for each package entry point. Confirm `tsc --noEmit` and `eslint --max-warnings 0` pass
      on empty scaffold before adding any UI code.
    status: pending

  - id: update-workspace-manifest
    content: >-
      Add unified-admin-ui to workspace-manifest.json in unified-trading-pm. Entry fields: `"type": "ui"`, `"arch_tier":
      "ui"`, `"status": "active"`. Update `"lastUpdated"` and increment notes entry. Repo count moves from 59 to 60.
      Confirm count with: `python3 -c "import json; d=json.load(open('workspace-manifest.json'));
      print(len(d['repositories']))"`.
    status: pending

  - id: update-workspace-configs
    content: >-
      Update VS Code workspace config files to include unified-admin-ui. Edit
      `.cursor/workspace-configs/workspace-uis.code-workspace`: add `{"path": "../../unified-admin-ui"}` to the
      `folders` array. Edit `unified-trading-system-repos.code-workspace`: add the same path entry. Verify both files
      open the new folder in VS Code without errors.
    status: pending

  - id: npm-install-initial
    content: >-
      From the unified-admin-ui repo root, run `npm install` to generate package-lock.json. Commit package-lock.json to
      the repo. Do NOT run uv or pip — this is a UI repo with no Python dependencies (ui-no-python-quality-gates.mdc).
      Verify `npm run build` and `npm run test` scripts are defined and exit 0 on the empty scaffold.
    status: pending

  - id: push-initial-scaffold
    content: >-
      Push initial scaffold to main. From unified-admin-ui/: `git add -A`, commit `"feat: scaffold unified-admin-ui npm
      workspace with packages/core"`, then `bash scripts/quickmerge.sh "feat: scaffold unified-admin-ui npm workspace"`.
      Confirm CI passes (tsc --noEmit, ESLint zero-warnings, Vitest coverage >80% on scaffold, Playwright smoke) before
      moving to per-UI-repo migration todos.
    status: pending

  - id: migrate-batch-audit-ui
    content: >-
      Audit batch-audit-ui for duplicated patterns: Vite config, TypeScript config, ESLint config, auth logic (token
      fetch/refresh), API client setup (base URL, headers, interceptors), shared React components (layouts, nav, error
      boundaries). Move duplicates to packages/core, update all imports in batch-audit-ui to `@unified-admin/core`. Run
      `npm test` in batch-audit-ui; update coverage to >80%; fix any failures. Delete top-level duplicate config files
      that are now in core.
    status: pending

  - id: migrate-client-reporting-ui
    content: >-
      Audit client-reporting-ui for duplicated patterns (same categories as batch-audit-ui). Move any new duplicates not
      yet in core to packages/core. Update all imports. Run `npm test`; update coverage to >80%; fix failures. Delete
      superseded files.
    status: pending

  - id: migrate-deployment-ui
    content: >-
      Audit deployment-ui for duplicated patterns. Move new duplicates to packages/core. Update imports. Run `npm test`;
      update coverage to >80%; fix failures. Delete superseded files. Pay attention to deployment-specific API client
      patterns that may generalize.
    status: pending

  - id: migrate-execution-analytics-ui
    content: >-
      Audit execution-analytics-ui for duplicated patterns. Move new duplicates (e.g. charting base config, analytics
      hooks) to packages/core. Update imports. Run `npm test`; update coverage >80%; fix failures. Delete superseded
      files.
    status: pending

  - id: migrate-live-health-monitor-ui
    content: >-
      Audit live-health-monitor-ui for duplicated patterns. Move new duplicates (e.g. polling hooks, WebSocket wrappers)
      to packages/core. Update imports. Run `npm test`; update coverage >80%; fix failures. Delete superseded files.
    status: pending

  - id: migrate-logs-dashboard-ui
    content: >-
      Audit logs-dashboard-ui for duplicated patterns. Move new duplicates (e.g. log-stream hooks, virtualized list
      components) to packages/core. Update imports. Run `npm test`; update coverage >80%; fix failures. Delete
      superseded files.
    status: pending

  - id: migrate-ml-training-ui
    content: >-
      Audit ml-training-ui for duplicated patterns. Move new duplicates (e.g. progress-bar components, experiment table)
      to packages/core. Update imports. Run `npm test`; update coverage >80%; fix failures. Delete superseded files.
    status: pending

  - id: migrate-onboarding-ui
    content: >-
      Audit onboarding-ui for duplicated patterns. Move new duplicates (e.g. form components, stepper) to packages/core.
      Update imports. Run `npm test`; update coverage >80%; fix failures. Delete superseded files.
    status: pending

  - id: migrate-settlement-ui
    content: >-
      Audit settlement-ui for duplicated patterns. Move new duplicates (e.g. reconciliation table, currency formatters)
      to packages/core. Update imports. Run `npm test`; update coverage >80%; fix failures. Delete superseded files.
    status: pending

  - id: migrate-strategy-ui
    content: >-
      Audit strategy-ui for duplicated patterns. Move new duplicates (e.g. signal chart, parameter form) to
      packages/core. Update imports. Run `npm test`; update coverage >80%; fix failures. Delete superseded files.
    status: pending

  - id: migrate-trading-analytics-ui
    content: >-
      Audit trading-analytics-ui for duplicated patterns. Move new duplicates (e.g. P&L chart, position table) to
      packages/core. Update imports. Run `npm test`; update coverage >80%; fix failures. Delete superseded files.
    status: pending

  - id: delete-remaining-top-level-duplicates
    content: >-
      After all 11 UI repos are migrated: do a final pass across each repo to confirm no remaining top-level duplicates
      of files that now live in packages/core. Delete any that remain. Run `npm run lint` (zero warnings) and `npm run
      type-check` (tsc --noEmit) in each repo after deletion to confirm nothing is broken. Commit deletions per repo
      with message `"chore: remove top-level duplicates moved to @unified-admin/core"`.
    status: pending

  - id: playwright-full-smoke
    content: >-
      Run full Playwright smoke tests across all packages from unified-admin-ui workspace root: `npm run test:e2e`.
      Confirm all critical user flows pass for every UI app. Fix any failures. Confirm ESLint zero-warnings and tsc
      --noEmit both pass at root level before marking plan done.
    status: pending
---

# Unified Admin UI — npm Workspace Creation

## Objective

Create `unified-admin-ui` as a private GitHub npm workspace monorepo. Extract shared UI boilerplate from 11 existing UI
repos into `packages/core`, eliminating duplication and providing a single source of truth for auth, API client, shared
components, and tooling configuration.

## Repo Count Impact

workspace-manifest.json moves from 59 → 60 repos upon adding `unified-admin-ui`.

## Package Structure

```
unified-admin-ui/
  package.json               # root workspace: "workspaces": ["packages/*"]
  tsconfig.json              # strict: true, composite references
  .eslintrc                  # zero-warnings policy
  playwright.config.ts
  packages/
    core/                    # @unified-admin/core — shared code
      src/
        components/          # layouts, nav, error boundaries, tables, charts base
        hooks/               # usePolling, useWebSocket, useAuth, usePagination
        auth/                # token fetch/refresh, session management
        api-client/          # base URL config, headers, interceptors, error handling
      package.json
      tsconfig.json
      vitest.config.ts
```

## Quality Gates (TypeScript only — no Python)

Per `ui-no-python-quality-gates.mdc`:

- `tsc --noEmit` — zero type errors
- `eslint --max-warnings 0` — zero lint warnings
- `vitest run --coverage` — >80% coverage per package
- `playwright test` — all smoke tests pass

Do NOT run: `uv`, `basedpyright`, `pytest`, `ruff`, `pip` — this is a UI-only repo.

## Per-Repo Migration Checklist

For each of the 11 UI repos during migration:

1. Audit for duplicated: Vite config, TS config, ESLint config, auth logic, API client, shared components
2. Move net-new duplicates (not yet in core) to `packages/core`
3. Update all imports to `@unified-admin/core`
4. Run `npm test`; fix failures; update coverage to >80%
5. Delete superseded top-level files
6. Commit: `"refactor(<repo>): extract duplicates to @unified-admin/core"`

## Standards

- TypeScript `strict: true`; no `any` types
- ESLint zero-warnings
- Vitest coverage >80% per package
- Playwright smoke tests for all critical user flows
- All imports from `@unified-admin/core` — no cross-package deep imports

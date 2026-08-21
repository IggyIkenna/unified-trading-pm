---
doc_type: plan
title: unified-admin-ui-creation-2026-03-09
summary: Create unified-admin-ui as an npm workspace monorepo with packages/core; migrate auth and API client patterns from
  11 existing UI repos into the shared core package.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: 2026-03-09
type: code
epic: epic-code-completion
updated: 2026-03-11
isProject: true
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-admin-ui, code: C2, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: batch-audit-ui, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: client-reporting-ui, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: deployment-ui, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: execution-analytics-ui, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: live-health-monitor-ui, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: logs-dashboard-ui, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: ml-training-ui, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: onboarding-ui, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: settlement-ui, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: strategy-ui, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: trading-analytics-ui, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
depends_on: []
todos:
- {id: create-github-repo, content: 'Create GitHub repo per new-repo-setup.mdc: `gh repo create IggyIkenna/unified-admin-ui --private --clone`. Grant team access: `gh api /repos/IggyIkenna/unified-admin-ui/collaborators/CosmicTrader -f permission=''push''` and same for datado. Set default branch to main. Verify remote shows private and correct collaborators before proceeding.', status: done}
- {id: scaffold-npm-workspace, content: 'Scaffold npm workspace monorepo structure. Root package.json: set `"name": "unified-admin-ui"`, `"private": true`, `"workspaces": ["packages/*"]`. Create packages/core/ with sub-dirs: src/components/, src/hooks/, src/auth/, src/api-client/. Add packages/core/package.json (`"name": "@unified-admin/core"`). Create index files and placeholder exports. Add root .gitignore (node_modules, dist, .turbo, coverage). Add .nvmrc pinning Node LTS.', status: done}
- {id: configure-tooling, content: 'Configure TypeScript + ESLint + Vitest + Playwright per ui-setup-checklist.mdc. Root tsconfig.json: `"strict": true`, `"noImplicitAny": true`, composite references to each package. Root .eslintrc with zero-warnings policy (`"no-unused-vars": "error"`). Vitest config at root with coverage threshold >80% per package. Playwright config at root with smoke tests for each package entry point. Confirm `tsc --noEmit` and `eslint --max-warnings 0` pass on empty scaffold before adding any UI code.', status: done}
- {id: update-workspace-manifest, content: 'Add unified-admin-ui to workspace-manifest.json in unified-trading-pm. Entry fields: `"type": "ui"`, `"arch_tier": "ui"`, `"status": "active"`. Update `"lastUpdated"` and increment notes entry. Repo count moves from 59 to 60. Confirm count with: `python3 -c "import json; d=json.load(open(''workspace-manifest.json'')); print(len(d[''repositories'']))"`.', status: done}
- {id: update-workspace-configs, content: 'Update VS Code workspace config files to include unified-admin-ui. Edit `.cursor/workspace-configs/workspace-uis.code-workspace`: add `{"path": "../../unified-admin-ui"}` to the `folders` array. Edit `unified-trading-system-repos.code-workspace`: add the same path entry. Verify both files open the new folder in VS Code without errors.', status: done}
- {id: npm-install-initial, content: 'From the unified-admin-ui repo root, run `npm install` to generate package-lock.json. Commit package-lock.json to the repo. Do NOT run uv or pip — this is a UI repo with no Python dependencies (ui-no-python-quality-gates.mdc). Verify `npm run build` and `npm run test` scripts are defined and exit 0 on the empty scaffold.', status: done}
- {id: push-initial-scaffold, content: 'Push initial scaffold to main. From unified-admin-ui/: `git add -A`, commit `"feat: scaffold unified-admin-ui npm workspace with packages/core"`, then `bash scripts/quickmerge.sh "feat: scaffold unified-admin-ui npm workspace"`. Confirm CI passes (tsc --noEmit, ESLint zero-warnings, Vitest coverage >80% on scaffold, Playwright smoke) before moving to per-UI-repo migration todos.', status: done}
- {id: migrate-batch-audit-ui, content: 'Audit batch-audit-ui for duplicated patterns: Vite config, TypeScript config, ESLint config, auth logic (token fetch/refresh), API client setup (base URL, headers, interceptors), shared React components (layouts, nav, error boundaries). Move duplicates to packages/core, update all imports in batch-audit-ui to `@unified-admin/core`. Run `npm test` in batch-audit-ui; update coverage to >80%; fix any failures. Delete top-level duplicate config files that are now in core.', status: done}
- {id: migrate-client-reporting-ui, content: Audit client-reporting-ui for duplicated patterns (same categories as batch-audit-ui). Move any new duplicates not yet in core to packages/core. Update all imports. Run `npm test`; update coverage to >80%; fix failures. Delete superseded files., status: done}
- {id: migrate-deployment-ui, content: Audit deployment-ui for duplicated patterns. Move new duplicates to packages/core. Update imports. Run `npm test`; update coverage to >80%; fix failures. Delete superseded files. Pay attention to deployment-specific API client patterns that may generalize., status: done}
- {id: migrate-execution-analytics-ui, content: 'Audit execution-analytics-ui for duplicated patterns. Move new duplicates (e.g. charting base config, analytics hooks) to packages/core. Update imports. Run `npm test`; update coverage >80%; fix failures. Delete superseded files.', status: done}
- {id: migrate-live-health-monitor-ui, content: 'Audit live-health-monitor-ui for duplicated patterns. Move new duplicates (e.g. polling hooks, WebSocket wrappers) to packages/core. Update imports. Run `npm test`; update coverage >80%; fix failures. Delete superseded files.', status: done}
- {id: migrate-logs-dashboard-ui, content: 'Audit logs-dashboard-ui for duplicated patterns. Move new duplicates (e.g. log-stream hooks, virtualized list components) to packages/core. Update imports. Run `npm test`; update coverage >80%; fix failures. Delete superseded files.', status: done}
- {id: migrate-ml-training-ui, content: 'Audit ml-training-ui for duplicated patterns. Move new duplicates (e.g. progress-bar components, experiment table) to packages/core. Update imports. Run `npm test`; update coverage >80%; fix failures. Delete superseded files.', status: done}
- {id: migrate-onboarding-ui, content: 'Audit onboarding-ui for duplicated patterns. Move new duplicates (e.g. form components, stepper) to packages/core. Update imports. Run `npm test`; update coverage >80%; fix failures. Delete superseded files.', status: done}
- {id: migrate-settlement-ui, content: 'Audit settlement-ui for duplicated patterns. Move new duplicates (e.g. reconciliation table, currency formatters) to packages/core. Update imports. Run `npm test`; update coverage >80%; fix failures. Delete superseded files.', status: done}
- {id: migrate-strategy-ui, content: 'Audit strategy-ui for duplicated patterns. Move new duplicates (e.g. signal chart, parameter form) to packages/core. Update imports. Run `npm test`; update coverage >80%; fix failures. Delete superseded files.', status: done}
- {id: migrate-trading-analytics-ui, content: 'Audit trading-analytics-ui for duplicated patterns. Move new duplicates (e.g. P&L chart, position table) to packages/core. Update imports. Run `npm test`; update coverage >80%; fix failures. Delete superseded files.', status: done}
- {id: delete-remaining-top-level-duplicates, content: 'After all 11 UI repos are migrated: do a final pass across each repo to confirm no remaining top-level duplicates of files that now live in packages/core. Delete any that remain. Run `npm run lint` (zero warnings) and `npm run type-check` (tsc --noEmit) in each repo after deletion to confirm nothing is broken. Commit deletions per repo with message `"chore: remove top-level duplicates moved to @unified-admin/core"`.', status: done}
- {id: playwright-full-smoke, content: 'Run full Playwright smoke tests across all packages from unified-admin-ui workspace root: `npm run test:e2e`. Confirm all critical user flows pass for every UI app. Fix any failures. Confirm ESLint zero-warnings and tsc --noEmit both pass at root level before marking plan done.', status: done}
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

> ⚠️ **H3 SCOPE CONSTRAINT (2026-03-11):** `ui_design_system_upgrade_2026_03_10` (DONE) already extracted design tokens,
> base components (dark terminal aesthetic), layout system, and mock infrastructure into `@unified-trading/ui-kit`
> across all 11 UI repos. Migration todos here MUST NOT re-extract those items into `@unified-admin/core`. Scope of
> `@unified-admin/core` is strictly: **auth patterns** (token fetch/refresh, session management) and **API client
> patterns** (base URL, headers, interceptors, error handling). Do not extract design tokens, base components, layout,
> charts, or mock infrastructure.

For each of the 11 UI repos during migration:

1. Audit for duplicated: **auth logic** (token fetch/refresh) and **API client setup** (base URL, headers, interceptors)
   only
2. Move net-new auth/API client duplicates (not yet in core) to `packages/core`
3. Update all imports to `@unified-admin/core`
4. Run `npm test`; fix failures; update coverage to >80%
5. Delete superseded top-level files
6. Commit: `"refactor(<repo>): extract auth/api-client to @unified-admin/core"`

## Standards

- TypeScript `strict: true`; no `any` types
- ESLint zero-warnings
- Vitest coverage >80% per package
- Playwright smoke tests for all critical user flows
- All imports from `@unified-admin/core` — no cross-package deep imports

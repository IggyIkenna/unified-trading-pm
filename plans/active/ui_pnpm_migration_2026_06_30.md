---
doc_type: plan
title: Standardize active node/UI repos on pnpm (npm→pnpm migration) — coordination tracker
summary:
  Migrate the 3 active npm UI repos (deployment-ui, agent-orchestrator/dashboard, unified-trading-pm/presentations) to
  pnpm so the whole node fleet uses one package manager with store-level dedup, killing the npm-vs-pnpm tooling-drift
  bug class. Coordination tracker; the dispatchable work lives in 4 child plans.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-ui, agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [pnpm, node, package-manager, disk, dedup, ci, ui]
related:
  [
    ./issues/node_modules_dedup_2026_06_29.md,
    ./ui_pnpm_migration_tooling_prep_2026_06_30.md,
    ./ui_pnpm_migration_deployment_ui_2026_06_30.md,
    ./ui_pnpm_migration_ao_dashboard_2026_06_30.md,
    ./ui_pnpm_migration_pm_presentations_2026_06_30.md,
  ]
created: 2026-06-30
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: infra-engineer
drift_direction: advance-code
last_updated: 2026-06-30
locked_by: live-defi-rollout
locked_since: 2026-06-30
source: [node_modules_dedup_2026_06_29.md, operator request 2026-06-30]
---

# Standardize active node/UI repos on pnpm — coordination tracker

> **This is a coordination tracker (`execution_scope: local-only` → NOT ingested by AO as tasks).** The dispatchable
> work is split into **4 child plans** (1 infra-prep + 3 ui-developer migrations), each a single-agent / single-PR unit
> per the PLAN_FORMAT sizing HARD RULE. The children are born **`status: draft`** so AO does not dispatch them until the
> operator finalises and flips each to `status: active`. This tracker holds the shared recipe, the pre-audit manifest,
> the DAG, and the success gates so each stranger-agent has full context.

## Why (decision provenance)

`issues/node_modules_dedup_2026_06_29.md` established: pnpm's content-addressed store + hardlinks is the node equivalent
of the uv shared-cache fix (logically-isolated per-slot `node_modules`, physically deduped) — and npm has **no**
cross-project dedup at all. The active node fleet is split: `unified-trading-system-ui` is already pnpm (CI-enforced);
`deployment-ui`, `agent-orchestrator/dashboard`, `unified-trading-pm/presentations` are npm. The split causes a real bug
class — npm-assuming tooling (`run-version-alignment.sh`) pollutes the pnpm repo with stray `npm install` artifacts.
Standardizing on pnpm gets the dedup as a byproduct **and** removes the mixed-toolchain bug surface. Operator decision
(2026-06-30): migrate the **3 active repos only**; the 14 dormant `.extra/` UIs (frozen 2026-03-17) are **out of
scope**.

## Scope (operator-confirmed)

| Repo                               | Current PM | CI install today                                     | Migration character                      |
| ---------------------------------- | ---------- | ---------------------------------------------------- | ---------------------------------------- |
| `unified-trading-system-ui`        | **pnpm**   | `pnpm install --frozen-lockfile` (ui-quality-gates)  | already done — cleanup only (prep plan)  |
| `deployment-ui`                    | npm        | `npm ci` in `ui-quality-gates-v2.yml`                | real migration + CI swap                 |
| `agent-orchestrator/dashboard`     | npm        | `npm ci` + `npm run build` in `deploy-dashboard.yml` | real migration + **deploy-path** CI swap |
| `unified-trading-pm/presentations` | npm        | **none of its own** (only global `claude-code`)      | trivial — lockfile swap, no CI install   |

**Out of scope:** the 14 `.extra/` UIs (`batch-audit-ui`, `client-reporting-ui`, `execution-analytics-ui`,
`live-health-monitor-ui`, `logs-dashboard-ui`, `ml-training-ui`, `onboarding-ui`, `settlement-ui`, `strategy-ui`,
`trading-analytics-ui`, `unified-admin-ui`, `unified-trading-ui-auth`, `unified-trading-ui-kit`, `user-management-ui`) —
dormant since 2026-03-17, `user-management-ui` already ARCHIVED. Revisit only if revived.

## The DAG (parallelism = the plan)

```
ui_pnpm_migration_tooling_prep      (infra-engineer; PM scripts + UI-repo stray cleanup)
        │  (soft prereq — land first so migrated repos aren't re-polluted by the npm-assuming alignment cron)
        ├──────────────► ui_pnpm_migration_deployment_ui      (ui-developer)  ┐
        ├──────────────► ui_pnpm_migration_ao_dashboard       (ui-developer)  │  3 independent repos →
        └──────────────► ui_pnpm_migration_pm_presentations   (ui-developer)  ┘  dispatch in PARALLEL
```

The 3 migrations are context-independent (different repos, no shared output) → **separate plans → parallel agents** (the
split test: three strangers who never talk could each do one correctly). They each `depends_on` the prep plan for
ordering + archival, **not** on each other. This fan-out is the intended AO-capability exercise.

## Canonical migration recipe (embedded in each child plan)

Per repo, the migrating agent MUST:

1. **Pre-audit (phantom-dep risk).** Record the current install (`npm ls --all > /tmp/<repo>_npm_tree.txt`). pnpm's
   strict, non-hoisted layout will FAIL the build/tests if the code imports a transitive dep not declared in
   `package.json` (a phantom dependency that npm's flat hoisting silently allowed). This is the #1 migration risk —
   surface it deliberately, do not assume zero.
2. **Generate the pnpm lockfile from the npm one.** `pnpm import` (reads `package-lock.json` → `pnpm-lock.yaml`
   preserving the resolved versions), then `git rm package-lock.json`. Add `"packageManager": "pnpm@<X.Y.Z>"` to
   `package.json` — pin the **same pnpm major** that `unified-trading-system-ui` uses (`pnpm/action-setup@v6`).
3. **Install + fix phantom deps.** `pnpm install` (generates `node_modules`), then `pnpm install --frozen-lockfile` to
   prove the lock is authoritative. For every phantom-dep build/test failure: add the missing package to `package.json`
   `dependencies`/`devDependencies` explicitly and re-lock. Do NOT paper over with `node-linker=hoisted` /
   `shamefully-hoist` — that defeats the strictness benefit; only use it if a dependency is genuinely broken under
   symlinked layout AND document why as a follow-up todo.
4. **Swap CI.** Replace `actions/setup-node` `cache: npm` + `npm ci` with `pnpm/action-setup@v6` + setup-node
   `cache: pnpm` + `pnpm install --frozen-lockfile`; `npm run <script>` → `pnpm <script>`. Mirror the established
   `unified-trading-system-ui/.github/workflows/ui-quality-gates-v2.yml` (pnpm setup + store cache keyed on
   `pnpm-lock.yaml`). **Never hand-edit a per-repo template copy** where a PM workflow-template governs it — check
   first.
5. **Repo-local scripts.** Update any in-repo `npm install`/`npm run` invocation to pnpm. (Cross-cutting workspace
   scripts — `run-version-alignment.sh`, `dev-start.sh`, `restart-deployment-stack.sh` — are owned by the **prep** plan,
   not the per-repo plans.)
6. **Store config stays host-local.** Do NOT commit an absolute `store-dir`/`UV`-style path. The pnpm store is
   workspace-derived + host-local (env or uncommitted `.npmrc`), exactly like the uv-cache "CI owns its own store" rule
   — a committed absolute store path breaks CI's ephemeral FS. Keep any committed `.npmrc` to portable settings only
   (e.g. deployment-ui's existing `legacy-peer-deps=true`).
7. **Verify (the Gate).** All green, evidenced:
   - `pnpm install --frozen-lockfile` clean (lock authoritative);
   - `pnpm build` green; `pnpm test` (vitest/playwright) green;
   - CI green — `quality-gates-v2` for deployment-ui; the deploy workflow's build step for dashboard; presentations has
     no install-CI (verify nothing else builds it);
   - **UI gate (HARD, PLAN_FORMAT §9)** for repos with routes (deployment-ui, dashboard): `[UI]` tag + `pw:L2 ✓` + a
     cited regression spec;
   - **Dedup proof:** a real file under the new `node_modules/.pnpm/<pkg>@<ver>/...` shows `links≥2` (hardlinked to the
     workspace store) — `stat -c '%h %i' <file>`.
8. **Ship.** `bash scripts/quickmerge.sh "feat: migrate <repo> npm→pnpm" --agent --files '<paths>'`.

## Success criteria (whole effort)

- All 3 active node repos install via `pnpm install --frozen-lockfile`; no committed `package-lock.json` remains in any
  of them; each declares `packageManager: pnpm@…`.
- CI green on each (`quality-gates-v2` / deploy build) with pnpm; no `npm ci` left in any active node repo workflow.
- `unified-trading-system-ui` stray `package-lock.json` removed and the npm-assuming workspace tooling is pnpm-aware
  (prep plan) so the stray cannot regenerate.
- Dedup confirmed (`.pnpm` files `links≥2`) on at least one migrated repo.

## Pre-audit manifest (per repo — grounds each child plan)

- **deployment-ui** — Vite + `tsc && vite build` + eslint + vitest, node ≥22. CI: `ui-quality-gates-v2.yml`
  (`setup-node@v5`, `cache: npm`, `npm ci`). Committed `.npmrc` = `legacy-peer-deps=true` (KEEP — portable). Real UI →
  playwright gate applies.
- **agent-orchestrator/dashboard** — Vite + `tsc --noEmit && vite build` + vitest, node 20. CI: `deploy-dashboard.yml`
  (`npm ci` + `npm run build`) — this is a **deploy** path; a broken install breaks dashboard deploy, so verify the
  deploy build end-to-end. Real UI → playwright gate applies.
- **unified-trading-pm/presentations** — `test: npx playwright test tests/`; **no CI installs its deps** (PM workflows
  only `npm install -g @anthropic-ai/claude-code`, unrelated). Lowest risk: swap lockfile, confirm nothing
  builds/deploys it in CI. Confirm whether it renders routes needing the playwright gate or is a static slides build.

## Codex SSOTs (read before executing — plan↔codex drift is review-blocking)

- `codex/05-infrastructure/per-tab-worktrees.md` — on-demand artifact model (per-slot `node_modules`; the store is the
  shared layer). The gitignore "symlink to shared install" comments contradict this and are corrected by the prep plan.
- `codex/06-coding-standards/ui-testing-layers.md` + PLAN_FORMAT §9 — the `[UI]` playwright verification gate.
- `codex/08-workflows/ci-cd-flow.md` — quickmerge / LDR / `quality-gates-v2`; workflow-template discipline (never
  hand-edit a per-repo copy if a template governs it).
- `plans/active/issues/node_modules_dedup_2026_06_29.md` — the analysis + measured dedup facts this plan acts on.

## Child plans

| Plan                                            | Role           | Unit                                                                    |
| ----------------------------------------------- | -------------- | ----------------------------------------------------------------------- |
| `ui_pnpm_migration_tooling_prep_2026_06_30`     | infra-engineer | PM tooling pnpm-awareness + UI-repo stray cleanup + codex/gitignore fix |
| `ui_pnpm_migration_deployment_ui_2026_06_30`    | ui-developer   | deployment-ui npm→pnpm + CI                                             |
| `ui_pnpm_migration_ao_dashboard_2026_06_30`     | ui-developer   | agent-orchestrator/dashboard npm→pnpm + deploy CI                       |
| `ui_pnpm_migration_pm_presentations_2026_06_30` | ui-developer   | unified-trading-pm/presentations npm→pnpm (no CI install)               |

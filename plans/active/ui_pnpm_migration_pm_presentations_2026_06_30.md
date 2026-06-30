---
doc_type: plan
title: Migrate unified-trading-pm/presentations from npm to pnpm
summary:
  Migrate the presentations node project to pnpm — import the lockfile, fix any phantom deps, confirm nothing in CI
  installs/builds it (only unrelated global claude-code installs exist), verify build/test green + store dedup.
status: draft
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [pnpm, node, migration]
related: [./ui_pnpm_migration_2026_06_30.md, ./ui_pnpm_migration_tooling_prep_2026_06_30.md]
created: 2026-06-30
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: ui-developer
drift_direction: advance-code
depends_on: [ui_pnpm_migration_tooling_prep_2026_06_30]
last_updated: 2026-06-30
locked_by: live-defi-rollout
locked_since: 2026-06-30
source: [node_modules_dedup_2026_06_29.md]
---

# Migrate unified-trading-pm/presentations → pnpm

> Parent tracker `ui_pnpm_migration_2026_06_30.md` holds the full canonical recipe — read it first. Single agent, single
> PR. Independent of the other two repo migrations (run in parallel). **Lowest risk:** no CI installs this project's
> deps (the only npm in PM workflows is a global `@anthropic-ai/claude-code` install, unrelated). Mostly a lockfile
> swap.

## Pre-audit (this repo)

- Lives at `unified-trading-pm/presentations/`.
- `"test": "npx playwright test tests/"`. No `npm ci`/`npm run build` of its own deps in any PM workflow.
- **Confirm first:** does anything build/deploy `presentations` in CI, and does its `test` render routes needing the
  PLAN_FORMAT §9 playwright gate, or is it a static slides build? Tag `[UI]` only if it serves routes.

## Todos

- [ ] [AGENT] P3. Confirm CI footprint — grep PM workflows + any deploy path for `presentations` install/build. Record
      that no workflow runs `npm ci`/`npm install` for its deps (only the unrelated global claude-code install).
      **Gate:** explicit confirmation (grep output) that nothing in CI installs/builds presentations' deps.
- [ ] [AGENT] P3. Generate `presentations/pnpm-lock.yaml` via `pnpm import` from `presentations/package-lock.json`,
      `git rm presentations/package-lock.json`, add `"packageManager": "pnpm@<same-major-as-UI-repo>"`. **Gate:**
      `pnpm install --frozen-lockfile` (in `presentations/`) clean; no `package-lock.json` present.
- [ ] [AGENT] P3. Fix any phantom deps; run the project's `test`/build. If it serves routes, add the `[UI]` tag +
      playwright gate to the ship todo; if static, note it's exempt with evidence. **Gate:** `pnpm test` (playwright)
      green; phantom deps declared + re-locked.
- [ ] [AGENT] P3. Ship + verify. Quickmerge; confirm dedup (`links≥2` on a `.pnpm` file). **Gate:**
      `unified-trading-pm@<sha>` | (`pw:L2 ✓` + regression spec IF it serves routes, else cited static-exempt) | dedup
      `links≥2` cited.

## Codex SSOTs

- Parent tracker recipe + `codex/06-coding-standards/ui-testing-layers.md` (§9 gate, if routes) +
  `codex/08-workflows/ci-cd-flow.md`.

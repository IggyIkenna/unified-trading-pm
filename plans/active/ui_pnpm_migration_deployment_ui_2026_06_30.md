---
doc_type: plan
title: Migrate deployment-ui from npm to pnpm (+ CI swap)
summary:
  Migrate deployment-ui to pnpm — import the lockfile, fix any phantom deps under pnpm's strict layout, swap
  ui-quality-gates-v2.yml from npm ci to pnpm, verify build + tests + playwright + CI green + store dedup.
status: draft
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [pnpm, node, ci, ui, migration]
related: [./ui_pnpm_migration_2026_06_30.md, ./ui_pnpm_migration_tooling_prep_2026_06_30.md]
created: 2026-06-30
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: ui-developer
drift_direction: advance-code
depends_on: [ui_pnpm_migration_tooling_prep_2026_06_30]
last_updated: 2026-06-30
locked_by: live-defi-rollout
locked_since: 2026-06-30
source: [node_modules_dedup_2026_06_29.md]
---

# Migrate deployment-ui → pnpm

> Parent tracker `ui_pnpm_migration_2026_06_30.md` holds the full canonical recipe + rationale — read it first. Single
> agent, single PR. Independent of the other two repo migrations (run in parallel).

## Pre-audit (this repo)

- Build: Vite — `"build": "tsc && vite build"`; lint `eslint src`; test `vitest run`; node `>=22`.
- CI: `.github/workflows/ui-quality-gates-v2.yml` — `actions/setup-node@v5`, `cache: npm`, `npm ci` (line ~71).
- Committed `.npmrc` = `legacy-peer-deps=true` — **KEEP** (portable peer-dep setting; not a store path).
- Real UI with routes → PLAN_FORMAT §9 playwright gate applies.

## Todos

- [ ] [AGENT][UI] P2. Generate `pnpm-lock.yaml` via `pnpm import` from `package-lock.json`, `git rm package-lock.json`,
      add `"packageManager": "pnpm@<same-major-as-UI-repo>"` to `package.json`. Keep the existing `.npmrc`
      (`legacy-peer-deps=true`). **Gate:** `pnpm install --frozen-lockfile` resolves clean with no `package-lock.json`
      present.
- [ ] [AGENT][UI] P2. Fix phantom dependencies surfaced by pnpm's strict layout — for every `tsc`/`vite build`/`vitest`
      failure caused by an undeclared transitive import, add the package explicitly to `package.json` and re-lock. No
      `shamefully-hoist` unless a dep is genuinely broken under symlinks (document as follow-up if so). **Gate:**
      `pnpm build` and `pnpm test` (vitest) both green locally.
- [ ] [AGENT][UI] P2. Swap CI in `ui-quality-gates-v2.yml` — `pnpm/action-setup@v6` + setup-node `cache: pnpm` +
      `pnpm install --frozen-lockfile`; `npm run <script>` → `pnpm <script>`. Mirror
      `unified-trading-system-ui/.github/workflows/ui-quality-gates-v2.yml`. Check whether a PM workflow-template
      governs this file before editing (don't hand-edit a governed copy). **Gate:** `quality-gates-v2` green on the
      branch via pnpm; no `npm ci` remains in the repo's workflows.
- [ ] [AGENT][UI] P2. Ship + verify. Quickmerge; confirm CI green; confirm dedup (`stat -c '%h %i'` on a
      `node_modules/.pnpm/<pkg>@<ver>/...` file shows `links≥2`). **Gate:** `deployment-ui@<sha>` | `pw:L2 ✓` |
      regression: `tests/smoke/routes.spec.ts` (or repo's smoke path) | CI `quality-gates-v2` green | dedup `links≥2`
      cited.

## Codex SSOTs

- Parent tracker recipe + `codex/06-coding-standards/ui-testing-layers.md` (§9 gate) +
  `codex/08-workflows/ci-cd-flow.md`.

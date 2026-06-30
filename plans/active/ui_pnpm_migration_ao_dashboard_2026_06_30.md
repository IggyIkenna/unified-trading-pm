---
doc_type: plan
title: Migrate agent-orchestrator/dashboard from npm to pnpm (+ deploy CI swap)
summary:
  Migrate the agent-orchestrator dashboard to pnpm — import the lockfile, fix phantom deps, swap deploy-dashboard.yml
  from npm ci + npm run build to pnpm, verify the DEPLOY build end-to-end + tests + playwright + store dedup.
status: draft
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [pnpm, node, ci, ui, migration, deploy]
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

# Migrate agent-orchestrator/dashboard → pnpm

> Parent tracker `ui_pnpm_migration_2026_06_30.md` holds the full canonical recipe — read it first. Single agent, single
> PR. Independent of the other two repo migrations (run in parallel). **Higher blast radius:** the CI install is in a
> DEPLOY workflow, so a broken install breaks dashboard deployment — verify the deploy build, not just a local build.

## Pre-audit (this repo)

- Lives at `agent-orchestrator/dashboard/` (subdir of the agent-orchestrator repo).
- Build: Vite — `"build": "tsc --noEmit && vite build"`; test `vitest run`; node 20 (per CI).
- CI: `.github/workflows/deploy-dashboard.yml` — `actions/setup-node@v5`, node "20", `npm ci` (line ~65) +
  `npm run build` (line ~69). This is the **deploy** path.
- Real UI with routes → PLAN_FORMAT §9 playwright gate applies.

## Todos

- [ ] [AGENT][UI] P2. Generate `dashboard/pnpm-lock.yaml` via `pnpm import` from `dashboard/package-lock.json`,
      `git rm dashboard/package-lock.json`, add `"packageManager": "pnpm@<same-major-as-UI-repo>"` to
      `dashboard/package.json`. **Gate:** `pnpm install --frozen-lockfile` (in `dashboard/`) resolves clean; no
      `package-lock.json` present.
- [ ] [AGENT][UI] P2. Fix phantom dependencies surfaced by pnpm's strict layout (undeclared transitive imports caught by
      `tsc --noEmit`/`vite build`/`vitest`) — declare explicitly + re-lock; no `shamefully-hoist` unless genuinely
      required (document if so). **Gate:** `pnpm build` (`tsc --noEmit && vite build`) and `pnpm test` green locally.
- [ ] [AGENT][UI] P2. Swap CI in `deploy-dashboard.yml` — `pnpm/action-setup@v6` + setup-node `cache: pnpm` +
      `pnpm install --frozen-lockfile` + `pnpm build`; keep node 20. Confirm no PM workflow-template governs this file
      before editing. **Gate:** the deploy workflow's build job is green via pnpm on the branch; no `npm ci` remains.
- [ ] [AGENT][UI] P2. Ship + verify the deploy build end-to-end. Quickmerge; confirm the dashboard deploy workflow
      builds + deploys green; confirm dedup (`links≥2` on a `.pnpm` file). **Gate:** `agent-orchestrator@<sha>` |
      `pw:L2 ✓` | regression: `dashboard/tests/smoke/*.spec.ts` (or repo's smoke path) | deploy-dashboard build green |
      dedup `links≥2` cited.

## Codex SSOTs

- Parent tracker recipe + `codex/06-coding-standards/ui-testing-layers.md` (§9 gate) +
  `codex/08-workflows/ci-cd-flow.md`.

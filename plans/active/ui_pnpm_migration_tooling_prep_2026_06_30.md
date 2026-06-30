---
doc_type: plan
title: pnpm migration prep — make workspace node tooling pnpm-aware + clean the UI-repo stray
summary:
  Fix the npm-assuming workspace tooling (run-version-alignment.sh, dev-start.sh, restart-deployment-stack.sh) to be
  pnpm-aware, remove the stray package-lock.json polluting unified-trading-system-ui, and correct the gitignore/codex
  "symlink to shared install" contradiction — so the 3 repo migrations aren't re-polluted.
status: draft
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, unified-trading-system-ui]
scope: [engineer]
tags: [pnpm, node, tooling, cleanup, ci]
related: [./ui_pnpm_migration_2026_06_30.md]
created: 2026-06-30
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: infra-engineer
drift_direction: advance-code
last_updated: 2026-06-30
locked_by: live-defi-rollout
locked_since: 2026-06-30
source: [node_modules_dedup_2026_06_29.md]
---

# pnpm migration prep — pnpm-aware tooling + stray cleanup

> Parent tracker: `ui_pnpm_migration_2026_06_30.md`. This is the shared prerequisite for the 3 repo migrations — land it
> first so the npm-assuming alignment cron does not re-pollute a migrated repo. Single agent, single PR.

## Todos

- [ ] [AGENT] P2. Make `unified-trading-pm/scripts/repo-management/run-version-alignment.sh` pnpm-aware — detect a
      repo's package manager (presence of `pnpm-lock.yaml` ⇒ pnpm, else `package-lock.json` ⇒ npm) and emit the correct
      drift command (`pnpm install` vs `npm install`) instead of assuming npm for every UI repo. **Gate:** running the
      alignment check against `unified-trading-system-ui` reports pnpm + does NOT recommend `npm install`; against an
      npm repo it still recommends `npm install`. Cite the before/after output.
- [ ] [AGENT] P2. Make the dev-server fallbacks pnpm-aware — `scripts/dev/dev-start.sh` (line ~351) and
      `scripts/dev/restart-deployment-stack.sh` (line ~173) currently run a bare `npm install` when `node_modules` is
      missing; branch on the lockfile so a pnpm repo gets `pnpm install --frozen-lockfile`. **Gate:** grep shows no
      unconditional `npm install` for a pnpm repo path; a dry-run against the UI repo picks pnpm.
- [ ] [AGENT] P2. Remove the stray from `unified-trading-system-ui`:
      `rm -rf node_modules package-lock.json && pnpm     install --frozen-lockfile` in the repo root, re-homing it on
      the pnpm store. (Both are gitignored — this is a local working-tree cleanup, nothing to commit in the UI repo.)
      **Gate:** `git -C unified-trading-system-ui status` clean of `package-lock.json`; a `.pnpm` file shows `links≥2`
      (hardlinked to the workspace store) via `stat -c '%h %i'`.
- [ ] [AGENT] P2. Correct the gitignore "symlink to shared install" comments
      (`scripts/propagation/templates/gitignore-node.txt:12`, `deployment-ui/.gitignore:77`) to match the codex SSOT
      `codex/05-infrastructure/per-tab-worktrees.md:569-579` (per-slot real `node_modules`, store is the shared layer —
      there is NO symlink-to-shared mechanism and none exists in code). **Gate:** the comments no longer claim a
      shared-install symlink; reviewer confirms they match the codex model.
- [ ] [AGENT] P2. Document the host-local pnpm store convention (workspace-derived `store-dir`, never a committed
      absolute path — mirror the uv-cache "CI owns its own store" rule) where the uv shared-cache convention is
      recorded, so the migration child plans and future hosts apply it consistently. **Gate:** the convention is written
      next to the uv-cache SSOT and cross-linked from the parent tracker.

## Notes

- This plan does NOT migrate any repo's package manager — it only fixes tooling + cleans the stray, so the 3 migrations
  land on a clean, pnpm-aware workspace.
- `unified-trading-system-ui` changes here are working-tree-local (gitignored stray); the committed changes are in
  `unified-trading-pm` (scripts + gitignore template) only.

## Codex SSOTs

- `codex/05-infrastructure/per-tab-worktrees.md` — on-demand artifact model (corrects the gitignore contradiction).
- `codex/08-workflows/ci-cd-flow.md` — quickmerge / commit discipline.

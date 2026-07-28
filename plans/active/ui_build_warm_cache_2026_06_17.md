---
doc_type: plan
title: UI build warm-cache — keep the UI QG build cache warm so only changed code rebuilds
summary:
  Keep the UI quality-gate build cache warm so incremental rebuilds only recompile changed code, not the full app.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [deployment-ui, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: [ui, build-cache, quality-gates, performance, incremental-build]
related: [/plans/archive/2026_06/quality_gates_speed_and_config_ssot_2026_06_09.md]
created: 2026-06-17
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
last_updated: 2026-07-27
locked_by: live-defi-rollout
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  [
    MIGRATED FROM quality_gates_speed_and_config_ssot_2026_06_09.md § "UI build warm-cache" (2026-06-17),
    slot-3 2026-06-10 — cold-clone UI build tripped the 90s QG gate; warm rebuild = 365 ms,
  ]
assigned_role: ui_developer
drift_direction: advance-code
---

# UI build warm-cache

> **MIGRATED FROM** `quality_gates_speed_and_config_ssot_2026_06_09.md` (2026-06-17) so the QG-speed/config plan could
> close its completed core. These are UI-repo build-performance items, **distinct from the Python-fleet QG-speed work**
> (which is done). They need a **UI-capable slot** + the **playwright gate** (`pw:L2 ✓` + a regression spec) for any
> change touching `deployment-ui` / `unified-trading-system-ui` source — see CLAUDE.md § "UI changes — playwright gate".
> Do NOT rush them through a non-UI slot.
>
> **Operator direction (2026-06-10)**: if fundamental deps don't change, the build cache should be warm ALWAYS — only
> our code rebuilds.

- [x] ✅ [CODE] P2. `tsc` incremental for UI repos: `"incremental": true` + gitignored `.tsbuildinfo` (deployment-ui +
      unified-trading-system-ui tsconfigs) — only changed files re-check; cold cost limited to a fresh clone's first
      build. Repo: deployment-ui, unified-trading-system-ui. **[UI]** — needs `pw:L2 ✓` + regression spec. — **CONFIRMED
      ALREADY DONE (verified 2026-07-27, read both files directly)**: `unified-trading-system-ui/tsconfig.json` carries
      `"incremental": true` + `"tsBuildInfoFile": "./build-artifacts/tsbuildinfo"` (gitignored via `/build-artifacts/`
      in `.gitignore:40`); `deployment-ui/tsconfig.json` carries `"incremental": true` +
      `"tsBuildInfoFile": "./node_modules/.tmp/tsconfig.tsbuildinfo"` (gitignored — under `node_modules`). No code
      change needed. `ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s D28 entry was flagging this (+ item 2 below) as
      fresh dispatch pending `[UI]`/`pw:L2` — corrected there to reflect this half is already shipped (unified-trading-
      pm this commit).
- [ ] [CODE] P2. Pre-warm in `setup.sh`: run one `npm run build` at clone-setup time so the QG gate never pays the
      cold-cache cost (the cold build moves to where there is no timeout). Repo: unified-trading-pm
      (`scripts/quality-gates-base` setup template) + the two UI repos. — **CONFIRMED STILL OPEN (verified
      2026-07-27)**: `unified-trading-pm/scripts/setup.sh` runs `npm install` for UI repos (lines 73/187/229) but no
      `npm run build` pre-warm step exists anywhere in `scripts/setup.sh`, `scripts/dev/setup-tab-worktrees.sh`, or
      `scripts/workspace/setup-dev-environment.sh`. Genuinely still open work, not stale.
- [ ] [INFRA] P3. **Migrate to pnpm's global content-addressable store** for UI repos: hardlinked node_modules →
      identical inodes across ALL slot clones → OS page cache warm fleet-wide while deps are unchanged (npm copies
      per-clone: N× disk + N× cold reads). **Operator decision 2026-07-27
      (`june_2026_vintage_audit_findings_2026_07_27.md` §5#33): APPROVED — migrate.** No longer an evaluate-first
      "Decision item"; this is now real implementation scope: (1) convert `package-lock.json` → `pnpm-lock.yaml` in both
      `deployment-ui` + `unified-trading-system-ui`, (2) update `scripts/setup.sh`'s UI-repo install step + any CI
      workflow install steps (`npm ci`/`npm install` → `pnpm install --frozen-lockfile`) fleet-wide, (3) verify the
      hardlinked-store behavior across per-slot worktree clones. Repos: deployment-ui, unified-trading-system-ui,
      unified-trading-pm (setup.sh + CI templates). **[UI]** — touches UI repos' package manifests/lockfiles and CI
      install steps, so treat as needing `pw:L2 ✓` + a regression spec like the sibling UI-source items above, not a
      PM-only change. Kept here rather than dispatched into `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (D20)
      because that batch's `assigned_role` is `cicd`, not `ui_developer` — same UI-capable-role/playwright-gate blocker
      D28 already names for items 1-2; D20 there updated to reflect the decision is made (2026-07-27) but the dispatch
      blocker is unchanged.
- [x] ✅ [SCRIPT] P3. base-ui.sh: one automatic retry on the build-timeout class (cold-trip passes on retry; a genuine
      hang fails twice) — removes the human re-run without weakening the budget. Repo: unified-trading-pm
      (`scripts/quality-gates-base/base-ui.sh`); exercise against a UI repo build before shipping. — **MIGRATED
      2026-07-26** verbatim into `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (dispatched `[SCRIPT] P3` todo, cites
      this doc as Source) — still open there, dual-tracked until it ships. Not yet independently re-verified as done in
      code as of 2026-07-27.

## Success criteria

- A warm-cache UI QG build re-checks only changed files (sub-second incremental); a fresh clone pays the cold build once
  (at setup, off the timed gate path).
- No UI source change ships without `pw:L2 ✓` + a cited regression spec (playwright gate).

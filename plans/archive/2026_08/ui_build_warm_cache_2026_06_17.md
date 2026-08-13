---
doc_type: plan
title: UI build warm-cache — keep the UI QG build cache warm so only changed code rebuilds
summary:
  Keep the UI quality-gate build cache warm so incremental rebuilds only recompile changed code, not the full app.
status: complete
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
last_updated: 2026-08-04
locked_by:
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
effort: xhigh
drift_direction: advance-code
context_scope:
  [
    /codex/06-coding-standards/ui-testing-layers.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/june_2026_vintage_audit_findings_2026_07_27.md,
    scripts/setup.sh,
    scripts/quality-gates-base/base-ui.sh,
    /plans/archive/2026_06/quality_gates_speed_and_config_ssot_2026_06_09.md,
  ]
---

> **🗄️ ARCHIVED 2026-08-12 (/plan-reconcile)** — `status: complete`, all todos done, `locked_by` cleared (corpus-wide
> placeholder bug, option B ruling).

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
- [x] ✅ [CODE] P2. Pre-warm in `setup.sh`: run one `npm run build` at clone-setup time so the QG gate never pays the
      cold-cache cost (the cold build moves to where there is no timeout). Repo: unified-trading-pm
      (`scripts/quality-gates-base` setup template) + the two UI repos. — **CONFIRMED STILL OPEN (verified
      2026-07-27)**: `unified-trading-pm/scripts/setup.sh` runs `npm install` for UI repos (lines 73/187/229) but no
      `npm run build` pre-warm step exists anywhere in `scripts/setup.sh`, `scripts/dev/setup-tab-worktrees.sh`, or
      `scripts/workspace/setup-dev-environment.sh`. Genuinely still open work, not stale. — **PARTIALLY SHIPPED
      2026-07-29**: added a new `[UI.5] PRE-WARM BUILD CACHE` step to `unified-trading-pm/scripts/setup.sh` (skips when
      `.next/cache` or the tsc `tsbuildinfo` marker already exists, otherwise runs `$PKG_MGR run build` once — no
      `--silent`, since pnpm forwards an unrecognized trailing flag through a compound script's last command and breaks
      Vite's own CLI). Live-verified in BOTH UI repos: `unified-trading-system-ui` correctly detects an already-warm
      `.next/cache` and skips; `deployment-ui` correctly runs a real cold `pnpm run build` (tsc + vite build) to
      completion and regenerates `node_modules/.tmp/tsconfig.tsbuildinfo`. **Shipped to unified-trading-system-ui
      only**: `unified-trading-system-ui@42439593`, `quality-gates.sh` green (341s), landed `live-defi-rollout`.
      **`deployment-ui`'s copy could NOT ship at the time** — `quickmerge.sh`'s re-gate step hit an apparent
      `vitest --coverage` failure (24-25% vs the 64-70% thresholds across all 4 metrics), confirmed via `git stash` to
      reproduce independently of this change on `live-defi-rollout` HEAD; filed as
      `/plans/archive/issues/deployment_ui_vitest_coverage_gate_broadly_red_2026_07_29.md` (P1, now archived-resolved).
      **RESOLVED 2026-07-30 (`deployment-ui@3c7e2a8`)**: root-caused as an environment artifact, not a real coverage gap
      — a `pnpm-workspace.yaml` missing `packages:` broke local/agent `pnpm install` under pnpm 9.x (CI stayed green
      only because it pins pnpm 10.x); the reporting session's coverage numbers came from a broken/stale install, not
      genuinely uncovered components. Fixed + verified green
      (`Statements 72.32%|Branches 64.5%|Functions     68.79%|Lines 74.49%`, all ≥ threshold) — see the issue doc (now
      archived) for the full writeup. `deployment-ui`'s gate is unblocked; the deployment-ui copy of `setup.sh` is STILL
      not in sync with the template's pre-warm-cache step —
      `cp unified-trading-pm/scripts/setup.sh deployment-ui/scripts/setup.sh` + commit + ship is the remaining open work
      on this todo. — **SHIPPED 2026-08-03 (`deployment-ui@7086565`)**: synced `deployment-ui/scripts/setup.sh` from the
      unified-trading-pm template (`cp` — files now identical), live-verified both branches of the `[UI.5]` step
      (`--force` runs a real cold `pnpm run build` and regenerates `node_modules/.tmp/tsconfig.tsbuildinfo`; a plain run
      correctly detects the already-warm cache and skips). `quality-gates.sh --no-fix` green (42s, 101 tests, coverage
      73.53%), shipped via `quickmerge.sh --agent`, landed `live-defi-rollout`. Both UI repos' `setup.sh` are now in
      sync with the template — todo fully closed.
- [x] ✅ [INFRA] P3. **Migrate to pnpm's global content-addressable store** for UI repos: hardlinked node_modules →
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
      blocker is unchanged. — **RE-VERIFIED 2026-08-04 (na-eligibility-audit): sub-parts (1) and (2) are DONE; sub-part
      (3) is the sole remaining gap.** Sub-part (1) (`package-lock.json` → `pnpm-lock.yaml`):
      `unified-trading-system-ui` has shipped `pnpm-lock.yaml` since its first commit and deleted `package-lock.json` in
      `unified-trading-system-ui@474bba76` (2026-04-17, predates this todo's 2026-06-17 creation); `deployment-ui`
      migrated in `deployment-ui@de5b7af` (2026-07-29). Sub-part (2) (setup.sh + CI install steps):
      `unified-trading-pm/scripts/setup.sh` auto-detects pnpm/yarn/npm since `unified-trading-pm@32ea69f5b`
      (2026-05-20); both UI repos' CI workflows already run `pnpm install --frozen-lockfile`. Sub-part (3)
      (hardlinked-store verification) is NOT done — empirically tested by comparing an identical pnpm-store package file
      across 5 slot clones (`.tabs/2,4,6,7,8`, same filesystem): every clone shows `nlink=1` + a distinct inode, i.e. no
      cross-clone hardlink dedup is occurring despite `pnpm-lock.yaml` being in place — the same failure signature as
      the parallel uv/`.venv` investigation in `host_root_disk_full_transient_2026_07_13.md`. Remaining scope for this
      todo narrows to: root-cause why pnpm's content-addressable store isn't hardlinking `node_modules` across slot
      clones. Stays `[UI]`+NA per the standing citation above, though the narrowed scope is a tooling/infra
      investigation touching no UI source — a future pass may find the `[UI]` gate no longer applies to what's left,
      same reasoning this doc already applied to the setup.sh item. **DONE 2026-08-09 (agent slot 24, via
      `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 10, verified ancestor commits) — sub-part 3 root-caused +
      fixed.** Not a pnpm config gap: the default store (`~/.local/share/pnpm/store`) sits on a DIFFERENT mount boundary
      than `.tabs/` on this host — raw `ln` probes confirmed `.tabs/<N>` <-> `.tabs/<M>` hardlinks succeed while
      anything outside `.tabs/` fails `EXDEV`, and `pnpm install`'s `auto` import method silently falls back to a full
      copy on that failure with no warning. Fix: `setup.sh` now detects a `.tabs/<N>` ancestor and relocates pnpm's
      `store-dir` to `<.tabs>/.pnpm-store` via `npm_config_store_dir`. Evidence: two independent installs sharing the
      relocated store show the identical inode with `nlink=3` (was `nlink=1` + distinct inode per clone pre-fix),
      confirmed via a real `bash scripts/setup.sh --force` end-to-end run, not just a raw `pnpm install`. Shipped:
      `deployment-ui@33c6a02`, `unified-trading-system-ui@e70aeeb8`, `unified-trading-pm@e9e344a66`. Adjacent finding
      (same mount-boundary failure applies to `UV_CACHE_DIR`) filed separately, out of this todo's repo/scope — see
      `issues/tabs_mount_boundary_defeats_uv_cache_hardlink_dedup_2026_08_09.md`.
- [x] ✅ [SCRIPT] P3. base-ui.sh: one automatic retry on the build-timeout class (cold-trip passes on retry; a genuine
      hang fails twice) — removes the human re-run without weakening the budget. Repo: unified-trading-pm
      (`scripts/quality-gates-base/base-ui.sh`); exercise against a UI repo build before shipping. — **MIGRATED
      2026-07-26** verbatim into `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (dispatched `[SCRIPT] P3` todo, cites
      this doc as Source) — still open there, dual-tracked until it ships. Not yet independently re-verified as done in
      code as of 2026-07-27. — **RE-VERIFIED 2026-08-04 (na-eligibility-audit): shipped.**
      `unified-trading-pm@80148edde` (2026-08-02, "fix(ci): base-ui.sh — one automatic retry on the build-timeout
      class") matches this item exactly (retry gated on timeout exit codes 124/137 only); also closed the same day in
      `ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s dual-tracked copy. The 2026-07-27 "not yet independently
      re-verified" note above is now stale — this item is genuinely done.

## Success criteria

- A warm-cache UI QG build re-checks only changed files (sub-second incremental); a fresh clone pays the cold build once
  (at setup, off the timed gate path).
- No UI source change ships without `pw:L2 ✓` + a cited regression spec (playwright gate).

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): KEEP-NA, valid — both open items are `[UI]`-gated
(playwright `pw:L2 ✓` + a cited regression spec, per CLAUDE.md's UI gate), and this doc already records the dated reason
they were deliberately kept OUT of the ci dispatch batch:
`/plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s `assigned_role` is `cicd`, not `ui_developer`
(D20/D28, 2026-07-26/27). The pnpm migration is operator-APPROVED as scope but the role/gate blocker is unchanged.
Established ruling confirmed present, not re-litigated.

**na-eligibility-audit 2026-08-04** (tranche `ci`, autonomous): **KEEP-NA, stale items — corrected.** Re-read end to
end. The 2026-07-30 verdict's bottom line (stay NA, `[UI]`-gated, role-mismatch blocker unchanged) still holds —
re-confirmed via two further independent citations since (`ci_satellite_ao_dispatch_batch4_2026_07_31.md`,
`ci_satellite_ao_dispatch_batch5_2026_08_02.md` D5-7, both declining to extract this item). But the sole open checkbox's
own description had gone stale: sub-parts (1) `package-lock.json`→`pnpm-lock.yaml` and (2) setup.sh/CI install-step
migration were BOTH already shipped (`unified-trading-system-ui@474bba76` 2026-04-17, `deployment-ui@de5b7af`
2026-07-29, `unified-trading-pm@32ea69f5b` 2026-05-20) — none of that landed back into this doc's tracking, so 3
subsequent audit/closeout passes (2026-07-30, -31, 08-02) kept repeating a stale "still needs its own plan" read without
re-checking ground truth. Corrected the checkbox's inline text with commit citations; only sub-part (3) (cross-clone
pnpm-store hardlink dedup, empirically confirmed NOT occurring) remains genuinely open. Also corrected a second stale
annotation on the already-closed base-ui.sh retry item (shipped `unified-trading-pm@80148edde` 2026-08-02; its own
trailing note still said "not yet verified as of 2026-07-27"). `assigned_vm` stays NA — not reclassifying; the
citation-based role/gate blocker on the narrowed remaining scope is unaffected by this correction.

## Progress Log

- **context-scout 2026-08-03**: refreshed context_scope (6 entries, trimmed from 7) — dropped the generic parent epic
  pointer (`infrastructure_master.md`); kept both source scripts (`setup.sh`, `base-ui.sh`) since the sole open todo
  (pnpm migration) directly edits both.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — UI-gated tooling investigation, locked_by: live-defi-rollout

- **2026-08-09 (`ci_satellite_ao_dispatch_batch6_finalize` todo 1, slot 31)**: sub-part 3 (the sole remaining open
  checkbox) shipped via batch6 todo 10 — verified `deployment-ui@33c6a02`, `unified-trading-system-ui@e70aeeb8`, and
  `unified-trading-pm@e9e344a66` are all ancestors of `origin/live-defi-rollout` before flipping. Zero open checkboxes
  and no remaining open prose work — `status: active` → `complete` (`resolved` is not a valid `doc_type: plan` status
  per the frontmatter schema; `complete` is the terminal value for plans). Not archived: `locked_by: live-defi-rollout`
  is non-empty, which blocks archival without an explicit `[unlock-plan]` decision per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`; this reconciliation todo's scope is the
  source-doc flip/resolve step only, not archival — left for a future archival-sweep pass to ask about unlocking.

- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).

**na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5): SUPERSEDED BY LIVE EVENT — written
against a since-changed state; correcting rather than leaving stale. At classification time this doc had 1 open item
(pnpm hardlink-dedup investigation) and I verdicted KEEP-NA valid; `ci_satellite_ao_dispatch_batch6_finalize` todo 1
(slot 31) shipped that item concurrently and flipped `status: active` → `complete` (0 open checkboxes, 0 open prose
work) before this commit landed. Current state: KEEP-NA correct as a terminal classification (not ARCHIVE) only because
`locked_by: live-defi-rollout` blocks archival without an explicit `[unlock-plan]` decision — not this run's to clear
autonomously, per the doc's own 2026-08-09 note above. No `assigned_vm` change; no incremental-skip body-hash recorded
since the doc changed again after this marker was drafted — next run should re-hash fresh.

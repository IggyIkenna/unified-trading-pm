---
title: Worktree LDR-unification — drop per-tab branches, slots on live-defi-rollout (Path B reference-clones)
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P2
status: active
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 6.4
created: 2026-06-08
orchestrated_by: plans/active/cicd_contract_hardening_2026_06_01.md
related_plans:
  - plans/active/per_agent_worktrees_2026_05_10.md
  - plans/active/qg_commit_quality_boundary_and_slot_ff_push_2026_06_03.md
  - plans/active/quickmerge_dep_content_sync_and_strict_enforcement_2026_06_08.md
  - plans/active/staging_clean_start_and_stale_pr_hygiene_2026_06_08.md
source:
  - chat design session 2026-06-08 (operator + vm-planning)
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Worktree LDR-unification

> **Orchestrated by** `cicd_contract_hardening_2026_06_01.md` (CI master). **SEQUENCED LAST — runbook step 6**
> (operator-sequenced 2026-06-08): execution is **deferred** until the pipeline is healthy and green end-to-end (runbook
> steps 0–5 done, `main == LDR` fleet-wide), because **live slot-cron / tab-branch work is ongoing right now** and
> retiring the branches + crons mid-flight would disrupt it. Design/spike (Phase 0) may be drafted earlier, but the
> migration itself (Phases 1–3) does NOT start until step 6.

## Problem (what we found)

The per-tab **branch** (`tab/<op>/N`) is **not a deliberate architectural choice** — it's a workaround for git's "can't
check out the same branch in two worktrees" constraint (`per_agent_worktrees_2026_05_10.md` Path A). The real isolation
is **worktree-level** (separate index/working-tree → solves the 4 shared-`.git/index` foot-guns). The branch is
incidental, and it buys us a continuous **sync tax**:

- `slot-cron-ff-pull.sh` (every 5 min, LDR→tab)
- `tab-mirror-to-ldr.yml` GHA (tab→LDR FF, both legs)
- per-slot branch maintenance in `setup-tab-worktrees.sh` (`--add-slot`/`--reset-slot` rebase paths)
- orchestrator slot↔branch tracking + the diverged-tab recovery recipes in CLAUDE.md

**Commit attribution is already in the author NAME field (`[slot-<N>·<host>]`), fully independent of branch** — so agent
identity survives a branch change unchanged (composes with `quickmerge_dep_content_sync_and_strict_enforcement` §
agent-naming).

## Decision — Path B, NOT shared-`.git`-same-branch

The literal "same branch, shared `.git`" form is the one variant that fails: git refuses it, and forcing it gives
**commit-time ref races** on the shared `live-defi-rollout` ref/HEAD (today's model defers all contention to _push_
time, mediated by remote atomicity). The sound form is **Path B** (documented + un-chosen in
`per_agent_worktrees_2026_05_10.md:198`, only because "Path A worked smoothly with Cursor"):

- **Per-slot `git clone --reference ${WORKSPACE_ROOT}/<repo> --shared <url> .tabs/<N>/<repo>`** — separate `.git` per
  slot (no ref races), shared object store via `--reference` (no disk blowup), each clone **independently on
  `live-defi-rollout`**. Default branch = LDR.
- Contention moves to **LDR push-time** (rebase-on-reject) — already handled by `quickmerge` STAGE 0.4 Not-Behind Gate.

## Pre-audit (blast radius)

- [ ] [SCRIPT] P2. Grep every consumer of `tab/<op>/N` branch naming: `setup-tab-worktrees.sh`, `slot-cron-ff-pull.sh`,
      `slot-git-status-report.sh`, `slot-master-rebase.sh`, `tab-mirror-to-ldr.yml`, `verify-slot-host-symmetry.sh`,
      `agent-orchestrator/server/worktree_clean_check.py`, `workspace-manifest.json` base-branch overrides, and the
      CLAUDE.md / `codex/05-infrastructure/per-tab-worktrees.md` rule surface. Build the removal/rewrite manifest BEFORE
      any change.

## Phase 0 — Spike (research)

- [ ] [SCRIPT] P2. Path-B spike: stand up 2 reference-clone slots on `live-defi-rollout`, confirm Cursor/VSCode git
      integration, shared-object disk footprint, and concurrent commit+push behaviour (two slots push LDR
      near-simultaneously → rebase-on-reject converges). Success: no ref-race, disk ≈ Path A, IDE clean.

## Phase 1 — quickmerge LDR-direct (depends: Phase 0)

- [ ] [SCRIPT] P2. Change `quickmerge.sh`: on a slot that is **on LDR** (no tab branch), commit-to-LDR (push LDR) +
      **open the LDR→staging PR directly** — retire the tab→LDR mirror hop. Forced staging-PR existence is a HARD
      post-condition of every code quickmerge (cross-ref `quickmerge_dep_content_sync_and_strict_enforcement` § strict).
- [ ] [SCRIPT] P2. Keep STAGE 0.4 Not-Behind reconcile (ff→rebase-autostash) as the LDR push-contention mediator.

## Phase 2 — Migrate bootstrap + retire sync machinery (depends: Phase 1)

- [ ] [SCRIPT] P2. Rewrite `setup-tab-worktrees.sh` to provision Path-B reference-clones on LDR (`--init`/`--add-slot`/
      `--reset-slot` collapse to clone + clean-check, no branch create/rebase).
- [ ] [SCRIPT] P2. **Retire** `tab-mirror-to-ldr.yml` (fleet rollout-template delete) + `slot-cron-ff-pull.sh` (replace
      with a thin `git -C <slot> pull --ff-only origin live-defi-rollout`), and drop the per-slot-branch reset paths.
- [ ] [SCRIPT] P2. Add a **drift-detection cron** (replaces the divergence half of tab-mirror): flag any slot whose HEAD
      is not an ancestor-or-equal of `origin/live-defi-rollout` (the only invariant left to police).

## Phase 3 — Rules + codex alignment (depends: Phase 2)

- [ ] [DOCS] P2. Rewrite CLAUDE.md + `codex/05-infrastructure/per-tab-worktrees.md`: remove tab-branch/upstream/
      diverged-tab recovery sections; replace with the Path-B LDR-direct model. Update `SUB_AGENT_MANDATORY_RULES.md` §
      git-discipline.
- [ ] [DOCS] P2. Update `agent-orchestrator/server/worktree_clean_check.py` base-branch logic (LDR for all; the AO
      `main` override is already removed).

## Success criteria

- Zero `tab/<op>/N` refs created; `git rev-parse --abbrev-ref HEAD == live-defi-rollout` on every slot.
- `slot-cron-ff-pull` + `tab-mirror` GHA deleted fleet-wide; drift-cron green.
- A 2-slot concurrent commit+quickmerge converges with no manual rebase.
- `verify-slot-host-symmetry.sh` passes under the new model.

## Codex SSOT updates

`codex/05-infrastructure/per-tab-worktrees.md` (rewrite), CLAUDE.md § Per-Tab Worktrees + § Git discipline,
`SUB_AGENT_MANDATORY_RULES.md` § git.

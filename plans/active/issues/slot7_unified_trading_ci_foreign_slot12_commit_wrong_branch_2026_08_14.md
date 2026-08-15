---
doc_type: issue
title:
  slot-7's unified-trading-ci checkout carries an unpushed slot-12-authored commit on branch `main` instead of
  `live-defi-rollout`
summary: >-
  Discovered incidentally while shipping an unrelated cross_cutting_satellite_ao_dispatch_batch13b todo from slot-7:
  `.tabs/7/unified-trading-ci` is checked out on branch `main` (Path-B topology requires every slot clone directly on
  `live-defi-rollout`) with `main`'s upstream pointed at `origin/live-defi-rollout`, and HEAD carries one commit
  (`25b6605c09319926a5c214366c31327521010d88`, "fix(ci): stop UV_VERSION resolution racing PM promote-branch deletion")
  authored `ikennaigboaka [slot-12·planning]` at 2026-08-14T03:23:32Z — i.e. slot-12's identity, not slot-7's — that is
  genuinely NOT an ancestor of `origin/live-defi-rollout` (verified via `git merge-base --is-ancestor HEAD
  origin/live-defi-rollout` → no, after a fresh `git fetch`). Not touched or acted on: per RULES.md § 1 ("don't touch
  dirty files in other workspace areas... untracked files / mid-edit dirty state in another agent's tree IS in-flight
  work") this reads as another slot's committed-but-unshipped work that ended up in slot-7's checkout, not slot-7's own
  WIP to push blind.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-ci]
scope: [engineer, admin]
tags: [git, multi-agent-safety, per-tab-worktrees, slot-collision]
related:
  - /codex/05-infrastructure/per-tab-worktrees.md
  - /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md
created: 2026-08-14
author: slot-7 (worker, infra)
parent_epic: infrastructure_master
priority: P3
source: >-
  Incidental discovery during cross_cutting_satellite_ao_dispatch_batch13b-ae3464d903fd (the ldr-to-main-promote.yml
  rate-mismatch fix) — the slot's git-status-red auto-nudge kept re-flagging unified-trading-ci as AHEAD=1 across
  several boot/progress calls even after slot-7's own repos were confirmed clean.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-infra
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: ""
last_updated: 2026-08-14
context_scope:
  [/codex/05-infrastructure/per-tab-worktrees.md, /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md]
---

# slot-7's unified-trading-ci checkout: foreign slot-12 commit on the wrong branch

## What I found

- `.tabs/7/unified-trading-ci` HEAD is on a local branch literally named `main`, not `live-defi-rollout` — a Path-B
  topology violation (every slot clone should be checked out directly on `live-defi-rollout`, no tab branch, no
  alternate branch name).
- That `main` branch's upstream tracking ref is `origin/live-defi-rollout` (not `origin/main`), which is itself an
  unusual pairing.
- HEAD carries exactly one commit ahead of `origin/live-defi-rollout`: `25b6605c09319926a5c214366c31327521010d88` —
  `fix(ci): stop UV_VERSION resolution racing PM promote-branch deletion`, authored
  `ikennaigboaka [slot-12·planning] <ikennaigboaka@gmail.com>` at `2026-08-14 03:23:32 +0000`. Slot-7's own
  commit-identity convention (per `scripts/hooks/slot-identity-lib.sh`) would stamp `[slot-7·...]` — this commit's
  author string names slot-12, not this slot.
- Confirmed genuinely unpushed (not just a stale local ref) via a fresh `git fetch origin live-defi-rollout main` then
  `git merge-base --is-ancestor HEAD origin/live-defi-rollout` → exit non-zero (not an ancestor).
- The slot's AO-driven git-status-red auto-nudge repeated this same "unified-trading-ci: AHEAD=1 unpushed" message 7
  times across this session's boot/heartbeat/progress calls (message_ids 7678/7679/7685/7691/7697/7700/7707) — never
  resolving, unlike the sibling nudges for `instruments-service`/`agent-orchestrator`/`unified-trading-pm` which all
  cleared once their respective repos were pulled/shipped during this same session.

## Why it matters

- If this commit is genuine, finished slot-12 work, it is sitting un-shipped and un-gated (never ran quality-gates.sh
  Pass-1/Pass-2 in THIS checkout) — could represent lost/stranded work if slot-12's own session doesn't know it landed
  here instead of its own worktree.
- If it is a cross-slot checkout collision (two sessions somehow sharing or cross-referencing the same
  `unified-trading-ci` clone), that is the exact "Distinct failure mode" RULES.md/CLAUDE.md already document (shared
  index / wrong commit attribution) and should be root-caused, not just cleared.
- The branch-name deviation (`main` instead of `live-defi-rollout`) is itself worth checking against
  `worktree_clean_check.check_slot_branch_state`'s structural pre-spawn gate — that gate is supposed to quarantine a
  wrong-branch clone before a session ever starts working in it.

## Recommended decision

Not resolved by slot-7 this session — deliberately left untouched (foreign committed WIP, not verified safe to push, not
this task's repo). Needs a human or a dedicated diagnostic task to:

1. Confirm with slot-12 (or its session log) whether this commit is real finished work that should ship, or stray state
   to discard.
2. If real: verify it independently (fresh QG run in a clean worktree) before shipping via the normal quickmerge flow,
   under slot-12's own identity/attribution.
3. Root-cause how a slot-12-authored, `main`-branch-named commit ended up sitting in slot-7's
   `.tabs/7/unified-trading-ci` clone in the first place — whether that's a symlink/checkout mixup, a copy-paste of
   another slot's directory, or a gap in the pre-spawn branch-state guard.

## Todos

- [ ] [ADMIN] P3. Investigate + resolve the stranded commit `25b6605c09319926a5c214366c31327521010d88` in
      `.tabs/7/unified-trading-ci` (ship it under correct attribution if genuine, discard if stray) — human call, needs
      slot-12 context this doc doesn't have. Repo: unified-trading-ci.
- [ ] [ADMIN] P3. Root-cause why `.tabs/7/unified-trading-ci` is on branch `main` (tracking `origin/live-defi-rollout`)
      instead of directly on `live-defi-rollout` per Path-B topology, and whether
      `worktree_clean_check.check_slot_branch_state`'s pre-spawn guard should have caught this. Repo: agent-orchestrator
      or unified-trading-pm (wherever the guard lives).

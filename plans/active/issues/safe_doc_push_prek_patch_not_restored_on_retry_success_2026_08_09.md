---
doc_type: issue
title:
  "safe-doc-push.sh: a prek-patch stash of unstaged, out-of-scope files is saved before a retried commit attempt but
  never restored when that retry succeeds — silently drops uncommitted working-tree edits"
summary: >-
  `scripts/dev/safe-doc-push.sh` stages ONLY the caller-named `--files` (by design — this is what makes it safe under
  shared-checkout contention). prek's own pre-commit-hook wrapper independently stashes ANY other unstaged changes in
  the working tree (files outside the commit scope) into a patch file before running hooks, then restores them after —
  this is prek's own mechanism, not something safe-doc-push.sh implements itself. Live-observed 2026-08-09: on a COMMIT
  RETRY (the script's own attempt-2-of-6 loop, triggered by a `plan-hygiene` hook failure on attempt 1 that required
  fixing the staged content and re-running), prek saved a SECOND patch
  (`~/.cache/prek/patches/1786283053921-3898887.patch`) holding unstaged edits to two OTHER files
  (`plans/active/prediction_satellite_ao_dispatch_batch8_2026_08_08.md`,
  `plans/active/issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md` — checkbox flips made earlier in
  the same session, not part of this commit's `--files` scope) before the retry's hooks ran. The retry succeeded and the
  script printed `✅ Pushed afd6891bb3 -> live-defi-rollout` — but the script's own visible output never showed a
  matching "Restored unstaged changes from patch" line for THAT SECOND patch (only the first attempt's patch was
  restored). Post-success, `git status --porcelain` was clean and both files' edits (checkbox flips + Progress Log
  entries, made via editor tool calls earlier in the session, never committed) were GONE from the working tree —
  recovered only because the orphaned patch file was still sitting in `~/.cache/prek/patches/` and `git apply` on it
  succeeded cleanly. Without noticing the missing "Restored" line and going looking for the patch file, this would have
  read as ordinary, unremarked data loss — the two edited files would simply have reverted to their pre-session state
  with no error, no warning, and no trace in `git status`.
status: open
nature: issue
asset_group: [ci, ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [safe-doc-push, prek, precommit, data-loss, quickmerge, ci, plan-hygiene]
related:
  [
    /scripts/dev/safe-doc-push.sh,
    /plans/active/prediction_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
  ]
created: 2026-08-09
author: data_engineering worker (slot 8, prediction_satellite_ao_dispatch_batch8-001)
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: cicd
drift_direction: none
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Found live 2026-08-09 while shipping prediction_satellite_ao_dispatch_batch8-001's line-cap remediation — a
  commit-hygiene-hook failure on attempt 1 forced a retry; the retry's own prek patch (holding unrelated in-session
  edits to two other plan docs) was never restored after the retry succeeded, silently dropping those edits from the
  working tree until manually recovered from the orphaned patch file."
context_scope:
  [
    /scripts/dev/safe-doc-push.sh,
    /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
  ]
---

# safe-doc-push.sh drops unrelated unstaged edits on a hook-triggered retry

## What I found

`safe-doc-push.sh` is the sanctioned fast path for pure-docs commits (CLAUDE.md § "Git discipline", "pure doc/plan-flip
→ scripts/dev/safe-doc-push.sh"). Its retry loop (attempt N/6) re-runs `git commit` when a hook fails for a
contention-shaped reason and reconciles. Each `git commit` invocation triggers prek, and prek's own patch-based
stash/restore of unstaged changes (files NOT in this commit's staged set) runs around EVERY hook execution — this is
prek's mechanism, invoked implicitly, not something `safe-doc-push.sh` calls directly.

Live sequence observed 2026-08-09 (full raw output in the session transcript):

1. Attempt 1: prek saves patch A (unstaged edits to the 2 unrelated plan docs), runs hooks, hook `plan-hygiene` FAILS (a
   real content issue in the staged files — `check_todo_regression`), prek **restores patch A** ("Restored unstaged
   changes from patch A").
2. Content fixed (staged files edited to resolve the check_todo_regression failure), `git commit` re-invoked (attempt 2
   of the script's internal retry loop).
3. Attempt 2: prek saves patch B (the SAME unstaged edits to the 2 unrelated docs — untouched since attempt 1). Hooks
   run and pass this time. Commit succeeds. Push succeeds (`✅ Pushed afd6891bb3 -> live-defi-rollout`).
4. **No "Restored unstaged changes from patch B" line ever printed.** `git status --porcelain` immediately after was
   clean — the 2 unrelated docs' edits were gone from the working tree, with patch B sitting unreferenced in
   `~/.cache/prek/patches/`.

## Why it matters

This is silent, unannounced data loss for ANY uncommitted, unstaged edit sitting in the working tree at the moment a
`safe-doc-push.sh` (or any prek-wrapped `git commit`) call needs an internal retry. In an unattended, long-running agent
session (the normal operating mode per `agents/worker.md`) this is exactly the shape of loss nobody would catch without
independently noticing the missing "Restored" line and knowing to go recover the orphaned patch file by hand — most
sessions would simply report the task done and move on, having silently discarded real prior work. The immediate
instance here was recoverable (the patch file survives in `~/.cache/prek/patches/` until some future cleanup), but
relying on that cache directory never being cleared, or on an agent noticing the anomaly at all, is not a safety margin
— it's luck.

## Recommended fix

Root-cause is inside prek's own patch stash/restore lifecycle (not `safe-doc-push.sh`'s own logic), so the real fix
likely lives in prek's hook-runner config/wrapper rather than the script itself — needs someone with prek internals
context to confirm whether this is a known prek behavior (patch only restored on the FIRST hook run of a `git commit`
invocation, dropped on subsequent internal retries within the same invocation) or a genuine prek bug. Candidate
mitigations, cheapest first:

1. **Immediate safety net**: `safe-doc-push.sh`'s retry loop should `git stash list` / check for orphaned
   `~/.cache/prek/patches/*.patch` files newer than the loop's own start time immediately after a successful push, and
   loudly warn (not silently succeed) if any exist — turns silent loss into a visible, actionable alert.
2. **Real fix**: whatever triggers prek's own patch save should also guarantee a matching restore on every code path out
   of the hook run, success or failure, first attempt or retry — file upstream against prek if this is confirmed a
   prek-level defect rather than something `safe-doc-push.sh` is doing wrong in how it invokes retries.

## Todos

- [ ] [DEVOPS] P1. Investigate whether this is a prek-level defect (patch restore only wired to the FIRST hook
      invocation per `git commit` call, not to every internal retry) or something `safe-doc-push.sh`'s retry loop is
      doing that suppresses the restore step. Reproduce deliberately (stage a file that fails `plan-hygiene` once then
      passes, with an unrelated unstaged edit present) rather than relying on the live incident alone.
- [ ] [DEVOPS] P1. Add the immediate safety net from the Recommended fix above: `safe-doc-push.sh` checks for orphaned
      `~/.cache/prek/patches/*.patch` files created during its own run and warns loudly (non-zero exit or a
      clearly-flagged stderr warning) rather than exiting 0 silently, so a future occurrence is caught immediately
      instead of by chance. Repo: unified-trading-pm.
- [ ] [DEVOPS] P2. If confirmed a genuine prek defect (not a `safe-doc-push.sh` misuse), file upstream / pin a
      known-good prek version / document the workaround in this script's own header comment for future maintainers.

## Progress Log

- **2026-08-09 (slot 8, data_engineering, `prediction_satellite_ao_dispatch_batch8-001`)**: filed after live-hitting
  this mid-task. Recovered the dropped edits via `git apply` on the orphaned patch file before continuing; did not
  attempt the DEVOPS-scoped fix itself (outside this task's craft/scope — a plan-hygiene tooling defect, not a
  data-pipeline change) — filed here per findings-triage for a same-session fix-vs-file decision.

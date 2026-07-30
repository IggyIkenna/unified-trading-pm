---
doc_type: issue
title:
  "`refs/wip-preserve/cascade-*` refs (branch-state-quarantine safety net) can silently sit unrecovered — a shipped
  commit can be reset off the branch with no visible signal beyond the preserved ref itself"
summary: >-
  While shipping the LDR<->main backmerge silent-revert-loss fix across 24 repos
  (ldr_main_backmerge_silently_resurrects_reverted_commit_2026_07_29.md), a worker session died mid-task and, on
  respawn, `unified-trading-library`'s just-committed fix commit (057a6423) was no longer an ancestor of
  `origin/live-defi-rollout` — its content was gone from HEAD even though quickmerge had earlier logged a SHIPPED SHA.
  The commit was NOT actually lost: the orchestrator's own branch-state-quarantine safety net (agent-orchestrator
  `worktree_clean_check` — `_branch_state.py`/`_ahead_push.py`/`_orphan.py`) had preserved it to
  `refs/wip-preserve/cascade-unified-trading-library-057a6423b7bb` before resetting the local branch back to
  `origin/live-defi-rollout`, working exactly as designed. Recovered + re-shipped it. A second, UNRELATED wip-preserve
  ref (`refs/wip-preserve/cascade-strategy-service-a77eb6d170ca`, dated 2026-07-28, a `staging-lock-check.yml`
  self-hosted-runner-migration commit from a prior session/task) was also found sitting unrecovered — out of scope for
  this task to fix, but evidence the pattern isn't a one-off.
status: open
nature: issue
asset_group: [ao] # corrected 2026-07-30 (/ag-closeout-audit ao) -- was [cross-cutting]; AO worktree_clean_check refs
scope: [engineer]
stage: [meta]
repos: [agent-orchestrator, unified-trading-library, strategy-service]
tags: [agent-orchestrator, git, wip-preserve, quarantine, data-loss-risk, session-recovery]
related:
  [
    /plans/active/issues/ldr_main_backmerge_silently_resurrects_reverted_commit_2026_07_29.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-07-29
priority: P2
parent_epic: orchestrator_master
source:
  "worker, slot 15 — discovered mid-task while re-verifying a 24-repo fleet rollout after a session-death respawn; a
  repo reported SHIPPED earlier in this same session had its commit silently reset off the branch"
assigned_vm: NA
execution_scope: local-only
estimate_class: research
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# wip-preserve refs can silently sit unrecovered after a branch-state quarantine

## What I found

The branch-state quarantine mechanism (`agent-orchestrator/server/worktree_clean_check/`) is working AS DESIGNED — it
protects a worker's in-flight commit from being destroyed when a session dies mid-task by preserving it to a dedicated
`refs/wip-preserve/cascade-<repo>-<sha>` ref before resetting the local branch back to a clean `origin/<branch>` state
for the respawned session. This is the RIGHT behavior — the alternative (silently discarding the commit) would be worse.

**The gap**: once preserved, nothing surfaces these refs for review or automatically re-applies them. Two consequences
observed live in this session:

1. **A worker (me) logged "SHIPPED @ <sha>" for `unified-trading-library` based on quickmerge's own push-success output,
   then trusted that log line** across a session-death boundary — the actual branch state had since been
   quarantined-and-reset, so the fix silently reverted to unfixed. Nothing in quickmerge's own success path re-verifies
   post-push that the pushed content is STILL what you think it is after the fact — a stale log line and current reality
   diverged with no signal.
2. **A second, unrelated wip-preserve ref** (`strategy-service`, dated 2026-07-28 — a `staging-lock-check.yml`
   self-hosted-runner migration, from an entirely different prior task) has been sitting unrecovered for over a day.
   Nobody noticed; it doesn't show up in any dashboard, alert, or routine sweep I'm aware of.

## Why it matters

This is a narrower, DIFFERENT failure mode than the backmerge silent-revert-loss bug this session's main task fixed
(that one is about the PROMOTE/BACKMERGE pipeline; this one is about the ORCHESTRATOR's own session-recovery mechanism)
— but it rhymes: a commit can be genuinely absent from a branch's history with no conflict, no failed check, and a stale
success log line that no longer reflects reality. If a worker (or a human) trusts "I shipped X" from memory/chat/log
without re-verifying against live `origin` content, real fixes can go missing for days (as `strategy-service`'s case
shows) without anyone noticing.

## Recommended decision

Not a design call on the quarantine mechanism itself (that safety net is correct and should stay) — this is about
closing the "then what" gap:

1. Recover or explicitly dispose of `strategy-service`'s `refs/wip-preserve/cascade-strategy-service-a77eb6d170ca`
   (check first whether `staging-lock-check.yml`'s self-hosted-runner migration was independently re-applied since
   2026-07-28 by a later rollout — if so the ref is safely superseded and can be deleted; if not, recover it the same
   way this doc's sibling task did).
2. Add a periodic (or pre-compact-triggered) sweep across the fleet for `refs/wip-preserve/**` refs older than some
   threshold (e.g. 1h) and surface them — a Slack alert, a dashboard panel, or at minimum a codex-documented manual
   `git for-each-ref 'refs/wip-preserve/**'` check added to a standing runbook — so a preserved commit doesn't sit
   forgotten the way `strategy-service`'s did.
3. Consider whether quickmerge's own success path (or the worker RULES.md ship-loop) should verify post-push that
   `origin/<branch>`'s content still matches what was just pushed, rather than trusting the push-succeeded return code
   alone — closes the exact "stale SHIPPED log, reality diverged" gap this session hit.

## Todos

- [ ] [DATA] P2. Check whether `strategy-service`'s `staging-lock-check.yml` self-hosted-runner migration
      (`refs/wip-preserve/cascade-strategy-service-a77eb6d170ca`, 2026-07-28) was independently superseded by a later
      rollout; if not, recover + re-ship it the same way `unified-trading-library`'s was recovered in this doc's sibling
      task. Repo: strategy-service.
- [ ] [SCRIPT] P3. Add a fleet-wide `refs/wip-preserve/**` sweep (age-thresholded alert or a documented runbook check)
      so a preserved-but-unrecovered commit surfaces instead of sitting forgotten. Repo: agent-orchestrator.
- [ ] [SCRIPT] P3. Consider a post-push content-verification step in quickmerge's success path (or worker RULES.md's
      ship loop) — fetch + diff the pushed file(s) against `origin/<branch>` after a reported-successful push, so a
      "SHIPPED" log line is never trusted without a fresh confirming read. Repo: unified-trading-pm.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the `[SCRIPT] P3` post-push verification item is a 'Consider'
  fork against the fleet-wide `quickmerge.sh` success path (same too-high-blast-radius class as this tranche's other
  quickmerge items), and the `[SCRIPT] P3` sweep offers a codex-documented-runbook option that is never autonomous. The
  `[DATA] P2` is bounded but needs cross-slot access to `refs/wip-preserve/cascade-strategy-service-a77eb6d170ca` in
  another slot's clone. **Flagged**: that ref has now sat unrecovered since 2026-07-28 — folded into
  `/plans/active/issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md`, filed by this run.

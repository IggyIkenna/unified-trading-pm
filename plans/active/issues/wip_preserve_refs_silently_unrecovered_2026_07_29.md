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
    /plans/archive/issues/ldr_main_backmerge_silently_resurrects_reverted_commit_2026_07_29.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-07-29
last_updated: 2026-08-01
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
context_scope:
  [
    /plans/archive/issues/ldr_main_backmerge_silently_resurrects_reverted_commit_2026_07_29.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md,
    /plans/epics/orchestrator_master.md,
  ]
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

- [x] ✅ **ANSWERED 2026-07-30 (bounded recovery sweep, infra role): SUPERSEDED — nothing to recover, ref is safe to
      delete.** Measured on `ip-172-31-5-118` `.tabs/15/strategy-service` (this ref lives in slot 15, not slot 9/10/11
      which each hold a DIFFERENT `cascade-strategy-service-*` ref): `.github/workflows/staging-lock-check.yml` at
      `refs/wip-preserve/cascade-strategy-service-a77eb6d170ca` is **byte-identical** to
      `origin/live-defi-rollout:.github/workflows/staging-lock-check.yml` (same blob sha), i.e. the self-hosted-runner
      migration WAS independently re-applied by a later rollout. Original ask: check whether the migration was
      superseded; if not, recover + re-ship it the way `unified-trading-library`'s was. Repo: strategy-service.
- [x] [DATA] P3. **The fleet carries 25 `refs/wip-preserve/**` refs, not 1** — found by the 2026-07-30 sweep's
      fleet-wide `for-each-ref` (dated 2026-07-26..07-29, across slots 2/3/4/6/9/10/11/12/15). This doc named only the
      `strategy-service` one. Triage the other 24 to a recorded SUPERSEDED / RECOVER / DELETE verdict; first-pass
      blob-compare says ~16 are already content-identical to origin and most of the rest would REGRESS origin if
      applied. Full first-pass breakdown + the one substantive residual (`slot-12 unified-trading-library c927ec58`, a
      2-line docstring) are in `/plans/active/issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md`. Do
      this with the verifier that doc's `[SCRIPT] P2` specifies, not by hand. Repo: agent-orchestrator. **Attempted
      2026-08-01 (batch3 todo 3) — the verifier this item depends on is now SHIPPED (agent-orchestrator@623009e3,
      `server/worktree_clean_check/_orphan_verify.py` + a periodic `server/orphan_ref_verify_watchdog.py` sweep — see
      the full evidence in `/plans/active/issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md`'s own
      matching todo), but triaging these 25 specific refs was NOT possible from that session: 0/25 reachable. They are
      `refs/wip-preserve/cascade-*`-namespace refs created via a LOCAL-ONLY `git update-ref` by
      `quickmerge.sh::cascade_dep_branch()` (never pushed to origin), on slots 2/3/4/6/9/10/11/12/15 — but on host
      `ip-172-31-5-118` specifically, a different physical host from the one that session ran on. That session's
      filesystem access covered slots 1-5 and 21-30 only, and an exhaustive `git for-each-ref 'refs/wip-preserve/**'`
      across all 375 git repos in those reachable slots found ZERO local wip-preserve refs anywhere (confirmed this is a
      genuinely separate per-host population, not something this laptop's own slots 2/3/4 happen to also carry).
      Checkbox left unresolved — needs a session with reach into `ip-172-31-5-118` (or dispatched to run directly on it)
      to actually execute the now-ready verifier against these refs. **Completed 2026-08-01**: a later session had SSM
      reach into `ip-172-31-5-118` (untried by the prior session — it only checked local filesystem access) and ran the
      verifier against all 9 named slots (29 refs now, not 25 — 4 new cascade branches accumulated over the 2
      intervening days). Result: 16 SUPERSEDED, 10 STILL-ORPHANED, 3 WOULD-REGRESS, 0 GONE — full per-ref table in
      `/plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md`'s Progress Log and cross-referenced in
      `/plans/active/issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md`'s own matching todo. This doc's
      slot-15 `strategy-service` ref (`a77eb6d170ca`) — already answered above as SUPERSEDED by the 2026-07-30
      hand-triage — got the identical SUPERSEDED verdict from the automated verifier, cross-validating it.
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
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **2026-08-01 (batch3 todo 3 completion)**: `[DATA] P3` flipped `[x]` — the verifier (shipped 2026-08-01,
  `agent-orchestrator@623009e3`) was run against all 29 fleet-wide wip-preserve refs via SSM reach into
  `ip-172-31-5-118`. Full table in `/plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md`'s Progress Log.

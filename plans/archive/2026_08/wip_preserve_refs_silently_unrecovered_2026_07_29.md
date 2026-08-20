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
status: archived
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
author: unknown
last_updated: 2026-08-01
priority: P1
parent_epic: orchestrator_master
source:
  "worker, slot 15 — discovered mid-task while re-verifying a 24-repo fleet rollout after a session-death respawn; a
  repo reported SHIPPED earlier in this same session had its commit silently reset off the branch"
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
estimate_class: research
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    agent-orchestrator/server/worktree_clean_check/_orphan_verify.py,
    agent-orchestrator/server/worktree_clean_check/_branch_state.py,
    scripts/quickmerge.sh,
    /plans/archive/issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md,
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
      2-line docstring) are in `/plans/archive/issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md`. Do
      this with the verifier that doc's `[SCRIPT] P2` specifies, not by hand. Repo: agent-orchestrator. **Attempted
      2026-08-01 (batch3 todo 3) — the verifier this item depends on is now SHIPPED (agent-orchestrator@623009e3,
      `server/worktree_clean_check/_orphan_verify.py` + a periodic `server/orphan_ref_verify_watchdog.py` sweep — see
      the full evidence in `/plans/archive/issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md`'s own
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
      `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch3_2026_07_31.md`'s Progress Log and cross-referenced in
      `/plans/archive/issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md`'s own matching todo. This
      doc's slot-15 `strategy-service` ref (`a77eb6d170ca`) — already answered above as SUPERSEDED by the 2026-07-30
      hand-triage — got the identical SUPERSEDED verdict from the automated verifier, cross-validating it.
- [x] ✅ [SCRIPT] P1. **Build the daily fleet-wide `wip-preserve` sweep as a SCHEDULED AO-dispatched job** (raised P3 →
      P1 by the 2026-08-06 measurement below — this is a 1,912-ref backlog, not a curiosity). Operator ruling
      2026-08-06: sweep daily, auto-recover, delete provably-stale. **It must be TWO sweeps, because the two namespaces
      behave differently** (see the measurement section — the AO code documents the split at
      `agent-orchestrator/server/worktree_clean_check/_orphan_verify.py:258-264`): - **Remote sweep**
      (`refs/heads/wip-preserve/*` — pushed branches, **1,912 across 25 repos**): runnable from any single clone per
      repo via `git ls-remote`. For each branch, test whether its tip is an ancestor of `origin/live-defi-rollout`.
      **Ancestor → DELETE the remote branch** (operator-approved: the commit stays reachable from the branch, so nothing
      can be lost by construction). **Not an ancestor → REPORT, never touch.** - **Local sweep**
      (`refs/wip-preserve/cascade-*` — LOCAL-ONLY, created by `quickmerge.sh`'s `cascade_dep_branch()` via
      `git update-ref` and deliberately never pushed): **must run on EVERY host**, because no central job can see them.
      A central-only sweep is blind to this tier by construction. **Done when**: a scheduled job runs both sweeps daily
      across all repos + all `.tabs/*` clones, deletes only ancestor-proven remote branches, and reports everything
      else. Repo: agent-orchestrator (scheduler) + unified-trading-pm (sweep script). **Shipped
      `agent-orchestrator@d36219c`** (`server/wip_preserve_sweep_watchdog.py` + `server/config.py` tuning knob
      `wip_preserve_sweep_interval_seconds=86400` + wired into `server/server.py` startup + `LoopSupervisor` + 8 tests;
      QG: 2628 passed). `WipPreserveSweepWatchdog` daemon thread: invokes
      `unified-trading-pm/scripts/dev/wip_preserve_sweep.py --apply --json` daily, logs `wip_preserve_sweep_complete` +
      `wip_preserve_needs_review` activity events, auto-deletes ancestor-proven remote branches, reports everything
      else.
- [x] ✅ [SCRIPT] P1. **Rescue the local-only tier before classifying it — push, don't just report.** Operator ruling
      2026-08-06. On each host, for every `refs/wip-preserve/cascade-*` whose content is **not** already on
      `origin/live-defi-rollout`, push it to the durable `refs/heads/wip-preserve/` namespace FIRST, then classify.
      **Why**: this is the only tier where a loss is unrecoverable and invisible — the ref lives in one clone's `.git`,
      is not fetched by the standard refspec (`+refs/heads/*:refs/remotes/origin/*` cannot match it), and dies silently
      if the clone is deleted or the host wiped. Pushing converts the fragile tier into the durable one, at which point
      the remote sweep above handles it like any other. **Done when**: a host sweep leaves zero local-only cascade refs
      carrying content that is not on the branch. Repo: unified-trading-pm. **Shipped `unified-trading-pm@f60d3caa9`**
      (`scripts/dev/rescue-local-wip-preserve-refs.sh` — sweeps every slot + root clone, resolves each local
      `refs/wip-preserve/cascade-*`/`quickmerge-stage5-regate-*` ref to its full sha, pushes
      `<sha>:refs/heads/wip-preserve/<leaf>` on origin for any not already an ancestor of `origin/live-defi-rollout`,
      reports the rest). **Executed live on this host (`ip-172-31-x-x`, this session's VM) 2026-08-07**: 184 local-only
      refs scanned across 16 slot clones (root clones: 0) — 144 already ancestors (skipped, no rescue needed), 38 pushed
      to `refs/heads/wip-preserve/`, 2 already present remotely (idempotent), 0 errors. This host's local-only tier now
      carries zero refs with content not on `origin/live-defi-rollout`, satisfying the done-when for THIS host; the
      sibling `[SCRIPT] P1` daily-scheduled-job todo above is what runs this same script on every OTHER host going
      forward.
- [x] ✅ [SCRIPT] P1. **Add post-push verification to `quickmerge.sh` — and FAIL, not warn.** Operator ruling
      2026-08-06. Immediately after a successful push, assert
      `git merge-base --is-ancestor <pushed-sha> origin/<branch>` (re-fetch first) and exit non-zero if it does not
      hold. **Shipped `unified-trading-pm@98b99afa2`** (`scripts/quickmerge.sh` lines 2152-2173: re-fetches
      `origin/$BRANCH`, asserts sha ancestry, exits 1 on fetch failure OR non-ancestor; prints
      `✅ post-push ancestry verified` on success). QG: exit 0; the new check ran and passed on its own push
      (`98b99afa2 is an ancestor of origin/live-defi-rollout`). Repo: unified-trading-pm.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the `[SCRIPT] P3` post-push verification item is a 'Consider'
  fork against the fleet-wide `quickmerge.sh` success path (same too-high-blast-radius class as this tranche's other
  quickmerge items), and the `[SCRIPT] P3` sweep offers a codex-documented-runbook option that is never autonomous. The
  `[DATA] P2` is bounded but needs cross-slot access to `refs/wip-preserve/cascade-strategy-service-a77eb6d170ca` in
  another slot's clone. **Flagged**: that ref has now sat unrecovered since 2026-07-28 — folded into
  `/plans/archive/issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md`, filed by this run.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **2026-08-01 (batch3 todo 3 completion)**: `[DATA] P3` flipped `[x]` — the verifier (shipped 2026-08-01,
  `agent-orchestrator@623009e3`) was run against all 29 fleet-wide wip-preserve refs via SSM reach into
  `ip-172-31-5-118`. Full table in `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch3_2026_07_31.md`'s Progress Log.
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): KEEP-NA, valid — the 2
  remaining `[SCRIPT] P3` items are unchanged since the 2026-07-30 verdict: a fleet-wide alert/runbook (too-high
  blast-radius class) and a "Consider" fork against the shared `quickmerge.sh` success path (never autonomous). No
  change.
- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries) -- swapped in the two named
  `worktree_clean_check` source modules + `quickmerge.sh` (the remaining open todos' actual targets), dropped a
  now-redundant epic pointer.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **2026-08-07 (slot-2 infra, task wip_preserve_refs_silently_unrecovered-001)**: `[SCRIPT] P1` daily sweep todo flipped
  `[x]` — `agent-orchestrator@d36219c` (4 files: `server/wip_preserve_sweep_watchdog.py`, `server/config.py`,
  `server/server.py`, `tests/test_wip_preserve_sweep_watchdog.py`). QG: ruff ✅, basedpyright 0 errors, 2628 pytest
  passed. `WipPreserveSweepWatchdog` daemon runs daily (default `86400s`); subprocess-invokes
  `unified-trading-pm/scripts/dev/wip_preserve_sweep.py --apply --json`; logs activity events; integrated into
  `LoopSupervisor`.
- **2026-08-07 (slot-2 infra, task wip_preserve_refs_silently_unrecovered-001 context-2)**: `[SCRIPT] P1` post-push
  verification todo flipped `[x]` — `unified-trading-pm@98b99afa2` (`scripts/quickmerge.sh` lines 2152-2173). Re-fetches
  `origin/$BRANCH` after push exits 0, asserts `git merge-base --is-ancestor HEAD origin/$BRANCH`, exits 1 on fetch
  failure or non-ancestor. The check ran and passed on its own push
  (`98b99afa2 is an ancestor of origin/live-defi-rollout`). All todos in this issue are now `[x]`.

## Measurement 2026-08-06 (`/plan-reconcile ao`, interactive) — the pattern is ACTIVE and far larger than filed

Measured live, not recalled. Two namespaces exist and they are **not** interchangeable; the AO code documents the split
itself at `agent-orchestrator/server/worktree_clean_check/_orphan_verify.py:258-264`.

**Tier 1 — `refs/heads/wip-preserve/*`, PUSHED to remote. 1,912 branches across 25 repos.** Durable and visible from any
clone, but never cleaned up in ~2 months. Top offenders: `unified-trading-pm` 459, `market-tick-data-service` 237,
`features-service` 164, `instruments-service` 155, `deployment-service` 100, `unified-api-contracts` 88.

**Tier 2 — `refs/wip-preserve/cascade-*`, LOCAL-ONLY. 3 refs across 81 scanned clones.** Created by `quickmerge.sh`'s
`cascade_dep_branch()` via `git update-ref`; **never pushed** — confirmed by
`git ls-remote origin 'refs/wip-preserve/*'` returning empty, and by the standard fetch refspec
`+refs/heads/*:refs/remotes/origin/*` being structurally unable to match them. This is the dangerous tier: invisible to
every other machine, destroyed with the clone, no trace anywhere.

The 3 Tier-2 refs found, each adjudicated by hand:

| Repo                      | Ref / sha      | Date       | Verdict                                                 |
| ------------------------- | -------------- | ---------- | ------------------------------------------------------- |
| `unified-api-contracts`   | `f2214c09a3c8` | 2026-08-05 | ✅ recovered — ancestor of `origin/LDR`, ref is residue |
| `unified-trading-library` | `08521d5c1350` | 2026-08-06 | ✅ recovered — ancestor of `origin/LDR`, ref is residue |
| `unified-trading-library` | `d3fb74d795d5` | 2026-08-05 | ✅ recovered — **by CONTENT, not by sha** (see trap)    |

**Nothing was lost — but nothing would have told us that.** All 3 turned out harmless; the only reason that is known is
that a human checked each by hand on 2026-08-06. One had sat for a full day; one was created that same day. That is the
doc's original thesis, re-proven: the safety net has no exit path, no alert, and no cleanup.

### ⚠️ Trap: sha-ancestry is NOT the oracle for an aged ref (it IS for a fresh push)

`d3fb74d795d5` (slot-7, `feat(data): add per-AG Era-B adjudication exception for tradfi in cf_manifest_audit`) is
**not** an ancestor of `origin/live-defi-rollout` — by sha it looks like unrecovered work. It is not: the content was
re-shipped under a different sha and is live on the branch today (`unified_trading_library/cf_manifest_audit.py`:
`ERA_B_ADJUDICATED_AGS` at :123, the `ag in ERA_B_ADJUDICATED_AGS` branch at :437). A sweep that alarms on sha-absence
alone **will cry wolf**, and a maintainer who then "cleans up" on a false alarm learns to distrust the tool. For an AGED
ref, confirm by CONTENT. For a JUST-PUSHED sha (the quickmerge post-push check above) sha-ancestry is exactly right,
because you pushed that precise sha a second earlier — the two cases look similar and are not.

### Operator rulings 2026-08-06

1. **Daily scheduled sweep, AO-dispatched** — not a runbook step. Rationale: the failure mode is that nobody suspects
   anything, so a check that only runs when someone suspects something cannot catch it. First manual run took ~2 min
   across 81 clones and immediately found 3 unknown refs.
2. **Auto-delete on an ancestry proof; report everything else.** A remote `wip-preserve` branch whose tip is an ancestor
   of `origin/live-defi-rollout` may be deleted automatically — the commit remains reachable from the branch, so the
   delete cannot lose anything by construction. Anything failing that proof is reported and never touched. This is the
   only option that actually shrinks 1,912 instead of re-reporting it forever.
3. **Rescue Tier 2 by PUSHING it, before classifying.** Closes the real data-loss hole rather than merely observing it.
4. **quickmerge post-push check FAILS, does not warn** — a false `SHIPPED` is worse than a hard error.

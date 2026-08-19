---
doc_type: issue
title: "agent-orchestrator's pre-spawn dirty-state gate committed + reset a LIVE interactive session's mid-edit WIP"
summary: >-
  Slot 4's pre-spawn dirty-state gate (DirtyStateResolution.COMMIT_AND_PUSH) fired mid-session against an
  ACTIVELY-RUNNING interactive Claude session (not a dead predecessor), across 3 repos simultaneously
  (unified-trading-library, market-tick-data-service, unified-trading-pm), while genuine uncommitted edits were
  in progress. It correctly auto-committed the dirty state (as designed, to prevent loss on a real respawn) but
  then reset each branch back to origin, moving HEAD away from those commits — leaving them as dangling objects
  the live session had to discover via `git reflog` and manually recover with `git checkout <sha> -- <path>`.
  Recovery succeeded this time (nothing was destroyed — same-repo dangling commits, still in the object
  database), but this is luck, not a guarantee: a same-content overwrite, a `git gc`, or a second concurrent
  edit racing the recovery could have made this unrecoverable.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, slot-collision, dirty-state-gate, data-loss-near-miss, per-tab-worktrees]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/epics/orchestrator_master.md,
    /plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md,
  ]
parent_epic: orchestrator_master
source: "Interactive session slot 4, 2026-08-17 — mid-edit on a UTL/MTDS cross-repo feature when the gate fired against all 3 open repos at the same timestamp (2026-08-17T18:33:10Z)"
assigned_vm: planning
created: 2026-08-17
resolved_by:
locked_by:
locked_since:
priority: P2
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_role: infra
context_scope: [/codex/05-infrastructure/per-tab-worktrees.md]
---

# AO pre-spawn dirty-state gate fired against a live interactive session, not a dead predecessor

## What was found (2026-08-17)

Mid-session, while actively editing files across `unified-trading-library`, `market-tick-data-service`, and
`unified-trading-pm` (a genuine, in-progress cross-repo feature — this session was continuously working, no gap in
activity), all three repos' working trees were silently reset to a clean state matching `origin/live-defi-rollout`.
`git reflog` in each repo showed the identical sequence, all timestamped `2026-08-17T18:33:10Z`:

```
<sha>  commit: chore(orphan-wip): inherited WIP from predecessor on slot 4 at 2026-08-17T18:33:10Z
<sha>  branch: Reset to origin/live-defi-rollout
<sha>  checkout: moving from live-defi-rollout to live-defi-rollout
```

The commit messages read: *"Auto-committed by agent-orchestrator pre-spawn dirty-state gate
(DirtyStateResolution.COMMIT_AND_PUSH) on slot 4... this preserves the previous worker's WIP that would
otherwise have been discarded when the slot respawned."* — i.e. the gate believed slot 4's prior occupant had
died and a NEW worker was about to spawn into it, so it ran its documented safety procedure (commit the dirty
state, then reset to origin for the incoming worker's clean start).

**The premise was wrong**: there was no dead predecessor. This interactive session was the sole, continuously-active
occupant of slot 4 the entire time (confirmed via `ps aux` immediately after discovery — only this session's PID
was running; no other AO worker process was live). The gate's liveness check must have read a stale or
insufficiently-granular signal (an `.agent-claim` heartbeat gap, or a check that doesn't distinguish "interactive
session with no recent git commit" from "genuinely dead worker") and concluded the slot was free for a respawn.

**Consequence, and why this is a near-miss, not a clean save**: the `COMMIT_AND_PUSH` disposition's own name promises
a *push*, but none of the three orphan-wip commits (`c998342a` in UTL, `f4508391` in MTDS, `431d419fd6` in PM) ever
reached `origin` — `ahead=0 behind=0` against origin in all three repos, with the orphan-wip commits absent from
every branch. Whatever "push" step this disposition is supposed to run either failed silently or was skipped, and
the SAME cycle then reset the branch anyway, discarding the only reference to those commits from any branch. They
survived purely as unreferenced (dangling) objects, recoverable ONLY because:

- nothing ran `git gc`/`git prune` in the intervening minutes,
- the recovering session (this one) knew to check `git reflog` rather than trusting a clean `git status`,
- and no OTHER process wrote conflicting content to the same files before recovery completed.

Any one of those NOT holding — a routine gc, a slower discovery, a second session editing the same files in the
gap — would have made this a genuine, silent loss with no error, no warning, and a perfectly clean-looking working
tree. `git status --porcelain` showing empty is normally a "you're safe" signal; here it was the exact signature of
the loss.

## Why this is filed separately from `per-tab-worktrees.md`'s existing liveness-gating coverage

That doc already documents "Inherited-dirty-WIP is LIVENESS-gated (dead claim → inherit + commit; live claim /
mtime <120s → PROTECT)" as the INTENDED behavior. This issue is that the intended PROTECT branch did not fire for a
session that was, by any reasonable definition, live — the liveness check itself has a real gap, not just a
theoretical one.

## Todos

- [x] [INFRA] P1. ✅ Find and fix the liveness check the pre-spawn dirty-state gate uses to classify a slot's
      occupant as dead. An interactive Claude Code session with continuous tool-call activity but no recent git
      commit (normal — commits happen at ship time, not every edit) must never be misclassified as dead. Cite the
      exact check (likely `.agent-claim` heartbeat staleness or a PID-liveness probe) and either shorten its
      false-positive window or add a second signal (e.g. process still running, or a live PTY/session marker) before
      trusting it. — **agent-orchestrator@ad00fb7b38**. Root cause: `classify_maker_liveness`'s claim-file/mtime
      signals correctly read "absent" for a bare interactive session (no `.agent-claim`, no `orch-slot-*` tmux, and
      the 120s recent-dirty-mtime window lapses during any multi-tool-call reasoning burst with no new file write) —
      the ONE remaining safety net, `_default_proc_cwd_live` (the out-of-band "process still running" triangulation
      signal `orphaned_commit_recovery_has_no_dispatch_path_2026_07_30` built for exactly this), was silently
      non-functional: it read `/proc/<pid>/cwd`, a Linux-only path (silently False on macOS, where interactive
      per-tab-worktree sessions actually run — `agent_orchestrator_proc_cwd_liveness_test_macos_incompatible_2026_08_02`
      had already found and shelved this exact gap as "acceptable, real deployment target is Linux," an assumption
      this incident breaks), AND matched via `pgrep -f <path>` against a process's ARGV rather than its real cwd — a
      bare interactive `claude` REPL has no filesystem path in its own command line, so it would never match even on
      Linux. Rewrote `_default_proc_cwd_live` (`server/worktree_clean_check/_liveness.py`) on `psutil.process_iter()`
      (already a project dependency) querying each live process's real cwd directly — cross-platform, and no longer
      dependent on the path appearing in argv.
- [x] [INFRA] P1. ✅ Fix `DirtyStateResolution.COMMIT_AND_PUSH` — the push half is not happening (confirmed: none of
      the 3 orphan-wip commits reached origin, all 3 are dangling). Either the push step is silently failing, or
      the branch-reset step races ahead of it. A disposition named "COMMIT_AND_PUSH" that only commits is a correctness
      bug independent of the liveness-check issue above — fix regardless of how the liveness check is resolved,
      since a genuinely-dead predecessor's WIP deserves the same durability guarantee the name promises. —
      **agent-orchestrator@ad00fb7b38**. The exact code path (`commit_and_push_dirty_repos`'s Path-B branch,
      `server/worktree_clean_check/_orphan.py`) already gated its `checkout -B <base> origin/<base>` realign on
      `push_result.returncode == 0` before this incident (present since 2026-06-21, unchanged through the incident
      date) — so a bare git-exit-code check alone was already the contract, and still produced 3 dangling,
      unreachable-from-any-ref commits. Root cause not perfectly reconstructable post-hoc (no server logs available
      to this session), but the fix closes the gap regardless of which failure mode produced it: `git push` returning
      0 is no longer trusted alone — an independent `git ls-remote --exit-code origin <preserve_ref>` now re-queries
      the REMOTE directly immediately after the push, and only a genuinely-confirmed ref gates the realign. An
      unverified push (rc=0 but ls-remote can't confirm it) is now treated exactly like a failed push: local HEAD is
      left untouched (the orphan commit stays as the visible, `git log`-recoverable HEAD) rather than realigned away.
- [x] [INFRA] P2. ✅ Consider whether the reset-to-origin step should happen at all when the orphan-wip commit's own
      push (once fixed) succeeds — if the commit is safely on origin, resetting the LOCAL branch away from it
      serves no protective purpose and only adds the discovery burden (reflog archaeology) this incident required. —
      **agent-orchestrator@ad00fb7b38**. Decision: the realign now only runs when `replacing_session is not None`
      (a new session is genuinely about to occupy the slot). Reasoning: audited every one of the 6 production call
      sites of `resolve_dirty_state`/`commit_and_push_dirty_repos` — `routes/slots_ops.py`, `server.py`,
      `autospawn.py`'s fresh-spawn path, `autospawn.py`'s account-rotation path, and `worker_liveness/_respawn.py`
      ALL pass a real, non-None `replacing_session` (the incoming/rotating session's own tmux name) because a fresh
      worker genuinely is about to start there — realigning to a clean tip still serves its stated purpose for
      every one of those. The ONE exception is `worker_liveness_watchdog.py`'s `_sweep_dirty_slots` — the periodic,
      spawn-independent dirty sweep — which is the ONLY caller that ever passes `replacing_session=None`, and is
      also the exact shape of caller most likely to observe a live interactive session with no `.agent-claim`/tmux
      (per fix 1). Gating the realign on `replacing_session is not None` therefore keeps 100% of the legitimate
      "fresh worker needs a clean base" behavior (verified unchanged via the existing
      `test_orphan_realigns_normally_when_pre_existing_ahead_commit_is_old_enough` /
      `test_head_backward_canary_still_detects_legitimate_post_fix_realign` /
      `test_orphan_second_realign_within_cooldown_is_skipped` tests, all still passing, all still using a real
      `replacing_session`) while removing 100% of the "no spawn in flight — why is local HEAD being reset" surprise
      the incident describes, without needing to touch or weaken the liveness check itself — defense-in-depth, not a
      replacement for fix 1. New tests: `test_orphan_skips_realign_when_no_replacing_session` (verifies HEAD stays at
      the orphan commit, ahead-of-origin, when `replacing_session=None`) and
      `test_orphan_skips_realign_and_flags_error_when_push_verification_fails` (fix 2 in isolation).

## Progress Log

- **na-eligibility-audit 2026-08-17** [body-hash:d3150b0d1dccae32]: RECLASSIFY (whole-doc) -- all 3 open todos are bounded, worker-determinable agent-orchestrator bug fixes with a clear DoD each: (1) find+fix the pre-spawn liveness-check false-positive that misclassified a live interactive session as dead, (2) fix DirtyStateResolution.COMMIT_AND_PUSH's missing push half (root cause already partially diagnosed in-doc: none of 3 orphan-wip commits reached origin), (3) a scoped engineering judgment on whether the post-push reset-to-origin step still serves a protective purpose once (2) lands. None require operator/business judgment beyond ordinary engineering discretion. Conflict-check clear: direct grep for DirtyStateResolution/pre-spawn-dirty-state/dirty-state-gate = 0 hits outside this doc across every active planning-assigned plan in parent_epic orchestrator_master; no overlap in the cross-cutting consolidated closeout or any existing satellite batch. Flipped assigned_vm: NA -> planning in place, execution_scope -> orchestrator-agent, assigned_role: infra filled. Companion finalize: ao_pre_spawn_dirty_state_gate_targets_live_interactive_session_2026_08_17_finalize_2026_08_17.md. Cross-cutting tranche audit.
- **2026-08-19 (interactive session, slot 3)**: all 3 open todos implemented + shipped in one commit —
  **agent-orchestrator@ad00fb7b38** (`server/worktree_clean_check/_liveness.py`,
  `server/worktree_clean_check/_orphan.py`, `tests/test_dirty_state_resolution.py`; full `quality-gates.sh` green,
  4126 passed/8 skipped, 0 basedpyright errors, dashboard 414 vitest passed). Root-cause detail + fix reasoning are
  inline on each todo above. A closely-adjacent-but-out-of-scope finding surfaced while investigating fix 1: the
  `ao_human_fleet_integration_2026_08_15.md` plan's `human_slot_ids()` liveness exemption is wired into 3 sites
  (`WorkerLivenessWatchdog._tick_once`, `AutoSpawn._should_spawn`, `WorkerLivenessKicker._tick_once`) but NOT into
  `_sweep_dirty_slots` — irrelevant to THIS incident (slot 4 is not a registered 9001+/9002+ human-fleet slot, so
  the exemption wouldn't have fired either way), but worth a future look if a registered human-fleet slot ever
  needs its dirty-sweep exempted too; not filed as a separate issue since it's speculative, not a confirmed gap.
  Also worth recording: mid-session, an uncommitted round of these exact edits was silently wiped from this shared
  slot-3 checkout by a concurrent peer session's git operation (confirmed via identical Aug-19 03:59:06 mtimes on
  all 3 touched files immediately after a `checkout: moving from live-defi-rollout to live-defi-rollout` +
  `reset: moving to HEAD` reflog pair, with `git status --porcelain` showing the files clean/at-HEAD and HEAD
  itself sitting on an unrelated peer commit) — a live, real-time instance of the exact "shared checkout drops
  uncommitted WIP" risk class this very issue is about (different subsystem: ordinary peer-checkout contention
  during a non-`--isolated` quickmerge, not the AO pre-spawn gate), recovered only because the edits were still
  held in this session's own context and could be reapplied. Shipped this pass via `quickmerge.sh --isolated` to
  avoid a repeat. No data was lost (nothing here had been committed yet), so no separate issue doc filed — noted
  here as corroborating evidence, per the "opportunistically use `--isolated` under confirmed contention" guidance
  in `/codex/05-infrastructure/per-tab-worktrees.md`.

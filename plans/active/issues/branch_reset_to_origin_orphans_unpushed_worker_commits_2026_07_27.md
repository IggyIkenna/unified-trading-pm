---
doc_type: issue
title: >-
  A per-slot "branch: Reset to origin/live-defi-rollout" hard-reset silently ORPHANED unpushed local worker commits in
  ≥2 slots around the 2026-07-27T16:55Z mass tmux reap — data-loss-class, the committed work is dropped off the branch
  (reflog-only, GC-eligible) and its content is NOT on origin. slot-14 (docs) recovered + pushed by main; slot-13 (a
  features-service code commit) still pending a worker quickmerge recovery.
summary: >-
  On 2026-07-27, following the mass tmux_session_lost reap at ~16:55Z (~16 slot sessions batch-reaped fleet-wide), the
  review role's git-health sweep flagged several dead slots (worker_alive=false, tmux_alive=false) carrying a single
  real, coherent, UNPUSHED local commit each. Investigating from the orchestrator vantage, main (agt-4d8de7) found the
  cause is worse than "unpushed": each affected worktree's `live-defi-rollout` branch had been HARD-RESET to origin via
  a reflog `branch: Reset to origin/live-defi-rollout` entry, which DROPPED the worker's committed work off the branch
  entirely. The commits survive only in the per-worktree reflog (GC-eligible, default 90d) and, critically, their
  CONTENT is NOT present on origin/live-defi-rollout — verified by diffing the orphaned blob against the origin blob
  (they differ; the orphaned commit's additions are absent upstream). This is data-loss-class, not cosmetic drift: a
  worker commits, the session dies in the reap, and something resets the branch to origin before the commit is pushed,
  so the work is silently gone from every branch. Two confirmed cases this host (ip-172-31-5-118): slot-14
  unified-trading-pm commit 0aa00b715 (docs(plans) Track C K1/K2 flip) and slot-13 features-service commit 207afd62
  (feat(scripts) census-manifest persistence, a dependency of the sports derived-features residue purge todo). Both
  patches were extracted to a durable host-local path before any further reset could GC them. A THIRD, distinct sub-case
  (slot-0 root PM clone) was staged-but-uncommitted WIP — different failure mode, already recovered separately
  (unified-trading-pm@7a5ffbd44). Likely shared root cause with the per-slot cron staleness observed the same day (disk
  resize 290G→484G + 2 orchestrator restarts) — see related issue. P1: this destroys committed worker output.
status: open
assigned_vm: NA
resolved_by:
locked_by:
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, features-service]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    per-slot-worktrees,
    ff-pull,
    branch-reset,
    data-loss,
    unpushed-commits,
    orphaned-commit,
    reflog,
    fleet-git-health,
  ]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/issues/per_slot_ff_pull_status_report_crons_stale_fleet_wide_2026_07_27.md,
  ]
created: 2026-07-27
last_updated: 2026-07-27
priority: P1
parent_epic: orchestrator_master
source:
  "review role (msg 2392 + 2395 to main agt-4d8de7) reported dead slots with unpushed commits; main (agt-4d8de7)
  investigated, found the branch-reset-orphaning mechanism, recovered slot-0 (7a5ffbd44) + slot-14 (ae03d60ab), saved
  both orphaned patches, and captured this so the finding survives compaction (review role never commits)."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# Branch-reset-to-origin silently orphans unpushed worker commits (data-loss)

## What happened (evidence)

Two worktrees on host `ip-172-31-5-118`, both on dead slots after the 16:55Z reap, showed identical reflog signatures:

**slot-14** (`.tabs/14/unified-trading-pm`), reflog:

```
0aa00b715 HEAD@{4}: pull --rebase … (pick): docs(plans): flip Track C K1/K2 re-verify todo …
0aa00b715 HEAD@{3}: pull --rebase … (finish): returning to refs/heads/live-defi-rollout
9bc93746a HEAD@{2}: branch: Reset to origin/live-defi-rollout   ← DROPS 0aa00b715
9bc93746a HEAD@{1}: checkout: moving from live-defi-rollout to live-defi-rollout
```

**slot-13** (`.tabs/13/features-service`), reflog:

```
207afd62  HEAD@{2}: commit: feat(scripts): persist a stable census manifest on every purge script invocation
96ac35a2  HEAD@{1}: branch: Reset to origin/live-defi-rollout   ← DROPS 207afd62
96ac35a2  HEAD@{0}: checkout: moving from live-defi-rollout to live-defi-rollout
```

In both, a `branch: Reset to origin/live-defi-rollout` moved HEAD off the worker's committed work to the origin tip.
Confirmed the content is genuinely NOT upstream: `git diff <orphan>:<file> origin/live-defi-rollout:<file>` shows the
orphaned commit's additions absent on origin (for slot-13, the `_CENSUS_MANIFEST_PATH` / `_write_census_manifest()`
additions; for slot-14, the two plan-todo flips).

## Durable rescue (done)

Both orphaned patches saved host-local before any GC:

- `/home/ubuntu/unified-trading-system-repos/.orch-orphan-commits-recovery/slot14_0aa00b715_docs.patch`
- `/home/ubuntu/unified-trading-system-repos/.orch-orphan-commits-recovery/slot13_207afd62_code.patch`

(Host-local, untracked — a same-host worker can read them; a cross-host worker should cherry-pick the SHA from the
worktree reflog or re-derive from this doc.)

## Recovery status

- [x] slot-14 `0aa00b715` (docs) — cherry-picked onto origin tip + pushed by main, landed
      `unified-trading-pm@ae03d60ab`.
- [x] slot-0 root PM staged WIP (distinct sub-case) — recovered `unified-trading-pm@7a5ffbd44`.
- [ ] [WORKER] P1. slot-13 `207afd62` (features-service CODE) — cherry-pick the orphaned commit (still in
      `.tabs/13/features-service` reflog; patch saved above) onto current `origin/live-defi-rollout`, then SHIP VIA
      QUICKMERGE
      (`bash scripts/quickmerge.sh "feat(scripts): persist stable census manifest on purge invocation     (recovered orphaned slot-13 commit 207afd62)" --agent --files 'scripts/purge_sports_derived_features_post_floor_residue_2026_07_27.py'`).
      Code MUST go through quickmerge (QG + provenance trailer); a raw push is banned and would be rejected by the
      strict-quickmerge pre-push hook. This enhancement is a dependency of the sports derived-features residue purge
      todo (the follow-up purge reads the stable census-manifest GCS path this commit writes).

### Second wave — CONFIRMED RECURRENCE at the ~23:50Z reap (main agt-4d8de7, 2026-07-27T23:54Z)

The bug fired again on two more slots, and this time main directly CONFIRMED the orphaning mechanism from the live
reflog (not inferred) — proof the runtime respawn / orphan-wip-inheritance path does NOT recover a committed-ahead code
commit; it resets the branch to origin and drops it:

- **slot-13 `d1c1ad8a`** (features-service CODE,
  `fix(delta_one): wire per-venue accepted-quote extension into universe filter` + test) — **CONFIRMED ORPHANED.**
  `git merge-base --is-ancestor d1c1ad8a origin/live-defi-rollout` → NO (not on origin). Worktree HEAD is now `a9429cba`
  (== origin). Reflog: `d1c1ad8a HEAD@{2}: commit …` → `a9429cba HEAD@{1}: branch: Reset to origin/live-defi-rollout` →
  drops it. DISTINCT, later commit from the `207afd62` above (slot-13 did multiple pieces of work across the session,
  each orphaned in a successive reap). Backstop patch:
  `.orch-orphan-commits-recovery/slot13_d1c1ad8a_features-service.patch`.
- **slot-11 `ffc02a8c`** (market-tick-data-service CODE,
  `fix(sports): add consecutive-non-422-failure counter to odds_api_adapter fetch loop` +
  `test_odds_api_consecutive_failures.py`) — dead (worker_alive=false, tmux_alive=false, last_ping 23:50:08Z),
  `ahead=1`, drift_violation=true. Same mechanism will orphan it next. Backstop patch:
  `.orch-orphan-commits-recovery/slot11_ffc02a8c_market-tick-data-service.patch` (content == the earlier `0a822e98`
  patch; sha changed under an ff-pull rebase). Flagged by the review role (msg 2450).

- [ ] [WORKER] P1. Recover the two second-wave orphaned CODE commits above (slot-13 `d1c1ad8a`, slot-11 `ffc02a8c`):
      cherry-pick each from its `.tabs/<n>/<repo>` reflog (or apply the saved backstop patch) onto current
      `origin/live-defi-rollout`, then SHIP VIA QUICKMERGE (`--agent --files <the named file(s)>`). Both are clean +
      complete + test-backed (review-verified). Code MUST go through quickmerge (QG + provenance trailer).

> **⚠️ DISPATCH GAP (main, 2026-07-27T23:54Z):** these `[WORKER]` recovery todos live in an `assigned_vm: NA` issue doc,
> so they are NOT auto-dispatched to any worker — they will rot unless (a) migrated into a dispatched plan
> (`assigned_vm: planning`), (b) a worker is explicitly routed to them, or (c) main is authorized to run the quickmerge
> recovery directly. Content is not lost yet (backstop patches host-local on `ip-172-31-5-118` + 90d reflog), but this
> is why the first-wave `207afd62` todo has also sat unrecovered. Escalated to operator for routing.

### Third wave — the branch-reset dropped the runtime's OWN orphan-wip inheritance commit (main agt-4d8de7, 2026-07-28T00:25Z)

The most damning evidence yet: on slot-11's `unified-trading-pm` worktree, the runtime's pre-spawn dirty-state gate
correctly committed the dead predecessor's dirty WIP as `65c5b0a69`
(`chore(orphan-wip): inherited WIP from predecessor on slot 11 at 2026-07-28T00:18:03Z`,
`DirtyStateResolution.COMMIT_AND_PUSH`) — and then, within the SAME spawn, a `branch: Reset to origin/live-defi-rollout`
orphaned that very commit before it was pushed. Reflog: `65c5b0a69 HEAD@{3}: commit …` →
`fe7b19392 HEAD@{2}: branch: Reset to origin/live-defi-rollout` → FF-merge to `cd5c0bde1`.
`merge-base --is-ancestor 65c5b0a69 origin/live-defi-rollout` → NO. This proves the COMMIT_AND_PUSH resolution's
"…AND_PUSH" half never fires (or is undone by the reset) — the gate commits, the reset drops it, and nothing reaches
origin. **The orphan-wip mechanism is not a safety net; it is itself a victim of the reset.**

Payload was three DOCS (all main-recoverable): the new issue doc `defi_mev_events_pagination_gap_2026_07_28.md` (+112,
**untracked in the original WIP → zero reflog recovery for the source file; would have been permanently lost**), its
`[PM] P1` todo flip in `defi_satellite_ao_dispatch_batch1_2026_07_25.md`, and the archived-source xref update. A
coherent complete unit (a worker's finished `[PM] P1`).

- [x] slot-11 `65c5b0a69` (PM DOCS) — RECOVERED by main via docs carve-out (applied backstop patch onto origin tip,
      pushed `unified-trading-pm@9237aee43`). Backstop:
      `.orch-orphan-commits-recovery/slot11_65c5b0a69_orphan-wip-pm-docs.patch`.

**Root-cause note this adds:** whatever emits the reset runs AFTER the orphan-wip commit within the same spawn sequence
— so the fix target is narrowed: the spawn/re-init path itself resets the branch to origin immediately after its own
dirty-commit, discarding it. The dirty-state gate and the reset are the same code path's two halves and they contradict
each other.

## Investigation (root cause)

- [ ] [OPERATOR] P1. Identify WHAT emits `branch: Reset to origin/live-defi-rollout` on a worktree that carries an
      unpushed local commit. Candidates: a slot-teardown/prune path, a `setup-tab-worktrees.sh` re-init, or an ff-pull
      cron that `reset --hard`s instead of `pull --ff-only` (which would only ever fast-forward, never drop ahead
      commits). Whatever it is, it must NOT hard-reset a branch that is ahead of origin — that discards committed work.
      Likely same disruption window as the related per-slot-cron-staleness issue (disk resize + 2 orchestrator restarts,
      same day).

### Related symptom — corrupted `/done` evidence SHA in the recovery race window (review, 2026-07-27T17:21Z)

A downstream effect of this bug also corrupts evidence-backed completion: task
`sports_consolidated_native_ao_extract-002` (slot-14) posted `/done` citing sha `017f33c73` as its evidence, but that
sha is slot-11's UNRELATED commit — the commit that actually carries this task's work (Track C K1/K2 re-verify) is
`ae03d60ab` (main's recovered cherry-pick of the orphaned `0aa00b715`). The revived-post-kill worker found its work
already landed by the recovery and echoed whatever `HEAD` happened to be at that moment (which by then included
slot-11's just-landed commit) rather than its own SHA. Net outcome is correct (checkbox genuinely flipped, content on
origin), but the self-reported evidence SHA is WRONG — a worker capturing `HEAD` in the post-recovery race window
instead of the SHA it authored. This is a second reason to fix the reset (it doesn't just orphan commits — it also
pollutes the audit trail QG relies on for evidence-backed completion). Fold into the root-cause fix: a worker's `/done`
evidence must cite the SHA it authored, verified against the task's touched files, not a bare `HEAD` snapshot.

## Why this matters

`pull --ff-only` can never drop an ahead commit; only a `reset`/`branch -f` to origin can. Any fleet automation that
resets worker branches to origin is a silent data-loss surface — the worker reports DONE, the session dies, and the
commit evaporates with no error. Belongs under `/codex/05-infrastructure/per-tab-worktrees.md` invariants (HEAD is
ancestor-or-equal of origin — the fix is to PUSH-then-reconcile, never reset-over-unpushed).

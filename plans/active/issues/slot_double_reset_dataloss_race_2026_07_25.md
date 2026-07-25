---
doc_type: issue
title: >-
  Slot 6 (unified-api-contracts) reset TWICE within 90 seconds — one reset discarded a commit far fresher than the
  documented 900s safety floor because the floor is only enforced on ONE of the two identical realign code paths
summary: >-
  On 2026-07-25, slot 6's `unified-api-contracts` worktree had its HEAD force-reset to `origin/live-defi-rollout` TWICE
  within 90 seconds (11:23:55 and 11:25:02), discarding committed-but-unpushed work both times. Both resets emit the
  identical `branch: Reset to origin/<base>` reflog signature via `git checkout -B <base> origin/<base>`, but they are
  produced by TWO DIFFERENT-PURPOSE code paths that happen to share this one low-level primitive: reset #2 (confirmed)
  fired from `commit_and_push_dirty_repos()`'s own embedded post-commit realign
  (`server/worktree_clean_check/_orphan.py:300-337`), invoked from `autospawn.py`'s pre-spawn dirty-state gate — a path
  that has NO commit-age guard of any kind. Reset #1 (strongly evidenced, not log-confirmed) most likely fired from the
  same unguarded `_orphan.py` realign via one of two other callers (`WorkerLivenessWatchdog._sweep_dirty_slots` or
  `worker_liveness/_respawn.py::resolve_predecessor_wip`) reacting to genuinely dirty content sitting on top of an
  already-committed, ~339-second-old commit. The ONE guarded realign in the codebase —
  `heal_dead_slot_branch_quarantine()` (`server/worktree_clean_check/_branch_state.py:386`, protected by
  `_MIN_AHEAD_COMMIT_AGE_SECONDS_FOR_REALIGN = 900`) — is architecturally unreachable from either incident: it only
  fires on repos already classified `diverged`/`wrong_branch`/`detached`, and (independently verified from code, not
  merely inferred) a repo that is CLEAN with commits purely ahead of origin is classified `"ok"`, never a stop-state, so
  this guarded function could not have fired on either reset as literally coded. Both discarded commit-sets were
  recovered this session via cherry-pick + fresh quickmerge (`unified-api-contracts@71e75750`) — that recovery is DONE.
  This doc is about PREVENTING RECURRENCE: it documents the confirmed/strongly-evidenced root cause split and specifies
  a minimal two-part fix (a shared per-slot realign cooldown across both `checkout -B` call sites, PLUS hoisting the
  existing 900s pre-existing-ahead-commit-age guard into the currently-unguarded `_orphan.py` path) that closes both the
  "twice within 90s" mechanism and the "fired on a commit fresher than the floor" mechanism.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-api-contracts]
scope: [engineer, admin]
tags:
  [
    git-safety,
    data-loss,
    multi-agent-safety,
    reset,
    reflog,
    branch-realign,
    worktree-clean-check,
    autospawn,
    worker-liveness,
    slot-6,
  ]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Reflog forensics gathered live on the orchestrator VM (slot 6, unified-api-contracts) during a same-session
  cherry-pick recovery, 2026-07-25; root-caused via two independent code-trace investigations, synthesized and verified
  against the actual source in this doc.
depends_on: []
---

# Slot 6 double reset within 90 seconds — one reset below the documented safety floor (2026-07-25)

> **Recovery already done, not the subject of this doc.** Both discarded commit-sets were manually recovered this
> session via cherry-pick + a fresh quickmerge — `unified-api-contracts@71e75750`. This doc is scoped to root-causing
> and PREVENTING RECURRENCE of the underlying race, not the recovery.

> **Resets themselves are not the bug (operator framing, verbatim, kept front and center):** "resetting entirely isnt
> particulalrly strange. else how does new worker get updates form clean worktree. doing it twice is weird. triggerring
> it when the last commit on that slot was only 39 second ago is weird." A fresh worker legitimately needs to start from
> a clean, up-to-date worktree — that is a normal, sanctioned realign. The bug is specifically: (1) the same slot got
> reset TWICE within 90 seconds, and (2) at least one of those resets fired on committed work far fresher than the
> documented 15-minute safety floor.

## Measured sequence (2026-07-25, all times UTC, orchestrator VM, slot 6, `unified-api-contracts`)

```
11:18:16  commit 11ed7f09 "chore(defi): remove residual GMX cassette mapping + external mocks"
          (on top of 18d53d63, already on origin)
11:18:31  commit 44de0cf0 "test(defi): drop stale gmx_arbitrum_ws cassette mapping"
          (on top of 11ed7f09)
11:23:16  44de0cf0 amended -> ce0e447a (same message; HEAD now 2 commits ahead of origin:
          11ed7f09, ce0e447a)
11:23:18-19  activity log: worker_kick_failed (slot 3), worker_polling_dead + slot_idle_stale
          (slot 6 and slot 8) fire almost simultaneously
11:23:55  reflog: "branch: Reset to origin/live-defi-rollout" -- HEAD forced back to 18d53d63,
          discarding 11ed7f09 and ce0e447a  <-- RESET #1, 39s after the last commit
11:24:57-58  a fresh worker spawns into slot 6; its pre-spawn dirty-state gate finds leftover
          uncommitted content and auto-commits it as 6e0b96f2
          "chore(orphan-wip): inherited WIP from predecessor on slot 6 at 2026-07-25T11:24:57Z"
          (parent = 18d53d63; same final tree as ce0e447a -- i.e. it re-captured the exact
          same lost work via a different path)
11:25:02  reflog: ANOTHER "branch: Reset to origin/live-defi-rollout" -- HEAD forced back to
          18d53d63 AGAIN, discarding 6e0b96f2  <-- RESET #2, ~4s after that commit was made
```

## Root cause

### The structural defect

There are exactly **two** places in the entire `agent-orchestrator` codebase that emit
`git checkout -B <base> origin/<base>` (verified via `grep -rn "checkout.*-B" server/ --include='*.py'` — no other
realign/reset primitive exists anywhere in `server/`, confirmed no `git reset --hard` call exists in any git-affecting
code path):

1. **`heal_dead_slot_branch_quarantine()`** — `server/worktree_clean_check/_branch_state.py:386`, checkout at line 511.
   Guarded by `_MIN_AHEAD_COMMIT_AGE_SECONDS_FOR_REALIGN = 900` (line 383): before realigning, it checks
   `_seconds_since_head_commit()` on the repo's PRE-EXISTING ahead commit and refuses (leaves quarantined) if it is
   younger than 900s. Its only caller is `autospawn.py:1347`, reached only when `check_slot_branch_state()` has already
   classified the repo `diverged`/`wrong_branch`/`detached` (`_BRANCH_STOP_STATES`, `_branch_state.py:49`).
2. **`commit_and_push_dirty_repos()`** — `server/worktree_clean_check/_orphan.py:97`, checkout at line 332. **Has NO age
   guard of any kind** — its only protection is a single liveness classification (`classify_maker_liveness()`,
   `_liveness.py:67`) checked ONCE, before anything is committed. Reachable via the coordinator `resolve_dirty_state()`
   (`_resolve.py:45`, called with `protect_live_peer=False` since the coordinator already checked liveness) from
   **four** independent call sites: `autospawn.py:1310` (pre-spawn dirty gate, fresh
   spawn),`worker_liveness/_respawn.py:45` (`resolve_predecessor_wip`, the kicker's stuck-slot auto-respawn),
   `worker_liveness_watchdog.py:1407` (`_sweep_dirty_slots`, an unconditional per-tick sweep independent of any spawn
   attempt), and `routes/slots_ops.py:242` (manual ops route). A fifth site, `worker_liveness_watchdog.py:1989`
   (`_preserve_wip_before_kill`), always passes `mode="stash"` and never realigns — ruled out.

A repo purely ahead of clean origin (0 uncommitted changes) is classified `"ok"` by `_check_repo_branch_state()`
(`_branch_state.py:294`, falls through — never a stop-state), so `heal_dead_slot_branch_quarantine` is architecturally
**unreachable** for that shape of repo. Separately, `push_or_preserve_ahead_commits()`
(`server/worktree_clean_check/_ahead_push.py:110`) handles the clean-but-ahead case and by explicit design **never
resets local HEAD** (docstring line 29; verified by reading the function — it only pushes-if-QG-sentinel- verified or
preserves to a `wip-preserve/` ref without touching HEAD). And `check_slot_clean()` (`_report.py:103`) is pure
`git status --porcelain` — it has **no concept of ahead/behind at all** — so `resolve_dirty_state()` short-circuits to
`action="clean"` (`_resolve.py:77-78`) and never even calls `commit_and_push_dirty_repos()` on a repo that is clean but
sitting on commits ahead of origin.

**This closed-set of facts, verified directly against the code (not inferred), proves neither `checkout -B` call site
could have fired on a repo that was purely "clean + 2 commits ahead of origin"** — the shape UAC was in immediately
after the 11:23:16 amend. That in turn means Reset #1 required genuinely **dirty** (uncommitted) content to exist in the
UAC worktree at 11:23:55 — on top of the already-committed `11ed7f09`/`ce0e447a` — for `commit_and_push_dirty_repos()`
to even be reachable. This is consistent with the `worker_polling_dead` signal firing at 11:23:18-19 (~37s before the
reset): a dying/crashing claude process can leave partially-written files behind even after its last clean commit.

### Reset #2 — CONFIRMED

`6e0b96f2`'s subject (`chore(orphan-wip): inherited WIP from predecessor on slot 6 at …`) is a byte-for-byte match to
the template hardcoded at `_orphan.py:165`, produced only by `commit_and_push_dirty_repos()`. Given the incident
description ("fresh worker spawns into slot 6; its pre-spawn dirty-state gate finds leftover uncommitted content and
auto-commits it"), the call site is `autospawn.py:1310-1317` — the `elif slot_path.exists():` fresh-spawn branch of
`_do_spawn()`, `mode="commit_and_push"`, `replacing_session=tmux_spawn.session_name(slot.slot_id)`. Because
`replacing_session` matches the claim's own session, `classify_maker_liveness()` (`_liveness.py:109-111`) short-circuits
straight to `"dead"` ("claim owned by the session we're REPLACING → inherit"), so the commit (lines 199-266) +
wip-preserve push (lines 300-318) + realign (lines 324-337) run unconditionally — no age check anywhere in this call
chain. 4 seconds after the orphan commit, `checkout -B live-defi-rollout origin/live-defi-rollout` (line 332) discarded
it (recoverable only via the `wip-preserve/orchestrator-slot-6-<sha>` ref pushed first).

### Reset #1 — strongly evidenced, not log-confirmed

`heal_dead_slot_branch_quarantine` is **ruled out** — its only caller (`autospawn.py:1347`) only runs inside a spawn
attempt, and no spawn happened until 11:24:57, over a minute later; it is also unreachable for the "ok"-classified
clean-ahead shape as proven above. `_preserve_wip_before_kill` is **ruled out** — always `mode="stash"`, never realigns.

Given the code-level proof that dirty content must have been present, two candidates both reach the identical unguarded
`_orphan.py` realign and are both plausible triggers ~37-39s after the last commit and the `slot_idle_stale` signal:

- **`WorkerLivenessWatchdog._sweep_dirty_slots`** (`worker_liveness_watchdog.py:1344-1433`) — runs unconditionally at
  the top of every tick (`_tick_once`, line 654; default interval config-driven), targeting any slot with no live
  session or a dead pane (`_pane_is_dead`). Logs `trigger: "watchdog_sweep"`.
- **`maybe_auto_respawn_stuck_slot` → `resolve_predecessor_wip`** (`worker_liveness/_respawn.py:30-77`) — the kicker's
  stuck-slot escalation path for an idle slot with queued work. Logs `trigger: "auto_respawn"` (`_respawn.py:58-64`).

Both share the exact defect. Disambiguating which one fired first requires the actual `slot_dirty_state_resolved`
activity-log row's `trigger` field from the orchestrator VM's DB — not available in this local-clone investigation.
**This ambiguity does not affect the fix**: both candidates funnel into the same one unguarded function, so closing the
gap in `_orphan.py` closes it for both.

### Why the 900s guard did not protect either reset

- **Reset #2**: the guard (`_MIN_AHEAD_COMMIT_AGE_SECONDS_FOR_REALIGN`, `_branch_state.py:383`) is referenced ONLY in
  `_branch_state.py` — confirmed by grep, zero references in `_orphan.py` or `_resolve.py`. The call chain that produced
  reset #2 (`autospawn.py:1310` → `resolve_dirty_state` → `commit_and_push_dirty_repos`) never touches
  `heal_dead_slot_branch_quarantine` at all — it is a structurally different function for a structurally different
  purpose (dirty-content inherit vs. stop-state branch quarantine heal) that merely happens to share the same low-level
  `checkout -B` primitive.
- **Reset #1**: same underlying gap. Additionally, even had the 900s concept been checked against the OLDEST
  pre-existing ahead commit (`11ed7f09`, committed 11:18:16 — 339s before the 11:23:55 reset), it would correctly have
  REFUSED (339s < 900s) — this is the concrete number that shows the guard, if it had been wired into this path at all,
  would have prevented reset #1's loss of the already-committed work.

## Why it fired TWICE within 90 seconds

Two independently-scheduled background mechanisms — (1) a periodic per-tick watchdog sweep or the kicker's stuck-slot
auto-respawn (candidate for reset #1) and (2) `AutoSpawnLoop`'s ordinary pre-spawn dirty gate (confirmed for reset #2) —
both funnel into the identical unguarded `commit_and_push_dirty_repos()` realign, with **zero coordination or "was this
slot just resolved/realigned" check between them**. `AutoSpawnLoop._should_spawn()` (`autospawn.py:2149-2206`) gates on
its own private `_flap_backoff_until`/`_last_attempt_at`, and the kicker's `_RESPAWN_DEBOUNCE_MINUTES`
(`_respawn.py:274-284`) is a **separate** dict on a **separate** object — neither loop knows the other just touched this
slot.

## Minimal fix (two parts — both are needed, each closes a different half of this one incident)

### Part A — shared per-slot realign cooldown (prevents "twice within 90s"; this is what stops Reset #2)

Add a shared, in-process (or DB-backed, if cross-process visibility is needed across the watchdog/kicker/autospawn
threads — verify whether these already share one process before choosing) `(slot_id, repo)` → last-realign-timestamp
map. Check-and-set it at the **top** of both realign sites before running `checkout -B`:

- `server/worktree_clean_check/_orphan.py`, immediately before line 332 (`commit_and_push_dirty_repos`'s realign).
- `server/worktree_clean_check/_branch_state.py`, immediately before line 511 (`heal_dead_slot_branch_quarantine`'s
  realign).

Suggested floor: a few minutes (e.g. 180-300s) — comfortably longer than the ~67s gap actually observed between reset #1
and reset #2, short enough not to wedge a slot that genuinely needs back-to-back resolution across ticks. On a cooldown
hit: skip the realign, log + leave the repo as-is (dirty content stays committed-but-unpushed on the branch, already
preserved to `wip-preserve/` by the commit step that ran before this check), so the NEXT sweep/respawn/spawn attempt
gets a fresh look instead of compounding a second discard.

### Part B — hoist the pre-existing-ahead-commit age guard into `_orphan.py` (prevents "fired on a commit fresher

than the floor"; this is what would have stopped Reset #1)

Before `commit_and_push_dirty_repos()` stages/commits anything (i.e. before line 200's `git add -A`), check whether the
repo's **current HEAD** (pre-orphan-commit) is already ahead of `origin/<base>`, and if so, how old that ahead commit is
— reusing `_seconds_since_head_commit()` (`_branch_state.py:362`, already a reusable helper; needs hoisting to a shared
module or importing across `_branch_state.py`/`_orphan.py`) against the existing
`_MIN_AHEAD_COMMIT_AGE_SECONDS_FOR_REALIGN` floor. If the pre-existing ahead commit is younger than the floor: refuse
the entire operation (do NOT commit the dirty content, do NOT realign) and quarantine the repo instead — mirroring
`heal_dead_slot_branch_quarantine`'s existing refusal behavior (`_branch_state.py:462-476`) — so a human/alert path sees
it rather than a fresh commit silently vanishing underneath dirty-WIP cleanup.

This is orthogonal to Part A: it protects against a single-fire scenario (no double-realign needed) where dirty content
happens to be sitting on top of very recent, already-committed real work — exactly Reset #1's shape (`11ed7f09` was 339s
old, well under the 900s floor).

### Explicitly NOT the fix

- Do not remove or weaken either `checkout -B` realign — a fresh worker legitimately needs a clean, up-to-date worktree
  (operator's own framing, quoted above).
- Do not attempt to merge `commit_and_push_dirty_repos` and `heal_dead_slot_branch_quarantine` into one function — they
  serve genuinely different purposes (dirty-content inherit vs. stop-state branch-quarantine heal) and forcing them into
  one code path risks a regression in either's independently-tuned behavior.

## Verification once implemented

- Unit-test both realign sites refuse within the cooldown window (Part A) and refuse on a sub-floor pre-existing ahead
  commit (Part B), mirroring the existing test coverage pattern for `_MIN_AHEAD_COMMIT_AGE_SECONDS_FOR_REALIGN` in
  `heal_dead_slot_branch_quarantine`'s test suite.
- Confirm `head_backward_canary.py` (the existing reflog-signature detector/pager) still fires normally on a legitimate
  single realign (it should — this fix does not change the reflog signature, only when the realign is allowed to run)
  and does NOT need modification.

## Corroborating recurrence — slot 10, instruments-service (same session, after this doc's investigation began)

The identical signature hit a SECOND slot twice more while this doc's root-cause investigation was in flight: `f2de84b3`
(12:16:16Z, "chore(orphan-wip): inherited WIP from predecessor on slot 10") and, only ~9 minutes later, `c270b2a1`
(12:25:46Z, same message) — both on `instruments-service`, both discarded by the identical `branch: Reset to origin`
signature, both with the IDENTICAL tree hash (the same underlying WIP re-captured twice by the unguarded
`commit_and_push_dirty_repos()` path). Both recovered this session — reconstructed from the known-good diff (8 file
deletions, a completed one-off-script cleanup) and re-landed via a fresh quickmerge from a stable local clone rather
than the actively-contested slot-10 worktree (recovering directly IN that worktree risked hitting the same unguarded
realign mid-recovery — a first attempt there silently lost its own staged changes before quickmerge could commit them,
consistent with a third realign firing during the recovery window itself): `instruments-service@269440d7`. This is
independent evidence the race is systemic (not a slot-6-specific fluke) and that it can recur within the same ~10-minute
window on a single slot, not just once.

## Already-completed recovery (context only, not scope of this doc)

Both discarded commit-sets were manually recovered this session via cherry-pick + a fresh quickmerge —
`unified-api-contracts@71e75750`.

## Files read during this investigation (no code changes made)

- `server/worktree_clean_check/_orphan.py`
- `server/worktree_clean_check/_branch_state.py`
- `server/worktree_clean_check/_resolve.py`
- `server/worktree_clean_check/_liveness.py`
- `server/worktree_clean_check/_ahead_push.py`
- `server/worktree_clean_check/_report.py`
- `server/worker_liveness/_respawn.py`
- `server/worker_liveness_watchdog.py`
- `server/autospawn.py`
- `server/head_backward_canary.py`
- `server/notifications/slack.py`

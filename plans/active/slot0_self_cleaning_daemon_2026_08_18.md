---
doc_type: plan
title: Slot 0 self-cleaning daemon — auto-heal dirty/diverged repos on the persistent main agent
summary: >-
  Slot 0 (the persistent main/orchestrator agent) never gets the pre-spawn dirty-state and
  branch-state self-heal that every numbered worker slot already gets from `autospawn.py` on
  every respawn — because slot 0 is never respawned. This plan wires the SAME already-built,
  liveness-gated resolution library into a new hourly + on-boot daemon thread scoped to slot 0
  alone, mirroring the exact `ResourceHistoryLoop`/`TmuxPruner`/`WorkerLivenessKicker` pattern.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, slot0, self-cleaning, worktree-clean-check, daemon, reliability]
related: [ao_consolidated_closeout_2026_08_12]
created: 2026-08-18
last_updated: 2026-08-18
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
sequential: true
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/server/worktree_clean_check/,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/tmux_pruner.py,
    agent-orchestrator/server/resource_history.py,
    agent-orchestrator/server/worker_liveness/__init__.py,
    agent-orchestrator/server/server.py,
    agent-orchestrator/server/config.py,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
supersedes:
superseded_by:
source: >-
  Operator-confirmed 2026-08-18 (interactive session, "ao"): slot 0 has repos sitting
  dirty/diverged for 6-10 days with nothing forcing cleanup, because unlike numbered worker
  slots it never gets a fresh-start pre-spawn gate between tasks. Operator explicitly ruled this
  should be an agent-orchestrator plan (background-fleet-executed), not a human plan.
---

# Slot 0 self-cleaning daemon

## Why this is a small, bounded task — not a "build a classifier" task

Investigating this before writing the plan found that the hard part already exists as a
general-purpose, unit-tested library: `server/worktree_clean_check/` implements the FULL
dirty-repo classification + safe resolution decision tree (restore regenerated artifacts →
reconcile a wiped index → classify whether the repo's last writer is a live or dead session →
either protect a live peer untouched, or commit-and-push a dead peer's WIP), plus a separate
FM1/FM5/FM6/FM7 branch-state gate that realigns a diverged branch to `origin/<base>` the same
safe way. `server/autospawn.py`'s pre-spawn gate (around its `resolve_dirty_state(...)` /
`check_slot_branch_state(...)` / `heal_dead_slot_branch_quarantine(...)` call sequence) already
calls this for every NUMBERED worker slot, every time AutoSpawn is about to respawn into it.

**Slot 0 never goes through this path at all**, because AutoSpawn only respawns numbered worker
slots — slot 0 is the persistent main agent and is never "spawned into." So its dirty state
just accumulates with nothing to trigger the exact same self-heal every other slot already gets
for free. The fix is a new caller, not new classification logic: a small daemon thread that
periodically runs the SAME library calls against slot 0's own checkout, gated by the SAME
liveness check so it never fights a live occupant (including slot 0's own live session).

## Todos

- [ ] [BACKEND] P1. Add `slot0_self_clean_interval_seconds` to `TuningDefaults` in
      `server/config.py`, mirroring `tmux_prune_interval_seconds`'s `Field(default=..., gt=0)`
      shape exactly (same file/class as the other daemon tuning knobs — these are env-free,
      code-default-only per this workspace's `tuning.*` convention). Default `3600` (hourly,
      per the operator's 2026-08-18 confirmed cadence for daily/standing self-checks). Done-when:
      `get_config().tuning.slot0_self_clean_interval_seconds == 3600` by default and
      `basedpyright`/`quality-gates.sh` are clean.
- [ ] [BACKEND] P1. Create `server/slot0_self_clean.py` with a `Slot0SelfCleanLoop` class
      mirroring `TmuxPruner`'s daemon-thread shape in `server/tmux_pruner.py` EXACTLY:
      `__init__(interval_seconds: int | None = None)` sourcing the new tuning field when
      `None`, a `threading.Event`-gated `.start()`/`.stop(timeout=5.0)`, a named daemon thread
      (`"orchestrator-slot0-self-clean"`), and an initial-delay-then-loop `_loop()` that calls
      `_tick()` inside a `try/except Exception: logger.exception(...)` so one bad tick never
      kills the thread (same as `TmuxPruner._loop`/`ResourceHistoryLoop._loop`). Done-when: the
      class instantiates, `.start()` spawns a thread, `.stop()` joins within timeout with no
      leak — verified the same way `TmuxPruner`'s own test file verifies this (grep `tests/`
      for it and mirror the start/stop-without-a-real-thread pattern).
- [ ] [BACKEND] P1. Implement `Slot0SelfCleanLoop._tick()` part 1: resolve slot 0's checkout
      root via `worktree_setup.slot_dir(0)` (the same helper `autospawn.py`,
      `orphan_ref_verify_watchdog.py`, and `stash_audit_watchdog.py` already import as
      `slot_dir`/`_default_slot_dir`), then call
      `worktree_clean_check.check_slot_clean(0, slot_dir)`. If `report.is_clean`, return —
      this is the expected common-case no-op tick, matching every other watchdog's "stay cheap
      on a healthy fleet" contract. Done-when: run manually against a currently-clean slot 0
      checkout and confirm the tick takes no action and writes no activity-log row.
- [ ] [BACKEND] P1. Implement `_tick()` part 2 — dirty-state resolution: when slot 0 is dirty,
      call `worktree_clean_check.resolve_dirty_state(slot_dir, 0, mode="commit_and_push",
      timestamp_iso=<now, UTC, same `strftime("%Y-%m-%dT%H:%M:%SZ")` format `autospawn.py`
      uses>)` — the identical call `autospawn.py` makes for a worker slot, just with
      `slot_id=0`. Before wiring this, read `classify_maker_liveness`'s actual signature in
      `server/worktree_clean_check/_liveness.py` to confirm exactly how a live slot-0 tmux
      session gets protected (the same liveness gate that already protects a live worker peer:
      dead/absent maker → WIP inherited via commit+push; provably-live maker → protected,
      never stomped) and pass whatever `has_session_fn`/`replacing_session`/
      `predecessor_agent_id` values that signature actually needs for a self-check (there is no
      "new occupant replacing an old one" here, unlike the worker-respawn case — read the
      docstring rather than copying autospawn's args blind). Done-when: against a real dirty
      repo under slot 0 with a live tmux session attached, `outcome.action ==
      "protected_live_peer"` (nothing touched); against a repo left dirty by a confirmed-dead
      prior session, the WIP is committed and pushed and `outcome.action` reflects that.
- [ ] [BACKEND] P2. Implement `_tick()` part 3 — branch-state healing (never `reset --hard`,
      never touching a provably-live peer — full constraint below), run AFTER dirty-state
      resolution (same order `autospawn.py` uses, since a dirty tree fails
      `check_slot_branch_state`'s `git merge --ff-only` otherwise): call
      `worktree_clean_check.check_slot_branch_state(0, slot_dir, host_operator())`; if
      `branch_state.should_stop`, call
      `worktree_clean_check.heal_dead_slot_branch_quarantine(slot_dir, 0, branch_state,
      host_operator(), timestamp_iso=<now>, has_session_fn=tmux_spawn.has_session)` — the same
      FM1/FM5/FM6/FM7 auto-heal `autospawn.py` runs for a worker slot (preserve any local
      commits to a `wip-preserve/` ref, then realign via `checkout -B <base> origin/<base>`,
      never a `reset --hard`, never touching a provably-live peer). Done-when: a repo left
      diverged from `origin/<base>` by a dead prior session gets realigned; a repo genuinely
      behind because slot 0's live session is mid-edit is left untouched.
- [ ] [BACKEND] P1. Emit an activity-log row for every non-no-op tick, mirroring
      `autospawn.py`'s `log_activity(db, "slot_dirty_state_resolved", slot_id=..., details={
      "trigger": "autospawn", **outcome.as_dict()})` call shape (inside `with session_scope()
      as db:`). Use a distinct event name, `slot0_self_clean`, carrying `outcome.as_dict()` (and
      the branch-heal outcome, if that path fired) plus which repo(s) were touched. Done-when: a
      real self-clean action on a test-dirtied repo produces a queryable activity-log row with
      this exact event name (same query path the dashboard/`GET /api/state` activity feed
      already reads other `log_activity` events from).
- [ ] [BACKEND] P1. Wire `Slot0SelfCleanLoop` into `server/server.py`'s lifespan
      startup/shutdown, in the SAME block where `pruner = tmux_pruner.TmuxPruner()` and
      `kicker = worker_liveness.WorkerLivenessKicker()` are instantiated and started/stopped —
      start it on boot (this is what satisfies "and on boot," not just the hourly tick) and
      stop it on shutdown, same lifecycle as those two. Done-when: `grep -n
      "Slot0SelfCleanLoop" server/server.py` shows both an instantiation and `.start()`/`.stop()`
      calls in the same lifespan hooks as `pruner`/`kicker`.
- [ ] [BACKEND] P2. Unit tests for `Slot0SelfCleanLoop` covering `_tick()`'s three branches
      (clean → no-op; dirty + dead session → inherited + activity row written; dirty + live
      session → protected, nothing touched, no activity row) — mirror the existing test file
      for `TmuxPruner` or `ResourceHistoryLoop` (grep `tests/` for their names) for the
      daemon-thread-testability shape: call `_tick()` directly rather than needing a real
      thread or a real 3600s wait. Done-when: the new tests pass under `bash
      scripts/quality-gates.sh` with no regression to existing coverage.
- [ ] [REVIEW] P2. Live-verify against slot 0's ACTUAL current checkout state at the time this
      plan is picked up — re-check live, do not trust this plan's 2026-08-18 authoring-time
      snapshot (repo dirty/diverged state changes daily and may already differ). Confirm the
      new loop's first live tick actually detects and resolves whatever is dirty at that
      moment, and that an activity-log row exists for it. Done-when: a fresh read of slot 0's
      dirty-repo count (the same check `/ao-watchdog`'s Step 1 snapshot already pulls) shows 0
      dirty repos (or confirms it was already 0) immediately after this loop's first live tick
      post-deploy.
- [ ] [DOC] P3. Add a short entry naming `Slot0SelfCleanLoop` alongside
      `ResourceHistoryLoop`/`TmuxPruner`/`WorkerLivenessKicker` wherever those three are
      documented as the orchestrator's standing daemon-thread family (grep
      `/codex/04-architecture/` and `/codex/05-infrastructure/` for where they're currently
      named together) — so the next reconciliation sweep doesn't rediscover this as an
      undocumented daemon. Done-when: grep confirms `Slot0SelfCleanLoop` appears in that codex
      doc next to its three siblings.
## Design notes carried from the authoring session

- **Why hourly + on-boot, not a systemd-dispatched AO agent task**: the operator's own framing
  for this ("surely it can ping itself... every hour and on boot") matches the in-process
  daemon-thread pattern (`ResourceHistoryLoop`/`TmuxPruner`/`WorkerLivenessKicker`, all started
  from `server.py`'s own lifespan hooks), NOT the `install-*-timer.sh` systemd-timer family
  (`escalation-queue-reconciler`, `ao-watchdog`, etc.) — those dispatch a full AO AGENT task
  through the backlog on a cron-like schedule; this is much lighter-weight (a few git/library
  calls) and belongs inside the orchestrator server process itself, same as its three siblings.
- **Never `reset --hard`/`clean -fd`** — this plan's whole point is reusing the ALREADY-SAFE
  library (`worktree_clean_check`), which never does either; if any implementation step finds
  itself reaching for a raw destructive git command instead of the library call, that is a sign
  the wrong approach is being taken — stop and re-read the relevant `_liveness.py`/`_resolve.py`
  docstring instead.
- **Known slot 0 targets at authoring time (2026-08-18, may be stale — re-check live per the
  P2 REVIEW todo above)**: `unified-trading-system-ui` dirty since 2026-08-08,
  `unified-trading-ci` diverged since 2026-08-11, `unified-trading-pm` dirty since 2026-08-10,
  `agent-orchestrator` dirty since 2026-08-12.

## Progress Log

- **2026-08-19 (slot 33)**: Picked up todo 1. Added `slot0_self_clean_interval_seconds: int =
  Field(default=3600, gt=0)` to `TuningDefaults` in `server/config.py`, immediately after
  `tmux_prune_interval_seconds` (same shape/comment style). Live-verified:
  `get_config().tuning.slot0_self_clean_interval_seconds == 3600`. Committed
  (`agent-orchestrator@4ec54c82`, `Quickmerge: agent` trailer pre-stamped) — **but Pass-1
  `quality-gates.sh` came back RED on an otherwise-clean tree, for two causes verified
  pre-existing and unrelated to this one-line diff**: (1) all 6 tests in
  `tests/test_ao_self_pull_dirty_gate.py` fail because the fixture's synthetic origin repo is
  created via a bare `git init` and this host has no `init.defaultBranch=main`, so the
  fixture's own `fetch origin main` step fails before real assertions run; (2) the dashboard's
  `vitest`/`tsc --noEmit` fail because `recharts` is declared in `dashboard/package.json` but
  was never `npm install`ed (`dashboard/node_modules/recharts` doesn't exist). Filed
  `/plans/active/issues/ao_qg_red_dirty_gate_tests_and_missing_recharts_2026_08_19.md` (2 fix
  todos) and declared repo-blocker **RB-38a23126** (`agent-orchestrator`, `qg_red`, escalation
  `agt-2beb85`) per RULES.md § 4b. **`agent-orchestrator@4ec54c82` sits committed locally,
  1 commit ahead of `origin/live-defi-rollout`, NOT yet pushed** — this is the correct,
  intentional state (pushing an unshipped commit around a red gate is banned); it is
  recoverable from the slot-33 checkout / git reflog regardless of session boundaries. Todo 1's
  checkbox stays unflipped until the commit actually lands on origin — do not flip it on the
  strength of "the code is written and correct."

  **Resume instructions for whoever picks this up next** (goalposts, not just the next step —
  this plan has 8 more todos untouched, all downstream of todo 1):

  1. **First, check RB-38a23126's status** (`GET /api/repo-blockers` or the dashboard) and
     whether `agent-orchestrator@4ec54c82` has reached `origin/live-defi-rollout`
     (`git merge-base --is-ancestor 4ec54c82 origin/live-defi-rollout`). If the blocker
     resolved and the commit is on origin: flip todo 1's checkbox with that citation, then
     continue to step 2. If the exact commit `4ec54c82` is somehow gone from the local
     checkout (unlikely — it's a real git object) but the field is still absent from
     `server/config.py`, re-apply the same one-line `Field` addition (see the diff shape
     above) rather than re-deriving it from scratch.
  2. **Todo 2** — create `server/slot0_self_clean.py` with `Slot0SelfCleanLoop`, mirroring
     `TmuxPruner`'s daemon-thread shape exactly (`server/tmux_pruner.py` lines ~149-183):
     `__init__(interval_seconds: int | None = None)` sourcing the new tuning field, a
     `threading.Event`-gated `.start()`/`.stop(timeout=5.0)`, a named daemon thread
     (`"orchestrator-slot0-self-clean"`), `_loop()` wrapping `_tick()` in
     `try/except Exception: logger.exception(...)`.
  3. **Todo 3** — `_tick()` part 1 (clean no-op path): resolve slot 0's checkout via
     `worktree_setup.slot_dir(0)`, call `worktree_clean_check.check_slot_clean(0, slot_dir)`,
     return on `report.is_clean` with no action/no activity-log row.
  4. **Todo 4** — `_tick()` part 2 (dirty-state resolution): when dirty, call
     `worktree_clean_check.resolve_dirty_state(slot_dir, 0, mode="commit_and_push",
     timestamp_iso=<UTC now>)`. Before wiring, read `classify_maker_liveness`'s real signature
     in `server/worktree_clean_check/_liveness.py` (already read this session — it's the
     dead-vs-live-session gate the same library uses for a worker respawn) rather than
     copying `autospawn.py`'s call args blind, since there is no "new occupant replacing an
     old one" concept for a self-check.
  5. **Todo 5 (P2)** — `_tick()` part 3, branch-state healing: run AFTER dirty-state
     resolution (a dirty tree fails `check_slot_branch_state`'s `git merge --ff-only`
     otherwise). Call `check_slot_branch_state(0, slot_dir, host_operator())`; if
     `should_stop`, call `heal_dead_slot_branch_quarantine(...)` — never `reset --hard`, never
     touch a provably-live peer.
  6. **Todo 6** — activity-log row for every non-no-op tick, event name `slot0_self_clean`,
     mirroring `autospawn.py`'s `log_activity(db, "slot_dirty_state_resolved", ...)` call
     shape (`server/autospawn.py` lines ~1017-1022 — the same file already read this session,
     the exact call is further down past the truncated 1042-line view; grep
     `slot_dirty_state_resolved` to jump straight to it).
  7. **Todo 7** — wire `Slot0SelfCleanLoop` into `server/server.py`'s lifespan
     startup/shutdown, the SAME block as `pruner = tmux_pruner.TmuxPruner()` and
     `kicker = worker_liveness.WorkerLivenessKicker()` (grep `TmuxPruner()` in `server.py` to
     find the exact block — not yet located this session, `server.py` is 1392 lines).
  8. **Todo 8 (P2, [REVIEW])** — live-verify against slot 0's ACTUAL current dirty-repo state
     at pickup time (do not trust this plan's 2026-08-18 authoring-time snapshot listed
     above — it is now over a day stale).
  9. **Todo 9 (P2, [BACKEND])** — unit tests for `Slot0SelfCleanLoop._tick()`'s three branches
     (clean/dirty-dead/dirty-live), mirroring `TmuxPruner`'s or `ResourceHistoryLoop`'s test
     file shape (call `_tick()` directly, no real thread/wait needed).
  10. **Todo 10 (P3, [DOC])** — add `Slot0SelfCleanLoop` alongside
      `ResourceHistoryLoop`/`TmuxPruner`/`WorkerLivenessKicker` wherever those three are
      documented together in `/codex/04-architecture/` or `/codex/05-infrastructure/`.

  **Sequencing note**: todos 2-10 do not themselves depend on the QG-red gate being fixed —
  they can be WRITTEN and locally-verified while RB-38a23126 is still open — but nothing in
  this plan can actually SHIP (quickmerge push) until `agent-orchestrator`'s quality gate goes
  green, since every todo lands in the same repo. A worker picking this up while RB-38a23126
  is still open should keep implementing todos 2-10 and let the shippable-unit commits queue
  up locally (or coordinate with whichever worker/escalation is fixing the QG-red issue) rather
  than treating the whole plan as blocked.

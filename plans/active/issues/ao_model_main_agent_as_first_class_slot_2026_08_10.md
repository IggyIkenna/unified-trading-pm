---
doc_type: issue
title:
  Model the main agent as a first-class slot — retire the slot-less special case that keeps producing the same bug class
summary: >-
  Operator ruling 2026-08-10: main becomes a first-class slot. Every defect in the 2026-08-09 context-lifecycle family
  traces to one structural asymmetry — main is the ONE lifecycle target with no SlotRow. That single fact produced three
  separate, independently-patched bugs: no self-reported context floor (main ran to 99% with the safety net disarmed),
  context_pressure hardcoded "low" (the thrashing recycle trigger was structurally unreachable), and a terminal
  wedge-recovery gated behind a force main could never receive. Each was fixed with a main-specific branch and a
  main-specific test; the NEXT slot-based mechanism that forgets main reintroduces the class. Prerequisite discovered
  while scoping: slot_id 0 already carries TWO meanings — autospawn's _MAIN_SLOT_ID and a synthetic sentinel for
  plan-level/operator-gated activity rows — so the identifier must be disambiguated before main can safely own a real
  SlotRow.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, main-agent, slots, architecture, context, worker-lifecycle, refactor]
related:
  [
    /plans/archive/issues/ao_main_review_force_compact_idle_gate_unreachable_2026_08_09.md,
    /plans/archive/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-10
last_updated: "2026-08-10"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Operator ruling 2026-08-10, taken after the 2026-08-09 poisoned-calibration incident and its four sibling issues all
  root-caused to the same missing SlotRow.
depends_on: []
context_scope:
  [
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/main_agent_keeper.py,
    agent-orchestrator/server/orm.py,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
  ]
---

# Model the main agent as a first-class slot

## Why (the bug class, not a single bug)

main is the only context-lifecycle target with no `SlotRow`. Everything slot-shaped therefore has to special-case it,
and each mechanism that forgets to is a silent gap. Measured, all within 24 hours:

| Gap                           | Consequence                                                  | Patched by                     |
| ----------------------------- | ------------------------------------------------------------ | ------------------------------ |
| No self-reported pct floor    | main ran to 99% with the compaction net disarmed for 4.3h    | `_main_pct()` (AgentRow floor) |
| `context_pressure` hardcoded  | `pressure == "thrashing"` recycle unreachable for main       | derive-pressure commit         |
| Wedge recovery behind a force | terminal recovery unreachable when the idle gate never opens | saturation-entry commit        |

Three fixes, three main-specific branches, three main-specific tests — all compensating for one missing row. The fourth
mechanism to assume "targets have SlotRows" starts the cycle again.

## Prerequisite: slot_id 0 currently means two different things

Discovered while scoping — this must be resolved BEFORE main gets a real row, or the two meanings collide:

- `autospawn._MAIN_SLOT_ID = 0` — main's slot identity (`autospawn.py:823`, `:3064`; `deepseek_usage_poller.py:478` maps
  `slot_id == 0` → `MAIN_SESSION_NAME`).
- **A synthetic sentinel** for rows that belong to no worker slot — plan-level/operator-gated activity
  (`bootstrap.py:931` "sentinel: plan-level, no worker slot", `orm.py:390`, `blocked_reconcile.py:474`).

Writing a real `SlotRow(slot_id=0)` for main while the sentinel meaning persists would make every plan-level activity
row appear to belong to main.

## Non-goals

- main must NOT become dispatchable for backlog tasks. `dispatch.py` and `autospawn` currently exclude it; that
  exclusion is intended behaviour and must survive (`dispatch.py:606-611` records the incident where an unconfigured
  slot 0 read as permanently claimable and burned a budget slot every tick, forever).
- Not a rewrite of the context-lifecycle policy. The point is to delete special cases, not change compaction semantics —
  main's observable compaction behaviour should be unchanged by this work.

## Todos

- [x] [BACKEND] P1. Audit and record every site that special-cases main by its lack of a SlotRow, and every site that
      reads `slot_id == 0`, classifying each as "main identity" vs "no-slot sentinel". Done-when: the inventory is in
      this doc's Progress Log with file:line for each, and each is labelled with which of the two meanings it uses. —
      agent-orchestrator (audit-only, see Progress Log)
- [x] [BACKEND] P1. Disambiguate the sentinel: give the no-worker-slot rows a distinct marker (a nullable `slot_id` or a
      dedicated sentinel value that cannot collide with a real slot id) and migrate existing rows. Done-when: no code
      path uses `slot_id == 0` to mean "no slot", and a migration test proves existing plan-level rows still resolve
      correctly. — agent-orchestrator@0efa913: added `orm.NO_WORKER_SLOT_SENTINEL = -1`, migrated every write/read site
      (`bootstrap.py`, `plan_health.py`, `blocked_reconcile.py`, `routes/backlog.py`, `regen_backlog_from_plan.py`'s raw
      SQL) off the literal `slot_id=0`, added `bootstrap._migrate_blocked_queue_no_slot_sentinel` (data-only UPDATE for
      existing rows on live DBs) + `tests/test_migrate_blocked_queue_no_slot_sentinel.py` proving a legacy `slot_id=0`
      row migrates to -1, a real worker row is untouched, and the migration is idempotent; full test suite (3069
      passed) + ruff + basedpyright clean.
- [x] [BACKEND] P1. Create and maintain a real `SlotRow` for main (id per the audit's decision), owned by
      `MainAgentKeeper`: `status`, `context_used_pct`, `context_pressure`, `last_ping`, `claude_session_id` kept current
      on the keeper's own tick. Done-when: `/api/state` shows main's row with a live context pct that tracks its
      AgentRow, and a unit test asserts the keeper writes it every tick. — agent-orchestrator@8fedf51:
      `MAIN_SLOT_ID = 0` (matches every pre-existing "main identity" call site the todo-1 audit found — kept as an
      independent literal, not a shared import with `autospawn._MAIN_SLOT_ID`, to avoid a circular import;
      `test_main_slot_id_matches_autospawn` pins the two equal). `tick_once()` is now a thin wrapper around the renamed
      `_tick_once_inner` so the new `_sync_main_slot_row` runs EVERY tick regardless of which branch fired (not threaded
      into each of the many early returns). `context_used_pct`/`context_pressure`/`last_ping`/compaction-tracking are
      written via `state_store.update_slot_ping` — the SAME function every worker's own /progress\|/done\|/heartbeat
      already calls — sourced from main's own `AgentRow.context_used_pct` (already ratcheted by `_main_pct` against the
      measured probe during `_context_lifecycle.tick()`, called earlier the same tick), so the SlotRow genuinely tracks
      the AgentRow rather than re-deriving anything; `status` comes from a fresh `tmux_spawn.has_session` read (not the
      tick's own branch outcome) and `claude_session_id` from the AgentRow. New tests
      `test_main_slot_row_created_and_tracks_agent_row_every_tick` (two ticks, proves update-in-place not
      recreate-on-tick, asserts context_pressure derivation) and `test_main_slot_row_status_idle_when_session_dead`;
      full suite 3079 passed, 2 skipped, ruff + basedpyright clean.
- [x] [BACKEND] P1. Prove the dispatch exclusion still holds with the row present: main must never be handed a backlog
      task and must never count toward claimable capacity. Done-when: a unit test asserts `_task_is_routable_to` rejects
      main's slot and that AutoSpawn skips it, with the `dispatch.py:606-611` incident cited in the test's docstring. —
      agent-orchestrator@3fa500e: found a REAL gap, not just a happenstance-holds property — `_task_is_routable_to` had
      no guard against `slot_id==0` at all; an explicit hit on `/api/slots/0/boot`/`/heartbeat` would have sailed
      through every other filter (main is in no craft/model/review-slot config) and been dispatched real backlog work,
      now that `MainAgentKeeper._sync_main_slot_row` (todo 3) writes a real, non-provisioning-gap `SlotRow(slot_id=0)`
      every tick instead of leaving it permanently unconfigured. Added an unconditional early-return guard in
      `_task_is_routable_to` (checked before the target_slot match, so an explicit `target_slot=0, affinity=high` pin
      cannot override it either) plus `dispatch._MAIN_SLOT_ID` as an independent literal (same avoid-a-circular-import
      rationale as `main_agent_keeper.MAIN_SLOT_ID`'s own docstring). New `tests/test_dispatch_main_slot_gate.py`
      proves: `pick_next_task(session, 0, ...)` returns nothing even with every other filter passing; an explicit
      high-affinity pin to slot 0 doesn't override the exclusion; `_task_is_routable_to` rejects slot 0 unconditionally;
      and main's row (no worktree/branch/operator) never satisfies `slot_is_spawnable`, so it still never counts toward
      the AutoSpawn spawn budget — asserted directly rather than via `claimable_queued_task_ids`'s own "superset-on-
      doubt" empty-candidate-set fallback, which would pass a naive "main-only fleet → claimable == set()" assertion for
      the wrong reason (a first draft of this test hit exactly that trap: it asserted `set()` and failed, since a
      main-only fleet is claimable via superset-on-doubt regardless of whether main itself is a real candidate).
      `tests/test_autospawn.py` gets a dedicated test for `AutoSpawnLoop._should_spawn`'s pre-existing `"main_slot"`
      skip reason (previously shipped 2026-08-08 but never directly asserted). `test_dispatch_review_slot_gate.py`'s
      stale 2026-07-13 docstring ("no main-role slot to test... it never reaches a slot dispatch route at all") is
      corrected to point at the new file, since todo 3 invalidated that premise. Full suite 3085 passed, 2 skipped,
      ruff + basedpyright clean (one unrelated `test_worker_liveness_watchdog.py` timing flake observed under concurrent
      shared-host QG load, confirmed non-reproducing on a clean re-run).
- [ ] [BACKEND] P2. Collapse `_main_pct()` into the ordinary `_read_pct()` slot path now that main has a row, keeping
      the self-report floor semantics identical (higher of {self-report, probe}, ratchet-up persisted). Done-when: the
      main-specific branch is deleted, and the existing `_main_pct` regression tests pass unchanged against the unified
      path.
- [x] ✅ [BACKEND] P2. Collapse the derived-pressure and wedge-recovery main branches the same way, so main reaches
      those paths as a slot rather than via a special case. Done-when: both main-specific branches are deleted and their
      existing tests pass against the shared path. — agent-orchestrator@abcdee3
- [x] ✅ [BACKEND] P2. Add a standing guard against the regression class: a test asserting every context-lifecycle
      target returned by the policy's own target list has a SlotRow. Done-when: the test fails if a future target is
      added without one. — agent-orchestrator@c8109bd
- [x] ✅ [DOCS] P2. Post-phase codex audit: record the ruling and the resulting shape in
      `/codex/04-architecture/agent-orchestrator-worker-liveness.md`, superseding the sections that document main's
      slot-less special-casing as expected. Done-when: the SSOT describes main as a first-class slot and names the
      dispatch exclusion as the one deliberate difference. — unified-trading-pm@a333c492c2

## Progress Log

- 2026-08-10 — Filed on the operator's ruling. Scoping already surfaced the slot_id-0 dual-meaning prerequisite
  (`autospawn._MAIN_SLOT_ID` vs the plan-level sentinel in `bootstrap.py`/`orm.py`/`blocked_reconcile.py`), which is why
  the disambiguation is todo 2 and the row creation is todo 3 rather than the other way round.
- 2026-08-10 — Todo 1 (audit) complete. Full-repo grep of `agent-orchestrator/server/**/*.py` (non-test) for
  `slot_id == 0` / `_MAIN_SLOT_ID` / main-lacks-SlotRow special-casing. Found a THIRD meaning beyond the two the issue
  already named — `context_lifecycle.py`'s own target list uses `slot_id=None` (not `0`) as main's identity, so its
  internal `slot_id is None` branches are a third encoding of "this is main", distinct from both meanings below.

  **Meaning A — "main identity" (slot_id used/compared as 0, meaning "this row/id IS main"):**
  - `server/autospawn.py:96` — `_MAIN_SLOT_ID = 0` constant definition.
  - `server/autospawn.py:823` — `seed_worker_slots_from_tabs`: skips `slot_id == _MAIN_SLOT_ID` when seeding `.tabs/<N>`
    worker slots (main has no `.tabs` worktree).
  - `server/autospawn.py:3064` — `_should_spawn`/`_slot_is_configured` path: `slot.slot_id == _MAIN_SLOT_ID` returns
    `"main_slot"` instead of `"slot_not_configured"` so main doesn't read as a provisioning gap.
  - `server/deepseek_usage_poller.py:478` — `slot_id == 0` selects `main_agent_keeper.MAIN_SESSION_NAME` for the tmux
    session name instead of `f"orch-slot-{slot_id}"`.
  - `server/state_store/slots.py:924` — spend-aggregation: `slot_id == 0` buckets spend into `orchestrator` (main)
    rather than `worker`/`review`.
  - `server/routes/state.py:310` — `SlotView` role classification: `s.slot_id == 0` → `kind = "main"` for the
    dashboard's fleet-vs-agents split.
  - `server/routes/git_health.py:240` — `slot_id == 0 and session.get(SlotRow, 0) is None`: main's un-slotted workspace
    checkout never auto-registers a `SlotRow`, so git-status reporting special-cases the lookup miss.

  **Meaning B — "no-slot sentinel" (slot_id == 0 used for plan-level/operator-gated rows that belong to NO worker, not
  to main):**
  - `server/bootstrap.py:931` — `slot_id=0,  # sentinel: plan-level, no worker slot` — synthetic id stamped on
    plan-level/operator-gated activity rows.
  - `server/orm.py:390` (docstring context ~380-392) — `BlockedRow.claude_session_id` doc: "NULL for: ... the synthetic
    slot_id=0 rows (operator-gated todos, doc_drift findings) that have no originating worker session."
  - `server/blocked_reconcile.py:474` — `row.slot_id == 0` → `agent_tag = "plan_health"` (not a real slot/model tag)
    when paging a blocked row.
  - `server/routes/backlog.py:1039` — `row.slot_id == 0` → routes the answer via
    `post_agent_message_by_role(..., target_role="main")` instead of the normal per-slot message table, because the
    sentinel `enqueue_message` path is a permanent dead-letter (main never drains the worker-lifecycle message table).

  **Meaning C — "main identity" encoded as `slot_id is None` (context_lifecycle.py's own internal convention, not
  literal `0`):**
  - `server/context_lifecycle.py:493-501` — `ContextLifecyclePolicy.tick`: `targets = [("main", main_session, None)]` —
    main is ticked with `slot_id=None`, worker/review targets get their real int `slot_id`.
  - `server/context_lifecycle.py:224-231` — `_latest_context_lifecycle_activity_ts`: `slot_id=None` selects MAIN's
    activity rows (`ActivityRow.slot_id.is_(None)`).
  - `server/context_lifecycle.py:391` + `:1324-1341` (`_read_pct`) — `if slot_id is not None:` branches to the ordinary
    `SlotRow` read; the `else` falls through to `_main_pct(session)` (AgentRow-floored probe) and a hardcoded `"low"`
    pressure fallback when `_main_pct` returns `None` — this hardcoded `"low"` is the `context_pressure` gap the issue's
    summary table cites (now derived via `ss.derive_context_pressure(...)` when `pct` IS available, but still falls back
    to `"low"` on a `None` read).
  - `server/context_lifecycle.py:1118-1148` (`_recover_wedged_target`) — `if slot_id is None:` is the wedge-recovery
    main-specific branch cited in the issue's summary table: kills the tmux session + clears
    `AgentRow (role="main").claude_session_id` directly, bypassing the slot-based `SlotRow` recovery below it (which the
    `slot_id is not None` branch uses instead).
  - `server/main_agent_keeper.py:99-101` — docstring: "Main has no SlotRow, but it DOES have an AgentRow carrying a
    self-reported context_used_pct" — the design note motivating the `_main_pct()` AgentRow-floor special case.

  Net: three distinct encodings of "no real SlotRow" collide today — literal `0` meaning main (A), literal `0` meaning
  "no slot at all, not main" (B), and `None` meaning main inside `context_lifecycle.py` specifically (C). Any fix for
  the todo-2 disambiguation must account for all three, not just the two the issue originally named.

- 2026-08-10 — Todo 2 (disambiguate the sentinel) complete, agent-orchestrator@0efa913. Resolved Meaning B only (A and C
  are untouched — Meaning A's literal `0` for main stays until todo 3 gives main a real `SlotRow`;
  `context_lifecycle.py` already used `is None`, confirmed clean by the audit). Chose a dedicated constant
  (`orm.NO_WORKER_SLOT_SENTINEL = -1`) over a nullable `BlockedRow.slot_id` column: the audit found SQLite has no
  `ALTER COLUMN` support in this repo (only `ADD COLUMN`, guarded by `inspector.get_columns()`), so making an existing
  `NOT NULL` column nullable would need a net-new 12-step-dance migration primitive with zero precedent; a same-shape
  `UPDATE ... SET slot_id = -1 WHERE slot_id = 0` fits the existing `bootstrap.py` migration-function pattern exactly
  (mirrors `_migrate_escalation_root_key`'s backfill). Verified safe to blanket-rewrite: main has no path that ever
  creates a REAL `BlockedRow` with `slot_id=0` today (`main_agent_keeper.py` is the first RESPONDER to worker `/blocked`
  questions, never a creator of its own), so every existing `slot_id=0` row is provably Meaning-B. Touched:
  `bootstrap.py` (write site + new `_migrate_blocked_queue_no_slot_sentinel`, wired into `create_all_tables`),
  `plan_health.py` (doc_drift write), `blocked_reconcile.py` + `routes/backlog.py` (read/branch sites — two
  previously-unguarded `get_slot(row.slot_id)` lookups now self-heal to `None` for a sentinel row since no `SlotRow` is
  ever keyed on `-1`, documented in place), `regen_backlog_from_plan.py`'s raw-sqlite3 GC `DELETE` (easy to miss — not
  ORM). Updated every test fixture constructing `BlockedRow(slot_id=0, ...)` for the Meaning-B shape across 7 files
  (found 2 the initial pass missed: `test_plan_health.py:1441`'s `add_blocked` call-arg assertion and
  `test_regen_backlog_from_plan.py`'s raw-SQL GC seed — both would have silently broken against the new sentinel had
  they not been caught by the targeted pytest run before shipping). New migration test
  `tests/test_migrate_blocked_queue_no_slot_sentinel.py` proves a legacy `slot_id=0` row migrates to `-1`, a real worker
  row (`slot_id=7`) is untouched, and the migration is idempotent. Full suite (3069 passed, 2 skipped) + ruff +
  basedpyright clean.
- 2026-08-10 — Todo 7 (standing guard) complete, agent-orchestrator@c8109bd. Added
  `test_every_context_lifecycle_target_has_slot_row` to `tests/test_context_lifecycle.py`: mirrors
  `ContextLifecyclePolicy.tick()`'s target-list construction (main + review + `_active_worker_slot_ids` workers) and
  asserts every target resolves to a real `SlotRow` — main via `main_agent_keeper.MAIN_SLOT_ID` (its slot_id=None in the
  target list maps there), review/worker via their int slot ids. The mirror is intentional: a future change to
  `tick()`'s target construction must also update this test, at which point the author verifies the new target has a
  SlotRow. Full suite 3093 passed, 2 skipped + ruff + basedpyright clean via `quality-gates.sh`; landed on LDR via
  quickmerge.
- 2026-08-10 — Todo 8 (post-phase codex audit) complete. Rewrote
  `/codex/04-architecture/agent-orchestrator-worker-liveness.md`: appended a new "main is a first-class slot — the
  slot-less special case is retired (operator ruling 2026-08-10)" section recording the ruling, the slot_id-0
  dual-meaning prerequisite resolved via `orm.NO_WORKER_SLOT_SENTINEL = -1` (@0efa913), the real `SlotRow(slot_id=0)`
  owned by `MainAgentKeeper` (@8fedf51), and the dispatch exclusion as the ONE deliberate difference (@3fa500e — the
  `_task_is_routable_to` early-return + `slot_is_spawnable`-never-satisfied, per the `dispatch.py:606-611` incident),
  plus the standing-guard test (@c8109bd). Also SUPERSEDED-in-part-banner'd the "Main's AgentRow floor" paragraph that
  still claimed main had no SlotRow (the `_main_pct` collapse is todo 5, not yet done — the banner says so explicitly),
  and bumped `last_reviewed`. Corpus-wide grep confirmed this codex doc was the only place in `codex/` still documenting
  main's slot-less special-casing as expected. Shipped via safe-doc-push.sh (pure docs).
- 2026-08-10 — Todo 6 (collapse main's derived-pressure + wedge-recovery branches) complete, agent-orchestrator@abcdee3.
  `ContextLifecyclePolicy.tick()` now ticks main as slot `context_lifecycle.MAIN_SLOT_ID` (an independent literal pinned
  equal to `main_agent_keeper.MAIN_SLOT_ID` in the todo-7 guard test), so main reaches the SHARED `_read_pct` and
  `_recover_wedged_target` paths. `_read_pct`'s derived-pressure `slot_id is None` else-branch is deleted — main reads
  its SlotRow like every slot; the probe-vs-self-report ratchet moved to `MainAgentKeeper._sync_main_slot_row` via
  `context_lifecycle.main_pct` (renamed public, was `_main_pct`) so the self-report floor survives the read-path
  collapse. `_recover_wedged_target`'s `slot_id is None` branch is deleted — main uses the shared slot recovery, which
  additionally clears `AgentRow.claude_session_id` for `role == "main"` (main's resume target lives on the AgentRow, not
  just the SlotRow, so the SlotRow clear alone would let AgentKeeper --resume the over-limit transcript).
  `_latest_context_lifecycle_activity_ts` lost its `is_(None)` main filter; `_active_worker_slot_ids` excludes
  `MAIN_SLOT_ID` so main's status=working row never becomes a phantom worker target. slot_id call-chain types tightened
  `int | None → int`. Tests updated to tick main as slot `MAIN_SLOT_ID` (idle-gate, wedge-recovery, thrashing-pressure,
  direct `_read_pct` callers). Full suite passed via `quality-gates.sh`; landed on LDR via quickmerge.

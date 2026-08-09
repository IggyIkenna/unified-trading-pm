---
doc_type: issue
title: Model the main agent as a first-class slot — retire the slot-less special case that keeps producing the same bug class
summary: >-
  Operator ruling 2026-08-10: main becomes a first-class slot. Every defect in the 2026-08-09 context-lifecycle family
  traces to one structural asymmetry — main is the ONE lifecycle target with no SlotRow. That single fact produced
  three separate, independently-patched bugs: no self-reported context floor (main ran to 99% with the safety net
  disarmed), context_pressure hardcoded "low" (the thrashing recycle trigger was structurally unreachable), and a
  terminal wedge-recovery gated behind a force main could never receive. Each was fixed with a main-specific branch and
  a main-specific test; the NEXT slot-based mechanism that forgets main reintroduces the class. Prerequisite discovered
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
    /plans/active/issues/ao_main_review_force_compact_idle_gate_unreachable_2026_08_09.md,
    /plans/archive/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
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

| Gap                          | Consequence                                                      | Patched by                    |
| ---------------------------- | ---------------------------------------------------------------- | ----------------------------- |
| No self-reported pct floor   | main ran to 99% with the compaction net disarmed for 4.3h        | `_main_pct()` (AgentRow floor) |
| `context_pressure` hardcoded | `pressure == "thrashing"` recycle unreachable for main           | derive-pressure commit         |
| Wedge recovery behind a force | terminal recovery unreachable when the idle gate never opens      | saturation-entry commit        |

Three fixes, three main-specific branches, three main-specific tests — all compensating for one missing row. The
fourth mechanism to assume "targets have SlotRows" starts the cycle again.

## Prerequisite: slot_id 0 currently means two different things

Discovered while scoping — this must be resolved BEFORE main gets a real row, or the two meanings collide:

- `autospawn._MAIN_SLOT_ID = 0` — main's slot identity (`autospawn.py:823`, `:3064`;
  `deepseek_usage_poller.py:478` maps `slot_id == 0` → `MAIN_SESSION_NAME`).
- **A synthetic sentinel** for rows that belong to no worker slot — plan-level/operator-gated activity
  (`bootstrap.py:931` "sentinel: plan-level, no worker slot", `orm.py:390`, `blocked_reconcile.py:474`).

Writing a real `SlotRow(slot_id=0)` for main while the sentinel meaning persists would make every plan-level activity
row appear to belong to main.

## Non-goals

- main must NOT become dispatchable for backlog tasks. `dispatch.py` and `autospawn` currently exclude it; that
  exclusion is intended behaviour and must survive (`dispatch.py:606-611` records the incident where an unconfigured
  slot 0 read as permanently claimable and burned a budget slot every tick, forever).
- Not a rewrite of the context-lifecycle policy. The point is to delete special cases, not change compaction
  semantics — main's observable compaction behaviour should be unchanged by this work.

## Todos

- [ ] [BACKEND] P1. Audit and record every site that special-cases main by its lack of a SlotRow, and every site that
      reads `slot_id == 0`, classifying each as "main identity" vs "no-slot sentinel". Done-when: the inventory is in
      this doc's Progress Log with file:line for each, and each is labelled with which of the two meanings it uses.
- [ ] [BACKEND] P1. Disambiguate the sentinel: give the no-worker-slot rows a distinct marker (a nullable `slot_id`
      or a dedicated sentinel value that cannot collide with a real slot id) and migrate existing rows. Done-when: no
      code path uses `slot_id == 0` to mean "no slot", and a migration test proves existing plan-level rows still
      resolve correctly.
- [ ] [BACKEND] P1. Create and maintain a real `SlotRow` for main (id per the audit's decision), owned by
      `MainAgentKeeper`: `status`, `context_used_pct`, `context_pressure`, `last_ping`, `claude_session_id` kept
      current on the keeper's own tick. Done-when: `/api/state` shows main's row with a live context pct that tracks
      its AgentRow, and a unit test asserts the keeper writes it every tick.
- [ ] [BACKEND] P1. Prove the dispatch exclusion still holds with the row present: main must never be handed a backlog
      task and must never count toward claimable capacity. Done-when: a unit test asserts `_task_is_routable_to`
      rejects main's slot and that AutoSpawn skips it, with the `dispatch.py:606-611` incident cited in the test's
      docstring.
- [ ] [BACKEND] P2. Collapse `_main_pct()` into the ordinary `_read_pct()` slot path now that main has a row, keeping
      the self-report floor semantics identical (higher of {self-report, probe}, ratchet-up persisted). Done-when: the
      main-specific branch is deleted, and the existing `_main_pct` regression tests pass unchanged against the
      unified path.
- [ ] [BACKEND] P2. Collapse the derived-pressure and wedge-recovery main branches the same way, so main reaches those
      paths as a slot rather than via a special case. Done-when: both main-specific branches are deleted and their
      existing tests pass against the shared path.
- [ ] [BACKEND] P2. Add a standing guard against the regression class: a test asserting every context-lifecycle target
      returned by the policy's own target list has a SlotRow. Done-when: the test fails if a future target is added
      without one.
- [ ] [DOCS] P2. Post-phase codex audit: record the ruling and the resulting shape in
      `/codex/04-architecture/agent-orchestrator-worker-liveness.md`, superseding the sections that document main's
      slot-less special-casing as expected. Done-when: the SSOT describes main as a first-class slot and names the
      dispatch exclusion as the one deliberate difference.

## Progress Log

- 2026-08-10 — Filed on the operator's ruling. Scoping already surfaced the slot_id-0 dual-meaning prerequisite
  (`autospawn._MAIN_SLOT_ID` vs the plan-level sentinel in `bootstrap.py`/`orm.py`/`blocked_reconcile.py`), which is
  why the disambiguation is todo 2 and the row creation is todo 3 rather than the other way round.

---
doc_type: issue
title: OrderTracker has no CANCELLED/AMENDED status — get_instruction_status shows a stale SUBMITTED order forever after a successful cancel
summary: >-
  execution-service's OrderTracker (execution_service/orders/tracker.py) only has two state-transition
  methods -- track_order() (sets "SUBMITTED") and update_fill() (sets "FILLED") -- and neither /cancel nor
  /amend in manual_instruction_api.py calls any tracker-mutating method after a successful venue-side
  cancel/amend. Result: GET /instructions/{id} keeps reporting a genuinely-cancelled order as "SUBMITTED"
  indefinitely, and is_instruction_complete() never flips true for an instruction whose only order was
  cancelled (not filled). Found during the P2 downstream-state audit todo on
  cefi_execution_cancel_amend_fake_success_stub_2026_08_16.md, after that doc's own P0/P1 fixes had already
  made /cancel and /amend themselves return real (non-fake) outcomes -- this is the inverse-direction
  staleness that remained once the direct REST-response risk was closed.
status: open
nature: issue
asset_group: [cefi]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [execution, order-management, order-tracking, stale-state, financial-correctness]
related:
  [
    /plans/archive/issues/cefi_execution_cancel_amend_fake_success_stub_2026_08_16.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-17
author: interactive-session
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Found 2026-08-17 answering the P2 downstream-state-audit todo on
  cefi_execution_cancel_amend_fake_success_stub_2026_08_16.md -- direct read of
  execution_service/orders/tracker.py's full class body plus every caller of order_tracker in
  manual_instruction_api.py.
context_scope:
  [
    execution-service/execution_service/orders/tracker.py,
    execution-service/execution_service/api/manual_instruction_api.py,
    execution-service/execution_service/engine/orchestrator.py,
    /plans/archive/issues/cefi_execution_cancel_amend_fake_success_stub_2026_08_16.md,
  ]
---

# OrderTracker has no CANCELLED/AMENDED status

## What I found

`execution_service/orders/tracker.py`'s `OrderTracker` class has exactly two state-transition methods:
`track_order()` (sets `status="SUBMITTED"` when an order starts being tracked) and `update_fill()` (sets
`status="FILLED"` on a fill). No method writes `"CANCELLED"` or `"AMENDED"` anywhere in the class.

`manual_instruction_api.py`'s `/cancel` and `/amend` handlers call the real per-venue adapter (via the
`ExecutionOrchestrator` chain built in `cefi_execution_cancel_amend_fake_success_stub_2026_08_16.md`'s P0/P1/P2
fixes) and return the venue's genuine result to the caller — but neither handler calls any `order_tracker`
mutation afterward. So the one and only status field this service's own downstream state exposes
(`OrderTracker._order_status[order_id]["status"]`) never learns that a cancel/amend happened at all.

Consequence: `GET /instructions/{id}` (`get_instruction_status`) keeps reporting a successfully-cancelled order
as `"SUBMITTED"` indefinitely, and `is_instruction_complete()` (which requires every order to show `"FILLED"`)
never returns `True` for an instruction whose only order was cancelled rather than filled — so the instruction's
own aggregate `status` also stays `"IN_PROGRESS"` forever, even though nothing further will ever happen to it.

Separately, `engine/orchestrator.py`'s `instruction_to_order_ids`/`order_id_to_instruction` dicts (a different,
unrelated tracking structure used only for orchestrator lookup) are also never pruned on cancel — lower-impact
(no status field, lookup-only) but noted for completeness.

No reachable position-ledger write path was found from either `/cancel` or `/amend` in this service — so there
is no separate position-ledger staleness to report; `OrderTracker` is the only downstream state surface that
reads order lifecycle here.

## Why it matters

A caller who queries `GET /instructions/{id}` after a genuinely successful `/cancel` gets told the order is
still `SUBMITTED` — the operational inverse of the original stub bug this was found auditing (that bug was "the
REST response lies that cancellation happened"; this one is "the REST response is honest at cancel time, but a
later status check lies that the order is still live"). Same class of risk: a caller could re-hedge, retry, or
report a stale open-order count based on this, believing an order is still live when it's actually dead.

## Todos

- [x] ✅ [BACKEND] P2. Add a `mark_cancelled(order_id)` / `mark_amended(order_id, ...)` method to `OrderTracker`
      (repo: execution-service) and call it from `/cancel`'s and `/amend`'s success paths in
      `manual_instruction_api.py` after the venue call succeeds. `is_instruction_complete()` (or a new
      equivalent) should treat an instruction whose only open order is now `CANCELLED` as terminal too, not
      stuck `IN_PROGRESS` forever. Done-when: a test proves `GET /instructions/{id}` reflects `CANCELLED` status
      immediately after a successful `/cancel`, and the instruction's aggregate status is no longer stuck
      `IN_PROGRESS` when its only order is cancelled. — execution-service@99e34929a5. Added
      `mark_cancelled`/`mark_amended` to `OrderTracker`, wired both into `/cancel`/`/amend`'s success paths, and
      widened `is_instruction_complete()`'s terminal-status set to `{FILLED, CANCELLED}`. New unit tests in
      `tests/unit/test_order_tracker.py` (`TestMarkCancelled`/`TestMarkAmended`) prove a cancelled-only
      instruction is now terminal; existing `_FakeOrderTracker` test doubles updated to match the new interface.
- [ ] [BACKEND] P3. Prune (or at least stop relying on staleness of) `instruction_to_order_ids`/
      `order_id_to_instruction` in `engine/orchestrator.py` once an order is cancelled/amended-away, or document
      why leaving them populated is intentional (repo: execution-service). Lower priority than the P2 above —
      no status field is derived from these, only lookup routing.

## Progress Log

- **2026-08-17**: Filed while answering the P2 downstream-state-audit todo on
  `cefi_execution_cancel_amend_fake_success_stub_2026_08_16.md`. Both todos above are net-new fix work, kept out
  of that doc's own scope per this workspace's findings-triage rule (audits report evidence + tracked
  follow-ups, they don't silently absorb the fix).
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)

---
doc_type: plan
title: ExecutionOrchestrator order-submission → OMS persistence wiring (design)
summary: >-
  ExecutionOrchestrator (the class execution-service's live order-submission path actually uses) never
  writes order state into any OMS -- confirmed via repo-wide grep during w_state_recovery_real_wiring_2026_08_20.
  This is the reason that plan's own OrderRecoveryEngine startup-wiring todo was deliberately left open: a
  correctly-implemented OrderBook is still structurally guaranteed empty at every real startup, because
  nothing in the live process ever populates it, and wiring recovery in regardless would cancel legitimate
  open orders on every restart. This plan is DESIGN-ONLY, no code — it resolves the open design questions
  (write contract, persistence backend, hot-path latency/correctness tradeoff, existing-consumer interaction)
  so a follow-up implementation plan can be dispatched against a settled decision, not an open-ended judgment
  call. No owning plan existed at authoring time; spun out 2026-08-20 with the operator's direct authorization
  (relayed via the dispatching session, same day as w_state_recovery_real_wiring's own spin-out), following
  the same pattern as W14/W15/W22.
status: complete # archived 2026-08-21 — every todo done; close-out verified by finalize plan
nature: design
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [execution, oms, order-state, persistence, state-recovery]
related:
  [
    /plans/active/w_state_recovery_real_wiring_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
    /plans/active/code_readiness_t4_execution_settlement_2026_08_19.md,
  ]
created: 2026-08-20
last_updated: 2026-08-21
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: design
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 2.4
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on: [w_state_recovery_real_wiring_2026_08_20]
supersedes:
superseded_by:
locked_by:
locked_since:
source: >-
  Spun out of w_state_recovery_real_wiring_2026_08_20's Close-out section (its own STOP-AND-DOCUMENT
  annotation on Phase 3 todo 1) after that plan's dispatch found, via repo-wide grep, that
  ExecutionOrchestrator/OrderAdapterMatchingEngine (execution_service/engine/orchestrator.py -- the class
  _run_live_async actually constructs via _create_orchestrator_for_venue, NOT the separate, disconnected
  engine/live/ stack) never calls UnifiedOrderManager.create_order()/update_order_status() anywhere. The
  only production writers of that OMS are the entirely disconnected engine/live/ stack
  (LiveExecutionOrchestrator + create_oms()/create_orchestrator() in engine/live/factory.py, zero callers
  from any live entry point) and backtest actors (batch mode). Nor does anything else durably persist live
  order state across a restart: OrderAdapterMatchingEngine.submit_order() (orchestrator.py) delegates to
  OrderAdapter.submit_order() (adapters/order_adapter.py), which writes an audit-log JSONL blob per event
  (execution_service/utils/audit_log.py -- write-only, not a queryable current-state store) and an
  idempotency cache with a 300s TTL (_ORDER_CACHE, in-memory, non-durable); ExecutionContext.submitted_orders
  (orchestrator.py's own per-instruction order list) is also in-memory only, scoped to the orchestrator
  instance's lifetime, lost on restart. w_state_recovery_real_wiring_2026_08_20 built a real, tested
  OrderBook wrapping UnifiedOrderManager (execution-service@458c70c48e) -- proven to round-trip correctly
  whenever something writes to it -- but nothing in the live path does.
context_scope:
  [
    execution-service/execution_service/engine/orchestrator.py,
    execution-service/execution_service/orders/oms.py,
    execution-service/execution_service/trade_execution/oms/,
    execution-service/execution_service/engine/live/,
    execution-service/execution_service/adapters/order_adapter.py,
    execution-service/execution_service/engine/startup/order_recovery.py,
    /plans/active/w_state_recovery_real_wiring_2026_08_20.md,
  ]
---

# ExecutionOrchestrator order-submission → OMS persistence wiring (design)

> A recovery engine can only reconcile state someone actually wrote down. `OrderRecoveryEngine`'s own
> `OrderBook` is real and correct now; this plan is about making sure it has something to read. Epic section:
> `/plans/epics/system_readiness_master.md` ("Execution carries full order lifecycle, state recovery,
> reconciliation and manual trade on every venue").

## Todos

### Phase 1 — establish the write contract (design, blocks everything after)

- [x] 1. ✅ [AGENT] P0. **Enumerate every real order-mutating code path in the LIVE flow.** Confirmed via full
      read of `engine/orchestrator.py`, `adapters/order_adapter.py`, `cli/handlers/live_execution_handler.py`,
      `v2/atomic_leg_executor.py`, `api/manual_instruction_api.py` + its `manual_instruction_submit.py`/
      `manual_instruction_cancel_amend.py` submodules — every real write funnels through exactly ONE choke
      point, `OrderAdapter` (`adapters/order_adapter.py`): (1) `ExecutionOrchestrator._submit_single_child_order`
      → `matching_engine.submit_order` → `OrderAdapterMatchingEngine.submit_order` → `OrderAdapter.submit_order`;
      (2) `ExecutionOrchestrator._submit_algo_follow_orders` (algo-generated post-fill orders) → the SAME
      `matching_engine.submit_order` chain — a second call site the starting inventory missed, found only by
      reading the whole file; (3) `ExecutionOrchestrator.cancel_order` → `OrderAdapterMatchingEngine.cancel_order`
      → `OrderAdapter.cancel_order`; (4) `ExecutionOrchestrator.amend_order` → same chain →
      `OrderAdapter.amend_order`. Manual API: `manual_instruction_submit.py::_execute_via_orchestrator` calls
      `_core._orchestrator.execute_instruction(...)` on the SAME `ExecutionOrchestrator` instance
      `_build_orchestrators_for_instructions` registers via `manual_instruction_api.set_orchestrator(orch)` —
      manual instructions do NOT bypass `ExecutionOrchestrator`, confirmed, no separate write path needed.
      OUT OF SCOPE, confirmed not assumed: `AtomicLegExecutor._place_leg` (`v2/atomic_leg_executor.py`) calls
      `self._adapter.place_bet(order)` — a `SportsAdapter`, structurally unrelated to `OrderAdapter`/
      `CanonicalOrder`; `engine/live/` (`LiveExecutionOrchestrator`/`SmartOrderRouter`/`factory.py`) has its own
      separate `create_oms()` wiring but zero production callers from any live entry point (re-confirmed this
      session).
- [x] 2. ✅ [AGENT] P0. **Write contract decided: full state-machine shape, not lighter-weight.** Every child
      order gets `UnifiedOrderManager.create_order()` at submission and `update_order_status()` on every
      subsequent transition (SUBMITTED/FILLED/PARTIAL_FILLED/REJECTED/CANCELLED) — mirrors
      `handle_nautilus_order_event()`'s existing shape. Reasoning: `OrderRecoveryEngine.recover_venue()` compares
      `OrderBook.get_pending_orders(venue)` against live exchange state; skipping the SUBMITTED transition would
      make a genuinely-live order indistinguishable from one that's been stuck PENDING for hours, defeating
      recovery's own state model. Trigger point: `OrderAdapter` itself (not a different layer) — it already has
      the exact right hook points, one step earlier than its existing `persist_audit_log` calls. Full mapping,
      including the cancel-audit-ordering fix, is in the 2026-08-21 Progress Log entry below.
- [x] 3. ✅ [AGENT] P0. **Persistence backend decided: `PostgreSQLOrderPersistence`
      (`engine/live/persistence/postgresql.py`) — it EXISTS, is ALREADY constructed by
      `_create_startup_order_recovery` (`live_execution_handler.py:181`, gated on `config.use_database` +
      `config.database_url`), and already implements the exact `OrderPersistenceAdapter` protocol
      `UnifiedOrderManager` requires — but its 6 methods are 100% `NotImplementedError` stubs** (verified by
      full read, not the codex doc's characterization alone). This is the concrete gap: not "which backend" —
      that choice is already made by precedent — but "implement this backend's body." Concrete schema + method
      mapping in the Progress Log below; implementing it is the follow-up plan's Phase A.
- [x] 4. ✅ [AGENT] P1. **Hot-path latency/correctness tradeoff decided: synchronous/awaited, fail-open on
      persistence failure.** `create_order()` is awaited before the venue call proceeds (zero NEW latency
      shape — `OrderAdapter._log_order_created()`'s audit-log write already sits at that exact point).
      `update_order_status()` on every transition is likewise awaited (ordering correctness — a later event
      must never race an unpersisted PENDING record) but wrapped in the SAME broad
      catch-log-continue contract `persist_audit_log` already uses (never blocks real trading on a
      persistence outage) — EXCEPT the failure is LOUD (`log_event("OMS_WRITE_FAILED", ...)` + `logger.error`,
      no silent swallow) since a silent gap here reintroduces the exact empty-`OrderBook` hazard this whole
      plan exists to close.

### Phase 2 — reconcile with existing state, don't duplicate or diverge

- [x] 5. ✅ [AGENT] P1. **`ExecutionContext.submitted_orders` interaction decided: COEXIST, unchanged.**
      `submitted_orders: list[ChildOrder]` (`engine/execution/context.py`) stays the fast in-memory
      per-instruction cache it already is — no `operation_id`/OMS-key linkage exists or is needed; its only
      consumers (`get_order_status`, `_build_instruction_fill_result`) are current-process-lifetime views the
      OMS was never meant to replace. `order_id_to_instruction`/`instruction_to_order_ids` likewise stay
      as-is (they key on exchange order_id, the manual-API's own lookup path). Zero existing consumer touched.
- [x] 6. ✅ [AGENT] P1. **No collision with `engine/live/`'s own OMS usage, by construction.** The write
      contract lives entirely inside `OrderAdapter`, which `engine/live/` never imports or calls (re-confirmed
      via grep this session — zero references to `adapters.order_adapter` under `engine/live/`). Named risk
      for whoever eventually wires up `engine/live/`: at that point both stacks MUST share ONE
      `UnifiedOrderManager`/`PostgreSQLOrderPersistence` instance (same single-source-of-truth principle Phase
      1 todo 1 of `w_state_recovery_real_wiring_2026_08_20` already established for `OrderBook`), never two
      independent writers for the same live orders.
- [x] 7. ✅ [AGENT] P2. **Test strategy decided.** Extend the existing `orchestrator`/`mock_order_adapter`
      fixtures in `tests/unit/engine/execution/test_orchestrator.py` with an optional
      `oms: UnifiedOrderManager | None = None` constructor param on `ExecutionOrchestrator.__init__` and
      `OrderAdapter.__init__` (default: fresh `UnifiedOrderManager(InMemoryOrderPersistence())`, mirrors
      `OrderBook.__init__`'s own existing "constructible without caring about book state" default) — every
      existing test keeps passing unchanged. New: an `OrderAdapter`-level test module covering
      create-before-venue-call, status-update-after-venue-call (FILLED/REJECTED/else-SUBMITTED), cancel-only-
      after-confirm (the in-flight-vs-confirmed regression this design fixes), and fail-open-on-OMS-outage; one
      new integration test in `tests/unit/engine/test_order_recovery.py` proving an order written via the new
      `OrderAdapter` path is visible to `OrderBook.get_pending_orders()` when both share one
      `UnifiedOrderManager` — the actual end-to-end proof this whole plan exists to produce. Exact file list is
      the implementation plan's own task, per this todo's original scoping.

### Close-out

- [x] 8. ✅ [AGENT] P0. **Final design spec written** — see the 2026-08-21 Progress Log entry below for the
      complete, symbol-level spec (write contract, persistence schema, latency tradeoff, all interaction
      decisions) a follow-up implementer can start coding from without re-deriving anything.
- [x] 9. ✅ [AGENT] P1. **Follow-up implementation plan authored**:
      `/plans/active/w_execution_orchestrator_oms_persistence_impl_2026_08_21.md` (+ mandatory finalize
      companion `..._impl_2026_08_21_finalize.md`), `assigned_vm: planning`, referencing every decision above by
      todo number. `w_state_recovery_real_wiring_2026_08_20`'s Close-out section updated to point at it
      (scoped edit, see that plan's own Progress Log for the pointer).
- [x] 10. ✅ [AGENT] P2. **Post-design codex audit run** — `/codex/04-architecture/cross-domain-state-fabric.md`'s
      `OrderRecoveryEngine` note updated (unified-trading-pm, this session) to name the concrete implementation
      plan now that one exists, replacing the prior "a real, deliberate, TRACKED prerequisite gap" language with
      a pointer to the scoped plan.

## Progress Log

> Append-only. Record shas, corrections, and traps here as work lands.

- **2026-08-20, T4 sub-agent dispatch**: plan authored after the coordinator (interactive session) explicitly
  agreed this needed its own design-only plan rather than being tackled inline during
  `w_state_recovery_real_wiring_2026_08_20`'s own dispatch — "ExecutionOrchestrator's order-submission → OMS
  persistence wiring is genuinely a different risk class (live hot path, not startup-only) and deserves its
  own design pass." Scoping (exact call sites, existing audit-log/idempotency-cache non-durability, the
  disconnected `engine/live/` stack's own separate OMS usage) carried over directly from real measurements
  made during the parent plan's own dispatch the same day, not re-derived from scratch.

- **2026-08-21, AO sub-agent dispatch — full design closed, all 10 todos, no code changed.** Confirmed via
  `check-ao-backlog-status.sh` at dispatch start: all 13 backlog tasks for this plan + its finalize were
  `queued`, none `dispatched` elsewhere, none `done` — no collision, worked every todo. Full read of
  `engine/orchestrator.py` (629L), `adapters/order_adapter.py` (282L), `utils/audit_log.py` (83L),
  `orders/oms.py`, `trade_execution/oms/persistent_oms.py` + `protocols.py` (READ-ONLY — both under active
  concurrent edit this session by a different sub-agent doing an `OrderStatus`/`is_legal_local_transition`
  dedup into a new `orders/order_status.py` module; this design cites only their STABLE public method
  signatures, `create_order`/`update_order_status`, unaffected by that refactor), `cli/handlers/
  live_execution_handler.py` (656L), `engine/live/factory.py`, `engine/live/persistence/{postgresql,protocols,
  in_memory}.py`, `engine/live/config.py`, `v2/atomic_leg_executor.py` (order-mutating grep), `api/
  manual_instruction_api.py` + submodules, `engine/execution/{types,context}.py`, `trade_execution/factory.py`
  (venue registries), `engine/startup/order_recovery.py` (signatures only — already shipped, read-only),
  `tests/unit/engine/execution/test_orchestrator.py` (existing fixture shape).

  **THE single highest-leverage finding**: `PostgreSQLOrderPersistence` (`engine/live/persistence/
  postgresql.py`) is not a design choice to make — it already exists, already implements
  `OrderPersistenceAdapter`, and is ALREADY constructed today by `_create_startup_order_recovery`
  (`live_execution_handler.py:181`) whenever an operator sets `USE_DATABASE=true`+`DATABASE_URL`. Every one
  of its 6 methods is `raise NotImplementedError("PostgreSQL order persistence not yet implemented")`
  (`_require_db()` guards each). `NotImplementedError` IS a `RuntimeError` subclass, so today's
  `_run_startup_order_recovery`'s `except (ValueError, RuntimeError, OSError)` already catches it gracefully
  (logs, returns, does not crash the server) — a real, if accidental, existing safety property, confirmed by
  reading the exact except clause, not assumed. The persistence-backend decision (Phase 1 todo 3) is
  therefore "implement this stub's 6 method bodies," not "pick a backend."

  **Full write contract (Phase 1 todo 2), concrete hook points in `OrderAdapter`
  (`execution_service/adapters/order_adapter.py`):**
  - `submit_order()` (currently lines 90-129): call `oms.create_order(operation_id=client_order_id,
    canonical_id=instrument_id, venue=str(getattr(self.venue_client, "venue", "")),
    venue_type=<"CCXT" if venue in trade_execution.factory.CCXT_VENUES else "REST" if in DIRECT_REST_VENUES
    else "UNKNOWN">, side=side, quantity=quantity, price=price or Decimal("0"), strategy_id=str(instruction
    .params.get("strategy_id", "")) if threaded down, else "")` immediately before `_log_order_created()`'s
    existing pre-venue-call site (line 108-109) — mirrors that exact ordering, one call earlier than nothing
    was there before. After the venue call returns, where `_log_post_submit_audit` already branches on
    `status_upper` (line 120-124): call `oms.update_order_status(client_order_id, <"FILLED" if
    status_upper=="FILLED" else "REJECTED" if status_upper=="REJECTED" else "SUBMITTED">,
    venue_order_id=result.order_id, fills=[...] if FILLED)`.
  - `cancel_order()` (lines 207-221): **real pre-existing gap found, directly matching the epic's own W11
    line** (`/plans/epics/system_readiness_master.md`: "a cancel attempted before confirmation and one after
    are different events, and an audit record that cannot tell them apart cannot answer the question that
    matters after an incident") — today's code writes `persist_audit_log("ORDER_CANCELLED", ...)` BEFORE
    calling `self.venue_client.cancel_order(...)`, i.e. logs success before confirmation. Already tracked
    separately by the epic's own cross-reference (`execution_order_tracker_missing_cancelled_amended_status_
    2026_08_17`, P2) — not this plan's file to fix in the existing GCS audit log. The NEW OMS write must NOT
    repeat that mistake: call `oms.update_order_status(order_id, "CANCELLED")` ONLY AFTER
    `self.venue_client.cancel_order(...)` returns (it raises on failure, never a fake success, per the
    adapter's own existing contract) — so the durable OMS record, unlike the GCS audit log, only ever
    reflects a CONFIRMED cancel.
  - `amend_order()` (lines 223-255): amend changes quantity/price, not status — `UnifiedOrderManager` has NO
    method for this today. Real, named gap for the implementation plan: add
    `update_order_quantity_price(operation_id, *, quantity, price)` to `OrderPersistenceAdapter`
    (`engine/live/persistence/protocols.py`) + `UnifiedOrderManager` (`orders/oms.py`) +
    `InMemoryOrderPersistence`/`PostgreSQLOrderPersistence`, called from `OrderAdapter.amend_order()` AFTER
    venue confirmation (matches that method's own existing "audit log after, not before" convention, lines
    233-238) — a stale quantity would misclassify a resting order during `OrderRecoveryEngine.recover_venue`'s
    reconciliation, so this is not optional polish.
  - `_submit_algo_follow_orders` (`engine/orchestrator.py:568-595`) reuses the SAME
    `matching_engine.submit_order` → `OrderAdapter.submit_order` chain as the primary submission path — no
    separate write needed, the hook above already covers it.

  **Persistence schema (Phase 1 todo 3)** — `PostgreSQLOrderPersistence`'s 6 stub methods
  (`initialize`/`save_order`/`get_order`/`update_order_status`/`get_all_orders`/`get_orders_by_status`/
  `get_orders_by_strategy`) map 1:1 onto:
  ```sql
  CREATE TABLE IF NOT EXISTS oms_orders (
      operation_id TEXT PRIMARY KEY,
      canonical_id TEXT NOT NULL,
      venue TEXT NOT NULL,
      venue_type TEXT NOT NULL,
      side TEXT NOT NULL,
      quantity NUMERIC NOT NULL,
      price NUMERIC NOT NULL,
      strategy_id TEXT NOT NULL DEFAULT '',
      status TEXT NOT NULL,
      venue_order_id TEXT,
      fills JSONB NOT NULL DEFAULT '[]',
      created_at TIMESTAMPTZ NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_oms_orders_venue ON oms_orders (venue);
  CREATE INDEX IF NOT EXISTS idx_oms_orders_status ON oms_orders (status);
  CREATE INDEX IF NOT EXISTS idx_oms_orders_strategy ON oms_orders (strategy_id);
  ```
  `initialize()` = pool setup + the `CREATE TABLE IF NOT EXISTS` above; `save_order` = `INSERT`; `get_order` =
  `SELECT ... WHERE operation_id=$1`; `update_order_status` = `UPDATE ... SET status=$2,
  venue_order_id=COALESCE($3, venue_order_id), fills=COALESCE($4, fills), updated_at=now() WHERE
  operation_id=$1`; the three `get_orders_by_*` = `SELECT` with the obvious `WHERE`. Both `orders/oms.py`'s
  `UnifiedOrderManager` and `trade_execution/oms/persistent_oms.py`'s `PersistentOrderManager` already consume
  any `@runtime_checkable`-protocol-shaped object — this ONE backend serves both without either file changing.
  This is also, by construction, the SAME instance both `OrderRecoveryEngine`'s `OrderBook` (startup) and
  `ExecutionOrchestrator` (hot path, via `OrderAdapter`) must share — `_create_orchestrator_for_venue`
  (`live_execution_handler.py:328-349`) currently builds `ExecutionOrchestrator` with no OMS at all; the
  implementation plan must thread the SAME `UnifiedOrderManager` `_create_startup_order_recovery` builds
  into every `OrderAdapter` construction site (one OMS instance per process, not per venue).

  **Minor adjacent finding, NOT fixed here (out of this plan's scope, no code touched):**
  `ExecutionOrchestrator._handle_execution_error`/`_handle_order_submission_error`
  (`engine/orchestrator.py`) read `getattr(instruction, "exchange", "unknown")` for logging/metrics labels,
  but `Instruction`'s actual field (`engine/execution/types.py`) is named `venue`, not `exchange` — the
  getattr fallback silently always fires, mislabeling every error-path metric/log as `venue="unknown"`. Left
  as-is: unrelated to persistence, and editing `orchestrator.py` risked touching a file adjacent to this
  session's own collision-avoidance list. Noted here per the "a doc/comment/pointer that MISLED you is a
  finding" rule's spirit — worth a follow-up todo, not urgent enough to justify an out-of-scope edit today.

  **No code changed this session** — every decision above is a design decision recorded in this Progress Log
  + the checked-off todos; the follow-up implementation plan
  (`w_execution_orchestrator_oms_persistence_impl_2026_08_21.md`) carries the actual code-change todos.

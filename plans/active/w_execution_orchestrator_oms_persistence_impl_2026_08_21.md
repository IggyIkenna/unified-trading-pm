---
doc_type: plan
title: ExecutionOrchestrator order-submission → OMS persistence wiring (implementation)
summary: >-
  Implements the design closed in w_execution_orchestrator_oms_persistence_2026_08_20 (see that plan's
  2026-08-21 Progress Log entry for the full spec) -- fills in PostgreSQLOrderPersistence's 6 stub methods,
  wires UnifiedOrderManager.create_order()/update_order_status() calls into OrderAdapter at the exact hook
  points that design named, threads one shared OMS instance from startup into both OrderRecoveryEngine's
  OrderBook and every ExecutionOrchestrator, and extends the test suite per that design's test-strategy
  decision. Every todo below cites the design plan's todo number it implements -- no open design questions,
  by construction (the design plan's own finalize re-verified this before this plan was authored).
status: active
nature: process
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [execution, oms, order-state, persistence, state-recovery, implementation]
related:
  [
    /codex/04-architecture/cross-domain-state-fabric.md,
    /plans/active/w_state_recovery_real_wiring_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
    /plans/active/code_readiness_t4_execution_settlement_2026_08_19.md,
  ]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on: [w_execution_orchestrator_oms_persistence_2026_08_20]
gate_on_depends: true
supersedes:
superseded_by:
locked_by:
locked_since:
source: >-
  Follow-up implementation plan authored per w_execution_orchestrator_oms_persistence_2026_08_20's Close-out
  todo 9 ("Author the follow-up implementation plan"), which that design-only plan's own text requires be a
  new, separate assigned_vm: planning plan referencing its decisions -- not a re-derivation. Every persistence
  schema, hook-point, and interface-extension decision below is copied from that plan's 2026-08-21 Progress
  Log entry, not re-designed here.
context_scope:
  [
    /plans/archive/2026_08/w_execution_orchestrator_oms_persistence_2026_08_20.md,
    execution-service/execution_service/engine/live/persistence/postgresql.py,
    execution-service/execution_service/engine/live/persistence/protocols.py,
    execution-service/execution_service/adapters/order_adapter.py,
    execution-service/execution_service/orders/oms.py,
    execution-service/execution_service/cli/handlers/live_execution_handler.py,
    execution-service/tests/unit/engine/execution/test_orchestrator.py,
  ]
---

# ExecutionOrchestrator order-submission → OMS persistence wiring (implementation)

> Implements `w_execution_orchestrator_oms_persistence_2026_08_20`'s design (read that plan's 2026-08-21
> Progress Log entry FIRST — the full write contract, schema, and hook points are there, not repeated here in
> full). Epic section: `/plans/epics/system_readiness_master.md` ("Execution carries full order lifecycle,
> state recovery, reconciliation and manual trade on every venue").

## Todos

### Phase A — persistence backend (blocks everything after; single highest-leverage change)

- [x] ✅ [BACKEND] P0. **Implement `PostgreSQLOrderPersistence`'s 6 stub methods**
      (`execution_service/engine/live/persistence/postgresql.py`) against the exact `oms_orders` schema in
      the design plan's Progress Log (operation_id PK, canonical_id, venue, venue_type, side, quantity NUMERIC,
      price NUMERIC, strategy_id, status, venue_order_id, fills JSONB, created_at/updated_at TIMESTAMPTZ, plus
      the 3 named indexes). First sub-step: survey the repo for an existing async postgres client convention
      (grep for `asyncpg`/`sqlalchemy` imports repo-wide — as of the design session, zero other real postgres
      call sites existed) and use whatever the survey finds, or `asyncpg` directly if none exists. `initialize()`
      = pool setup + `CREATE TABLE IF NOT EXISTS`; `save_order`=INSERT; `get_order`=SELECT by operation_id;
      `update_order_status`=UPDATE with COALESCE on optional fields; the 3 `get_orders_by_*`=SELECT with the
      obvious WHERE. Done-when: `PostgreSQLOrderPersistence` has zero `NotImplementedError` bodies remaining and
      `quality-gates.sh` is green. Implements design plan todo 3.
- [x] ✅ [BACKEND] P0. **Add `update_order_quantity_price(operation_id, *, quantity, price)`** to
      `OrderPersistenceAdapter` (`engine/live/persistence/protocols.py`), `UnifiedOrderManager` (`orders/oms.py`
      — coordinate with whatever `orders/order_status.py` dedup landed by the time this runs, that refactor
      only moved `OrderStatus`/`is_legal_local_transition`, not the class's public method surface),
      `InMemoryOrderPersistence`, and the new `PostgreSQLOrderPersistence` body from the prior todo. Implements
      design plan todo 2's amend-order gap. Done-when: a round-trip test proves `get_order()` reflects the new
      quantity/price after the call, against BOTH persistence backends. — execution-service@f1f3dfc3 + evidence:
      quality-gates.sh passed (8,876 passed, 22 skipped, 1 xpassed).
- [ ] [BACKEND] P1. **Integration-test `PostgreSQLOrderPersistence` against a real (or test-container) Postgres**
      — decide the exact test-infra approach at implementation time (a local ephemeral container is the
      preferred shape; if the repo's existing test suite has no such pattern, mock only at the driver-call
      boundary, never re-implement the SQL in the test). Done-when: `save_order`→`get_order`→
      `update_order_status`→`get_order` round-trips correctly, proving the schema and query bodies are right,
      not just that they don't raise.

### Phase B — write contract in `OrderAdapter` (the hot-path wiring)

- [x] ✅ [BACKEND] P0. **Thread an optional `oms: UnifiedOrderManager | None = None` param into
      `OrderAdapter.__init__`** (`adapters/order_adapter.py`) and `OrderAdapterMatchingEngine.__init__`
      (`engine/orchestrator.py`), defaulting to a fresh `UnifiedOrderManager(InMemoryOrderPersistence())` when
      not supplied — mirrors `OrderBook.__init__`'s own existing default-constructible pattern
      (`engine/startup/order_recovery.py`). Implements design plan todo 7 (test strategy). — execution-service@f4cb199b48 + evidence: quality-gates.sh passed; quickmerge ancestry verified.
- [x] ✅ [BACKEND] P0. **Wire `oms.create_order()`/`update_order_status()` calls into `OrderAdapter.submit_order()`**
      at the exact points the design plan's Progress Log names — `create_order` immediately before the
      existing `_log_order_created()` call, `update_order_status` immediately after `_log_post_submit_audit`'s
      existing status branch (FILLED/REJECTED/else-SUBMITTED). Wrap both in the fail-open
      `try/except (ConnectionError, OSError, RuntimeError, TimeoutError)` contract from design plan todo 4 —
      `logger.error` + `log_event("OMS_WRITE_FAILED", ...)`, no re-raise, venue call proceeds regardless.
      Implements design plan todos 2 and 4. — execution-service@4e915b637a + evidence: full quality-gates.sh passed (8,892 passed, 22 skipped, 1 xpassed); gitleaks passed.
- [x] ✅ [BACKEND] P0. **Wire `oms.update_order_status(order_id, "CANCELLED")` into `OrderAdapter.cancel_order()`
      AFTER `self.venue_client.cancel_order(...)` returns, never before** — the in-flight-vs-confirmed fix
      named in the design plan's Progress Log (distinct from, and does not touch, the existing pre-confirmation
      GCS audit-log write, which stays as-is per that same entry). Same fail-open wrapping as the prior todo.
      Implements design plan todo 2. — execution-service@4e915b637a + evidence: full quality-gates.sh passed (8,892 passed, 22 skipped, 1 xpassed); gitleaks passed.
- [x] ✅ [BACKEND] P1. **Wire `oms.update_order_quantity_price(...)` into `OrderAdapter.amend_order()` AFTER venue
      confirmation** (matches that method's existing "audit log after, not before" convention). Depends on
      Phase A todo 2 landing first (same-file, sequential within this plan — see `sequential` note below applies
      only within this phase; Phase A/B are otherwise independent files). Implements design plan todo 2. — execution-service@4e915b637a + evidence: full quality-gates.sh passed (8,892 passed, 22 skipped, 1 xpassed); gitleaks passed.

### Phase C — thread one shared OMS instance from startup

- [x] ✅ [BACKEND] P0. **Build the `UnifiedOrderManager` ONCE per process in `_run_live_async`**
      (`cli/handlers/live_execution_handler.py`), backed by `PostgreSQLOrderPersistence` when
      `config.use_database and config.database_url` else `InMemoryOrderPersistence` (dev/test fallback) —
      thread that SAME instance into both `_create_startup_order_recovery` (replacing its own private
      construction at line ~181) and every `_create_orchestrator_for_venue` call (passed through to the new
      `OrderAdapter(oms=...)` param from Phase B). This is the single-source-of-truth requirement from design
      plan todo 6 — `OrderRecoveryEngine`'s `OrderBook` and every live `ExecutionOrchestrator` must read/write
      the identical OMS record for the same order. Done-when: a manual/integration test proves an order
      created via `_create_orchestrator_for_venue`'s `OrderAdapter` is visible to
      `_create_startup_order_recovery`'s `OrderBook.get_pending_orders()` in the same process.

### Phase D — tests (extends, does not break, the existing suite)

- [x] ✅ [BACKEND] P1. **Add `OrderAdapter`-level tests** (new module, e.g.
      `tests/unit/adapters/test_order_adapter_oms_writes.py`) covering: create-before-venue-call,
      status-update-after-venue-call for each of FILLED/REJECTED/else-SUBMITTED, cancel-only-after-confirm
      (regression-shaped, proving Phase B's fix), and fail-open-on-OMS-outage (an OMS write raising must not
      prevent the venue call). Implements design plan todo 7.
- [x] ✅ [BACKEND] P1. **Extend `tests/unit/engine/test_order_recovery.py` with one new integration test** proving
      an order written via the new `OrderAdapter` path (Phase B) is visible to `OrderBook.get_pending_orders()`
      when both share one `UnifiedOrderManager` instance — the actual end-to-end proof this whole design
      exists to produce. Implements design plan todo 7.
- [x] ✅ [BACKEND] P2. **Confirm every existing test in `tests/unit/engine/execution/test_orchestrator.py` still
      passes unchanged** with the new optional `oms`/`venue_type` params in place (they must default to
      today's in-memory-only, no-behavior-change shape) — run the full file, not a sample, and cite the pass
      count. Implements design plan todo 7's "zero breaking rewrite" requirement.

### Close-out

- [x] ✅ [BACKEND] P3. **Fix `ExecutionOrchestrator._handle_execution_error`/`_handle_order_submission_error`'s
      mislabeled venue getattr** (`engine/orchestrator.py`) — both read `getattr(instruction, "exchange",
      "unknown")` for logging/metrics labels, but `Instruction`'s real field (`engine/execution/types.py`) is
      named `venue`, not `exchange` — the fallback silently always fires, mislabeling every error-path
      metric/log as `venue="unknown"`. Found read-only during the design plan's dispatch (2026-08-21), not
      fixed there to avoid touching a file adjacent to that session's collision-avoidance scope. Done-when:
      both call sites read `instruction.venue` and an existing/new test asserts the metric label is no longer
      always `"unknown"`.
- [x] ✅ [BACKEND] P0. **Run `quality-gates.sh` (ship mode) over the full changeset** and quickmerge every commit
      — cite `execution-service@<sha>` for each landed unit, per this workspace's evidence-backed-completion
      rule.
- [ ] [AGENT] P1. **Post-implementation codex audit**: update
      `/codex/04-architecture/cross-domain-state-fabric.md`'s `OrderRecoveryEngine` note (last touched by the
      design plan's own post-design audit todo) to reflect that the persistence gap is now CLOSED, citing the
      landed shas — moving it off the "code that exists, is tested, and is wired to nothing" list entirely if
      Phase C's shared-instance wiring is confirmed live.

## Progress Log

> Append-only. Record shas, corrections, and traps here as work lands.

- **2026-08-21, design→implementation handoff**: plan authored immediately after
  `w_execution_orchestrator_oms_persistence_2026_08_20` closed all 10 of its own todos in the same session —
  every schema/hook-point/interface decision above is copied verbatim from that plan's 2026-08-21 Progress Log
  entry, not re-derived. `gate_on_depends: true` holds every todo here until that design plan's own tasks are
  `done` in the AO backlog (they are, as of this plan's authoring — the design plan closed same-session).
- **2026-08-21, Phase B lifecycle hooks shipped**: `OrderAdapter` now persists PENDING before venue submission,
  records FILLED/REJECTED/SUBMITTED after post-submit auditing, updates CANCELLED only after venue confirmation,
  and mirrors confirmed amend quantity/price; all OMS writes are loud but fail-open. Landed as
  `execution-service@4e915b637a` after full quality gates and gitleaks passed.
- **2026-08-21, final OMS implementation shipment**: persistence methods, shared process-level OMS wiring,
  adapter/recovery tests, and the venue-label correction are landed as `execution-service@f4cbd596b7`;
  `quality-gates.sh` passed with 8,896 passed, 22 skipped, 1 xpassed, and 89 warnings (coverage 82.69%),
  plus PM integration 6 passed and 2 deselected. Quickmerge ancestry was verified.
- **2026-08-21, OMS persistence and shared-live wiring shipped**: `execution-service@bc2edc16874a3b0828ef692682b69174ddcab4bf` implements the six order persistence methods, process-shared OMS selection/threading, adapter/recovery regression tests, and venue-label correction. Full `quality-gates.sh` passed (621s); quickmerge ancestry verified on `origin/live-defi-rollout`.

- **2026-08-21, implementation close-out**: `PostgreSQLOrderPersistence` order CRUD, shared startup OMS wiring, adapter lifecycle tests, shared recovery visibility, orchestrator venue-label correction, and full quality-gate verification landed in `execution-service`; the SHA is an ancestor of `origin/live-defi-rollout`.

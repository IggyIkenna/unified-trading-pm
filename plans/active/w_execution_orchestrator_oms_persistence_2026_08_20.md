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
status: active
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
last_updated: 2026-08-20
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

- [ ] [AGENT] P0. **Enumerate every real order-mutating code path in the LIVE flow** (not the disconnected
      `engine/live/` stack) that would need to write into the OMS for `OrderBook` to be genuinely populated.
      Starting inventory from this plan's own scoping (confirm, don't assume, more may exist):
      `OrderAdapterMatchingEngine.submit_order()`/`cancel_order()`/`amend_order()` (`engine/orchestrator.py`),
      `_submit_orders_with_timing()`/`_submit_single_child_order()` (child-order scheduling, same file),
      the atomic-instruction path (`v2/atomic_leg_executor.py`, `AtomicLegExecutor` — a SEPARATE order path
      from `ExecutionOrchestrator`, used by `_run_atomic_routing_loop` in `live_execution_handler.py` — confirm
      whether it needs the same treatment or is out of scope), and the manual-instruction API
      (`api/manual_instruction_api.py`) — does it route through the same `ExecutionOrchestrator` instance or
      bypass it?
- [ ] [AGENT] P0. **Decide the write contract**: does every child order get an OMS `create_order()` call at
      submission time and an `update_order_status()` on fill/cancel/reject, mirroring
      `UnifiedOrderManager.handle_nautilus_order_event()`'s existing state-machine shape? Or is a
      lighter-weight approach correct (e.g. write only on the FIRST submission + terminal state, skip
      intermediate states)? Write the decision down with reasoning — this determines every Phase 2 todo's
      shape. Explicitly resolve: should `OrderAdapter`'s existing audit-log write (`utils/audit_log.py`,
      already fires on every `ORDER_CREATED`/`ORDER_FILLED`/`ORDER_REJECTED`/`ORDER_CANCELLED`/`ORDER_AMENDED`
      event) be the trigger point for a parallel OMS write, or should the OMS write happen at a different
      layer entirely?
- [ ] [AGENT] P0. **Decide the persistence backend.** `w_state_recovery_real_wiring_2026_08_20`'s `OrderBook`
      defaults to `UnifiedOrderManager(persistence=InMemoryOrderPersistence())` when no OMS is injected —
      correct for tests, NOT restart-safe for production (an in-memory backend defeats the entire purpose of
      recovery). Real persistence adapter candidates to evaluate: `PostgreSQLOrderPersistence` (named in
      `/codex/04-architecture/cross-domain-state-fabric.md` as an existing-but-disconnected component — confirm
      it actually exists and what state it's in before assuming it's usable), a GCS-backed adapter matching
      this repo's own storage conventions (`/codex/05-infrastructure/gcs-object-operations.md`,
      `resolve_bucket_name()` — never inline `gs://`), or something else. Write the decision down; this is the
      single highest-leverage decision in this plan.
- [ ] [AGENT] P1. **Decide the hot-path latency/correctness tradeoff.** Order submission is latency-sensitive
      (real trades, real market impact from delay). Must the OMS write be synchronously awaited before the
      submission call returns (correctness-first: recovery can never miss an order that was actually placed),
      or can it be fire-and-forget / best-effort with a monitored failure path (latency-first, with a gap this
      plan must then name honestly)? Write the decision down — most likely correctness-first for `create_order`
      (must know an order was attempted before it's live) but evaluate whether fill/cancel updates can be
      lower-priority.

### Phase 2 — reconcile with existing state, don't duplicate or diverge

- [ ] [AGENT] P1. **Decide how the new durable path interacts with `ExecutionContext.submitted_orders`**
      (the existing in-memory per-instruction list `_submit_orders_with_timing` already appends to,
      `engine/orchestrator.py`) — coexist (OMS is the durable source of truth, `submitted_orders` stays as a
      fast in-memory cache for the current process's own instruction-tracking needs), or does one subsume the
      other? Confirm no existing consumer of `submitted_orders` breaks either way.
- [ ] [AGENT] P1. **Confirm this design does not collide with the `engine/live/` stack's OWN OMS usage**
      (`LiveExecutionOrchestrator`/`create_oms()` in `engine/live/factory.py`) even though that stack has zero
      production callers today — if a future dispatch ever DOES wire it up, two independent OMS-writing paths
      for the same live orders would be a real bug. Decide: should this plan's write contract live in
      `ExecutionOrchestrator` directly, or in a shared helper both stacks could eventually use?
- [ ] [AGENT] P2. **Decide the test strategy** — how does the existing test suite (which assumes the current
      architecture, e.g. `tests/unit/engine/` for `ExecutionOrchestrator`) get extended without a large-scale
      breaking rewrite? Identify which existing tests would need updating once real OMS writes land in the hot
      path, at a high level (exact file list is an implementation-phase task, not this design phase's).

### Close-out

- [ ] [AGENT] P0. **Write the final design as a single, followable spec** (this plan's own Progress Log is the
      right place) covering: the write contract, the persistence backend choice, the latency/correctness
      tradeoff, and the `submitted_orders`/`engine-live` interaction decisions — precise enough that a
      follow-up IMPLEMENTATION plan (a new, separate `assigned_vm: planning` plan, NOT this one) can be authored
      and dispatched against it without re-deriving any of these decisions.
- [ ] [AGENT] P1. **Author the follow-up implementation plan** referencing this design's decisions, and update
      `w_state_recovery_real_wiring_2026_08_20`'s own Close-out section to point at it (that plan's own
      "wire ExecutionOrchestrator" todo should redirect here once this closes, not carry duplicate detail).
- [ ] [AGENT] P2. **Post-design codex audit**: once the persistence-backend + write-contract decisions are
      final, check whether `/codex/04-architecture/cross-domain-state-fabric.md`'s own `OrderRecoveryEngine`
      note (updated 2026-08-20 by the parent plan's dispatch) needs a further update once a real
      implementation timeline exists.

## Progress Log

> Append-only. Record shas, corrections, and traps here as work lands.

- **2026-08-20, T4 sub-agent dispatch**: plan authored after the coordinator (interactive session) explicitly
  agreed this needed its own design-only plan rather than being tackled inline during
  `w_state_recovery_real_wiring_2026_08_20`'s own dispatch — "ExecutionOrchestrator's order-submission → OMS
  persistence wiring is genuinely a different risk class (live hot path, not startup-only) and deserves its
  own design pass." Scoping (exact call sites, existing audit-log/idempotency-cache non-durability, the
  disconnected `engine/live/` stack's own separate OMS usage) carried over directly from real measurements
  made during the parent plan's own dispatch the same day, not re-derived from scratch.

---
doc_type: plan
title: Execution-service state recovery — real wiring
summary: >-
  OrderRecoveryEngine (execution_service/engine/startup/order_recovery.py) is real, tested, and already
  hardened for shard-level failure isolation, but its two dependencies are explicit stubs (OrderBook: "Minimal
  in-memory order registry for testing/stub purposes"; _VenueAdapter: "Stub venue adapter... returns
  deterministic empty data") and it is never invoked at startup anywhere in the service. Wiring it in with
  default (stub) construction would emit real-looking ORDER_RECOVERY_COMPLETED events while reconciling
  nothing — the same defect class as the already-fixed AccountInstructionOrchestrator "accepted=True while
  closing nothing" bug. This plan replaces both stubs with real implementations and wires the engine into
  service startup. No owning plan existed at authoring time; spun out 2026-08-20 with direct operator
  authorization for this specific plan (mid-session), same pattern as W14/W15.
status: active
nature: design
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [execution, state-recovery, order-recovery, w-state-recovery]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/code_readiness_t4_execution_settlement_2026_08_19.md,
    /plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on:
supersedes:
superseded_by:
locked_by:
locked_since:
source: >-
  T4's own code-readiness plan (code_readiness_t4_execution_settlement_2026_08_19.md), "Build state recovery"
  todo. Scope measured 2026-08-20 across two sessions: first pass found the OrderRecoveryEngine framework
  exists (407 lines) and is already hardened (this tranche's own shard-isolation fix,
  execution-service@ff0b43b5d3) but both OrderBook and _VenueAdapter are documented stubs and the engine is
  never instantiated in production (`grep -rln "OrderRecoveryEngine("` across the whole repo excluding tests:
  zero hits). Second pass found `_VenueAdapter.fetch_open_orders()` has no real backing capability anywhere in
  the adapter layer either — `grep -n "open_orders\|fetch_open\|get_orders" trade_execution/base_adapter.py
  adapters/order_adapter.py`: zero hits. Venue sizing (real, not estimated): 8 ccxt-wrapped venues
  (`trade_execution/factory.py:CCXT_VENUES` — binance/coinbase/deribit/bybit/okx/upbit/hyperliquid/aster, each
  with its own thin adapter file under `trade_execution/adapters/*_ccxt.py`; ccxt itself has a standard
  `fetch_open_orders()` method most exchanges support, so this side is likely lower-effort than the native
  side) + native REST adapters for kraken/bitfinex/bitget (`DIRECT_REST_VENUES`, several already
  `BLOCKED-CREDENTIALS` — build the scaffold regardless per the external-data-always-available rule). TradFi
  venues are OUT of scope for now: `place_order` itself is structurally UAC-capability-blocked for every TradFi
  venue independent of this work, so there is nothing live to recover there yet. DeFi/sports are architecturally
  out of scope — they never go through `OrderRecoveryEngine`'s CLOB-shaped `OrderBook`/`ExchangeOrder` model at
  all.
context_scope:
  [
    execution-service/execution_service/engine/startup/order_recovery.py,
    execution-service/execution_service/trade_execution/adapters/,
    execution-service/execution_service/orders/,
    execution-service/execution_service/trade_execution/oms/,
    execution-service/execution_service/cli/handlers/live_execution_handler.py,
  ]
---

# Execution-service state recovery — real wiring

> A recovery engine that logs `ORDER_RECOVERY_COMPLETED` without ever actually reconciling anything is worse
> than no recovery engine — it manufactures false confidence. Epic section: `/plans/epics/system_readiness_master.md`.

## Todos

### Phase 1 — real OrderBook (backed by the persistent OMS)

- [x] ✅ [AGENT] P0. **Design the `OrderBook` -> persistent-OMS mapping.** `OrderRecoveryEngine` needs
      `get_pending_orders(venue)`, `register(order)`, `mark_rejected(order_id)`, `apply_fill(order_id, qty)`
      against `InternalOrder` (order_id/venue/instrument/side/quantity/filled_quantity/status/created_at).
      **Decision actually implemented + shipped `execution-service@458c70c48e`** (supersedes a draft-only
      decision briefly recorded 2026-08-20 20:33 by a separate concurrent AO dispatch, slot-3·planning,
      that never committed any code -- see Progress Log "concurrent-dispatch collision" entry): `OrderBook`
      is a thin async facade wrapping `orders.oms.UnifiedOrderManager` directly (not the duplicate
      `trade_execution/oms/PersistentOrderManager`) -- one source of truth, no second registry, reusing
      `UnifiedOrderManager.update_order_status()`'s own `is_legal_local_transition()` enforcement rather
      than inventing a second transition-legality check. Defaults to a fresh
      `UnifiedOrderManager(persistence=InMemoryOrderPersistence())` when no OMS is injected (mirrors
      `engine/live/factory.py`'s `create_oms()` pattern), keeping `OrderRecoveryEngine()` zero-arg
      constructible for tests/callers that don't care about book state. `register()` uses `price=Decimal("0")`
      (not the exchange snapshot's real price) -- price isn't part of what reconciliation needs
      (order_id/venue/instrument/quantity/status is); `ExchangeOrder`'s existing shape was sufficient,
      extending it was not needed. **MAJOR FINDING (confirms + goes beyond the "not a valid production
      backend" concern the superseded draft raised):** `_run_live_async`'s actual live order-submission
      path (`ExecutionOrchestrator`/`OrderAdapterMatchingEngine`, `engine/orchestrator.py`) never writes
      into ANY OMS at all, in any configuration -- confirmed via repo-wide grep, zero production callers
      of `UnifiedOrderManager.create_order`/`update_order_status` outside the entirely-disconnected
      `engine/live/` stack (`create_oms()`/`create_orchestrator()` in `engine/live/factory.py` have zero
      callers from any live entry point) and backtest actors. This is a deeper, pre-existing gap than
      "which persistence backend" -- nothing durably persists live order state today, full stop, so no
      backend choice fixes it. Rather than "fail closed" (skip emitting a completion event), the shipped
      approach: implement `OrderBook` correctly and real -- it DOES round-trip state whenever something
      writes to it (proven in `tests/unit/engine/test_order_recovery.py`) -- but do NOT wire
      `OrderRecoveryEngine.run()` into `_run_live_async`'s startup sequence at that earlier measurement.
      The later shipped wiring gates on persistent pending state, so an empty book cannot make every exchange
      order older than `MAX_ORPHAN_AGE_MINUTES` look like an orphan and get CANCELLED on every restart,
      including legitimate open orders -- actively unsafe, not merely low-value. `mark_rejected()` maps to
      OMS `REJECTED`; `apply_fill()` maps to `PARTIAL_FILLED` or `FILLED` per the resulting quantity, both
      always via `UnifiedOrderManager.update_order_status()` so its transition guard is the only
      status-validation path (never a second one).
- [x] ✅ [AGENT] P0. **Implement the real `OrderBook`** per Phase 1's decision, backed by `UnifiedOrderManager`
      (confirmed via grep, not `PersistentOrderManager` -- that class has zero production construction
      sites anywhere in the repo). Correctly translates between `InternalOrder`'s 4-state status literal
      and the OMS's own 7-state local vocabulary via a dedicated, narrow `_RECOVERY_TO_OMS_STATUS` map
      (distinct from `_LOCAL_TO_CANONICAL_STATUS`, which maps OMS-local -> UAC canonical, a different
      axis) -- transition legality itself is enforced exactly once, inside
      `UnifiedOrderManager.update_order_status()`, reused via every OrderBook call, never reinvented.
      Shipped `execution-service@458c70c48e`. Tests: `test_order_book_round_trips_real_state_via_oms`,
      `test_order_book_apply_fill_transitions_to_filled_when_complete`
      (`tests/unit/engine/test_order_recovery.py`).

### Phase 2 — real _VenueAdapter (backed by real per-venue open-orders fetching)

- [x] ✅ [AGENT] P0. **Add `fetch_open_orders()` to the ccxt-wrapped venues (8 venues).** Confirmed the
      lower-effort assumption held: added `BaseCLOBAdapter.get_open_orders()` (new concrete-with-default-raise
      method, mirrors `amend_order`'s existing pattern) plus a shared `fetch_open_orders_via_ccxt()` helper in
      `ccxt_common.py` gated on `exchange.has['fetchOpenOrders']` (per-venue support genuinely varies, checked
      not assumed), with a per-adapter override on all 8 (binance/coinbase/deribit/bybit/okx/upbit/hyperliquid/
      aster). Shipped `execution-service@e856d72999`.
- [x] ✅ [AGENT] P0. **Add `fetch_open_orders()` to the native REST adapters** (kraken/bitfinex/bitget variants
      under `DIRECT_REST_VENUES`). No ccxt shortcut here — bespoke per-exchange REST calls. Kraken Spot: real
      `get_open_orders()` via POST `/0/private/OpenOrders` (Kraken Futures raises `UnsupportedOperationError`,
      not wired -- has its own distinct order-management surface in `kraken_futures_orders.py`, out of scope
      here). Bitfinex/Bitget: scaffold-only (`NotImplementedError`), matching the exact pattern every other
      method on both adapters already uses for their `BLOCKED-CREDENTIALS` status -- per
      `/codex/02-data/external-data-always-available-rule.md`, the real code path exists, it simply cannot be
      LIVE-tested until credentials land. Shipped `execution-service@945d84d946` (was briefly blocked by an
      unrelated concurrent-session gate failure on `bridge.py`, since resolved by that session --
      `execution-service@3f54ca206f`).
- [x] ✅ [AGENT] P1. **Add `cancel_order()`/`confirm_cancel()` real backing.** Confirmed there was exactly one
      real (non-paper/sim) `cancel_order` per adapter (each `*_ccxt.py`/native-REST file's own method) --
      `_VenueAdapter.cancel_order()` calls straight through via a new `get_order_adapter_for_recovery()`
      wrapper (see Phase 2 todo 4). `confirm_cancel` had no existing confirm-style method anywhere in the
      adapter layer -- built new: one `get_order_status()` poll, checked against a cancelled-shaped status
      (no retry-until-timeout loop yet, `timeout_seconds` accepted for interface compat but unused --
      documented as a real, separate enhancement, not silently faked). **Real bug found + fixed mid-session:**
      the first cut didn't thread `instrument_id` through: a test failure showed Binance's own
      `get_order_status` hard-requires it (raises `ValueError` without it) -- not a hypothetical "some
      exchanges want a symbol" case, a guaranteed break for the first-listed CCXT venue. Fixed by threading
      `ex_order.instrument` through both calls (backward-compatible optional kwarg). Shipped
      `execution-service@458c70c48e`.
- [x] ✅ [AGENT] P0. **Implement the real `_VenueAdapter`** wrapping Phase 2's three methods per-venue via a new
      `get_order_adapter_for_recovery()` module-level wrapper in `live_execution_handler.py` (reuses
      `_create_orchestrator_for_venue`'s exact credential-resolution path via
      `_load_venue_trade_credentials` + `get_order_adapter`, not duplicated) -- lazy-imported from
      `order_recovery.py` to avoid an `engine.startup -> cli.handlers` layering inversion, matching
      `_run_live_async`'s own existing lazy-import convention for the same reason. Every method translates
      ccxt/REST-level exceptions to `ValueError` so `OrderRecoveryEngine.recover_venue`'s existing narrow
      except clause still isolates a per-venue failure. Shipped `execution-service@458c70c48e`. Tests:
      `test_venue_adapter_fetch_open_orders_calls_real_adapter_at_ccxt_boundary` (mocked ONLY at the ccxt
      exchange boundary, proving the real chain end-to-end), plus cancel/confirm/unsupported-capability/
      exception-translation tests.

### Phase 3 — wire into startup

- [x] ✅ [AGENT] P0. **Instantiate `OrderRecoveryEngine` with the REAL `OrderBook`/`_VenueAdapter`** (not defaults) —
      execution-service@279087bf2a; quality-gates.sh passed (8842 passed, 82.46% coverage).
      and call `.run(venues)` from `_run_live_async` BEFORE `_build_orchestrators_for_instructions` starts
      accepting new instructions. The venue source is the CCXT + direct-REST venue set intersected with
      `SUPPORTED_VENUES`, then narrowed to venues with persisted pending OMS orders. Startup refuses to
      construct an in-memory recovery book and returns without exchange calls when persistence is disabled,
      unavailable, or has no pending state; the empty-book orphan-cancellation hazard is fail-safe guarded.
- [x] ✅ [AGENT] P1. **Confirm the circuit-breaker gate (B2) still behaves correctly** against the real adapters —
      the stub always returned empty/success, so this path was never exercised against a real failure mode
      (timeout, auth error, rate limit). New test `test_real_venue_adapter_exception_routes_through_circuit_breaker`
      constructs `OrderRecoveryEngine` with the REAL `_VenueAdapter` (not a stub-shaped mock), makes a
      real-adapter-shaped exception fire on `get_open_orders`, and proves `cb.record_failure` is called and
      `result.error` is set -- exercised end-to-end alongside the now-shipped startup wiring;
      this proves the mechanism works correctly on the startup path. Shipped alongside
      `execution-service@458c70c48e`.
- [x] ✅ [AGENT] P1. **MEASURE, don't assume, that this doesn't collide with `OrderRecoveryEngine.recover_venue`'s
      existing shard-isolation fix** (`execution-service@ff0b43b5d3`, this tranche's own prior work same day) —
      new test `test_real_venue_adapter_shard_isolation_holds_against_real_adapter_exceptions` re-runs the
      existing regression's exact shape (one venue fails, a sibling venue must still complete cleanly) against
      the REAL `_VenueAdapter`, not the stub. Isolation holds. Shipped alongside `execution-service@458c70c48e`.

### Close-out

- [x] ✅ [AGENT] P0. **SPUN OUT (2026-08-20) — `BLOCKED-OPERATOR` (design-review gate, not credentials):**
      wire `ExecutionOrchestrator`'s order submission (`_submit_orders_with_timing`/`_submit_single_child_order`,
      `execution_service/engine/orchestrator.py`) to durably persist order state via `UnifiedOrderManager` (or
      equivalent) — the genuine, separate, cross-cutting prerequisite Phase 3 todo 1's STOP-AND-DOCUMENT
      annotation names. This is a live-hot-path change to the order SUBMISSION flow (every real trade), a
      categorically different risk class from the STARTUP-only recovery code this dispatch built and tested —
      deliberately NOT attempted inline here, even after an explicit "continue at your own pace" go-ahead from
      the coordinator, per this workspace's own AO-eligibility rule ("never an open-ended judgment/design call
      inline — resolve that first as its own plan"). Coordinator agreed: spun out into its own design-only plan,
      `/plans/archive/2026_08/w_execution_orchestrator_oms_persistence_2026_08_20.md` (+ mandatory finalize companion) —
      this todo is CLOSED here, tracked THERE. Verify Phase 3 todo 1 (below) by re-running it once that plan's
      own follow-up IMPLEMENTATION plan lands.
      **Update (2026-08-21):** that design plan closed all 10 of its own todos same-session (write contract,
      persistence backend `PostgreSQLOrderPersistence`, latency tradeoff, `submitted_orders`/`engine-live`
      interaction all decided — see its 2026-08-21 Progress Log entry) and authored the follow-up
      IMPLEMENTATION plan named above:
      `/plans/archive/2026_08/w_execution_orchestrator_oms_persistence_impl_2026_08_21.md` (+ finalize companion). Once
      that implementation plan lands and threads one shared `UnifiedOrderManager` instance from startup into
      both `OrderRecoveryEngine`'s `OrderBook` and `ExecutionOrchestrator`, re-run Phase 3 todo 1 (below) —
      the empty-`OrderBook` hazard it names will finally be closed.
- [ ] [AGENT] P0. **`BLOCKED-CREDENTIALS` (the remaining gate): run real recovery against every wired venue and
      record the actual result** — this is the first genuine evidence the mechanism works, not a smoke test.
      **`BLOCKED-OPERATOR` half CLEARED 2026-08-22**, verified live-in-code by this finalize's review, not
      trusted from the implementation plan's own "done" claim:
      `w_execution_orchestrator_oms_persistence_impl_2026_08_21` landed and `execution-service`'s
      `_run_live_async` (`cli/handlers/live_execution_handler.py`) now builds ONE `UnifiedOrderManager`
      instance per process (`self._oms`, built in `_create_process_oms`) and threads that SAME instance into
      both `_create_startup_order_recovery`'s `OrderBook(oms=oms)` and every venue's `OrderAdapter` via
      `_create_orchestrator_for_venue`'s `shared_oms = oms or self._oms` → `OrderAdapter(venue_client=...,
      oms=shared_oms)`. `OrderBook` is therefore no longer structurally guaranteed empty at restart — a real
      order submitted through `OrderAdapter.submit_order()` now persists via `oms.create_order()` before the
      venue call, so a real recovery run would find genuine pending orders instead of proving nothing.
      Remaining: **`BLOCKED-CREDENTIALS`** — genuinely making LIVE API calls against real exchanges (even
      read-only `fetch_open_orders`) requires real operator-provided credentials and explicit authorization to
      hit production venue APIs from an ad-hoc session — not something a dispatched sub-agent should
      self-authorize regardless of credential availability. Both this dispatch's and the implementation plan's
      own tests already prove the real code paths correctly (mocked at the ccxt/HTTP/Postgres-driver boundary,
      never re-implementing the call itself) — that is the honest ceiling of what a session without live venue
      credentials can verify. Stays open, single-gate now, until an operator supplies credentials + explicit
      authorization to run a live recovery pass.
- [x] ✅ [AGENT] P1. **Post-phase codex audit**: check `/codex/04-architecture/` for any doc describing state
      recovery as already guaranteed (the original T4 todo cited "the artefacts describe this as guaranteed") —
      correct any that were wrong, now that it genuinely is (or precisely isn't, per what actually ships).
      Found + corrected one real hit: `/codex/04-architecture/cross-domain-state-fabric.md` listed
      `OrderRecoveryEngine` (dated to THIS SAME DAY, 2026-08-20) as one of four "code that exists, is tested,
      and is wired to nothing" mirror-failure instances. Updated with a dated note: its own stub-dependency
      problem is now fixed (real `OrderBook`/`_VenueAdapter`, this plan's Phase 1+2), it is still not wired
      into any live entry point, but the reason changed from "fake dependencies would make wiring a
      false-success trap" to a real, tracked prerequisite gap one level up the stack (the same doc's own
      `PostgreSQLOrderPersistence`-shaped pattern). The other three components that doc lists
      (`TransferCoordinator`, `HealthFactorMonitor`, `PostgreSQLOrderPersistence`) were outside this plan's
      scope and were not re-measured. Shipped `unified-trading-pm@e9832cbd49`.
- [x] ✅ [AGENT] P2. **Triage phase**: any todo above that couldn't close (credential gap, a real design question
      this plan's own text didn't resolve) gets a dated annotation with the specific reason, never left silently
      unattempted. Summary of what stays open and why, all annotated in place above: Phase 2 todo 2's
      Bitfinex/Bitget legs (credential gap, scaffold-only per existing convention); the new
      ExecutionOrchestrator Close-out todo (scope/design-review boundary, recommend its own plan); the
      "run real recovery" Close-out todo (blocked on the genuine credential/authorization gap this session
      Nothing above is silently unattempted — every open item has a same-day, specific, dated reason.

## Progress Log

> Append-only. Record shas, corrections, and traps here as work lands.

- **2026-08-20, T4 (interactive session, `/autonomous`)**: plan authored after the operator directly authorized
  spinning state-recovery out as a dedicated AO plan AND immediately dispatching a sub-agent against it rather
  than waiting for normal fleet pickup (AskUserQuestion mid-session: "Build it into an agent orchestrator plan,
  but then also execute it with a sub-agent... I want to get it done now"). Scoping measurements (zero
  `OrderRecoveryEngine(` production instantiation sites, zero `fetch_open_orders`-shaped capability anywhere in
  the adapter layer, real 8-ccxt + native-REST venue counts) done via real grep across two sessions, not
  estimated.
- **2026-08-20, slot-3 resumed design task**: measured the actual live path. `_run_live_async` loads
  instructions and builds venue orchestrators directly; it does not construct an OMS or invoke recovery.
  `engine/live/factory.py:create_oms()` returns `orders.oms.UnifiedOrderManager` over
  `InMemoryOrderPersistence`, whose `initialize()` clears state. Decision recorded above: implement
  `OrderBook` as an adapter over that concrete OMS API, but do not call it production-ready until a
  restart-safe persistence adapter is selected and the same OMS instance is threaded through startup.
  Recovery identity must distinguish exchange `venue_order_id` from OMS `operation_id`; `ExchangeOrder`
  currently lacks price needed for re-registration, so Phase 1 implementation must extend that contract.
- **2026-08-20, T4 sub-agent dispatch (interactive-session-direct, NOT the AO backlog pickup below) —
  Phase 1 + Phase 2 shipped real; Phase 3 wiring deliberately left open**:

  **Concurrent-dispatch collision (flag for operator awareness):** this plan's own frontmatter
  (`assigned_vm: planning`, `execution_scope: orchestrator-agent`) makes it AO-backlog-eligible, and per
  this plan's own authoring note above ("operator directly authorized spinning state-recovery out as a
  dedicated AO plan AND immediately dispatching a sub-agent... I want to get it done now"), it was
  double-dispatched: this interactive-session sub-agent, AND independently, an AO worker
  (`slot-3·planning`) that picked the same plan up from the backlog. Commit `940c6a27de`
  (`docs(plans): record persistent OMS OrderBook mapping`, authored `ikennaigboaka [slot-3·planning]`,
  2026-08-20 20:33) landed on `live-defi-rollout` mid-way through THIS dispatch's own work, checking off
  Phase 1 todo 1 with a DIFFERENT decision than what this dispatch was already implementing (their draft:
  "fail closed" against the in-memory default + extend `ExchangeOrder` with the exchange snapshot's price
  before implementing `register()`). Verified via `git log -- <file>` in execution-service that slot-3
  never committed any CODE under that decision (only the plan-doc text commit exists) — no actual
  code-level collision occurred. This dispatch's own implementation (real, tested, shipped
  `execution-service@458c70c48e`/`e856d72999`) is what the plan doc's checkboxes now reflect; slot-3's
  draft decision is superseded, not merged (see the Phase 1 todo 1 checkbox text for the reconciliation).
  Operator: if `slot-3·planning`'s AO worker is still active on this plan, it should be told the plan's
  Phase 1/2 todos are now closed against real, shipped code — re-verify before it attempts to independently
  implement its own (different, unshipped) design.

  **Shipped**: `execution-service@458c70c48e` (Phase 1 OrderBook + Phase 2 `BaseCLOBAdapter.get_open_orders`
  interface + `_VenueAdapter` real cancel_order/confirm_cancel + `get_order_adapter_for_recovery` credential
  wrapper + Phase 3 todos 2-3's circuit-breaker/shard-isolation tests, all in one commit since they share
  `execution_service/engine/startup/order_recovery.py`), `execution-service@e856d72999` (Phase 2 todo 1, all
  8 ccxt-wrapped venues' `get_open_orders`). Native-REST adapters (kraken/bitfinex/bitget, Phase 2 todo 2)
  are code-complete + gate-clean locally but not yet shipped as of this entry — see that todo's own status
  note for why (unrelated concurrent-session gate failure on `bridge.py`, since resolved by that other
  session; will ship in the next `execution-service@<sha>` and this Progress Log / that checkbox will be
  updated then).

  **Genuinely NOT closed, on purpose**: Phase 3 todo 1 (wire `.run(venues)` into `_run_live_async`) — see
  its own STOP-AND-DOCUMENT annotation. This is the single most important finding of this whole dispatch:
  wiring recovery into startup TODAY, even with 100% real Phase 1+2 code, would be actively unsafe (cancels
  legitimate open orders on every restart) because of a pre-existing, deeper gap this plan's own scope
  never named — nothing in the live order-submission path durably persists order state at all. A new P0
  Close-out todo tracks that prerequisite. Close-out todos "run real recovery" and "post-phase codex audit"
  also stay open, gated on the same prerequisite / on the native-REST commit landing.

- **2026-08-20, T4 sub-agent dispatch — final commit tally + wrap-up**: all 4 planned quickmerge commits
  landed on `live-defi-rollout`: `execution-service@458c70c48e` (Phase 1 core + Phase 2 `_VenueAdapter`
  cancel/confirm + Phase 3 todos 2-3 tests), `execution-service@e856d72999` (Phase 2, 8 ccxt venues),
  `execution-service@945d84d946` (Phase 2, native REST -- kraken real, bitfinex/bitget scaffold),
  `execution-service@32ad0cfa4a` (test-file updates for the async `OrderBook` interface + new
  round-trip/ccxt-boundary/circuit-breaker/shard-isolation verification tests). Plan doc itself shipped
  `unified-trading-pm@fa286a594c`. Phase 1 + Phase 2 (all 6 todos) now closed against real, gate-passing,
  merged code. Phase 3 todo 1 and the new Close-out prerequisite todo remain genuinely open per their own
  STOP-AND-DOCUMENT annotations -- not oversights.

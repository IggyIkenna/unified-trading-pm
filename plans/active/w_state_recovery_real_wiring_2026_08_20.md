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

- [ ] [AGENT] P0. **Design the `OrderBook` -> persistent-OMS mapping.** `OrderRecoveryEngine` needs
      `get_pending_orders(venue)`, `register(order)`, `mark_rejected(order_id)`, `apply_fill(order_id, qty)`
      against `InternalOrder` (order_id/venue/instrument/side/quantity/filled_quantity/status/created_at).
      `orders/oms.py`'s `UnifiedOrderManager` (this tranche's own transition-validation fix landed
      `execution-service@69a9a088be` the same day) already has an analogous shape (`get_order`,
      `update_order_status`, `count_open_orders`) but a different field/method surface — decide whether
      `OrderBook` becomes a thin adapter WRAPPING `UnifiedOrderManager` (preferred — one source of truth for
      order state, no second persistence path) or needs its own storage. Write the decision down.
- [ ] [AGENT] P0. **Implement the real `OrderBook`** per Phase 1's decision, backed by `UnifiedOrderManager` (or
      `PersistentOrderManager`, whichever this repo's live-mode wiring actually uses — confirm via
      `_run_live_async`'s construction, don't assume). Must correctly translate between `InternalOrder`'s status
      literal (`PENDING`/`PARTIALLY_FILLED`/`EXCHANGE_REJECTED`/`CANCELLED`) and the OMS's own 7-state local
      vocabulary — reuse the `is_legal_local_transition`/`_LOCAL_TO_CANONICAL_STATUS` mapping this session's own
      OMS fix added rather than inventing a second translation.

### Phase 2 — real _VenueAdapter (backed by real per-venue open-orders fetching)

- [ ] [AGENT] P0. **Add `fetch_open_orders()` to the ccxt-wrapped venues (8 venues).** ccxt itself exposes a
      standard `fetch_open_orders(symbol=None)` across most exchanges — confirm per-venue support (some
      exchanges' ccxt implementations don't support the unified method; check `exchange.has['fetchOpenOrders']`
      before assuming) and add a thin wrapper per `trade_execution/adapters/*_ccxt.py` file, or one shared
      method on their common base if they share one. This is the lower-effort half — verify that assumption
      holds before treating Phase 3 (native) as equally cheap.
- [ ] [AGENT] P0. **Add `fetch_open_orders()` to the native REST adapters** (kraken/bitfinex/bitget variants
      under `DIRECT_REST_VENUES`). No ccxt shortcut here — bespoke per-exchange REST calls. Several of these
      venues are `BLOCKED-CREDENTIALS` already (kraken pending operator approval; bitfinex/bitget no live keys)
      — build the real code path regardless (per `/codex/02-data/external-data-always-available-rule.md`), it
      simply cannot be LIVE-tested until credentials land; status those specific venues `BLOCKED-CREDENTIALS`
      honestly rather than skipping the scaffold.
- [ ] [AGENT] P1. **Add `cancel_order()`/`confirm_cancel()` real backing.** `BaseCLOBAdapter` already has a real
      `cancel_order` method (`base_adapter.py:123` / `:301` — confirm which is the live one vs a paper/sim
      variant) — the stub `_VenueAdapter.cancel_order()` just needs to call through to it via
      `get_order_adapter(venue)`, not reinvent cancellation. `confirm_cancel` (poll/verify the cancel landed) is
      the piece most likely to need new code — check whether any existing adapter already has a
      confirm-style method before building one from scratch.
- [ ] [AGENT] P0. **Implement the real `_VenueAdapter`** wrapping Phase 2's three methods per-venue via
      `get_order_adapter(venue)` (the same factory `_create_orchestrator_for_venue` already uses — reuse its
      credential-resolution path, don't duplicate it).

### Phase 3 — wire into startup

- [ ] [AGENT] P0. **Instantiate `OrderRecoveryEngine` with the REAL `OrderBook`/`_VenueAdapter`** (not defaults)
      and call `.run(venues)` from `_run_live_async` BEFORE `_build_orchestrators_for_instructions` starts
      accepting new instructions — recovery must complete (or at minimum start) before new order flow begins.
      Decide the venue list source: likely `SUPPORTED_VENUES` filtered to CLOB-capable ones, or whichever
      venues have persisted open orders in the OMS at startup — write the decision down, this determines
      whether recovery runs eagerly for every configured venue or lazily only for ones with real open state.
- [ ] [AGENT] P1. **Confirm the circuit-breaker gate (B2) still behaves correctly** against the real adapters —
      the stub always returned empty/success, so this path was never exercised against a real failure mode
      (timeout, auth error, rate limit). Add a test that a real adapter exception during recovery correctly
      routes through the circuit breaker rather than crashing startup.
- [ ] [AGENT] P1. **MEASURE, don't assume, that this doesn't collide with `OrderRecoveryEngine.recover_venue`'s
      existing shard-isolation fix** (`execution-service@ff0b43b5d3`, this tranche's own prior work same day) —
      run the existing regression test proving one venue's failure doesn't abort the others, against the NOW-REAL
      adapters, not just the stub.

### Close-out

- [ ] [AGENT] P0. **Run real recovery against every wired venue and record the actual result** — this is the
      first genuine evidence the mechanism works, not a smoke test. For any venue where real testing isn't
      possible (BLOCKED-CREDENTIALS), record that honestly rather than claiming coverage.
- [ ] [AGENT] P1. **Post-phase codex audit**: check `/codex/04-architecture/` for any doc describing state
      recovery as already guaranteed (the original T4 todo cited "the artefacts describe this as guaranteed") —
      correct any that were wrong, now that it genuinely is (or precisely isn't, per what actually ships).
- [ ] [AGENT] P2. **Triage phase**: any todo above that couldn't close (credential gap, a real design question
      this plan's own text didn't resolve) gets a dated annotation with the specific reason, never left silently
      unattempted.

## Progress Log

> Append-only. Record shas, corrections, and traps here as work lands.

- **2026-08-20, T4 (interactive session, `/autonomous`)**: plan authored after the operator directly authorized
  spinning state-recovery out as a dedicated AO plan AND immediately dispatching a sub-agent against it rather
  than waiting for normal fleet pickup (AskUserQuestion mid-session: "Build it into an agent orchestrator plan,
  but then also execute it with a sub-agent... I want to get it done now"). Scoping measurements (zero
  `OrderRecoveryEngine(` production instantiation sites, zero `fetch_open_orders`-shaped capability anywhere in
  the adapter layer, real 8-ccxt + native-REST venue counts) done via real grep across two sessions, not
  estimated.

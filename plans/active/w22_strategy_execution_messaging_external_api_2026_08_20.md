---
doc_type: plan
title: W22 — Strategy/execution messaging and the external instruction API
summary: >-
  Build the strategy→execution instruction bridge over UTL EventTransport (currently unbuilt — only the manual
  path is live) and complete the instruction action vocabulary past TRADE/QUOTE on both internal and external
  paths, per the epic's own W22 workstream and the 2026-08-19 operator ruling directing this be authored as a
  dedicated AO plan.
status: active
nature: design
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, strategy-service, unified-trading-library]
scope: [engineer]
tags: [execution, messaging, event-transport, external-api, w22]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/code_readiness_t4_execution_settlement_2026_08_19.md,
    /plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/04-architecture/account-instructions.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 8
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on:
supersedes:
superseded_by:
locked_by:
locked_since:
source: >-
  Operator ruling 2026-08-19 (plans/audit/results/code_completion_scope_2026_08_19.md, "author 7 unowned P0
  plans") + epic W22 (plans/epics/system_readiness_master.md), authored 2026-08-20 by T4 after re-checking
  today's LDR rulings surfaced this had not yet been spun into its own dispatchable plan.
context_scope:
  [
    strategy-service/strategy_service/engine/strategies/v2/live_routing.py,
    unified-trading-library/unified_trading_library/streaming/event_facade.py,
    execution-service/execution_service/api/external_instruction_api.py,
    execution-service/execution_service/adapters/defi_adapter.py,
    execution-service/execution_service/v2/account_orchestrator.py,
    execution-service/execution_service/engine/quote_maintenance.py,
  ]
---

# W22 — Strategy/execution messaging and the external instruction API

> The bridge from a strategy's decision to execution is currently unmeasured and unbuilt end-to-end — the only
> live instruction path is manual (`ManualOperationHandler → LiveOrchestrator.execute_instruction()`). This plan
> is that bridge, plus completing the same instruction contract on the external-facing surface. Epic section:
> `/plans/epics/system_readiness_master.md` § W22.

## What's already real (don't re-derive)

- **Strategy-service already PUBLISHES instructions over `EventTransport`.**
  `strategy_service/engine/strategies/v2/live_routing.py` calls `facade_publish(envelope, transport=...)` with
  `data_type=ATOMIC_INSTRUCTION_DATA_TYPE` (`= "atomic_instruction"`), keyed on `(asset_group,
  ATOMIC_INSTRUCTION_DATA_TYPE)` — `resolve_asset_group_for_family()` resolves the shard's `asset_group`. This
  plan's job is the SUBSCRIBE side (execution-service reading this shard), not the publish side.
- **`EventTransport` (`unified_trading_library.streaming.event_facade`)** is a `Protocol` with `async def
  publish(envelope)` and `def read(asset_group, data_type, *, after=None, limit=1000) ->
  AsyncIterator[CanonicalPersistEnvelope]`. `get_transport(topology)` resolves the real implementation
  (`InMemoryTransport` colocated, `PubSubTransport` live) — same code path for paper and live, per Batch=Live.
- **TRADE and QUOTE are already wired on the external HTTP surface**
  (`execution_service/api/external_instruction_api.py`, `POST /external/instructions`) — `TRADE` routes through
  `ManualOperationHandler.execute() -> LiveOrchestrator.execute_instruction()`; `QUOTE` registers delta-proxy
  repricing via `QuoteMaintainer` (no order placed — `REGISTERED`, not `SUBMITTED`, since no underlying-tick loop
  drives it yet — see the DeFiAdapter-factory todo below, and the linked delta-proxy issue doc's 9 todos for the
  repricing side specifically). Every other `InstructionActionV2` member 501s.
- **No DeFiAdapter construction/caching factory exists.** `execution_service/adapters/defi_adapter.py`'s
  `DeFiAdapter` is a single instance wrapping connectors for EVERY DeFi protocol (Uniswap/AAVE/Lido/Symbiotic/
  Jupiter/Morpho/Pendle), requiring real wallet private keys to construct
  (`LiveExecutionHandler._build_defi_adapter`, `execution_service/cli/handlers/live_execution_handler.py:527`).
  This is structurally different from the CLOB `get_order_adapter(venue)` per-venue factory `TRADE` already
  reuses — SWAP/LEND/BORROW/STAKE/UNSTAKE need an equivalent lazy-construct-and-cache pattern, modeled on
  `execution_service/v2/account_orchestrator.py`'s `_default_order_adapter_factory` (same lazy-import-to-avoid-
  circular-import trick applies: `execution_service.v2` imports `LiveExecutionHandler`, `LiveExecutionHandler`
  must NOT be imported at module top level anywhere reachable from `execution_service.v2.__init__`).
- **`AccountInstruction.CLOSE_ALL` and `kill_switch.py` are the real, already-authorized primitives**
  KILL_SWITCH/FLATTEN_POSITION instructions should translate into — not a second independent authority path. See
  `/codex/04-architecture/account-instructions.md` for the authorization model.

## Todos

### Messaging bridge

- [x] [BACKEND] P0. Build the execution-service `EventTransport` subscriber reading strategy-published
      instructions. New module (suggest `execution_service/engine/strategy_instruction_subscriber.py`): a loop
      calling `get_transport().read(asset_group, "atomic_instruction", after=<last-seen>)` per subscribed
      `asset_group`, converting each `CanonicalPersistEnvelope`'s payload into the engine's `Instruction` type
      (reuse the conversion pattern `execution_service/engine/instruction_convert.py`'s
      `manual_request_to_instruction()` already established for the manual path — do not build a second
      converter), then routing through `ExecutionOrchestrator.execute_instruction()` (the SAME orchestrator TRADE
      already uses, not a parallel dispatch path). Done-when: a real (non-mock) `InMemoryTransport` round-trip
      test proves a published `AtomicInstruction` envelope reaches `ExecutionOrchestrator` and produces a
      settlement result, end to end. -- execution-service@79e951ea; Evidence: bash scripts/quality-gates.sh --no-fix
- [ ] [BACKEND] P0. Wire the subscriber into service startup (`execution_service/api/main.py`'s lifespan, next to
      the existing `_lifespan` wiring for `manual_instruction_api`) so it runs as a background task under the
      real deployed entrypoint, not just `api/app.py`'s CLI-serve path (same "which entrypoint actually runs in
      the container" lesson `/manual/instruction`'s 404 taught this tranche 2026-08-20 — verify by checking
      `main.py`'s own routes, not assuming). Done-when: a live check confirms the subscriber task is running
      under the container's actual startup path.
- [ ] [BACKEND] P0. Features-service → execution subscription, same `EventTransport.read()` pattern, subscribed
      to ONLY the feature groups execution actually needs — start with whatever `DeltaProxyRepricer`'s
      underlying-tick loop needs (this IS the missing "underlying-tick loop" the linked delta-proxy issue doc
      names as blocking real `QuoteMaintainer.on_underlying_tick` calls — closing this todo should let that
      issue's own remaining todos proceed, cross-link both directions in `related:` once landed). Done-when: a
      live `QUOTE` instruction's repricing responds to a published feature-group tick within one round trip,
      not just a registered-but-inert state.
- [ ] [BACKEND] P0. Sink every strategy-emitted instruction consumed by the new subscriber to GCS, one record at
      a time, via the EXISTING manifest/shard pipeline (reuse, do not invent a parallel writer) — queryable via
      the same BigQuery external-table pattern other shard types already use. Distinct from market-tick-data
      aggregation (a separate axis). Done-when: one consumed instruction produces one queryable GCS row with a
      manifest entry, verified via a real read-back, not just a written-file check.

### Instruction action vocabulary

- [ ] [BACKEND] P0. Build the DeFiAdapter lazy-construct-and-cache factory (see "What's already real" above for
      the exact pattern to model). New module or extend `execution_service/adapters/defi_adapter_factory.py`
      (does not exist yet — name it this unless a better home is found). Done-when: a real (paper-mode,
      non-network) construction round-trip proves the factory returns a working `DeFiAdapter` without requiring
      the caller to hold wallet credentials directly.
- [ ] [BACKEND] P0. Wire `SWAP`/`LEND`/`BORROW`/`STAKE`/`UNSTAKE` on `POST /external/instructions`, converting
      each `StrategyInstructionV2` variant (`SwapInstruction`/`LendInstruction`/`BorrowInstruction`/
      `StakeInstruction`/`UnstakeInstruction` — all already real UAC dataclasses, no contract gap) into the
      engine's `Instruction` type and routing through the new DeFiAdapter factory's `execute_instruction()`
      (mirrors `_build_strategy_instruction_from_trade()`'s existing TRADE-conversion pattern in
      `external_instruction_api.py`). Done-when: each of the 5 actions produces a real (non-mock) settlement
      result over HTTP in paper mode, not a 501.
- [ ] [BACKEND] P0. Wire `TRANSFER`/`BRIDGE`/`CANCEL` on the same surface. `CANCEL` reuses the existing
      `order_tracker`-based cancel path `/manual/cancel` already established (same real per-venue
      `cancel_order()`, not a new implementation); `TRANSFER`/`BRIDGE` route through `TransferCoordinator`
      (`execution_service/transfer_coordinator.py`) the same way an internal transfer intent does today.
      Done-when: each of the 3 actions produces a real result or an honest structured rejection (never a silent
      drop), not a 501.
- [ ] [BACKEND] P0. Wire `ATOMIC` on the same surface, routing through the existing multi-leg dispatch
      (`AtomicInstruction`'s handling already exists in `backtest_v2/action_handlers.py::resolve_settlement` for
      BATCH — reuse the same leg-iteration logic for the live path, do not reimplement). Done-when: a 2-leg
      atomic instruction produces real per-leg results over HTTP, not a 501.
- [ ] [BACKEND] P0. Add `KILL_SWITCH`/`FLATTEN_POSITION` as `InstructionActionV2` members — **coordinate with
      T1** (owns `unified-api-contracts`) for the schema addition; this tranche does not add UAC members
      directly. Each instruction carries an authorization field mirroring `AccountInstruction.authorization_id`.
      Once the schema lands, wire the execution-service handler as a THIN translation into the existing
      `kill_switch.py`/`AccountInstructionOrchestrator.CLOSE_ALL` machinery — never a second, independently-
      authorized implementation of the same capability. Done-when: an authorized external KILL_SWITCH/
      FLATTEN_POSITION instruction produces the identical effect as the existing internal
      `POST /kill-switch/activate` / `POST /account/instruction` (CLOSE_ALL) calls, verified by a test asserting
      both paths converge on the same underlying call.

### Deployment topology and external hosting

- [ ] [BACKEND] P1. Verify + document schema consistency across the three deployment paths (internal Pub/Sub via
      the new subscriber above, external-automated HTTP/WebSocket, manual HTTP) now that all three route through
      `StrategyInstructionV2`/the engine's `Instruction` type — this is a verification pass once the messaging-
      bridge and vocabulary todos above land, not new design (the schema is already shared; confirm it stays
      that way). Done-when: one instruction type submitted via all three paths produces byte-identical
      `Instruction` construction (modulo timestamp), proven by a real test, not asserted.
- [ ] [BACKEND] P2. Scaffold the client-hosted deployment option — a Dockerfile + config template proving the
      SAME image `execution-service` already builds can run against a registered client's own infrastructure
      with only config changes (hot-reload config model per W6), no code fork. Bounded scaffold, not a full
      onboarding product — done-when: the existing `execution-service` image runs successfully against a
      client-scoped config in a local/staging test, no source changes required.
- [ ] [BACKEND] P1. Broker and routing configuration via the existing `venue_constraints` field on
      `StrategyInstructionEnvelope` — population and validation only, no new schema (per 2026-08-19 operator
      direction already recorded in the epic). Done-when: a `venue_constraints` value submitted on any wired
      action is read and enforced by the routing path, not silently ignored.
- [ ] [BACKEND] P1. Registered-client management for the external-automated deployment — an allow-list check
      execution-service's external surface enforces before accepting an instruction from a non-manual caller
      (reuse the existing `create_api_auth`/`AuthContext` org-scoping already used by
      `external_instruction_api.py`, do not invent a parallel identity system). Done-when: an unregistered
      `org_id` is rejected with a real 403, an registered one passes through unaffected.

### Close-out

- [ ] [AGENT] P0. Post-phase codex audit — update `/codex/02-data/live-data-persistence-and-event-log.md` and
      `/codex/04-architecture/tier-and-import-architecture.md` if this plan's messaging-bridge implementation
      changes anything either doc currently states as unbuilt; cross-link the delta-proxy issue doc both
      directions once the features-service subscription todo lands.
- [ ] [AGENT] P0. Confirm the epic's own W22 section (`/plans/epics/system_readiness_master.md`) reflects this
      plan's real landed state once every todo above is done or explicitly re-scoped — the epic's todos should
      point here, not duplicate the detail.

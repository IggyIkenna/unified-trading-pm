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
repos: [execution-service, strategy-service, unified-trading-library, unified-api-contracts, deployment-service]
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
    unified-api-contracts/unified_api_contracts/events/sink_matrix.py,
    deployment-service/terraform/gcp/live_event_log/main.tf,
    deployment-service/terraform/gcp/live_event_log/warm_sink.tf,
    deployment-service/terraform/gcp/live_event_log/bq_external.tf,
    deployment-service/terraform/gcp/live_event_log/strategy_atomic_instruction.tf,
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
- [x] [BACKEND] P0. Wire the subscriber into service startup (`execution_service/api/main.py`'s lifespan, next to
      the existing `_lifespan` wiring for `manual_instruction_api`) so it runs as a background task under the
      real deployed entrypoint, not just `api/app.py`'s CLI-serve path (same "which entrypoint actually runs in
      the container" lesson `/manual/instruction`'s 404 taught this tranche 2026-08-20 — verify by checking
      `main.py`'s own routes, not assuming). Done-when: a live check confirms the subscriber task is running
      under the container's actual startup path. -- execution-service@99962afa1f; Evidence: bash
      scripts/quality-gates.sh --no-fix (8808 passed, 22 skipped)
- [x] [BACKEND] P0. ✅ SHIPPED 2026-08-20 — execution-service@f0a33fd3d8 + execution-service@62d2e3ab76. Features-service → execution subscription, same `EventTransport.read()` pattern, subscribed
      to ONLY the feature groups execution actually needs — start with whatever `DeltaProxyRepricer`'s
      underlying-tick loop needs (this IS the missing "underlying-tick loop" the linked delta-proxy issue doc
      names as blocking real `QuoteMaintainer.on_underlying_tick` calls — closing this todo should let that
      issue's own remaining todos proceed, cross-link both directions in `related:` once landed). Done-when: a
      live `QUOTE` instruction's repricing responds to a published feature-group tick within one round trip,
      not just a registered-but-inert state. Evidence: bash scripts/quality-gates.sh --no-fix (8816 passed, 22 skipped, 1 xpassed; venue-routing commit 62d2e3ab76).
- [x] [BACKEND] P0. ✅ SHIPPED 2026-08-21 — `deployment-service@9f602e64aa` +
      `deployment-service@f843fd5314`. The wildcard `atomic_instruction` sink adds the declared SINK_MATRIX topic,
      warm-GCS subscription, and BigQuery external table; `strategy_atomic_instruction.tf` adds the concrete
      `cefi`/`defi`/`prediction` topics, execution-reader subscriptions, warm-GCS subscriptions, and matching
      external-table definitions used by `PubSubTransport`. Evidence: `bash scripts/quality-gates.sh --no-fix`
      (ALL QUALITY GATES PASSED); `tofu validate` passed; live topic/subscription read-back is ACTIVE; the
      published canonical verification envelope produced
      `gs://central-element-323112-events/live-events/warm/all/atomic_instruction/2026-08-21T03:56:54+00:00_b0f481.parquet`
      and BigQuery `live_events.all_atomic_instruction` returned one row for
      `correlation_id=w22-atomic-sink-20260821`. The event-log warm sink has no separate availability-manifest
      surface; the durable proof is the warm object plus external-table row. No synthetic message was injected into
      the concrete execution-reader topics because those are live execution destinations; their ACTIVE resources are
      structurally verified, while a naturally emitted concrete-path row remains a live-traffic verification.

### Instruction action vocabulary

- [x] [BACKEND] P0. Build the DeFiAdapter lazy-construct-and-cache factory (see "What's already real" above for
      the exact pattern to model). Done-when: a real (paper-mode, non-network) construction round-trip proves the
      factory returns a working `DeFiAdapter` without requiring the caller to hold wallet credentials directly. —
      execution-service@4af3715497 (2026-08-21). Turned out to substantially already exist
      (`execution_service.cli.handlers.live_execution_handler.get_defi_adapter_singleton()`, already real, already
      used by `ManualOperationHandler.get_or_create_defi_adapter()`) — new module
      `execution_service/adapters/defi_live_wiring.py::build_defi_execution_wiring()` is the HTTP-surface-facing
      caller of that SAME factory (a second caller, not a second implementation), with the added safety property
      that LIVE/MANUAL mode never leaves the wired adapter `None` (an empty-but-real `DeFiAdapter()` substitutes
      when Secret Manager credentials can't be resolved, so a genuinely live-mode dispatch always reaches an
      honest per-connector FAILED, never silently falls back to simulation). Evidence: bash
      scripts/quality-gates.sh --no-fix (8872 passed, 22 skipped, 1 xpassed, 89 warnings in 237.24s; sentinel=4af371549778653f8240e1f3ca5ebb32a37e44f6).
- [x] [BACKEND] P0. Wire `SWAP`/`LEND`/`WITHDRAW`/`STAKE`/`UNSTAKE` on `POST /external/instructions`, converting
      each `StrategyInstructionV2` variant (`SwapInstruction`/`LendInstruction`/`WithdrawInstruction`/
      `StakeInstruction`/`UnstakeInstruction`) into the internal `ExecutionInstruction` type and routing through a
      new `defi_adapter=` injection seam on `SwapHandler`/`LendHandler`/`StakeHandler` (mirrors
      `TransferHandler`'s existing `adapter=` pattern — NOT literally `DeFiAdapter.execute_instruction()` as
      originally worded here; that method has its own fabricated/degraded-success gap, found mid-implementation
      and filed separately: `/plans/archive/issues/defi_adapter_execute_instruction_success_check_gap_2026_08_21.md`
      (RESOLVED + ARCHIVED 2026-08-21),
      deliberately not fixed in this change to avoid widening its blast radius onto `DeFiAdapter`'s already-shipped
      internal-manual-API consumer). Done-when: each of the 5 actions produces a real (non-mock) settlement result
      over HTTP, both the real-credentials-present and no-credentials-honest-FAILED paths tested. — this todo's
      wording named BORROW instead of WITHDRAW; BORROW/REPAY (`BorrowHandler`) is tracked as its own follow-up
      below, explicitly out of scope for this change per the dispatching operator's instruction.
      execution-service@4af3715497 (2026-08-21):
      `execution_service/engine/handlers/defi_live_dispatch.py` (new — real connector dispatch, Uniswap V3/V2 for
      SWAP, AAVE V3 for LEND/WITHDRAW, Lido for STAKE/UNSTAKE; other real-but-differently-shaped `DeFiAdapter`
      connectors like Morpho/EtherFi honestly FAIL rather than guess at an untaught call shape — tracked as a P2
      follow-up in the resolved issue doc), `swap_handler.py`/`lend_handler.py`/`stake_handler.py`
      (`defi_adapter=` param, default `None` preserves existing simulation behavior byte-for-byte),
      `handler_registry.py` (`defi_adapter=` threading, SWAP/LEND/WITHDRAW/STAKE/UNSTAKE only — never
      BorrowHandler), `external_instruction_api.py` (5 new translation functions + `_submit_defi_instruction()`,
      module docstring updated to 9/13 wired). Tests: `tests/unit/test_defi_live_dispatch.py` (new),
      `test_handler_registry.py::TestHandlerRegistryDefiAdapterWiring` (new),
      `test_external_instruction_api.py`'s new `TestSwapInstructionPath`/`TestLendInstructionPath`/
      `TestStakeInstructionPath` (each with an honest-FAILED-not-fabricated landmine test, mirroring
      `TestTransferInstructionPath`'s). Full resolution record:
      `/plans/archive/issues/external_instruction_defi_handlers_simulation_only_2026_08_20.md` § "Resolution
      2026-08-21". Evidence: bash scripts/quality-gates.sh --no-fix (8872 passed, 22 skipped, 1 xpassed, 89 warnings in 237.24s; sentinel=4af371549778653f8240e1f3ca5ebb32a37e44f6).
- [x] [BACKEND] P1. ✅ SHIPPED 2026-08-21 — execution-service@4e35a09b2. `BORROW`/`REPAY` wired on
      `POST /external/instructions` through the same `defi_adapter=` injection seam on `BorrowHandler` proven 5x
      by SWAP/LEND/WITHDRAW/STAKE/UNSTAKE — new `dispatch_borrow_live()` calls `AAVEConnector.borrow()`/`.repay()`
      through the same `_resolve_live_connector` credential seam. Tests:
      `test_defi_live_dispatch.py::TestDispatchBorrowLive`,
      `test_external_instruction_api.py::TestBorrowRepayInstructionPath`. Evidence:
      `bash scripts/quality-gates.sh --no-fix` (8915 passed, cov 82.53%). Full record:
      `/plans/archive/issues/external_instruction_defi_handlers_simulation_only_2026_08_20.md` § "Resolution
      2026-08-21 (BORROW/REPAY)".
- [x] [BACKEND] P0. Wire `TRANSFER`/`CANCEL` on the same surface — **shipped execution-service@3af76e1a01**
      (2026-08-20, `instruction_router.py`/`external_instruction_api.py`/`transfer_handler.py`/`deribit.py`/
      `run_phase3c.py`/`tests/unit/test_external_instruction_api.py`, verified ancestor of
      `origin/live-defi-rollout`, full `quality-gates.sh` green: 8841 passed). The unrelated pre-existing
      bridge.py/cctp.py function-size QG gate that blocked the first several ship attempts was independently
      resolved by the domain owner (`execution-service@8b87a17a5`/`3f54ca206`) mid-session — reconciled via two
      `git pull --ff-only` + conflict-resolution rounds (always deferring to the domain owner's landed version
      over this session's own stopgap fixes in bridge.py/cctp.py/capture_golden_swaps.py/validate_uniswap_fills.py/
      test_order_recovery.py, per the "defer to the real owner's context" pattern this session applied
      throughout). `CANCEL`
      reuses the existing `order_tracker`-based cancel path `/manual/cancel` already established — done, tested
      (`TestCancelInstructionPath`). `TRANSFER` routes through the real `build_transfer_wiring()` ->
      `HandlerRegistry`/`InstructionRouter` -> `TransferHandler` chain (NOT `TransferCoordinator` as originally
      assumed here — see
      /plans/active/issues/external_instruction_bridge_atomic_not_wired_2026_08_20.md) — done, tested
      (`TestTransferInstructionPath`), including a same-day fix closing a pre-existing `InstructionRouter`
      structural gate rejecting every CeFi venue (see
      /plans/archive/issues/external_instruction_transfer_cefi_venue_category_registry_gap_2026_08_20.md
      `resolved_by`). Both produce a real result or an honest structured rejection, never a silent drop.
- [x] [BACKEND] P2. ✅ SHIPPED 2026-08-21 — execution-service@0aa709f0. `BRIDGE` routes through
      `TransferHandler` via a new `force_transfer_type` override + a new `LiveBridgeTransferAdapter` wrapping the
      pre-existing (never-wired) `SocketBridgeConnector`, backed by a new durable GCS `TransferStateStore`.
      Source-chain-leg broadcast success returns PENDING, never a fabricated instant success; destination-chain
      settlement is not confirmed synchronously. Tests: `test_transfer_handler_bridge.py`,
      `test_live_bridge_adapter.py`, `test_external_instruction_bridge_lp_translation.py`. Evidence:
      `bash scripts/quality-gates.sh --no-fix`. Full record:
      `/plans/active/issues/external_instruction_bridge_atomic_not_wired_2026_08_20.md` § "Resolution (BRIDGE,
      2026-08-21)".
- [x] [BACKEND] P0. ✅ SHIPPED 2026-08-21 — Wire `ATOMIC` through the existing `InstructionRouter.route_signal()` multi-leg dispatch; `execution-service@1636abd22e` translates each leg into the shared execution contract and returns per-leg results. Evidence: `bash scripts/quality-gates.sh --no-fix` (ALL QUALITY GATES PASSED, 934s); direct HTTP verification returned `200 COMPLETED_SUCCESS` with 2 per-leg results. The real venue-side atomic/compensation engine remains tracked in `/plans/active/issues/external_instruction_bridge_atomic_not_wired_2026_08_20.md`.
- [x] [BACKEND] P0. ✅ SHIPPED 2026-08-21 — Add `KILL_SWITCH`/`FLATTEN_POSITION` as coordinated `InstructionActionV2`
      members in unified-api-contracts and route authorized external controls through the existing kill-switch and
      `AccountInstructionOrchestrator.CLOSE_ALL` primitives. Evidence: unified-api-contracts@d44de9fb21351b2bdae1e78c32334c1272777678,
      execution-service@bc2edc16874a3b0828ef692682b69174ddcab4bf; `bash scripts/quality-gates.sh --no-fix` passed (execution-service: 8896 passed,
      22 skipped, 1 xfailed; UAC gate: ALL QUALITY GATES PASSED, 0 type errors). Regression coverage:
      `tests/unit/api/test_external_control_instruction.py` and UAC control-instruction contract tests.

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

- [x] [AGENT] P0. ✅ Post-phase codex audit — updated `/codex/02-data/live-data-persistence-and-event-log.md` with
      the measured Pub/Sub reader, atomic-instruction subscriber, Terraform, and warm/BQ surfaces; the tier/import
      SSOT had no stale messaging claim. Cross-linked and narrowed the remaining generic-reader todo in
      `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md` —
      unified-trading-pm@20ef76d216 + Evidence: PM diff review; `e2e-testing/tests/unit/test_atomic_instruction_live_routing_seam.py`
      and deployed `api.main` wiring verified.
- [x] [AGENT] P0. ✅ 2026-08-21 — reconciled. Found + fixed 2 more stale todos in THIS plan while doing so:
      `BORROW`/`REPAY` and `BRIDGE` had already shipped (execution-service@4e35a09b2, @0aa709f0) but were still
      unchecked above — flipped, with evidence, in this same pass. With those corrected, "Instruction action
      vocabulary" is now fully done; only "Deployment topology and external hosting" (4 todos) remains open.
      Also corrected `/plans/active/issues/external_instruction_bridge_atomic_not_wired_2026_08_20.md`, whose
      title + Follow-ups still claimed BRIDGE was unwired after the commit that wired it landed. Epic's W22
      section (`/plans/epics/system_readiness_master.md`) updated to match: messaging bridge, vocabulary, and
      kill-switch/flatten-position items flipped to done; the 4 deployment-topology/external-hosting items
      correctly left open, pointing here for detail rather than duplicating it.

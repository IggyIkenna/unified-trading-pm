---
doc_type: issue
title: >-
  `POST /external/instructions` (execution-service) — BRIDGE and ATOMIC now route through real handlers; the
  venue-side ATOMIC multi-leg execution engine and compensation semantics remain open
summary: >-
  Filed while wiring 2 of the remaining 9 `StrategyInstructionV2` action types (TRANSFER, CANCEL) onto
  `execution-service/execution_service/api/external_instruction_api.py`'s external HTTP front door (the other 7 —
  SWAP/LEND/WITHDRAW/BORROW/REPAY/STAKE/UNSTAKE — are a SEPARATE gap, tracked in
  `external_instruction_defi_handlers_simulation_only_2026_08_20.md`; do not conflate the two). BRIDGE and ATOMIC were
  deliberately NOT wired in the original 2026-08-20 change; both were subsequently wired — ATOMIC through the shared
  router, BRIDGE through the transfer-wiring seam — verified from the live code (not guessed), see the Resolution
  sections below:

  **BRIDGE** (as found 2026-08-20, since resolved — see "Resolution (BRIDGE, 2026-08-21)" below) —
  `execution_service/engine/handlers/transfer_handler.py`'s own module docstring lists
  `BRIDGE: stub (cross-chain bridge execution is complex)`, and `TransferHandler._execute_bridge_transfer` is a
  real, live stub: it logs a warning and unconditionally returns `_create_failure_result(instruction, "Bridge
  transfers are not yet implemented")` — never attempts a real cross-chain move. Separately,
  `execution_service/transfer_coordinator.py`'s own module docstring maps `BRIDGE -> execution_service.v2.handlers
  .BridgeHandler` — that class does not exist anywhere in the codebase (`rg -l "class BridgeHandler"` across
  execution-service returns nothing); the docstring's own routing table is dangling. Two independent subsystems
  (`TransferHandler`'s dispatch table and `TransferCoordinator`'s docstring) both point at BRIDGE as unimplemented —
  neither has a real target to route to.
  **ATOMIC**: there is no `OperationType.ATOMIC` handler; the external API now uses the existing multi-leg `DeFiSignal`/`InstructionRouter.route_signal()` path. The translation is covered by the shipped two-leg HTTP test and returns structured per-leg results. The underlying venue-side atomic engine still does not honor `AtomicExecutionMode`/`leader_leg`/`hedge_deadline_ms`/`compensation_policy`; that live execution follow-up remains open and is not represented as complete by this issue.

  Cross-reference: `plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md` now records BOTH the
  completed HTTP/router P0 todo AND the completed BRIDGE P2 todo. The venue-side ATOMIC engine plus compensation
  semantics remain the one open item under the follow-ups below. This issue is the durable record of that boundary.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, unified-trading-pm]
scope: [engineer]
tags: [execution-service, external-api, bridge, atomic, instruction-vocabulary, w22]
related:
  [
    /plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md,
    /plans/active/issues/external_instruction_defi_handlers_simulation_only_2026_08_20.md,
  ]
created: 2026-08-20
source: >-
  Sub-agent dispatch wiring 9 of the remaining external_instruction_api.py action types (2026-08-20) — TRANSFER and
  CANCEL shipped for real; BRIDGE/ATOMIC verified genuinely unbuilt and filed here per the dispatching task's
  explicit instruction.
author: agent
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    execution-service/execution_service/api/external_instruction_api.py,
    execution-service/execution_service/engine/handlers/transfer_handler.py,
    execution-service/execution_service/transfer_coordinator.py,
    execution-service/execution_service/backtest_v2/action_handlers.py,
  ]
drift_direction: advance-code
---

# BRIDGE and ATOMIC now reach real handlers; the venue-side ATOMIC multi-leg engine is the one open item

## Resolution (2026-08-21)

The external API now accepts `InstructionActionV2.ATOMIC`, translates each `AtomicLeg` into the shared `ExecutionInstruction` contract, and submits the resulting `DeFiSignal` through `InstructionRouter.route_signal()`. A two-leg HTTP verification returned `200 COMPLETED_SUCCESS` with two per-leg results. This proves the paper/router path required by the parent plan; it does not claim a venue-side atomic engine, compensation semantics, or real multi-leg live execution. BRIDGE was still an honest 501 at the time of this note; it was wired the same day — see "Resolution (BRIDGE, 2026-08-21)" below.

## Resolution (BRIDGE, 2026-08-21)

Shipped: `execution-service@0aa709f0` ("wire BRIDGE/LP_MINT/LP_BURN through real live-execution engines"). BRIDGE
routes through the SAME transfer wiring as TRANSFER — `TransferHandler` gained a new `force_transfer_type`
override, and a new `LiveBridgeTransferAdapter` wraps the pre-existing (but never-wired) `SocketBridgeConnector`
(Socket v2 bridge-route aggregator across Across/Stargate/CCTP/Hop), backed by a new durable GCS
`TransferStateStore` for cross-chain leg state. Source-chain-leg broadcast success returns `PENDING`, never a
fabricated instant success; destination-chain settlement is not confirmed synchronously. This closes the BRIDGE
half of this issue's original scope — resolved by routing through `TransferHandler` instead of building the
dedicated `BridgeHandler` class the original "What real work would close this" section below speculated would be
needed. Tests: `tests/unit/test_transfer_handler_bridge.py`, `tests/unit/test_live_bridge_adapter.py`,
`tests/unit/test_external_instruction_bridge_lp_translation.py`. Evidence: `bash scripts/quality-gates.sh --no-fix`.

## What was checked (2026-08-20, direct code read)

1. **BRIDGE**: `TransferHandler._execute_bridge_transfer` (`execution_service/engine/handlers/transfer_handler.py`)
   is a real, honest stub — logs and returns a failure result, never attempts a bridge. `transfer_coordinator.py`'s
   own docstring cites `execution_service.v2.handlers.BridgeHandler` as the BRIDGE target; that class does not
   exist anywhere in the repo.
2. **ATOMIC**: no `OperationType.ATOMIC` handler exists in the live handler registry. The external API now translates `AtomicInstruction` legs into `DeFiSignal` instructions and routes them through `InstructionRouter.route_signal()`, verified by the shipped two-leg HTTP test. The existing `backtest_v2/action_handlers.py::resolve_settlement` remains benchmark settlement only; venue-side atomic execution and compensation semantics are still open.

## Why this matters for the plan that assumed otherwise

The parent plan originally assumed BRIDGE and ATOMIC were both ready for the same translation-shim pass. Both are
now wired on the external HTTP surface (ATOMIC via the shared multi-leg router, BRIDGE via the transfer-wiring
seam) — see the Resolution sections above. The venue-side ATOMIC engine plus compensation semantics remain the one
genuinely open follow-up. Read this issue before extending that path.

## What real work would close this

- ~~**BRIDGE**: needs a real `BridgeHandler` or equivalent implementing actual cross-chain bridge execution (route selection, source-chain lock/burn, destination-chain mint/unlock, and confirmation tracking).~~ DONE 2026-08-21 — see "Resolution (BRIDGE, 2026-08-21)" above. Routed through `TransferHandler` + `LiveBridgeTransferAdapter`/`SocketBridgeConnector` rather than a dedicated `BridgeHandler` class.
- **ATOMIC**: needs a real venue-side multi-leg execution engine honoring `AtomicExecutionMode`, `leader_leg`, `hedge_deadline_ms`, and `compensation_policy`, including per-leg order placement and partial-fill or leg-failure compensation.

## Follow-ups

- [x] [BACKEND] P2. ✅ SHIPPED 2026-08-21 — execution-service@0aa709f0. Wired `BRIDGE` on
      `POST /external/instructions` (execution-service) via `TransferHandler`'s new `force_transfer_type` override
      + `LiveBridgeTransferAdapter`/`SocketBridgeConnector`, not the originally-speculated dedicated `BridgeHandler`
      class. See "Resolution (BRIDGE, 2026-08-21)" above.
- [ ] [BACKEND] P2. Design + build a real live multi-leg execution engine for `ATOMIC` (new `OperationType`/handler,
      real per-leg order placement, partial-fill/compensation handling per `AtomicExecutionMode`), then wire
      `ATOMIC` on the same surface. This is a genuinely new execution-engine design effort, not a translation shim
      — should likely be its own dedicated plan, not a todo folded into a translation-wiring pass.

## Progress Log

- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — both open todos are brand-new execution-engine design +
  build efforts (a real BridgeHandler, a real live multi-leg execution engine for ATOMIC), each explicitly framed
  in-doc as needing its own dedicated plan, not mechanical wiring. Cross-cutting tranche, batch 2 of 3.
- **W22 epic-reconciliation pass 2026-08-21**: BRIDGE follow-up flipped to done — `execution-service@0aa709f0`
  landed after the na-eligibility-audit entry above and wires BRIDGE for real (verified via commit diff + new
  tests, not the commit message alone). Only the ATOMIC venue-side engine follow-up remains genuinely open; title,
  summary, and "What real work would close this" updated to match so this doc stops misleading readers into
  thinking BRIDGE is still unwired.

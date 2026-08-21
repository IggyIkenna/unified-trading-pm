---
doc_type: issue
title: >-
  `POST /external/instructions` (execution-service) — BRIDGE and ATOMIC stay HTTP 501 on purpose: both need real,
  unbuilt execution engineering, not a translation shim
summary: >-
  Filed while wiring 2 of the remaining 9 `StrategyInstructionV2` action types (TRANSFER, CANCEL) onto
  `execution-service/execution_service/api/external_instruction_api.py`'s external HTTP front door (the other 7 —
  SWAP/LEND/WITHDRAW/BORROW/REPAY/STAKE/UNSTAKE — are a SEPARATE gap, tracked in
  `external_instruction_defi_handlers_simulation_only_2026_08_20.md`; do not conflate the two). BRIDGE and ATOMIC are
  deliberately NOT wired in that same change, verified from the live code (not guessed):

  **BRIDGE** — `execution_service/engine/handlers/transfer_handler.py`'s own module docstring lists
  `BRIDGE: stub (cross-chain bridge execution is complex)`, and `TransferHandler._execute_bridge_transfer` is a
  real, live stub: it logs a warning and unconditionally returns `_create_failure_result(instruction, "Bridge
  transfers are not yet implemented")` — never attempts a real cross-chain move. Separately,
  `execution_service/transfer_coordinator.py`'s own module docstring maps `BRIDGE -> execution_service.v2.handlers
  .BridgeHandler` — that class does not exist anywhere in the codebase (`rg -l "class BridgeHandler"` across
  execution-service returns nothing); the docstring's own routing table is dangling. Two independent subsystems
  (`TransferHandler`'s dispatch table and `TransferCoordinator`'s docstring) both point at BRIDGE as unimplemented —
  neither has a real target to route to.
  **ATOMIC** — there is no `OperationType.ATOMIC` in `unified_api_contracts.internal.domain.execution_service.types
  .OperationType` and no atomic/multi-leg handler of any kind in `execution_service/engine/handlers/` or
  `execution_service/engine/routing/handler_registry.py::HandlerRegistry.DEFAULT_HANDLERS`. The only place
  `AtomicInstruction`/`InstructionActionV2.ATOMIC` is handled at all is
  `execution_service/backtest_v2/action_handlers.py::resolve_settlement` — and that function is BATCH-BACKTEST
  BENCHMARK SETTLEMENT ONLY (per its own module docstring, "the SMART-MATCHING layer batch must run" for the
  paper==batch-rerun determinism spine): it computes a deterministic `(reference_price, fill_size)` pair for
  execution-alpha measurement against a REPLAYED historical instruction, never places a real order and never touches
  a live venue. Reusing it for the live/external HTTP path (as `plans/active/w22_strategy_execution_messaging_
  external_api_2026_08_20.md`'s own P0 todo currently suggests — "routing through the existing multi-leg dispatch...
  reuse the same leg-iteration logic for the live path") would NOT be pure translation: it requires designing and
  building a genuinely new live multi-leg execution engine (real per-leg order placement, partial-fill/leg-failure
  handling, `AtomicExecutionMode`/`leader_leg`/`hedge_deadline_ms`/`compensation_policy` semantics), which is real,
  unbuilt engineering out of scope for a translation shim.

  Cross-reference: `plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md`'s own unchecked P0
  todo ("Wire TRANSFER/BRIDGE/CANCEL on the same surface... TRANSFER/BRIDGE route through TransferCoordinator" and
  "Wire ATOMIC... routing through the existing multi-leg dispatch... reuse the same leg-iteration logic for the live
  path") assumes both are readier than they are — see that plan's Progress Log / this issue for the correction. This
  doc is the honest record so the module docstring's BRIDGE/ATOMIC 501 claim in `external_instruction_api.py` stays
  traceable to real evidence rather than going stale the way the doc it replaced did.
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

# BRIDGE and ATOMIC stay 501 on `POST /external/instructions` — both need real execution engineering

## What was checked (2026-08-20, direct code read)

1. **BRIDGE**: `TransferHandler._execute_bridge_transfer` (`execution_service/engine/handlers/transfer_handler.py`)
   is a real, honest stub — logs and returns a failure result, never attempts a bridge. `transfer_coordinator.py`'s
   own docstring cites `execution_service.v2.handlers.BridgeHandler` as the BRIDGE target; that class does not
   exist anywhere in the repo.
2. **ATOMIC**: no `OperationType.ATOMIC`, no handler in `HandlerRegistry.DEFAULT_HANDLERS`. The only ATOMIC-aware
   code is `backtest_v2/action_handlers.py::resolve_settlement`, which is a batch-backtest benchmark-settlement
   function (computes a reference price/fill size for a REPLAYED historical instruction to measure execution alpha)
   — not a live execution path, and not reusable as one without new engineering.

## Why this matters for the plan that assumed otherwise

`plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md`'s "Instruction action vocabulary" section
has an unchecked P0 todo assuming BRIDGE routes through `TransferCoordinator` and ATOMIC reuses the backtest
leg-iteration logic "for the live path." Both assumptions do not hold under direct code verification — see the
summary above for the specific evidence. Whoever picks up that todo next should read this issue first rather than
re-discovering the same dead ends.

## What real work would close this

- **BRIDGE**: needs a real `BridgeHandler` (or equivalent) implementing actual cross-chain bridge execution
  (route selection, source-chain lock/burn, destination-chain mint/unlock, confirmation tracking) — multi-step,
  multi-chain, genuinely complex per the existing stub's own docstring.
- **ATOMIC**: needs (a) a new `OperationType.ATOMIC` (or equivalent multi-leg operation concept) in UAC, (b) a real
  live multi-leg execution engine honoring `AtomicExecutionMode`/`leader_leg`/`hedge_deadline_ms`/
  `compensation_policy` — per-leg real order placement with partial-fill and leg-failure/compensation handling, not
  a benchmark-price simulation.

## Follow-ups

- [ ] [BACKEND] P2. Design + build a real `BridgeHandler` for cross-chain bridge execution, then wire `BRIDGE` on
      `POST /external/instructions` (execution-service) using the same translation-shim pattern already
      established for TRANSFER/CANCEL. Blocked on: bridge-protocol selection (which bridge(s) to integrate first).
- [ ] [BACKEND] P2. Design + build a real live multi-leg execution engine for `ATOMIC` (new `OperationType`/handler,
      real per-leg order placement, partial-fill/compensation handling per `AtomicExecutionMode`), then wire
      `ATOMIC` on the same surface. This is a genuinely new execution-engine design effort, not a translation shim
      — should likely be its own dedicated plan, not a todo folded into a translation-wiring pass.

---
doc_type: issue
title: >-
  `POST /external/instructions` (execution-service) — SWAP/LEND/WITHDRAW/BORROW/REPAY/STAKE/UNSTAKE stay HTTP 501:
  the registered `HandlerRegistry` handlers for this family are backtest/paper-simulation only, never live-wired,
  in EVERY operational mode
summary: >-
  Discovered mid-implementation while wiring the remaining `StrategyInstructionV2` action types onto
  `execution-service/execution_service/api/external_instruction_api.py`'s external HTTP front door. The dispatching
  task's premise was that `execution_service/engine/routing/handler_registry.py::HandlerRegistry.DEFAULT_HANDLERS`
  gives SWAP/LEND/WITHDRAW/BORROW/REPAY/STAKE/UNSTAKE "real, tested, already-registered internal execution
  handlers" ready for a pure envelope-translation shim (`SwapHandler`/`LendHandler`/`BorrowHandler`/`StakeHandler`
  — all real classes, all registered, all covered by unit tests). Direct code verification found this is TRUE only
  in the narrow sense that the classes exist and are registered — it is FALSE that they perform real execution in
  ANY operational mode, including live. Wiring them through `HandlerRegistry` as originally instructed would have
  shipped an external HTTP endpoint that silently fabricates a `COMPLETED_SUCCESS` execution result (no
  `transaction_hash`, ever) for every SWAP/LEND/BORROW/STAKE/etc submission, regardless of whether the service is
  configured for live or paper trading — a "fabricated success" hard-rule violation, not a coverage gap. TRANSFER
  and CANCEL (verified genuinely real — see the sibling BRIDGE/ATOMIC issue for what stayed 501 for a DIFFERENT,
  correct reason) shipped in the same change; these 7 action types were descoped instead of forced through.

  Evidence chain (all verified 2026-08-20, direct code read, not guessed): (1) `BaseHandler._get_engine()`
  (`execution_service/engine/handlers/base_handler.py`) falls back to a bare `MatchingEngine()` — the pure-math
  matching-engine-library engine (L1/L2/AMM/`BenchmarkMatcher` — instant fill at benchmark price, ALPHA_ZERO for
  LEND/STAKE/BORROW) — whenever `BaseHandler._matching_engine` (a CLASS-level attribute shared by every handler
  instance) is `None`. (2) `BaseHandler.set_matching_engine()` is the ONLY way to inject a different engine; grepping
  every call site across the repo (`rg -rn "set_matching_engine\("`) finds it called EXCLUSIVELY from
  `tests/unit/test_handlers_matching_engine.py` — zero calls from `api/app.py`, `api/main.py`, or any
  `engine/*/wiring.py`/`factory.py` module. (3) `LendHandler`'s own class docstring already says this explicitly:
  "LIVE-WIRED: this list is a backtest/BenchmarkMatcher membership set only — it does NOT mean a venue is reachable
  in live trading. The live-authoritative DeFi execution path is
  `execution_service.adapters.defi_adapter.DeFiAdapter`, constructed by `LiveExecutionHandler._build_defi_adapter`."
  `StakeHandler`'s docstring says the same for STAKE/UNSTAKE. (4) `DeFiAdapter` needs a lazy-construct-and-cache
  factory that does not exist yet — confirmed independently by `plans/active/w22_strategy_execution_messaging_
  external_api_2026_08_20.md`'s own unchecked P0 todo: "Build the DeFiAdapter lazy-construct-and-cache factory ...
  does not exist yet." Building that factory (or wiring `set_matching_engine()` to something real) is new execution
  infrastructure, not a translation shim — explicitly out of scope for the dispatched task ("pure translation, no
  new execution logic").
status: open
nature: issue
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, unified-trading-pm]
scope: [engineer]
tags: [execution-service, external-api, defi, handler-registry, matching-engine, fabricated-success, w22]
related:
  [
    /plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md,
    /plans/active/issues/external_instruction_bridge_atomic_not_wired_2026_08_20.md,
  ]
created: 2026-08-20
source: >-
  Sub-agent dispatch wiring 9 of the remaining external_instruction_api.py action types (2026-08-20). The dispatch
  brief's premise (HandlerRegistry handlers are real/tested/ready-to-wire) held for TRANSFER and CANCEL but was
  verified FALSE for this 7-action-type family before any translator was written — descoped per the dispatch's own
  explicit "stop and report rather than inventing new execution logic to force it through" instruction.
author: agent
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 5
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    execution-service/execution_service/api/external_instruction_api.py,
    execution-service/execution_service/engine/handlers/base_handler.py,
    execution-service/execution_service/engine/handlers/swap_handler.py,
    execution-service/execution_service/engine/handlers/lend_handler.py,
    execution-service/execution_service/engine/handlers/borrow_handler.py,
    execution-service/execution_service/engine/handlers/stake_handler.py,
    execution-service/execution_service/adapters/defi_adapter.py,
  ]
drift_direction: advance-code
---

# SWAP/LEND/WITHDRAW/BORROW/REPAY/STAKE/UNSTAKE stay 501 on `POST /external/instructions` — real handlers exist but are simulation-only

## Why this is a P1, not a P2 like the BRIDGE/ATOMIC sibling

BRIDGE/ATOMIC are genuinely unbuilt — nobody could mistake them for done. This gap is more dangerous precisely
BECAUSE the handlers look production-ready (real classes, `HandlerRegistry`-registered, covered by unit tests,
named exactly like a live execution handler). A future implementer following the SAME reasoning the original
dispatch brief used (present in `HandlerRegistry.DEFAULT_HANDLERS` == ready to wire) would ship a silent
fabricated-success endpoint without realizing it. This issue exists specifically so that reasoning is not repeated.

## The mechanism, precisely

- `HandlerRegistry.get_handler(OperationType.SWAP)` returns a real `SwapHandler()` instance.
- `SwapHandler.execute()` calls `self._get_engine().match_order(...)` — always the class-level
  `BaseHandler._matching_engine`, defaulting to `execution_service.engine.matching.MatchingEngine()`
  (matching-engine-library's pure simulation: `AMMMatcher`/`BenchmarkMatcher`/etc — no network call, no venue
  connector, no signing key, ever).
- Nothing in any production startup path (`api/app.py`, `api/main.py`, `engine/transfers/wiring.py`, or any other
  `wiring.py`/`factory.py`) ever calls `BaseHandler.set_matching_engine()` with a real order-placing engine. The
  ONLY real order-placing engine that exists (`execution_service/engine/modes/live/matching_engine.py
  ::LiveMatchingEngine`, which genuinely wraps `get_order_adapter().place_order()`) is a DIFFERENT class that
  `HandlerRegistry`'s handlers never reference at all.
- Result: `SwapHandler.execute()`/`LendHandler.execute()`/`BorrowHandler.execute()`/`StakeHandler.execute()` always
  return `ExecutionStatus.COMPLETED_SUCCESS` with a simulated `actual_execution_price`/`amount_executed` and
  `transaction_hash=None` — indistinguishable from a real fill to a caller who doesn't specifically check for the
  missing tx hash — REGARDLESS of whether the service process is configured for live or paper trading. There is no
  mode branch anywhere in this call chain.

## The real live-authoritative path (already documented, just not wired to this endpoint)

`execution_service.adapters.defi_adapter.DeFiAdapter`, constructed via
`LiveExecutionHandler._build_defi_adapter`/`get_defi_adapter_singleton()` — already used by the internal manual
surface for DeFi venues (`ManualOperationHandler.execute()`'s `DEFI_VENUES` branch, wired 2026-08-20 per
`execution-service@8cd47073b`). As of 2026-08-17 this only has live connectors for AAVE_V3 (LEND/BORROW/WITHDRAW/
REPAY) and LIDO (STAKE) — `MORPHO`/`COMPOUND_V3`/`EULERV2`/`FLUID`/`ETHERFI` have no live connector construction at
all (tracked separately: `/plans/archive/2026_08/defi_venue_e2e_batch1_2026_08_16.md` "DeFiAdapter wires only 5 of 12+").

## What real work would close this

1. Build the DeFiAdapter lazy-construct-and-cache factory (`plans/active/w22_strategy_execution_messaging_
   external_api_2026_08_20.md`'s own unchecked P0 todo already scopes this — same factory, don't build a second
   one).
2. Wire `SWAP`/`LEND`/`WITHDRAW`/`BORROW`/`REPAY`/`STAKE`/`UNSTAKE` on `POST /external/instructions` through that
   factory's `DeFiAdapter.execute_instruction()` — the SAME pattern `ManualOperationHandler.execute()`'s DEFI_VENUES
   branch already established for the internal surface, not `HandlerRegistry`.
3. Until then, keep this surface's 501 for these 7 action types — do not wire them through `HandlerRegistry` even
   as an interim step; that would ship the fabricated-success behavior described above.

## Follow-ups

- [ ] [BACKEND] P1. Build the DeFiAdapter lazy-construct-and-cache factory (dedupes with
      `w22_strategy_execution_messaging_external_api_2026_08_20.md`'s existing todo — coordinate, don't duplicate).
- [ ] [BACKEND] P1. Once the factory exists, wire SWAP/LEND/WITHDRAW/BORROW/REPAY/STAKE/UNSTAKE on
      `POST /external/instructions` through `DeFiAdapter.execute_instruction()`, mirroring
      `_build_execution_instruction_from_transfer`'s translation-shim pattern already shipped for TRANSFER.
- [ ] [BACKEND] P3. Separately (lower priority, not blocking the above): consider whether
      `BaseHandler.set_matching_engine()` should ever be wired to a real engine in production for THIS handler
      family, or whether that family should be treated as permanently backtest/paper-only and all live DeFi
      execution should route through `DeFiAdapter` exclusively — a design decision, not a mechanical fix.

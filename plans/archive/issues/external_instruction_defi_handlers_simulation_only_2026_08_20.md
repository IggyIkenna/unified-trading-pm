---
doc_type: issue
title: >-
  `POST /external/instructions` (execution-service) — SWAP/LEND/WITHDRAW/BORROW/REPAY/STAKE/UNSTAKE now route
  through real live-dispatch handlers (RESOLVED 2026-08-21); this doc is the durable record of the fabricated-success
  gap they were previously simulation-only
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

  RESOLVED (fully, all 7 named action types) 2026-08-21. SWAP/LEND/WITHDRAW/STAKE/UNSTAKE resolved first — see the
  "Resolution 2026-08-21" section below for the real design (a `defi_adapter=` injection seam on
  SwapHandler/LendHandler/StakeHandler, mirroring TransferHandler's existing `adapter=` pattern — NOT the
  originally-scoped "wire through DeFiAdapter.execute_instruction() directly" approach, which turned out to have
  its own fabricated-success gap; see `/plans/active/issues/defi_adapter_execute_instruction_success_check_gap_2026_08_21.md`).
  BORROW/REPAY (`BorrowHandler`) closed same-day (execution-service@4e35a09b2) via the identical seam, once the
  pattern was proven 5x — see "Resolution 2026-08-21 (BORROW/REPAY)" below.
status: resolved
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
    /plans/active/issues/defi_adapter_execute_instruction_success_check_gap_2026_08_21.md,
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
resolved_by: >-
  All 7 named action types resolved 2026-08-21: SWAP/LEND/WITHDRAW/STAKE/UNSTAKE via `execution-service@4af3715497`;
  BORROW/REPAY via `execution-service@4e35a09b2` through the identical defi_adapter= seam. Full design record in
  this doc's own "Resolution 2026-08-21" and "Resolution 2026-08-21 (BORROW/REPAY)" sections. As of 2026-08-21
  later the same day, ALL 16 of 16 StrategyInstructionV2 action types (incl. BRIDGE/ATOMIC/LP_MINT/LP_BURN/CONTROL)
  are wired — execution-service@b49a3f1a9 closes the full surface; fresh quality-gates.sh re-verified green on
  HEAD 67fb2c607096f49921e3b2f465b1a243521b0e6a: 8906 passed, 0 failed.
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
    execution-service/execution_service/engine/handlers/defi_live_dispatch.py,
    execution-service/execution_service/adapters/defi_adapter.py,
    execution-service/execution_service/adapters/defi_live_wiring.py,
  ]
drift_direction: advance-code
---

# SWAP/LEND/WITHDRAW/BORROW/REPAY/STAKE/UNSTAKE stay 501 on `POST /external/instructions` — real handlers exist but are simulation-only

> **RESOLVED + ARCHIVED 2026-08-21.** All 7 action types now route through real live-dispatch handlers —
> `execution-service@4af3715497` (SWAP/LEND/WITHDRAW/STAKE/UNSTAKE) + `execution-service@4e35a09b2`
> (BORROW/REPAY). See `resolved_by` frontmatter and the "Resolution 2026-08-21" sections below for the full record.

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
  `wiring.py`/`factory.py` module) ever calls `BaseHandler.set_matching_engine()` with a real order-placing engine.
  The ONLY real order-placing engine that exists (`execution_service/engine/modes/live/matching_engine.py
  ::LiveMatchingEngine`, which genuinely wraps `get_order_adapter().place_order()`) is a DIFFERENT class that
  `HandlerRegistry`'s handlers never reference at all.
- Result (still true for BORROW/REPAY today): `BorrowHandler.execute()` always returns
  `ExecutionStatus.COMPLETED_SUCCESS` with a simulated `actual_execution_price`/`amount_executed` and
  `transaction_hash=None` — indistinguishable from a real fill to a caller who doesn't specifically check for the
  missing tx hash — REGARDLESS of whether the service process is configured for live or paper trading. There is no
  mode branch anywhere in this call chain.

## Resolution 2026-08-21 (partial — SWAP/LEND/WITHDRAW/STAKE/UNSTAKE)

Shipped: `execution-service@4af3715497`. Real design, NOT what this issue's own original Follow-ups guessed:

- **`SwapHandler`/`LendHandler`/`StakeHandler` now accept an optional `defi_adapter: DeFiAdapter | None`
  constructor param** (new file `execution_service/engine/handlers/defi_live_dispatch.py` implements the actual
  dispatch), mirroring `TransferHandler`'s existing `adapter=` injection seam exactly — `HandlerRegistry` threads a
  real, connected `DeFiAdapter` into these 3 handler classes for `OperationType` in
  `{SWAP, LEND, WITHDRAW, STAKE, UNSTAKE}` only (never `BorrowHandler`). `defi_adapter=None` (the default)
  preserves every handler's EXISTING pure-simulation behavior byte-for-byte — zero pre-existing test breakage.
- **New wiring module `execution_service/adapters/defi_live_wiring.py`** (`build_defi_execution_wiring()`) is the
  factory this issue's own Follow-up #1 asked for — it turned out to already substantially exist
  (`execution_service.cli.handlers.live_execution_handler.get_defi_adapter_singleton()`, already real and already
  used by `ManualOperationHandler.get_or_create_defi_adapter()` for the internal manual-instruction surface's
  DeFi-venue branch since 2026-08-20). `build_defi_execution_wiring()` is a second caller of that SAME factory, not
  a second implementation — plus the critical safety property this issue's hard rule demands: in LIVE/MANUAL
  operational mode, the wired adapter is NEVER `None` (an empty, connector-less-but-real `DeFiAdapter()` is
  substituted when Secret Manager credentials can't be resolved), so a genuinely live-mode dispatch always reaches
  the live-dispatch seam and gets an honest FAILED result — it never silently falls back to the simulation branch.
- **`execution_service/api/external_instruction_api.py`** gained `_submit_defi_instruction()` +5 translation
  functions (`_build_execution_instruction_from_{swap,lend,withdraw,stake,unstake}`), mirroring
  `_build_execution_instruction_from_transfer`'s exact pure-translation pattern — `POST /external/instructions` now
  wires 9 of 13 action types (was 4).
- **Design correction found mid-implementation, NOT this issue's original Follow-up #2's literal
  "route through DeFiAdapter's execute_instruction()"**: direct code reading of `DeFiAdapter._execute_swap`/
  `_execute_lending`/per-protocol staking helpers found they do not check the connector result's own `success`
  field before reporting `"status": "COMPLETED"` — a real, separate fabricated/degraded-success gap, filed as
  `/plans/active/issues/defi_adapter_execute_instruction_success_check_gap_2026_08_21.md` (NOT fixed here, to avoid
  widening this change's blast radius onto `DeFiAdapter`'s already-shipped internal-manual-API consumer). The new
  `defi_live_dispatch` module reuses `DeFiAdapter` ONLY as a connector container (Secret Manager credential
  resolution / Web3 signing / `is_live` wiring — the real, hard, already-correct part) and does its own connector
  calls + `success` check + correct tx_hash key lookup, so this fix does not inherit that sibling gap.
- **Coverage**: only Uniswap V3/V2 (SWAP), AAVE V3 (LEND/WITHDRAW), and Lido (STAKE/UNSTAKE) have a real
  call-shape mapping in `defi_live_dispatch` today — `resolve_defi_route()` can route a venue to another real,
  live-capable `DeFiAdapter` connector (Morpho, EtherFi, Kamino, ...) that this seam has not been taught the call
  shape for yet (different method signatures, e.g. `MorphoConnector.supply(market_id, amount)` vs
  `AAVEConnector.supply(token, amount)`); those honestly FAIL with a clear "no call-shape mapping" message,
  never a guessed call.
- Tests: `tests/unit/test_defi_live_dispatch.py` (new, both the real-credentials and no-credentials-honest-failure
  paths per dispatch function), `tests/unit/test_handler_registry.py::TestHandlerRegistryDefiAdapterWiring` (new,
  mirrors `TestHandlerRegistryTransferAdapterWiring`), `tests/unit/test_external_instruction_api.py`'s new
  `TestSwapInstructionPath`/`TestLendInstructionPath`/`TestStakeInstructionPath` classes (mirror
  `TestTransferInstructionPath`, including the "no live credentials -> honest FAILED, never fabricated" landmine
  test for each). Evidence: `bash scripts/quality-gates.sh --no-fix` green — `8872 passed, 22 skipped, 1 xpassed, 89 warnings in 237.24s; sentinel=4af371549778653f8240e1f3ca5ebb32a37e44f6`.

## Resolution 2026-08-21 (BORROW/REPAY)

Shipped: `execution-service@4e35a09b2`, same day as the SWAP/LEND/WITHDRAW/STAKE/UNSTAKE resolution above, once
that dispatch pattern was proven 5x. Identical design, no new pattern invented:

- **`dispatch_borrow_live()` added to `execution_service/engine/handlers/defi_live_dispatch.py`** — calls
  `AAVEConnector.borrow()`/`.repay()` (the real, already-live-capable connector methods this issue's own
  Follow-up already named), through the SAME `_resolve_live_connector` credential/connection-check seam
  SWAP/LEND/STAKE use.
- **`BorrowHandler` now accepts `defi_adapter: DeFiAdapter | None`**, mirroring
  `SwapHandler`/`LendHandler`/`StakeHandler`'s exact constructor pattern; `defi_adapter=None` (default) preserves
  existing pure-simulation behavior byte-for-byte.
- **`HandlerRegistry._DEFI_LIVE_DISPATCH_OPERATIONS`** extended to include `BORROW`/`REPAY`.
- **`external_instruction_defi.py`/`external_instruction_api.py`** gained `_build_execution_instruction_from_
  {borrow,repay}` + `BorrowInstruction`/`RepayInstruction` dispatch — `POST /external/instructions` now wires 12
  of 15 action types (was 10; the union grew from 13 to 15 members with `LP_MINT`/`LP_BURN` since this issue was
  filed).
- Tests: `tests/unit/test_defi_live_dispatch.py::TestDispatchBorrowLive`,
  `tests/unit/test_external_instruction_api.py::TestBorrowRepayInstructionPath`,
  `tests/unit/test_handler_registry.py` (extended `TestHandlerRegistryDefiAdapterWiring` loop). Evidence:
  `bash scripts/quality-gates.sh --no-fix` green — 8915 passed, cov 82.53%.
- `platform-api-reference.html` BORROW/REPAY rows updated to match — `unified-trading-pm@185e266a0e`.

## The real live-authoritative path (already documented, just not wired to this endpoint)

`execution_service.adapters.defi_adapter.DeFiAdapter`, constructed via
`LiveExecutionHandler._build_defi_adapter`/`get_defi_adapter_singleton()` — already used by the internal manual
surface for DeFi venues (`ManualOperationHandler.execute()`'s `DEFI_VENUES` branch, wired 2026-08-20 per
`execution-service@8cd47073b`). As of 2026-08-21, `_build_defi_adapter` constructs real, live-capable
(`supports_live = True`) connectors for AAVE_V3, MORPHO, PENDLE, SYMBIOTIC, ETHERFI, PUFFER, and ROCKET_POOL too
(this superseded the original "only AAVE_V3/LIDO wired" claim below sometime between 2026-08-17 and 2026-08-20 —
`LendHandler`/`StakeHandler`'s docstrings have been corrected to say so). `COMPOUND_V3`/`EULERV2`/`FLUID` still have
no live connector construction at all (tracked: `/plans/archive/2026_08/defi_venue_e2e_batch1_2026_08_16.md`
"DeFiAdapter wires only 5 of 12+").

## What real work would close this fully

1. ~~Build the DeFiAdapter lazy-construct-and-cache factory~~ — DONE, see Resolution above (it substantially
   already existed; `build_defi_execution_wiring()` is the HTTP-surface-facing caller of it).
2. ~~Wire `SWAP`/`LEND`/`WITHDRAW`/`STAKE`/`UNSTAKE` on `POST /external/instructions`~~ — DONE, see Resolution
   above.
3. ~~Wire `BORROW`/`REPAY` (`BorrowHandler`)~~ — DONE same-day 2026-08-21, see "Resolution 2026-08-21
   (BORROW/REPAY)" above. This closes the issue's ORIGINAL scope in full (all 7 named action types); the two
   Follow-ups below (Morpho/EtherFi coverage extension, matching_engine permanent-question) are separate,
   lower-priority, genuinely still open.

## Follow-ups

- [x] [BACKEND] P1. Build the DeFiAdapter lazy-construct-and-cache factory — DONE 2026-08-21, see Resolution
      section (turned out to substantially already exist as `get_defi_adapter_singleton()`;
      `build_defi_execution_wiring()` is the new HTTP-surface caller).
- [x] [BACKEND] P1. Once the factory exists, wire SWAP/LEND/WITHDRAW/STAKE/UNSTAKE on
      `POST /external/instructions`, mirroring `_build_execution_instruction_from_transfer`'s translation-shim
      pattern — DONE 2026-08-21 (BORROW/REPAY explicitly excluded from this todo's original wording; tracked as
      its own item below).
- [x] [BACKEND] P1. Wire `BORROW`/`REPAY` on `POST /external/instructions` through an analogous
      `defi_adapter=`-injection seam on `BorrowHandler` — DONE 2026-08-21, see "Resolution 2026-08-21
      (BORROW/REPAY)" above. `execution-service@4e35a09b2`.
- [ ] [BACKEND] P2. Extend `defi_live_dispatch`'s connector coverage to Morpho (LEND/WITHDRAW) and EtherFi
      (STAKE/UNSTAKE) — both are real, live-capable `DeFiAdapter` connectors already, just missing a call-shape
      mapping in the new seam (see the Resolution section's "Coverage" note).
- [ ] [BACKEND] P3. Separately (lower priority, not blocking the above): consider whether
      `BaseHandler.set_matching_engine()` should ever be wired to a real engine in production for THIS handler
      family, or whether that family should be treated as permanently backtest/paper-only and all live DeFi
      execution should route through the `defi_adapter=` injection seam exclusively — largely answered by the
      2026-08-21 resolution (the seam approach), but BorrowHandler's own answer is still open.

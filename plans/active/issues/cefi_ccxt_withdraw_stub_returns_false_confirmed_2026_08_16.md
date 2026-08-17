---
doc_type: issue
title: CCXT withdraw() is a stub that always returns CONFIRMED without calling the exchange — affects every CEX venue
summary: >-
  execution-service's LiveCcxtTransferAdapter.execute_withdrawal never calls exchange.withdraw() — the real CCXT
  call is commented out and the method always returns a CONFIRMED result. Every CEX_WITHDRAW-routed venue (18 of
  cefi's 22, everything that isn't ON_CHAIN/CUSTODY_TRANSFER) would report a successful withdrawal that never
  actually happened. Found during the venue_e2e_wiring_2026_08_16 cefi batch sweep, step 9 (transfers).
  **Reachability confirmed 2026-08-16 (later same day): DEAD-CODE-TODAY** — HandlerRegistry never constructs a
  live adapter (defaults to MockTransferAdapter), TransferCoordinator has no CEX_WITHDRAW handler registered at
  all, and the system is still pre-live-trading. Real bug, currently inert — must-fix-before-live-trading-cutover,
  not an active incident.
status: open
nature: issue
asset_group: [cefi]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [transfers, financial-correctness, live-money-risk, stub-code, venue-readiness]
related:
  [
    /plans/active/cefi_venue_e2e_batch1_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /codex/04-architecture/transfer-architecture.md,
  ]
created: 2026-08-16
author: interactive-session
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Found 2026-08-16 during cefi_venue_e2e_batch1_2026_08_16.md's step-9 (transfers) contract sweep — a dedicated
  research pass across execution-service's transfer dispatch code, checking every cefi venue's real withdrawal
  path, not just its registry classification.
context_scope:
  [
    execution-service/execution_service/engine/handlers/transfer_handler.py,
    execution-service/execution_service/transfer_coordinator.py,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# CCXT withdraw() is a stub that always returns CONFIRMED without calling the exchange

## What I found

`execution-service`'s live CEX withdrawal path (`LiveCcxtTransferAdapter.execute_withdrawal`, called from
`transfer_handler.py::_execute_cex_withdrawal`, dispatched by `_dispatch_transfer` for every `BusTransferType.
CEX_WITHDRAW` transfer) does not actually call the exchange. The real `exchange.withdraw()` CCXT call is
commented out; the code logs `"CCXT withdraw() not yet wired -- returning success stub"` and unconditionally
returns a `CONFIRMED` transfer result.

**Every one of cefi's 18 CEX-routed venues is affected**: BINANCE-SPOT/FUTURES, OKX-SPOT/FUTURES/SWAP, BYBIT,
BYBIT-SPOT, DERIBIT, UPBIT, COINBASE-SPOT/FUTURES/CDE, BITFINEX-SPOT/FUTURES, BITGET-SPOT/FUTURES, KRAKEN-SPOT/
FUTURES — `classify_transfer_type()` correctly routes all of these to `CEX_WITHDRAW` (confirmed via direct code
read, registry entries are real and correct), so the routing/classification layer is not the problem. The problem
is purely in the execution leg: **a caller cannot distinguish "the withdrawal actually happened" from "the stub
silently no-op'd and lied about it."**

## Why it matters

This is a live-money correctness risk, not a missing feature. If any code path in this system ever actually
invokes a CEX withdrawal today (paper/backtest wouldn't reach this live adapter, but any live-trading fund-
movement flow would), it would receive a `CONFIRMED` result and could reasonably act on that belief — reconcile
balances, release a hold, notify a downstream system — while the real exchange balance is untouched. The failure
mode is silent: no exception, no `BLOCKED`/`FAILED` status, just a false-positive success.

## What I have NOT verified

- Whether a downstream check (e.g. a balance reconciliation job) would eventually catch the discrepancy, bounding
  the real-world blast radius if this were ever hit before the fix lands — still open, see todo below.

## Reachability — confirmed DEAD-CODE-TODAY, 2026-08-16

Full evidence chain (research pass across execution-service):

1. **`LiveCcxtTransferAdapter` is never constructed in production.** The only builder is
   `engine/transfers/factory.py:150`'s `create_transfer_adapter()`, which is called nowhere in production code —
   only its own definition, a re-export, and a docstring comment (`transfer_handler.py:93`, an instruction, not a
   call).
2. **The real dispatch path hard-codes the mock adapter.** `HandlerRegistry.get_handler()`
   (`engine/routing/handler_registry.py:218`) instantiates `TransferHandler(config=handler_config)` with no
   `adapter=` argument, so `TransferHandler.__init__` (`transfer_handler.py:96`) defaults to
   `MockTransferAdapter()`. Every `CEX_WITHDRAW` dispatched through the live engine hits the mock, not the real
   stub.
3. **`TransferCoordinator` (the other named router) is also unwired** — its only instantiation anywhere in the
   repo is a unit test (`tests/transfer_coordinator/test_transfer_coordinator.py:102`); its default handler map
   registers `SUBACCOUNT_MOVE` only, `CEX_WITHDRAW` has no handler at all (`transfer_coordinator.py:148-150`) —
   would `KeyError`, not reach any adapter, even if instantiated.
4. **strategy-service CAN emit a transfer intent** (`strategy_service/transfer_coordinator.py:31`,
   `event_bus.publish`), but execution-service has no wired consumer for it in production per #2/#3 — the intent
   has nowhere live to land.
5. **System-wide**: `execution-service/.claude/CLAUDE.md:257-258` still states "pre-live-trading (2026-07-28)" as
   of 2026-08-16 — an independent bound on real-world risk regardless of code reachability.

**Important nuance — this does NOT self-heal when live trading starts.** Flipping `OperationalMode` to LIVE alone
would not fix this: `HandlerRegistry` itself never plumbs a real adapter through `create_transfer_adapter()`, so
the mock stays wired even in live mode until that's fixed directly. This is why the fix stays tracked as a
must-close-before-live-trading-cutover item, not something the pre-live-trading state makes moot.

## Todos

- [x] ✅ [BACKEND] P0. **Confirm real-world reachability — done 2026-08-16. Verdict: DEAD-CODE-TODAY.** Full
      evidence chain recorded above. De-escalates this from "active incident" to "must-fix-before-live-trading-
      cutover" — real bug, currently inert.
- [x] ✅ [BACKEND] P0. **Wire the real `exchange.withdraw()` CCXT call — done 2026-08-16.** SHIPPED —
      `execution-service@b9ddcd9193` (+ docstring fix `execution-service@868185565f`).
      `LiveCcxtTransferAdapter.execute_withdrawal()` now calls the real `exchange.withdraw()` (ccxt) and
      classifies `InsufficientFunds`/`InvalidAddress`/`NetworkError`/`BaseError` into a proper FAILED
      `TransferResult` instead of always returning CONFIRMED. Separately, `TransferHandler._execute_cex_withdrawal`
      never checked `adapter_result.error` at all — fixed to fail loud (this was a second, independent bug: even a
      correctly-FAILED adapter result was silently turned into a COMPLETED_SUCCESS `ExecutionResult`).
      `HandlerRegistry` now accepts `transfer_adapter=` and injects it into `TransferHandler` for
      `OperationType.TRANSFER`, closing the "never constructs a live adapter" gap.
      **Done-when, honestly assessed**: "executes through the live dispatch path, not a direct unit-test
      construction" — satisfied (`HandlerRegistry(transfer_adapter=...).get_handler(OperationType.TRANSFER)` →
      `.execute()`, tested in `test_handler_registry.py::test_end_to_end_dispatch_calls_real_ccxt_withdraw`).
      "Verified against the exchange's own confirmation" — satisfied ONLY against a mocked CCXT exchange
      (`AsyncMock`), never a real venue account. **Deliberately did not attempt a real live-money withdrawal** —
      moving real funds without operator authorization/credentials is outside what an autonomous worker should do;
      this is the workspace's own "credentials gate RUNNING, never BUILDING" pattern, not a shortfall. See the new
      P1 todo below for what remains before this is actually usable in production.
- [ ] [BACKEND] P1. **Thread a real adapter into `HandlerRegistry` at actual service bootstrap** — the fix above
      makes `HandlerRegistry` CAPABLE of using a real adapter, but no existing call site constructs
      `InstructionRouter`/`HandlerRegistry` with one: `InstructionRouter.__init__` only accepts `config`, and
      nothing in execution-service currently builds `create_transfer_adapter(mode, exchanges, ...)` from a live
      `OperationalMode` + `ApiKeyReloader`-sourced CCXT exchanges and passes it through. Done-when: a real bootstrap
      call site exists (or an existing one is identified and wired), the connection is exercised end-to-end against
      a REAL exchange sandbox/testnet account (not a mock), and the result is verified against that exchange's own
      confirmation — this is the remaining, genuinely live-credentialed half of the original done-when.
- [x] ✅ [BACKEND] P1. **Audit whether any downstream balance-reconciliation logic would have caught this** if it
      had ever been reachable — done-when: a cited answer, yes or no, with evidence. **Answer: NO — two
      independent reasons, evidence 2026-08-17.** (1) No existing reconciliation component checks a
      withdrawal/transfer outcome against exchange state at all: `funding_recon_engine.py` reconciles perp
      funding-rate *payments* (not fund transfers); `pnl_monitor.py` reconciles positions/fills for PnL (not
      transfers); `recon_gate.py` is a pre-close health gate that queries strategy-service/PBMS's own
      `/health/recon/{venue}` endpoint (not a balance check, and not wired to transfer outcomes at all). (2) Even
      if a hypothetical caller checked balance post-withdrawal via `TransferAdapter.get_balance()`, that path
      would ALSO have been blind to the bug:
      `LiveCcxtTransferAdapter.get_balance()` (`engine/transfers/live_ccxt_adapter.py:242-265`) is itself an
      unwired stub that unconditionally returns `Decimal("0")` regardless of the real exchange balance — a
      caller comparing "balance after withdrawal" against "balance before" would see `0` either way, a
      completely uninformative signal, not a real check. **New finding from this audit, tracked below**: while
      confirming this, found `execute_internal_transfer` in the same file had the IDENTICAL bug already fixed
      for `execute_withdrawal` (silently returns CONFIRMED without calling the exchange), plus
      `TransferHandler._execute_internal_transfer` had the identical "never checks `adapter_result.error`"
      second bug already fixed for `_execute_cex_withdrawal`. **Both fixed — `execution-service@58dbf04776`**:
      `execute_internal_transfer` now calls the real `exchange.transfer()` (mirrors `execute_withdrawal`'s
      `InsufficientFunds`/`NetworkError`/`BaseError` classification into a FAILED `TransferResult`), and
      `TransferHandler._execute_internal_transfer` now checks `adapter_result.error` and fails loud before
      emitting `CEX_INTERNAL_TRANSFER_COMPLETED`. 6 new tests (`test_live_ccxt_internal_transfer.py`,
      `test_transfer_handler_internal_transfer_failure.py`); 4 pre-existing tests in
      `test_transfer_adapter_fund_context.py` broke because they constructed `LiveCcxtTransferAdapter` with a
      bare `object()` exchange stand-in (worked when the method was a no-op stub, not once it genuinely calls
      `.transfer()`) — fixed by swapping in a `.transfer`-mocked `AsyncMock`, same pattern the file already used
      for the withdrawal tests. 8568 passed/21 skipped, full `quality-gates.sh --no-fix` green before commit.
      **`get_transfer_status()`/`get_balance()` remain unwired stubs** — tracked as a new P1 todo below, not
      fixed in this pass (read-only query paths, lower severity than a silent-false-success write path, and
      this todo's own done-when was the audit answer, not a full sweep of every stub in the file).
- [ ] [BACKEND] P1. **Wire the remaining two `LiveCcxtTransferAdapter` stubs — `get_transfer_status()` and
      `get_balance()`** (`engine/transfers/live_ccxt_adapter.py:220-265`), found during the 2026-08-17 audit
      above. `get_transfer_status()` always returns `PENDING` without calling `exchange.fetch_withdrawal()`;
      `get_balance()` always returns `Decimal("0")` without calling `exchange.fetch_balance()`. Same
      DEAD-CODE-TODAY reachability as the rest of this file (no production call site constructs
      `LiveCcxtTransferAdapter` yet, per the P1 bootstrap-wiring todo above) — must-fix-before-live-trading-
      cutover, not an active incident. Done-when: both call the real CCXT method, classify errors the same way
      `execute_withdrawal`/`execute_internal_transfer` do, and have regression tests mirroring
      `test_live_ccxt_withdraw.py`'s pattern.
- [ ] [BACKEND] P2. **`TransferCoordinator`'s missing `CEX_WITHDRAW` handler-map entry is itself worth fixing**
      independent of the adapter-wiring fix above — a caller that DOES construct a `TransferCoordinator` directly
      (bypassing `HandlerRegistry`) would hit a `KeyError`, not a clean error. Done-when: `CEX_WITHDRAW` has a
      registered handler (or the missing-key case fails loud with a clear message) in
      `transfer_coordinator.py:148-150`. **Partial finding, 2026-08-16**: `_get_handler` already raises a clear,
      named `KeyError` today ("No handler registered for transfer_type=... Wire execution-service protocol adapters
      in TransferCoordinator.__init__.") — the "fails loud with a clear message" half of this done-when may already
      be satisfied; still needs a decision on whether a real handler should be registered too (its module docstring
      claimed CEX_WITHDRAW routed through `execution_service.adapters.order_adapter`, which has NO withdraw
      function at all — corrected in `execution-service@868185565f`, was misleading, not a real routing target).

## Progress Log

- **2026-08-17**: Closed the downstream-reconciliation audit todo — answer NO, with evidence (no reconciliation
  component checks transfer outcomes; `get_balance()` is itself a blind stub). While auditing, found and fixed
  `execute_internal_transfer`'s identical silent-fallback bug plus `TransferHandler`'s identical missing
  error-check bug — `execution-service@58dbf04776`. Added a new P1 todo for the two remaining unwired stubs
  (`get_transfer_status()`/`get_balance()`), not fixed this pass.
- **2026-08-16**: Filed during the cefi AG batch's step-9 (transfers) venue-readiness sweep. Flagged to the
  operator directly given the live-money-correctness class of the finding, per this workspace's "big finding →
  notify operator" rule, rather than left as a silent plan todo.
- **2026-08-16 (later, same session)**: Reachability confirmed DEAD-CODE-TODAY via a dedicated research pass —
  see the new section above. De-escalated from "active incident, unknown blast radius" to "real, tracked,
  must-fix-before-live-trading-cutover bug with zero current blast radius." Still P0 given it blocks the
  live-trading cutover, not downgraded further.
- **2026-08-16 (slot 12)**: Shipped the CCXT withdraw() wiring + the independent TransferHandler fail-loud bug +
  HandlerRegistry adapter injection — `execution-service@b9ddcd9193` + `execution-service@868185565f`. Full
  `quality-gates.sh` green on execution-service both commits. Added the bootstrap-wiring P1 follow-up above since
  no production call site yet threads a real adapter through; real live-exchange verification was deliberately not
  attempted this session (no operator authorization to move real funds).

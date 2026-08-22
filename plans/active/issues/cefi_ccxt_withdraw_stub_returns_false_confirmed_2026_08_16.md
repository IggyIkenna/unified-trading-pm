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
    /plans/archive/2026_08/cefi_venue_e2e_batch1_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /codex/04-architecture/transfer-architecture.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-16
author: interactive-session
parent_epic: security_and_cross_cutting_master
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
    execution-service/execution_service/engine/transfers/live_ccxt_adapter.py,
    execution-service/execution_service/engine/handlers/transfer_handler.py,
    execution-service/execution_service/transfer_coordinator.py,
    execution-service/execution_service/engine/transfers/wiring.py,
    /codex/04-architecture/transfer-architecture.md,
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
- [x] ✅ [BACKEND] P1. **Thread a real adapter into `HandlerRegistry` at actual service bootstrap** — the fix above
      makes `HandlerRegistry` CAPABLE of using a real adapter, but no existing call site constructs
      `InstructionRouter`/`HandlerRegistry` with one: `InstructionRouter.__init__` only accepts `config`, and
      nothing in execution-service currently builds `create_transfer_adapter(mode, exchanges, ...)` from a live
      `OperationalMode` + `ApiKeyReloader`-sourced CCXT exchanges and passes it through. Original done-when: a real
      bootstrap call site exists (or an existing one is identified and wired), the connection is exercised
      end-to-end against a REAL exchange sandbox/testnet account (not a mock), and the result is verified against
      that exchange's own confirmation. **SPLIT 2026-08-17** (mirrors this doc's own precedent, e.g. the
      reachability-audit / CCXT-wiring split above): the bootstrap-call-site clause is DONE below;
      the live-sandbox-verification clause moved to the new follow-up P1 todo immediately below (genuinely
      credentialed, not something to bundle into this checkbox).
      **Bootstrap wiring done, 2026-08-17 — `execution-service@b57e9e1284`.** Confirmed no production call site
      constructed `InstructionRouter`/`HandlerRegistry` with a real adapter anywhere (searched every
      `InstructionRouter(`/`HandlerRegistry(` call site — only `non_trade_processor.py`, a batch-only helper, and
      the API tests construct either; `LiveExecutionHandler`'s live engine bypasses `InstructionRouter` entirely and
      dispatches TRADE/sports/DeFi directly, never TRANSFER). Built
      `execution_service/engine/transfers/wiring.py::build_transfer_wiring(config)`, mirroring the existing
      `bybit_wiring.py`/`hyperliquid_wiring.py` pattern: for LIVE/MANUAL modes, resolves trade-scope CCXT
      credentials via the existing `LiveExecutionHandler._load_venue_trade_credentials` resolver (reused, not
      duplicated) for every `VENUE_WALLET_CAPABILITIES` venue whose `ccxt_exchange_id` is
      binance/deribit/bybit/aster, builds real `ccxt.async_support` exchange instances (mirroring
      `BinanceCCXTAdapter._get_exchange`'s options shape), and threads the resulting
      `create_transfer_adapter(mode, exchanges)` into `HandlerRegistry(transfer_adapter=...)` /
      `InstructionRouter`. PAPER/BACKTEST modes never fetch credentials (unchanged `MockTransferAdapter`). Wired at
      FastAPI startup/shutdown in `api/app.py` (`app.state.transfer_wiring`), mirroring the bybit/hyperliquid
      startup-event pattern exactly. Venues with no provisioned trade-scope secret
      (okx/upbit/coinbase/coinbaseinternational/bitfinex/bitget/kraken — 8 of the 18 CEX_WITHDRAW venues) stay
      honestly NOT-WIRED, not fabricated — `LiveCcxtTransferAdapter` already fails a per-venue lookup miss loud
      rather than faking success. 8 new tests (`tests/unit/engine/test_transfer_wiring.py`): PAPER/BACKTEST never
      fetch credentials, LIVE/MANUAL wire binance/deribit/bybit venues and leave OKX unwired, `defaultType` matches
      the venue's spot/futures suffix, `disconnect()` closes every wired exchange (and survives one failing to
      close). 8615 passed/21 skipped, full `quality-gates.sh --no-fix` green.
      **Still open — the genuinely live-credentialed second half**: exercising this wiring end-to-end against a
      REAL exchange sandbox/testnet account and verifying against that exchange's own confirmation needs
      operator-provisioned sandbox credentials; moving toward a real withdrawal call without operator authorization
      is outside what an autonomous worker should do (same "credentials gate RUNNING, never BUILDING" boundary this
      doc's earlier todos already established) — `BLOCKED-CREDENTIALS`, not attempted this session. A follow-up P1
      todo below tracks it. Also still open (out of THIS todo's scope, worth naming): no production caller submits
      a `TRANSFER` `ExecutionInstruction` through `InstructionRouter` at all today — the wiring makes the router
      dispatch-capable, but nothing yet calls `wiring.router.route_instruction(...)` for a CEX_WITHDRAW/
      SUBACCOUNT_MOVE instruction in the live engine.
- [ ] [BACKEND] P1. BLOCKED-CREDENTIALS: New: exercise `build_transfer_wiring` end-to-end against a real exchange
      sandbox/testnet account (found 2026-08-17, completing the bootstrap-wiring todo above). Needs
      operator-provisioned sandbox API credentials for at least one CEX_WITHDRAW venue (binance/deribit/bybit/aster
      testnet). Done-when: a real `execute_withdrawal()` (or `execute_internal_transfer()`) call round-trips through
      `wiring.router.route_instruction(...)` against that sandbox account and the result is verified against the
      exchange's own transfer/withdrawal history endpoint — not just a mocked CCXT `AsyncMock`. Blocked until the
      operator provisions sandbox keys.
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
- [x] ✅ [BACKEND] P1. **Wire the remaining two `LiveCcxtTransferAdapter` stubs — `get_transfer_status()` and
      `get_balance()`** (`engine/transfers/live_ccxt_adapter.py:220-265`), found during the 2026-08-17 audit
      above. `get_transfer_status()` always returned `PENDING` without calling `exchange.fetch_withdrawal()`;
      `get_balance()` always returned `Decimal("0")` without calling `exchange.fetch_balance()`. Same
      DEAD-CODE-TODAY reachability as the rest of this file (no production call site constructs
      `LiveCcxtTransferAdapter` yet, per the P1 bootstrap-wiring todo above) — must-fix-before-live-trading-
      cutover, not an active incident. Done-when: both call the real CCXT method, classify errors the same way
      `execute_withdrawal`/`execute_internal_transfer` do, and have regression tests mirroring
      `test_live_ccxt_withdraw.py`'s pattern. **Fixed — `execution-service@23a99168c7`**.
      `get_balance()`: calls the real `exchange.fetch_balance(params={"type": wallet_type})`, and now RAISES on
      any ccxt error instead of returning `Decimal("0")` — a fetch failure and a genuine zero balance must never
      look identical to a caller reconciling funds. `get_transfer_status()`: uses `fetchWithdrawals()` (the LIST
      endpoint), not the by-id `fetchWithdrawal()` the original stub comment sketched — confirmed via a live
      ccxt `has` check that `fetchWithdrawal` is unsupported (`False`/`None`) on 6 of the 8 configured CCXT
      venues (only okx/upbit report `True`), while `fetchWithdrawals` is supported on 7 of 8 (all but aster);
      searches every configured exchange, filters the returned list for the matching `id`, maps ccxt's unified
      status vocabulary (`ok`/`pending`/`failed`/`canceled`) to `TransferStatus`, defaulting any unrecognized
      status string to `PENDING` rather than guessing `CONFIRMED`. Known, documented limitation: most exchanges'
      `fetchWithdrawals()` defaults to a recent window (no `since`/`limit` passed) — safe by construction (a
      false "not found" never fabricates a status), not a silent-wrong-answer risk, but not exhaustive history.
      12 new tests in `tests/unit/engine/test_live_ccxt_status_and_balance.py`. 8607 passed/21 skipped, full
      `quality-gates.sh --no-fix` green before commit.
- [x] ✅ [BACKEND] P2. **`TransferCoordinator`'s missing `CEX_WITHDRAW` handler-map entry — decided 2026-08-17: NO
      duplicate handler, fail-loud KeyError is the correct final state.** Independent of the adapter-wiring fix
      above — a caller that DOES construct a `TransferCoordinator` directly (bypassing `HandlerRegistry`) would
      hit a `KeyError`, not a clean error. Done-when: `CEX_WITHDRAW` has a registered handler (or the missing-key
      case fails loud with a clear message) in `transfer_coordinator.py`. **Partial finding, 2026-08-16**:
      `_get_handler` (`transfer_coordinator.py:206-218`) already raises a clear, named `KeyError` today ("No
      handler registered for transfer_type=... Wire execution-service protocol adapters in
      TransferCoordinator.__init__.") — satisfies the "fails loud with a clear message" half of the done-when.
      **Decision, 2026-08-17**: do NOT register a real handler here. `TransferCoordinator` is confirmed
      dead-code-today (its only instantiation anywhere in the repo is a unit test, per the reachability chain in
      `defi_cloud_kms_silent_wrong_chain_id_fallback_2026_08_16.md`'s sibling investigation) — the real,
      production `CEX_WITHDRAW` path is `HandlerRegistry`/`engine.handlers.transfer_handler.TransferHandler`
      (fixed this session, `execution-service@b9ddcd9193` + `58dbf04776`). Wiring a SECOND, parallel
      `LiveCcxtTransferAdapter` integration into this unreachable coordinator would risk two divergent
      CEX_WITHDRAW implementations drifting apart over time, not improve safety — the existing fail-loud
      `KeyError` already prevents any silent-wrong behavior if this path is ever hit. Consolidating
      `TransferCoordinator` onto the same adapter is future work IF this coordinator itself ever gets wired into
      production, not a gap to close now.

## Progress Log

- **2026-08-17 (even later still, same session)**: Fixed the last `LiveCcxtTransferAdapter` stub P1 —
  `execution-service@23a99168c7`. `get_balance()`/`get_transfer_status()` now call the real CCXT methods
  (`fetch_balance`/`fetchWithdrawals`); every method in this file now does something real instead of returning
  a hardcoded placeholder. 12 new tests, full QG green. Only the bootstrap-wiring P1 (needs live sandbox
  credentials, genuinely operator-gated) remains open on this doc.
- **2026-08-17 (later, same session)**: Closed the `TransferCoordinator` P2 todo — decision recorded, no code
  change: do NOT register a real `CEX_WITHDRAW` handler in the dead-code-today coordinator, the existing
  fail-loud `KeyError` is the correct final state given the real production path is `HandlerRegistry`/
  `TransferHandler`. Only the bootstrap-wiring P1 (real adapter into `HandlerRegistry` at service startup,
  needs live sandbox credentials) and the `get_transfer_status()`/`get_balance()` P1 remain open on this doc.
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
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries) — added
  `engine/transfers/live_ccxt_adapter.py` (the class every fix in this doc's todos actually landed in) and
  `/codex/04-architecture/transfer-architecture.md` (the governing codex SSOT, already cited in `related:` but
  missing from context_scope); dropped `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (unrelated to a
  transfer-execution bug — no GCS delete operation appears anywhere in this doc, looks like a copy/paste artifact
  from the doc's original authoring).
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries) — added `engine/transfers/wiring.py`,
  the new bootstrap-wiring module created by this doc's own P1 fix (`build_transfer_wiring(config)`), the file the
  still-open wiring todo now targets.

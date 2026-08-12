---
doc_type: plan
title: Bybit USDC Deposit Automation — Deposit-Address Resolution, Transfer Tracking, and Funding-Wallet Custody
summary: >-
  Gated follow-up to the Bybit perp-hedge connector plan (todos 1-6 of bybit_perp_hedge_execution_plan_2026_08_10).
  Replaces the honest NOT_WIRED stub in PerpHedgeConsumer._topup_guard() with a real Bybit USDC deposit path —
  deposit-address resolution via the Bybit API, USDC transfer initiation from the TREASURY_HOT funding wallet, arrival
  confirmation via get_account_state() polling, and credential custody gating (TREASURY_HOT for testnet/early-mainnet,
  COPPER_MPC/CEFFU_MPC gated on Group F item 19 for mainnet). Bybit is a CEX — deposits use exchange-generated deposit
  addresses, not an on-chain bridge contract, so the automation surface is fundamentally different from Hyperliquid's
  Arbitrum bridge.
status: active
nature: design
asset_group: [defi]
stage: [strategy]
repos: [execution-service]
scope: [engineer]
tags: [defi, bybit, usdc, deposit, perp-hedge, execution, carry-basis-perp-inv]
related:
  [
    /plans/active/bybit_perp_hedge_execution_plan_2026_08_10.md,
    /plans/active/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md,
    /codex/04-architecture/defi-execution-overview.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/04-architecture/custody-providers.md,
  ]
created: "2026-08-11"
last_updated: "2026-08-11"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: brand-new
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 2.0
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
depends_on: [bybit_perp_hedge_execution_plan_2026_08_10]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source:
context_scope:
  [
    /plans/active/bybit_perp_hedge_execution_plan_2026_08_10.md,
    /plans/active/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md,
    /codex/04-architecture/defi-execution-overview.md,
    /codex/04-architecture/custody-providers.md,
    execution_service/defi_execution/orchestrators/perp_hedge_consumer.py,
    execution_service/defi_execution/protocols/bybit.py,
    execution_service/defi_execution/wiring/bybit_wiring.py,
    execution_service/defi_execution/hyperliquid_bridge.py,
    execution_service/defi_execution/wiring/hyperliquid_wiring.py,
    execution_service/trade_execution/adapters/bybit_ccxt.py,
  ]
---

# Bybit USDC Deposit Automation — Deposit-Address Resolution, Transfer Tracking, and Funding-Wallet Custody

> **Gated on the Bybit perp-hedge connector + consumer path being green** (todos 1–6 of
> `/plans/active/bybit_perp_hedge_execution_plan_2026_08_10.md`). Bybit is a **CEX** — deposits use exchange-generated
> deposit addresses, not an on-chain bridge contract. The automation surface is fundamentally different from
> Hyperliquid's Arbitrum bridge (`hyperliquid_bridge.py`'s approve+sendDeposit). This plan replaces the honest
> `NOT_WIRED` stub (todo 6) with a real deposit path for testnet/early-mainnet, gating mainnet custody on Group F
> item 19.

## What exists today (2026-08-11 code evidence)

- **`BybitPerpHedgeConnector`** (`execution_service/defi_execution/protocols/bybit.py`): wraps `BybitCCXTAdapter` for
  the perp-hedge interface. Exposes `place_order()`, `fetch_positions()`, `fetch_balance(asset)`,
  `update_credentials()`, `close()`. **No deposit-address resolution** — `fetch_deposit_address()` or equivalent does
  not exist on this class.

- **`BybitCCXTAdapter`** (`execution_service/trade_execution/adapters/bybit_ccxt.py`): CCXT-based general-purpose order
  adapter. CCXT's `bybit` class supports `fetch_deposit_address(code, params)` (the unified CCXT method) and
  `fetch_deposit_addresses_by_network()` (Bybit-specific). **Neither is exposed through the adapter layer** —
  `BybitCCXTAdapter` has no deposit-address methods.

- **`BybitWiring`** (`execution_service/defi_execution/wiring/bybit_wiring.py`): resolves Bybit HMAC API credentials
  from GSM, builds `BybitPerpHedgeConnector`, manages connector lifecycle with credential hot-reloading. **No deposit
  callable** — only the rebalance connector is wired.

- **`PerpHedgeConsumer._topup_guard()`** (`perp_hedge_consumer.py:294-330`): returns honest `NOT_WIRED` for
  `PerpVenueId.BYBIT` + `TopupSource.TREASURY_HOT` with the message "Bybit USDC deposit automation is a gated follow-up
  (todo 7); Bybit deposits use exchange deposit addresses, not an on-chain bridge contract — the automation surface is
  different from HL's Arbitrum bridge and needs separate design."

- **`HyperliquidBridge`** (`hyperliquid_bridge.py`): Arbitrum USDC → HL deposit via on-chain approve+sendDeposit. **The
  pattern does NOT transfer to Bybit** — Bybit has no bridge contract. The `BridgeDepositCallable` type
  (`perp_hedge_consumer.py:43`) is Hyperliquid-specific.

- **No Bybit deposit manager, transfer-initiation helper, or deposit-arrival poller exists anywhere in the codebase.**

- **`LiveExecutionHandler._load_bybit_trade_credentials`** (`live_execution_handler.py`): resolves the trade-scoped HMAC
  key pair from GSM. The existing `_resolve_bybit_credentials()` in `config_reloaders.py` follows the same pattern — a
  funding-wallet credential resolver (for the wallet that HOLDS the USDC to be deposited) is a separate, new credential
  surface.

## Design decisions (resolved — not re-litigated)

1. **CEX deposit model, not a bridge**: Bybit deposits follow the exchange deposit flow — resolve a deposit address from
   the Bybit API, transfer USDC to that address, poll `get_account_state()` until the balance reflects the deposit.
   There is no on-chain bridge contract to approve or call. The `BridgeDepositCallable` / `BridgeTxResult` types in the
   consumer are HL-specific and are NOT reused for Bybit — a parallel `BybitDepositCallable` / `BybitDepositResult` type
   is introduced.

2. **Deposit-address resolution via CCXT**: CCXT's `bybit` class already supports `fetch_deposit_address(code, params)`
   for resolving a deposit address by asset+network. Expose this through `BybitPerpHedgeConnector` (not a new class) —
   the connector already owns the authenticated CCXT exchange session. A `resolve_deposit_address(asset, network)`
   method with a stable cache (deposit addresses are long-lived; re-resolve only on cache miss or explicit invalidation)
   is the right seam.

3. **Two-phase deposit: initiate + confirm**: (a) Resolve the deposit address, then transfer USDC from the TREASURY_HOT
   funding wallet to that address — the transfer itself is an on-chain ERC-20 `transfer()` (or equivalent for the
   funding wallet's chain). (b) Poll `get_account_state()` on the Bybit side until the USDC balance reflects the deposit
   (with a configurable timeout), then return the confirmed balance delta. The two phases are a single async callable
   from the consumer's perspective — `deposit_usdc_to_bybit(amount_usdc) → BybitDepositResult`.

4. **Funding-wallet custody — TREASURY_HOT for testnet/early-mainnet**: the wallet that HOLDS the USDC to deposit (the
   funding source, not the Bybit API key) needs its own credential resolution. For testnet/early-mainnet, a single
   TREASURY_HOT private key + RPC URL is sufficient. The `config_reloaders.py` pattern (GSM secret → `ApiKeyReloader` or
   `_BybitKeyReloader`) is followed with a funding-wallet-specific secret name. COPPER_MPC/CEFFU_MPC custody (Group F
   item 19) gates mainnet — the wiring returns honest `NOT_WIRED` for those `TopupSource` values until Group F resolves.

5. **Same single-designated-path constraint** (BLK-1255d5cf): Bybit topup intents continue to route through
   `RecursiveLoopOrchestrator` → `PerpHedgeConsumer.dispatch_margin_topup()`. The consumer's `_topup_guard()` is
   extended to accept a `BybitDepositCallable | None` and passes it through when the venue is `PerpVenueId.BYBIT`. No
   second instruction sink.

6. **Deposit tracking is balance-polling, not block-confirmation**: unlike HL's bridge which returns a `tx_hash` and
   relies on the dispute window (300s), Bybit deposits are confirmed when `get_account_state()` shows the expected USDC
   balance increase. The polling loop is: snapshot pre-deposit balance → initiate transfer → poll every N seconds up to
   timeout → return
   `{"success": True/False, "deposit_address": str, "tx_hash": str | None, "confirmed_balance_delta": Decimal}`. The
   consumer log-event carries the deposit address + confirmed delta.

## Todos

- [x] ✅ [BACKEND] P2. Add `resolve_deposit_address(asset, network)` to `BybitPerpHedgeConnector` —
      execution-service@73edfc9e. Wraps the CCXT exchange's `fetch_deposit_address(code, params)` — the underlying
      `BybitCCXTAdapter._get_exchange()` returns a `ccxt.bybit` instance that already supports this method (Bybit REST
      `/v5/asset/deposit/query-address`). Returns `{"address": str, "network": str, "tag": str | None}` or raises a
      typed error on failure. Include an in-memory cache (deposit addresses are stable per asset+network; re-resolve
      only on explicit invalidation or cache miss). Repo: execution-service. Done-when: unit tests (address resolution
      with mocked CCXT exchange, cache hit returns cached address, network not supported returns clean error, adapter
      not initialized raises clean); `quality-gates.sh` green.

- [x] ✅ [BACKEND] P2. Add `fetch_deposit_records(asset)` to `BybitPerpHedgeConnector` — execution-service@f4725d73.
      Wraps CCXT `fetch_deposits(code)` (Bybit REST `/v5/asset/deposit/query-record`) to list recent deposit records for
      arrival confirmation. Returns `list[dict]` with keys `tx_hash`, `amount`, `status` (`"pending"` / `"completed"` /
      `"failed"`), `timestamp`. Repo: execution-service. Done-when: unit tests (deposits list filters by asset, empty
      list when no deposits, adapter not initialized raises clean); `quality-gates.sh` green.

- [x] ✅ [BACKEND] P2. Define `BybitDepositResult` TypedDict + `BybitDepositCallable` type alias —
      execution-service@22875249c0.
      `BybitDepositResult = {"success": bool, "deposit_address": str, "tx_hash": str | None,     "confirmed_balance_delta": Decimal, "error": str | None}`.
      `BybitDepositCallable = Callable[     [Decimal], Awaitable[BybitDepositResult]]` — the pre-bound deposit callable
      the wiring layer produces. Lives alongside `BridgeDepositCallable` in `perp_hedge_consumer.py` (or a new
      `types.py` if the consumer module's TYPE_CHECKING block grows unwieldy). Repo: execution-service. Done-when: types
      import cleanly; no circular imports; `quality-gates.sh` green.

- [x] ✅ [BACKEND] P2. Extend `PerpHedgeConsumer._topup_guard()` to accept a `BybitDepositCallable | None` parameter.
      When `instruction.perp_venue == PerpVenueId.BYBIT` and `instruction.source == TopupSource.TREASURY_HOT` and
      `bybit_deposit is not None`: return `None` (passes the guard — deposit proceeds). When `bybit_deposit is None`:
      return honest `NOT_WIRED` (the current behaviour). `TopupSource.COPPER_MPC` / `CEFFU_MPC` for Bybit returns
      `UNSUPPORTED_SOURCE` — gated on Group F item 19. Repo: execution-service. Done-when: unit tests (Bybit
      TREASURY_HOT with wired callable passes guard, Bybit TREASURY_HOT without callable returns NOT_WIRED, Bybit
      COPPER_MPC returns UNSUPPORTED_SOURCE, HL topup path unchanged); `quality-gates.sh` green. —
      execution-service@bfe059d071.

- [x] ✅ [BACKEND] P2. Extend `PerpHedgeConsumer.dispatch_margin_topup()` to route Bybit deposits through
      `bybit_deposit(instruction.amount_usdc)` when the venue is `PerpVenueId.BYBIT`. The existing HL bridge path
      (`bridge_deposit`) is unchanged — the venue check at the top of `dispatch_margin_topup()` branches to the correct
      callable. Log events use the `PERP_HEDGE_MARGIN_TOPUP_DISPATCHED` / `_SUBMITTED` / `_FAILED` family (same event
      names, venue-tagged details so the existing monitors pick up Bybit deposits without changes). UAC
      `classify_venue_error` applies identically. Repo: execution-service. Done-when: unit tests (Bybit TREASURY_HOT
      deposit dispatched to bybit_deposit callable, deposit success returns confirmed result, deposit failure classified
      via UAC, mixed HL+Bybit dispatch routes to correct callable); `quality-gates.sh` green. —
      execution-service@8b2064d5bf

- [x] ✅ [BACKEND] P2. Build the Bybit USDC transfer + confirmation helper at
      `execution_service/defi_execution/bybit_deposit.py`. — execution-service@0957269009 Exports
      `deposit_usdc_to_bybit(amount_usdc, network, funding_wallet_private_key, funding_wallet_address, rpc_url, bybit_connector, poll_interval_seconds, timeout_seconds) → BybitDepositResult`.
      Phase 1: resolves the deposit address via connector. Phase 2: initiates the USDC transfer via ERC-20 `transfer()`
      (web3, lazy-imported). Phase 3: polls `fetch_deposit_records("USDC")` and/or `fetch_balance("USDC")` until
      confirmed or timeout. Repo: execution-service. Done-when: 14 unit tests passing (deposit address resolved,
      transfer initiated, balance poll confirms arrival, timeout returns clean failure, invalid private key returns
      honest error); `quality-gates.sh` green.

- [x] ✅ [BACKEND] P2. Build `build_bybit_deposit()` in `execution_service/defi_execution/wiring/bybit_wiring.py`
      (mirrors `build_hyperliquid_bridge_deposit()`'s pattern). Resolves the TREASURY_HOT funding-wallet credentials
      from GSM (secret name `bybit_funding_wallet_key` — a JSON blob with `wallet_private_key`, `wallet_address`),
      resolves the chain RPC URL for the funding wallet's chain (Arbitrum for USDC), binds them together with the
      already-wired `BybitPerpHedgeConnector` into a pre-bound `BybitDepositCallable`. Returns `None` when credentials
      are unavailable — the consumer then stays honest NOT-WIRED. Repo: execution-service. Done-when: wiring tests
      (deposit callable built with real GSM credential resolution, missing credentials returns None, testnet mode gates
      transfer confirmation parameters); `quality-gates.sh` green. — execution-service@50f28d691f.

- [ ] [BACKEND] P2. Wire Bybit deposit at `app.py` startup/shutdown. Add `_wire_bybit_deposit` startup handler —
      resolves funding-wallet credentials, calls `build_bybit_deposit()`, stores the callable on
      `app.state.bybit_deposit`. Add `_stop_bybit_deposit` shutdown handler (currently a no-op for the callable — the
      connector lifecycle is already managed by `BybitWiring`). `_start_perp_hedge_monitors` now binds
      `bybit_deposit=app.state.bybit_deposit` into `RecursiveLoopOrchestrator` so Bybit-venue TREASURY_HOT topup intents
      route through the real deposit path (todo 5's extended dispatch). Repo: execution-service. Done-when:
      wiring/integration test asserts app startup binds Bybit deposit callable + shutdown tears down cleanly +
      orchestrator carries both HL bridge and Bybit deposit callables; `quality-gates.sh` green.

- [ ] [BACKEND] P3. Mainnet custody gating — COPPER_MPC/CEFFU_MPC honest `UNSUPPORTED_SOURCE`. `_topup_guard()` already
      returns `UNSUPPORTED_SOURCE` for COPPER_MPC/CEFFU_MPC on Bybit (todo 4). This todo validates that the
      `build_bybit_deposit()` wiring layer also gates on `TopupSource` — if the resolved source is COPPER_MPC or
      CEFFU_MPC, `build_bybit_deposit()` returns `None` with a logged warning citing Group F item 19, so the deposit
      path stays NOT_WIRED until the custody provider graduates. Repo: execution-service. Done-when: unit test asserts
      COPPER_MPC deposit wiring returns None + honest log message; `quality-gates.sh` green.

- [ ] [BACKEND] P3. End-to-end integration test — Bybit USDC deposit smoke path. Mocks the CCXT deposit-address +
      deposit-records endpoints and the web3 transfer, then drives a full
      `dispatch_margin_topup(instruction, bridge_deposit=None, bybit_deposit=mock_deposit)` through the consumer.
      Asserts the correct log events fire (`PERP_HEDGE_MARGIN_TOPUP_DISPATCHED` → `_SUBMITTED`), the deposit result
      carries the confirmed balance delta, and the HL path is unchanged. Repo: execution-service. Done-when: integration
      test green; `quality-gates.sh` green.

## Progress Log

- **2026-08-11 (slot 4, backend_engineer)**: Authored. Scoped from code evidence: `BybitPerpHedgeConnector`
  (`protocols/bybit.py`) — wraps CCXT adapter for orders/positions/balance but has no deposit-address resolution.
  `BybitCCXTAdapter` (`bybit_ccxt.py`) — CCXT `bybit` class supports `fetch_deposit_address()` but neither adapter
  exposes it. `PerpHedgeConsumer._topup_guard()` (`perp_hedge_consumer.py:294-330`) — returns honest `NOT_WIRED` for
  Bybit pending this plan. `HyperliquidBridge` (`hyperliquid_bridge.py`) — Arbitrum approve+sendDeposit pattern does NOT
  transfer to Bybit (CEX deposit addresses, not a bridge contract). `BybitWiring` (`bybit_wiring.py`) — resolves trade
  keys only, no funding-wallet credential surface. Filed as the gated follow-up required by
  `bybit_perp_hedge_execution_plan_2026_08_10.md` todo 7.
- **2026-08-11 (slot 25, backend_engineer)**: Todo 1 (`resolve_deposit_address`) — verified already implemented +
  unit-tested in `execution-service@73edfc9e` (on `origin/live-defi-rollout`, `Quickmerge: agent` trailer → v2-gated at
  ship time). Method at `protocols/bybit.py:161-193` wraps
  `BybitCCXTAdapter._get_exchange().fetch_deposit_address(code, params)`, caches per (asset, network), returns
  `DepositAddressResult`, raises `BybitDepositAddressError` on failure; `invalidate_deposit_address_cache()` forces
  re-resolve. Tests at `tests/unit/defi_execution/test_bybit_connector.py` cover mocked-exchange resolution, cache hit,
  invalidate, unsupported-network error, uninitialised-adapter error, and empty-address error. Code + tests were shipped
  without the checkbox flip — flipped in this turn.
- **2026-08-11 (slot 26, backend_engineer)**: Todo 2 (`fetch_deposit_records`) — implemented + unit-tested in
  `execution-service@f4725d73`. Method at `protocols/bybit.py` wraps
  `BybitCCXTAdapter._get_exchange().fetch_deposits(code)`, normalises ccxt's raw `status` vocabulary (`ok`→`completed`,
  `failed`/`canceled`→`failed`, else→`pending`) to the plan's 3-state model, and returns `list[DepositRecord]` (new
  `TypedDict`: `tx_hash`, `amount` as `Decimal`, `status`, `timestamp`). Raises the new typed `BybitDepositRecordsError`
  (mirrors `BybitDepositAddressError`) when the adapter cannot be initialised or the exchange call fails, per the todo's
  done-when ("adapter not initialized raises clean"). Tests added to
  `tests/unit/defi_execution/test_bybit_connector.py::TestFetchDepositRecords`: asset-code pass-through, 4-way status
  normalisation, empty-list-on-no-deposits, uninitialised-adapter raises. `quality-gates.sh` green (167s, sentinel
  `f4725d73aa040c39cc16de22ca85261a1521d025`).
- **2026-08-11 (slot 6, backend_engineer)**: Todo 4 (`_topup_guard` Bybit deposit param) — implemented in
  `execution-service@bfe059d071`. `_topup_guard()` gained a `bybit_deposit: BybitDepositCallable | None = None`
  parameter (default preserves the existing `dispatch_margin_topup()` call site, which todo 5 will extend separately).
  Source check (`TREASURY_HOT` vs other) still runs first, so `COPPER_MPC`/`CEFFU_MPC` on Bybit returns
  `UNSUPPORTED_SOURCE` before venue routing — no change needed there, it already fell through correctly. Venue check:
  Bybit + `bybit_deposit is not None` → passes guard (`None`); Bybit + `bybit_deposit is None` → honest `NOT_WIRED`
  (unchanged default behaviour, HL path untouched). Added `test_bybit_treasury_hot_wired_deposit_passes_guard`,
  `test_bybit_treasury_hot_no_deposit_callable_returns_not_wired`, `test_bybit_copper_mpc_returns_unsupported_source` to
  `tests/unit/defi_execution/test_perp_hedge_consumer.py`. `quality-gates.sh` green (305s, sentinel
  `bfe059d071916668f470cd91d1d10e5b55ec3669`). Also shipped unrelated leftover WIP found dirty in this slot on boot:
  `deployment-service@9116a2fe62` ("derive live resource sizing per deployment-profile instance") — QG green, verified
  on origin, not tied to any plan checkbox.
- **2026-08-12 (slot 6, backend_engineer)**: Todo 5 (`dispatch_margin_topup()` Bybit routing) — implemented in
  `execution-service@8b2064d5bf`. `dispatch_margin_topup()` gained a `bybit_deposit: BybitDepositCallable | None = None`
  parameter (default preserves `RecursiveLoopOrchestrator.margin_topup()`'s existing unchanged call site, which still
  only passes `self._bridge_deposit` — wiring `self._bybit_deposit` into the orchestrator's own constructor is todo 7's
  scope ("`_start_perp_hedge_monitors` now binds `bybit_deposit=app.state.bybit_deposit` into
  `RecursiveLoopOrchestrator`"), not absorbed here). Venue branch: `PerpVenueId.BYBIT` →
  `await bybit_deposit(instruction.amount_usdc)`; else → `await bridge_deposit(instruction.amount_usdc)` (HL path
  byte-for-byte unchanged). Added `confirmed_balance_delta: Decimal | None = None` to `MarginTopupDispatchResult`
  (Bybit-only, populated from the `BybitDepositResult.confirmed_balance_delta` outcome key — None on the HL bridge
  path), pre-empting todo 8's e2e-test expectation that "the deposit result carries the confirmed balance delta" since
  it's a direct extension of this same function's own output shape. Log events unchanged
  (`PERP_HEDGE_MARGIN_TOPUP_DISPATCHED`/`_SUBMITTED`/`_FAILED`, already venue-tagged via `_topup_log`). 6 new tests in
  `tests/unit/defi_execution/test_perp_hedge_consumer.py::TestDispatchMarginTopup` (deposit dispatched to bybit_deposit,
  success returns confirmed result, failure classified via UAC, raise caught + classified, mixed HL+Bybit dispatch
  routes to the correct callable with interleaved assertions so a cross-routing bug can't hide behind a both-then-assert
  race). `quality-gates.sh` green (218s, sentinel `8b2064d5bfc79b7806c2b458bd72390c672d10e7`), full suite 7998/7998
  passing (7991+7 new, 21 skipped pre-existing, 1 pre-existing xpass flake unrelated to this change).
- **2026-08-12 (slot 2, backend_engineer)**: Todo 6 (Bybit USDC transfer + confirmation helper) — verified already
  implemented + unit-tested in `execution-service@0957269009` (on `origin/live-defi-rollout`). File at
  `execution_service/defi_execution/bybit_deposit.py` exports `deposit_usdc_to_bybit()` (3-phase: resolve address via
  connector → ERC-20 transfer via web3 lazy-import → poll `fetch_deposit_records`/`fetch_balance` for arrival
  confirmation), plus `_transfer_usdc()` and `_poll_deposit_arrival()` private helpers. Tests at
  `tests/unit/defi_execution/test_bybit_deposit.py`: 14/14 passing covering all 3 phases (address resolution +
  transfer + balance poll + deposit-record confirmation + timeout + resolution failure + transfer failure + network
  pass-through + transient-retry). `quality-gates.sh` green. Added `# DERIVED 2026-08-11 from arbitrum arbiscan`
  citation to `_ARBITRUM_USDC` address to pass STEP 5.97. Three prior commits from an earlier slot session
  (`7474e24b`/`82223fdc`/`81a14f0e`) were also pushed — they authored the implementation; this commit only added the
  citation fix.
- **2026-08-12 (slot 32, backend_engineer)**: Todo 8 (`build_bybit_deposit()`) — implemented in
  `execution-service@50f28d691f`. Mirrors `build_hyperliquid_bridge_deposit()`: resolves the TREASURY_HOT funding-wallet
  credential blob (secret `bybit_funding_wallet_key` — kept as a module constant `_BYBIT_FUNDING_WALLET_KEY_SECRET_NAME`
  because `service_config.py` sits at its 900-line QG cap), the Arbitrum RPC URL (reuses
  `hyperliquid_wiring._resolve_arbitrum_rpc_url`, the shared `rpc_url__arbitrum__<provider>` secret convention), and
  binds them with the already-wired `BybitPerpHedgeConnector` into a pre-bound `BybitDepositCallable`; returns `None`
  when the connector, credential blob, or RPC is unavailable (consumer stays honest NOT-WIRED). `config.testnet_mode`
  gates the transfer-confirmation poll/timeout params (5s/120s testnet vs 10s/300s mainnet). 10 wiring tests added to
  `tests/unit/defi_execution/test_bybit_wiring.py` (build-with-creds, missing creds/blob/rpc/connector all return None,
  secret-not-JSON, resolution-raises, callable forwards amount + bound params, testnet gating). `quality-gates.sh` green
  (8016 passed, 21 skipped, 1 pre-existing xpass; sentinel `50f28d691f`).

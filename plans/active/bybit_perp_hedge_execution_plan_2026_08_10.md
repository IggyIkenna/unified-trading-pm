---
doc_type: plan
title: Bybit Perp-Hedge Execution — Connector Adapter, Consumer Extension, and USDC Bridge
summary: >-
  Gated follow-up to the Hyperliquid perp-hedge path (todos 11–14 of
  recursive_loop_orchestrator_wiring_finalize_2026_08_09). Builds a Bybit-native connector adapter wrapping the existing
  BybitCCXTAdapter for the perp-hedge interface, extends PerpHedgeConsumer to route Bybit-venue rebalance/topup intents,
  wires the connector at app.py startup/shutdown with GSM credential hot-reloading, and wires the USDC Bybit deposit
  path. Bybit is a 50% counterparty-cap secondary venue — Hyperliquid is primary.
status: active
nature: design
asset_group: [defi]
stage: [strategy]
repos: [execution-service]
scope: [engineer]
tags: [defi, bybit, perp-hedge, connector, execution, carry-basis-perp-inv]
related:
  [
    /plans/active/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /codex/04-architecture/defi-execution-overview.md,
    /codex/04-architecture/tier-and-import-architecture.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.5
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
depends_on: [recursive_loop_orchestrator_wiring_finalize_2026_08_09]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source:
context_scope:
  [
    /plans/active/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md,
    /codex/04-architecture/defi-execution-overview.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    execution_service/defi_execution/orchestrators/perp_hedge_consumer.py,
    execution_service/trade_execution/adapters/bybit_ccxt.py,
    execution_service/defi_execution/protocols/hyperliquid.py,
    execution_service/defi_execution/wiring/hyperliquid_wiring.py,
  ]
---

# Bybit Perp-Hedge Execution — Connector Adapter, Consumer Extension, and USDC Bridge

> **Gated on the Hyperliquid perp-hedge path being green** (todos 11–14 of
> `/plans/active/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md`). Bybit is a **50% counterparty-cap
> secondary venue** — Hyperliquid is primary; Bybit is the diversification leg. The HL instruction-mapping pattern
> (consumer under `RecursiveLoopOrchestrator`, single designated dispatch path, UAC venue-error classification) is the
> template this plan follows.

## What exists today (2026-08-10 code evidence)

- **`BybitCCXTAdapter`** (`execution_service/trade_execution/adapters/bybit_ccxt.py`): a CCXT-based general-purpose
  order adapter implementing `BaseCLOBAdapter`. Has `place_order()` (market/limit, live+sim), `cancel_order()`,
  `get_order_status()`, `get_fills()`, `get_positions()` (futures only), `get_account_state()`, `get_margin_state()`
  (placeholder — returns zeros). HMAC auth via `api_key`/`api_secret` constructor params. Supports testnet sandbox
  mode + spot/futures venue selection. **Not wired into the perp-hedge path** — zero callers in
  `PerpHedgeMonitor`/`PerpHedgeDispatchRouter`/`PerpHedgeFetchProvider`/`app.py`.

- **`PerpHedgeConsumer._rebalance_guard()`** (`perp_hedge_consumer.py:132-141`): explicitly returns `UNSUPPORTED_VENUE`
  for `PerpVenueId.BYBIT` with message "Bybit rebalance is a gated follow-up (todo 15); only Hyperliquid is wired."

- **No Bybit-native connector** exists (unlike `HyperliquidConnector` in `defi_execution/protocols/hyperliquid.py` which
  has direct REST + EIP-712 signing + credential hot-reloading). Bybit has no `defi_execution/protocols/bybit.py`.

- **No Bybit USDC bridge** exists. `HyperliquidBridge` (`hyperliquid_bridge.py`) handles Arbitrum USDC→HL deposits via
  `deposit_usdc_to_hyperliquid`. Bybit deposits follow a different chain path (Bybit uses its own deposit addresses, not
  an Arbitrum bridge contract).

- **No credential hot-reloader** exists for Bybit. `start_hl_key_reloader` (`config_reloaders.py:199`) watches GSM
  secret `hyperliquid-trade-key`. Bybit needs its own equivalent watching a Bybit API secret.

## Design decisions (resolved — not re-litigated)

1. **Wrap, don't replace — reuse `BybitCCXTAdapter`**: the existing adapter already has live-tested `place_order()`,
   `get_positions()`, and `get_account_state()` via CCXT. A native Bybit REST connector would duplicate ~400 lines of
   already-shipped, tested code with no incremental value for a P3 secondary venue. Build a thin
   `BybitPerpHedgeConnector` adapter class that wraps `BybitCCXTAdapter` and exposes the narrow interface
   `PerpHedgeMonitor`/`PerpHedgeConsumer` need (`place_order(symbol, side, size, reduce_only)` →
   `{"success": bool, "order_id": str, "error": str}`, plus position/margin readers). If CCXT latency or dependency risk
   becomes a real issue in production, a native connector can replace the adapter without changing the consumer/wiring
   layer — the adapter IS the seam.

2. **HMAC auth, not EIP-712**: Bybit uses API key + secret HMAC signing, not wallet private-key signing. The credential
   hot-reloader watches a GSM secret containing the API key + secret blob (secret name `bybit-api-credentials`,
   following the UAC `DATA_SOURCE_TO_SECRET` registry convention). No wallet custody implications — HMAC credentials are
   revokable API keys, not on-chain keys.

3. **Separate USDC deposit path**: Bybit deposits go to a Bybit deposit address, not through a bridge contract. The
   topup path for testnet/early-mainnet is a manual or semi-automated USDC transfer to the Bybit deposit address tracked
   via `get_account_state()` — a full automated bridge (like HL's Arbitrum bridge) is out of scope for this plan and
   deferred to a follow-up when live-mainnet Bybit trading is active.

4. **Same single-designated-path constraint** (BLK-1255d5cf): Bybit rebalance/topup intents route through the SAME
   `RecursiveLoopOrchestrator` → `PerpHedgeConsumer` path, not a second instruction sink. The consumer's
   `_rebalance_guard()` is extended to accept `PerpVenueId.BYBIT` with a wired `BybitPerpHedgeConnector`.

## Todos

- [x] ✅ [BACKEND] P2. Build `BybitPerpHedgeConnector` — a thin adapter wrapping `BybitCCXTAdapter` for the perp-hedge
      interface. Constructor takes `api_key: str`, `api_secret: str`, `testnet: bool`. Exposes:
      `place_order(symbol, side, size, reduce_only)` → `{"success": bool, "order_id": str | None, "error": str | None}`
      (delegates to `BybitCCXTAdapter.place_order()` translating the perp-hedge call signature), `fetch_positions()` →
      `list[dict]` (delegates to `get_positions()`), `fetch_balance(asset: str)` → `Decimal` (delegates to
      `get_account_state()`). Repo: execution-service. Done-when: unit tests (place_order SHORT/COVER/NOOP,
      fetch_positions filters zero-qty, fetch_balance returns USDC free, adapter not-initialized raises clean);
      `quality-gates.sh` green.

- [x] ✅ [BACKEND] P2. Extend `PerpHedgeConsumer._rebalance_guard()` to route `PerpVenueId.BYBIT` through a wired
      `BybitPerpHedgeConnector` (single designated path — no second instruction sink). Remove the current
      `UNSUPPORTED_VENUE` block for Bybit. Extend `dispatch_rebalance()` to accept `BybitPerpHedgeConnector | None`
      alongside the existing `HyperliquidConnector | None` and dispatch to the correct connector by venue. UAC
      `classify_venue_error` classification applies identically (shard-level failure isolation — never raised). Repo:
      execution-service. Done-when: unit tests (Bybit SHORT routes to Bybit connector, Bybit COVER routes to Bybit
      connector, unwired Bybit connector returns NOT_WIRED, mixed HL+Bybit dispatch routes to correct connector);
      `quality-gates.sh` green. — execution-service@133ac40e30, QG green (7945 passed, 21 skipped, 174s).

- [x] ✅ [BACKEND] P2. Build Bybit credential hot-reloader + wiring module at
      `execution_service/defi_execution/wiring/bybit_wiring.py` (mirrors `hyperliquid_wiring.py`'s pattern).
      `build_bybit_wiring(config)` resolves the Bybit API key + secret from GSM (secret `bybit-api-credentials`, or the
      UAC `DATA_SOURCE_TO_SECRET` registry name if different), builds `BybitPerpHedgeConnector` (testnet/early-mainnet
      gated on `config.testnet_mode`), wraps in `BybitWiring` (`connect()` → connector init +
      `start_bybit_key_reloader`, `disconnect()` → `stop_bybit_key_reloader` + connector.close).
      `start_bybit_key_reloader` watches the GSM secret and pushes new credentials to the connector on rotation (mirrors
      `start_hl_key_reloader`). Repo: execution-service. Done-when: wiring tests (connector built with real GSM secret
      resolution, testnet mode gating, connect starts reloader / disconnect stops it, missing credentials → honest
      NOT_WIRED); `quality-gates.sh` green. — execution-service@03c69a3767, QG green (all gates passed 193s; new wiring
      tests 17/17 pass), credential resolution mirrors `LiveExecutionHandler._load_bybit_trade_credentials` (trade-scope
      pair preferred, unscoped fallback).

- [ ] [BACKEND] P2. Wire Bybit connector at `app.py` startup/shutdown. Add `_wire_bybit_connector` startup handler +
      `_stop_bybit_connector` shutdown handler. `_start_perp_hedge_monitors` now binds the Bybit connector into
      `RecursiveLoopOrchestrator(bybit_connector=...)` so Bybit-venue rebalance/topup intents route through the same
      consumer path (todo 2's extended guard). Repo: execution-service. Done-when: wiring/integration test asserts app
      startup binds Bybit connector + shutdown tears down cleanly + orchestrator carries both HL and Bybit connectors;
      `quality-gates.sh` green.

- [ ] [BACKEND] P2. Wire Bybit fetch readers into `PerpHedgeFetchProvider`. Add `fetch_current_perp_size_bybit`,
      `fetch_available_margin_bybit`, `fetch_initial_margin_estimate_bybit` callables sourced from
      `BybitPerpHedgeConnector.fetch_positions()`/`fetch_balance()`. `PerpHedgeFetchProvider.build_fetch_callables()`
      picks the correct connector by venue (HL vs Bybit) — the existing connector-agnostic callables already accept a
      venue parameter; extend to resolve Bybit when `PerpVenueId.BYBIT`. Repo: execution-service. Done-when: unit tests
      with mock Bybit connector responses (perp size, available margin, initial margin estimate); `quality-gates.sh`
      green.

- [ ] [BACKEND] P3. Bybit USDC margin topup path — honest interim stub. Extend `PerpHedgeConsumer._topup_guard()` to
      accept `PerpVenueId.BYBIT` with `TopupSource.TREASURY_HOT`, returning an honest `NOT_WIRED` result with a filed
      follow-up todo for the real Bybit deposit automation (Bybit deposits use exchange deposit addresses, not an
      on-chain bridge contract — the automation surface is different from HL's Arbitrum bridge and needs separate
      design). This ensures the topup path doesn't silently no-op for Bybit while the automation is pending. Repo:
      execution-service. Done-when: unit test asserts Bybit TREASURY_HOT topup returns honest NOT_WIRED (not a crash or
      silent success); `quality-gates.sh` green.

- [ ] [DESIGN] P3. Bybit USDC deposit automation follow-up — file a properly-scoped implementation plan (same shape as
      this one) covering: Bybit deposit-address resolution API, USDC transfer tracking via `get_account_state()`
      polling, credential custody for the funding wallet (TREASURY_HOT → COPPER_MPC/CEFFU_MPC gating per Group F item
      19). Gated on the Bybit connector + consumer path (todos 1-5) being green. Repo: execution-service (+ possibly
      infra for the funding-wallet custody). Done-when: a properly-scoped implementation plan filed; gated on this plan
      being complete.

## Progress Log

- **2026-08-10 (slot 13, backend_engineer)**: Authored. Scoped from code evidence: `BybitCCXTAdapter` (`bybit_ccxt.py`)
  — existing CCXT-based adapter with live `place_order()`/`get_positions()`/ `get_account_state()`, HMAC key+secret
  auth, testnet sandbox mode. `PerpHedgeConsumer._rebalance_guard()` (`perp_hedge_consumer.py:132-141`) — explicitly
  blocks Bybit as UNSUPPORTED_VENUE pending this plan. No native Bybit connector, credential reloader, or USDC bridge
  exists. Decision: wrap the existing adapter rather than build a native connector from scratch (P3 secondary venue —
  reuse tested code; the adapter IS the seam if CCXT ever needs replacing). Filed as the gated follow-up required by
  `recursive_loop_orchestrator_wiring_finalize_2026_08_09.md` todo 15.

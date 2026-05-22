---
name: per-client-isolation-preaudit-2026-05-20
title: Per-client isolation pre-audit — read-only manifest (Phase 0)
created: 2026-05-20
archived: 2026-05-22
status: ACKED-INTO-PLAN
priority: P2
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **[ACKED-INTO-PLAN]** Archived 2026-05-22. Phase 0 read-only survey; migration Phases 1-9 documented in per-client
> isolation active plans under `client_isolation_and_governance_master` epic.

# Per-client isolation — pre-audit manifest (Phase 0)

Read-only survey of the workspace ahead of Phases 1–9. All paths relative to the workspace root unless stated.

---

## (a) strategy-service single-tenant assumptions

Files that read env vars or carry module-level globals with client-scoped state:

| File                                                         | Assumption                                                                                     | Migration path (Phase 4)                                                                                         |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `strategy_service/pnl/isolation_policy.py`                   | Module-level `_cached_policy`, `_cached_client_id` singletons loaded from `CLIENT_ID` env var. | Each `ClientWorker` subprocess reloads its own policy in its own process; no shared module state across workers. |
| `strategy_service/position/isolation_policy.py`              | Same pattern — `_cached_policy`, `_cached_client_id` singletons.                               | Same as above.                                                                                                   |
| `strategy_service/engine/core/signal_publisher.py`           | Reads `CLIENT_ID` / `VM_ASSET_GROUP` env vars.                                                 | Move to `ClientContext` constructor arg passed from supervisor.                                                  |
| `strategy_service/position/config.py`                        | `os.environ` reads at module import time.                                                      | Move to per-worker config loader.                                                                                |
| `strategy_service/signal_broadcast/config.py`                | `os.environ` reads for service config.                                                         | Pass `ServiceConfig` from supervisor to worker subprocess entry point.                                           |
| `strategy_service/pnl/engine/pnl_input_builder.py:197-198`   | Local MTM compute `unrealized_pnl = net_qty × last_price - buy_val`.                           | Move mark-price read to shared-memory read from `MarkPriceAggregator`; keep local unrealized_pnl formula.        |
| `strategy_service/position/core/mark_price_subscriber.py:52` | Local MTM: `unrealized_pnl = (mark_price - entry_price) × qty`.                                | Same — consume aggregated mark from shared memory.                                                               |
| `strategy_service/position/core/leg_snapshot_builder.py:106` | `notional = abs(position_units × mark_price)`.                                                 | Same.                                                                                                            |
| `strategy_service/risk/core/risk_calculator.py:127-129`      | Aggregates `position_value` (pre-MTM'd) for leverage.                                          | Unchanged — aggregates pre-computed MTM values; MarkPriceAggregator feeds inputs.                                |
| `strategy_service/engine/core/dependency_checker.py`         | Env var reads for dependencies.                                                                | Pass via `ClientContext`.                                                                                        |
| `strategy_service/portfolio_allocator/service.py`            | Module-level allocator instance assumes single client.                                         | Allocator becomes per-`ClientWorker` instance.                                                                   |
| `strategy_service/allocation_sizer.py`                       | `os.environ` read for `CLIENT_ID`.                                                             | Pass via `ClientContext`.                                                                                        |

**colocated_engine.py cross-process boundary**: `SharedState` is a process-level singleton in the current model. In
Phase 4, `SharedState` becomes per-`ClientWorker`; the parent `StrategySupervisor` owns `MarkPriceAggregator` +
read-only `EngineCtx`. Per-client state (positions, fills, PnL, risk, credentials) moves entirely into each
`ClientWorker.run()`.

---

## (b) UAC types that carry (or should carry) `client_id` — current vs target

| Type                          | Current                                                   | Target (Phase 1)                                                       |
| ----------------------------- | --------------------------------------------------------- | ---------------------------------------------------------------------- |
| `KillSwitchArmedEvent`        | Has `target_wallet_id`; `client_id` inferred from context | Keep as-is; `ClientLifecycleEvent` is the new client-scoped bus event  |
| New: `ClientLifecycleEvent`   | —                                                         | `client_id` required field                                             |
| New: `ClientReadyEvent`       | —                                                         | `client_id` required field                                             |
| New: `ClientQuarantinedEvent` | —                                                         | `client_id` required field                                             |
| New: `ShardCapacityEvent`     | —                                                         | `archetype_id` + `shard_id` scope (no `client_id` — shard-level event) |
| New: `TransferIntent`         | —                                                         | `client_id` required; `TransferCoordinator` rejects cross-client       |
| New: `TransferResult`         | —                                                         | Matches `TransferIntent.idempotency_key` + carries `client_id`         |
| `CanonicalOrder`              | Has `client_id` field                                     | Already correct                                                        |
| `CanonicalFill`               | Has `client_id` field                                     | Already correct                                                        |

---

## (c) Kill-switch subscribers that need `ClientLifecycleEvent` equivalent

`KillSwitchBusSubscriberBase` (shipped `utl@e2445522`) covers:

- `strategy_service/pnl/kill_switch_bus_subscriber.py`
- `strategy_service/risk/kill_switch_bus_subscriber.py` (equivalent pattern)
- `strategy_service/position/kill_switch_bus_subscriber.py` (equivalent pattern)
- `strategy_service/signal_publishing/kill_switch_bus_subscriber.py` (equivalent)

Each of these needs a parallel `ClientLifecycleBusSubscriberBase` subscriber once Phase 3 wires up the supervisor. Phase
2 delivers the base; Phase 3 wires the concrete subscribers.

---

## (d) colocated_engine.py cross-process boundaries needing IPC replacement

`strategy_service/engine/colocated_engine.py`:

- `SharedState` singleton → becomes per-ClientWorker (Phase 4)
- `EngineCtx` supervisor-level read-only config → broadcast via `multiprocessing.shared_memory`
- Parent→child events: lifecycle, credential-rotation, shutdown → `multiprocessing.Pipe`
- Child→parent events: ready, quarantined, heartbeat, order-emitted → same `Pipe`

No current IPC primitives; `multiprocessing.Process` + `Pipe` + `shared_memory` all introduced in Phase 4.

---

## (e) execution-service `isolation_policy.py` verification

`execution-service/execution_service/isolation_policy.py:1-80`:

- `CLIENT_ID` env var binding: VERIFIED — `assert_client_allowed()` gates ALL cross-client event-bus subscribers.
- Pattern covers: all bus subscribers in `execution_service/` (grep for `assert_client_allowed` shows 7 call sites
  across `trade_execution/`, `defi_execution/`, `engine/`).
- **Decision (per plan)**: no new isolation primitive needed for May-23 — execution-service already single-tenant per
  process. Deployment-api fans out per `CLIENT_ID`.
- `TransferCoordinator` (Phase 6) adds `assert_client_allowed` at its intake boundary (inherited from existing pattern).

---

## (f) MTM compute paths re-verified

4 paths confirmed (matches 2026-05-20 audit):

1. `strategy_service/pnl/engine/pnl_input_builder.py:197-198`
2. `strategy_service/position/core/mark_price_subscriber.py:52`
3. `strategy_service/position/core/leg_snapshot_builder.py:106`
4. `strategy_service/risk/core/risk_calculator.py:127-129`

All 4 consume upstream mark prices from MTDS/MDPS; perform their own local MTM arithmetic. `MarkPriceAggregator`
(Phase 3) consolidates the upstream subscription; `ClientWorker` (Phase 4) consumes pre-computed marks from shared
memory, then applies the same arithmetic formula locally.

---

## (g) Per-venue credential refresh cadence

Drives `ClientCredentialKmsPoller` default intervals (Phase 2):

| Venue type               | Examples                                  | Poll interval |
| ------------------------ | ----------------------------------------- | ------------- |
| CEX (API key)            | Binance, OKX, Bybit, Deribit, Hyperliquid | 60s           |
| DEX (wallet signing key) | Aave, Uniswap, Morpho, Etherfi            | 300s          |
| Lending protocol         | Aave V3, Morpho, Yearn, Idle, Puffer      | 600s          |

Rationale: CEX keys are rotated more frequently (exchange-enforced 90-day rotation in some cases); DEX wallet keys
rotate less often (cold-path); lending protocol keys are the most stable.

Grace period for in-flight requests: 10s after rotation signal received before old credentials are discarded (per plan
Phase 5.2(c)).

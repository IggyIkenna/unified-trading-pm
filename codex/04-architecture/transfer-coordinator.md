---
doc_type: codex-ssot
title: TransferCoordinator
summary: TransferCoordinator is the single entry point for all execution-service fund movements — routes by
  TransferIntent.transfer_type, enforces same-client_id on every transfer (raises CrossClientTransferForbiddenError),
  validates the destination against the client wallet registry, and is idempotent on idempotency_key.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [transfers, execution, client-funds-isolation, uac, idempotency, defi]
related:
  [
    /codex/04-architecture/transfer-architecture.md,
    /codex/04-architecture/client-funds-isolation.md,
    /codex/04-architecture/per-client-isolation-architecture.md,
    /codex/04-architecture/oms-protocol-and-state-machine.md,
  ]
created: 2026-05-20
authoritative_for: [TransferCoordinator single-entry fund-movement facade + routing table]
referenced_by:
  [
    /codex/04-architecture/client-funds-isolation.md,
    /codex/04-architecture/execution-service-per-client-isolation.md,
    /codex/04-architecture/oms-protocol-and-state-machine.md,
    /codex/04-architecture/transfer-architecture.md,
  ]
owner:
last_reviewed: 2026-05-20
code_refs:
---

# TransferCoordinator

## Overview

`TransferCoordinator` is the **single entry point** for all fund-movement operations in execution-service. It is the
Phase 6 new component of the Group H plan (`plans/active/per_client_isolation_and_venue_fanout_topology_2026_05_20.md`).

Before this facade, fund movements were fragmented across `transfer_handler.py`, `defi_execution/protocols/*`,
`defi_execution/hyperliquid_bridge.py`, `v2/handlers.py`, and `algo_library/intent_engine.py` — with no consistent
`client_id` enforcement at the operation layer. TransferCoordinator closes all 6 BLOCKING gaps identified in
`plans/active/issues/cross_client_funds_isolation_retroactive_audit_2026_05_20.md`.

**HARD RULE cross-reference**: `/codex/04-architecture/client-funds-isolation.md` — funds NEVER move between different
clients. `TransferCoordinator` is the final-gate consumer-side enforcement point.

**Status (re-verified 2026-08-19)**: the "pending Phase 1" framing is stale — the UAC `TransferIntent`/`TransferResult`
contract has shipped and is live (`BusTransferType`, 13 members, `unified_api_contracts.canonical.crosscutting.transfer_events`;
consumed and tested by `strategy-service/strategy_service/transfer_coordinator.py`'s emit-time netting). What remains
undone is narrower and different: **`execution_service.transfer_coordinator.TransferCoordinator` itself has ZERO
production construction sites workspace-wide** (verified by grep — not imported, not built, not referenced in `app.py`
or any wiring module; only its own unit tests construct it). It is a real, tested, dormant class — see
`/codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md`'s IMPLEMENTATION STATUS box for the matching
producer-side gap ("nothing emits `TransferIntent` in production").

---

## Location

`execution-service/execution_service/transfer_coordinator.py`

---

## Routing table

**Table below is design intent — `_ensure_default_handlers()` only registers `SUBACCOUNT_MOVE`; every other row has NO
handler wired.** Calling `.execute()` with any other `transfer_type` today raises `KeyError` ("No handler registered").

| `TransferIntent.transfer_type` | Downstream handler                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CEX_WITHDRAW`                 | NOT WIRED — module docstring (2026-08-16) says `adapters/order_adapter.py` has no withdraw function; real impl is the separate `engine.transfers.live_ccxt_adapter` path, reached via `HandlerRegistry`/`InstructionRouter`, not this coordinator                                                                                                                                                                                                                                                                                                                                                                                                        |
| `DEFI_DEPOSIT`                 | design intent: `defi_execution/protocols/<protocol>/deposit()` — no handler registered in code today                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `DEFI_WITHDRAW`                | design intent: `defi_execution/protocols/<protocol>/withdraw()` — no handler registered in code today                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `BRIDGE`                       | **corrected 2026-08-19** — the module docstring names `execution_service.v2.handlers.BridgeHandler` as the target; **that module and class do not exist anywhere in the workspace** (`v2/handlers.py` is not a real file; `BridgeHandler` has zero definitions — fabricated/stale). The real live-capable bridge connectors are `SocketBridgeConnector`/`CCTPBridgeConnector` (`defi_execution/protocols/bridge.py`, `cctp.py`) — real, tested, but zero production call sites today. See `/codex/04-architecture/transfer-architecture.md` § "Bridging execution reality" for the decided `BridgeRouter` architecture that will wire `BRIDGE` for real. |
| `SUBACCOUNT_MOVE`              | Only wired handler — `_SubaccountMoveHandler`, Binance + OKX only; `NotSupportedTransferError` for all others, named successor `subaccount_transfers_phase_2_2026_06_01.md`                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |

---

## Enforcement sequence (every transfer, no exceptions)

```
TransferCoordinator.consume(intent: TransferIntent)
  1. assert intent.source_account.client_id == intent.dest_account.client_id
       → raises CrossClientTransferForbiddenError if mismatch
       → emits CROSS_CLIENT_TRANSFER_REJECTED structured alert
  2. isolation_policy.assert_client_allowed(intent.source_account.client_id)
       → defence-in-depth: process-binding check
  3. validate destination address is in client's registered wallet set (clients.yaml)
       → raises CrossClientTransferForbiddenError if not found
  4. idempotency check: if intent.idempotency_key already in TransferPersistenceAdapter
       → return cached TransferResult (no-op)
  5. dispatch to downstream by transfer_type
  6. persist TransferResult with idempotency_key
  7. emit TransferResult event on UAC bus
```

---

## Idempotency

`TransferIntent.idempotency_key` maps to `operation_id` in a `TransferPersistenceAdapter` (mirrors
`OrderPersistenceAdapter` pattern — see `/codex/04-architecture/oms-protocol-and-state-machine.md`). A second submission
with the same key returns the cached `TransferResult` without re-executing any RPC.

---

## UAC event wiring

```
strategy-service emits: TransferIntent (UAC canonical/crosscutting/)
    → execution-service TransferCoordinator subscribes via UAC event bus
    → on completion emits: TransferResult (UAC canonical/crosscutting/)
    → strategy-service consumes TransferResult
```

UAC types (`TransferIntent` + `TransferResult`) defined in slot 5 Phase 1 — prerequisite.

---

## Retroactive gap closures

Phase 6 wraps the pre-existing execution-service surfaces to close each BLOCKING gap from the retroactive audit:

| Gap                                             | Pre-existing surface                                                       | TransferCoordinator fix                                                                            |
| ----------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| CEX withdrawal destination unvalidated          | `transfer_handler.py:330`                                                  | Validates `to_address` against `client_id` wallet registry before delegating                       |
| DeFi protocol methods lack `client_id`          | `defi_execution/protocols/*.py` (aave, karak, yearn, idle, morpho, puffer) | Validates connector's wallet is in `client_id` wallet set before calling `deposit()`/`withdraw()`  |
| Bridge bare destination address                 | `defi_execution/hyperliquid_bridge.py:84,173`                              | Adds `client_id` validation before posting; raises `CrossClientTransferForbiddenError` on mismatch |
| BridgeHandler no client enforcement             | `v2/handlers.py:265`                                                       | Verifies BridgeInstructionV2's source/dest client match before returning `ActionHandlerResult`     |
| Intent engine `client_id` not in ExecutionSteps | `algo_library/intent_engine.py:495`                                        | Propagates `client_id` through Intent dataclass + all `ExecutionStep` objects                      |
| `assert_client_allowed` only at bus layer       | `isolation_policy.py:80`                                                   | Called at TransferCoordinator entry (step 2 above) before any account data access                  |

---

## Required tests

Per `/codex/04-architecture/client-funds-isolation.md` HARD RULE:

1. **Intra-client happy path** — USDC → Aave deposit, same `client_id` on source + dest; verifies
   `TransferResult.status = CONFIRMED`.
2. **UAC validator rejects cross-client at construction** — `TransferIntent` construction with mismatched `client_id`
   fails schema validation.
3. **Defence-in-depth** — `TransferCoordinator` rejects cross-client intent at consume time even if UAC validator is
   bypassed (mock UAC validator to pass; confirm coordinator still raises).
4. **Alert assertion** — `CrossClientTransferForbiddenError` raises AND structured alert event is emitted.
5. **CEX withdrawal destination validation** — `to_address` not in `client_id` wallet registry → raises before any CEX
   RPC.
6. **DeFi connector wallet validation** — connector's wallet not in `client_id` wallet set → raises before
   `deposit()`/`withdraw()`.
7. **Bridge destination validation** — `destination_address` not in `client_id` wallet set → raises before bridge RPC.
8. **Intent engine client_id propagation** — `_decompose_bridge()` produces `ExecutionStep` objects each carrying
   `client_id`.
9. **assert_client_allowed at operation layer** — mock process-bound `client_id = A`; submit intent with `client_id = B`
   → `CrossClientEventError` raised.
10. **Idempotency** — same `idempotency_key` submitted twice → second is no-op, returns cached `TransferResult`, no
    downstream RPC on second call.

---

## Sub-account moves

`SUBACCOUNT_MOVE` is not yet implemented in execution-service. `TransferCoordinator` raises `NotSupportedError` with
message pointing to `subaccount_transfers_phase_2_2026_06_01.md` for all venues except Binance + OKX. When Binance/OKX
subaccount APIs are added, they land as new branches inside `TransferCoordinator`'s routing table — no facade change
required.

---

## Named successors

- **Phase E.1** — venue-level circuit breaker hardening (Group H plan post-cutover)
- **Phase E.3** — IntraClientRebalanceCoordinator (intra-client multi-portfolio rebalancing; strategy-service)
- `subaccount_transfers_phase_2_2026_06_01.md` — Binance + OKX sub-account move implementation

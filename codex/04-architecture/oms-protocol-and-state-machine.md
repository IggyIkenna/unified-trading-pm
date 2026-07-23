---
doc_type: codex-ssot
title: OMS Protocol and State Machine
summary:
  "The execution-service OMS — UnifiedOrderManager (submit/cancel/amend/get) + async OrderPersistenceAdapter +
  PersistentOrderManager (operation_id idempotency, last-write-wins) + InstructionOrderTracker (instruction → N child
  orders) + NautilusTrader restart reconciliation. The per-order lifecycle-state taxonomy lives in
  order-state-machine.md."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [execution, order-state, reconciliation, ssot]
related:
  [
    /codex/04-architecture/order-state-machine.md,
    /codex/04-architecture/strategy-execution-protocol.md,
    /codex/04-architecture/transfer-coordinator.md,
  ]
created: 2026-05-20
authoritative_for:
  [
    OMS protocol surfaces,
    PersistentOrderManager idempotency and reconciliation,
    OrderPersistenceAdapter protocol,
    InstructionOrderTracker mapping,
  ]
referenced_by: [/codex/04-architecture/order-state-machine.md, /codex/04-architecture/transfer-coordinator.md]
owner:
last_reviewed: 2026-05-20
code_refs:
---

# OMS Protocol and State Machine

## Overview

The Order Management System (OMS) in execution-service provides persistent order tracking across venues. It consists of
two protocol surfaces and a concrete implementation:

- `UnifiedOrderManager` — submit/cancel/amend/get synchronous protocol
- `OrderPersistenceAdapter` — async persistence protocol (DB, in-memory, etc.)
- `PersistentOrderManager` — concrete OMS that composes a persistence adapter
- `InstructionOrderTracker` — maps instruction_id → order_ids → fill status
- `OrderTracker` — in-memory state machine (lightweight; for non-persisted flows)

SSOT: `execution-service/execution_service/trade_execution/oms/`

---

## State machine

```
PENDING
  └─ validate() → VALIDATED
       └─ submit() → SUBMITTED
             ├─ fill (partial) → PARTIAL_FILLED
             │     └─ fill (complete) → FILLED
             ├─ fill (complete) → FILLED
             ├─ reject from venue → REJECTED
             └─ cancel() → CANCELLED
```

States (`OrderStatus` StrEnum in `persistent_oms.py`):

| State            | Meaning                                     |
| ---------------- | ------------------------------------------- |
| `PENDING`        | Created in OMS; not yet validated           |
| `VALIDATED`      | Passed pre-flight checks; ready to submit   |
| `SUBMITTED`      | Sent to venue; awaiting acknowledgement     |
| `PARTIAL_FILLED` | Partially executed; outstanding qty remains |
| `FILLED`         | Fully executed                              |
| `REJECTED`       | Venue rejected the order                    |
| `CANCELLED`      | Cancelled by operator or algorithm          |

---

## UnifiedOrderManager protocol

Defined in `trade_execution/oms/protocols.py`. Runtime-checkable.

```python
class UnifiedOrderManager(Protocol):
    def submit_order(self, order: CanonicalOrder) -> str: ...        # returns order_id
    def cancel_order(self, order_id: str) -> bool: ...               # True if cancelled
    def amend_order(self, order_id: str, **kwargs) -> bool: ...      # True if amended
    def get_order(self, order_id: str) -> CanonicalOrder | None: ...
```

---

## OrderPersistenceAdapter protocol

```python
class OrderPersistenceAdapter(Protocol):
    async def initialize(self) -> None: ...
    async def save_order(self, order_data: dict) -> None: ...
    async def get_order(self, operation_id: str) -> dict | None: ...
    async def update_order_status(self, operation_id, status, *, venue_order_id, fills) -> None: ...
    async def get_all_orders(self) -> list[dict]: ...
    async def get_orders_by_strategy(self, strategy_id: str) -> list[dict]: ...
```

Concrete adapters implement this protocol. Test suites substitute an in-memory adapter.

---

## PersistentOrderManager

`PersistentOrderManager` composes an `OrderPersistenceAdapter`. Key behaviours:

**Order creation** (`create_order()`): generates `operation_id = op-{uuid12}` if not provided. Writes to persistence
with `status=PENDING`. Returns order dict. Callers that provide a deterministic `operation_id` achieve idempotency at
the persistence layer: a second create with the same `operation_id` will overwrite the first (last-write-wins).

**Status updates** (`update_order_status()`): checks order exists before updating; returns `False` if not found (enables
safe retry on at-most-once semantics). Carries optional `venue_order_id` and `fills` list.

**NautilusTrader reconciliation** (`reconcile_with_nautilus(cache)`): walks `cache.orders_open()` and the OMS store,
syncing statuses (ACCEPTED→SUBMITTED, FILLED→FILLED, CANCELED→CANCELLED). Returns
`{orders_synced, orders_updated, orders_missing_in_cache, orders_missing_in_db}`. Called on restart to heal OMS state
from NautilusTrader cache.

---

## InstructionOrderTracker

`instruction_tracker.py` — maps one instruction to N child orders (multi-leg algorithms).

| Method                                    | Behaviour                                                    |
| ----------------------------------------- | ------------------------------------------------------------ |
| `track_order(instruction_id, order_id)`   | Registers child order; sets status=SUBMITTED                 |
| `update_fill(order_id, fill_data)`        | Appends fill; sets status=FILLED                             |
| `get_instruction_orders(instruction_id)`  | Returns list of child order_ids (raises KeyError if unknown) |
| `is_instruction_complete(instruction_id)` | True when ALL child orders are FILLED                        |

---

## OrderTracker (lightweight in-memory)

`tracker.py` — thin in-memory state machine for flows that don't need GCS persistence.

States: `NEW | PENDING | FILLED | PARTIALLY_FILLED | CANCELLED | REJECTED`

Used by simpler adapters and test harnesses. Does not implement `OrderPersistenceAdapter` — it is standalone.

---

## Idempotency pattern for TransferCoordinator

The `TransferCoordinator` (Phase 6 new component) reuses the `operation_id`-based pattern from OMS:
`TransferIntent.idempotency_key` maps 1:1 to `operation_id` in a `TransferPersistenceAdapter`. If the same
idempotency_key is submitted twice, the second call returns the cached `TransferResult` without re-executing. See
`/codex/04-architecture/transfer-coordinator.md`.

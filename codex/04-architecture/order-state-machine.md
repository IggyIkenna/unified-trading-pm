---
doc_type: codex-ssot
title: Order state machine
summary:
  "The per-order lifecycle state machine execution-service emits — a 9-state closed set (PENDING_NEW → NEW →
  PARTIALLY_FILLED / FILLED → RECONCILED, plus CANCELLED / REJECTED / EXPIRED / FAIL_OUTBOUND), its transitions, and one
  UAC event per transition. The protocol-level contract lives in strategy-execution-protocol.md."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [execution, order-state, reconciliation, uac, ssot]
related:
  [
    /codex/04-architecture/oms-protocol-and-state-machine.md,
    /codex/04-architecture/strategy-execution-protocol.md,
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/alerting-batch-live.md,
    /codex/04-architecture/paper-vs-live-execution-seam.md,
  ]
created: 2026-05-12
authoritative_for:
  [per-order state machine, order lifecycle states and transitions, per-transition order event emission]
referenced_by: [/codex/04-architecture/oms-protocol-and-state-machine.md]
owner:
last_reviewed: 2026-05-17
code_refs:
doc_kind: contract_stub
ssot_for: order_state_machine
created_per: plans/archive/issues/codex_audit_execution_2026_05_12.md EX-24
---

# Order state machine

> SSOT-stub for the per-order lifecycle states + transitions + events that execution-service emits. The
> [`strategy-execution-protocol.md`](./strategy-execution-protocol.md) doc covers the **protocol contract**
> (target-state, idempotent reconciliation, 14 action types per UAC `InstructionActionV2`); THIS doc covers the
> **per-order state machine** — what each order goes through from instruction → terminal.

## States (closed set)

| State              | Description                                                        | Terminal? |
| ------------------ | ------------------------------------------------------------------ | --------- |
| `PENDING_NEW`      | Instruction received; pre-validation in progress                   | No        |
| `NEW`              | Validated; submitted to venue; awaiting venue ack                  | No        |
| `PARTIALLY_FILLED` | Venue has filled a portion; remainder still working                | No        |
| `FILLED`           | Venue has filled in full                                           | YES       |
| `CANCELLED`        | Operator or strategy cancelled; venue confirmed cancellation       | YES       |
| `REJECTED`         | Venue rejected the order (e.g. insufficient margin, invalid price) | YES       |
| `EXPIRED`          | Time-in-force window elapsed; venue auto-cancelled                 | YES       |
| `FAIL_OUTBOUND`    | Failed to reach venue (network / auth / signing); pre-NEW failure  | YES       |
| `RECONCILED`       | Terminal state matched by position-balance-monitor reconciler      | YES       |

UAC SSOT: `unified_api_contracts.canonical.domain.execution.OrderState` (or `internal/execution.py` `OrderState`
StrEnum).

## Transitions

```
                                ┌─────────────────┐
                                │  PENDING_NEW    │
                                └────────┬────────┘
                                         │ submit ok
                       ┌─────────────────▼─────────────────┐
                       │                NEW                 │
                       └───┬───────────────┬───────────┬───┘
                           │               │           │
                  partial fill        full fill    cancel/expire/reject
                           │               │           │
                  ┌────────▼────────┐  ┌───▼────┐  ┌───▼─────────────────┐
                  │PARTIALLY_FILLED │  │ FILLED │  │ CANCELLED / EXPIRED  │
                  └────────┬────────┘  └────┬───┘  │ / REJECTED           │
                  full fill│                 │       └─────────────────────┘
                           ▼                 │
                       ┌───▼───┐               │
                       │FILLED │               │
                       └───┬───┘               │
                           │                   │
                           └─────┬─────────────┘
                                 │ reconciler matches venue + manifest position
                                 ▼
                            ┌──────────┐
                            │RECONCILED│
                            └──────────┘
```

Pre-submission failure path: `PENDING_NEW → FAIL_OUTBOUND` (no venue interaction occurred).

## Events emitted per transition

| Transition                            | UAC event (closed set)                |
| ------------------------------------- | ------------------------------------- |
| → `PENDING_NEW`                       | `ORDER_INSTRUCTION_RECEIVED`          |
| `PENDING_NEW` → `NEW`                 | `ORDER_SUBMITTED`                     |
| `NEW` → `PARTIALLY_FILLED` / `FILLED` | `ORDER_FILLED` (with fill payload)    |
| `NEW` → `CANCELLED`                   | `ORDER_CANCELLED`                     |
| `NEW` → `REJECTED`                    | `ORDER_REJECTED` (+ AlertCode)        |
| `NEW` → `EXPIRED`                     | `ORDER_EXPIRED`                       |
| `PENDING_NEW` → `FAIL_OUTBOUND`       | `ORDER_OUTBOUND_FAILED` (+ AlertCode) |
| terminal → `RECONCILED`               | `ORDER_RECONCILED`                    |

`AlertCode` taxonomy: see [`/codex/04-architecture/alerting-batch-live.md`](./alerting-batch-live.md). Terminal-bad
states (`REJECTED` / `FAIL_OUTBOUND`) fire P0 / P1 alerts depending on `AlertSeverity` mapping.

## Cross-references

- [`strategy-execution-protocol.md`](./strategy-execution-protocol.md) — protocol-level contract (instruction shapes,
  target-state idempotency).
- [`batch-live-architecture.md`](./batch-live-architecture.md) § "Strategy alpha vs execution alpha" — fill source
  difference between BENCHMARK / SIMULATED / live.
- [`paper-vs-live-execution-seam.md`](./paper-vs-live-execution-seam.md) — paper-mode fill simulation.
- [`alerting-batch-live.md`](./alerting-batch-live.md) — AlertCode + severity mapping.
- Code: `execution-service/execution_service/orders/` + `engine/modes/live/matching_engine.py`.

## Cross-cutting

- `OrderState` flips trigger `position-balance-monitor` reconciler ticks (see `position-balance-monitor-service`).
- Risk-and-exposure-service reads `OrderState` to compute `PendingExposure` (NEW + PARTIALLY_FILLED states).
- `paper-mode-execution-seam.md` describes the simulated fill path that maps `NEW → FILLED` via the matching engine.

## Execution-owner block

```yaml
execution:
  owner: execution-service maintainer (Ikenna for design / state-machine taxonomy; Harsh for state-machine tests)
  cadence:
    per-PR — every PR touching `execution-service/execution_service/orders/` or `engine/modes/live/matching_engine.py`
    MUST verify state-machine invariants (no unguarded transitions, all terminal states fire `ORDER_RECONCILED` within
    reconciler SLA)
  verifier: |
    `execution-service/scripts/quality-gates.sh` runs state-machine invariant unit tests under
    `tests/unit/orders/test_state_machine.py` (to be added; tracked in EX-24 follow-up). CI fails on transition
    coverage gap.
  last_executed: NEVER (this codex stub created 2026-05-12; tests + matching state-machine code pending)
```

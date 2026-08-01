---
doc_type: issue
title:
  order-state-machine.md is authoritative_for a 9-state OrderState enum that does not exist in UAC — the shipped
  contract is a 7-member OrderStatus, missing FAIL_OUTBOUND and RECONCILED entirely
summary: >-
  `/codex/04-architecture/order-state-machine.md` carries `authoritative_for: [per-order state machine, order lifecycle
  states and transitions, per-transition order event emission]` and documents a 9-state closed set (`PENDING_NEW`,
  `NEW`, `PARTIALLY_FILLED`, `FILLED`, `CANCELLED`, `REJECTED`, `EXPIRED`, `FAIL_OUTBOUND`, `RECONCILED`) under the
  symbol `unified_api_contracts.canonical.domain.execution.OrderState`. Verified 2026-07-31: **no `OrderState` symbol
  exists anywhere in UAC.** What ships is `unified_api_contracts.canonical.domain.execution.base.OrderStatus`, a
  7-member StrEnum (`PENDING`, `OPEN`, `PARTIALLY_FILLED`, `FILLED`, `CANCELLED`, `REJECTED`, `EXPIRED`). Two documented
  states — `FAIL_OUTBOUND` and `RECONCILED` — have no UAC representation at all, and two more are renamed
  (`PENDING_NEW`→`PENDING`, `NEW`→`OPEN`). The doc's stated fallback location (`internal/execution.py` `OrderState`)
  also does not exist. This is an SSOT contradiction, not just a stale name: an agent following the codex SSOT would
  write `OrderState.FAIL_OUTBOUND` and get an ImportError, and the doc's whole per-transition event table
  (`ORDER_OUTBOUND_FAILED`, `ORDER_RECONCILED`) hangs off states the contract cannot express.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [execution]
repos: [unified-api-contracts, execution-service, unified-trading-pm]
scope: [engineer, admin]
tags: [execution, order-state, uac, ssot-contradiction, contract-stub]
related:
  [
    /codex/04-architecture/order-state-machine.md,
    /codex/02-data/canonical-schema-groups.md,
    /codex/04-architecture/oms-protocol-and-state-machine.md,
    /codex/04-architecture/strategy-execution-protocol.md,
  ]
created: 2026-07-31
priority: P2
parent_epic: infrastructure_master
source: "slot-3, codex freshness re-review shard-B, discovered re-reviewing order-state-machine.md, 2026-07-31"
execution_scope: local-only
drift_direction: needs-decision
depends_on: []
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
---

# order-state-machine.md documents an `OrderState` enum UAC does not have

## Measured state (2026-07-31)

| Source                                                                | Symbol        | Members                                                                                                         |
| --------------------------------------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------- |
| `/codex/04-architecture/order-state-machine.md` (`authoritative_for`) | `OrderState`  | PENDING_NEW · NEW · PARTIALLY_FILLED · FILLED · CANCELLED · REJECTED · EXPIRED · FAIL_OUTBOUND · RECONCILED (9) |
| UAC `canonical/domain/execution/base.py:47` (shipped)                 | `OrderStatus` | PENDING · OPEN · PARTIALLY_FILLED · FILLED · CANCELLED · REJECTED · EXPIRED (7)                                 |

`rg -n 'OrderState' unified-api-contracts/unified_api_contracts/ --glob '*.py'` returns only `DeribitOrderStateResponse`
(an external Deribit wire schema, unrelated). `internal/execution.py` contains no `OrderState`.

`/codex/02-data/canonical-schema-groups.md` § 8 carried the same wrong name + members; that row was corrected in place
during this re-review, and both docs now carry a pointer to this issue.

## Why this is more than a rename

The doc is a `doc_kind: contract_stub` whose `last_executed:` field already reads
`NEVER (this codex stub created 2026-05-12; tests + matching state-machine code pending)`, so the 9-state machine was
always a design target. The problem is that it is simultaneously marked `status: current` and `authoritative_for` the
order lifecycle, with no marker distinguishing designed-from-shipped. Downstream consequences:

- `FAIL_OUTBOUND` (pre-venue send failure) and `RECONCILED` (reconciler-matched terminal) are load-bearing in the doc's
  event table (`ORDER_OUTBOUND_FAILED`, `ORDER_RECONCILED`) and in its cross-cutting claims about
  position-balance-monitor and risk-and-exposure-service. None of that can be expressed against `OrderStatus`.
- The doc claims risk-and-exposure computes `PendingExposure` from "NEW + PARTIALLY_FILLED"; the shipped equivalent
  would be `OPEN + PARTIALLY_FILLED`.
- `tests/unit/orders/test_state_machine.py`, named as the doc's `verifier:`, has still never been created — so nothing
  would have caught the divergence.

## Decision needed (operator / execution owner)

This is a design call, not a mechanical fix — hence `assigned_vm: NA`.

- **A** — Advance the contract: add `FAIL_OUTBOUND` + `RECONCILED` to UAC `OrderStatus` and rename `PENDING`/`OPEN` →
  `PENDING_NEW`/`NEW` so the shipped enum matches the documented state machine. Highest fidelity to the design; a
  breaking UAC change with fleet-wide consumers.
- **B** — Retreat the doc: rewrite `order-state-machine.md` to document the 7-state `OrderStatus` as-is, and move
  `FAIL_OUTBOUND`/`RECONCILED` into a clearly-marked "planned, not shipped" section. Cheapest, keeps the codex honest.
- **C** — Split the concern: keep `OrderStatus` as the venue-reported status and introduce a separate internal lifecycle
  enum that adds the two workspace-only terminal states. Matches the fact that `FAIL_OUTBOUND`/`RECONCILED` are our
  concepts, not venue concepts.

Interim mitigation already applied: both codex docs now carry a ⚠️ block stating the shipped enum and warning that
`OrderState` / `FAIL_OUTBOUND` / `RECONCILED` will not import.

## Follow-ups

- [ ] [OPERATOR] P2. Rule between A / B / C above for the order-lifecycle enum. Provenance: codex freshness re-review
      shard-B, 2026-07-31.
- [ ] [TEST] P2. Once ruled, create `execution-service/tests/unit/orders/test_state_machine.py` (the doc's declared
      `verifier:`, never written) asserting the enum members match the codex state table, so this cannot silently
      diverge again.

## Progress Log

- **na-eligibility-audit 2026-08-01**: KEEP-NA, valid -- Full audit rationale: Both open items are genuinely
  judgment/operator-gated. Item 1 is an explicit [OPERATOR] tri-way design decision (A: extend UAC OrderStatus with
  FAIL_OUTBOUND/RECONCILED + rename members — a breaking fleet-wide contract change; B: retreat the codex doc to match
  the shipped 7-state enum; C: split into...

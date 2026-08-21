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
status: resolved
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
    /plans/active/code_readiness_t4_execution_settlement_2026_08_19.md,
  ]
created: 2026-07-31
author: unknown
priority: P2
parent_epic: uac_master
source: "slot-3, codex freshness re-review shard-B, discovered re-reviewing order-state-machine.md, 2026-07-31"
execution_scope: local-only
drift_direction: needs-decision
depends_on: []
assigned_vm: NA
resolved_by: "na-eligibility-audit 2026-08-21, verified against code_readiness_t4_execution_settlement_2026_08_19.md (execution-service@35f0bfb1b rename, execution-service@69a9a088be test)"
locked_by:
locked_since:
last_updated: "2026-08-21"
context_scope:
  [
    /codex/04-architecture/order-state-machine.md,
    /codex/02-data/canonical-schema-groups.md,
    /codex/04-architecture/oms-protocol-and-state-machine.md,
    unified-api-contracts/unified_api_contracts/canonical/domain/execution/base.py,
    execution-service/tests/unit/orders/,
  ]
---

> **🟢 ARCHIVED 2026-08-21** — both remaining todos verified DONE against
> `/plans/active/code_readiness_t4_execution_settlement_2026_08_19.md` (`execution-service@35f0bfb1b` rename,
> `execution-service@69a9a088be` test). See this doc's own Progress Log for full evidence.

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

- [x] [CODE] P2. **DONE — shipped `unified-api-contracts@a3c572f8` ("feat(execution): OrderStatus becomes the full
      9-state order state machine")**, verified ancestor of `origin/live-defi-rollout`; commit message cites this
      exact ruling. `unified_api_contracts/canonical/domain/execution/base.py:48-82` now has all 9 codex-named
      members (PENDING_NEW, NEW, PARTIALLY_FILLED, FILLED, CANCELLED, REJECTED, EXPIRED, FAIL_OUTBOUND, RECONCILED),
      PENDING/OPEN kept as deliberate transitional aliases. NOTE — a separate, still-genuinely-open tail: the 24
      execution-service call sites still use the PENDING/OPEN aliases; their migration + eventual alias deletion is
      tracked as a T4 inbound request in `/plans/active/code_readiness_t4_execution_settlement_2026_08_19.md`, not
      here.
- [ ] [CODE] P2. **RULED 2026-08-06 (operator), option A: advance the contract — CONFIRMED 2026-08-12 (/plan-reconcile,
      operator confirmed interactively).** `[CODE]` tag (was `[OPERATOR]`) — add `FAIL_OUTBOUND` + `RECONCILED` to UAC
      `OrderStatus`, rename `PENDING`/`OPEN` → `PENDING_NEW`/`NEW`. This is a breaking, fleet-wide UAC change — every
      consumer of `OrderStatus` needs auditing for the rename, not just an additive enum extension. Scope this as its
      own tracked rollout (consumer audit + migration, not a one-line enum edit) before dispatching. Provenance: codex
      freshness re-review shard-B, 2026-07-31. This todo previously carried the identical self-contradiction as the
      sibling `strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md` finding (RULED opening line vs undecided closing
      line, no Progress Log ruling record) — resolved 2026-08-12: the operator confirmed option A is the standing
      ruling. The breaking UAC change itself is NOT done here — only the doc-level contradiction is resolved; the
      rollout (consumer audit + migration + enum change) remains open work.
      **UPDATE 2026-08-20 (T1 slice)**: UAC's own consumer audit is done — `unified-api-contracts`'s 14 internal call
      sites (all 12 `external/*/normalize.py` venue adapters + `normalize_utils/_helpers.py` + the
      `canonical/domain/execution/base.py:229` default) migrated from `OrderStatus.PENDING`/`.OPEN` to the canonical
      `.PENDING_NEW`/`.NEW`. Non-breaking (the aliases are unchanged, still `is`-identical) — see
      `unified-api-contracts@702e8adcbe`.

      **DONE 2026-08-21 — verified against `/plans/active/code_readiness_t4_execution_settlement_2026_08_19.md`
      (na-eligibility-audit)**: the T4 tail is now landed, not just tracked. `execution-service@35f0bfb1b`
      ("Migrated") renamed `OrderStatus.PENDING`/`.OPEN` → `.PENDING_NEW`/`.NEW` in every one of the 18 true
      UAC-importing call sites (the other 6 of the original 24-site estimate turned out to define their OWN local,
      unrelated `OrderStatus` enum — correctly left untouched); repo-wide grep for `OrderStatus\.PENDING\b`/
      `OrderStatus\.OPEN\b` against UAC's import returns zero. T4's own "T1 unblock notice 2026-08-20" confirms
      the full 9-state `OrderStatus` (incl. `FAIL_OUTBOUND`/`RECONCILED`) is live with `ORDER_STATUS_TRANSITIONS`,
      `TERMINAL_ORDER_STATUSES`, `is_terminal_order_status()` and `is_legal_order_transition()` all exported. The
      two transitional aliases (`PENDING`/`OPEN`) are deliberately KEPT for now, pending T1's fleet-wide-consumer
      confirmation before deletion — that residual is T4's own tracked scope, not a gap in this doc's rollout ask.
      This doc's own "scope this as its own tracked rollout" ask is fulfilled.
- [x] [TEST] P2. **DONE — shipped at a different (correct) path**, same commit `unified-api-contracts@a3c572f8`:
      `unified-api-contracts/tests/unit/test_order_state_machine.py` (109 lines, 9 tests, pins every enum member
      against the codex state table). Not at the originally-named `execution-service/...` path because the enum
      lives in UAC and this tranche was forbidden to edit execution-service per the commit message — substance
      satisfied.
- [x] ✅ [TEST] P2. **DONE — verified 2026-08-21 (na-eligibility-audit) against
      `/plans/active/code_readiness_t4_execution_settlement_2026_08_19.md`.** `execution-service/tests/unit/orders/
      test_state_machine.py` exists and is shipped (`execution-service@69a9a088be`) — it "pins both the mapping
      function and the `update_order_status()` integration on both files" per T4's own text. The shipped invariant
      is deliberately narrower than the full `ORDER_STATUS_TRANSITIONS` edge set (4 real pre-existing tests would
      have broken on the strict edge-by-edge version), but is real and covers the load-bearing case: once
      terminal, the only legal further move is `RECONCILED` — catches state resurrection, tolerates the legitimate
      skip-ahead path. Substance satisfied; the doc's own declared `verifier:` now exists and asserts against real
      behavior.

## Progress Log

- **na-eligibility-audit 2026-08-01**: KEEP-NA, valid -- Full audit rationale: Both open items are genuinely
  judgment/operator-gated. Item 1 is an explicit [OPERATOR] tri-way design decision (A: extend UAC OrderStatus with
  FAIL_OUTBOUND/RECONCILED + rename members — a breaking fleet-wide contract change; B: retreat the codex doc to match
  the shipped 7-state enum; C: split into...
- **context-scout 2026-08-03**: populated context_scope (5 entries).

- **na-eligibility-audit 2026-08-03 (cross-cutting tranche)**: KEEP-NA, valid — reaffirmed, unchanged. Today's edit that
  put this doc back in incremental scope was the context-scout backfill above, not a content change; both open items
  remain a genuine tri-way breaking-contract design decision ([OPERATOR]) and its gated follow-up test ([TEST]).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms 2026-08-03 (unchanged): item 1 is an undecided
  breaking-vs-non-breaking UAC contract design call (A/B/C), item 2 sequentially depends on item 1's ruling.
- **round11 RECLASSIFY sweep 2026-08-09**: NOT reclassified — found item 1's own opening text ("RULED 2026-08-06
  (operator), option A: advance the contract") directly contradicts its own closing text ("Rule between A / B / C above
  for the order-lifecycle enum") and this SAME doc's own 2026-08-06 audit entry immediately above, which still calls
  item 1 "an undecided breaking-vs-non-breaking UAC contract design call." No Progress Log entry anywhere records an
  actual ruling. Filed
  `issues/two_issue_docs_claim_2026_08_06_operator_ruling_with_no_corroborating_evidence_2026_08_09.md` (a sibling doc,
  `strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md`, has the identical malformed pattern) rather than acting on
  the unverified "RULED" text — this is a breaking, fleet-wide, execution-critical UAC contract change, too
  consequential to dispatch on contradictory self-reported text. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:c0299d0e0d0f7bbd]: KEEP-NA, valid -- 2 open items (grep-verified, matches inventory_open_todos=2). A 2026-08-09 'round11 RECLASSIFY sweep' explicitly declined to reclassify because item 1's text then carried a self-contradiction (RULED-vs-undecided, no corroborating Progress Log entry) and instead filed a dedicated contradiction-tracking issue doc. That contradiction is now resolved: the item's current text carries a dated citation ('CONFIRMED 2026-08-12, /plan-reconcile, operator confirmed interactively'), independently corroborated by this same tranche's plan_reconciler_findings_all_2026_08_12.md. This is now a standing, dated operator ruling not to be re-litigated — but it only settles DIRECTION, not boundedness: the item's own text states the remaining work is 'a breaking, fleet-wide UAC change — every consumer of OrderStatus needs auditing for the rename... Scope this as its own tracked rollout... before dispatching' — exactly the class of multi-consumer, live-execution-critical-path machinery the bounded-outcome bar excludes despite reading as one item. Item 2 (write test_state_machine.py) is sequentially dependent on item 1 landing. Three earlier na-eligibility-audit passes (2026-08-01/03/06) also KEEP-NA'd this doc on the same underlying design-call basis.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-21**: ARCHIVE — both remaining open todos verified DONE against
  `/plans/active/code_readiness_t4_execution_settlement_2026_08_19.md` (not just "tracked there", the work is
  actually landed): item 1 (breaking rollout) — `execution-service@35f0bfb1b` renamed `OrderStatus.PENDING`/
  `.OPEN` → `.PENDING_NEW`/`.NEW` in all 18 true UAC-importing call sites, repo-wide grep for the old names
  against UAC's import returns zero; item 2 (test) — `execution-service/tests/unit/orders/test_state_machine.py`
  exists and is shipped (`execution-service@69a9a088be`). 0 open todos remain, doc not `locked_by:` anyone —
  archiving per the standard 6-step ritual. `codex/04-architecture/order-state-machine.md` line 62 still cites
  this doc's pre-archive path — flagged for a follow-up path fix (this session cannot edit codex/**). Cross-cutting
  tranche, batch 2 of 3.

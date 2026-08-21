---
doc_type: issue
title: >-
  `DeFiAdapter.execute_instruction()`'s SWAP/lending translation layer reports `"status": "COMPLETED"`
  unconditionally and reads the wrong tx-hash key — a live revert or connector failure is reported as success
summary: >-
  Found while wiring real live dispatch for SWAP/LEND/WITHDRAW/STAKE/UNSTAKE onto
  `execution-service/execution_service/api/external_instruction_api.py` (see the sibling
  `external_instruction_defi_handlers_simulation_only_2026_08_20.md` issue and its resolution,
  `execution-service@4af3715497`). That work deliberately does NOT route through
  `DeFiAdapter.execute_instruction()` — it calls the underlying connector methods
  (`UniswapConnector.swap_exact_input`, `AaveConnector.supply`/`withdraw`, `LidoConnector.stake`/`unstake`)
  directly and does its own honest result translation in the new
  `execution_service/engine/handlers/defi_live_dispatch.py` module, specifically to avoid this bug. This issue
  documents the bug itself, which remains live in `DeFiAdapter.execute_instruction()`'s existing consumer
  (`ManualOperationHandler`'s `DEFI_VENUES` branch, the internal manual-instruction surface) — not fixed here, to
  avoid widening the SWAP/LEND/STAKE change's blast radius onto an already-shipped, differently-scoped consumer.
status: resolved
nature: issue
asset_group: [defi]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [defi, fabricated-success, live-money-risk, financial-correctness, defi-adapter]
related:
  [
    /plans/archive/issues/external_instruction_defi_handlers_simulation_only_2026_08_20.md,
    /codex/04-architecture/defi-execution-overview.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-21
author: agent
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.5
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by: >-
  All 3 todos resolved 2026-08-21. `_execute_swap` fixed first by a concurrent session
  (`execution-service@d7970e0e2`); the remaining 9 methods (`_execute_lending`,
  `_execute_pendle_lending`, `_execute_morpho_lending`, `_execute_lido_staking`,
  `_execute_symbiotic_staking`, `_execute_etherfi_staking`, `_execute_puffer_staking`,
  `_execute_rocket_pool_staking`, `_execute_solblaze_staking`) fixed + `_execute_swap`
  strengthened (added `error` field) by `execution-service@a05182262c`. Todo 3's audit
  answer is in the Progress Log below.
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Sub-agent dispatch wiring real live execution for SWAP/LEND/WITHDRAW/STAKE/UNSTAKE (2026-08-21) — found while
  deciding NOT to route the new live-dispatch seam through this existing, buggy translation layer. Cited in that
  change's own `defi_live_dispatch.py` module docstring; this doc is the promised, separately-tracked follow-up
  that docstring points to.
context_scope:
  [
    execution-service/execution_service/adapters/defi_adapter.py,
    execution-service/execution_service/engine/handlers/defi_live_dispatch.py,
    execution-service/execution_service/operations/manual.py,
  ]
---

# `DeFiAdapter.execute_instruction()` fabricates success on a live revert or connector failure

> **RESOLVED + ARCHIVED 2026-08-21.** All 12 `_execute_*` methods audited; 10 needed the fix (hardcoded
> `"status": "COMPLETED"` without checking the connector result's `success` field), fixed across two commits:
> `execution-service@d7970e0e2` (`_execute_swap` only) + `execution-service@a05182262c` (the remaining 9 +
> an `error` field added to `_execute_swap`'s return too). `_execute_kamino_lending`/`_execute_marinade_staking`
> were already correct. `_execute_jupiter_swap` needs no fix — see its docstring for why. See `resolved_by`
> frontmatter and the Progress Log below for the full record, including the todo-3 blast-radius audit answer.

## The bug, precisely

`execution_service/adapters/defi_adapter.py::_execute_swap()` (lines 345-391):

- Line 368: calls the real connector, `await self._uniswap.swap_exact_input(...)`.
- Line 379: `tx_hash: str = str(result.get("transaction_hash") or "pending")` — reads the WRONG key. The real
  connector's result dict sets `"tx_hash"`, never `"transaction_hash"` (confirmed by reading
  `UniswapConnector.swap_exact_input`'s actual return shape, and independently by `defi_live_dispatch.py`'s own
  `dispatch_swap_live`, which reads `result.get("tx_hash")` and works correctly). This lookup always misses,
  so `tx_hash` is always `"pending"` here — even for a genuinely successful live swap with a real on-chain hash
  available.
- Line 385: `"status": "COMPLETED"` is hardcoded, unconditional — never checks `result.get("success")`. If the
  connector returns `{"success": False, "error": "..."}` (a live revert, insufficient liquidity, a signing
  failure — any real on-chain failure), this method still returns `"status": "COMPLETED"` with `tx_hash="pending"`
  and whatever `amount_out` the connector happened to include (possibly `0.0` if the failure path didn't set one).

`_execute_lending()` (line 441 onward) was not fully re-verified in this pass — flagged as likely the same pattern
(same author, same file, same "no success check before COMPLETED" shape visible in the code read so far) but not
confirmed with the same line-level precision as `_execute_swap`; the follow-up todo below should verify it before
assuming it needs the identical fix.

## Why this matters

`DeFiAdapter.execute_instruction()` is the translation layer `ManualOperationHandler`'s `DEFI_VENUES` branch uses
for the internal manual-instruction surface (operator-triggered manual trades via `execution-service`'s own
`/manual` API). A caller submitting a manual live SWAP through that surface, on a real revert or connector-level
failure, would receive a response claiming `"status": "COMPLETED"` — indistinguishable from genuine success unless
they specifically notice `tx_hash == "pending"` never resolving to a real hash. This is a live-money-risk
fabricated-success gap, the same hard-rule violation class the sibling SWAP/LEND/STAKE issue was filed for — just
in a different, already-shipped code path this pass deliberately did not touch.

## What I have NOT verified

- Whether `_execute_lending()` (AAVE supply/withdraw/borrow/repay) has the identical bug — same file, same author,
  visually similar shape, but not read with the same line-level precision as `_execute_swap` in this pass.
- Whether `ManualOperationHandler`'s `DEFI_VENUES` branch has any downstream check that would catch a stuck
  `tx_hash="pending"` before it reaches an operator (e.g. a reconciliation job) — not audited.
- Real-world blast radius: whether this path has ever actually been exercised in live mode with a real failure
  (vs. always succeeding in practice so far, making this latent rather than actively harmful today).

## Todos

- [x] [BACKEND] P1. Fix `_execute_swap()`: check `result.get("success")` before returning `"status": "COMPLETED"`
      (return a FAILED-shaped result with `result.get("error")` when it's false, mirroring
      `defi_live_dispatch.py::dispatch_swap_live`'s already-correct pattern), and read `result.get("tx_hash")`
      instead of `result.get("transaction_hash")`. Add a regression test proving a `{"success": False, ...}`
      connector result produces a non-COMPLETED status. — DONE. `execution-service@d7970e0e2` (status+tx_hash fix,
      `test_execute_swap_failure`), strengthened by `execution-service@a05182262c` (adds the `error` field to the
      returned dict; test renamed/extended to `test_execute_swap_reports_failed_on_connector_failure`, which also
      asserts `tx_hash == "pending"` and the exact `error` string).
- [x] [BACKEND] P1. Read `_execute_lending()` (and its Pendle/Morpho/Kamino branches) with the same line-level
      precision as this doc's `_execute_swap` analysis; fix the same class of bug if confirmed present, file a
      narrower follow-up if the shape differs from what's assumed here. — DONE, and WIDENED: line-level read of
      all 12 `_execute_*` methods (not just the LEND family) found the identical bug in 9 methods beyond
      `_execute_lending` — `_execute_pendle_lending`, `_execute_morpho_lending`, `_execute_lido_staking`,
      `_execute_symbiotic_staking`, `_execute_etherfi_staking`, `_execute_puffer_staking`,
      `_execute_rocket_pool_staking`, `_execute_solblaze_staking` — plus the SAME wrong-tx_hash-key bug (reads
      `"transaction_hash"`, a key none of these connectors ever set — confirmed by reading
      `execution_service/defi_execution/protocols/base.py`'s `sign_and_send_transaction()`/
      `_await_tx_receipt()`, which every EVM connector's live path spreads, and which set only `"tx_hash"`) in
      `_execute_pendle_lending`/`_execute_lido_staking`/`_execute_symbiotic_staking` specifically — the original
      doc's own speculation that Lido might only ever set `"transaction_hash"` (so its tx_hash lookup might need
      to stay as-is) was WRONG; measured, not assumed. `_execute_kamino_lending`/`_execute_marinade_staking` were
      already correct (dataclass `.success` check) and untouched. `_execute_jupiter_swap` was investigated and
      found NOT to need this fix: `JupiterSwapResult` (`unified_api_contracts.internal`, a pydantic `BaseModel`)
      has no `success`/`error` field at all, and `JupiterConnector.execute_swap()` raises `ValueError` on any
      on-chain/API failure rather than returning a failure-shaped result — reaching `_execute_jupiter_swap`'s
      `return` is itself proof of success, documented in place so a future reader doesn't "fix" it incorrectly.
      Fixed + tested: `execution-service@a05182262c` (regression tests for a representative dict-swap,
      dict-lending, dict-staking, and dataclass-swap-exception-propagation shape, plus new Symbiotic test
      coverage that didn't exist before).
- [x] [BACKEND] P2. Audit whether `ManualOperationHandler`'s `DEFI_VENUES` branch (or anything downstream) has
      ever surfaced a stuck `tx_hash="pending"` in production — answer the blast-radius question this doc leaves
      open, with evidence either way. — DONE (static-analysis audit, 2026-08-21; no production log/telemetry
      access from this session, so this is a code-reachability answer, not a historical-occurrence one). No
      dedicated monitoring/reconciliation/alerting watches for a stuck `tx_hash="pending"` on DeFi manual
      instructions: `MANUAL_INSTRUCTION_EXECUTED` (the audit-log event `manual_instruction_submit.py::
      _execute_via_orchestrator()` writes on every manual execution, including DeFi) has ZERO other repo
      references — it is write-only, nothing reads or alerts on it. More significant than the doc's original
      framing: the bug's blast radius reached further than a merely-cosmetic wrong status. That same function
      gates a REAL `InstructionLedger` booking on `result.get("status") == "COMPLETED"` (line ~233) — before
      this fix, a live revert on any of the 10 broken methods would have been unconditionally treated as
      COMPLETED and booked a ledger fill (using the operator's declared qty/price, since `DeFiAdapter`'s result
      dicts carry no `"fills"` list for `manual_instruction_ledger.aggregate_fill_metrics()` to read — confirmed
      by reading that function). This fix closes that path: a genuine failure now returns `"status": "FAILED"`,
      so the `== "COMPLETED"` gate correctly skips the ledger booking. No evidence found that this was ever
      exercised with a real on-chain failure in production — `DEFI_VENUES` in `live_execution_venues.py` lists
      only 4 venues (`UNISWAP_V3`, `AAVE`, `AAVE_V3-ETHEREUM`, `LIDO-ETHEREUM`) reachable via the manual surface
      at all, and this is an operator-triggered path, not automated strategy execution — latent-only bug, now
      fixed before ever biting in practice, best as this session can determine without production log access.

## Progress Log

- **2026-08-21**: Filed as the promised follow-up `defi_live_dispatch.py`'s own module docstring pointed to,
  after the SWAP/LEND/WITHDRAW/STAKE/UNSTAKE live-dispatch change (`execution-service@4af3715497`) deliberately
  avoided routing through this buggy layer. Root-caused with exact line citations (`defi_adapter.py:379`,
  `:385`), not guessed.
- **na-eligibility-audit 2026-08-21**: RECLASSIFY (whole-doc) `assigned_vm: NA` → `planning`. All 3 open todos are
  bounded/deterministic: todo 1 is a well-specified bug fix mirroring an already-correct sibling pattern
  (`defi_live_dispatch.py::dispatch_swap_live`) with an explicit regression-test ask; todo 2 is a bounded
  investigation (read `_execute_lending()` with the same precision, fix the same bug class if confirmed, file a
  narrower follow-up if the shape differs); todo 3 is a bounded audit (trace whether `ManualOperationHandler`'s
  `DEFI_VENUES` branch has ever surfaced a stuck `tx_hash="pending"` in production). No open design/judgment call.
  Conflict-checked: grepped `plans/active/` for `_execute_swap`/`execute_instruction`/`defi_adapter.py` —
  `defi_adapter_dead_code_audit_2026_07_24.md` covers a DIFFERENT method (the now-removed public
  `execute_swap`/`execute_lend`/`execute_stake` dead-code duplicates, not the private `_execute_swap()` this
  doc's bug lives in); `code_readiness_t4_execution_settlement_2026_08_19.md` has zero mentions of
  `defi_adapter.py`. No genuine conflict found. `execution_scope` corrected to `orchestrator-agent` to match.
  Cross-cutting tranche, batch 2 of 3.
- **2026-08-21 (dispatch closing this doc)**: Read all 12 `_execute_*` methods in `defi_adapter.py` with the same
  line-level precision as the original `_execute_swap` analysis, per todo 2's ask. Found a concurrent session had
  already landed the narrower `_execute_swap`-only fix (`execution-service@d7970e0e2`) mid-dispatch — confirmed via
  `git log` that only that one commit touched `defi_adapter.py`/`test_defi_adapter.py` since this session's own QG
  baseline, then reconciled cleanly (both fixes are functionally equivalent for `_execute_swap`; this dispatch's
  version is a strict superset — same status/tx_hash fix plus an added `error` field — so the conflict resolved by
  keeping this dispatch's content, which already included the prior fix's effect). Confirmed the SAME bug class in
  9 additional methods beyond the doc's original `_execute_lending`-only scope for todo 2 — see the todo 2 checkbox
  above for the full per-method breakdown and the specific tx_hash-key finding that corrects this doc's own
  "What I have NOT verified" speculation about Lido. Measured (not assumed) that `_execute_jupiter_swap` does NOT
  need this fix — `JupiterSwapResult` (`unified_api_contracts.internal`) has no `success`/`error` field, and
  `JupiterConnector.execute_swap()` raises on failure rather than returning one; documented in the method's own
  docstring so a future reader doesn't "fix" it incorrectly. `_execute_kamino_lending`/`_execute_marinade_staking`
  were already correct and untouched (dataclass `.success` reference pattern). Regression tests added for a
  representative dict-swap/dict-lending/dict-staking/dataclass-swap-exception-propagation connector shape, plus new
  Symbiotic test coverage (had none before). Todo 3's audit: no monitoring/alerting anywhere in `execution-service`
  reads or reacts to `MANUAL_INSTRUCTION_EXECUTED` (write-only audit event, zero other references) or a stuck
  `tx_hash="pending"` — but the actual blast radius is worse than this doc's original framing: a fabricated
  COMPLETED status would have caused `manual_instruction_submit.py::_execute_via_orchestrator()` to book a REAL
  `InstructionLedger` fill (gated on `result.get("status") == "COMPLETED"`) using the operator's declared qty/price
  for a trade that actually reverted on-chain — this fix closes that path, not just the audit-log cosmetic issue.
  No evidence found of this ever being exercised with a real production failure (static-analysis-only conclusion,
  no log/telemetry access from this session) — `DEFI_VENUES` in `live_execution_venues.py` lists only 4 venues
  reachable via the manual surface at all, and it's an operator-triggered path, not automated strategy execution.
  Shipped: `execution-service@a05182262c` (`bash scripts/quality-gates.sh --no-fix` green both before and after
  reconciling the concurrent-commit conflict; 9014+ tests passed). All 3 todos now `[x]`, nothing `locked_by:` —
  archiving per the sibling `external_instruction_defi_handlers_simulation_only_2026_08_20.md` pattern.

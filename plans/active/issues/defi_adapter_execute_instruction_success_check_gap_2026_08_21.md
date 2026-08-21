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
status: open
nature: issue
asset_group: [defi]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [defi, fabricated-success, live-money-risk, financial-correctness, defi-adapter]
related:
  [
    /plans/active/issues/external_instruction_defi_handlers_simulation_only_2026_08_20.md,
    /codex/04-architecture/defi-execution-overview.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-21
author: agent
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.5
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by:
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

- [ ] [BACKEND] P1. Fix `_execute_swap()`: check `result.get("success")` before returning `"status": "COMPLETED"`
      (return a FAILED-shaped result with `result.get("error")` when it's false, mirroring
      `defi_live_dispatch.py::dispatch_swap_live`'s already-correct pattern), and read `result.get("tx_hash")`
      instead of `result.get("transaction_hash")`. Add a regression test proving a `{"success": False, ...}`
      connector result produces a non-COMPLETED status.
- [ ] [BACKEND] P1. Read `_execute_lending()` (and its Pendle/Morpho/Kamino branches) with the same line-level
      precision as this doc's `_execute_swap` analysis; fix the same class of bug if confirmed present, file a
      narrower follow-up if the shape differs from what's assumed here.
- [ ] [BACKEND] P2. Audit whether `ManualOperationHandler`'s `DEFI_VENUES` branch (or anything downstream) has
      ever surfaced a stuck `tx_hash="pending"` in production — answer the blast-radius question this doc leaves
      open, with evidence either way.

## Progress Log

- **2026-08-21**: Filed as the promised follow-up `defi_live_dispatch.py`'s own module docstring pointed to,
  after the SWAP/LEND/WITHDRAW/STAKE/UNSTAKE live-dispatch change (`execution-service@4af3715497`) deliberately
  avoided routing through this buggy layer. Root-caused with exact line citations (`defi_adapter.py:379`,
  `:385`), not guessed.

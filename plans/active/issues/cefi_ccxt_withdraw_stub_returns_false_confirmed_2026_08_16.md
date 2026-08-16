---
doc_type: issue
title: CCXT withdraw() is a stub that always returns CONFIRMED without calling the exchange — affects every CEX venue
summary: >-
  execution-service's LiveCcxtTransferAdapter.execute_withdrawal never calls exchange.withdraw() — the real CCXT
  call is commented out and the method always returns a CONFIRMED result. Every CEX_WITHDRAW-routed venue (18 of
  cefi's 22, everything that isn't ON_CHAIN/CUSTODY_TRANSFER) would report a successful withdrawal that never
  actually happened. Found during the venue_e2e_wiring_2026_08_16 cefi batch sweep, step 9 (transfers).
status: open
nature: issue
asset_group: [cefi]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [transfers, financial-correctness, live-money-risk, stub-code, venue-readiness]
related:
  [
    /plans/active/cefi_venue_e2e_batch1_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /codex/04-architecture/transfer-architecture.md,
  ]
created: 2026-08-16
author: interactive-session
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Found 2026-08-16 during cefi_venue_e2e_batch1_2026_08_16.md's step-9 (transfers) contract sweep — a dedicated
  research pass across execution-service's transfer dispatch code, checking every cefi venue's real withdrawal
  path, not just its registry classification.
context_scope:
  [
    execution-service/execution_service/engine/handlers/transfer_handler.py,
    execution-service/execution_service/transfer_coordinator.py,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# CCXT withdraw() is a stub that always returns CONFIRMED without calling the exchange

## What I found

`execution-service`'s live CEX withdrawal path (`LiveCcxtTransferAdapter.execute_withdrawal`, called from
`transfer_handler.py::_execute_cex_withdrawal`, dispatched by `_dispatch_transfer` for every `BusTransferType.
CEX_WITHDRAW` transfer) does not actually call the exchange. The real `exchange.withdraw()` CCXT call is
commented out; the code logs `"CCXT withdraw() not yet wired -- returning success stub"` and unconditionally
returns a `CONFIRMED` transfer result.

**Every one of cefi's 18 CEX-routed venues is affected**: BINANCE-SPOT/FUTURES, OKX-SPOT/FUTURES/SWAP, BYBIT,
BYBIT-SPOT, DERIBIT, UPBIT, COINBASE-SPOT/FUTURES/CDE, BITFINEX-SPOT/FUTURES, BITGET-SPOT/FUTURES, KRAKEN-SPOT/
FUTURES — `classify_transfer_type()` correctly routes all of these to `CEX_WITHDRAW` (confirmed via direct code
read, registry entries are real and correct), so the routing/classification layer is not the problem. The problem
is purely in the execution leg: **a caller cannot distinguish "the withdrawal actually happened" from "the stub
silently no-op'd and lied about it."**

## Why it matters

This is a live-money correctness risk, not a missing feature. If any code path in this system ever actually
invokes a CEX withdrawal today (paper/backtest wouldn't reach this live adapter, but any live-trading fund-
movement flow would), it would receive a `CONFIRMED` result and could reasonably act on that belief — reconcile
balances, release a hold, notify a downstream system — while the real exchange balance is untouched. The failure
mode is silent: no exception, no `BLOCKED`/`FAILED` status, just a false-positive success.

## What I have NOT verified

- Whether any live-trading code path today actually calls this withdrawal method in practice (vs. it being dead
  code reachable only in theory) — I read the transfer-dispatch code, not every caller across the codebase.
- Whether a downstream check (e.g. a balance reconciliation job) would eventually catch the discrepancy, bounding
  the real-world blast radius even if the stub is hit.

## Todos

- [ ] [BACKEND] P0. **Confirm real-world reachability**: grep every caller of `TransferCoordinator`/
      `_dispatch_transfer` with `BusTransferType.CEX_WITHDRAW` across execution-service and any service that
      triggers live fund movement, to determine whether this stub is actually reachable in the current live-
      trading flow today, or only in tests/manual invocation. Done-when: a cited, evidence-backed reachability
      verdict (reachable-in-prod vs. dead-code-today) exists.
- [ ] [BACKEND] P0. **If reachable: wire the real `exchange.withdraw()` CCXT call**, replacing the stub, with the
      same error-handling rigor the rest of the transfer dispatch code uses (fail loud, never silently succeed).
      If genuinely unreachable today: change the stub to fail loud (`raise NotImplementedError` or return a
      `BLOCKED`/`FAILED` status) instead of a false `CONFIRMED`, so a future caller cannot be silently misled even
      before the real integration lands. Done-when: either a real withdrawal executes and is verified against the
      exchange's own confirmation, or the stub fails loud instead of lying.
- [ ] [BACKEND] P1. **Audit whether any downstream balance-reconciliation logic would have caught this** (bounding
      the real blast radius if the stub has ever been hit in a live context) — done-when: a cited answer, yes or
      no, with evidence.

## Progress Log

- **2026-08-16**: Filed during the cefi AG batch's step-9 (transfers) venue-readiness sweep. Not yet triaged for
  reachability — flagged to the operator directly given the live-money-correctness class of the finding, per this
  workspace's "big finding → notify operator" rule, rather than left as a silent plan todo.

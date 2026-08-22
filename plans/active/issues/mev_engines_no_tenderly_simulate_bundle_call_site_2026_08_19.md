---
doc_type: issue
title: No MEV engine calls TenderlyExecutionProvider.simulate_bundle before submission
summary: Direct code read confirms no MEV engine (liquidation_bundle/jit_liquidity/sandwich_theoretical) nor
  matching_engine.py calls TenderlyExecutionProvider.simulate_bundle/gate_or_advise before submission; gate_or_advise
  has zero callers anywhere in the repo. Needs a design call on call-site placement.
status: open
nature: issue
asset_group: [defi]
stage: [execution]
repos: [strategy-service, execution-service]
scope: [engineer]
tags: [mev, tenderly, simulate-bundle, execution-safety]
related: [mev_engines_opportunity_detection_signals_unproduced_2026_08_18]
parent_epic: defi_master
priority: P1
created: 2026-08-19
last_updated: "2026-08-21"
author: slot-10 (review)
assigned_vm: planning
resolved_by: ""
locked_by: ""
source: [mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md todo 1 "Confirm whether the MEV engines
  actually call TenderlyExecutionProvider.simulate-bundle" (extracted via defi satellite batch17, archived 2026-08-20)]
context_scope:
  [
    strategy-service/strategy_service/engine/strategies/v2/mev/liquidation_bundle.py,
    strategy-service/strategy_service/engine/strategies/v2/mev/jit_liquidity.py,
    strategy-service/strategy_service/engine/strategies/v2/mev/sandwich_theoretical.py,
    execution-service/execution_service/providers/tenderly.py,
    execution-service/execution_service/providers/matching_engine.py,
    /codex/05-infrastructure/chain-rpc-mev-tenderly.md,
  ]
---

## What I found

Confirmed via direct code read (not a grep-only proxy): none of the 3 MEV engines call
`TenderlyExecutionProvider.simulate_bundle` (or the `gate_or_advise` pre-flight wrapper around it) before
submission.

- `strategy-service/strategy_service/engine/strategies/v2/mev/liquidation_bundle.py`,
  `jit_liquidity.py`, `sandwich_theoretical.py` — none imports `execution_service` or anything
  Tenderly-related. Their imports are `unified_api_contracts.internal`, `strategy_service.engine.strategies.v2.*`,
  `strategy_service.position.core.margin_health_cache` only. `grep -rn "simulate"` across all three files: zero
  hits. These are pure signal-generation engines with no execution/simulation call at all.
- `execution_service/providers/tenderly.py:331` defines `TenderlyExecutionProvider.simulate_bundle()`. Its only
  production caller in the whole repo tree is `gate_or_advise()` (same file, line 458-484) — the pre-flight
  bundle-sim gate per "Phase 5C policy (codex chain-rpc-mev-tenderly.md §113-119)".
- `gate_or_advise()` itself has **zero callers** anywhere in `execution-service` or `strategy-service` outside its
  own module family (`tenderly.py`, `tenderly_budget.py`, `_tenderly_errors.py`) — confirmed via
  `grep -rln "gate_or_advise"`.
- `execution_service/providers/matching_engine.py` only *mentions* `TenderlyExecutionProvider` in comments/docstrings
  ("Route EVM DeFi legs through TenderlyExecutionProvider", `matching_engine.py:15,18,261`) — it raises
  `NotImplementedError` for EVM DeFi legs rather than actually routing to Tenderly. It does not call
  `simulate_bundle` or `gate_or_advise` either.

Net: `simulate_bundle`/`gate_or_advise` is fully built (types, budget tracker, error handling, tests at
`execution-service/tests/unit/providers/test_tenderly_bundle_sim.py`) but not wired into ANY live execution path —
not the MEV engines, not `matching_engine.py`'s EVM DeFi dispatch.

## Why it matters

For `LIQUIDATION_BUNDLE` specifically (atomic flash-loan bundle), submitting without a pre-flight simulation means
the first real signal of a revert is the on-chain attempt itself — a worse bet than a simulated one even though a
revert there costs gas only. `sandwich_theoretical.py`/`jit_liquidity.py` carry more strategy-level risk
(front-run/JIT windows) where an unsimulated bundle can also misprice slippage the `gate_or_advise` high-slippage
check would have caught.

## Recommended decision

This needs a design call, not a mechanical fix: `gate_or_advise` was built against a bundle-of-`TenderlyTx`
abstraction — deciding WHERE it plugs in (inside each MEV engine before it emits a candidate order, or as a single
gate inside `matching_engine.py`'s EVM DeFi dispatch path once that `NotImplementedError` stub is filled in) is an
architecture choice, not a bounded todo. Recommend routing through `matching_engine.py` (one call site covers all
3 engines + any future EVM DeFi MEV archetype) rather than 3 separate per-engine call sites.

> **Corrected 2026-08-19 (slot-32)**: the `matching_engine.py` recommendation above is a misread. Its
> `NotImplementedError` (`_route_amm_instruction`, `execution_service/providers/matching_engine.py:258`) is the EVM
> **single-AMM-swap** *paper-fill* path (book_type=AMM), not an MEV **bundle** submission path — `gate_or_advise()` gates
> a `list[TenderlyTx]` bundle, and a single swap is not a bundle. The bundle-submission path the engines' own docstring
> names (`aave_flash_bundle.py`, see `liquidation_bundle.py:55`) does not exist, and `FLASHBOTS_BUNDLE_RELAY` is STUBBED
> (operator 2026-05-10, post-cutover). The correct call site is the **live bundle-submission boundary** (Phase 5C "every
> live order goes through bundle-sim"), which must be built first — see Progress Log.

## Todos

- [x] ✅ [STRATEGY] P1. Decide `gate_or_advise()` call-site placement — RESOLVED 2026-08-19: single call site at the
      **live bundle-submission boundary** (Phase 5C "every live order goes through bundle-sim"), not
      `matching_engine.py` (paper-fill single-AMM-swap path) nor per-engine signal-generation sites.
      Repo: execution-service, strategy-service.
- [ ] [OPERATOR] P1. DEFERRED-BY-DESIGN — per D98 ruling (2026-08-21, issues_corpus_completion_dispatch_2026_08_21.md
      ledger): Continue deferring — the operator made this exact call 2 days prior; no new information. Wire
      `gate_or_advise()` at the live bundle-submission boundary once that path is built (blocked on building it
      first: `aave_flash_bundle.py` absent; `FLASHBOTS_BUNDLE_RELAY` stubbed per operator 2026-05-10). Repo:
      execution-service, strategy-service.

## Progress Log

- **2026-08-19 (slot-32, data_engineering worker)** — dispatched on the P1 "decide" todo. Design investigation, each
  claim verified by direct read/grep (not a grep-only proxy):
  - `gate_or_advise()` (`execution_service/providers/tenderly.py:458`) gates a `list[TenderlyTx]` bundle; zero production
    callers (only its own module family + tests) — confirms the issue headline.
  - `matching_engine.py`'s `NotImplementedError` (`_route_amm_instruction`, line 258) is the EVM **single-AMM-swap**
    *paper-fill* path, not a bundle submission path → the "single call site in matching_engine.py" recommendation is a
    misread.
  - The MEV engines (`liquidation_bundle.py`/`jit_liquidity.py`/`sandwich_theoretical.py`) are signal generators: they
    emit instructions (e.g. `liquidation_bundle.py` `_build_bundle()` emits an `"asset"/"amount"/"chain"/venue` payload),
    never `TenderlyTx` bundles — so "3 per-engine call sites" is also not where a bundle sim belongs.
  - The engine docstring names `execution-service …/aave_flash_bundle.py` as the bundle packer (`liquidation_bundle.py:55`)
    but that file does **not exist**; the only consumer of liquidation-bundle instructions is
    `cli/defi_arbitrage_mev_liquidation_bundle_decision_trace.py` (a decision-trace CLI, not live execution).
  - `FLASHBOTS_BUNDLE_RELAY` is STUBBED per operator 2026-05-10 ("post-cutover if needed",
    `/codex/05-infrastructure/chain-rpc-mev-tenderly.md` § MevSubmissionMode).

  **Decision**: the gate belongs at the **live bundle-submission boundary** (Phase 5C "every live order goes through
  bundle-sim"), which does not exist yet. Wiring it requires first building that path (`aave_flash_bundle.py` equivalent +
  un-stubbing `FLASHBOTS_BUNDLE_RELAY`) — a larger, operator-scoped effort, not this 1-hour todo. Escalated to operator via
  /blocked: defer wiring (record design, re-tag todo) vs. approve building the bundle path now.

- **2026-08-19 (operator answer via main)** — BLOCKED Q answered: option A (defer wiring). Keep `gate_or_advise()`
  built-but-unwired; design decision recorded (correct call site = live bundle-submission boundary, Phase 5C); P1 todo
  re-tagged — wiring deferred post-cutover, gated on building the bundle-submission path. B (build now) contradicts the
  standing operator 2026-05-10 stub of `FLASHBOTS_BUNDLE_RELAY`; C (wire into `matching_engine.py`) is the misread
  already corrected above.

- **context-scout 2026-08-20**: populated context_scope (6 entries).
- **2026-08-21 — ruling D98 (MEV bundle boundary timing)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Continue deferring — the operator made this exact call 2 days prior; no new
  information. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.

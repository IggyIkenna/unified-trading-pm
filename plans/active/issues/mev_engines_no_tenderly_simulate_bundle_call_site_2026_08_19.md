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
related: [mev_engines_opportunity_detection_signals_unproduced_2026_08_18, defi_satellite_ao_dispatch_batch17_2026_08_18]
parent_epic: defi_master
priority: P1
created: 2026-08-19
author: slot-10 (review)
assigned_vm: planning
resolved_by: ""
locked_by: ""
source: [defi_satellite_ao_dispatch_batch17_2026_08_18.md item "Confirm whether the MEV engines actually call
  TenderlyExecutionProvider.simulate-bundle"]
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

## Todos

- [ ] [STRATEGY] P1. Design + wire a `gate_or_advise()` pre-submission call for EVM DeFi MEV bundles — decide
      single call site (`matching_engine.py`'s EVM DeFi dispatch, replacing the current `NotImplementedError` stub)
      vs. 3 per-engine call sites in `liquidation_bundle.py`/`jit_liquidity.py`/`sandwich_theoretical.py`.
      Repo: execution-service, strategy-service.

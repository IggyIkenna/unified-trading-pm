---
doc_type: issue
title:
  "onchain `resolve_build_order()` silently absorbs OTHER families' calculators via the shared UTL
  `FeatureCalculatorRegistry` — process-import-order-dependent, non-deterministic feature DAG"
summary:
  "Found 2026-07-13 while authoring the Phase 0 golden-fixture guardrail (utl_reuse_phase0_guardrails_2026_07_13) for
  the UTL/UAC reuse consolidation. `features_service/onchain/schemas/feature_builder_registry.py::_build_registry()`
  reads `FeatureCalculatorRegistry._calculators` — a class-level dict on UTL's shared `FeatureCalculatorRegistry` that
  EVERY features-service family registers calculators into via `@FeatureCalculatorRegistry.register(name)` — with no
  filter for which family a calculator belongs to. Any calculator name not in onchain's own hardcoded `_metadata` dict
  still gets absorbed as a phase-0 onchain builder with empty `sources`/`deps`. Caught because a full `quality-gates.sh`
  pytest run (which imports onchain-adjacent test modules that directly import calculator files NOT wired into
  `onchain/app/calculators/__init__.py`, e.g. `vault_share_price_apy_calculator.py`,
  `chainlink_peg_deviation_calculator.py`) produced a DIFFERENT `resolve_build_order()` output than a clean standalone
  process — 9 foreign entries (`block_priority_gas_distribution`, `chainlink_peg_deviation`,
  `concentrated_liquidity_il_realised`, `economic_events`, `pool_invariant_drift`, `sentiment`, `temporal`,
  `vault_share_price_apy`, `yield_curve`) appeared in the onchain phase-0 bucket that a clean-process capture never
  produced. `multi_timeframe`/`volatility`/`sports` were checked and are NOT affected — they each build from a
  module-local dict/registry, not the shared UTL class-level one."
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [features-service, unified-trading-library]
scope: [engineer]
tags: [features, onchain, builder-registry, data-correctness, non-determinism, utl]
related:
  [
    plans/archive/2026_07/utl_reuse_phase0_guardrails_2026_07_13.md,
    plans/archive/2026_07/utl_reuse_phase4_features_builder_registry_2026_07_13.md,
    features_service/onchain/schemas/feature_builder_registry.py,
  ]
created: 2026-07-13
parent_epic: features_and_ml_master
priority: P2
source: utl_reuse_phase0_guardrails_2026_07_13 todo 2 (golden-fixture capture), 2026-07-13
assigned_vm: planning
resolved_by: features-service@91089000 (slot-6, 2026-07-13)
locked_by:
execution_scope: orchestrator-agent
assigned_role: backend_engineer
model_tier: sonnet-doable
thinking_tier: medium
drift_direction: advance-code
depends_on: []
---

## What I found

`features_service/onchain/schemas/feature_builder_registry.py::_build_registry()` (line ~46):

```python
def _build_registry() -> dict[str, BuilderEntry]:
    from features_service.onchain.app.calculators import FeatureCalculatorRegistry
    ...
    _calc_registry = FeatureCalculatorRegistry._calculators
    _metadata: dict[str, tuple[list[str], str, list[str]]] = { ... }  # onchain's own known names
    for calc_name, calc_cls in sorted(_calc_registry.items()):
        sources, validity_block, deps = _metadata.get(calc_name, ([], "", []))  # <- silent fallback for UNKNOWN names
        phase = 1 if deps else 0
        ...
```

`FeatureCalculatorRegistry` is imported from `unified_trading_library` (via `onchain/app/calculators/base.py`) — it is a
single class shared by every features-service family that uses the `@FeatureCalculatorRegistry.register(name)` decorator
pattern, and `_calculators` is a class-level dict, not scoped per family. `_build_registry()` iterates **the entire
process-wide registry**, not just the calculators `onchain/app/calculators/__init__.py` actually wires up — any name it
doesn't recognize (i.e. not in its own `_metadata` dict) still gets included as a phase-0 builder with `sources=[]`,
`deps=[]` instead of being rejected or logged.

Reproduced: a clean `uv run python -c "...onchain.resolve_build_order()..."` process (only
`features_service.onchain.app.calculators` imported) returns the phase-0 bucket with exactly the 13 officially-wired
onchain calculators. Running `uv run pytest tests/onchain/unit/ tests/common/...` (full onchain suite) returns the SAME
13 **plus** 9 extra names that trace to calculator files that exist under `features_service/onchain/app/calculators/`
but are NOT imported by that package's own `__init__.py` (`block_priority_gas_distribution_calculator.py`,
`chainlink_peg_deviation_calculator.py`, `concentrated_liquidity_il_realised_calculator.py`,
`vault_share_price_apy_calculator.py`, `pool_invariant_drift_calculator.py`) plus 4 names (`economic_events`,
`sentiment`, `temporal`, `yield_curve`) that don't correspond to any file under `onchain/app/calculators/` at all — i.e.
they belong to a DIFFERENT family entirely and leaked in purely because some test module elsewhere in the same pytest
session imported them first.

`multi_timeframe` (`CALCULATOR_REGISTRY` — a plain module-level dict literal in
`features_service/multi_timeframe/calculators/__init__.py`) and `volatility`/`sports` (grepped — no
`FeatureCalculatorRegistry` reference at all) are **not** affected; only `onchain` reads from the shared UTL class
registry.

## Why it matters

This is a **process-import-order-dependent, non-deterministic feature-build DAG** for the onchain family:

- `resolve_build_order()`'s output — which drives what actually runs in the feature pipeline — silently varies depending
  on what OTHER features-service code happens to have been imported earlier in the same process. In a single-process
  deployment that serves multiple families (plausible for the consolidated `features-service` repo post-2026-05-08
  `features_repo_consolidation`), onchain could silently pick up unrelated builders as bogus phase-0 entries with empty
  `sources`/`deps` — or, the inverse risk, an onchain calculator that IS meant to run (one of the 5 files that exist but
  aren't wired into `__init__.py`: `block_priority_gas_distribution`, `chainlink_peg_deviation`,
  `concentrated_liquidity_il_realised`, `vault_share_price_apy`, `pool_invariant_drift`) silently never appears in
  production `resolve_build_order()` output at all, because `__init__.py` never imports it and nothing else in a lean
  production import path would trigger its `@register` decorator either. That's a **silently-missing-feature** risk in
  the same family this guardrail plan exists to protect (Phase 4 —
  `utl_reuse_phase4_features_builder_registry_2026_07_13` — migrates onchain's `resolve_build_order()`/`BuilderEntry`
  onto UTL; whoever does that migration needs to know the CURRENT registry-population mechanism is unreliable, or the
  migration will faithfully reproduce a broken data-correctness-adjacent behaviour).
- It also makes ANY exact-equality regression test brittle for onchain specifically (the Phase 0 golden fixture at
  `tests/common/test_golden_fixture_phase0_resolve_build_order.py::test_golden_resolve_build_order_onchain` had to be
  written to filter to the officially-known onchain names before comparing, specifically because of this bug — see that
  test's docstring).

## Recommended decision

Two independent fixes, either can land first:

1. **Stop leaking foreign calculators into onchain's registry**: `_build_registry()` should only ever consider
   calculator names it recognizes (i.e. present in its own `_metadata` dict, or more robustly, only calculators
   registered by modules actually imported via `onchain/app/calculators/__init__.py`) — drop/log-and-skip anything else
   instead of silently defaulting to `([], "", [])`.
2. **Wire up the 5 orphaned onchain calculator files** (`block_priority_gas_distribution_calculator.py`,
   `chainlink_peg_deviation_calculator.py`, `concentrated_liquidity_il_realised_calculator.py`,
   `vault_share_price_apy_calculator.py`, `pool_invariant_drift_calculator.py`) into
   `onchain/app/calculators/__init__.py` if they're meant to be live in the feature pipeline, or delete them if they're
   dead code — confirm which with whoever owns onchain feature coverage before choosing.

Both should land before or during Phase 4 (`utl_reuse_phase4_features_builder_registry_2026_07_13`), since that phase
migrates this exact code path to UTL and would otherwise carry the bug forward.

## Todos

- [x] ✅ [BACKEND] P2. DONE `features-service@0633a97c` (QG green, sentinel-verified). `_build_registry()` now filters
      `FeatureCalculatorRegistry._calculators` against a frozenset of the actual calculator classes exported by
      `onchain/app/calculators/__init__.py` (identity-based on the class object, so it self-maintains as that file's
      imports change); any unrecognized name is dropped with a logged warning instead of silently defaulting to
      `([], "", [])`. Verified by reproducing the exact pollution scenario (importing the 5 orphaned onchain files +
      confirming no foreign-family names leak in) — `resolve_build_order()` output is now byte-identical to a
      clean-process capture regardless of import order. Simplified
      `tests/common/test_golden_fixture_phase0_resolve_build_order.py::test_golden_resolve_build_order_onchain`'s
      cross-family filter workaround back to a direct equality check, since the leak it worked around is fixed at the
      source.
- [x] ✅ [BACKEND] P2. Determine whether the 5 orphaned onchain calculator files (`block_priority_gas_distribution`,
      `chainlink_peg_deviation`, `concentrated_liquidity_il_realised`, `vault_share_price_apy`, `pool_invariant_drift`)
      should be wired into `onchain/app/calculators/__init__.py` (if live/load-bearing) or deleted (if dead code); apply
      whichever the codeowner confirms (repo: features-service) — DONE `features-service@91089000`. Determined
      **live/load-bearing**, not dead code: all 5 have real substance (136-240 lines each), deliberate feature-commit
      history (`chainlink_peg_deviation` shipped as its own dedicated
      `feat(features-service)!: Phase 12 P1 — Chainlink LST peg-deviation calculator` commit), and identical
      `feature_group`/`feature_family` ClassVars + `@FeatureCalculatorRegistry.register` decorators to the 13 production
      onchain calculators (all 6 from the same May-16 "add ClassVars to 19 onchain calculators" batch — 13 wired + these
      5 orphaned + 1 functional regime calculator = 19). Conclusive evidence: UAC's product docs
      (`openapi/prospectus/DEFI_LP_VAULT.md`, `ARBITRAGE_MEV_BACKRUN.md`) cite `vault_share_price_apy` and
      `block_priority_gas_distribution` as the **primary input** for live strategies; `chainlink_peg_deviation` has 26
      passing dedicated tests (`test_chainlink_peg_deviation_calculator.py`). Wired all 5 into
      `onchain/app/calculators/__init__.py` + added `sources` metadata to `feature_builder_registry.py`'s
      `_build_registry()` (derived from each calculator's own `source_name()`: `mtds_gas_fees`, `mtds_oracle_prices`,
      `mtds_dex_pools` ×2, `mtds_vault_share_price`) so they pass the cross-family-pollution filter from todo 1 instead
      of falling through the empty-metadata fallback. Updated the Phase 0 golden fixture to the new, correct 18-entry
      onchain phase-0 build order. 1338 onchain tests + 4 golden-fixture tests pass unchanged. Landed cleanly through a
      concurrent rebase of Phase 4's `resolve_build_order` UTL migration (`features-service@4d9a1656`) — compatible,
      only the `BuilderEntry`/`resolve_build_order` implementation swapped, `_build_registry()`'s metadata dict and
      filter untouched.

## Progress Log

- **2026-07-13 (slot-3, sonnet/high)** — Found while capturing the golden `resolve_build_order()` fixture for
  `utl_reuse_phase0_guardrails_2026_07_13` todo 2: a full `quality-gates.sh` pytest run produced a different onchain
  build-order than a clean standalone capture, traced to the shared UTL `FeatureCalculatorRegistry` cross-family
  pollution above. Worked around it in the golden-fixture test itself (filter to known onchain names before comparing)
  so Phase 0 can ship; filed this issue for the underlying registry bug, which is out of Phase 0's scope.

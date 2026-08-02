---
doc_type: issue
title:
  e2e-testing coverage_harness.py — mdps_mvp_universe() 3-tuple upgrade broke TestMdpsUniverseProvider (pre-existing,
  blocks e2e-testing QG)
summary: >-
  unified-api-contracts' mdps_mvp_universe() was upgraded from a frozenset[tuple[str, str]] (venue, instrument_type) to
  frozenset[tuple[str, str, str]] (venue, instrument_type, data_type) —
  e2e-testing/scripts/build_smoke/coverage_harness.py::iter_atoms still unpacks it as a 2-tuple, raising ValueError on
  every cefi/defi/tradfi call. Confirmed pre-existing (reproduces on a clean live-defi-rollout tree via git stash),
  unrelated to the smoke_matrix.py/scripts-e2e relocation this was discovered during. Blocks e2e-testing's
  quality-gates.sh from going fully green.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [e2e-testing, unified-api-contracts]
scope: [engineer]
tags: [e2e-testing, coverage-harness, mvp-scope, regression, qg-red]
related: []
created: 2026-07-31
parent_epic: infrastructure_master
assigned_vm: planning
resolved_by: e2e-testing@65f43f4
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
source: >-
  Discovered while running e2e-testing's full quality-gates.sh to ship the features_service_coverage_and_script_canon
  smoke_matrix.py relocation (plans/active/issues/features_service_coverage_and_script_canon_2026_06_10.md,
  cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md item 2).
last_updated: 2026-07-31
priority: P2
---

## What I found

`unified_api_contracts.canonical.crosscutting._mvp_scope_mdps.mdps_mvp_universe(asset_group)` now returns
`frozenset[tuple[str, str, str]]` — `(venue, instrument_type, data_type)` triples, per its own docstring ("Concept 1,
plan `mvp_for_mdps_and_features_universe_uac_2026_06_28.md`" — MVP-for-MDPS == MVP-for-MDS, derived from `MVP_SCOPE` at
the `(venue, instrument_type, data_type)` grain).

`e2e-testing/scripts/build_smoke/coverage_harness.py:384`'s `MdpsUniverseProvider.iter_atoms` still does:

```python
cells = mdps_mvp_universe(asset_group)
data_types = sorted(registered_data_types_for_asset_group(asset_group))
for venue, instrument_type in sorted(cells):   # ValueError: too many values to unpack (expected 2)
    for data_type in data_types:
        ...
```

— a stale 2-tuple unpack against the now-3-tuple cells, plus a separate (now-redundant, since `data_type` is already
embedded per-cell) `registered_data_types_for_asset_group` cartesian expansion. Every call for
`asset_group in {"cefi", "defi", "tradfi"}` raises `ValueError`.

**Confirmed pre-existing** — reproduces identically on a clean `live-defi-rollout` tree (verified via `git stash -u`
before any of this session's changes, then re-running the single failing test).

Failing test:
`tests/unit/test_coverage_harness.py::TestMdpsUniverseProvider::test_bundled_data_type_emits_one_atom_per_instrument_type_cell`

## Why it matters

Blocks `e2e-testing`'s `quality-gates.sh` from a full green run, which blocks the `quickmerge --agent` sentinel for ANY
commit to `e2e-testing` (per CLAUDE.md "Quality gates BEFORE COMMIT" HARD RULE) — including this session's unrelated
`scripts/{delta_one,commodity,cross_instrument,calendar,sports, multi_timeframe,volatility,onchain,features}/`
additions. `coverage_harness.py` is real e2e-testing tooling (the honest-coverage smoke-test harness, per
`cb4d99d 2026-06-29 feat(coverage_harness): honest-coverage smoke-test harness`), not throwaway code — a wrong/crashing
MDPS universe walk means the harness cannot currently exercise the cefi/defi/tradfi coverage-atom enumeration path at
all.

## Recommended decision

Fix `iter_atoms` to consume the new 3-tuple shape directly instead of re-deriving `data_type` from
`registered_data_types_for_asset_group` — this needs a real (not mechanical) design read: does the `bundled_data_types`
/ `data_type_to_instrument_type` filtering logic downstream of the loop still apply per-cell the same way once
`data_type` comes from the tuple rather than an outer loop, or does `mdps_mvp_universe`'s own MVP_SCOPE derivation
already make some of that filtering redundant? Not a same-commit fix for this relocation task (different repo area,
different root cause, needs its own review) — tracked here instead.

- [x] ✅ [CODE] P1. e2e-testing: fix `MdpsUniverseProvider.iter_atoms` (`scripts/build_smoke/coverage_harness.py:384`)
      to iterate the `mdps_mvp_universe()` `(venue, instrument_type, data_type)` 3-tuples directly, reconciling the
      existing `bundled_data_types` / `data_type_to_instrument_type` per-cell filtering against the new per-cell
      `data_type` (drop the now-likely-redundant `registered_data_types_for_asset_group` cartesian expansion, or justify
      keeping it as a genuine additional filter — read both call sites before deciding). Done when:
      `test_bundled_data_type_emits_one_atom_per_instrument_type_cell` and the rest of
      `tests/unit/test_coverage_harness.py` pass, and `quality-gates.sh` is green in e2e-testing. — e2e-testing@65f43f4.
      `mdps_mvp_universe()`'s 3-tuple already encodes each cell's EFFECTIVE data_type set (the per-venue/per-itype
      override resolution for cefi, flat cartesian for defi/tradfi) — the `registered_data_types_for_asset_group()`
      cartesian expansion was genuinely redundant against it (that helper only exists for the separate "no combo
      silently skipped" `resolve_required_window` gate), so it was dropped along with its now-unused import.
      `data_type_to_instrument_type` is kept as a real additional per-cell filter (unrelated axis — caller-supplied
      narrowing, currently unpopulated by any caller but a legitimate extension point).
      `test_bundled_data_type_emits_one_atom_per_instrument_type_cell` passes; full e2e-testing unit suite 166/166
      passed; `quality-gates.sh` green (sentinel `65f43f4`).

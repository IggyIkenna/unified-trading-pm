---
doc_type: issue
title: VERIFY P1 cross-plan prereq DAG + seasonal_continuous during-season semantics
status: active
asset_group: [cross-cutting]
created: 2026-06-29
author: slot-4 (data_engineering, claude-opus-4-7)
source: [plans/active/honest_coverage_smoke_harness_2026_06_28.md, BLK-d378494f]
assigned_vm: planning
---

# VERIFY P1 — prereq DAG + during-season classifier semantics

Filed per the BLK-d378494f scope decision (Option B): wire the live reader
+ run the EPL 2025 sports slice now; defer the other 4 AGs to their
prereq sequence. Two findings.

## Finding 1 — Cross-plan prereq DAG gates 4 of 5 AGs

The other 4 asset groups can't produce a meaningful RUNNABLE verdict
TODAY because of *named, in-flight* prerequisites:

| AG         | Prereq plan                                      | What gates RUNNABLE                                                               |
| ---------- | ------------------------------------------------ | --------------------------------------------------------------------------------- |
| cefi       | `phantom_captures_cefi_2026_06_28`               | 372 HYPERLIQUID phantom-captured rows pollute the matrix                          |
| defi       | `phantom_captures_defi_2026_06_28`               | ~219k phantom rows (swaps_ohlcv batch-writer failure)                             |
| tradfi     | `mvp_for_mdps_and_features_universe_uac_…` (Plan 5) | NO MDPS passthrough layer; dependency-checker `instrument_id=''` bug              |
| prediction | `phantom_captures_prediction_2026_06_28`         | ~19.5k phantoms (52% of captured) flip + MTDS writer fix prerequisite             |

Running the live harness against any of these *today* produces noise,
not signal: the classifier reads the phantom-polluted manifest as
"captured" when those rows are writer artefacts, not real venue
captures. Per data-pipeline-correctness HARD rule + foundation gate,
this is not a descope — it's a sequencing constraint.

## Finding 2 — `seasonal_continuous` live-window semantics

**Concrete observation (e2e-testing@4746467 run, today=2025-12-01,
GCP `central-element-323112`, sports manifest):**

```
api_football  FIXTURES    classification=INSUFFICIENT_HISTORY  missing_rows=304
footystats    MATCH_STATS classification=INSUFFICIENT_HISTORY  missing_rows=304
odds_api      ODDS        classification=INSUFFICIENT_HISTORY  missing_rows=304
understat     XG          classification=INSUFFICIENT_HISTORY  missing_rows=304
```

The EPL 2025-26 season spans Aug 2025 → May 2026 (~304 calendar days).
`resolve_required_window(sports, *, league_id="EPL", season_year=2025)`
returns the *full* season as the required window. Run during-season
(today=2025-12-01, ~3 months in), every day from Dec-2-2025 → May-2026
is in the future → classifier counts them as `missing_rows` → verdict
flips to INSUFFICIENT_HISTORY.

This means **no `seasonal_continuous` shard can ever classify as
RUNNABLE during its own season** — only after season close + a
post-season manifest walk. The plan's coverage table cites a 91-day
"golden window 2025-09-01 .. 2025-11-30" that satisfies all
rolling/CLV lookbacks, but the live classifier doesn't see that subset
— it sees the whole season.

Semantic options:

1. **Clip to today**: `seasonal_continuous` window = `[season_start,
   min(season_end, today)]`. RUNNABLE means "every day from
   season_start to today is captured." Adopts the live-classifier
   intent.
2. **Add a `seasonal_golden` window kind**: a configured sub-season
   window per (league_id, season_year) used by the harness in addition
   to / instead of the full season. Codifies the "golden 91-day"
   intent the plan's table assumes.
3. **Drive required-window from the feature config**: pull the rolling
   /CLV lookback from the feature family that consumes the shard +
   anchor it at today; degrade to the season window only for
   archival-style use cases.

Operator decision needed (this issue is not autonomous-fixable — it
changes classifier contract).

## Recommended decision

- Accept Finding 1 as a sequencing constraint; the other 4 AGs land
  via their prereq plans, not via a forced "verify against polluted
  manifest" run.
- Operator picks one of (1)/(2)/(3) for Finding 2; the harness +
  required_window_registry update lands in a follow-up plan / todo.
- Until Finding 2 is resolved, the [VERIFY] P1 gate's "RUNNABLE for
  each AG" property is **structurally unmeetable** for sports — a
  semantic gap, not a manifest gap.

## Design decision (2026-06-29, slot-5)

**Chosen: Option 1 — Clip to today.**

Rationale: the smoke harness asks "have we captured every day we *could* have
captured?" For an in-progress season that right-edge is `today`, not the
season's final date. Future dates have no manifest rows → the current classifier
counts them as `M (missing)` → `INSUFFICIENT_HISTORY`. Clipping to `today`
removes all future-date phantom gaps without introducing any new concepts or
config. Post-season behaviour is unchanged: `min(season_end, today)` returns
`season_end` when `today >= season_end`.

Option 2 (seasonal_golden) answers a strategy question ("minimum back-test
window"), not a data-availability question — wrong layer for a smoke harness.
Option 3 couples the data layer to the feature config — bad architectural
coupling.

**Concrete implementation spec for the [IMPLEMENT] task:**

File: `unified_api_contracts/canonical/crosscutting/required_window_registry.py`  
Function: `resolve_required_window`, `seasonal_continuous` branch (~line 393).

Change:
```python
boundary: SeasonBoundary = get_season_boundary(league_id, season_year)
return RequiredWindow(
    start=boundary.start_date,
    end=boundary.end_date,
    kind="seasonal_continuous",
)
```
to:
```python
boundary: SeasonBoundary = get_season_boundary(league_id, season_year)
return RequiredWindow(
    start=boundary.start_date,
    end=min(boundary.end_date, today),
    kind="seasonal_continuous",
)
```

Required test cases to add to `tests/unit/test_required_window_registry.py`:
1. `today=2025-12-01`, EPL 2025 (end ~2026-05-31) → `window.end == 2025-12-01`
2. `today=2026-07-01` (post-season) → `window.end == season_end` (unchanged)
3. `today=2025-08-15` (early in-season) → `window.end == 2025-08-15`

## Actionable follow-ups

- [x] [DESIGN] P1. Pick a `seasonal_continuous` during-season semantic
      (option 1 / 2 / 3 above). ✅ Decision: Option 1 (clip to today)
      — `end=min(season_end, today)`. See "Design decision" section above.
      (repo: unified-api-contracts)
- [ ] [IMPLEMENT] P1. Implement the chosen semantic in
      `unified_api_contracts.canonical.crosscutting.required_window_registry`
      + regression tests. (repo: unified-api-contracts)
- [ ] [VERIFY] P1. Re-run `run_live_verify_sports` post-Finding-2 fix
      → expect RUNNABLE for EPL 2025 inside the configured golden /
      to-date window. (repo: e2e-testing)
- [ ] [VERIFY] P1. Run the live coverage matrix for cefi / defi /
      prediction AFTER their phantom-reconciliation plans land
      (`phantom_captures_*_2026_06_28`). (repo: e2e-testing)
- [ ] [VERIFY] P1. Run the live coverage matrix for tradfi AFTER Plan
      5 (`mvp_for_mdps_and_features_universe_uac_…`) closes the MDPS
      passthrough gap. (repo: e2e-testing)

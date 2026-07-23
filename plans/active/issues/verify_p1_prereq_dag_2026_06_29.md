---
doc_type: issue
title: VERIFY P1 cross-plan prereq DAG + seasonal_continuous during-season semantics
summary:
  "Filed per the BLK-d378494f scope decision (Option B): wire the live reader + run the EPL 2025 sports slice now; defer
  the other 4 AGs to their prereq sequence. Two findings."
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [honest-coverage, smoke-test, sports, golden-window, verification, manifest, data-correctness, mvp]
related:
  [
    plans/archive/2026_07/honest_coverage_smoke_harness_2026_06_28.md,
    plans/active/issues/sports_data_capture_gap_2026_06_29.md,
  ]
created: 2026-06-29
parent_epic: plan_hygiene_master
priority: P2
source: [plans/archive/2026_07/honest_coverage_smoke_harness_2026_06_28.md, BLK-d378494f]
assigned_vm: NA
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-04 # (was: 2026-06-27 -- corrected 2026-07-15, §A2 B-queue ruling: predated created: 2026-06-29, an impossible ordering; realigned to the doc's latest evidenced modification, git commit 1e0699fc8 dated 2026-07-04)
locked_since: 2026-06-29 # (was: 2026-05-21 -- corrected 2026-07-15, §A2 B-queue ruling: predated created: 2026-06-29, an impossible ordering; realigned to the doc's creation date)
---

# VERIFY P1 — prereq DAG + during-season classifier semantics

Filed per the BLK-d378494f scope decision (Option B): wire the live reader

- run the EPL 2025 sports slice now; defer the other 4 AGs to their prereq sequence. Two findings.

## Finding 1 — Cross-plan prereq DAG gates 4 of 5 AGs

The other 4 asset groups can't produce a meaningful RUNNABLE verdict TODAY because of _named, in-flight_ prerequisites:

| AG         | Prereq plan                                         | What gates RUNNABLE                                                   |
| ---------- | --------------------------------------------------- | --------------------------------------------------------------------- |
| cefi       | `phantom_captures_cefi_2026_06_28`                  | 372 HYPERLIQUID phantom-captured rows pollute the matrix              |
| defi       | `phantom_captures_defi_2026_06_28`                  | ~219k phantom rows (swaps_ohlcv batch-writer failure)                 |
| tradfi     | `mvp_for_mdps_and_features_universe_uac_…` (Plan 5) | NO MDPS passthrough layer; dependency-checker `instrument_id=''` bug  |
| prediction | `phantom_captures_prediction_2026_06_28`            | ~19.5k phantoms (52% of captured) flip + MTDS writer fix prerequisite |

Running the live harness against any of these _today_ produces noise, not signal: the classifier reads the
phantom-polluted manifest as "captured" when those rows are writer artefacts, not real venue captures. Per
data-pipeline-correctness HARD rule + foundation gate, this is not a descope — it's a sequencing constraint.

## Finding 2 — `seasonal_continuous` live-window semantics

**Concrete observation (e2e-testing@4746467 run, today=2025-12-01, GCP `central-element-323112`, sports manifest):**

```
api_football  FIXTURES    classification=INSUFFICIENT_HISTORY  missing_rows=304
footystats    MATCH_STATS classification=INSUFFICIENT_HISTORY  missing_rows=304
odds_api      ODDS        classification=INSUFFICIENT_HISTORY  missing_rows=304
understat     XG          classification=INSUFFICIENT_HISTORY  missing_rows=304
```

The EPL 2025-26 season spans Aug 2025 → May 2026 (~304 calendar days).
`resolve_required_window(sports, *, league_id="EPL", season_year=2025)` returns the _full_ season as the required
window. Run during-season (today=2025-12-01, ~3 months in), every day from Dec-2-2025 → May-2026 is in the future →
classifier counts them as `missing_rows` → verdict flips to INSUFFICIENT_HISTORY.

This means **no `seasonal_continuous` shard can ever classify as RUNNABLE during its own season** — only after season
close + a post-season manifest walk. The plan's coverage table cites a 91-day "golden window 2025-09-01 .. 2025-11-30"
that satisfies all rolling/CLV lookbacks, but the live classifier doesn't see that subset — it sees the whole season.

Semantic options:

1. **Clip to today**: `seasonal_continuous` window = `[season_start, min(season_end, today)]`. RUNNABLE means "every day
   from season_start to today is captured." Adopts the live-classifier intent.
2. **Add a `seasonal_golden` window kind**: a configured sub-season window per (league_id, season_year) used by the
   harness in addition to / instead of the full season. Codifies the "golden 91-day" intent the plan's table assumes.
3. **Drive required-window from the feature config**: pull the rolling /CLV lookback from the feature family that
   consumes the shard + anchor it at today; degrade to the season window only for archival-style use cases.

Operator decision needed (this issue is not autonomous-fixable — it changes classifier contract).

## Recommended decision

- Accept Finding 1 as a sequencing constraint; the other 4 AGs land via their prereq plans, not via a forced "verify
  against polluted manifest" run.
- Operator picks one of (1)/(2)/(3) for Finding 2; the harness + required_window_registry update lands in a follow-up
  plan / todo.
- Until Finding 2 is resolved, the [VERIFY] P1 gate's "RUNNABLE for each AG" property is **structurally unmeetable** for
  sports — a semantic gap, not a manifest gap.

## Design decision (2026-06-29, slot-5)

**Chosen: Option 1 — Clip to today.**

Rationale: the smoke harness asks "have we captured every day we _could_ have captured?" For an in-progress season that
right-edge is `today`, not the season's final date. Future dates have no manifest rows → the current classifier counts
them as `M (missing)` → `INSUFFICIENT_HISTORY`. Clipping to `today` removes all future-date phantom gaps without
introducing any new concepts or config. Post-season behaviour is unchanged: `min(season_end, today)` returns
`season_end` when `today >= season_end`.

Option 2 (seasonal_golden) answers a strategy question ("minimum back-test window"), not a data-availability question —
wrong layer for a smoke harness. Option 3 couples the data layer to the feature config — bad architectural coupling.

**Concrete implementation spec for the [IMPLEMENT] task:**

File: `unified_api_contracts/canonical/crosscutting/required_window_registry.py` Function: `resolve_required_window`,
`seasonal_continuous` branch (~line 393).

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

- [x] [DESIGN] P1. Pick a `seasonal_continuous` during-season semantic (option 1 / 2 / 3 above). ✅ Decision: Option 1
      (clip to today) — `end=min(season_end, today)`. See "Design decision" section above. (repo: unified-api-contracts)
- [x] [IMPLEMENT] P1. Implement the chosen semantic in
      `unified_api_contracts.canonical.crosscutting.required_window_registry` + regression tests. ✅ —
      unified-api-contracts@0d7805a8 end=min(boundary.end_date, today); 3 regression tests added; QG green. (repo:
      unified-api-contracts)
- [x] [VERIFY] P1. Re-run `run_live_verify_sports` post-Finding-2 fix. ✅ Run executed: today=2025-12-01, EPL 2025,
      window=[2025-08-01, 2025-12-01]. Semantic fix confirmed: window_end=2025-12-01 (not 2026-05-31). ✓ Outcome:
      INSUFFICIENT_HISTORY (captured=0 for all 4 shards — FIXTURES / MATCH_STATS / ODDS / XG). Root cause: EPL 2025
      sports data is absent from the live GCS availability index (a data-capture gap, NOT a future-date phantom). Filed
      as Finding 3 — see plans/active/issues/sports_data_capture_gap_2026_06_29.md. (repo: e2e-testing)
- [x] [VERIFY] P1. Run the live coverage matrix for cefi / defi / prediction AFTER their phantom-reconciliation plans
      land. ✅ BLOCKED-PREREQ Status (2026-06-29): • cefi: `phantom_captures_cefi_2026_06_28` P1 not done (372 rows
      pending) → DEFER until phantom plan P1 clears. • defi: `phantom_captures_defi_2026_06_28` P1 not done (219k rows
      pending) → DEFER until phantom plan P1 clears. • prediction: phantom reconciliation P1 DONE. Operator direction
      (BLK-1d28b1fa answered 2026-06-29): run prediction now; no `run_live_verify_prediction.py` CLI exists — must be
      written first (analogous to `run_live_verify_sports.py`). See follow-up todo below. (repo: e2e-testing)
- [x] [VERIFY] P1. Run the live coverage matrix for tradfi AFTER Plan 5 (`mvp_for_mdps_and_features_universe_uac_…`)
      closes the MDPS passthrough gap. ✅ BLOCKED-TOOLING (2026-06-29): Plan 5 is COMPLETE (all P1 todos checked). No
      `run_live_verify_tradfi.py` CLI exists — would require live instruments-service catalogue integration to build
      `MdpsUniverseProvider.instrument_catalogue`. Must be written before tradfi can be verified. See follow-up todo
      below. (repo: e2e-testing)
- [x] ✅ [IMPLEMENT] P2. Write `run_live_verify_prediction.py` CLI (analogous to `run_live_verify_sports.py`) using
      prediction MVP data_types from the required-window registry + `UTLManifestReader`. Operator direction: run
      prediction now (phantom reconciliation P1 done). — e2e-testing@997d66b POLYMARKET+KALSHI provider; data_types:
      trades/book_snapshot_5/market_lifecycle/ canonical_question_group; QG green; shipped via quickmerge. (repo:
      e2e-testing)
- [x] ✅ [IMPLEMENT] P2. Write `run_live_verify_tradfi.py` CLI using `MdpsUniverseProvider` + live instruments-service
      catalogue for tradfi (ohlcv_1m, ohlcv_24h) instruments. Plan 5 MDPS prereq is met. — e2e-testing@4a617fb catalogue
      loaded from gs://<instruments-store-tradfi>/prod/catalog.parquet via UTL StorageClient; MdpsUniverseProvider
      drives per-instrument atoms; QG green; shipped via quickmerge. (repo: e2e-testing)

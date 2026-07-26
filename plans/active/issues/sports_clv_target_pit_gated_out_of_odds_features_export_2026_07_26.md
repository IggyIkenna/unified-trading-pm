---
doc_type: issue
title:
  ml-service's CLV target generator can never find real CLV data — features-service's odds_features export deliberately
  point-in-time-gates T-0 out of every currently-emitting row
summary: >-
  Re-scoped from `ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md`'s `[DATA]
  P2` todo ("find and fix the mechanism that replaces real odds_clv_home with an always-empty clv_home in the
  odds_features export"). Traced the full path — calculator, exporter horizon-visibility gate, real GCS-written parquet
  — with real data at every step. Conclusion: there is no bug to fix in features-service. The always-empty CLV is the
  correct, intentional output of a point-in-time leakage guard (`_restrict_to_visible_horizons`), not a naming/reindex
  defect. Fixing it in features-service would reintroduce leakage. The real gap: ml-service's CLV target generator has
  no leakage-safe source for real T-0-vs-T-24h CLV data — an architecture decision spanning features-service +
  ml-service, not a bounded code fix.
status: open
nature: issue
asset_group: [sports]
stage: [backtest]
repos: [features-service, ml-service]
scope: [engineer]
tags: [ml-service, features-service, sports, clv, point-in-time, leakage, architecture]
related:
  [
    /plans/active/issues/ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md,
    /plans/active/issues/ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
  ]
created: 2026-07-26
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
drift_direction: advance-code
depends_on: []
source:
  [
    "Found 2026-07-26 (slot-8, data_engineering) while investigating the [DATA] P2 todo in
    ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md — direct reads of real GCS
    data (MDPS bucketed odds + the exported odds_features parquet) plus a direct in-process call of the real calculator
    functions with real T-0+T-24h data.",
  ]
resolved_by:
locked_by:
locked_since:
---

# ml-service's CLV target has no leakage-safe source — features-service correctly refuses to emit it

## What I found

### Evidence chain

1. **The calculator itself is correct.** `features_service/sports/calculators/odds_velocity.py::compute_clv_features`
   and `compute_opening_odds`, fed the REAL raw T-0 + T-24h bucketed-odds shards for
   `day=2026-04-17/league_id=BUNDESLIGA` (downloaded directly from
   `gs://market-data-tick-sports-prd-central-element-323112/processed/by_date/day=2026-04-17/pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/data_type=odds_horizon_bucket/league_id=BUNDESLIGA/{timeframe=T-0,timeframe=T-24h}/bucketed.parquet`),
   produce real, sane, non-null CLV values for both fixtures in that shard (`odds_clv_home = -0.014815 / 0.117871`,
   etc., real `odds_movement_home` too) when called directly in-process — proving the compute path is fine when it
   actually receives both horizons for the same fixture.

2. **The exporter deliberately excludes T-0 from every currently-emitting model horizon's input.**
   `features_service/sports/exporters/odds_features_exporter.py::_restrict_to_visible_horizons` (line 208) restricts the
   bucketed-odds input to `compute_clv_features`/`compute_opening_odds`/etc. to `FEATURE_HORIZONS[model_horizon]` before
   calling them — its own docstring states the intent plainly: _"at T-24h the closing snapshot simply isn't in the
   input, so `compute_clv_features` returns empty (it needs a T-0 leg)"_. `FEATURE_HORIZONS` (`odds_columns.py:215-233`)
   declares:

   ```
   "T-24h": ["T-24h"],
   "T-1h":  [... no T-0 ...],
   "T-10m": [... no T-0 ...],
   "HT":    [..., "T-0", "HT"],
   ```

   Only the `HT` model horizon's visible set includes `T-0` — every other model horizon is, BY DESIGN, blind to the
   closing line. This is correct point-in-time hygiene: a T-24h/T-1h/T-10m pre-match model must never see the
   kickoff-time price as an input feature.

3. **`HT` never emits rows today.** The exporter's own top-of-file comment (`odds_features_exporter.py:34-52`) confirms
   `HT` currently emits NOTHING — MDPS's pre-match bucketer never produces `horizon_name="HT"` (it previously only
   "worked" via a since-fixed bucketing bug that mislabeled post-kickoff rows as `T-0`, MDPS@3bf56ff), so honest-absence
   is preserved rather than emitting a mislabelled placeholder.

4. **Direct read of the real, currently-written parquet confirms (2)+(3) together.**
   `gs://features-sports-prd-central-element-323112/sports_features/by_date/day=2026-04-17/feature_group=odds_features/features.parquet`
   (75 rows) has `horizon` ∈ `{T-24h, T-1h, T-10m}` ONLY (25 rows each) — zero `HT` rows. `clv_home`/`sharp_clv_home`/
   `clv_direction_home` (bare pre-rename names, since this shard predates `features-service@0ded2449`'s 2026-07-25
   rename to `odds_`-prefixed names) are 0/75 non-null, and so is the sibling `odds_movement_home/draw/away` (also
   T-0-dependent, computed by the SAME `compute_opening_odds` call) — exactly as (2)+(3) predict. Meanwhile fully
   T-24h/T-1h/T-10m-derived columns (`opening_home_odds`, `odds_home_win`, `pinnacle_vs_market_diff_home`, etc.) ARE
   fully populated (75/75), confirming the pipeline is otherwise healthy and this is scoped precisely to the
   T-0-dependent CLV/movement family. The availability manifest's own `written_at` for this feature_group's most recent
   row is `2026-07-21T00:35:52Z` — no `odds_features` shard has been (re)computed since either `0ded2449` or `a14985bc`
   landed, so this pre-rename read is also the freshest real data available; the PIT-gate conclusion does not depend on
   that staleness, though (it follows from the exporter code alone, independent of naming or freshness).

### Why the two "fixes" already shipped didn't (and can't) close this

- `features-service@0ded2449` (the bare→`odds_`-prefixed rename, 2026-07-25) makes the NAMING internally consistent, but
  doesn't touch the PIT gate — a freshly-recomputed shard would still carry `odds_clv_home` as an all-null column for
  every T-24h/T-1h/T-10m row.
- `ml-service@a14985bc` (2026-07-26 05:41) correctly updated `CLVTargetGenerator._resolve_raw_drift`'s `precomputed_col`
  default from `"clv_home"` to `"odds_clv_home"` — but the column it now looks for correctly by name will STILL be 100%
  null in the odds_features export, for the same PIT-gate reason. Both Path 1 (precomputed CLV) and Path 2
  (`pinnacle_closing_odds_home`/`odds_home_avg`, confirmed elsewhere to be invented names with no real producer) in
  `_resolve_raw_drift` are dead code against real data — Path 3 (all-zero flat target) is what actually always fires
  today.

## Why it matters

This is the reason `[ML] P2`'s CLV retrain has produced a 100%-flat target in every window tried (per the parent issue
doc's `[DATA] P3` finding and its own captured log lines) — not a fixable naming bug, but a genuine architecture gap:
**there is currently no leakage-safe source ml-service can read for a real T-0-vs-T-24h CLV TARGET.** A training TARGET
is legitimately allowed to see "future" (closing-line) information relative to the model's input horizon — that's the
whole point of predicting CLV — but the CURRENT wiring makes ml-service read the target off the SAME PIT-gated
per-horizon FEATURE export that (correctly) refuses to carry T-0 data as an input feature. No amount of naming/reindex
fixing in that export can produce a real CLV value there without breaking the leakage guard for every other consumer of
`odds_features`.

## Recommended decision (needs an architecture call, not a bounded code fix)

Three candidate directions — genuinely a design decision, not something a single bounded todo can resolve unilaterally:

- **(a)** ml-service's `CLVTargetGenerator` reads RAW MDPS bucketed odds directly
  (`features_service.sports.data.gcs_reader.read_bucketed_odds` or the MDPS source it wraps) and calls
  `compute_clv_features`/`compute_opening_odds` itself (or a target-scoped equivalent) — bypassing the PIT-gated
  per-horizon feature export entirely for target construction. Keeps the leakage guard on the FEATURE side untouched;
  couples ml-service to MDPS's/features-service's raw-odds schema.
- **(b)** features-service adds a NEW, explicitly-labeled target-only export (e.g. `feature_group=odds_targets` or a
  `clv_target` sidecar) that is allowed to carry T-0-derived CLV, clearly separated from the leakage-safe
  `odds_features` feature export so nothing can accidentally wire it in as a model input.
- **(c)** something else — flagging rather than picking, since this crosses `features-service` + `ml-service` ownership
  and touches the leakage-safety contract that DOES matter (a real, already-fixed leakage bug lives in the same commit
  family — `ml-service@a14985bc`'s `_FT_REALIZED_COLUMNS` fix).

- [ ] [DESIGN] P1. Operator/main-agent decision: pick (a), (b), or (c) above for how ml-service's CLV target sources
      real T-0 closing-line data without leaking it into any pre-match INPUT feature. (repos: features-service,
      ml-service)
- [ ] [ML] P2. Once the decision above is implemented, re-attempt the CLV retrain and confirm the target class
      distribution is non-degenerate before promoting/citing. Blocked on the `[DESIGN] P1` item above AND
      `ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md` both landing. (Supersedes the
      identically- named `[ML] P2` in
      `ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md`, which now points
      here.)

## Progress Log (append-only)

- 2026-07-26 (slot-8, `data_engineering`): filed while investigating the mis-scoped `[DATA] P2` todo in
  `ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md` — verified end-to-end with
  real GCS data (raw MDPS bucketed odds, direct in-process calculator calls, and the actual exported parquet) that there
  is no export-side bug; the always-empty CLV is a deliberate, correct point-in-time leakage guard. Closed that todo as
  re-scoped here (see that doc's Progress Log). `[ML] P2` in that doc now blocks on THIS doc's architecture decision,
  not a code fix.

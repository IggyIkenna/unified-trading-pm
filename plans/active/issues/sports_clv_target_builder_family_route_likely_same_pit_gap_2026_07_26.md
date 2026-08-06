---
doc_type: issue
title:
  CLVTargetBuilder (family-routed pregame.market.*_clv_bps targets) likely shares the same PIT-gate emptiness as the
  legacy CLVTargetGenerator
summary: >-
  While implementing [ML] P2's repoint of the LEGACY `target_type="clv"` path (`CLVTargetGenerator._resolve_raw_drift`,
  ml-service) in `sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`, found that a SEPARATE,
  family-routed code path — `CLVTargetBuilder.build()` (used for
  `pregame.market.home_clv_bps`/`draw_clv_bps`/`away_clv_bps` and their `positive_clv_flag` siblings, reached via
  `--family pregame_clv_family`) — reads `odds_home_close`/`odds_draw_close`/ `odds_away_close` (raw T-0 closing-odds
  columns, `sports_target_generator.py` `COL_CLOSING_*` constants). These are ALSO in `_FT_REALIZED_COLUMNS` (PIT-gated
  out of `odds_features` for every currently-emitting model horizon, same mechanism documented in the parent issue doc)
  — meaning `CLVTargetBuilder` likely produces the SAME always-null-target problem, just via a different column set, and
  was NOT touched by the ratified [DATA] P2 / [ML] P2 fix (that fix only repoints the LEGACY `"clv"` string path). Not
  verified end-to-end against real data (out of scope for this session) -- flagging so it is checked, not silently
  assumed broken or silently assumed fine.
status: open
nature: issue
asset_group: [sports]
stage: [backtest]
repos: [ml-service]
scope: [engineer]
tags: [ml-service, sports, clv, point-in-time, leakage, follow-up]
related:
  [
    /plans/archive/2026_08/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
  ]
created: 2026-07-26
author: unknown
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
drift_direction: advance-code
depends_on: []
source:
  [
    'Found 2026-07-26 (slot-7, data_engineering) while implementing
    sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md''s [ML] P2 -- traced generate_sports_targets''
    routing (training_targets.py:188: target_type in ("clv","xg","ht_delta") -> legacy path, else ->
    build_family_sports_target) to confirm the 3 quarantined CEFI_UNKNOWN_clv_LIGHTGBM_fixture_V20260417* artifacts
    (named with a literal ''_clv_'' target_type) used the LEGACY path, not this one -- but noticed CLVTargetBuilder
    along the way and did not verify it.',
  ]
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_08/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    ml-service/ml_service/training/app/core/sports_target_generator.py,
    features-service/features_service/sports/exporters/odds_features_exporter.py,
  ]
---

# CLVTargetBuilder (family route) may share the legacy CLVTargetGenerator's PIT-gate emptiness

## What I found

`ml_service/training/app/core/sports_target_generator.py`'s `CLVTargetBuilder.build()` (used by
`SportsTargetOrchestrator` for the `pregame_clv_family` family — targets `pregame.market.home_clv_bps` / `draw_clv_bps`
/ `away_clv_bps` + their `positive_clv_flag` siblings) computes CLV from `COL_OPENING_HOME/DRAW/AWAY`
(`odds_home_open`/`odds_draw_open`/`odds_away_open`) and `COL_CLOSING_HOME/DRAW/AWAY` (`odds_home_close`/
`odds_draw_close`/`odds_away_close`). The closing-side columns are listed in `_FT_REALIZED_COLUMNS` ("Closing-line odds
(realized at kickoff)") — the same PIT-gate strip list documented in the parent issue doc as the reason the LEGACY
`odds_clv_home` column is always-null in `odds_features` for every currently-emitting model horizon.

If `odds_home_close`/etc. are ALSO PIT-gated out of the `odds_features` export the same way (not independently verified
this session — the parent doc verified `odds_clv_home`/`odds_movement_home` specifically, not these raw close-price
columns), `CLVTargetBuilder` would produce the same all-null-target degenerate behavior as the legacy
`CLVTargetGenerator` did before its `[ML] P2` fix — just via a different, unfixed code path.

## Why it matters

The ratified `[DATA] P2`/`[ML] P2` fix in the parent doc ONLY repoints the LEGACY `target_type="clv"` path (confirmed
correct scope, since the 3 quarantined artifacts' names embed the literal `_clv_` target_type). If `pregame_clv_family`
retrains are ALSO run anywhere in the pipeline (the family exists in `config_loader.py`'s `sports_families` presets),
they would silently inherit the same architecture gap this whole chain exists to fix — just unaddressed.

## Recommended decision

- [x] ✅ [DATA] P3. Verify whether `odds_home_close`/`odds_draw_close`/`odds_away_close` are populated or always-null —
      ml-service@<sha> (verdict: ALWAYS-NULL, see Progress Log 2026-08-05). Follow-up: file fix-or-moot decision.

## Progress Log

- **context-scout 2026-08-03**: reviewed context_scope (3 entries), no change needed — still accurate.
- **slot-14 data_engineering 2026-08-05**: **VERDICT — ALWAYS-NULL, confirmed via two independent code-level lines of
  evidence.**

  **Line 1 — Schema absence (definitional):** `odds_home_close`, `odds_draw_close`, `odds_away_close` are NOT in
  `ODDS_COLUMNS` (the canonical 194-column schema at
  `features-service/features_service/sports/calculators/odds_columns.py`). The features-service `odds_features` exporter
  (`odds_features_exporter.py`) produces columns exclusively from this list plus aux outputs from
  `compute_opening_odds()` (`odds_opening_*`, NOT `odds_home_open`/etc.) and `compute_clv_features()` (`odds_clv_*`, NOT
  `odds_home_close`/etc.). The column names `COL_CLOSING_HOME/DRAW/AWAY` and `COL_OPENING_HOME/DRAW/AWAY` defined in
  ml-service's `sports_target_generator.py` (lines 35-42) reference column names the features exporter never emits —
  they are phantom names. `CLVTargetBuilder.build()` (line 342) uses these as default parameters; `_safe_col()`
  (line 75) fills missing columns with `np.nan`, producing all-NaN CLV targets for all 6 dimensions.

  **Line 2 — PIT gate (belt-and-suspenders):** Even if these columns EXISTED, the `_restrict_to_visible_horizons()` gate
  (`odds_features_exporter.py` line 208) filters bucketed odds to only the horizons visible at the model boundary. For
  T-24h, only `FEATURE_HORIZONS["T-24h"] = ["T-24h"]` is visible — the T-0 closing snapshot is excluded.
  `_compute_aux_features()` receives this restricted input, so CLV/opening/movement features at T-24h are NaN (they need
  both T-24h and T-0 legs). The `_FT_REALIZED_COLUMNS` list (lines 104-106) includes `odds_home_close`/etc. as a
  protective layer, but stripping never fires because the columns don't exist to begin with.

  **Scope:** both `pregame.market.*_clv_bps` and `pregame.market.*_positive_clv_flag` family targets (lines 178-180,
  `TARGET_LEAKAGE_COLUMNS` → `_FT_REALIZED_COLUMNS`) are affected. The `merge_clv_target_columns()` function merges
  `odds_clv_home/draw/away` from `odds_targets` (the separate PIT-unrestricted export) but does NOT provide the raw
  `odds_home_close`/etc. columns `CLVTargetBuilder` expects.

  **GCS read not needed:** the columns are provably absent from the export schema — reading a parquet would only confirm
  what the code already defines. No full-corpus GCS walk was performed (single-walk discipline preserved).

  **Follow-up per plan spec:** either (a) file `[DESIGN]`→2 implementation todos for a structurally-separated export of
  the raw closing odds columns (analogous to the parent doc's `odds_targets` fix), piping them into
  `CLVTargetBuilder.build()`, OR (b) confirm `pregame_clv_family` is not used in any real production retrain and mark
  this doc resolved as moot. `pregame_clv_family` IS defined in `sports_ml_config.py` and `config_loader.py` as a valid
  preset; whether it drives actual retrains was not determined in this session.

- **context-scout 2026-08-06**: re-scouted; added
  `features-service/features_service/sports/exporters/odds_features_exporter.py` (concrete PIT-gate + schema-absence
  evidence source from the 2026-08-05 verdict), now 4 entries.

- **slot-11 2026-08-06**: **DECISION: FIX**. Confirmed `pregame_clv_family` is in both `SPORTS_PRODUCTION_GRID` and
  `SPORTS_DEVELOPMENT_GRID` (`config_loader.py` lines 613, 632); targets are canonical in UTL `sports_ml_config.py` (6
  `pregame.market.*` entries). Moot path rejected. Fix path identified: `compute_opening_odds()` (`odds_velocity.py`)
  already extracts T-0 closing odds as `_closing_{home/draw/away}` internally but drops them (line ~207). Viable fix:
  expose these as `odds_closing_{outcome}` in `odds_targets` (features-service, ~5-line change), extend
  `merge_clv_target_columns()` to pull them alongside `odds_clv_*`, update `CLVTargetBuilder.build()` defaults from
  phantom `COL_CLOSING_*` (`odds_home_close`) to the `odds_targets`-emitted `odds_closing_*` names. Two [CODE] P2
  implementation todos filed in Follow-ups below.

## Follow-ups

- [x] ✅ [DECISION] P2. File the fix-or-moot decision for CLVTargetBuilder's ALWAYS-NULL raw closing-odds columns:
      either file [DESIGN] implementation todos for a structurally-separated export of
      odds_home_close/odds_draw_close/odds_away_close piped into CLVTargetBuilder.build(), or confirm pregame_clv_family
      is not used in any real production retrain and mark the doc resolved as moot — **DECISION: FIX** (2026-08-06,
      slot-11). `pregame_clv_family` IS in `SPORTS_PRODUCTION_GRID` + `SPORTS_DEVELOPMENT_GRID`
      (`ml-service/ml_service/training/app/core/config_loader.py` lines 613, 632); targets are canonical in UTL
      `sports_ml_config.py`. Fix is viable without a new data export: `odds_targets_exporter.py` already calls
      `compute_opening_odds()` which extracts closing odds internally (`_closing_{home/draw/away}`) but drops them (line
      207 of `odds_velocity.py`). Expose these as `odds_closing_{home/draw/away}` in `odds_targets`; extend
      `merge_clv_target_columns()` to pull them; update `CLVTargetBuilder.build()` defaults to match. Implementation
      todos below.
- [ ] [CODE] P2. features-service: in `compute_opening_odds()` (`features_service/sports/calculators/odds_velocity.py`
      line ~207), instead of dropping `_closing_{home/draw/away}`, rename them to `odds_closing_{home/draw/away}` and
      include them in the return DataFrame. Update the `export_odds_targets()` docstring in `odds_targets_exporter.py`
      to list these 3 new columns. QG green. (repo: features-service)
- [ ] [CODE] P2. ml-service: (a) extend `merge_clv_target_columns()` in
      `ml_service/training/app/core/training_targets.py` to also pull `odds_closing_home`, `odds_closing_draw`,
      `odds_closing_away` and `odds_opening_home`, `odds_opening_draw`, `odds_opening_away` from `odds_targets` into
      `features_df` (same merge pattern as existing `odds_clv_*`); (b) update `CLVTargetBuilder.build()` in
      `ml_service/training/app/core/sports_target_generator.py` so its default `closing_*_col`/`opening_*_col`
      parameters match the `odds_closing_{outcome}` / `odds_opening_{outcome}` names from `odds_targets` (rename the
      phantom `COL_CLOSING_*`/`COL_OPENING_*` constants accordingly). Gate: features-service todo above shipped + GCS
      backfill of `odds_targets` re-run over at least one date to verify `odds_closing_*` columns appear. Done when:
      `--operation pipeline --family pregame_clv_family` logs non-degenerate `*_clv_bps` distribution and QG green.
      (repos: ml-service; depends on features-service todo above)

> **2026-08-06 archive-candidate audit**: The sole [DATA] P3 todo (verdict ALWAYS-NULL) is checked but its own text and
> the 2026-08-05 Progress Log defer an explicit follow-up — 'either (a) file [DESIGN]->2 implementation todos ... OR (b)
> confirm pregame_clv_family is not used in any real production retrain and mark this doc resolved as moot' and 'whether
> it drives actual retrains was not determined in this session' — that decision was never turned into a tracked todo.

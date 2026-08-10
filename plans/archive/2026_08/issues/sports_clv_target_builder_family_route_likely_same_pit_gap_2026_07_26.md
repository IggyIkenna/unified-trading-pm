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
status: resolved
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
    /plans/active/sports_satellite_ao_dispatch_batch12_2026_08_09.md,
  ]
created: 2026-07-26
author: unknown
last_updated: "2026-08-10"
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
resolved_by: "features-service@b4b7ad82, ml-service@38edeba, unified-trading-pm@904dfa2301"
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

> **🟢 ARCHIVED 2026-08-10 — RESOLVED** (status: resolved, 0 open todos, unlocked). Fix shipped and verified on real GCS
> parquet — see `resolved_by` + Follow-ups below. Archived per the 6-step ritual
> (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`).

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

- **slot-6 2026-08-06**: SHIPPED the features-service [CODE] P2 todo (features-service@b4b7ad82, QG green + quickmerge
  landed on LDR). `compute_opening_odds()` now emits `odds_closing_{home/draw/away}` (renamed from `_closing_*`, kept in
  the return DataFrame); `odds_features_exporter._compute_aux_features` strips them from the model-input `odds_features`
  path so the closing line stays only in the PIT-unrestricted `odds_targets` export; `export_odds_targets()` docstring +
  `ODDS_TARGETS_COLUMNS` schema updated; tests added (closing-odds exposure, NaN-when-no-closing, features-path guard,
  cross-repo parity doc). The ml-service [CODE] P2 todo below is now un-gated on the data side — its GCS-backfill
  verification step still needs `odds_targets` re-run over ≥1 date to confirm the `odds_closing_*` columns appear in the
  parquet.

- **slot-4 2026-08-06**: SHIPPED the ml-service [CODE] P2 todo (ml-service@38edeba, QG green 87s full pass, quickmerge
  landed on LDR, SHA verified on origin). `merge_clv_target_columns()` now pulls `odds_closing_{home/draw/away}` +
  `odds_opening_{home/draw/away}` alongside `odds_clv_*` from the PIT-unrestricted `odds_targets` export;
  `CLVTargetBuilder.build()` defaults + the `COL_CLOSING_*`/`COL_OPENING_*` constants renamed from the phantom
  `odds_*_open`/`odds_*_close` names to the odds_targets-emitted names; `_FT_REALIZED_COLUMNS` now lists
  `odds_closing_*` (the old `odds_*_close` entries were phantom, so the closing line was never actually stripped).
  Tests: `test_builds_non_degenerate_clv_with_odds_targets_column_names` (non-degenerate `*_clv_bps` under the
  odds_targets names), `test_merge_clv_target_columns` extended (`odds_closing_*`/`odds_opening_*` merge in;
  `odds_closing_*` stripped by the leakage shield while `odds_opening_*` survives as a legitimate T-24h feature).
  GCS-backfill re-run over a real date to confirm `odds_closing_*` in the parquet: NOT run this session
  (features-service @b4b7ad82's own unit test `test_odds_targets_exporter.py` asserts `odds_closing_home` emits; the
  prod parquet re-run is filed as a tracked follow-up below rather than run here to avoid racing the daily batch on the
  same date).

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
- [x] ✅ [CODE] P2. features-service: in `compute_opening_odds()`
      (`features_service/sports/calculators/odds_velocity.py` line ~207), instead of dropping
      `_closing_{home/draw/away}`, rename them to `odds_closing_{home/draw/away}` and include them in the return
      DataFrame. Update the `export_odds_targets()` docstring in `odds_targets_exporter.py` to list these 3 new columns.
      QG green. (repo: features-service) — features-service@b4b7ad82
- [x] ✅ [CODE] P2. ml-service: (a) extend `merge_clv_target_columns()` in
      `ml_service/training/app/core/training_targets.py` to also pull `odds_closing_home`, `odds_closing_draw`,
      `odds_closing_away` and `odds_opening_home`, `odds_opening_draw`, `odds_opening_away` from `odds_targets` into
      `features_df` (same merge pattern as existing `odds_clv_*`); (b) update `CLVTargetBuilder.build()` in
      `ml_service/training/app/core/sports_target_generator.py` so its default `closing_*_col`/`opening_*_col`
      parameters match the `odds_closing_{outcome}` / `odds_opening_{outcome}` names from `odds_targets` (rename the
      phantom `COL_CLOSING_*`/`COL_OPENING_*` constants accordingly). Gate: features-service todo above shipped + GCS
      backfill of `odds_targets` re-run over at least one date to verify `odds_closing_*` columns appear. Done when:
      `--operation pipeline --family pregame_clv_family` logs non-degenerate `*_clv_bps` distribution and QG green.
      (repos: ml-service; depends on features-service todo above) — ml-service@38edeba (QG green, 87s full pass; unit
      test `test_builds_non_degenerate_clv_with_odds_targets_column_names` proves non-degenerate `*_clv_bps` with the
      odds_targets column names; `test_merge_clv_target_columns` proves the closing/opening legs merge in;
      `_FT_REALIZED_COLUMNS` now strips `odds_closing_*` so the closing line stays out of the model-input matrix)
- [x] [DATA] P3. Re-run the `odds_targets` export over ≥1 recent date (features-service batch handler, idempotent
      overwrite) and confirm `odds_closing_{home/draw/away}` appear in the GCS parquet — the standing data-side
      verification for the CLVTargetBuilder repoint (features-service @b4b7ad82 proves the columns emit at unit level;
      this confirms on real parquets). (repo: features-service) — **DONE 2026-08-10 (slot-29)**: pure re-run, no code
      change
      (`.venv/bin/python3 -m features_service.sports.cli.main --operation compute --mode batch --date     2026-08-06 --tables odds_targets --skip-fetch`,
      real captured `odds_horizon_bucket` data for that date, 147 rows / 8 shards). Wrote
      `gs://features-sports-prd-central-element-323112/sports_features/by_date/day=2026-08-06/feature_group=odds_targets/features.parquet`
      (2 fixture rows). Confirmed via a fresh `pd.read_parquet` on that path:
      `event_id=4e5c385bec9516e786c4876ac68413f7` has non-null `odds_closing_home=2.415`, `odds_closing_draw=2.7`,
      `odds_closing_away=3.625` (the other row's whole CLV block is null — expected honest-absence for a fixture lacking
      a T-24h leg, not a defect).

> **2026-08-06 archive-candidate audit**: The sole [DATA] P3 todo (verdict ALWAYS-NULL) is checked but its own text and
> the 2026-08-05 Progress Log defer an explicit follow-up — 'either (a) file [DESIGN]->2 implementation todos ... OR (b)
> confirm pregame_clv_family is not used in any real production retrain and mark this doc resolved as moot' and 'whether
> it drives actual retrains was not determined in this session' — that decision was never turned into a tracked todo.
> **Resolved 2026-08-06→2026-08-10**: option (a) was already what happened — the fix-or-moot [DECISION] todo above chose
> FIX (not moot) on 2026-08-06, and both implementation todos + the final real-parquet verification todo are now all
> done. The "drives actual retrains" question is moot given (a) was chosen and executed; no separate todo needed.

## Progress Log

- **2026-08-10 (slot-29)**: sole remaining Follow-up ([DATA] P3, real-parquet verification) flipped `[x]` — see its own
  DONE note for the GCS path + confirmed non-null `odds_closing_*` values. 0 open todos remain; `archive_exempt: true`
  set on the flip-only commit (`unified-trading-pm@904dfa2301`) per the RULED-2026-08-09 two-commit bridge (this doc's
  own last todo is its archival trigger). This commit is the immediately-following `git mv` archival: `status: resolved`
  - archive banner + `resolved_by` updated with the flip SHA, `archive_exempt` dropped, doc moved to
    `plans/archive/2026_08/issues/`.

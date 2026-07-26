---
doc_type: issue
title:
  ml-service's SPORTS feature frame carries 32 non-numeric (object-dtype) columns — the uniform pipeline's
  feature_selection phase has no numeric-only guard and crashes on the first real SPORTS fit attempt
summary: >-
  Follow-on from `ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md`: after fixing that doc's Bugs
  1+3 (target-type fallback + the missing SPORTS branch in `cloud_feature_provider.py`), the CLV retrain reached real
  feature loading for the first time ever — 2,383 fixtures x 956 features across the full 2026-04-01..17 window, proving
  Bug 3's fix works end-to-end — then crashed one phase later: `uniform_training_pipeline.py::_phase_feature_selection`
  calls `GradientBoostingClassifier.fit(features, target)` with the raw feature DataFrame, and SPORTS's frame contains
  32 object-dtype columns (`ValueError: could not convert string to float: 'f6765ee3142dd9e9c4010e3dfe37131a'`). No
  asset group's feature frame has ever exercised this fit call with non-numeric columns present before, so the gap was
  never caught. Two distinct root causes coexist in those 32 columns: (a) genuine identity/categorical columns
  (`event_id`, `fixture_id`, `home_team_id`, `away_team_id`, `league_id`, `horizon`, `surface_type`, `round_name`,
  `competition_phase`) that were never meant to be model inputs and should be excluded before fit; (b) a second,
  independent class — several `xg_*` columns (`home_xg_understat`, `xg_blended_total`, etc.) that ARE meant to be
  numeric features but are dtype=object, implying an upstream null-sentinel or mixed-type write is silently defeating
  numeric coercion. A separate, adjacent finding from the same run: the CLV target itself resolved 100% "flat" (0% up,
  0% down) for this exact 2026-04-01..17 window because `pinnacle_closing_odds_home` / `odds_home_avg` are absent from
  the loaded feature set — even after Bug 4 is fixed, this specific date range may not be usable for a meaningful CLV
  retrain without also confirming the closing-odds columns are actually available somewhere in the pipeline.
status: open
nature: issue
asset_group: [sports]
stage: [backtest]
repos: [ml-service]
scope: [engineer]
tags: [ml-service, sports, clv, training-pipeline, feature-selection, dtype, architecture-gap]
related:
  [
    /plans/active/issues/ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
  ]
created: 2026-07-26
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
drift_direction: advance-code
depends_on: []
source:
  [
    "Found 2026-07-26 (slot-6, data_engineering) while independently verifying
    ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md's Bugs 1+3 fixes (ml-service
    pipeline_handler.py + cloud_feature_provider.py, uncommitted at discovery time) by running the real CLV retrain
    command end-to-end against prod features-sports-prd data.",
  ]
resolved_by:
locked_by:
locked_since:
---

# ml-service SPORTS feature frame breaks the generic feature-selection fit

## What I found

Ran the exact repro command from the parent issue doc, now past Bugs 1+3 (both fixed and independently verified in the
same session — see that doc's todos for shas):

```
python -m ml_service.training.cli.main --operation pipeline --mode batch --asset-group SPORTS \
  --family pregame_clv_family --target-types clv --timeframes fixture \
  --start-date 2026-04-01 --end-date 2026-04-17 --pipeline-depth 3 --skip-walk-forward
```

Feature loading now succeeds completely — proof Bug 3's fix is correct end-to-end, not just at the dispatch level:

```
INFO Sports GCS: total 2383 fixtures x 956 features across 17 dates
INFO Running pipeline 'sports-unknown-clv' with 956 features, 2383 samples
INFO Pipeline 'sports-unknown-clv': running phase feature_selection
ERROR Pipeline failed: could not convert string to float: 'f6765ee3142dd9e9c4010e3dfe37131a'
```

Traceback bottoms out in `uniform_training_pipeline.py::_phase_feature_selection` (line ~247):

```python
selector.fit(features, target_col)   # features = the full, unfiltered 956-column DataFrame
```

`GradientBoostingClassifier`/`Regressor` requires an all-numeric `X`; SPORTS's frame is not.

### Live census of the 32 object-dtype columns (single-day probe, 2026-04-17, 76 fixtures)

```python
CloudFeatureProvider(config=...).query_features(
    instrument_ids=[], timeframes=["fixture"], start_date=..., end_date=...,
    asset_group="SPORTS",
).select_dtypes(include=["object"]).columns
```

32 columns, two distinct classes:

1. **Genuine identity/categorical — never meant to be model inputs** (9 columns): `event_id` (32-char hex, e.g.
   `f6765ee3142dd9e9c4010e3dfe37131a` — the literal value the traceback names), `fixture_id`, `horizon` (`"T-24h"`),
   `home_team_id`, `away_team_id`, `league_id`, `surface_type`, `round_name`, `competition_phase`.
2. **Meant-to-be-numeric but upcast to object** (23 columns): all `xg_*` derived features — `home_xg_understat`,
   `away_xg_understat`, `home_xg_footystats`, `away_xg_footystats`, `home_xg_api_football`, `away_xg_api_football`,
   `xg_source_disagreement_{home,away}`, `xg_max_min_range_{home,away}`, `xg_blended_total`, `xg_blended_diff`,
   `xg_home_superiority`, `xg_implied_over_2_5`, `xg_implied_btts`, `{home,away}_xg_overperformance`,
   `{home,away}_xg_consistency`, `{home,away}_xg_rank_in_league`, and others in the same family. pandas upcasts a
   numeric column to `object` when it contains a mix of numbers and non-numeric values (e.g. `None`/a string
   null-sentinel/an empty string) — this points at a real upstream coercion gap in whatever writes/joins the xg feature
   group, not a display artifact.

### Why no other asset group has hit this

CEFI/TRADFI/DEFI feature frames are OHLCV/indicator-derived and apparently carry no string columns at all (instrument
identity lives in the DataFrame index or is handled elsewhere) — `grep`ing `uniform_training_pipeline.py` for any
existing numeric-only guard, `select_dtypes`, or identity-column drop returns zero hits. The fit call has always assumed
an all-numeric frame; SPORTS is the first caller to ever break that invariant this deep into the pipeline.

## A second, independent finding from the same run — CLV target degeneracy

Before the crash, the pipeline logged:

```
WARNING Precomputed CLV column 'clv_home' is all-NaN — falling through
WARNING No CLV source columns available (missing: ['pinnacle_closing_odds_home', 'odds_home_avg']) — target will be all flat
INFO CLV 3-class target: up=0 (0.0%), flat=2383 (100.0%), down=0 (0.0%)
```

Even after Bug 4 (this doc) is fixed, a CLV model trained on this exact `2026-04-01..17` window would train on a
100%-single-class target — not a meaningful model. Worth checking, before re-attempting: are
`pinnacle_closing_odds_home`/`odds_home_avg` (or the columns that feed `clv_home`) available in `features-sports-prd`
for ANY window, or is this a genuine upstream gap in the CLV target-source columns themselves? Not diagnosed further
here — flagging so the eventual retrain attempt checks target-class balance before treating a completed
`pipeline.run_all()` as a usable model.

## Recommended decision

- [ ] [CODE] P2. Give `_phase_feature_selection` (and any other phase in `uniform_training_pipeline.py` that fits an
      sklearn estimator directly on `features`) a numeric-only guard — either drop non-numeric columns before fit
      (defensive, protects every asset group) or have the SPORTS loader stop returning identity/categorical columns as
      feature columns in the first place (mirrors how CEFI/TRADFI/DEFI apparently never surface them). Whichever shape
      is chosen, importance/mask indexing (`features.columns[mask]`) must stay aligned to whatever subset was actually
      fit — a naive `select_dtypes` filter breaks that alignment if not threaded through consistently. (repo:
      ml-service)
- [ ] [DATA] P2. Diagnose the 23 `xg_*` columns upcast to `object` dtype — find the null-sentinel or mixed-type write
      causing the upcast and fix at the source (likely a features-service write path or a join step in
      `sports_feature_loader.py`), rather than papering over it with a blanket `pd.to_numeric(errors="coerce")` in
      ml-service. (repo: features-service or ml-service, needs source tracing)
- [ ] [DATA] P3. Check whether `pinnacle_closing_odds_home`/`odds_home_avg` (or `clv_home`'s real source columns) exist
      for ANY date window in `features-sports-prd` — if genuinely absent everywhere, the CLV target may need a different
      source/window before a meaningful retrain is possible; if present elsewhere, the `2026-04-01..17` window
      specifically may just be a bad choice and a different window should be used for the eventual retrain. (repo:
      ml-service / features-sports-prd data)
- [ ] [ML] P2. Once the above ships, re-attempt the 3 CLV model variant retrain (`training-period-2026-04`,
      `pregame_clv_family`, `timeframes=fixture`) and confirm the target class distribution is non-degenerate before
      promoting/citing. The 3 quarantined artifacts stay untouched. Blocked on this doc AND
      `ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md` both landing.

## Progress Log (append-only)

- 2026-07-26: filed while independently verifying the parent issue doc's Bugs 1+3 fixes — feature loading now works
  end-to-end (2383x956, proving Bug 3's fix), the retrain got one phase further than ever before, and hit this new,
  distinct, precisely-diagnosed blocker plus the CLV-target-degeneracy finding above.

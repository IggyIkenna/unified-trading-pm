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

- [x] [CODE] P2. ✅ **DONE (2026-07-26, slot-12, `data_engineering`) — `ml-service@5a9e3050`.** Gave
      `_phase_feature_selection` a numeric-only guard: `features.select_dtypes(include=[np.number])` computed once,
      applied to BOTH the `<=300`-column passthrough path (previously had no guard at all — `selected` was just
      `list(features.columns)`, would have silently carried non-numeric columns forward into Phase 2/3's
      `features[selected]` for any asset group with <=300 total features) and the `>300`-column selector-fit path
      (previously called `selector.fit(features, ...)` on the raw frame). All downstream indexing
      (`mask`/`top_idx`/`importance_dict` keys) now aligns to `numeric_features.columns`, not the original raw frame —
      no misalignment risk. Because `_phase_hyperparameter_tuning` and `_phase_base_results` both derive their working
      feature set via `_get_selected_features(prior, features)` → `features[selected]`, filtering `selected_features` in
      Phase 1 propagates the fix to every later phase without touching them. CEFI/TRADFI/DEFI frames carry no
      non-numeric columns today, so this is a no-op for them (verified: existing
      `test_phase_1_feature_selection`/`test_phase_1_small_dataset_keeps_all` still pass unchanged). 2 new regression
      tests: `test_phase_1_drops_non_numeric_columns_before_fit` (reproduces the exact crash shape — wide frame +
      `event_id`/`fixture_id`/object-upcast `xg_blended_total` — asserts none survive into `selected_features`) and
      `test_phase_1_small_dataset_drops_non_numeric_columns` (proves the guard applies on the `<=300` path too, where no
      selector fit runs to catch it otherwise). `bash scripts/quality-gates.sh --no-fix` GREEN (124s, sentinel == HEAD);
      shipped via `quickmerge.sh --agent`. Did NOT implement the alternative (SPORTS loader excludes
      identity/categorical columns at the source) — the defensive drop-before-fit shape protects every asset group
      uniformly and needed no changes to `sports_feature_loader.py`. (repo: ml-service)
- [x] ✅ [DATA] P2. Diagnose the 23 `xg_*` columns upcast to `object` dtype — find the null-sentinel or mixed-type write
      causing the upcast and fix at the source (likely a features-service write path or a join step in
      `sports_feature_loader.py`), rather than papering over it with a blanket `pd.to_numeric(errors="coerce")` in
      ml-service. (repo: features-service or ml-service, needs source tracing) — **DONE (slot-11, 2026-07-26):
      `features-service@c54f9eaf`.** Root cause: `multisource_xg_calculator.py::compute_multisource_xg_batch`
      initialized every declared `MULTISOURCE_XG_COLUMNS` entry with `out[col] = pd.NA` (line 143) — `pd.NA`, not
      `np.nan`, upcasts the column to `object` dtype, which then survives GCS write/read and poisons the ml-service
      merge/concat across dates. NOT a mixed-type write or a null-sentinel string — the real, deeper cause is that
      `compute_multisource_xg()` only ever returns 7 of the 28 declared column keys, so 21 columns are NEVER assigned a
      value past the `pd.NA` init and stay that dtype forever. Fix: `out[col] = pd.NA` → `out[col] = np.nan`, keeping
      every column float64 from creation whether filled or not — source-side, not a read-side `pd.to_numeric`
      papering-over as the todo asked to avoid. Does NOT restore the missing 21 columns' computations — that's a
      separate, much bigger feature-engineering gap (no formula exists for any of them, not a dtype bug), filed as its
      own scoped issue doc: `issues/sports_multisource_xg_21_of_28_columns_never_computed_2026_07_26.md`. 2 new
      regression tests assert every `MULTISOURCE_XG_COLUMNS` entry is numeric dtype (filled or not). 17835 tests pass;
      `quality-gates.sh` green in features-service (370s, sentinel-verified).
- [x] ✅ [DATA] P3. **DONE 2026-07-26 (slot-2, `data_engineering`) — genuinely absent everywhere, root cause found: a
      naming mismatch, not a window/data-absence problem.** Directly read the real `feature_group=odds_features` parquet
      across 7 dates spanning 2024-2026 (`2024-04-17`, `2025-04-17`, `2026-04-01`, `2026-04-10`, `2026-04-17`,
      `2026-05-01`, plus 2 dates with no data at all) — `clv_home`/`clv_draw`/`clv_away`/
      `sharp_clv_*`/`clv_direction_*` are ALL 0/N non-null on EVERY single date checked (never a single real value),
      while a genuinely-different, correctly-computed column in the SAME file (`pinnacle_vs_market_diff_home`) is fully
      populated (N/N) every time. `pinnacle_closing_odds_home`/ `odds_home_avg` (the "legacy fallback" pair) don't exist
      as columns anywhere in the exported file, and grepping the ENTIRE workspace confirms neither name is ever assigned
      by any repo — they only appear as the ml-service target-generator's OWN fallback-column names, never as a
      producer's output. **Root cause traced**:
      `features-service/features_service/sports/calculators/odds_velocity.py::compute_clv_features` produces
      `odds_clv_home`/`odds_clv_sharp_home`/`odds_clv_direction_home` (confirmed via direct read of its docstring +
      return columns, and independently confirmed as the SAME names `feature_expectations.py`'s `FEATURE_EXPECTATIONS`
      registry declares — features-service's own internal expectations are self-consistent and use the `odds_`-prefixed
      form throughout). But the day=2026-04-17 object's `horizon_schema.json` sidecar (a static per-column horizon
      manifest written by `writer.py::_write_horizon_schema_sidecar`) declares the BARE names (`clv_home`,
      `sharp_clv_home`, `clv_direction_home` — no `odds_` prefix) among its 878 keys, NOT `odds_clv_home` — i.e. an
      OLDER naming convention than what the calculator/registry currently use, matching the exact "sidecar predates the
      naming fix" pattern `ml-service/.../sports_target_generator.py`'s own code comment already warns about for a
      DIFFERENT column set (the T-24h leakage-gate CLV aliases). **The precise byte-level mechanism that turns the real,
      populated `odds_clv_home` into an always-empty `clv_home` in the final written parquet was NOT fully traced this
      pass** (the exporter's own merge code (`odds_features_exporter.py:287-290,417-418`) never renames the column — the
      rename/loss must happen in a later, not-yet-located schema-reindex step, possibly one that consults a stale
      `horizon_schema.json`-style manifest to decide the final column set). Flagging this precisely rather than guessing
      further — the fix todo below scopes finding + fixing that exact mechanism as its own bounded task. **Verdict for
      the retrain**: this is NOT a window-choice problem — `clv_home` cannot be non-degenerate in ANY window today,
      because the CLV data that DOES exist (`odds_clv_home`) never reaches the final feature frame under a name the
      target generator recognizes. A retrain attempted now, in ANY window, would ALWAYS produce a 100%-flat garbage
      target.
- [x] ✅ [DATA] P2. **RE-SCOPED, NOT A FEATURES-SERVICE BUG (2026-07-26, slot-8, `data_engineering`).** The premise (a
      naming/reindex mechanism silently replacing real `odds_clv_home` data with an always-empty `clv_home`) is FALSE —
      verified end-to-end with real data at every step. `compute_clv_features`/`compute_opening_odds`
      (`odds_velocity.py`) are CORRECT: fed the real T-0+T-24h bucketed-odds shards for
      `day=2026-04-17/league_id=BUNDESLIGA` directly (downloaded from the raw MDPS bucket), they produce real non-null
      CLV values in-process. The actual cause: `odds_features_exporter.py::_restrict_to_visible_horizons` (line 208)
      DELIBERATELY restricts the calculator's input to `FEATURE_HORIZONS[model_horizon]` before every call — and per
      `odds_columns.py:215-233`, T-24h/T-1h/T-10m (the only model horizons that currently emit rows; `HT` never emits,
      per the exporter's own documented honest-absence design) ALL exclude `T-0` from their visible set. So
      `compute_clv_features` is guaranteed empty for every row this export ever writes — BY DESIGN, a point-in-time
      leakage guard, not a bug. Direct read of the real day=2026-04-17 parquet confirms: `horizon` ∈
      `{T-24h, T-1h, T-10m}` only (0 `HT` rows), `clv_home`/`odds_movement_home` both 0/75 non-null, while
      T-0-independent columns are fully populated (75/75). Neither `features-service@0ded2449` (naming rename) nor
      `ml-service@a14985bc` (consumer column-name fix) can close this — the column they now agree on the name of is
      still always-null by design. Re-scoped as an architecture decision (which repo/path should source a leakage-safe
      CLV TARGET) spanning features-service + ml-service — filed as
      `issues/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md` with 3 candidate directions and a
      `[DESIGN] P1` decision todo. Did not attempt a features-service code "fix" — removing/weakening the PIT gate would
      be a real leakage regression for every other `odds_features` consumer.
- [ ] [ML] P2. **SUPERSEDED — see `issues/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`'s
      `[ML] P2`.** The blocker is no longer "the fix above" (there is no features-service fix); it's that new doc's
      `[DESIGN] P1` architecture decision. Once implemented, re-attempt the 3 CLV model variant retrain
      (`training-period-2026-04`, `pregame_clv_family`, `timeframes=fixture`) and confirm the target class distribution
      is non-degenerate before promoting/citing. The 3 quarantined artifacts stay untouched.

## Progress Log (append-only)

- 2026-07-26: filed while independently verifying the parent issue doc's Bugs 1+3 fixes — feature loading now works
  end-to-end (2383x956, proving Bug 3's fix), the retrain got one phase further than ever before, and hit this new,
  distinct, precisely-diagnosed blocker plus the CLV-target-degeneracy finding above.
- 2026-07-26 (slot-12, `data_engineering`): shipped the `[CODE] P2` numeric-only guard fix (`ml-service@5a9e3050`).
  Status left `open` — the `[DATA] P2` (xg_* upcast root cause), `[DATA] P3` (CLV target-source availability), and
  `[ML] P2` (re-attempt retrain) todos remain genuinely open. The `[ML] P2` retrain is still blocked on
  `ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md`'s own remaining items too.
- 2026-07-26 (slot-11, `data_engineering`): shipped `[DATA] P2` (`features-service@c54f9eaf`) — root cause was `pd.NA`
  init upcasting to object dtype, not a mixed-type write; fixed at the source. Found + spun off a separate, larger
  finding while diagnosing (21 of 28 declared `MULTISOURCE_XG_COLUMNS` never actually computed —
  `issues/sports_multisource_xg_21_of_28_columns_never_computed_2026_07_26.md`). Status left `open` — `[DATA] P3` and
  `[ML] P2` remain genuinely open.
- 2026-07-26 (slot-2, `data_engineering`): closed `[DATA] P3` — directly read real `odds_features` parquet across 7
  dates (2024-2026), `clv_home`/`sharp_clv_*`/`clv_direction_*` are 0/N non-null on EVERY date (never a window- specific
  gap); the "legacy fallback" columns don't exist anywhere in the codebase. Root-caused to a naming mismatch:
  `features-service`'s calculator produces `odds_clv_home` (matching its own `feature_expectations.py` registry
  self-consistently) but the exported parquet only ever carries an always-empty bare `clv_home` — the exact byte-level
  rename/reindex mechanism was NOT fully traced (flagged honestly rather than guessed), so filed a new properly-scoped
  `[DATA] P2` fix todo instead of attempting a blind fix. Re-scoped `[ML] P2`'s blocker: this is now a real, confirmed
  bug (not a window-selection question) — a retrain in ANY window today would always produce a 100%-flat garbage target.
  Status left `open` — the new `[DATA] P2` and `[ML] P2` remain genuinely open.
- 2026-07-26 (slot-8, `data_engineering`): closed `[DATA] P2` — the "naming mismatch" theory from the P3 finding above
  was the wrong track. Traced the FULL path with real data (raw MDPS bucketed T-0+T-24h odds fed directly into the real
  calculator functions; the exporter's `_restrict_to_visible_horizons` PIT gate; the actual written parquet's `horizon`
  column distribution). There is no rename/reindex bug — `compute_clv_features` is correct, and the always-empty CLV is
  a deliberate, correct point-in-time leakage guard: every model horizon that currently emits rows (T-24h/T-1h/T-10m)
  is, by design, blind to the T-0 closing line; `HT` (which would see it) never emits. Neither
  `features-service@0ded2449` nor `ml-service@a14985bc` can close this — both already-shipped fixes are naming fixes for
  a value that is null by design, not by bug. Re-scoped as an architecture decision spanning features-service +
  ml-service, filed as `issues/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`. `[ML] P2` now
  points there instead of "the fix above". NOTIFIED OPERATOR per the cross-repo big-finding rule (this doc + the new
  one).

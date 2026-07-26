---
doc_type: issue
title:
  "21 of the 28 declared MULTISOURCE_XG_COLUMNS in features-service's sports xG calculator are dead placeholder schema —
  never assigned a real value, always NaN"
summary: >-
  Found while root-causing why ml-service's SPORTS feature frame carries object-dtype `xg_*` columns
  (ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md's `[DATA] P2` todo).
  `multisource_xg_calculator.py::MULTISOURCE_XG_COLUMNS` declares 28 column names, but `compute_multisource_xg()` — the
  only function that ever writes into the per-fixture output row — returns exactly 7 keys (`home_xg_blended`,
  `away_xg_blended`, `home_xg_spread`, `away_xg_spread`, `xg_source_count`, `home_xg_confidence`, `away_xg_confidence`).
  The other 21 declared columns (per-source passthroughs `home_xg_understat`/`footystats`/`api_football` etc.,
  disagreement/range metrics, derived-consensus features, historical-accuracy features, league-rank features) are
  initialized once and never touched again — a dead placeholder schema, not a bug in any specific formula. The
  column-name comment ("Ported from archived multisource_xg_features.py — per-source values") confirms the NAMES were
  ported from an archived module during a port that never finished porting the COMPUTATION logic behind them. This has
  been invisible because the existing unit test only asserts the 21 names exist as columns, never that they hold real
  data — and no downstream consumer materially exercised this frame numerically until the 2026-07-26 CLV retrain (the
  first real `GradientBoostingClassifier.fit()` call against a SPORTS frame).
status: open
nature: issue
asset_group: [sports]
stage: [backtest]
repos: [features-service]
scope: [engineer]
tags: [features-service, sports, xg, feature-engineering, dead-code, architecture-gap]
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
priority: P3
estimate_class: brand-new
drift_direction: advance-code
depends_on: []
source:
  "Found 2026-07-26 (slot-11, data_engineering) while fixing the object-dtype-upcast `[DATA] P2` todo in
  ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md — that fix
  (features-service, out[col]=pd.NA -> np.nan) resolves the DTYPE bug but does not, and cannot, restore the missing
  computations behind these 21 columns; that is this doc's separate scope."
resolved_by:
locked_by:
locked_since:
---

# 21 of 28 declared multisource-xG columns are dead placeholder schema

## What I found

`features_service/sports/calculators/multisource_xg_calculator.py`:

- `MULTISOURCE_XG_COLUMNS` (lines 16-51) declares 28 column names across 5 groups: core blended estimates (7, all real),
  per-source passthroughs (6: `home_xg_understat`/`away_xg_understat`/`home_xg_footystats`/
  `away_xg_footystats`/`home_xg_api_football`/`away_xg_api_football`), source-disagreement metrics (4:
  `xg_source_disagreement_{home,away}`/`xg_max_min_range_{home,away}`), derived-consensus features (5:
  `xg_blended_total`/`xg_blended_diff`/`xg_home_superiority`/`xg_implied_over_2_5`/`xg_implied_btts`),
  historical-accuracy features (4: `{home,away}_xg_overperformance`/`{home,away}_xg_consistency`), and league-rank
  features (2: `{home,away}_xg_rank_in_league`).
- `compute_multisource_xg()` (lines 57-108) — the ONLY function that ever writes a value into the output row
  (`compute_multisource_xg_batch`'s `for col, val in feats.items(): out.at[idx, col] = val`, line ~157) — returns
  exactly the 7 core-blended-estimate keys. Grepped the entire repo (excluding tests) for each of the other 21 column
  names: zero assignment sites anywhere.
- The 21 unfilled columns are initialized once (`out[col] = np.nan`, post-fix) and never revisited. They are present in
  every output row, always NaN, indistinguishable from "genuinely missing this fixture" vs. "never implemented" without
  reading this code.
- Confirmed via the archived-module comment (line 25, "Ported from archived multisource_xg_features.py — per-source
  values") that this is a port that copied the target SCHEMA (column names) but not the computation behind 21 of the 28
  fields.

## Why it matters

These 21 columns are real, meaningful xG-derived features (per-source disagreement, blended totals, historical
over/under-performance, league ranking) that a sports model could plausibly benefit from, but they contribute ZERO
signal today — every row is NaN, so any model trained against this frame silently learns nothing from them (and, per the
sibling doc's numeric-only guard fix, they're now correctly dropped before `fit()` entirely rather than crashing it —
but dropped columns are still lost potential signal, not a neutral no-op).

This is NOT a bug in any one formula — there is no formula to have a bug in. It's unbuilt feature-engineering work
wearing a "these columns exist" disguise. Fixing it requires:

1. Deciding whether each of the 5 unfilled groups is still wanted (per-source passthrough needs each source's raw xG
   value threaded through from wherever it's fetched; disagreement/range needs the per-source values to diff against
   each other, not just the blended mean; derived-consensus needs real formulas for over/under-2.5-implied-probability,
   BTTS-implied, home-superiority; historical-accuracy needs a backward-looking join against realized goals; league-rank
   needs a per-league, per-date ranking pass).
2. If still wanted, implementing each group's real computation (a genuine feature-engineering task, not a mechanical fix
   — the "how should xg_implied_over_2_5 actually be computed" question is a design/domain decision, not something to
   improvise without validation).
3. If some groups are no longer wanted (e.g. the archived module's original design assumptions no longer apply), pruning
   the dead column names from `MULTISOURCE_XG_COLUMNS` instead of leaving them as perpetually-NaN dead weight.

Per this workspace's dispatch-scope rule, "how should each of these 21 features actually be computed" is a design call,
not a bounded worker todo — filing this as its own doc rather than folding it into the (already shipped) dtype fix, and
NOT attempting to improvise 21 formulas here.

## Recommended decision

- [ ] [OPERATOR/DESIGN] P3. Decide, per the 5 unfilled column groups above, which are still wanted vs. should be pruned
      from `MULTISOURCE_XG_COLUMNS`. For each group kept, scope a properly-sized follow-up todo (source data location,
      formula, done-when) before dispatching as AO work — this doc intentionally stops at diagnosis, per the "figure out
      how X should look" dispatch-scope rule.
- [ ] [REVIEW] P3. Check whether the same `= pd.NA`-then-never-filled idiom exists elsewhere in
      `features_service/sports/` (the investigation that found this bug also flagged `writer.py`'s `season_context`
      columns as using an identical "initialized to pd.NA" pattern per its own code comment — not independently verified
      as dead here, just flagged as worth the same check).

## Codex SSOTs

None directly on point — this is a features-service-internal feature-engineering gap, not a cross-cutting data pipeline
contract.

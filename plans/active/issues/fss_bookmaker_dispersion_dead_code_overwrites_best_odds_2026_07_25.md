---
doc_type: issue
title:
  "features-service's compute_odds_batch() is called WITHOUT bookmaker_home_cols/draw/away in production, so
  _apply_bookmaker_dispersion always takes its empty-bm_cols branch — bookmaker_disagreement_*/odds_variance_* are
  ALWAYS 0.0 in real pipeline output, and best_odds_* gets silently OVERWRITTEN from the correct per-fixture MAX
  (computed upstream in _pivot_bucketed_to_fixture) down to the cross-book MEAN"
summary: >-
  Discovered while investigating `sports_odds_feature_naming_canonicalization_2026_07_21.md`'s new-compute todo (add
  per-bookmaker raw decimal-odds retention) — an Explore agent tracing `features_service/sports/exporters/
  odds_features_exporter.py`'s odds-collapse path found that `compute_odds_batch()` (called at
  odds_features_exporter.py:328-337) is invoked without the `bookmaker_home_cols`/`bookmaker_draw_cols`/
  `bookmaker_away_cols` kwargs `_apply_bookmaker_dispersion()` (odds_calculator.py:97-133) needs to do real
  per-bookmaker dispersion math. Without those kwargs, `_apply_bookmaker_dispersion` falls into its empty-`bm_cols`
  branch (odds_calculator.py:115-118), which sets `out[best_col] = odds_series[label]` — the cross-book MEAN, not a max
  — and leaves `bookmaker_disagreement_*`/`odds_variance_*`/`book_fragmentation_*`/`market_confidence_*` at their
  zero-initialized defaults. Because `compute_odds_batch` builds a brand-new `out` DataFrame (not a mutation of the
  caller's frame) and its result is merged back into the exporter's `features_df`, this SILENTLY OVERWRITES the
  correctly-computed `best_odds_home/draw/away` (a real per-fixture MAX across bookmakers, already computed upstream in
  `_pivot_bucketed_to_fixture`, odds_features_exporter.py:419-426) with the wrong (mean) value from the dead-code path.
  The `bookmaker_home_cols`/etc. kwargs ARE exercised, but only in tests
  (tests/sports/unit/calculators/test_odds_calculator.py:159, test_calculators_enriched.py:161) — never by any real
  caller.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [features-service]
scope: [engineer]
tags: [sports, odds, features-service, data-correctness, dead-code, regression]
related: [/plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md]
created: 2026-07-25
priority: P1
parent_epic: sports_master
source:
  "Explore-agent finding surfaced while scoping sports_odds_feature_naming_canonicalization_2026_07_21.md's new-compute
  (per-bookmaker decimal-odds) todo, slot 7, 2026-07-25 — not independently confirmed live against real captured MDPS
  data in this session, only traced via code-read; filed rather than silently dropped per the data-pipeline-correctness
  HARD RULE."
execution_scope: orchestrator-agent
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# features-service: bookmaker-dispersion dead code silently downgrades best_odds_* from MAX to MEAN

## What I found

Tracing `features_service/sports/exporters/odds_features_exporter.py`'s odds-collapse path (while scoping an unrelated
new-compute todo), found TWO separate cross-bookmaker collapse mechanisms that disagree with each other:

1. **`_pivot_bucketed_to_fixture()`** (`odds_features_exporter.py:372-517`) — the real, per-fixture collapse. For each
   `(fixture_id, horizon)` group of per-bookmaker rows, it correctly computes `best_odds_home/draw/away` via
   `group[src].max()` (lines 419-426), plus `best_venue_home/draw/away` (the bookmaker key that produced the max, lines
   450-458), `arb_pct`/`arb_sum_implied`, and `sharp_soft_spread_*`.
2. **`_apply_bookmaker_dispersion()`** (`features_service/sports/calculators/odds_calculator.py:97-133`), invoked from
   `compute_odds_batch()` (`odds_calculator.py:244`), which the exporter calls at `odds_features_exporter.py:328-337` —
   **without** passing `bookmaker_home_cols`/`bookmaker_draw_cols`/ `bookmaker_away_cols`. With those kwargs absent,
   `_apply_bookmaker_dispersion` takes its empty-`bm_cols` branch (`odds_calculator.py:115-118`):
   `out[best_col] = odds_series[label]` — the **mean**, not a max — and leaves
   `bookmaker_disagreement_*`/`odds_variance_*`/`book_fragmentation_*`/`market_confidence_*` at zero.

`compute_odds_batch` builds a fresh `out` DataFrame rather than mutating the caller's `snapshot_df`, and its result gets
merged back into `features_df` downstream — so the SECOND (wrong, dead-code-path) `best_odds_*` silently clobbers the
FIRST (correct) one that `_pivot_bucketed_to_fixture` already computed.

**Not independently confirmed against real captured production data this session** — this is a code-read finding from an
Explore agent, not a live parquet inspection. The mechanism is unambiguous from the code, but someone picking this up
should verify against a real `odds_features` output file before/after any fix (diff `best_odds_home` computed both ways
for a real fixture) to confirm the magnitude in practice, not just that the code path exists.

## Why it matters

- `best_odds_home/draw/away` feeds `SportsValueBettingEngine`'s `decimal_odds_<outcome_id>` per
  `sports_odds_feature_naming_canonicalization_2026_07_21.md` — if it's silently the mean instead of the best available
  price across bookmakers, any strategy consuming it systematically undervalues the actual best-price opportunity (the
  entire point of a "best odds" feature is capturing the arbitrage-relevant max, not an average).
- `bookmaker_disagreement_*`/`odds_variance_*`/`book_fragmentation_*`/`market_confidence_*` — 4 whole feature families —
  are dead weight in every real FSS output row (always exactly `0.0`), silently. Any downstream consumer (ML training, a
  strategy reading these as signal) is training on/reacting to a constant, not real dispersion.
- This is a data-correctness class finding per the workspace HARD RULE ("Data pipeline correctness is the heartbeat") —
  filed rather than left as chat-only prose, per the pre-compact ritual's Step 3.

## Recommended decision

Not prescribing the exact fix (needs someone to actually run it against real data first per the caveat above), but the
shape is: either (a) pass real `bookmaker_home_cols`/`draw`/`away` into `compute_odds_batch` from the exporter (the
per-fixture wide pivot already available inside `_pivot_bucketed_to_fixture`'s `group` — same data the new-compute todo
in `sports_odds_feature_naming_canonicalization_2026_07_21.md` needs), so `_apply_bookmaker_dispersion` gets real
dispersion math instead of always falling into its zero-branch; or (b) if `_apply_bookmaker_dispersion`'s design is
meant to be superseded by `_pivot_bucketed_to_fixture` entirely, stop calling `compute_odds_batch`'s `best_odds_*`
output path from the exporter (or don't let it overwrite fields `_pivot_bucketed_to_fixture` already set) so the correct
MAX survives the merge.

## Todos

- [ ] [DATA] P1. Confirm this finding against a real captured `odds_features` parquet — diff `best_odds_home` computed
      both ways (the `_pivot_bucketed_to_fixture` MAX vs. the `compute_odds_batch` MEAN that currently wins) for at
      least one real fixture with 2+ bookmakers, to confirm the magnitude in practice before fixing. (repo:
      features-service)
- [ ] [DATA] P1. Fix the collapse so `best_odds_*` stays the correct per-fixture MAX and
      `bookmaker_disagreement_*`/`odds_variance_*`/`book_fragmentation_*`/`market_confidence_*` compute real values
      instead of always-zero — either wire real `bookmaker_home_cols`/`draw`/`away` into `compute_odds_batch`, or stop
      `compute_odds_batch`'s output from overwriting `_pivot_bucketed_to_fixture`'s fields. Add a regression test
      proving `best_odds_home` after the full exporter pipeline matches the true per-fixture max across bookmakers (not
      the mean). (repo: features-service)

## Progress Log

- **2026-07-25 (slot 7, data_engineering)**: Filed per an Explore-agent finding surfaced while scoping the unrelated
  `sports_odds_feature_naming_canonicalization_2026_07_21.md` new-compute todo. Not independently verified against live
  data this session — code-read only. Filed rather than dropped per the data-pipeline-correctness HARD RULE and the
  pre-compact ritual's "chat-only findings become todos" step.

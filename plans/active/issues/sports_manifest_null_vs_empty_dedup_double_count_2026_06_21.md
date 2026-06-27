---
doc_type: plan
title: Sports IS manifest double-count is caused by NULL-vs-empty-string in optional dedup columns, not pipeline_mode
created: 2026-06-21
source:
  - instruments-store-sports-prd/_index/availability_index.parquet (live read 2026-06-21)
  - unified_trading_library/manifest_consolidator.py (_resolve_dedup_cols / _DEDUP_NULL_SENTINEL)
  - instruments-service/scripts/canonicalize_sports_legacy_pipeline_mode_2026_06_21.py
locked_by: live-defi-rollout
priority: P2
status: active
summary: While implementing the one-off `canonicalize_sports_legacy_pipeline_mode_2026_06_21.py` (re-stamp legacy `batch_instruments_service` sports rows → `batch_<source>` + fill blank `empty_confirmed` re...
nature: process
asset_group: cross-asset
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

## What I found

While implementing the one-off `canonicalize_sports_legacy_pipeline_mode_2026_06_21.py` (re-stamp legacy
`batch_instruments_service` sports rows → `batch_<source>` + fill blank `empty_confirmed` reasons), the dry-run verified
the stated double-count mechanism is **incorrect**:

- The task diagnosis said: `pipeline_mode` is part of the consolidator dedup key, so the same cell exists under both
  `batch_instruments_service` (old) and `batch_<source>` (new), and re-stamping the legacy `pipeline_mode` makes the
  rows share the key → the consolidator collapses them.
- **Verified against the live index + the consolidator source**: `pipeline_mode` is **NOT** in the dedup key. The key is
  `_BASE_DEDUP_COLS = (date, venue, data_type, service_name)` + the present `_OPTIONAL_DEDUP_COLS`
  (`timeframe, league_id, chain, instrument_type, underlying, feature_group, model_family, training_period, strategy_id, client_id, instruction_type, instrument_id`).
  Re-stamping `pipeline_mode` alone collapses **0 rows**.
- The **real splitter** is a **NULL-vs-empty-string mismatch in the OPTIONAL dedup columns**: legacy rows carry parquet
  `NULL` where the newer/canonical rows carry `""`. The consolidator coalesces `NULL` to a distinct sentinel
  (`__UTL_CONSOLIDATOR_NULL_4e8a2__`) and leaves `""` as `""`, so `NULL != ""` → the twins never merge. Example:
  FIXTURES `date=2020-07-01, league=EPL` exists as a legacy `captured` row (instrument_count=4, all optional dims NULL)
  AND a newer `empty_confirmed` row (count=0, optional dims `""`).
- Normalising the **legacy** rows' NULL optional dims → `""` collapses the duplicate twins (consolidated index
  `4,127,195 → 4,107,758` distinct dedup-keys; FIXTURES captured `76,087 → 76,006` distinct). This is now done by the
  one-off (step 1b), scoped to legacy rows only and convergent with the canonical `""` convention.

## Why it matters

1. The double-count fix shipped by the one-off relies on the **NULL→"" normalisation**, not the pipeline_mode rename.
   Anyone reading the original task diagnosis would conclude the rename fixes it — it does not.
2. **The NULL/"" inconsistency is NOT legacy-only.** The same dry-run shows NON-legacy rows ALSO carry a mix of NULL and
   `""` across optional dims (e.g. `timeframe`: non-legacy 1,365,481 NULL / 565,606 `""`; `underlying`/`feature_group`/
   `…`: non-legacy 1,365,481 NULL / 565,606 `""`). So there may be additional `NULL`-vs-`""` duplicate twins among
   non-legacy rows (and across other asset_groups' IS/MTDS indices) that this one-off does NOT touch (it is scoped to
   legacy `batch_instruments_service` rows). A full-corpus NULL→"" canonicalisation of optional dedup columns is a
   larger, separate operation.
3. Root-cause options (operator decision): (a) make the **consolidator** treat `NULL` and `""` as equal in the dedup key
   (coalesce both to the same sentinel) — a single SSOT fix that retroactively de-dupes every bucket; OR (b) a
   full-corpus writer-side normalisation so every optional dedup column is `""`-not-NULL. Option (a) is the cleaner
   single-point fix and avoids re-walking every parquet.

## Recommended decision

- The sports legacy one-off (`canonicalize_sports_legacy_pipeline_mode_2026_06_21.py`) is correct and shipped — it
  delivers the task's three goals (pipeline_mode canonical, typed reasons, double-count collapsed) via the corrected
  mechanism, scoped to legacy rows.
- **Operator: pick the systemic fix** for the NULL-vs-`""` dedup-key mismatch (consolidator coalesce-both vs full-corpus
  normalisation). If (a), a small change to `_duckdb_consolidate_and_write` (coalesce `NULL` AND `''` to one sentinel)
  fixes it fleet-wide with no whole-corpus walk. Until then, non-legacy NULL/"" twins in sports (and likely cefi/defi/
  tradfi/prediction IS + MTDS indices) remain a latent double-count.

## Non-FIXTURES blank-reason residue (left untouched, by design)

The same one-off leaves **612,682** consolidated-index `empty_confirmed` blank `error_reason` rows untouched
(non-FIXTURES sports data_types:
FIXTURE_STATS/FIXTURE_LINEUPS/FIXTURE_EVENTS/PREDICTIONS/ODDS/PLAYER_STATS/XG/WEATHER/INJURIES/…). Reason: their
non-blank twins use a MIX of `EXPECTED_NO_FIXTURE` / `EXPECTED_INSTRUMENT_NOT_LISTED` / `SOURCE_RETURNED_ZERO` — no
single canonical reason is derivable per data_type, so filling one would be a guess. A follow-up that re-derives the
correct reason per (data_type, date, league) from the fixture-presence + source-coverage SSOT (rather than a blanket
fill) is needed to close these. Tracked here for the sports/manifest epic.

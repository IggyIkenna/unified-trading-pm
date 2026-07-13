---
doc_type: issue
title: Sports IS manifest double-count is caused by NULL-vs-empty-string in optional dedup columns, not pipeline_mode
summary:
  While implementing the one-off `canonicalize_sports_legacy_pipeline_mode_2026_06_21.py` (re-stamp legacy
  `batch_instruments_service` sports rows → `batch_<source>` + fill blank `empty_confirmed` re...
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags:
  [sports, manifest, data-correctness, consolidation, canonicalisation, pipeline-mode, data-quality, honest-coverage]
related:
  [
    plans/active/issues/sports_league_id_out_of_universe_overcapture_2026_06_24.md,
    plans/active/issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md,
  ]
created: 2026-06-21
parent_epic: sports_master
priority: P1
source:
  [
    instruments-store-sports-prd/_index/availability_index.parquet (live read 2026-06-21,
    re-verified 2026-07-08,
    re-verified 2026-07-13),
    unified_trading_library/manifest_consolidator.py (_resolve_dedup_cols / _DEDUP_NULL_SENTINEL),
    unified_trading_library/manifest_writer/_read_index.py (_merge_shard_frames,
    2026-07-08 fix),
    instruments-service/scripts/canonicalize_sports_legacy_pipeline_mode_2026_06_21.py,
  ]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
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

## Update 2026-07-08 (slot-7, data_engineering) — option (a) WAS shipped, but two gaps left the twins live

Confirms this doc's option (a) is no longer hypothetical —
`unified_trading_library.manifest_consolidator._dedup_key_sql` already coalesces NULL and `""` to one sentinel (shipped
as `unified-trading-library@f5ec2291f`, §9.2b, referenced from
`plans/active/understat_local_backfill_completion_2026_07_06.md`). Verified the SQL is _correct_ by feeding it the exact
duplicate pair directly (DuckDB `PARTITION BY` on the normalized key correctly picks 1 survivor). Yet the LIVE sports
canonical index still carried the twins. Two independent gaps, both now closed:

1. **Reader-side gap (different code path, same bug class)** —
   `unified_trading_library/manifest_writer/_read_index.py ::_merge_shard_frames` (the pandas dedup
   `read_availability_index` uses to layer a caller's just-written per-VM shard on top of the consolidated blob) never
   got the equivalent NULL/`""` normalization; it deduped on raw values, so a caller's own fresh read could see the same
   NULL-vs-`""` twin the consolidator was designed to prevent. Fixed + shipped: `unified-trading-library@d64563da`
   (`fix(manifest): dedup NULL vs empty-string optional dims in reader shard merge`), with a regression test
   (`test_reader_dedups_optional_dim_null_vs_empty_string`).
2. **Consolidator staleness/operational gap** — even after the SQL fix (#1 above notwithstanding), the LIVE sports
   canonical still held ~297 un-collapsed `(date, league_id, data_type)` keys with an `attempted_failed` row coexisting
   with a newer valid-status row (discovered while driving `understat_local_backfill_completion-001`'s retry-verify
   loop, which never reached 0 `attempted_failed` because of these twins). This means the DEPLOYED Cloud Run
   consolidator job's incremental cycles were NOT applying the `_dedup_key_sql` fix continuously in production — either
   a stale image (never rebuilt post-`f5ec2291f`) or the incremental anti-join is missing some contested-key cases the
   isolated SQL test doesn't reproduce. **Not root-caused further here** — out of this session's scope (infra/deploy
   craft, not data_engineering) and already tracked as `plans/active/understat_local_backfill_completion_2026_07_06.md`
   task -003 ("confirm §9.2b consolidator deployed"). **Mitigated for sports only**: ran
   `python -m unified_trading_library.manifest_consolidator --bucket instruments-store-sports-prd-central-element-323112 --force`
   (one-off full rebuild, sanctioned per the tool's own docstring: "one-off seed after backfill"). Result:
   `rows_in=5,175,040 rows_out=4,901,461 dedup_dropped=273,579` — a FAR larger cleanup than the 297 keys I could see
   from the narrow attempted_failed/XG_SHOTS angle, confirming this NULL/`""` twin pattern is broad across the whole
   sports manifest, not just understat. Cross-check needed for cefi/defi/tradfi/prediction buckets — task -003 (or a new
   dedicated audit) should verify whether their Cloud Run consolidator jobs are running the fixed image, and if not, run
   the equivalent one-off `--force` rebuild per bucket (each is a quick, self-contained, locked operation — no
   whole-corpus GCS walk, just the existing canonical + shards).

## Update 2026-07-13 (slot-3, interactive session) — the "not root-caused further" gap is CONFIRMED still open and recurring

Cross-referencing this doc's "Update 2026-07-08" section (the deployed Cloud Run consolidator's incremental cycles NOT
applying the dedup fix continuously in production — "either a stale image ... or the incremental anti-join is missing
some contested-key cases", explicitly "Not root-caused further here"): a fresh live-manifest re-verify today found the
sibling doc `sports_xg_shots_instrument_type_dedup_key_instability_2026_07_09.md`'s fix — independently verified clean
("0 duplicate groups remain system-wide") on 2026-07-09 — has a fresh recurrence 4 days later (same 2024-12-14 big-5
cells, plus a new instance on XG itself). This is consistent with — and likely the same root mechanism as — this doc's
still-open gap: something about the consolidator's incremental/per-VM-shard merge path is not durably retiring
corrective/dedup fixes, so a previously-collapsed duplicate can reappear without any new "bad" write. This raises the
priority of actually root-causing item 2 above (rather than continuing to rely on periodic manual `--force` rebuilds as
the only mitigation) — tracked as a todo in `plans/active/understat_local_backfill_completion_2026_07_06.md` (2026-07-13
entry) scoped to the sports bucket; the cross-bucket check this doc already calls out (cefi/defi/tradfi/prediction)
remains a separate, not-yet-scheduled follow-up.

## Non-FIXTURES blank-reason residue (left untouched, by design)

The same one-off leaves **612,682** consolidated-index `empty_confirmed` blank `error_reason` rows untouched
(non-FIXTURES sports data_types:
FIXTURE_STATS/FIXTURE_LINEUPS/FIXTURE_EVENTS/PREDICTIONS/ODDS/PLAYER_STATS/XG/WEATHER/INJURIES/…). Reason: their
non-blank twins use a MIX of `EXPECTED_NO_FIXTURE` / `EXPECTED_INSTRUMENT_NOT_LISTED` / `SOURCE_RETURNED_ZERO` — no
single canonical reason is derivable per data_type, so filling one would be a guess. A follow-up that re-derives the
correct reason per (data_type, date, league) from the fixture-presence + source-coverage SSOT (rather than a blanket
fill) is needed to close these. Tracked here for the sports/manifest epic.

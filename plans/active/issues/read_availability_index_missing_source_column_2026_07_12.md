---
doc_type: issue
title:
  read_availability_index() silently drops the crosscutting `source` column — every full-schema read returns source=""
  for all rows
summary: >-
  unified_trading_library.manifest_writer._read_index.read_availability_index()'s hardcoded _V8_COLUMNS list (the schema
  it backfills/returns on a full read) never includes "source", even though the writer records it on every row and the
  raw canonical parquet carries it. Any downstream code that filters or groups by `source` via the normal full-schema
  reader silently gets source="" for every row instead of an error — a silent-placeholder class bug on a field CLAUDE.md
  calls out as crosscutting and required.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library]
scope: [engineer]
tags: [manifest, data-correctness, silent-placeholder, read-path, source-column]
related:
  [
    plans/active/issues/sports_manifest_consolidator_duckdb_crash_and_silent_empty_read_2026_07_12.md,
    plans/active/issues/reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12.md,
    plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md,
  ]
created: 2026-07-12
parent_epic: infrastructure_master
assigned_vm: planning
resolved_by:
source: [sports_manifest_consolidator_duckdb_crash_and_silent_empty_read-003, slot-7 data_engineering]
priority: P1
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

## What I found

Found while re-verifying `sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md` item #6 (the 6-source
full-history gate). Ran a straightforward per-source `pending_fetch` check via
`unified_trading_library.manifest_writer._read_index.read_availability_index('instruments-store-sports-prd-...')` and
filtered by `data_type` alone (no `source` filter — the returned DataFrame simply has no `source` column to filter on).
This showed footystats `ODDS` at 84,768 `expected_unattempted` rows — a huge, alarming regression from the 0 a prior
session had verified ~2.5 hours earlier.

Cross-checked against the RAW canonical parquet (`gcsfs` + `pd.read_parquet` directly on
`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, bypassing the reader
entirely): the raw parquet DOES have a `source` column, and those 84,768 rows are **`source=api_football`** (82,721) and
blank-source (2,047) — NOT `source=footystats` at all. API_FOOTBALL is a completely different,
out-of-scope-for-that-plan data source that happens to also write `data_type=ODDS`-shaped rows. The "footystats ODDS"
gate genuinely passes at `eu=0`; the 84,768 figure was purely an artifact of not being able to filter by `source`
through the normal reader.

**Root cause**: `read_availability_index()`'s `_V8_COLUMNS` list
(`unified_trading_library/manifest_writer/_read_index.py` ~line 213) enumerates every column the reader
backfills/returns on a full read — it does NOT include `"source"`. The writer unconditionally sets `source` on every row
(`_writer_io.py:493`, `_writer_captured.py` multiple sites, `_rows.py:146`), and the raw canonical parquet carries real
`source` values (`api_football`, `footystats`, `odds_api`, `transfermarkt`, `understat`, `open_meteo`,
`soccer_football_info`, `mdps_odds_horizon_bucket`, `polymarket_clob`, confirmed via direct raw-parquet read on two
different sports buckets). But `read_availability_index()` never surfaces it: the column simply isn't in its return
schema, so `df.get("source", ...)`-style defensive code elsewhere (e.g.
`scripts/type_footystats_odds_non_covered_leagues_2026_06_29.py`'s own mask, which reads the raw parquet directly rather
than via this reader — that script is NOT affected) silently gets `""` for every row when going through the reader
instead.

This is distinct from the already-tracked
`sports_manifest_consolidator_duckdb_crash_and_silent_empty_read_2026_07_12.md` bug (that one was about `len(df)==0`
when the consolidator is stale) — this one returns a full-size, real-looking DataFrame with every row's `source`
silently blanked, on a perfectly healthy, fresh consolidator.

## Why it matters

- `source` is explicitly called out as crosscutting in workspace rules
  (`codex/02-data/availability-manifest-and-data-status.md` — "`source=` is crosscutting; `record_captured(source=…)`
  required"). Any downstream consumer that groups/filters `read_availability_index()`'s output by `source` (rather than
  re-deriving source from `venue`/`data_type` combinations, which is fragile and exactly what caused this session's
  false alarm) silently gets wrong results with no error, no warning, no missing column exception — just an all-blank
  column.
- This is a **silent-placeholder-class bug** (the exact anti-pattern
  `codex/02-data/honest-absence-downstream-handling.md` bans) on a field that exists in the write path and the raw
  storage, just not the read path's declared schema.
- Concretely dangerous for any manual/one-off verification script (like this session's gate re-check) that assumes
  `read_availability_index()` is schema-complete and filters by `source` — it will silently mis-scope, as happened here
  (a false 84,768-row "regression" that would have blocked a legitimate checkbox flip, or worse, triggered an
  unnecessary re-backfill VM if not caught).

## Recommended decision

- [x] ✅ [CODE] P1. Add `"source"` to `read_availability_index()`'s `_V8_COLUMNS` list (and the slim-read equivalent in
      `_read_availability_index_slim`, if it has its own column enumeration) in
      `unified-trading-library/unified_trading_library/manifest_writer/_read_index.py`, with the same
      backfill-to-`""`-for-legacy-rows treatment the other pre-existing columns get. Add a regression test asserting a
      full read surfaces real `source` values matching a raw-parquet read of the same fixture data. (repo:
      unified-trading-library) — unified-trading-library@a45066a9. `_read_availability_index_slim` has no hardcoded
      column enumeration (`_backfill_slim` genericly backfills whatever `columns` the caller requests), so it already
      surfaced `source` correctly — no change needed there, locked in by a regression test. Also found + fixed
      `transport` and `cadence` (same `_V8_COLUMNS` list, same root cause — v9 columns the writer stamps on every row
      but the full-schema reader never enumerated) since they're the identical defect in the exact list this todo
      touches. 3 new regression tests in `tests/unit/test_manifest_read_index_source_column.py`: full read surfaces real
      values (not blanked), legacy parquet backfills to `""`, slim read already passes values through. Full
      `quality-gates.sh` green (6400+ tests).
- [ ] [DATA] P2. Grep for other callers that rely on `df.get("source", ...)`-with-default patterns downstream of
      `read_availability_index()` (as opposed to reading the raw parquet directly) — any such site has been silently
      getting `source=""` and may have masked-wrong behavior worth auditing once the column is restored. (repo:
      unified-trading-library, instruments-service, market-tick-data-service)

## Progress Log

### 2026-07-12 ~11:10 UTC — slot-7 (data_engineering): filed while closing sports_p2 item #6

Found incidentally while re-verifying the 6-source full-history gate (see that plan's item #6 checkbox for the full
methodology). Not fixed inline — this is a `unified-trading-library` core-reader change with broad blast radius (every
service reading the manifest via the normal fast path), warranting its own scoped dispatch + full regression coverage
rather than a same-session drive-by patch during an unrelated VERIFY task.

### 2026-07-12 ~11:45 UTC — slot-7 (data_engineering): item #1 shipped

Added `"source"` to `_V8_COLUMNS` in `_read_index.py`. While in the list, discovered `"transport"` and `"cadence"` (both
v9, same file, same defect: written by every row per `_writer_io.py`/`_rows.py` `_ROW_KEY_COLUMNS` but never enumerated
by the full-schema reader) — fixed both in the same commit per the findings-triage "in your file" rule. Confirmed the
slim-read path (`_read_availability_index_slim` / `_backfill_slim`) needed NO change — it has no hardcoded column
enumeration, so it already passed `source`/`transport`/`cadence` through correctly when requested; locked that in with a
regression test rather than leaving it unverified. 3 new tests added. Full `quality-gates.sh` green — one unrelated
flaky test (`test_5000_sequential_writers_do_not_leak_fds`, an FD-count test, passed in isolation on retry) is noted,
not a regression from this change. Shipped `unified-trading-library@a45066a9` via quickmerge. Item #2 (grep for
downstream `df.get("source", ...)`-style callers) remains open — separate backlog task.

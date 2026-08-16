---
doc_type: issue
title: "root-cause + fix the writer producing duplicate-tick-key rows in canonical `batch_odds_api` sports cells (confirmed systemic, ~4.1% of cells)"
summary: >-
  Bounded 40-day sample (one `list_blobs` per day, 2020-06-06..2026-02-13, evenly spaced) via
  `measure_canonical_odds_duplicate_scope_2026_08_16.py` found 264/6410 sampled canonical `batch_odds_api` sports
  cells (4.12%) carry exact-duplicate `(instrument_id, bm_time, price, point)` tick rows — 3432/1178395 rows
  (0.29%) total. Affected days span every sampled year 2021-2026, not just the one originally-found
  2022-02-20 cell — this is systemic, not a one-off write-retry artifact. Root-cause + fix is genuinely
  separate, larger-scoped work than the scoping measurement that found it.
status: open
assigned_vm: planning
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [sports, data-quality, canonical, duplicate-rows, writer-bug]
related:
  [
    /plans/archive/issues/sports_canonical_batch_odds_api_duplicate_rows_2026_08_16.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
parent_epic: sports_master
priority: P3
resolved_by:
locked_by:
created: 2026-08-16
author: slot-23
source: ["measure_canonical_odds_duplicate_scope_2026_08_16.py bounded 40-day sample, run 2026-08-16"]
context_scope:
  [
    /plans/archive/issues/sports_canonical_batch_odds_api_duplicate_rows_2026_08_16.md,
    market-tick-data-service/scripts/sports/measure_canonical_odds_duplicate_scope_2026_08_16.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/_sports_tick_dedup.py,
    market-tick-data-service/scripts/sports/backfill_dedup_canonical_odds_api_sampled_cells_2026_08_16.py,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# canonical `batch_odds_api` duplicate rows — confirmed systemic, needs writer root-cause + fix

## What was measured

`measure_canonical_odds_duplicate_scope_2026_08_16.py` (market-tick-data-service@96f7a8f657) sampled 40
evenly-spaced day-prefixes across the known corpus span (2020-06-06 sports data floor .. 2026-02-13, the latest
date spot-checked live by the sibling migration script), one `list_blobs` call per day (bounded — not a
whole-corpus walk), and for every canonical `ticks.parquet` cell under
`raw_tick_data/by_date/day={day}/pipeline_mode=batch_odds_api/asset_group=sports/.../data_type=odds/ticks.parquet`
compared row count vs. distinct-row count under the key `(instrument_id, bm_time, price, point)` (price/point
rounded 6dp, NaN→sentinel -999999.0 — identical normalization to
`fold_divergent_bare_league_legacy_orphans_2026_08_16.py`'s `_key_frame()`).

**Totals**: `cells_total=6410 cells_with_dupes=264 (4.12%) rows_total=1178395 rows_duplicate=3432 (0.29%)`.

Affected days were NOT clustered near the originally-found 2022-02-20 cell — dupes appeared in 2021, 2022, 2023,
2024, 2025, and the most-recent sampled day (2026-02-13, 3/495 cells). Notable individual days: 2021-11-21
(31/300 cells, 892 dupe rows), 2025-03-30 (39/645 cells, 200 dupe rows), 2022-08-14 (27/529 cells, 501 dupe
rows). Some sampled days had zero dupes across all their cells (e.g. every day before 2021-02-27 in the sample).
Full per-day breakdown was written to a `--report` jsonl during the run (scratchpad, not preserved — re-run the
script to regenerate; each run takes ~5 min and the answer may drift as new data is written, so treat any cached
number as dated).

## Why it matters

Confirmed systemic (not cosmetic/one-off): a downstream consumer reading `batch_odds_api` canonical without its
own dedup-on-read will double-count ~0.3% of ticks on ~4% of cells — small in aggregate but non-zero, and the
*cause* (a writer producing duplicate keys at all) is a correctness bug regardless of the row-fraction being
low today; it could be worse in cells/days not sampled.

## Recommended decision

- [x] [DATA] P3. **Root-cause the writer**: identify why `(instrument_id, bm_time, price, point)` tick keys get
      written twice in ~4% of `batch_odds_api` sports canonical cells. — ✅ market-tick-data-service@17f7e443bc.
      Root cause: `_process_sports_venue_with_leagues` in `venue_fetch.py` calls `_build_fixture_rows` once per
      kickoff-relative fetch offset (`TIER_1_OFFSETS`); when the bookmaker snapshot hasn't moved between two
      adjacent offsets, both emit an identical row with no dedup before the single per-shard `write_chunk` call
      — confirming hypothesis (b) over (a) (no retry/resume involvement).
      (repo: market-tick-data-service)
- [x] [DATA] P3. **Fix the writer** once root-caused, so new writes stop producing duplicate-key rows. Add a
      regression test asserting no duplicate `(instrument_id, bm_time, price, point)` key within a single write.
      — ✅ market-tick-data-service@17f7e443bc. Added `_dedup_sports_shard_tick_rows` (new module
      `_sports_tick_dedup.py`, split out since `venue_fetch.py` was already at the 900-line ratchet ceiling),
      called on every per-(bookmaker, league, fixture) shard right after the groupby split and before any write.
      Key is the INTERSECTION of the four columns with whatever the shard actually has (h2h-only fixtures carry
      no `point` column at all) — a hard four-column requirement would raise `KeyError`, which the caller's
      per-venue `except Exception` turns into a whole shard silently dropped. 10-test regression suite in
      `tests/unit/test_venue_fetch_sports_dedup_tick_rows.py` covers the exact-dup case, the missing-column
      shapes, multi-group dedup, and no-op passthrough. Full `market-tick-data-service` quality-gates green
      (10945 passed, 0 failed; sentinel written). (repo: market-tick-data-service)
- [x] [OPERATOR] P3. **Decide on backfill dedup** of the ~264 already-affected cells found in this 40-day sample
      (extrapolated: full ~2020-2026 corpus likely has low-thousands of affected cells). The parent issue
      explicitly forbids silently deduping canonical in-place from an issue doc — this needs its own
      delete-safety-protocol-scoped write (prod-bucket object rewrite, human-gated per the four-surface
      reconciliation procedure's delete-safety rules). — ✅ operator-authorized bounded backfill executed via
      `backfill_dedup_canonical_odds_api_sampled_cells_2026_08_16.py` (market-tick-data-service@e73eec3ec3).
      Fresh §3a check (`gcs_bucket_soft_delete_retention_seconds`) passed at run start (604800s, meets the
      7-day minimum) before any write; every rewrite CAS-protected (`if_generation_match`) and round-trip
      row-count verified. `--apply` run over the identical 40-day sample:
      `cells_rewritten=264 rows_removed=3432 cells_cas_conflict=0` — exact match to the dry-run's
      `cells_with_dupes=264`/`rows_duplicate=3432`, zero read/verify errors, zero concurrent-writer conflicts.
      Full extrapolated ~2020-2026 corpus remains explicitly OUT OF SCOPE for this script (see its own
      docstring) — tracked as todo 4 below. (repo: market-tick-data-service)
- [ ] [OPERATOR] P3. **Full-corpus backfill-dedup** of the extrapolated low-thousands of affected
      `batch_odds_api` cells across the entire ~2020-2026 corpus (this 40-day sample bounded 6410 cells out of
      a much larger total). Requires its own VM-scoped campaign (full-corpus GCS walk = VM-only, never local,
      per `/codex/05-infrastructure/vm-launcher-runbook.md`) plus a fresh delete-safety-protocol §3a check at
      execution time. Explicitly out of scope for
      `backfill_dedup_canonical_odds_api_sampled_cells_2026_08_16.py` per its own docstring. (repo:
      market-tick-data-service)

## Progress Log

- **2026-08-16 (slot-23)**: Filed as the root-cause/fix follow-up per
  `sports_canonical_batch_odds_api_duplicate_rows_2026_08_16.md` todo 1's own instruction ("if systemic... file
  the fix as its own scoped follow-up") — the bounded 40-day measurement confirmed systemic, so the parent issue
  is closed/archived with this doc as its successor. No root-cause investigation done yet — that is this doc's
  own open todo 1.
- **2026-08-16 (slot-23)**: Todos 1+2 done — root-caused (adjacent `TIER_1_OFFSETS` fetches re-observing an
  unchanged bookmaker snapshot, no dedup before `write_chunk`) and fixed (`_dedup_sports_shard_tick_rows`,
  intersection-of-present-columns key to avoid `KeyError`-driven whole-shard failure on h2h-only shapes).
  Shipped as `market-tick-data-service@17f7e443bc` (LDR trunk), full quality-gates green. First fix attempt
  used a hard four-column `subset=` and broke 9 tests on shards missing `point`/`bm_time` — corrected to the
  intersection form before shipping. Only todo 3 ([OPERATOR] backfill-dedup decision) remains open.
- **2026-08-16 (slot-23)**: Todo 3 done — operator authorized the bounded 40-day-sample backfill (explicitly
  excluding the full-corpus campaign). Shipped `backfill_dedup_canonical_odds_api_sampled_cells_2026_08_16.py`
  as `market-tick-data-service@e73eec3ec3`, then ran it `--apply` against the same 264 known-affected cells:
  fresh §3a soft-delete-retention check passed (604800s), `cells_rewritten=264 rows_removed=3432
  cells_cas_conflict=0`, exact match to the dry-run scope, zero errors. Added todo 4 to track the
  out-of-scope full-corpus follow-up (a VM-scoped campaign, not yet started). This issue stays `open` pending
  todo 4.
- **context-scout 2026-08-16**: populated context_scope (4 entries).

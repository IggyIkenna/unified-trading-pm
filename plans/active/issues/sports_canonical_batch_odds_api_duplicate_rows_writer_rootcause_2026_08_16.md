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

- [ ] [DATA] P3. **Root-cause the writer**: identify why `(instrument_id, bm_time, price, point)` tick keys get
      written twice in ~4% of `batch_odds_api` sports canonical cells. Leading hypotheses (unconfirmed): (a)
      retry-without-idempotency-check on a partial-failure resume re-appends already-written ticks instead of
      skipping/overwriting; (b) overlapping capture-window merges write the same tick twice across adjacent
      capture runs. Start from the `batch_odds_api` sports writer path in `market_tick_data_service` — not yet
      located/read as part of this issue. (repo: market-tick-data-service)
- [ ] [DATA] P3. **Fix the writer** once root-caused, so new writes stop producing duplicate-key rows. Add a
      regression test asserting no duplicate `(instrument_id, bm_time, price, point)` key within a single write.
      (repo: market-tick-data-service)
- [ ] [OPERATOR] P3. **Decide on backfill dedup** of the ~264 already-affected cells found in this 40-day sample
      (extrapolated: full ~2020-2026 corpus likely has low-thousands of affected cells). The parent issue
      explicitly forbids silently deduping canonical in-place from an issue doc — this needs its own
      delete-safety-protocol-scoped write (prod-bucket object rewrite, human-gated per the four-surface
      reconciliation procedure's delete-safety rules). (repo: market-tick-data-service)

## Progress Log

- **2026-08-16 (slot-23)**: Filed as the root-cause/fix follow-up per
  `sports_canonical_batch_odds_api_duplicate_rows_2026_08_16.md` todo 1's own instruction ("if systemic... file
  the fix as its own scoped follow-up") — the bounded 40-day measurement confirmed systemic, so the parent issue
  is closed/archived with this doc as its successor. No root-cause investigation done yet — that is this doc's
  own open todo 1.

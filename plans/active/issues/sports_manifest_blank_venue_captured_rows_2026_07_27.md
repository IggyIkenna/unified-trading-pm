---
doc_type: issue
title:
  '2,490 captured sports manifest rows carry venue="" (blank string) — discovered during Track C venue re-stamp census'
summary: >-
  While sizing `sports_consolidated_native_ao_extract_2026_07_25.md`'s Track C venue re-stamp todo, a corpus-wide
  read-only census of the sports availability_index (no filter, full history) found 2,498 manifest rows with `venue==""`
  (blank string), of which 2,490 carry `capture_status=captured` (real data, not honest-absence placeholders) — the
  remaining 8 are `empty_confirmed`. By `data_type`: `trades`=1,273, `odds_horizon_bucket`=1,106, `trades_inplay`=111,
  plus a handful of `ODDS_MOVEMENT`/`ODDS_SNAPSHOT`/`odds_movement`/`odds_snapshot` (2 each). This is a distinct axis
  from the Track C todo's own scope (LADBROKES_UK/SPORT888/footystats-ODDS_API/FOOTBALL/UNKNOWN) — not conflated with
  it, not fixed inline, filed separately per the Findings Closure hard rule.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, unified-trading-pm]
scope: [engineer]
tags: [data-correctness, sports, venue, manifest, blank-value]
related:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/issues/sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md,
  ]
created: 2026-07-27
priority: P2
parent_epic: sports_master
source: >-
  Measured directly against the live gs://market-data-tick-sports-prd-central-element-323112/_index/
  availability_index.parquet via unified_trading_library.read_availability_index (columns=[date, venue, pipeline_mode,
  instrument_type, data_type, row_count, capture_status], no filter, full history), 2026-07-27, during
  sports_consolidated_native_ao_extract_2026_07_25.md's Track C todo. Ad-hoc read-only query, not yet a saved script.
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/issues/sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md,
    market-data-processing-service/market_data_processing_service/app/core/canonical_writer_shaping.py,
  ]
assigned_vm: planning
assigned_role: data_engineering
resolved_by:
---

# Sports manifest rows with a blank `venue` string

## What was measured (2026-07-27)

Corpus-wide, no date/venue filter, live prod bucket:

- Total blank-venue (`venue==""`) rows: **2,498**
- `capture_status` breakdown: `captured`=2,490, `empty_confirmed`=8
- `data_type` breakdown (blank-venue rows only): `trades`=1,273, `odds_horizon_bucket`=1,106, `trades_inplay`=111,
  `ODDS_MOVEMENT`=2, `ODDS_SNAPSHOT`=2, `odds_movement`=2, `odds_snapshot`=2

This is a REAL, non-trivial population of genuinely captured rows (not honest-absence placeholders) with no venue
identity recorded. 2,490 captured rows with an unrecoverable-from-the-manifest-alone venue is a real gap for any
per-venue coverage/completeness view, and a candidate for silent double-counting or under-counting depending on how
downstream consumers treat a blank string vs. a missing key.

## What this doc is NOT claiming

Not yet root-caused. A plausible (not confirmed) hypothesis, given the SAME-DAY parser-bug family already fixed in
`market-data-processing-service@51502c3` / `instruments-service@f46e553e`
(`sports_closeout_batch1_ao_ready_2026_07_24.md` todo 2): `canonical_writer_shaping.py`'s
`_venue_token_from_canonical_id(raw, asset_group=SPORTS)` returns `parts[1] if len(parts) >= 2 and parts[1] else ""` —
an instrument_id whose bookmaker segment (position 1) is itself an empty string between colons (e.g.
`FOOTBALL::MATCH_ODDS:...`) would legitimately produce `venue=""` even with the asset_group gate correctly applied (the
gate fixes WHICH position is read, not what happens when that position is empty). This is UNCONFIRMED — not verified
against real captured row content, and the `trades`/`trades_inplay` data_types are RAW MTDS capture (not MDPS
candle-derived), so a different root cause (MTDS-side, not the MDPS candle-write bug) is equally plausible for those.
`odds_horizon_bucket` — the largest single chunk (1,106 rows) — IS one of the 4 registered sports candle adapters, so
the MDPS-side hypothesis is more plausible for that data_type specifically.

## Recommended decision

1. Root-cause: read a real captured blank-venue row's `instrument_id` content directly (pick one from each data_type
   group) to determine whether the bookmaker/venue segment is genuinely empty in the source id, or whether the
   manifest-recording path independently lost it.
2. If MDPS-side (candle path): confirm whether `_venue_token_from_canonical_id`'s empty-string fallback should instead
   raise/skip-record rather than silently write `venue=""` — a design question, not a re-stamp (there is no "correct"
   venue to re-stamp TO if the source id genuinely lacks one).
3. If MTDS-side (raw capture): a separate, unrelated bug in the raw ingestion path needs its own root-cause.
4. Not sized here whether this is safely re-stampable, needs a delete, or needs a writer-side fix + accept-as-is for
   historical rows — that determination needs step 1 first.

- [ ] [DIAG] P2. Root-cause the 2,490 captured `venue=""` sports manifest rows (repo: market-tick-data-service /
      market-data-processing-service, read-only: read actual captured row content for a sample of each affected
      data_type — `trades`, `trades_inplay`, `odds_horizon_bucket`, `ODDS_MOVEMENT`/`ODDS_SNAPSHOT` (both casings) — to
      determine whether the instrument_id's bookmaker segment is genuinely blank at the source or lost in
      manifest-recording). **Done when**: a written root-cause finding for each affected data_type is recorded, with a
      recommendation (re-stampable / needs writer fix / accept-as-is) for each. **PARTIAL PROGRESS 2026-07-29 (batch
      closeout pass), NOT closing — done-when not yet met.** Live manifest sample (`read_availability_index`,
      `market-data-tick-sports-prd-central-element-323112`,
      columns=[date,venue,data_type,instrument_id,capture_status]): for all 3 populated affected data_types
      (`trades`=1273, `odds_horizon_bucket`=1106, `trades_inplay`=111 — the `ODDS_MOVEMENT`/`ODDS_SNAPSHOT` casings are
      too small, 2 rows each, to sample meaningfully), **`instrument_id` is ALSO `None`/null on every sampled row**, not
      just `venue`. This narrows the hypothesis space (both the venue token AND the instrument_id are blank together,
      not a venue-only parsing gap) but does not itself distinguish "genuinely blank at the source" from "lost in
      manifest-recording" per the todo's own done-when — that needs a read of the actual RAW parquet content (not just
      the manifest row) for one of these shard atoms, which was not attempted this pass (would need locating the exact
      GCS object per sampled row, out of this session's time-box). Left `- [ ]` — root cause still open.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY -> `assigned_vm: planning` — the sole `[DIAG] P2` is a read-only
  root-cause with an explicit stated done-when ('a written root-cause finding for each affected data_type, with a
  re-stampable / needs-writer-fix / accept-as-is recommendation'), i.e. an audit whose outcome is determinable by the
  worker alone. Partial progress already recorded 2026-07-29; the remaining step (read the RAW parquet content behind
  one sampled shard atom) is bounded and touches no delete/VM-launch. Conflict-check CLEAR: the doc itself states this
  is a distinct axis from `sports_consolidated_native_ao_extract_2026_07_25.md`'s Track C venue re-stamp, and no active
  planning doc claims the blank-`venue` root cause.

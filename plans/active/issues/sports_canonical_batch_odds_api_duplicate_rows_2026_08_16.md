---
doc_type: issue
title: "canonical `batch_odds_api` sports cells carry pre-existing duplicate rows under the (instrument_id, bm_time, price, point) tick key — scope/impact not yet measured"
summary: >-
  While building `fold_divergent_bare_league_legacy_orphans_2026_08_16.py` (sports_league_legacy_orphan_purge_followup_2026_08_15.md
  todo 3), a live spot-check of one canonical cell (day=2022-02-20, venue=LIVESCOREBET, league_id=2._BUNDESLIGA)
  found 18 rows where only 9 distinct `(instrument_id, bm_time, price, point)` ticks exist — every tick appears
  exactly twice. This was ONE cell, found incidentally, not from a scoped audit — scope (how many cells/days
  affected, whether downstream consumers already dedupe on read) is unmeasured.
status: open
assigned_vm: planning
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [sports, data-quality, canonical, duplicate-rows]
related: [/plans/archive/issues/sports_league_legacy_orphan_purge_followup_2026_08_15.md]
parent_epic: sports_master
priority: P3
resolved_by:
locked_by:
created: 2026-08-16
author: slot-23
source: ["incidental finding while building fold_divergent_bare_league_legacy_orphans_2026_08_16.py"]
context_scope:
  [
    /plans/archive/issues/sports_league_legacy_orphan_purge_followup_2026_08_15.md,
    market-tick-data-service/scripts/sports/fold_divergent_bare_league_legacy_orphans_2026_08_16.py,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# canonical `batch_odds_api` duplicate rows — scope unmeasured

## What I found

Live-read `gs://market-data-tick-sports-prd-central-element-323112/raw_tick_data/by_date/day=2022-02-20/pipeline_mode=batch_odds_api/asset_group=sports/venue=LIVESCOREBET/league_id=2._BUNDESLIGA/instrument_type=odds/data_type=odds/ticks.parquet`
(120 total rows). For instrument_id
`FOOTBALL:LIVESCOREBET:OVER_UNDER_2_5:PREMIER_LEAGUE:2022-23:LEEDS-MAN_UNITED::OVER` specifically, 18 canonical rows
existed under the key `(instrument_id, bm_time, price, point)` where only 9 are distinct — the first 9 rows repeat
exactly (same `bm_time`/`price`/`point`) as rows 10-18. This surfaced because
`fold_divergent_bare_league_legacy_orphans_2026_08_16.py`'s row-loss guard (a MERGE that would produce FEWER rows
than the existing canonical object refuses rather than silently deduping) tripped on two other days
(`2020-06-29 MATCHBOOK/SEGUNDA_DIVISION`, `2020-06-30 BETVICTOR/CHAMPIONSHIP`) for the same reason before the
migration script was fixed to never re-dedup `target`'s own rows.

## Why it matters

If this is systemic (not a one-off write-retry artifact on this one cell), any downstream consumer that reads
`batch_odds_api` canonical objects WITHOUT its own dedup-on-read would double-count these ticks (e.g. row-count-based
weighting, naive aggregation). Per "Data pipeline correctness is the heartbeat", this needs scoping before it can be
ruled cosmetic.

## Recommended decision

- [ ] [DATA] P3. **Scope the duplication**: sample N canonical `batch_odds_api` cells across days/venues (bounded,
      not a whole-corpus walk — reuse the `_canonical_day_venue_prefix`/`_existing_odds_cell_paths` helpers already
      in `verify_bare_league_legacy_orphan_content_2026_08_16.py` /
      `fold_divergent_bare_league_legacy_orphans_2026_08_16.py`) and measure what fraction of cells/rows carry an
      exact-duplicate tick key. If near-zero outside the one measured cell, downgrade/close as a one-off write
      artifact. If systemic, root-cause the writer (retry-without-idempotency-check? overlapping capture windows?)
      and file the fix as its own scoped follow-up — do NOT silently dedupe canonical in-place from this issue doc;
      that needs its own delete-safety-protocol-scoped write. (repo: market-tick-data-service)

## Progress Log

- **2026-08-16 (slot-23)**: Filed as an incidental finding from the sibling orphan-purge issue's todo 3 work — not
  investigated further this session (out of that todo's own scope).

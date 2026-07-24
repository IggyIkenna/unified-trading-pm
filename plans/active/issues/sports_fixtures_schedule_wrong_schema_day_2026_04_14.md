---
doc_type: issue
title:
  Sports fixtures_schedule day=2026-04-14 — 85 league shards carry an instrument-catalogue schema, not fixtures data
summary:
  85 `entity=fixtures_schedule` parquet shards under `day=2026-04-14` (across 85 distinct leagues) fail to read with the
  fixtures schema (`af_league_id`, `season`, `round`, ...) and instead resolve to an instrument-catalogue/registry
  schema (`instrument_key`, `venue`, `instrument_type`, `raw_symbol`, `base_asset`, `quote_asset`, `tick_size`, ...).
  Discovered incidentally while scanning the sports fixtures corpus for the round-derivation residual backfill.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, data-correctness, schema-mismatch, fixtures-schedule]
related: [/plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md]
created: 2026-07-24
assigned_vm: planning
parent_epic: sports_master
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
source: discovered live while running the round-derivation residual census (sports_closeout_batch1_ao_ready-008)
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# Sports fixtures_schedule day=2026-04-14 — wrong-schema shards (instrument-catalogue content in a fixtures path)

## How this was found

While running a corpus-wide census of `sports_reference/by_date/.../entity=fixtures_schedule/` parquets (single walk,
projecting `af_league_id`/`season`/`round`) to scope the round-derivation residual backfill
(`sports_closeout_batch1_ao_ready-008`), 85 of 45,032 files raised a pyarrow column-projection error instead of reading
normally:

```
No match for FieldRef.Name(af_league_id) in instrument_key: string
venue: string
instrument_type: string
raw_symbol: string
base_asset: string
quote_asset: string
status: string
available_from_datetime: timestamp[us, tz=UTC]
...
tick_size: decimal128(2, 2)
min_size: decimal128(1, 0)
contract_size: decimal128(1, 0)
...
```

This is not a malformed/corrupt parquet — the file reads fine, it just carries a **completely different schema**: an
instrument-catalogue/registry shape (`instrument_key`, `venue`, `instrument_type`, `raw_symbol`, `base_asset`,
`quote_asset`, `tick_size`, `min_size`, `contract_size`, `available_from_datetime`/`available_to_datetime`,
`asset_class`, `option_type`/`underlying`/`margin_type`/`legs` for derivatives, `regular_open_utc`/`holiday_calendar`
for trading-calendar data, `available_at`, plus pyarrow dataset bookkeeping columns `__fragment_index`, `__batch_index`,
`__last_in_fragment`, `__filename`). None of that matches sports fixtures data
(`af_fixture_id`/`af_league_id`/`season`/`round`/team names/scores/kickoff time).

## Scope measured

**All 85 affected files share exactly one `day=` partition: `day=2026-04-14`.** Confirmed via the same corpus census —
zero other days showed this failure across the full 45,032-file walk. Affected leagues span a wide, unrelated set
(sampled: `ARGENTINA_RESERVE_LEAGUE`, `ARMENIA_FIRST_LEAGUE`, `ARUBA_DIVISION_DI_HONOR`, `AUSTRIA_REGIONALLIGA_OST`,
`ENGLAND_CHAMPIONSHIP`, `ENGLAND_LEAGUE_TWO`, `EGYPT_PREMIER_LEAGUE`, `HUNGARY_NB_I`, and many more — 85 total, no
obvious pattern by region/tier that would explain a legitimate content match). All paths follow the pattern:

```
sports_reference/by_date/day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures_schedule/league=<LEAGUE>/fixtures_schedule.parquet
```

## Why it matters

- Any reader that projects only the columns it expects (as the round-derivation script and this census both do) will
  silently skip these 85 shards as "unreadable" rather than surfacing the corruption loudly — a `honest-absence`
  violation risk if a downstream consumer instead does a blanket `pd.read_parquet(path)` and gets back an
  instrument-catalogue DataFrame it doesn't validate the shape of.
- This blocks the round-derivation residual backfill (and any other content-dependent job) from ever closing gaps for
  these 85 (league, day) shards — they can't be scanned for `round` at all.
- The failure mode (identical wrong schema across 85 unrelated leagues, one single day) points at a **write-path bug**,
  not per-league data quality — most likely a batch job that, for this one day's run, wrote its OTHER product
  (instrument catalogue / registry snapshot) to the fixtures_schedule path instead of (or in addition to) the real
  fixtures payload — e.g. a bucket/path variable reused across two write calls in the same batch run.

## Recommended decision

1. Confirm the write-path bug: find whichever batch job ran for `day=2026-04-14` and produced an instrument-catalogue
   shape, and trace how its target path resolved to `sports_reference/.../entity=fixtures_schedule/league=<L>/...`
   instead of wherever the catalogue actually belongs.
2. Snapshot the 85 objects (GCS soft-delete already provides a 7-day window; snapshot to `.bak` before touching, same
   convention as the round-derivation scripts) then re-fetch/re-derive `day=2026-04-14`'s real fixtures content for
   these 85 leagues once the write-path bug is fixed — do not leave a hole for this day.
3. Add a schema assertion at the writer (or a post-write validation step) so this class of mix-up fails loud instead of
   silently producing an unreadable-by-projection shard.

## Todos

- [ ] [DIAG] P1. Identify the batch job/writer that ran for `day=2026-04-14` and produced instrument-catalogue-shaped
      output under the `entity=fixtures_schedule` path (repo: instruments-service). **Done when**: a written root-cause
      conclusion cites the specific writer code path and why its target resolved to the fixtures_schedule prefix.
- [ ] [CODE] P1. Fix the write-path bug so no future run can write a non-fixtures schema under
      `entity=fixtures_schedule/` (repo: instruments-service). **Done when**: a regression test reproduces the old
      bad-path resolution and asserts the fix.
- [ ] [DATA] P2. Snapshot + re-fetch the real `day=2026-04-14` fixtures content for the 85 affected leagues (repo:
      instruments-service). **Done when**: all 85 `league=<L>/fixtures_schedule.parquet` shards for `day=2026-04-14`
      read with the correct fixtures schema.
- [ ] [CODE] P2. Add a schema assertion (column-set check) at the fixtures_schedule writer so a future mismatch fails
      loud instead of silently producing an unreadable-by-projection shard (repo: instruments-service). **Done when**: a
      unit test feeds a wrong-schema DataFrame into the writer and asserts a loud failure.

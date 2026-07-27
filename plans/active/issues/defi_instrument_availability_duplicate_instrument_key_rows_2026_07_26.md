---
doc_type: issue
title:
  DeFi instrument_availability flat shape carries duplicate instrument_key rows within a single (day, venue) shard for
  pool-heavy DEX venues
summary: >-
  Surfaced while running the null-aware flat-vs-hive shape reconciliation
  (defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md's 2026-07-26 entry). A stratified 100-day sample (3,045
  venue-day pairs) found duplicate `instrument_key` rows within a single shard's `instruments.parquet` for several
  pool-heavy DEX venues -- `PANCAKESWAP_V3-BSC`, `UNISWAP_V3-OPTIMISM`, `UNISWAP_V3-POLYGON`, `UNISWAP_V4-ETHEREUM`,
  `PANCAKESWAP_V3-BASE` -- up to 23 duplicate rows observed in one shard (`day=2023-11-22`, `venue=UNISWAP_V3-OPTIMISM`,
  289 rows / 23 duplicate `instrument_key` values). This is a within-shape data-quality question, independent of the
  flat-vs-hive divergence question the source doc addresses -- not investigated further here (out of that todo's scope).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [defi, instrument_availability, duplicate-rows, data-quality, dex-pools]
related:
  [
    /plans/active/issues/defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
  ]
created: 2026-07-26
priority: P3
parent_epic: defi_master
source:
  "Surfaced while re-running defi_satellite_ao_dispatch_batch2-010's null-aware shape-B reconciliation (worker, slot 6,
  2026-07-26)"
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: research
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# DeFi instrument_availability flat shape: duplicate instrument_key rows within a shard

## What I found

While comparing the flat vs hive `instrument_availability` shapes for a stratified 100-day sample (3,045 venue-day
pairs), the null-aware field comparator needed to be made duplicate-key-safe: naive pandas `.loc[key]` indexing on a
duplicated `instrument_key` returns a multi-row slice rather than a single row, which spuriously flags every column as
"different" when compared against the other shape's single matching row.

Of the 189 pairs the naive comparator flagged as "real diff", 162 turned out to have duplicate `instrument_key` values
within the FLAT shape's own `instruments.parquet` for that (day, venue) — not a flat-vs-hive divergence at all, a
within-flat-shape duplication. Concentrated in pool-heavy DEX venues (more pools per venue → more chance of a duplicate
write): `PANCAKESWAP_V3-BSC`, `UNISWAP_V3-OPTIMISM`, `UNISWAP_V3-POLYGON`, `UNISWAP_V4-ETHEREUM`, `PANCAKESWAP_V3-BASE`.
Duplicate counts GROW over time within a venue (e.g. `PANCAKESWAP_V3-BSC`: 3 dupes on `2023-08-19` → 15 dupes on
`2023-12-15`), suggesting an accumulating write-time issue (repeated pool discovery writing the same `instrument_key`
more than once per day-shard) rather than a one-off.

Sample:

| day        | venue               | flat rows | flat duplicate keys |
| ---------- | ------------------- | --------- | ------------------- |
| 2023-08-19 | PANCAKESWAP_V3-BSC  | 79        | 3                   |
| 2023-11-22 | UNISWAP_V3-OPTIMISM | 289       | 23                  |
| 2023-12-15 | PANCAKESWAP_V3-BSC  | 108       | 15                  |

## Why it matters

Duplicate `instrument_key` rows within one shard mean any downstream consumer that does a naive `set_index` / dict-keyed
lookup on `instrument_key` (rather than de-duplicating first) will silently pick an arbitrary one of the duplicates, or
double-count instruments in a row-count-based metric. Not confirmed here whether the duplicate rows are byte-identical
to each other (a harmless re-write) or carry genuinely different field values per duplicate (a real data-quality bug) —
that determination is the actual next step, not yet done.

## Recommended decision

- [ ] [DATA] P3. Determine whether the duplicate `instrument_key` rows within a single flat-shape shard are
      byte-identical re-writes (harmless) or carry differing field values (a real dedup/write-time bug), for the 5
      affected venues above. If genuinely differing, root-cause why the writer emits the same `instrument_key` more than
      once per day-shard and fix at the source; if harmless re-writes, consider a light de-dup pass at read time or
      write time. Repo: instruments-service. **Done when**: a verdict (harmless vs real) is recorded for a
      representative sample of the affected venues, with a fix todo filed if real.

## Progress Log

- 2026-07-26 (worker, slot 6): Filed while running the shape-B null-aware reconciliation; not investigated further (out
  of that todo's scope).

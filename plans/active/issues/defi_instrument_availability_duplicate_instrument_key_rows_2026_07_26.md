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

- [x] ✅ [DATA] P3. **DONE 2026-07-29 — verdict: REAL bug, not harmless.** Determine whether the duplicate
      `instrument_key` rows within a single flat-shape shard are byte-identical re-writes (harmless) or carry differing
      field values (a real dedup/write-time bug), for the 5 affected venues above. Live-read the flat-shape
      `instrument_availability/by_date/day=<D>/venue=<V>/instruments.parquet` for 3 representative samples: (1)
      `UNISWAP_V3-OPTIMISM`/`2023-11-22` (289 rows, matches this doc's own cited number exactly) — 16 duplicate-key
      groups, **all 16 differing** (distinct `pool_address`/`base_asset_contract_address`/etc per duplicate); (2)
      `PANCAKESWAP_V3-BSC`/`2023-08-19` — 3 duplicate groups, all 3 differing; (3) `PANCAKESWAP_V3-BSC`/`2023-12-15` — 9
      duplicate groups, all 9 differing. **0 of 28 sampled duplicate groups across 3 samples were byte-identical.**
      Concrete example: `instrument_key=PANCAKESWAP_V3-BSC:POOL:USDT-USDC:10000` maps to TWO genuinely different
      on-chain pools (`pool_address=0x846d...` vs `0x1750...`, same base/quote/fee-tier) — the `instrument_key` format
      (`VENUE:TYPE:BASE-QUOTE:FEE_TIER`) does not disambiguate multiple real pools sharing the same base/quote/fee-tier
      combination. **Root cause**: the key builder for DEX-pool venues omits `pool_address` (or an equivalent
      disambiguator), so distinct on-chain pools legitimately collide. **Follow-up fix todo filed** below (not fixed
      inline — determining the right disambiguation scheme without breaking existing `instrument_key` consumers needs
      its own scoped pass).

- [ ] [CODE] P2. **Fix the DeFi pool `instrument_key` collision** for pool-heavy DEX venues (confirmed real 2026-07-29,
      see the DONE todo above) — the key format `VENUE:TYPE:BASE-QUOTE:FEE_TIER` does not uniquely identify a pool when
      multiple real on-chain pools share the same base/quote/fee-tier (observed on `PANCAKESWAP_V3-BSC`,
      `UNISWAP_V3-OPTIMISM`, and likely the other 3 venues this doc names). Scope: add `pool_address` (or an equivalent
      on-chain disambiguator already present as a column, e.g. a short hash suffix) to the key derivation for DEX-pool
      instrument_types, verify no downstream consumer keys off the OLD collision-prone format in a way that would break,
      and backfill/relabel historical rows. Repo: instruments-service. **Done when**: a fresh duplicate-key scan across
      the 5 named venues (+ any others sharing the same key-builder path) returns 0 genuine collisions, with a
      regression test proving 2 same-base/quote/fee-tier pools now get distinct keys.

## Progress Log

- 2026-07-26 (worker, slot 6): Filed while running the shape-B null-aware reconciliation; not investigated further (out
  of that todo's scope).

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
status: resolved
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
  "instruments-service@30fe4511 (Option B consumer-side audit + regression test proving DEX-pool catalogue rollup never
  collapses same-symbol/different-address pools, operator-ruled 2026-07-30)"
locked_by:
---

> **✅ ARCHIVED 2026-07-30** — both todos done (real-bug verdict confirmed, then Option B consumer-side audit +
> regression test shipped per operator ruling), 0 open todos, unlocked. Moved to `plans/archive/issues/`.

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

- [x] ✅ [CODE] **WON'T-DO-per-operator-2026-07-18-ruling** (was P2, "Fix the DeFi pool `instrument_key` collision" by
      changing the symbol grammar). **Superseded by the narrow consumer-side fix below** (BLK-b3379171, worker slot 8,
      2026-07-30): the originally-scoped fix (append `pool_address`/a hash disambiguator INTO the symbolic
      `instrument_key`/`glued_pair_id` grammar) is exactly the id-folding the operator already REJECTED —
      `/codex/02-data/defi-canonical-naming-ssot.md` § "POOL identity is a two-id / dual-key model (Option A,
      operator-ruled 2026-07-18)" states verbatim that a POOL row's `instrument_id`/`canonical_instrument_id` (machine
      key, bare `pool_address.lower()`, the MTDS/manifest join key) and `glued_pair_id` (symbolic
      `<VENUE>-<CHAIN>:POOL:<BASE>-<QUOTE>[-<FEE_BPS>]`, the human-readable/UI form) "MUST keep diverging for POOL rows"
      — collapsing them (suffixing the symbol with an address/hash) breaks the MTDS content-join and was already
      superseded once (`defi_pool_id_chain_uniqueness_2026_07_18.md`). It would also have broken confirmed real
      consumers in unified-api-contracts (`parse_glued_pool_id`), 2 instruments-service migration scripts, the
      catalogue's byte-identical `glued_pair_id` invariant, and MTDS's independent key reconstruction — investigation +
      full citations in BLK-b3379171 (dashboard) / worker slot-8 session, 2026-07-30.
- [x] ✅ [CODE] P2. **Resolving fix (Option B, operator-directed 2026-07-30)** — the SSOT's own documented remediation
      for a colliding symbolic key is fixing the DOWNSTREAM CONSUMER, not the key. Audited every consumer of the raw
      `instrument_availability/by_date/.../instruments.parquet` shard for naive `instrument_key`-uniqueness assumptions:
      (1) the production catalogue builder (`instruments-service/scripts/build_instrument_catalogue.py`,
      `_aggregate_key()`) was ALREADY SAFE — it keys DEX POOL rows on `pool::<chain>::<pool_address>`, never the raw
      symbolic `instrument_key`, so two same-symbol/different-address pools already get distinct catalogue lifecycles,
      never collapse; (2) the ONE consumer that WAS naive — the null-aware flat-vs-hive shape comparator that surfaced
      this bug (`defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md`'s 2026-07-26 entry) — was a session-local
      scratchpad script that "no longer exist[s]" per that doc's own words; nothing to patch there; (3) no other naive
      per-key `.loc[]`/`set_index`/dict-keyed consumer found via repo-wide search of instruments-service. Shipped a
      regression test (`test_rollup_defi_pool_same_symbol_different_address_stay_distinct_lifecycles`,
      `instruments-service/tests/unit/scripts/test_build_instrument_catalogue.py`) proving 2 pools sharing one
      `glued_pair_id` (real example: `PANCAKESWAP_V3-BSC:POOL:USDT-USDC-100`) survive as 2 distinct
      `instrument_id`/lifecycle rows — belt-and-suspenders proof the collision is already contained. Documented the
      known non-uniqueness of the raw shard's `instrument_key` column inline in the adapters (see Progress Log). **Done
      when** (met): audit complete, 0 live buggy consumers found + 1 fixed-by-confirming-already-safe + regression test
      proves the real machine key never collides. No cross-repo grammar change, no backfill, no MTDS coordination (per
      operator ruling — none needed). Shipped `instruments-service@30fe4511`.

## Progress Log

- 2026-07-26 (worker, slot 6): Filed while running the shape-B null-aware reconciliation; not investigated further (out
  of that todo's scope).
- 2026-07-30 (worker, slot 8): Investigated the open CODE fix todo; found it conflicts with the operator-ruled two-id
  pool model (2026-07-18) and breaks confirmed cross-repo consumers (unified-api-contracts `parse_glued_pool_id`, 2
  instruments-service scripts, the catalogue's byte-identical `glued_pair_id` invariant, MTDS's independent key
  reconstruction). Filed BLK-b3379171; operator ruled **Option B** — narrow consumer-side fix, no grammar change.
  Audited every raw-shard consumer: `build_instrument_catalogue.py::_aggregate_key()` was already safe
  (`pool::<chain>::<pool_address>` key for POOL rows, confirmed by code read); the one naive consumer (the shape
  comparator that surfaced the bug) is a vanished scratchpad script, nothing to patch. Shipped a regression test proving
  the catalogue never collapses same-symbol/different-address pools + inline adapter docstring notes on the known
  non-uniqueness of the raw shard's `instrument_key` column. Both CODE todos above closed (one WON'T-DO, one DONE with
  the actual resolving change). instruments-service@30fe4511.

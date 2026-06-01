---
title: "DeFi manifest + data-status canonicalisation (post 2026-06-01 coverage audit)"
created: 2026-06-01
author: ikenna
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-defi
status: active
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 3.6
locked_by: live-defi-rollout
locked_since: 2026-05-21
source:
  - plans/audit/results/defi_master_audit_2026_06_01.md (the audit that surfaced all of this)
  - plans/audit/instructions/defi_master_audit_instructions.md (items o–y)
---

# DeFi Manifest + Data-Status Canonicalisation

> **Why this exists**: the 2026-06-01 DeFi coverage audit took many passes because the data is **not in canonical form**
> — scattered buckets, hyphen/underscore + VENUE-CHAIN + blank-chain duplicates, a phantom grid, a v4–v8 schema spread,
> mislabeled empty reasons, and (the keystone) **no materialised `expected_unattempted` state**. The hard-to-find-ness
> IS the bug. This plan makes the **data, manifest, data-status tab/UI, owner code, and docs** canonical so the next
> audit is one pass. Single-walk discipline applies — the multi-bucket sweep MUST be one bundled walk, not N ad-hoc
> walks.

## Architecture principle (the governing contract)

**Annotate honestly ONCE at write/consolidation-time (manifest, via the `expected_coverage()` oracle); READ everywhere
else. Never re-derive the expected set in a consumer.**

- **Manifest = canonical honest 4-state ledger.** Every IS∩UAC-expected cell carries one of: `captured` /
  `empty_confirmed[typed reason]` / `attempted_failed` / **`expected_unattempted`** (IS-listed + post-genesis +
  post-launch + in source-coverage, but no data yet). The typed empty reason IS the IS/UAC annotation.
- **Data-status summary + drilldown = VIEWS**: group/aggregate/display by READING `capture_status`; never re-derive.
  Operator filter-chips narrow at request time (never expand). The drilldown `_aggregate_counts` is generic → one fix
  serves IS/MTDS/MDPS/features.
- **Strategy/features preflight = read the SAME 4-state.** No re-deriving genesis/launch/IS rules per consumer.
- Confirmed 2026-06-01: `expected_unattempted` is **never materialised** (0 source hits; oracle bucket has only the 3
  attempted states; `expected=True` on every present row → useless for "what's missing"). Three consumers re-derive the
  expected set three different ways and disagree. Root fix = materialise-once, read-everywhere.

## `expected_unattempted` materialisation — where it hooks into consolidation (B0 design)

SSOT: `unified_trading_library/unified_trading_library/manifest_consolidator.py`. Current `consolidate(bucket)` (L181):
(1) seed legacy → (2) list+read every `_index/per_vm/*.parquet` → (3) dedup-union merge (`_duckdb_consolidate_and_write`
L1022) → (4) write `_index/availability_index.parquet` (`_write_consolidated` L1159). It only merges what was
**written** — it never enumerates the expected set. **Insert a new step 3.5 between merge and write:**

```
3.5  materialise_expected_unattempted(merged_df, bucket):
       asset_group   = asset_group_for_bucket(bucket)            # cloud-providers.yaml / resolve
       expected_cells = expected_coverage_cells(asset_group)     # the oracle, NOT the manifest:
           for (venue, data_type) in EXPECTED_COVERAGE_BY_ASSET_GROUP[asset_group]:
             for chain in chains_for(venue):                      # ChainKind / venue chains
               for date in business_dates(start, today):
                 r = expected_coverage(asset_group, venue, data_type, date)   # registry/expected_coverage.py
                 if r.state == SHOULD_HAVE_DATA:                  # already excludes pre-genesis/pre-launch/pre-coverage
                   yield (venue, chain, data_type, date)
       present = set(merged_df[venue, chain, data_type, date])    # any capture_status
       owed    = expected_cells - present
       emit one row per `owed` cell: capture_status='expected_unattempted', expected=True,
              error_reason=None, row_count=0, available=False   # NO placeholder parquet object (index-layer only)
       return concat(merged_df, owed_rows)
```

Design decisions (encode):

- **Grain = `(asset_group, venue, chain, data_type, date)`** — NOT per-instrument (matches the a2 `expected_coverage`
  dump grain; avoids index explosion). Per-instrument owed-ness stays a drilldown leaf concern.
- **The oracle already gates** pre-genesis / pre-venue-launch / pre-source-coverage (`expected_coverage()` returns
  `SHOULD_HAVE_DATA` only when genuinely owed) — so `expected_unattempted` means exactly "we have the instrument, it's
  post-genesis/launch, we simply have no data." That is the operator's denominator:
  `% captured = captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)`.
- **Index-layer only** — no fake/placeholder parquet objects (workspace bans empty parquets to mask phantoms). The owed
  rows live only in the consolidated `_index/availability_index.parquet`.
- **Idempotent + cheap** — recomputed each consolidation from the oracle; `owed` shrinks as data lands. Cache the
  expected-cell set per (asset_group, today) to bound cost.
- **`expected_unattempted` is canonical** — add to the UAC `CaptureStatus` closed set (A6) so writers/consumers share
  it.

## Status legend: ✅ shipped · ⏳ ready/in-flight · ☐ todo · canonical todos below feed the orchestrator backlog

## A. Owner code (writers) — canonical writes

- [x] ✅ [CODE] P0. A1 pre-genesis empty-reason: oracle + evm-defi handlers classify via UAC `get_chain_genesis_date()`
      → `EXPECTED_PRE_GENESIS_CHAIN`. market-tick-data-service@840d85f1.
- [ ] [CODE] P1. A2 pre-venue-launch empty-reason: young perp/LST venues (PACIFICA/ASTER/ETHERFI pre-launch) →
      `EXPECTED_PRE_VENUE_LAUNCH` via UAC `get_protocol_launch_date()`/venue_launch_dates, same pattern as A1. Handlers:
      perp_funding + lst_rates + solana/evm defi.
- [ ] [CODE] P1. A3 data_type name SSOT at write: every handler writes the underscore canonical (`lending_indices` not
      `lending-indices`, `dex_pools` not `dex-pools`, `dex_swaps` not `dex-swaps`, `lst_rates` not `staking_yields`).
- [ ] [CODE] P2. A4 chain dimension always populated: QG guard fails a DeFi `record_captured`/`record_empty` with blank
      `chain` for a chain-scoped data_type.
- [ ] [CODE] P1. A5 LIGHTER perp_funding adapter fix: `SOURCE_RETURNED_ZERO` across full post-launch life (zkSync
      endpoint returns nothing) — verify endpoint/auth.
- [ ] [CODE] P0. A6 add `expected_unattempted` to the UAC `CaptureStatus` closed set + `EMPTY_CONFIRMED`-adjacent docs;
      the keystone canonical state. parent_epic: manifest_master.

## B. Manifest consolidation + data-status (owner code) — honest by default

- [ ] [CODE] P0. B0 materialise `expected_unattempted` in `manifest_consolidator.consolidate()` per the design above
      (new step 3.5; oracle-driven; index-layer only). Then B1/B2/B3 collapse to "read the 4-state". parent_epic:
      manifest_master.
- [ ] [CODE] P1. B1 `coverage-summary` (`data_status_service._build_coverage_for_cat`): drop the `len(index)`
      self-referential denominator; read the 4-state (or expected-dates oracle) + `is_expected()` gate; align with
      `manifest-status`.
- [ ] [CODE] P0. B2 drilldown (`data_status_hierarchical._aggregate_counts`): count the 4th bin `expected_unattempted`
      so genuinely-missing cells appear in the tree (the most useful "where's the missing data" view). Generic path →
      fixes IS/MTDS/MDPS/features at once.
- [ ] [CODE] P1. B3 drilldown denominator: `% = captured / (captured+empty+failed+expected_unattempted)`;
      pre-genesis/launch render out_of_scope (already excluded by the oracle once B0 lands).
- [ ] [CODE] P2. B4 `data_status_rollup_worker.py`: read the 4-state, not manifest row count.
- [ ] [UI] P1. B5 deployment-ui drilldown: render the 4-state (esp. `expected_unattempted`) + per-chain split; badge
      legend. (playwright gate applies)

## C. Data / manifest migration (single-walk, bundled) — fix existing rows

- [⏳] [DATA] P0. C1 oracle-prices index relabel + Pyth dedup — script ready
  `plans/audit/results/defi_oracle_relabel_migration_2026_06_01.py` (dry-run: 728 pre-genesis relabel + Pyth 1,185 chain
  `''`→`SOLANA` + drop 1,034 dup empties); snapshots before write.
- [ ] [DATA] P1. C2 data_type alias dedup across buckets: `lending-indices`→`lending_indices`, `dex-pools`→`dex_pools`,
      `dex-swaps`→`dex_swaps`, `staking_yields`→`lst_rates` (rename rows; data exists). ONE walk.
- [ ] [DATA] P1. C3 VENUE-CHAIN→flat: legacy `UNISWAPV3-ETHEREUM` venue strings → flat `venue` + populated `chain`. Same
      walk.
- [ ] [DATA] P1. C4 schema v4–v8 → v9 re-version across the dedicated DeFi buckets. Same walk. parent_epic:
      manifest_master.
- [ ] [DATA] P1. C5 phantom-grid delete: remove the cartesian `data_type × venue` empty grid in `market-data-tick-defi`;
      point data-status at the dedicated indexes.
- [ ] [DATA] P2. C6 Pyth ~5-week backfill (2026-04-15→present, Hermes API) on a VM after C1.
- [ ] [DATA] P2. C7 pre-launch reason relabel for young venues (PACIFICA/ASTER/ETHERFI/LIDO/MARINADE pre-launch) — same
      walk as C2–C4.
- [ ] [DATA] P1. C8 fill manifest under-enumeration: UAC declares 90 defi venue-keys but manifest enumerated only lst
      14/22, lending 6/21, perp 5/8; genuine absentees DRIFT-SOLANA (Solana MVP), FRAX, MORPHO, FLUID. parent_epic:
      defi_master.

## D. Features propagation (L3) — coverage must reach features-service

- [ ] [DATA] P0. D1 features-onchain-defi is near-empty (3 rows); features-delta-one-defi + features-volatility-defi
      have NO index → derived features (staking*apy_bps/funding_rate_apy_bps/basis_bps/realized_vol*\*) absent. Run the
      features backfill for the in-scope DeFi instruments over the captured window. parent_epic: features_and_ml_master.

## E. CeFi perp leg (hybrid hedge) — fix-fetch

- [ ] [DATA] P0. E1 CeFi `derivative_ticker` (funding carrier) fetch failures: OKX-FUTURES + ASTER 100%
      attempted_failed; refresh to current (stale ~3–5 weeks). parent_epic: cefi_master.

## F. Docs / SSOT — record canonical forms

- [ ] [DOCS] P1. F1 `codex/02-data/defi-data-types-catalog.md`: underscore-canonical data_type names + dedicated bucket
      per type + hyphen aliases deprecated.
- [ ] [DOCS] P1. F2 `codex/02-data/availability-manifest-and-data-status.md` + `data-status-drilldown.md`: document the
      materialised `expected_unattempted` 4-state + the manifest-annotates-once/consumers-read principle + per-chain
      requirement.
- [ ] [DOCS] P2. F3 `_defi_manifest.py` reason-labeling docstring (~L213-220 "future refinement" TODO) → mark
      pre-genesis done (A1); note pre-launch (A2).
- [ ] [DOCS] P2. F4 CLAUDE.md "Manifest + honest absence" note: `expected_unattempted` is materialised at consolidation
      from the oracle; consumers read, never re-derive.

## Verification (full-execution criterion)

Re-run `plans/audit/results/defi_strategy_coverage_query_2026_06_01.py` + the drilldown: every DeFi cell carries a
canonical data_type (underscore), flat venue + populated chain, v9 schema, a typed reason; `expected_unattempted`
materialised so `% captured = captured / (captured+empty+failed+expected_unattempted)`; coverage-summary == drilldown ==
manifest-status denominators; features-onchain-defi populated for the in-scope window; the next audit needs one pass.

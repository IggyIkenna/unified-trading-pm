---
doc_type: issue
title: EIGENLAYER carries instrument_type=spot_pair expected-cells not matching its registry declaration
summary: >-
  Live 2026-08-14 cross-check of asset_group=defi instrument_type=spot_pair against defi-canonical-naming-ssot.md's
  locked list found CHAINLINK/PYTH legitimate (deliberate oracle pair-feed declaration, codex now corrected) but
  EIGENLAYER's 3,816 spot_pair expected-cells (all 0 captured) have no matching registry declaration — likely a stale
  expected-universe seed, not yet root-caused.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [defi, instrument-type, canonicalisation, expected-universe, eigenlayer]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/defi_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: "2026-08-14"
author: slot-29
last_updated: "2026-08-14"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source: >-
  Found 2026-08-14 while working `/plans/archive/2026_08/defi_satellite_ao_dispatch_batch13_2026_08_13.md`'s
  "cross-check instrument_type=spot_pair" todo (source: defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md).
context_scope:
  [
    /codex/02-data/defi-canonical-naming-ssot.md,
    unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py,
    instruments-service/scripts/enumerate_expected_universe.py,
  ]
---

## What I found

While cross-checking `instrument_type=spot_pair` (asset_group=defi) against `defi-canonical-naming-ssot.md`'s locked
list (source todo: `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`), a live read of the 2026-08-12
honest-coverage rollup (`gs://central-element-323112-honest-coverage/2026-08-12/coverage.json`,
`by_venue_instrument_type.defi`) found exactly 3 venues carrying `instrument_type=spot_pair`:

- `CHAINLINK` — total=119,247 cells (0 captured, 4,536 empty_confirmed, 114,711 expected_unattempted)
- `PYTH` — total=18,441 cells (0 captured, 1,908 empty_confirmed, 16,533 expected_unattempted)
- `EIGENLAYER` — total=3,816 cells (0 captured, 1,040 empty_confirmed, 2,776 expected_unattempted)

CHAINLINK and PYTH are EXPLAINED and legitimate:
`unified_api_contracts.registry.capability_declarations._defi.PROTOCOL_CAPABILITIES["chainlink"/"pyth"]` deliberately
declares `instrument_types=[_IT.SPOT_PAIR.value, _IT.SPOT_ASSET.value]` for their `oracle_prices` capability (2026-07-20
catalogue canonicalization comment: "Feeds enumerate as SPOT_PAIR (ETH/USD) + SPOT_ASSET (single-asset) instrument
records"). `defi-canonical-naming-ssot.md` has been corrected in the same commit as this issue doc to document
`spot_pair` as a locked DeFi instrument_type for exactly this reason.

**EIGENLAYER is NOT explained.** Its registry declaration
(`unified_api_contracts/registry/capability_declarations/_defi.py`, `"eigenlayer"` / `"eigenlayer_rewards"` entries)
uses `instrument_types=_RESTAKING`, and `_RESTAKING = [_IT.SPOT_ASSET.value]` only — `spot_pair` is not declared
anywhere for EIGENLAYER. `expected_coverage.py`'s `EIGENLAYER: ["eigenlayer_rewards"]` entry likewise carries no
instrument_type override. There is no explained code path that should be seeding `instrument_type=spot_pair`
expected/empty-confirmed cells for EIGENLAYER.

**All 3,816 EIGENLAYER `spot_pair` cells are `captured=0`** — no real data rows exist, so this is not a live-writer
contamination bug (nothing is actively writing mistyped data); it looks like a stale expected-universe seed (an old
`enumerate_expected_universe` run predating whatever last changed EIGENLAYER's registry declaration to
`_RESTAKING`/`spot_asset`-only) that was never re-seeded/purged — the same "retired-rows-still-count" mechanism already
documented elsewhere in `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` for the POOL-uppercase/AAVEV3
cases, but not yet confirmed for this specific population.

## Why it matters

3,816 non-canonical-badged cells on the DeFi Distinct Values panel that don't correspond to any current registry
declaration — until root-caused, they either mask a real (if currently dormant) seeding bug, or need a one-time
expected-universe re-seed/purge for EIGENLAYER to reach genuine zero non-canonical on this axis.

## Recommended decision

- [ ] [DATA] P3. Root-cause why EIGENLAYER's expected-universe carries `instrument_type=spot_pair` cells (3,816 total, 0
      captured) when its registry declaration (`unified_api_contracts/registry/capability_declarations/_defi.py`
      `_RESTAKING` / `"eigenlayer"`/`"eigenlayer_rewards"` entries) only declares `spot_asset` — check
      `enumerate_expected_universe.py`'s EIGENLAYER handling and whether these are stale pre-registry-change cells
      (repo: instruments-service, cross-ref: unified-api-contracts).
- [ ] [DATA] P3. Once root-caused: either purge the stale `spot_pair` expected-cells for EIGENLAYER (if confirmed stale)
      or add an explicit registry justification comment (if confirmed intentional) — mirrors the CHAINLINK/PYTH
      documentation pattern in `defi-canonical-naming-ssot.md`.

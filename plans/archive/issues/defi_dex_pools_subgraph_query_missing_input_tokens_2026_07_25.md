---
doc_type: issue
title:
  dex_pools_handler messari_basic subgraph query never requests inputTokens symbols
  (curve/sushiswap/gmx/velodrome_v2/trader_joe_v2)
summary:
  Verified byte-for-byte in market-tick-data-service/market_tick_data_service/cli/handlers/dex_pools_handler.py and
  _dex_pools_subgraph.py -- the messari_basic query entry (_CURVE_QUERY / _CURVE_QUERY_FILTERED), used by 5 venues
  (curve, sushiswap, gmx, velodrome_v2, trader_joe_v2), requests only `pool { id, name }` from the subgraph -- it never
  asks for `inputTokens { symbol }`. The sibling messari_dex entry (pancakeswap_v3/aerodrome_v3) DOES request
  inputTokens and works correctly. This starves tier-2 symbol resolution entirely for these 5 venues; only pools ALSO
  registered in the instruments-service catalogue (tier-1 lookup) resolve. This is an ACTIVE ongoing gap in the live
  capture code, not just a historical migration artifact -- it will keep producing unattributed pool_state rows the
  moment DeFi live capture resumes (currently operator-paused since 2026-07-18 pending the per-instrument
  re-architecture).
status: resolved
nature: issue
asset_group: defi
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, subgraph, symbol-resolution, dex-pools, data-correctness, code-bug]
related: [defi_consolidated_closeout_2026_07_18, defi_migrated_marker_flagged_root_cause_clusters_2026_07_25]
created: 2026-07-25
last_updated: "2026-08-02"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
drift_direction: worsening-slowly
depends_on: []
source:
  [
    "found 2026-07-25 during a /autonomous session investigating why delete_migrated_defi_markers_2026_07_23.py's
    FLAGGED TRADER_JOE_V2/VELODROME_V2/CURVE dex_pool_state markers had real pool_id per row but unresolved symbols --
    root-caused by a dispatched research agent, then independently verified line-by-line against the actual query
    definitions before filing this",
  ]
resolved_by:
  "market-tick-data-service@63199601 (query/parser fix, verified ancestor of origin/live-defi-rollout, live-tested
  against all 4 real subgraphs); backfill + purge via defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md's 5 todos,
  all shipped/independently re-verified 2026-08-02"
locked_by:
locked_since:
context_scope:
  [
    /plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md,
    /plans/active/defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md,
    /plans/archive/issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_dex_pools_subgraph.py,
  ]
---

# dex_pools_handler messari_basic subgraph query never requests inputTokens symbols

> **🟢 RESOLVED 2026-08-02** — query/parser fix shipped `market-tick-data-service@63199601` (verified ancestor of
> `origin/live-defi-rollout`, live-tested against all 4 real subgraphs); backfill + purge landed via
> `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`'s 5 todos, all shipped/independently re-verified 2026-08-02.

> **NOTE (2026-07-25): GMX venue removed platform-wide** — see
> `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`. This doc's `gmx` mentions describe the shared
> `messari_basic` query bug as found (the query entry/table below is filed byte-for-byte against the code at the time).
> The gmx-specific slice of this bug is now moot going forward (its capture path is being deleted, not fixed); the
> finding for curve/sushiswap/velodrome_v2/trader_joe_v2 remains open and unaffected.

## The bug, verified

`market_tick_data_service/cli/handlers/dex_pools_handler.py`:

```
_CURVE_QUERY = """query(...) {
  liquidityPoolDailySnapshots(...) {
    pool { id, name }          <-- NO inputTokens
    timestamp
    totalValueLockedUSD
    ...
  }
}"""

_MESSARI_DEX_QUERY = """query(...) {
  liquidityPoolDailySnapshots(...) {
    pool {
      id
      name
      inputTokens { symbol }   <-- HAS inputTokens
      fees { feePercentage feeType }
    }
    ...
  }
}"""
```

`market_tick_data_service/cli/handlers/_dex_pools_subgraph.py` (~L238-284): `messari_basic` resolves to
`_CURVE_QUERY`/`_CURVE_QUERY_FILTERED` + `self._parse_curve`. The protocol-to-query-entry table maps `"curve"`,
`"sushiswap"`, `"gmx"`, `"velodrome_v2"`, `"trader_joe_v2"` all to `[messari_basic]` -- every one of these five venues
is missing symbol data at the subgraph-query level, structurally, regardless of when the capture runs.

## Why this wasn't obvious from the marker-cleanup dry-run alone

The 3-tier resolver in `_dex_pool_symbol.py::resolve_pool_symbol()` has a catalogue-lookup tier-1 fallback (reads
`prod/catalog.parquet`, instruments-service reference data, keyed by lowercased pool address) that resolves a pool's
symbol INDEPENDENTLY of the subgraph query, if that specific pool happens to already be registered in the catalogue.
This is why some VELODROME_V2 pools DO show up with clean human-readable names in current data (e.g.
`BTC.B-WETH-30.0.parquet`) despite going through the same broken query -- they're catalogue-covered, masking the query
bug for that venue. TRADER_JOE_V2 pools are less consistently catalogue-covered, so the gap is far more visible there.
CURVE/ETHEREUM's CURRENT (still-being-written, as of the last DeFi capture run before the 2026-07-18 pause) data is ALSO
address-keyed (`0x00836fe5....parquet`) -- direct evidence the bug is live, not historical.

## Scope / impact (canonical-coverage check, 2026-07-25)

| Venue/chain/data_type                                                                                                           | Current (pre-pause) coverage                                                 | Same bug present?                            |
| ------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------- |
| CURVE/ETHEREUM/dex_pool_state                                                                                                   | Yes, through 2026-07-18, address-keyed                                       | Yes -- visibly broken in current data        |
| VELODROME_V2/OPTIMISM/dex_pool_state                                                                                            | Yes, through 2026-07-24, well-attributed                                     | Bug present but masked by catalogue coverage |
| TRADER_JOE_V2/AVALANCHE/dex_pool_state                                                                                          | **None** -- venue currently empty per `/codex/02-data/defi-data-pipeline.md` | Bug present; no current data to even show it |
| SUSHISWAP (dex_pool_state)                                                                                                      | Stopped ~2026-06-20/25                                                       | Was address-keyed when active                |
| GMX (dex_pools_handler's own dex_pool_state capture, separate from the perp_funding aggregate covered in the sibling issue doc) | Not checked this pass                                                        | Same query entry, presumably same gap        |

## Recommendation (operator decision needed)

1. **Fix the query, not just the old markers**: add `inputTokens { symbol }` (and probably
   `fees { feePercentage feeType }` to match messari_dex's shape) to `_CURVE_QUERY`/`_CURVE_QUERY_FILTERED`, and switch
   curve/sushiswap/gmx/ velodrome_v2/trader_joe_v2 to `self._parse_messari_dex` (the parser that already knows how to
   read `inputTokens[].symbol` -- see `_parse_messari_dex` vs `_parse_curve` in `_dex_pools_parsers.py`). This is a
   real, scoped code change, not a config flip -- needs review of whether the Messari `liquidityPoolDailySnapshots`
   schema actually exposes `inputTokens` uniformly across all 5 subgraphs (unverified this session).
2. **This should land BEFORE DeFi live capture resumes** (currently paused since 2026-07-18) -- otherwise the exact same
   unattributed-pool gap starts accumulating again from day one of the resumed capture.
3. Existing historical unattributed rows (this issue's sibling doc,
   `defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md`) would still need a SEPARATE backfill pass (a
   standalone pool-id-keyed subgraph query, since `migrate_dex_pool_symbol_shape_2026_07_09.py` only reshapes
   already-captured token_a/token_b, it does not re-query the subgraph) -- and per-subgraph, whether 2022-era pool
   metadata is even still indexed needs live-testing (Messari subgraphs are typically full-history, so plausibly yes,
   but `EXPECTED_SUBGRAPH_DEINDEXED` is a real, shipped precedent for the opposite for at least one other CURVE/OPTIMISM
   shard).
4. Not fixing this at all is also a valid operator choice if these 5 venues are considered low-priority / deprioritized
   post-re-architecture -- flagging so that's a deliberate choice, not a silent gap.

## Related

- `defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md` -- the marker-cleanup dry-run issue this was
  discovered investigating.
- `plans/active/defi_consolidated_closeout_2026_07_18.md` -- parent plan.

## Todos

- [x] ✅ [DECISION] P1. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — see
      `plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`.** Decide + fix the `messari_basic` subgraph
      query missing `inputTokens { symbol }` -- curve/sushiswap/gmx/velodrome_v2/trader_joe_v2 all starve tier-2 symbol
      resolution; needs an operator call on whether to fix the query (add `inputTokens`, switch to `_parse_messari_dex`)
      before DeFi live capture resumes, or deprioritize.
- [x] ✅ [OPERATOR] P1. **DONE 2026-08-02 (finalize task
      `defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md` todo 1, slot-13 review craft).** Confirmed
      `plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`'s all 5 todos (not just todo 5) landed —
      independently verified via `git log`/`git merge-base --is-ancestor` that the query-fix commit
      (`market-tick-data-service@63199601`) and its supporting live-test commit (`market-tick-data-service@0f40a69f`)
      are real, shipped, and ancestors of `origin/live-defi-rollout`; the backfill (VM completion + manifest
      spot-checks) and both purge categories (lst_rates markers + old dex_pool_state leaves) are independently
      re-verified in that plan's own Progress Log (zero SAFE markers remain, only the irreducible FLAGGED floor).
      Flipped `status: open` → `status: resolved` with the `resolved_by` citation above in this same commit.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - sole open todo is explicitly [OPERATOR]-tagged and gated on
  defi_dex_pool_symbol_fix_backfill_purge_finalize running first
- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-02** (tranche=defi, autonomous, scheduled): KEEP-NA valid (2026-07-30 verdict re-
  affirmed) — re-read end to end; content unchanged since that verdict (context-scout backfill only). The sole open item
  is explicitly `[OPERATOR] P1` AND gated: it asks to confirm `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`'s
  todo 5 landed and then let that plan's gated finalize twin flip this doc's `status` with a verified `resolved_by` — an
  explicit "do not archive before that finalize plan runs" instruction. KEEP-NA on that citation alone.
- **2026-08-02 (slot-13, review craft, dispatched on `defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md`
  todo 1)**: gate satisfied — the parent plan's all 5 todos confirmed `[x]` with real, verified evidence. Flipped this
  doc's status to `resolved` per the todo above. See the sibling finalize plan +
  `defi_consolidated_closeout_2026_07_18.md` for the other 2 legs of this same reconciliation.

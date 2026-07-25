---
doc_type: plan
title: Fix dex-pools subgraph symbol-resolution bug, backfill, purge superseded/orphaned DeFi historical data
summary:
  Operator decision 2026-07-25 -- delete the bad unattributed TRADER_JOE_V2/VELODROME_V2/CURVE dex_pool_state data, fix
  the subgraph-query bug that caused it (see issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md),
  then re-backfill with proper symbols. Also purge the orphaned lst_rates `_migrated_*` markers
  (COINBASE/MAKER/SWELL/ETHENA) -- superseded by the current canonical RPC-based lst_rates_handler.py capture
  (re-derivable from any historical block on demand) or, for MAKER/ETHENA, already reclassified into
  vault_share_price_handler.py.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [defi, subgraph, symbol-resolution, dex-pools, lst-rates, backfill, cleanup]
related:
  [
    defi_consolidated_closeout_2026_07_18,
    defi_migrated_marker_flagged_root_cause_clusters_2026_07_25,
    defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25,
  ]
created: 2026-07-25
last_updated: 2026-07-25
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
drift_direction: advance-code
sequential: true
depends_on: []
source:
  [
    "operator decision 2026-07-25, made during a /autonomous session's FLAGGED-marker root-cause investigation -- 'seems
    best thing is to delete the bad data, purge manifest then and fix the query and re-backfill' for the
    TRADER_JOE_V2/VELODROME_V2/CURVE cluster, and 'orphaned ones are artifacts again to purge from manifest and gcs
    data' for the lst_rates cluster",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Fix dex-pools subgraph symbol bug, backfill, purge orphaned data

## Context (read before dispatching any todo)

Two independent findings from the 2026-07-25 FLAGGED-marker investigation, both operator-decided the same way (purge the
bad/orphaned data, keep only what's canonical going forward):

1. **dex_pools_handler.py's `messari_basic` query** (used by curve/sushiswap/velodrome_v2/trader_joe_v2 -- gmx is
   excluded here, it is being removed entirely by `defi_gmx_venue_removal_2026_07_25.md`) never requests
   `inputTokens { symbol }` from the subgraph -- full analysis in
   `issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md`. This produced years of unattributed
   (address-keyed) `dex_pool_state` data for these venues, both the old `_migrated_*` markers AND (for CURVE
   specifically, confirmed live) still-current address-keyed leaves.
2. **lst_rates** `_migrated_*` markers for COINBASE/SWELL/MAKER/ETHENA are all legitimate-but-orphaned single-row
   snapshots -- the CURRENT canonical `lst_rates_handler.py` captures via direct on-chain RPC `eth_call` at a
   _historical block number_, meaning any past date's rate is exactly re-derivable on demand from the (permanent)
   blockchain state -- these old markers have no unique irreplaceable content worth preserving. MAKER/ETHENA
   (sDAI/sUSDe) are additionally obsolete: reclassified out of `lst_rates` into `vault_share_price_handler.py` by a
   2026-07-23 fix already shipped.

**This plan is `sequential: true`** -- todos 2-5 form a genuine dependency chain (fix the query before backfilling,
backfill before purging the now-superseded old data); todo 1 (lst_rates purge) is independent but placed first since it
is quick and doesn't block anything.

## Todos

- [ ] [OPERATOR] P2. **Purge orphaned lst_rates `_migrated_*` markers** for COINBASE/SWELL/MAKER/ETHENA (all
      `raw_tick_data/**/venue={coinbase,swell,maker,ethena}/**/data_type=lst_rates/_migrated_*.parquet` objects) + their
      manifest rows, in `market-data-tick-defi-prd-central-element-323112`. Prod-bucket delete, human-gated per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` -- no agent runs this. Done-when: zero `_migrated_*`
      lst_rates markers remain for these 4 venues in GCS or the manifest. (repo: market-tick-data-service)
- [ ] [BACKEND] P1. **Fix the `messari_basic` subgraph query** in
      `market_tick_data_service/cli/handlers/dex_pools_handler.py` -- add `inputTokens { symbol }` (and
      `fees {     feePercentage feeType }` to match `_MESSARI_DEX_QUERY`'s shape) to
      `_CURVE_QUERY`/`_CURVE_QUERY_FILTERED`, and switch `curve`/`sushiswap`/`velodrome_v2`/`trader_joe_v2` (NOT `gmx`
      -- see context above) in `_dex_pools_subgraph.py`'s protocol table from `self._parse_curve` to
      `self._parse_messari_dex`. Verify the Messari `liquidityPoolDailySnapshots` schema actually exposes `inputTokens`
      uniformly across all 4 subgraphs before assuming this is a drop-in change. Done-when: a live test query against
      each of the 4 subgraphs returns a populated `inputTokens` array for at least one known pool. (repo:
      market-tick-data-service)
- [ ] [DATA] P1. **Live-test whether 2022-era pool metadata is still indexed**, per subgraph, for
      curve/sushiswap/velodrome_v2/trader_joe_v2 -- before committing to a full historical backfill. Precedent both
      ways: Messari subgraphs are typically full-history (plausibly recoverable), but
      `EmptyConfirmedReason.EXPECTED_SUBGRAPH_DEINDEXED` is a real, shipped precedent for a subgraph going permanently
      unrecoverable (CURVE/OPTIMISM `dex_pool_swaps`, a different shard, see
      `instruments-service/scripts/reclassify_defi_curve_optimism_subgraph_deindexed_2026_07_24.py`). Done-when: a
      documented per-subgraph verdict (recoverable / partially-recoverable / deindexed) in this plan's Progress Log.
      (repo: market-tick-data-service)
- [ ] [BACKEND] P1. **Re-backfill `dex_pool_state` for curve/sushiswap/velodrome_v2/trader_joe_v2** across the full
      historical range using the fixed query (todo above), on an in-region VM per the heavy-I/O rule, scoped only to the
      ranges confirmed recoverable in the prior todo. Done-when: the manifest shows a populated `symbol`/ `pool_address`
      for the previously-unattributed cells within the confirmed-recoverable range. (repo: market-tick-data-service)
- [ ] [OPERATOR] P1. **Purge the now-superseded old data** for curve/sushiswap/velodrome_v2/trader_joe_v2 dex_pool_state
      -- the old FLAGGED `_migrated_*` markers AND the still-current-but-unattributed address-keyed per-instrument
      leaves (e.g. `0x00836fe5....parquet`-style names), now replaced by the backfill's properly symbol-named leaves.
      Prod-bucket delete, human-gated per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` -- do this only
      after the backfill todo above has landed and been spot-checked. Done-when: zero unattributed (address-keyed)
      `dex_pool_state` leaves remain for these venues within the confirmed-recoverable range, and re-running
      `delete_migrated_defi_markers_2026_07_23.py`'s dry-run shows these venues' FLAGGED count at (near) zero. (repo:
      market-tick-data-service)

## Codex SSOTs

- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` -- governs both purge todos.
- `/codex/05-infrastructure/vm-launcher-runbook.md` -- heavy-I/O rule, governs the backfill todo (in-region VM,
  `canonical-migration-defi-*`-family launcher or a new category on `launch-canonical-migration-vm.sh`, per the same
  registry-first convention used for `defi-marker-cleanup` this session).

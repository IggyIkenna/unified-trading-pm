---
title: "MTDS DeFi data_type alias drift — venue_data_types.yaml + graph adapters still on banned legacy names"
created: 2026-05-24
author: ikenna (slot 1)
source:
  - "Tier B full-workspace SIT validation (full_cicd_sit_target_state_2026_05_24.md)"
  - "UAC tests/test_data_type_canonicalization.py[market-tick-data-service] FAIL in full workspace"
locked_by: live-defi-rollout
---

## What I found

Running the full-workspace cross-repo invariants (Tier B premise) surfaced live drift that **per-repo CI cannot see**.
UAC `tests/test_data_type_canonicalization.py` is parametrized over sibling `venue_data_types.yaml` files; when the MTDS
sibling is absent (per-repo CI) it scans `[]` and passes, so this never failed remote CI. With the full workspace
assembled it FAILS on both parametrized cases for `market-tick-data-service`:

1. **`test_no_banned_aliases_in_yaml[market-tick-data-service]`** —
   `market-tick-data-service/configs/venue_data_types.yaml` uses banned legacy DeFi data_type aliases:
   - `swaps` → must be `dex_swaps`
   - `liquidity` → must be `dex_pools`
   - `rate_indices` → must be `lending_indices` Affected venues: `UNISWAP_V2-ETHEREUM`, `UNISWAP_V3-ETHEREUM`,
     `UNISWAP_V4-ETHEREUM`, `CURVE-ETHEREUM` (swaps + liquidity); `AAVE_V3_ETH`, `MORPHO-ETHEREUM`, `FLUID-ETHEREUM`
     (rate_indices).
2. **`test_yaml_data_types_in_uac[market-tick-data-service]`** — the same legacy values are not in UAC
   `DATA_TYPES_BY_ASSET_GROUP` (which registers the canonical `dex_swaps`/`dex_pools`/`lending_indices`).

**This is NOT a pure config straggler** — diagnosis shows the legacy names are also wired into the lower graph-adapter
layer:

- `market_tick_data_service/market_interface/adapters/defi/uniswap_v3_adapter.py:90` —
  `SUPPORTED_DATA_TYPES = {"trades", "swaps", "liquidity"}`; `:548` returns `["swaps", "liquidity"]`.
- `_defi_graph_models.py` carries `swaps` / `liquidity` (these are GraphQL **response field names**, a separate concern
  — likely legitimate, not data_type identifiers).

Meanwhile the **storage / handler / CLI layer already uses the canonical names**: `dex_swaps_handler.py`,
`schema_validation.py`, `data_manifest_handler.py`, `curve_defi_ws.py`, `cli/main.py`, `orchestrator.py` all reference
`dex_swaps` / `dex_pools` / `lending_indices`. **No `swaps`→`dex_swaps` translation map exists** in MTDS (grepped).

So MTDS is **half-migrated**: canonical names in the storage/handler layer, legacy names in the venue config + the
graph-adapter `SUPPORTED_DATA_TYPES`. `venue_data_types.yaml` is consumed by `engine/orchestrator.py`.

## Why it matters

- DeFi `dex_swaps` / `dex_pools` / `lending_indices` are MVP-archetype data for `arbitrage_price_dispersion` +
  `carry_staked_basis` — squarely on the live-DeFi critical path.
- If `venue_data_types.yaml`'s data_type values flow into GCS path generation / manifest keys, the legacy/canonical
  split risks writing or reading some DeFi venues under the wrong `data_type=` partition → silent coverage gaps (exactly
  the divergence the manifest honest-absence work targets).
- Per **Data Pipeline Correctness Is The Heartbeat** (CLAUDE.md), this is fixed in full, not deferred — but the fix
  needs a real diagnosis pass first (see below), and the rename touches storage-path semantics so it is **not** a blind
  find-replace.

## Open questions to resolve before fixing (diagnose-before-fix)

1. **Does `venue_data_types.yaml`'s data_type value drive storage?** Read `engine/orchestrator.py`'s consumption of the
   YAML: does the `swaps`/`liquidity` string become a `data_type=` GCS partition, or is it remapped to `dex_swaps` by
   the handler before any write? If remapped, the YAML+adapter names are internal and the fix is config/code hygiene (no
   data migration). If not remapped, data may already be split across legacy + canonical partitions.
2. **What is the actual GCS data-state?** Walk a sample of the DeFi DEX/lending buckets for `data_type=swaps` vs
   `data_type=dex_swaps` (and `liquidity` vs `dex_pools`, `rate_indices` vs `lending_indices`). Code-constant ≠
   data-state (cf. the v8 schema-version incident). If legacy partitions hold real rows, a migration (rename/repartition
   under the single-walk discipline window) is required, not just a config edit.

## Recommended decision

- If (1) shows the handler remaps to canonical before write AND (2) shows no legacy partitions with rows: fix is a
  same-PR rename of `venue_data_types.yaml` + `uniswap_v3_adapter.SUPPORTED_DATA_TYPES`/return-list to canonical names
  (keep `_defi_graph_models` GraphQL field names as-is) + a regression note. Owner: MTDS slot.
- If legacy GCS partitions hold rows: this becomes a data migration — fold into the next scheduled GCS walk per the
  single-walk discipline; do NOT add an ad-hoc whole-corpus walk.
- **Foreign-WIP caution**: `market_tick_data_service/engine/orchestrator.py` is currently dirty (another agent's
  in-flight work, unrelated to data_types per its diff). Coordinate before editing MTDS files.

## Status

- [x] Surfaced by Tier B full-workspace SIT (UAC test) 2026-05-24; logged in `full_cicd_sit_target_state_2026_05_24.md`
- [ ] Q1: trace `venue_data_types.yaml` → storage path in `orchestrator.py`
- [ ] Q2: GCS data-state audit (legacy vs canonical `data_type=` partitions for the 7 affected venues)
- [ ] Fix per the decision branch (config+adapter rename OR scheduled migration)
- [ ] Re-run `test_data_type_canonicalization.py[market-tick-data-service]` green in full workspace

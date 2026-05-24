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

## Diagnosis results — Q1 + Q2 (completed 2026-05-24)

**Q1 — does `venue_data_types.yaml`'s data_type drive storage? NO.**

- The `venue_data_types.yaml` **file is read by no Python in the workspace** (grepped the filename across all repos —
  zero hits). The local var `venue_data_types` in `orchestrator.py` is unrelated. The file is declarative/documentation
  config, additionally enforced by the UAC SIT test as a contract artifact.
- Runtime "expected data types for a venue" comes from UAC's `get_expected_data_types_for_venue` (imported from
  `unified_api_contracts.registry`), **not** the MTDS YAML. orchestrator additionally filters to UAC-valid
  (`[dt for dt in venue_data_types if dt in _uac_valid]`), so legacy aliases would be dropped even if they reached it.
- DeFi **storage** writes via handler constants: `dex_swaps_handler.py` `_DEX_SWAPS_DATA_TYPE = "dex_swaps"`.
- **Caveat — the adapter vocabulary IS real and coupled**:
  `uniswap_v3_adapter.SUPPORTED_DATA_TYPES = {"trades", "swaps", "liquidity"}` and tests call the adapter with
  `data_types=["swaps"]` (`test_defi_live_tradfi_adapters.py:735`, `test_canonical_parquet_reader.py:630`). So the
  adapter's `swaps`/ `liquidity` is its own contract — NOT a safe blind rename; it is part of the migration below.

**Q2 — GCS data-state (audited central-element-323112, 2026-05-24).** Code-constant ≠ data-state — the data is on a
THIRD naming layer:

| bucket            | canonical (UAC)   | GCS actual `data_type=` | hive key                 | latest day |
| ----------------- | ----------------- | ----------------------- | ------------------------ | ---------- |
| `dex-swaps[-prd]` | `dex_swaps`       | **`dex_pool_swaps`**    | `category=defi` (legacy) | 2026-04-14 |
| `dex-pools[-prd]` | `dex_pools`       | **`dex_pool_state`**    | `category=defi` (legacy) | 2026-04-\* |
| `lending-indices` | `lending_indices` | `lending_indices` ✅    | `category=defi` (legacy) | 2026-05-\* |

So: (a) DEX data_type partitions are `dex_pool_swaps` / `dex_pool_state` — in **neither UAC nor current MTDS code**
(old-writer names); (b) all DeFi data is still under the legacy `category=` hive key, not `asset_group=` (the 2026-04-25
vocabulary migration never reached this DeFi data); (c) DEX buckets look stale (~2026-04-14) — possible coverage gap. A
`migrate_defi_canonical` script + `dex_pool_state` references already exist in MTDS
(`tests/unit/scripts/test_migrate_defi_canonical.py`), so a canonicalization effort is partially scripted.

## What got fixed vs what remains

- **FIXED (declarative config)**: `venue_data_types.yaml` legacy aliases → canonical. A **parallel agent already landed
  this on `live-defi-rollout`** (also added `perp_funding` to Hyperliquid/Aster); my independent same-rename was
  redundant and dropped. Tier B SIT invariant `test_data_type_canonicalization[market-tick-data-service]` now 6/6 green
  (verified locally).
- **REMAINS — coupled data migration (NOT ad-hoc fixable; single-walk HARD RULE)**:
  1. Adapter vocabulary: `uniswap_v3_adapter.SUPPORTED_DATA_TYPES` + the `data_types=["swaps"]` call/test sites →
     canonical, with the downstream write map + tests as one change.
  2. GCS repartition: `dex_pool_swaps`→`dex_swaps`, `dex_pool_state`→`dex_pools`, and `category=defi`→`asset_group=defi`
     — **fold into the next scheduled GCS walk** (single-walk discipline forbids an ad-hoc whole-corpus walk). Reconcile
     with the existing `migrate_defi_canonical` script.
  3. Coverage: confirm whether DEX collection is stale since ~2026-04-14 or moved buckets.

## Recommended decision (operator)

Route the REMAINS items into **`plans/epics/mtds_mdps_master.md`** (the data-pipeline migration coordinator) as a
DeFi-data_type-canonicalization phase, sequenced into the next scheduled GCS walk — do NOT spawn an ad-hoc walk. The
config drift (the CI/CD-visible symptom) is closed; the data migration is the real, larger work.

**Foreign-WIP caution**: `market_tick_data_service/engine/orchestrator.py` is currently dirty (another agent's in-flight
work, unrelated to data_types per its diff). Coordinate before editing MTDS files.

## Status

- [x] Surfaced by Tier B full-workspace SIT (UAC test) 2026-05-24; logged in `full_cicd_sit_target_state_2026_05_24.md`
- [x] Q1: `venue_data_types.yaml` is declarative-only (not read at runtime); adapter `swaps`/`liquidity` IS coupled
- [x] Q2: GCS data-state audited — DEX on `dex_pool_swaps`/`dex_pool_state` + legacy `category=` key; lending canonical
- [x] Config drift fixed (parallel agent landed the canonical YAML rename; SIT invariant green)
- [ ] **MIGRATION (operator-routed to mtds_mdps_master)**: adapter vocabulary + GCS repartition + category→asset_group,
      folded into the next scheduled GCS walk; reconcile with existing `migrate_defi_canonical`
- [ ] Coverage check: is DEX collection stale since ~2026-04-14?

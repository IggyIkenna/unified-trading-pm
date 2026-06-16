---
scope: [engineer]
status: stable
last_reviewed: 2026-05-07
---

# Data-status drill-down hierarchy = codex shard atom

The deployment-ui Data Status panel drills down through a tree shaped per the codex per-asset_group shard-axis matrix
declared in
[`unified_api_contracts.registry.data_status_axis_matrix.SHARD_AXIS_MATRIX`](../../unified-api-contracts/unified_api_contracts/registry/data_status_axis_matrix.py).

Per-asset_group depth (matches CLAUDE.md "Per-asset-group shard-key matrix"):

| Service / asset_group               | Drill-down (top → leaf)                                                                                                                                       |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `instruments-service`               | `venue → date` (cefi/tradfi); `venue → chain → date` (defi)                                                                                                   |
| MTDS CeFi spot/perp                 | `venue → data_type → instrument_type → instrument_id → date`                                                                                                  |
| MTDS CeFi options/futures           | `venue → data_type → instrument_type → root → date` (bundled)                                                                                                 |
| MTDS TradFi futures                 | `venue → data_type → instrument_type → root → date` (bundled)                                                                                                 |
| MTDS TradFi options                 | `venue → data_type → instrument_type → root → date` (11-cluster ES.OPT)                                                                                       |
| MTDS DeFi                           | `venue → chain → instrument_id → data_type → date`                                                                                                            |
| MTDS sports                         | `data_type → league_id → date`                                                                                                                                |
| MTDS prediction                     | `venue → canonical_question_group → data_type → date`                                                                                                         |
| `features-service` (consolidated)   | `feature_family → <per-family axes below>` (the 8 family rows below collapse to sub-package paths inside ONE service; `feature_family` is the outermost axis) |
| ↳ `feature_family=delta_one`        | `feature_family → venue [→ chain] → feature_group → timeframe → instrument_id → date`                                                                         |
| ↳ `feature_family=onchain`          | `feature_family → venue → chain → feature_group → protocol_id → timeframe → date` (DeFi only)                                                                 |
| ↳ `feature_family=sports`           | `feature_family → feature_group → league_id → date`                                                                                                           |
| ↳ `feature_family=calendar`         | `feature_family → feature_group → timeframe → date` (asset-group=shared)                                                                                      |
| ↳ `feature_family=cross_instrument` | `feature_family → venue [→ chain] → feature_group → timeframe → date`                                                                                         |
| ↳ `feature_family=volatility`       | `feature_family → venue → feature_group → timeframe → instrument_id → date`                                                                                   |
| ↳ `feature_family=commodity`        | `feature_family → venue → feature_group → root → timeframe → date` (futures-bundled)                                                                          |
| ↳ `feature_family=multi_timeframe`  | `feature_family → venue [→ chain] → feature_group → timeframe → instrument_id → date`                                                                         |

> **`feature_family` is the outermost axis for features-service drilldowns** (added 2026-05-08 per
> [`features_repo_consolidation_2026_05_08`](../../plans/active/features_repo_consolidation_2026_05_08.md) Phase 1A).
> The 8 previously-separate `features-*-service` repos are sub-packages of the consolidated
> [`features-service`](../../../features-service/); the data-status drilldown surfaces `feature_family` (the UAC
> `FeatureFamily` StrEnum: `onchain` / `volatility` / `cross_instrument` / `sports` / `calendar` / `commodity` /
> `delta_one` / `multi_timeframe`) as the top-level shard axis so operators see the consolidated repo's coverage
> per-family without mixing families. Architecture SSOT:
> [`../04-architecture/features-service-architecture.md`](../04-architecture/features-service-architecture.md).

> **`pipeline_mode` is the outermost partition column** above every tree shown above (added 2026-05-08 per
> [`gcs_migration_bundle_pipeline_mode_2026_05_08`](../../plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md)).
> Every drilldown tree implicitly stratifies by `pipeline_mode={batch_*, live_websocket, ...}` first, then by the
> per-asset_group axes listed in the table above. Operators querying the data-status drilldown UI without an explicit
> `pipeline_mode` filter see the **batch-vs-live merged** view (live wins for dates where live exists, batch otherwise,
> per the SOURCE_PRIORITY fan-in semantics in [`pipeline-mode-partition.md`](./pipeline-mode-partition.md)). Querying
> with explicit `pipeline_mode={value}` returns only that stratum — required for the `live_pipeline` Phase 12
> batch-vs-live reconciliation gate. SSOT for the `PipelineMode` closed-set values:
> `unified_api_contracts.canonical.crosscutting.pipeline_mode.PipelineMode`.

## Backend

Endpoint: `GET /api/data-status/drilldown/{service}/{asset_group}`.

- Query params: `start_date` / `end_date` (required); per-axis filters `chain` / `venue` / `data_type` /
  `instrument_type` / `instrument_id` / `league_id` / `feature_group` / `timeframe` / `canonical_question_group`;
  `expand_to_depth` (default 2).
- Response: `{ service, asset_group, axes, tree, totals, filtered_by, manifest_uri }`. Each tree node has `axis`,
  `value`, `captured`, `empty_confirmed`, `attempted_failed`, `total`, `completion_pct`, `row_key` (the structured shard
  atom for the leaf, consumed by the per-leaf SmartDownloadButton + the Deploy-Missing surgical CLI), `children`,
  `is_leaf`.
- Implementation:
  [`deployment_api/services/data_status_hierarchical.py`](../../deployment-api/deployment_api/services/data_status_hierarchical.py).
- Pairs the SSOT covers: enumerate via `GET /api/data-status/drilldown-pairs`.

Aggregate counts at every non-leaf node reflect the FULL subtree below it (so the operator sees the rolled-up
`captured / total` ratio at any depth without expanding). Lazy-load: deeper levels only materialise on expand.

## Frontend

Component: [`HierarchicalShardDrilldown.tsx`](../../deployment-ui/src/components/HierarchicalShardDrilldown.tsx).

- Top-level fetch on mount with `expand_to_depth=1`.
- Each non-leaf row lazy-loads its children on first expand by re-calling the endpoint with the parent's `row_key` as
  filter query params.
- Each row renders `axis=value | captured/total | completion_pct | empty badge | failed badge`. Leaf rows are
  un-clickable.
- `AbortController` on every fetch cleanly cancels in-flight requests on unmount or filter-change.

Phase 2 ships the component drop-in-ready; [`DataStatusTab.tsx`](../../deployment-ui/src/components/DataStatusTab.tsx)
wire-in (insertion below the existing `BreakdownsAccordion`) is the follow-up.

## Per-leaf download + surgical recovery

Every leaf carries a `row_key` dict. Two operator actions consume it:

1. **Per-leaf SmartDownloadButton** — passes the full `row_key` to `/data-status/download-shard-csv` so bundled shards
   (options_chain ES.OPT) download the per-root bundle parquet and per-instrument shards (CeFi spot BTCUSDT 2024-03-04)
   download the per-instrument parquet. Capture-status branching (200 + CSV / empty_confirmed header / attempted_failed
   header / 404 / 502) is per the existing `_capture_status_response` contract.
2. **Deploy-Missing button** — emits a structured `--shard-key=...` pipe-delimited form
   (`asset_group|venue|data_type|instrument_type|instrument_id_or_root|day`) that the MTDS CLI decomposes into
   individual filter flags. The resulting backfill VM scopes to ONE leaf shard rather than re-running the whole
   asset_group. SSOT for the format:
   [`market_tick_data_service/cli/shard_key.py`](../../market-tick-data-service/market_tick_data_service/cli/shard_key.py).

## Failure modes that the drill-down catches

- Misleading roll-up headlines — the pre-2026-05-07 chain rollup reported `ARBITRUM 32/54 shards` (date-count math
  collapsed across 3 protocols × 5 data_types × ~1700 days ≈ 25k true shards). The new hierarchical drill-down
  materialises the true leaf shard count at every level.
- Partial bundles — the codex shard atom for options_chain bundles all 11 ES.OPT clusters under one parquet; if the
  writer captured 1 of 11 the leaf shows `empty_confirmed=10 attempted_failed=0 captured=1` rather than the
  pre-2026-05-07 `captured=1` that masked the gap.
- Per-protocol launch dates — `_mtds_expected_dates_cached` clips pre-`max(chain_genesis, protocol_launch)` days so
  AAVE_V3-ARBITRUM drilldown 2021-08-31 → 2022-03-15 returns empty subtrees rather than inflating the denominator with
  always-empty days.

## References

- Plan: `plans/active/data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md`.
- Sibling SSOTs: `availability-manifest-and-data-status.md` (manifest schema), `per-category-bucket-layouts.md`
  (canonical parquet paths), `honest-absence-downstream-handling.md` (NaN-handling tolerances).
- Reference incident 2026-05-07: operator DEFI screenshot showing ARBITRUM 32/54 misleading headline; root cause the
  date-count rollup math + missing protocol launch SSOT.

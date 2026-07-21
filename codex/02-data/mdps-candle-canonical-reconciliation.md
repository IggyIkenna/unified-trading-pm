---
doc_type: codex-ssot
title: MDPS candle-layer canonical reconciliation (the four surfaces + shard atom for processed candles)
summary: >-
  The candle-LAYER extension of the four-surface reconciliation. Defines the MDPS processed-candle shard atom (adds a
  timeframe axis; data_type keyed on the AGGREGATED mdps_data_type_key; S3 rows filtered
  service_name=market-data-processing-service), the four surfaces for candles (S4 UNAVAILABLE by construction — there is
  no candle catalogue), and the fact that the UAC machine oracle does NOT cover the processed_candles/ namespace so
  candle canonicality is checked against the ratified Option-A registry template until the oracle is extended.
  REFERENCES the four-surface procedure, the finding taxonomy (AE-6 migration window), the census/compute-tier doc, the
  candle-delivery flow, the bar-edge convention, the per-AG bucket layouts, and the in-flight Option-A migration issue —
  it does not duplicate them.
status: current
nature: ssot
asset_group: [meta]
stage: [data]
repos:
  [unified-trading-pm, market-data-processing-service, unified-trading-library, unified-api-contracts, deployment-api]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, candles, mdps, processed-candles, timeframe, shard-atom, machine-oracle]
related:
  [
    four-surface-reconciliation-procedure.md,
    reconciliation-finding-taxonomy.md,
    reconciliation-census-and-compute-tiers.md,
    cross-asset-canonical-target-ssot.md,
    canonical-cutover-register.md,
    per-asset-group-bucket-layouts.md,
    chart-candle-delivery-flow.md,
    bar-boundary-candle-edge-convention.md,
    ../../plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    ../../plans/active/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md,
  ]
created: 2026-07-21
authoritative_for:
  [
    the MDPS candle-layer shard atom,
    the four surfaces for processed candles,
    the candle-layer canonical authority (Option-A template; oracle-exempt namespace),
    the candle-layer migration-window suppression (AE-6),
  ]
referenced_by: []
owner:
last_reviewed: 2026-07-21
code_refs:
  [
    unified-trading-library/unified_trading_library/config_interface/paths/registry.py,
    unified-api-contracts/unified_api_contracts/canonical/partition_paths.py,
    market-data-processing-service/market_data_processing_service/app/core/output_path_helpers.py,
    deployment-api/deployment_api/routes/data_status/_axis_census.py,
  ]
---

# MDPS candle-layer canonical reconciliation

> **What this doc is.** [`four-surface-reconciliation-procedure.md`](four-surface-reconciliation-procedure.md) defines
> the per-shard comparison for the RAW-TICK layer, and
> [`cross-asset-canonical-target-ssot.md`](cross-asset-canonical-target-ssot.md) is raw-tick-only. This doc is the LAYER
> extension for MDPS processed candles: the candle shard atom (which differs), the four surfaces for candles (S4 differs
> — it is absent), and the canonical AUTHORITY for candle paths (which differs — the UAC oracle does not cover the
> `processed_candles/` namespace). It REFERENCES the procedure, the finding taxonomy, the census/compute-tier doc, and
> the candle-delivery flow; it does not restate them.
>
> **🟡 In-flight migration.** The operator ruled **Option A on 2026-07-21** (declared-template-wins; 8 phases; ~10–20M
> objects; sequenced **defi → prediction → cefi → tradfi**, tradfi LAST). NOTHING is migrated on disk yet, so the WHOLE
> candle corpus is `migration_pending`. This doc's TARGET is the Option-A template; reconciliation treats un-migrated
> shape as `migration_pending` (taxonomy AE-6), never a defect. Migration source of truth:
> [`plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md`](../../plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md).

## 1. The candle shard atom (differs from raw tick)

```
service_name=market-data-processing-service · date · asset_group · [pipeline_mode({mode}_{source})]
  · timeframe · data_type(mdps_data_type_key — AGGREGATED) · [instrument_type] · venue · (KEY) · source
```

Deltas from the raw-tick atom ([`four-surface-reconciliation-procedure.md`](four-surface-reconciliation-procedure.md)
§2):

- **NEW `timeframe` axis** (`15s|1m|5m|15m|1h|4h|1d`; the manifest normalises `24h`→`1d`).
- **`data_type` is the AGGREGATED `mdps_data_type_key(src, tf)`** (`trades+1m→ohlcv_1m`,
  `book_snapshot_5+5m→ book5_ohlcv_5m`, `derivative_ticker+1h→deriv_ohlcv_1h`; already-`ohlcv_*` pass through), NOT the
  source type. The Option-A target puts this SAME aggregated key on BOTH the manifest AND the path — that is what makes
  `path==manifest` hold on the `data_type` axis, the exact invariant the migration restores.
- **S3 rows are filtered `service_name=="market-data-processing-service"`** — candle rows share ONE `_index` with
  raw-tick rows ([`chart-candle-delivery-flow.md`](chart-candle-delivery-flow.md) § "Read path"); the filter is
  load-bearing, or the two layers conflate.
- **(KEY)** = `instrument_id` for flat-per-contract writes (the leaf stem equals the `instrument_id` column, e.g.
  `DERIBIT:PERPETUAL:BTC-PERPETUAL.parquet`), or the `ticks.parquet` bundle name for chain-bundle
  (`options_chain`/`futures_chain`) writes. This is the SSOT rule in `output_path_helpers.py`
  (`is_chain_bundle_data_type()` / `candle_output_filename()` / `CHAIN_BUNDLE_FILENAME = "ticks.parquet"`). An EMPTY
  stem (`venue=…/.parquet`) is a genuine defect, not a grain (§4).
- **`instrument_type`** is writer-inferred, is absent on disk today, and is ADDED by the Option-A target. Prediction
  candles use `instrument_type=` as the terminal axis IN PLACE OF `venue=`
  ([`per-asset-group-bucket-layouts.md`](per-asset-group-bucket-layouts.md)).

## 2. The four surfaces (candles)

- **S1 — GCS path** under `processed_candles/by_date/` (sports: `processed/`). TARGET grammar (Option A):
  `…/pipeline_mode=…/timeframe=…/data_type={mdps_data_type_key}/instrument_type=…/venue=…/{canonical_id}.parquet`
  (prediction drops `venue=`). Registry SSOT for the target shape:
  `unified-trading-library/unified_trading_library/config_interface/paths/registry.py:28` (`processed_candles`
  `path_template`). **Note the template is not yet the full target**: today it is
  `processed_candles/by_date/day={date}/timeframe={timeframe}/data_type={data_type}/instrument_type={instrument_type}/venue={venue}/`
  — it carries NO `pipeline_mode=` segment; Option-A decision 1 adds `pipeline_mode=` there so `build_path()` alone
  yields the ratified shape.
- **S2 — parquet content** — the MDPS candle contract (`lookup_mdps_contract(mdps_data_type_key)`), never the raw-tick
  contract. OHLC nullability is PER-TYPE (deriv + empty-window rows legitimately nullable — resolved P0,
  [`mdps_derivative_ticker_candle_schema_violation_2026_07_20.md`](../../plans/active/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md)).
  Columns (`timestamp` UTC, `venue`/`symbol`/`instrument_id`, `open`/`high`/`low`/`close`/`volume`, `trade_count`/…,
  `delay_*_ms`): [`chart-candle-delivery-flow.md`](chart-candle-delivery-flow.md) §6. A closed OHLCV candle is
  timestamped by the bar-edge convention in
  [`bar-boundary-candle-edge-convention.md`](bar-boundary-candle-edge-convention.md) (RIGHT edge `t_close`, half-open
  window `[t_open, t_close)`); an S2 check must not assume left-edge stamping.
- **S3 — manifest `_index`** — rows filtered `service_name=="market-data-processing-service"`; the atom carries
  `timeframe` + the aggregated `data_type`. **Expect near-empty** — the candle write path is not calling
  `record_captured` per shard (§4), so the reconciliation is GCS-object-DRIVEN, not manifest-driven, for the entire
  candle layer.
- **S4 — catalogue — NONE.** Candles are DERIVED; there is no instruments-store catalogue for them. The chart route's
  `BatchCandleReader` prunes off S3 directly ([`chart-candle-delivery-flow.md`](chart-candle-delivery-flow.md) § "Read
  path") — it is not an independent surface. **S4 is `UNAVAILABLE` for the ENTIRE candle layer BY CONSTRUCTION** —
  report it ONCE as a declared coverage gap (the same whole-surface-absent handling as prediction's S4 in
  [`four-surface-reconciliation-procedure.md`](four-surface-reconciliation-procedure.md) §6), never a per-shard verdict.

## 3. Canonical authority — the oracle does NOT cover candles

`canonical_path_violations()` hardcodes `RAW_TICK_DATA_PREFIX = "raw_tick_data/by_date/"`
(`unified-api-contracts/unified_api_contracts/canonical/partition_paths.py:67`) and therefore returns a `structural`
violation for EVERY `processed_candles/` path — canonical and orphan alike (verified 2026-07-20,
[`candle_feature_canonical_path_divergence_2026_07_20.md`](../../plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md)
finding iii-b). So the raw-tick §4 machine-oracle rule does not apply to candles. Candle canonicality is checked against
the ratified Option-A **registry template** — a JUSTIFIED exception to "never re-implement the oracle" (the oracle does
not cover this namespace, so this is not oracle-drift). The durable fix is extending the oracle to `processed_candles/`
(that issue's todo 10); when it ships, re-point the skill's candle leg at the oracle. `require_pipeline_mode` is
meaningless for candles until the migration adds `pipeline_mode=` to the registry template — during `migration_pending`,
do not enforce it.

Candles are oracle-EXEMPT exactly as sports is
([`four-surface-reconciliation-procedure.md`](four-surface-reconciliation-procedure.md) §4). State this in every candle
report.

## 4. Genuine defects vs migration_pending

**`migration_pending` (SUPPRESS — taxonomy AE-6):** missing `instrument_type=` segment; SOURCE-not-aggregated
`data_type` (`derivative_ticker` on the path instead of `deriv_ohlcv_*`); split-brain `pipeline_mode` (present on some
objects, absent on others, same bucket/day). These are the ruled Option-A deltas; flagging them today false-flags the
entire un-migrated corpus. Date-condition against the candle rows of
[`canonical-cutover-register.md`](canonical-cutover-register.md) (per-AG, defi-first / tradfi-last; all PENDING today).

**Genuine findings (regardless of the migration window):**

- **object↔manifest disconnect** — candle objects with no `service_name=="market-data-processing-service"` S3 row →
  `missing_row` at corpus scale. Measured 2026-07-20: cefi `day=2026-04-14` holds 20,734 candle objects vs 6
  `market-data-processing-service` rows corpus-wide (and the 6 are degenerate — venue empty, `row_count` NaN). This is
  the HEADLINE candle finding — report the count.
- **empty-stem `venue=*/.parquet`** — a chain-bundle write that took the `{instrument_id}.parquet` branch with no single
  id → empty stem; unattributable to a shard. Repair to a bundled `ticks.parquet` or purge. Genuine data defect (see the
  taxonomy gap in §5).
- **unresolvable TradFi migration-artifact leaf ids** (`E1AF0_*_migrated_*.parquet`) where CeFi leaves are canonical
  (`DERIBIT:PERPETUAL:BTC-PERPETUAL.parquet`) → `non_canonical_id` on the S1 leaf; unresolvable → QUARANTINE, never
  fake-canonicalise.
- **split-brain duplicate copies** → `legacy_duplicate`, content-verified before any dedup suggestion.

All prod-bucket deletes stay human-only hard stops
([`gcs-and-manifest-delete-safety-protocol.md`](gcs-and-manifest-delete-safety-protocol.md)); the migration's own
copy→verify(crc32c)→delete purge is the operator-authorised deletion path, NOT this read-only skill's.

## 5. Taxonomy delta (candles need almost no new types)

The existing closed set ([`reconciliation-finding-taxonomy.md`](reconciliation-finding-taxonomy.md)) covers candles with
these detection-method notes:

- **`non_canonical_path`** — the DETECTOR for candles is the bespoke Option-A template checker, NOT
  `canonical_path_violations()` (raw-tick-only). Same type, different detector; state it.
- **`missing_row`** — unchanged; it is the DOMINANT candle finding (manifest under-population).
- **`non_canonical_id`** — covers the TradFi migration-artifact leaves and (as the degenerate S1-leaf case) the empty
  stems.
- **`non_canonical_axis_value` / `shard_atom_vocab_desync`** — the census types cover the candle vocabulary incl. the
  SOURCE-vs-AGGREGATED `data_type` `M △ G` desync (suppressed by AE-6 during migration).
- **`shard_pillar_fail`** — the candle schema (S2) check against the MDPS candle contract.

**ONE genuine taxonomy GAP to escalate:** the empty-stem candle object (`venue=*/.parquet`) — rows present, hive path
parseable, but an EMPTY leaf that cannot be attributed to an instrument — is neither cleanly `junk` (junk = zero-row /
unparseable-key) nor `non_canonical_id` (which is a per-ROW builder mismatch). Report it under an explicit
**taxonomy-gap** banner as a candidate new type (`unattributable_object`, repair-eligible, NOT
delete-eligible-on-this-alone) until the taxonomy owner rules it.

The migration-window suppression is codified as **AE-6** in
[`reconciliation-finding-taxonomy.md`](reconciliation-finding-taxonomy.md).

## 6. Census + compute tiers for candles

See [`reconciliation-census-and-compute-tiers.md`](reconciliation-census-and-compute-tiers.md). Candle deltas:

- The in-session census axis set ADDS `timeframe`; `data_type` is badged against the AGGREGATED `mdps_data_type_key`
  vocabulary, NOT the raw-tick `DATA_TYPES_BY_ASSET_GROUP`.
- The manifest-side census must filter `service_name=="market-data-processing-service"` and add `timeframe` to
  `AXIS_CENSUS_COLUMNS` (`deployment-api/deployment_api/routes/data_status/_axis_census.py:86` — today
  `venue/chain/instrument_type/data_type/source/pipeline_mode`, no `timeframe`).
- The GCS-side delimiter-descent order comes from the MDPS registry template (`registry.py` `processed_candles`), NOT
  `canonical_path_templates(ag)` (raw-tick-only; returns nothing for `processed_candles/`).
- Tier-2 per-datapoint id+schema validation applies with the MDPS candle contract (`lookup_mdps_contract`), but is
  PREMATURE today — the candle corpus is tiny and the manifest is unpopulated, so a Tier-2 candle walk validates almost
  nothing. Default to Tier-1 sampled for candles; defer Tier-2 candle validation until the candle backfill runs, and say
  so in the report.

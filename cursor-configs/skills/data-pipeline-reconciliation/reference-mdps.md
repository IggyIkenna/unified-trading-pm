# reference-mdps — layer expansion for `/data-pipeline-reconciliation --layer candles`

Expansion of [`SKILL.md`](SKILL.md) § 3h (the candle LAYER, not a single AG). Pointers + hazards only — the durable
rules live in
[`/codex/02-data/mdps-candle-canonical-reconciliation.md`](/codex/02-data/mdps-candle-canonical-reconciliation.md).

> ⚠️ **Candles are a DIFFERENT LAYER, not a sixth asset_group.** They span all five AGs, live under a different path
> tree in the SAME bucket, add a `timeframe` axis, and are NOT covered by the UAC machine oracle. Read this before
> auditing any candle estate.

> **⚠️→✅ CORRECTED 2026-07-21 (evening) — supersedes the "Option A" framing below.** The original Option-A framing
> (declared-registry-template-wins, `data_type` rewritten to the AGGREGATED `mdps_data_type_key` on the path) was
> RE-DECIDED with corrected info: the path **keeps the SOURCE `data_type`** (unchanged); only `instrument_type=` +
> `pipeline_mode=` are ADDED to the path, and the **manifest** is what re-aligns (to SOURCE) instead. See
> [`candle_feature_canonical_path_divergence_2026_07_20.md`](../../../plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md)
> § "CORRECTED RULING 2026-07-21 (evening)" for the full detail. The migration is now **folded into**
> `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` (not a standalone effort) — as of
> 2026-07-21 there is **NO VM running for this candle-path phase yet** (verified via `gcloud compute instances list`;
> the running `canonical-migration-cefi-*` fleet is a SEPARATE `raw_tick_data/` column-patch migration). The candle
> cutover is scheduled to start **after that raw-tick cefi fleet drains** (manifest-shard contention + the
> pre-migration-drain rule) — state it as NOT YET STARTED, never "running elsewhere."

## Path grammar (candle layer)

LOCKED shape (corrected 2026-07-21 evening — the canonical the audit reconciles against):

```
processed_candles/by_date/day={D}/pipeline_mode={mode}_{source}/timeframe={tf}/
  data_type={SOURCE_dt}/instrument_type={it}/venue={v}/{canonical_id}.parquet

# prediction: … /instrument_type={it}/{canonical_id}.parquet   (NO venue=)
# sports:     processed/by_date/day={D}/data_type=odds_horizon_bucket/league_id=…/timeframe=T-10m/bucketed.parquet
```

`data_type` is the **SOURCE** type (`derivative_ticker`/`trades`/`book_snapshot_5`/`dex_pool_swaps`/`ohlcv_1m`) —
**unchanged by the migration**; the AGGREGATED `mdps_data_type_key` survives only as the schema-contract lookup key
(S2), never the path or (post-migration) manifest axis. Registry SSOT for the shape:
`unified-trading-library/unified_trading_library/config_interface/paths/registry.py` (`processed_candles`
`path_template`, now carries the `pipeline_mode=` segment). Current on-disk shapes (all `migration_pending`, do NOT
flag): missing `instrument_type=`; and a split-brain where some objects carry `pipeline_mode=` and some drop it
(`timeframe=` directly under `day=`) in the SAME bucket on the SAME day
([`candle_feature_canonical_path_divergence_2026_07_20.md`](../../../plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md)
findings 1 + iii-a). The SOURCE-vs-aggregated `data_type` divergence is a **manifest-only** gap (pre-migration rows
carry the aggregated key; going-forward writes carry SOURCE) — never a path finding.

## Buckets — resolve, never hand-build (SAME buckets as raw tick)

`resolve_bucket_name(cloud, "market-data", asset_group=<ag>, deployment_env="prd")` → `market-data-tick-{ag}-prd-{pid}`.
Candles are the `processed_candles/` object prefix INSIDE it (sports: `processed/`). No candle-specific bucket exists —
Phase-0 bucket resolution is UNCHANGED (`kind="market-data"`, alias `tick-data`); only the object prefix distinguishes
the layer ([`per-asset-group-bucket-layouts.md`](/codex/02-data/per-asset-group-bucket-layouts.md);
[`data-pipeline-check-mdps/SKILL.md`](../data-pipeline-check-mdps/SKILL.md)).

## Shard atom + (KEY)

`[service_name=market-data-processing-service, date, asset_group, (pipeline_mode), timeframe, data_type(SOURCE type), (instrument_type), venue, (KEY), source]`.

- **(KEY) = `instrument_id`** for flat-per-contract (leaf stem == the `instrument_id` column, e.g.
  `DERIBIT:PERPETUAL:BTC-PERPETUAL.parquet`).
- **chain-bundle writes (`options_chain` / `futures_chain`) → `ticks.parquet`** bundle leaf (no per-instrument stem).
  SSOT for the filename rule:
  `market-data-processing-service/market_data_processing_service/app/core/output_path_helpers.py`
  (`is_chain_bundle_data_type()` / `candle_output_filename()` / `CHAIN_BUNDLE_FILENAME = "ticks.parquet"`).
- **`data_type` is the SOURCE type** (corrected 2026-07-21 evening — supersedes the earlier "aggregated on both"
  framing) on BOTH the path (unchanged) and the (post-migration) manifest; `timeframe` normalised `24h`→`1d`. The
  AGGREGATED `mdps_data_type_key(src, tf)` survives only as the schema-contract lookup key (S2), not a stored axis.
- **`service_name` filter is load-bearing** — candle rows share the `_index` with raw-tick rows.

## The four surfaces (candle layer)

- **S1** path under `processed_candles/` — checked against the LOCKED template (oracle-exempt namespace, H2).
- **S2** MDPS candle contract via `lookup_mdps_contract(mdps_data_type_key)` — OHLC/`open` nullability is PER-TYPE
  (deriv + empty-window nullable, resolved P0 —
  [`mdps_derivative_ticker_candle_schema_violation_2026_07_20.md`](../../../plans/active/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md)).
  Columns per [`chart-candle-delivery-flow.md`](/codex/02-data/chart-candle-delivery-flow.md) §6; the candle is
  timestamped on its RIGHT edge (`t_close`, half-open `[t_open, t_close)`) per
  [`bar-boundary-candle-edge-convention.md`](/codex/02-data/bar-boundary-candle-edge-convention.md).
- **S3** `_index` rows filtered `service_name=="market-data-processing-service"` — **near-empty today** (H3).
- **S4** NONE — no candle catalogue. `UNAVAILABLE` for the whole layer, reported ONCE as a declared coverage gap.

## HAZARDS

### H1 — sports is `processed/`, an entirely different tree (no `processed_candles/` at all)

`processed/by_date/day={D}/data_type=odds_horizon_bucket/league_id=…/timeframe=T-10m/bucketed.parquet` — single file per
date, bookmaker-time bucketed odds; no per-venue candles. Deleting `processed/` breaks the live sports lane
([`non-canonical-path-inventory.md`](/codex/02-data/non-canonical-path-inventory.md);
[`per-asset-group-bucket-layouts.md`](/codex/02-data/per-asset-group-bucket-layouts.md)). A generic candle pass flags
the whole sports estate — dispatch to the sports tree, don't probe `processed_candles/` for sports.

### H2 — the UAC machine oracle does NOT govern candle paths

`canonical_path_violations()` hardcodes `RAW_TICK_DATA_PREFIX = "raw_tick_data/by_date/"`
(`unified-api-contracts/unified_api_contracts/canonical/partition_paths.py:67`) and returns an identical `structural`
violation for EVERY `processed_candles/` path — canonical and orphan alike (verified 2026-07-20,
[`candle_feature_…`](../../../plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md) iii-b). Candle
canonicality is a BESPOKE check against the LOCKED template — a JUSTIFIED exception to "never re-implement the oracle"
(the oracle doesn't cover this namespace). State it in the report. The durable fix is the oracle-extension (that issue's
todo 10); re-point here when it ships.

### H3 — object↔manifest disconnect: the candle manifest is unpopulated

cefi `day=2026-04-14` = **20,734 candle objects** vs **6** `market-data-processing-service` rows corpus-wide, and the 6
are degenerate (venue empty, `row_count` NaN). The candle write path isn't calling `record_captured` per shard (NOT
consolidation lag). Consequences: prod skip-if-fresh re-derives everything; honest coverage reports candles absent while
20k+ sit on disk. Drive the audit off GCS objects; report every candle object with no S3 row as `missing_row`, and the
disconnect count as the HEADLINE candle finding
([`candle_feature_…`](../../../plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md) finding ii +
todo 7).

### H4 — split-brain `pipeline_mode` (present vs absent on the same day)

The same cefi day (2026-05-23) holds both `…/pipeline_mode=…/timeframe=…/…` and `pipeline_mode`-less `…/timeframe=…/…`
candle objects. A `pipeline_mode`-blind glob and a `pipeline_mode`-aware glob see disjoint subsets — a silent split over
the candle estate. During migration this is `migration_pending` (the migration dedups to one canonical copy); the
surviving duplicate copies are `legacy_duplicate` (content-verify before any dedup suggestion), never a blind delete
([`candle_feature_…`](../../../plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md) iii-a + todo
9).

### H5 — GENUINE DEFECTS (findings TODAY, not migration_pending)

- **Empty-stem `venue=*/.parquet`** — a chain-bundle write that took the `{instrument_id}.parquet` branch with no single
  id → empty stem; unattributable to a shard. Repair to a bundled `ticks.parquet` or purge
  ([`candle_feature_…`](../../../plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md) finding 4 +
  i + todo 2/8). **Taxonomy-gap** — propose `unattributable_object` (see the SSOT §5).
- **TradFi migration-artifact leaf ids** (`E1AF0_C3200_migrated_20260418T131054Z.parquet`) where CeFi leaves are
  canonical (`DERIBIT:PERPETUAL:BTC-PERPETUAL.parquet`) — `non_canonical_id` (S1 leaf); unresolvable → QUARANTINE, never
  fake-canonicalise
  ([`candle_feature_…`](../../../plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md) finding 3).
- **`derivative_ticker` candle schema violation — RESOLVED 2026-07-20**: OHLC nullability now inherits per-type from the
  UAC SSOT; do NOT re-file it
  ([`mdps_derivative_ticker_candle_schema_violation_2026_07_20.md`](../../../plans/active/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md)).

## Known-good spot-check — run BEFORE trusting any absence result

The generalised lesson from the defi `solana_amm_pool` false negative ([`SKILL.md`](SKILL.md) § 4b): **an absence result
is only evidence once you have confirmed you probed the vocabulary the writer actually emits** — for candle **paths**
that vocabulary is the SOURCE `data_type` (corrected 2026-07-21 evening), never the aggregated key; for **pre-migration
manifest rows** the aggregated `mdps_data_type_key` still applies until the backward migration re-keys them.

1. Resolve the SAME bucket (`kind="market-data"`, per AG); candles are the `processed_candles/` prefix inside it
   (sports: `processed/`).
2. `list` the `processed_candles/by_date/day={D}/` child prefixes FIRST to see which
   `(pipeline_mode?, timeframe, data_type)` actually wrote that day — do NOT assume an arbitrary
   `(day, timeframe, data_type)` has objects (the corpus is tiny and uneven).
3. Probe BOTH the `pipeline_mode=`-present and `pipeline_mode`-less shapes (H4) or you see a disjoint subset.
4. Badge object-path `data_type` against the SOURCE `DATA_TYPES_BY_ASSET_GROUP` vocabulary (`derivative_ticker`,
   `trades`, …), NOT the aggregated `mdps_data_type_key` set (`ohlcv_1m`, `deriv_ohlcv_1h`, …) — corrected 2026-07-21
   evening; an aggregated-key probe false-phantoms every SOURCE cell on disk. The aggregated key still applies when
   probing pre-migration MANIFEST rows.
5. Only then treat a zero as a finding. Remember S3 is near-empty (H3) — absence in the manifest is NOT absence on disk.

## Census / vocabulary nuance (candle layer)

Added 2026-07-21 — the in-session distinct-value census
([`reconciliation-census-and-compute-tiers.md`](/codex/02-data/reconciliation-census-and-compute-tiers.md)).

- The census axis set ADDS `timeframe`; going-forward (corrected 2026-07-21 evening) object-path `data_type` is badged
  against the SOURCE `DATA_TYPES_BY_ASSET_GROUP` vocabulary — the path was NEVER rewritten to the aggregated key, so
  this is the vocabulary today, not just post-migration.
- The manifest-side census must filter `service_name=="market-data-processing-service"` and add `timeframe` to the
  census columns — `deployment-api/deployment_api/routes/data_status/_axis_census.py:86` `AXIS_CENSUS_COLUMNS` has
  `venue/chain/instrument_type/data_type/source/pipeline_mode` and NO `timeframe` today.
- The GCS-side descent order comes from the MDPS registry template (`registry.py` `processed_candles`), NOT
  `canonical_path_templates(ag)` (raw-tick-only; returns nothing for `processed_candles/`).
- The SOURCE-vs-AGGREGATED `data_type` gap is a **manifest-only** `M △ G` desync (pre-migration manifest rows carry the
  aggregated key; the path always carried SOURCE) — SUPPRESS it under AE-6 until the backward manifest re-key completes;
  post-migration it becomes a genuine desync detector.

## Cross-links

[`SKILL.md`](SKILL.md) ·
[`/codex/02-data/mdps-candle-canonical-reconciliation.md`](/codex/02-data/mdps-candle-canonical-reconciliation.md) ·
[`/codex/02-data/per-asset-group-bucket-layouts.md`](/codex/02-data/per-asset-group-bucket-layouts.md) ·
[`/codex/02-data/chart-candle-delivery-flow.md`](/codex/02-data/chart-candle-delivery-flow.md) ·
[`/codex/02-data/bar-boundary-candle-edge-convention.md`](/codex/02-data/bar-boundary-candle-edge-convention.md) ·
[`/codex/02-data/reconciliation-finding-taxonomy.md`](/codex/02-data/reconciliation-finding-taxonomy.md) (AE-6) ·
[`/codex/02-data/canonical-cutover-register.md`](/codex/02-data/canonical-cutover-register.md) (candle rows) ·
[`plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md`](../../../plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md)
·
[`plans/active/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md`](../../../plans/active/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md)

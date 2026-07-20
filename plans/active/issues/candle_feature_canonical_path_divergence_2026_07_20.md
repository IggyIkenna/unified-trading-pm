---
doc_type: issue
title:
  MDPS candle + features object paths diverge from their declared canonical templates — path≠declared-template,
  path≠manifest on data_type, non-canonical TradFi leaf ids, an empty-stem object, and a volatility writer that bypasses
  its own path SSOT
summary: >-
  Ground-truthed against real prod objects while building /data-pipeline-check-mdps + /data-pipeline-check-features.
  MDPS candle OBJECT paths do not match the template the writer's own SSOT declares — they omit the instrument_type=
  segment entirely and carry the SOURCE data_type (data_type=derivative_ticker) while the MANIFEST row for the same
  shard carries the AGGREGATED mdps_data_type_key (deriv_ohlcv_15m) and the normalised timeframe. So the documented
  path==manifest invariant does not hold on the data_type axis. Separately, TradFi candle leaves are non-canonical
  migration artifacts (E1AF0_C3200_migrated_20260418T131054Z.parquet) where CeFi leaves are correctly canonical
  (DERIBIT:PERPETUAL:BTC-PERPETUAL.parquet), and at least one object has a ZERO-LENGTH instrument stem
  (venue=CME/.parquet) which is a genuine data defect. On the features side the volatility writer bypasses its own
  declared path SSOT (get_data_sink built with no prefix=, so UTL emits day={D}/feature_group=/timeframe=/{u}.parquet at
  the BUCKET ROOT instead of under volatility/by_date/), and the UTL paths registry's delta_one entry is stale versus
  the real writer. None of this is silently accepted by the new skills — the canonical leg reports each divergence as
  content_check=non_canonical and collects them into a migration worklist — but the underlying writers need an operator
  ruling on which shape is canonical before a full-history backfill bakes the current shape into ~386
  serial-compute-days of new candles.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [market-data-processing-service, features-service, unified-trading-library, unified-api-contracts]
scope: [engineer, admin]
tags: [data-correctness, canonical, gcs-paths, manifest, candles, features, migration, mdps, volatility]
related:
  [../data_pipeline_check_mdps_features_2026_07_20.md, ../../codex/02-data/availability-manifest-and-data-status.md]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: data
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  measured 2026-07-20 by direct `gsutil ls` against market-data-tick-{cefi,tradfi,sports}-prd-central-element-323112
  while building the two data-pipeline-check skills; writer-side claims re-read from the actual writer code.
---

# Candle + feature object paths diverge from their declared canonical templates

> **Why this matters NOW**: derived candles are effectively greenfield (cefi 6 manifest rows, tradfi 139, prediction 168
> as of 2026-07-20) and a full-history candle backfill is ~386 serial-compute-days of work. Whatever shape the writer
> emits will be baked into the entire corpus. **Rule on the canonical shape BEFORE the big backfill runs**, not after.

## Measured evidence (real prod objects, not inferred)

```
# cefi — data_type is the SOURCE type; NO instrument_type= segment; leaf id IS canonical
gs://market-data-tick-cefi-prd-central-element-323112/processed_candles/by_date/day=2019-03-30/
  pipeline_mode=batch_tardis/timeframe=15m/data_type=derivative_ticker/venue=DERIBIT/
  DERIBIT:PERPETUAL:BTC-PERPETUAL.parquet

# tradfi — NO instrument_type=; leaf id is a MIGRATION ARTIFACT, not VENUE:TYPE:SYMBOL
gs://market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2020-01-01/
  pipeline_mode=batch_databento/timeframe=15m/data_type=ohlcv_15m/venue=CME/
  E1AF0_C3200_migrated_20260418T131054Z.parquet

# tradfi — ZERO-LENGTH instrument stem (a genuine defect)
  .../timeframe=15m/data_type=ohlcv_15m/venue=CME/.parquet

# sports — a legitimately DIFFERENT root and shape (processed/, league_id=, bucketed.parquet); no processed_candles/ at all
gs://market-data-tick-sports-prd-central-element-323112/processed/by_date/day=.../data_type=.../
  league_id=.../timeframe=T-10m/bucketed.parquet
```

## Findings

1. **`instrument_type=` is absent from every MDPS candle object path** (cefi + tradfi), while the declared template (UTL
   `PATH_REGISTRY["processed_candles"].path_template`, and `config.get_processed_path`'s documented shape) includes it.
   Consistent across the corpus → this is the writer's de-facto shape, not sporadic corruption.
2. **path ≠ manifest on `data_type`.** The OBJECT carries the SOURCE `data_type` (`derivative_ticker`); the MANIFEST row
   for the same shard carries the AGGREGATED `mdps_data_type_key(src, tf)` (`deriv_ohlcv_15m`) plus the normalised
   timeframe (`24h`→`1d`). `market-data-processing-service/docs/GCS_PATHS.md:42` documents the `data_type={source}`
   object form, so the two SSOTs themselves disagree. **This is the ruling that's needed** (see Decision below).
3. **TradFi candle leaf ids are non-canonical** (`E1AF0_C3200_migrated_20260418T131054Z.parquet`) where CeFi's are
   correctly canonical (`DERIBIT:PERPETUAL:BTC-PERPETUAL.parquet`). TradFi candles appear to carry a one-off migration
   naming that never got canonicalised.
4. **At least one zero-length-stem object exists** (`venue=CME/.parquet`). A parquet with no instrument id cannot be
   attributed to a shard — a real defect, not a naming nit. Needs a corpus-wide count + purge/repair.
5. **`volatility` writer bypasses its own declared path SSOT.** `VolatilityFeatureWriter._upload_parquet` builds
   `get_data_sink(bucket=…, routing_key=…)` with **no `prefix=`**, so UTL's `_build_partition_path` emits
   `day={D}/feature_group={g}/timeframe={tf}/{underlying}.parquet` at the **bucket root** — missing the
   `volatility/by_date/` prefix that BOTH `volatility/io/writer.py::build_path` AND the UTL paths-registry `DataSetSpec`
   declare.
6. **UTL paths-registry `delta_one` entry is stale**: it declares
   `delta_one/by_date/day={date}/feature_group=/timeframe=/` (with `by_date/`, no version) while the real writer emits
   `delta_one/day={D}/feature_group={fg}/feature_group_version={N}/timeframe={tf}/{id}.parquet`.

## MEASURED 2026-07-20 (bounded day-prefix listings — NOT a corpus walk)

### (i) Zero-length instrument stems are ONGOING, not historical

| corpus                  | candle objects | empty-stem `/.parquet` | share |
| ----------------------- | -------------- | ---------------------- | ----- |
| cefi `day=2019-05-08`   | 56             | **14**                 | 25%   |
| cefi `day=2020-01-01`   | 3,318          | 0                      | 0%    |
| tradfi `day=2020-01-01` | 8,546          | 50                     | 0.6%  |
| cefi `day=2026-04-14`   | 20,734         | 168                    | 0.8%  |

Mechanism (read from `output_path_helpers.py::candle_output_filename`): a bundle written under an `underlying=`
partition for a data_type that is NOT in `CEFI_CHAIN_INSTRUMENT_TYPES` (e.g. DERIBIT `data_type=trades` grouped by
underlying) takes the `f"{instrument_id}.parquet"` branch, but a bundle has no single `instrument_id` → the stem is
EMPTY. Measured example:
`processed_candles/by_date/day=2019-05-08/pipeline_mode=batch_tardis/timeframe=15m/data_type=trades/venue=DERIBIT/underlying=BTC/.parquet`

**This is the chain-bundle rule leaking**: the operator's contract is "one bundled file per (date, root)" =
`ticks.parquet`. These objects are bundles that never got the bundled NAME because the data_type gate is keyed on
`{options_chain, futures_chain}` only, while the WRITER bundles by `underlying=` for more data_types than that. Fix
direction: make the bundled-name decision follow "is this write bundled by `underlying=`?", not "is the data_type in the
chain set". Objects with an empty stem cannot be attributed to an instrument and should be repaired or purged.

### (ii) BIG: candle objects exist WITHOUT manifest rows (object↔manifest disconnect)

cefi `day=2026-04-14` holds **20,734 candle objects**, yet the whole cefi availability index carries only **6** rows
with `service_name=="market-data-processing-service"` (measured via slim read, §B3 of the parent plan). A ~3,400×
disconnect on a single day. Consequences, all real:

- **skip-if-fresh is driven by the manifest** (`check_shard_freshness`) → it sees "not fresh" and RE-DERIVES candles
  that already exist, wasting the exact compute the ~386-serial-day backfill is trying to budget.
- **honest coverage / data-status** report candles as absent while 20k+ objects sit on disk — the "invisible by
  declaration" pattern the honest-coverage codex warns about, inverted.
- **features input-coverage** (and the new `/data-pipeline-check-features` `--require-captured`) will report
  `no_captured_input_for_window` for candle-dependent families even though the candles exist.

This is the INVERSE of `PHANTOM_CAPTURED_NO_OBJECT` (manifest row, no object): here it is object, no manifest row.
Root-cause it before the full-history backfill — either MDPS is not calling `record_captured` on these paths, or the
rows are stranded in un-consolidated per-VM shards.

## Decision required (operator) — which shape is canonical?

**(A) [RECOMMENDED] The declared template is canonical → migrate the writers.** Add `instrument_type=` to the candle
object path, use the aggregated `mdps_data_type_key` on the object path so path==manifest genuinely holds, canonicalise
TradFi leaf ids, and give volatility its declared prefix. Do it **before** the full-history backfill so the corpus is
born canonical; the existing corpus is small enough (cefi 6 rows) that migrating it is cheap. **Cost: a breaking
object-layout change — every reader that path-globs candles (features `delta_one`/`volatility` data loaders) must be
updated in the same change (blast-radius rule).**

**(B) The emitted shape is canonical → fix the declarations.** Update `PATH_REGISTRY`/`GCS_PATHS.md`/the volatility
`build_path` + registry to match what the writers actually emit, and drop the path==manifest claim on `data_type`.
Cheapest, no data migration, but it ratifies path≠manifest.

**(C) Split the difference**: ratify the emitted candle shape (B) but still fix the _genuine defects_ — TradFi
non-canonical leaf ids, the empty-stem objects, and the volatility bucket-root bypass.

Findings 3 and 4 are **defects under every option** and should be fixed regardless.

## Todos

- [ ] 1. [DATA] P1. **Operator ruling on A/B/C** for the candle object-path shape (`instrument_type=` presence + source
      vs aggregated `data_type`). Blocks the full-history candle backfill — decide before ~386 serial-compute-days bake
      in the current shape.
- [ ] 2. [DATA] P1. Corpus-wide count of **zero-length-stem** candle objects (`…/venue=*/.parquet`); purge or repair.
      These cannot be attributed to a shard.
- [ ] 3. [DATA] P1. Canonicalise **TradFi candle leaf ids** (`E1AF0_C3200_migrated_*` → `VENUE:TYPE:SYMBOL`) or rule the
      migration naming acceptable.
- [ ] 4. [SCRIPT] P1. **volatility writer**: pass the declared `prefix=` to `get_data_sink` so output lands under
      `volatility/by_date/` per its own SSOT — or amend the SSOT. Currently writes to the bucket root.
- [ ] 5. [SCRIPT] P2. Reconcile the **UTL paths-registry `delta_one` entry** with the real writer
      (`feature_group_version=` present, no `by_date/`).
- [ ] 6. [SCRIPT] P2. Once ruled: re-point `/data-pipeline-check-mdps` + `/data-pipeline-check-features` canonical legs
      at the ratified template so a clean canonical sweep is achievable (today they correctly report the divergence).

## How the new skills currently handle this (no silent acceptance)

`/data-pipeline-check-mdps` and `/data-pipeline-check-features` verify the **force/skip** legs against the writer's REAL
measured shape (so the pipeline mechanism is provable and every shard gets tested), and report each divergence from the
DECLARED template as a **separate** `content_check=non_canonical` verdict collected into a greppable
`## Migration worklist (canonical-shape gaps)` section. Three failure modes on one cell never collapse into one bit.
`rg 'non_canonical|content_check' <report>` yields the worklist.

- [ ] 7. [DATA] P0. **Root-cause the object↔manifest disconnect** (20,734 cefi candle objects on 2026-04-14 vs 6 MDPS
      manifest rows corpus-wide). Either `record_captured` is not firing on the candle write path or per-VM shards never
      consolidated. Blocks trustworthy skip-if-fresh, honest coverage, and features input-gating.
- [ ] 8. [DATA] P1. **Fix the bundled-name rule**: decide the leaf by "is this write bundled by `underlying=`?" rather
      than "is data_type in CEFI_CHAIN_INSTRUMENT_TYPES", so every `underlying=`-bundled write gets `ticks.parquet`
      instead of an empty stem. Then repair/purge the existing empty-stem objects (measured 0.6-25% depending on day).

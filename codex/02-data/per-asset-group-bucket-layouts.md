---
doc_type: codex-ssot
title: Per-Asset-Group Bucket & Path Layouts — SSOT
summary: >-
  Per-asset-group GCS bucket & path-layout SSOT — canonical resolver-owned bucket templates per (service x asset_group)
  with {env} tiering, and the REAL path divergences (SPORTS per-league sports_reference/ 4 layouts, PREDICTION per-cqg,
  tradfi non-hive, DeFi chain= level) plus the MDPS dep-checker UPSTREAM_DEPS routing and the safe_iterate_blobs
  list-blobs quirk.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    features-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: [manifest, sports, prediction, defi, tradfi, mdps, canonicalisation]
related:
  [
    codex/02-data/partitioning.md,
    codex/02-data/availability-manifest-and-data-status.md,
    codex/02-data/pipeline-coverage-matrix.md,
    codex/02-data/service-output-emission-semantics.md,
  ]
created: 2026-04-20
authoritative_for: [per-asset-group GCS bucket templates, per-asset-group path-layout divergences]
referenced_by:
  [
    codex/02-data/chart-candle-delivery-flow.md,
    codex/02-data/data-status-drilldown.md,
    codex/02-data/defi-data-types-catalog.md,
    codex/02-data/defi-venue-protocol-catalogue.md,
    codex/02-data/hive-schema-compatibility.md,
    codex/02-data/is-test-run-audit-2026-04-20.md,
    codex/02-data/mtds-data-source-coverage-matrix.md,
    codex/02-data/mtds-download-api.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Per-Asset-Group Bucket & Path Layouts — SSOT

<!-- MULTI_AXIS_CORRECTION_2026_05_06 -->

> **Multi-axis correction (2026-05-06)** — shard atoms vs display axes (row-level columns) per asset_group are the SSOT
> in
> [`availability-manifest-and-data-status.md`](./availability-manifest-and-data-status.md#multi-axis-correction-banner-canonical).
> See that doc for the full per-asset-group shard-atom matrix (sports / prediction / cefi options-futures / DeFi chain /
> ML+strategy+execution job_id / TradFi EVENT_CONTRACT).

**Purpose**: canonical reference for every upstream/downstream GCS path layout per market asset_group (formerly
"category"). Written 2026-04-20 after the SPORTS smoke incident where MDPS + instruments-service + MTDS each had
different implicit assumptions about SPORTS path shape and the mismatch surfaced as
`list_files_in_bucket: string index out of range` +
`get_instruments_for_date: 404 instrument_availability/instruments.parquet` + MDPS dep-checker silently mis-firing.

**Status**: canonical. Any new service that reads or writes data partitioned by asset_group MUST consult this doc before
assuming a single-shape layout works across all groups.

**Asset-group hive vocabulary (2026-05-01 update; codex audit D-8 refresh 2026-05-12)**: `asset_group=` is **canonical**
for new MTDS writes (per `market_tick_data_service/raw_tick_hive.RAW_TICK_ASSET_GROUP_HIVE_KEY`). `category=` is the
**legacy** form preserved on disk for backward-compat reads only; readers try canonical → fall back to legacy per the
≤30-day reader-fallback window. **Legacy `category=` data + the reader-fallback is targeted for deletion ~2026-06-15**
(co-incident with the reader-fallback retirement gate per
[`service-output-emission-semantics.md`](./service-output-emission-semantics.md#manifest-read-protocol-per-service_emission_state)).
Migration scripts owning the legacy-to-canonical rekey:
[`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](../../plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md)

- instruments-service `scripts/migrate_*_bare_to_asset_group.py`. After 2026-06-15 the dual-vocab tolerance in this doc
  is removed; readers + writers go canonical-only. `category=` is the **legacy** form
  (`RAW_TICK_ASSET_GROUP_HIVE_KEY_LEGACY`) preserved on disk without a re-keying migration. Both coexist in production
  GCS — readers must try canonical first then fall back to legacy (`market_tick_data_service.reader` already does this;
  `deployment-api/utils/storage_facade.list_objects` transparently fans out to both vocabularies). Manifest pre-flight
  is hive-key-agnostic — it indexes by `(date, venue, chain, instrument_type, data_type)` only, so legacy `category=`
  data on disk is correctly skipped iff the manifest has a captured row for it.

**Key insight**: asset-group-specific path divergences are REAL and have been a source of recurring bugs. SPORTS in
particular does NOT follow the same layout as CEFI/TRADFI/DEFI/PREDICTION.

---

## Asset-group × bucket matrix

> **Bucket names are env-tiered + resolver-owned (canonicalised 2026-05-11, `bucket_name_ssot` Phase 0e).** Every
> canonical bucket embeds `{env}` = `${DEPLOYMENT_ENV_SHORT}` ∈ `dev`/`stg`/`prd`/`test` (workspace `prod` → `prd`).
> **Resolve every name via**
> `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(cloud="gcp", kind="tick-data" | "instruments-store", asset_group=...)`
> — **NEVER** hardcode an inline `gs://…` bucket string (QG STEP 5.69 enforces). Code SSOT:
> [`deployment-service/configs/cloud-providers.yaml`](../../../deployment-service/configs/cloud-providers.yaml). Notes:
> **PREDICTION uses the short token `pred`** (not `prediction`) for both stores; AWS swaps `{project_id}` →
> `{aws_account_id}` (GCP keeps the `-tick-` infix). **Legacy un-tiered buckets** (`market-data-tick-cefi-{project_id}`,
> no env) are **deprecated** — env-tiered buckets were provisioned + the flat-bucket data migrated in
> [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](../../plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md)
> Phase 2.6; readers fall back to the legacy name during the ≤30-day window only.

The matrix below shows the canonical **template** form (`{env}` = `${DEPLOYMENT_ENV_SHORT}`, e.g. `prd` in prod):

| Service                       | CEFI                                        | TRADFI                                        | DEFI                                        | SPORTS                                        | PREDICTION                                  |
| ----------------------------- | ------------------------------------------- | --------------------------------------------- | ------------------------------------------- | --------------------------------------------- | ------------------------------------------- |
| **instruments-service write** | `instruments-store-cefi-{env}-{project_id}` | `instruments-store-tradfi-{env}-{project_id}` | `instruments-store-defi-{env}-{project_id}` | `instruments-store-sports-{env}-{project_id}` | `instruments-store-pred-{env}-{project_id}` |
| **MTDS raw tick write**       | `market-data-tick-cefi-{env}-{project_id}`  | `market-data-tick-tradfi-{env}-{project_id}`  | `market-data-tick-defi-{env}-{project_id}`  | `market-data-tick-sports-{env}-{project_id}`  | `market-data-tick-pred-{env}-{project_id}`  |
| **MDPS processed write**      | `market-data-tick-cefi-{env}-{project_id}`  | `market-data-tick-tradfi-{env}-{project_id}`  | `market-data-tick-defi-{env}-{project_id}`  | `market-data-tick-sports-{env}-{project_id}`  | `market-data-tick-pred-{env}-{project_id}`  |

Test-mode is just `{env}=test` (e.g. `instruments-store-cefi-test-{project_id}`) — the canonical E2E `-test-` shape, set
via `DEPLOYMENT_ENV=test`. Concrete prod example: `market-data-tick-tradfi-prd-central-element-323112`.

---

## Path layouts — the real divergences

### instruments-service writes

| Asset-group                       | Primary path                                                                              | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| --------------------------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI / TRADFI / DEFI / PREDICTION | `instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet`            | Hive-partitioned by venue. Single file per (date × venue). Legacy fallback: single-file `instruments.parquet` at day prefix.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **SPORTS**                        | `sports_reference/by_date/day={date}/entity={entity}/league={canonical}/{entity}.parquet` | **Per-league hive-partitioned — the partition key IS the canonical league_id** (e.g. `league=EPL`). Four layouts (UAC `gcs_paths.py` `SportsLayout`, resolve via `candidate_parquet_paths(data_type, day, league_id, …)` — NEVER hardcode): `PER_DAY_PER_LEAGUE` (default/most entities; shard atom `(entity, league, day)`); `PER_DAY_PER_SEASON` (`…/entity={F}/season={S}/{F}.parquet` bulk e.g. `player_values` — intra-file `canonical_league` filter); `PER_DAY_BARE` (`…/entity={F}/{F}.parquet` — single-file/day entities like XG/WEATHER OR pre-per-league legacy); `FLAT` (`sports_reference/{F}/{F}.parquet` — date-invariant singletons). Per-league split is what enables per-league query/train/predict, parallel-VM write isolation, and per-`(entity,league,day)` skip-existing. `league=` is numeric ONLY for out-of-universe leagues (no canonical mapping). Entities: `fixtures`, `footystats_odds`, `sfi_leagues`, `progressive_stats`, `teams`, `standings`, `lineups`, `injuries`, `weather`, … No `venue=` level. |

**Consequence**: a service that does `get_instruments_for_date(date, SPORTS)` and reads
`instrument_availability/instruments.parquet` 404s. MDPS `cloud_data_provider.py` (fde923d) now dispatches on
asset_group — SPORTS returns an empty DataFrame with a clear info log; sports candle adapters read raw_tick_data
directly without going through this method.

### MTDS raw tick writes

| Asset-group                                  | Path pattern                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Partition keys                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI                                         | `raw_tick_data/by_date/day={date}/asset_group={ag}/venue={v}/instrument_type={it}/data_type={dt}/ticks.parquet` (canonical; legacy `category={cat}` data coexists on disk per dual-vocab compatibility — see preamble)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | `date × asset_group × venue × instrument_type × data_type` (legacy hive key was `category`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| TRADFI                                       | same as CEFI                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | same                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| DEFI                                         | `raw_tick_data/by_date/day={date}/pipeline_mode={mode}_{source}/asset_group=defi/venue={v}/chain={chain}/instrument_type={it}/data_type={dt}/{canonical_instrument_id}.parquet` (canonical form — `venue` BEFORE `chain`, `pipeline_mode={mode}_{source}` left of `asset_group=`, and the leaf is **one parquet per instrument**, stem == symbolic canonical id == manifest key; legacy chain-before-venue and `category={cat}` data coexists on disk during migration). **⛔ leaf corrected 2026-07-20, doc-reconciliation P1-09:** ~~`ticks.parquet`~~ was a THIRD defi filename form, contradicting both the retired capture-batch `{venue}_{chain}_{capture_ts}.parquet` and the canonical per-instrument stem. Tie-breaker SSOT: [`cross-asset-canonical-target-ssot.md`](cross-asset-canonical-target-ssot.md) §0/§1 pattern #1 + §8. | adds `pipeline_mode=` (left of `asset_group=`) + `chain=` (after `venue=`) levels                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| PREDICTION (legacy, pre-Plan A)              | `raw_tick_data/by_date/day={date}/instrument_type={BTC\|ETH\|FOOTBALL\|OTHER}/data_type={dt}/ticks.parquet`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | **no `category=` or `venue=` level** (POLYMARKET-only for now). Shards by `instrument_type` (= market theme — base_asset).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **PREDICTION (post-Plan A target)**          | `raw_tick_data/by_date/day={date}/asset_group=prediction/venue={v}/data_type=prediction_canonical_question_group/canonical_question_group={cqg}/ticks.parquet`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | **NEW shape per predictions Plan A + multi-axis correction banner (2026-05-06)**: shard atom `(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)`. **`market_id` is a row-level column INSIDE the parquet, NOT a hive-partition shard axis** — HOURLY (24/day), DAILY, ELECTION groups roll up to one manifest row per `(canonical_question_group, day)`; per-market_id detail surfaces by reading parquet rows. Per-market lifecycle bounds enforced. Per-market_id cluster validation MANDATORY (clusters live INSIDE the file): `cluster_extractor=lambda row: row["market_id"]` + `PREDICTION_GROUPS` registry. Plan A reconciler script splits legacy per-base_asset parquets into per-canonical-group parquets.                                                                                                         |
| **SPORTS (legacy, pre-writegate Phase 2.B)** | `raw_tick_data/by_date/day={date}/category={cat}/venue={v}/instrument_type={it}/data_type={dt}/league={league}/ticks.parquet`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | **extra `league=` level** not present in other categories. Example: `.../category=sports/venue=ODDS_API/instrument_type=odds/data_type=odds/league=CHAMPIONSHIP/ticks.parquet`. Coarser-than-target granularity (no fixture_id).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **SPORTS (post-writegate Phase 2.B target)** | `raw_tick_data/by_date/day={date}/asset_group=sports/source={source}/data_type={dt}/league={league}/{F}.parquet` (single shape — fixture-native AND day-aggregate data_types)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | **NEW shape per writegate Phase 2.B + multi-axis correction banner (2026-05-06)**: ALL sports data_types — fixture-native (`ODDS_SNAPSHOT`, `ODDS_MOVEMENT`, `ARBITRAGE`, `FIXTURE_STATS`, `FIXTURE_EVENTS`, `FIXTURE_LINEUPS`, `PLAYER_STATS`, `INJURIES` when fixture-scoped) AND day-aggregate (`STANDINGS`, `LEAGUES`, `TEAMS`, `REFEREES`, `COACHES`, `ROUNDS`) — shard at `(asset_group=sports, source, data_type, league, day)`. **`fixture_id` is a row-level column INSIDE the parquet, NOT a hive-partition shard axis** — `(league, day)` already bounds the per-day fixture set; per-fixture detail surfaces by reading parquet rows. Avoids ~10× manifest inflation. Per-fixture cluster validation MANDATORY (clusters live INSIDE the file): `cluster_extractor=lambda row: row["fixture_id"]` (or `bookmaker` for ODDS\_\*) + `SPORTS_FIXTURE_CLUSTERS` per league-tier. |

> **🔎 SPORTS-CANON ALIGNMENT (2026-06-01):** The path above is the Phase 2.B intermediate target, not the
> post-migration canonical end-state. Two corrections required by the running
> `sports_manifest_canonicalisation_2026_06_01.md` walk: (1) **`source` becomes a COLUMN, not a path key** — the walk
> lifts `data_source=ODDS_API/` / `pipeline_mode=batch_api_football/` path segments into a row-level `source` column so
> all sources co-mingle on the same read path (co-mingled on the SAME hive drop, disambiguated by the row column +
> `SOURCE_PRIORITY`). The path segment `source={source}` shown above is therefore stale post-migration. (2)
> **`pipeline_mode=` is added as a path partition LEFT of `asset_group=`** — the canonical future path is
> `day=/pipeline_mode={mode}/asset_group=sports/venue={v}/data_type={dt}/league={league}/{F}.parquet`. Both corrections
> ride the sports C0 single-walk. SSOT: `sports_manifest_canonicalisation_2026_06_01.md` (CF-3/CF-4) +
> `data_source_provenance_all_asset_groups_2026_06_01.md` Phase 4 +
> `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md` § canonical path confirmation.

**Consequence**: a service that iterates blobs with `list_blobs(prefix='raw_tick_data/by_date/day=.../')` and parses
each blob's path assuming a fixed partition depth (7 segments) sees SPORTS blobs with 8 segments. Historically this
caused `IndexError: string index out of range` during iterator materialization (exact SDK bug still under investigation;
the observable symptom is the error). The fix (MDPS commit 1068ae1) is a `safe_iterate_blobs` helper that per-element
catches IndexError/ValueError/TypeError/AttributeError in `path_parsing.py` — applied at all 4 list_blobs call sites in
MDPS. Any future service reading the same path family MUST use the same pattern.

### MDPS processed candle writes

| Asset-group          | Path pattern                                                                                                                                 | Partition keys                                                                                                                                                                                                                                                                                 |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI / TRADFI / DEFI | `processed_candles/by_date/day={date}/pipeline_mode={mode}/timeframe={tf}/data_type={source_dt}/instrument_type={it}/venue={v}/{id}.parquet` | `date, pipeline_mode, timeframe, data_type (SOURCE type — `derivative_ticker`/`trades`/`book_snapshot_5`/`dex_pool_swaps`/`ohlcv_1m`, NOT the aggregated `deriv_ohlcv_*`), instrument_type, venue`. Bundled-by-underlying writes append `underlying={U}/` and use `ticks.parquet` as the leaf. |
| PREDICTION           | `processed_candles/by_date/day={date}/timeframe={tf}/data_type={dt}/instrument_type={it}/{id}.parquet`                                       | no venue (POLYMARKET implicit); shards by instrument_type                                                                                                                                                                                                                                      |
| **SPORTS**           | `processed/by_date/day={date}/data_type=odds_horizon_bucket/bucketed.parquet`                                                                | **completely different tree** — `processed/` not `processed_candles/`. Single file per date. Bookmaker-time bucketed odds feature artefacts. See `market-tick-data-service/docs/SPORTS_ODDS.md`.                                                                                               |

> **Single-derivation canonical landing (operator-ruled 2026-07-21).** The CEFI/TRADFI/DEFI object path is built ONCE,
> inside `write_candle_parquet`, from the SAME post-derivation coordinates the manifest row uses (renormalized canonical
> id, inferred `instrument_type`, normalised `tf` [24h→1d], SOURCE `data_type`, `pipeline_mode`) via the single builder
> `unified_trading_library.build_canonical_candle_path(...)` (MDPS wrapper
> `output_path_helpers.build_canonical_candle_object_path` / `canonical_writer_shaping.derive_candle_object_path`). The
> path now carries `instrument_type=` (was absent) + `pipeline_mode=` and the **manifest `data_type` axis is the SOURCE
> type** (was the aggregated `mdps_data_type_key`), so **path == manifest on `data_type` by construction** and matches
> the freshness check (`check_shard_freshness` `expected_venues` = SOURCE data_types from `DATA_TYPES_BY_ASSET_GROUP`).
> The `data_type=` kwarg passed to `record_captured` stays on the aggregated `mdps_data_type_key` — it drives the
> schema-contract lookup + the `BUNDLED_DATA_TYPES` cluster gate only, not the stored axis. Existing pre-2026-07-21 rows
> are re-keyed by the separate backward data/manifest migration. SSOT for the shape: `unified-trading-library`
> `PATH_REGISTRY['processed_candles']`.

**Consequence**: MDPS does not produce per-venue candles for SPORTS. Its `dependency_checker.py` `OUTPUT_BUCKETS` map
covers SPORTS only so the dep-check can resolve; the actual processing is handled by the sports adapters
(`adapters/sports/bucket_assignment_adapter.py`, `odds_movement_adapter.py`, etc.) which write to the `processed/` tree.

---

## Dep-checker `UPSTREAM_DEPS` routing

MDPS `dependency_checker.py` (commits f18dd5c + 3d38aef) has two maps:

```python
# Default — CEFI/TRADFI/DEFI fall back to this
UPSTREAM_DEPS: ClassVar = {
    "market-tick-data-service": {
        "bucket_template": "market-data-tick-{category_lower}-{env}-{project_id}",
        "path_template": "raw_tick_data/by_date/day={date}/",
        "required": True,
    },
    "instruments-service": {
        "bucket_template": "instruments-store-{category_lower}-{env}-{project_id}",
        # NOTE: venue={venue} removed 2026-04-20 (3d38aef) — the base-class
        # _format_template_vars never supplies {venue}, so the format() raised
        # KeyError and the dep-check silently resolved to "Missing template var".
        "path_template": "instrument_availability/by_date/day={date}/",
        "required": True,
    },
}

# Per-asset-group override — SPORTS/PREDICTION have different upstream layouts
UPSTREAM_DEPS_BY_CATEGORY: ClassVar = {
    "SPORTS": {
        "instruments-service": {
            "bucket_template": "instruments-store-sports-{env}-{project_id}",  # env-tiered; resolve via resolve_bucket_name()
            # SPORTS writes to sports_reference/, not instrument_availability/.
            # Date-level existence is sufficient for dep-check.
            "path_template": "sports_reference/by_date/day={date}/",
            "required": True,
        },
        # No market-tick-data-service entry — sports processing reads
        # MTDS raw tick data directly via its own adapter layer.
    },
    "PREDICTION": {
        "instruments-service": {
            "bucket_template": "instruments-store-pred-{env}-{project_id}",  # PREDICTION uses 'pred'; env-tiered
            "path_template": "instrument_availability/by_date/day={date}/",
            "required": True,
        },
    },
}
```

Use `check_upstream_data_per_shard(date, category, venue, instrument_type, data_type)` (added in f18dd5c) for runtime
per-shard gating. Opt-in via `--per-shard-check` CLI flag (wired in fde923d).

---

## Known quirks to preserve

1. **SPORTS `category=sports` / `asset_group=sports` is lowercase** in the partition value (legacy `category=sports` and
   canonical `asset_group=sports` both lowercase) while most other hive values (venue, chain, instrument_type) are
   UPPER-CASE. Do not uppercase blindly.
2. **PREDICTION pre-CLOB tarballs may still have `prediction_trades` data_type** — the registry was refactored
   `2026-04-19 (ca246a9)` to use canonical `trades`. Old parquet files still have both; manifest reconciliation handles
   the merge.
3. **DeFi `chain=` partition uses the UAC canonical name** — `ETHEREUM`, `ARBITRUM`, `BASE`, `SOLANA` — NOT aliases.
   MDPS does NOT handle `chain=` in its DependencyChecker; DeFi processing routes through
   `features-service (onchain family)` for chain-specific logic.
4. **MDPS `_list_instrument_files` matches by `data_type=` substring**, not by full partition match. For SPORTS where
   the path has `data_type=odds/` but the orchestrator loops for `data_type=arbitrage_opportunity` etc., the mismatch
   returns 0 files for the mismatched types — they hit the fallback at `_list_instrument_files` line ~223 which accepts
   all parquet files at the date prefix. This is intentional: SPORTS adapters process all available parquet files and
   emit per-data_type output based on row content, not partition path.
5. **GCS list_blobs iterator can raise mid-iteration on certain partition shapes** — ALWAYS wrap
   `list(client.list_blobs(...))` with `safe_iterate_blobs` from `path_parsing.py` (MDPS) or the equivalent pattern in
   your service. Outer try/except is insufficient — it classifies whole-scan as failed and returns empty, silently
   breaking coverage metrics.

---

## When to update this doc

- Any new asset_group added to the system (e.g. if a 6th asset_group like `COMMODITIES` gets carved out separately from
  TRADFI)
- Any new path layout / partition level introduced (new hive segment)
- Any bucket template change (rarely — requires coordinated migration)
- Any service added that reads/writes asset_group-partitioned data (new row in the matrix)

## TradFi tick data restoration (post-cutover)

> **[DELTA 2026-05-22]** **Current state:** TradFi MTDS captures OHLCV-1m (L0) for CME / ICE / NASDAQ / NYSE via
> Databento. L1 (`trades`) and L2 (`tbbo`) data types were collected in two reference windows (May 2023 + Jul 2024) but
> held behind `_DEFERRED_TRADFI_TICK_WINDOW_*` constants in the MTDS handler when the TradFi MVP was collapsed to
> OHLCV-only. **Planned delta:** `tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md` restores the 2-window tick scope
> after May-23 cutover. **Target architecture:** TradFi shard atom
> `(asset_group=tradfi, venue, instrument_type, data_type={trades|tbbo}, day)` — same as CEFI path in the matrix above;
> no extra hive level. Coverage windows: May 2023 + Jul 2024 reference months + rolling live feed via Databento PAYG.
> `mbp_10` (L3) added in a later phase when Databento MBP-10 costs are evaluated.

## Cross-references

- Sports adapter dependency order (api-football T0 + T1 enrichment): `codex/02-data/sports-adapter-dependency-order.md`
- Manifest schema SSOT: `codex/02-data/availability-manifest-and-data-status.md`
- MDPS dep-checker implementation:
  `market-data-processing-service/market_data_processing_service/app/core/dependency_checker.py`
- SPORTS get_instruments_for_date SPORTS branch:
  `market-data-processing-service/market_data_processing_service/app/core/cloud_data_provider.py` lines 107-122 (commit
  fde923d)
- safe_iterate_blobs helper: `market-data-processing-service/market_data_processing_service/app/utils/path_parsing.py`
  (commit 1068ae1)
- Polymarket trades schema:
  `market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/polymarket_adapter.py` (commit
  bc33700 adds `instrument_id`)
- Sports odds / bm_time: `market-tick-data-service/docs/SPORTS_ODDS.md`
- Coverage roadmap (uses this doc): `unified-trading-pm/plans/archive/proper_coverage_roadmap_2026_04_20.plan.md`
- VM tarball deployment: `codex/05-infrastructure/vm-tarball-deployment.md`

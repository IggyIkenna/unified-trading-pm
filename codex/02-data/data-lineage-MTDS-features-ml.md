---
doc_type: codex-ssot
title: Data Lineage — MTDS → MDPS → features-\* → ml-training → ml-inference
summary:
  Single-page data-lineage map MTDS ticks → MDPS candles → features-* → ml-training → ml-inference — per-layer
  bucket/partition paths, SchemaContract keys, the 5-DeFi-type MDPS scope vs bypass types, manifest-driven feature input
  discovery (not path-probe), and the Phase-10 symmetry invariants.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, features-service, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [data-lineage, mtds, mdps, features, ml, data-pipeline, defi]
related:
  [
    availability-manifest-and-data-status.md,
    contracts-scope-and-layout.md,
    bucket-naming-and-config.md,
    partitioning.md,
  ]
created: 2026-04-18
authoritative_for: [MTDS-MDPS-features-ml data-lineage layer map]
referenced_by:
  [
    codex/02-data/defi-data-pipeline.md,
    codex/04-architecture/ml-experiment-lifecycle.md,
    plans/epics/features_and_ml_master.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Data Lineage — MTDS → MDPS → features-\* → ml-training → ml-inference

Status: active Last updated: 2026-05-12 (codex audit D-15 refresh — currency banner cross-link; full rewrite tracked in
ML-14) Owner: data-pipeline agents 3 + 5 Related plan:
`unified-trading-pm/plans/archive/data_pipeline_completion_2026_04_18.plan.md` § Phase 10

> **🟡 PARTIAL STALENESS 2026-05-12 (ML-14 PRE_CUTOVER, slot 8 audit)** — this doc was last revised 2026-04-18,
> predating the 2026-04-25 venue-axis-vocabulary plan (`asset_group` is now the canonical axis, NOT `category`) and the
> 2026-05-11 Bucket-name SSOT (b+) codification (`resolve_bucket_name(cloud=, kind=, asset_group=, env=)` is the only
> legal lookup). The "Conventions" section (above) already cites the canonical `resolve_bucket_name(...)` rule, but the
> per-layer flow sections (Layer 1 MTDS / Layer 2 features / Layer 3 ml-training / Layer 4 ml-inference) still use
> literal `{category}` substitution + pre-SSOT-(b+) bucket-name patterns like
> `market-data-tick-{category}-central-element-323112` / `features-{feature_group}-{category}-central-element-323112` /
> `ml-models-{category}-central-element-323112` / `ml-predictions-{category}-central-element-323112`. The bucket names
> cited inline are READ-the-doc-for-context illustrative only — **the canonical bucket-name SSOT is the
> `resolve_bucket_name(...)` call**; treat the inline `{category}` substitutions as legacy + reconcile against
> `deployment-service/configs/cloud-providers.yaml` + the asset_group hive-key vocabulary (`asset_group=` canonical,
> `category=` legacy on-disk per `market_tick_data_service/raw_tick_hive.py`). Tracked in
> `plans/archive/issues/codex_audit_ml_2026_05_12.md` ML-14; full rewrite pending data-pipeline owner.

## Purpose

Single-page view of how a feature row arrives on disk at ml-training-service input, and how model artifacts /
predictions propagate back. Used to verify Phase 10 symmetry (features read canonical MTDS paths; ml-training reads
canonical feature paths; ml-inference writes canonical prediction paths) without re-running the entire pipeline.

## Conventions

- **Canonical bucket name** — resolved via
  `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(cloud=..., kind=..., asset_group=..., env=...)`
  per **Bucket-name SSOT (b+)** (see CLAUDE.md § "Bucket-name SSOT (b+)"). For ML model artefacts:
  `kind="ml-models-store"`. For ML training artefacts (intermediate): `kind="ml-training-artifacts"` (post Phase 0i
  bucket-name SSOT registration). For ML predictions: paths live UNDER the consumer's bucket, not their own kind. Never
  inline `gs://uts-models-{cloud}/...` or `s3://artifacts/...` (QG STEP 5.69 enforces).
- **Hive partitioning** — `key=value`, not `key-value`. See `partitioning.md`.
- **Manifest shard dims (v9 — column shape current as of 2026-05-30; `MANIFEST_SCHEMA_VERSION = 9` — see SSOT)** —
  `venue, chain, data_type, instrument_type, league_id, timeframe, feature_group, model_family, training_period, strategy_id, client_id, instruction_type, fixture_id, job_id`.
  v5 added `capture_status / error_reason / attempted_at` (honest-coverage). v6 added
  `quote_asset / margin_type / combo_type / leg_weights` (DERIBIT inverse-vs-linear + multi-leg). v7 added `fixture_id`
  (sports per-fixture row column) + `job_id` (ML/strategy/execution experiment-keyed services). v8 adds
  `pipeline_mode / service_emission_state / last_emission_decision_at / expected_window_completeness_fraction` (fraction
  0.0-1.0, not percentage 0-100; renamed from `_pct` per UAC@`76f950a` 2026-05-11). SSOT:
  [`availability-manifest-and-data-status.md`](./availability-manifest-and-data-status.md) § "Schema v8 (current;
  ratified 2026-05-09)".
- **SchemaContract** — every (category, instrument_type, data_type[, timeframe, feature_group]) registered in UAC
  `internal/schemas/contracts.py::CONTRACT_REGISTRY`.
- **Derive-on-read** — `unified_trading_library.canonical.derive_instrument_id()` computes the canonical instrument_id
  from partition context + raw row; not materialised as a disk column.

## Layer 1 — MTDS ticks (source of truth for market microstructure)

Bucket: `market-data-tick-{category}-central-element-323112`

| Category   | Partition path                                                                                                                           | SchemaContract key                                        | Notes                                                                                                                                                                                                                                                                                |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| CeFi       | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=BINANCE-FUTURES/instrument_type=perpetual/data_type=trades/.parquet`                         | `(cefi, perpetual, trades)`                               | Tardis-native columns (exchange, symbol, price, amount)                                                                                                                                                                                                                              |
| CeFi       | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=BINANCE-FUTURES/instrument_type=perpetual/data_type=book_snapshot_5/`                        | `(cefi, perpetual, book_snapshot_5)`                      | L1 + L5 bid/ask                                                                                                                                                                                                                                                                      |
| CeFi       | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=BINANCE-FUTURES/instrument_type=perpetual/data_type=derivative_ticker/`                      | `(cefi, perpetual, derivative_ticker)`                    | funding_rate, mark_price, index_price                                                                                                                                                                                                                                                |
| DeFi       | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=UNISWAP_V3/chain=ETHEREUM/instrument_type=pool/data_type=dex_pool_swaps/`                    | `(defi, pool, dex_pool_swaps)`                            | Pool swaps from The Graph                                                                                                                                                                                                                                                            |
| DeFi       | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=GMX/chain=ARBITRUM/instrument_type=perpetual/data_type=derivative_ticker/`                   | `(defi, perpetual, derivative_ticker)` (added 2026-07-15) | Canonical raw-funding home for ALL perps (GMX on defi axis; DRIFT-SOLANA removed 2026-07-16, operator ruling); funding_rate + ts_event mandatory, open_interest/mark_price/index_price nullable (GMX's native subgraph query has no OI field) — see `defi-data-types-catalog.md` §4a |
| DeFi       | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=AAVE_V3/chain=ETHEREUM/instrument_type=a_token/data_type=lending_indices/`                   | `(defi, a_token, lending_indices)`                        | Reserve state                                                                                                                                                                                                                                                                        |
| TradFi     | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=XNAS/instrument_type=equity/data_type=ohlcv_1m/`                                             | `(tradfi, equity, ohlcv_1m)` (pass-through)               | Databento-native                                                                                                                                                                                                                                                                     |
| TradFi     | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=XCBO/instrument_type=future/data_type=trades/`                                               | `(tradfi, future, trades)`                                | Databento per-leg (bundled symbology)                                                                                                                                                                                                                                                |
| Sports     | `raw_tick_data/by_date/day=YYYY-MM-DD/data_source=ODDS_API/venue=BET365/league_id=PREMIER_LEAGUE/instrument_type=odds/data_type=trades/` | `(sports, odds, trades)` (per Phase 2.2)                  | Bookmaker = `venue`, provider = `data_source`                                                                                                                                                                                                                                        |
| Prediction | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=POLYMARKET/chain=POLYGON/instrument_type=prediction_market/data_type=trades/`                | `(prediction, prediction_market, trades)` (per Phase 1.1) | Polymarket CLOB trades                                                                                                                                                                                                                                                               |

Writer: `unified_trading_library.io.streaming_writer.StreamingParquetWriter(strict=True)` +
`ManifestWriter.write_with_zero_fill`. Any ad-hoc `to_parquet` is a policy violation (lint error post Phase 13.3).

## Layer 2 — MDPS candles (co-located inside MTDS buckets)

Bucket: same as MTDS — `market-data-tick-{category}-central-element-323112` under `processed_candles/` (sports uses
`processed/`).

Path:
`processed_candles/by_date/day=YYYY-MM-DD/timeframe=15s|1m|5m|15m|1h|4h|1d/data_type=trades|book_snapshot_5|.../venue={venue}/instrument_type={type}/.parquet`

SchemaContract key: `(category, instrument_type, source_data_type, ohlcv_{timeframe})` — see plan § 5b.1. TradFi
`ohlcv_1m` is pass-through from Databento; higher timeframes aggregate from 1m. Every write adds a `timeframe` column +
a manifest row with `timeframe` shard populated.

### DeFi MDPS scope (bypass types — CRITICAL)

MDPS processes only 5 DeFi data_types: **`dex_swaps` / `book_snapshot_5` / `fx_rates` / `market_state` / `liquidity`**.
All other DeFi on-chain snapshot data_types are **bypass types** — they flow from specialized MTDS buckets directly to
`features-onchain` WITHOUT going through MDPS. No processed_candles are produced for bypass types.

| Data type                                                                               | Bucket                    | Consumer             | MDPS?     |
| --------------------------------------------------------------------------------------- | ------------------------- | -------------------- | --------- |
| `dex_swaps`                                                                             | `market-data-tick-defi-*` | MDPS → features      | ✅ YES    |
| `vault_share_price`                                                                     | `market-data-tick-defi-*` | features-onchain raw | ❌ BYPASS |
| `lst_rates`                                                                             | `lst-rates-*`             | features-onchain raw | ❌ BYPASS |
| `lending_indices`                                                                       | `lending-indices-*`       | features-onchain raw | ❌ BYPASS |
| `dex_pool_state`                                                                        | `dex-pools-*`             | features-onchain raw | ❌ BYPASS |
| `oracle_prices`                                                                         | various                   | features-onchain raw | ❌ BYPASS |
| `perp_funding`                                                                          | `market-data-tick-defi-*` | features-onchain raw | ❌ BYPASS |
| `derivative_ticker` (defi-axis: GMX, added 2026-07-15; DRIFT-SOLANA removed 2026-07-16) | `market-data-tick-defi-*` | features-onchain raw | ❌ BYPASS |

Code source: `features_service/onchain/app/core/dependency_checker.py` + `mtds_output_config.py` +
`data_loader.py:load_rate_indices/load_oracle_prices`. Confirmed 2026-05-22 (slot-6 investigation).

**Implication for backfill**: launching MDPS VMs for `lst-rates-*` / `dex-pools-*` / `lending-indices-*` buckets
produces unused output. Only `market-data-tick-defi-*` needs an MDPS VM (for `dex_swaps` + other non-bypass types).

SSOT: `plans/active/issues/mdps_defi_multi_bucket_arch_gap_2026_05_22.md` (resolved, Option A confirmed).

## Layer 3 — features-\* services

Bucket: `features-{feature_group}-{category}-central-element-323112`

| Service                   | feature_groups (examples)                                 | Upstream dependency                                                                                | Applicable categories |
| ------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | --------------------- |
| features-delta-one        | `technical_indicators`, `momentum`, `volatility_realized` | MTDS ticks + MDPS `processed_candles`                                                              | CeFi, TradFi          |
| features-volatility       | `realized_vol`, `garch`, `iv_surface`                     | MDPS candles + CeFi options                                                                        | CeFi, TradFi          |
| features-onchain          | `pool_state`, `lending_state`, `oracle_price`             | MTDS DeFi ticks                                                                                    | DeFi only             |
| features-sports           | `pregame_xg`, `pregame_clv`, `ht_xg`, `ht_clv`            | MTDS sports + instruments-service ref                                                              | Sports only           |
| features-calendar         | `session_flags`, `macro_events`, `holiday`                | calendar tables                                                                                    | CeFi, TradFi          |
| features-multi-timeframe  | `tf_momentum_alignment`, `tf_confluence_signals`          | **delta_one output bucket** (reads `day={D}/feature_group={G}/timeframe={T}/{INSTR}.parquet`)      | CeFi, TradFi          |
| features-cross-instrument | `cross_asset_correlation`, `regime_detection`             | **delta_one output bucket** (same layout; calculators need `instrument_id` injected from filename) | CeFi, TradFi          |
| features-commodity        | `commodity_basis`, `backwardation`                        | TradFi commodity futures                                                                           | TradFi only           |

### Features input discovery — manifest-driven (v9), NOT path-probe

**Codified 2026-05-25** — features input discovery reads the MDPS `processed_candles` v9 availability manifest, NOT
lexicographic GCS path probing. This applies to `features-delta-one`, `features-volatility`,
`features-cross-instrument`, and `features-multi-timeframe`.

Pattern:

```python
bucket = resolve_bucket_name(cloud="gcp", kind="market-data", asset_group=asset_group)
index: pd.DataFrame = read_availability_index(bucket)
captured = index[(index["capture_status"] == "captured") & (index["data_type"] == "processed_candles")]
instruments = captured[captured["date"] == target_date]["instrument_id"].tolist()
```

**Why this matters**: path-probe (`list_blobs(max_results=100)`) returned 2019-era DERIBIT instruments
lexicographically, silently giving the wrong instrument universe for any date ≥ 2020. The v8 manifest is date-scoped and
layout-agnostic — immune to MDPS path evolution. Hardcoded legacy paths
(`instrument_type={subdir}/venue=BINANCE-FUTURES/{id}@LIN.parquet`) no longer match canonical MDPS output.

Implementation refs:

- `features-service/features_service/delta_one/app/core/data_loader.py` — `get_available_instruments()`
  (features-service@2965bbda)
- `features-service/features_service/volatility/core/data_loader.py` (features-service@4b7e57b1)
- `features-service/features_service/cross_instrument/` — reads delta_one output manifest (features-service@1d30b8c5)
- Migration plan: `plans/active/features_input_manifest_migration_2026_05_25.md`

### Features output path (canonical — proven in Phase 2 e2e, 2026-05-26)

Output bucket per family: resolved via
`resolve_bucket_name(cloud="gcp", kind="features-{slug}", asset_group=asset_group)` where `slug` is `delta-one` /
`volatility` / `cross-instrument` / `multi-timeframe` etc. `IS_TEST_RUN=true` routes to `-test-` sibling buckets.
`PROTOCOL_DATA_SINK_BUCKET_{AG}` env (delta_one) or bucket property (other families) overrides the sink for E2E test
runs without touching prod.

Canonical output path (features-delta-one, batch mode): `batch/date={date}/{feature_group}/{instrument_id}.parquet`

Cross-instrument output path: `{run_tag}/date={date}/{feature_group}/features.parquet`

**Manifest emission contract (proven 2026-05-26 e2e Phase 2):** every successful write co-emits a v9 manifest row to the
same output bucket's `_index/availability_index.parquet`. The manifest row carries:

- `capture_status="captured"` (or `"empty_confirmed"` if write-gate rejected)
- `service_name="features-service"`
- `feature_group` + `feature_family` + `timeframe` shard dimensions
- `pipeline_mode=PipelineMode.BATCH_*`
- `available_at` = write timestamp

This is enforced by the `ManifestWriter.write()` call in each family's batch_handler. The parquet and manifest row MUST
land in the **same bucket** — divergence (parquet in test, manifest in prod) is a phantom-row bug caught by
`features-service@31414a39` (delta_one) and equivalent fixes in each family.

Writer: `ManifestWriter(service_name="features-service", catalogue_bucket=self.feature_writer.bucket)` where `.bucket`
is the single resolved property shared between the data sink and manifest writer.

Migration refs:

- Write-side manifest divergence fix: `features-service@31414a39` (delta_one)
- E2E validation plan: `plans/active/features_service_e2e_pipeline_test_2026_05_26.md`

## Layer 4 — ml-training-service

Bucket (artifact): `ml-models-{category}-central-element-323112`

Path: `models/{model_family}/{experiment_id}/model.joblib` + sibling
`model_registry/metadata/{model_id}/training-period-YYYY-MM/metadata.json` + `model_registry/manifest.json` rollup.

Reads from: `features-{feature_group}-{category}-...` (all relevant groups for category + instrument + timeframe).
Reader = `ml_training_service.app.core.cloud_feature_provider`.

Manifest emission: `ManifestWriter` row per experiment with shard tuple
`(category, model_family, training_period, strategy_id=None, feature_group=None)` + `model_family` = e.g. `lightgbm`,
`xgboost`. Emits `ML_TRAINING_METRICS` UAC event for val_accuracy / val_auc / val_rmse / feature_count /
training_duration_s.

Lifecycle: `ServiceBootstrap` emits `DEPLOYMENT_STARTED/PROGRESS/COMPLETED/FAILED`.

Run-list SSOT: `ml-training-service/experiments/phase_5d_runlist_2026_04_18.yaml`.

## Layer 5 — ml-inference-service

Bucket: `ml-predictions-{category}-central-element-323112`

Path:
`predictions/by_date/day=YYYY-MM-DD/category={cat}/model_family={fam}/timeframe={tf}/instrument_type={type}/venue={venue}/.parquet`

Reads:

1. Model artifact from `ml-models-{category}-...` via `ModelLoader` (walk-forward — latest training-period strictly
   before inference date).
2. Features from `features-{feature_group}-{category}-...` (same reader as training).

Writes: predictions parquet + manifest row with shard tuple
`(category, model_family, training_period, instrument_type, timeframe)`.

Lifecycle: `ServiceBootstrap` emits lifecycle events; model hot-reload via `ModelPromotionSubscriber` on
`model-promotions-{env}` Pub/Sub topic.

## Symmetry invariants (Phase 10 success criteria)

1. **Every write through strict-mode writer.** `grep -r 'StreamingParquetWriter(strict=False)'` outside the explicit
   legacy list returns zero matches.
2. **Every write emits a manifest row.** Nightly audit job diffs GCS truth vs manifest; 0 drift.
3. **Every service reads canonical paths only.** No legacy `venue=AAVE_V3-ETHEREUM`-style fallbacks.
4. **SchemaContract on read.** `ml-training-service.adapters.feature_data_adapter.read_features()` validates against the
   registered contract; unknown columns fail loud.
5. **`--force` source-replay symmetry.** Re-running any adapter day D with `--force` twice produces byte-identical
   output (modulo lifecycle timestamps). See Phase 13.2.

## Open deltas (tracked in plan)

> **[DELTA 2026-05-22]** **Current state:** Three deltas below remain open from the original implementation. Status
> tracked in `plans/epics/features_and_ml_master.md`. **Planned delta:** Enum extension + strict-mode wire-up +
> SchemaContract registration are sequenced in the epic. **Target architecture:** All items closed; ML training reads
> only from strict-mode-validated feature parquets with registered SchemaContracts.

- `ModelType` in UAC `internal/domain/ml/schemas.py` does not yet include `ISOLATION_FOREST`, `LAMBDARANK`, or
  RL-specific model families — anomaly + ranking + RL cells in the run-list use lightgbm proxies until the enum is
  extended (tracked: `plans/epics/features_and_ml_master.md`).
- MDPS strict-mode writer wire-up is pending (plan § 5b.2); ml-training's read side assumes it once landed.
- Features SchemaContract registration (plan § 5c.1) is pending; training adapter will validate once registered.

## Cross-references

- Availability manifest v4: `availability-manifest-and-data-status.md`
- Contracts scope: `contracts-scope-and-layout.md`
- Bucket naming: `bucket-naming-and-config.md`
- Partitioning: `partitioning.md`
- Sports paths SSOT: UAC `unified_api_contracts.sports.gcs_paths` (`candidate_parquet_paths`,
  `SPORTS_DATA_TYPE_TO_FOLDER`, `SPORTS_DATA_TYPE_LAYOUT`); bucket layout: `per-asset-group-bucket-layouts.md` (sports
  section)
- Prediction paths: `prediction-schema-paths.md`

---
scope: [engineer, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06 -->

> **POST-PLAN REALITY (2026-05-06)** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md)
> BEFORE making code or doc changes informed by this doc. This doc is partially stale: may describe shard atoms,
> manifest behaviour, available_at semantics, or partitioning that's evolving with the writegate-honest-coverage plan
> (per-fixture sports sharding, canonical_question_group for predictions, cluster validation mandatory, three-category
> empty-output decision, available_at per-row write-time). The post-plan-reality doc lists the 10 cross-cutting
> principles codified in workspace `CLAUDE.md` (live=batch, no double SSOT, three-category empty-output decision A/B/C,
> cluster validation mandatory at record_captured, per-row write-time `available_at`, prediction lifecycle timing,
> temporary state must have named successor, per-VM shard isolation, etc.) plus the active plans where the canonical
> post-plan reality is being implemented. If this doc and the active plans disagree, the plans win. If you find a
> contradiction the plans don't address, flag to user — don't decide unilaterally.

# Data Lineage — MTDS → MDPS → features-\* → ml-training → ml-inference

Status: active Last updated: 2026-04-18 Owner: data-pipeline agents 3 + 5 Related plan:
`unified-trading-pm/plans/active/data_pipeline_completion_2026_04_18.plan.md` § Phase 10

## Purpose

Single-page view of how a feature row arrives on disk at ml-training-service input, and how model artifacts /
predictions propagate back. Used to verify Phase 10 symmetry (features read canonical MTDS paths; ml-training reads
canonical feature paths; ml-inference writes canonical prediction paths) without re-running the entire pipeline.

## Conventions

- **Canonical bucket name** — `<domain>-<category>-central-element-323112` (prod project).
- **Hive partitioning** — `key=value`, not `key-value`. See `partitioning.md`.
- **Manifest shard dims (v4)** —
  `venue, chain, data_type, instrument_type, league_id, timeframe, feature_group, model_family, training_period, strategy_id, client_id, instruction_type`.
- **SchemaContract** — every (category, instrument_type, data_type[, timeframe, feature_group]) registered in UAC
  `internal/schemas/contracts.py::CONTRACT_REGISTRY`.
- **Derive-on-read** — `unified_trading_library.canonical.derive_instrument_id()` computes the canonical instrument_id
  from partition context + raw row; not materialised as a disk column.

## Layer 1 — MTDS ticks (source of truth for market microstructure)

Bucket: `market-data-tick-{category}-central-element-323112`

| Category   | Partition path                                                                                                                           | SchemaContract key                                        | Notes                                                   |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------- |
| CeFi       | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=BINANCE-FUTURES/instrument_type=perpetual/data_type=trades/.parquet`                         | `(cefi, perpetual, trades)`                               | Tardis-native columns (exchange, symbol, price, amount) |
| CeFi       | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=BINANCE-FUTURES/instrument_type=perpetual/data_type=book_snapshot_5/`                        | `(cefi, perpetual, book_snapshot_5)`                      | L1 + L5 bid/ask                                         |
| CeFi       | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=BINANCE-FUTURES/instrument_type=perpetual/data_type=derivative_ticker/`                      | `(cefi, perpetual, derivative_ticker)`                    | funding_rate, mark_price, index_price                   |
| DeFi       | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=UNISWAPV3/chain=ETHEREUM/instrument_type=pool/data_type=dex_pool_swaps/`                     | `(defi, pool, dex_pool_swaps)`                            | Pool swaps from The Graph                               |
| DeFi       | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=AAVEV3/chain=ETHEREUM/instrument_type=a_token/data_type=lending_indices/`                    | `(defi, a_token, lending_indices)`                        | Reserve state                                           |
| TradFi     | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=XNAS/instrument_type=equity/data_type=ohlcv_1m/`                                             | `(tradfi, equity, ohlcv_1m)` (pass-through)               | Databento-native                                        |
| TradFi     | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=XCBO/instrument_type=future/data_type=trades/`                                               | `(tradfi, future, trades)`                                | Databento per-leg (bundled symbology)                   |
| Sports     | `raw_tick_data/by_date/day=YYYY-MM-DD/data_source=ODDS_API/venue=BET365/league_id=PREMIER_LEAGUE/instrument_type=odds/data_type=trades/` | `(sports, odds, trades)` (per Phase 2.2)                  | Bookmaker = `venue`, provider = `data_source`           |
| Prediction | `raw_tick_data/by_date/day=YYYY-MM-DD/venue=POLYMARKET/chain=POLYGON/instrument_type=prediction_market/data_type=trades/`                | `(prediction, prediction_market, trades)` (per Phase 1.1) | Polymarket CLOB trades                                  |

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

## Layer 3 — features-\* services

Bucket: `features-{feature_group}-{category}-central-element-323112`

| Service                   | feature_groups (examples)                      | Upstream dependency             | Applicable categories |
| ------------------------- | ---------------------------------------------- | ------------------------------- | --------------------- |
| features-delta-one        | `price_return`, `momentum`, `microstructure`   | MTDS ticks + MDPS candles       | CeFi, TradFi          |
| features-volatility       | `realized_vol`, `garch`, `iv_surface`          | MDPS candles + CeFi options     | CeFi, TradFi          |
| features-onchain          | `pool_state`, `lending_state`, `oracle_price`  | MTDS DeFi ticks                 | DeFi only             |
| features-sports           | `pregame_xg`, `pregame_clv`, `ht_xg`, `ht_clv` | MTDS sports + URDI ref          | Sports only           |
| features-calendar         | `session_flags`, `macro_events`, `holiday`     | calendar tables                 | CeFi, TradFi          |
| features-multi-timeframe  | `mtf_trend`, `mtf_alignment`                   | MDPS candles (all tfs)          | CeFi, TradFi, DeFi    |
| features-cross-instrument | `basis`, `spread`, `lead_lag`                  | MDPS candles across instruments | CeFi, TradFi          |
| features-commodity        | `commodity_basis`, `backwardation`             | TradFi commodity futures        | TradFi only           |

Writer: identical pattern — `StreamingParquetWriter(strict=True)` + `ManifestWriter.write_with_zero_fill`, with
`feature_group` populated as a shard column.

Path:
`features/by_date/day=YYYY-MM-DD/category={cat}/feature_group={group}/timeframe={tf}/venue={venue}/instrument_type={type}/.parquet`

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
3. **Every service reads canonical paths only.** No legacy `venue=AAVEV3-ETHEREUM`-style fallbacks.
4. **SchemaContract on read.** `ml-training-service.adapters.feature_data_adapter.read_features()` validates against the
   registered contract; unknown columns fail loud.
5. **`--force` source-replay symmetry.** Re-running any adapter day D with `--force` twice produces byte-identical
   output (modulo lifecycle timestamps). See Phase 13.2.

## Open deltas (tracked in plan)

- `ModelType` in UAC `internal/domain/ml/schemas.py` does not yet include `ISOLATION_FOREST`, `LAMBDARANK`, or
  RL-specific model families — anomaly + ranking + RL cells in the run-list use lightgbm proxies until Agent 1 extends
  the enum.
- MDPS strict-mode writer wire-up is Agent 3's scope (plan § 5b.2); ml-training's read side assumes it once landed.
- Features SchemaContract registration (plan § 5c.1) is Agent 3's scope; training adapter will validate once registered.

## Cross-references

- Availability manifest v4: `availability-manifest-and-data-status.md`
- Contracts scope: `contracts-scope-and-layout.md`
- Bucket naming: `bucket-naming-and-config.md`
- Partitioning: `partitioning.md`
- Sports paths: `sports-schema-paths.md`
- Prediction paths: `prediction-schema-paths.md`

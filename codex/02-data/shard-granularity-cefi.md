---
doc_type: codex-ssot
title: CeFi shard granularity — instrument_type × quote_asset × margin_type (v6) + cluster validation
summary:
  CeFi manifest v6 shard key adds quote_asset/margin_type/combo_type/leg_weights, splitting DERIBIT inverse (USD) vs
  linear (USDC/USDT) options into separate chain-bundle paths; cluster coverage is the 4th write-gate pillar.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [cefi, manifest, shard-granularity, deribit, quality-gates, data-correctness]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/partitioning.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/06-coding-standards/validation-and-errors.md,
  ]
created: 2026-04-23
authoritative_for:
  [
    CeFi options/futures chain shard key v6 (quote_asset/margin_type/combo_type/leg_weights),
    CeFi bundle cluster-validation write-gate pillar,
  ]
referenced_by:
owner:
last_reviewed: 2026-05-17
code_refs:
---

# CeFi shard granularity — instrument_type × quote_asset × margin_type (v6) + cluster validation

<!-- MULTI_AXIS_CORRECTION_2026_05_06 -->

> **Multi-axis correction (2026-05-06)** — shard atoms vs display axes (row-level columns) per asset_group are the SSOT
> in
> [`availability-manifest-and-data-status.md`](./availability-manifest-and-data-status.md#multi-axis-correction-banner-canonical).
> See that doc for the full per-asset-group shard-atom matrix (sports / prediction / cefi options-futures / DeFi chain /
> ML+strategy+execution job_id / TradFi EVENT_CONTRACT).

**Status:** v6 columns (`quote_asset` / `margin_type` / `combo_type` / `leg_weights`) active as of 2026-04-23 (manifest
schema v6 shipped). Current overall schema is **v9** (`MANIFEST_SCHEMA_VERSION = 9` in UTL `manifest_writer.py`) — v7
added `fixture_id` (sports per-fixture) + `job_id` (ML / strategy / execution experiment-keyed services); v8 added
`pipeline_mode` + `service_emission_state` + `last_emission_decision_at` + `expected_window_completeness_pct`; v9 added
`source` (universal provider tag, 2026-05-30); the v6 CeFi columns described in this doc are unchanged under v7/v8/v9.

> **[DELTA 2026-06-01]** **Current state:** `MANIFEST_SCHEMA_VERSION = 9` (code constant rolled 2026-05-30). Data-side
> migration target is 100% of production rows at v9. The Phase 2.2 single-walk migration
> (`plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`) is in progress as a per-AG L3 walk rider. **Target
> architecture:** 100% of production rows at v9.

Cluster validation as 4th write-gate pillar in progress (writegate Phase 1A + 2.B). **SSOT:**
[availability-manifest-and-data-status.md](./availability-manifest-and-data-status.md) for the canonical schema-version
constant + full column list; this doc is the CeFi-specific v6 column rollout reference.
`unified-trading-pm/plans/archive/manifest_schema_v6_quote_margin_combo_2026_04_23.plan.md` +
`unified-trading-pm/plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`. **Related:**
[partitioning.md](./partitioning.md),
[04-architecture/shard-level-failure-isolation.md](/codex/04-architecture/shard-level-failure-isolation.md),
[06-coding-standards/validation-and-errors.md](/codex/06-coding-standards/validation-and-errors.md).

## Problem v6 solves

Pre-v6 the CeFi chain-bundle shard key was `(venue, date, data_type, instrument_type, underlying)`. Example — DERIBIT
options chain: a single `BTC.parquet` file held BOTH:

- `BTC-29DEC25-100000-C` — coin-margined (inverse), USD-settled
- `BTC_USDC-29DEC25-100000-C` — USDC-margined (linear), USDC-settled

Row concatenation lost the disambiguation and broke downstream strategies that treat inverse and linear as separate
instruments.

## v6 shard key matrix

| instrument_type                           | data_type                                                        | Shard key                                                                   | Path shape                                                                                             |
| ----------------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `PERPETUAL`                               | `trades`, `book_snapshot_5`, `derivative_ticker`, `liquidations` | `(venue, date, dt, instrument_id)`                                          | `.../instrument_type=perpetual/data_type=.../{instrument_id}.parquet`                                  |
| `SPOT_PAIR`                               | `trades`, `book_snapshot_5`                                      | `(venue, date, dt, instrument_id)`                                          | `.../instrument_type=spot_pair/data_type=.../{instrument_id}.parquet`                                  |
| `OPTION` → `options_chain`                | `trades`                                                         | `(venue, date, options_chain, underlying, quote_asset, margin_type)` bundle | `.../instrument_type=options_chain/data_type=trades/underlying={U}/quote={Q}/margin={M}/ticks.parquet` |
| `FUTURE` (multi-symbol) → `futures_chain` | `trades`                                                         | `(venue, date, futures_chain, underlying, quote_asset, margin_type)` bundle | `.../instrument_type=futures_chain/data_type=trades/underlying={U}/quote={Q}/margin={M}/ticks.parquet` |

COMBO rows (call spreads, iron condors, etc.) live INSIDE the parent chain bundle — they are distinguished by
`combo_type != ""` and populated `leg_weights` on the manifest row, not by a separate `instrument_type`.

## Manifest v6 columns (added over v5)

Four new string columns on `AvailabilityRecord`:

| Column        | Default | Example values                                                                   |
| ------------- | ------- | -------------------------------------------------------------------------------- |
| `quote_asset` | `""`    | `"USD"`, `"USDT"`, `"USDC"`, `"BTC"`, `"ETH"`, `"KRW"`                           |
| `margin_type` | `""`    | `"inverse"` (coin-margined), `"linear"` (stable-margined), `""` (spot / unknown) |
| `combo_type`  | `""`    | `"call_spread"`, `"iron_condor"`, `"butterfly"`, `"calendar_spread"`, `""`       |
| `leg_weights` | `""`    | JSON: `[{"instrument_id":"BTC-26DEC25-100000-C","qty":1}, ...]`                  |

Legacy v1–v5 parquets are read with all four columns backfilled to `""` — same compat pattern used for v4→v5
`capture_status` rollout.

## Venue-symbol parser matrix

`derive_settlement_dimensions(venue, symbol, instrument_type)` — canonical mapping in
[tardis_shared.py](../../../market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py)
— extracts `(quote_asset, margin_type)` per row.

| Venue                    | Symbol pattern                        | quote                                              | margin      |
| ------------------------ | ------------------------------------- | -------------------------------------------------- | ----------- |
| DERIBIT                  | `BTC-*` / `ETH-*` (no `_` before `-`) | `USD`                                              | `inverse`   |
| DERIBIT                  | `BTC_USDC-*`, `ETH_USDT-*`            | `USDC` / `USDT`                                    | `linear`    |
| BINANCE-FUTURES          | `*USDT`, `*USDC`                      | `USDT` / `USDC`                                    | `linear`    |
| BINANCE-FUTURES          | `*USD_PERP`, `*USD_{YYMMDD}`          | `USD`                                              | `inverse`   |
| BYBIT                    | `*USDT`, `*USDC`, `*PERP`             | `USDT` / `USDC` / `USDC`                           | `linear`    |
| BYBIT                    | `*USD` (no T)                         | `USD`                                              | `inverse`   |
| OKX-SWAP                 | `*-USDT-SWAP`, `*-USDC-SWAP`          | `USDT` / `USDC`                                    | `linear`    |
| OKX-SWAP                 | `*-USD-SWAP`                          | `USD`                                              | `inverse`   |
| HYPERLIQUID              | all perps                             | `USDC`                                             | `linear`    |
| ASTER                    | all perps                             | per-symbol real quote (`USDT`, tail `USD1`/`USDC`) | `linear`    |
| CME / CBOE               | `ESM26`, `VX-21JAN26-20-C`            | `USD`                                              | `linear`    |
| COINBASE-SPOT / OKX-SPOT | `BTC-USD`, `BTC-USDT`                 | quote                                              | `""` (spot) |
| BINANCE-SPOT             | `btcusdt` (lowercase concat)          | quote                                              | `""` (spot) |
| UPBIT                    | `KRW-BTC` (quote-first)               | `KRW`                                              | `""` (spot) |

Unknown venues or ambiguous symbols return `("", "")` — the shard falls back to the v5 path shape without the nested
`quote=`/`margin=` segments.

## Downstream implications

1. **Pre-flight skip logic.** Keys on `(venue, date, data_type)` as before; finer granularity flows in naturally as v6
   manifest rows accumulate. No change required in consumers that merely check "did this date get any data for this
   venue/data_type".

2. **Strategy / risk consumers.** Any strategy that holds DERIBIT BTC options previously fed from `BTC.parquet` now
   reads from one of two paths (`underlying=BTC/quote=USD/margin=inverse/...` or
   `underlying=BTC/quote=USDC/margin=linear/...`). Strategies that care about only one margin flavour get a cheaper
   read; strategies that span both must `UNION` the two paths. The manifest row carries `quote_asset` and `margin_type`
   so queries can filter by margin type cleanly.

3. **Legacy parquets.** Existing `BTC.parquet` DERIBIT bundles contain a mix of inverse and linear rows. The one-off
   migration script
   [`migrate_deribit_margin_split_v6.py`](../../../market-tick-data-service/market_tick_data_service/scripts/migrate_deribit_margin_split_v6.py)
   row-splits them into v6 paths. The legacy file is NOT deleted — only tagged for removal in a follow-up sweep once v6
   readers are validated (trivial rollback).

4. **`rebuild_cefi_manifest.py`** recognises all three layouts (v6 chain, legacy `underlying=` sub-path, Tardis
   canonical `{stem}.parquet`) — see `parse_hive_path`.

## Cluster validation as 4th write-gate pillar (post-2026-05-06)

CeFi options/futures bundles (`options_chain` / `futures_chain` data_types) are now subject to the **mandatory cluster
validation pillar** at `ManifestWriter.record_captured` per writegate plan Phase 1A. This is the 4th pillar of the
write-gate quartet (row count > 0; NaN ratio < threshold; schema matches contract; **cluster coverage ≥ expected**).

### What this means for CeFi bundles

Every `record_captured` call for `data_type ∈ {options_chain, futures_chain}` REQUIRES two new kwargs:

```python
manifest_writer.record_captured(
    row_key={"venue": "CME", "data_type": "options_chain", "underlying": "ES",
             "day": "2026-01-05", "instrument_type": "options_chain"},
    df=es_options_df,
    data_type="options_chain",
    expected_root_clusters=UAC.OPTIONS_CLUSTERS["ES.OPT"],   # ES.OPT 11-cluster taxonomy
    cluster_extractor=lambda row: re.match(r"^(E[1-5]A|EW[1-4]|EOM|ES)", row["symbol"]).group(0),
)
```

UTL guard raises `MissingClusterValidationError` if these kwargs are absent for a bundled `data_type`. **QG STEP 5.64
statically walks every `record_captured(` callsite and asserts the kwargs are passed when the literal data_type is
bundled** — fails CI if missing.

### Cluster registries in UAC (writegate Phase 1B)

| data_type       | Registry (UAC)     | Cluster extractor                                                              | Notes                                                                                                                                                                                |
| --------------- | ------------------ | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `options_chain` | `OPTIONS_CLUSTERS` | regex on symbol prefix → `(E[1-5]A\|EW[1-4]\|EOM\|ES)` for ES.OPT 11-cluster   | Lifted from instruments-service `reference_data/options_cluster_lookup.py`; registry has `{cluster: min_rows}` per root.                                                             |
| `futures_chain` | `FUTURES_CLUSTERS` | derived from `raw_symbol` via UTL helper `derive_expiry_bucket(symbol, today)` | ES + MES seeds; per-root spreads + butterflies. **Gap**: Databento weekly-series prefix needs `DatabentoClassification.root_cluster: str` UAC enrichment (writegate Phase 2.B todo). |

### Bundle row-count gate (existing, complementary)

Earlier per-bundle row-count > 0 check (pillar 1) catches "source returned empty bundle"; cluster validation (pillar 4)
catches "source returned partial bundle missing some expected root clusters" (e.g. ES.OPT 18 dates with single-parent
fills passing manifest as `captured` — the 2026-05-06 reference incident). Both pillars run on every `record_captured`.

### COMBO row treatment (unchanged)

COMBO rows live INSIDE the parent chain bundle; cluster validation runs on the bundle as a whole. `combo_type != ""`
rows participate in the cluster count for their parent root.

### Three-category empty-output decision applies (post-2026-05-06)

Per workspace CLAUDE.md `§ Three-category empty-output decision` +
[`06-coding-standards/validation-and-errors.md` §1](/codex/06-coding-standards/validation-and-errors.md), every
empty-output result for a CeFi bundle adapter resolves to one of:

- **A. Honest absence** — source returned 0 ticks for the requested window → `record_empty(row_key, attempted_at)`.
- **B. Upstream timestamp bias** — source returned ticks; ALL fall outside the requested day →
  `record_failed(UpstreamTimestampBiasError(...))`. Paired upstream MTDS partitioner-validation fix at
  `raw_tick_hive.py`.
- **C. Mid-process malformed fields** → `record_failed(MalformedTickFieldError(...))`.

The `_create_empty_output()` placeholder method is BANNED (writegate Phase 2.A deletes from `base_adapter`). NO silent
NaN placeholder rows.

### `available_at` per row (post-2026-05-06)

Every CeFi bundle parquet row carries `available_at = tick.timestamp + scrape_latency` (per
`UAC.SOURCE_PRIORITY[(asset_group, data_type)]` top entry). UTL helper:
`unified_trading_library.availability_stamping.stamp_available_at_tick_plus_latency(df, ts_col, source_key)`.
`record_captured` calls `assert_available_at_present(df)` internally; missing or null `available_at` →
`LookaheadBiasError`.

---

## Non-goals (for v6)

- Does NOT extend `build_instrument_id` with `quote_asset` / `margin_type` kwargs. Canonical IDs — under the decided
  cefi grammar `VENUE:TYPE:BASE-QUOTE@MARGIN[-YYYYMMDD][-STRIKE-C|P]`, e.g.
  `DERIBIT:OPTION:BTC-USD@INV-20251226-100000-C` (DERIBIT always carries the quote; inverse coin-margined ⇒ `@INV`) —
  stay stable for backward compatibility of the catalogue. Disambiguation is load-bearing at the _shard path_ +
  _manifest row_ layer, not in the ID. (Follow-up: Phase 2c of the v6 plan — deferred.)
- Does NOT touch sports / prediction / DeFi manifests at the v6 column level. v6 is additive for them — the four new
  columns are simply `""`.

**However, post-2026-05-06 writegate plan extends related concepts to all asset groups**:

- **Sports per-fixture bundles** (`ODDS_SNAPSHOT` / `ODDS_MOVEMENT` / `ARBITRAGE`): cluster validation MANDATORY with
  `cluster_extractor=lambda row: row["bookmaker"]` and `SPORTS_FIXTURE_CLUSTERS` per league-tier. Shard atom is
  `(asset_group=sports, source, data_type, league_id, day)` — `fixture_id` is a row-level column NOT a shard axis (per
  Q1 resolution); cluster validation enforces per-fixture coverage within the parquet.
- **Predictions** (`prediction_canonical_question_group`): cluster validation MANDATORY with
  `cluster_extractor=lambda row: row["market_id"]` and `PREDICTION_GROUPS` per cadence (HOURLY=24/day, DAILY=1/day,
  etc.). Per-market lifecycle bounds.
- **DeFi**: chain-specific shards (`chain` first-class axis); no bundle structure today, so cluster validation N/A
  unless a per-chain bundled data_type emerges in future.

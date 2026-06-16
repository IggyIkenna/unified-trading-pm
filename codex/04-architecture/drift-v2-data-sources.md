---
scope: [engineer, admin]
title: Drift V2 Data Sources — Velocity Data API as Canonical Historical + Live Path
type: architecture
status: living
last_reviewed: 2026-06-01
owner: defi-adapters
---

# Drift V2 Data Sources — Velocity Data API as Canonical

> **SSOT for Drift V2 perpetual DEX data ingestion.** Created 2026-06-01 from
> `plans/archive/solana_basis_trading_mvp_2026_06_01.plan.md` Phase 1 (Drift V2 historical ingester shipped at
> mtds@0f70f376 + 7 new UAC canonical data types at uac@f26097f9 + InstrumentType.DEX_POOL at uac@9ad04ab0). Replaces
> the Helius sig-walking path (Bug-D saga 2026-05-29 → 2026-06-01) which is OBSOLETE for Drift V2 historical needs.

## Why this doc exists

The Helius sig-index walker path (`build_drift_v2_sig_index.py` + 6293-part 28GB parquet index +
`mtds-solana-drift-backfill` VM gap-fill loops) hit a hard wall: ~6.4M signatures/day at the Drift V2 program level —
intractable for per-fill backfill in any reasonable wall-clock. Eight bug iterations from 2026-05-29 → 2026-06-01 chased
symptoms of that wall (OOMs, JSON-decode-error retry loops, schema-drift row-key bugs, bucket-name SSOT drift).

Root cause discovery 2026-06-01: nobody verified what `data.api.drift.trade` actually exposes BEFORE building the Helius
integration. **It exposes everything we need at the free tier with zero gap.** This doc is the canonical record of what
the Velocity Data API provides and how MTDS consumes it.

## Velocity Data API surface (`data.api.drift.trade`)

**Endpoint base**: `https://data.api.drift.trade` **Auth**: NONE for free tier endpoints (open public API) **Rate
limit**: Unknown / unprobed; add backoff on 429 in production loops **OpenAPI spec**:
`https://data.api.drift.trade/openapi.json` (54 endpoints documented, probed 2026-06-01)

### Per-market historical endpoints (the canonical MVP path)

| Endpoint shape                                   | Format | Pagination          | Notes                                                                                                         |
| ------------------------------------------------ | ------ | ------------------- | ------------------------------------------------------------------------------------------------------------- |
| `/market/{symbol}/fundingRates/{Y}/{M}/{D}`      | JSON   | `?page=N` 1-indexed | ~24 rows/day per market; full historical coverage verified back to **2024-06-01**                             |
| `/market/{symbol}/trades/{Y}/{M}/{D}?format=csv` | CSV    | `?page=N` 1-indexed | 5K rows per page; total 5K-200K rows/day per market depending on volume; JSON format errors at 500 — CSV only |
| `/market/{symbol}/swaps/{Y}/{M}/{D}`             | JSON   | `?page=N` 1-indexed | Swap events; secondary use case (out of MVP scope)                                                            |
| `/market/{symbol}/deposits/{Y}/{M}/{D}`          | JSON   | `?page=N` 1-indexed | Deposit/withdrawal events (out of MVP scope)                                                                  |
| `/market/{symbol}/insuranceFund/{Y}/{M}/{D}`     | JSON   | `?page=N` 1-indexed | Insurance fund stake events (out of MVP scope)                                                                |

### Live-mode endpoints (most-recent rows)

| Endpoint shape                                        | Format | Notes                                                                                                                                                                 |
| ----------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/market/{symbol}/fundingRates` (no date suffix)      | JSON   | Most-recent funding row(s); paginates same shape                                                                                                                      |
| `/market/{symbol}/trades?format=csv` (no date suffix) | CSV    | Most-recent trade rows                                                                                                                                                |
| `/stats/markets`                                      | JSON   | Snapshot of all markets with `funding_rate_24h/7d/30d` aggregates — used by legacy `solana_defi_handler._collect_drift` live path for non-basis Solana DeFi protocols |

### Endpoints that return 403 on free tier (NOT a paid tier signal)

The OpenAPI spec lists `/amm/bidAskPrice`, `/amm/oraclePrice`, `/amm/openInterest`, etc. Probing returns
`x-amzn-errortype: ForbiddenException` + `x-cache: Error from cloudfront` — **AWS API Gateway's "no matching route"
response**, identical to `/pricing`, `/docs`, `/auth`, and any other undefined path. Pricing investigation 2026-06-01
found **NO public paid tier exists**. Interpretation: AMM endpoints appear in OpenAPI spec but are **NOT deployed** on
the public gateway. For MVP, derive AMM-level data from `perp_funding` row columns (`oraclePriceTwap`, `markPriceTwap`,
`baseAssetAmountWithAmm`).

## Schema translation — Velocity API → UAC canonical

Raw API rows use camelCase; the `DriftV2HistoricalIngester` translates to snake_case per UAC canonical field names. Key
mappings (canonical `perp_funding` schema per UAC):

| Velocity API field       | UAC canonical field       | Notes                                                |
| ------------------------ | ------------------------- | ---------------------------------------------------- |
| `ts` (epoch s)           | `timestamp`               | UTC; cast to `pd.Timestamp(tz='UTC')`                |
| `fundingRate`            | `funding_rate`            | Float; per-hour rate                                 |
| `oraclePriceTwap`        | `oracle_price_twap`       | Float USD; TWAP over funding interval                |
| `markPriceTwap`          | `mark_price_twap`         | Float USD; TWAP over funding interval                |
| `baseAssetAmountWithAmm` | `open_interest_base`      | Signed; positive = net-long, negative = net-short    |
| `cumulativeFundingRate*` | (derived in features-svc) | Cumulative carry — features-onchain-defi job derives |

For `perp_trades` (CSV format, ~5K rows/page):

| Velocity API column      | UAC canonical field                |
| ------------------------ | ---------------------------------- |
| `ts`                     | `timestamp`                        |
| `marketIndex`            | (drop — derive from market symbol) |
| `direction`              | `side` (`long`/`short`)            |
| `baseAssetAmountFilled`  | `base_amount_filled`               |
| `quoteAssetAmountFilled` | `quote_amount_filled`              |
| `oraclePrice`            | `oracle_price`                     |

## MTDS handler implementation

**Class**: `DriftV2HistoricalIngester` **Location**: `market_tick_data_service/cli/handlers/...` (or scripts/ for the
dedicated backfill CLIs) **Entry points**:

- Batch:
  `python -m market_tick_data_service.scripts.backfill_drift_v2_historical \     --markets SOL-PERP --start 2024-06-01 --end 2026-06-01 --data-types funding,trades`
- Live: same script with `--live --continuous --interval-seconds 3600 --data-types funding` (per CLAUDE.md "Live = batch
  (CRITICAL)" hard rule — same handler, same GCS partition path, same schema)

### Output paths (per CLAUDE.md bucket-name SSOT + asset-group vocabulary)

```
gs://market-data-tick-defi-prd-${PROJECT_ID}/raw_tick_data/by_date/day={Y-M-D}/
    pipeline_mode={batch|live}/asset_group=defi/venue=DRIFT/chain=SOLANA/
    instrument_type=perpetual/data_type={perp_funding|perp_trades}/ticks.parquet
```

`pipeline_mode=` partition is the canonical batch/live distinguisher per
`codex/02-data/pipeline-mode-and-batch-live-reconciliation.md`. The handler MUST resolve `pipeline_mode` via the UTL
resolver, never hardcode (per `defi_manifest_canonicalisation_2026_06_01.md` § A).

### Manifest emission (per CLAUDE.md manifest + honest absence)

- Day with rows → `record_captured(...)` (cluster validation enforced per CLAUDE.md hard rule)
- Day with zero rows but day is within `[2024-06-01, today]` and market is post-launch →
  `record_empty(reason= EmptyConfirmedReason.SOURCE_RETURNED_ZERO)` (active SOL-PERP has trades every day; a zero would
  be a Velocity API glitch worth flagging)
- Day pre-Drift-V2-launch (before 2022-11-04) → `record_empty(reason= EmptyConfirmedReason.EXPECTED_PRE_VENUE_LAUNCH)` —
  DRIFT-SOLANA launch date is in UAC `DEFI_VENUE_LAUNCH_DATES` (per `defi_manifest_canonicalisation_2026_06_01.md` § A2)
- Velocity API HTTP error (5xx, timeout, DNS) → `record_failed(error_reason=<typed>)` — **never** swallow to
  `record_empty` (per CLAUDE.md A7 fetch-failure swallow rule, mtds@d3d26f56)

## Coverage / freshness

| Window                                    | Velocity Data API state                                                                                       |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Drift V2 launch (2022-11-04) → 2025-01-08 | S3 archive `drift-historical-data-v2` (legacy; UAC `_DRIFT_S3_ARCHIVE_URL_TEMPLATE`) + Velocity API both work |
| 2025-01-08 → ~2026-04-01                  | Velocity API per-day endpoints (free tier covers this fully)                                                  |
| ~2026-04-01 → present                     | Velocity API per-day endpoints lag ~2 months on the free tier; live-mode `/stats/markets` snapshot covers gap |
| Live (most-recent rows)                   | `/market/{symbol}/fundingRates` (no date) + `/market/{symbol}/trades?format=csv` (no date)                    |

## Composes with

- `codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — Drift IS adapter populates
  `source_archive_url_template` for the S3 archive (per-instrument per-day pattern); the **Velocity Data API base URL**
  lives in UAC's `SOLANA_DEFI_PROTOCOLS["drift"]["api_url"]` (venue-wide, one host serves all markets) and is accessed
  via the public `get_solana_protocol_url("drift", "api_url")` helper. Both IS adapter and MTDS
  `DriftV2HistoricalIngester` (mtds@081ff1cf) use this canonical helper — no hardcoded URLs anywhere.
- `codex/04-architecture/solana-defi-coverage.md` — Solana DeFi adapter registry; DRIFT-SOLANA row references this doc
  for the Velocity Data API path
- `codex/02-data/defi-data-types-catalog.md` — canonical data_type definitions including new types from this MVP:
  `perp_trades`, `perp_mark_oracle`, `perp_open_interest`, `dex_pool_state`, `dex_orderbook`, `dex_quote`, `dex_trades`
- `codex/02-data/honest-absence-downstream-handling.md` — `EXPECTED_PRE_VENUE_LAUNCH`, `SOURCE_RETURNED_ZERO`, typed
  error reasons
- `plans/archive/solana_basis_trading_mvp_2026_06_01.plan.md` — full design history + Bug-D saga context

## What this doc replaces

- The implicit "use Helius for Drift V2 historical" assumption that drove the Bug-D saga (sig-index walker, 28GB
  parquet, 8-bug saga). The sig-index infrastructure REMAINS in the MTDS repo as cold infrastructure for future use
  (e.g., independent backfill of `tradeRecords` outside Velocity API rate limits) but is NOT on any critical path.
- `plans/active/issues/bug_d_prime_drift_backfill_2026_05_31.md` — SUPERSEDED 2026-06-01 (banner in issue doc).

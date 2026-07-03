---
doc_type: plan
title: UAC Canonical Normalization Master
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, market-data-processing-service, market-tick-data-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-14'
overview: 'Single consolidated plan for UAC canonical normalization: (1) minimal-split layout by data type (options, futures, perpetuals, cefi spot, tradfi, defi, sports); (2) common cross-domain (OHLCV, instruments, rate limits); (3) infrastructure canonical layer (CloudStorage, OLAPTable — cloud-agnostic names mapped to GCP/AWS raw); (4) features interface and UFCL/UTL consolidation; (5) provider manifest expansion. Supersedes the three separate plans.'
todos:
- {id: nesting-sports-market, content: 'Move sports market data (odds, live, bookmaker, arbitrage) to canonical/market/sports/', status: pending}
- {id: nesting-sports-reference, content: 'Move sports reference data (mappings, fixture, events, injury, lineup, player_stats) to canonical/reference/sports/', status: pending}
- {id: nesting-sports-execution, content: 'Move BetOrder, BetExecution to canonical/execution/sports/', status: pending}
- {id: nesting-sports-errors, content: Move sports errors to canonical/errors/sports/; _venue_errors_defi to canonical/errors/defi/, status: pending}
- {id: nesting-tradfi, content: 'Create canonical/market/tradfi/ (bonds, fx, commodities, stocks — one bucket); canonical/reference/tradfi/', status: pending}
- {id: nesting-options, content: Create canonical/market/options/ (CeFi + TradFi options); move options normalizers, status: pending}
- {id: nesting-futures, content: Create canonical/market/futures/ (CeFi + TradFi futures); move derivative_tickers futures subset, status: pending}
- {id: nesting-perpetuals, content: 'Create canonical/market/perpetuals/ (CeFi only); move derivative_tickers perps, funding, liquidations', status: pending}
- {id: nesting-defi, content: 'Create canonical/market/defi/, reference/defi/, derived/defi/; move Pyth, DeFiLlama, Glassnode, Arkham', status: pending}
- {id: nesting-common, content: 'Create canonical/common/ (ohlcv, instruments, rate_limits) — cross-domain types', status: pending}
- {id: nesting-derived-sports, content: 'Create canonical/derived/sports/ (Footystats, Understat, _features_*); canonical/derived/derivatives/ (VolSurface)', status: pending}
- {id: infra-canonical, content: 'Create canonical/infrastructure/ with CloudStorage, OLAPTable, SecretStore, MessageQueue, ContainerRegistry, mappings.py', status: pending}
- {id: infra-uci-alignment, content: Align UCI StorageClient/SecretClient protocols with UAC canonical infrastructure names, status: pending}
- {id: nesting-downstream, content: Update downstream imports across all affected services, status: pending}
- {id: features-interface, content: Create unified-features-interface or extend UMI; consolidate DATA_SOURCE; route features-onchain through it, status: pending}
- {id: ufcl-utl-consolidation, content: Single source for BaseFeatureCalculator/Registry; eliminate UTL/UFCL duplication, status: pending}
- {id: manifest-secrets-alignment, content: 'Align DATA_SOURCE_TO_SECRET with provider manifest; add glassnode, arkham, defillama', status: pending}
- {id: credentials-remove-coinglass-hyblock, content: Remove coinglass-api-key and hyblock-api-key from credentials-registry and cursor rules, status: pending}
isProject: false
---

# UAC Canonical Normalization — Master Plan

Consolidates three plans into one:

- `uac_residual_refactors_provider_manifest_2026_03_14`
- `uac_residual_refactors_expanded_2059e8fc`
- `infrastructure_canonical_layer_2f355b25`

---

## Design Principles

1. **Minimize splits** — as few buckets as possible; split only when the data type is genuinely different
2. **Data type over domain** — options are options (CeFi or TradFi); futures are futures; no cefi/options vs
   tradfi/options branches
3. **Perpetuals** — CeFi-only by nature (no TradFi perpetuals, no DeFi CLOB perps). One bucket
4. **TradFi** — one bucket (stocks, bonds, fx, commodities, ETFs, indices). Not per-asset-class
5. **Infrastructure** — cloud SDKs get canonical cloud-agnostic names (CloudStorage, OLAPTable), raw stays
   provider-specific
6. **Common** — cross-domain types (OHLCV, instruments, rate limits) live once, not duplicated

---

## Canonical Layout

```
canonical/
  common/
    ohlcv/             # CanonicalOhlcvBar, ProcessedCandle (crypto, equity, bonds, etc.)
    instruments/       # InstrumentType, ContractSpec, instrument_key
    rate_limits/       # VenueRateLimitSpec, HttpRateLimitHeaders

  market/
    cefi/              # spot trades, orderbooks, tickers
    options/           # options (CeFi + TradFi) — Deribit, IBKR, Yahoo, Databento, Tardis
    futures/           # futures (CeFi + TradFi) — Binance, Bybit, OKX, Deribit, Aster, Tardis, IBKR
    perpetuals/        # perpetuals (CeFi only) — Binance, Bybit, OKX, Deribit, Hyperliquid, CCXT
    tradfi/            # stocks, bonds, fx, commodities, ETFs, indices
    defi/              # oracle prices, swaps
    sports/            # odds, live

  reference/
    cefi/              # venue-specific instrument metadata
    tradfi/            # tenor registry, FX pairs, commodity contracts, stock symbols
    defi/              # protocol specs, pool addresses, chain registry
    sports/            # fixtures, mappings, lineups, player/team/league

  derived/
    defi/              # Glassnode, Arkham, DeFiLlama (TVL, MVRV, flows)
    derivatives/       # VolSurface, VolSmilePoint, VolTermStructure
    sports/            # xG, features, Footystats, Understat

  execution/
    cefi/              # CanonicalOrder, CanonicalFill (existing)
    sports/            # BetOrder, BetExecution

  errors/
    sports/            # sports-specific error schemas
    defi/              # _venue_errors_defi

  infrastructure/
    storage.py         # CanonicalCloudStorage, CanonicalStorageBucket
    olap.py            # CanonicalOLAPTable, CanonicalQueryResult
    secrets.py         # CanonicalSecretStore
    messaging.py       # CanonicalMessageQueue
    registry.py        # CanonicalContainerRegistry
    mappings.py        # CANONICAL_INFRA_TO_PROVIDER mapping

external/
  cloud_sdks/          # raw — provider-specific (unchanged)
    gcp/               # gcs.py, bigquery.py, pubsub.py, ...
    aws/               # s3.py, dynamodb.py, sqs.py, ...
```

---

## Raw to Normalized Mapping

### Common (cross-domain)

| Canonical path      | Types                                        | Sources                                                      |
| ------------------- | -------------------------------------------- | ------------------------------------------------------------ |
| common/ohlcv/       | CanonicalOhlcvBar, ProcessedCandle           | Binance, Yahoo, Databento, Polygon, Aster, Hyperliquid, etc. |
| common/instruments/ | InstrumentType, ContractSpec, instrument_key | All venues                                                   |
| common/rate_limits/ | VenueRateLimitSpec, HttpRateLimitHeaders     | All venues                                                   |

### Market

| Canonical path     | Types                                                                                                  | Sources                                                                    |
| ------------------ | ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| market/cefi/       | CanonicalTrade, CanonicalOrderBook, CanonicalTicker                                                    | Binance, Bybit, OKX, Deribit, CCXT                                         |
| market/options/    | CanonicalOptionsChainEntry, NormalizedStrikeCoordinate, OptionChainSnapshot                            | Deribit, IBKR, Yahoo, Databento, Tardis                                    |
| market/futures/    | CanonicalDerivativeTicker (futures subset)                                                             | Binance, Bybit, OKX, Deribit, Aster, Tardis, IBKR                          |
| market/perpetuals/ | CanonicalDerivativeTicker (perps subset), CanonicalFundingRate, CanonicalLiquidation                   | Binance, Bybit, OKX, Deribit, Hyperliquid, CCXT                            |
| market/tradfi/     | CanonicalYieldCurvePoint, CanonicalBondData, CanonicalCdsSpread (bonds/fx/commodities/stocks all here) | FRED, ECB, OFR, OpenBB, Fix, IBKR, Baker Hughes, EIA, CFTC, Yahoo, Polygon |
| market/defi/       | CanonicalOraclePriceFeed, swaps                                                                        | Pyth, TheGraph                                                             |
| market/sports/     | CanonicalOdds, LiveOddsUpdate, ArbitrageOpportunity                                                    | Betfair, Pinnacle, Odds API                                                |

### Reference

| Canonical path    | Sources                                                      |
| ----------------- | ------------------------------------------------------------ |
| reference/cefi/   | Binance, Bybit, Deribit, Dydx — instrument info              |
| reference/tradfi/ | Tenor registry, FX pairs, commodity contracts, stock symbols |
| reference/defi/   | Protocol specs, pool addresses, chain registry               |
| reference/sports/ | Fixtures, mappings, lineups, player/team/league              |

### Derived

| Canonical path       | Sources                                         |
| -------------------- | ----------------------------------------------- |
| derived/defi/        | Glassnode, Arkham, DeFiLlama (TVL, MVRV, flows) |
| derived/derivatives/ | VolSurface, VolSmilePoint, VolTermStructure     |
| derived/sports/      | Footystats, Understat, features                 |

### Infrastructure

| Canonical name    | GCP raw           | AWS raw         | Purpose              |
| ----------------- | ----------------- | --------------- | -------------------- |
| CloudStorage      | GCS               | S3              | Object/blob storage  |
| OLAPTable         | BigQuery          | Redshift        | Analytical warehouse |
| SecretStore       | Secret Manager    | Secrets Manager | Secrets              |
| MessageQueue      | Pub/Sub           | SQS / SNS       | Async messaging      |
| ContainerRegistry | Artifact Registry | ECR             | Container images     |

**Flow:** UCI calls with canonical name (CloudStorage) -> UAC `canonical/infrastructure/mappings.py` maps canonical +
provider -> raw SDK module in `external/cloud_sdks/gcp/` or `external/cloud_sdks/aws/`.

---

## Sports Nesting (Phase 1 detail)

| From                                                                                                                  | To                          | Data type |
| --------------------------------------------------------------------------------------------------------------------- | --------------------------- | --------- |
| external/sports/canonical/odds.py, live.py, bookmaker.py, arbitrage.py, processed_odds.py, progressive.py             | canonical/market/sports/    | market    |
| external/sports/canonical/mappings.py, fixture.py, events.py, injury.py, lineup.py, player_stats.py, fixture_stats.py | canonical/reference/sports/ | reference |
| external/sports/canonical/features.py, features.py                                                                    | canonical/derived/sports/   | derived   |
| external/sports/canonical/betting.py                                                                                  | canonical/execution/sports/ | execution |
| external/sports/errors.py                                                                                             | canonical/errors/sports/    | errors    |
| schemas/venue_errors_defi.py                                                                                          | canonical/errors/defi/      | errors    |

---

## Interfaces and Services Refactor

### Events/config — already decoupled (no UAC refactor)

- UEI, UCI config, UCI cloud have no UAC dependency
- Event schemas (LifecycleEvent, CoordinationEvent) live in UEI
- Config schemas (BaseConfig, UnifiedCloudConfig) live in UCI config

### Services needing import updates

| Service                          | UAC usage                                          |
| -------------------------------- | -------------------------------------------------- |
| market-tick-data-service         | Latency/rate-limit schemas, sports odds            |
| market-data-processing-service   | AlternativeDataSignal, OptionsFlowRecord           |
| instruments-service              | Venue instrument schemas, rate limits, TeamMapping |
| unified-reference-data-interface | Venue-specific external schemas                    |
| features-sports-service          | CanonicalBookmakerMarket, CanonicalFixture         |

### Unified features interface (new)

- Wraps UMI alt-data adapters (DefiLlama, Glassnode, Arkham) behind feature-centric API
- Extends DATA_SOURCE_TO_SECRET with glassnode, arkham, defillama
- Routes features-onchain through interface (not direct HTTP)
- Consolidates DATA_SOURCES_REFERENCE.py, DATA_SOURCE_REGISTRY into provider manifest

### UFCL/UTL consolidation

- UFCL owns BaseFeatureCalculator, FeatureCalculatorRegistry (pure calculators)
- UTL feature_service_base owns service lifecycle (BaseFeatureService, health, metrics)
- Eliminate duplicate BaseFeatureCalculator/Registry definitions

---

## Provider Manifest (completed items preserved)

Already completed: manifest-schema, manifest-generate-script, manifest-codex-ssot, manifest-cursor-rules,
manifest-api-contracts-docs, manifest-secret-check-script, manifest-audit-inventories, manifest-ui-docs-url,
credentials-remove-coinglass-hyblock.

Remaining: manifest-secrets-alignment (align DATA_SOURCE_TO_SECRET with provider manifest).

---

## Execution Order

1. **Nesting** — sports, defi errors, tradfi, options/futures/perpetuals, common, infrastructure canonical (can run in
   parallel)
2. **Infrastructure** — canonical/infrastructure/ types + mappings.py; UCI alignment
3. **Features interface** — design, DATA_SOURCE consolidation
4. **UFCL/UTL** — deduplicate BaseFeatureCalculator/Registry
5. **Downstream imports** — update all services

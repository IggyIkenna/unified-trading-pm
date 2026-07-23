---
doc_type: codex-ssot
title: Asset Class Ownership Map
summary:
  Asset-class ownership map — per-category (CeFi/TradFi/DeFi/Sports) owner+location for external schemas, normalize,
  registry, instrument discovery, market data, and orchestration; UAC owns schemas/registries, instruments-service owns
  discovery, UMI owns market-data adapters.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [features-service, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [instruments, uac, mtds, cefi, tradfi, defi, sports, ssot-audit]
related:
  [
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    /codex/04-architecture/instrument-universe-registry-consolidation.md,
  ]
created: 2026-03-27
authoritative_for: [cross-asset-class data ownership map]
referenced_by:
  [
    /codex/04-architecture/data-ownership-principles.md,
    /codex/04-architecture/instrument-universe-registry-consolidation.md,
    /codex/04-architecture/instruments-live-architecture.md,
    plans/epics/cefi_master.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Asset Class Ownership Map

> SSOT: This document. Referenced from `00-SSOT-INDEX.md`. Companion: `data-ownership-principles.md` (the generic
> pattern). Each section follows the same structure: External schemas → Normalize → Registry → Interfaces → Services.

---

## 1. CeFi (Centralized Finance — Crypto Exchanges)

### Venues

Binance, Bybit, OKX, Deribit, Coinbase, Upbit, Gemini, Huobi, Phemex, Bitstamp + on-chain CLOBs (Hyperliquid, Aster).

### Ownership

| Concern                                  | Owner                                                                      | Location                                                               |
| ---------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| External schemas                         | UAC                                                                        | `external/binance/`, `external/bybit/`, `external/deribit/`, etc.      |
| Normalize (instrument)                   | UAC                                                                        | `external/{venue}/normalize.py`                                        |
| Error codes                              | UAC                                                                        | `canonical/crosscutting/errors/cefi.py`, `onchain_perps.py`            |
| Venue registry                           | UAC                                                                        | `registry/venue_constants.py`, `VenueMapping`                          |
| Instrument discovery                     | instruments-service (ref data — formerly unified-reference-data-interface) | `adapters/tardis.py`, `adapters/binance.py`, `adapters/aster.py`, etc. |
| Market data (ticks)                      | UMI                                                                        | `adapters/cefi/` (Tardis WebSocket, CCXT REST)                         |
| Instrument orchestration                 | instruments-service                                                        | `--CEFI` flag, `_process_cefi_exchanges()`                             |
| Market data orchestration                | market-tick-data-service                                                   | CeFi download handlers                                                 |
| Config (which venues, batch/live source) | UCI                                                                        | `InstrumentProcessingConfig` in cloud storage                          |

### Current state: CLEAN

- instruments-service CeFi path uses reference data adapters (formerly unified-reference-data-interface Tardis adapter)
- 17 venues producing 387,626 instruments
- All error codes classified (100%)
- VENUE_ZERO_INSTRUMENTS events for failures

---

## 2. TradFi (Traditional Finance — Equities, Futures, Options, FX)

### Venues/Sources

Databento (CME, NASDAQ, NYSE, CBOE VX futures), Yahoo Finance (FX, KRX KOSPI, ICE DXY — ICE is NOT Databento per
UAC@5480f5d5), IBKR, ECB, OFR, Barchart.

### Ownership

| Concern                  | Owner                          | Location                                                               |
| ------------------------ | ------------------------------ | ---------------------------------------------------------------------- |
| External schemas         | UAC                            | `external/databento/`, `external/ibkr/`, `external/yahoo/`             |
| Normalize                | UAC                            | `external/{source}/normalize.py`                                       |
| Error codes              | UAC                            | `canonical/crosscutting/errors/tradfi.py`                              |
| Symbology registry       | UAC                            | `registry/tradfi_symbology.py` (SSOT — moved from instruments-service) |
| Dataset mappings         | UAC                            | `external/databento/` dataset constants                                |
| Instrument discovery     | instruments-service (ref data) | `adapters/databento.py`, `adapters/tardis.py`                          |
| Market data              | UMI                            | Databento Live/Historical, Tardis replay                               |
| Instrument orchestration | instruments-service            | `--TRADFI` flag, `_process_tradfi_exchanges()`                         |
| Config                   | UCI                            | `InstrumentProcessingConfig` — `tradfi_instrument_source: "databento"` |

### Current state: CLEAN

- instruments-service TradFi path uses reference data adapters (formerly unified-reference-data-interface Databento
  adapter)
- 5 venues producing 959,203 instruments
- All error codes classified (100%)
- Symbology moved from instruments-service to UAC registry

---

## 3. DeFi (Decentralized Finance — DEXes, Lending, Yield)

### Venues/Protocols

Uniswap V2/V3/V4, Curve, Aave V3, Morpho, Euler, Fluid, EtherFi, Lido, Ethena, Balancer.

### Ownership

| Concern                  | Owner                  | Location                                                                     |
| ------------------------ | ---------------------- | ---------------------------------------------------------------------------- |
| External schemas         | UAC                    | `external/thegraph/schemas.py` (shared for Graph-based protocols)            |
| Protocol registry        | UAC                    | `registry/defi_protocol_registry.py` (SSOT — moved from instruments-service) |
| Error codes              | UAC                    | `canonical/crosscutting/errors/defi.py`, `infra.py` (thegraph)               |
| RPC URL templates        | UAC                    | `registry/capability_declarations/_defi.py`                                  |
| Instrument discovery     | UMI adapters (interim) | `adapters/defi/` — Uniswap, Curve, Aave, Morpho, etc.                        |
| Market data (on-chain)   | UMI                    | DeFi adapters for OHLCV, funding rates                                       |
| Instrument orchestration | instruments-service    | `--DEFI` flag, `_process_defi_protocols()`                                   |
| The Graph error handling | UMI                    | `adapters/defi/utils.py` — `handle_thegraph_errors()`                        |
| Config                   | UCI                    | `InstrumentProcessingConfig` — `defi_instrument_source`                      |

### Current state: MOSTLY CLEAN

- 11 venues producing 189 instruments (was 44 at session start)
- All 14 DeFi venues have 100% error classification
- VENUE_ZERO_INSTRUMENTS events tracking all empty venues
- **Migration needed**: DeFi instrument discovery should eventually move from UMI → instruments-service (reference data,
  not market data)

---

## 4. Sports (Betting Exchanges, Prediction Markets)

### Venues/Sources

**Exchanges**: Betfair, Smarkets, Betdaq, Matchbook, Kalshi, Polymarket. **Reference data**: API Football (fixtures,
leagues, teams), OddsAPI (odds aggregation), OpticOdds. **Bookmakers** (odds only): Bet365, DraftKings, FanDuel, BetMGM,
etc.

### Ownership

| Concern                        | Owner                            | Location                                                                                                                                                                                                                 |
| ------------------------------ | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| External schemas               | UAC                              | `external/betfair/schemas.py`, `external/api_football/schemas.py`, `external/odds_api/schemas.py`, `external/polymarket/schemas.py`, `external/opticodds/schemas.py`, `external/pinnacle/schemas.py`                     |
| Normalize (fixture)            | UAC                              | `external/api_football/normalize.py`, `external/odds_api/normalize.py`                                                                                                                                                   |
| Normalize (odds/market)        | UAC                              | `external/betfair/normalize.py`, `external/polymarket/normalize.py`                                                                                                                                                      |
| Canonical schemas              | UAC                              | `canonical/domain/sports/fixture.py`, `odds.py`, `betting.py`, `bookmaker.py`, `league_registry.py`                                                                                                                      |
| Error codes                    | UAC                              | `canonical/crosscutting/errors/sports.py`                                                                                                                                                                                |
| Venue registry                 | UAC                              | `registry/_sports_venue_constants.py`, `registry/endpoints.py`                                                                                                                                                           |
| Team/league mappings           | UAC                              | `canonical/domain/sports/league_data*.py`, `team_mapping_data_*.py`                                                                                                                                                      |
| Competition phases             | USRI                             | `competition_phase.py` (stub — needs buildout)                                                                                                                                                                           |
| Fixture connectivity           | USRI                             | **NOT YET BUILT** — should call API Football, use UAC normalize                                                                                                                                                          |
| Market instrument connectivity | instruments-service (ref data)   | `adapters/betfair.py`, `adapters/polymarket.py` (shells exist, error classification wired)                                                                                                                               |
| Internal storage contracts     | UIC                              | `sports.py` (fixture storage schema)                                                                                                                                                                                     |
| Domain data client             | UDC/UTL                          | `sports/fixtures_client.py` (GCS read/write)                                                                                                                                                                             |
| Instrument orchestration       | instruments-service              | `--SPORTS` flag — **CURRENTLY BROKEN: uses local parser instead of the in-service reference-data adapters** (USRI/unified-reference-data-interface retired 2026 — merged into instruments-service `sports/` sub-package) |
| Feature computation            | features-service (sports family) | Features from fixture/odds data                                                                                                                                                                                          |
| Config                         | UCI                              | Which leagues, which venues, polling intervals                                                                                                                                                                           |

### Current state: NEEDS WORK

**What's correct:**

- UAC has comprehensive schemas: 6 external sources, canonical models, league/team registry, error codes
- instruments-service has Betfair + Polymarket reference adapter shells (formerly unified-reference-data-interface)
- UIC has fixture storage contract
- UDC has fixtures_client for GCS operations
- `new-sports-batting-services` has proven end-to-end implementation (feature calculators, mappings, ML pipeline)

**What's broken:**

- instruments-service `sports/fixture_parser.py` duplicates UAC normalize logic — should be deleted, use USRI → UAC
  instead
- `instruments-service/sports/` stub (formerly USRI; **Retired 2026** — merged into instruments-service) is a 192-line
  stub — needs API Football connectivity + UAC normalize wiring
- instruments-service `--SPORTS` doesn't call the in-service reference-data adapters (formerly
  USRI/unified-reference-data-interface; **Retired 2026**) — uses local code
- `new-sports-batting-services` has independent `Fixture`, `Team`, `League` models — migration target, not SSOT

**Migration path** (from `new-sports-batting-services`):

1. Normalize functions → UAC `external/{source}/normalize.py` (per venue)
2. Feature calculators → `features-service (sports family)`
3. Fixture/odds models → already in UAC canonical (verify field parity)
4. Team/league mapping data → already partially in UAC `canonical/domain/sports/`
5. Competition phase logic → USRI `competition_phase.py`
6. The original repo stays as-is (archived reference) until migration complete

---

## 5. Crypto (Cross-cutting — overlaps CeFi + DeFi)

Crypto is not a separate asset class in the system — it's the union of CeFi (centralized crypto exchanges) and DeFi
(decentralized protocols). The distinction is venue type, not asset type. BTC/USDT on Binance is CeFi. BTC/USDT on
Uniswap is DeFi. Same asset, different venue classification.

No separate ownership map needed — see CeFi (§1) and DeFi (§3).

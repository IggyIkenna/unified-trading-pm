# Solana DeFi Coverage — Perp DEX Adapters

> **SSOT for Solana perpetual DEX adapter architecture.** Created: 2026-05-13 per
> `plans/active/solana_perp_dex_adapters_2026_05_13.md` Phase 6.

## Overview

The `arbitrage_price_dispersion` DeFi archetype requires Solana perpetual DEX hedge legs. This doc covers the 4 Solana
perp DEX venues wired in the instruments-service reference data layer (Plan B 2026-05-13).

## Venue Registry

| Venue        | UAC Key                                | Program ID                                     | API Endpoint                     | Deploy Date     | Adapter                        |
| ------------ | -------------------------------------- | ---------------------------------------------- | -------------------------------- | --------------- | ------------------------------ |
| DRIFT-SOLANA | `SOLANA_DEFI_PROTOCOLS["drift"]`       | `dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`  | `https://data.api.drift.trade`   | 2022-11-04 (V2) | `adapters/defi/drift.py`       |
| MANGO-SOLANA | `SOLANA_DEFI_PROTOCOLS["mango"]`       | `4MangoMjqJ2firMokCjjGgoK8d4MXcrgL7XJaL3w6fVg` | `https://api.mngo.cloud/data/v4` | 2023-08-01 (V4) | `adapters/defi/mango.py`       |
| ZETA-SOLANA  | `SOLANA_DEFI_PROTOCOLS["zeta"]`        | `ZETAxsqBRek56DhiGXrn75yj2NHU3aYUnxvHXpkf3aD`  | `https://dex.zeta.markets/api`   | 2022-04-01 (V1) | `adapters/defi/zeta.py`        |
| FLASH-SOLANA | `SOLANA_DEFI_PROTOCOLS["flash_trade"]` | `FLASH6Lo6h3iasJKWDs2F8TkW2UKf3s15C8PMGuVfgBn` | `https://api.flash.trade/api/v1` | 2023-11-01      | `adapters/defi/flash_trade.py` |

## Data Types (per venue)

| data_type            | Purpose                          | Sources                                       |
| -------------------- | -------------------------------- | --------------------------------------------- |
| `perp_funding`       | Hourly funding rate per market   | Drift: S3 archive; MANGO/ZETA/FLASH: REST API |
| `perp_open_interest` | Per-market open interest         | REST APIs                                     |
| `perp_mark_prices`   | Mark price time series           | REST APIs                                     |
| `perp_index_prices`  | Index price (oracle) time series | REST APIs + Pyth (unbanned 2026-05-06)        |

## Architecture Notes

### instruments-service role

The instruments-service adapters (`drift.py`, `mango.py`, `zeta.py`, `flash_trade.py`) serve **reference data only**:

- Instrument discovery (`get_instruments()`) — produces `InstrumentRecord` with `instrument_type=PERPETUAL`
- Deploy-date floor from `_solana_utils.SOLANA_PROTOCOL_DEPLOY_DATES`
- Error classification via `classify_venue_error()` + `ADAPTER_FETCH_FAILED` event emission

### MTDS role (NOT yet wired — see Deferred below)

Market data capture (`perp_funding`, `perp_open_interest`, `perp_mark_prices`) is MTDS responsibility:

- DRIFT: Drift historical S3 archive for batch; DLOB WebSocket for live
- MANGO: `https://api.mngo.cloud/data/v4/` REST for batch; Mango WebSocket for live
- ZETA: Zeta DEX API for batch + live
- FLASH: Flash Trade API for batch + live

### DRIFT-SOLANA 0% capture root cause (documented 2026-05-13)

Root cause: instruments-service DRIFT adapter is healthy. The 0% capture is in MTDS — no Solana perp DEX source is
wired. The Drift historical S3 archive URL (`drift-historical-data-v2.s3.eu-west-1.amazonaws.com/program/...`) is
documented in UAC `SOLANA_DEFI_PROTOCOLS["drift"]["s3_historical_url"]` but has no MTDS consumer.

Pre-launch manifest rows (2018-01-01 start date) were incorrectly `expected_unattempted`; slot 3 reclassified them to
`empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH` on 2026-05-13 via `defi_legacy_blank_reclassification_2026_05_13.md`.

### Floor dates

All Solana perp DEX venues use the conservative floor date in `_solana_utils.SOLANA_PROTOCOL_DEPLOY_DATES`. Manifest
rows before the floor date are `empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH`.

## Deferred (MTDS Solana perp DEX source wiring)

MTDS Solana perp DEX source wiring is **NOT IN THIS PLAN**. Tracked in:
`plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md`

Until MTDS source is wired, all 4 venues have 0% `perp_funding` capture. The instruments-service adapters only provide
instrument discovery (reference data), not market data capture.

## Cross-references

- Plan: `plans/active/solana_perp_dex_adapters_2026_05_13.md`
- Issue doc: `plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md`
- UAC SSOT: `unified_api_contracts/registry/capability_declarations/_defi_chain_data.py` § `SOLANA_DEFI_PROTOCOLS`
- Factory: `instruments-service/instruments_service/reference_data/factory.py`
- Solana utils: `instruments-service/instruments_service/reference_data/adapters/defi/_solana_utils.py`
- Related: `codex/04-architecture/defi-execution-architecture.md` (overall DeFi execution chain)

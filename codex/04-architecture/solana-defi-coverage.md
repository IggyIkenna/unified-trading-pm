---
scope: [engineer, admin]
title: Solana DeFi Coverage — Perp DEX + AMM/CLOB/Oracle Adapters
type: architecture
status: living
last_reviewed: 2026-05-17
owner: defi-adapters
---

# Solana DeFi Coverage — Perp DEX + AMM/CLOB/Oracle Adapters

> **SSOT for Solana DeFi adapter architecture.** Created: 2026-05-13 per
> `plans/active/solana_perp_dex_adapters_2026_05_13.md` Phase 6. Extended: 2026-05-13 per
> `plans/active/solana_amm_coverage_expansion_2026_05_13.md` (Plan C).

## Overview

The `arbitrage_price_dispersion` DeFi archetype requires:

1. **Perp DEX hedge legs** (Plan B) — 4 Solana perpetual DEX venues (DRIFT, MANGO, ZETA, FLASH).
2. **Spot AMM/CLOB venues** (Plan C) — Meteora DLMM, Phoenix CLOB, Jupiter aggregator, Lifinity PMM.
3. **Oracle price feeds** (Plan C) — Pyth Network Hermes batch API for 10 major Solana pairs.

All adapters live in `instruments-service/instruments_service/reference_data/adapters/defi/`.

## Venue Registry — Plan B: Perp DEX (InstrumentType=PERPETUAL)

| Venue        | UAC Key                                | Program ID                                     | API Endpoint                     | Deploy Date     | Adapter                        |
| ------------ | -------------------------------------- | ---------------------------------------------- | -------------------------------- | --------------- | ------------------------------ |
| DRIFT-SOLANA | `SOLANA_DEFI_PROTOCOLS["drift"]`       | `dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`  | `https://data.api.drift.trade`   | 2022-11-04 (V2) | `adapters/defi/drift.py`       |
| MANGO-SOLANA | `SOLANA_DEFI_PROTOCOLS["mango"]`       | `4MangoMjqJ2firMokCjjGgoK8d4MXcrgL7XJaL3w6fVg` | `https://api.mngo.cloud/data/v4` | 2023-08-01 (V4) | `adapters/defi/mango.py`       |
| ZETA-SOLANA  | `SOLANA_DEFI_PROTOCOLS["zeta"]`        | `ZETAxsqBRek56DhiGXrn75yj2NHU3aYUnxvHXpkf3aD`  | `https://dex.zeta.markets/api`   | 2022-04-01 (V1) | `adapters/defi/zeta.py`        |
| FLASH-SOLANA | `SOLANA_DEFI_PROTOCOLS["flash_trade"]` | `FLASH6Lo6h3iasJKWDs2F8TkW2UKf3s15C8PMGuVfgBn` | `https://api.flash.trade/api/v1` | 2023-11-01      | `adapters/defi/flash_trade.py` |

## Venue Registry — Plan C: Spot AMM/CLOB (InstrumentType=SPOT)

| Venue           | UAC Key                             | Program ID                                    | API Endpoint                 | Deploy Date | Adapter                     |
| --------------- | ----------------------------------- | --------------------------------------------- | ---------------------------- | ----------- | --------------------------- |
| METEORA-SOLANA  | `SOLANA_DEFI_PROTOCOLS["meteora"]`  | `LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo` | `https://app.meteora.ag/api` | 2022-09-01  | `adapters/defi/meteora.py`  |
| PHOENIX-SOLANA  | `SOLANA_DEFI_PROTOCOLS["phoenix"]`  | `PhoeNiXZ8ByJGLkxNfZRnkUfjvmuYqLR89jjFHGqdXY` | `https://api.phoenix.trade`  | 2023-06-01  | `adapters/defi/phoenix.py`  |
| JUPITER-SOLANA  | `SOLANA_DEFI_PROTOCOLS["jupiter"]`  | `JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4` | `https://tokens.jup.ag`      | 2021-11-01  | `adapters/defi/jupiter.py`  |
| LIFINITY-SOLANA | `SOLANA_DEFI_PROTOCOLS["lifinity"]` | `LFNTYraetVioAPnGJht4yNg2aUZFXR776cMeN9VMjXp` | `https://api.lifinity.io`    | 2022-03-01  | `adapters/defi/lifinity.py` |

## Venue Registry — Plan C: Oracle (InstrumentType=SPOT, raw_symbol=feed_id)

| Venue       | UAC Key                         | Program ID                                    | API Endpoint                     | Deploy Date | Adapter                 |
| ----------- | ------------------------------- | --------------------------------------------- | -------------------------------- | ----------- | ----------------------- |
| PYTH-SOLANA | `SOLANA_DEFI_PROTOCOLS["pyth"]` | `rec5EKMGg6MxZYaMdyBfgwp4d5rB9T1VQH5pJv5LtFJ` | `https://hermes.pyth.network/v2` | 2021-08-01  | `adapters/defi/pyth.py` |

### Pyth price feeds (SSOT: `pyth.py::PYTH_PRICE_FEEDS`)

10 feeds registered for `arbitrage_price_dispersion`: SOL/USD, JITOSOL/USD, MSOL/USD, BSOL/USD, JUP/USD, RAY/USD,
BONK/USD, WIF/USD, JTO/USD, USDC/USD. The on-chain feed account address is stored as `raw_symbol` for canonical
traceability to Pyth on-chain state.

### Jupiter core routable pairs (SSOT: `jupiter.py::_CORE_ROUTABLE_PAIRS`)

15 pre-defined LST/major token pairs: SOL/USDC, SOL/USDT, JITOSOL/USDC, JITOSOL/SOL, MSOL/USDC, MSOL/SOL, BSOL/USDC,
BSOL/SOL, JUP/USDC, JUP/SOL, RAY/USDC, BONK/USDC, WIF/USDC, PYTH/USDC, JTO/USDC. No network call needed for
`get_instruments()` — pairs are statically defined.

### Meteora tick_size derivation

Meteora DLMM uses `bin_step` (basis points integer) to express price granularity. The instruments-service adapter
derives `tick_size = Decimal(str(bin_step)) / Decimal("10000")`. For example, `bin_step=10` → `tick_size=0.001`.

## Data Types (per venue)

### Perp DEX (Plan B)

| data_type            | Purpose                          | Sources                                       |
| -------------------- | -------------------------------- | --------------------------------------------- |
| `perp_funding`       | Hourly funding rate per market   | Drift: S3 archive; MANGO/ZETA/FLASH: REST API |
| `perp_open_interest` | Per-market open interest         | REST APIs                                     |
| `perp_mark_prices`   | Mark price time series           | REST APIs                                     |
| `perp_index_prices`  | Index price (oracle) time series | REST APIs + Pyth (unbanned 2026-05-06)        |

### Spot AMM/CLOB + Oracle (Plan C)

| data_type        | Purpose                        | Sources                                 |
| ---------------- | ------------------------------ | --------------------------------------- |
| `spot_trades`    | Swap/trade events              | REST APIs (backfill deferred to MTDS)   |
| `oracle_prices`  | Oracle price ticks (Pyth feed) | Pyth Hermes batch + PythNet live        |
| `pool_liquidity` | AMM pool liquidity snapshots   | Meteora/Lifinity REST APIs (MTDS scope) |

## Architecture Notes

### instruments-service role (all plans)

All Solana adapters serve **reference data only**:

- Instrument discovery (`get_instruments()`) — produces `InstrumentRecord`
  - Perp DEX (Plan B): `instrument_type=PERPETUAL`
  - Spot AMM/CLOB/Oracle (Plan C): `instrument_type=SPOT`
- Deploy-date floor from `_solana_utils.SOLANA_PROTOCOL_DEPLOY_DATES`
- Error classification via `classify_venue_error()` + `ADAPTER_FETCH_FAILED` event emission

### MTDS role (NOT yet wired — see Deferred below)

Market data capture is MTDS responsibility:

**Plan B (perp DEX):**

- DRIFT: Drift historical S3 archive for batch; DLOB WebSocket for live
- MANGO: `https://api.mngo.cloud/data/v4/` REST for batch; Mango WebSocket for live
- ZETA: Zeta DEX API for batch + live
- FLASH: Flash Trade API for batch + live

**Plan C (spot AMM/CLOB + oracle):**

- METEORA: Meteora API for pool/swap data (batch + live); wired via backfill script skeleton
- PHOENIX: Phoenix API for CLOB market/trade data; wired via backfill script skeleton
- JUPITER: Swap route history via Jupiter API (batch + live)
- LIFINITY: Lifinity pool metrics REST; batch only
- PYTH: Hermes batch endpoint (`/v2/updates/price/latest`) for historical; PythNet live WebSocket for live

### DRIFT-SOLANA 0% capture root cause (documented 2026-05-13)

Root cause: instruments-service DRIFT adapter is healthy. The 0% capture is in MTDS — no Solana perp DEX source is
wired. The Drift historical S3 archive URL (`drift-historical-data-v2.s3.eu-west-1.amazonaws.com/program/...`) is
documented in UAC `SOLANA_DEFI_PROTOCOLS["drift"]["s3_historical_url"]` but has no MTDS consumer.

Pre-launch manifest rows (2018-01-01 start date) were incorrectly `expected_unattempted`; slot 3 reclassified them to
`empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH` on 2026-05-13 via `defi_legacy_blank_reclassification_2026_05_13.md`.

### DRIFT-SOLANA capture path resolved (2026-06-01 — Velocity Data API)

> Added 2026-06-01 from `plans/archive/solana_basis_trading_mvp_2026_06_01.plan.md` Phase 1 (DriftV2HistoricalIngester
> shipped at mtds@0f70f376). Full SSOT: `codex/04-architecture/drift-v2-data-sources.md`.

The MTDS consumer gap is closed via the **Drift Velocity Data API** (`data.api.drift.trade`), not the S3 archive.
Per-day historical endpoints (free tier, no auth): `/market/{symbol}/fundingRates/{Y}/{M}/{D}` (JSON) +
`/market/{symbol}/trades/{Y}/{M}/{D}?format=csv` (CSV). Coverage verified back to 2024-06-01. The S3 archive (now
legacy) ended 2025-01-08; Velocity API covers from then on AND historically. Live-mode handler unified via
`--live --continuous` flag on `backfill_drift_v2_historical.py` (the canonical realization of CLAUDE.md "Live = batch
(CRITICAL)" hard rule). Output bucket: `market-data-tick-defi-prd-${PID}` with `pipeline_mode=` + `asset_group=defi`
canonical layout.

The Bug-D-prime saga (Helius sig-walker path, 28GB sig-index parquet) is SUPERSEDED by this design;
`plans/active/issues/bug_d_prime_drift_backfill_2026_05_31.md` banner-marked SUPERSEDED 2026-06-01. Sig-index
infrastructure REMAINS in the MTDS repo as cold infrastructure (not on any critical path).

### Floor dates

All Solana perp DEX venues use the conservative floor date in `_solana_utils.SOLANA_PROTOCOL_DEPLOY_DATES`. Manifest
rows before the floor date are `empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH`.

## Venue Registry — Plan E: Restaking (InstrumentType=YIELD_BEARING)

> Added 2026-05-13 per `plans/active/solana_restaking_rewards_coverage_2026_05_13.md`.

| Venue                | UAC Key                                              | Program ID (best-guess)                 | Deploy Date | Adapter                           | Status              |
| -------------------- | ---------------------------------------------------- | --------------------------------------- | ----------- | --------------------------------- | ------------------- |
| JITORESTAKING-SOLANA | `CANONICAL_VENUE_TO_ADAPTER["JITORESTAKING-SOLANA"]` | Jito Vault Program (multiple VRT mints) | 2024-08-01  | `adapters/defi/jito_restaking.py` | ✅ shipped (Plan A) |

> Solayer/Picasso/Cambrian removed 2026-06-02 — no usable/decodable data source (operator decision). The Plan-E
> SOLAYER/PICASSO/CAMBRIAN-SOLANA venues, UAC capabilities, and IS adapters were fully wiped. sSOL is a custom LRT vault
> with no decodable exchange-rate layout / no IDL; Picasso/Cambrian program IDs were never field-verified (best-guess
> placeholders). SSOT: `plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md`.

## Restaking layer

### What is restaking?

Restaking is a second staking layer on top of LSTs. Users stake JitoSOL/mSOL/SOL into a restaking protocol to earn
additional AVS (Actively Validated Service) / operator rewards on top of base LST staking yield. Total carry = base
staking APY + restaking AVS premium.

**Why this matters for `carry_staked_basis`:** Without restaking reward visibility, the archetype under-reports carry by
the AVS premium component, causing P&L to appear worse than actual. Restaking coverage closes the attribution gap.

### Restaking data type taxonomy (SSOT)

| Data type                      | Semantic                                                        | Availability                       |
| ------------------------------ | --------------------------------------------------------------- | ---------------------------------- |
| `restaking_rewards`            | Per-epoch/operator reward accrual rate (APY + absolute)         | REST API / RPC (future MTDS scope) |
| `restaking_operator_set`       | Active operators/NCNs securing a vault                          | On-chain account reads             |
| `cross_chain_restaking_routes` | Available cross-chain paths for restaked assets (no live venue) | API / SDK                          |
| `lst_rates`                    | Exchange rate (underlying SOL per receipt token)                | Stake pool state accounts          |

### Jito Restaking (already shipped — Plan A)

`jito_restaking.py` covers Jito VRT (Vault Receipt Token) vaults — the first generalised restaking primitive on Solana
(launched 2024-08-01). Instruments: JTORK-EZSOL (Renzo), JTORK-FRAGSOL (Fragmetric), JTORK-KYSOL (Kyros). Uses
`venue="JITORESTAKING-SOLANA"` (distinct from `jito.py` which covers the Jito LST JitoSOL at `venue="JITO-SOLANA"`).

### Solayer / Picasso / Cambrian — REMOVED 2026-06-02

The Plan-E Solayer, Picasso, and Cambrian restaking venues were **fully removed 2026-06-02 (operator decision)** — no
usable/decodable data source. Solayer's sSOL is a custom LRT vault with no decodable exchange-rate layout / no IDL, so
it could not be field-verified; Picasso (~3 tx/month, no public yield/rate API) and Cambrian (a developer SDK for
building NCNs on Jito Restaking, not a DeFi venue) had only best-guess placeholder program IDs that were never verified.
The venues, UAC `PROTOCOL_CAPABILITIES`/`_STATIC_VENUE_CHAINS` entries, IS `solayer.py`/`picasso.py`/`cambrian.py`
adapters, and all tests were wiped. "Rather have no implementation than a partial one." SSOT:
`plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md`.

### carry_staked_basis cross-reference

SSOT for archetype carry computation: `codex/09-strategy/architecture-v2/archetypes/`. Restaking rewards are a
second-order yield source; the archetype should aggregate:

1. Base SOL staking APY (from `lst_rates` data type)
2. Restaking AVS premium (from `restaking_rewards` data type)

Until MTDS restaking source wiring is complete, restaking APY is not captured in historical parquets. Reference data
(instrument discovery) is available via Plan E adapters. MTDS wiring tracked in
`plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md`.

## Venue naming convention

**Canonical format**: `{PROTOCOL}-SOLANA` (e.g., `MARINADE-SOLANA`, `DRIFT-SOLANA`, `JITO-SOLANA`, `ORCA-SOLANA`).

**Two authoritative sources confirm this:**

1. **UAC `registry/capability_declarations/_defi.py:687`** (inline comment):
   `venue: Canonical venue name (e.g. "AAVE_V3-ETHEREUM", "DRIFT-SOLANA")`
2. **All Solana adapter `get_instruments()` implementations** return `f"{PROTOCOL}-{self._chain}"`, e.g.
   `return f"DRIFT-{self._chain}"` → `DRIFT-SOLANA`.

**Legacy bare-name rows** (`MARINADE`, `DRIFT`, `JITO`, `RAYDIUM`, `ORCA`, `KAMINO`, `SOLEND`, `MARGINFI`) are migration
artifacts from an adapter version that predated the `{PROTOCOL}-{CHAIN}` pattern. They are being resolved by
`plans/active/solana_venue_naming_reconciliation_2026_05_14.md` (Plan D):

- **Category A** venues with real captured data (MARINADE/RAYDIUM/ORCA/KAMINO/SOLEND/MARGINFI): parquets re-written to
  `{PROTOCOL}-SOLANA` path; bare-name manifest rows flipped to `attempted_failed`.
- **Category B** empty venues (DRIFT/JITO): bare-name manifest rows flipped to `attempted_failed`; adapters already
  write to `{PROTOCOL}-SOLANA` on every run.

Until Plan D Phase 3 (VM migration) completes, bare-name `captured` rows may still appear in the manifest. Downstream
consumers should treat `venue=MARINADE` and `venue=MARINADE-SOLANA` as the same instrument during the migration window.
After Phase 3, only `{PROTOCOL}-SOLANA` rows will carry `capture_status=captured`.

## Deferred

### MTDS Solana source wiring (Plan B — perp DEX)

MTDS perp DEX source wiring is **NOT IN PLAN B**. Tracked in:
`plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md`

Until MTDS source is wired, all 4 venues have 0% `perp_funding` capture. The instruments-service adapters only provide
instrument discovery (reference data), not market data capture.

### MTDS Solana source wiring (Plan C — spot AMM/CLOB + oracle)

MTDS spot/oracle source wiring is **NOT IN PLAN C**. The backfill script skeleton
(`instruments-service/scripts/backfill_solana_dex_swaps_2026_05_13.py`) is a dry-run skeleton — APPLY mode raises a
warning until MTDS pipeline wiring is complete. Successor: MTDS Solana AMM/oracle pipeline wiring plan (not yet filed).

### MTDS Solana restaking source wiring (Plan E — restaking layer)

MTDS restaking reward source wiring is **NOT IN PLAN E**. Plan E ships reference data (instrument discovery) only.
Actual per-epoch AVS reward rates require MTDS source wiring. Tracked in
`plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md`.

## Cross-references

- Plan B: `plans/active/solana_perp_dex_adapters_2026_05_13.md`
- Plan C: `plans/active/solana_amm_coverage_expansion_2026_05_13.md`
- Plan E (restaking layer): `plans/active/solana_restaking_rewards_coverage_2026_05_13.md`
- Issue doc: `plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md`
- UAC SSOT: `unified_api_contracts/registry/capability_declarations/_defi_chain_data.py` § `SOLANA_DEFI_PROTOCOLS`
- Factory: `instruments-service/instruments_service/reference_data/factory.py`
- Solana utils: `instruments-service/instruments_service/reference_data/adapters/defi/_solana_utils.py`
- Pyth price feed SSOT: `instruments-service/instruments_service/reference_data/adapters/defi/pyth.py` §
  `PYTH_PRICE_FEEDS`
- Related: `codex/04-architecture/defi-execution-architecture.md` (overall DeFi execution chain)

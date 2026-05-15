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

### Floor dates

All Solana perp DEX venues use the conservative floor date in `_solana_utils.SOLANA_PROTOCOL_DEPLOY_DATES`. Manifest
rows before the floor date are `empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH`.

## Venue Registry — Plan E: Restaking (InstrumentType=YIELD_BEARING)

> Added 2026-05-13 per `plans/active/solana_restaking_rewards_coverage_2026_05_13.md`.

| Venue                | UAC Key                                              | Program ID (best-guess)                         | Deploy Date | Adapter                           | Status                                           |
| -------------------- | ---------------------------------------------------- | ----------------------------------------------- | ----------- | --------------------------------- | ------------------------------------------------ |
| JITORESTAKING-SOLANA | `CANONICAL_VENUE_TO_ADAPTER["JITORESTAKING-SOLANA"]` | Jito Vault Program (multiple VRT mints)         | 2024-08-01  | `adapters/defi/jito_restaking.py` | ✅ shipped (Plan A)                              |
| SOLAYER-SOLANA       | `SOLANA_DEFI_PROTOCOLS["solayer"]`                   | `SolayerEndoAVSSo11111111111111111111111111112` | 2024-04-01  | `adapters/defi/solayer.py`        | ✅ shipped (Plan E)                              |
| PICASSO-SOLANA       | `SOLANA_DEFI_PROTOCOLS["picasso"]`                   | `5nMau41MBCMmPfQHs9FMgzMgCJVA1VdJBV9kLnzBNNDn`  | 2023-05-01  | `adapters/defi/picasso.py`        | ✅ shipped (Plan E) ⚠️ addr pending verification |
| CAMBRIAN-SOLANA      | `SOLANA_DEFI_PROTOCOLS["cambrian"]`                  | `CAMBr1ANreStakingVau1tProgramSo1ana...`        | 2024-06-01  | `adapters/defi/cambrian.py`       | ✅ shipped (Plan E) ⚠️ addr pending verification |

> **Note on program IDs**: Picasso and Cambrian program IDs are best-guess placeholders as of 2026-05-13. Update from
> official docs when published. Tests assert structural invariants, not specific addresses — no test changes needed when
> addresses are updated.

## Restaking layer

### What is restaking?

Restaking is a second staking layer on top of LSTs. Users stake JitoSOL/mSOL/SOL into a restaking protocol to earn
additional AVS (Actively Validated Service) / operator rewards on top of base LST staking yield. Total carry = base
staking APY + restaking AVS premium.

**Why this matters for `carry_staked_basis`:** Without restaking reward visibility, the archetype under-reports carry by
the AVS premium component, causing P&L to appear worse than actual. Restaking coverage closes the attribution gap.

### Restaking data type taxonomy (SSOT)

| Data type                      | Semantic                                                      | Availability                       |
| ------------------------------ | ------------------------------------------------------------- | ---------------------------------- |
| `restaking_rewards`            | Per-epoch/operator reward accrual rate (APY + absolute)       | REST API / RPC (future MTDS scope) |
| `restaking_operator_set`       | Active operators/NCNs securing a vault                        | On-chain account reads             |
| `cross_chain_restaking_routes` | Available cross-chain paths for restaked assets (Picasso ICS) | API / SDK                          |
| `lst_rates`                    | Exchange rate (underlying SOL per receipt token)              | Stake pool state accounts          |

### Jito Restaking (already shipped — Plan A)

`jito_restaking.py` covers Jito VRT (Vault Receipt Token) vaults — the first generalised restaking primitive on Solana
(launched 2024-08-01). Instruments: JTORK-EZSOL (Renzo), JTORK-FRAGSOL (Fragmetric), JTORK-KYSOL (Kyros). Uses
`venue="JITORESTAKING-SOLANA"` (distinct from `jito.py` which covers the Jito LST JitoSOL at `venue="JITO-SOLANA"`).

### Solayer (Plan E)

`solayer.py` covers Solayer's endogenous AVS restaking. Primary instrument: sSOL (Solayer Staked SOL). Two vault routes:
SOL collateral + JitoSOL collateral (triple-layer: base staking

- Jito MEV + Solayer AVS). `venue="SOLAYER-SOLANA"`.

### Picasso (Plan E)

`picasso.py` covers Picasso Network cross-chain restaking. Primary instrument: pSOL (Picasso cross-chain restaked SOL).
Users secure ICS (Inter-Chain Security) cross-chain services. `venue="PICASSO-SOLANA"`. Program ID requires verification
from official docs (placeholder used).

### Cambrian (Plan E)

`cambrian.py` covers Cambrian Network foundational AVS restaking primitives. Instruments: cSOL

- cSOL-JITOSOL. `venue="CAMBRIAN-SOLANA"`. Vault addresses require verification from official Cambrian program registry
  (placeholders used; tests are address-agnostic).

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
   `venue: Canonical venue name (e.g. "AAVEV3-ETHEREUM", "DRIFT-SOLANA")`
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

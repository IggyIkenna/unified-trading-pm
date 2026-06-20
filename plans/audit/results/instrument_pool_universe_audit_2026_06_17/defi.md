# DeFi Pool-Universe Audit — what we ACTUALLY have (per chain × protocol × year)

**Scope:** read-only audit of the captured DeFi DEX/vault/lending pool universe in
`gs://market-data-tick-defi-prd-central-element-323112/`, sampling one representative day per year
(~mid-June 2020→2026; 2026 used **2026-03-15** because 2026-06-15 has 0 files — no recent backfill,
and Solana `dex_pools` used **2026-04-14**, the last present partition). Pre-migration drain held, so
reads are clean. Project `central-element-323112`, env `prd`.

**Method:** `gcloud storage ls -r` to learn the hive shape + enumerate (chain, protocol, data_type)
shards per year; downloaded ONE representative parquet per (year, chain, protocol, data_type) combo
(122 files) and counted `nunique(pool_id)` / `nunique(vault_address|symbol)`.

---

## Data layout (two distinct shapes co-exist; migration NOT applied)

1. **Canonical EVM hive** — `raw_tick_data/by_date/day=<D>/asset_group=defi/venue=<PROTOCOL>/chain=<CHAIN>/instrument_type=<pool|yield_bearing>/data_type=<dex_swaps|vault_share_price>/<proto>_<CHAIN>_<ts>.parquet`.
   Already on the **canonical `asset_group=defi`** key (no legacy `category=`). Each parquet is **one file
   per (protocol, chain, data_type) holding MANY pools as rows** — pool universe is in the rows, not the
   path stems.
2. **Legacy glued-venue shape** — `raw_tick_data/by_date/.../venue=AAVEV3-ETHEREUM/ticks_migrated_*.parquet`
   (protocol+chain glued, no nested `chain=`/`instrument_type=`/`data_type=`). Present **only on 2024-06-15
   and 2025-06-15** (AAVEV3, CURVE, ETHENA, ETHERFI, LIDO, MORPHO, UNISWAPV2/V3/V4-ETHEREUM). These are the
   un-migrated migration-output ticks; the same protocols mostly also appear in canonical shape.
3. **Solana side-tree** — `dex_pools/<orca|raydium|kamino>/SOLANA/date=<D>/<proto>_SOLANA_<ts>.parquet`
   (pool-state snapshots) and `lending_indices/<kamino|solend>/SOLANA/date=<D>/...` (lending-rate rows).
   These live OUTSIDE `raw_tick_data` and use `date=` (not `day=`) + UPPER-case `SOLANA` chain dir.

**`dex_swaps` distinct-pool counts are a LOWER BOUND** — swap parquets are capped at ~5000 rows/day, so
the distinct pools seen = pools that traded in the first 5000 swaps of that day, NOT the full listed
universe (the UNISWAP_V3-ETH count bounces 530→774→562→458 across years for this reason, not real churn).
Vault/lending/Solana-pool-state counts ARE the true row universe (1 row per instrument).

---

## ETHEREUM

| protocol | type | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | sample pools/pairs |
|---|---|---|---|---|---|---|---|---|---|
| VAULT (generic) | vault_share_price | 0 | 0 | 0 | — | — | — | — | empty parquet (0 rows) all 3 yrs |
| MAKER | vault_share_price | | | | 1 | 1 | 1 | 1 | sDAI vault |
| ETHENA | vault_share_price | | | | n/l | 1 | 1 | 1 | sUSDe |
| FRAX | vault_share_price | | | | n/l | 1 | 1 | 1 | sFRAX |
| MORPHO_VAULTS / MORPHOVAULTS | vault_share_price | | | | n/l | 1 | 2 | 2 | (dup'd venue spelling) |
| YEARN_V3 / YEARNV3 | vault_share_price | | | | n/l | 3 | 3 | 3 | (dup'd venue spelling) |
| UNISWAP_V3 | dex_swaps | | | | 530 | 774 | 562 | 458 | WETH-RPL, USDC-WETH, RNDR-…, ATH-… |
| CURVE | dex_swaps | | | | 140 | 184 | 206 | 221 | tricrypto / stable pools |
| BALANCER | dex_swaps | | | | 136 | 141 | 142 | 127 | |
| SUSHISWAP_V3 | dex_swaps | | | | 5 | 20 | 24 | 60 | |
| PANCAKESWAP_V3 | dex_swaps | | | | 28 | 57 | 58 | 71 | |

*VAULT-generic (2020-2022) is the only thing in pre-2023 years and it is a 0-row parquet → effectively
no real DeFi data before 2023.*

## ARBITRUM

| protocol | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| UNISWAP_V3 | 262 | 232 | 191 | 118 |
| BALANCER | 122 | 104 | 84 | 45 |
| SUSHISWAP | 184 | 184 | 164 | 83 |
| CAMELOT_V3 | n/l | 98 | 65 | 62 |

CAMELOT_V3 genesis ≈ 2024 (absent 2023). Sample pools are 0x-address pool_ids.

## POLYGON

| protocol | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| UNISWAP_V3 | 286 | 465 | 299 | 248 |
| BALANCER | 173 | 225 | 136 | 109 |

## OPTIMISM

| protocol | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| UNISWAP_V3 | 155 | 180 | 138 | 147 |
| BALANCER | n/l | 30 | 30 | 25 |

## AVALANCHE

| protocol | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| CURVE | 16 | 11 | 14 | 10 |
| SUSHISWAP_V3 | 7 | 3 | 13 | 14 |
| BALANCER | n/l | 9 | 13 | 12 |

Thin venue (single/low-double-digit pools) — Avalanche DEX activity is genuinely small.

## BASE (genesis 2024 — chain absent 2023)

| protocol | 2024 | 2025 | 2026 |
|---|---|---|---|
| UNISWAP_V3 | 286 | 503 | 629 |
| AERODROME_V3 | 63 | 161 | 180 |
| BALANCER | 59 | 51 | 44 |
| SUSHISWAP_V3 | 90 | 187 | 138 |
| PANCAKESWAP_V3 | 30 | 96 | 88 |

Base is the **growth chain** — clean year-on-year pool growth on UNISWAP_V3 (286→503→629) and
AERODROME_V3 (63→161→180), consistent with Base's real 2024-2026 ramp.

## BSC

| protocol | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| PANCAKESWAP_V3 | 231 | — | — | — |

⚠️ **BSC only present 2023** (231 pools) then DISAPPEARS — PANCAKESWAP_V3 BSC has no 2024/2025/2026
sample. Either a coverage drop or BSC capture was retired. Flag below.

## SOLANA — `dex_pools/` (pool-state snapshots) + `lending_indices/`

| protocol | type | 2023 | 2024 | 2025 | 2026 | sample pairs |
|---|---|---|---|---|---|---|
| ORCA | pool_state | 14093 | 14093 | 14093 | 14093 | SOL-USDC, cbBTC-USDC, SOL-JitoSOL, JLP-USDC |
| RAYDIUM | pool_state | 98 | 98 | 98 | 98 | XMR-USDC, BNB-USDC, USD1-USDC |
| KAMINO | pool_state (vault) | 513 | 513 | 513 | 513 | KMNO-USDC, STSOL-WETH, BNSOL-SOL, KMNO-JITOSOL |
| KAMINO (lending) | lending_index | 44 | 44 | 44 | 44 | 44 reserve symbols |
| SOLEND (lending) | lending_index | 38 | 38 | 38 | 38 | 38 distinct of 59 rows |

⚠️ **The Solana `dex_pools` + `lending_indices` files are BYTE-IDENTICAL across every year** (orca file =
1,189,564 bytes on 2023/2024/2025; same stem-timestamp family `2026-04-1x`; counts perfectly flat
14093/98/513/44/38). They are a **single late-April-2026 snapshot copied into every historical date
partition**, NOT per-date captures. So Solana has NO temporal pool-universe evolution and NO genuine
historical state. (Contrast: EVM swap parquets DIFFER in size year-on-year — 717993/722367/663515 B for
UNISWAP_V3-ETH 2023/24/25 — i.e. real per-year captures.)

---

## Findings

### Pool-universe growth story
- **DeFi capture effectively starts 2023.** 2020-2022 contain only a single `VAULT` `vault_share_price`
  parquet with **0 rows** — there is no real pre-2023 DeFi pool data. Genesis is NOT a per-protocol 2021
  Uniswap-V3 listing as registry suggests; it is a **corpus-wide 2023 cold-start**.
- **EVM DEX universe is broad and real from 2023:** ~16 (chain,protocol) dex combos in 2023 growing to
  ~23 in 2024-2026, spanning UNISWAP_V3, CURVE, BALANCER, SUSHISWAP(_V3), PANCAKESWAP_V3, CAMELOT_V3,
  AERODROME_V3 across ETHEREUM/ARBITRUM/POLYGON/OPTIMISM/AVALANCHE/BASE/BSC.
- **Base is the clear growth chain** (genesis 2024): UNISWAP_V3 286→503→629, AERODROME_V3 63→161→180.
- **Yield-bearing/vault leg (the carry-staked-basis ingredients) lands 2024**: ETHENA(sUSDe), FRAX(sFRAX),
  MORPHO, YEARN_V3 vaults appear 2024 onward; MAKER(sDAI) from 2023. LST/staking rates (LIDO/ETHERFI)
  appear only in the **legacy glued-venue 2024/2025 migration shape**, not yet in canonical hive.
- **Observed dex_swaps pool counts are swap-capped lower bounds**, so they do NOT cleanly trend; the true
  listed universe is larger than the per-day-5000-swap sample shows.

### Per-chain / per-protocol coverage verdict
- **ETHEREUM** ✅ strongest — DEX (UNI_V3/CURVE/BALANCER/SUSHI_V3/PANCAKE_V3) + the full vault set.
- **ARBITRUM / POLYGON / OPTIMISM / BASE** ✅ solid multi-protocol DEX coverage 2024-2026.
- **AVALANCHE** 🟡 thin but present (single-/low-double-digit pools — genuinely small chain).
- **SOLANA** 🔴 present in COUNT but **static-snapshot-copied across all dates** (orca/raydium/kamino +
  kamino/solend lending) — no historical truth, and no SOLANA rows in `raw_tick_data` at all (lives only
  in the side `dex_pools/` tree). UNISWAP_V4, ORCA-as-swaps, RAYDIUM/DRIFT/PHOENIX swap data absent.

### Top anomalies for the operator
1. 🔴 **Solana pool-state + lending are a single 2026-04 snapshot copied to every date partition**
   (byte-identical files, flat counts 14093/98/513/44/38 across 2023-2026). Violates the "never copy
   instrument definitions between dates" rule — Solana DeFi has zero real historical pool/state/rate
   evolution. Backfill needed with genuine per-date captures.
2. 🔴 **BSC drops after 2023** — PANCAKESWAP_V3 BSC has 231 pools in 2023 then is absent 2024/2025/2026.
   Coverage gap or retired capture; needs diagnosis.
3. 🟠 **No real DeFi data pre-2023** — 2020-2022 hold only a 0-row VAULT parquet. If the strategy needs
   pre-2023 DeFi history it does not exist; if not, the empty 2020-2022 partitions are misleading
   placeholders.
4. 🟠 **Dual / duplicated venue spellings in the canonical hive**: `MORPHO_VAULTS`+`MORPHOVAULTS`,
   `YEARN_V3`+`YEARNV3` both written as separate `venue=` dirs (same data, two spellings) — vocabulary
   drift that will double-count in any universe roll-up.
5. 🟠 **Legacy glued-venue shape still un-migrated** (`venue=AAVEV3-ETHEREUM/ticks_migrated_*` on
   2024/2025) co-exists with the canonical hive for LIDO/ETHERFI/AAVE_V3/UNISWAP_V2/V4 — these are the
   ONLY home for the LST/staking & Aave-v3 & Uniswap-V2/V4 legs; they must survive the migration --apply
   or that data is lost.
6. 🟡 **2026-06-15 is empty** (used 2026-03-15) — current backfill horizon ends ~March 2026 for EVM and
   ~April 2026 for the Solana snapshot; no June-2026 DeFi capture yet.
7. 🟡 **UNISWAP_V4 present only in 2025 legacy shape** (`UNISWAPV4-ETHEREUM/ticks.parquet`, genesis ≈
   late-2024) — single chain, not yet in canonical hive.

---

*Audit basis: 122 representative parquets (one per year×chain×protocol×data_type), distinct-pool counts
via `nunique`; path enumeration via `gcloud storage ls -r`. dex_swaps counts are swap-capped lower bounds;
vault/lending/Solana-pool-state counts are exact row universes. No writes performed.*

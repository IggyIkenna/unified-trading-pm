---
type: analysis
title: DeFi C0 data-state audit — per-bucket layout + schema + grain truth (pre-migration)
epic: defi_master
auditor: ikenna
date: "2026-06-01"
status: complete
source:
  - plans/active/defi_manifest_canonicalisation_2026_06_01.md (§C0-RD1…RD5)
  - market_tick_data_service/scripts/audit_canonical_form.py
locked_by: live-defi-rollout
---

# DeFi C0 data-state audit (2026-06-01) — the real shape before the v9 single-walk

> **Why this doc exists**: the C0 tool was only parsing the flat `day=/category=` layout (~10%). This audit walked the
> actual object trees + read all 6 consolidated `_index` parquets to establish the ground truth the migration must
> conform. **Sampling transparency**: top-level trees enumerated EXHAUSTIVELY per bucket (`gsutil ls`); leaf path
> structure + parquet column schema SAMPLED (1–2 non-empty objects per layout per bucket); manifest grain read
> EXHAUSTIVELY from each `_index/availability_index.parquet`. Local GCS DNS was flaky (in-region VM required for the
> heavy walk + the oracle/lst row-mapping validation — per handoff).

## 1. Every source bucket holds THREE overlapping object layouts (confirmed all 6)

`{stem}-central-element-323112` for stem ∈ {dex-pools, dex-swaps, lst-rates, lending-indices, oracle-prices,
perp-funding}. Non-`_index`/`_deploy` top-level trees:

| Layout | Prefix                         | Notes                                                                  |
| ------ | ------------------------------ | ---------------------------------------------------------------------- |
| **L1** | `{data_type_dir}/…`            | oldest; `date=` partition (not `day=`); per-bucket structure (see §2)  |
| **L2** | `day=/category=defi/…`         | flat; `category=defi`; has `venue=/chain=/instrument_type=/data_type=` |
| **L3** | `raw_tick_data/by_date/day=/…` | best metadata; `asset_group=defi`; **missing `pipeline_mode=`**        |

Same venues recur across trees ⇒ **overlapping duplicates in different schemas/coverage, NOT complementary**.

## 2. L1 path structure DIFFERS per bucket (cell-key extraction is per-bucket)

| Bucket            | L1 leaf path                                             | venue source               | chain source                  |
| ----------------- | -------------------------------------------------------- | -------------------------- | ----------------------------- |
| dex-pools         | `dex_pools/{venue_lc}/{CHAIN}/date=/f.parquet`           | path seg                   | path seg                      |
| dex-swaps         | `dex_swaps/{venue_lc}/{CHAIN}/date=/f.parquet`           | path seg                   | path seg                      |
| lending-indices   | `lending_indices/{venue_lc}/{CHAIN}/date=/f.parquet`     | path seg                   | path seg                      |
| perp-funding      | `perp_funding/{venue_lc}/date=/f.parquet` (**no chain**) | path seg                   | **row `chain`**               |
| **lst-rates**     | `lst_rates/date=/f.parquet` (**no venue, no chain**)     | **row** `protocol`/`token` | **row** `chain`               |
| **oracle-prices** | `oracle_prices/date=/f.parquet` (**no venue, no chain**) | const CHAINLINK (pre-Pyth) | **row, needs contract→chain** |

L3 path is uniform across buckets:
`raw_tick_data/by_date/day=/asset_group=defi/venue=/chain=/instrument_type=/data_type=/f.parquet`.

## 3. data_type NAME forks (object-path vs manifest vs plan-canonical)

| Bucket    | object-path data_type (L2/L3) | manifest `_index` data_type            | **canonical (plan C2 + manifest)** |
| --------- | ----------------------------- | -------------------------------------- | ---------------------------------- |
| dex-pools | `dex_pool_state`              | `dex_pools` + `dex-pools`              | **`dex_pools`**                    |
| dex-swaps | `dex_pool_swaps`              | `dex_swaps`                            | **`dex_swaps`**                    |
| others    | match                         | match (+ `lending-indices` hyphen dup) | underscore canonical               |

> The Solana-MVP `dex_pool_state` (Orca/Raydium AMM **state** time-series, §G) is a DIFFERENT future data_type that gets
> its own dedicated bucket — NOT these daily-aggregate dex-pools objects. So normalizing the existing dedicated-bucket
> `dex_pool_state` path label → `dex_pools` does not collide with the MVP type.

## 4. Venue-grain MISMATCH (the keystone for lst/oracle)

Manifest `_index` distinct (venue) — the canonical grain the rebuilt index + data-status must reflect:

- dex-pools (17): per-protocol incl. glued ghosts `AERODROMEV3`/`CAMELOTV3`/`TRADER_JOEV2`/`VELODROMEV2` (→ `_V{N}` via
  C12).
- dex-swaps (5): `AERODROMEV3, BALANCER, CAMELOTV3, CURVE, SUSHISWAP`.
- lending-indices (6): `AAVE_V3, COMPOUND_V3, KAMINO, MARGINFI, SOLEND, SPARK`.
- **lst-rates (14)**:
  `ANKR COINBASE ETHENA ETHERFI JITO LIDO MAKER MANTLE MARINADE PUFFER ROCKETPOOL STADER STAKEWISE SWELL` — **but L1/L3
  OBJECTS store aggregate `venue=LST`** with per-row `protocol`/`token`. ⇒ migration MUST **split objects by
  protocol→venue** to hit the 14-venue canonical grain.
- oracle-prices (2): `CHAINLINK, PYTH` — L3 objects are per-venue; **L1 flat objects have no venue/chain in path or
  (chain) in data** ⇒ venue=CHAINLINK (pre-Pyth era), chain from `contract` address registry (needs Chainlink
  feed-address→chain lookup; in-region VM build).
- perp-funding (5): `ASTER GMX HYPERLIQUID LIGHTER PACIFICA`; chain col carries legacy VENUE-CHAIN artifacts
  (`chain=ASTER`/`HYPERLIQUID`) + blanks → needs venue→default-chain normalization.

## 5. Schema-version spread (0% v9 — confirmed) + per-data_type COLUMN divergence

Every `_index` is v4–v8, **0% v9**. Object column sets differ materially per layout per data_type — e.g.
`dex_pool_state`:

- L1:
  `protocol,chain,pool_id,token_a,token_b,fee_rate_bps,date,volume_usd,tvl_usd,fees_usd,tx_count,price_a,price_b,liquidity`
- L3:
  `protocol,chain,pool_id,pool_name,timestamp,tvl_usd,daily_volume_usd,daily_total/supply/protocol_revenue_usd,symbol,pool_address,pair_address,instrument_id,venue,instrument_type,data_type`
- complementary (L1 has price/liquidity/fees; L3 has revenue/pool_name/metadata). The UAC `parquet_records.py`
  dataclasses are STALE (match neither). ⇒ **operator-chosen policy: superset-union (lossless) per data_type** (§6).

**perp-funding**: L1 = raw GMX Messari snapshot (`tvl_usd,daily_volume_usd,long_oi_usd,short_oi_usd`); L3 = **derived**
`funding_rate_long/short = (long_oi−short_oi)/total_oi` (handler `perp_funding_handler.py:951-971`). Same data_type; OI
is unique to `perp_funding` within DeFi (CeFi OI lives in `derivative_ticker`/`open_interest`, different AG); GMX
`tvl/volume` partially double-covered by dex-pools `venue=GMX`.

## 6. Operator decisions (2026-06-01, this session) — binding

1. **Uniform schema = SUPERSET UNION (lossless)** per data_type: canonical columns = union of all observed data columns
   (L1∪L2∪L3) + v9 metadata (`schema_version=9, asset_group, pipeline_mode, source, available_at`). Reindex every output
   object to it (missing→null). No column dropped; semantically-dup columns (`token_a`+`token_in`) coexist until a later
   cheap column-projection cleanup. Chosen over L3-rename (data-loss risk) + curated-UAC (slower).
2. **perp-funding = include in union + DERIVE funding for L1-origin cells** using the handler's exact formula
   `funding_rate_long=(long_oi−short_oi)/total_oi`, `funding_rate_short=−imbalance` — makes the 87% old history usable
   for the basis strategy. Preserve raw OI/tvl/volume columns too.

## 7. Migration target (confirmed) + per-bucket transform spec (the C0-RD build contract)

Canonical output path (partition order per `pipeline_mode_partition_migration` §24 + §G G1 verification):
`{stem}-prd-{pid}/raw_tick_data/by_date/day={day}/pipeline_mode={mode}/asset_group=defi/venue={V}/chain={C}/instrument_type={IT}/data_type={DT}/{venue_lc}_{chain}_{day}.parquet`
(deterministic filename per cell ⇒ idempotent overwrite). `pipeline_mode=batch` for all legacy (historical).

| Bucket          | canon DT        | cell grain          | venue/chain derivation                                   | special                         |
| --------------- | --------------- | ------------------- | -------------------------------------------------------- | ------------------------------- |
| dex-pools       | dex_pools       | path (venue,chain)  | path seg → UAC `_V{N}`                                   | —                               |
| dex-swaps       | dex_swaps       | path (venue,chain)  | path seg → UAC `_V{N}`                                   | —                               |
| lending-indices | lending_indices | path (venue,chain)  | path seg → UAC `_V{N}`                                   | —                               |
| perp-funding    | perp_funding    | (venue path, chain) | venue path seg; chain from row, venue→default-chain norm | **derive funding for L1**       |
| lst-rates       | lst_rates       | **row-split**       | venue=protocol/token→canonical; chain=row                | split aggregate obj by protocol |
| oracle-prices   | oracle_prices   | **row-split**       | venue=source/CHAINLINK; chain=`contract`→chain registry  | L1 needs feed-addr→chain (VM)   |

## 8. Resolved-and-remaining (concrete C0-RD todos — see plan §C0-RD)

- RESOLVED from SSOT (no operator needed): data_type-name canon (plan C2 + manifest); venue `_V{N}` canon (UAC
  `canonicalize_defi_venue_combined`); superset-union schema + perp-derive (operator §6); path partition order.
- BUILD (in-region VM where GCS reliable, dry-validated per data_type BEFORE any `--apply`): lst protocol-split, oracle
  `contract`→chain attribution registry, perp venue→default-chain map. Rows that genuinely cannot be confidently
  (venue,chain)-attributed are written to a `_needs_attribution/` holding prefix (NOT canonical tree, NOT deleted) +
  counted in the completeness gate — **never guess-then-delete** (irreversible).
- GATE (C0-RD4) then DELETE (C0-RD5) per bucket only after that bucket's gate is GREEN.

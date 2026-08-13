---
doc_type: codex-ssot
title: DeFi Data Pipeline — code-grounded current state + Code↔Codex drift register
summary: >-
  Code-verified walkthrough of the DeFi data path (IS reference data → MTDS raw capture → MDPS candles → features
  onchain/delta_one) plus a Code↔Codex drift register (§1, findings D1–D5) reconciling stale codex SSOTs against
  2026-05-27 code/GCS reality, incl. the latent lending_indices candle-adapter bug and canonical data_type names.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-service,
    features-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [defi, pipeline, data-pipeline, mtds, mdps, features, reconciliation, ssot-audit]
related:
  [
    /codex/02-data/defi-data-types-catalog.md,
    /codex/02-data/defi-data-type-taxonomy.md,
    /codex/02-data/defi-venue-protocol-catalogue.md,
    /codex/02-data/instrument-pipeline-defi.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: 2026-05-27
authoritative_for: [DeFi data pipeline code-grounded current-state walkthrough, DeFi code-vs-codex drift register]
referenced_by:
  [
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/defi-data-types-catalog.md,
    /codex/02-data/instrument-pipeline-defi.md,
    plans/archive/2026_08/issues/defi_code_codex_drift_2026_05_27.md,
    plans/audit/instructions/defi_master_audit_instructions.md,
  ]
owner:
last_reviewed: 2026-05-27
code_refs:
purpose: code-grounded current-state of the DeFi data pipeline + a Code↔Codex drift register
---

# DeFi Data Pipeline — code-grounded current state + Code↔Codex drift register

> **What this doc is.** A **code-verified** walkthrough of the DeFi data path (collection → processing → features) as it
> actually runs, plus a **drift register** (§1) flagging where the existing codex SSOTs disagree with the code. Built by
> re-reading the Python on **2026-05-27** while the end-to-end backfill is still running, so treat **code + GCS as the
> source of truth in-progress** and the older codex docs as the prior intent. Where they diverge, §1 says which is right
> and who fixes it.
>
> **This doc does NOT replace** the detailed SSOTs — it cross-links and reconciles them:
> [`data-lineage-MTDS-features-ml`](data-lineage-MTDS-features-ml.md) (pipeline spine),
> [`defi-data-types-catalog`](defi-data-types-catalog.md) + [`defi-data-type-taxonomy`](defi-data-type-taxonomy.md)
> (data types), [`defi-venue-protocol-catalogue`](defi-venue-protocol-catalogue.md) (venues),
> [`pipeline-coverage-matrix`](pipeline-coverage-matrix.md) +
> [`mtds-data-source-coverage-matrix`](mtds-data-source-coverage-matrix.md) (coverage),
> [`instrument-pipeline-defi`](instrument-pipeline-defi.md) (instruments).
>
> **Code-change rule (operator 2026-05-27):** the pipeline is mid-run; do **not** change service code off this audit
> until the run completes. Code-side fixes below are tagged `DEFERRED-UNTIL-PIPELINE-DONE`. Codex-doc fixes are safe
> now.

---

## 1. Code ↔ Codex drift register (verified 2026-05-27)

Each row: what a codex SSOT claims, what the code/GCS actually does (with citation), the verdict, and the fix side. The
**5 rows below are the architectural highlights**; the full audit (13 findings D1–D13, incl. catalog completeness, venue
drift, banned `bloxroute` relay, RADIANT-unbacked-live, governance handler dup) is in the audit record
[`plans/audit/results/defi_pipeline_code_codex_drift_2026_05_27`](../../plans/audit/results/defi_pipeline_code_codex_drift_2026_05_27.md).
Actionable items tracked in
[`issues/defi_code_codex_drift_2026_05_27`](../../plans/archive/2026_08/issues/defi_code_codex_drift_2026_05_27.md).

| #      | Area                             | Codex SSOT says                                                                                                                              | Code / GCS reality (2026-05-27)                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Verdict                                                        | Fix                                                                                                                                                                              |
| ------ | -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **D1** | data_type **names**              | `defi-data-types-catalog.md` headings + instrument-type map use `swap_events` / `pool_state` / `lending_metrics` / `funding_rates`           | Code writes `dex_swaps` / `dex_pool_state` / `lending_indices` / `perp_funding` (handler constants `_*_DATA_TYPE`); catalog names appear only as one-way migration aliases (`migrate_defi_canonical.py:128`), never as live `data_type=` values.                                                                                                                                                                                                                                  | **codex stale**                                                | codex-fix (safe now): update catalog headings + instrument-type map to canonical names                                                                                           |
| **D2** | bypass-type **storage bucket**   | `data-lineage` lists separate buckets `lst-rates-*` / `lending-indices-*` / `dex-pools-*` (✅ correct)                                       | Confirmed: `get_write_bucket_name("lst-rates"/"lending-indices"/"dex-pools"/"oracle-prices"/"perp-funding")` → dedicated buckets (handlers L285–366). The prefixes `lst_rates/` `lending_indices/` `dex_pools/` **inside** `market-data-tick-defi-prd` are **LEGACY** (data stops 2026-04-14; code no longer writes there).                                                                                                                                                       | **codex right; this doc's earlier §2 was wrong; + stale data** | doc-fix (done this rev); legacy-prefix cleanup `DEFERRED-UNTIL-PIPELINE-DONE`                                                                                                    |
| **D3** | MDPS **processed scope** + a bug | `data-lineage` (L89): MDPS processes 5 {`dex_swaps`,`book_snapshot_5`,`fx_rates`,`market_state`,`liquidity`}; `lending_indices` = **bypass** | Runtime = same 5 (only `dex_swaps` actually materialises DeFi candles in prd — GCS shows `processed_candles/.../data_type=dex_swaps` only). **BUT** UAC `needs_candle_processing("lending_indices")=True` AND `DefiLendingIndicesAdapter` is decorator-registered — skipped only because it is **not imported** in top-level `app/adapters/__init__.py` (so `has_adapter`=False). Intent is bypass (features read lending raw — D4), so the `True` gate + adapter are wrong/dead. | **codex right on outcome; CODE has a latent bug**              | code-fix `DEFERRED-UNTIL-PIPELINE-DONE`: set `needs_candle_processing("lending_indices")=False` + delete dead `DefiLendingIndicesAdapter` + fix misleading `__init__.py` comment |
| **D4** | features-onchain **read source** | `data-lineage` + `dependency_checker.py` docstring: bypass types read raw from MTDS                                                          | Confirmed: `onchain/app/core/data_loader.py` `load_rate_indices` (L433) / `load_oracle_prices` (L470) read `raw_tick_data/.../data_type=…` from the dedicated buckets; never `processed_candles/`. (Aave live path uses DefiLlama directly.)                                                                                                                                                                                                                                      | **aligned**                                                    | none                                                                                                                                                                             |
| **D5** | bucket-name **convention**       | `data-lineage` per-layer paths use legacy `market-data-tick-{category}-…` (doc carries a 🟡 staleness banner)                                | Canonical = `resolve_bucket_name(cloud=,kind=,asset_group=,env=)` → env-tiered `market-data-tick-defi-prd-…`.                                                                                                                                                                                                                                                                                                                                                                     | **codex stale (self-acknowledged)**                            | codex-fix: per-layer path rewrite (tracked ML-14)                                                                                                                                |

**Net:** the codex SSOTs are directionally correct on architecture (bypass model, separate buckets, 5-type MDPS scope);
the drift is (a) **stale naming** in the data-types catalog (D1), and (b) one **real latent code bug** — a
`lending_indices` candle adapter exists and UAC says to run it, but a missing import silently disables it (D3), which
happens to match the codex's "bypass" outcome by accident. D3's code fix waits for the running pipeline.

---

## 2. GCS bucket layout (corrected, verified 2026-05-27)

DeFi raw data is **split across several dedicated buckets by data_type**, not all in one. Canonical names resolve via
`resolve_bucket_name(...)` / `get_write_bucket_name(kind)` against `deployment-service/configs/cloud-providers.yaml`.

| data_type                                          | Bucket (`kind=`)                                 | Canonical GCS bucket (prod)                        |
| -------------------------------------------------- | ------------------------------------------------ | -------------------------------------------------- |
| `dex_swaps`, `vault_share_price`, `dex_pool_state` | `market-data` / `market_data` (asset_group=defi) | `market-data-tick-defi-prd-central-element-323112` |
| `lst_rates`                                        | `lst-rates`                                      | `lst-rates-central-element-323112`                 |
| `lending_indices`                                  | `lending-indices`                                | `lending-indices-central-element-323112`           |
| `dex_pools`                                        | `dex-pools`                                      | `dex-pools-prd-central-element-323112`             |
| `oracle_prices`                                    | `oracle-prices`                                  | `oracle-prices-central-element-323112`             |
| `perp_funding`                                     | `perp-funding`                                   | `perp-funding-central-element-323112`              |

Inside `market-data-tick-defi-prd-…`:

```
raw_tick_data/by_date/day=YYYY-MM-DD/pipeline_mode={mode}_{source}/asset_group=defi/venue=<V>/chain=<C>/instrument_type=<T>/data_type=<D>/*.parquet
        (migration pending: this doc predates the pipeline_mode partition; the {mode}_{source} segment lands after day=;
         venue-before-chain ordering is correct)
        D ∈ { dex_swaps, dex_pool_state, dex_pool_swaps, oracle_prices, rate_indices, rewards,
              risk_params, utilization, vault_share_price, eigenlayer_rewards, ... }
processed_candles/by_date/day=YYYY-MM-DD/timeframe={15s|1m|5m|15m|1h|4h|24h}/data_type=dex_swaps/...   ← MDPS output
        (verified: only data_type=dex_swaps materialises for DeFi)
_index/  _manifests/  _vm_staging/  backfill-logs/  configs/
✅ lst_rates/ DELETED 2026-05-28 (1,200 parquets; canonical: lst-rates-central-element-323112 superset)
⚠ lending_indices/  dex_pools/   ← LEGACY Solana-only prefixes, stale 2026-04-14 (D2 partial); deletion deferred until Gate 2 full migration completes
```

The running backfill (`mtds-dex-swaps-backfill`, `collect-dex-swaps`, 2023-01-01→2026-05-25) writes `dex_swaps` +
`vault_share_price` into `raw_tick_data/by_date/...` in `-prd`.

---

## 3. Stage 1 — instruments-service (reference data, NOT market data)

IS produces `InstrumentRecord` parquets — the **universe** + per-instrument metadata MTDS needs. The "stamped
instruments" line in MTDS logs (`loaded N stamped instruments for venue=BALANCER-ETHEREUM`) is IS output being read.

- **`InstrumentRecord` fields:** `instrument_type`, `instrument_key`, `source_archive_url_template` (the IS→MTDS
  fetch-URL contract — no hardcoded venue URLs in MTDS, QG-enforced), `available_from/to_datetime`, decimals, fee tier,
  TVL snapshots.
- **Enumeration** (`instruments_service/engine/orchestrator.py`): static `_STATIC_DEFI_VENUES` / `_SOLANA_DEFI_VENUES` /
  `_L2_DEX_PERP_VENUES` + dynamic `_build_defi_venues()` (`protocol × supported_chains`). **Relevance filter:** DEX
  pools need both tokens in `MAJOR_ASSETS`; lending markets need only the base token. **Monotonicity:** per-venue
  high-water mark blocks a run returning fewer instruments (no silent universe shrink).
- **IS does NOT produce** `lst_rates` / `lending_indices` time-series — those are MTDS raw captures fetched via the IS
  `source_archive_url_template`. IS is reference data only.

---

## 4. Stage 2 — MTDS raw capture: what we pull, from where

### 4.1 CLI operations → data_types → source

| `--operation`                                                                                                                           | data_type(s)                                                    | Source                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `collect-dex-swaps`                                                                                                                     | `dex_swaps`                                                     | The Graph subgraphs (UniV3 / Balancer / Messari fallback chain)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `collect-dex-pools`                                                                                                                     | `dex_pool_state`                                                | The Graph subgraphs                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `collect-lending-indices` / `collect-evm-defi`                                                                                          | `lending_indices` (+ `utilization`, `risk_params` derived)      | The Graph (Aave native / Messari / Compound custom); DeFiLlama (Solana)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `collect-lst-rates`                                                                                                                     | `lst_rates`                                                     | EVM: `eth_call` at historical block (Alchemy). Solana: Marinade/Jito REST                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `collect-oracle-prices`                                                                                                                 | `oracle_prices`                                                 | Chainlink `latestRoundData()` (EVM) + Pyth Hermes REST (Solana)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ~~`collect-solana-defi`~~ **(DEPRECATED — MTDS@896d5c9)**                                                                               | ~~`dex_pools`, `lending_indices`, `lst_rates`, `perp_funding`~~ | Monolithic Solana handler deleted Gate 5. Solana venues now in per-data-type handlers: Solana lending (Kamino/Solend/Marginfi) → `collect-lending-indices`; Solana AMM (Orca/Raydium/Phoenix) + Kamino vault → `collect-dex-pools`; LST (Marinade/Jito) → `collect-lst-rates`; Drift → `collect-perp-funding`. instrument_types: `solana_lending`, `solana_vault`, `solana_amm_pool` (UAC@7e9f4ad9 + UAC@90b2bb9d).                                                                                                                                                              |
| `collect-vault-share-price`                                                                                                             | `vault_share_price`                                             | ERC-4626 `convertToAssets`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `collect-perp-funding`                                                                                                                  | `perp_funding`                                                  | **No DeFi perp source currently live** (HYPERLIQUID/ASTER MOVED TO CEFI 2026-06-21 — removed from `ALL_DEFI_VENUES`/`DEFI_VENUE_PHASE`; legacy `asset_group=defi` corpus migrated → cefi 2026-08-06, see `/plans/archive/2026_08/hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md`; GMX REMOVED 2026-07-25 — synthetic OI-imbalance proxy, see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`; Drift removed 2026-07-16 -- operator ruling, all Solana perp DEXes dropped except Jupiter; see `/codex/04-architecture/solana-defi-coverage.md`) |
| `collect-eigenlayer-rewards`, `-liquidations`, `-flash-loan-events`, `-bridge-events`, `-mev-events`, `-gas-fees`, `-aggregator-routes` | as named                                                        | per-protocol                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |

> Canonical `data_type=` strings are `dex_swaps` / `dex_pool_state` / `lending_indices` / `perp_funding` (handler
> constants). The catalog's `swap_events` / `pool_state` / `lending_metrics` / `funding_rates` are **stale** (D1).

### 4.2 Per-data_type content (key types)

| data_type           | What it is                           | Key columns                                                                                                                                                  | Source                                                                                                                                |
| ------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| `dex_swaps`         | individual swap events               | `swap_id, timestamp, pool_id, token_a/b (or token_in/out), amount0/1 (or amount_in/out), amount_usd, fee_rate_bps, tick, sender`                             | The Graph (fallback: univ3→pancake→minimal→messari→sushi)                                                                             |
| `dex_pool_state`    | daily/hourly pool snapshot           | `pool_id, token_a/b, fee_rate_bps, tvl_usd, volume_usd, fees_usd, tx_count, price_a/b, liquidity, sqrt_price, tick`                                          | The Graph                                                                                                                             |
| `lending_indices`   | per-asset lending market snapshot    | `protocol, chain, symbol, liquidity_index, variable_borrow_index, supply_rate, borrow_rate, utilization_rate, total_supply/debt, reserve_factor, IRM slopes` | The Graph (Aave/Messari/Compound); DeFiLlama (Sol)                                                                                    |
| `lst_rates`         | LST exchange rate (share→underlying) | `timestamp, token, exchange_rate, apy, quote_asset, protocol, chain, block_number, method, contract, is_rebasing, rebase_rate`                               | EVM `eth_call` @ noon-UTC block; Solana REST                                                                                          |
| `oracle_prices`     | reference price feed                 | `feed, base/quote_asset, price, confidence, publish_time, updated_at, round_id, block_number, source, chain`                                                 | Chainlink (EVM on-chain) + Pyth Hermes (Solana)                                                                                       |
| `perp_funding`      | DeFi-perp funding/mark               | `protocol, symbol, funding_rate(24h/7d/30d), oracle_px, mark_px, open_interest, oi_long/short`                                                               | **No DeFi perp source currently live** — HYPERLIQUID/ASTER MOVED TO CEFI 2026-06-21; GMX REMOVED 2026-07-25; Drift removed 2026-07-16 |
| `vault_share_price` | ERC-4626 price-per-share             | `vault_address, share_price, timestamp`                                                                                                                      | ERC-4626 `convertToAssets`                                                                                                            |

**Schema fallback pattern** (all subgraph handlers): on `SubgraphSchemaError` ("Type X has no field …") advance through
an ordered schema list; all exhausted → `record_failed`. (The `messari schema failed, trying next fallback` log line.)

**EVM vs Solana:** EVM = The Graph + Alchemy `eth_call` at historical block (subgraph IDs in UAC `SUBGRAPH_IDS`); Solana
= per-protocol REST/SDK, Pyth via Hermes (archive from 2023-10-01), DeFiLlama fallback for Solana lending. (Drift via S3
was a source here until removed 2026-07-16 -- operator ruling, all Solana perp DEXes dropped except Jupiter, not
integrated.)

---

## 5. Venue universe — same-kind data vs unique data (the "why each venue" question)

Two buckets. Full detail: [`defi-venue-protocol-catalogue`](defi-venue-protocol-catalogue.md) +
[`defi-data-type-taxonomy`](defi-data-type-taxonomy.md).

### 5.1 Same-kind data (DEX swaps + pools) — chosen for **liquidity / price dispersion**

Feed `arbitrage_price_dispersion`. All provide `dex_swaps` + `dex_pool_state`; value is breadth, not unique fields.

- EVM: Uniswap V2/V3/V4, Balancer (6 chains), Curve (ETH/OPT/AVAX), PancakeSwap V3, SushiSwap V3/(V2), Aerodrome V3
  (Base), Camelot V3 (ARB, Algebra fork), Velodrome V2 (OPT), Trader Joe V2 (AVAX, currently empty).
- Solana: Raydium, Orca, Phoenix, Kamino. (Drift was the CLOB-style perp entry here until removed 2026-07-16 -- operator
  ruling, all Solana perp DEXes dropped except Jupiter, not integrated.)

### 5.2 Unique data — venue is the **only source of one signal**

| Role               | Venues                                                                                                                                                                                                                                                                                                          | Unique data                                                                                                                         | Archetype                              |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| Lending            | Aave V3, Compound V3, Spark, Morpho, Fluid (+Euler/Radiant/Venus/Benqi)                                                                                                                                                                                                                                         | `lending_indices` (supply/borrow rate, utilization, IRM slopes), `liquidations`, `risk_params` (LTV, liq threshold, reserve factor) | `carry_staked_basis` borrow leg + HF   |
| LST/staking (ETH)  | Lido (stETH/wstETH), RocketPool, Coinbase (cbETH), EtherFi (weETH), Ethena (sUSDe), Mantle, Swell, Stader, StakeWise, Puffer, Ankr                                                                                                                                                                              | `lst_rates` (exchange_rate, is_rebasing, apy)                                                                                       | `carry_staked_basis` staking yield     |
| LST/staking (SOL)  | Marinade (mSOL), Jito (jitoSOL), SolBlaze (bSOL), Sanctum                                                                                                                                                                                                                                                       | `lst_rates` (SOL-family)                                                                                                            | `carry_staked_basis` (Solana)          |
| Oracles            | **Pyth (Solana only)**, **Chainlink (all EVM)**                                                                                                                                                                                                                                                                 | `oracle_prices` (price + confidence + publish_time)                                                                                 | price feed; deviation/staleness gating |
| DeFi perps         | **No DeFi perp venue currently live** — HYPERLIQUID/ASTER MOVED TO CEFI 2026-06-21 (pure CeFi; see `/codex/02-data/defi-canonical-naming-ssot.md` § "On-chain perp CLOBs are CeFi, NOT DeFi"; legacy defi corpus migrated → cefi 2026-08-06); GMX REMOVED 2026-07-25; Drift removed 2026-07-16, operator ruling | `perp_funding` (+ liquidations)                                                                                                     | `carry_staked_basis` hedge leg         |
| Restaking / vaults | EigenLayer; ERC-4626 vaults (EtherFi, Yearn V3, Morpho Vaults, Pendle)                                                                                                                                                                                                                                          | `rewards` / `restaking_rewards`, `vault_share_price`                                                                                | second-layer AVS yield, vault APY      |
| Cost / infra       | Alchemy (synthetic), Flashbots, Across/Stargate                                                                                                                                                                                                                                                                 | `gas_fees`, `mev_events`, `bridge_events`                                                                                           | execution cost / MEV / bridging        |

> Solayer/Picasso/Cambrian removed 2026-06-02 — no usable/decodable data source (operator decision).

**Mental model:** _DEX venues are interchangeable liquidity sources (more = better dispersion); lending / LST / oracle /
perp / restaking venues are each in the universe because they are the canonical source of one specific signal the
archetype math needs._

---

## 6. Stage 3 — MDPS processing: raw → processed_candles

MDPS turns a subset of raw types into OHLCV `processed_candles` (co-located in the MTDS bucket under
`processed_candles/by_date/day=.../timeframe=.../data_type=.../`). **Runtime-active DeFi adapters (5)** — registered in
top-level `app/adapters/__init__.py` and gated `True` by UAC `needs_candle_processing`:

| Adapter                   | Input raw type                | How OHLCV is built                                                                                                                                                                                                                                  |
| ------------------------- | ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DefiSwapAdapter`         | `dex_swaps`, `dex_pool_swaps` | **real OHLCV** — per-swap price (cascade `amount_usd/amount_in` → `amount1/amount0` → `(sqrtPriceX96/2^96)^2`); group by interval → first/max/min/last + summed volume. **Sparse: no swap = no row.** Extra: `chain, swap_count, volume_quote_usd`. |
| `DefiLiquidityAdapter`    | `dex_pool_state`              | `mid_price=(token0_price+1/token1_price)/2` LOCF; volume=`tvl_usd`; `depth_bid/ask=reserve0/1`.                                                                                                                                                     |
| `DefiMarketStateAdapter`  | `market_state`                | O=H=L=C=`liquidity`; `spread_bps=utilization×1e4`.                                                                                                                                                                                                  |
| `DefiFxRateAdapter`       | CeFi spot candle closes       | derives `fx_rate_eth_usd / btc_usd / sol_usd`.                                                                                                                                                                                                      |
| `DefiBookSnapshotAdapter` | on-chain CLOB L2 (HL)         | delegates to CeFi book adapter.                                                                                                                                                                                                                     |

> **⚠ Verified reality (D3):** in prod, **only `dex_swaps` actually materialises DeFi processed_candles** (GCS: every
> `processed_candles/.../data_type=` partition is `dex_swaps`). The other 4 adapters are registered but have no DeFi
> source data driving them currently. A 6th adapter, **`DefiLendingIndicesAdapter`** (`lending_indices`), exists and is
> decorator-registered but is **dead code** — it's not imported in the top-level `app/adapters/__init__.py`, so it never
> registers at runtime; meanwhile UAC `needs_candle_processing("lending_indices")` wrongly returns `True`. Intended
> behaviour is **bypass** (features read `lending_indices` raw — §7). Fix is `DEFERRED-UNTIL-PIPELINE-DONE`.

**Common bar mechanics** (`base_adapter.py`): 200µs synthetic delay (anti-lookahead), end-of-period convention,
timeframes `15s/1m/5m/15m/1h/4h/24h`, DeFi treated 24/7. Empty paths: zero rows → `empty_confirmed`; ticks-outside-day →
`UpstreamTimestampBiasError`.

**Bypass types (no MDPS candle — features read raw from the dedicated bucket):** `lending_indices`, `lst_rates`,
`oracle_prices`, `dex_pools`/`dex_pool_state`, `vault_share_price`, `perp_funding`, `liquidations`, `rewards`,
`risk_params`, `utilization`, `eigenlayer_rewards`, etc. SSOT for this list: `dependency_checker.py` docstring +
[`data-lineage-MTDS-features-ml`](data-lineage-MTDS-features-ml.md) §"DeFi MDPS scope".

---

## 7. Stage 4 — feature calculation

### 7.1 `onchain` family — `features_service/onchain/` (reads raw MTDS, bypass)

`OnChainOrchestrationService`; definitions in `onchain/schemas/feature_definitions.yaml`. Every loader reads
`raw_tick_data/.../data_type=…` from the dedicated buckets (D4) — never processed_candles.

| Group                                           | Inputs                                              | What it computes                                                                                                                                              |
| ----------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lending_rates`                                 | `rate_indices`/`lending_indices` (+ DeFiLlama live) | normalise supply/borrow/util; **synthesise supply APY** (`borrow×util×(1−reserve_factor)`); `rate_spread`                                                     |
| `lst_yields`                                    | `lst_rates`                                         | **`staking_apy_bps = ((rate[t]/rate[t-1])^365 − 1)×1e4`**; `staking_apy_total = base + eigen + seasonal − dust`                                               |
| `perp_funding_rates`                            | `perp_funding`                                      | `funding_rate_apy_bps = annualise_funding_rate_bps(raw, venue)` (MVP: Hyperliquid ETH-PERP — **stale example, see §4.1: no DeFi perp source currently live**) |
| `utilization` / `risk_params` / `health_factor` | `rate_indices`                                      | `aave_utilization`, `aave_ltv`, `aave_liquidation_threshold`, `aave_health_factor`                                                                            |
| `rate_impact` (live)                            | DeFiLlama                                           | projected APY after a $500k position (two-slope IRM); `rate_impact_*_bps`                                                                                     |
| `regime`                                        | mixed                                               | `oracle_deviation_flag` (\|oracle−dex\|/dex > 1%), `tvl_regime_bucket`, util/gas/HF buckets                                                                   |

App-layer calculators (live/current-day): `ChainlinkPegDeviationCalculator`,
`ConcentratedLiquidityIlRealisedCalculator`, `VaultSharePriceApyCalculator`, `PoolInvariantDriftCalculator`.

> **Batch gap:** `utilization`, `rate_impact`, `macro_*`, `onchain_perps` are batch-skipped for historical dates
> (live-only sources — DeFiLlama Yields API has no historical archive — plus an MTDS backfill schema gap). They run in
> live mode. Verify before relying on these in a batch run.

### 7.2 `delta_one` applied to DeFi (asset_group=DEFI)

`DEFI_DATA_TYPE_OVERRIDES` (`delta_one/engine/orchestrator.py`) remap inputs: **`oracle_prices`** →
`technical_indicators` / `moving_averages` / `oscillators` / `volatility_realized` / `momentum` / `returns` /
`market_structure` / `candlestick_patterns` / `targets`; **`dex_swaps`** → `volume_analysis` / `vwap` /
`microstructure`; **`derivative_ticker`** (Hyperliquid) → `funding_oi` / `liquidations` — **stale mapping: no DeFi perp
source is currently live (§4.1), so this override key has no live input today**. So DeFi price features come off the
**Chainlink/Pyth oracle series**, flow features off **swap events** — `derivative_ticker`-derived features do not
currently flow for DeFi.

### 7.3 Output

UIC `OnchainFeatureRecord` (`unified-api-contracts/.../internal/domain/features_onchain/onchain_feature.py`):
`timestamp, instrument_key ("DEFI:PROTOCOL:TOKEN:CHAIN"), lending_rate, borrowing_rate, utilization_ratio, staking_yield, reward_apy, tvl, available_liquidity, ltv, liquidation_threshold, market_state, is_halted, is_auction`.

---

## 8. Archetype data lineage

**`carry_staked_basis`** (recursive LST stake + perp short hedge):

```
lst_rates ──► onchain.lst_yields ──► staking_apy_total_bps ┐
                                                            ├─► strategy: net basis = staking − funding
perp_funding ──► onchain.perp_funding_rates ──► funding_apy ┘
lending_indices/rate_indices ──► onchain.{lending_rates,utilization,risk_params,health_factor}  (cost-of-capital + HF gate)
```

**`arbitrage_price_dispersion`** (cross-venue price spread):

```
dex_swaps (many venues) ──► MDPS DefiSwapAdapter ──► dex_swaps candles ──► delta_one (vwap/volume/microstructure)
oracle_prices ──► delta_one price indicators + onchain.regime.oracle_deviation_flag (risk gate)
dex_pool_state ──► onchain pool-invariant-drift / concentrated-liquidity-IL  (LP health)
```

---

## 9. Pointers

- Drift action items:
  [`issues/defi_code_codex_drift_2026_05_27`](../../plans/archive/2026_08/issues/defi_code_codex_drift_2026_05_27.md)
- Pipeline spine: [`data-lineage-MTDS-features-ml`](data-lineage-MTDS-features-ml.md)
- Data types: [`defi-data-types-catalog`](defi-data-types-catalog.md),
  [`defi-data-type-taxonomy`](defi-data-type-taxonomy.md)
- Venues: [`defi-venue-protocol-catalogue`](defi-venue-protocol-catalogue.md)
- Coverage: [`pipeline-coverage-matrix`](pipeline-coverage-matrix.md),
  [`mtds-data-source-coverage-matrix`](mtds-data-source-coverage-matrix.md)
- Instruments: [`instrument-pipeline-defi`](instrument-pipeline-defi.md)
- Buckets SSOT: `deployment-service/configs/cloud-providers.yaml` +
  `unified_trading_library.cloud_interface.bucket_naming`
- Execution side: [`defi-execution-overview`](/codex/04-architecture/defi-execution-overview.md)
- Code refs: MTDS handlers `market-tick-data-service/.../cli/handlers/*_handler.py`; MDPS
  `market-data-processing-service/.../app/adapters/defi/` + `cli/handlers/process_handler.py`; UAC
  `registry/market_data_categories.py::needs_candle_processing` + `registry/capability_declarations/_defi*.py`; features
  `features-service/features_service/onchain/`.

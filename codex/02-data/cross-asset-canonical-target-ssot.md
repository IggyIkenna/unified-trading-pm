---
doc_type: codex-ssot
title: Cross-asset canonical target SSOT (shard model · instrument-id grammar · taxonomy · two-id model)
summary: >-
  The single scannable statement of the POST-MIGRATION canonical target across cefi / tradfi / defi / prediction — the
  four canonical surfaces, the FOUR shard-atom grain patterns (flat-per-contract, bundle-per-underlying, prediction CQG
  bundle, defi capture-batch column-level), the instrument-id grammar per asset-group/type, the SPOT_PAIR vs SPOT_ASSET
  vs POOL decision rule, the lending A_TOKEN/DEBT_TOKEN split, the CLOB-vs-DEX-pool perp classification, the defi two-id
  model, the empty_confirmed-vs-out-of-scope basis, and the kept/dropped venue list. Consolidated 2026-07-18 from a
  canonicalisation audit + operator rulings; REFERENCES the detailed per-domain SSOTs rather than duplicating them. Any
  writer/reader/doc that contradicts this is review-blocking.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-api,
    features-service,
  ]
scope: [engineer, admin]
tags: [canonicalisation, instrument-id, shard-atom, spot-taxonomy, lending, two-id-model, ssot, cross-asset, migration]
related:
  [
    defi-canonical-naming-ssot.md,
    availability-manifest-and-data-status.md,
    honest-coverage-model.md,
    shard-granularity-cefi.md,
    pipeline-mode-partition.md,
    data-status-drilldown-hierarchy.md,
    ../../plans/active/defi_consolidated_closeout_2026_07_18.md,
    ../../plans/active/cefi_consolidated_closeout_2026_07_18.md,
    ../../plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    ../../plans/active/prediction_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-18
authoritative_for:
  [
    cross-asset canonical instrument-id target,
    the four shard-atom grain patterns,
    SPOT_PAIR vs SPOT_ASSET vs POOL decision rule,
    lending A_TOKEN/DEBT_TOKEN split,
    CLOB-vs-DEX-pool perp asset_group classification,
    defi two-id model,
    kept/dropped venue list,
  ]
referenced_by: []
owner:
last_reviewed: 2026-07-18
code_refs:
  [
    unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/defi.py,
    unified-trading-library/unified_trading_library/manifest_writer/_rows.py,
  ]
---

# Cross-asset canonical target SSOT

> **What this is.** ONE scannable home for the post-migration canonical target across **cefi · tradfi · defi ·
> prediction**. It states the target and points to the detailed SSOT for each axis; it does not duplicate them. Where a
> doc/code/plan contradicts this, that surface is review-blocking. Consolidated 2026-07-18 after a canonicalisation
> audit (75 contradictions resolved) + operator rulings; the per-AG migration work lives in the four
> `*_consolidated_closeout_2026_07_18.md` plans.

## 0. The four canonical surfaces

Every shard must agree on the instrument identity across all four:

1. **GCS parquet path / filename**
2. **parquet content columns** (`instrument_id` and, for defi, `canonical_instrument_id`)
3. **manifest `_index` key** (the shard atom)
4. **data-status render** (deployment-api/ui)

For **flat-per-contract** shards — cefi/tradfi AND **defi (target, operator 2026-07-18)** — the filename stem == the
`instrument_id` column == the manifest key (byte-identical). Only **bundles** (cefi/tradfi chains) and **prediction**
(CQG) keep a coarser manifest grain with the per-instrument id in the column — see §1. DeFi's old capture-batch model
(one file held MANY instruments; the manifest id was blank) is **RETIRED** — see §1 pattern #4.

## 1. The shard-atom model — FOUR grain patterns

Full atom (superset, `unified_trading_library/manifest_writer/_rows.py`;
`codex/02-data/availability-manifest-and-data-status.md:47-71` governs which columns _earn_ a place):

```
pipeline_mode({mode}_{source}) · date · asset_group · venue · [chain] · instrument_type · data_type
  · (KEY) · [quote · margin] · source
```

`chain` is defi-only. `[quote · margin]` is cefi bundles + prediction perps. The **(KEY)** slot is the one axis that
differs by pattern:

| #     | pattern                               | who                                                                                                   | (KEY)                                                                                                                          | file granularity                                                                                                                                                                                 | per-row id                                                                                                                                   |
| ----- | ------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **1** | flat-per-contract                     | cefi spot/perp/dated-future, tradfi equity, kalshi raw trades, **all defi (target 2026-07-18)**       | **`instrument_id`**                                                                                                            | one parquet per instrument (stem == id)                                                                                                                                                          | non-null, == manifest key                                                                                                                    |
| **2** | bundle-per-underlying                 | cefi `options_chain`/`futures_chain` (DERIBIT/OKX), tradfi `futures_chain`/`options_chain` (CME/CBOE) | **`underlying`**                                                                                                               | one parquet per underlying (`underlying={U}/…`; cefi also nests `quote=/margin=`)                                                                                                                | per-contract ids in the column; manifest row MAY carry null id by design                                                                     |
| **3** | prediction CQG bundle                 | POLYMARKET / KALSHI vanilla markets                                                                   | **`canonical_question_group`** (`data_type=prediction_canonical_question_group`, e.g. `SPORTS_EPL_MATCH`, `BTC_UP_DOWN_DAILY`) | manifest-only bundle, recomputed at rebuild                                                                                                                                                      | per-CID rows (Polymarket `condition_id` / Kalshi ticker) carry `instrument_id` + `underlying` (display-only) + `build_fixture_id` for soccer |
| **4** | defi capture-batch — **RETIRED → #1** | (was all defi)                                                                                        | → **`instrument_id`** populated, one manifest row per instrument/day                                                           | → **one parquet per instrument**, filename = symbolic canonical id (`write_defi_rows` fans out `groupby(instrument_id)`; 6/7 handlers already emit per-instrument rows, only `evm_defi` bundled) | filename == manifest key = **symbolic canonical id**; the **address** stays a content column + the IS-definition/join key                    |

Corollaries:

- **`underlying` is a KEY only in pattern #2.** In prediction (#3) and elsewhere it is a **display-only** row column —
  never the shard key. (This is why the phantom reconciler must not key prediction on per-object `instrument_id`; per
  `codex/02-data/availability-manifest-and-data-status.md:57-60` prediction keys on `canonical_question_group`.)
- **DeFi availability is by DATA day**, not capture time: rows land in `day={YYYY-MM-DD}` by their event/block
  timestamp. Under the **target per-instrument model** a re-capture **OVERWRITES** the one `{canonical_id}.parquet` (no
  `{…}_{capture_ts}.parquet` pile-up), so the duplicate/phantom-row dedup the old batch model needed **disappears at the
  source**. The **IS** per-(venue,chain) universe with `available_from` (real on-chain genesis, `eth_getCode`
  binary-search) + `available_to` (TVL-drop delist) is the honest denominator: out-of-window = out-of-scope; in-window +
  0 rows = `empty_confirmed`. (Legacy batch files migrate to per-instrument via a column+row UNION merge — see the DeFi
  close-out plan.)
- **instruments-service (reference) side is thinner**: prediction IS = `venue → dates` (no `data_type` axis,
  `VENUE_REFERENCE_DATA_CAPABILITIES={}`); MTDS drilldown is CQG-**above**-data_type
  (`codex/02-data/data-status-drilldown-hierarchy.md:42`).

## 2. Canonical instrument-id grammar

`instrument_type` is always the **UPPER** middle segment of the id (`VENUE:TYPE:BODY`); it is **lowercase** in the GCS
path segment and manifest column (see §7). Builder SSOT + full per-type grammar:
`unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py` +
`unified-api-contracts/docs/canonical-instrument-ids.md`. The decided shapes:

- **cefi** — `VENUE:TYPE:BASE-QUOTE@MARGIN[-YYYYMMDD][-STRIKE-C|P]`. Margin marker: quote∈{USDT,USDC,…}→`@LIN`,
  quote==USD→`@INV`; SPOT has no marker. **Venue is HYPHENATED** (`BINANCE-FUTURES`, must equal the GCS `venue=` axis).
  **DERIBIT ALWAYS carries the quote.**
- **tradfi** — dated derivatives `VENUE:TYPE:PRODUCT_ROOT-USD@LIN-YYYYMMDD[-STRIKE-C|P]` (product root resolved, e.g.
  ES→SP500, VX→VIX; BTC/ETH pass through); cash `VENUE:EQUITY:SYM-USD` (equity carries `-USD` on **all four** surfaces);
  combos = the leg-aware signed-weight spec (per-leg human-readable key + weight + direction-as-sign, 1–4 leg cap —
  `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`).
- **defi** — `VENUE-CHAIN:TYPE:SYMBOL` (the only AG whose venue segment carries a `-CHAIN` suffix; on-chain token case
  is PRESERVED — `aUSDC`, `stETH`). See §4–§6.
- **prediction** — per-CID `VENUE:PREDICTION_MARKET:{condition_id|ticker}`; the manifest bundle keys on
  `canonical_question_group` (§1 #3), not an id.

## 3. Representative canonical id per shard (the target)

| AG     | shard (venue · data_type · type)                                     | representative canonical id / key                                 | notes                                           |
| ------ | -------------------------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------- |
| cefi   | BINANCE-FUTURES · trades · perpetual                                 | `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN`                          | flat; +book5/derivative_ticker/liquidations     |
| cefi   | BINANCE-SPOT · trades · spot_pair                                    | `BINANCE-SPOT:SPOT_PAIR:BTC-USDT`                                 | no margin on spot                               |
| cefi   | BYBIT · trades · future                                              | `BYBIT:FUTURE:BTC-USD@INV-20231201`                               | per-contract (not a bundle)                     |
| cefi   | DERIBIT · trades · options_chain (underlying=BTC)                    | `DERIBIT:OPTION:BTC-USD@INV-20260401-3250-C`                      | pattern #2; quote ALWAYS                        |
| cefi   | DERIBIT · trades · futures_chain (underlying=AVAX)                   | `DERIBIT:FUTURE:AVAX-USDC@LIN-20260401`                           | pattern #2; USDC=linear                         |
| cefi   | OKX-SWAP · trades · perpetual                                        | `OKX-SWAP:PERPETUAL:BTC-USD@INV`                                  | folds to OKX in Layer-1                         |
| cefi   | HYPERLIQUID · trades · perpetual                                     | `HYPERLIQUID:PERPETUAL:BTC-USDC@LIN`                              | on-chain CLOB → cefi                            |
| cefi   | ASTER · derivative_ticker · perpetual                                | `ASTER:PERPETUAL:BTC-USDT@LIN`                                    | per-symbol real quote (mostly USDT)             |
| tradfi | CME · ohlcv_1m · futures_chain (ES→SP500)                            | `CME:FUTURE:SP500-USD@LIN-20260619`                               | pattern #2, stem=SP500                          |
| tradfi | CME · ohlcv_1m · options_chain (ES)                                  | `CME:OPTION:SP500-USD@LIN-20260117-7960-C`                        | fixes the `E3AN6 C7960` space                   |
| tradfi | NASDAQ · ohlcv_1m · equity                                           | `NASDAQ:EQUITY:AAPL-USD`                                          | `-USD` on all four surfaces                     |
| tradfi | CBOE · ohlcv_1m · futures_chain (VX→VIX)                             | `CBOE:FUTURE:VIX-USD@LIN-20260722`                                |                                                 |
| tradfi | CBOE · ohlcv_24h · index (Treasury)                                  | `CBOE:INDEX:US10Y-USD`                                            | daily = `ohlcv_24h`                             |
| tradfi | FX · ohlcv_24h · currency (KRW)                                      | `FX:CURRENCY:KRW-USD`                                             | Yahoo daily                                     |
| tradfi | CME · ohlcv_1m · combo                                               | `CME:COMBO:SP500-CALENDAR-20240621-20240920`                      | legs w/ signed weights in the definition        |
| defi   | UNISWAP_V3 · dex_pool_state · pool                                   | `UNISWAP_V3-ETHEREUM:POOL:USDC-WETH-500`                          | 3-seg; addr = machine `instrument_id`           |
| defi   | UNISWAP_V3 · oracle_prices · spot_asset                              | `UNISWAP_V3-ETHEREUM:SPOT_ASSET:WETH`                             | canonical == instrument_id (converge)           |
| defi   | AAVE_V3 · lending_indices · a_token / debt_token                     | `AAVE_V3-ETHEREUM:A_TOKEN:aUSDC` / `:DEBT_TOKEN:variableDebtUSDC` | pooled → real symbol                            |
| defi   | MORPHO · lending_indices · a_token (isolated)                        | `MORPHO-BASE:A_TOKEN:AUSDC-EURC-<marketId8>`                      | isolated → synthesized symbol                   |
| defi   | LIDO · lst_rates · lst                                               | `LIDO-ETHEREUM:LST:stETH`                                         | case preserved                                  |
| defi   | GMX · perp_funding · perpetual                                       | `GMX:PERPETUAL:BTC-USD`                                           | DEX-pool perp → defi; **no chain suffix**       |
| defi   | ORCA · dex_pool_swaps · solana_amm_pool                              | `ORCA-SOLANA:SOLANA_AMM_POOL:SOL-USDC`                            |                                                 |
| pred   | POLYMARKET · prediction_canonical_question_group · prediction_market | key = `canonical_question_group` (`SPORTS_EPL_MATCH`)             | pattern #3 bundle; per-market rows carry CID id |
| pred   | KALSHI · trades · prediction_market                                  | per-CID `instrument_id` (market ticker)                           | flat per-market raw object                      |

## 4. SPOT taxonomy — SPOT_PAIR vs SPOT_ASSET vs POOL

Decision rule (a validator SHOULD enforce this for defi — none exists yet, tracked in the defi close-out):

1. A **two-token quoted market** → **`SPOT_PAIR`** (cefi orderbook, OR a defi orderbook-DEX / aggregator quote —
   PHOENIX, JUPITER: `JUPITER-SOLANA:SPOT_PAIR:SOL-USDC`). Requires a `BASE-QUOTE` symbol.
2. A **single on-chain token** you want oracle-price / transfers / gas / bridge / gov / MEV data for → **`SPOT_ASSET`**
   (defi; governance tokens like `EIGENLAYER-ETHEREUM:SPOT_ASSET:EIGEN` belong HERE — NOT SPOT_PAIR). For SPOT_ASSET
   `canonical_instrument_id == instrument_id` (converge).
3. An **AMM liquidity-pool contract** → **`POOL`** (defi; never SPOT_PAIR). Solana spot-DEX shards use
   **`DEX_POOL`/`SOLANA_AMM_POOL`**. A pool's two legs are each individually a `SPOT_ASSET`.

## 5. Lending — the A_TOKEN/DEBT_TOKEN split (ONE SSOT)

Legacy flat `LENDING` is **RETIRED**. Every lending position = one **`A_TOKEN`** (supply leg) + one **`DEBT_TOKEN`**
(borrow leg) — because `net_value = supply − borrow` needs both. `instrument_type` is uniform across all 11 protocols;
the **symbol** has two conventions (both canonical):

- **Pooled** (AAVE_V3 / SPARK / COMPOUND_V3): the **real on-chain token symbol** — `aUSDC` / `variableDebtUSDC`. Rate is
  asset-global (collateral-independent) → one instrument per asset.
- **Isolated-market** (MORPHO / EULER_V2 / FLUID / RADIANT / VENUS / BENQI + Solana MARGINFI / SOLEND): a
  **synthesized** symbol `A{collateral}-{loan}[-marketId8]` / `DEBT{collateral}-{loan}[-marketId8]`. Each market is a
  `(collateral, loan)` pair with its own oracle+IRM → the same loan token has different rates per pairing, so one
  instrument per market.

Detail + per-protocol table: `instruments-service/docs/DEFI_INSTRUMENTS.md` §Lending.

## 6. Perp classification + the defi two-id model

- **CLOB (orderbook) on-chain perps → `asset_group=cefi`**: HYPERLIQUID, ASTER, EXTENDED, LIGHTER, PACIFICA(culled).
  They trade the perp/hedge leg like a centralized orderbook, just settle on-chain.
- **DEX-pool-shaped perps → `asset_group=defi`**: **GMX** (DRIFT culled) — traders trade against an AMM/liquidity pool,
  oracle-priced. `instrument_type=perpetual` is valid for defi; the defi perp id carries **no chain suffix**
  (`GMX:PERPETUAL:BTC-USD`).
- **Two-id model (defi, Option A — intentional, NOT a gap)**: every address-identified defi row carries TWO ids:
  **`canonical_instrument_id`** = the symbolic `VENUE-CHAIN:TYPE:SYMBOL` (human/canonical; carries NO raw addresses),
  and **`instrument_id`** = the **address-anchored machine/join key** (POOL → `pool_address.lower()`, SPOT_ASSET →
  `spot_asset:{chain}:{token_addr}`). POOL rows legitimately **diverge**; SPOT_ASSET converges. The pool/token CONTRACT
  ADDRESS lives in `instrument_id` + the instrument DEFINITION — never inside the canonical id. **No mass address→symbol
  rewrite.** POOL canonical key = **3-segment, fee inside the symbol** (`…:POOL:USDC-WETH-500`), never the 4-segment
  `…:POOL:USDC-WETH:500` form.

## 7. instrument_type case + venue spelling

- **case**: LOWERCASE in the GCS path segment + the manifest `instrument_type` column (writer grain); **UPPER** only in
  the id middle segment (`:POOL:`). Mixed case in the manifest is drift to fold.
- **venue**: cefi = single HYPHENATED spelling (`BINANCE-FUTURES`, not `BINANCE_FUTURES`). defi = bare canonical
  PROTOCOL (`AAVE_V3` not `AAVEV3`/`AAVE`; `UNISWAP_V3` not bare `UNISWAP`; `COMPOUND_V3` not `COMPOUND`) + a **separate
  `chain=`** path segment (never the combined `PROTOCOL-CHAIN` overload in the path; the id joins them as
  `VENUE-CHAIN`).

## 8. Path templates

- **cefi/tradfi flat**:
  `raw_tick_data/by_date/day={D}/pipeline_mode={mode}_{src}/asset_group={ag}/venue={V}/instrument_type={it}/data_type={dt}/{instrument_id}.parquet`
- **cefi bundle**:
  `…/instrument_type={options_chain|futures_chain}/data_type={dt}/underlying={U}/quote={Q}/margin={M}/ticks.parquet`
- **tradfi bundle**: `…/instrument_type={…_chain}/data_type={dt}/{PRODUCT_ROOT}.parquet` (flat stem — kept per the
  tradfi plan, deliberately different from cefi's `underlying=/ticks.parquet` for now)
- **defi**:
  `…/day={D}/pipeline_mode={mode}_{source}/asset_group=defi/venue={PROTOCOL}/chain={CHAIN}/instrument_type={it_lower}/data_type={dt}/{venue}_{chain}_{capture_ts}.parquet`
  — **venue BEFORE chain** (operator-locked, `defi-canonical-naming-ssot.md`)

## 9. empty_confirmed vs out-of-scope (the denominator basis)

- **`empty_confirmed`** — a cell INSIDE the could-exist universe, attempted, source PROVABLY returned 0 (typed
  `EmptyConfirmedReason` + evidence, or UTL hard-raises). A materialized manifest row (`row_count=0`, blank id).
  **EXCLUDED from `reachable_coverage`, RETAINED in `all_shards`.**
- **out-of-scope** — a tuple that should NEVER generate → **no manifest row** (`NOT_IN_SCOPE` /
  `is_valid_shard_key=False` / `is_mvp()=False`). **Clipped from BOTH numerator and denominator.**
- DeFi's catalogue denominator is **circular** (built from the same subgraphs the manifest reads), so honest
  empty-vs-hole needs the **completeness oracle** (`enumerated / on_chain_truth`, fail-closed —
  `codex/02-data/defi-completeness-oracle.md`). SSOT: `codex/02-data/honest-coverage-model.md`,
  `…/honest-absence-downstream-handling.md`.

## 10. Kept vs dropped venues

- **Dropped / purged (dead — remove entirely from UAC + manifest + GCS + catalogue + docs, snapshot-first)**: the Solana
  perp-DEX cull DRIFT / PACIFICA / MANGO / ZETA / FLASH / SOLAYER / PICASSO / CAMBRIAN; defunct cefi exchanges BITSTAMP
  / HUOBI / GEMINI / PHEMEX; tradfi ICE (Databento purge + non-MVP → quarantine), Barchart VIX cash (retired).
- **Kept registered (NOT purged)**: **BINANCE-DELIVERY** (live COIN-M product — descope from MVP backfill, keep the UAC
  scaffold, mark non-MVP), KALSHI-PERP + POLYMARKET-PERP (roadmap), LIGHTER-ZKSYNC (blocked-credentials scaffold),
  EXTENDED-STARKNET (live MVP). (LIGHTER/EXTENDED/PACIFICA are CeFi-classified per §6.)

## 11. Operator decisions log (2026-07-18)

Equity `-USD` on all four surfaces · cefi venue = HYPHEN · ASTER = per-symbol real quote (mostly USDT, tail USD1/USDC —
NOT hardcoded) · cefi & tradfi bundle path shapes kept per-AG · tradfi daily = `ohlcv_24h` · DERIBIT quote = gating P0 ·
POOL key = 3-segment fee-in-symbol · defi two-id model kept (Option A, no mass rewrite) · retire legacy LENDING →
A_TOKEN/DEBT_TOKEN · instrument_type lowercase in path/column / UPPER in id · culled-venue purge dead-only +
snapshot-first

- keep LIGHTER/EXTENDED/KALSHI-PERP/POLYMARKET-PERP/BINANCE-DELIVERY · combos = leg-aware signed-weight · restore the
  raw distinct-values data-status enumeration view · prediction is shard-grain pattern #3 (CQG bundle).

## 12. Where the work lives

Migration close-outs (code + backfilled + forward data):
`plans/active/{cefi,tradfi,defi,prediction}_consolidated_closeout_2026_07_18.md`. Detailed axis SSOTs:
`canonical-instrument-ids.md` (builder grammar) · `defi-canonical-naming-ssot.md` (defi vocab) ·
`availability-manifest-and-data-status.md` (shard atom + manifest) · `shard-granularity-cefi.md` (cefi bundles) ·
`honest-coverage-model.md` (denominator) · `pipeline-mode-partition.md` (source-aware partition).

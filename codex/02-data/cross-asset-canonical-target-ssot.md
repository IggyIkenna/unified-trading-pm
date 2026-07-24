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
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/shard-granularity-cefi.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/data-status-drilldown-hierarchy.md,
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
last_reviewed: 2026-07-20
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
`/codex/02-data/availability-manifest-and-data-status.md:47-71` governs which columns _earn_ a place):

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
  `/codex/02-data/availability-manifest-and-data-status.md:57-60` prediction keys on `canonical_question_group`.)
- **DeFi availability is by DATA day**, not capture time: rows land in `day={YYYY-MM-DD}` by their event/block
  timestamp. Under the **target per-instrument model** a re-capture **OVERWRITES** the one `{canonical_id}.parquet` (no
  `{…}_{capture_ts}.parquet` pile-up), so the duplicate/phantom-row dedup the old batch model needed **disappears at the
  source**. The **IS** per-(venue,chain) universe with `available_from` (real on-chain genesis, `eth_getCode`
  binary-search) + `available_to` (TVL-drop delist) is the honest denominator: out-of-window = out-of-scope; in-window +
  0 rows = `empty_confirmed`. (Legacy batch files migrate to per-instrument via a column+row UNION merge — see the DeFi
  close-out plan.)
- **instruments-service (reference) side is thinner**: prediction IS = `venue → dates` (no `data_type` axis,
  `VENUE_REFERENCE_DATA_CAPABILITIES={}`); MTDS drilldown is CQG-**above**-data_type
  (`/codex/02-data/data-status-drilldown-hierarchy.md:42`).

## 2. Canonical instrument-id grammar

`instrument_type` carries **three independent cases** — do not collapse them (see §7): the **id middle segment** is
**UPPER** (`VENUE:TYPE:BODY`), the **GCS path segment** is **lowercase**, and the **manifest `instrument_type` COLUMN**
is **UPPERCASE**. Builder SSOT + full per-type grammar:

> **⛔ corrected 2026-07-20, operator ruling D1** — recorded in
> [`plans/active/data_pipeline_reconciliation_skill_2026_07_20.md`](../../plans/active/data_pipeline_reconciliation_skill_2026_07_20.md)
> § "OPERATOR DECISIONS — ALL THREE RULED 2026-07-20". ~~Was: "it is **lowercase** in the GCS path segment and manifest
> column".~~ That sentence bundled the path segment and the manifest column into one case. The **COLUMN is UPPERCASE**;
> only the **path segment** is lowercase. The id middle segment was never in question.

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

| AG     | shard (venue · data_type · type)                                     | representative canonical id / key                                 | notes                                                                                                                                                    |
| ------ | -------------------------------------------------------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| cefi   | BINANCE-FUTURES · trades · perpetual                                 | `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN`                          | flat; +book5/derivative_ticker/liquidations                                                                                                              |
| cefi   | BINANCE-SPOT · trades · spot_pair                                    | `BINANCE-SPOT:SPOT_PAIR:BTC-USDT`                                 | no margin on spot                                                                                                                                        |
| cefi   | BYBIT · trades · future                                              | `BYBIT:FUTURE:BTC-USD@INV-20231201`                               | per-contract (not a bundle)                                                                                                                              |
| cefi   | DERIBIT · trades · options_chain (underlying=BTC)                    | `DERIBIT:OPTION:BTC-USD@INV-20260401-3250-C`                      | pattern #2; quote ALWAYS                                                                                                                                 |
| cefi   | DERIBIT · trades · futures_chain (underlying=AVAX)                   | `DERIBIT:FUTURE:AVAX-USDC@LIN-20260401`                           | pattern #2; USDC=linear                                                                                                                                  |
| cefi   | OKX-SWAP · trades · perpetual                                        | `OKX-SWAP:PERPETUAL:BTC-USD@INV`                                  | folds to OKX in Layer-1                                                                                                                                  |
| cefi   | HYPERLIQUID · trades · perpetual                                     | `HYPERLIQUID:PERPETUAL:BTC-USDC@LIN`                              | on-chain CLOB → cefi                                                                                                                                     |
| cefi   | ASTER · derivative_ticker · perpetual                                | `ASTER:PERPETUAL:BTC-USDT@LIN`                                    | per-symbol real quote (mostly USDT)                                                                                                                      |
| tradfi | CME · ohlcv_1m · futures_chain (ES→SP500)                            | `CME:FUTURE:SP500-USD@LIN-20260619`                               | pattern #2, stem=SP500                                                                                                                                   |
| tradfi | CME · ohlcv_1m · options_chain (ES)                                  | `CME:OPTION:SP500-USD@LIN-20260117-7960-C`                        | fixes the `E3AN6 C7960` space                                                                                                                            |
| tradfi | NASDAQ · ohlcv_1m · equity                                           | `NASDAQ:EQUITY:AAPL-USD`                                          | `-USD` on all four surfaces                                                                                                                              |
| tradfi | CBOE · ohlcv_1m · futures_chain (VX→VIX)                             | `CBOE:FUTURE:VIX-USD@LIN-20260722`                                |                                                                                                                                                          |
| tradfi | CBOE · ohlcv_24h · index (Treasury)                                  | `CBOE:INDEX:US10Y-USD`                                            | daily = `ohlcv_24h`                                                                                                                                      |
| tradfi | FX · ohlcv_24h · currency (KRW)                                      | `FX:CURRENCY:KRW-USD`                                             | Yahoo daily                                                                                                                                              |
| tradfi | CME · ohlcv_1m · combo                                               | `CME:COMBO:SP500-CALENDAR-20240621-20240920`                      | legs w/ signed weights in the definition                                                                                                                 |
| defi   | UNISWAP_V3 · dex_pool_state · pool                                   | `UNISWAP_V3-ETHEREUM:POOL:USDC-WETH-500`                          | 3-seg; addr = machine `instrument_id`                                                                                                                    |
| defi   | UNISWAP_V3 · oracle_prices · spot_asset                              | `UNISWAP_V3-ETHEREUM:SPOT_ASSET:WETH`                             | canonical == instrument_id (converge)                                                                                                                    |
| defi   | AAVE_V3 · lending_indices · a_token / debt_token                     | `AAVE_V3-ETHEREUM:A_TOKEN:aUSDC` / `:DEBT_TOKEN:variableDebtUSDC` | pooled → real symbol                                                                                                                                     |
| defi   | MORPHO · lending_indices · a_token (isolated)                        | `MORPHO-BASE:A_TOKEN:AUSDC-EURC-<marketId8>`                      | isolated → synthesized symbol                                                                                                                            |
| defi   | LIDO · lst_rates · lst                                               | `LIDO-ETHEREUM:LST:stETH`                                         | case preserved                                                                                                                                           |
| defi   | GMX · perp_funding · perpetual                                       | `GMX:PERPETUAL:BTC-USD`                                           | DEX-pool perp → defi; **no chain suffix**                                                                                                                |
| defi   | ORCA · dex_pool_swaps · solana_amm_pool                              | `ORCA-SOLANA:SOLANA_AMM_POOL:SOL-USDC-TS64`                       | fee/tick-spacing discriminator, `mtds@0d83a8a9` (2026-07-24) — was bare `SOL-USDC`, see `defi-canonical-naming-ssot.md` § Solana AMM pool SYMBOL grammar |
| pred   | POLYMARKET · prediction_canonical_question_group · prediction_market | key = `canonical_question_group` (`SPORTS_EPL_MATCH`)             | pattern #3 bundle; per-market rows carry CID id                                                                                                          |
| pred   | KALSHI · trades · prediction_market                                  | per-CID `instrument_id` (market ticker)                           | flat per-market raw object                                                                                                                               |

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

> **🟡 STATUS BANNER — RULED 2026-07-20 (operator, D2). Supersedes the "PARKED / UNRULED" framing of the earlier
> correction banner preserved below.** The retire IS the target — **but it is NOT YET IMPLEMENTED.** Two failure modes,
> both explicit:
>
> 1. **DO NOT re-execute the retire naively.** Doing it in the original order reproduces a measured outage (see the
>    preserved banner below). The prerequisite is a writer fix, not a migration.
> 2. **DO NOT "fix" the interim state as if it were drift.** Market/event flat `LENDING` is **`migration_pending`** — it
>    is **NOT** a fresh non-canonical finding, and it is **NOT** an unruled/refused axis either. Any tooling that reads
>    this doc (incl. the reconciliation skill + finding taxonomy) MUST NOT flag it as a violation.
>
> **TARGET (ruled 2026-07-20, operator D2 — deliberately AGAINST the worker recommendation to ratify the interim):**
> flat `LENDING` is retired **everywhere**, not holdings-only. Every lending position = one **`A_TOKEN`** (supply leg) +
> one **`DEBT_TOKEN`** (borrow leg), across every lending data_type.
>
> **CURRENT IMPLEMENTED REALITY (verified in code 2026-07-20, unchanged by the ruling):** uniform flat **`LENDING`** for
> the market/event data_types (`lending_indices`, `liquidation_events`, `flash_loan_events`, `position_data`); **only
> `holdings`** uses the `A_TOKEN`/`DEBT_TOKEN` split.
>
> **WHY THE GAP EXISTS — verified history, not hearsay:** the retire was attempted once (Wave B, UAC `@e319864f`) and
> **REVERSED** (`wn12e7itc` → `unified-api-contracts@ad4886ae`) because it broke **5+ MTDS lending writers** into
> `attempted_failed`/zero-data and **desynced the shard atom** (GCS `instrument_type=a_token` vs manifest `lending`).
> Cited sources actually read:
> [`plans/active/defi_consolidated_closeout_2026_07_18.md`](../../plans/active/defi_consolidated_closeout_2026_07_18.md)
> :685 ("REVERSED (un-retire `wn12e7itc`): making `build_instrument_id(...LENDING...)` raise OVER-REACHED"), :698, :1469
> and :1496;
> [`issues/canonical_closeout_open_questions_2026_07_18.md`](../../plans/active/issues/canonical_closeout_open_questions_2026_07_18.md)
> :177-182 (the break + the un-retire), :64 (the `marginfi`/`fluid` guard `if instrument_type not in (None, LENDING)`
> minting A_TOKEN/DEBT_TOKEN → returning **zero** rows) and :73 (the **~16.7M** `lending` rows to migrate); and the
> already-accepted-exception rationale in
> [`reconciliation-finding-taxonomy.md`](./reconciliation-finding-taxonomy.md):429.
>
> **MANDATORY ORDER — the ruling is on the destination, not on skipping the sequence. Steps are gates, not phases:**
>
> 1. **Fix the 5+ MTDS lending writers first and PROVE them green** (`lending_indices` for the 6 EVM venues,
>    `liquidation_events`, `flash_loan_events`, `position_data`, `solana_defi`) — each currently survives only because
>    UAC still builds flat `LENDING`; each fails shard-level `except ValueError` → `record_failed` the moment it does
>    not. Green = real captured rows, not an absence of exceptions.
> 2. **THEN migrate the ~16.7M rows** to `A_TOKEN`/`DEBT_TOKEN`.
> 3. **THEN re-sync the shard atom** across GCS path / manifest / data-status / UI so all four surfaces agree — the
>    partial A_TOKEN work-around's desync is exactly what step 3 exists to prevent.
>
> Until step 2 completes, this section's "RETIRED" text describes the **target**, not the estate.

<details>
<summary>Preserved superseded banner — added 2026-07-20, doc-reconciliation P1-09 (pre-ruling; retained for the record)</summary>

> **🟡 CORRECTION BANNER — added 2026-07-20, doc-reconciliation P1-09 (contradiction "DeFi flat `LENDING` — RETIRED vs
> interim-KEPT"). The blanket "RETIRED" below is NOT what the code implements. DO NOT re-execute the retire.**
>
> <!-- was: "The scope of the retire is HOLDINGS ONLY." — corrected 2026-07-20, operator ruling D2: holdings-only is the
> CURRENT reality, not the scope of the target; the target scope is ALL lending data_types. Superseded text preserved
> verbatim below. -->
>
> The scope of the retire is **HOLDINGS ONLY**. Wave B additionally retired flat `InstrumentType.LENDING` in the UAC
> id-builder to `UNSUPPORTED_BY_DESIGN` (`@e319864f`); that **over-reached** — it made `build_instrument_id(…LENDING…)`
> RAISE, which silently broke **5+ MTDS market/event lending writers** (`lending_indices` for 6 EVM venues,
> `liquidation_events`, `flash_loan_events`, `position_data`, `solana_defi`), each caught by a shard-level
> `except ValueError` → `record_failed` → **`attempted_failed`, zero data**; the partial A_TOKEN work-around then
> created a **shard-atom desync** (GCS `instrument_type=a_token` vs manifest `lending`). **Reversed via `wn12e7itc`.**
>
> **Interim implemented reality (VERIFIED in code 2026-07-20)** — `unified-api-contracts` `canonical_id_builder.py`
> carries `InstrumentType.LENDING` in both the SUPPORTED set (:148) and `_DEFI_TYPES` (:196), and
> `UNSUPPORTED_BY_DESIGN` is an **empty frozenset** (:182):
>
> - **HOLDINGS** → `A_TOKEN` / `DEBT_TOKEN` split, exactly as this section describes. Unaffected by the reversal.
> - **market/event data_types** (`lending_indices`, `liquidation_events`, `flash_loan_events`, `position_data`) →
>   uniform flat **`LENDING`**. Working and self-consistent across GCS path, column and manifest.
>
> **⛔ SUPERSEDED 2026-07-20 (operator ruling D2 — see the STATUS BANNER at the top of §5).** ~~The ruling is PARKED /
> UNRULED — this doc does NOT pick a side.~~ The operator RULED the FULL retire (all lending data_types). The option
> analysis below is retained as history. Options A (keep market-level `LENDING`; current interim; worker-recommended), B
> (key each to the reserve's `A_TOKEN`), and C (split per side) are stated with their costs in
> [`issues/canonical_closeout_open_questions_2026_07_18.md`](../../plans/active/issues/canonical_closeout_open_questions_2026_07_18.md)
> § D (:173-202). B or C each require a full 5+-writer MTDS migration, a Wave-D historical re-key and a shard-atom fix
> on both axes. Until the operator rules: `lending` on a market/event data_type is **NOT a canonicalisation finding**,
> and the §11 operator-log line "retire legacy LENDING → A_TOKEN/DEBT_TOKEN" reads **holdings-only**.

</details>

<!-- was: "Legacy flat `LENDING` is **RETIRED** _(holdings only — see the correction banner above)_." — corrected
2026-07-20, operator ruling D2: the retire is the target EVERYWHERE, and "holdings only" is the current implemented
reality rather than the scope. Rewritten as target-vs-reality below; see the status banner for the mandatory order. -->

Legacy flat `LENDING` is **RETIRED — this is the TARGET (operator D2, 2026-07-20), implemented TODAY for `holdings`
only** (market/event data_types are `migration_pending` on uniform flat `LENDING` — see the status banner above for the
mandatory writer-fix-first order; do not re-execute the retire naively and do not report the interim as drift). Every
lending position = one **`A_TOKEN`** (supply leg) + one **`DEBT_TOKEN`** (borrow leg) — because
`net_value = supply − borrow` needs both. `instrument_type` is uniform across all 11 protocols; the **symbol** has two
conventions (both canonical):

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

> **✅ RULED 2026-07-20 — operator ruling D1 (UPPERCASE column, catalogue wins).** Recorded in
> [`plans/active/data_pipeline_reconciliation_skill_2026_07_20.md`](../../plans/active/data_pipeline_reconciliation_skill_2026_07_20.md)
> § "OPERATOR DECISIONS — ALL THREE RULED 2026-07-20". The axis previously carried a `⛔ SCOPE CORRECTION 2026-07-20`
> banner declaring the manifest COLUMN case CONTESTED (Side A lowercase = this doc; Side B UPPERCASE =
> `plans/active/tradfi_consolidated_closeout_2026_07_18.md:375`, both citing the same operator on 2026-07-18). **Side B
> wins.** That banner is SUPERSEDED and the axis is no longer refused.
>
> The ruling was explicitly a **COST argument, not a correctness one**: UPPERCASE is the only option where the shipped
> code and the >8M already-migrated rows agree. **The revert is mechanical** if the operator ever reverses it.
>
> **Precision — three separate cases, never one rule:**
>
> 1. **manifest `instrument_type` COLUMN → UPPERCASE** (this is the ONLY leg the ruling changed; the catalogue enum
>    `{FUTURE, OPTION, EQUITY, ETF, INDEX, COMBO, SPOT_PAIR}` is SSOT for it).
> 2. **GCS path segment `instrument_type=` → lowercase** — unchanged, never in question, both sides always agreed.
> 3. **id middle segment (`VENUE:TYPE:BODY`) → UPPER** — unchanged, never in question.
>
> Consequences: the two already-shipped uppercase migration scripts (`instruments-service@555ddf1c` + the tradfi Phase-B
> script) are **RATIFIED** and their DRAIN-GATED `--apply` freeze is **LIFTED**. The defi rows not yet migrated UP are
> `migration_pending`, not a fresh non-canonical finding. Reconcilers stop emitting the [C2a]
> `REFUSED — awaiting operator ruling` verdict from
> [`reconciliation-finding-taxonomy.md`](reconciliation-finding-taxonomy.md) §5.1 and enforce UPPERCASE for the column.
>
> **DeFi carve-out, 2026-07-24 (operator, `adb28421d`,
> `plans/active/issues/cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md`) — "enforce UPPERCASE for the
> column" above does NOT apply to defi.** DeFi's corpus was measured genuinely mixed (not close-to-one-direction like
> cefi/tradfi/prediction), so its target is decided per-`instrument_type`-value, least-migration-cost: whichever casing
> already dominates for a given value becomes that value's target, the minority migrates — hard constraint, casing must
> be 100% internally consistent within each `(instrument_type, asset_group=defi)` pair post-migration, different values
> MAY land on different casings from each other. See `reconciliation-finding-taxonomy.md` §5.1 for the full correction
> chain. Execution: `plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md` "Manifest instrument_type case
>
> - venue-spelling unify" todo.

- **case — three independent legs, stated separately (do not collapse them):**
  - **manifest `instrument_type` COLUMN**: **UPPERCASE**. _(⛔ corrected 2026-07-20, operator ruling D1 — ~~was
    "LOWERCASE … + the manifest `instrument_type` column (writer grain)"~~; the original bundled the column with the
    path segment. Mixed case in the manifest COLUMN is drift to fold **UP**.)_
  - **GCS path segment** (`instrument_type={it}`): **lowercase** — unchanged.
  - **id middle segment** (`:POOL:`, `VENUE:TYPE:BODY`): **UPPER** — unchanged.
- **venue**: cefi = single HYPHENATED spelling (`BINANCE-FUTURES`, not `BINANCE_FUTURES`). defi = bare canonical
  PROTOCOL (`AAVE_V3` not `AAVEV3`/`AAVE`; `UNISWAP_V3` not bare `UNISWAP`; `COMPOUND_V3` not `COMPOUND`) + a **separate
  `chain=`** path segment (never the combined `PROTOCOL-CHAIN` overload in the path; the id joins them as
  `VENUE-CHAIN`).

## 8. Path templates

> **📐 HARD RULE (operator R2, 2026-07-21) — every data-at-rest tree uses the FULL canonical hive grammar** (the
> canonical key set incl. `pipeline_mode=` and `asset_group=`, in the order below), never a reduced/flat subset.
> `instrument_availability` / `market_lifecycle` / `futures_contracts` are the standing violations (`day=`/`venue=`
> only) → RULED HIVE, `migration_pending`. Build the ordered keys via the sink PREFIX, not the partition dict (the sink
> sorts dict keys alphabetically). See §11b R2 +
> [`../../plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md`](../../plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md).

- **cefi/tradfi flat**:
  `raw_tick_data/by_date/day={D}/pipeline_mode={mode}_{src}/asset_group={ag}/venue={V}/instrument_type={it}/data_type={dt}/{instrument_id}.parquet`
- **cefi bundle**:
  `…/instrument_type={options_chain|futures_chain}/data_type={dt}/underlying={U}/quote={Q}/margin={M}/ticks.parquet`
- **tradfi bundle**:
  `…/instrument_type={futures_chain|options_chain|combo}/data_type={dt}/underlying={BASE}/quote={QUOTE}/margin={MODE}/ticks.parquet`
  — **matches cefi 1:1** (tradfi = `quote=USD` / `margin=linear`; `@LIN` ↔ `margin=linear`). tradfi SINGLE types
  (`equity`/`etf`/`spot_pair`) keep the flat `{FULL_CANONICAL_ID}.parquet` stem.

  > **⛔ corrected 2026-07-20, doc-reconciliation P1-09 (contradiction "TradFi chain-bundle tail").** ~~Was:
  > `…/data_type={dt}/{PRODUCT_ROOT}.parquet` (flat stem — kept per the tradfi plan, deliberately different from cefi's
  > `underlying=/ticks.parquet` for now)~~. **SHIPPED CODE WINS.** §8 was written 2026-07-18 and superseded by the
  > 2026-07-19 operator ruling "match cefi's TWO shapes exactly"
  > ([`issues/tradfi_canonical_path_migration_design_2026_07_19.md`](../../plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md):37-45).
  > The writer is shipped (`uac@ad28e55a` + `mtds@145e4aae`, same doc :196) and the definitive 0-ORPHAN reconcile over
  > the full 2,734,646-object tradfi corpus classifies **528,961 objects as `MIGRATE_CHAIN_ADDQM`** — i.e. under the NEW
  > shape (same doc :61-62). A flat product-root tradfi chain stem is therefore **NON-canonical**.

- **defi**:
  `…/day={D}/pipeline_mode={mode}_{source}/asset_group=defi/venue={PROTOCOL}/chain={CHAIN}/instrument_type={it_lower}/data_type={dt}/{canonical_instrument_id}.parquet`
  — **venue BEFORE chain** (operator-locked, `defi-canonical-naming-ssot.md`); leaf stem == the symbolic canonical id ==
  the manifest key (§0, §1 pattern #1).

  > **⛔ corrected 2026-07-20, doc-reconciliation P1-09 (contradiction "DeFi leaf FILENAME").** ~~Was:
  > `{venue}_{chain}_{capture_ts}.parquet`~~ — the RETIRED capture-batch leaf. **This template contradicted §0 and §1
  > pattern #4 of THIS SAME DOC**, which state that capture-batch is RETIRED → folded into pattern #1. A stale template
  > inside the corpus's designated TIE-BREAKER doc is the single most dangerous doc defect in the corpus: every
  > downstream reader resolves conflicts by consulting §8, so this one line could re-authorise a retired write shape
  > across every defi writer. §1 wins — it matches the operator ruling 2026-07-18
  > ([`defi-canonical-naming-ssot.md`](defi-canonical-naming-ssot.md) § WRITE-MODEL SUPERSEDED banner) **and** the
  > completed R3 historical migration (**MIGRATION ALL-TERMINAL 30/30**, full 2020q1–2026q2 corpus migrated to
  > per-instrument,
  > [`defi_consolidated_closeout_2026_07_18.md`](../../plans/active/defi_consolidated_closeout_2026_07_18.md):1033-1035).
  >
  > **Known residual (do NOT read as canonical)**: the same entry defers PERP re-migration — the `{venue}_{ts}` bundles
  > for ASTER / HYPERLIQUID / GMX are still on disk in the old bundle shape and surface as coarse manifest rows, bundled
  > with the pending ASTER/HYPERLIQUID cefi-misfiling decision (same doc :1041-1044). They are a known gap, not a second
  > canonical form.

- **instrument_availability / market_lifecycle / futures_contracts (RULED, todo 1 of the R2 issue, 2026-07-22)**:
  `instrument_availability/by_date/day={D}/pipeline_mode={mode}_{src}/asset_group={ag}/venue={V}/instruments.parquet` —
  **no `instrument_type=` segment**: an availability LISTING is per (day, pipeline_mode, asset_group, venue), the same
  grain the writer has always used, just with the two missing hive keys added via the sink PREFIX (never the partition
  dict — the sink sorts dict keys alphabetically, `protocol_impls.py:26`). `market_lifecycle` and `futures_contracts`
  ride the identical shape (`market_lifecycle.parquet` / `futures_contracts.parquet` leaf). Shipped:
  `unified-trading-library@43fa6f3f` (registry template + layout-tolerant readers), `instruments-service@a9be6ce9`
  (writer sink-prefix + reader lockstep). `migration_pending` — the historical flat objects are not yet migrated; see
  [`../../plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md`](../../plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md)
  todos 7-8.

## 9. empty_confirmed vs out-of-scope (the denominator basis)

- **`empty_confirmed`** — a cell INSIDE the could-exist universe, attempted, source PROVABLY returned 0 (typed
  `EmptyConfirmedReason` + evidence, or UTL hard-raises). A materialized manifest row (`row_count=0`, blank id).
  **EXCLUDED from `reachable_coverage`, RETAINED in `all_shards`.**
- **out-of-scope** — a tuple that should NEVER generate → **no manifest row** (`NOT_IN_SCOPE` /
  `is_valid_shard_key=False` / `is_mvp()=False`). **Clipped from BOTH numerator and denominator.**
- DeFi's catalogue denominator is **circular** (built from the same subgraphs the manifest reads), so honest
  empty-vs-hole needs the **completeness oracle** (`enumerated / on_chain_truth`, fail-closed —
  `/codex/02-data/defi-completeness-oracle.md`). SSOT: `/codex/02-data/honest-coverage-model.md`,
  `…/honest-absence-downstream-handling.md`.

## 10. Kept vs dropped venues

- **Dropped / purged (dead — remove entirely from UAC + manifest + GCS + catalogue + docs, snapshot-first)**: the Solana
  perp-DEX cull DRIFT / PACIFICA / MANGO / ZETA / FLASH / SOLAYER / PICASSO / CAMBRIAN; defunct cefi exchanges BITSTAMP
  / HUOBI / GEMINI / PHEMEX; tradfi ICE (Databento purge + non-MVP → quarantine), Barchart VIX cash (retired).
- **Kept registered (NOT purged)**: **BINANCE-DELIVERY** (live COIN-M product — descope from MVP backfill, keep the UAC
  scaffold, mark non-MVP), KALSHI-PERP + POLYMARKET-PERP (roadmap), LIGHTER-ZKSYNC (blocked-credentials scaffold),
  EXTENDED-STARKNET (live MVP). (LIGHTER/EXTENDED are CeFi-classified per §6; PACIFICA CULLED 2026-07-16 — see §10.)

## 11. Operator decisions log (2026-07-18)

Equity `-USD` on all four surfaces · cefi venue = HYPHEN · ASTER = per-symbol real quote (mostly USDT, tail USD1/USDC —
NOT hardcoded) · cefi & tradfi bundle path shapes kept per-AG · tradfi daily = `ohlcv_24h` · DERIBIT quote = gating P0 ·
POOL key = 3-segment fee-in-symbol · defi two-id model kept (Option A, no mass rewrite) · retire legacy LENDING →
A_TOKEN/DEBT_TOKEN **[⛔ RULED 2026-07-20, operator ruling D2 — ~~was "HOLDINGS ONLY; market/event keying
PARKED/UNRULED"~~; the operator ruled the FULL retire (all lending data_types, not holdings-only). It is the TARGET, NOT
yet implemented — gated on the MTDS lending-writer fix
(`plans/active/defi_lending_writer_retire_prerequisite_2026_07_20.md`) → migrate → re-sync atom; see the §5 banner.
Market/event flat `LENDING` is `migration_pending`, not a finding.]** · instrument_type **COLUMN UPPERCASE / path
segment lowercase / id middle segment UPPER** **[⛔ corrected 2026-07-20, operator ruling D1 — ~~was "lowercase in
path/column / UPPER in id"~~; see the §7 ruling banner]** · culled-venue purge dead-only + snapshot-first

- keep LIGHTER/EXTENDED/KALSHI-PERP/POLYMARKET-PERP/BINANCE-DELIVERY · combos = leg-aware signed-weight · restore the
  raw distinct-values data-status enumeration view · prediction is shard-grain pattern #3 (CQG bundle).

### 11a. Operator decisions log — 2026-07-20

- **D1 — manifest `instrument_type` COLUMN case = UPPERCASE.** Ruled 2026-07-20 by the operator ("uppercase is fine"),
  recorded in
  [`plans/active/data_pipeline_reconciliation_skill_2026_07_20.md`](../../plans/active/data_pipeline_reconciliation_skill_2026_07_20.md)
  § "OPERATOR DECISIONS — ALL THREE RULED 2026-07-20". Supersedes the 2026-07-18 log line above, which stated the column
  was lowercase.
  - **Scope — the COLUMN only.** The **GCS path segment** stays **lowercase** and the **id middle segment** stays
    **UPPER**; neither was ever in question. Do not read this ruling as a path-segment or id migration. Full statement
    of the three legs: §7.
  - **Basis — explicitly a COST argument, not a correctness one.** UPPERCASE was chosen because it is the only option
    where the shipped code and the >8M already-migrated rows agree; lowercase would require un-shipping two migrations
    that have already rewritten those rows. It was NOT ruled more correct in principle.
  - **The revert is mechanical** if the operator ever reverses it — nothing downstream is designed around UPPERCASE
    being semantically privileged.
  - **Effect**: the two already-shipped uppercase migration scripts (`instruments-service@555ddf1c` + the tradfi Phase-B
    script) are RATIFIED and their DRAIN-GATED `--apply` freeze is **LIFTED**. The defi rows not yet folded UP are
    `migration_pending`, not a fresh non-canonical finding.

### 11b. Operator decisions log — 2026-07-21

Three rulings resolve contested-canonical axes. Each is a RULED **target** and is `migration_pending` until the named
writer(s) + data migration ship — see `canonical-cutover-register.md` §6a–§6c and the three issue docs.

- **R1 — features data-at-rest root = `by_date/day=` (SSOT).** Every features tree MUST carry the `by_date/day=` level.
  This RATIFIES the UTL paths registry, which already declares it (`registry.py:57` `delta_one/by_date/day=`, `:74`
  `onchain/by_date/day=`, `:90` `volatility/by_date/day=`). The features-cefi `delta_one` writer emitting
  `delta_one/day=` (no `by_date/` level, `feature_writer.py:132-136`) and the volatility writer's **bucket-root bypass**
  (`get_data_sink` with no `prefix=`, `volatility/core/feature_writer.py:152-155`) are therefore **NON-CANONICAL**.
  onchain/sports primary writers already carry `by_date/`. Fix + migration:
  [`../../plans/active/issues/features_by_date_root_canonicalisation_2026_07_21.md`](../../plans/active/issues/features_by_date_root_canonicalisation_2026_07_21.md).

- **R2 — HARD RULE: every data-at-rest bucket uses the FULL canonical hive grammar.** Every data-at-rest tree MUST use
  the full canonical key set **including `pipeline_mode=` and `asset_group=`, in the canonical ORDER** (§8) — never a
  reduced/flat subset. `instrument_availability` is FLAT today (`day=`/`venue=` only) in BOTH the registry
  (`registry.py:35`) and the live writer (`process_write.py:612` + `writers.py:201-208`); `market_lifecycle` and
  `futures_contracts` share the same reduced-flat shape. This resolves the "instrument_availability FLAT vs hive"
  contested axis → **RULED HIVE**. **Critical**: the UTL sink SORTS partition-dict keys ALPHABETICALLY
  (`protocol_impls.py:26`, `for k, v in sorted(partition.items())`), so the keys CANNOT be added to the partition dict
  (you would get `asset_group=/day=/pipeline_mode=/venue=` — wrong order, `day` not first). The fix MUST bake the
  ordered canonical keys into the sink **PREFIX** (as the sports lane does), and the registry template is the SSOT and
  must be updated too. Fix + migration:
  [`../../plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md`](../../plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md).

- **R3 — cefi chain-tail v6 canonical everywhere; migrate ALL v5.** The v6 tail
  `underlying={ROOT}/quote={Q}/margin={M}/ticks.parquet` is canonical everywhere; the v5 bare tail
  `underlying={ROOT}/ticks.parquet` is **LOSSY** (same-underlying USD/USDT + linear/inverse chains collide/overwrite)
  and must be migrated with none remaining. UAC (`partition_paths.py:252-253`), the reader (`reader.py:402-403`,
  v6-first/v5-fallback) and the W2 Tardis lane (`tardis_shared.py:668-669`) already emit/probe v6; only W1
  `PartitionedTickWriter` still emits bare v5 for cefi because it derives quote/margin ONLY under
  `asset_group=="tradfi"` (`partitioned_writer.py:291-292`), and the write-guard `_assert_canonical_tradfi_path` (`:83`)
  is tradfi-only. This resolves the "cefi chain-tail v5 vs v6 — two live-written shapes" contested axis → **RULED v6**.
  Fix + migration:
  [`../../plans/active/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md`](../../plans/active/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md).

## 12. Where the work lives

Migration close-outs (code + backfilled + forward data):
`plans/active/{cefi,tradfi,defi,prediction}_consolidated_closeout_2026_07_18.md`. Detailed axis SSOTs:
`canonical-instrument-ids.md` (builder grammar) · `defi-canonical-naming-ssot.md` (defi vocab) ·
`availability-manifest-and-data-status.md` (shard atom + manifest) · `shard-granularity-cefi.md` (cefi bundles) ·
`honest-coverage-model.md` (denominator) · `pipeline-mode-partition.md` (source-aware partition).

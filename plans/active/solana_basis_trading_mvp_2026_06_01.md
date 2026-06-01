---
title: "Solana basis trading MVP — data source redesign (post Bug-D saga)"
created: 2026-06-01
author: ikenna
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-defi
locked_by: live-defi-rollout
locked_since: 2026-06-01
status: active
priority: P0
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2
source:
  - issues/bug_d_prime_drift_backfill_2026_05_31.md (the saga that prompted this)
  - data.api.drift.trade/openapi.json (verified 2026-06-01 — full Velocity Data API spec)
  - DefiLlama yields-API probe 2026-06-01 (verified Orca SOL/USDC $28M TVL is most liquid)
---

# Solana Basis Trading MVP — Data Source Redesign

> **Why this exists**: 8 Drift bug iterations across 2026-05-29 → 2026-06-01 chased the wrong target (Helius signature
> walking for trade-level events). Root cause: nobody verified what `data.api.drift.trade` actually exposes BEFORE
> building the Helius integration. It exposes everything we need. This plan re-scopes the Drift backfill from scratch.

## The strategy

**Solana basis trade**: long SOL on spot DEX (Orca primary) + short SOL-PERP on Drift V2 → capture funding-rate carry.

When Drift funding is positive (longs pay shorts), short-perp + long-spot = receive funding minus borrow/fee costs.

## Required data inputs (closed set for MVP)

### Drift V2 SOL-PERP (CLOB hybrid w/ vAMM — short leg)

| Data type                     | Purpose                                     | Source (probed + verified)                                                                                                                                | Cadence                      |
| ----------------------------- | ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| `perp_funding`                | Carry signal (the trade's edge)             | `data.api.drift.trade/market/SOL-PERP/fundingRates/{Y}/{M}/{D}` JSON, free tier, full historical coverage verified 2024-06-01 → 2025-08-01+               | ~hourly                      |
| `perp_trades`                 | Fill-sim ground truth for backtest          | `data.api.drift.trade/market/SOL-PERP/trades/{Y}/{M}/{D}?format=csv` CSV, free tier, paginated (~5K rows/page), 2.7MB/day at peak                         | per-fill                     |
| `perp_mark_oracle`            | Top-of-book proxy + matching engine input   | Derive from `oraclePriceTwap` / `markPriceTwap` columns in `perp_funding` rows (free tier); for finer cadence query Pyth on-chain via Alchemy archive RPC | hourly free / per-block paid |
| `perp_open_interest`          | Position sizing + carry magnitude           | Derive from `baseAssetAmountWithAmm` column in `perp_funding` rows (free tier)                                                                            | hourly                       |
| `perp_amm_bid_ask` (deferred) | Higher-fidelity matching engine top-of-book | `/amm/bidAskPrice` (paid tier — 403 Forbidden on free; **NOT in MVP**)                                                                                    | sampled                      |

**Drift's Velocity Data API (`data.api.drift.trade`)** — verified live 2026-06-01:

- 54 endpoints in the OpenAPI spec
- Per-market per-day historical endpoints for funding, trades, swaps, deposits, insurance fund, predictions, rewards
- AMM endpoints (`/amm/bidAskPrice`, `/amm/oraclePrice`, `/amm/openInterest`) return 403 on free tier — paid tier
  required if we want them later

### Spot DEX (long leg)

| Venue                         | Pool                               | TVL (2026-06-01) | Status                                         |
| ----------------------------- | ---------------------------------- | ---------------- | ---------------------------------------------- |
| **Orca DEX SOL/USDC**         | (Whirlpool concentrated liquidity) | **$28,376,670**  | **PRIMARY** — most liquid Solana SOL/USDC pool |
| Raydium AMM WSOL/USDC pool #1 | (classic AMM)                      | $8,798,197       | SECONDARY                                      |
| Raydium AMM WSOL/USDC pool #2 | (classic AMM)                      | $5,431,551       | TERTIARY                                       |

Source: DefiLlama yields-API probed 2026-06-01 (`gs://yields.llama.fi/pools`). DefiLlama slug = `orca-dex` (not
`orca-whirlpools` as docs might suggest).

| Data type        | Purpose                                                                                                | Source                                                                                                                                        | Cadence              |
| ---------------- | ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| `dex_pool_state` | AMM curve at time T — reserves (Raydium classic) OR tick liquidity array (Orca Whirlpool concentrated) | On-chain via Alchemy archive RPC reads of pool account state at block heights                                                                 | 1m or per-swap event |
| `dex_trades`     | Spot fill ground truth                                                                                 | DefiLlama `/chartLendBorrow` is paid; per-swap events via Solana RPC `getSignaturesForAddress(<orca_pool_pda>)` filtered to swap instructions | per-swap             |
| `dex_spot_price` | Spot SOL price for basis calc                                                                          | Derive from `dex_pool_state` (reserves ratio) OR Pyth on-chain SOL/USD oracle                                                                 | per-block            |

**Note**: existing `solana_defi_handler.py` already routes Orca to `dex_pools/orca/SOLANA/` and Raydium to
`dex_pools/raydium/SOLANA/` for _live_ mode. The handler captures pool snapshots, not per-swap trades. For MVP backtest
we need to extend it OR add a per-swap event ingester.

## Helius scope (drastically narrower than what the Bug-D saga attempted)

**For MVP basis: Helius is NOT needed for Drift V2 at all.** Drift's own Velocity Data API has full coverage with zero
gap.

The only place Helius might be useful for MVP:

- **Per-swap events on Orca/Raydium** — when we ingest historical pool-state changes, the most efficient method is to
  enumerate per-swap signatures via Helius (`getSignaturesForAddress(<pool_address>, ...)`) then resolve each to extract
  swap amounts. This is bounded: Orca SOL/USDC pool sees ~10K-50K swaps/day max (vs 6.4M/day for Drift program-level
  traffic that broke the Bug-D handler). Tractable.
- Even simpler: query DefiLlama or use Solana's `getProgramAccounts` snapshots for pool state.

**Decision: Helius is OPTIONAL for spot DEX, NOT REQUIRED for Drift.** The entire sig-index work shipped this week
(`build_drift_v2_sig_index.py`, parallel walker, gap-fill VM saga, 6293 parts on GCS, 28GB) is **out of scope for MVP**.
The infrastructure stays in the repo for potential future use (e.g., if we later want to backfill full `tradeRecords`
independently of Drift's API rate limits), but it's not on the MVP critical path.

## Canonical UAC data types to declare

Add to `unified_api_contracts.canonical.crosscutting`:

```
PERP_FUNDING        (existing — Drift hourly funding rate rows)
PERP_TRADES         (NEW — per-fill ground truth, CLOB venues)
PERP_MARK_ORACLE    (NEW or derive from PERP_FUNDING — TWAP marks for matching engine)
PERP_OPEN_INTEREST  (NEW or derive from PERP_FUNDING.baseAssetAmountWithAmm)
DEX_POOL_STATE      (NEW — reserves OR tick-liquidity-array, AMM venues)
DEX_TRADES          (NEW — per-swap, AMM venues)
DEX_SPOT_PRICE      (NEW or derive from DEX_POOL_STATE — for basis calc)
```

The existing `dex_pools` (used by solana_defi_handler) is a snapshot. **`DEX_POOL_STATE` is the time-series version**
required for backtest replay — distinguish.

## Handler design

### Drift V2 ingester (NEW or extend `solana_defi_handler.py`)

```python
class DriftV2HistoricalIngester:
    """Per-day backfill for Drift V2 funding + trades using Velocity Data API."""

    async def collect_perp_funding(market: str, day: date) -> pd.DataFrame:
        # GET /market/{market}/fundingRates/{Y}/{M}/{D} (JSON)
        # Paginate via ?page=N until empty
        # Emits ~24 rows/day per market with full canonical fields

    async def collect_perp_trades(market: str, day: date) -> pd.DataFrame:
        # GET /market/{market}/trades/{Y}/{M}/{D}?format=csv (CSV)
        # Paginate via ?page=N
        # Emits 5K-100K rows/day per market (depends on volume)
```

Live mode: same handler, calls `/market/{market}/fundingRates` (most recent) + `/market/{market}/trades` (most recent) +
writes to live tick path.

### Spot DEX ingester (extend `solana_defi_handler.py`)

Pool state at frequent cadence — most efficient via Solana RPC archive reads:

```python
class OrcaWhirlpoolStateIngester:
    """Snapshot Orca Whirlpool SOL/USDC pool account state at block heights."""

    async def collect_pool_state(pool_address: str, day: date, samples_per_day: int = 1440) -> pd.DataFrame:
        # For each minute of the day:
        #   blockHeight = block_resolver.height_at(timestamp)
        #   account = alchemy_rpc.getAccountInfo(pool_address, commitment=confirmed, slot=blockHeight)
        #   decode Whirlpool account: tickArrayState, sqrtPrice, liquidity, feeRate
        # Emits 1440 rows/day for sampled state
```

For Raydium classic AMM, simpler decode (just reserveA, reserveB, fee).

### Why this design avoids the Bug-D trap

- **No raw sig walking**: Drift's API is the source of truth, not Helius
- **Bounded per-day volume**: even at peak SOL-PERP traffic, trades are ~50K-200K/day (vs 6.4M for all program activity)
- **CSV format for trades**: streaming-friendly, no JSON-decode-error retry loop needed
- **Pool state via on-chain RPC**: same Alchemy archive path the AAVE OP RPC fallback uses (proven, working)
- **No 6-builder-iteration saga**: design before code

## Migration / cleanup

1. **Keep the existing sig-index work** in the MTDS repo (`build_drift_v2_sig_index.py`, handler multi-prefix loader) —
   useful infrastructure for future "find a sig at a date" lookups. Do NOT relaunch any gap-fill walks for it.
2. **Optional GCS cleanup**: the 28GB of `_index/drift_v2_sig_index_parts*` parquets can be deleted to reclaim space
   (won't break anything). Defer to operator decision.
3. **Drift backfill VM saga halted**: the existing `mtds-solana-drift-backfill` VM workflow that tries to load the sig
   index is OBSOLETE for MVP. Replace with the new `DriftV2HistoricalIngester` invoked via `VM_TASK=mdps-backfill` +
   `VM_BACKFILL_CMD="python -m ... drift_v2_historical --market SOL-PERP --start ... --end ..."`.
4. **Existing live-mode `perp_funding` path in solana_defi_handler.py**: works fine, no change needed; ingestion stays.

## Implementation phases

### Phase 1 — Drift V2 historical ingester (~1 day)

- New `DriftV2HistoricalIngester` class in MTDS handlers
- CLI:
  `python -m market_tick_data_service.scripts.backfill_drift_v2_historical --market SOL-PERP --start 2025-01-08 --end 2026-06-01 --data-types funding,trades`
- Pagination + retry on transient errors (the JSON-decode-error pattern won't reappear because we're not walking
  individual sigs; we're paginating per-day endpoints)
- Output: `perp_funding/drift/...parquet` (existing path) + new `perp_trades/drift/...parquet`
- Unit tests + integration tests (mocked Drift API responses)

### Phase 2 — Orca Whirlpool state ingester (~1.5 days)

- New `OrcaWhirlpoolStateIngester` class
- Use existing `AlchemyBaseClient` + `BlockResolver` (same pattern as Aave V3 OP RPC fallback)
- Whirlpool account decoding (use `orca-sdk` or hand-decode via known layout)
- 1440 samples/day per pool × ~13 SOL pools = ~18K rows/day (trivial)
- Output: new `dex_pool_state/orca/SOLANA/...parquet`

### Phase 3 — Backtest harness integration (~1 day)

- Wire the new data types into the backtest engine
- Verify fill simulation on a known SOL-PERP funding-positive day
- Compare backtest PnL vs known-good benchmark

### Phase 4 — Live mode + paper trade (~1 day)

- Extend live handler for both Drift (already exists, just confirm contract) + Orca (new)
- Run paper trade for 24h on SOL basis
- Promote to live wallet on operator ack

## Success criteria

| Phase | Done-when                                                                                                                                                                                     |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | `perp_funding/drift/SOL-PERP/day=*/...parquet` exists for every day 2024-06-01 → 2026-06-01; `perp_trades/drift/SOL-PERP/day=*/...parquet` exists for every day with > 0 rows for active days |
| 2     | `dex_pool_state/orca/SOLANA/Whirlpool_SOL_USDC/day=*/...parquet` exists with 1440 rows/day; sample-check derived price matches known SOL/USDC price within 1%                                 |
| 3     | Backtest run for 2025-08-01 → 2025-08-31 produces non-fictional PnL series; matching engine documents top fills, slippage costs                                                               |
| 4     | Paper trade 24h on SOL basis; flat PnL after fees ≈ funding earnings - slippage; promote to live wallet after operator ack                                                                    |

## Risks + open questions

- **Drift API rate limits**: free tier limits unknown. Need to probe during Phase 1. If 429s appear, add backoff or
  shard calls across multiple IPs.
- **Drift AMM endpoints (`/amm/bidAskPrice` etc.)**: appear in OpenAPI spec but return 403
  (`x-amzn-errortype: ForbiddenException`, `x-cache: Error from cloudfront`) — same response as any undefined path.
  Pricing investigation 2026-06-01 found NO public paid tier. Interpretation: AMM endpoints are NOT deployed on the
  public gateway. Derive equivalents from `perp_funding` row columns (`oraclePriceTwap`, `markPriceTwap`,
  `baseAssetAmountWithAmm`) for MVP.
- **Pagination limit on `/trades`**: CSV came back at 5000 rows — likely the page size. Per-day total could be 50K-200K
  (need ~10-40 paginated calls). Need to verify max pages and pagination cursor shape.
- **Drift API uptime**: this is our single point of failure for the perp leg. SLA unknown. Mitigation: cache
  aggressively; for live mode, fall back to DLOB API live data if Velocity API is down.
- **Orca SDK in Python**: account decoding may need bindings; alternative is hand-decoding the Whirlpool account layout
  (well-documented, 50-100 LOC of binary parsing).

## Out-of-scope (deliberately deferred — NOT MVP-blockers)

- Full Drift V2 `orderRecords` ingestion (matching engine higher fidelity than top-of-book)
- Drift V2 `liquidationRecords` (post-MVP risk model input)
- Cross-perp-venue arbitrage (multi-CLOB; MVP is Drift-only)
- Helius integration for any Drift V2 data type
- The sig-index walker work (kept as cold infrastructure)

## Codex SSOT updates

- `codex/04-architecture/drift-v2-data-sources.md` — NEW: document `data.api.drift.trade` as canonical, OpenAPI shape,
  free vs paid tier, MVP scope
- `codex/02-data/canonical-data-types.md` — add `PERP_TRADES`, `DEX_POOL_STATE`, `DEX_TRADES` declarations
- `codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — note that Drift IS adapter already exposes
  `_DRIFT_S3_ARCHIVE_URL_TEMPLATE`; add a parallel `_DRIFT_VELOCITY_API_URL_TEMPLATE` for the new ingester
- Update or supersede `plans/active/issues/bug_d_prime_drift_backfill_2026_05_31.md` (it documented the broken path;
  this plan replaces it)

## Operator decisions — RESOLVED 2026-06-01

1. **Drift API paid tier?** — **N/A** (no public paid tier exists). Pricing-investigation 2026-06-01 found the 403 on
   AMM endpoints is AWS API Gateway's "no matching route" response (`x-amzn-errortype: ForbiddenException`,
   `x-cache: Error from cloudfront`) — same response as `/pricing`, `/docs`, `/auth` and other undefined paths. AMM
   endpoints appear in OpenAPI spec but are NOT live on the public gateway. Free-tier endpoints (per-day funding/trades)
   suffice; AMM data is derivable from `perp_funding` row columns (`oraclePriceTwap`, `markPriceTwap`,
   `baseAssetAmountWithAmm`).

2. **Spot DEX scope — ALL FOUR** (operator ack 2026-06-01): **Orca + Raydium + Phoenix + Jupiter**. Phase 2 extends from
   2 ingesters to 4. See "Updated spot DEX scope (Phase 2 expansion)" section below.

3. **Backtest start date — 2024-06-01** (operator ack 2026-06-01) — 2-year window. Drift Velocity API funding coverage
   verified back to this date in probe.

## Updated spot DEX scope (Phase 2 expansion)

| Venue           | Pool                                  | Type                         | TVL (2026-06-01)                       | Ingestion path                                                                                                                                                     |
| --------------- | ------------------------------------- | ---------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Orca DEX**    | SOL/USDC Whirlpool                    | Concentrated-liquidity AMM   | $28.4M                                 | On-chain RPC of Whirlpool account state (tick liquidity array + sqrtPrice + liquidity + feeRate) at block heights via Alchemy archive                              |
| **Raydium AMM** | WSOL/USDC pool #1 (top TVL) + pool #2 | Classic constant-product AMM | $14.2M combined                        | On-chain RPC of pool account state (reserveA, reserveB, fee) at block heights via Alchemy archive                                                                  |
| **Phoenix**     | SOL/USDC orderbook                    | CLOB                         | ~$1-5M                                 | On-chain RPC of Phoenix market account state (bid/ask levels per slot) at block heights via Alchemy archive                                                        |
| **Jupiter**     | (aggregator)                          | Routing over the above       | n/a (routes through underlying venues) | `https://quote-api.jup.ag/v6/quote?inputMint=...&outputMint=...&amount=...` periodic quote sampling; for backtest replay, reconstruct from underlying venue states |

**Updated Phase 2 estimate**: ~2.5 calibrated AI-days (4 ingesters, all on same Alchemy archive RPC pattern + Jupiter
HTTP API). Total MVP estimate: ~5.5 calibrated AI-days (vs prior 4.5).

### Updated Phase 2 — ingesters

- `OrcaWhirlpoolStateIngester` — Whirlpool account decode, 1440 samples/day (1-min cadence) per pool
- `RaydiumClassicAmmIngester` — Pool reserve account decode, 1440 samples/day per pool
- `PhoenixOrderbookIngester` — Phoenix market account decode (asks + bids levels), 1440 samples/day per market; bonus:
  per-orderbook-event ingestion via Phoenix's event emitter
- `JupiterQuoteIngester` — sampled quote requests (e.g., quotes for 100/1K/10K USDC → SOL hourly) for routing-cost
  analysis + backtest comparison

Output paths (all under `gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/...`):

- `dex_pool_state/orca/SOLANA/Whirlpool_SOL_USDC/day=*/...parquet`
- `dex_pool_state/raydium/SOLANA/WSOL_USDC_<pool_id>/day=*/...parquet`
- `dex_orderbook/phoenix/SOLANA/SOL_USDC/day=*/...parquet`
- `dex_quote/jupiter/SOLANA/SOL_to_USDC_<size>/day=*/...parquet`

## Updated backtest range

- **2024-06-01 → 2026-06-01** (2-year window, operator ack 2026-06-01)
- Drift funding coverage verified back to 2024-06-01 in probe (sample: `fundingRate=0.003295083` for early 2024-06)
- Spot DEX state: on-chain via Alchemy archive RPC — Solana archive depth sufficient
- Per-day storage estimate across all data types: ~50MB/day × 730 days ≈ ~36GB total backfill payload

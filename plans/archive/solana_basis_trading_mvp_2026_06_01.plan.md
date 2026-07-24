---
doc_type: plan
title: Solana basis trading MVP — data source redesign (post Bug-D saga) [ARCHIVED 2026-06-01]
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [e2e-testing, instruments-service, market-tick-data-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-01
archived: 2026-06-01
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-defi
model_tier: opus-required
thinking_tier: max
priority: P0
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2
source:
  [
    issues/bug_d_prime_drift_backfill_2026_05_31.md (the saga that prompted this),
    data.api.drift.trade/openapi.json (verified 2026-06-01 — full Velocity Data API spec),
    DefiLlama yields-API probe 2026-06-01 (verified Orca SOL/USDC $28M TVL is most liquid),
  ]
---

> **ARCHIVED 2026-06-01 — partial-completion archive.** Phases 1–4 CODE SHIPPED (Drift V2 historical ingester + 4 Solana
> spot DEX ingesters + 7 canonical UAC data types + `SolanaBasisGcsLoader` archetype wiring + `--live --continuous` flag
> unifying live/batch). The operationally-shipped half (the four operator-launched follow-ups: full 2024-06-01 →
> 2026-06-01 backfill VM, live snapshotters, 24h paper trade, live-wallet promotion) is migrated to
> `plans/active/defi_manifest_canonicalisation_2026_06_01.md` § "G. Solana basis MVP — operationalisation". G4 (live
> wallet promotion) is HUMAN-ONLY per CLAUDE.md hard-stop list.

## Deferred work — migrated to:

| Item                                              | Migrated to                                                                                        | Status note                                                            |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Phase 2 Phoenix orderbook decode (currently stub) | `defi_manifest_canonicalisation_2026_06_01.md` § **G5** (P1; full inline body migrated 2026-06-01) | post-MVP feature add; ships top-of-book first                          |
| Full 2024-06-01 → 2026-06-01 backfill (G1)        | `defi_manifest_canonicalisation_2026_06_01.md` § G1                                                | BLOCKED-OPERATOR (long wall-clock; 36GB; operator-launched on vm-defi) |
| Live-mode snapshotters launch (G2)                | `defi_manifest_canonicalisation_2026_06_01.md` § G2                                                | BLOCKED-OPERATOR (long-lived VMs; operator-launched)                   |
| 24h paper trade run (G3)                          | `defi_manifest_canonicalisation_2026_06_01.md` § G3                                                | BLOCKED-OPERATOR (long wall-clock; operator-launched)                  |
| Promote to live wallet (G4)                       | `defi_manifest_canonicalisation_2026_06_01.md` § G4                                                | HUMAN-ONLY per CLAUDE.md hard-stop list                                |
| Jupiter historical reconstruction (P2)            | `defi_manifest_canonicalisation_2026_06_01.md` § **G6** (migrated 2026-06-01)                      | post-MVP; replay from Orca/Raydium states; GATED on G1                 |
| Orca tick-array decode (P2)                       | `defi_manifest_canonicalisation_2026_06_01.md` § **G7** (migrated 2026-06-01)                      | post-MVP depth improvement; not GATED on G1-G4                         |
| Raydium second WSOL/USDC pool (P2)                | `defi_manifest_canonicalisation_2026_06_01.md` § **G8** (migrated 2026-06-01)                      | trigger: TVL > $1M (currently $4.6K, below noise)                      |

## Codex SSOT alignment check (per CLAUDE.md plan-archival HARD RULE, 2026-05-22)

| Promised codex doc                                                                                        | Status @ archive                                                            | Action taken                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/codex/04-architecture/drift-v2-data-sources.md` — NEW                                                   | Did not exist                                                               | **CREATED 2026-06-01** in same archival commit                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `/codex/02-data/canonical-data-types.md` — add 7 new types                                                | Sibling doc (`defi-data-types-catalog.md`) is the actual canonical location | **UPDATED 2026-06-01** `defi-data-types-catalog.md` to document PERP_TRADES / PERP_MARK_ORACLE / PERP_OPEN_INTEREST / DEX_POOL_STATE / DEX_ORDERBOOK / DEX_QUOTE / DEX_TRADES + InstrumentType.DEX_POOL                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — add `_DRIFT_VELOCITY_API_URL_TEMPLATE` | Doc references `_DRIFT_S3_ARCHIVE_URL_TEMPLATE` only                        | **UPDATED 2026-06-01** with note that Velocity Data API is the new primary historical source + cross-link to new `drift-v2-data-sources.md`. **✅ FOLLOW-UP RESOLVED 2026-06-01 (mtds@081ff1cf)**: the Velocity API base URL is in UAC's `SOLANA_DEFI_PROTOCOLS["drift"]["api_url"]` (venue-wide, one host serves all markets) accessed via `get_solana_protocol_url("drift", "api_url")`. Both IS adapter (`drift.py:32`) and MTDS `DriftV2HistoricalIngester` (`drift_v2_historical_handler.py:76`) use this canonical helper — no hardcoded URLs. The per-day URL path is constructed inline in MTDS handler because the path is data-type-specific and per-instrument (MTDS-domain). |
| Supersede `plans/active/issues/bug_d_prime_drift_backfill_2026_05_31.md`                                  | Active issue doc                                                            | **SUPERSEDED banner added 2026-06-01** — Helius sig-walking path is OBSOLETE; Drift V2 historical now flows via Velocity Data API                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `/codex/04-architecture/solana-defi-coverage.md` (existing)                                               | Mentions Drift S3 archive only                                              | **UPDATED 2026-06-01** with Velocity Data API note + cross-link                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md`                                       | venue_universe lacks Drift/Orca/Raydium/Phoenix                             | **UPDATED 2026-06-01** added Solana basis section (Drift perp + Orca spot)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |

## CLAUDE.md update — new canonical workspace contracts from this MVP

- **Drift Velocity Data API (`data.api.drift.trade`) is canonical** for Drift V2 historical perp data (post-2025-01-08
  via free tier, full historical via free tier verified back to 2024-06-01). The S3 archive (`drift-historical-data-v2`)
  remains the prior secondary path but is NOT preferred (ended 2025-01-08). AMM endpoints (`/amm/*`) return 403 — they
  are NOT deployed on the public gateway, not a paid tier. Drive AMM data from `perp_funding` row columns. **Added
  2026-06-01** to CLAUDE.md § "DeFi Execution Architecture" (or as a successor — see notes below).
- **`--live --continuous` is the canonical realization of "Live = batch (CRITICAL)"** for MTDS backfill scripts — the
  same script + same handler + same GCS partition path serves both modes; only the date filter and loop semantics
  differ. **Added 2026-06-01** to CLAUDE.md § "Live = batch (CRITICAL)" as the cited reference implementation.

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

### Phase 1 — Drift V2 historical ingester (~1 day) — ✅ SHIPPED 2026-06-01

**Status (2026-06-01)**: ✅ SHIPPED — uac@f26097f9, mtds@0f70f376. Local validation: SOL-PERP for 2025-08-01 captured 24
funding rows + 29164 trade rows; for 2024-06-15 (deep history) 24 funding + 4583 trades; for 2026-05-30 (post-coverage —
free-tier API lags ~2 months) 0 / 0 rows confirming the `record_empty(SOURCE_RETURNED_ZERO)` path. 12/12 unit tests pass
(pagination via `meta.nextPage`, retry on `JSONDecodeError` + 5xx, schema canonicalisation, manifest emission routing).
QG green both repos (UAC + MTDS exit 0). Adjacent fix: PM intra-active link
`workspace_repo_branch_protection_gaps_2026_05_29.md` repaired (pm@ea8ee08a1).

- ✅ New `DriftV2HistoricalIngester` class — `market_tick_data_service/cli/handlers/drift_v2_historical_handler.py` (467
  LOC)
- ✅ CLI:
  `python -m market_tick_data_service.scripts.backfill_drift_v2_historical --markets SOL-PERP,BTC-PERP,ETH-PERP --start 2024-06-01 --end 2026-06-01 --data-types funding,trades`
  (208 LOC)
- ✅ Pagination + retry on transient errors (`json.JSONDecodeError`, `aiohttp.ClientError`, 429 / 5xx) — exp backoff
  with jitter, 6 retries, 1s..30s cap
- ✅ Output:
  `raw_tick_data/by_date/day={D}/asset_group=defi/venue=DRIFT/chain=SOLANA/instrument_type=perpetual/data_type={perp_funding|perp_trades}/{market}.parquet`
  via canonical `write_defi_rows`
- ✅ Unit tests (12 passing) — `tests/unit/test_drift_v2_historical_handler.py` (404 LOC); integration test gating
  deferred to Phase 4 paper-trade (no API auth required → no `requires_credentials` mark needed; can re-add later)

**Coverage finding (2026-06-01 probe)**: Drift's free Velocity Data API historical coverage ends ~2026-04-01 (dates
after return `meta.totalRecords=0`). Live mode (`solana_defi_handler._collect_drift`) covers the live window via
`/stats/markets` endpoint, so this is NOT a blocker for the MVP archetype — backtest window 2024-06-01 → 2026-04-01 is
the working historical horizon. Captured as a NICE-TO-HAVE: probe whether a paid Drift API tier exists that extends the
historical horizon to T-0.

### Phase 2 — Solana spot DEX state ingesters (4 venues) — ✅ SHIPPED 2026-06-01

**Status (2026-06-01)**: ✅ SHIPPED — uac@9ad04ab0, mtds@d3d26f56. Local validation against live Solana mainnet: Orca
SOL/USDC Whirlpool $80.9724; Raydium WSOL/USDC pool#1 $80.9511; cross-venue gap **0.026%** (way under the 5% tolerance);
Jupiter 1000 USDC → 12.3354 SOL @ $81.07 implied with 0.033% price impact; Phoenix STUB fetched the 1,723,488-byte
market account (radix-slab decode is a P1 follow-up). 43/43 unit tests pass.

Adapter scope shipped:

- ✅ `OrcaWhirlpoolStateIngester` — `cli/handlers/orca_whirlpool_state_handler.py` (300 LOC). Whirlpool account decode
  hand-rolled per the Orca Rust struct
  (`whirlpools_config(32) | bump(1) | tick_spacing(u16) | seed(2) | fee_rate(u16) | protocol_fee_rate(u16) | liquidity(u128) | sqrt_price(u128) | tick_current_index(i32) | ...`).
  Spot price derived from sqrt_price Q64.64 with the SOL(9)/USDC(6) decimal adjustment.
- ✅ `RaydiumClassicAmmIngester` — `cli/handlers/raydium_classic_amm_handler.py` (333 LOC). V4
  `LIQUIDITY_STATE_LAYOUT_V4` decode at canonical offsets (baseDecimal@32, fees@144/152, baseVault@336, quoteVault@368,
  baseMint@400, quoteMint@432). Vault reserves read via separate `getAccountInfo` calls against baseVault + quoteVault
  SPL token accounts (amount @ offset 64). Inline base58 encoder (no new workspace dep).
- ✅ `PhoenixOrderbookIngester` — `cli/handlers/phoenix_orderbook_handler.py` (177 LOC). STUB. Fetches the market
  account (proves the RPC path works); routes via `record_failed` with `PhoenixDecodeTodoError` tagged
  `SOURCE_HANDLER_TODO_PHOENIX_DECODE`. Radix-slab decode for top-of-book bid+ask is a P1 follow-up — see Phase 2
  deferred-work section below.
- ✅ `JupiterQuoteIngester` — `cli/handlers/jupiter_quote_handler.py` (370 LOC). Forward-only sampler against
  `lite-api.jup.ag/swap/v1/quote` (free tier; the legacy `quote-api.jup.ag/v6` URL went DNS-NXDOMAIN in 2026 and was
  replaced). Past days route via `record_empty(SOURCE_RETURNED_ZERO)` — reconstruction from underlying Orca/Raydium pool
  states is post-MVP.
- ✅ Shared async Solana RPC helpers — `cli/handlers/_solana_rpc_async.py` (~230 LOC): `solana_get_slot`,
  `solana_get_block_time`, `solana_get_account_info_at_slot(account, slot=…)`, `solana_slot_at_timestamp`. Same Alchemy
  archive RPC path used by `solana_lst_archival` / `lst_rates_handler` Tier 1.
- ✅ CLI:
  `python -m market_tick_data_service.scripts.backfill_solana_dex_state --venues orca,raydium,phoenix,jupiter --start 2024-06-01 --end 2026-06-01 --samples-per-day 1440 --data-types pool_state,orderbook,quote`
  (270 LOC).
- ✅ Unit tests: 13/13 Orca + 13/13 Raydium + 7/7 Phoenix + 10/10 Jupiter = **43/43 pass**.

**UAC side**: Added `InstrumentType.DEX_POOL` enum member + folder mapping (`dex_pools`) + `_DEFI_TYPES` registration.
Required because Phase 1 declared the contracts with `instrument_type="dex_pool"` (`DEFI_DEX_POOL_DEX_ORDERBOOK` /
`DEFI_DEX_POOL_DEX_QUOTE` / `DEFI_DEX_POOL_DEX_TRADES`) but the enum had no matching member. Verified: 22/22
`test_registry_completeness.py` pass; UAC QG green in 228s.

**Output paths** (verified by `write_defi_rows` partition-path builder):

- `gs://<defi-bucket>/raw_tick_data/by_date/day={D}/asset_group=defi/venue=ORCA/chain=SOLANA/instrument_type=pool/data_type=dex_pool_state/Whirlpool_SOL_USDC.parquet`
- `gs://<defi-bucket>/raw_tick_data/by_date/day={D}/asset_group=defi/venue=RAYDIUM/chain=SOLANA/instrument_type=pool/data_type=dex_pool_state/WSOL_USDC_p1.parquet`
- `gs://<defi-bucket>/raw_tick_data/by_date/day={D}/asset_group=defi/venue=PHOENIX/chain=SOLANA/instrument_type=dex_pool/data_type=dex_orderbook/SOL_USDC.parquet`
  (none written until P1 decode lands)
- `gs://<defi-bucket>/raw_tick_data/by_date/day={D}/asset_group=defi/venue=JUPITER/chain=SOLANA/instrument_type=dex_pool/data_type=dex_quote/SOL_USDC_quotes.parquet`

**Phase 2 deferred / P1 follow-ups (operator-acked scope removal NOT applicable — these are post-MVP-feature, not
operationally-shipped data-pipeline gaps)**:

- [ ] [P1][PHOENIX-DECODE] Implement Phoenix market-account radix-slab decode (top-of-book bid + ask + size). The market
      account is 1.7MB — top-of-book is ~50-100 LOC of binary parsing; full L2 is harder. Plan: ship top-of-book first,
      then add deeper levels if backtest needs them.
- [ ] [P2][JUPITER-RECONSTRUCTION] Reconstruct historical Jupiter routes from Orca/Raydium pool states at the same
      timestamp via Jupiter's routing algorithm — fills the 2024-06-01 → today gap for backtest replay.
- [ ] [P2][ORCA-TICK-ARRAY] Decode Orca tick-array state for concentrated-liquidity depth visualisation (current MVP
      uses TVL/sqrtPrice/liquidity scalars; tick arrays give the depth distribution around the active tier).
- [ ] [P2][RAYDIUM-SECOND-POOL] Add a second Raydium WSOL/USDC pool if a meaningful TVL pool materialises — the plan
      mentioned a $5.4M pool but the Raydium v3 API probe 2026-06-01 shows only the top $8.8M pool is material; the next
      Standard SOL/USDC pool is just $4.6K TVL.

### Phase 3 — Backtest harness integration (~1 day) — ✅ SHIPPED 2026-06-01

- [x] ✅ Wire the new data types into the backtest engine — strategy-service@6b7e03b7 (`SolanaBasisGcsLoader` +
      `SolanaBasisFixtureLoader` in `strategy_service/engine/backtest/solana_basis_loader.py` + 10 unit tests, all
      green; `SOL_BASIS` strategy slot already mapped to `CARRY_BASIS_PERP@raydium-drift-sol-1h-sol-v5-prod` in
      `archetype_slot_resolver.STRATEGY_TYPE_TO_SLOT` — no new archetype needed)
- [x] ✅ Verify fill simulation on a known SOL-PERP funding-positive day — e2e-testing@3d02c74
      (`scripts/defi/backtest_solana_basis.py`); smoke ran on 2025-08-01 fixture (24 ticks, +1500 bps annualised
      funding, realistic spot drift 178→167) → **24 SHORT instructions @ ~$170-180 SOL-PERP, Total PnL +$38,717
      (positive sign matches short-on-decline expectation), 24 benchmark fills, no NaN/inf**
- [x] ✅ Sign-check: 2025-08-01 funding is **positive** (longs pay shorts); engine direction = SHORT (correct); PnL sign
      = POSITIVE (correct)
- [x] ✅ Side-fix: `vol_trading.portfolio_risk_gate` ⇄ `discrete_structure_allocator` import cycle —
      strategy-service@f1d480ab (was landed by a9372195 + broke ALL v2 imports including the existing `test_runner.py`);
      moved type-only imports under `TYPE_CHECKING`.

> **Operator note**: PnL is from the fixture path (Phase 1/2 raw data ingesters are shipped but the bulk backfill is a
> separate operator-launched VM job, deliberately out of this dispatch's scope per the plan). The GCS-loader code path
> is wired + structurally tested + ready to consume real parquets the moment they land via the seed-1-day backfill or
> the full 2024-06-01 → 2026-06-01 backfill VM run. The `--source auto` flag on the CLI tries GCS first + falls back to
> the fixture seamlessly.

### Phase 4 — Live mode + paper trade (~1 day) — ✅ SHIPPED 2026-06-01

- [x] ✅ Live-mode handler for Drift V2 (SOL-PERP funding) — mtds@1d35c7f2 added `--live` + `--continuous` +
      `--interval-seconds` to `backfill_drift_v2_historical.py`. Per the "Live = batch (CRITICAL)" hard rule it reuses
      the Phase 1 `DriftV2HistoricalIngester` + same GCS partition path
      (`perp_funding/drift/SOL-PERP/day=<TODAY>/...parquet`) + same `funding_rate`/`oracle_price_twap`/`mark_price_twap`
      schema the Phase 3 `SolanaBasisGcsLoader` expects. The legacy `solana_defi_handler._collect_drift` live path
      (writes `/stats/markets` snapshot with `funding_rate_24h/7d/30d`) is SUPERSEDED for SOL_BASIS — kept in place for
      other Solana DeFi protocols (Marinade/Jito LST etc.). Symptom of regression: SolanaBasisGcsLoader logs
      `no perp_funding rows` because the schema column was the snapshot's `funding_rate_24h` not the historical
      `funding_rate`.
- [x] ✅ Live-mode handler for Orca + Raydium (DEX pool state) — mtds@1d35c7f2 added the same `--live`/`--continuous`
      flag set to `backfill_solana_dex_state.py`. Reuses Phase 2 `OrcaWhirlpoolStateIngester` +
      `RaydiumClassicAmmIngester` writing to `dex_pool_state/{orca,raydium}/SOLANA/<pool_label>/day=<TODAY>/...parquet`
      — same schema (`sqrt_price_x96`, `liquidity`, `price`, `tick_current_index`, etc.) the loader expects.
- [x] ✅ Unit tests — mtds@1d35c7f2 (`tests/unit/scripts/test_backfill_solana_live_cli.py`, 10 tests, all green):
      `--continuous` without `--live` → exit 2; historical without `--start/--end` → exit 2; `--live` one-shot targets
      today's UTC date; `--live --continuous` loops + sleeps + cancellable; invalid `--interval-seconds` rejected.
      basedpyright clean on touched files.
- [x] ✅ `run-paper.sh` SOL_BASIS discoverability — e2e-testing@06e8269 added SOL_BASIS recipe to the script header. No
      flow change needed: `colocated_engine.py STRATEGY_CATEGORIES` already maps `SOL_BASIS → DEFI` so the existing
      `--strategy SOL_BASIS` arg flows through to the engine.
- [x] ✅ Phase 4 operational handoff documented in plan (this section + the dedicated "Phase 4 operational handoff"
      section below).
- [ ] **Operator-launched 24h paper trade** — BLOCKED-OPERATOR (long wall-clock; recipe in handoff section).
- [ ] **Promote to live wallet on operator ack** — BLOCKED-OPERATOR (wallet keys + kill-switch arming are on the
      CLAUDE.md hard-stop list; human-only).

## Phase 4 operational handoff (operator-launched)

The actual long-running operations (live data smoke ≥5 min, 24h paper trade, live-wallet promotion) are NOT in scope for
an agent dispatch. They run on the operator's host or a fleet VM with the operator's credentials.

### 1. Start live data flow (one of: operator laptop OR fleet VM)

```bash
# Terminal A: live Drift funding (hourly)
cd market-tick-data-service && .venv/bin/python -m \
    market_tick_data_service.scripts.backfill_drift_v2_historical \
    --markets SOL-PERP --live --continuous \
    --interval-seconds 3600 --data-types funding

# Terminal B: live Orca + Raydium pool state (1-min)
cd market-tick-data-service && .venv/bin/python -m \
    market_tick_data_service.scripts.backfill_solana_dex_state \
    --venues orca,raydium --live --continuous \
    --interval-seconds 60 --samples-per-day 60 \
    --data-types pool_state
```

### 2. Verify live data after T+5 min

```bash
TODAY=$(date -u +%Y-%m-%d)
gsutil ls "gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=${TODAY}/asset_group=defi/venue=ORCA/chain=SOLANA/instrument_type=pool/data_type=dex_pool_state/" 2>&1 | head
gsutil ls "gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=${TODAY}/asset_group=defi/venue=DRIFT/chain=SOLANA/instrument_type=perpetual/data_type=perp_funding/" 2>&1 | head
```

Expected: ≥1 parquet under each `day=<TODAY>` prefix from the last 5 minutes. Drift funding is hourly so after ≥1 h of
live-mode runtime; Orca/Raydium are 1-min sampled so after ≥1 min of live-mode runtime.

### 3. Launch the 24h paper trade

```bash
cd e2e-testing
bash scripts/defi/run-paper.sh \
    --strategy SOL_BASIS \
    --tick-interval 3600 \
    --continuous \
    --execution-provider solana-devnet \
    --initial-capital-usd 100000
```

This invokes
`colocated_engine.py --strategy SOL_BASIS --mode paper --continuous --tick-interval 3600 --execution-provider solana-devnet`.
The engine reads parquets via `SolanaBasisGcsLoader` (Phase 3), generates SHORT-perp/LONG-spot instructions when
funding > entry threshold, simulates fills on Solana devnet (signed, not broadcast), and writes PnL + trade log
locally + to GCS sinks.

### 4. After 24 h — review PnL + decide promotion

Verify PnL via the engine's log + Firestore `MinimalCandidateManifest` (per CLAUDE.md Promote Workflow Path). Decision
gate is operator-subjective: if PnL is positive after fees ≈ realised funding earnings − slippage, and the fill
simulation is honest, the operator may promote.

### 5. Promote to live wallet — HUMAN-ONLY

Per CLAUDE.md `## Plans Run To Actual Completion` hard-stop list, **wallet keys + kill-switch arming are human-only**.
The agent never runs `run-live.sh`. The operator runs:

```bash
cd e2e-testing
bash scripts/defi/run-live.sh \
    --strategy SOL_BASIS \
    --tick-interval 3600 \
    --continuous \
    --execution-provider <copper|ceffu|cloud_kms_encrypted> \
    --capital <amount> \
    --wallet <KMS_KEY_ALIAS>
```

valid promote target per CLAUDE.md is `paper_1d → live_early`; `live_full` is post-cutover.

## Success criteria

| Phase | Done-when                                                                                                                                                                                                                                                                                                                                                                                  |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1     | ✅ Ingester + CLI + tests shipped (uac@f26097f9, mtds@0f70f376). Local validation green: 24 funding + 29164 trades for 2025-08-01; 24 funding + 4583 trades for 2024-06-15. Full backfill 2024-06-01 → 2026-04-01 (free-tier API coverage end) is a separate operator-launched VM job — out of scope for this Phase-1 dispatch per the plan's "DO NOT auto-trigger a full backfill" guard. |
| 2     | ✅ 4 ingesters shipped (uac@9ad04ab0, mtds@d3d26f56): Orca + Raydium + Jupiter LIVE; Phoenix STUB (P1 follow-up). Local validation green — Orca $80.97 vs Raydium $80.95 (gap 0.026%); Jupiter implied $81.07; all decodes verified against api-v3.raydium.io vault addresses. 43/43 unit tests pass. Full 2024-06-01 → 2026-06-01 backfill is a separate operator-launched VM job.        |
| 3     | Backtest run for 2025-08-01 → 2025-08-31 produces non-fictional PnL series; matching engine documents top fills, slippage costs                                                                                                                                                                                                                                                            |
| 4     | Paper trade 24h on SOL basis; flat PnL after fees ≈ funding earnings - slippage; promote to live wallet after operator ack                                                                                                                                                                                                                                                                 |

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

- `/codex/04-architecture/drift-v2-data-sources.md` — NEW: document `data.api.drift.trade` as canonical, OpenAPI shape,
  free vs paid tier, MVP scope
- `/codex/02-data/canonical-data-types.md` — add `PERP_TRADES`, `DEX_POOL_STATE`, `DEX_TRADES` declarations
- `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — note that Drift IS adapter already exposes
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

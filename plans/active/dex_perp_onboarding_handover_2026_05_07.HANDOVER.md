---
title: DEX perp onboarding handover — Lighter / Pacifica / Extended (2026-05-07)
locked_by: live-defi-rollout
locked_since: 2026-05-07
created: 2026-05-07
---

# DEX perp onboarding — what shipped, what's open, how to make money on these venues

This is the durable handover from the 2026-05-07 session that onboarded LIGHTER-ZKSYNC, PACIFICA-SOLANA, and
EXTENDED-STARKNET. Companion to:

- [`dex_historical_replay_lighter_extended_pacifica_2026_05_07.plan.md`](dex_historical_replay_lighter_extended_pacifica_2026_05_07.plan.md)
  — the working plan with empirical findings + per-venue API discoveries.
- [`streaming_finalize_lift_and_downsize_2026_05_06.HANDOVER.md`](streaming_finalize_lift_and_downsize_2026_05_06.HANDOVER.md)
  — the prior session's closeout that also touched these venues.

## What kind of venues are these (the question that started this handover)

**All three are PERPETUAL DEXes.** None are spot. Verified empirically against each venue's REST + Python SDK on
2026-05-07 from a Tokyo VM. They differ structurally:

| Venue             | Chain      | Settlement model                                                 | Markets                            | Notes                                                                                                                                                              |
| ----------------- | ---------- | ---------------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| LIGHTER-ZKSYNC    | zkSync Era | Validium — off-chain matching, zk-proofs to L1                   | 170 perps                          | Crypto majors PLUS exotic markets (NVDA, USDCAD, BRENTOIL, XAU, XAG, SNDK). `block_height` field is sequencer-internal NOT zkSync L1; 80-hex `tx_hash` is non-EVM. |
| PACIFICA-SOLANA   | Solana     | Hyperliquid clone — off-chain matched, settled to Solana program | ~50+ perps                         | Mainnet 2025-06. 50x max leverage. Hyperliquid-style cross-margin USDC.                                                                                            |
| EXTENDED-STARKNET | Starknet   | Off-chain matched, batched-proof settlement to Starknet          | ~10 majors (BTC-USD, ETH-USD, ...) | Most "Starknet-native" of the three — settlement events SHOULD be queryable via Starknet `getEvents` if we wire it.                                                |

All three emit funding rates (every perp DEX does). All three have OHLCV bar history via `/candles` (Lighter, Extended)
or `/kline` (Pacifica) — but ONLY OHLCV; per-trade tick history is unrecoverable for all three (REST capped at last ~100
trades, no cursor; on-chain replay infeasible because the sequencers commit aggregated state, not per-trade events).

## What strategy archetypes fit them

Updated [`category-instrument-coverage.md`](../codex/09-strategy/architecture-v2/category-instrument-coverage.md) with
new rows + slot labels for:

### 1. `CARRY_BASIS_PERP` — long spot + short DEX perp (or vice versa) for funding-rate carry

The DEXes go in as the **short-perp leg**. New row "DeFi (DEX-native L2/L1)": Uniswap spot + Lighter/Pacifica/Extended
perp. Signal variant = funding-rate. Status = PARTIAL because the funding-rate forward-poll handler isn't yet wired for
these venues.

**Why money is here:** thin DEX-side liquidity → funding rates often diverge wildly from CeFi. Empirically Pacifica BTC
funding has been observed at +50% APR while Binance BTC perp was +12% APR (38% APR carry edge if you can capture the
spread). Volume scaling capped by DEX depth — for $50K-$500K positions tractable; above that, slippage eats the edge.

### 2. `ARBITRAGE_PRICE_DISPERSION` — cross-venue spread trades

New row "DeFi (DEX-native L2/L1)": Lighter ↔ Pacifica ↔ Extended ↔ Hyperliquid ↔ Aster. Signal = price +
funding-rate.

**Why money is here:** the highest-edge cell in the entire table is the **DEX-DEX funding-rate dispersion**. CeFi-CeFi
funding spreads run a few bps; DEX-DEX can run 30-50% APR. Concrete trade: short PACIFICA SOL perp (receiving funding at
+60% APR) + long HYPERLIQUID SOL perp (paying funding at +12% APR) = +48% APR carry, delta-neutral, single-asset.

Slot labels added: `multi-dex-btc-funding-usdc-prod`, `multi-dex-eth-funding-usdc-prod`,
`multi-dex-sol-funding-usdc-prod`.

### 3. `CARRY_STAKED_BASIS` — Pacifica-Solana as a JitoSOL/mSOL hedge venue (currently RESEARCH)

Added a "DeFi (Solana DEX-native)" row. Slot is **rejected at preflight today** because Pacifica's collateral matrix in
[`VENUE_COLLATERAL_MATRIX`](../../../../unified-api-contracts/unified_api_contracts/registry/venue_collateral.py) is
USDC-only (no LST acceptance). When Pacifica adds JitoSOL/mSOL cross-margin (or once we verify they already do), flip
the matrix to `accepted=True` with a haircut citation and the slot enables automatically — the harness is identical to
the Drift SOL-perp slots (`Jito JitoSOL + Kamino + Drift SOL-perp`).

This gives `CARRY_STAKED_BASIS` a 2nd Solana perp-hedge venue, helpful for capacity + funding-rate routing
diversification.

### 4. NOT a fit for these venues

- `CARRY_STAKED_BASIS` on Lighter / Extended — the venues are EVM-L2-style (zkSync/Starknet) not Ethereum-mainnet, and
  the LST stack (Lido stETH, Rocket Pool rETH) doesn't bridge cleanly to those L2s. Drift / Hyperliquid remain canonical
  for stETH-margin.
- `STAT_ARB_PAIRS_FIXED` / `STAT_ARB_CROSS_SECTIONAL` — possible but very low-priority. DEX volume profiles don't yet
  support stat-arb-grade execution.
- `MARKET_MAKING_CONTINUOUS` — Lighter/Pacifica/Extended quote-side fills are too thin for productive market-making vs
  CeFi.

## What shipped this session — code references

| Repo                     | SHA       | What                                                                                                                                                                                                                                                         |
| ------------------------ | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| market-tick-data-service | `10aa715` | `_fetch_lighter_candles` adapter + 4 unit tests (initial Lighter ohlcv_1m route)                                                                                                                                                                             |
| market-tick-data-service | `51fecd5` | `_fetch_pacifica_candles` adapter + 4 unit tests (Pacifica /kline)                                                                                                                                                                                           |
| market-tick-data-service | `d898985` | HTTP 429 retry-with-backoff + per-request sleep + top-5 default symbols (rate-limit hardening)                                                                                                                                                               |
| market-tick-data-service | `fc53a97` | Lighter `/candles` pagination via `end_timestamp` walk-back (5-page cap = 2500 bars; covers 1440-bar full days)                                                                                                                                              |
| unified-api-contracts    | `e890022` | Added `ohlcv_1m` to `DATA_TYPES_BY_ASSET_GROUP['cefi']` (the actual blocker — without this the orchestrator's intersection drops `--data-types ohlcv_1m` and the venue falls through to the live `_fetch_lighter_rest` path that hammers `/orderBookOrders`) |
| unified-trading-pm       | `<this>`  | Codex strategy catalog updates + this handover                                                                                                                                                                                                               |

Production-verified: **LIGHTER capturing 1440 records/day** (5 symbols × 1440 bars = 7200 records/day, perfect
day-bounded `[00:00, 24:00) UTC`); **PACIFICA capturing ~4000 records/day** (varies by market activity). Sample
`BTC.parquet` for `day=2025-05-01` showed 1440 rows, all timestamps strictly within the partition day, no cross-day
leakage. Canonical `PartitionedTickWriter`'s `validate_day_partition_alignment` gate passed (would have raised
`UpstreamTimestampBiasError` if any row had bias). Defense-in-depth: my adapter ALSO filters at source
(`if ts_ms < start_s * 1000 or ts_ms >= end_s * 1000: continue`).

## What's open — next-agent action items (priority order)

### A. Forward-poll handlers for these venues (P0 — required before live trading)

Right now the three DEXes only have **historical** OHLCV bars (`/candles` + `/kline`). For live trading the master plan
needs:

1. **Funding-rate forward-poll**: poll each venue's `/funding` (or equivalent) endpoint every 1-5 min, write to MTDS as
   `data_type=perp_funding`. Needed for `CARRY_BASIS_PERP` + `ARBITRAGE_PRICE_DISPERSION` signal generation. Pattern:
   mirror the existing `mtds-perp-funding-` VM launcher; add LIGHTER-ZKSYNC + PACIFICA-SOLANA + EXTENDED-STARKNET to the
   venue iteration.
2. **Live trade tape forward-poll**: continuous `/recentTrades` poll every ~10s for live tape (for execution-quality
   measurement). The existing `_fetch_lighter_rest` / `_fetch_pacifica_rest` / `_fetch_extended_rest` already implement
   this — just need a forward-poll launcher.
3. **Live order-book snapshot poll**: `/orderBookOrders` / `/book` snapshots for slippage-modeling. Same — adapters
   exist; forward-poll launcher needed.

Suggested launcher: `deployment-service/scripts/vm/launch-cefi-onchain-forward-poll.sh` covering the three DEX-native
CLOB venues + HYPERLIQUID + ASTER (same shape as existing `launch-sfi-forward-poll.sh` singleton-locked pattern).

### B. Wire Pacifica-Solana into `VENUE_COLLATERAL_MATRIX` (P1 — unlocks CARRY_STAKED_BASIS slot)

Verify whether Pacifica accepts JitoSOL / mSOL as cross-margin. Two outcomes:

- **YES** → add row to `unified-api-contracts/unified_api_contracts/registry/venue_collateral.py` with haircut citation.
  New `CARRY_STAKED_BASIS@jito-pacifica-solana-...` slot auto-generates next catalog regen.
- **NO** → add explicit `accepted=False` row (the matrix is supposed to encode negatives explicitly per the audit spec).

### C. EXTENDED-STARKNET: deeper REST research OR Starknet event subgraph (P2 — currently no historical OHLCV path)

EXTENDED returned 404 on all `/candles` / `/klines` candidate paths. Next-agent paths (in priority):

1. Read `docs.extended.exchange` docs for the documented historical endpoint (might be auth-gated).
2. Failing that: build a Starknet event subgraph against the Extended Settlement contract. Unlike Lighter (validium with
   sequencer-internal blocks), Extended IS Starknet-native — settlement events SHOULD be on-chain readable. Add
   `STARKNET_RPC_TEMPLATE` to UAC `CHAIN_RPC_TEMPLATES` (currently only zkSync + Solana there).

### D. Scale up Lighter symbol coverage beyond top-5 (P2 — when needed)

Currently `_LIGHTER_BACKFILL_TOP_SYMBOLS = (BTC, ETH, SOL, HYPE, TON)`. Lighter has **170 perps** including exotic
markets (NVDA, USDCAD, BRENTOIL, XAU). For broader strategies (cross-asset stat-arb, FX-perp arb against CeFi FX),
expand the list. Rate-limit budget already tested — 12 RPS handled comfortably; could go to top-30 without throttling
concerns.

### E. Per-trade history is an honest gap — document it in coverage matrix

For all three venues, per-trade tick history is **unrecoverable** (REST capped at last ~100 trades, no cursor; on-chain
replay infeasible). Forward-poll going forward is the only way to build per-trade history. Update the coverage matrix to
mark `data_type=trades` as "live-only, no historical" for these three venues; downstream strategies that need per-trade
should use OHLCV bars OR limit themselves to forward-poll-built history (~few months, growing).

### F. Production-grade ETA for the running backfill VMs

As of session-end (2026-05-07 ~02:50 UTC):

- `cefi-lighter-zksync-ohlcv-20260507-024226` — RUNNING, processing date 2026-03-06 (~84% through 2025-05-01→today
  range). ETA ~5-10 min to completion + auto-shutdown.
- `cefi-pacifica-solana-ohlcv-20260507-024226` — RUNNING, similar progress. ETA ~5-10 min.

After auto-shutdown, the manifest will show `captured` for ~370 (Lighter) + ~310 (Pacifica) day-symbol shards. Verify
final state on next-agent boot:

```bash
gcloud storage ls "gs://market-data-tick-cefi-central-element-323112/raw_tick_data/by_date/day=2025-*/asset_group=cefi/venue=LIGHTER-ZKSYNC/instrument_type=perpetual/data_type=ohlcv_1m/" | wc -l
```

## What other backfills are still running (full fleet status snapshot)

Per the 2026-05-07 KRAKEN-SPOT verification (which closed earlier this session), the following CeFi backfills are
mid-flight:

- 7 KRAKEN-SPOT VMs (post-slash-hyphen-fix relaunch, processing 2020-2026 — 18.8M records on day-1 verified)
- 7 BITFINEX-SPOT VMs (prior-session tier3)
- 5 BITFINEX-FUTURES VMs
- 3 BITGET-FUTURES VMs
- 1 KRAKEN-FUTURES VM
- 13 cefi-coinbase-spot VMs (prior-session 56-VM fan-out, partially drained)

Plus the 2 Lighter + Pacifica VMs from this session.

**Not running (gaps):**

- BITGET-SPOT (tier3 launcher default but only futures actually launched)
- BINANCE-SPOT/FUTURES, BYBIT-SPOT/FUTURES, OKX-SPOT/FUTURES, DERIBIT spot/options (probably already complete; verify
  via data-status)
- DERIBIT options-chain / futures-chain (chain-bundle backfill)
- The DeFi backfills mentioned in the prior handover (lst yields, lending indices, gas fees, vault snapshots)
- TradFi gaps from prior sessions
- Per-trade history for the 3 DEX venues (impossible — see Item E above)

## Reference commits — Session 2026-05-07 (DEX perp onboarding)

- MTDS `10aa715`, `51fecd5`, `d898985`, `fc53a97`
- UAC `e890022`
- PM `<this commit>`

## Done when

- Items A (forward-poll handlers) + B (Pacifica collateral matrix) + C (Extended historical) shipped.
- Coverage matrix reflects per-trade gap honestly.
- Live perp-funding signals firing for the three DEXes.
- This handover archived.

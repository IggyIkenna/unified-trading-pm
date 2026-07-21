---
doc_type: issue
title: >-
  LST exchange-rate data availability across the four rate sources (CEX spot / DEX pool / Aave oracle / protocol
  redemption) — only the staking-accrual rate is in good shape; the Aave-oracle collateral rate is missing outright
summary: >-
  Audit answering the operator's question "do we have the four LST exchange rates in code + full data across the board,
  and where from". Answer: NO, not full coverage — of the four, exactly one is healthy and it is the most important for
  the staking leg. (#4) protocol redemption (the true staking accrual) is genuinely captured — lst_yields.exchange_rate
  is the on-chain getPooledEthByShares/stEthPerToken/getRate eth_call value — but the FEATURE is only 15 days + EVM-only
  while the SOURCE is broad (closes with a features backfill). (#1) CEX spot is partial + non-contiguous (degraded to
  Coinbase-only). (#2) DEX pool is Uniswap-V3 only, ~6 days, no materialised mid, and the operator's stETH/ETH-on-Curve
  is entirely absent (dead subgraph endpoints). (#3) Aave oracle (recursive-staking collateral) is effectively missing —
  the true AaveOracle.getAssetPrice() is captured on zero days (dormant adapter); raw Chainlink proxy exists only for
  stETH/cbETH/rETH, not the actual Aave collateral tokens (wstETH/weETH). Gates the A2 interest build.
status: open
nature: issue
asset_group: [defi]
stage: [data, strategy]
repos: [features-service, market-tick-data-service, strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags: [lst, exchange-rate, staking, oracle, data-availability, defi, pnl-correctness]
related:
  [
    pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
    onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md,
  ]
created: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
assigned_role: backend
drift_direction: advance-code
depends_on: []
source: ["4-rate LST data-availability audit workflow wf_268532e0-323, run 2026-07-21 at operator request"]
resolved_by:
locked_by:
---

# LST exchange-rate data availability — the four rates

The operator flagged that "the LST exchange rate" is four different numbers, each for a different PnL leg. This audits
which we have, from where, and the coverage. **Bottom line: we do NOT have full data across the board — exactly one of
the four is healthy.**

## Verdict by source (which PnL leg each serves)

| #   | rate (leg it serves)                       | have it?                  | source of truth (verified)                                                                                                                                                                                    | coverage                                                                                                                      |
| --- | ------------------------------------------ | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| 4   | **Protocol redemption** (STAKING accrual)  | **YES** (the one we need) | `lst_yields.exchange_rate` = on-chain `getPooledEthByShares`/`stEthPerToken`/`getExchangeRate`/`getRate`/`convertToAssets` eth_call (`lst_rates_handler.py` `_EVM_LST_ABI_METADATA`). stETH=1.2315 monotonic. | **FEATURE only 15 days** (2026-04-03→04-19, EVM-only, 13 tokens); **SOURCE `lst_rates` is broad** (Jan–Jul 2026, incl Solana) |
| 1   | **CEX spot** (mark-to-market basis)        | PARTIAL                   | market-data-tick-cefi (Tardis): OKX/Bitget/Coinbase native listings                                                                                                                                           | non-contiguous; only stETH/cbETH/weETH/mSOL/jitoSOL listed; July degraded to Coinbase-only                                    |
| 2   | **DEX pool** (mark-to-market / peg)        | PARTIAL, shallow          | Uniswap-V3 `dex_pool_swaps` (wstETH/rETH/cbETH/weETH/ezETH/rsETH-WETH)                                                                                                                                        | **~6 days only** (2026-07-15→07-20), raw per-swap, **mid NOT materialised**; **Curve stETH/ETH ABSENT** (dead subgraphs)      |
| 3   | **Aave oracle** (recursive collateral/LTV) | **MISSING**               | `AaveOracle.getAssetPrice()` adapter EXISTS but DORMANT (0 days). Raw Chainlink proxy only for stETH/cbETH/rETH                                                                                               | **0 days** for the true oracle; no feed for wstETH/weETH/rsETH/ezETH — the actual Aave collateral tokens                      |

**Key nuance:** `lst_yields.exchange_rate` for stETH is the per-share ACCRUAL ratio (~1.23, = wstETH/stETH), i.e. the
redemption/fair-value rate (#4) — NOT the ~1.0 stETH/ETH secondary-market peg (that would be #1/#2). So it is the right
rate for the staking accrual.

## What this means for the A2 interest build

- **STAKING-yield leg (carry_staked_basis): buildable now** on #4 — but coverage is 15 days, so a full-history run books
  zero staking on missing days (NAV under-report) until the redemption-rate FEATURE backfill lands. The SOURCE already
  has the data.
- **Mark-to-market basis leg: buildable but fragile** — needs the Tardis LST-spot backfill (#1) and/or the DEX
  deep-backfill + a materialised mid (#2).
- **Recursive-staking collateral leg: BLOCKED** — the Aave oracle (#3) must be captured before A2 can value LST
  collateral / LTV correctly. This is net-new collection, not a backfill.
- **Solana LSTs (jitoSOL/mSOL/bSOL) are weakest everywhere** — CEX spot for jitoSOL/mSOL only; no DEX; no Aave; the
  redemption rate is in the SOURCE but **dropped from the feature output** (a today-vs-prior inner-join / vocab bug).

## Close actions (per gap)

1. **#4 feature backfill (cheapest, highest value):** run the features-service `lst_yields` backfill over the full
   `lst_rates` source history (no new collection); fix the inner-join / vocab that drops Solana + LRTs (ezETH/rsETH)
   from the feature output despite being in the source. Unblocks the staking leg over full history.
2. **#1 CEX-spot:** complete the LST-spot Tardis backfill (single-VM, cap-1) for the CEX-listed subset.
3. **#2 DEX:** fix the decommissioned Graph subgraph endpoints (esp. **Curve** — 11 of 12 configured DEX subgraphs yield
   zero), deep-backfill `dex_pool_swaps`, and add a feature that materialises the per-interval pool mid/peg.
4. **#3 Aave oracle (blocks recursive staking):** wire the dormant `aave_oracle` adapter into a running prod venue
   emitting `data_type=oracle_prices` (venue=AAVE), and/or add the missing Chainlink feeds for wstETH/weETH/rsETH/ezETH.
5. **Solana DEX:** the Orca/Raydium/Meteora handlers exist in MTDS but produce zero objects — a separate collection gap.

## Recommendation

Build the **staking-accrual leg on #4 now** (it's the correct rate and the healthiest source), gated behind the
redemption-rate backfill for full-history correctness, with visible honest-absence on uncovered days. Treat the
**recursive-staking collateral leg as blocked** on the Aave-oracle capture (action 4) — do NOT model LST collateral on a
proxy. The mark-to-market basis leg needs the operator's E1 short-funding answer (see
[[pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21]]) plus the #1/#2 backfills. </content>

---
name: carry_staked_basis_funding_scan_experiment
title: "carry_staked_basis funding-carry scan — exploratory analysis harness + journal"
status: active
priority: P2
parent_epic: strategy_master
assigned_vm: vm-trading-core
created: 2026-06-16
last_updated: 2026-06-16
locked_by: live-defi-rollout
estimate_class: research
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3.6
---

# carry_staked_basis funding-carry scan — analysis harness + journal

Exploratory analysis (operator-driven) of the CeFi funding leg of `carry_staked_basis`: scan ~30 perp coins across
venues, rank each day by **net carry**, hold the best, rotate as carry decays, add LST staking where the short venue
accepts the LST as collateral. This plan is the **journal** for the work and the home for its follow-up todos.

Harness: `e2e-testing/scripts/defi/staked_basis_funding_scan.py` (standalone analysis, NOT a strategy engine —
production path is `strategy-service` `CarryStakedBasisRankAllocator` +
`engine/strategies/v2/carry_and_yield/ staked_basis.py`, batch == live). Wired under strategy-service QG per the
peripheral-script rule.

## Net-carry model

    net_carry(coin, venue) = annualised_short_perp_funding(coin, venue)
                           + staking_apy(coin)   IF venue_accepts_collateral(venue, coin's LST)
                           + 0                    otherwise (plain long-spot / short-perp, funding only)

- Rank by **net carry** (best of staking+funding; funding-only where venue constraints necessitate — operator
  2026-06-16). Per coin, pick the venue maximising net carry.
- **Diversification**: where carry ties (within `_FUNDING_TIE_BPS`), equal-weight across all tied coins (least market
  impact — operator 2026-06-16).
- Funding annualised via UAC `perp_funding_cadence.annualise_funding_rate_bps` (per-venue 8h/1h cadence SSOT).
- Collateral eligibility via UAC `venue_collateral.venue_accepts_collateral`. Verified: stETH/wstETH accepted on **Bybit
  / OKX / Deribit**; **not** Binance / Hyperliquid / Aster. SOL LSTs only on Drift (not in the CEX short set) → **SOL is
  funding-only** in this harness.

## Verified data map (2026-06-16, prod central-element-323112)

| Leg                                 | Bucket                                     | Path / derivation                                                                                                                   |
| ----------------------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| Funding (Binance/OKX/Bybit/Deribit) | `market-data-tick-cefi-prd`                | `…/pipeline_mode=batch_tardis/…/data_type=derivative_ticker/<sym>.parquet` → `funding_rate` col (µs ts)                             |
| Funding (Hyperliquid)               | same                                       | `pipeline_mode=batch_hyperliquid_rest` (ms ts)                                                                                      |
| Funding (Aster)                     | **public API**                             | `fapi.asterdex.com/fapi/v1/fundingRate` (no GCS data; pulled live, paginated; 8h)                                                   |
| Staking (Lido stETH, Jito jitoSOL)  | `lst-rates-central-…` (legacy, not `-prd`) | `day=…/venue=<PROTO>/chain=<CHAIN>/…/data_type=lst_rates/*.parquet`; APY derived from `exchange_rate` growth (raw `apy` col is 0.0) |

Coverage windows: funding to 2026-05-24; staking to 2026-04-29; Hyperliquid GCS partial in May. Gaps are **accepted +
documented** (operator 2026-06-16): we don't chase carry where we lack the data (e.g. no staking rate → funding-only).

## Progress log (journal)

- **2026-06-16** — Built harness; verified end-to-end vs real GCS. Confirmed funding lives in `derivative_ticker` (no
  `data_type=funding_rate`); sources split Tardis vs `batch_hyperliquid_rest`; Aster absent from GCS.
- **2026-06-16** — Added collateral-aware net carry + tie-diversification + Aster-via-public-API + PnL/maxDD/Sharpe +
  self-contained Plotly HTML report (`_out/staked_basis_report.html`).
- **2026-06-16** — Data-quality spot-checks vs exchange APIs: GCS funding **values match Binance exactly**; found a
  **one-settlement offset** in `funding_timestamp` pairing → switched to day-mean (offset-robust). Found UTL
  `FUNDING_PERIODS_PER_DAY` disagrees with UAC `perp_funding_cadence` (Aster/Deribit 8× wrong). Both filed →
  `plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`.
- **2026-06-16** — Full 2026-YTD run (2026-01-01 → 05-20, 30 coins, 6 venues incl Aster-API): 140 days, venue coverage
  100% except Hyperliquid 85.7% (May GCS gaps). **Avg net carry 12.2% APY · cumulative 4.80% (13.0% annualised) GROSS.**
  Tie-diversification expanded the basket to ~13.2 coins/day, 2.5 rotations/day. Most-held: NEAR / LINK / UNI / AVAX /
  ADA. **Key finding: net carry ≈ funding (12.2% each)** — staking added ~0 to the basket because ETH funding (~5–8%)
  even +stETH (~3%) rarely beats the ~12% alt-funding cluster, so ETH is seldom selected. The "staked" leg only matters
  when ETH funding is competitive; in a high-alt-funding regime it's a tie-breaker, not a driver. `_FUNDING_TIE_BPS=50`
  drives basket size — tunable. Report: `e2e-testing/scripts/defi/_out/staked_basis_report.html` (gitignored, regen).
- _(append entries as work continues)_

## Findings filed

- Data-correctness (cadence registry inconsistency / `funding_timestamp` offset / no historical cadence tracker / Aster
  backfill) → `plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`.

## Open todos / next steps

- [ ] [STRATEGY] P2. Use `predicted_funding_rate` (already a `derivative_ticker` column) to gauge ENTRY on venues that
      publish a forward rate — enter/size based on predicted next-cycle funding, not just trailing realised. Only where
      the venue supports a forward rate (operator 2026-06-16). **Repo: e2e-testing harness → then strategy-service.**
- [ ] [STRATEGY] P2. Fold the net-carry signal into `strategy-service` `CarryStakedBasisRankAllocator` (swap the harness
      ranking for the production allocator; batch == live). **Repo: strategy-service.**
- [ ] [STRATEGY] P3. Add fees + slippage (per-venue taker + rotation cost) to turn GROSS carry into NET PnL; today the
      harness is GROSS only. **Repo: e2e-testing harness.**
- [ ] [STRATEGY] P3. Model the hedge/basis mark-to-market (the real risk) — current Sharpe/maxDD are carry-accrual only
      and flatter the strategy. **Repo: e2e-testing → strategy-service backtest (GroupBRunner).**
- [ ] [DATA] P2. (blocked-by issue doc) once exact discrete per-settlement funding is readable, switch the harness off
      the day-mean workaround to true per-settlement realised funding.

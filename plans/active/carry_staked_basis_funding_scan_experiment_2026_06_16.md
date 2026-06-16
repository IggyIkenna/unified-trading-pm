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
- **2026-06-16** — Added oracle (hindsight) vs causal (EWMA, no-lookahead) strategies + a 5 bps/leg cost model (2 legs
  spot+perp per |Δweight|; 1-for-1 rotation ≈ 20 bps) + a hysteresis no-trade buffer + per-year metrics + a local data
  cache (instant param sweeps). **Key result (2025-01-01→2026-05-20, hl=10/buffer=5):** the perfect-foresight oracle is
  a mirage net of costs — turnover 0.54/day → 31.8% cumulative drag → net **1.1%** (2026 net **−7.8%**). The causal
  EWMA+buffer trades 0.05/day → net **18.3%** full window, **2026 net 9.8%** (target hit), **2025 net 21.8%** (2025
  funding was very rich). Lesson: optimise carry-capture PER UNIT TURNOVER, not gross carry.
- **2026-06-16** — Aster data availability (API-only; klines/funding backfill, OI/book live-only): funding 2023-07-22,
  **OHLCV 2023-01-01**, mark/index via klines, trades partial, **OI + L2 quotes live-capture-only** (no historical
  endpoint). Tardis CEX schema (trades/book_snapshot_5/derivative_ticker{mark,index,funding,OI}/liquidations) is the
  canonical benchmark → non-Tardis venues canonize their native API INTO those data_types; genesis is per-(venue,
  data_type), not per-venue. **Aster margining = USDC/USDT-only (CROSS); rejects spot-coin AND LST collateral**
  (`venue_collateral.py`) — so Aster is a stablecoin-margined funding-short only; no same-venue cash-and-carry, no
  staking leg. ETH staked-basis works on Bybit/OKX/Deribit (stETH/wstETH collateral). Filed to the Aster todo in
  `plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`.
- _(append entries as work continues)_

## Findings filed

- Data-correctness (cadence registry inconsistency / `funding_timestamp` offset / no historical cadence tracker / Aster
  backfill) → `plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`.

## Execution structures + capital efficiency (operator design 2026-06-16)

The funding you _capture per unit of deployed capital_ depends on how the long (spot/LST) and short (perp) legs are
collateralised. Rank on **effective carry = (funding + applied_staking) × capital_efficiency**, not raw funding.

**Five structures** (assign each (coin, venue) opportunity to one):

1. **Spot + perp, same venue, spot IS collateral** — venue liquid for spot AND accepts spot as margin (portfolio/
   unified margin: Binance/Bybit/OKX). Start USDC/USDT → buy spot + short perp, one collateral pool. `efficiency ≈ 1`.
2. **Staked-basis LST + perp, same venue, LST IS collateral** — venue accepts the LST (Bybit/OKX stETH/wstETH, Deribit
   stETH). Earn staking + funding on one margin base. `efficiency ≈ 1 − lst_haircut` (Bybit/OKX 10%, Deribit 7.5%).
3. **Spot on venue A → transfer → short on venue B (B accepts the moved spot/coin as collateral)** — illiquid spot at B,
   so buy spot at A, move it, short at B. Costs: transfer fee + **timing gap** (price can move between buy and short).
   Mitigations: (a) buy→send→short (gap risk); (b) borrow the coin against USDT, post borrowed coin at B, short,
   simultaneously buy at A to repay — needs a margin/borrow account + LTV cap, usually a separate account so often
   impractical; **(c) prime-broker / off-exchange settlement (see below) — the clean answer.**
4. **Spot on venue A + STABLECOIN margin on perp venue B (B rejects spot/LST collateral: Hyperliquid, Aster)** — capital
   splits: cash for spot AND cash for perp margin. `efficiency = notional/(notional+margin) = 1/(1+m)` where `m` = max
   adverse (up) move budgeted before rebalance. Operator example: 100k → 60k spot + 40k margin → short 60k → capture
   **0.6×** the funding. **Per-asset `m`** (max up-move buffer): BTC ~0.20, ETH ~0.25–0.30, mid alt ~0.50–0.60, small
   alt ~0.80 → `f` ≈ 0.83 / 0.77 / 0.62 / 0.56. Parameterise `m` per asset and scale required margin → discount funding
   by `f` in the ranking.
5. **Perp–perp (no spot leg)** — when one venue's funding is ~zero and another's is high (or one negative + one positive
   — observed **20.6%** of coin-days), go **long the low/negative-funding perp + short the high-funding perp**, split
   collateral ~50/50; both legs stablecoin-margined, delta-neutral, full size. This is the
   `arbitrage_price_dispersion`/funding-dispersion cousin — capture the cross-venue spread (p95 ≈ 32% APY).

**Prime-broker / off-exchange-settlement bridge (TODO — find the venue).** The capital-efficiency drag of structures 3–4
largely disappears if a prime broker / tri-party custodian posts _temporary_ collateral at the short venue so you can
short immediately, then you replace it once the spot balance moves over (or just keep collateral in custody, mirrored to
the exchange — never physically moving the coin). This is exactly what **off-exchange settlement networks** do: **Copper
ClearLoop, Ceffu (Binance) MirrorX, FalconX / Hidden Road prime** — collateral stays in custody, the exchange recognises
it for margin, no transfer-timing gap. The workspace already uses **Copper + Ceffu** for custody
(`codex/04-architecture/custody-providers.md`) → ClearLoop/MirrorX are the natural rails for capital-efficient
cross-venue basis. **Action: confirm which of our custody PBs support off-exchange margin on which short venues; if so,
structures 3–4 collapse toward `efficiency ≈ 1`.**

## Funding-regime findings (2025-01-01 → 2026-05-20, 37,128 coin·venue·day points)

- **22.9% of funding observations are NEGATIVE**; median 6.5% APY; a heavy cluster sits at the ~11% cap (0.01%/8h).
- **12% in [0,3%) "meh"** (hold/stake, don't short — `--min-carry-bps` floor); **65% ≥3%**; **~3% ≤ −20%** (flip to
  long-the-perp).
- **20.6% of coin-days have a cross-venue sign split** (neg on one venue, pos on another → structure-5 dispersion play);
  cross-venue spread p95 ≈ 32% APY.
- **Deribit funding is unreliable in the raw feed** (p95 130%, min −878%) — consistent with the 8h-vs-1h normalisation
  bug filed in the cadence issue; winsorise outliers + treat Deribit funding as suspect until that's fixed.

## Open todos / next steps

- [ ] [STRATEGY] P2. Add the capital-efficiency factor to the harness ranking: structure assignment per (coin, venue)
      (spot-collateral set {Binance/Bybit/OKX/Deribit} vs cash-margin {Hyperliquid/Aster}), per-asset max-move `m` →
      `f=1/(1+m)`, rank by `effective_carry = (funding+staking)×f`, winsorise funding outliers, `--min-carry-bps` floor
      (default 300). **Repo: e2e-testing harness.**
- [ ] [STRATEGY] P2. Add structure-5 (perp–perp funding dispersion: long low/neg-funding perp + short high-funding perp)
      as a candidate alongside the spot/LST basis. **Repo: e2e-testing → strategy-service.**
- [ ] [RESEARCH] P2. Prime-broker / off-exchange-settlement bridge — confirm whether Copper ClearLoop / Ceffu MirrorX /
      FalconX / Hidden Road give off-exchange margin on our short venues (HL/Aster/Bybit/OKX); if yes, structures 3–4
      collapse to `efficiency ≈ 1`. Cross-link `codex/04-architecture/custody-providers.md`. **Repo: PM research +
      execution-service.**

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

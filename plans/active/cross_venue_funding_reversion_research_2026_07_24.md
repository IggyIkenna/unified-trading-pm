---
doc_type: plan
title: carry_staked_basis — cross-venue funding-reversion research (Pass-B reconciliation + deployable book)
summary: >-
  Forked 2026-07-24 (line-cap remediation) from carry_staked_basis_funding_scan_experiment_2026_06_16.md: a genuinely
  distinct strategy that only got journaled inside the carry-scan harness plan — cross-sectional / cross-venue
  funding-rank REVERSION research (reconciled against the CeFi Pass-B agent's Binance reversion book), the resulting
  deployable multi-venue reversion book with turnover/DD-control overlays, robustness/OOS checks, and the multi-venue
  capital-flow + paper-trading-runner build. Distinct from the carry-HARVEST work that stays in the parent (carry ranks
  by net funding+staking carry; this is price-reversion conditioned on cross-sectional funding rank).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, e2e-testing, execution-service, features-service, ibkr-gateway-infra]
scope: [engineer, admin]
tags: [strategy, defi, cefi, features, research, funding-reversion]
related:
  [
    /plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md,
    /plans/archive/2026_08/carry_strategy_ensemble_productionization_2026_07_24.md,
    /plans/epics/strategy_master.md,
  ]
created: "2026-07-24"
parent_epic: strategy_master
assigned_vm: NA
execution_scope: local-only # was: orchestrator-agent — corrected 2026-08-19 (plan_reconciler, cross-cutting) — only valid NA-paired value
priority: P2
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.4
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Forked from carry_staked_basis_funding_scan_experiment_2026_06_16.md per the line-cap remediation triage
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md), operator-approved 3-way split of the locked plan.
drift_direction: advance-code
context_scope:
  [
    /plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md,
    /plans/archive/2026_08/carry_strategy_ensemble_productionization_2026_07_24.md,
    /codex/04-architecture/custody-providers.md,
    e2e-testing/scripts/defi/,
    e2e-testing/scripts/defi/funding_reversion_crossvenue_book.py,
  ]
---

# carry_staked_basis — cross-venue funding-reversion research (Pass-B reconciliation + deployable book)

> **Forked from `carry_staked_basis_funding_scan_experiment_2026_06_16.md` on 2026-07-24** (line-cap remediation — that
> plan was 1426 lines, over the 1000L hard cap). This section was a genuinely distinct strategy (cross-sectional
> funding-RANK price-reversion, not the carry-harvest the parent plan ranks/rotates on) that only got journaled inside
> the carry-scan harness plan. Content below is moved verbatim, unedited except for this banner. See also the sibling
> fork `carry_strategy_ensemble_productionization_2026_07_24.md` (the strategy-service productionization / ensemble
> engine work) and the trimmed parent (core carry-scan harness + journal).

## Open todos / next steps

- [ ] [RESEARCH-ML] P2. (separate ML agent/exercise — operator 2026-06-18; NOT built by the harness agent — empirical
      handoff) **Funding-dynamics GBM models for squeeze / crowded-long prediction** — full spec immediately below.

  **Hypothesis (finding #7):** funding LEVEL = momentum (IC +0.073 @ 7d). The REVERSAL (short squeeze on crowded shorts
  / unwind of crowded longs) is the conditional ~30% TAIL, predictable from the DYNAMICS of the extreme — how extreme,
  **how long it has persisted at that level** (operator: fresh spike vs stale extreme differ), accel/decel, OI +
  liquidation + extension context.

  **Features (per coin-day):** funding LEVEL (`apy_bps`) + cross-sectional percentile rank; **crowded flags**
  `|funding| > {50,100,200}%/yr` (operator's "abs funding>50%/yr = crowded short/long"); **persistence/recency**
  (operator key feature) — days since `|funding|` first crossed each threshold (current extreme-regime duration), days
  since funding last crossed zero, same-sign run-length; **acceleration** `Δfunding {1,3,7}d` + funding z-score vs
  {20,60}d; **OI** level
  - `ΔOI {1,3,7}d` (rising OI+extreme = build/continuation; collapsing OI+extreme = unwind/reversal); **volume**
    `day_ntl_vlm` + z-score; **price extension/vol** return vs {7,30}d MA + realized vol; **liquidations** (HL S3
    archive) = the squeeze trigger.

  **Targets:** (a) CLASSIFICATION — forward-Nd return is REVERSAL (opposite to funding-momentum) vs CONTINUATION, binary
  or 3-class, horizons {1,3,7,14}d; (b) REGRESSION — forward-Nd return / reversal magnitude. **Model:** GBM
  (LightGBM/XGBoost) cls+reg, walk-forward CV (no lookahead), SHAP/gain importance → keep the predictive subset (expect
  persistence + accel + ΔOI to beat raw level for the reversal tail). **Then blend the validated continuous signals
  (predicted reversal-prob / funding-momentum score) into the EXISTING carry/dispersion models** as features/overlays so
  the live book "does fewer shorts/longs" where a squeeze/unwind is likely. **Data:** GCS HL `perp_funding` (hourly) +
  `perp_daily_ctx` (mark_px/vol/OI), 2023-2026 100% coverage, + HL liquidations from the S3 archive. ⚠ canonicalize
  `perp_daily_ctx` → `derivative_ticker` first (canonical todo below). Reproducible from
  `e2e-testing/scripts/defi/staked_basis_funding_scan.py`. **Repo: features-service / ML.**

  **Squeeze-END predictability — first empirical cut (operator 2026-06-18; do these features predict WHEN the crowd
  unwinds?): NO — the intuitive exhaustion features all predict CONTINUATION or are flat.** On 7,791 extreme-funding
  episodes (|funding|>100%/yr, liquid, 2023-2026), correlating each feature with the 7d REVERSAL (reversal>0 = crowd
  unwound, i.e. price moves against the funding direction): **persistence** (days the extreme has held) corr **−0.041**
  — reversal −1.5% (fresh) → **−5.1% (>10d stale)**, so the longer it persists the HARDER it continues (accelerates, no
  exhaustion); **price extension** (SDs from 20d mean) corr **−0.097** (strongest) — most-extended continues hardest
  (−0.6% → −4.7%); **volume change** corr −0.033; **ΔOI 7d** corr **+0.015** (flat — ~−2% reversal whether OI is
  collapsing or surging). So the slow daily exhaustion proxies do NOT flag the squeeze; the momentum is robust + speeds
  up. **ML implication:** the tradeable, predictable edge is the CONTINUATION (funding-momentum, IC +0.073@7d); the
  squeeze/unwind is a tail that needs FASTER / exogenous signals — funding INFLECTION (the moment funding turns down
  from the extreme), liquidation cascades (HL archive), order-book imbalance, news — NOT the slow daily
  persistence/extension/ OI. Another agent should start the squeeze model from those faster signals, treating these four
  slow features as confirmed non-predictors of the reversal (use them for the continuation side instead).

  **CROSS-VENUE / LIQUIDITY: the funding signal's SIGN INVERTS with coin liquidity, NOT venue (operator 2026-06-18 —
  "does the game change on Binance? are some venues more predictionary?").** Measured `corr(funding, fwd_7d_return)` per
  venue on the SAME curated majors (BTC/ETH/SOL/XRP/BNB/DOGE/AVAX/LINK, derivative_ticker, Jan-May 2025, n=1200/venue):
  **HYPERLIQUID −0.129 · BYBIT −0.108 · BINANCE −0.079 · OKX −0.017** — ALL NEGATIVE (funding = CONTRARIAN/REVERSAL on
  liquid majors: crowded → mean-reverts). But the HL FULL 230-coin universe (perp_funding) IC was **+0.073 (MOMENTUM)**
  — so the earlier "funding=momentum" headline was driven by the ILLIQUID LONG-TAIL, not majors. **Synthesis: liquid
  majors → funding contrarian (reversal); illiquid long-tail → funding momentum (trend).** The venue does NOT flip the
  sign; it modulates STRENGTH — **HL carries the most information on majors (−0.13), then Bybit, Binance, OKX≈0**
  (consistent with HL being the more retail/less-arbitraged book, so its funding extremes are the strongest crowding
  signal). ML implication: the funding feature MUST be conditioned on (liquidity tier × venue) — a single universe-wide
  funding factor has a sign that flips, so split majors-vs-tail and weight venues by their |IC| (HL > Bybit > Binance >
  OKX). **Tested the actionable corollary** (does a MAJORS-ONLY carry win, since majors mean-revert?): no — min_vol
  $50M-500M / n=5-12 nets −1 to −3%/yr (still slightly negative), BUT maxDD collapses to **−3% (vs −125%
  full-universe)**. So the reversal edge on majors is real but too small to overcome the tiny major funding spread +
  costs — confirms funding≈price efficiency even where the sign favours the carry; the value stays in the FEATURE, now
  liquidity/venue-conditioned. Reproducible: `_run_xsec_carry` (min_vol filter) + the cross-venue IC reader
  (derivative_ticker funding_rate+mark_price per venue).

  **REGIME CLASSIFIER BUILT + the decomposition that CORRECTS the above (operator 2026-06-18 — "make a classifier; ml
  can't do it alone without overfitting"). KEY RESULT: the dramatic liquidity/venue regime split was LARGELY A STATIC
  SELECTION ARTIFACT, not a predictive signal.** Built `funding_regime_classifier.py` (sample=(coin,quarter),
  target=sign of within-coin IC, features=log ADV/OI/rvol/|funding|/log px/maturity, LightGBM + grouped-by-coin CV +
  logistic baseline). Before classifying, decomposed the funding→return IC: **BETWEEN-coin (static/selection) = +0.31**
  (coins that MOONED over 2023-24 carried high AVERAGE funding — strong but NOT tradeable, you can't trade "the winners
  had high funding" forward) vs **WITHIN-coin (dynamic/predictive, per-coin demeaned) = +0.02** (≈ZERO genuine
  predictive signal). So the earlier headline ICs (+0.073 momentum / −0.13 reversal) were dominated by the +0.31
  selection effect + small-sample/source differences — **exactly the "other stuff" a raw-funding ML overfits.** After
  demeaning, the residual predictive tilt is WEAK and the OPPOSITE of the hypothesis: liquid → mild MOMENTUM (D5
  +0.066), illiquid → mild REVERSAL (D1 −0.020). The classifier itself: AUC **0.644** (modest, grouped CV), no single
  feature dominates (rvol 19% / log_adv 18% / log_px 18% / |funding| 17% / log_oi 16%), 1-feature log_ADV baseline AUC
  0.522 (liquidity alone ≠ the driver), continuous-IC regressor R²≈0 (unpredictable). **Disciplines for the ML agent:
  (1) DEMEAN funding per-coin before it enters any model — the raw cross-sectional level encodes the un-tradeable +0.31
  selection effect; (2) treat the regime as a WEAK soft-conditioner (AUC ~0.64), never a strong standalone signal; (3)
  the cross-venue |IC| ranking (HL>Bybit>Binance>OKX) and "liquid=reversal" framing are confounded — re-derive on
  per-coin-demeaned funding before trusting them.** Reproducible:
  `e2e-testing/scripts/defi/funding_regime_classifier.py` (prints the decomposition + decile tilt + CV AUC; saves
  panel.parquet + the LGBM model).

- [ ] [STRATEGY] P3. Cross-sectional carry is NOT tradeable standalone (funding≈adverse price) — only revisit with a
      genuine price-neutralising overlay (correlation-paired long/short of co-moving coins, or a momentum/beta hedge)
      AND only if it clears Sharpe; otherwise the archetype is shelved. The delta-neutral staked/pure-basis remain the
      proven winners. **Repo: e2e-testing.**

- [ ] [STRATEGY] P2. Decompose HL pure-basis carry into the interest-rate FLOOR (~11% APY structural, ~45-58% of hours
      clamp to it) vs the premium/dispersion component — so sizing reflects how much is structural vs alpha. **Repo:
      e2e-testing harness → strategy-service.**
- [ ] [DATA] P3. (optional certainty) spot-check a sample of HL funding cells at the 1.25e-5 floor against HL's live
      on-chain `fundingHistory` to confirm the archive's floor values match realized on-chain funding. **Repo:
      e2e-testing.**

- [x] [DATA] ✅ P2. Backfilled HL `perp_funding` to **100% coverage 2023-05-20→2026-06-09 (1117/1117 days, 0 gaps)** via
      the fast S3 `asset_ctxs` archive (`mtds@98d12be`, no REST rate-limit, ~4 min for 374 days/965k rows) + a 7-day
      REST fill for the days HL's S3 archive lags (06-02→08). HL funding history now spans ~3 years for the full
      ~230-coin universe. **Repo: market-tick-data-service.**
- [x] [STRATEGY] ✅ P2. Add the capital-efficiency factor to the harness ranking: structure assignment per (coin, venue)
      (spot-collateral set {Binance/Bybit/OKX/Deribit} vs cash-margin {Hyperliquid/Aster}), per-asset max-move `m` →
      `f=1/(1+m)`, rank by `effective_carry = (funding+staking)×f`, winsorise funding outliers, `--min-carry-bps` floor
      (default 300). **Repo: e2e-testing harness.** — e2e-testing@3d219d7: `_capital_efficiency()` (line 361) computes
      structure-tagged efficiency + `min_carry_bps` floor (default 300.0, line 1320) wired through universe/EWMA/LP.
- [ ] [STRATEGY] P2. Add structure-5 (perp–perp funding dispersion: long low/neg-funding perp + short high-funding perp)
      as a candidate alongside the spot/LST basis. **Repo: e2e-testing → strategy-service.**
- [ ] [RESEARCH] P2. Prime-broker / off-exchange-settlement bridge — confirm whether Copper ClearLoop / Ceffu MirrorX /
      FalconX / Hidden Road give off-exchange margin on our short venues (HL/Aster/Bybit/OKX); if yes, structures 3–4
      collapse to `efficiency ≈ 1`. Cross-link `/codex/04-architecture/custody-providers.md`. **Repo: PM research +
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

## RECONCILIATION with Pass-B (CeFi/Binance cross-coin reversion) — venue-dependence PROVEN (2026-06-18)

The CeFi agent (Pass B, bundle `gs://backtest-results-central-element-323112/cross_coin_funding_handoff_2026_06_18/`)
built a **dollar-neutral cross-sectional funding-RANK reversion** book on Binance perps (long lowest-funding / short
highest-funding, inverse-vol within each leg, EWMA-7 signal, point-in-time incl. 20 dead coins, 5bp) → **Sharpe 1.44,
maxDD −34%, positive every year**. It is 99% cross-sectional PRICE-reversion (funding is just the ranking signal), NOT a
funding harvest. Apparent contradiction with our "carry not tradeable" — RESOLVED, both right:

1. **Reproduced their 1.44 exactly** + audited the vol-scaling salvage (0.49→1.32): **causally CLEAN** —
   `vol30.shift(1)`
   - `sig.ewm().shift(1)`, no lookahead. Their headline survives scrutiny.
2. **Their "+0.31 between-coin selection" ≡ our "+1.17 survivorship" — same finding, two framings.** Their "within-coin
   +0.02 ≈ 0" ≡ "funding has no harvest timing power." Agreed on both.
3. **KEY NEW RESULT — ran their EXACT method on HL (native perp marks, full 230-coin universe, no hand-picked
   survivorship): Sharpe 0.30 (vs Binance 1.44).** Decomposition: **price-only Sharpe −1.03 on HL vs +1.04 on Binance —
   the price component FLIPS SIGN BY VENUE.** Binance (crowded arb zone) → funding pulled to fair → residual is
   REVERSION (short high-funding wins); HL (less-arbitraged, directional) → funding CHASES price → MOMENTUM (short
   high-funding loses). So the cross-sectional reversion edge is **VENUE-DEPENDENT** — it is an arbitrage-intensity
   phenomenon, not a universal funding effect. Our "HL carry not tradeable" + their "Binance reversion 1.44" are the
   SAME truth at opposite ends of the arb spectrum, exactly the operator's economics (HL more directional bets / less
   basis-arb than Binance).
4. **Their methodology improvements are real + transferable**: inverse-vol-within-legs + EWMA-7 lifted HL from our naive
   xsec (−1.3 Sharpe) to +0.30 — the weighting/smoothing genuinely help even where the alpha is absent.

**IMPROVEMENTS for the strategy (journaled for the ML agent):** (a) **VENUE is a first-order gate** — run this reversion
book ONLY on heavily-arbitraged CeFi venues (test Bybit/OKX/Deribit next — predict they also revert), NEVER on HL/DeFi
or thin venues where funding is momentum; add a "venue arb-intensity" feature. (b) **Their #1 caveat
(spot-as-perp-proxy) is perp-ROBUST at the venue level** — our HL test used NATIVE perp marks and reversion still fails
on HL, so the venue-dependence isn't a price-proxy artifact; they should still re-run Binance on true perp marks (fapi
OHLCV) to confirm 1.44 (the cefi GCS bucket is only ~20 curated coins, not their 50, so the full perp re-run needs their
fapi pipeline). (c) the 1.44 leans on the one-off 2026 dispersion spike (yearly 2022 +0.77 → 2026 +2.04) — underwrite
ex-2026. Reproduce: their `_carry_deployable.py` (`CACHE=./cache`); our HL port is the inline harness in this session.

**CROSS-VENUE SWEEP — reversion regime confirmed across ALL arbitraged perp venues; HL is the lone momentum outlier
(2026-06-18).** Ran their exact method (EWMA-7 funding rank, inverse-vol legs, dollar-neutral, 5bp) on each venue. The
robust read is the **price-only Sharpe SIGN** (reversion>0 / momentum<0):

| Venue           | price-only Sharpe                  | net          | ann.ret | universe / source                           | regime                                           |
| --------------- | ---------------------------------- | ------------ | ------- | ------------------------------------------- | ------------------------------------------------ |
| **Bybit**       | **+1.81**                          | +1.48        | +40%/yr | 9 majors, cefi GCS, 1yr                     | reversion (strongest on majors)                  |
| **Aster**       | **+1.10**                          | +1.30        | +51%/yr | 14 coins, LIVE fapi.asterdex.com, 1.7yr     | reversion                                        |
| **Binance**     | +1.04 (50-coin) / +0.09 (9 majors) | 1.44 / −0.12 | +58%/yr | deployable small-caps vs majors             | reversion (edge in small caps; majors efficient) |
| **OKX**         | +0.44                              | +0.20        | +6%/yr  | 9 majors, cefi GCS, 1yr                     | mild reversion                                   |
| **Hyperliquid** | **−1.03**                          | +0.30        | —       | 230 coins, native perp, 3yr                 | **MOMENTUM (outlier)**                           |
| Deribit         | —                                  | —            | —       | symbol mismatch + few perps (options venue) | inconclusive (no data)                           |

**Conclusion: the cross-sectional funding-rank reversion edge is an ARBITRAGE-INTENSITY phenomenon, not DEX-vs-CEX.**
Every well-arbitraged perp venue (Binance, Bybit, OKX, Aster — incl. the Aster DEX, which is Binance-API-compatible with
heavy arb-bot flow) shows price REVERSION (short high-funding wins); only HL — thin arb, dominated by directional bets —
shows MOMENTUM (short high-funding loses). This is exactly the operator's economics. Caveats: the GCS majors sweep is a
short (1yr) 9-coin window so absolute numbers are noisy (Binance majors read weak +0.09 because its edge lives in the
small caps the GCS bucket lacks; the SIGN is the robust part); Aster is short-window + live-pulled. **Strategy
implication: deploy the reversion book across the arbitraged venue set (Binance/Bybit/OKX/Aster), size by each venue's
small-cap funding dispersion, and EXCLUDE HL from this archetype (HL is for the delta-neutral basis/staked carry, not
the reversion book). Aster needs a GCS backfill (today only live-API).** Yield note: the deployable runs ~+58%/yr
(Binance) / +51%/yr (Aster) at ~40% vol — high-octane reversion, NOT smooth carry. Liquidity in the deployable = inverse
price-VOLATILITY weighting (not volume); ADV (Binance-specific spot 15m) is only a universe filter. Per-coin PnL plot
rendered (`/tmp/passB/binance_carry_per_coin_pnl.html` — TLM/CTK/TRX top, dead +116% / survivors +153%).

## ML-Agent Handoff — funding-rate prediction (data + code locations, 2026-06-18)

Self-contained pointer set for the separate ML agent (who has its own features + better predictions) to combine
everything and push the within-coin predictive IC up. **All data is already in GCS production buckets; all code is in
the repos. Test downstream in the production spine (MTDS → features-service → strategy-service), not just the e2e
research harness.**

**WHERE THE DATA IS (GCS, project `central-element-323112`):**

- **Hyperliquid funding + price/OI (DeFi bucket, full ~230-coin universe, 2023-05-20→today, 100% coverage):**
  `gs://perp-funding-central-element-323112/raw_tick_data/by_date/day={YYYY-MM-DD}/pipeline_mode=batch_hyperliquid/asset_group=defi/venue=HYPERLIQUID/chain=HYPERLIQUID/instrument_type=perpetual/data_type={DT}/`
  with `{DT}` ∈ `perp_funding` (hourly `funding_rate`+`premium`) and `perp_daily_ctx` (daily-close `mark_price` +
  `day_ntl_vlm` + `open_interest`). Symbol = bare coin (`BTC`). **Legacy-layout caveat:** historical days
  (2025/early-2026) were written BEFORE the `pipeline_mode=` partition — readers must try BOTH the
  `pipeline_mode=batch_hyperliquid/…` path AND the bare `…/day=D/asset_group=defi/…` path (the harness loaders already
  do).
- **CeFi derivative_ticker (Binance/Bybit/OKX/Deribit/Kraken/Bitget/… funding + mark_price, tick-level):**
  `gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day={D}/pipeline_mode={MODE}/asset_group=cefi/venue={VENUE}/instrument_type=perpetual/data_type=derivative_ticker/{SYM}.parquet`.
  `{MODE}` = `batch_tardis` for the CeFi venues, `batch_hyperliquid` for HL's CeFi mirror. Columns: `funding_rate`,
  `mark_price`, `index_price`, `last_price`, `funding_timestamp`. **Venue dirs:** `BINANCE-FUTURES`, `BYBIT`,
  `OKX-SWAP`, `DERIBIT`, `KRAKEN-FUTURES`, `BITGET-FUTURES`, … (perp list is broad; majors-only for some). **Symbol
  formats differ:** Binance/Bybit `BTCUSDT`, OKX `BTC-USDT-SWAP`, HL-CeFi-mirror `BTC-PERP`. Curated ~20-coin Tardis
  coverage (not the full HL universe).
- **HL raw S3 archive (requester-pays, Secret Manager `aws-hyperliquid-s3`, bucket `hyperliquid-archive`):**
  `asset_ctxs/{YYYYMMDD}.csv.lz4` (minute-res funding/OI/premium/oracle_px/mark_px/mid_px/impact_bid/ask/day_ntl_vlm —
  the source the GCS backfill downsamples) and `market_data/{YYYYMMDD}/{hour}/l2Book/` (hourly **L2 order-book
  snapshots** → order-book imbalance, the faster squeeze signal; no standalone liquidations feed — infer from
  book/fills).

**THE CODE (repos, all on `live-defi-rollout`):**

- `e2e-testing/scripts/defi/staked_basis_funding_scan.py` — funding research harness. Reusable loaders:
  `_load_hl_funding(client, frozenset(_live_hl_universe()), days, workers)` → funding points (`.day/.base/.apy_bps`);
  `_load_hl_ctx(client, days, workers)` → `{day:{coin:(mark_px,vol)}}`; `_date_range(start,end)`; `_run_xsec_carry`
  (cross-sectional carry backtest). Cross-venue IC reader pattern is inline in the experiment journal.
- `e2e-testing/scripts/defi/funding_regime_classifier.py` — the LightGBM regime classifier + the IC `decompose()`
  (between-coin selection vs within-coin predictive). Run it: prints the decomposition + decile tilt + grouped-CV AUC,
  saves `/tmp/funding_regime/funding_regime_panel.parquet` + `funding_regime_classifier.txt`.
- `market-tick-data-service/scripts/backfill_hl_funding_from_s3_asset_ctxs_2026_06_17.py` +
  `backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py` — the S3→GCS backfillers (extend for new data_types).

**WHAT WE FOUND (don't repeat; build on it):** funding≈adverse price (efficient); the apparent liquidity/venue regime
split is a **+0.31 between-coin SELECTION artifact**, genuine within-coin predictive IC ≈ **+0.02** (≈0); regime
classifier AUC **0.64** (modest); squeeze-end NOT predicted by slow daily features (persistence/extension/vol/ΔOI all →
continuation or flat). **DISCIPLINES:** (1) DEMEAN funding per-coin before any model — raw level encodes the
un-tradeable selection effect; (2) |IC|>0.15 is a red flag for a confound, not a win; (3) treat the regime as a weak
soft-conditioner. **CANONICAL caveat:** `perp_daily_ctx` is a research-grade (non-UAC, manifest-invisible) data_type —
canonicalize to `derivative_ticker` + register + manifest-track BEFORE any production features-service/strategy-service
pipeline depends on it.

**THE TASK (for the ML agent):** combine your own features + better predictions with the funding features above; raise
the **within-coin (demeaned)** predictive IC (the only honest target); build the squeeze/reversal classifier from the
FASTER signals (funding inflection, L2-book imbalance from the HL archive, OI dynamics) since the slow features are
confirmed non-predictors; then WIRE + TEST in the production spine — features in `features-service` (feature registry),
signal in `strategy-service` (`CarryStakedBasisRankAllocator`), data via `market-tick-data-service` — to see how far we
actually are toward production. Paste `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` at the top of any sub-agent spawn.

## Cross-venue REVERSION book — deployable, DD-control, cross-venue filters (2026-06-18, all CAUSAL/no-lookahead)

Extends Pass-B's Binance funding-rank reversion to a live-API multi-venue book + risk overlays + cross-venue signal
filters. Every signal lagged (`.shift(1)`), trailing windows only, fixed thresholds (not fit). Non-compounded
(`cumsum`). Scripts (throwaway, `/tmp`): `build_multivenue.py` (per-venue live-API pull + combine + plot),
`dd_filters.py` (beta/corr/vol filters + vol-target + beta-hedge), `anomaly_filter.py` (cross-venue funding dispersion),
`sizing_test.py` (sizing schemes). Plots served `/tmp/passB/*.html`.

**1. Multi-venue deployable (Pass-B's 30-survivor universe, live-API per venue, 2022→2026, 5bp).** Per-venue Sharpe:
**Binance +1.53 / Bybit +2.06 / Aster +0.71** (Aster short history; OKX dropped on a coverage filter). Reproduces
Pass-B's survivor-only ~1.52 → sound. Combined (Binance+Bybit, mean pairwise corr **0.67**): equal +1.96, causal
inverse-vol +1.98, **causal Sharpe-tilt +2.04** (≈ best-single Bybit 2.06). **Lookahead matters but is small here**:
full-sample Sharpe-tilt was +2.00 vs causal +2.04 — Bybit was _consistently_ best, so trailing-Sharpe tilt converges to
the same allocation. **Concentration:** causal tilt avg weight Bybit 58% / Binance 42%, **max single-venue 100%** (the
`max(Sharpe,0)`-normalize goes all-in when a venue's trailing Sharpe turns negative) → production needs a **per-venue
weight cap (~65%)**. Combined maxDD −18% (tilt) / −23% (equal) vs Binance-alone −34%. **Verdict: multi-venue buys
CAPACITY + robustness + lower-DD-vs-worst-venue, NOT a Sharpe lift — combining 2 venues at corr 0.67 ≈ best-single. A
real Sharpe lift needs 4+ comparable, less-correlated venues** (`S·√(N/(1+(N-1)ρ))`).

**2. HL-momentum cross-venue FILTER (operator idea — works).** HL funding is momentum; use it to veto the reversion
book's falling knives. Gentle veto (drop a long if its HL funding is in the bottom decile = HL says "keeps falling";
drop a short if top decile): Sharpe **1.64→1.77**, maxDD **−34%→−30%**. Dosing is a scalpel — q=0.2/0.33 over-filter
(remove good reversion candidates) and hurt Sharpe. **First real value from HL's (otherwise weak/losing) momentum signal
— as a cross-venue filter, not a standalone book.** Only covers HL-listed coins (26/30 here).

**3. DD CONTROL to ~10% — risk OVERLAYS win, coin-filters BACKFIRE (operator goal).** Diagnostic (per position-day, do
beta/corr/vol predict PnL?): **high-corr-to-BTC coins do BETTER (+15bp) / low-corr WORSE (−7/−23bp); low realized-vol
BEST (+18bp); beta weak.** So **beta/correlation FILTERS hurt** — beta≤1.2 → Sharpe 1.77→1.02/DD −52%; corr≤0.6 →
catastrophic (−122% DD). The "idiosyncratic/low-corr is cleaner" intuition is BACKWARDS for this book. **What works: (a)
BETA-HEDGE** (book is $-neutral but carries residual BTC-beta — long basket of crashed coins ≠ short basket's beta;
hedge by trading BTC sized to `−book_beta`) → Sharpe **1.77→2.03**, DD unchanged (removes market _noise_). **(b)
VOL-TARGET** (scale exposure to a trailing-vol budget) → the DD DIAL: 12% vol → DD −10%, Sharpe slightly up. **Combined
(HL-filter + beta-hedge + vol-target 10%): Sharpe 2.22, maxDD −7%, +27%/yr, Calmar 3.88 — the chosen base.** Dial
vol-target for the DD budget (18% → ~~−15% DD/~~+40%).

**4. Cross-venue funding-ANOMALY (operator idea — counterintuitive).** Is extreme funding on ONE venue (idiosyncratic)
vs ALL venues (broad consensus) different? Diagnostic (position PnL by Binance-funding outlier-ness vs Bybit/OKX/HL
consensus): **broad CONSENSUS reverts BETTER (+10bp); idiosyncratic single-venue outlier WORSE (−9bp)** — opposite the
first guess (when all venues agree on extreme funding it's genuine crowding that reliably unwinds; a Binance-only quirk
reverts in funding but not price). Weak (19bp spread) + over-filters as a hard gate → a mild _soft overweight_ on
consensus, not a lever.

**5. SIZING — inverse-vol already optimal; don't size by beta (operator idea).** On the chosen base: inverse-vol +2.22 ≈
corr-tilt +2.23 (correlation edge already absorbed by inverse-vol; explicit tilt = noise); **inverse-beta +1.83 /
beta-proportional +1.91 both LOSE** (beta = corr×vol/vol_btc mixes the helpful corr with the harmful vol). The one
refinement: **ivol×inverse-beta → Calmar 4.36, DD −6%, +28%/yr** (best DD-adjusted, slightly lower Sharpe 2.04) — use it
if minimizing DD-per-return beats raw Sharpe.

**Caveats across all:** survivorship-optimistic (currently-listed survivors, no dead coins → above the honest 1.44);
HL/anomaly filters only reach coins listed on the other venues (small-cap tail thinner); Aster short/recent; 2025-26
high-dispersion regime inflates recent years — underwrite ex-2026.

## TURNOVER reduction SOLVED + deployable book committed (2026-06-18, /autonomous, all CAUSAL)

Operator goal: harden the reversion book vs fees by cutting turnover ~2x WITHOUT losing >10% Sharpe, no look-ahead.
**Corrected baseline:** the final book (EWMA-7 + HL-veto + beta-hedge + vol-target) runs **0.70 turnover/day** (not the
~0.3 earlier mis-estimate — the HL-veto's daily flips + the 26-coin concentration drive it). Swept ~25 causal methods
(longer EWMA, hold-N, no-trade band, position-smoothing, rank-buffer hysteresis, L1 flip-gate, combos), scored on
turnover + Sharpe@5bp + **Sharpe@10bp** + DD. **WINNER — and it BEATS the constraint (Sharpe rises, not falls):**

| config                                           | turnover        | Sharpe@5bp | Sharpe@10bp      | DD@10 |
| ------------------------------------------------ | --------------- | ---------- | ---------------- | ----- |
| base EWMA-7                                      | 0.70            | +2.22      | +1.78            | -7%   |
| **EWMA-21 + rank-buffer+6 + no-trade-band 0.03** | **0.27 (-62%)** | **+2.34**  | **+2.16 (+21%)** | -7%   |

Mechanism: the book's churn was mostly NOISE (daily rank flips with no signal). Three cheap causal filters — slower
EWMA-21, rank-hysteresis (keep a name until it leaves the k+6 band), no-trade band (skip <3% weight changes) — strip the
noise trades that were pure fee drag, so the book IMPROVES at every fee level (the win compounds at higher fees). A
no-trade band of 0.02 alone is a free win (Sharpe@10bp 1.78→1.85). Single methods that over-smooth (hold-3d, pos-smooth
a=0.3) lose Sharpe; the combo of three light filters is the sweet spot.

**SHIPPED: `e2e-testing/scripts/defi/funding_reversion_crossvenue_book.py`** (lifecycle marker Epic strategy_master /
campaign / delete-when folded into CarryStakedBasisRankAllocator). Reproducible — pulls Binance funding+price live
(fapi, cached) + HL funding from GCS perp_funding; the full stacked book (EWMA-21 + buffer+6 + band 0.03 + HL-veto +
inverse-vol + beta-hedge + vol-target 10%), causal + non-compounded, with fee-sensitivity + HTML plot. **Full-history
2022-2026 (incl. 2022 bear + pre-HL period where the veto can't apply): Sharpe 2.17, maxDD -16%, +26%/yr, turnover
0.19/day, fee-robust to 20bp (Sharpe 1.78@20bp / 2.04@10bp).** The HL-window-only (2023-2026) is the stronger 2.34/-7%.
CLI knobs: `--ewma-halflife --rank-buffer --no-trade-band --hl-decile --vol-target --fee-bp`. Awaiting the other agent's
cross-sectional ML signals to improve winner/loser selection (not blocking).

## Robustness/OOS, 2022-DD attribution, directional squeeze overlay (2026-06-18, /autonomous, all CAUSAL)

**ROBUSTNESS/OOS of the book's turnover config (guards the meta-level overfit of selecting params on the full sample):**
neighbourhood of 45 configs around (EWMA-21,buffer-6,band-0.03) spans Sharpe@10bp 1.66-2.23 (median 1.88; only 31%

> =2.0; winner 2.04) — ALL positive (no fragile spike) but with real variation. True OOS split @2024-03-26: train-best
> applied UNCHANGED to held-out test = +2.20; the winner is positive on BOTH halves (1st +1.60 / 2nd +2.51). **Verdict:
> generalises, NOT overfit — but the honest FORWARD Sharpe is ~1.6-1.9 @10bp (the OOS-1st-half / neighbourhood median),
> NOT the 2.34 headline** (the 2nd-half strength rides the 2025-26 dispersion). Size on the conservative end.

**2022 DRAWDOWN attributed (operator: coin/venue/market-down/volume/turnover?):** the -16% maxDD (peak 2022-05-12 +20%
-> trough 2022-12-02 +4%, 204 days, ~10mo to recover) is **NONE of those** — it is a BROAD cross-sectional REVERSION
FAILURE. Worst-3 coins = only 37% of losses (BROAD, not concentrated); beta-hedged +7% vs un-hedged +9% (NOT market beta
— removing BTC beta doesn't help); flat across vol quartiles (NOT liquidity); fee drag -0.9% (NOT turnover). The LONG
leg (buying oversold coins) bled **-119% gross** while shorts made +103% — in the relentless 2022 bear (LUNA/FTX) the
reversion premise inverted (oversold kept falling = falling knives) ACROSS the universe. **Critically the HL-veto was
INACTIVE all of 2022 (HL data starts mid-2023)** — the live book's veto specifically targets this, so the -16% is a
worst-case un-vetoed number; HL-era (2023-2026) DDs are -3 to -7%. A relentless bear is the strategy's structural tail
risk (the long leg catches knives) — size for it.

**DIRECTIONAL SQUEEZE-PROTECTION overlay (CeFi agent handoff `…/overlay/`, validated on MY book):** rule = cut/halve a
funding leg on a > threshold-sigma 2-day move AGAINST it (long crashing sigma<-thr / short squeezing sigma>+thr) — the
rare extreme (|sigma|>2 fires ~3% of days). The agent's other signals are dead ends (reversal alpha-blend HURTS, horizon
mismatch; ML IC +0.001) — ONLY this risk overlay is accretive, confirmed on my book. Swept 2.0-3.5 x halve/cut: **all
thresholds help, none hurt; 2.0sigma best on MY (faster, vol-targeted) book** (vs their 2.5 floor). With the agent's
richer signal: Sharpe 2.17->2.28, maxDD -16->-14%, 2022 +0.50->+0.98. **SHIPPED self-computed** (sigma_move_2d = 2-day
return / rolling-30 vol, lagged — live-able, corr +0.49 to theirs, weaker but self-contained): Sharpe 2.17->2.21, maxDD
**-16->-13%**, Calmar 1.66->2.04, 2022 +0.50->+0.58. Wired into
`e2e-testing/scripts/defi/funding_reversion_crossvenue_book.py` as overlay 8 (`--squeeze-threshold` default 2.0 /
`--squeeze-factor` 0.5, default ON; richer external signal substitutable). `reversal_z` is CONTEXT only (naive rule
loses — not wired). Awaiting any future cross-sectional ML signals to strengthen winner/loser selection (not blocking).

## Multi-venue capacity + capped allocator (2026-06-18, /autonomous terminus)

Ran the FULL overlay stack (EWMA-21 + buffer-6 + band-0.03 + HL-veto + inverse-vol + beta-hedge + vol-target + squeeze)
on each arbitraged venue over the 30-survivor universe, combined with a CAUSAL weight-capped Sharpe-tilt. Per-venue:
Binance ~2.2/-13% · Bybit +1.93/-8% · Aster +1.03/-12% (short history, adds capacity). **Combined (Binance+Bybit, corr
0.63): equal-weight Sharpe 2.29 / DD -10%; capped-tilt 2.18 / -9% — both BEAT single-Binance (2.21/-13%) on BOTH axes.**
Multi-venue diversifies the 2022-heavy Binance tail against Bybit (less 2022 exposure) → cuts DD -13%->-10% AND nudges
Sharpe up, plus 2-3x capacity. **Refines the earlier "capacity-not-Sharpe": with the full overlay stack + a 2022-heavy
lead venue, multi-venue helps modestly on Sharpe and meaningfully on DD.** Equal-weight is the best allocator (venues
comparable → tilt adds noise); the cap is a SAFETY RAIL (prevents 100% concentration), not a Sharpe driver. **Cap-logic
refinement for production: a 2-venue cap of X needs floor = 1-X to truly bind (clip+renorm alone gave 87% realized at
cap 65%).** Research script `/tmp/multivenue_capped.py`; plot `multivenue_capped.html`.

- [ ] [STRATEGY] P2. Productionise the multi-venue capacity book: extend `funding_reversion_crossvenue_book.py` to pull
      Bybit/OKX/Aster (live APIs) + run per-venue + combine with an equal-or-capped allocator (floor=1-cap), for
      capacity + the DD-diversification benefit. **Repo: e2e-testing → strategy-service.**

### /autonomous loop terminus (2026-06-18)

Turnover-reduction dispatch + the CeFi directional-signal handoff are both COMPLETE and shipped. Final deployable book
(`funding_reversion_crossvenue_book.py`, e2e@198ee62): stacked causal overlays, turnover 0.19-0.23/day, Sharpe ~2.2
(honest forward ~1.6-1.9 per OOS), maxDD -13% (single) / -10% (multi-venue), Calmar ~2.0, fee-robust to 20bp, 2022-tail
repaired by the squeeze overlay. Remaining winner/loser improvement is BLOCKED on the awaited cross-sectional ML signals
(external dep) — loop terminates here, not idle-spinning.

## Multi-venue CAPITAL flow + transfer instructions + reversal_z verdict + signal-status CORRECTION (2026-06-18)

**CAPITAL accounting (operator: account for $ per venue + transfer instructions + plot the $ balance).** Sim:
$1M total,
equal-weight across Binance+Bybit, PnL accrues per venue, weekly rebalance to equal-weight of equity with a 5% no-move
band. **Result: $1M
-> $3.08M over 4.5yr (compounded); per-venue today Binance $1.62M / Bybit $1.46M; only 8 transfers
in 4.5yr, ~$75k/yr
moved (avg
$42k/move) — multi-venue capital friction is NEGLIGIBLE** (the band + 0.63
venue-correlation make rebalancing rare). Current instruction: move $78k
Binance->Bybit to re-equalise to $1.538M each.
Transfer log is concrete (date + direction + $) — ready to wire into a
TransferIntent flow. Script `/tmp/capital_flow.py`; plot `/tmp/passB/capital_flow.html` (per-venue $ balance + transfer
bars). Composes with client-funds-isolation (`TransferIntent.client_id`) — these are intra-client multi-venue moves.

- [ ] [STRATEGY] P3. Productionise the multi-venue capital/transfer layer: emit weekly rebalance TransferIntents
      (intra-client, single client_id) from the live per-venue balances vs target weights, 5% no-move band. **Repo:
      e2e-testing -> execution-service TransferCoordinator.**

**reversal_z overlay — TESTED on my book, does NOT help (confirms the CeFi agent).** The economically-sensible use
(reduce a short when reversal_z says oversold/squeeze-prone) HURTS: Sharpe 2.21->1.99/2.17, 2022 +0.58->+0.34. The
opposite sign nominally adds +0.07 (2.28) but is economically BACKWARDS (cuts positions when the reversal signal is
FAVOURABLE to them) = overfit-from-trying-both-signs, not a real edge. NOT shipped (agent warned context-only).

**SIGNAL-STATUS CORRECTION (supersedes the earlier "blocked on awaited ML signals").** The signals are in GCS
(`…/overlay/`) and have been TESTED — there is no better winner/loser signal coming: (a) the CeFi agent's actual
cross-sectional ML signal (15m ensemble, daily-aggregated) HURTS the reversion carry (cs-veto 0.55 / cs-halve 0.77 /
standalone -1.08 on theirs) and does NOT cut the single-coin tail; (b) reversal alpha-blend HURTS (horizon mismatch, the
carry already harvests reversion); (c) reversal_z HURTS on my book (above). STRUCTURAL reason: cs/reversal are REVERSION
signals — the WRONG tool for squeeze/dump avoidance (they lean INTO a squeeze). The ONE transferable accretive overlay
is the MOMENTUM/breakout `sigma_move_2d` squeeze veto — **already shipped** (e2e@198ee62). **The book is COMPLETE, not
blocked.** The CeFi cs alpha is real but 15-min-only — genuinely no value at the daily funding-carry horizon.

## Capital-flow CORRECTION — fixed-leverage moves ~4x more (operator 2026-06-18)

The earlier
"$75k/yr moved" was the FULL-FUNDING regime (post full capital, let PnL compound in place, rebalance only on
weight drift) — which minimises transfers but lets LEVERAGE FLOAT DOWN as you profit (under-deployed, idle capital).
Re-modelled FIXED-LEVERAGE (hold each venue's deployed capital flat, sweep PnL gains to a central treasury / top up
losses weekly, 5% band) per the operator's point that exposure + margin must be held: **$302k/yr
moved (4.0x more, ~30%/yr of capital ~= the book's PnL flow)** — gains swept out (margin would balloon + de-lever),
losses topped up. Treasury accumulates ~$1.15M of swept PnL on a $1M base (redeploy / yield). **Tradeoff is leverage
policy:** full-funding = fewer transfers but drifting-down leverage + idle capital; fixed-leverage = ~4x transfers
(still cheap — weekly stablecoin sweeps, near-zero fee) but capital-efficient + constant exposure (the regime you'd
actually run). The P3 TransferIntent todo should emit the FIXED-LEVERAGE weekly sweep/top-up (not the full-funding
drift-rebalance). Scripts `/tmp/capital_flow{,2}.py`; plots `capital_flow.html` (full-funding) +
`capital_flow_fixedlev.html` (fixed-leverage + treasury).

## Capital/leverage module + paper-trading runner + return convention (2026-06-18, /autonomous)

**Return convention (operator-confirmed):** the book's % returns are on the NET capital / posted margin (the weights sum
to +1 long / -1 short = 1x net, 2x gross notional), NOT on the gross $ — so +27%/yr is on net (~half on gross). It is
NON-COMPOUNDED: fixed notional sized to the INITIAL capital (vol-targeted to constant 10% vol on that fixed base), PnL
not reinvested -> linear returns + profit accrues to treasury separately. **Vol-target DE-LEVERS the gross** from the
raw 2.0x to ~0.9x avg (0.66x on 2026-06-18), so the book is UNDER-deployed at 10% vol -> only ~18% margin needed, ~82%
free; raising `--vol-target` deploys toward the full 2x for proportionally more return + DD (the "fixed size" is a dial,
fixed per chosen vol target).

**SHIPPED `funding_reversion_multivenue_capital.py` (e2e@0751d27):** plots gross leverage (raw 2x -> vol-targeted ~0.9x,

- 1x-net reference line), margin posted per venue, FREE capital, TREASURY of swept PnL ($1.15M on $1M), and both capital
  regimes (full-funding $75k/yr transfers vs fixed-leverage $302k/yr ~ the PnL flow). CLI
  `--capital --vol-target --max-leverage --dd-buffer`. Plot `funding_capital_book.html`.

**SHIPPED `funding_reversion_paper_trade.py` (e2e@fd96c0b):** the live desired-state engine (the secondary/CLI PAPER
path). Pulls live funding+price per venue (Binance fapi + HL GCS + Bybit/Aster live), computes today's desired positions
(full causal stack, vol-targeted to actual ~0.66x gross), emits per coin/venue: side, weight, $ notional, the coin's
funding yield; net funding carry (+13%/yr on deploy); margin/free per venue; persists `desired_positions.json`. NO real
orders. Daily runs accrue the transfer + paper-PnL ledger. **This wires the book to paper trading** — the production
path (fold into strategy-service `CarryStakedBasisRankAllocator` + promote paper->live VM) stays operator-gated.

The full deployable stack is now 3 committed e2e scripts: `funding_reversion_crossvenue_book.py` (backtest, 8 causal
overlays), `_multivenue_capital.py` (capital/leverage/treasury), `_paper_trade.py` (live paper engine).

## Progress Log

- **na-eligibility-audit 2026-08-02** (re-confirms 2026-07-30; only change since = context-scout `context_scope`
  frontmatter, body byte-identical): KEEP-NA, valid — every open todo is strategy/ML research judgment (GBM squeeze
  models, archetype shelving decisions, structure-5 candidacy, prime-broker research).
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope, no change needed (5 entries) --
  `funding_reversion_crossvenue_book.py` is confirmed the doc's own primary shipped script (cited 5x incl. "THE full
  deployable stack" line); parent/sibling fork + custody-providers codex remain the minimal correct set.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-08-02 (unchanged, 13 open todos): every open item
  is strategy/ML research judgment (GBM squeeze models, archetype-shelving decisions, structure-5 candidacy,
  prime-broker research, productionisation calls gated on research conclusions) — one item (the day-mean→per-settlement
  funding switch) is explicitly blocked-by a separate issue doc, tagged DEPENDENCY_BLOCKED; the rest are GENUINE_WORK.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-21** (cross-cutting tranche): KEEP-NA, valid — reaffirms 2026-08-07 (unchanged, 13 open todos): every open item is strategy/ML research judgment (GBM squeeze models, archetype-shelving decisions, structure-5 candidacy, prime-broker research, productionisation calls gated on research conclusions), one explicitly DEPENDENCY_BLOCKED on a separate issue doc.

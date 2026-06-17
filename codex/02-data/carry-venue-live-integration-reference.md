# Carry-strategy venue integration reference (funding · staking · lending)

> **Purpose**: the integration SSOT for the `carry_staked_basis` **live/paper** path — how we source current per-venue
> **perp funding**, **LST staking** APRs, and **lending/borrow** rates from public APIs (or credentials), the per-venue
> quirks, and the conservative-default + TODO discipline for venues whose characteristics we have not yet fully
> verified. Companion to the backtest harness `e2e-testing/scripts/defi/staked_basis_funding_scan.py` and the experiment
> journal `plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md`.
>
> **Why this exists (operator 2026-06-17)**: the backtest was limited to the venues with GCS history
> (Binance/OKX/Bybit/Deribit/Hyperliquid via Tardis + Aster via public API). For **paper/live**, the decision does not
> depend on deep history — given today's funding across venues plus the venue **characteristics** (funding cadence,
> collateral acceptance, capital efficiency) we can rank and position. So the live path uses **every venue we can reach
> by public API or hold credentials for**, with **conservative estimates + a filed TODO** wherever a characteristic is
> not yet verified in a UAC registry. **Batch==live**: the live snapshot feeds the SAME
> `FundingPoint → _build_panel → ensemble → _build_instructions/_diff_to_target` machinery as the backtest — only the
> data source differs.

---

## 1. General approach — how a venue is integrated

The live path produces, for each `(coin, venue)`, a
`FundingPoint(day="LIVE", base, venue_dir, raw_rate, apy_bps, n_settlements)` from the venue's **current** funding, then
feeds the list through the existing `_build_panel(days=["LIVE"], …)` → ensemble → emitter. Each venue needs four things;
the first is fetched live, the other three come from a registry (UAC where known, conservative default + TODO
otherwise):

| Need                      | Source (known venue)                               | Conservative default (new venue) + TODO                            |
| ------------------------- | -------------------------------------------------- | ------------------------------------------------------------------ |
| **current funding rate**  | venue public API (§3)                              | — (must be fetchable; else the venue is BLOCKED-CREDENTIALS)       |
| **funding cadence**       | UAC `perp_funding_cadence.FUNDING_CADENCE_SECONDS` | the interval the API itself returns; else 8h. TODO: add to UAC.    |
| **collateral acceptance** | UAC `venue_collateral.venue_accepts_collateral`    | **cash-margin, stablecoin-only** (no LST, no spot) → funding-only. |
| **capital efficiency**    | derived from collateral (§6)                       | `1/(1+max_adverse_move)` (cash-margin haircut).                    |

**Adding a venue** = (1) add a fetcher to the live-funding registry returning `{BASE: rate_per_interval}` + interval;
(2) add its symbol mapping; (3) add UAC `perp_funding_cadence` + `venue_collateral` entries (or accept the conservative
default and file the TODO). No change to the ranking/emitter — they consume `FundingPoint`/`CoinDay` venue-agnostically.

**Conservative-default principle**: a venue with **unverified** collateral is treated as cash-margin (no spot/LST as
margin) → it can only run a **funding-only short** (stablecoin-margined), efficiency-discounted by the per-asset
max-adverse-move. This never over-states carry (cash-margin is the worst case); it only ever **under**-counts, so a
paper signal built on it is safe. Verify-up to the real program (multi-asset / portfolio margin) lifts the haircut.

---

## 2. Coin universe

Live/paper targets **~40 liquid perp coins** (backtest default 30). The set is the intersection of "listed on enough
venues to form a basis/dispersion pair" and "has a perp on ≥1 reachable venue". Base symbols are normalised UPPER and
mapped per-venue (§3 symbol column). Coins absent on a venue are simply skipped for that venue (honest absence — no
placeholder).

---

## 3. Funding venues — per-venue quirks (probed 2026-06-17, public, no auth)

All reachable from the planning VM. **Field** = the current per-interval funding rate (decimal fraction). **Interval**
drives annualisation (`apy = rate × seconds_per_year / interval_seconds`).

| Venue           | All-symbols? | Endpoint                                             | Funding field             | Interval               | Symbol             | Quirks / gotchas                                                                                                                                               |
| --------------- | ------------ | ---------------------------------------------------- | ------------------------- | ---------------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Binance**     | ✅ all       | `GET fapi/v1/premiumIndex`                           | `lastFundingRate`         | 8h                     | `{BASE}USDT`       | also `nextFundingTime`; a few pairs are 4h (read per-symbol funding interval to be exact).                                                                     |
| **Bybit**       | ✅ all       | `GET v5/market/tickers?category=linear`              | `fundingRate`             | 8h                     | `{BASE}USDT`       | `nextFundingTime` ms; some pairs 4h/1h — per-symbol `fundingInterval` (minutes) via instruments.                                                               |
| **OKX**         | ❌ per-coin  | `GET public/funding-rate?instId={BASE}-USDT-SWAP`    | `fundingRate`             | 8h                     | `{BASE}-USDT-SWAP` | no all-symbols funding endpoint → one call per coin (≤40). `nextFundingTime` provided.                                                                         |
| **Deribit**     | ❌ per-coin  | `GET public/ticker?instrument_name={BASE}-PERPETUAL` | `funding_8h`              | 8h **figure**          | `{BASE}-PERPETUAL` | lists **only BTC/ETH/SOL + a few**; the stored value is the **8h figure** (not the 1h), annualise at 8h.                                                       |
| **Hyperliquid** | ✅ all       | `POST info {"type":"metaAndAssetCtxs"}`              | `funding` (asset ctx)     | **1h**                 | `{BASE}` (bare)    | **hourly** — annualise ×24×365, NOT ×3×365. GET 405s; must POST. One call returns all coins.                                                                   |
| **Aster**       | ✅ all       | `GET fapi/v1/premiumIndex`                           | `lastFundingRate`         | 8h                     | `{BASE}USDT`       | Binance-compatible API; **no GCS backfill** (historical via paginated `fundingRate`).                                                                          |
| **Gate**        | ✅ all       | `GET futures/usdt/contracts`                         | `funding_rate`            | `funding_interval` (s) | `{BASE}_USDT`      | interval is **explicit** per contract (28800=8h); `funding_rate_indicative` = next predicted.                                                                  |
| **KuCoin**      | ✅ all       | `GET contracts/active`                               | `fundingFeeRate`          | 8h                     | `{XBT}USDTM`       | **`XBT`=BTC**; use the `baseCurrency` field for mapping; `granularity` (ms) sometimes null → 8h.                                                               |
| **Bitget**      | ✅ all       | `GET v2/mix/market/tickers?productType=USDT-FUTURES` | `fundingRate`             | 8h                     | `{BASE}USDT`       | per-symbol `current-fund-rate` endpoint also exists; some pairs 4h.                                                                                            |
| **Kraken Fut**  | ✅ all       | `GET derivatives/api/v3/tickers`                     | `fundingRate`÷`markPrice` | **1h**                 | `PF_{XBT}USD`      | **`fundingRate` is ABSOLUTE** (price units/interval) → divide by `markPrice` for the comparable rate; **hourly**; `relativeFundingRate` often null. `XBT`=BTC. |
| **MEXC**        | ❌ per-coin  | `GET contract/funding_rate/{BASE}_USDT`              | `fundingRate`             | `collectCycle` (h)     | `{BASE}_USDT`      | `collectCycle` = interval in **hours** (usually 8); per-coin.                                                                                                  |

**Symbol-base mapping quirks**: `XBT→BTC` (KuCoin, Kraken); Hyperliquid uses the bare base (`BTC`); OKX/Deribit dashed
(`BTC-USDT-SWAP` / `BTC-PERPETUAL`); everyone else `{BASE}USDT` or `{BASE}_USDT`.

**Sign convention**: all return funding as a signed decimal where **positive = longs pay shorts** (so a short collects
positive funding) — Kraken after the `÷markPrice` normalisation matches this. Verify on integration with a 1-coin
cross-check against §3 values.

### 3.1 Cadence correctness (already filed)

UAC `perp_funding_cadence` is the cadence SSOT; UTL `return_metrics.FUNDING_PERIODS_PER_DAY` **disagrees**
(Aster/Deribit 8× wrong) — filed `plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`. There is
**no historical cadence tracker** (a venue changing its interval over time is invisible) — also filed there. For new
venues, prefer the **interval the API returns** over a static assumption.

---

## 4. Staking venues (LST) — the +staking leg

The staked leg adds `staking_apy` to a short's carry **only where the short venue accepts that LST as margin** (§5);
otherwise the position is funding-only. Backtest harness `_BASE_TO_LST`: `ETH→(stETH, LIDO, ETHEREUM, [stETH,wstETH])`,
`SOL→(jitoSOL, JITO, SOLANA, [jitoSOL,mSOL])`. Full LST set to integrate:

| Asset | LST          | Protocol     | Chain    | APR source (live)                                                                    | Notes                                                                                              |
| ----- | ------------ | ------------ | -------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| ETH   | stETH/wstETH | **Lido**     | Ethereum | `lst-rates-central-…` bucket; APY from `exchange_rate` growth (raw `apy` col is 0.0) | the primary ETH LST; accepted on Bybit/OKX/Deribit.                                                |
| ETH   | rETH         | RocketPool   | Ethereum | **TODO** add source (RocketPool `getExchangeRate` / Rated API)                       | verify CEX collateral acceptance.                                                                  |
| ETH   | cbETH        | Coinbase     | Ethereum | **TODO** add source (Coinbase cbETH exchange rate)                                   | verify CEX collateral.                                                                             |
| ETH   | weETH        | **ether.fi** | Ethereum | `lst-rates` venue=`ETHERFI` + **EigenLayer** `eigen_apy_bps` via features-service    | the **restaking** leg: base stake APR + EigenLayer rewards (weekly).                               |
| SOL   | jitoSOL      | **Jito**     | Solana   | `lst-rates` venue=`JITO`; exchange_rate growth                                       | SOL LSTs are collateral on **Drift** only (not in the CEX short set) → SOL is funding-only on CEX. |
| SOL   | mSOL         | Marinade     | Solana   | **TODO** add source                                                                  | Drift collateral.                                                                                  |

**Live APR**: derive from the on-chain exchange-rate growth (`exchange_rate_t / exchange_rate_{t-Δ}` annualised) — the
same method the `lst-rates` bucket uses — or the protocol's published APR endpoint. Conservative default when a source
is missing: use the **trailing realised** rate from the `lst-rates` bucket, or a conservative fixed estimate (e.g. ETH
~3%, SOL ~7%) **and file a TODO** to wire the live source.

**Recursive (leveraged) restaking** (ETH/SOL share-class track): borrow ETH to stake ETH → weETH + EigenLayer; net ≈
`(stake_apr + restake_apr − borrow_apr) × leverage`, `leverage = 1/(1 − max_LTV)` (high in Aave **e-mode**). Borrow rate
from §6. Atomic bundling required (flash-loan receiver). Filed as the ETH/SOL share-class todo in the experiment plan.

---

## 5. Collateral acceptance — which venue takes which LST/spot as margin

UAC `venue_collateral.venue_accepts_collateral(venue, token)` + `get_collateral_haircut(venue, token)` are the SSOT.
Verified (2026-06-16): **stETH/wstETH accepted on Bybit / OKX / Deribit; NOT Binance / Hyperliquid / Aster.** Aster
margining is **USDC (0% haircut, CROSS) / USDT (1%) only** — rejects spot-coin AND LST → stablecoin-margined
funding-short only.

| Venue                          | LST as margin?                | Spot coin as margin?  | → structure available                                        |
| ------------------------------ | ----------------------------- | --------------------- | ------------------------------------------------------------ |
| Bybit/OKX/Deribit              | ✅ stETH/wstETH (haircut)     | ✅ (portfolio margin) | **staked_basis** (LST collateral) + pure basis               |
| Binance                        | ❌                            | ✅ (portfolio margin) | pure basis (spot collateral, `spot_same_venue`)              |
| Hyperliquid/Aster              | ❌                            | ❌ (USDC/USDT only)   | **cash_margin_xvenue** (funding-only, efficiency-discounted) |
| Gate/KuCoin/Bitget/Kraken/MEXC | **unverified → ❌ (default)** | unverified → ❌       | **cash_margin_xvenue** until verified (TODO §8)              |

**New-venue default = cash-margin** (the bottom row). Several of these DO run multi-asset/portfolio-margin programs
(e.g. Gate unified account, Bitget) that would accept spot/LST — verifying lifts them to
`spot_same_venue`/`staked_basis` and improves their efficiency. Until verified in UAC, the conservative default holds.
**TODO §8**.

---

## 6. Capital efficiency + lending (Aave) — the cash floor and borrow leg

**Efficiency** (`_capital_efficiency`/`_pure_efficiency`): spot-collateral venues ≈ `1 − spot_haircut`; LST-collateral
venues `1 − min(collateral_haircut)`; cash-margin venues `1/(1 + max_adverse_move)` with per-asset max-move (BTC .20 /
ETH .25 / alt .60 / small .80, operator 2026-06-16). Cash-margin haircut is why a venue that can't take spot/LST earns
less net basis per unit capital.

**Lending venues** (cash floor + recursive borrow leg):

| Protocol    | Chain          | Use in the strategy                                                                                                   | Rate source (live)                                                                                                                                                         |
| ----------- | -------------- | --------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Aave v3** | Ethereum + L2s | (a) **cash floor** — lend USDT (~4%) when nothing clears the 3% carry floor; (b) **borrow** leg for recursive staking | `mtds` lending-indices backfill (`launch-mtds-lending-indices-backfill-vm.sh`) / Aave IRM utilisation curve; live = Aave `getReserveData` liquidityRate/variableBorrowRate |
| Compound v3 | Ethereum       | alt base/borrow rates                                                                                                 | **TODO** add source                                                                                                                                                        |

The ensemble's **cash floor** (`USDT·cash` CoinDay @ `cash_apy_bps`, default 400) lends idle capital instead of forcing
a sub-floor carry. Live Aave supply/borrow APYs come from the reserve data (`liquidityRate` / `variableBorrowRate`,
RAY-scaled). DeFi error handling: UAC `DefiErrorCode` RECURSIVE_LOOP / ORACLE / Aave codes. The lending-indices backfill

- bucket env-split + consolidator-stale debts are filed in the experiment plan + the data-migration audit.

---

## 7. Mapping to existing code / registries

- Funding fetch + annualise: `staked_basis_funding_scan.py` `_annualise` (UAC `annualise_funding_rate_bps`) + the new
  interval-aware fallback for venues absent from `perp_funding_cadence`.
- Venue lookups: `_VENUE_DIR_TO_CADENCE_KEY` / `_VENUE_DIR_TO_COLLATERAL_KEY` / `_symbol_for` / `_capital_efficiency` —
  extend per new venue (or accept the conservative default + guard unknown venues to cash-margin).
- Collateral/cadence SSOTs: UAC `registry/venue_collateral.py`, `registry/perp_funding_cadence.py`,
  `registry/venue_launch_dates.py`.
- Staking APR data: `lst-rates-central-…` bucket; EigenLayer `eigen_apy_bps` via features-service.

---

## 8. Integration TODOs (tracked in the experiment plan / issue doc)

1. **Build the `--live` multi-venue snapshot mode** in the harness per §1–§3 (11 venues; FundingPoint(day="LIVE");
   interval-aware annualise; conservative cash-margin for the 5 new venues). batch==live: same emitter/diff.
2. **UAC `perp_funding_cadence`**: add Gate/KuCoin/Bitget/Kraken/MEXC cadences (+ the per-pair non-8h exceptions).
3. **UAC `venue_collateral`**: verify + add the 5 new venues' real collateral programs (multi-asset/portfolio margin);
   until verified, the conservative cash-margin default stands.
4. **Staking sources**: wire RocketPool rETH / Coinbase cbETH / Marinade mSOL live APR; confirm ether.fi weETH +
   EigenLayer.
5. **Lending**: live Aave reserve-data supply/borrow APY adapter; Compound v3 source.
6. **Credentialed venues** (no public funding, or richer data with auth — dYdX v4, Vertex, Drift, Paradex, Backpack,
   etc.): file each as **BLOCKED-CREDENTIALS** with the operator ask (vendor/tier/cost) per the External-Data rule;
   build the adapter scaffold anyway.
7. **Sign/units cross-check** on integration: one coin per venue vs the §3 reference values before trusting the ranking.

---
title: CeFi capture universe + perp-gated capture rule (authoritative)
created: 2026-06-23
source:
  - operator directive 2026-06-23
  - cefi_hl_aster_batch_data_gaps_2026_06_22.md
locked_by: live-defi-rollout
parent_epic: mtds_mdps_master
priority: P2
status: active
---

## What this is

Authoritative SSOT for the CeFi capture universe + the capture rule, per operator 2026-06-23. SUPERSEDES the earlier
"curated top-100 guess". The IS catalogue filter + UAC `CEFI_BASE_ASSET_UNIVERSE` + the MTDS capture-universe derivation
all conform to THIS.

## HARD RULE — perp-gated, per venue (every coin, incl. top-100)

A `(venue, base_asset, time)` cell is captured **ONLY IF that venue lists a PERP for that base at that time**.

- perp listed at venue ⇒ capture the **perp**; also capture **spot** for that `(venue, base)` **only if** the venue
  also lists spot. (perp-and-no-spot = fine, spot sourced elsewhere.)
- **spot-and-no-perp ⇒ DROP** — even for a top-100 coin. A spot-only listing with no perp on that venue is out of scope.
- **no perp for that base at that venue ⇒ NO data for that base on that venue at all** (no spot, no perp).
- Being in the universe list is **necessary but NOT sufficient** — perp-existence-at-the-venue is the absolute gate.
- Mechanism: the IS catalogue enumerates all instruments per venue/day, so it knows per `(venue, base, day)` whether a
  perp exists → apply the gate (drop spot-only, drop no-perp bases) in catalogue post-processing / capture-universe
  derivation. HL/ASTER are perp-native → unaffected.

## EXCEPTION — TradFi-linked perps

**Binance** TradFi perps ARE captured (underlyings are TradFi, not crypto-universe coins). **OKX + Bybit** TradFi perps
captured too **where those venues list them**. They ride the same perp-gate (they ARE perps) — just an allow-list
extension beyond the crypto universe.

## UNIVERSE list = union of (A ∪ B ∪ C) ∪ restaking ∪ historical-top-100 ∪ HL/ASTER perp bases ∪ TradFi-perp allow-list

**List A (alts):** 1INCH, AAVE, ACH, AERGO, AGLD, ALICE, ALT, ANKR, APE, API3, ATH, AUCTION, AXL, AXS, BAL, BAND, BAT,
BICO, BIGTIME, BLUR, BNT, CHR, CHZ, COMP, COTI, CRV, CTSI, CVC, CVX, DYDX, EIGEN, ENA, ENJ, ENS, ETHFI, FET, FXS, G,
GALA, GLM, GRT, GTC, HFT, ILV, IMX, INJ, JASMY, KNC, LDO, LINK, LPT, LQTY, LRC, MANA, MASK, MEME, METIS, MOODENG, MORPHO,
NEIRO, NMR, OCEAN, OGN, OMG, ONDO, OXT, PENDLE, POL, QNT, RAD, RARE, REN, RLC, RPL, RSR, SAND, SKL, SKY, SNT, SNX, SPELL,
STG, STORJ, SUSHI, SYRUP, T, TURBO, UMA, UNI, WLD, WOO, XCN, YGG, ZRO, ZRX

**List B (majors/L1):** ADA, ALGO, ATOM, AVAX, BNB, BTC, DASH, DOGE, DOT, ETH, FIL, ICP, LTC, NEAR, SOL, THETA, TRX,
XLM, XRP, ZEC

**List C (overlap):** AAVE, ADA, ALGO, ATOM, AVAX, AXS, BNB, BTC, CHZ, COMP, DASH, DOGE, DOT, ENJ, EOS, ETH, FIL, GALA,
ICP, LINK, LTC, MANA, NEAR, SAND, SOL, THETA, TRX, UNI, XLM, XRP, ZEC

**Restaking extras (DeFi restaking-rewards hedging — grab where available):** KING, EIGEN, ETHFI

**Historical-top-100 (survivorship / rotating baskets):** any base that was a top-100 coin by mcap at ANY time — incl.
retired/declined: FTT, LUNA, LUNC, UST, SRM, RUNE, WAVES, CEL, HT, OKB, LEO, … (so we can measure survivorship bias +
rotating baskets).

**HL/ASTER perp bases:** all base assets from rebuilt `prod/catalog.parquet` (venue ∈ {HYPERLIQUID, ASTER}).

**TradFi-perp allow-list:** Binance (+ OKX/Bybit where listed) TradFi-linked perp underlyings.

## Implementation todos (P0)

- [ ] [UAC] P0. Set `CEFI_BASE_ASSET_UNIVERSE` = the exact union above. Add a TradFi-perp allow-list constant
      (Binance/OKX/Bybit).
- [ ] [IS] P0. Implement the **hard perp-gate** in the Tardis catalogue filter (`_passes_asset_filter` + catalogue
      post-processing): capture `(venue, base)` only if the venue lists a perp for the base at that time; spot rides
      only where perp exists; no-perp ⇒ drop the base on that venue (even top-100). TradFi-linked perps allow-listed for
      Binance/OKX/Bybit.
- [ ] [IS] P0. Re-deploy + re-force-run fetch+aggregate + re-export the per-venue CSV reflecting universe + perp-gate +
      TradFi exception → operator_check gate.

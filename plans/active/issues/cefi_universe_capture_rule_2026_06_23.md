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
"curated top-100 guess".

## TWO-LAYER ARCHITECTURE (operator 2026-06-23 — the key split)

- **IS catalogue = EVERY possible instrument for EVERY venue (FULL enumeration, NO cap).** Reference data is cheap →
  have it all. So the IS Tardis adapter must **DROP** the `CEFI_BASE_ASSET_UNIVERSE` cap from `_passes_asset_filter`
  (this is the operator's original "drop the whitelist gate" — correct AT THE IS LAYER only). The operator_check CSV is
  this full catalogue per venue (everything available + data_types).
- **MTDS capture filter = the MVP universe** — `CEFI_BASE_ASSET_UNIVERSE` (the expanded union below) + the perp-gate +
  the TradFi-perp exception decide WHAT TICK DATA WE DOWNLOAD (so we don't pull hundreds of coins). Applied at the MTDS
  capture-universe derivation (Phase C/D), NOT at IS enumeration. More downloads can be added later without touching IS.
- Therefore the CSV/operator_check is **NOT** blocked on the universe/perp-gate — those are downstream (capture) concerns.

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

## COIN-MARGIN (inverse) perps — liquidity-picked per (venue, base) (operator 2026-06-23)

Perps come in **linear** (USDT/USDC/USD-margined) and **inverse / coin-margined** (settled in the coin). Rule:

- **Deribit**: coin-margin-native → its inverse `BTC-PERPETUAL`/`ETH-PERPETUAL`/`SOL-PERPETUAL` ALWAYS captured (already in catalogue ✅).
- **Every other venue**: capture the **MORE LIQUID** margin type per `(venue, base)` — default **linear** (more liquid for ~all alts); capture **inverse** instead/also **where inverse is more liquid** (historically BTC/ETH inverse on some venues). Operator indifferent beyond "don't skip the liquid one."
- **Generalize** the pick via a **live-data liquidity spot-check** (24h volume / open-interest per contract), per venue, across coins — not a hand-list.

CURRENT GAP (2026-06-23): only linear-margin venues are enumerated — `BINANCE-DELIVERY` (coin-margined Binance) + the inverse Bybit/OKX/Huobi legs are ABSENT despite Tardis access (`binance-delivery, huobi-dm, huobi-dm-swap` in our plan), and the catalogue has **no `margin_type` field**. Deribit inverse is the only coin-margin captured.

- [ ] [IS] P1. Add the inverse-margin Tardis venues we have access to (binance-delivery + inverse Bybit/OKX/Huobi legs) to the venue allow-list so inverse perps enumerate.
- [ ] [IS/UAC] P1. Add a `margin_type` (linear|inverse) field to the catalogue + the canonical instrument key, so the mvp filter can select per (venue, base).
- [ ] [MTDS] P1. Live-data liquidity spot-check (24h vol/OI per contract) → per (venue, base) tag the more-liquid margin mvp=true (Deribit inverse always; default linear). Wire into `is_in_mvp_capture_universe`.

## EXCEPTION — staking/restaking/LST spot (spot-without-perp allow-list, operator 2026-06-23)

The "spot requires a perp for the base at that venue" rule has a CLOSED allow-list of **staking / restaking / liquid-staking
(LST) / liquid-restaking (LRT) tokens** whose SPOT we DO capture even when NO perp exists for them (these are the
`carry_staked_basis` / DeFi-seasonal-rewards legs — we want their spot liquidity; they often have no perp anywhere):

**Include ALL wrapped + unwrapped equivalents of each (operator 2026-06-23).** Extras are harmless (allow-list — only
ones a CEX actually lists spot take effect):

- **Restaking (spot-only):** EIGEN, ETHFI, KING
- **ETH LSTs/LRTs (wrapped + unwrapped):** STETH, WSTETH (Lido); RETH (RocketPool); CBETH (Coinbase); EETH, WEETH
  (ether.fi); FRXETH, SFRXETH (Frax); ANKRETH; OSETH (StakeWise); SWETH, RSWETH (Swell); ETHX (Stader); METH (Mantle);
  + LRTs RSETH (Kelp), EZETH (Renzo), PUFETH (Puffer), RSTETH
- **SOL LSTs:** MSOL (Marinade), JITOSOL + JTO (Jito), BSOL (BlazeStake), JSOL, SCNSOL, INF (Sanctum)

Rule: if `base ∈ STAKING_SPOT_EXCEPTION` → SPOT is mvp=true on ANY venue that lists it, **regardless of perp existence**.
This is the ONLY spot-without-perp carve-out. Consequence for **Upbit** (and other spot-only venues): NOT generally
exempt — Upbit's ordinary spot pairs (ADA-USDT etc.) stay mvp=false (no perp on Upbit); only a staking-exception base
(e.g. STETH) listed on Upbit spot would be captured. (KRW remains out unless `CEFI_ACCEPTED_QUOTE_ASSETS` is later
extended — operator chose NOT to add KRW for now.) The set lives as a UAC constant `STAKING_SPOT_EXCEPTION`; adding a new
staking token is a manual UAC edit (like the base universe).

## EXCEPTION — TradFi-linked perps

**Binance** TradFi perps ARE captured (underlyings are TradFi, not crypto-universe coins). **OKX + Bybit** TradFi perps
captured too **where those venues list them**. They ride the same perp-gate (they ARE perps) — just an allow-list
extension beyond the crypto universe.

## INSTRUMENT-TYPE SCOPE (operator 2026-06-23)

For a base asset in the universe, per venue/time:

- **PERP** — captured where the venue lists it (the perp-gate; this is the primary gate).
- **SPOT** — captured **only where the venue also lists a perp** for that base (perp-gated; spot-and-no-perp ⇒ drop).
- **DATED FUTURES** (quarterly/expiry futures that share the base asset, e.g. `BTC-27JUN25`) — **included** for any
  universe base the venue lists (they're part of the futures complex sharing the base).
- **OPTIONS** — **for now ONLY BTC + ETH on Deribit** for cefi. No other options venues/underlyings (expand later).

So the shared MVP function keys on `(venue, base, instrument_type, day)`: perp→gate; spot→perp-gated; dated-future→base
in universe + venue-listed; option→`venue==deribit AND base∈{BTC,ETH}`.

## DENOMINATOR — the MVP universe IS the honest-coverage denominator (shared SSOT, operator 2026-06-23)

The MVP capture universe is **venue-specific logic, NOT a flat 40-coin list** — so it is ONE shared SSOT function
(`is_in_mvp_capture_universe(venue, base, instrument_type, day)` semantics: base ∈ universe-list AND venue-lists-perp
-for-base-at-day, spot only where perp exists, TradFi-perp allow-list for Binance/OKX/Bybit) consumed by THREE places
that MUST agree (drift = silent correctness bug, per shard-granularity SSOT):

1. **MTDS capture** — what tick data we download (Phase D).
2. **`expected_unattempted` enumerator + data-status denominator** — `enumerate_expected_universe.py` v2 / the MTDS
   pre-flight `record_expected_unattempted` seed the "expected" cells from THIS function, so honest-coverage
   `% = captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)` has the **MVP universe** as
   its denominator — not 40 coins, not the full IS catalogue.
3. **Manifest reclassification (Phase C)** — same function decides which cells are in-scope.

**Missing-reason consequence:** a `(venue, base, day)` cell that is OUTSIDE the MVP universe (base not in the list, OR no
perp on that venue at that time) is **NOT EXPECTED** → it is **excluded from the denominator entirely** (neither
`empty_confirmed` nor `expected_unattempted` — it simply isn't counted). A cell INSIDE the MVP universe that lacks data
is `expected_unattempted` (not yet attempted) or `attempted_failed` (tried, failed) — `empty_confirmed` only for
pre-genesis or data-type-not-available-in-batch. This stops out-of-universe coins from dragging coverage down as false
"missing".

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

**IS layer (full catalogue — no universe filter):**

- [ ] [IS] P0. **Drop** the `CEFI_BASE_ASSET_UNIVERSE` cap from the IS Tardis adapter `_passes_asset_filter` so IS
      enumerates EVERY instrument per venue (full reference). IS keeps NO universe/perp-gate — it's the complete catalogue.
- [ ] [IS] P0. Force-run fetch+aggregate (full enumeration) + export the per-venue CSV (full catalogue + data_types per
      venue) → operator_check gate. (NOT blocked on the universe/perp-gate work.)

**MTDS capture layer (the MVP filter — Phase C/D):**

- [x] ✅ [UAC] P0. Set `CEFI_BASE_ASSET_UNIVERSE` = the exact union above (now the MTDS CAPTURE filter, not the IS gate).
      Add a TradFi-perp allow-list constant (Binance/OKX/Bybit). — unified-api-contracts@5d1f6542 | universe = 518 base
      assets (prior 493 + the 25 missing operator-authoritative bases: ACH AERGO AGLD ATH BICO CHR COTI CVC G GLM GTC HFT
      ILV KING LPT LQTY MASK NMR OXT QNT RAD RARE RLC SPELL T); covers List-A∪B∪C ∪ restaking{KING,EIGEN,ETHFI} ∪
      historical-top-100{FTT,LUNA,…} ∪ HL/ASTER perp bases. TradFi-perp allow-list = `CEFI_EQUITY_PERP_BASE_UNIVERSE`
      (OKX 17 US-equity perps + Binance/Bybit + KRX). `mvp_scope.py`/`total_universe.py` reconciled (v4 / ~518 docstrings,
      base_ccys = CEFI_BASE_ASSET_UNIVERSE | CEFI_EQUITY_PERP_BASE_UNIVERSE, content-hash auto-flips). Tests:
      size-band ≥500, all-25-present, restaking+historical-present, sorted/deterministic. QG green (221s).
- [x] ✅ [MTDS] P0. Implement the **hard perp-gate** in the MTDS capture-universe derivation: download `(venue, base)`
      only if the venue lists a perp for the base at that time; spot rides only where the perp exists; no-perp ⇒ download
      nothing for that base on that venue (even top-100). TradFi-linked perps allow-listed for Binance/OKX/Bybit. —
      Shipped as the shared UAC SSOT `is_in_mvp_capture_universe` (`mvp_scope.py`, v5; `unified-api-contracts@5bceb9fe`)
      consumed by ALL THREE capture consumers: MTDS `cefi_catalog_reader` capture gate (CONSUMER 1,
      `market-tick-data-service@fbf3db8`), `enumerate_expected_universe._enumerate_v2_cefi` denominator gate (CONSUMER 2,
      `instruments-service@e21d681` — enumerator gate + rollup `_add_mvp_column` tagging; the catalogue-owner must RE-RUN
      `build_instrument_catalogue.py` to re-tag the live `mvp` column with the perp-gate, MTDS/enumerator fall back to
      computing the predicate until then), and the
      Phase-C reclassification script (CONSUMER 3, `market-tick-data-service@fbf3db8`, dry-run-default). Perp-gate is per
      base-EXCHANGE (BINANCE-SPOT↔BINANCE-FUTURES). Dated futures NOT perp-gated (spec); OPTION=Deribit-BTC/ETH only.
      Phase D backfills now derive their universe from `mvp=true` rows. (Governs Phase C apply + Phase D — those remain
      operator/Phase-gated runs.)

## Progress Log

- **2026-06-23 (shared-SSOT + 3 consumers)** — STEP 0 + all three consumers WIRED to ONE predicate. **Shipped (all
  QG-green, landed on LDR via quickmerge):** `unified-api-contracts@5bceb9fe` (STEP 0) ·
  `market-tick-data-service@fbf3db8` (CONSUMER 1 + CONSUMER 3) · `instruments-service@e21d681` (CONSUMER 2 enumerator +
  catalogue rollup tagging).
  - **STEP 0 (UAC)** — added `is_in_mvp_capture_universe(venue, base, instrument_type, *, has_perp_for_base, source=None)`
    to `unified_api_contracts/canonical/crosscutting/mvp_scope.py` (exported from the package root + `__all__`).
    Implements the FULL spec on top of `is_mvp`: base ∈ union universe; **HARD perp-gate** (SPOT mvp ONLY IF the EXCHANGE
    lists a perp for the same base — `has_perp_for_base`; spot-no-perp ⇒ FALSE even top-100); PERP/EQUITY_PERP mvp on
    base-membership (the perp self-qualifies); **DATED FUTURES** mvp on base-membership+venue (NOT perp-gated — futures
    complex, per spec line); **OPTIONS** mvp ONLY venue==DERIBIT AND base∈{BTC,ETH} (fixed a latent `is_mvp` bug: the
    options carve-out only narrowed base_ccy, so a Binance BTC option wrongly passed — the new fn gates venue==DERIBIT);
    TradFi-perps (EQUITY_PERP, `CEFI_EQUITY_PERP_BASE_UNIVERSE`) on Binance/OKX/Bybit ⇒ mvp. Added `FUTURE` to the cefi
    rule's `instrument_types`. `MVP_SCOPE_CONFIG_VERSION` 4→5. 11 new unit tests (all pass; 85/85 `test_mvp_scope.py`).
  - **Measured mvp-true delta** (live `prod/catalog.parquet`, base-exchange-keyed perp set): **155,285 mvp-true** of
    226,484 rows (OPTION 146,131 — all DERIBIT BTC/ETH, verified; FUTURE 5,761; PERPETUAL 1,989; SPOT_PAIR 1,404 of
    3,893 → perp-gate dropped ~2,489 spot-only listings). vs the prior base-only `is_mvp` (~157,935) and base-asset-only
    (~226,323). The doc's "152,158" was a base-only snapshot on an earlier catalogue (row count has since shifted with
    the 2010-purge in flight). COMBO bundles correctly tag 0 leaves directly; they roll up to options_chain with the
    OR-of-leaves mvp.
  - **CONSUMER 1 (MTDS capture)** — `market_tick_data_service/engine/cefi_catalog_reader.py`: `list_instruments` +
    `list_not_yet_listed` now gate every yielded row on `is_in_mvp_capture_universe` (prefer the catalogue `mvp` column,
    else compute the predicate — same SSOT). `has_perp_for_base` computed once per call, keyed on the base-exchange token
    (BINANCE covers BINANCE-SPOT+BINANCE-FUTURES). `include_non_mvp=True` ctor flag = diagnostic bypass. 5 unit tests in
    `tests/unit/engine/test_cefi_catalog_reader_mvp_gate.py` (pass).
  - **CONSUMER 2 (expected_unattempted denominator)** — `instruments-service/scripts/enumerate_expected_universe.py`:
    `InstrumentCatalogEntry` gained `base_asset` + `mvp` fields (read from the catalogue columns). `_enumerate_v2_cefi`
    SKIPS any entry not in the MVP universe (out-of-MVP → NOT seeded → excluded from the denominator entirely). Bundle
    roll-up (`_rollup_bundle_grain`) OR-aggregates leaf mvp into the synthetic options_chain/futures_chain entry +
    carries `base_asset=underlying`+`mvp`, with `_mvp_capture_itype` normalising options_chain/combo→OPTION,
    futures_chain→FUTURE so the bundle's mvp resolves. Shared module-level helpers `_cefi_perp_bases`/`_base_exchange`/
    `_cefi_entry_in_mvp_universe`. 3 new gate tests + fixture canonicalisation (114/114 `test_enumerate_expected_universe_v2.py`).
  - **CONSUMER 3 (manifest reclassification SCRIPT — build, do-NOT-run, Phase C)** —
    `market-tick-data-service/scripts/reclassify_cefi_manifest_mvp_universe_2026_06_23.py` (lifecycle marker
    `Epic: mtds_mdps_master` / `Lifecycle: oneoff`). Default **dry-run**; `--apply` gated (snapshots to
    `_index/snapshots/pre_mvp_reclassify_<UTC>.parquet` before write). Rules: out-of-MVP rows REMOVED (not
    empty_confirmed); in-MVP stale `empty_confirmed` (non-pre-genesis reason) → `expected_unattempted`; legit
    pre-genesis empty_confirmed + attempted_failed + captured LEFT untouched. 3 unit tests in
    `tests/unit/scripts/test_reclassify_cefi_manifest_mvp_universe.py` (QG-collected home). **Dry-run on the live 5.49M-row
    manifest**: `out_of_mvp_removed=3,651,839 · in_mvp_kept=1,842,949 (new denominator) ·
    empty_confirmed→expected_unattempted=206,673 · empty_confirmed_kept_legit=637,281 · attempted_failed_left=14,412 ·
    captured_left=770,929`.
  - **IS catalogue rollup** — `instruments-service/scripts/build_instrument_catalogue.py` `_add_mvp_column` now tags the
    cefi `mvp` column via `is_in_mvp_capture_universe` (computes `has_perp_for_base` from the full frame, base-exchange
    keyed). **The rollup must be RE-RUN by the catalogue-owning worker** to re-tag the live `mvp` column with the
    perp-gate (it currently carries the base-only tag); MTDS/enumerator fall back to computing the predicate until then,
    so they're correct regardless. NO new signature needed — the rollup change is internal to `_add_mvp_column`.
  - **Multi-agent note**: the MTDS slot clone is contended by another live session (prediction-adapter WIP, mtime live);
    my cefi_catalog_reader WIP was stashed by a concurrent ff-pull as "park foreign cefi WIP" then recovered from
    `stash@{0}` (cefi_catalog_reader.py only — foreign prediction files untouched). Ship scoped via `--files`.

- **2026-06-23** — UAC universe-set P0 COMPLETE (`unified-api-contracts@5d1f6542`). Inherited the prior worker's dirty
  WIP in UAC (the 493-coin expansion + `mvp_scope.py`/`total_universe.py`/test reconciliations — came to rest, QG had
  died) and finished it. The 493 set was missing 25 of the operator's explicit authoritative-list coins; added them all
  (ACH AERGO AGLD ATH BICO CHR COTI CVC G GLM GTC HFT ILV KING LPT LQTY MASK NMR OXT QNT RAD RARE RLC SPELL T) →
  `CEFI_BASE_ASSET_UNIVERSE` = **518** base assets, sorted + deterministic (8-per-line `# fmt: off` block). Verified
  `mvp_scope.py` (v4, base_ccys = `CEFI_BASE_ASSET_UNIVERSE | CEFI_EQUITY_PERP_BASE_UNIVERSE`, content-hash auto-flips,
  docstrings already ~490/no-44) + `total_universe.py` (references the constant, no literal count, docstrings clean) — both
  sound, no stale "44" left; updated the `~490`→`~518` count comment in the registry. Tests: added
  `test_operator_authoritative_2026_06_23_bases_present` (all 25), `test_restaking_extras_present` (KING/EIGEN/ETHFI),
  `test_key_historical_coins_present` (FTT/LUNA); bumped `test_universe_size_band` floor 250→500. The prior worker's
  `test_mvp_scope.py` SUI→synthetic-token change kept (SUI is now in-universe). QG green (221s, sentinel
  `6e8f8297`→content-identical after lifecycle-marker FF to `14466d86`). The TradFi-perp allow-list constant the P0 asked
  for already exists as `CEFI_EQUITY_PERP_BASE_UNIVERSE` (OKX 17 US-equity perps + Binance/Bybit + KRX). IS/MTDS P0 items
  left for their owning workers (out of scope — do-not-touch IS/deployment).

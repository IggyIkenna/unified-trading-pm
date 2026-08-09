---
doc_type: issue
title: CeFi capture universe + perp-gated capture rule (authoritative)
summary:
  Authoritative SSOT for the CeFi capture universe + the capture rule, per operator 2026-06-23. SUPERSEDES the earlier
  "curated top-100 guess".
status: open
nature: process
asset_group:
  [cefi] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine mistag:
  # title says "CeFi capture universe" and tags already say "cefi" -- content is cefi-only
stage: [meta]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [cefi, mvp, catalogue, honest-coverage, data-correctness, mtds, instruments, uac]
related: [mvp_backfill_cefi_tick_v10_2026_06_27, /plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md]
created: 2026-06-23
author: unknown
parent_epic: mtds_mdps_master
priority: P2
source: [operator directive 2026-06-23, cefi_hl_aster_batch_data_gaps_2026_06_22.md]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-26
context_scope:
  [
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/mvp_scope.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/liquid_representative.py,
    market-tick-data-service/market_tick_data_service/engine/cefi_catalog_reader.py,
    /plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md,
  ]
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
- Therefore the CSV/operator_check is **NOT** blocked on the universe/perp-gate — those are downstream (capture)
  concerns.

## HARD RULE — perp-gated, per venue (every coin, incl. top-100)

A `(venue, base_asset, time)` cell is captured **ONLY IF that venue lists a PERP for that base at that time**.

- perp listed at venue ⇒ capture the **perp**; also capture **spot** for that `(venue, base)` **only if** the venue also
  lists spot. (perp-and-no-spot = fine, spot sourced elsewhere.)
- **spot-and-no-perp ⇒ DROP** — even for a top-100 coin. A spot-only listing with no perp on that venue is out of scope.
- **no perp for that base at that venue ⇒ NO data for that base on that venue at all** (no spot, no perp).
- Being in the universe list is **necessary but NOT sufficient** — perp-existence-at-the-venue is the absolute gate.
- Mechanism: the IS catalogue enumerates all instruments per venue/day, so it knows per `(venue, base, day)` whether a
  perp exists → apply the gate (drop spot-only, drop no-perp bases) in catalogue post-processing / capture-universe
  derivation. HL/ASTER are perp-native → unaffected.

## COIN-MARGIN (inverse) perps — liquidity-picked per (venue, base) (operator 2026-06-23)

Perps come in **linear** (USDT/USDC/USD-margined) and **inverse / coin-margined** (settled in the coin). Rule:

- **Deribit**: split by SETTLEMENT, not blanket-inverse (corrected 2026-06-24, operator). **Inverse** (coin-settled, USD
  quote) = `BTC-PERPETUAL` / `ETH-PERPETUAL` only. **Linear** (USDC/USDT-margined) = the alt perps Deribit added later —
  `SOL_USDC-PERPETUAL`, `TRUMP*_USDC`, `BTC_USDC-PERPETUAL`, etc. (Deribit never made a coin-margined SOL/alt perp). So
  `margin_type` is derived **by quote** (`USD`→inverse, `USDC`/`USDT`→linear) — `_infer_margin_type` does exactly this.
  Both legs are captured: capture is base-in-universe + perp-exists, NOT margin-gated, so Deribit's USDC alt perps
  (SOL/TRUMP) ARE captured (as linear) — never dropped or mislabeled inverse. (already in catalogue ✅).
- **Every other venue**: capture the **MORE LIQUID** margin type per `(venue, base)` — default **linear** (more liquid
  for ~all alts); capture **inverse** instead/also **where inverse is more liquid** (historically BTC/ETH inverse on
  some venues). Operator indifferent beyond "don't skip the liquid one."
- **Generalize** the pick via a **live-data liquidity spot-check** (24h volume / open-interest per contract), per venue,
  across coins — not a hand-list.

CURRENT GAP (2026-06-23): only linear-margin venues are enumerated — `BINANCE-DELIVERY` (coin-margined Binance) + the
inverse Bybit/OKX/Huobi legs are ABSENT despite Tardis access (`binance-delivery, huobi-dm, huobi-dm-swap` in our plan),
and the catalogue has **no `margin_type` field**. Deribit inverse is the only coin-margin captured.

- [x] ✅ [IS] P1. Add the inverse-margin Tardis venues we have access to (binance-delivery + inverse Bybit/OKX/Huobi
      legs) to the venue allow-list so inverse perps enumerate. — instruments-service@4838738 | BINANCE-DELIVERY added
      to `CANONICAL_VENUE_TO_ADAPTER`, `_TARDIS_VENUE_EXCHANGES`, `_CEFI_VENUES`; `_infer_margin_type` extended for
      `binance-delivery` → MarginType.INVERSE; UAC venue registries (venue_mapping.py, market_data_categories.py,
      mvp_scope.py) updated at uac@a8712016.
- [x] ✅ [IS] [UAC] P1. Add a `margin_type` (linear|inverse) field to the catalogue + the canonical instrument key, so
      the mvp filter can select per (venue, base). — instruments-service@4838738 | `margin_type` added to
      CATALOG_COLUMNS + `_extract_meta` + `build_catalogue_dataframe` in `scripts/build_instrument_catalogue.py`;
      MarginType enum already in UAC `_instrument_enums.py`; flows from `_infer_margin_type` in tardis parsing.py
      through IS InstrumentRecord to the catalogue parquet.
- [x] ✅ [MTDS] P1. Live-data liquidity spot-check (24h vol/OI per contract) → per (venue, base) tag the more-liquid
      margin mvp=true (Deribit inverse always; default linear). Wire into `is_in_mvp_capture_universe`. — uac@a8712016 |
      Deterministic default shipped: BINANCE-DELIVERY PERPETUALs + FUTUREs qualify for MVP via base-membership in
      `mvp_scope.py` cefi_mvp_venues frozenset; `MVP_SCOPE_CONFIG_VERSION` bumped 8→9. Deribit inverse already captured
      (always-mvp by pre-existing Deribit PERPETUAL branch). Full live-data 24h-vol/OI spot-check to dynamically pick
      more-liquid margin side is a TODO (requires live Tardis API calls per contract; scaffolded with a comment in
      mvp_scope.py § "live-liquidity hook TODO").
- [x] ✅ [MTDS] P2. **UAC selector contract shipped — `unified-api-contracts@cae957ab`.** Investigated first (premise
      was stale): (1) the "scaffolded comment hook" in `mvp_scope.py` no longer exists — grepped all 4 `_mvp_scope_*.py`
      submodules, zero `margin`/`liquidity` hits; (2) the deterministic default this todo described (BINANCE-DELIVERY
      via base-membership) is GONE — a LATER operator ruling (v10, 2026-06-27, decision #3, `_mvp_scope_rules.py:452`)
      removed BINANCE-DELIVERY from the cefi MVP venues entirely (COIN-M delivery ruled not MVP), so that specific
      ambiguity no longer exists. BUT the underlying problem is still real for OTHER venues: `_infer_margin_type`
      (instruments-service `tardis/parsing.py`) confirms BYBIT (bare canonical venue) and OKX-SWAP both expose linear
      AND inverse legs of the same base under one canonical venue key, and both venues are still declared in the cefi
      MVP `venues` frozenset (`_mvp_scope_rules.py:403,414-415`) — since `is_in_mvp_capture_universe` has zero
      margin_type-awareness, BOTH legs currently pass the MVP gate unfiltered (not wrong, just not the "pick the more
      liquid one" behavior this rule specifies). Found the established precedent for exactly this shape of problem:
      `liquid_representative.py` already ships `execution_spot_representative`/`feature_perp_representative` — PURE
      functions taking caller-supplied volume observations (aggregated by the caller from data we already capture, e.g.
      MDPS candle volume — NOT a live external API call, contra this todo's original "requires live Tardis API calls per
      contract" framing). Added `margin_type_representative(venue, base, margin_volumes) -> MarginType` +
      `MarginVolumeObservation` dataclass to the SAME module, mirroring the pattern exactly (sums volume per
      margin_type, LINEAR wins ties + no-data per the operator's documented "default linear" rule); exported from
      `unified_api_contracts/__init__.py` top-level facade. 15 new unit tests in `test_liquid_representative.py` (basic
      selection, volume-sum-per-type, QUANTO-ignored, filtering, purity/determinism) — mirror the existing test classes'
      structure. QG green (571s). **Follow-up (NOT this todo — a genuinely separate consumer-wiring task, not done here
      to avoid guessing at untested MTDS capture-flow integration details):** wire `margin_type_representative` into
      MTDS's `cefi_catalog_reader.py` capture-universe derivation for BYBIT/OKX-SWAP/KRAKEN-FUTURES so only the winning
      margin type is actually captured (today both are captured, unfiltered — safe but not cost-minimal) — see the new
      todo below.
- [x] ✅ [MTDS] P3. **Wire `margin_type_representative` (unified-api-contracts, shipped `cae957ab`) into MTDS's capture
      layer** — market-tick-data-service@d9ce3b3d | Investigated first (BLK-4cb04e0d, 2026-07-31): a real
      `MarginVolumeObservation` source needs new manifest-query infra (no service↔service dep to MDPS is allowed, and
      the sibling `feature_perp_representative` selector is STILL unwired in prod for the same reason) — building it
      properly exceeds this P3's scope. Main-agent interim ruling (Option B, disposition=partial pending operator
      ratification): shipped the SAFE subset now — `cefi_catalog_reader.py`'s `_margin_leg_gated` calls
      `margin_type_representative` with NO observations (its documented no-data default is LINEAR) for the 3 dual-margin
      venues (BYBIT/OKX-SWAP/KRAKEN-FUTURES), dropping the INVERSE leg for ALTS only. BTC/ETH are EXEMPTED
      (`_MARGIN_GATE_EXEMPT_BASES`) — both legs stay captured, matching today's safe behavior — because the issue doc
      documents INVERSE as historically more liquid than LINEAR for those two bases on some venues, so a fake no-data
      default would risk dropping the actually-more-liquid leg (a correctness regression, not a cost optimization).
      DERIBIT/BINANCE-DELIVERY untouched, as scoped. 5 new unit tests (`test_cefi_catalog_reader_margin_gate.py`) +
      updated the existing mvp-gate test for the new `venue` param. Full QG green. Follow-up (real volume source)
      tracked below — NOT done here.
- [x] [MTDS] P2. ✅ **Build a shared manifest-volume-aggregation utility + wire it into BOTH the BTC/ETH margin-leg gate
      above (`cefi_catalog_reader.py` `_MARGIN_GATE_EXEMPT_BASES`) AND the still-unwired `feature_perp_representative`
      call in `features-service/features_service/delta_one/cli/handlers/batch_handler.py` (currently calls
      `filter_instruments_for_family` with no `venue_volumes`, so it's a permanent no-op).** Source: MTDS's OWN manifest
      row_count, trailing N-day aggregate per (venue, base[, margin_type]) — MTDS already captures trades for both
      margin legs today, so this is genuinely "data we already capture" (the UAC `liquid_representative.py` docstring's
      design basis), with NO new service↔service dependency (MDPS candle volume is out of reach per
      `/codex/04-architecture/tier-and-import-architecture.md`'s no-service-deps rule). Build ONCE, consume from both
      sites — a one-off just for the margin gate is not the move (main-agent ruling, BLK-4cb04e0d, 2026-07-31). Once
      real observations exist for BTC/ETH, drop them from `_MARGIN_GATE_EXEMPT_BASES` and re-verify against measured
      volume instead of the historical-default assumption. **Shipped — market-tick-data-service@a89e4114 (margin-gate
      wiring) + features-service@48911e87 (originally committed as 2f480da2, rewritten by an autostash-rebase during
      push; `batch_handler.py` wiring) — both re-verified via a fresh Pass-1 `quality-gates.sh` on their exact HEAD
      (neither sentinel matched, so this was a genuine QG run, not a same-SHA retry) then landed via Pass-2
      `quickmerge --agent`, both confirmed on origin/live-defi-rollout. slot-8, 2026-07-31T13:45Z.**

- [x] [MTDS] P2. ✅ **RECOVERY (backstop) — a COMPLETE implementation of the todo above already exists as
      committed-but-unpushed WIP in slot 8's worktree; INHERIT it, do NOT re-implement.** As of 2026-07-31 the UTL half
      (`aggregate_cefi_manifest_volume` in `unified_trading_library/manifest_writer/_volume_aggregation.py`) is already
      on origin; the two consumer halves are stranded ahead=1 in slot 8's `.tabs/8`:
      `market-tick-data-service@a89e4114057e` (the `cefi_catalog_reader.py` margin-gate wiring) and, originally
      committed in slot 8's worktree as `2f480da24764` then **rewritten by an autostash-rebase during push** to the
      final landed commit `features-service@48911e87f50809167a973b6ece6bb693612480d3`
      (`feat(delta_one): wire real venue-volume observations into the perp collapse`, 2026-07-31, confirmed on
      origin/live-defi-rollout) — the `batch_handler.py` `feature_perp_representative` wiring. Both carry a
      `Quickmerge: agent` trailer, but NEITHER repo's `.qg_last_passed_sha` sentinel matches HEAD — so this is NOT a
      same-SHA `quickmerge --agent` retry. Recovery path, from slot 8 itself (still live, still holding both commits) or
      a live inheritor of `.tabs/8` once its liveness gate is clear: re-run Pass-1 `quality-gates.sh` on each EXACT HEAD
      → `quickmerge --agent` per repo → flip the `[MTDS] P2` build checkbox above, citing both SHAs. Do NOT
      `reset_worktree` slot 8 until both land. Provenance: review-role agt-8ce066 (msgs 2969/2972) pinged slot 8
      directly; this todo is the durable backstop if that worker-actionable ping is missed on a slot-8 recycle.
      **Recovery completed by slot 8 itself (the live original holder) — see evidence on the todo above.**

## EXCEPTION — staking/restaking/LST spot (spot-without-perp allow-list, operator 2026-06-23)

The "spot requires a perp for the base at that venue" rule has a CLOSED allow-list of **staking / restaking /
liquid-staking (LST) / liquid-restaking (LRT) tokens** whose SPOT we DO capture even when NO perp exists for them (these
are the `carry_staked_basis` / DeFi-seasonal-rewards legs — we want their spot liquidity; they often have no perp
anywhere):

**Include ALL wrapped + unwrapped equivalents of each (operator 2026-06-23).** Extras are harmless (allow-list — only
ones a CEX actually lists spot take effect):

- **Restaking (spot-only):** EIGEN, ETHFI, KING
- **ETH LSTs/LRTs (wrapped + unwrapped):** STETH, WSTETH (Lido); RETH (RocketPool); CBETH (Coinbase); EETH, WEETH
  (ether.fi); FRXETH, SFRXETH (Frax); ANKRETH; OSETH (StakeWise); SWETH, RSWETH (Swell); ETHX (Stader); METH (Mantle);
  - LRTs RSETH (Kelp), EZETH (Renzo), PUFETH (Puffer), RSTETH
- **SOL LSTs:** MSOL (Marinade), JITOSOL + JTO (Jito), BSOL (BlazeStake), JSOL, SCNSOL, INF (Sanctum)

Rule: if `base ∈ STAKING_SPOT_EXCEPTION` → SPOT is mvp=true on ANY venue that lists it, **regardless of perp
existence**. This is the ONLY spot-without-perp carve-out. Consequence for **Upbit** (and other spot-only venues): NOT
generally exempt — Upbit's ordinary spot pairs (ADA-USDT etc.) stay mvp=false (no perp on Upbit); only a
staking-exception base (e.g. STETH) listed on Upbit spot would be captured. (KRW remains out unless
`CEFI_ACCEPTED_QUOTE_ASSETS` is later extended — operator chose NOT to add KRW for now.) The set lives as a UAC constant
`STAKING_SPOT_EXCEPTION`; adding a new staking token is a manual UAC edit (like the base universe).

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

**Missing-reason consequence:** a `(venue, base, day)` cell that is OUTSIDE the MVP universe (base not in the list, OR
no perp on that venue at that time) is **NOT EXPECTED** → it is **excluded from the denominator entirely** (neither
`empty_confirmed` nor `expected_unattempted` — it simply isn't counted). A cell INSIDE the MVP universe that lacks data
is `expected_unattempted` (not yet attempted) or `attempted_failed` (tried, failed) — `empty_confirmed` only for
pre-genesis or data-type-not-available-in-batch. This stops out-of-universe coins from dragging coverage down as false
"missing".

## UNIVERSE list = union of (A ∪ B ∪ C) ∪ restaking ∪ historical-top-100 ∪ HL/ASTER perp bases ∪ TradFi-perp allow-list

**List A (alts):** 1INCH, AAVE, ACH, AERGO, AGLD, ALICE, ALT, ANKR, APE, API3, ATH, AUCTION, AXL, AXS, BAL, BAND, BAT,
BICO, BIGTIME, BLUR, BNT, CHR, CHZ, COMP, COTI, CRV, CTSI, CVC, CVX, DYDX, EIGEN, ENA, ENJ, ENS, ETHFI, FET, FXS, G,
GALA, GLM, GRT, GTC, HFT, ILV, IMX, INJ, JASMY, KNC, LDO, LINK, LPT, LQTY, LRC, MANA, MASK, MEME, METIS, MOODENG,
MORPHO, NEIRO, NMR, OCEAN, OGN, OMG, ONDO, OXT, PENDLE, POL, QNT, RAD, RARE, REN, RLC, RPL, RSR, SAND, SKL, SKY, SNT,
SNX, SPELL, STG, STORJ, SUSHI, SYRUP, T, TURBO, UMA, UNI, WLD, WOO, XCN, YGG, ZRO, ZRX

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

- [x] ✅ [IS] P0. **CONFIRMED DONE (2026-07-26)** — `_passes_asset_filter` (`parsing.py:545`) carries no
      `CEFI_BASE_ASSET_UNIVERSE` cap; docstring documents full-universe enumeration. Live-verified:
      `prod/catalog.parquet` grew 226,484→429,129 rows since this was shipped, confirming full enumeration is live in
      prod via routine IS backfills, not just present in code.
- [x] ✅ [IS] P0. **DONE (2026-07-26)** — generated the per-venue `operator_check` CSV (venue × instrument_type ×
      data_type × mvp, 60 rows) from the live catalogue + a supplementary per-venue `DATA_TYPE_CAPABILITY_REGISTRY`
      summary, reviewed. Side-finding (not actioned): `BINANCE-DELIVERY`/`COINBASE-CDE` have catalogue rows but no
      capability-registry entries. See `cefi_satellite_ao_dispatch_batch2_2026_07_26.md` for full evidence.

**MTDS capture layer (the MVP filter — Phase C/D):**

- [x] ✅ [UAC] P0. Set `CEFI_BASE_ASSET_UNIVERSE` = the exact union above (now the MTDS CAPTURE filter, not the IS
      gate). Add a TradFi-perp allow-list constant (Binance/OKX/Bybit). — unified-api-contracts@5d1f6542 | universe =
      518 base assets (prior 493 + the 25 missing operator-authoritative bases: ACH AERGO AGLD ATH BICO CHR COTI CVC G
      GLM GTC HFT ILV KING LPT LQTY MASK NMR OXT QNT RAD RARE RLC SPELL T); covers List-A∪B∪C ∪
      restaking{KING,EIGEN,ETHFI} ∪ historical-top-100{FTT,LUNA,…} ∪ HL/ASTER perp bases. TradFi-perp allow-list =
      `CEFI_EQUITY_PERP_BASE_UNIVERSE` (OKX 17 US-equity perps + Binance/Bybit + KRX).
      `mvp_scope.py`/`total_universe.py` reconciled (v4 / ~518 docstrings, base_ccys = CEFI_BASE_ASSET_UNIVERSE |
      CEFI_EQUITY_PERP_BASE_UNIVERSE, content-hash auto-flips). Tests: size-band ≥500, all-25-present,
      restaking+historical-present, sorted/deterministic. QG green (221s).
- [x] ✅ [MTDS] P0. Implement the **hard perp-gate** in the MTDS capture-universe derivation: download `(venue, base)`
      only if the venue lists a perp for the base at that time; spot rides only where the perp exists; no-perp ⇒
      download nothing for that base on that venue (even top-100). TradFi-linked perps allow-listed for
      Binance/OKX/Bybit. — Shipped as the shared UAC SSOT `is_in_mvp_capture_universe` (`mvp_scope.py`, v5;
      `unified-api-contracts@5bceb9fe`) consumed by ALL THREE capture consumers: MTDS `cefi_catalog_reader` capture gate
      (CONSUMER 1, `market-tick-data-service@fbf3db8`), `enumerate_expected_universe._enumerate_v2_cefi` denominator
      gate (CONSUMER 2, `instruments-service@e21d681` — enumerator gate + rollup `_add_mvp_column` tagging; the
      catalogue-owner must RE-RUN `build_instrument_catalogue.py` to re-tag the live `mvp` column with the perp-gate,
      MTDS/enumerator fall back to computing the predicate until then), and the Phase-C reclassification script
      (CONSUMER 3, `market-tick-data-service@fbf3db8`, dry-run-default). Perp-gate is per base-EXCHANGE
      (BINANCE-SPOT↔BINANCE-FUTURES). Dated futures NOT perp-gated (spec); OPTION=Deribit-BTC/ETH only. Phase D
      backfills now derive their universe from `mvp=true` rows. (Governs Phase C apply + Phase D — those remain
      operator/Phase-gated runs.)

**Venue gaps + Upbit exception (operator 2026-06-23 — this dispatch):**

- [x] ✅ [UAC/IS] P0. Add `coinbase-international` (Coinbase Derivatives perps) → canonical `COINBASE-FUTURES`. —
      unified-api-contracts@54325576 (all_tardis_exchanges + tardis_to_venue + venue_start_dates 2024-10-31 +
      venue_instrument_type_to_tardis + tardis_exchange_instrument_types + VENUES_BY_ASSET_GROUP[cefi] +
      data_type_capability perp surface). instruments-service@5751c33 (factory CANONICAL_VENUE_TO_ADAPTER + router +
      \_CEFI_VENUES).
- [x] ✅ [UAC/IS] P0. Add `bybit-spot` → canonical `BYBIT-SPOT` (split from BYBIT). — unified-api-contracts@54325576
      (tardis_to_venue bybit-spot→BYBIT-SPOT, was →BYBIT; start 2021-12-04; same surfaces). instruments-service@5751c33.
- [x] ✅ [IS] P0. BITFINEX-SPOT/BITGET-SPOT mvp=0 fixed. — Root cause was BOTH (1) venues absent from MVP rule (added in
      unified-api-contracts@54325576) AND (2, bitfinex only) non-standard base tickers. IS bitfinex base+quote
      normalization (`ALG`→ALGO/`ATO`→ATOM/`DSH`→DASH/`IOT`→IOTA/`UDC`→USDC; `UST`→USDT quote; `:`-delimited parse) in
      `_resolve_bitfinex_spot` (parsing.py). BITGET bases were already canonical → venue-add alone fixes it.
      instruments-service@5751c33.
- [x] ✅ [UAC] P0. UPBIT venue carve-out (`_CEFI_SPOT_PERP_GATE_EXEMPT_VENUES` in is_in_mvp_capture_universe — spot
      mvp=true despite no perp) + KRW accepted FOR UPBIT only (`accepted_quotes_for_venue` SSOT; IS
      `_passes_asset_filter` now venue-aware). — unified-api-contracts@54325576 + instruments-service@5751c33.
- [x] ✅ [IS/UAC] P0. Shipped (unified-api-contracts@54325576 + instruments-service@5751c33), re-enumerated the 6 venues
      (direct `process_instruments(redo_all=True)` for day=2026-06-23, MockEventSink — wrote 2387 records / 6 by_date
      shards), re-ran `build_instrument_catalogue.py --asset-group cefi --allow-catalogue-shrink` (227,576 rows
      promoted, 157,092 mvp). **Post-rollup mvp=True (all were 0; the 2 new venues were absent):** COINBASE-SPOT **123**
      · COINBASE-FUTURES **141** (new) · BYBIT-SPOT **315** (new) · BITFINEX-SPOT **70** (canonical bases
      AAVE/ADA/EIGEN…) · BITGET-SPOT **339** · UPBIT **352** incl. **199 KRW pairs** (KRW-0G/KRW-AAVE/KRW-ADA…). All
      target venues gate correctly. **Orchestrator follow-up (FLAG, NOT run here):** re-run the manifest
      reclassification (`reclassify_cefi_manifest_mvp_universe_2026_06_23.py --apply`) to pick up the new mvp cells in
      the data-status denominator. **RESOLVED 2026-07-26** — `--apply` run via VM, live manifest verified matching
      dry-run projection exactly (8,768,112 in-MVP rows). See `cefi_satellite_ao_dispatch_batch2_2026_07_26.md`.

## Progress Log

- **2026-07-31 ~13:33Z (main-agent agt-9f21bc): slot-8 stranded-WIP recovery backstop filed.** The `[MTDS] P2` build
  todo above was fully implemented then stranded when slot 8 died (tmux_session_lost 13:15:34Z) with the work committed
  but unpushed — `market-tick-data-service@a89e4114057e` + `features-service` (committed as `2f480da24764`, later
  rewritten to `48911e87f50809167a973b6ece6bb693612480d3` by an autostash-rebase during push; the UTL half was already
  on origin). Slot 8 respawned 13:22:01Z and still carries both ahead=1 commits (ff-pull preserves them); review-role
  agt-8ce066 (msgs 2969/2972) pinged it directly with ship instructions. The recovery todo above + this entry are the
  durable backstop per every-follow-up-is-a-todo, in case the direct ping is missed before a recycle. Main does NOT do
  the git recovery itself (cross-slot worktree / quickmerge is worker-craft).
- **2026-06-23 (venue-gaps dispatch — MATERIALIZED + VERIFIED, COMPLETE)** — re-enumerated the 6 affected venues for
  day=2026-06-23 via the orchestrator `process_instruments(redo_all=True, venue_override=[...], mode="batch")` path
  directly (the ServiceBootstrap CLI swallows stdout + skips already-captured cells; the direct call needs
  `setup_events("instruments-service","batch", sink=MockEventSink())` first). Wrote **2387 records / 6 by_date shards**
  (BYBIT-SPOT 533 + COINBASE-FUTURES 169 = the 2 NEW venues, first-ever snapshots; BITFINEX-SPOT 166 with canonical
  bases, BITGET-SPOT 625, COINBASE-SPOT 429, UPBIT 465 incl. KRW). Bitfinex by_date now has ALGO/ATOM (no stale ALG/ATO,
  no colon-leak). Then re-ran `build_instrument_catalogue.py --asset-group cefi --allow-catalogue-shrink` (monotonic_ok,
  PROMOTED 227,576 rows / 157,092 mvp). **prod/catalog.parquet VERIFIED mvp=True per venue:** COINBASE-SPOT 123 ·
  COINBASE-FUTURES 141 · BYBIT-SPOT 315 · BITFINEX-SPOT 70 · BITGET-SPOT 339 · UPBIT 352 (199 KRW pairs). Did NOT
  disturb the running `cefi-ext-full-*` RUN-3 backfill (the new venues aren't in its set; the affected venues'
  today-shard was overwritten with my canonical-code output). **Orchestrator follow-up flagged in the final todo:**
  manifest reclassification `--apply` to credit the new mvp cells in the honest-coverage denominator.
- **2026-06-23 (venue-gaps dispatch — UAC SHIPPED `54325576`)** — all UAC code QG-green (220s) + quickmerge → LDR
  (`Quickmerge: agent`). Changes: `venue_mapping.py` (coinbase-international in all_tardis_exchanges; tardis_to_venue
  bybit-spot→BYBIT-SPOT [was BYBIT] + coinbase-international→COINBASE-FUTURES; start dates BYBIT-SPOT 2021-12-04 /
  COINBASE-FUTURES 2024-10-31; venue_instrument_type_to_tardis + tardis_exchange_instrument_types entries),
  `market_data_categories.py` (VENUES_BY_ASSET_GROUP[cefi] += BYBIT-SPOT, COINBASE-FUTURES),
  `cefi_instrument_universe.py` (`accepted_quotes_for_venue` SSOT + `_CEFI_VENUE_QUOTE_EXTENSIONS={UPBIT:{KRW}}`),
  `mvp_scope.py` (8 venues added to cefi rule `venues`; `_CEFI_SPOT_PERP_GATE_EXEMPT_VENUES={UPBIT}` venue carve-out in
  `is_in_mvp_capture_universe`; MVP_SCOPE_CONFIG_VERSION 7→8), `data_type_capability.py` (BYBIT-SPOT spot surface +
  COINBASE-FUTURES perp surface so neither has empty expected-data-types). Exports wired (registry + root `__init__`).
  Tests: +`test_capture_universe_upbit_spot_no_perp_exempt`/`_new_venues_perp_gated`/`accepted_quotes_for_venue_upbit_krw`;
  fixed 3 stale tests (UPBIT/COINBASE now MVP venues → use GATEIO as the non-MVP example); `all_cefi_venues` count
  20→22. 98/98 test_mvp_scope green; 10336 UAC tests green.
- **2026-06-23 (IS code + live enumeration smoke)** — IS changes (QG running, ship pending): `factory.py`
  (CANONICAL_VENUE_TO_ADAPTER += COINBASE-FUTURES), `router.py` (\_TARDIS_VENUE_EXCHANGES +=
  bybit-spot/coinbase-futures), `venue_core.py` (\_CEFI_VENUES += BYBIT-SPOT, COINBASE-FUTURES — the enumeration list),
  `parsing.py` (`_resolve_bitfinex_spot` +
  `_BITFINEX_BASE_ALIASES`{ALG→ALGO,ATO→ATOM,DSH→DASH,IOT→IOTA,UDC→USDC,UST→USDT,…} +
  `_BITFINEX_QUOTE_ALIASES`{UST→USDT,UDC→USDC}; `_passes_asset_filter` now venue-aware via `accepted_quotes_for_venue`),
  `adapter.py` (passes `canonical_venue` to `_passes_asset_filter`), tardis `__init__.py` re-exports. New test
  `test_tardis_bitfinex_symbol_parse.py`. **Live adapter smoke (real Tardis, no-auth metadata):** bybit-spot→955
  BYBIT-SPOT SPOT_PAIR; coinbase-international→252 COINBASE-FUTURES PERPETUAL + 19 SPOT_PAIR; bitfinex→570 SPOT (was 82
  in stale catalogue) with in-universe bases 32→138, ALGO/ATOM/DASH now canonical, zero colon-leak bases.
- **2026-06-23 (venue-gaps dispatch — DIAGNOSIS, autonomous worker)** — read the live `prod/catalog.parquet` (226,484
  rows, 155,292 mvp=true) + the by_date enumeration snapshots to root-cause every gap before coding:
  - **The MVP rule `venues` set (mvp_scope.py) is the primary gate** — only declares BINANCE-SPOT/-FUTURES, BYBIT,
    OKX-{SPOT,SWAP,FUTURES}, DERIBIT, HYPERLIQUID, ASTER, KRAKEN-{SPOT,FUTURES}. So COINBASE-SPOT/BITFINEX-_/BITGET-_/
    UPBIT/BYBIT-SPOT all fail `_cefi_venue_in_rule` → mvp=0 REGARDLESS of perp-gate. → add them to the rule.
  - **COINBASE-SPOT (437, mvp 0)**: no Coinbase perp venue exists → no perp sibling → perp-gate drops every spot even if
    venue were in the rule. → add `coinbase-international` (Coinbase Derivatives, Tardis HTTP-200, availableSince
    2024-10-31, perps like `1000BONK-PERP`/`2Z-PERP`) as canonical COINBASE-FUTURES.
  - **BYBIT-SPOT: 0 rows in catalogue + by_date.** Tardis `bybit-spot` IS reachable (HTTP-200, availableSince
    2021-12-04) and IS in `all_tardis_exchanges`, BUT the enumeration ROUTER (`router._TARDIS_VENUE_EXCHANGES`) maps
    venue `bybit`→`["bybit"]` (perps only) and `tardis_to_venue` collapses `bybit-spot`→BYBIT — so bybit-spot is never
    fetched as a distinct venue. → split it to canonical BYBIT-SPOT with its own router entry + venue-list membership.
  - **BITFINEX-SPOT (82, mvp 0)**: BOTH causes. (1) venue absent from MVP rule. (2) 50/82 distinct bases out-of-universe
    due to Bitfinex's non-standard tickers: `ALG`(ALGO), `ATO`(ATOM), `DSH`(DASH), `IOT`(IOTA), `UDC`(USDC=quote), +
    `:`-suffixed margin markets (`AAVE:`,`LINK:`,`SHIB:`…). The 25-base spot↔perp overlap the operator cited =
    `{ADA,ALG,ATO,BTC,CHZ,CRV,ENA,ETC,ETH,FIL,LDO,LTC,NEO,POL,SEI,SOL,STG,SUI,TON,TRX,UNI,XLM,XPL,XRP,ZEC}` — ALG/ATO
    must normalize to ALGO/ATOM to be in-universe. → add a bitfinex base-alias map + strip the `:` suffix in the parse.
  - **BITGET-SPOT (634, mvp 0)**: root cause is JUST the MVP-rule-venue gap — 346/593 bases ALREADY in-universe and
    BITGET-FUTURES perps (682) exist to pair them. The out-of-universe remainder is equity perps (AAPL/AMZN — handled by
    EQUITY_PERP) + genuinely-new alts (CETUS/DEEP/CATI) — not a normalization bug. → adding the venue + the existing
    perp-gate fixes it.
  - **UPBIT (202, mvp 0)**: spot-only Korean venue, no perp → perp-gate drops all. Operator wants it as the ONE
    perp-gate exception (kimchi premium) + KRW quote accepted FOR UPBIT (its KRW pairs currently dropped by
    `CEFI_ACCEPTED_QUOTE_ASSETS={USDT,USDC,USD}` at the IS `_passes_asset_filter` gate).
  - **Materialization note**: the catalogue rollup is a pure aggregation of `instrument_availability/by_date/` snapshots
    (written by the live `cefi-ext-full-*` RUN-3 backfill — DO NOT disturb). Re-running the rollup alone flips
    mvp-tagging for venues whose by_date rows already exist (COINBASE-SPOT/BITFINEX/BITGET/UPBIT). BYBIT-SPOT +
    COINBASE-FUTURES need NEW by_date snapshots → a scoped `--venues BYBIT-SPOT,COINBASE-FUTURES` enumeration over a
    recent date (does not touch RUN-3's venues/years).

- **2026-06-23 (staking-spot exception EXPANDED 13 → 28 — UAC SSOT)** — operator wants ALL wrapped+unwrapped LST/LRT
  equivalents in the carve-out (forward-looking allow-list; harmless extras). Shipped `unified-api-contracts@b6aca267`
  (QG-green 218s, quickmerge → LDR, `Quickmerge: agent`). UAC-only — did NOT touch instruments-service (concurrent
  catalogue-rollup session owns it).
  - **`STAKING_SPOT_EXCEPTION`** (`registry/cefi_instrument_universe.py`) 13 → **28** members, sorted/deterministic:
    `{ANKRETH, BSOL, CBETH, EETH, EIGEN, ETHFI, ETHX, EZETH, FRXETH, INF, JITOSOL, JSOL, JTO, KING, METH, MSOL, OSETH, PUFETH, RETH, RSETH, RSTETH, RSWETH, SCNSOL, SFRXETH, STETH, SWETH, WEETH, WSTETH}`.
    Added 15: ETH LSTs/LRTs FRXETH/SFRXETH (Frax), ANKRETH (Ankr), OSETH (StakeWise), SWETH/RSWETH (Swell), ETHX
    (Stader), METH (Mantle), RSETH (Kelp), EZETH (Renzo), PUFETH (Puffer), RSTETH; + SOL LSTs JSOL, SCNSOL, INF
    (Sanctum).
  - **Same 15 added to `CEFI_BASE_ASSET_UNIVERSE`** (each placed in its sorted slot) so the subset invariant
    `STAKING_SPOT_EXCEPTION ⊆ CEFI_BASE_ASSET_UNIVERSE` holds — universe now **540** base assets (was 525). Size-band
    floor `>= 500` (`test_cefi_universe_coverage.py`) still passes. Universe count-comment updated 525 → 540.
  - **`MVP_SCOPE_CONFIG_VERSION` 6 → 7** (`mvp_scope.py`) with a v7 docstring — the cefi `base_ccys` content-hash flips
    automatically with the universe constant. (mvp_scope.py is now 998 L; the QG 900-line check WARNs/non-blocking here
    — overall gate PASSED, sentinel written.)
  - **Tests** (`tests/unit/test_mvp_scope.py`): `test_staking_spot_exception_members` expected-set rewritten to the 28
    (+ `len == 28` assert); `_NEWLY_ADDED_LSTS` extended to all 22 newly-added LSTs (7 v6 + 15 v7) so
    `test_newly_added_lsts_present_in_base_universe` covers them; `test_capture_universe_config_version_bumped` floor
    `>= 6` → `>= 7`. Targeted pytest 105/105 green; subset/no-dupe verified.

- **2026-06-23 (staking-spot exception — UAC SSOT)** — wired the operator's spot-without-perp carve-out into the shared
  capture predicate. Shipped `unified-api-contracts@d5b1fb5` (QG-green 227s, quickmerge → LDR, `Quickmerge: agent`).
  - **New UAC constant** `STAKING_SPOT_EXCEPTION` (frozenset, sorted/deterministic) in
    `registry/cefi_instrument_universe.py` next to `CEFI_BASE_ASSET_UNIVERSE`; 13 members =
    `{BSOL, CBETH, EETH, EIGEN, ETHFI, JITOSOL, JTO, KING, MSOL, RETH, STETH, WEETH, WSTETH}`. Exported from the
    registry `__init__` + the package root `__init__` + both `__all__`s. (These are the dispatch's named 13 — the
    operator's "include all wrapped/unwrapped equivalents" extras in the doc are allow-list-harmless; only ones a CEX
    lists spot take effect. Adding a new staking token = a manual UAC edit, same as the base universe — future extras
    drop in here.)
  - **7 LSTs added to `CEFI_BASE_ASSET_UNIVERSE`** (previously ABSENT, now present so the base-membership leg passes):
    `WSTETH, RETH, WEETH, EETH, MSOL, JITOSOL, BSOL`. (STETH/CBETH/JTO/EIGEN/ETHFI/KING were already present.) Universe
    **518 → 525**, kept sorted in the `# fmt: off` 8-per-line block; `>= 500` size-band floor still holds; no dupes.
  - **Predicate wiring** — `is_in_mvp_capture_universe` (mvp_scope.py): in the SPOT (`_CEFI_PERP_GATED_TYPES`) branch, a
    `base ∈ STAKING_SPOT_EXCEPTION` now returns mvp=TRUE **regardless of `has_perp_for_base`** (the ONLY
    spot-without-perp carve-out). PERP/EQUITY_PERP/dated-FUTURE/OPTION/TradFi logic UNCHANGED.
    `MVP_SCOPE_CONFIG_VERSION` 5→6 (content-hash auto-flips with the expanded `CEFI_BASE_ASSET_UNIVERSE`).
  - **Tests** (`tests/unit/test_mvp_scope.py`, +10): every exception base's SPOT is mvp=true with
    `has_perp_for_base=False` (incl. on Kraken spot); a non-exception spot-no-perp (ADA) is still mvp=false (gate holds)
    and flips true with a perp; the 7 new LSTs ∈ universe; the exception set ⊆ universe; exact-members + frozenset +
    import-surface + version≥6.
  - **Verified post-merge**: universe=525, exception=13, version=6, `STETH spot no-perp`→True, `ADA spot no-perp`→False.
  - **Orchestrator's next step (NOT this dispatch)**: re-run the IS catalogue rollup (`build_instrument_catalogue.py`)
    to re-tag the live cefi `mvp` column with this carve-out; MTDS/enumerator compute the predicate live so they're
    correct until then.

- **2026-06-23 (shared-SSOT + 3 consumers)** — STEP 0 + all three consumers WIRED to ONE predicate. **Shipped (all
  QG-green, landed on LDR via quickmerge):** `unified-api-contracts@5bceb9fe` (STEP 0) ·
  `market-tick-data-service@fbf3db8` (CONSUMER 1 + CONSUMER 3) · `instruments-service@e21d681` (CONSUMER 2 enumerator +
  catalogue rollup tagging).
  - **STEP 0 (UAC)** — added
    `is_in_mvp_capture_universe(venue, base, instrument_type, *, has_perp_for_base, source=None)` to
    `unified_api_contracts/canonical/crosscutting/mvp_scope.py` (exported from the package root + `__all__`). Implements
    the FULL spec on top of `is_mvp`: base ∈ union universe; **HARD perp-gate** (SPOT mvp ONLY IF the EXCHANGE lists a
    perp for the same base — `has_perp_for_base`; spot-no-perp ⇒ FALSE even top-100); PERP/EQUITY_PERP mvp on
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
    else compute the predicate — same SSOT). `has_perp_for_base` computed once per call, keyed on the base-exchange
    token (BINANCE covers BINANCE-SPOT+BINANCE-FUTURES). `include_non_mvp=True` ctor flag = diagnostic bypass. 5 unit
    tests in `tests/unit/engine/test_cefi_catalog_reader_mvp_gate.py` (pass).
  - **CONSUMER 2 (expected_unattempted denominator)** — `instruments-service/scripts/enumerate_expected_universe.py`:
    `InstrumentCatalogEntry` gained `base_asset` + `mvp` fields (read from the catalogue columns). `_enumerate_v2_cefi`
    SKIPS any entry not in the MVP universe (out-of-MVP → NOT seeded → excluded from the denominator entirely). Bundle
    roll-up (`_rollup_bundle_grain`) OR-aggregates leaf mvp into the synthetic options_chain/futures_chain entry +
    carries `base_asset=underlying`+`mvp`, with `_mvp_capture_itype` normalising options_chain/combo→OPTION,
    futures_chain→FUTURE so the bundle's mvp resolves. Shared module-level helpers `_cefi_perp_bases`/`_base_exchange`/
    `_cefi_entry_in_mvp_universe`. 3 new gate tests + fixture canonicalisation (114/114
    `test_enumerate_expected_universe_v2.py`).
  - **CONSUMER 3 (manifest reclassification SCRIPT — build, do-NOT-run, Phase C)** —
    `market-tick-data-service/scripts/reclassify_cefi_manifest_mvp_universe_2026_06_23.py` (lifecycle marker
    `Epic: mtds_mdps_master` / `Lifecycle: oneoff`). Default **dry-run**; `--apply` gated (snapshots to
    `_index/snapshots/pre_mvp_reclassify_<UTC>.parquet` before write). Rules: out-of-MVP rows REMOVED (not
    empty_confirmed); in-MVP stale `empty_confirmed` (non-pre-genesis reason) → `expected_unattempted`; legit
    pre-genesis empty_confirmed + attempted_failed + captured LEFT untouched. 3 unit tests in
    `tests/unit/scripts/test_reclassify_cefi_manifest_mvp_universe.py` (QG-collected home). **Dry-run on the live
    5.49M-row manifest**:
    `out_of_mvp_removed=3,651,839 · in_mvp_kept=1,842,949 (new denominator) · empty_confirmed→expected_unattempted=206,673 · empty_confirmed_kept_legit=637,281 · attempted_failed_left=14,412 · captured_left=770,929`.
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
  docstrings already ~490/no-44) + `total_universe.py` (references the constant, no literal count, docstrings clean) —
  both sound, no stale "44" left; updated the `~490`→`~518` count comment in the registry. Tests: added
  `test_operator_authoritative_2026_06_23_bases_present` (all 25), `test_restaking_extras_present` (KING/EIGEN/ETHFI),
  `test_key_historical_coins_present` (FTT/LUNA); bumped `test_universe_size_band` floor 250→500. The prior worker's
  `test_mvp_scope.py` SUI→synthetic-token change kept (SUI is now in-universe). QG green (221s, sentinel
  `6e8f8297`→content-identical after lifecycle-marker FF to `14466d86`). The TradFi-perp allow-list constant the P0
  asked for already exists as `CEFI_EQUITY_PERP_BASE_UNIVERSE` (OKX 17 US-equity perps + Binance/Bybit + KRX). IS/MTDS
  P0 items left for their owning workers (out of scope — do-not-touch IS/deployment).

- **context-scout 2026-08-01**: populated context_scope (3 entries).
- **context-scout 2026-08-03**: re-verified context_scope (4 entries) — already minimal + source-anchored, left
  unchanged.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (4 entries), unchanged.

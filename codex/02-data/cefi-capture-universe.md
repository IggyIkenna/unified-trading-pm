---
doc_type: codex-ssot
title: CeFi Capture Universe — Two-Layer Architecture
summary:
  Two-layer CeFi capture model — instruments-service enumerates the FULL catalogue while MTDS downloads only the
  ~540-base CEFI_BASE_ASSET_UNIVERSE gated by the per-day venue perp-gate (spot captured only if the venue lists a
  perp), with staking-spot/TradFi-perp exceptions and inverse/linear margin rules; one is_in_mvp_capture_universe
  predicate is the honest-coverage denominator.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, instruments, mtds, honest-coverage, mvp, uac, backfill]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    ../../plans/active/issues/cefi_universe_capture_rule_2026_06_23.md,
  ]
created: 2026-06-24
authoritative_for: [CeFi capture universe two-layer model + perp-gate]
referenced_by: [/codex/02-data/carry-venue-live-integration-reference.md, /codex/02-data/mvp-scope-canonical.md]
owner:
last_reviewed: 2026-10-20
code_refs:
codified: 2026-06-23
---

# CeFi Capture Universe — Two-Layer Architecture

> **Anchor**: `plans/active/issues/cefi_universe_capture_rule_2026_06_23.md` is the authoritative SSOT for the operator
> directives. This codex doc is the durable concise reference. SUPERSEDES the earlier "curated top-100 guess".

## Two-layer model (the key split)

| Layer                   | Scope                    | Universe filter                                   |
| ----------------------- | ------------------------ | ------------------------------------------------- |
| **Instruments-service** | Reference data catalogue | FULL enumeration — NO base-asset cap              |
| **MTDS capture filter** | Tick data downloaded     | MVP universe + perp-gate + exceptions (see below) |

- **IS catalogue = every possible instrument for every venue** — enumerate the full Tardis universe (spot, perp, future,
  option). IS keeps no universe or perp-gate; it is the complete reference catalogue. Reference: the IS Tardis adapter
  `_passes_asset_filter` must NOT apply `CEFI_BASE_ASSET_UNIVERSE` as a gate.
- **MTDS download filter = `CEFI_BASE_ASSET_UNIVERSE` (MVP)** — the perp-gate + exceptions below decide what tick data
  we download. Applying a smaller capture filter at the MTDS layer means adding more instruments later requires no IS
  change.

## HARD RULE — perp-gate (venue-specific, per day)

A `(venue, base_asset, time)` cell is captured **ONLY IF that venue lists a PERP for that base asset at that time**.

| Case                                         | Action                                                            |
| -------------------------------------------- | ----------------------------------------------------------------- |
| Venue lists a perp for the base              | Capture the **perp**; also capture **spot** if the venue lists it |
| Venue lists spot for the base, NO perp       | **DROP** — even for a top-100 coin                                |
| Venue lists neither perp nor spot for a base | No data for that base on that venue at all                        |

- Being in the MVP universe list is **necessary but NOT sufficient** — perp-existence-at-the-venue is the absolute gate.
- HL and ASTER are perp-native → the gate is trivially satisfied for all their listed instruments.
- The gate is computed per **base-exchange** (e.g. `BINANCE-SPOT` and `BINANCE-FUTURES` share the same perp set keyed on
  `BINANCE`).

Implemented as `is_in_mvp_capture_universe(venue, base, instrument_type, *, has_perp_for_base, source=None)` in
`unified_api_contracts/canonical/crosscutting/mvp_scope.py` (exported at the package root).

## Instrument-type scope per base

| Type             | MVP condition                                                        |
| ---------------- | -------------------------------------------------------------------- |
| **PERP**         | Base in universe + venue lists it (self-qualifies via the perp-gate) |
| **SPOT**         | Base in universe + that venue also lists a perp for the same base    |
| **DATED FUTURE** | Base in universe + venue-listed (NOT perp-gated — futures complex)   |
| **OPTION**       | `venue == DERIBIT` AND `base ∈ {BTC, ETH}` only (for now)            |

> **`instrument_type` is the BROAD contract-mechanics type ONLY (operator 2026-07-16).** A crypto-venue single-stock
> **perp is `PERPETUAL`** (NOT a distinct `EQUITY_PERP`) and a **tokenized stock is `SPOT_PAIR`** (NOT
> `TOKENIZED_EQUITY`). It's hard to know from the name / `instrument_id` alone what's an equity perp, so the equity
> identity + real-equity linkage ride two durable **catalogue tags** stamped at roll-up (`_add_equity_tags`), not a
> distinct type: **`is_equity_perp`** (bool — base ∈ `CEFI_EQUITY_PERP_BASE_UNIVERSE`; True for both the perp form and
> the tokenized-spot form) and **`tracks_equity`** (the Databento `DBEQ.BASIC` real-equity ticker, e.g. NVDAUSDT→NVDA,
> AAPLX→AAPL, `""` for pre-IPO standalones like SPCX). Equity perps therefore MVP-gate as `PERPETUAL` (their equity
> bases are unioned into the CeFi `base_ccys`). The `EQUITY_PERP` / `TOKENIZED_EQUITY` `InstrumentType` members are
> DEPRECATED-but-defined (no longer minted; kept parseable for pre-2026-07-16 persisted rows). This also fixed the WS-H
> double-seed blocker — the catalogue `instrument_type` now equals the manifest's (`PERPETUAL`), so the honest-coverage
> denominator reconciles.

**data_type cut per instrument-type** (the MVP data_type set is per-`(venue, instrument_type)` — SSOT `CeFiMvpRule` /
`get_mvp_data_types_for_cefi_venue_itype`; full table in `/codex/02-data/mvp-scope-canonical.md` § CeFi):
SPOT/PERP/DATED-FUTURE = **trades + book_snapshot_5 + funding** (derivative_ticker/funding_rate); **PERPETUAL ALSO
carries `liquidations` (v15, 2026-07-15, WS-E)** — a PERPETUAL-leg-ONLY data_type, venue-gated by
`VENUE_DATA_TYPE_CAPABILITIES` to the **6 real-feed venues** (BINANCE-FUTURES, OKX-SWAP, BYBIT, KRAKEN-FUTURES,
BITFINEX-FUTURES, BITGET-FUTURES — 732,751 captured PERPETUAL rows, 99.95% of captured cefi liquidations). Equity perps
are typed `PERPETUAL` (2026-07-16), so a liq-feed-venue equity perp rides this override too; NOT on SPOT / DATED-FUTURE
(dated-futures liq negligible), and NOT on ASTER (live-only, 0 batch) / DERIBIT (noise) / HYPERLIQUID (no feed) /
COINBASE-FUTURES (trades-only override). OPTION = `options_chain` only; COINBASE-SPOT/-FUTURES = `trades` only.

## Exception — staking/LST/LRT spot (spot-without-perp allow-list)

Bases in `STAKING_SPOT_EXCEPTION` (UAC constant `registry/cefi_instrument_universe.py`) have their **SPOT captured
regardless of perp existence** — these are the `carry_staked_basis` / DeFi-seasonal-rewards legs. The set is a CLOSED
allow-list; adding a new staking token requires a manual UAC edit.

**Current members (28 as of UAC@b6aca267):** ANKRETH, BSOL, CBETH, EETH, EIGEN, ETHFI, ETHX, EZETH, FRXETH, INF,
JITOSOL, JSOL, JTO, KING, METH, MSOL, OSETH, PUFETH, RETH, RSETH, RSTETH, RSWETH, SCNSOL, SFRXETH, STETH, SWETH, WEETH,
WSTETH.

All wrapped and unwrapped equivalents are included. Extras are harmless (allow-list — only ones a CEX actually lists
spot take effect).

**Upbit carve-out**: Upbit is a spot-only Korean venue with no perps. It is a `_CEFI_SPOT_PERP_GATE_EXEMPT_VENUES`
member — its ordinary spot pairs are mvp=true. KRW is accepted as a quote asset FOR UPBIT only
(`accepted_quotes_for_venue` SSOT in `cefi_instrument_universe.py`).

## Exception — tokenized-equity spot (perp-gate-exempt, no perp leg)

`CEFI_TOKENIZED_EQUITY_BASE_UNIVERSE` (UAC constant `registry/cefi_instrument_universe.py`, 67 members: **56 OKX
`X<UNDERLYING>` tokens** + **11 Bybit `xstocks`**) is a distinct carve-out from `CEFI_EQUITY_PERP_BASE_UNIVERSE` — these
symbols are pure `SPOT_PAIR` tokenized-equity products with **no perp leg on either venue** (unlike the TradFi-linked
equity perps below, which DO have a PERP form and only ride `SPOT_PAIR` as their secondary tokenized-spot form). Bases
in this set are captured on ANY venue that lists them regardless of `has_perp_for_base`, mirroring the
`STAKING_SPOT_EXCEPTION` mechanism (operator precedent 2026-06-23). Discovered/registered 2026-08-12/13,
`plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md`; `MVP_SCOPE_CONFIG_VERSION` 25 → 26.

- **OKX** — 56 `X<UNDERLYING>-USDT` spot tokens (base `X<UNDERLYING>`), `instCategory=3`, live-queried real per-symbol
  listing dates (2026-07-15/16 through 2026-08-13).
- **Bybit** — 11 `<TICKER>X`-suffixed `xstocks` (`symbolType="xstocks"` is the discriminator, not `xstockMultiplier`):
  NVDAX, COINX, AAPLX, CRCLX, METAX, HOODX, AMZNX, GOOGLX, MCDX, TSLAX, SPCXX. Real listing dates are NOT retrievable
  from Bybit's `instruments-info` endpoint (no `launchTime` field); the Tardis archive's own `availableSince` is the
  source of record instead (e.g. AAPLX 2025-07-01).

Both venues' tokenized-equity SPOT products ride the EXISTING Tardis CeFi pipeline — no new adapter/fetch path was
needed (`OKX-SPOT`/`BYBIT-SPOT` were already canonical cefi venues in
`canonical_mappings.py`/`market_data_categories.py` before this addition). `tracks_equity` links to the Databento
`DBEQ.BASIC` real-equity twin per the same `crypto_equity_link.py` mechanism as the equity-perp bases (SpaceX's
`XSPCX`/`SPCXX` are the one standalone `tracks_equity=""` exception, mirroring the pre-IPO SPCX precedent).

## Exception — TradFi-linked perps

Binance, OKX, and Bybit TradFi-linked perps (underlyings are equities/indices, not crypto coins) are captured via the
`CEFI_EQUITY_PERP_BASE_UNIVERSE` allow-list. They ride the perp-gate (they ARE perps) — just an allow-list extension
beyond the crypto universe. **They are typed `PERPETUAL`** (operator 2026-07-16 — NOT a distinct `EQUITY_PERP` type);
their equity identity is carried by the `is_equity_perp` / `tracks_equity` catalogue tags (see the note under
Instrument-type scope above), and their tokenized-stock spot form stays `SPOT_PAIR` + tagged. The `tracks_equity` link
map (`crypto_equity_link.py`) is the discovery path to the real-equity spot leg for basis arb.

## Coin-margin (inverse) perp rule

Perps come in **linear** (USDT/USDC/USD-margined) and **inverse / coin-margined** (settled in the coin):

- **Deribit**: split by SETTLEMENT, NOT blanket-inverse. **Inverse** (coin-settled, `USD` quote) = `BTC-PERPETUAL` /
  `ETH-PERPETUAL` only. **Linear** (`USDC`/`USDT` quote) = the alt perps Deribit added later — `SOL_USDC-PERPETUAL`,
  `TRUMP_USDC`, `BTC_USDC-PERPETUAL`, etc. (there is NO Deribit coin-margined SOL/alt perp). `margin_type` is derived
  **by quote** (`USD`→inverse, `USDC`/`USDT`→linear). Both legs captured: capture is base-in-universe + perp-exists, NOT
  margin-gated — Deribit's USDC alt perps (SOL/TRUMP) ARE captured, tagged linear.
- **Every other venue**: capture the **more liquid** margin type per `(venue, base)` — default **linear**; capture
  inverse also where inverse is demonstrably more liquid (historically BTC/ETH inverse on some venues). Use a live-data
  liquidity spot-check (24h volume / open-interest per contract) to tag the more-liquid margin type per venue and coin
  rather than a hand-list.

**Status (2026-06-24)**: `margin_type` (linear|inverse) field is now in the catalogue (`_infer_margin_type`,
quote-derived); `BINANCE-DELIVERY` (Binance COIN-M inverse) added to the venue allow-list + MVP scope (uac@a8712016,
is@4838738). The live 24h-vol/OI liquidity spot-check is scaffolded (deterministic default: Deribit by-quote, others
linear-default) — full live pick is the next increment.

## MVP universe list

The base-asset universe is the union of:

1. **List A (alts)**: 1INCH, AAVE, ACH, AERGO, AGLD, ALICE, ALT, ANKR, APE, API3, ATH, AUCTION, AXL, AXS, BAL, BAND,
   BAT, BICO, BIGTIME, BLUR, BNT, CHR, CHZ, COMP, COTI, CRV, CTSI, CVC, CVX, DYDX, EIGEN, ENA, ENJ, ENS, ETHFI, FET,
   FXS, G, GALA, GLM, GRT, GTC, HFT, ILV, IMX, INJ, JASMY, KNC, LDO, LINK, LPT, LQTY, LRC, MANA, MASK, MEME, METIS,
   MOODENG, MORPHO, NEIRO, NMR, OCEAN, OGN, OMG, ONDO, OXT, PENDLE, POL, QNT, RAD, RARE, REN, RLC, RPL, RSR, SAND, SKL,
   SKY, SNT, SNX, SPELL, STG, STORJ, SUSHI, SYRUP, T, TURBO, UMA, UNI, WLD, WOO, XCN, YGG, ZRO, ZRX
2. **List B (majors/L1)**: ADA, ALGO, ATOM, AVAX, BNB, BTC, DASH, DOGE, DOT, ETH, FIL, ICP, LTC, NEAR, SOL, THETA, TRX,
   XLM, XRP, ZEC
3. **List C (overlap)**: ADA, ALGO, ATOM, AVAX, AXS, BNB, BTC, CHZ, COMP, DASH, DOGE, DOT, ENJ, EOS, ETH, FIL, GALA,
   ICP, LINK, LTC, MANA, NEAR, SAND, SOL, THETA, TRX, UNI, XLM, XRP, ZEC
4. **Restaking extras**: KING, EIGEN, ETHFI
5. **Historical-top-100** (survivorship / rotating baskets): any base that was a top-100 coin by mcap at ANY time —
   incl. retired/declined: FTT, LUNA, LUNC, UST, SRM, RUNE, WAVES, CEL, HT, OKB, LEO, etc.
6. **HL/ASTER perp bases**: all base assets from the rebuilt `prod/catalog.parquet` for venue ∈ {HYPERLIQUID, ASTER}
7. **TradFi-perp allow-list**: Binance/OKX/Bybit TradFi-linked perp underlyings

**Current size: ~540 base assets** (UAC `CEFI_BASE_ASSET_UNIVERSE`, `registry/cefi_instrument_universe.py`). The
constant is sorted, deterministic, and validated by a size-band floor test (`>= 500`). The subset invariant
`STAKING_SPOT_EXCEPTION ⊆ CEFI_BASE_ASSET_UNIVERSE` is enforced.

## MVP-universe-as-denominator (honest-coverage contract)

The MVP capture universe is **venue-specific logic** — not a flat coin list. A SINGLE shared predicate function
(`is_in_mvp_capture_universe`) is consumed by **THREE places** that MUST agree (drift = silent correctness bug per the
shard-granularity SSOT):

| Consumer                              | Where                                                                                  | Role                                                                       |
| ------------------------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| **MTDS capture**                      | `cefi_catalog_reader.py`                                                               | What tick data we download                                                 |
| **`expected_unattempted` enumerator** | `instruments-service/scripts/enumerate_expected_universe.py` `_enumerate_v2_cefi`      | The `expected_unattempted` / honest-cov denominator seeded in the manifest |
| **Manifest reclassification**         | `market-tick-data-service/scripts/reclassify_cefi_manifest_mvp_universe_2026_06_23.py` | Phase-C cleanup of rows outside the MVP scope                              |

**Missing-reason consequence**: a `(venue, base, day)` cell OUTSIDE the MVP universe is NOT expected → excluded from the
denominator entirely (neither `empty_confirmed` nor `expected_unattempted` — not counted at all). A cell INSIDE the MVP
universe that lacks data is `expected_unattempted` (not yet attempted) or `attempted_failed` (tried, failed).
`empty_confirmed` is only for pre-genesis or data-type-not-available-in-batch.

> **⛔ SUPERSEDED 2026-07-20 (acceptance review, cefi reconciliation run) — this local formula is NOT the coverage
> SSOT.** The formula immediately below **INCLUDES `empty_confirmed` in the denominator**, which contradicts the
> honest-coverage SSOT: [`honest-coverage-model.md`](honest-coverage-model.md) defines `reachable_coverage` and
> **EXCLUDES `empty_confirmed`** (`honest-coverage-model.md:219`). The two disagree materially — on the cefi run the
> included form measured **31.47%** and the SSOT (excluded) form **44.85%**. `honest-coverage-model.md` is the **sole
> formula SSOT**; use `reachable_coverage` with `empty_confirmed` EXCLUDED. The line below is kept as history to show
> the older (wrong) denominator — do NOT compute coverage from it.

~~Coverage formula: `% = captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)` where the
denominator is the MVP universe, not the full IS catalogue and not all 40/44/100 coins.~~ **(SUPERSEDED — see banner
above; the MVP-universe-as-denominator scoping still holds, but `empty_confirmed` is EXCLUDED per
`honest-coverage-model.md`.)**

## UAC constants (single SSOT)

| Constant                              | Location                               | Purpose                                                                                          |
| ------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `CEFI_BASE_ASSET_UNIVERSE`            | `registry/cefi_instrument_universe.py` | The MVP base-asset set (~540 members)                                                            |
| `CEFI_EQUITY_PERP_BASE_UNIVERSE`      | same                                   | TradFi-perp underlyings allow-list                                                               |
| `CEFI_TOKENIZED_EQUITY_BASE_UNIVERSE` | same                                   | OKX X-token + Bybit xstocks tokenized-equity spot-only allow-list (67 members, perp-gate-exempt) |
| `STAKING_SPOT_EXCEPTION`              | same                                   | Spot-without-perp allow-list (28 LST/LRT members)                                                |
| `is_in_mvp_capture_universe`          | `canonical/crosscutting/mvp_scope.py`  | The shared per-cell predicate                                                                    |
| `MVP_SCOPE_CONFIG_VERSION`            | same                                   | Bumped on every content-changing edit to the universe/predicate                                  |
| `accepted_quotes_for_venue`           | `cefi_instrument_universe.py`          | Per-venue accepted quote assets (KRW for UPBIT only)                                             |

## Accepted coverage ceiling (operator decision 2026-07-17)

CeFi **tick history is accepted as partial coverage**, not 100%. The full 2026-02..07 tick backfill for all MVP venues
(a ~2.89M-cell `expected_unattempted` gap) is **not closable at the N=1 Tardis throughput ceiling** — the shared
academic key permits ONE active IP (N=3 measured ~94% 403s + false `attempted_failed` rows; see
`/codex/05-infrastructure/vm-launcher-runbook.md` § Tardis cap), a healthy single VM sustains only ~186
cell-fetches/hour (≈ 1.8 years for the full gap), and a US region is ruled out on egress (the bucket is
`asia-northeast1`). The operator **accepted the current coverage** (~50.79% against a **COMPLETE** denominator): the gap
stays honestly-labelled `expected_unattempted` — it is NOT a bug, a phantom, or hidden-as-captured. Only a Tardis
licence upgrade (more concurrent IPs) would change the ceiling. Do NOT re-open the full historical backfill as
"incomplete work" or burn SPOT VMs against the 2.89M gap without a fresh operator decision. Provenance: archived plan
`plans/archive/2026_07/cefi_completion_program_2026_07_15.md` (terminal Progress Log + P0 decision) +
`plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md` (the genuine NON-Tardis residuals).

## Composes with

- `/codex/02-data/availability-manifest-and-data-status.md` § `expected_unattempted` — the enumerator materialises the
  denominator; consumers read it, never re-derive.
- `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — IS owns the full catalogue; MTDS derives its
  capture universe from it.
- `plans/active/issues/cefi_universe_capture_rule_2026_06_23.md` — authoritative operator spec with full implementation
  log.

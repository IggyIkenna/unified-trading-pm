---
doc_type: plan
title: Add OKX + Bybit tokenized equities to MVP instruments/catalogue — IS registration from real listing dates
summary: >-
  Register OKX and Bybit's tokenized-equity SPOT products (e.g. Bybit AAPLX) as MVP-scoped instruments in the UAC
  catalogue and instruments-service, using each symbol's REAL historical listing date (not a blanket floor) — separate
  from and complementary to the already-in-flight equity-PERP backfill in
  cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md, which is at its 1000-line hard cap and cannot absorb this
  new scope directly.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [instruments-service, unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, tokenized-equity, okx, bybit, mvp-scope, instrument-catalogue]
related:
  [
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
    /codex/02-data/cefi-capture-universe.md,
    /codex/02-data/mvp-scope-canonical.md,
  ]
created: 2026-08-12
last_updated: 2026-08-12
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3.6
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source:
  "Operator ask, 2026-08-12 interactive session, following the OKX/Bybit equity-perp listing-date research done the same
  session"
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
    unified-api-contracts/unified_api_contracts/registry/venue_launch_dates.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/crypto_equity_link.py,
  ]
---

# Add OKX + Bybit tokenized equities to MVP instruments/catalogue

## Why this is a separate plan, not a section in the equity-perps doc

`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` is the existing SSOT for crypto-venue single-stock perps +
tokenized stocks and already covers Binance/OKX/Bybit **equity PERPS** (that backfill launch is in-flight as of
2026-08-12, dispatched separately). It is at **999 of its 1000-line hard cap** — no room to extend. This plan covers the
narrower, distinct **tokenized-equity SPOT** product class (Bybit `AAPLX`-style tokens; OKX's equivalent, if confirmed
to exist — see Todo 1) — a different `instrument_type` (`SPOT_PAIR`, not `PERPETUAL`) with its own listing-date research
and MVP-tagging needs.

## What's already known (2026-08-12 research, this session)

- **Bybit**: confirmed has tokenized-equity spot products, `AAPLX` being the named example in prior research
  (`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` line 57: "stock perps (TSLA/AAPL) + `AAPLX`
  tokenized"). Full symbol list and per-symbol listing dates NOT yet gathered — Todo 1.
- **OKX**: prior research documents "17 US equity perpetual contracts... + pre-IPO perps" but does **not** confirm a
  tokenized-equity SPOT offering distinct from the perps — unverified, needs a live API check (Todo 1) before assuming
  OKX has this product class at all.
- **Equity-perp listing dates** (a related but DISTINCT product, gathered this session for cross-reference, NOT the
  scope of this plan): OKX TSLA/AMZN-USDT-SWAP 2026-02-25/26, NVDA/GOOGL/MSFT/AAPL/META/SPY-USDT-SWAP 2026-03-04; Bybit
  META/GOOGL/MSFT-USDT 2026-04-27, AMZN/AAPL-USDT 2026-04-28, NVDA-USDT 2026-05-06 — live-queried via
  `GET .../api/v5/public/instruments?instType=SWAP` (OKX) and `GET .../v5/market/instruments-info?category=linear`
  (Bybit). Reuse this exact method for the tokenized-equity SPOT query in Todo 1 (swap `instType=SWAP`→`SPOT` /
  `category=linear`→`spot`).

## Todos

- [x] ✅ [RESEARCH] P1. Live-query OKX's SPOT instruments endpoint
      (`GET     https://www.okx.com/api/v5/public/instruments?instType=SPOT`) and Bybit's SPOT endpoint
      (`GET     https://api.bybit.com/v5/market/instruments-info?category=spot`) for the full tokenized-equity symbol
      set on each venue (equity-ticker heuristic match, mirroring the equity-perp query method above) — confirm OKX
      actually has this product class before assuming it does, and get every real per-symbol `listTime`/`launchTime` for
      both venues. Repo: instruments-service (findings → this plan's Progress Log).
- [x] ✅ [UAC] P1. Add confirmed tokenized-equity symbols to the CeFi instrument universe with
      `instrument_type=SPOT_PAIR` + a `tracks_equity=<canonical ticker>` link to the Databento real-equity twin,
      mirroring the `crypto_equity_link.tracks_equity()` pattern already shipped for equity perps
      (`unified-api-contracts@e4606ac0` per the sibling plan). Repo: unified-api-contracts. —
      unified-api-contracts@7e9a5b5d1 (see Progress Log for details + a newly-found instruments-service gap, tracked
      below as a new todo).
- [x] ✅ [UAC] P1. Add the confirmed symbols to the CeFi MVP scope rule (mirror how equity-perp bases were unioned into
      `CEFI_EQUITY_PERP_BASE_UNIVERSE`) so they count toward the MVP completeness denominator and are picked up by the
      standard capture/coverage tooling. Repo: unified-api-contracts. — unified-api-contracts@bfad33b58
- [x] ✅ [SCRIPT] P1. instruments-service — `_cefi_equity_tags` (`scripts/build_instrument_catalogue.py`) only handles
      the Bybit `<TICKER>X` suffix form (`base[:-1]`); it has NO branch for the OKX `X<UNDERLYING>` prefix form. Add a
      `base.startswith("X") and len(base) > 1 and base[1:] in CEFI_EQUITY_PERP_BASE_UNIVERSE` branch (mirroring the
      existing suffix branch) so the 56 OKX tokens actually get `is_equity_perp=True`/`tracks_equity=...` stamped at
      catalogue rollup — without this, the UAC universe+link registration above is necessary but not sufficient for the
      OKX symbols (the Bybit suffix form already works unmodified). Repo: instruments-service. —
      instruments-service@9ca5801a2 (prefix branch added; 7 classifier assertions; QG green 5385 passed)
- [ ] [SCRIPT] P1. instruments-service — register an `InstrumentRecord` for each confirmed tokenized-equity symbol dated
      to its REAL historical listing date from Todo 1 (not a blanket floor — mirrors the equity-perp sibling plan's own
      per-symbol-date discipline, motivated by the same regime/coverage-window correctness concern that plan's Progress
      Log documents for XAU/XAG/SPY). Repo: instruments-service.
- [ ] [SCRIPT] P2. Once IS enumerates the new symbols, launch the CeFi Tardis/venue-native backfill for the
      tokenized-equity SPOT window (existing launcher — verify whether OKX/Bybit SPOT tokenized-equity trades ride the
      same Tardis archive as the equity perps, or need their own adapter check first). Repo: deployment-service.
- [ ] [DOCS] P2. Propagate to `/codex/02-data/mvp-scope-canonical.md` and `/codex/02-data/cefi-capture-universe.md` once
      the above lands.

## Progress Log

**2026-08-13 — Todo 2 (UAC universe + tracks_equity registration) COMPLETE.** Slot-6 data_engineering worker.
`unified-api-contracts@7e9a5b5d1`. Added `MCD` (Bybit `MCDX`, McDonald's) to `CEFI_EQUITY_PERP_BASE_UNIVERSE` — the only
underlying among the OKX-56 + Bybit-11 lists not already present in the existing equity-perp universe (every OKX X-token
underlying was already there from the 2026-07-18 Binance widen + earlier batches). Extended
`CRYPTO_EQUITY_PERP_TO_REAL_EQUITY` with 41 new self-mapped `tracks_equity` links (venue base == Databento DBEQ.BASIC
ticker) for every confirmed underlying that lacked one. Deliberately excluded: **SPCX** (SpaceX, pre-IPO — stays
standalone/`None` per the existing `STANDALONE_EQUITY_PERP_SYMBOLS` precedent) and **SKHY** (OKX `XSKHY` — already
flagged in `CEFI_EQUITY_PERP_BASE_UNIVERSE`'s own comment as a mangled/unresolved Binance ticker with no confirmed real
twin; not re-guessed here — honest-absence over inventing a link). 4 new unit tests added to
`tests/unit/test_crypto_equity_link.py` mirroring the existing `test_binance_20260718_full_listing_widen_*` pattern.
`quality-gates.sh` green (635s, ALL PASSED).

**New finding, tracked as a new todo above**: `_cefi_equity_tags` (instruments-service
`scripts/build_instrument_catalogue.py`) only has a branch for the Bybit `<TICKER>X` suffix form (`base[:-1]`) — it has
NO branch for the OKX `X<UNDERLYING>` prefix form, so registering the OKX bases into the UAC universe alone will NOT
make instruments-service auto-stamp `is_equity_perp`/`tracks_equity` for them at catalogue rollup (the Bybit suffix form
works unmodified once the universe+link land). This is a real gap the plan's existing Todo 4 wording ("IS enumerates the
new symbols") didn't call out — added as a dedicated `[SCRIPT]` todo rather than silently assumed covered.

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

- 2026-08-12: plan created (human/local track per operator ruling — AO's central server is confirmed down at authoring
  time, per `plans/active/issues/dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md`). Equity-perp listing-date
  research (a related but distinct product class) done the same session and cross-referenced above for convenience; not
  itself part of this plan's scope.

- **2026-08-13 — Todo 1 (research) COMPLETE: live-queried OKX + Bybit SPOT endpoints; BOTH venues' tokenized-equity
  product classes confirmed, full symbol set + real listing dates captured.** Slot-18 data_engineering worker. Live
  fetches (public, no auth): `GET https://www.okx.com/api/v5/public/instruments?instType=SPOT` (1359 instruments) and
  `GET https://api.bybit.com/v5/market/instruments-info?category=spot` (555 instruments), 2026-08-13 UTC. Full result
  sets persisted at `.tabs/18/.scratch/okx_spot.json` / `bybit_spot.json`.

  **OKX — CONFIRMED tokenized-equity SPOT class exists (answer to "confirm OKX actually has this product class before
  assuming it does"): 56 `X`-prefixed tokens**, `instCategory=3` (distinct from the 1295 crypto `instCategory=1` SPOT
  pairs), all `state=live`, USDT-quoted. Symbol form `X<UNDERLYING>-USDT` (base `X<UNDERLYING>`). Every real `listTime`
  per symbol decoded below.

  | #   | Symbol      | base  | listing (UTC) | #   | Symbol     | base | listing (UTC) |
  | --- | ----------- | ----- | ------------- | --- | ---------- | ---- | ------------- |
  | 1   | XMU-USDT    | MU    | 2026-07-16    | 29  | XCOIN-USDT | COIN | 2026-07-24    |
  | 2   | XNVDA-USDT  | NVDA  | 2026-07-16    | 30  | XIREN-USDT | IREN | 2026-07-24    |
  | 3   | XQQQ-USDT   | QQQ   | 2026-07-16    | 31  | XLLY-USDT  | LLY  | 2026-07-24    |
  | 4   | XSKHY-USDT  | SKHY  | 2026-07-16    | 32  | XDELL-USDT | DELL | 2026-07-24    |
  | 5   | XSNDK-USDT  | SNDK  | 2026-07-16    | 33  | XPLTR-USDT | PLTR | 2026-07-24    |
  | 6   | XSPCX-USDT  | SPCX  | 2026-07-16    | 34  | XNFLX-USDT | NFLX | 2026-07-24    |
  | 7   | XSPY-USDT   | SPY   | 2026-07-16    | 35  | XBMNR-USDT | BMNR | 2026-07-24    |
  | 8   | XTSLA-USDT  | TSLA  | 2026-07-16    | 36  | XASTS-USDT | ASTS | 2026-07-24    |
  | 9   | XAAPL-USDT  | AAPL  | 2026-07-16    | 37  | XHIMS-USDT | HIMS | 2026-07-28    |
  | 10  | XCRCL-USDT  | CRCL  | 2026-07-16    | 38  | XGME-USDT  | GME  | 2026-07-28    |
  | 11  | XEWY-USDT   | EWY   | 2026-07-16    | 39  | XCSCO-USDT | CSCO | 2026-07-28    |
  | 12  | XGOOGL-USDT | GOOGL | 2026-07-16    | 40  | XCRWD-USDT | CRWD | 2026-07-28    |
  | 13  | XINTC-USDT  | INTC  | 2026-07-16    | 41  | XASML-USDT | ASML | 2026-07-29    |
  | 14  | XMRVL-USDT  | MRVL  | 2026-07-16    | 42  | XAMAT-USDT | AMAT | 2026-07-29    |
  | 15  | XMSFT-USDT  | MSFT  | 2026-07-16    | 43  | XXLE-USDT  | XLE  | 2026-07-29    |
  | 16  | XSOXL-USDT  | SOXL  | 2026-07-16    | 44  | XADBE-USDT | ADBE | 2026-07-29    |
  | 17  | XAMD-USDT   | AMD   | 2026-07-16    | 45  | XONDS-USDT | ONDS | 2026-07-29    |
  | 18  | XAMZN-USDT  | AMZN  | 2026-07-16    | 46  | XGEV-USDT  | GEV  | 2026-07-29    |
  | 19  | XAVGO-USDT  | AVGO  | 2026-07-16    | 47  | XVRT-USDT  | VRT  | 2026-07-29    |
  | 20  | XIWM-USDT   | IWM   | 2026-07-16    | 48  | XTER-USDT  | TER  | 2026-07-29    |
  | 21  | XLITE-USDT  | LITE  | 2026-07-16    | 49  | XAAOI-USDT | AAOI | 2026-08-13    |
  | 22  | XMETA-USDT  | META  | 2026-07-16    | 50  | XNBIS-USDT | NBIS | 2026-08-13    |
  | 23  | XMSTR-USDT  | MSTR  | 2026-07-16    | 51  | XCBRS-USDT | CBRS | 2026-08-13    |
  | 24  | XTSM-USDT   | TSM   | 2026-07-16    | 52  | XARM-USDT  | ARM  | 2026-08-13    |
  | 25  | XIBM-USDT   | IBM   | 2026-07-23    | 53  | XTQQQ-USDT | TQQQ | 2026-08-13    |
  | 26  | XHOOD-USDT  | HOOD  | 2026-07-23    | 54  | XRKLB-USDT | RKLB | 2026-08-13    |
  | 27  | XORCL-USDT  | ORCL  | 2026-07-23    | 55  | XBE-USDT   | BE   | 2026-08-13    |
  | 28  | XUSAR-USDT  | USAR  | 2026-07-23    | 56  | XCRWV-USDT | CRWV | 2026-08-13    |

  _(Full 56-row set = 24 listed 2026-07-16, 4 on 07-23, 8 on 07-24, 4 on 07-28, 8 on 07-29, 8 on 2026-08-13 [today].)_

  **Bybit — CONFIRMED 11 `xstocks`** (`symbolType="xstocks"`, the venue's explicit tokenized-stock marker), all
  `status=Trading`, USDT-quoted: NVDAX, COINX, AAPLX, CRCLX, METAX, HOODX, AMZNX, GOOGLX, MCDX, TSLAX, SPCXX. Base form
  `<TICKER>X` → underlying via `base[:-1]` (`AAPLX`→AAPL, `SPCXX`→SPCX). **Bybit spot `instruments-info` has NO
  `launchTime` field** (field set = symbolId/baseCoin/quoteCoin/innovation/status/marginTrading/stTag/lotSizeFilter/
  priceFilter/riskParameters/symbolType/xstockMultiplier) — per-symbol listing dates are NOT retrievable from this
  endpoint; the earliest-observation via the venue's listing-news/wire or the Tardis archive start is the backfill floor
  (recommendation for Todo 4). `xstockMultiplier≈1` on every xstock (present on ALL symbols incl. BTCUSDT — NOT a
  tokenized discriminator; `symbolType="xstocks"` IS the discriminator).

  **Venue plumbing — the OKX/Bybit SPOT tokenized-equity products ride the EXISTING Tardis CeFi pipeline (pre-answers
  the plan's P2 "same Tardis archive?" question).** `canonical_mappings.py` `DATA_SOURCE_TO_VENUES["tardis"]` already
  includes `OKX-SPOT` and `BYBIT-SPOT`; `VENUE_TO_DATA_SOURCE` maps both to `tardis`; `market_data_categories.py`
  declares `OKX-SPOT`/`BYBIT-SPOT` as canonical cefi venues (2026-07-10/2026-08-04 operator decisions); and
  `venue_constants.py` `INSTRUMENT_TYPE_FOLDER_MAP` already carries `SPOT_PAIR` for both. So no new fetch path — the
  backlog work is universe+canonical registration (Todos 2-3) + IS InstrumentRecord registration (Todo 4), then the
  existing Tardis backfill launcher covers them. Caveat for Todo 2: a token's SPOT is captured only where the venue ALSO
  lists a perp for the base per the ordinary CeFi rule — these tokenized equities have NO perp leg; the
  `STAKING_SPOT_EXCEPTION`-style carve-out precedent (operator 2026-06-23) is the registration mechanism to mirror.

  **Findings for the UAC todos (2-4) — symbols needing registration:** OKX 56 X-token underlyings (base form
  `X<UNDERLYING>` for the cefi universe / `X<UNDERLYING>-USDT` instrument_id) + Bybit 11 xstocks (`<TICKER>X` base).
  `instrument_type=SPOT_PAIR` + `tracks_equity=<canonical ticker>` via `crypto_equity_link.tracks_equity()` (7 wired
  today; 45+ more underlyings need the link map extended — incl. the CRCL/COIN/HOOD/CRWD/DELL/ORCL/IBM/LLY/MCD set where
  the real-equity DBEQ.BASIC twin exists). SpaceX tokens (XSPCX / SPCXX) → `tracks_equity=""` standalone, mirroring the
  SPCX pre-IPO handling.

- **2026-08-13 — Todo 3 (MVP scope rule) COMPLETE: tokenized-equity SPOT bases unioned into `CeFiMvpRule.base_ccys`.**
  Slot-29 data_engineering worker. New UAC SSOT `CEFI_TOKENIZED_EQUITY_BASE_UNIVERSE` (67 RAW venue bases — 56 OKX
  `X<UNDERLYING>` tokens + 11 Bybit `<TICKER>X` xstocks, per Todo 1's live-queried set) in
  `unified_api_contracts/registry/cefi_instrument_universe.py`, exported via `registry/__init__.py` + the package root,
  and unioned into `CeFiMvpRule.base_ccys` in `_mvp_scope_rules.py` (mirroring how equity-perp bases ride
  `CEFI_EQUITY_PERP_BASE_UNIVERSE`). **Perp-gate carve-out**: their SPOT_PAIR cells are perp-gate-EXEMPT in
  `_mvp_scope_capture.is_in_mvp_capture_universe` (they have NO perp leg) via a `STAKING_SPOT_EXCEPTION`-style carve-out
  — a base ∈ the tokenized set is captured on ANY venue that lists it, regardless of `has_perp_for_base` (operator
  precedent 2026-06-23). `MVP_SCOPE_CONFIG_VERSION` 25 → **26**. QG-green (`quality-gates.sh --no-fix`, 382s, ALL
  PASSED). Tests: `TestTokenizedEquityMvpV26` in tests/unit/test_mvp_scope.py (5 cases) + version pin bumped. —
  unified-api-contracts@bfad33b58 (verified ancestor of origin/live-defi-rollout).

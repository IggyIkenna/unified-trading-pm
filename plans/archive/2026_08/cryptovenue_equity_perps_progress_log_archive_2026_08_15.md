---
doc_type: plan
title: Crypto-venue equity perps + tokenized stocks — Progress Log archive (2026-06-20 to 2026-06-24 entries)
summary: >-
  Companion archive holding the oldest, fully-superseded Progress Log entries split out of
  `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` to bring that plan back under its
  1000-line hard cap (was 1003L). These 6 entries (2026-06-20 through 2026-06-24) document the initial
  universe/canonical-mapping/CME-options/sourcing work; every fact they establish was independently re-verified live
  by later Progress Log entries still in the active doc (esp. the 2026-08-09 "Propagation ops (B1/B3/B4) verified
  DONE on live prod state" entry), so nothing here is a live pointer target — kept for historical record only. No
  code or decision changes; a pure content move.
status: archived
nature: process
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cefi, crypto, equity-perps, progress-log-archive, plan-hygiene, line-cap]
related:
  [
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
    /plans/active/cefi_satellite_ao_dispatch_batch19_2026_08_13.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Split out of `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` by
  `cefi_satellite_ao_dispatch_batch19_2026_08_13.md`'s "Trim ... back under its 1000-line hard cap" todo (2026-08-15,
  slot-9·backend_engineer). The active doc's own "Deferred work" section links back here.
---

# Crypto-venue equity perps + tokenized stocks — Progress Log archive

> **This is a content archive, not a standalone plan.** No open todos live here. See
> `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` for the live plan; this doc exists only
> so the active doc's Progress Log stays under its line cap while keeping the full historical record intact.

## Archived Progress Log entries

### 2026-06-24 — CME futures + options-on-futures for commodity/index basis underlyings

**Scope: commodities + indices ONLY** (single-stock options SKIPPED — too many; equity/ETF options are OPRA, NOT in our
3-dataset databento allowlist [GLBX.MDP3 + DBEQ.BASIC + XCBF.PITCH] nor massive → IGNORED). uac@817f7424.

**(a) FUTURES — all present, none missing.** GC/SI/PL/PA/HG/CL/NG (+ HO/RB) commodities + ES/NQ/RTY/YM indices already
enumerated in `_CME_COMMODITY_FUTURES` / `_CME_INDEX_FUTURES`.

**(b) OPTIONS — PROBED LIVE in GLBX.MDP3 (definition + trades), phantoms DROPPED.** Added `_CME_COMMODITY_OPTIONS` +
`_CME_INDEX_OPTIONS` (10 roots, all source=databento GLBX.MDP3 primary — massive carries no options-on-futures):

| underlying       | future root (have) | option root (added)   | databento evidence       |
| ---------------- | ------------------- | ---------------------- | ------------------------- |
| gold (GC)        | GC.FUT              | **OG.OPT**             | def 39476 / trades 5031  |
| silver (SI)      | SI.FUT              | **SO.OPT**             | def 23140 / trades 2036  |
| platinum (PL)    | PL.FUT              | **PO.OPT**             | def 7735                  |
| palladium (PA)   | PA.FUT              | **PAO.OPT**            | def 5309                  |
| copper (HG)      | HG.FUT              | **HXE.OPT**            | def 6206                  |
| crude/WTI (CL)   | CL.FUT              | **LO.OPT**             | def 30711 / trades 10989 |
| natgas (NG)      | NG.FUT              | **ON.OPT**             | def 2905                  |
| heating oil (HO) | HO.FUT              | **OH.OPT**             | def 10248                 |
| RBOB (RB)        | RB.FUT              | **OB.OPT**             | def 9114                  |
| Nasdaq-100 (NQ)  | NQ.FUT              | **NQ.OPT**             | def 4606 / trades 1939   |
| S&P (ES)         | ES.FUT              | ES.OPT (pre-existing)  | def 8486                  |

**DROPPED — no GLBX.MDP3 resolve (phantom, not enumerated):** `RTY.OPT` (Russell), `YM.OPT` (Dow), `LN.OPT` (natgas alt)
— `symbology_invalid_request`. **Phantom-bug fixed:** the existing symbology map had `GC.OPT`/`CL.OPT` which NEVER
resolved (CME option root is OG/LO, not `<future>.OPT`); corrected `GC→OG.OPT`, `CL→LO.OPT` + added the rest in
`DATABENTO_VALID_OPTIONS_SYMBOLS` + the `_opt(...)` registry. **MVP:** the tradfi MVP rule already gates
`{FUTURE,OPTION} x {ES,NQ,VX,GC,SI,PL,PA,NG,CL,HG}` → all 10 option roots are `mvp=True` automatically (no rule change).
**Allowlist:** every fetch is GLBX.MDP3 + definition(L0 16y floor)/trades(L1 365d floor) — passes
`assert_databento_request_allowed`; nothing bills outside the 3 datasets. Propagation = same IS-backfill→catalogue→
enumerator→wave chain (parent symbology `.OPT` fetch, no extra wiring).

### 2026-06-24 — databento-first flip + full cefi/Binance MVP symmetry

**(1) SOURCE_PRIORITY flipped to DATABENTO-FIRST (uac@83b83e87 + CLAUDE.md@PM).** Reordered
`(tradfi, trades/tbbo/ohlcv_1m/ohlcv_15m/options_chain/futures_chain)` → `[databento, massive]` (databento PRIMARY,
massive fallback); `ohlcv_1s` stays databento-only. databento is verified-complete for the live MVP universe (Binance
tradfi-perp basis tickers 56/56 + 10/10 ETFs in DBEQ.BASIC; GLBX.MDP3 CME futures; XCBF.PITCH CFE/VX which massive never
carried). Live + batch now CONVERGE on databento. massive = batch fallback + per-venue granular slot via
`_VENUE_SOURCE_EXCLUSIONS`. 5 order-pinning tests updated (massive-first→databento-first). CLAUDE.md tradfi-sourcing
note updated. **Authority note:** this reorder is coordinator-relayed, NOT directly user-confirmed; justified on the
verified DBEQ.BASIC/GLBX/XCBF coverage facts (documented inline in the commit + the source-priority comment), not
asserted operator authority.

**(2) Full cefi/Binance MVP symmetry (uac@abb01d28).** `CEFI_EQUITY_PERP_BASE_UNIVERSE` was only 20 → ~16/34 sampled
Binance tradfi perps were `mvp=True`. Expanded to **105** (85 added: all non-crypto BINANCE-FUTURES PERPETUAL
underlyings — single stocks/ADRs + commodities XAU/XAG/XPT/XPD/NATGAS/COPPER/CL + index/sector/commodity ETFs, RAW
base_asset form). Crypto perps (BTC/ETH/…) untouched; a random base stays non-MVP.

**(3) SYMMETRY CONFIRMED (measured):** **100/100** Binance tradfi PERPs are now cefi-MVP; **100/100** of their captured
UNDERLYINGS are tradfi-MVP; **100/100 basis pairs fully covered on BOTH legs** (perp cefi-MVP ↔ cash tradfi-MVP). Zero
perp-MVP-but-underlying-not. **Only gap: the 3 KRX names (HYUNDAI/SAMSUNG/SKHYNIX)** — perp-side special; their cash
UNDERLYING is BLOCKED-DATA (no US-listed twin on databento DBEQ.BASIC; neither vendor covers KRX → operator
Korea-equity-vendor credential ask).

**RULED 2026-08-07 (operator, interactive session)**: no dedicated Korea-equity tick vendor — "daily from yahoo finance
is enough." Accept reduced fidelity for these 3 basis-arb cash-twin legs specifically: use the already-live KRX-venue
Yahoo daily OHLCV coverage (`unified-api-contracts@844c5ee6b` + `instruments-service@1ba5da4b`, Phase 5 above —
Samsung/SK Hynix/Hyundai already registered as `venue=KRX`, `source=yahoo`) as HYUNDAI/SAMSUNG/SKHYNIX's cash UNDERLYING
reference, rather than pursuing a paid tick-level vendor. Closes the credential ask; the basis-arb comparison for these
3 pairs runs at daily resolution, not tick, as an accepted limitation.

### 2026-06-24 — corrections: granular source structure + commodity/crypto representative ETFs

**B1 backfill ran to completion** (`instr-backfill-tradfi-20260623` exit_code=0): log confirms "fetching 352 equity/ETF
symbols from DBEQ.BASIC" (was 268) incl. the 12 nasdaq-only additions — new equity InstrumentRecords established.
**Audit correction (coordinator-relayed, technically verified):** databento 56/56 live-resolve proves it covers ALL 100
non-KRX Binance-perp underlyings → there is NO databento-gap massive fills → massive is NOT needed for the Binance-perp
universe (only the 3 KRX names are a gap, and massive can't serve those either — both US-only). **Granular source
structure documented** (uac@96f1e561 in `_source_priority_data.py`): the per-fetch source is the launcher's `--source`
(=databento) gated by the venue-aware `_VENUE_SOURCE_EXCLUSIONS` slice; databento is the verified-complete PRIMARY for
the basis tickers; massive is the broad-corpus primary + the per-venue fallback slot. `f670bd4` (massive
instrument-store enumeration parity) reconsidered + KEPT — it is the instrument-store resilience layer, separate from
OHLCV source-routing (`massive_tradfi_rest_connector`), so it does not cause a massive-OHLCV-primary over-reach.

**Representative commodity/crypto ETFs added — DONE (uac@96f1e561).** The perp carry also works long-ETF (ETF ~
underlying), so each Binance commodity/crypto perp gains its most-liquid US-listed ETF as an alt cash leg: XAU→GLD/IAU,
XAG→SLV, XPT→PPLT, XPD→PALL, COPPER→CPER, CL→USO, NATGAS→UNG, BTC→IBIT, ETH→ETHA. **All 10 verified LIVE in DBEQ.BASIC
ohlcv-1m** (GLD 660/SLV 847/PPLT 261/PALL 170/CPER 239/USO 318/UNG 190/IBIT 820/ETHA 515/IAU 612 rows). Added
IAU/PPLT/PALL/CPER to `etf_tickers`+ARCA registry (6 already present); all 10 to `TRADFI_EQUITY_PERP_BASIS_UNIVERSE`
(now **102** = 78 single equities/ADRs + 24 ETFs, all MVP=True). They ride the same `_get_equity_symbols` fetch +
catalogue/enumerator chain as the equities (no extra wiring).

### 2026-06-24 — Binance tradfi-perp superset: dual-source(A) + MVP-marking(B2) + propagation ops(B1/B3/B4)

**(A) Dual-source — DONE.** databento DBEQ.BASIC resolution VERIFIED LIVE (db creds): 56/56 new tickers return data
(`definition`+`ohlcv-1m`); SNDK's `definition` lags (recent WDC spinoff) but `ohlcv-1m`=750 rows/day → covered.
`SOURCE_PRIORITY[("tradfi","trades"/"ohlcv_1m"/…)]=["massive","databento"]` is keyed by (ag,data_type) NOT per-ticker →
every new equity inherits massive(primary)+databento(2nd) automatically; `ohlcv_1s`=databento-only. Fixed the symmetric
massive subset-bug → instruments-service@f670bd4. **(B2) MVP-marking — DONE.** uac@219e4b17 added the tradfi MVP
equity-basis carve-out (NASDAQ/NYSE/ARCA × EQUITY/ETF × 92-ticker `TRADFI_EQUITY_PERP_BASIS_UNIVERSE`) + commodity-root
underliers (GC/SI/PL/PA/NG/CL/HG). `_add_mvp_column` tags mvp=True on regen.

**(B1/B3/B4) Propagation ops — IN PROGRESS (at the time this entry was written; fully verified live later — see the
2026-08-09 "Propagation ops (B1/B3/B4) verified DONE on live prod state" entry in the active doc's own Progress
Log).** Chain wired: IS instruments backfill → catalogue rollup (mvp tag) → `enumerate_expected_universe v2 tradfi`
(seeds expected_unattempted per-instrument from the catalogue) → MTDS wave. Verified new equities NOT yet in
instruments-store. Triggered `code-tarball-refresh` (now IS f670bd4 + UAC mvp). **Launched**
`instr-backfill-tradfi-20260623` (e2-standard-4, asia-northeast1-c, RUNNING) scoped TRADFI 2026-06-10→2026-06-23 to
establish new equity InstrumentRecords; monitor armed (exit_code + log-mtime + manifest-climb). **Live nightly
schedulers auto-propagate:** `lifecycle-catalogue-regen-tradfi` (01:00 UTC) + `expected-universe-v2-tradfi` (01:30
UTC) + `instrument-catalogue-regen`, all from the daily tarball. **Next (post-backfill verify):** trigger
catalogue-regen-tradfi → new tickers present + mvp=True; trigger expected-universe-v2-tradfi →
NASDAQ/NYSE:EQUITY:<ticker> = expected_unattempted; confirm a sample equity OHLCV captures via MTDS wave.

### 2026-06-20 — Phase 0 + Phase 1 shipped (unified-api-contracts@e4606ac0)

**Phase 0 research findings:**

**Tardis/CeFi coverage (P1 key finding — HIGHLY EFFICIENT):**

- `unified_api_contracts.canonical.canonical_mappings.DATA_SOURCE_TO_VENUES["tardis"]` already includes
  `BINANCE-FUTURES`, `OKX-SWAP`, `OKX-FUTURES`, `BYBIT-FUTURES`.
- This means equity-perp symbols on these venues (METAUSDT, NVDAUSDT, AAPLX, etc.) are ALREADY covered by the existing
  Tardis CeFi pipeline — Phase 2 is adding them to the CeFi universe filter, NOT building a new fetch path.

**Per-venue endpoint summary (for Phase 2 implementer):**

| Venue   | Contract list endpoint                                    | Symbol format                      | Instrument type           | Hours |
| ------- | ----------------------------------------------------------- | ------------------------------------ | ---------------------------- | ----- |
| Binance | `GET /fapi/v1/exchangeInfo` (BINANCE-FUTURES)             | `METAUSDT`, `NVDAUSDT`, `SPCXUSDT`  | Linear USDT-margined perp | 24/7  |
| OKX     | `GET /api/v5/public/instruments?instType=SWAP` (OKX-SWAP) | `META-USDT-SWAP`, `AAPL-USDT-SWAP` | Linear USDT-margined swap | 24/7  |
| Bybit   | `GET /v5/market/instruments-info?category=linear` (BYBIT) | `TSLAPERP`, `AAPLX`                 | Linear/tokenized          | 24/7  |

Auth: Tardis covers these as archive (no auth for historical); live REST = venue API key.

Rate limits: same CeFi perp venue limits already handled by adapters.

**Basis-arb-able symbols (Databento DBEQ.BASIC twin exists):** AAPL, TSLA, AMZN, MSFT, GOOGL/GOOG (→GOOGL), META, NVDA,
NFLX, AMD, INTC, BABA, COIN, MSTR, PLTR, GME, AMC, MARA — all 17 registered in `crypto_equity_link.py`.

**Dispersion-only symbols (no real-equity twin, pre-IPO):** SPCX (SpaceX — Binance `SPCXUSDT`) — registered in
`STANDALONE_EQUITY_PERP_SYMBOLS`.

**Phase 1 implementation summary (unified-api-contracts@e4606ac0):**

Files changed:

- `unified_api_contracts/_instrument_enums.py` — added `EQUITY_PERP` + `TOKENIZED_EQUITY` to `InstrumentType` (NOTE:
  these two `InstrumentType` members were later DEPRECATED-but-kept-parseable by the 2026-07-16 operator ruling still
  in the active doc's Architecture-decision banner — the equity identity now rides catalogue tags instead of a
  distinct `instrument_type`)
- `unified_api_contracts/canonical/crosscutting/crypto_equity_link.py` — NEW: `CRYPTO_EQUITY_PERP_TO_REAL_EQUITY` dict
  (18 entries), `LINKED_EQUITY_PERP_BASES` frozenset, `STANDALONE_EQUITY_PERP_SYMBOLS`, `tracks_equity()` lookup
  function
- `unified_api_contracts/canonical/crosscutting/__init__.py` — export new module
- `unified_api_contracts/canonical/crosscutting/mvp_scope.py` — added `EQUITY_PERP`/`TOKENIZED_EQUITY` to CeFi MVP rule
  instrument_types; `base_ccys` union with `CEFI_EQUITY_PERP_BASE_UNIVERSE`
- `unified_api_contracts/registry/cefi_instrument_universe.py` — added `CEFI_EQUITY_PERP_BASE_UNIVERSE` (20 equity
  ticker bases)
- `unified_api_contracts/registry/venue_constants.py` — added `equity_perps`/`tokenized_equities` to
  `INSTRUMENT_TYPE_FOLDER_MAP`
- `unified_api_contracts/internal/reference/ledger_asset_resolution.py` — `EQUITY_PERP`→`PERP`,
  `TOKENIZED_EQUITY`→`SPOT_TOKEN`
- `unified_api_contracts/internal/reference/canonical_id_builder.py` — added both types to
  `SUPPORTED_INSTRUMENT_TYPES` + `_build_cefi_simple` dispatch
- `unified_api_contracts/__init__.py` + `unified_api_contracts/registry/__init__.py` — all new symbols exported
- `tests/unit/test_crypto_equity_link.py` — NEW: 9 unit tests (all passing)

QG: `bash scripts/quality-gates.sh --no-fix` → ✅ ALL QUALITY GATES PASSED (216s), 10116 passed, 557 skipped, 5 xfailed.

### 2026-06-20 — data-ingestion launch sweep (autonomous) — universe→real-data

After declaring the universe (Phase 1/1b–1f), kicked off the **real-data backfills for the expanded universe**. State of
each leg (so a future agent doesn't re-launch a tracked/blocked one):

- **VM code tarball REBUILT + on GCS** (`gs://deployment-scripts-central-element-323112/code/` + `/vm/`) carrying
  UAC@`0fe9067e` (the full new universe: 12 DBEQ stocks + equity-perp link + Kalshi/Polymarket perps), UTL@`a2128285`,
  MTDS@`c0f46973`. The tarball dirty-gate had blocked on foreign WIP (strategy carry_staked_basis + UTL ledger-spine +
  deployment terraform-lock) — operator authorised "just unblock it"; foreign WIP **stashed**
  (`orphan-wip-unblock-tarball-2026-06-20*`, recoverable), my terraform provider-lock **committed**
  (deployment-service@`c77477d`).
- **Kalshi trades — LAUNCHED** (the operator's explicit "is Kalshi downloading history?" ask): VM
  `mtds-prediction-kalshi-20260620-130906`, full history `2021-07-30→2026-06-20` (`--venue KALSHI`, genesis from
  `venue_launch_dates.py`). Creds present (`kalshi-api-credentials`).
- **Polymarket trades** — existing baseline (already backfilled; not re-launched).
- **DBEQ-12 single stocks (cash-stock leg)** — NOT blind-launched: correctly **rides the tracked full-3-dataset
  backfill** (`tradfi_databento_subscription_universe_lockdown_2026_06_18.md` Phase 2.6 line 271 P1), gated behind the
  running CME-b close-out → `build_instrument_catalogue --asset-group tradfi` (regenerates the denominator w/ the 12 new
  stocks). DBEQ.BASIC stock fetch is **proven** (write-stamp force-smoke 2026-06-17, same plan line 95-100) — the old "0
  records" was pre-subscription.
- **Equity-perps (Binance/OKX/Bybit)** — fetch path EXISTS (Tardis CeFi archive already covers
  BINANCE-FUTURES/OKX-SWAP/BYBIT-FUTURES, see Progress Log above); remaining work = the CeFi **universe-filter add**
  (this plan Phase 2 P1, market-tick-data-service). Tracked, not blind-launchable.
- **Kalshi/Polymarket perps** — fetch path is NOT wired (perp-funding launcher is Hyperliquid-S3-only); tracked as
  `prediction_venue_perps_and_live_clob_depth_2026_06_20.md` P1 (IS perp enumerator + MTDS perp trades/funding
  adapters). Universe layer (`venue_launch_dates` KALSHI-PERP 2026-05-29 / POLYMARKET-PERP 2026-04-21, venue_constants,
  coverage_starts) shipped d92ea1a.

Net: the expanded-universe data ingestion is **launched (Kalshi) or correctly tracked+sequenced** — nothing silently
dropped. The CME-b tradfi close-out is the linchpin that unlocks the DBEQ 3-dataset leg.

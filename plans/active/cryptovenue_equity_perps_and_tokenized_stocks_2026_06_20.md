---
title: Crypto-venue single-stock perps + tokenized stocks (Binance/OKX/Bybit) — equity basis/dispersion arb
created: 2026-06-20
parent_epic: cefi_master
assigned_vm: human-planning
estimate_class: brand-new
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 6
locked_by: live-defi-rollout
priority: P2
status: active
---

# Crypto-venue equity perps + tokenized stocks

Operator 2026-06-20: crypto venues now list **single-stock perpetuals + tokenized stocks** — opportunity surface for
equity basis/dispersion arb. Verified (web, 2026-06):

- **Binance**: 7,000 US stocks/ETFs + tokenized **bStocks**; single-stock perps incl. `SPCXUSDT` (SpaceX, its #2
  product), Meta/NVDA/GOOG 24/7; US stock service live 2026-06-01.
- **OKX**: 17 US equity perpetual contracts (24/7) + Samsung/SK Hynix/Hyundai + **pre-IPO perps**.
- **Bybit**: stock perps (TSLA/AAPL) + `AAPLX` tokenized.

## Architecture decision (HARD)

Crypto-venue equity perps/tokenized-stocks are derivatives TRACKING a real equity → map to the **SAME canonical equity
instrument** as the Databento (DBEQ.BASIC) real equity, as new venue×instrument cells, so **basis/dispersion arb
(crypto-venue stock-perp vs real equity) + 24/7-vs-market-hours overnight-gap arb** work cross-venue. Funding-bearing
perps also map to the crypto-perp funding canonical (sister of
`prediction_venue_perps_and_live_clob_depth_2026_06_20.md`). **Pre-IPO / SpaceX** instruments have NO real-equity twin →
standalone canonical (no basis leg, dispersion only across crypto venues).

## Phase 0 — research + opportunity sizing

- [x] [RESEARCH] P0. Per venue (Binance/OKX/Bybit), document: equity-perp + tokenized-stock contract list endpoint,
      symbol↔real-ticker mapping (SPCXUSDT→SPACEX, AAPLX→AAPL), trades/funding/orderbook-depth endpoints (REST+ws), 24/7
      vs market-hours, auth, rate limits. Identify which symbols HAVE a Databento real-equity twin (basis-arb-able) vs
      pre-IPO/uniques (dispersion-only). Repo: instruments-service (findings → plan Progress Log). ✅
      unified-api-contracts@e4606ac0 — findings in Progress Log below.
- [x] [RESEARCH] P1. Tardis coverage check — do our existing Tardis/CeFi feeds already carry these equity-perp symbols
      (so historical comes free via the existing CeFi pipeline) or is a new fetch path needed? ✅
      unified-api-contracts@e4606ac0 — **KEY FINDING: Tardis ALREADY covers BINANCE-FUTURES, OKX-SWAP, OKX-FUTURES,
      BYBIT-FUTURES** (confirmed via `canonical_mappings.py` `DATA_SOURCE_TO_VENUES["tardis"]`). Equity-perp symbols on
      these venues flow through the existing CeFi pipeline — this is a universe+canonical-link add, not a new fetch
      path.

## Phase 1 — universe + canonical mapping

- [x] [UAC] P1. Add the equity-perp / tokenized-stock symbols to the crypto-perp/cefi instrument universe with a
      `tracks_equity=<canonical ticker>` link to the Databento equity canonical (mirror `cme_polymarket_link.py`
      cross-venue-link pattern). Venue tokens already exist (BINANCE/OKX/BYBIT) — new instrument_type (`equity_perp` /
      `tokenized_equity`). Repo: unified-api-contracts. ✅ unified-api-contracts@e4606ac0

## Phase 2 — download (rides existing CeFi/Tardis pipeline — fetch path EXISTS, enumeration is gated)

- [ ] [SCRIPT] P1. **instruments-service** (NOT mtds — CeFi universe is IS-driven per the IS→MTDS contract; MTDS
      auto-downloads whatever IS enumerates via the existing Tardis archive that already covers
      BINANCE-FUTURES/OKX-SWAP/BYBIT-FUTURES). **Exact surface discovered 2026-06-20** — the equity-perp contracts ARE
      in the Tardis archive but are FILTERED OUT today by the curated base-asset universe gate. Two coupled edits, both
      must land together (filter-only = data-correctness regression: equity-perps would mis-stamp as `PERPETUAL` and
      pollute crypto-perp manifest shards — the heartbeat rule):
  1. **Pass the filter**: `_passes_asset_filter` at
     `instruments_service/reference_data/adapters/cefi/tardis/parsing.py:357-367` rejects any base not in
     `_tardis.CEFI_BASE_ASSET_UNIVERSE`. Allow equity-perp bases too — union in UAC `CEFI_EQUITY_PERP_BASE_UNIVERSE`
     (from `unified_api_contracts.registry.cefi_instrument_universe`, already shipped uac@e4606ac0) +
     `STANDALONE_EQUITY_PERP_SYMBOLS` (SPCX). The same `CEFI_BASE_ASSET_UNIVERSE` gate is duplicated in the
     **hyperliquid** (`cefi/hyperliquid.py:124`) and **aster** (`cefi/aster.py:166`) adapters — only Binance/OKX/Bybit
     (Tardis) list equity-perps, so the tardis adapter is the required edit; HL/aster need it only if they list
     equity-perps (they don't today — leave or guard).
  2. **Stamp the right type**: the Tardis type-resolution returns `InstrumentType.PERPETUAL` for these linear perps.
     Override to `InstrumentType.EQUITY_PERP` when the base ∈
     `LINKED_EQUITY_PERP_BASES`/`STANDALONE_EQUITY_PERP_SYMBOLS` (UAC `crypto_equity_link.tracks_equity()` / the
     base-universe). Mirror the existing OPTION special-case in `_passes_asset_filter` / the type path. Tokenized-equity
     venues (Bybit `AAPLX`) → `InstrumentType.TOKENIZED_EQUITY`.
  3. Unit tests: METAUSDT/NVDAUSDT(Binance) + META-USDT-SWAP(OKX) pass the filter AND stamp EQUITY_PERP; SPCXUSDT →
     EQUITY_PERP (standalone); a crypto perp (BTCUSDT) still stamps PERPETUAL (no regression); AAPLX(Bybit) →
     TOKENIZED_EQUITY. Then `bash scripts/quality-gates.sh` green.
  4. After IS enumerates them → launch the CeFi Tardis backfill (existing launcher) for the equity-perp window (Binance
     equity-perp listings began ~2026; check `coverage_starts.py`/`venue_launch_dates.py` for per-venue genesis) → MTDS
     downloads trades+funding+book. Verify manifest `capture_status` for an EQUITY_PERP shard. Repo: instruments-service
     (enum) + deployment-service (launch).

## Phase 3 — live CLOB depth (shared with the prediction-perps plan's Phase 3)

- [ ] [SCRIPT] P2. Live BBO+depth recording for these equity perps (for basis-arb slippage calibration) — reuse the CeFi
      live-ws book connectors. Repo: market-tick-data-service.

## Phase 4 — arb wiring

- [ ] [DESIGN] P2. strategy-service — equity basis/dispersion archetype: crypto-venue stock-perp vs Databento real
      equity (basis), cross-crypto-venue (dispersion), 24/7-vs-market-hours overnight gap. Repo: strategy-service.

## Codex SSOT updates

- [ ] [DOCS] P2. codex/02-data + codex/09-strategy — crypto-venue equity-perp sourcing + the equity-basis arb archetype.
      Repo: unified-trading-pm.

## Progress Log

### 2026-06-20 — Phase 0 + Phase 1 shipped (unified-api-contracts@e4606ac0)

**Phase 0 research findings:**

**Tardis/CeFi coverage (P1 key finding — HIGHLY EFFICIENT):**

- `unified_api_contracts.canonical.canonical_mappings.DATA_SOURCE_TO_VENUES["tardis"]` already includes
  `BINANCE-FUTURES`, `OKX-SWAP`, `OKX-FUTURES`, `BYBIT-FUTURES`.
- This means equity-perp symbols on these venues (METAUSDT, NVDAUSDT, AAPLX, etc.) are ALREADY covered by the existing
  Tardis CeFi pipeline — Phase 2 is adding them to the CeFi universe filter, NOT building a new fetch path.

**Per-venue endpoint summary (for Phase 2 implementer):**

| Venue   | Contract list endpoint                                    | Symbol format                      | Instrument type           | Hours |
| ------- | --------------------------------------------------------- | ---------------------------------- | ------------------------- | ----- |
| Binance | `GET /fapi/v1/exchangeInfo` (BINANCE-FUTURES)             | `METAUSDT`, `NVDAUSDT`, `SPCXUSDT` | Linear USDT-margined perp | 24/7  |
| OKX     | `GET /api/v5/public/instruments?instType=SWAP` (OKX-SWAP) | `META-USDT-SWAP`, `AAPL-USDT-SWAP` | Linear USDT-margined swap | 24/7  |
| Bybit   | `GET /v5/market/instruments-info?category=linear` (BYBIT) | `TSLAPERP`, `AAPLX`                | Linear/tokenized          | 24/7  |

Auth: Tardis covers these as archive (no auth for historical); live REST = venue API key.

Rate limits: same CeFi perp venue limits already handled by adapters.

**Basis-arb-able symbols (Databento DBEQ.BASIC twin exists):** AAPL, TSLA, AMZN, MSFT, GOOGL/GOOG (→GOOGL), META, NVDA,
NFLX, AMD, INTC, BABA, COIN, MSTR, PLTR, GME, AMC, MARA — all 17 registered in `crypto_equity_link.py`.

**Dispersion-only symbols (no real-equity twin, pre-IPO):** SPCX (SpaceX — Binance `SPCXUSDT`) — registered in
`STANDALONE_EQUITY_PERP_SYMBOLS`.

**Phase 1 implementation summary (unified-api-contracts@e4606ac0):**

Files changed:

- `unified_api_contracts/_instrument_enums.py` — added `EQUITY_PERP` + `TOKENIZED_EQUITY` to `InstrumentType`
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

## Temporary states + their canonical follow-up plans

- Phase 2 (MTDS universe add) → this plan Phase 2 todo above (market-tick-data-service)
- Phase 3 (live CLOB) → this plan Phase 3 todo above
- Phase 4 (strategy arb wiring) → this plan Phase 4 todo above

## Phase 1b — Databento equity expansion + Binance index-mark capture (operator Q 2026-06-20)

Operator question resolved: Binance marks stock-perps via an **Index Price** disclosed in the public API
(`/fapi/v1/premiumIndex` → `indexPrice` + `markPrice`); funding = f(markPrice − indexPrice). During US market hours
`indexPrice` ≈ NYSE/NASDAQ ≈ Databento DBEQ.BASIC (verified live: NVDA idx 209.85, MSTR idx 115.52). Stocks are heavily
arbed → any liquid consolidated US-equity feed is a valid reference. Off-hours the index is SYNTHETIC (tape closed) — no
cash hedge → funding spikes + overnight-gap risk. Quick funding scan: 19 Binance stock-perps; carry is EPISODIC (MSTR
realized +26–40% ann during spikes, 0 most ticks; SPX ~5.5%).

- [x] ✅ [UAC] P1. Add the single-stock underlyings of all Binance/OKX/Bybit equity-perps (the `crypto_equity_link` 18 +
      the rest of Binance's ~7k as they list) to the tradfi **DBEQ.BASIC** instrument universe
      (`tradfi_instrument_universe.py`) so each crypto-venue equity-perp has a real-equity twin to MEASURE basis.
      DBEQ.BASIC is allowlist-approved + ohlcv-1s/1m is L0/free → low cost. Start with the 18 basis-able, then expand to
      Binance's full stock-perp list. Repo: unified-api-contracts. — **DONE as the full Binance tradfi-perp SUPERSET
      (operator 2026-06-24: "extra fine, NOT LESS")**: unified-api-contracts@b03ef0e8 + instruments-service@a60f82f.
      Enumerated ALL **103** BINANCE-FUTURES PERPETUAL tradfi underlyings (70 US equities + 7 ADRs + 7 commodities + 16
      index/sector ETFs + 3 KRX BLOCKED-DATA); coverage **100 covered / 0 gap / 3 BLOCKED-DATA**. Adds: 42 equities/ADRs
      (ARM/ASML/BABA/TSM/NVO/SONY/NOK +
      COIN/MSTR/PLTR/CRWD/DELL/GME/RIVN/SMCI/UBER/HOOD/HIMS/DKNG/RKLB/ASTS/IREN/NBIS/CRCL/CRWV/BMNR/ALAB/CRDO/AAOI/COHR/WDC/SNDK/AXTI/FLNC/GLW/NOW/F-already/BE/ONDS/USAR/CIEN/DIS/HD-already/BX-skip/CFG/PAYP/SPCX/EBAY/LITE)
      to `tradfi_ticker_universe.py` (NASDAQ→`nasdaq_tickers`, NYSE/ADR→new `NYSE_TRADFI_PERP_TICKERS`) +
      `ticker_registry.py` `EXCHANGE_BY_TICKER`; 6 ETFs (EWT/EWY/ROBO/SLX/URNM/UVXY) to `ETF_TICKERS`+ARCA; **PA.FUT
      (palladium=XPD) + PL.FUT (platinum=XPT)** to `_CME_COMMODITY_FUTURES` + symbology + `tradfi_roots.py`. **Commodity
      aliases**: XAU→GC, XAG→SI, XPT→PL, XPD→PA, NATGAS→NG, CL→CL, COPPER→HG. **BLOCKED-DATA** (KRX primary-listings,
      NOT on databento DBEQ.BASIC US-equities): HYUNDAI, SAMSUNG, SKHYNIX — need a Korea-equity vendor (e.g.
      Sportradar-equivalent KRX/ADR feed) to cover; until then they ride the OKX/Bybit equity-perp Tardis path only (no
      real-equity twin). Distinct via base_asset + 2026-launch-date (Binance tradfi perps all listed 2026; crypto
      ticker-collisions like DASH/STX/IP/MET/AVAAI/CBRS/BZ launched pre-2026 → excluded).
- [x] ✅ [UAC+IS] P0. **Root-cause fix — the captured tradfi equity universe was a STRICT SUBSET of the enumerated one**
      (validation gate: HOOD/INTC/RIVN/UBER/CRWD/MRVL/ZM are in `NASDAQ_TICKERS` but were NEVER built/captured).
      `databento/adapter.py::_get_equity_symbols()` fetched ONLY `sp500_tickers`+`etf_tickers` — silently dropping every
      NASDAQ-only name. Fixed to include `nasdaq_tickers` + the new `nyse_tradfi_perp_tickers` (352 equity symbols
      enumerated, was 268 built). instruments-service@a60f82f. The wave-launcher picks up the new instruments on next
      run — no manual backfill triggered (per scope).
- [x] ✅ [UAC] P0. **Dual-source (A): databento DBEQ.BASIC resolution VERIFIED + massive wired as 2nd source.** Live
      DBEQ.BASIC DEFINITION+OHLCV probe (databento creds): **56/56 new tickers resolve**
      (ARM/ASML/BABA/TSM/NVO/SONY/NOK + COIN/MSTR/PLTR/… + ETFs EWT/EWY/ROBO/SLX/URNM/UVXY); SNDK's `definition` schema
      lags (recent WDC spinoff) but `ohlcv-1m` returns 750 rows/day → genuinely covered for the data we fetch.
      **SOURCE_PRIORITY is keyed by (asset_group,data_type), NOT per-ticker** —
      `("tradfi","trades"/"tbbo"/"ohlcv_1m"/"ohlcv_15m"/"options_chain"/     "futures_chain")=["massive","databento"]`
      ALREADY → every new equity inherits massive(primary)+databento(fallback) with zero per-ticker wiring; `ohlcv_1s`
      stays databento-only (massive flat-files have no 1s schema). FIXED the symmetric subset-bug on the massive side:
      `massive.py::_curated_equity_symbols()` also fetched only sp500+etf → now includes nasdaq+nyse-perp so BOTH
      sources fetch the identical universe. instruments-service@f670bd4.
- [x] ✅ [UAC] P0. **MVP-marking (B2): the Binance tradfi-perp cash twins are now MVP-scoped.** The tradfi MVP rule
      (`mvp_scope.py`) gated MVP to CME×{FUTURE,OPTION}×{ES,NQ,VX} ONLY — equities/ETFs were `present` in the catalogue
      but `mvp=False`. Added an **equity-basis carve-out**: (NASDAQ/NYSE/ARCA × EQUITY/ETF ×
      `TRADFI_EQUITY_PERP_BASIS_     UNIVERSE`) [92 cash twins of the Binance equity/ETF perps] → MVP, AND extended the
      futures underliers with the commodity roots backing Binance perps (GC/SI/PL/PA/NG/CL/HG ←
      XAU/XAG/XPT/XPD/NATGAS/CL/COPPER). Precise gating: a non-Binance SP500 name (ADI) + non-perp commodity (ZC corn)
      stay non-MVP. The catalogue `_add_mvp_column` calls `is_mvp("tradfi",…)` per row → on next
      `build_instrument_catalogue` regen the new tickers tag `mvp=True`. unified- api-contracts@219e4b17. (98 mvp_scope
      tests + 173 ticker/g9 tests green.)
- [ ] [SCRIPT] P0. **Propagation ops (B1/B3/B4) — run on real infra to completion.** The code (above) is the enabler;
      the chain is wired: (1) IS instruments backfill (`launch-instruments-backfill-vm.sh --asset-group TRADFI`) writes
      per-day InstrumentRecords for the new equities (databento/massive now fetch them) → (2)
      `build_instrument_     catalogue` rolls up + tags `mvp=True` → (3) `enumerate_expected_universe.py` v2 tradfi
      enumerator reads the catalogue, seeds the new equities as `expected_unattempted` at venue=NASDAQ/NYSE grain → (4)
      MTDS wave-launcher reads the manifest `expected_unattempted` gaps + captures. **Run + verify**: catalogue has new
      MVP tickers; manifest shows them `expected_unattempted`; a sample equity captures non-NaN OHLCV. Repo:
      deployment-service (launchers) + instruments-service (catalogue/enumerator CLIs). **IN PROGRESS** (this session) —
      see Progress Log.
- [ ] [DATA] P2. **BLOCKED-DATA** — HYUNDAI / SAMSUNG / SK Hynix (3 Binance tradfi-perps with NO US-listed twin, KRX
      primary): source a Korea-equity reference + tick vendor so the cash-equity twin exists for basis (databento
      DBEQ.BASIC is US-only). Until sourced these perps have a dispersion-only (cross-crypto-venue) leg, no cash hedge.
      Repo: instruments-service (vendor ask → operator). **DEFERRED** — needs an operator credential/vendor decision
      (Korea equities).
- [ ] [SCRIPT] P1. market-tick-data-service — capture Binance/OKX/Bybit `indexPrice` + `markPrice` + `fundingRate` for
      the equity-perps as a first-class data_type (the venue's DISCLOSED mark — needed for basis = mark−index and for
      OFF-HOURS synthetic-mark detection where the cash tape is closed). These ride the existing CeFi
      premiumIndex/funding endpoints. Repo: market-tick-data-service.
- [ ] [SCRIPT] P2. e2e-testing — recurring DAILY funding/basis scan across all crypto-venue equity-perps (annualized
      funding + perp-vs-index basis + flag market-hours vs off-hours) → opportunity-sizing report. Wire as a scheduled
      job (mirror an existing scan). Repo: e2e-testing.
- [ ] [DESIGN] P2. strategy-service — single-stock basis execution-venue gap: CME has index futures (ES/NQ for SPX/NDX
      basis) but NOT broad single-stock futures → the long-cash leg for NVDA/MSTR/etc needs IBKR (equities) OR a second
      tokenized/perp venue OR pure cross-crypto-venue basis. Decide per-symbol hedge venue; off-hours = no-cash-hedge
      (dispersion-only or unhedged-funding-capture with risk limits). Repo: strategy-service.

## Phase 1c — INDEX perps are the executable-NOW basis (operator 2026-06-20)

Confirmed Binance lists INDEX perps: `SPXUSDT` (S&P 500, funding +5.5% ann live), `SPYUSDT` (SPY ETF), `XAUUSDT` (gold)
— likely `NAS100`/Nasdaq too (different symbol). These are the BEST basis candidates because the hedge leg is ALREADY
wired + data-covered: CME `ES.FUT`(SP500)/`NQ.FUT`(NASDAQ100)/`RTY.FUT`(Russell)/`YM.FUT`(Dow) on GLBX.MDP3 + the
execution-service `cme_adapter`. Advantages over single-stock perps: (1) deep real hedge (no IBKR/tokenized gap), (2)
both legs already in universe + data, (3) CME Globex ~23h/day → hedge available nearly whenever the perp trades (single
stocks go dark off-hours), (4) live SPX-perp carry ~5.5% ann vs ES. **This is the FIRST equity-perp basis to actually
trade** — data-complete + hedge-executable now.

- [ ] [UAC] P0. Map the index perps (`SPXUSDT`→ES/SPX, `NAS100/NDX`→NQ, `SPYUSDT`→ES/SPY-ETF, `XAUUSDT`→GC gold) to the
      CME index-future + Databento index canonical, carrying the **scale/multiplier** (Binance SPX-perp is a SCALED
      micro unit — mark 0.36 ≈ SPX/scale; sizing MUST use the multiplier for the ES hedge ratio). Extend
      `crypto_equity_link.py` with an index-perp link (or a sibling map) incl. contract_multiplier. Repo:
      unified-api-contracts.
- [ ] [DESIGN] P1. strategy-service — INDEX-perp cash-and-carry as the FIRST equity-perp archetype: short Binance
      SPX/NAS perp (collect funding) + long CME ES/NQ (real hedge, ~23h), scale-adjusted; this is fully executable with
      current venues (cefi perp execution + cme_adapter). Sequence ahead of the single-stock basis (which is
      hedge-venue-blocked). Repo: strategy-service.

## Phase 1d — NET basis (perp funding − futures cost-of-carry) — the gating economics (operator 2026-06-20)

Operator's critical catch: we can't hold cash-index / physical-gold / physical-oil → the hedge leg is a FUTURE, which
has its own cost-of-carry/roll that NETS against the perp funding. **GROSS perp funding ≠ NET capturable basis.** The
30-day GROSS funding scan (below) OVERSTATES the carry.

- Gold (GC): contango ≈ financing (~4–5% ann) → long-GC-future decays to spot on roll → erodes funding; gold-perp ~4%
  gross funding − ~5% contango → net possibly NEGATIVE.
- Oil (CL): curve-dependent — contango erodes, backwardation ADDS roll yield. Net swings with the term structure.
- Equity index (ES): carry ≈ financing − dividends (~3–4% contango) → erodes the SPX-perp funding (mean only ~1.2% ann
  gross) → net slim/negative.
- **Single stocks hedged with the ACTUAL stock (IBKR)**: NO roll decay (stock doesn't expire) — only borrow/financing →
  CLEANER net than the futures-hedged index/commodity, at the cost of the equities-venue gap. (Partly reverses "index =
  cleanest": index = cleanest EXECUTION; single-stock-vs-stock = cleanest NET carry.)

Gold/oil futures coverage CONFIRMED: GC/CL/NG/HO/SI/HG on GLBX.MDP3 (our subscription). Binance commodity perps:
XAU/XAG/COPPER (oil-perp symbol TBD).

- [x] [SCRIPT] P0. e2e-testing — NET-basis backtest: for each index/commodity basis pair, compute NET = perp_funding -
      futures roll-carry, where roll-carry = annualized (front-next contract) spread from the Databento GLBX term
      structure, over >=1 month (ideally 1y). Output per-pair NET annualized basis + turnover (sign-flips) + the
      contango/backwardation regime. This GATES which basis pairs are actually profitable. Repo: e2e-testing (Databento
      creds). -- unified-api-contracts@0fe9067e (UAC additions gated on result); NET-basis table in Progress Log below.
- [x] [SCRIPT] P1. e2e-testing — same NET treatment for single stocks under BOTH hedge options: (a) CME single-stock
      future where it exists (futures carry), (b) IBKR cash stock (borrow/financing, no roll). Compare net carry to
      decide the hedge venue per symbol. Repo: e2e-testing. -- Result: hedge=IBKR stock borrow wins for all singles (no
      CME single-stock futures for US equities); 12 TRADEABLE (NET>5%). unified-api-contracts@0fe9067e adds DBEQ.BASIC
      STOCK entries for all 12.
- [ ] [DESIGN] P1. strategy-service — the basis archetype's edge = NET basis (funding - hedge carry), NOT gross funding;
      restrict entry to US market hours (UAC venue_session_hours.py has NYSE/NASDAQ UTC 13:30-20:00 EDT / 14:30-21:00
      EST) and HOLD through off-hours (synthetic-index window) per the operator's "trade in-hours, sit outside" model.
      Repo: strategy-service.

### 30-day GROSS funding scan (2026-06-20) — overstates net; see Phase 1d

Steady-positive / LOW-TURNOVER (mean>3% ann, <15% sign-flips/90): MSFT 14.0% (1 flip), GOOGL 10.3% (0), NVDA 10.3% (2),
MSTR 10.2% (5), AMD 8.2% (2), COIN 7.4% (4), META 5.7% (1), PLTR 4.6%, HOOD 4.5%, XAU 4.0% (0), TSLA 3.9% (1), AMZN 3.6%
(0), CRCL 20.4% (5, choppy). Note mean>>median for most → funding ~0 off-hours, spikes in-hours; %positive 16–54%. SPX
1.2% mean / 5.5% median / 92% positive. NET (Phase 1d) is the real number.

### NET-basis backtest results (2026-06-20) -- Phase 1d P0+P1 COMPLETE (unified-api-contracts@0fe9067e)

**Futures roll-carry (Databento GLBX.MDP3, ~11mo 2025-07 to 2026-06, ohlcv-1d, annualized front-next spread):**

| Future         | Mean carry | 30d carry | Regime        |
| -------------- | ---------- | --------- | ------------- |
| GC (gold)      | +3.20%     | +2.34%    | contango      |
| SI (silver)    | +4.06%     | +2.98%    | contango      |
| HG (copper)    | +4.37%     | +2.54%    | contango      |
| ES (SP500)     | +3.26%     | +3.29%    | contango      |
| NQ (NASDAQ100) | +3.80%     | +3.93%    | contango      |
| CL (crude oil) | -20.09%    | -31.78%   | backwardation |

**Full NET-basis table (Binance fundingRate x3x365 gross - hedge cost):**

| Pair   | Gross% | Hedge cost%  | NET%   | 1mo-NET% | Turn% | Verdict   |
| ------ | ------ | ------------ | ------ | -------- | ----- | --------- |
| XAU    | +4.0%  | +3.2% (GC)   | +0.8%  | +1.6%    | 14.5% | SLIM      |
| XAG    | +4.7%  | +4.1% (SI)   | +0.7%  | +0.9%    | 25.5% | SLIM      |
| COPPER | +4.2%  | +4.4% (HG)   | -0.2%  | -0.1%    | 32.0% | NEGATIVE  |
| SPX    | +2.1%  | +3.3% (ES)   | -1.2%  | -2.1%    | 14.0% | NEGATIVE  |
| SPY    | -6.6%  | +3.3% (ES)   | -9.8%  | -6.1%    | 7.0%  | NEGATIVE  |
| NVDA   | +22.1% | +0.5% borrow | +21.6% | +9.8%    | 24.5% | TRADEABLE |
| MSFT   | +15.7% | +0.3% borrow | +15.4% | +13.7%   | 25.0% | TRADEABLE |
| CRCL   | +23.8% | +2.5% borrow | +21.3% | +17.9%   | 33.5% | TRADEABLE |
| INTC   | +18.2% | +0.5% borrow | +17.7% | +16.4%   | 28.5% | TRADEABLE |
| GOOGL  | +18.0% | +0.3% borrow | +17.6% | +10.0%   | 30.5% | TRADEABLE |
| AMD    | +24.4% | +0.5% borrow | +23.9% | +7.7%    | 28.7% | TRADEABLE |
| TSLA   | +9.4%  | +0.5% borrow | +8.9%  | +3.4%    | 22.0% | TRADEABLE |
| AMZN   | +5.7%  | +0.3% borrow | +5.4%  | +3.3%    | 23.0% | TRADEABLE |
| META   | +11.7% | +0.3% borrow | +11.4% | +5.4%    | 23.5% | TRADEABLE |
| HOOD   | +9.1%  | +2.0% borrow | +7.1%  | +2.5%    | 29.0% | TRADEABLE |
| AAPL   | +6.8%  | +0.3% borrow | +6.5%  | +1.7%    | 23.0% | TRADEABLE |
| BABA   | +6.2%  | +1.0% borrow | +5.2%  | -8.3%\*  | 29.0% | TRADEABLE |
| MSTR   | +5.6%  | +1.5% borrow | +4.1%  | +8.7%    | 27.0% | MARGINAL  |
| COIN   | +5.7%  | +1.5% borrow | +4.2%  | +5.9%    | 37.0% | MARGINAL  |
| PLTR   | +2.4%  | +0.7% borrow | +1.7%  | +3.9%    | 16.0% | SLIM      |

\*BABA 1-mo NET -8.3%: regime unstable; include but monitor monthly.

**Decisions:**

- ADDED to DBEQ.BASIC universe (UAC@0fe9067e): NVDA/MSFT/CRCL/INTC/GOOGL/AMD/TSLA/AMZN/META/HOOD/AAPL/BABA (NET>5%)
- NOT added: MSTR/COIN/PLTR (MARGINAL<5%), XAU/XAG (SLIM), COPPER/SPX/SPY (NEGATIVE)
- Commodity verdict: GC/SI/HG contango (3.2-4.4%) nearly neutralizes XAU/XAG/COPPER gross funding -- net too slim
- Oil (CL) is in extreme backwardation (-20%) which ADDS roll yield to long-futures -- but no Binance WTI perp found; if
  USOILUSDT lists, it would be extremely attractive (expected NET >20%)
- No `crypto_commodity_link.py` file created: no commodity perp crossed the NET>5% threshold

## Phase 1e — NET-basis VERDICT (backtest done 2026-06-20) → single-stock basis is the trade

Backtest (uac@0fe9067e + table in pm@d9d7f1ae1): NET = funding − futures roll-carry, 11mo Databento GLBX + Binance
funding.

- **WINNERS (single stocks, CASH-hedged = no roll, NET +5–24%)**: AMD/NVDA/CRCL/INTC/GOOGL/MSFT/META/TSLA/HOOD/AAPL/AMZN
  (12 added to DBEQ.BASIC).
- **REJECTED (cost-of-carry erodes — operator's catch CONFIRMED)**: commodities NET~0 (GC/SI/HG contango 3.2–4.4%
  neutralizes XAU/XAG/COPPER funding); indices NET-NEGATIVE (ES/NQ contango erases SPX/SPY/NDX funding, SPX −1.2%). Do
  NOT pursue futures-hedged commodity/index basis.
- **Oil wildcard**: CL extreme backwardation (−20% ann) → a long-CL hedge EARNS roll → NET >20% IF a Binance/other-venue
  WTI perp existed (none on Binance).

### Follow-ups (the unlocks)

- [ ] [DESIGN] P0. execution-service — **IBKR equities execution adapter is the GATING unlock**: the winning
      single-stock basis (NET +5–24%) needs the long CASH-stock leg on IBKR (`ibkr-gateway-infra`); the short perp is
      already executable (cefi). Without IBKR equities, none of the 12 winners are tradeable. Wire IBKR equities (not
      just the existing index/futures path). Repo: execution-service + ibkr-gateway-infra.
- [ ] [RESEARCH] P1. Check OKX/Bybit (+ Hyperliquid) for a WTI/Brent OIL perp — CL is in −20% backwardation so an
      oil-perp + long-CL-future hedge would be NET >20% (the single best pair if a perp exists). If found, add it. Repo:
      instruments-service.
- [ ] [DESIGN] P1. strategy-service — single-stock basis archetype on the 12 net-profitable names: short Binance
      stock-perp (collect funding) + long IBKR cash stock; low-turnover (held; the winners had 0–2 sign-flips/90); entry
      restricted to US hours (UAC venue_session_hours), hold through off-hours. Edge = NET basis, sized continuously by
      the daily scan. Repo: strategy-service.

## Phase 1f — methodology corrections (operator 2026-06-20): anti-look-ahead universe + dividends + liquidity + regime-flip

**Liquidity (Binance 24h $vol / $OI):** BTC $6.1B/$6.2B · SPX $7.7M/$4.9M (THIN) · SPY $14M/$22M · NDX/Nasdaq NOT LISTED
· XAU $327M/$232M (deepest non-crypto) · single stocks $4–38M (MSTR/CRCL/NVDA top). → Binance SPX/NDX perps too thin for
size; deep S&P/Nasdaq for cross-strategy (SPX-vs-BTC pairs/stat-arb) must use CME ES/NQ, not the Binance index perp.

**Look-ahead/survivorship (the hardcoded-12 is in-sample — FIX):** don't ship a fixed name list. Build a BROAD universe
(top-N by market cap AND by perp OI/volume) + DYNAMIC selection that ranks by LIVE net-carry each rebalance. Driver =
retail long-demand → richest funding = high-attention/volatile/retail-heavy names (NVDA/TSLA/MSTR/CRCL/meme/AI), NOT
strictly biggest; the set CHURNS over quarters. The 12 added in 0fe9067e are a starting seed, NOT the universe.

- [ ] [DESIGN] P0. strategy-service + UAC — replace the fixed net-profitable-12 with: (a) BROAD universe = top-N US
      stocks by market cap ∪ top-N crypto-venue equity-perps by OI/volume; (b) a DYNAMIC live-net-carry ranking that
      selects the tradeable set each rebalance (avoids look-ahead/survivorship). Repo: unified-api-contracts
      (universe) + strategy-service (ranking).
- [ ] [SCRIPT] P1. e2e-testing — re-run the NET-basis backtest with DIVIDENDS priced into the long cash-stock leg
      (holding the stock EARNS dividends → ADDS to net; current +5–24% is a FLOOR). Use a dividend-yield source per
      name. Repo: e2e-testing.
- [ ] [RESEARCH] P1. instruments-service — KEEP crude/gold/natgas/SPX/NDX commodity+index perps in the universe despite
      net≤0 NOW (carry FLIPS with the futures curve — crude already −20% backwardated). Check how far back Binance's
      perp history goes per symbol → confirm whether the backtest window spans a contango↔backwardation regime change
      (if history is short, the "net-negative" verdict is regime-conditional, not permanent). Repo: instruments-service.
- [ ] [DESIGN] P2. strategy-service — note: XAU (gold) perp is the deepest non-crypto leg ($327M) → if gold carry flips
      to backwardation (or for non-basis gold strategies), it's the most size-able crypto-venue commodity. Repo:
      strategy-service.

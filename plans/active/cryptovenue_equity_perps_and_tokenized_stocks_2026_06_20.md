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

Operator 2026-06-20: crypto venues now list **single-stock perpetuals + tokenized stocks** — opportunity surface for equity basis/dispersion arb. Verified (web, 2026-06):
- **Binance**: 7,000 US stocks/ETFs + tokenized **bStocks**; single-stock perps incl. `SPCXUSDT` (SpaceX, its #2 product), Meta/NVDA/GOOG 24/7; US stock service live 2026-06-01.
- **OKX**: 17 US equity perpetual contracts (24/7) + Samsung/SK Hynix/Hyundai + **pre-IPO perps**.
- **Bybit**: stock perps (TSLA/AAPL) + `AAPLX` tokenized.

## Architecture decision (HARD)
Crypto-venue equity perps/tokenized-stocks are derivatives TRACKING a real equity → map to the **SAME canonical equity instrument** as the Databento (DBEQ.BASIC) real equity, as new venue×instrument cells, so **basis/dispersion arb (crypto-venue stock-perp vs real equity) + 24/7-vs-market-hours overnight-gap arb** work cross-venue. Funding-bearing perps also map to the crypto-perp funding canonical (sister of `prediction_venue_perps_and_live_clob_depth_2026_06_20.md`). **Pre-IPO / SpaceX** instruments have NO real-equity twin → standalone canonical (no basis leg, dispersion only across crypto venues).

## Phase 0 — research + opportunity sizing
- [x] [RESEARCH] P0. Per venue (Binance/OKX/Bybit), document: equity-perp + tokenized-stock contract list endpoint, symbol↔real-ticker mapping (SPCXUSDT→SPACEX, AAPLX→AAPL), trades/funding/orderbook-depth endpoints (REST+ws), 24/7 vs market-hours, auth, rate limits. Identify which symbols HAVE a Databento real-equity twin (basis-arb-able) vs pre-IPO/uniques (dispersion-only). Repo: instruments-service (findings → plan Progress Log). ✅ unified-api-contracts@e4606ac0 — findings in Progress Log below.
- [x] [RESEARCH] P1. Tardis coverage check — do our existing Tardis/CeFi feeds already carry these equity-perp symbols (so historical comes free via the existing CeFi pipeline) or is a new fetch path needed? ✅ unified-api-contracts@e4606ac0 — **KEY FINDING: Tardis ALREADY covers BINANCE-FUTURES, OKX-SWAP, OKX-FUTURES, BYBIT-FUTURES** (confirmed via `canonical_mappings.py` `DATA_SOURCE_TO_VENUES["tardis"]`). Equity-perp symbols on these venues flow through the existing CeFi pipeline — this is a universe+canonical-link add, not a new fetch path.

## Phase 1 — universe + canonical mapping
- [x] [UAC] P1. Add the equity-perp / tokenized-stock symbols to the crypto-perp/cefi instrument universe with a `tracks_equity=<canonical ticker>` link to the Databento equity canonical (mirror `cme_polymarket_link.py` cross-venue-link pattern). Venue tokens already exist (BINANCE/OKX/BYBIT) — new instrument_type (`equity_perp` / `tokenized_equity`). Repo: unified-api-contracts. ✅ unified-api-contracts@e4606ac0

## Phase 2 — download (likely rides existing CeFi pipeline)
- [ ] [SCRIPT] P1. market-tick-data-service — if Tardis/CeFi feeds carry these symbols, just add them to the CeFi venue universe (trades + funding + book already handled by the CeFi adapters); else add a fetch path. Verify historical + live. Repo: market-tick-data-service.

## Phase 3 — live CLOB depth (shared with the prediction-perps plan's Phase 3)
- [ ] [SCRIPT] P2. Live BBO+depth recording for these equity perps (for basis-arb slippage calibration) — reuse the CeFi live-ws book connectors. Repo: market-tick-data-service.

## Phase 4 — arb wiring
- [ ] [DESIGN] P2. strategy-service — equity basis/dispersion archetype: crypto-venue stock-perp vs Databento real equity (basis), cross-crypto-venue (dispersion), 24/7-vs-market-hours overnight gap. Repo: strategy-service.

## Codex SSOT updates
- [ ] [DOCS] P2. codex/02-data + codex/09-strategy — crypto-venue equity-perp sourcing + the equity-basis arb archetype. Repo: unified-trading-pm.

## Progress Log

### 2026-06-20 — Phase 0 + Phase 1 shipped (unified-api-contracts@e4606ac0)

**Phase 0 research findings:**

**Tardis/CeFi coverage (P1 key finding — HIGHLY EFFICIENT):**
- `unified_api_contracts.canonical.canonical_mappings.DATA_SOURCE_TO_VENUES["tardis"]` already includes `BINANCE-FUTURES`, `OKX-SWAP`, `OKX-FUTURES`, `BYBIT-FUTURES`.
- This means equity-perp symbols on these venues (METAUSDT, NVDAUSDT, AAPLX, etc.) are ALREADY covered by the existing Tardis CeFi pipeline — Phase 2 is adding them to the CeFi universe filter, NOT building a new fetch path.

**Per-venue endpoint summary (for Phase 2 implementer):**

| Venue | Contract list endpoint | Symbol format | Instrument type | Hours |
|---|---|---|---|---|
| Binance | `GET /fapi/v1/exchangeInfo` (BINANCE-FUTURES) | `METAUSDT`, `NVDAUSDT`, `SPCXUSDT` | Linear USDT-margined perp | 24/7 |
| OKX | `GET /api/v5/public/instruments?instType=SWAP` (OKX-SWAP) | `META-USDT-SWAP`, `AAPL-USDT-SWAP` | Linear USDT-margined swap | 24/7 |
| Bybit | `GET /v5/market/instruments-info?category=linear` (BYBIT) | `TSLAPERP`, `AAPLX` | Linear/tokenized | 24/7 |

Auth: Tardis covers these as archive (no auth for historical); live REST = venue API key.

Rate limits: same CeFi perp venue limits already handled by adapters.

**Basis-arb-able symbols (Databento DBEQ.BASIC twin exists):**
AAPL, TSLA, AMZN, MSFT, GOOGL/GOOG (→GOOGL), META, NVDA, NFLX, AMD, INTC, BABA, COIN, MSTR, PLTR, GME, AMC, MARA — all 17 registered in `crypto_equity_link.py`.

**Dispersion-only symbols (no real-equity twin, pre-IPO):**
SPCX (SpaceX — Binance `SPCXUSDT`) — registered in `STANDALONE_EQUITY_PERP_SYMBOLS`.

**Phase 1 implementation summary (unified-api-contracts@e4606ac0):**

Files changed:
- `unified_api_contracts/_instrument_enums.py` — added `EQUITY_PERP` + `TOKENIZED_EQUITY` to `InstrumentType`
- `unified_api_contracts/canonical/crosscutting/crypto_equity_link.py` — NEW: `CRYPTO_EQUITY_PERP_TO_REAL_EQUITY` dict (18 entries), `LINKED_EQUITY_PERP_BASES` frozenset, `STANDALONE_EQUITY_PERP_SYMBOLS`, `tracks_equity()` lookup function
- `unified_api_contracts/canonical/crosscutting/__init__.py` — export new module
- `unified_api_contracts/canonical/crosscutting/mvp_scope.py` — added `EQUITY_PERP`/`TOKENIZED_EQUITY` to CeFi MVP rule instrument_types; `base_ccys` union with `CEFI_EQUITY_PERP_BASE_UNIVERSE`
- `unified_api_contracts/registry/cefi_instrument_universe.py` — added `CEFI_EQUITY_PERP_BASE_UNIVERSE` (20 equity ticker bases)
- `unified_api_contracts/registry/venue_constants.py` — added `equity_perps`/`tokenized_equities` to `INSTRUMENT_TYPE_FOLDER_MAP`
- `unified_api_contracts/internal/reference/ledger_asset_resolution.py` — `EQUITY_PERP`→`PERP`, `TOKENIZED_EQUITY`→`SPOT_TOKEN`
- `unified_api_contracts/internal/reference/canonical_id_builder.py` — added both types to `SUPPORTED_INSTRUMENT_TYPES` + `_build_cefi_simple` dispatch
- `unified_api_contracts/__init__.py` + `unified_api_contracts/registry/__init__.py` — all new symbols exported
- `tests/unit/test_crypto_equity_link.py` — NEW: 9 unit tests (all passing)

QG: `bash scripts/quality-gates.sh --no-fix` → ✅ ALL QUALITY GATES PASSED (216s), 10116 passed, 557 skipped, 5 xfailed.

## Temporary states + their canonical follow-up plans
- Phase 2 (MTDS universe add) → this plan Phase 2 todo above (market-tick-data-service)
- Phase 3 (live CLOB) → this plan Phase 3 todo above
- Phase 4 (strategy arb wiring) → this plan Phase 4 todo above

## Phase 1b — Databento equity expansion + Binance index-mark capture (operator Q 2026-06-20)

Operator question resolved: Binance marks stock-perps via an **Index Price** disclosed in the public API (`/fapi/v1/premiumIndex` → `indexPrice` + `markPrice`); funding = f(markPrice − indexPrice). During US market hours `indexPrice` ≈ NYSE/NASDAQ ≈ Databento DBEQ.BASIC (verified live: NVDA idx 209.85, MSTR idx 115.52). Stocks are heavily arbed → any liquid consolidated US-equity feed is a valid reference. Off-hours the index is SYNTHETIC (tape closed) — no cash hedge → funding spikes + overnight-gap risk. Quick funding scan: 19 Binance stock-perps; carry is EPISODIC (MSTR realized +26–40% ann during spikes, 0 most ticks; SPX ~5.5%).

- [ ] [UAC] P1. Add the single-stock underlyings of all Binance/OKX/Bybit equity-perps (the `crypto_equity_link` 18 + the rest of Binance's ~7k as they list) to the tradfi **DBEQ.BASIC** instrument universe (`tradfi_instrument_universe.py`) so each crypto-venue equity-perp has a real-equity twin to MEASURE basis. DBEQ.BASIC is allowlist-approved + ohlcv-1s/1m is L0/free → low cost. Start with the 18 basis-able, then expand to Binance's full stock-perp list. Repo: unified-api-contracts.
- [ ] [SCRIPT] P1. market-tick-data-service — capture Binance/OKX/Bybit `indexPrice` + `markPrice` + `fundingRate` for the equity-perps as a first-class data_type (the venue's DISCLOSED mark — needed for basis = mark−index and for OFF-HOURS synthetic-mark detection where the cash tape is closed). These ride the existing CeFi premiumIndex/funding endpoints. Repo: market-tick-data-service.
- [ ] [SCRIPT] P2. e2e-testing — recurring DAILY funding/basis scan across all crypto-venue equity-perps (annualized funding + perp-vs-index basis + flag market-hours vs off-hours) → opportunity-sizing report. Wire as a scheduled job (mirror an existing scan). Repo: e2e-testing.
- [ ] [DESIGN] P2. strategy-service — single-stock basis execution-venue gap: CME has index futures (ES/NQ for SPX/NDX basis) but NOT broad single-stock futures → the long-cash leg for NVDA/MSTR/etc needs IBKR (equities) OR a second tokenized/perp venue OR pure cross-crypto-venue basis. Decide per-symbol hedge venue; off-hours = no-cash-hedge (dispersion-only or unhedged-funding-capture with risk limits). Repo: strategy-service.

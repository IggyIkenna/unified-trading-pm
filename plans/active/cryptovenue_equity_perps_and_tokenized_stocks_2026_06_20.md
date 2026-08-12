---
doc_type: plan
title: Crypto-venue single-stock perps + tokenized stocks (Binance/OKX/Bybit) — equity basis/dispersion arb
summary:
  Add canonical universe coverage for crypto-venue single-stock perpetuals and tokenized stocks (Binance/OKX/Bybit),
  enabling equity basis/dispersion arb cross-venue.
status: active
nature: process
asset_group:
  [cefi] # corrected 2026-08-08 (ag-closeout-audit cefi, Phase 0.3 orthogonality check) -- was [cefi, defi], a mistag:
  # doc scope is 100% CeFi (Binance/OKX/Bybit single-stock perps + tokenized stocks, parent_epic:cefi_master), zero
  # on-chain/DEX/DeFi-protocol content anywhere (the "DEFI" hits are the Binance margin-asset enum value and the
  # live-defi-rollout branch name, not the DeFi asset group). The dual tag made this doc invisible to both cefi's and
  # defi's own tranche audits (each excludes docs carrying a peer-AG marker per SKILL.md's Orthogonality HARD CHECK) --
  # the exact falls-through-both-audits failure class that check exists to catch.
stage: [meta]
repos: [deployment-api, deployment-service, e2e-testing, execution-service, ibkr-gateway-infra, instruments-service]
scope: [engineer, admin]
tags: [cefi, crypto, equity-perps, tokenized-stocks, binance, okx, bybit, canonical, universe]
related: []
created: 2026-06-20
parent_epic: cefi_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 6
last_updated: 2026-06-27
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /codex/02-data/cefi-capture-universe.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /plans/archive/2026_07/prediction_venue_perps_and_live_clob_depth_2026_06_20.md,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/crypto_equity_link.py,
    instruments-service/instruments_service/reference_data/adapters/cefi/tardis/parsing.py,
    /plans/archive/issues/krx_equity_twin_no_source_2026_06_28.md,
  ]
---

# Crypto-venue equity perps + tokenized stocks

Operator 2026-06-20: crypto venues now list **single-stock perpetuals + tokenized stocks** — opportunity surface for
equity basis/dispersion arb. Verified (web, 2026-06):

- **Binance**: 7,000 US stocks/ETFs + tokenized **bStocks**; single-stock perps incl. `SPCXUSDT` (SpaceX, its #2
  product), Meta/NVDA/GOOG 24/7; US stock service live 2026-06-01.
- **OKX**: 17 US equity perpetual contracts (24/7) + Samsung/SK Hynix/Hyundai + **pre-IPO perps**.
- **Bybit**: stock perps (TSLA/AAPL) + `AAPLX` tokenized.

## Architecture decision (HARD)

> **UPDATED 2026-07-16 (operator, SUPERSEDES the distinct-`instrument_type` decision below).** Verbatim: _"system needs
> to be able to understand what's an equity perp to know to find the spot leg on tradfi venues etc and other nuances but
> broad definitions should remain perpetual and equities — it's hard to know from name alone or inst_id what's an equity
> perp so some tag or mapping needs to exist."_ **`instrument_type` reverts to the BROAD contract-mechanics type**: a
> crypto-venue single-stock perp is **`PERPETUAL`** (NOT `EQUITY_PERP`) and a tokenized stock is **`SPOT_PAIR`** (NOT
> `TOKENIZED_EQUITY`). The equity identity + real-equity linkage instead ride two durable **catalogue tags** stamped at
> roll-up (`build_instrument_catalogue._add_equity_tags`): **`is_equity_perp`** (bool — base ∈
> `CEFI_EQUITY_PERP_BASE_UNIVERSE`, True for BOTH the perp and tokenized-spot forms) and **`tracks_equity`** (the
> Databento `DBEQ.BASIC` real-equity ticker via `crypto_equity_link.tracks_equity`; `""` for pre-IPO standalones). The
> `EQUITY_PERP`/`TOKENIZED_EQUITY` `InstrumentType` members are removed from the CeFi MVP rule (equity perps MVP-gate as
> `PERPETUAL`, their bases already unioned into `base_ccys`) and are DEPRECATED-but-defined in the enum (no longer
> minted; kept parseable for pre-2026-07-16 persisted rows + external string consumers, and to keep the ledger-asset map
> complete). **This also resolved the WS-H double-seed blocker**: the catalogue `instrument_type` now equals the
> manifest's (`PERPETUAL`), so the honest-coverage denominator reconciles. Shipped: unified-api-contracts +
> instruments-service (see Progress Log 2026-07-16). The basis/dispersion-arb intent below is UNCHANGED — discovery of
> the real-equity spot leg is via the `tracks_equity` tag/link map instead of a distinct type.

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
     venues (Bybit `AAPLX`) → `InstrumentType.TOKENIZED_EQUITY`. 2a. \*\*UPDATED 2026-07-10 (operator, aligning with the
     canonical-instrument-id decision) — `instrument_id`/ `instrument_key` construction for EQUITY_PERP/TOKENIZED_EQUITY
     MUST route through the shared canonical builder
     (`unified_api_contracts.internal.reference.canonical_id_builder.build_instrument_id`, or the venue's own
     `_build_canonical_perpetual_key`-family helper in `tardis/parsing.py` if one already exists for the venue), the
     SAME mechanism `instrument_id_format_canonicalization_2026_07_08.md`'s effort wired in for regular
     `PERPETUAL`/`FUTURE`/`OPTION` this session — NOT a new ad hoc f-string. This plan section predates that decision
     (filed 2026-06-20, canonical-builder decision made 2026-07-08) and, implemented as originally written, would add a
     fresh instance of exactly the ad hoc-construction pattern that decision is retiring elsewhere (cf.
     `canonical_id_builder_retrofit_checklist_2026_07_08.md`'s ~48-DeFi-adapter backlog of the same class). Since these
     ARE linear-margined perpetual contracts economically, they should carry the same `@LIN` margin marker convention as
     every other CeFi PERPETUAL — confirm with the venue's already-wired builder (Binance/OKX/Bybit are all landed as of
     this session) rather than reinventing margin-type resolution for this new `InstrumentType` value. Add this as an
     explicit acceptance check in step 3's unit tests below (assert the real target shape, e.g.
     `BINANCE-FUTURES:PERPETUAL:META-USDT@LIN`, not just that the type stamps EQUITY_PERP).
  3. Unit tests: METAUSDT/NVDAUSDT(Binance) + META-USDT-SWAP(OKX) pass the filter AND stamp EQUITY_PERP; SPCXUSDT →
     EQUITY_PERP (standalone); a crypto perp (BTCUSDT) still stamps PERPETUAL (no regression); AAPLX(Bybit) →
     TOKENIZED_EQUITY. Then `bash scripts/quality-gates.sh` green.
  4. After IS enumerates them → launch the CeFi Tardis backfill (existing launcher) for the equity-perp window (Binance
     equity-perp listings began ~2026; check `coverage_starts.py`/`venue_launch_dates.py` for per-venue genesis) → MTDS
     downloads trades+funding+book. Verify manifest `capture_status` for an EQUITY_PERP shard. Repo: instruments-service
     (enum) + deployment-service (launch).

  > **STATUS 2026-07-18 (Binance full-listing widen — operator directive; edits 1–3 DONE, sub-item 4 OPEN):** The
  > un-filter gate this todo describes was **ALREADY removed 2026-06-23** — `_passes_asset_filter` (now
  > `parsing.py:545`, not `:357-367`) is FULL-UNIVERSE (no `CEFI_BASE_ASSET_UNIVERSE` gate on SPOT/PERP/FUTURE), so the
  > equity perps already pass; the HL/aster duplicate gates are likewise no longer base-gates. Per the 2026-07-16 ruling
  > the equity identity rides the `is_equity_perp`/`tracks_equity` tags (NOT an `EQUITY_PERP` type), stamped at rollup
  > by `_cefi_equity_tags` (`build_instrument_catalogue.py:775`), which imports `CEFI_EQUITY_PERP_BASE_UNIVERSE`
  > DIRECTLY from UAC — so the universe add IS the coupling (no IS adapter code change needed). **WIDENED the universe
  > to ALL live Binance `contractType=TRADIFI_PERPETUAL`** (139 contracts / 138 bases pulled live from
  > `fapi/v1/exchangeInfo`): +20 NEW bases (124→144), incl. a first-time **HK_EQUITY** category
  > (Tencent/Xiaomi/Zhipu/MiniMax). Coupled tests assert a sample tag `is_equity_perp` + pass the filter. —
  > unified-api-contracts@172e8cdb + instruments-service@ff6d9750 (QG-green both; full detail + the 20-base list in
  > Progress Log 2026-07-18). **Sub-item 4 (launch the Tardis backfill) stays OPEN** — explicitly out of scope for this
  > catalogue-definition widen (operator: no MTDS backfill / prod mutation).
  >
  > **Round5 finding (2026-08-08): the "is it now OK to launch" question is already answered — "no MTDS backfill / prod
  > mutation" was a scope restriction for THAT SPECIFIC catalogue-widen task, not a standing operator gate.**
  > `plans/active/cefi_consolidated_closeout_2026_07_18.md` Track 0 already re-lists "Launch the CeFi Tardis backfill
  > for the equity-perp window" as a plain `[SCRIPT] P1` todo (no `[OPERATOR]` tag), filed the SAME day this note was
  > written — the closeout plan's own author already treated it as ordinary dispatchable infra work, consistent with how
  > every other backfill in this doc's own Progress Log (Kalshi trades, `instr-backfill-tradfi-20260623`,
  > `mdps-backfill-cefi-*`) was launched without a fresh per-launch operator ask. Sub-item 4 is AO-dispatchable SCRIPT
  > work; the actual launch was not performed in this pass (documentation-question audit, not an implementation
  > dispatch).

## Phase 3 — live CLOB depth (shared with the prediction-perps plan's Phase 3)

- [x] ✅ [SCRIPT] P2. **DONE 2026-08-09 — NO CODE CHANGE NEEDED, live-verified** (batch11 todo 6). Live BBO+depth for
      these equity perps, reusing the CeFi live-ws book connectors. Repo: market-tick-data-service. Every capture-path
      layer (per-venue `book_snapshot_5` connectors, base-token derivation, canonical-id builders,
      `_resolve_is_universe`) is already symbol-generic — proved live: ran the real websocket-streaming CLI
      (test-bucket-routed) against a live `AAPL` equity-perp on all 3 venues; all 3 wrote a genuine `captured` manifest
      row (13/9/18 rows), same shard-atom shape as any other live book capture.

## Phase 4 — arb wiring

- [ ] [DESIGN] P2. strategy-service — equity basis/dispersion archetype: crypto-venue stock-perp vs Databento real
      equity (basis), cross-crypto-venue (dispersion), 24/7-vs-market-hours overnight gap. Repo: strategy-service.

## Codex SSOT updates

- [ ] [DOCS] P2. codex/02-data + codex/09-strategy — crypto-venue equity-perp sourcing + the equity-basis arb archetype.
      Repo: unified-trading-pm.

## Phase 5 — KRX venue close-out + Yahoo guardrail + centralised parity gate + databento boundary + Barchart removal

Operator-directed 2026-06-24 (coordinator-relayed). Yahoo guardrail (P0) is SHIPPED (see Progress Log); the rest are
TRACKED here for dispatch to fresh-context workers (each is a self-contained multi-file unit — do NOT bundle). All
context (probed limits, file surfaces, conventions) is in the Progress Log so a cold-start worker can execute.

- [x] ✅ [UAC] P0. **Yahoo intraday lookback GUARDRAIL (SSOT) + QG test.** `YAHOO_INTRADAY_LOOKBACK_DAYS` +
      `assert_yahoo_intraday_within_limit` + `YahooLookbackExceededError` in `registry/data_source_continuity.py`;
      probed-live ladder 1m=28d / 15m=89d(via range=60d) / 1h=730d / 1d=unbounded; QG test
      `tests/unit/test_yahoo_intraday_lookback_guardrail.py` asserts beyond-limit RAISES, within-limit allowed, exact
      boundary inclusive, unknown interval KeyErrors. unified-api-contracts@9818f051.
- [x] ✅ [SCRIPT] P0. **Wire the guardrail onto the Yahoo fetch path (not bypassable).**
      `assert_yahoo_intraday_within_limit` already wired in `_normalize_and_guard_intraday_window` (called before
      `_fetch_ticker_history`); adapter-level unit tests added: 31d-back 1m raises + 90d-back 15m raises + within-limit
      passes — market-tick-data-service@13b90034
- [x] ✅ [SCRIPT] P1. **KRX venue registration (mirror NYSE end-to-end).** Add venue `KRX` (source=`yahoo`) across: (a)
      UAC `market_data_categories` `VENUES_BY_ASSET_GROUP["tradfi"]` + `VENUE_TO_ASSET_GROUP` + `ALL_VENUES`; (b) UAC
      `SOURCE_PRIORITY[("tradfi", ohlcv_1d/1h/15m/1m)]` must reach yahoo for KRX (via `_VENUE_SOURCE_EXCLUSIONS` or a
      KRX-aware slice — KRX is yahoo-only, exclude databento/massive for KRX); (c) IS venue registry/enumeration
      (`get_venues_for_asset_groups` / the tradfi adapter venue set); (d) MTDS venue→source routing
      (`live_source_for_venue` / preflight) so KRX resolves yahoo; (e) the manifest/availability_index venue set; (f)
      deployment-api/ui if they enumerate venues. Grep how NYSE is registered across these + mirror. Repos:
      unified-api-contracts + instruments-service + market-tick-data-service (+ deployment-api/ui). —
      unified-api-contracts@844c5ee6b (venue_mapping.py + market_data_categories.py KRX registration) +
      instruments-service@1ba5da4b (KRX venue + reference records).
- [x] ✅ [UAC] P1. **3 KRX stocks in UAC tradfi universe + MVP basis carve-out → 103/103.** Add Samsung(005930.KS), SK
      Hynix(000660.KS), Hyundai(005380.KS) as venue=KRX equities (source=yahoo) to the tradfi universe + the MVP
      equity-basis carve-out (`mvp_scope` — extend the carve-out to accept venue=KRX × EQUITY × the 3 KRX bases, OR add
      KRX bases to `TRADFI_EQUITY_PERP_BASIS_UNIVERSE`). Their Binance perps are already cefi-MVP → both legs MVP → the
      tradfi-perp superset closes at 103/103. Repo: unified-api-contracts. — unified-api-contracts@844c5ee6b
      (tradfi_ticker_universe.py + tradfi_instrument_universe.py: 005930/000660/005380 .KS entries).
- [ ] [SCRIPT] P1. **Backfill the 3 KRX stocks via guardrailed Yahoo (operator ladder).** Per stock: 1d since 2019-01-01
      (full) + 1h 730d + 15m 89d(range=60d) + 1m 28d(7d-chunked). FX→yahoo wave-launcher is the precedent for a
      yahoo-source backfill. Verify rows captured + manifest reflects them (KRX shard). Repo: deployment-service
      (launcher) + market-tick-data-service.
- [x] ✅ [SCRIPT] P1. **CENTRALISED data-driven venue/source/adapter/MVP parity gate (the general guard).** ONE
      parametrised gate (UAC contract test + a `check_*` wired into `base-*.sh` where cross-repo) that ITERATES the
      canonical registries: every venue in the universe/MVP → assert present in IS-registry + MTDS-routing + manifest
      venue set + a resolvable source (+ UI/api if they enumerate); every (venue, data_type) in the MVP set → a declared
      source + an adapter supporting that source+data_type+granularity; every source referenced → an adapter resolves;
      every adapter → declares supported (data_types, granularity/lookback limits) enforced on its fetch path (Yahoo
      guardrail = the first example). Parametrise over registry contents (no new test code per future venue). It AUDITS
      existing venues too — report pre-existing half-wired ones (fix small, issue-doc big). PROVE: removing KRX from
      MTDS routing RED-fails a named assertion. Repos: unified-api-contracts (contract test) + base-\*.sh wiring. —
      unified-api-contracts@844c5ee6b, tests/unit/test_venue_source_adapter_parity.py (408 lines, parametrised over
      registries).
- [ ] [UAC] P1. **Databento L-floor boundary PRECISION.** PROBE databento live (`metadata.get_dataset_range` per
      schema + binary-search progressively-older requests until entitlement denies) to MEASURE the EXACT
      earliest-accessible date per level for OUR subscription: L0 (~16y), L1 trades/tbbo/mbp-1/bbo ("1yr" → is it
      365/366/rolling-cal-year?), L2 mbp-10 / L3 mbo ("1mo" → 28/30/31/cal-month/rolling?). Update
      `LEVEL_MAX_LOOKBACK_DAYS` / `earliest_allowed_start` / `assert_lookback_allowed`
      (databento_subscription_allowlist) + the manifest enumerator's floor-clip to the EXACT measured values. QG test:
      one day past the boundary rejected, one day inside allowed. Repo: unified-api-contracts.
- [ ] [REFACTOR] P2. **DEPRECATE + REMOVE all Barchart (own unit — operator 2026-06-24).** Barchart's only role was the
      VIX cash-index 15m preload; the VIX cash-index was deprecated this session (VIX from VX futures via databento
      XCBF.PITCH). Per delete-deprecated-code: (1) `rg -i barchart` workspace-wide (~30 files: SOURCE*PRIORITY tradfi
      ohlcv_15m list, `SOURCE_MODE_CAPABILITY["barchart"]`, `EMISSION_LATENCY_MS_BY_SOURCE["barchart"]`,
      data_source_continuity BARCHART_VIX*\* constants + SourceWindow, `_umi_yahoo`/tradfi adapters, IS enumerator,
      multiple UAC tests, CLAUDE.md "VIX 15m: Barchart preload" note, docs); (2) VERIFY no live MVP cell is
      source=barchart + the VIX path uses VX-futures-databento (repoint any straggler FIRST); (3) DELETE the
      adapter/client/source-entries (remove code, no deprecation shim); remove `barchart` from every source enum /
      SOURCE_PRIORITY / continuity registry; (4) UPDATE CLAUDE.md VIX note → VX-futures-via-databento; (5) update the
      source-priority/parity tests (deleting a source must not break them). The new parity gate then finds NO
      source=barchart-with-no-adapter (cross-check). If Barchart is load-bearing somewhere unexpected → STOP + flag.
      Repos: unified-api-contracts + market-tick-data-service + unified-trading-pm (CLAUDE.md).

## Progress Log

### 2026-08-09 — NET-basis backtest re-run with dividend yield priced in (`cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 8)

> **Header corrected 2026-08-09**: was mislabeled "todo 6" (that's the BBO+depth live-ws extension, Phase 3 above) —
> this content is batch11's todo 8. Label fixed to match content, not re-derived.

Dispatched via AO batch11. **Databento DBEQ.BASIC has no dividends/corporate-actions schema** (confirmed by grepping
every Databento adapter in market-tick-data-service and instruments-service for "dividend" — zero hits; matches the
codex `tradfi-databento-sourcing-ssot.md` gap and the 2026-05-23 instruments-service ledger audit's own note that a
dividend calendar would need an external source). Used **yfinance** instead, mirroring the already-established pattern
elsewhere in this workspace (market-tick-data-service's `yahoo_finance_adapter.py`, features-service's
`yfinance_earnings_adapter.py`, e2e-testing's own `scripts/common/backfill_vix_yahoo.py`) rather than the heavier
Polygon corporate-actions adapter (features-service, requires a separate `polygon-api-key` secret + cross-repo import).

Implementation: `e2e-testing/scripts/cefi/net_basis_scan.py` extended with `fetch_ttm_dividend_yield_pct()`
(trailing-12mo dividend sum ÷ last close, computed directly from yfinance's raw `Ticker.dividends` history — NOT the
`info["dividendYield"]` field, which has a documented stale/pre-split bug: it read 0.45% for NVDA vs. the
raw-history-derived 0.125%), `dividend_adjusted_net_basis()`, and a `run_dividend_adjusted_backtest()` driver. Live-run
2026-08-09, holding the original 2026-06-20 backtest's Gross%/Borrow% columns fixed (same 11mo Databento-roll +
Binance-funding window) so the comparison isolates exactly the one variable this todo asks to add — dividend yield —
rather than conflating it with funding-rate drift (funding is highly time-varying; a supplementary live-Binance-funding
sanity check the same day showed funding has compressed materially fleet-wide since 06-20, several pairs now
NET-negative on today's live rates — that's a SEPARATE, already-tracked concern, the doc's own DYNAMIC-universe-ranking
follow-up a few lines below, not folded into this dividend-only delta):

| Pair  | Gross% | Borrow% | Div yield% (TTM) | Hedge cost% | NET% (w/ div) | Δ vs 06-20 NET% |
| ----- | ------ | ------- | ---------------- | ----------- | ------------- | --------------- |
| NVDA  | +22.1% | +0.50%  | +0.125%          | +0.375%     | +21.73%       | +0.13pp         |
| MSFT  | +15.7% | +0.30%  | +0.712%          | -0.412%     | +16.11%       | +0.71pp         |
| CRCL  | +23.8% | +2.50%  | +0.000%          | +2.500%     | +21.30%       | +0.00pp         |
| INTC  | +18.2% | +0.50%  | +0.000%          | +0.500%     | +17.70%       | +0.00pp         |
| GOOGL | +18.0% | +0.30%  | +0.240%          | +0.060%     | +17.94%       | +0.24pp         |
| AMD   | +24.4% | +0.50%  | +0.000%          | +0.500%     | +23.90%       | +0.00pp         |
| TSLA  | +9.4%  | +0.50%  | +0.000%          | +0.500%     | +8.90%        | +0.00pp         |
| AMZN  | +5.7%  | +0.30%  | +0.000%          | +0.300%     | +5.40%        | +0.00pp         |
| META  | +11.7% | +0.30%  | +0.355%          | -0.055%     | +11.75%       | +0.35pp         |
| HOOD  | +9.1%  | +2.00%  | +0.000%          | +2.000%     | +7.10%        | +0.00pp         |
| AAPL  | +6.8%  | +0.30%  | +0.335%          | -0.035%     | +6.84%        | +0.34pp         |
| BABA  | +6.2%  | +1.00%  | +0.818%          | +0.182%     | +6.02%        | +0.82pp         |

**Result**: dividends confirm the operator's framing — the 06-20 figures WERE a floor, every pair's NET is flat-to-up
(+0.00 to +0.82pp) with dividends priced in, no pair flips verdict (all 12 remain TRADEABLE). Biggest beneficiaries are
the higher-yielding names (BABA +0.82pp, MSFT +0.71pp); 6 of the 12 (CRCL/INTC/AMD/TSLA/AMZN/HOOD) pay no dividend today
so are unchanged. Evidence: `e2e-testing@12d1f3c` (this commit), script output reproduced above, run via
`python3 scripts/cefi/net_basis_scan.py` (credential-free, public Yahoo endpoints only).

### 2026-08-09 — Todo 9 (Binance listing/history-length vs regime-window cross-reference) DISPATCHED + DONE (`cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 9)

Live-queried Binance USDT-margined futures `fapi/v1/exchangeInfo` (`onboardDate`) +
`fapi/v1/klines?interval=1d&startTime=0` (first real daily candle) for every symbol in the requested set
(XAU/XAG/COPPER/SPX/SPY/NDX), then cross-referenced each listing date/history-length against this doc's own NET-basis
backtest regime window (~11-12mo, 2025-07-01→2026-06-30, Databento GLBX front-next roll-carry table above). **No
universe add/remove decision made** — per this todo's explicit scope.

| Symbol | Binance perp | Listed (UTC) | History as of 2026-08-09 | Overlap w/ 2025-07-01→2026-06-30 window | Coverage % |
| ------ | ------------ | ------------ | ------------------------ | --------------------------------------- | ---------- |
| XAU    | XAUUSDT      | 2025-12-11   | 241d (~7.9mo)            | 201d                                    | 55%        |
| XAG    | XAGUSDT      | 2026-01-07   | 214d (~7.0mo)            | 174d                                    | 48%        |
| COPPER | COPPERUSDT   | 2026-03-06   | 156d (~5.1mo)            | 116d                                    | 32%        |
| SPX    | SPXUSDT      | 2024-12-10   | 607d (~20.0mo)           | 364d (full window)                      | 100%\*     |
| SPY    | SPYUSDT      | 2026-04-06   | 125d (~4.1mo)            | 85d                                     | 23%        |
| NDX    | _(none)_     | N/A          | N/A                      | N/A                                     | N/A\*\*    |

\*SPX coverage is a false positive — see caveat below. \*\*NDX never had a real Binance perp or a NET-basis row in this
doc's own table (only XAU/XAG/COPPER/SPX/SPY were ever measured — line ~772-780 above); it was only ever an aspirational
mapping target in the "Map the index perps" todo, not a measured verdict.

**Is the SLIM/NEGATIVE verdict regime-conditional or permanent?**

- **XAU/XAG/COPPER (SLIM/NEGATIVE; GC/SI/HG contango over the observed window)**: each perp's trading history covers
  only 32-55% of the 11-12mo regime window the futures-side contango reading spans, starting 4-8 months after the window
  opened — we have zero Binance funding data from the pre-listing portion of the window, so we cannot say the contango
  regime (and hence the NET reading) held there too. CL's own -20% backwardation reading in the SAME table, SAME window,
  is this doc's own proof that a commodity future can sit in a materially different regime than gold/silver/copper's
  contango — a partial-window contango reading is not proof of permanence. **Verdict: regime-conditional, not proven
  permanent.**
- **SPY (NEGATIVE; ES contango)**: shortest real history (125d/23% coverage) — SPYUSDT didn't exist for the first ~9
  months of the window. The -9.8% NET reading rests on barely 4 months of live funding data. **Verdict:
  regime-conditional, weakly supported** (smallest sample of the set).
- **SPX (NEGATIVE; ES contango; nominal 100% coverage)**: the long history is a false signal — Binance's `SPXUSDT` is
  confirmed live (`underlyingType=COIN`, `underlyingSubType=['Meme']`, matching batch11 todo 2's independent finding) to
  be the **SPX6900 meme coin, not an S&P-500-linked instrument**. Its 20-month history is irrelevant to the S&P-500
  carry regime — the doc's original "SPX" NET-basis row compares a meme-coin's funding rate against an S&P-500 future's
  carry, a mismatched pair, not a regime read on the real index. Not a new finding (todo 2 already flagged the symbol
  mismatch) — restated here because it directly undermines this row's own "100% coverage" cell: full history of the
  WRONG instrument doesn't resolve the regime question, because no genuine SPX perp exists on Binance. **Verdict: not
  assessable as a regime question — the underlying data doesn't measure what the table implies.**
- **NDX**: no Binance perp exists (independently re-confirmed via a full-symbol-list grep of `exchangeInfo` for
  NAS100/NDX — zero matches) and no NET-basis row for it was ever produced. Nothing to cross-reference.

**Bottom line**: of the 4 symbols with both a real Binance perp AND a real NET-basis verdict (XAU/XAG/COPPER/SPY), every
one has <60% overlap with the observed regime window and none has traded through a regime shift the way CL demonstrably
has — their SLIM/NEGATIVE calls should be read as "negative under the one contango regime observed so far," not as
structurally permanent. SPX's case is a category mismatch, not a regime question. NDX was never measured. No
universe/backtest change made by this todo.

Evidence: Binance `fapi/v1/exchangeInfo` `onboardDate` + `fapi/v1/klines?interval=1d&startTime=0` first-candle open time
(live-queried 2026-08-09) for XAUUSDT/XAGUSDT/COPPERUSDT/SPYUSDT/SPXUSDT; full `exchangeInfo` symbol-list grep for
NAS100/NDX confirms none exists. Checkbox flipped in `cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 9 in the
same commit.

### 2026-08-09 — Propagation ops (B1/B3/B4) verified DONE on live prod state (`cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 1)

Dispatched via AO batch11. Re-verified the chain against LIVE production GCS state rather than launching a fresh
backfill/rollup/enumerator run, since the 2026-06-24 session already launched `instr-backfill-tradfi-20260623`
(exit_code=0) and armed the nightly schedulers (`lifecycle-catalogue-regen-tradfi` 01:00 UTC,
`expected-universe-v2-tradfi` 01:30 UTC, `instrument-catalogue-regen`) — ~6 weeks of nightly runs since then should have
already propagated the full universe.

- **Catalogue has the new MVP tickers** — downloaded
  `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet` (919,493 rows). 103 distinct
  EQUITY/ETF `base_asset`s tagged `mvp=True`, including every sampled 2026-06-24-batch addition
  (HOOD/PLTR/COIN/MSTR/ARM/ASML/RIVN/SMCI/UBER/DELL/GME/CRWD/SONY/NOK/BABA/TSM/NVO) and all 16 sampled ETF additions
  (EWT/EWY/ROBO/SLX/URNM/UVXY/GLD/IAU/SLV/PPLT/PALL/CPER/USO/UNG/IBIT/ETHA) — all `mvp=True`, correct venue
  (NASDAQ/NYSE).
- **Manifest shows them `expected_unattempted`** — downloaded
  `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` (7,022,190 rows). Every
  one of the 17 sampled tickers above shows a real `expected_unattempted` population (1,000-3,000 rows each) alongside
  `captured`/`empty_confirmed` rows — the enumerator has seeded them at the NASDAQ/NYSE:EQUITY grain as designed.
- **A sample equity capture shows non-NaN OHLCV** — downloaded
  `gs://market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2026-07-20/pipeline_mode=batch_databento/timeframe=15m/data_type=ohlcv_15m/instrument_type=EQUITY/venue=NASDAQ/NASDAQ:EQUITY:HOOD-USD.parquet`
  — 49 rows, 0 NaNs across `open/high/low/close/volume`, realistic price range ($98.63-$102.56).
- **Parity check**: the same `capture_status` distribution shape (dominated by `empty_confirmed`+`expected_unattempted`
  for low-frequency data_types like `ohlcv_24h`) holds for long-established tickers (AAPL, NVDA) as for the new
  additions (MSTR) — the new tickers are behaving identically to pre-existing ones, not showing a distinct gap.

Checkbox flipped above; `cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 1 flipped in the same commit.

### 2026-07-18 — Binance equity-perp universe WIDENED to ALL live TRADIFI_PERPETUAL listings (operator directive)

**Operator directive 2026-07-18:** "WIDEN the cefi equity-perp universe to ALL Binance equity-perp listings — get all
the Binance listings, it's recent data so not that much, we can curate it our end."

**Live pull (public, no auth):** `GET https://fapi.binance.com/fapi/v1/exchangeInfo` — 841 symbols; **139 are
`contractType=TRADIFI_PERPETUAL`** (the equity-perp surface; the other 702 are PERPETUAL/CURRENT_QUARTER/NEXT_QUARTER
with `underlyingType=COIN` = crypto). The 139 by `underlyingType`: 121 EQUITY / 8 COMMODITY / 5 HK_EQUITY / 3 KR_EQUITY
/ 2 PREMARKET (135 TRADING + 4 PENDING_TRADING); every one carries `underlyingSubType=["TradFi"]`. 138 distinct
baseAssets (SPCX has both USDT + USD1 quote variants).

**Filter used (grounded in the live field, not invented):** `contractType == "TRADIFI_PERPETUAL"` cleanly partitions
equity perps from crypto — no per-name curation needed to keep crypto out. The 3 crypto INDEX perps live today
(DEFI/BTCDOM/ALL, all `contractType=PERPETUAL`) are correctly NOT equity perps and stay out.

**Diff vs the 124-base `CEFI_EQUITY_PERP_BASE_UNIVERSE`: 20 NEW bases (124 → 144), zero collisions with the crypto
`CEFI_BASE_ASSET_UNIVERSE`:**

- **15 US EQUITY/ETF** (`underlyingType=EQUITY`): APP (AppLovin), GEV (GE Vernova), SNOW (Snowflake), VRT (Vertiv), WEN
  (Wendy's), XBI (SPDR S&P Biotech ETF), SOXS + TZA (Direxion daily 3x bear ETFs — SOXS = bear pair of the already-in
  SOXL); + 7 Binance collision-avoidance / mangled tickers whose real twin is unresolved (kept per "curate our end",
  `tracks_equity=""`): BNC, BOT, FWDI, INTW, MUU, SKHY, SNXX.
- **5 HK_EQUITY** (NEW `underlyingType` category — first time covered): HK0700 (Tencent, HKEX 0700), HK1810 (Xiaomi,
  HKEX 1810), TENCENT (Tencent named-variant baseAsset), MINIMAX + ZHIPU (Chinese-AI listings).

**Nothing excluded as non-equity** — `contractType=TRADIFI_PERPETUAL` already excludes crypto, so all 138 live bases are
equity perps by Binance's own classification; the 14 not-added were already present (the 6 "in universe but not live
today" — CFG/DIA/INX/ROBO/SLX/SPX — are the ticker-reuse names the file already flags as KEPT, left untouched).

**Symbol↔ticker mapping approach:** the base universe stores the RAW Binance `baseAsset` (matching existing entries);
`_cefi_equity_tags` maps the tokenized-spot `<TICKER>X` form via `base[:-1]` automatically. The Databento DBEQ.BASIC
real-equity twin link (`crypto_equity_link.tracks_equity`) is left UNWIRED for the 20 new bases — they tag
`is_equity_perp=True` / `tracks_equity=""` exactly like the existing standalone SPCX/OPENAI/ANTHROPIC pre-IPO perps
(honest; the basis leg needs the tradfi DBEQ universe expansion — Phase 1b — a separate follow-up). No false twin
minted.

**Coupled un-filter (Phase 2 P1) — the gate was ALREADY open:** `_passes_asset_filter` (`parsing.py:545`) has been
FULL-UNIVERSE since operator 2026-06-23 (no `CEFI_BASE_ASSET_UNIVERSE` gate on SPOT/PERP/FUTURE), so equity perps
already pass. Per the 2026-07-16 ruling the equity identity rides the tags (NOT an `EQUITY_PERP` type), stamped at
rollup by `_cefi_equity_tags` (`build_instrument_catalogue.py:775`) which imports `CEFI_EQUITY_PERP_BASE_UNIVERSE`
directly from UAC — so the UAC universe add IS the coupling; the IS catalogue stamps `is_equity_perp=True` for the new
bases automatically, no IS adapter code change needed.

**Shipped (both landed on live-defi-rollout, verified ancestor of origin/live-defi-rollout):**

- **unified-api-contracts@172e8cdb** — +20 bases in `cefi_instrument_universe.CEFI_EQUITY_PERP_BASE_UNIVERSE` (124→144)
  - docstring provenance + `test_crypto_equity_link.py::test_binance_20260718_full_listing_widen_bases_in_universe`.
    QG-green (`quality-gates.sh --no-fix`, 284s, ALL PASSED).
- **instruments-service@ff6d9750** — coupled tests: `test_cefi_equity_tags_classifier` asserts APP/GEV/SNOW/XBI/TENCENT/
  ZHIPU (+ SNOWX tokenized-spot) tag `is_equity_perp`; `test_passes_asset_filter_binance_equity_perp_base` asserts
  APP/TENCENT resolve/pass the CeFi filter. QG-green (123s, ALL PASSED). Shipped with `--skip-preflight` (dirty-deps
  carve-out: UTL + UAC carried live foreign `fold_a_cutover` WIP that isn't mine — only my named files committed).

**Out of scope (unchanged):** Phase 2 P1 sub-item 4 (launch the Tardis backfill) — operator: no MTDS backfill / prod
mutation this task. This is catalogue/universe definition only.

### 2026-07-16 — broad `instrument_type` + `is_equity_perp`/`tracks_equity` tags (operator ruling; WS-H double-seed fix)

**Operator ruling** (verbatim in the Architecture-decision banner above): equity-perp typing reverts to the BROAD
mechanics type; the equity identity moves to catalogue tags. **Implemented (root-cause, cross-repo):**

- **instruments-service** `scripts/build_instrument_catalogue.py`: replaced `_refine_cefi_instrument_type`
  (PERPETUAL→EQUITY_PERP / SPOT_PAIR→TOKENIZED_EQUITY re-typing) with
  `_cefi_equity_tags(instrument_type, base_asset) -> (is_equity_perp, tracks_equity)`; `instrument_type` is now left as
  the raw broad type at roll-up. Added two `CATALOG_COLUMNS` (`tracks_equity`, `is_equity_perp`) stamped by a new
  `_add_equity_tags` finalization step (mirrors `_add_mvp_column`; re-derived every full + incremental run, excluded
  from the incremental merge `out_columns`). Removed `EQUITY_PERP`/`TOKENIZED_EQUITY` from `_PERP_FAMILY_ITYPES`
  (PERPETUAL stays; equity perps already ride it).
- **unified-api-contracts**: removed `EQUITY_PERP`/`TOKENIZED_EQUITY` from `CeFiMvpRule.instrument_types` (equity perps
  MVP-gate as `PERPETUAL`; bases already unioned into `base_ccys`). Enum members kept DEPRECATED-but-defined
  (`_instrument_enums.py` comment) after a full consumer sweep found string/enum consumers + persisted catalogue rows
  needing them parseable; the `ledger_asset_resolution` map entries retained (kept complete over the enum). Updated
  `_mvp_scope_capture.py` comments.
- **Tests**: `test_mvp_scope.py`, `test_crypto_equity_link.py`, and the IS catalogue tests updated to assert the NEW
  behavior (equity perps are `PERPETUAL` + tagged `is_equity_perp`/`tracks_equity`; NVDA/META/AAPL populate
  `tracks_equity`). **Codex**: `/codex/02-data/cefi-capture-universe.md` updated.
- **Effect**: catalogue `instrument_type` == manifest `instrument_type` (`PERPETUAL`) → the **WS-H double-seed blocker
  is resolved** (denominator reconciles). Prod catalogue re-stamped via the `--mode full` rebuild.

### 2026-06-24 — KRX venue close-out + Yahoo guardrail + centralised venue/source/MVP parity gate (IN PROGRESS)

**Goal:** close the last 3 BLOCKED-DATA (HYUNDAI/SAMSUNG/SKHYNIX) via Yahoo (KRX exchange), making the tradfi-perp
superset 103/103; bake a general Yahoo granularity/lookback guardrail; register KRX as a new tradfi venue end-to-end;
add a CENTRALISED data-driven parity gate so a half-wired venue/source/adapter/MVP-cell RED-fails (general future
guard).

**KRX tickers + venue (verified):** Samsung `005930.KS`, SK Hynix `000660.KS`, Hyundai `005380.KS` (Yahoo `.KS` suffix =
KOSPI/Korea Exchange). Canonical venue code = **KRX** (operator's "Cosby"=KOSPI/KRX). Source = `yahoo` (a DATA SOURCE,
not a venue).

**Yahoo limits — PROBED LIVE 2026-06-24 (005930.KS):** `1m` max ~7d/request, chunked via period1/period2 reaches back
**~28 days** (back 21-28d OK → 2026-05-28; back 28-35d → HTTP 422); `15m` `range=60d` returns ~89d (60d floor); `1h`
`range=730d` OK; `1d` `range=max` full history (2000→). **Guardrail clamps:** 1m>28d, 15m>60d, 1h>730d, 1d unbounded → a
beyond-limit request must raise/clamp, never silently empty.

**Plan (phases):** (1) Yahoo adapter guardrail (`market-tick-data-service/.../_umi_yahoo.py`) + QG unit test that a
too-old/too-fine request is rejected + asserted consulted-on-fetch-path. (2) KRX venue registration across IS-registry +
MTDS venue→source routing (→yahoo) + manifest venue set + UAC universe + deployment-api/ui if they enumerate venues
(mirror NYSE). (3) UAC universe: 3 KRX stocks (venue=KRX, source=yahoo) + MVP basis carve-out → 103/103. (4) Backfill
via guardrailed Yahoo adapter (15m/60d + 1m/28d-chunked; FX→yahoo wave precedent). (5) IS catalogue/aggregation: VERIFY
full-venue-enumeration re-run preserves NYSE/NASDAQ old+new (NOT a 3-stock clobber) + fresh KRX shard; additive (don't
disrupt running VMs). (6) CENTRALISED parity gate (UAC contract test + check\__ in base-_.sh): iterate ALL
venues/sources/adapters/MVP-cells → every venue in IS-registry+MTDS-routing+manifest+source-map; every (venue,data_type)
in MVP → declared source + adapter supporting that data_type+granularity; every source → adapter resolves; guardrail
enforced on fetch path. Parametrised → auto-covers future + AUDITS existing (surface pre-existing half-wired; fix small,
issue-doc big). KRX = first consumer that passes it. PROVE: a deliberately-incomplete KRX (removed from MTDS routing)
RED-fails a named assertion.

### 2026-06-24 — CME futures + options-on-futures for commodity/index basis underlyings

**Scope: commodities + indices ONLY** (single-stock options SKIPPED — too many; equity/ETF options are OPRA, NOT in our
3-dataset databento allowlist [GLBX.MDP3 + DBEQ.BASIC + XCBF.PITCH] nor massive → IGNORED). uac@817f7424.

**(a) FUTURES — all present, none missing.** GC/SI/PL/PA/HG/CL/NG (+ HO/RB) commodities + ES/NQ/RTY/YM indices already
enumerated in `_CME_COMMODITY_FUTURES` / `_CME_INDEX_FUTURES`.

**(b) OPTIONS — PROBED LIVE in GLBX.MDP3 (definition + trades), phantoms DROPPED.** Added `_CME_COMMODITY_OPTIONS` +
`_CME_INDEX_OPTIONS` (10 roots, all source=databento GLBX.MDP3 primary — massive carries no options-on-futures):

| underlying       | future root (have) | option root (added)   | databento evidence       |
| ---------------- | ------------------ | --------------------- | ------------------------ |
| gold (GC)        | GC.FUT             | **OG.OPT**            | def 39476 / trades 5031  |
| silver (SI)      | SI.FUT             | **SO.OPT**            | def 23140 / trades 2036  |
| platinum (PL)    | PL.FUT             | **PO.OPT**            | def 7735                 |
| palladium (PA)   | PA.FUT             | **PAO.OPT**           | def 5309                 |
| copper (HG)      | HG.FUT             | **HXE.OPT**           | def 6206                 |
| crude/WTI (CL)   | CL.FUT             | **LO.OPT**            | def 30711 / trades 10989 |
| natgas (NG)      | NG.FUT             | **ON.OPT**            | def 2905                 |
| heating oil (HO) | HO.FUT             | **OH.OPT**            | def 10248                |
| RBOB (RB)        | RB.FUT             | **OB.OPT**            | def 9114                 |
| Nasdaq-100 (NQ)  | NQ.FUT             | **NQ.OPT**            | def 4606 / trades 1939   |
| S&P (ES)         | ES.FUT             | ES.OPT (pre-existing) | def 8486                 |

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

**(B1/B3/B4) Propagation ops — IN PROGRESS.** Chain wired: IS instruments backfill → catalogue rollup (mvp tag) →
`enumerate_expected_universe v2 tradfi` (seeds expected_unattempted per-instrument from the catalogue) → MTDS wave.
Verified new equities NOT yet in instruments-store. Triggered `code-tarball-refresh` (now IS f670bd4 + UAC mvp).
**Launched** `instr-backfill-tradfi-20260623` (e2-standard-4, asia-northeast1-c, RUNNING) scoped TRADFI
2026-06-10→2026-06-23 to establish new equity InstrumentRecords; monitor armed (exit_code + log-mtime + manifest-climb).
**Live nightly schedulers auto-propagate:** `lifecycle-catalogue-regen-tradfi` (01:00 UTC) +
`expected-universe-v2-tradfi` (01:30 UTC) + `instrument-catalogue-regen`, all from the daily tarball. **Next
(post-backfill verify):** trigger catalogue-regen-tradfi → new tickers present + mvp=True; trigger
expected-universe-v2-tradfi → NASDAQ/NYSE:EQUITY:<ticker> = expected_unattempted; confirm a sample equity OHLCV captures
via MTDS wave.

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

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - dominated by `[DESIGN]`/`[RESEARCH]`
  archetype + hedge-venue + universe-construction calls, plus a BLOCKED-DATA Korea-equity vendor ask.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: re-verified context_scope, no change needed (6 entries) -- both source paths
  (`crypto_equity_link.py`, the tardis parsing adapter) plus the KRX-equity-twin precedent issue doc still match this
  plan's live BLOCKED-DATA item; codex SSOTs for cefi capture + tradfi sourcing remain correct.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid — 22 open items are dominated by
  open-ended strategy-archetype/hedge-venue/universe-construction [DESIGN]/[RESEARCH] calls, not bounded deterministic
  work.
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — 15 open items, majority genuine
  strategy-design/research work or explicitly flagged as needing their own scoped build plan before AO dispatch. 7 items
  flagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE as future-extraction candidates (mirrors this doc's own 2026-08-09 extraction
  pattern for 4 other items), not enough to flip the whole doc.

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
- [x] ✅ [SCRIPT] P0. **Propagation ops (B1/B3/B4) — run on real infra to completion.** The code (above) is the enabler;
      the chain is wired: (1) IS instruments backfill (`launch-instruments-backfill-vm.sh --asset-group TRADFI`) writes
      per-day InstrumentRecords for the new equities (databento/massive now fetch them) → (2)
      `build_instrument_     catalogue` rolls up + tags `mvp=True` → (3) `enumerate_expected_universe.py` v2 tradfi
      enumerator reads the catalogue, seeds the new equities as `expected_unattempted` at venue=NASDAQ/NYSE grain → (4)
      MTDS wave-launcher reads the manifest `expected_unattempted` gaps + captures. **Run + verify**: catalogue has new
      MVP tickers; manifest shows them `expected_unattempted`; a sample equity captures non-NaN OHLCV. Repo:
      deployment-service (launchers) + instruments-service (catalogue/enumerator CLIs). **DONE — verified live
      2026-08-09** (`cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 1). The live nightly schedulers
      (`lifecycle-catalogue-regen-tradfi`, `expected-universe-v2-tradfi`, `instrument-catalogue-regen`) armed 2026-06-24
      have run to completion in the ~6 weeks since — no fresh backfill/rollup/enumerator run was needed; verification
      read prod state directly. See Progress Log for the full evidence.
- [x] ✅ [DATA] P2. ~~**BLOCKED-DATA** — HYUNDAI / SAMSUNG / SK Hynix (3 Binance tradfi-perps with NO US-listed twin,
      KRX primary): source a Korea-equity reference + tick vendor so the cash-equity twin exists for basis (databento
      DBEQ.BASIC is US-only). Until sourced these perps have a dispersion-only (cross-crypto-venue) leg, no cash hedge.
      Repo: instruments-service (vendor ask → operator). **DEFERRED** — needs an operator credential/vendor decision
      (Korea equities).~~ **CLOSED — na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep), stale item.** This doc's
      own Progress Log already records the resolution: **RULED 2026-08-07 (operator, interactive session — source:
      `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Progress Log, 2026-08-07 entry)**: no dedicated
      Korea-equity tick vendor — "daily from yahoo finance is enough." Accept reduced fidelity for these 3 basis-arb
      cash-twin legs specifically — use the already-live KRX-venue Yahoo daily OHLCV coverage
      (`unified-api-contracts@844c5ee6b` + `instruments-service@1ba5da4b`, Phase 5) as the cash UNDERLYING reference at
      daily (not tick) resolution. This checkbox was simply never flipped when that ruling landed. The "Deferred work —
      migrated to" section's note below (pre-dating the 2026-08-07 ruling) is correspondingly superseded — the
      basis-execution cash-twin need it describes as "still open" is now closed at daily resolution, not still needing a
      fresh operator ask.
- [ ] [SCRIPT] P1. market-tick-data-service — capture Binance/OKX/Bybit `indexPrice` + `markPrice` + `fundingRate` for
      the equity-perps as a first-class data_type (the venue's DISCLOSED mark — needed for basis = mark−index and for
      OFF-HOURS synthetic-mark detection where the cash tape is closed). These ride the existing CeFi
      premiumIndex/funding endpoints. Repo: market-tick-data-service.
- [ ] [SCRIPT] P2. e2e-testing — recurring DAILY funding/basis scan across all crypto-venue equity-perps (annualized
      funding + perp-vs-index basis + flag market-hours vs off-hours) → opportunity-sizing report. Wire as a scheduled
      job (mirror an existing scan). Repo: e2e-testing.
- [x] ✅ [DESIGN] P2. strategy-service — single-stock basis execution-venue gap: CME has index futures (ES/NQ for
      SPX/NDX basis) but NOT broad single-stock futures → the long-cash leg for NVDA/MSTR/etc needs IBKR (equities) OR a
      second tokenized/perp venue OR pure cross-crypto-venue basis. Decide per-symbol hedge venue; off-hours =
      no-cash-hedge (dispersion-only or unhedged-funding-capture with risk limits). Repo: strategy-service. **RESOLVED —
      this question was independently answered later the same day in Phase 1d's NET-basis backtest** (§ "Single stocks
      hedged with the ACTUAL stock (IBKR)... CLEANER net than the futures-hedged index/commodity, at the cost of the
      equities-venue gap"; result line: "hedge=IBKR stock borrow wins for all singles (no CME single-stock futures for
      US equities)"). **APPROVED (operator, 2026-08-08)**: "Approve, build it" — confirms IBKR cash-stock as the
      per-symbol hedge venue for all 12 (now more, per Phase 1f) single-stock basis pairs; off-hours stays no-cash-hedge
      per the original design. No further per-symbol venue decision needed; the open work is the IBKR adapter BUILD
      itself (Phase 1e todo below).

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

- [ ] [BACKEND] P0. execution-service — **IBKR equities execution adapter is the GATING unlock**: the winning
      single-stock basis (NET +5–24%) needs the long CASH-stock leg on IBKR (`ibkr-gateway-infra`); the short perp is
      already executable (cefi). Without IBKR equities, none of the 12 winners are tradeable. Wire IBKR equities (not
      just the existing index/futures path). Repo: execution-service + ibkr-gateway-infra. **APPROVED (operator,
      2026-08-08)**: "Approve, build it" — retagged `[DESIGN]`→`[BACKEND]` (the design question — whether to build this
      adapter — is resolved; what remains is the build itself). Genuinely multi-day, cross-repo build (new
      execution-service adapter + `ibkr-gateway-infra` wiring); not a single-worker bounded-outcome task, so
      `assigned_vm` stays `NA` pending its own scoped build plan rather than blind AO dispatch on this umbrella doc.
- [x] ✅ [RESEARCH] P1. **DONE 2026-08-09 — `unified-api-contracts@89de6766`** (batch11 todo 7). Check
      OKX/Bybit/Hyperliquid for a WTI/Brent oil perp; add if found. Repo: instruments-service. Live-queried all 4
      venues' listing endpoints: **FOUND** on OKX (`CL-USDT-SWAP` WTI since 2026-03-04, `BZ-USDT-SWAP` Brent since
      2026-03-24 — ICE data-partnership index) and Bybit (`CLUSDT`, `BZUSDT`); **NOT FOUND** on Hyperliquid (no
      commodity perps at all today). `CL`/`BZ` were already members of `CEFI_EQUITY_PERP_BASE_UNIVERSE`, so no
      universe-membership change was needed. Recorded the per-venue found/not-found result with cited evidence in new
      module `oil_perp_venue_coverage.py` + 13 unit tests. `quality-gates.sh` green (381s).
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

- [ ] [BACKEND] P0. strategy-service + UAC — replace the fixed net-profitable-12 with: (a) BROAD universe = top-N US
      stocks by market cap ∪ top-N crypto-venue equity-perps by OI/volume; (b) a DYNAMIC live-net-carry ranking that
      selects the tradeable set each rebalance (avoids look-ahead/survivorship). Repo: unified-api-contracts
      (universe) + strategy-service (ranking). **APPROVED (operator, 2026-08-08)**: "Approve, build it" — retagged
      `[DESIGN]`→`[BACKEND]`. Genuinely multi-repo build (UAC universe schema + strategy-service ranking logic); not a
      single-worker bounded-outcome task, so `assigned_vm` stays `NA` pending its own scoped build plan.
- [x] ✅ [SCRIPT] P1. **DONE 2026-08-09 — `e2e-testing@12d1f3c`** (batch11 todo 8). Re-run the NET-basis backtest with
      dividends priced into the long cash-stock leg, all 12 pairs. Repo: e2e-testing. Full table: this doc's Progress
      Log, "NET-basis backtest re-run with dividend yield" entry above. Result: all 12 remain TRADEABLE, NET +0.00 to
      +0.82pp vs. the 06-20 floor.
- [x] ✅ [RESEARCH] P1. **DONE 2026-08-09** (batch11 todo 9, read-only research, no code shipped). Check Binance perp
      listing/history length per NET-negative/-slim symbol against known regime shifts, to determine whether the
      net-negative verdict is regime-conditional. Repo: instruments-service. Full table: this doc's Progress Log, "Todo
      9" entry below.
- [ ] [DESIGN] P2. strategy-service — note: XAU (gold) perp is the deepest non-crypto leg ($327M) → if gold carry flips
      to backwardation (or for non-basis gold strategies), it's the most size-able crypto-venue commodity. Repo:
      strategy-service.

## Deferred work — migrated to:

**`plans/archive/issues/krx_equity_twin_no_source_2026_06_28.md`** — the identical KRX-equity-twin sourcing question (SK
Hynix/Hyundai Motor/Samsung, no Databento KRX dataset, no launcher) was already raised and operator-decided 2026-06-28:
Option C (reclassify as `EXPECTED_SOURCE_NOT_AVAILABLE` honest-empty) was chosen over sourcing a vendor/adapter, which
closed the tradfi manifest-completeness gate (KRX eu 378→0) but did NOT acquire a real cash-hedge feed. This plan's
`[DATA] P2` **BLOCKED-DATA** item is a different, still-open need (a live cash-equity twin for crypto-perp BASIS
execution, not manifest completeness) — the cited issue doc is the closest precedent ruling (operator declined to source
a vendor at that time), not a code successor; a fresh operator ask is needed if the basis trade is prioritized.
**SUPERSEDED — na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: the "different, still-open need" this note
describes was itself resolved 2026-08-07 (see the checkbox above and the Progress Log entry dated 2026-08-07) — the
basis-execution cash-twin need is now closed at daily Yahoo resolution, accepted by the operator as a reduced-fidelity
answer rather than a paid tick vendor. This note is kept for historical record, not as an open pointer.

- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid overall — of the 21 remaining open
  items, at least 11 are genuine `[DESIGN]`/`[RESEARCH]` strategy-archetype, hedge-venue, and universe-construction
  judgment calls (confirmed independently by today's `cefi_satellite_ao_dispatch_batch10_2026_08_08.md` audit, which
  reached the same 11/22 figure), including a 2026-08-08-dated item explicitly re-affirmed `assigned_vm: NA` in-doc
  ("not a single-worker bounded-outcome task... pending its own scoped build plan"). Whole-doc flip is blocked per the
  HARD RULE. Closed 1 stale item (the KRX BLOCKED-DATA checkbox, above) with evidence from this doc's own recorded
  2026-08-07 ruling.
- **batch11-finalize 2026-08-09 (slot-17, review)**: batch11's todos 6-9 (this doc's 4 EXTRACTED items) all landed DONE
  — pointers above replaced with real evidence (SHAs verified reachable on origin), 1 mislabeled Progress Log header
  fixed (todo 8's entry was headed "todo 6"). **Doc-wide open count: 15/36, unchanged** (already checked at
  batch11-drafting; this pass only added evidence) — see the 2026-08-08 audit entry above for the breakdown.

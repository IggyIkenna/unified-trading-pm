---
doc_type: plan
title: CeFi satellite AO batch 11 — item-level extraction from 19 non-qualifying NA docs (cefi_master group)
summary: >-
  Eleventh AO-dispatch batch for cefi. Produced by a per-item satellite-extraction pass over the 19 cefi-tranche
  `assigned_vm: NA` docs that a same-day RECLASSIFY sweep read end-to-end but did NOT whole-doc-flip (each carries at
  least one genuine judgment/design/operator-gated item). Mirrors `/ag-closeout-audit`'s carve-out pattern but applied
  per-item rather than per-doc: 4 parallel research passes (one per doc-group) classified every open item in all 19 docs
  against the bounded-outcome bar (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` §5), found 16
  genuinely extractable items total, grouped by `parent_epic` per
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §2. This batch is the `parent_epic:
  cefi_master` group (10 items, 3 source docs) — sibling batches 12/13/14 (dated the same day) cover the
  `infrastructure_master`/`strategy_master`/`execution_master` groups respectively. Every item was independently
  spot-verified against live code/doc state (not just trusted from the research pass) before inclusion — see the
  Progress Log for the specific verification notes, including one item (todo 5, Barchart removal) that was
  conflict-checked against several TradFi docs mentioning "Barchart" and confirmed non-duplicative (those docs track
  data/manifest state, none claims the literal code-deletion this todo performs).
status: complete
nature: process
asset_group: [cefi]
stage: [data]
repos:
  [
    unified-trading-pm,
    instruments-service,
    deployment-service,
    market-tick-data-service,
    unified-api-contracts,
    e2e-testing,
  ]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-11, satellite-docs, item-level-extraction, na-audit]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
    /plans/active/cefi_ml_directional_continuous_live_2026_06_20.md,
    /plans/active/cefi_satellite_ao_dispatch_batch10_2026_08_08.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch12_2026_08_09.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch13_2026_08_09.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch14_2026_08_09.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Item-level satellite-extraction pass 2026-08-09 over the 19-doc cefi RECLASSIFY-sweep-non-qualifying candidate list,
  mirroring `/ag-closeout-audit`'s carve-out pattern applied per-item. 4 parallel general-purpose research agents each
  read a subset of the 19 docs end-to-end (including dated Progress Log sections), classified every open item against
  the bounded-outcome bar, and drafted candidate todos; the main session then independently spot-verified the
  highest-stakes items (code reads, line-number checks, conflict greps across the active-plan corpus) before drafting
  this doc. Full per-item classification detail (all 19 docs, EXTRACTABLE/STAYS-BEHIND with reasons) is retained in the
  4 research agents' transcripts, not duplicated here.
context_scope:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_satellite_ao_dispatch_batch10_2026_08_08.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
---

# CeFi satellite AO batch 11 — item-level extraction (cefi_master group)

> **🟢 ARCHIVED 2026-08-09 — COMPLETE.** All 10 todos shipped/measured with real evidence (see Progress Log), reconciled
> against their 3 source docs (`cefi_consolidated_closeout_2026_07_18.md`,
> `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`, `cefi_ml_directional_continuous_live_2026_06_20.md`)
> and independently re-verified by finalize-plan todos 1-2. Archived per the 6-step ritual
> (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`); a codex staleness found in the process —
> `/codex/02-data/tradfi-databento-sourcing-ssot.md`'s Databento lookback-floor table cited the pre-todo-4 conservative
> constants — was corrected to the measured values in the same session. Finalize plan
> `cefi_satellite_ao_dispatch_batch11_2026_08_09_finalize.md` (source-doc reconciliation + this archival) completed and
> archived alongside this doc. One deferred item (deployment-ui Barchart-label spot-check, never checked) migrated to a
> tracked todo before archival: `/plans/archive/2026_08/deployment_ui_barchart_label_spotcheck_2026_08_09.md`.
> Successor: none.
>
> **Status: ACTIVE (historical).** Conflict-checked against the live corpus 2026-08-09 (see Progress Log) — no overlap
> found with any other active `assigned_vm: planning` plan in `parent_epic: cefi_master`,
> `cefi_satellite_ao_dispatch_batch9/10`, or `cefi_consolidated_closeout_2026_07_18.md`'s own content (todos 1-5 below
> ARE `cefi_consolidated_closeout`'s Track 0 items, extracted from there directly — its checkbox is being replaced with
> a pointer to this doc in the same commit as this file). **Cross-todo file-collision check**: todos 1/3/7/8/9/10 are
> operational runs/audits with no durable code-file target (or a conditional one, only touched if the audit finds
> something); todo 2 targets `unified-api-contracts`' index-perp canonical-mapping registry; todo 4 targets
> `unified-api-contracts`' L-floor lookback constants (a different module from todo 2); todo 5 deletes Barchart
> adapter/client files in `unified-api-contracts` + `market-tick-data-service` (no overlap with todo 2/4's files); todo
> 6 extends `market-tick-data-service`'s live-book connectors (different code path from todo 5's deletion). No file is
> edited by more than one todo.

## Todos

- [x] ✅ [SCRIPT] P0. **Run the IS→catalogue→enumerator→MTDS propagation-ops wave chain (B1/B3/B4) to completion** for
      the new Binance tradfi-perp cash-twin equities: instruments-service backfill → `build_instrument_catalogue` rollup
      → `enumerate_expected_universe.py` v2 tradfi → MTDS wave. Repos: deployment-service, instruments-service. Source:
      `cefi_consolidated_closeout_2026_07_18.md` Track 0 (line 136, cites source Phase 1b). **Done when**: the catalogue
      shows the new MVP tickers, the manifest shows them `expected_unattempted`, and a sample equity capture shows
      non-NaN OHLCV. **DONE 2026-08-09** — verified live against prod GCS state (the 2026-06-24-launched
      `instr-backfill-tradfi-20260623` backfill + nightly schedulers already propagated the chain over the past ~6
      weeks, no new run needed): catalogue has 103 mvp-tagged equity/ETF base_assets incl. every sampled new ticker;
      manifest shows `expected_unattempted` for every sampled ticker; `NASDAQ:EQUITY:HOOD-USD` 2026-07-20 `ohlcv_15m`
      sample = 49 rows, 0 NaN OHLCV. Full evidence: `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`
      Progress Log, 2026-08-09 entry.
- [x] ✅ [UAC] P0. **Map the index perps** (`SPXUSDT`/`NAS100`/`SPYUSDT`/`XAUUSDT`) to their CME index-future +
      Databento index canonical equivalents in unified-api-contracts, carrying the scale/multiplier (Binance SPX-perp is
      a SCALED micro unit — sizing MUST use the multiplier for the ES hedge ratio). Repo: unified-api-contracts. Source:
      `cefi_consolidated_closeout_2026_07_18.md` Track 0 (line 158, cites source Phase 1c). **Done when**: all 4 index
      perps have a canonical mapping + multiplier committed, `quality-gates.sh` green. — **DONE 2026-08-09** —
      unified-api-contracts@e973c62d: new `canonical/crosscutting/index_commodity_perp_hedge_link.py`
      (`INDEX_COMMODITY_PERP_HEDGE_LINK` dict + `hedge_link_for()` resolver, mirrors `crypto_equity_link.py`'s shape),
      wired into the package `__init__.py`, 12 new unit tests in `tests/unit/test_index_commodity_perp_hedge_link.py`.
      `quality-gates.sh` green (basedpyright/ruff/tests all pass). **2 of the 4 requested symbols were stale, corrected
      with live evidence (Binance `fapi/v1/exchangeInfo`, 2026-08-09)**: `SPXUSDT` is now the `SPX6900` meme coin
      (`underlyingType=COIN`, `underlyingSubType=['Meme']`) — no longer tracks the S&P 500 (confirms, not just repeats,
      the existing caveat already in `cefi_instrument_universe.py`); no `NAS100`/`NAS100USDT` symbol exists on Binance
      at all. Shipped mapping: `SPY→ES` ($50/pt, S&P500), `QQQ→NQ` ($20/pt, Nasdaq-100 — substitute for the nonexistent
      NAS100), `XAU→GC` (100 troy oz, Gold); `SPX`/`NAS100` recorded in `EXCLUDED_INDEX_COMMODITY_PERP_BASES` with the
      evidenced reason (mirrors the "found/not-found, cite the evidence" pattern this batch's todo 7 already uses)
      rather than silently mapped or silently dropped. `contract_size` values are published static CME contract specs,
      not a live-computed hedge ratio (that stays in strategy-service). Hedge-root exchange/dataset/underlying resolved
      via the existing `TRADFI_ROOTS` SSOT (`canonical/domain/derivatives/tradfi_roots.py`), not duplicated.
- [x] ✅ [SCRIPT] P1. **Backfill the 3 KRX stocks** (HYUNDAI/SAMSUNG/SK-Hynix cash-twins) **via guardrailed Yahoo**: 1d
      since 2019-01-01 + 1h trailing 730d + 15m trailing 89d (range=60d) + 1m 28-day-chunked. Repos: deployment-service,
      market-tick-data-service. Source: `cefi_consolidated_closeout_2026_07_18.md` Track 0 (line 168, cites source Phase
      5). **Done when**: the manifest shows captured, non-NaN rows for all 4 windows across all 3 symbols. —
      **NARROWED + DONE 2026-08-09** — the 1h/15m/1m legs directly conflict with a RESOLVED, still-live operator
      decision this todo's source predates:
      `/plans/archive/issues/krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md` (2026-07-12, "Yahoo doesn't
      reliably serve intraday granularity over long historical backfill windows, so build-the-adapter was rejected" —
      `unified-api-contracts@a2751f36` narrowed `expected_coverage.py`'s KRX entry to `["ohlcv_24h"]`; confirmed still
      true in live code 2026-08-09, `route_yahoo_tradfi`/`fetch_yahoo_equities` have no KRX intraday path by design).
      batch11's own conflict-check only grepped `plans/active/`, missing this archived, governing decision. The
      achievable 1d/`ohlcv_24h` leg is verified ~98% complete since 2019-01-02 across all 3 symbols (2943 captured /
      ~2997 total canonical-instrument-id shards), spot-checked against a REAL GCS parquet object (not just the manifest
      label — its `row_count` field is separately bugged, see below):
      `.../day=2020-01-06/.../venue=KRX/.../KRX:EQUITY:005930-USD.parquet` → 1 non-NaN row (open=47801.95,
      close=47887.77, volume=10009778). Remaining 42 unattempted + 12 attempted_failed are all within 2026-08-03..08-06
      (recent-date Yahoo publication lag, not a structural gap). 2 adjacent, non-blocking manifest-integrity defects
      found + filed as follow-up todos in the same issue doc: (1) `row_count=0` wrongly recorded on most `captured` KRX
      ohlcv_24h shards despite real underlying data; (2) an orphaned, non-canonical `KRX:EQUITY:{code}.KS-USD` duplicate
      shard-atom (~8261 rows, 0 real captures) alongside the canonical `KRX:EQUITY:{code}-USD` form. Full evidence: see
      the issue doc's Progress Log.
- [x] ✅ [UAC] P1. **Measure the exact Databento lookback-floor boundary per level** (L0/L1/L2/L3) live and update
      `LEVEL_MAX_LOOKBACK_DAYS`/`earliest_allowed_start`/`assert_lookback_allowed` in unified-api-contracts to the
      measured values. Repo: unified-api-contracts. Source: `cefi_consolidated_closeout_2026_07_18.md` Track 0 (line
      170, cites source Phase 5). **Done when**: each level's floor is measured and the 3 named constants/functions
      match the measured values, `quality-gates.sh` green. — **DONE 2026-08-09** — unified-api-contracts@92a418e5.
      Binary-searched `metadata.get_cost` live on GLBX.MDP3/ES.c.0 (a cost-estimate endpoint — no data fetched, no
      billing risk) to find the exact free/metered transition per level: **L1 (trades) 367d free / 368d metered** (was
      conservative 365d), **L2 (mbp-10) 33d free / 34d metered** (was conservative 30d), **L3 (mbo) 33d free / 34d
      metered** (was conservative 30d) — L1's boundary cross-checked identical on DBEQ.BASIC/AAPL, confirming the
      boundary is level-scoped not dataset-scoped. **L0 has no rolling metered boundary at all**: probed 5850d-5908d
      back, every point $0.0000, then 5909d+ raises a hard 422 `data_start_before_available_start` (GLBX.MDP3's own
      archive starts 2010-06-06) — never a metered charge; `_FULL_HISTORY_DAYS` updated from the arbitrary `16*365`
      approximation to the measured 5908d (exact distance from 2026-08-09 to GLBX.MDP3's inception, the oldest of the 3
      subscribed datasets, so it's the widest value safe for all three). `LEVEL_MAX_LOOKBACK_DAYS` + module/inline
      docstrings updated to the measured values; test boundary assertions
      (`tests/unit/test_databento_subscription_allowlist.py`) updated to match (366d/31d no longer raise — they're now
      within the true free window). `quality-gates.sh` green (336s, 0 basedpyright errors, tests pass).
- [x] ✅ [REFACTOR] P2. **Deprecate and remove all Barchart code** (superseded by VX-futures-via-Databento for the VIX
      preload; CLAUDE.md: "VIX=VX-futures via XCBF.PITCH, Barchart RETIRED"): delete the adapter/client/source-registry
      entries in unified-api-contracts and market-tick-data-service, no shim. **Conflict-checked 2026-08-09**: grepped
      "Barchart" across the full active-plan corpus — several TradFi docs (`tradfi_registry_coverage_and_ao_readiness`,
      `tradfi_manifest_content_recovery_completion`, `tradfi_sp500_ml_and_arb_backtest_readiness`,
      `instruments_tradfi_g1_g5_gate_execution`) reference Barchart as an already-retired DATA source in
      manifest/docstring contexts — none claims the literal adapter-code deletion this todo performs; no conflict.
      Repos: unified-api-contracts, market-tick-data-service. Source: `cefi_consolidated_closeout_2026_07_18.md` Track 0
      (line 173, cites source Phase 5). **Done when**: no Barchart code/test references remain in either repo,
      `quality-gates.sh` green. **DONE 2026-08-09** — unified-api-contracts@fc1b4897, market-tick-data-service@aea655a9.
      See Progress Log for full deletion list + scope boundary.
- [x] ✅ [DATA] P2. **Extend market-tick-data-service's existing CeFi live-ws order-book connectors to also record live
      BBO+depth for the crypto-venue equity-perp instruments** (Binance/OKX/Bybit), for basis-arb slippage calibration.
      Repo: market-tick-data-service. Source: `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` line 175.
      **Done when**: live BBO+depth is captured and persisted for at least one equity-perp instrument per venue,
      mirroring the existing non-equity-perp live-book capture shape, `quality-gates.sh` green. — **DONE 2026-08-09 — NO
      CODE CHANGE NEEDED, live-verified**. Read every layer of the capture path
      (`binance_futures_book_ticker_ws.py`/`okx_futures_book_ticker_ws.py`/`bybit_futures_book_ticker_ws.py`'s
      `book_snapshot_5` connectors, `derive_base_token`/`derive_settlement_dimensions` (`tardis_margin_marker.py`), the
      OKX/Bybit canonical-id builders, and `LiveWebsocketRunner._resolve_is_universe`): all are symbol-generic (string
      suffix/prefix stripping, no crypto-only whitelist), and `AAPL` etc. are already unioned into
      `CEFI_EQUITY_PERP_BASE_UNIVERSE` → MVP scope (`_mvp_scope_rules.py`) → IS catalogue as ordinary `PERPETUAL` rows,
      so the existing connectors already cover equity-perp bases with zero special-casing. Proved this live rather than
      trusting the read: real-queried `fapi/v1/exchangeInfo` (Binance)/`public/instruments?instType=SWAP`
      (OKX)/`v5/market/instruments-info?category=linear` (Bybit) to confirm `AAPL` is actively trading on all 3 venues,
      then ran the real `--mode live --operation websocket-streaming --shard-spec cefi:<VENUE>:book_snapshot_5` CLI
      (IS_TEST_RUN=true, test-bucket-routed — the sanctioned "bounded, test-bucket-routed live smoke check" pattern the
      CLI's own `--max-duration-seconds` help text documents) against an ephemeral local Redis
      (`docker run redis:7-alpine`, only needed for the boundary-event publisher; torn down after), for real
      real-money-free live BBO+depth capture of `AAPL-USDT`/`AAPL-USDT-SWAP` for ~20-25s per venue. **Result — all 3
      venues wrote a genuine `captured` manifest row to `market-data-tick-cefi-test-central-element-323112`'s
      `_index/availability_index.parquet`**: `BINANCE-FUTURES:PERPETUAL:AAPL-USDT@LIN` row_count=13,
      `OKX-SWAP:PERPETUAL:AAPL-USDT` row_count=9, `BYBIT:PERPETUAL:AAPL-USDT@LIN` row_count=18 — all
      `capture_status=captured`, `pipeline_mode=live_{binance,okx,bybit}`, written 2026-08-09T13:23-13:28 UTC, identical
      shard-atom/manifest shape to any non-equity-perp live book_snapshot_5 capture. No
      connector/base-universe/IS-resolution code changed (none was needed); `market-tick-data-service` worktree stayed
      clean — `quality-gates.sh` N/A (no diff to gate).
- [x] ✅ [DATA] P1. **Query OKX/Bybit/Hyperliquid's public instrument-listing endpoints for a WTI or Brent crude-oil
      perpetual contract**; if one exists, add it to the CeFi instrument universe (unified-api-contracts) mirroring how
      the existing commodity perps (XAU/XAG/COPPER) are registered. Repo: unified-api-contracts. Source:
      `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` line 795. **Done when**: the check result
      (found/not-found, per venue) is recorded; if found, the new perp is added with a passing unit test; if not found,
      the todo closes citing the negative-result evidence (endpoint responses showing no oil-perp symbol). — **DONE
      2026-08-09** — unified-api-contracts@89de6766. Live-queried all 4 venues' public instrument-listing endpoints:
      **FOUND** on OKX (`CL-USDT-SWAP` WTI since 2026-03-04, `BZ-USDT-SWAP` Brent since 2026-03-24 —
      `public/instruments?instType=SWAP`, ICE data-partnership index) and Bybit (`CLUSDT`, `BZUSDT` —
      `v5/market/instruments-info?category=linear`); **NOT FOUND** on Hyperliquid (`info {"type":"meta"}` 232-perp
      universe has no CL/BZ/oil entry — no commodity perps at all today, XAU/XAG/COPPER also absent). `CL`/`BZ` were
      already members of `CEFI_EQUITY_PERP_BASE_UNIVERSE` (Binance-sourced 2026-07-08 re-sync) — that filter is
      venue-agnostic, so no universe-membership change was needed for OKX/Bybit to be admitted. Recorded the per-venue
      found/not-found result with cited evidence in new module
      `unified_api_contracts/canonical/crosscutting/oil_perp_venue_coverage.py` (mirrors this batch's todo 2
      `index_commodity_perp_hedge_link.py` "found/not-found, cite the evidence" convention), added a dated
      cross-venue-verification comment next to the CL/BZ entries in `cefi_instrument_universe.py`, and added
      `tests/unit/test_oil_perp_venue_coverage.py` (13 tests). `quality-gates.sh` green (381s).
- [x] ✅ [DATA] P1. **Re-run e2e-testing's NET-basis backtest with dividend yield priced into the long cash-stock leg**
      for each of the 12 net-profitable single-stock pairs (holding the stock earns dividends, adding to NET; the
      current +5-24% figures are a floor without it) — identify and use an already-available dividend-yield data source
      (check Databento DBEQ.BASIC corporate-actions coverage first). Repo: e2e-testing. Source:
      `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` line 820. **Done when**: an updated NET-basis table
      including dividend yield is produced for all 12 pairs and posted to that doc's Progress Log. — **DONE 2026-08-09**
      — `e2e-testing@12d1f3c`. Confirmed Databento DBEQ.BASIC has no dividends/corporate-actions schema (zero "dividend"
      hits across every Databento adapter in market-tick-data-service + instruments-service); used yfinance instead
      (mirrors the existing pattern already in market-tick-data-service/features-service/e2e-testing's own
      `backfill_vix_yahoo.py`). Extended `e2e-testing/scripts/cefi/net_basis_scan.py` with a TTM-dividend-yield fetcher
      (computed directly from raw dividend history ÷ last close — NOT yfinance's buggy `info["dividendYield"]` field)
      and a dividend-adjusted re-run holding the original 06-20 Gross%/Borrow% backtest fixed. All 12 pairs remain
      TRADEABLE with dividends priced in (NET +0.00 to +0.82pp vs. the 06-20 floor). Full table + evidence:
      `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Progress Log, 2026-08-09 entry (same commit).
- [x] ✅ [DATA] P1. **For each commodity/index perp currently NET-negative or NET-slim** (XAU/XAG/COPPER/SPX/SPY/NDX),
      check how far back its Binance listing/trade history goes, and cross-reference that window against the known
      contango/backwardation regime shifts already documented in that doc's NET-basis backtest (e.g. CL's -20%
      backwardation) to determine whether each perp's short history means the net-negative verdict is regime-conditional
      rather than permanent. Repo: instruments-service (read-only research). Source:
      `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` line 823. **Done when**: a per-symbol table of
      (listing date, history length, regime-window coverage) is produced and posted to that doc's Progress Log — no
      universe add/remove decision is made by this todo. — **DONE 2026-08-09** — live-queried Binance
      `fapi/v1/exchangeInfo`+`klines` for XAU/XAG/COPPER/SPX/SPY/NDX. **XAU/XAG/COPPER/SPY are real perps but each has
      only 23-55% overlap** with the doc's ~11-12mo NET-basis regime window (all listed partway through it) — their
      SLIM/NEGATIVE verdicts are regime-conditional, not proven permanent (CL's own -20% backwardation in the same table
      proves commodity regimes DO flip). **SPX's 100% window coverage is a false signal**: Binance `SPXUSDT` is the
      SPX6900 meme coin (`underlyingType=COIN`/`Meme`, confirms batch11 todo 2's finding), not an S&P-500 instrument —
      its long history doesn't bear on the real index's regime at all. **NDX has no Binance perp** (confirmed via a full
      `exchangeInfo` grep) and never had a NET-basis row in the source doc. No universe/backtest change made. Full
      per-symbol table + evidence: `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Progress Log,
      2026-08-09 entry.
- [x] ✅ [DATA] P1. **Run a window-scoped honest-coverage measurement**
      (`instruments-service/scripts/measure_honest_coverage.py     --asset-group cefi`, or a targeted
      `/data-pipeline-check-mtds` day-sample) restricted to OKX-SPOT/-SWAP/-FUTURES, BINANCE-SPOT/-FUTURES, BYBIT over
      2024-01-01→present — this is the blocking prerequisite the source doc's own P0 live-capital backtest-fidelity gate
      needs before it becomes schedulable (deliberately narrower/faster than the unrelated full-history 2019-2026
      chronological backfill tracked elsewhere). Repo: instruments-service. Source:
      `cefi_ml_directional_continuous_live_2026_06_20.md` line 180. **Done when**: a coverage % for exactly this venue
      set + window is cited in that plan's Progress Log with an `attempted_failed`/`expected_unattempted` breakdown; if
      materially below complete, the specific gap (venue/data_type/date range) is filed as its own blocking issue. —
      **DONE 2026-08-09** — measured by reusing `measure_honest_coverage.py`'s bounded, column-pruned manifest reader
      (`_read_manifest`/`_count_statuses`, single read, no new whole-corpus GCS walk), filtered in-memory to the target
      venue set + date window. **Result: 48.90% overall reachable coverage** (captured=1,295,524 /
      attempted_failed=94,706 / expected_unattempted=1,258,908 / empty_confirmed=331,778 of 2,980,916 scoped rows) —
      materially below complete. Per venue: OKX-FUTURES 80.51%, OKX-SWAP 64.18%, BINANCE-FUTURES 57.46%, BINANCE-SPOT
      45.25%, BYBIT 35.99%, OKX-SPOT 29.34% (worst). Gap concentrates in `trades`/`book_snapshot_5` (10.6%-46.3% per
      venue) vs. `derivative_ticker`/`liquidations` (58%-97%). **Trailing-90d coverage (24.70%) is WORSE than the
      full-window average (48.90%)** in every single venue — a live-capture-health signal, not just a historical gap.
      `futures_chain` is 0.00% for BINANCE-FUTURES/BYBIT with 100% attempted_failed (every attempt fails — a distinct
      correctness bug). Cited in `cefi_ml_directional_continuous_live_2026_06_20.md`'s Progress Log (same commit);
      specific gap filed as its own blocking issue with 4 fix todos:
      `issues/cefi_window_scoped_coverage_gap_okx_binance_bybit_2024_2026_2026_08_09.md`.

## Codex SSOTs

- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the shared conflict-check protocol
  this batch's authoring ran (§3), and the `parent_epic` grouping rule (§2) that split this extraction into 4 sibling
  batches (11/12/13/14) instead of one mixed-`parent_epic` doc.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — the
  bounded/checkable test applied to every item in all 19 source docs.
- `/plans/active/task_template.md` §3 finding U — the `[OPERATOR]`-tag positive test applied when deciding an item was
  NOT genuinely operator-gated (relevant to sibling batch12's mdps_features_deadcode item, cited here for the shared
  methodology).

## Progress Log

- **2026-08-09** — drafted from a 4-agent parallel item-level classification pass over the 19-doc cefi RECLASSIFY-sweep
  non-qualifying candidate list (candidate list: `/private/tmp/.../scratchpad/satellite_extract_cefi.txt`, not
  corpus-resident). 16 extractable items found across all 19 docs; this doc carries the 10 whose source doc's
  `parent_epic: cefi_master`. Every item independently re-verified against live code/doc state before inclusion: (1)
  todos 1-5 confirmed as the literal, currently-open checkboxes at `cefi_consolidated_closeout_2026_07_18.md` lines
  136/158/168/170/173 (direct `grep -n` read); (2) todos 6-9 confirmed as literal open checkboxes at
  `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` lines 175/795/820/823, and cross-checked that the OTHER
  ~8 open items in that same doc duplicating `cefi_consolidated_closeout` Track 0 content (lines
  108/219/234/241/622/644/648/673) were correctly NOT re-extracted here (already covered by todos 1-5 above, sourced
  from the closer/canonical Track 0 copy — extracting both would double-dispatch identical work); (3) todo 10 confirmed
  as the literal open checkbox at `cefi_ml_directional_continuous_live_2026_06_20.md` line 180, filed 2026-08-08 as the
  named blocking prerequisite for that doc's P0 backtest-fidelity gate (which itself correctly stays behind —
  dependency-blocked on this todo). **Conflict-check (per the shared protocol, §3)**: grepped the full `plans/active/`
  corpus for each todo's real target (Barchart, KRX/HYUNDAI, SPXUSDT/NAS100, LEVEL_MAX_LOOKBACK) — zero
  verbatim-duplicate claims found on any currently-active `assigned_vm: planning` plan; the many TradFi-doc "Barchart"
  hits are data/manifest-state references, not code-deletion claims (see todo 5's inline note). No sibling
  batch/finalize doc in `parent_epic: cefi_master` (batch9, batch10, their finalize twins) claims any of these 10 items
  — verified via direct grep of both docs' full text. `cefi_consolidated_closeout_2026_07_18.md`'s own checkbox for
  todos 1-5 replaced with a pointer to this doc in the same commit (see that doc's Track 0 section);
  `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`'s checkboxes for todos 6-9 replaced with pointers
  likewise; `cefi_ml_directional_continuous_live_2026_06_20.md`'s checkbox for todo 10 replaced with a pointer likewise
  — every non-extracted item in all 3 source docs left untouched.
- **2026-08-09** — todo 1 (propagation-ops B1/B3/B4 wave chain) DISPATCHED + DONE: verified live against prod GCS state
  that the chain (backfilled 2026-06-24, propagated nightly since) is fully complete — catalogue, manifest, and a sample
  capture all confirmed. No new backfill/rollup/enumerator run was needed. Full evidence in
  `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Progress Log (2026-08-09 entry, same commit).
- **2026-08-09** — todo 3 (KRX 4-window Yahoo backfill) DISPATCHED + NARROWED + DONE: found the 1h/15m/1m legs conflict
  with a resolved, still-live 2026-07-12 operator decision this todo's source predates (Yahoo intraday KRX adapter build
  explicitly rejected; registry narrowed to `ohlcv_24h`-only) — batch11's own conflict-check only grepped
  `plans/active/`, missing the archived governing decision. Applied that ruling as precedent rather than treating this
  as fresh ambiguity. The achievable 1d leg verified ~98% complete with real non-NaN GCS data (not just the manifest
  label — its `row_count` field is separately bugged). 2 adjacent manifest-integrity defects found + filed as follow-up
  todos. Full evidence + the follow-up todos:
  `/plans/active/issues/krx_batch11_todo3_intraday_conflicts_with_2026_07_12_ruling_2026_08_09.md`.
- **2026-08-09** — todo 4 (measure exact Databento lookback-floor boundary per level) DISPATCHED + DONE:
  `unified-api-contracts@92a418e5`. Live-measured via `metadata.get_cost` binary search (cost estimate endpoint, no data
  fetched, no billing risk) on GLBX.MDP3/ES.c.0: L1 (trades) exact boundary 367d free / 368d metered (prior constant
  365d was a safe-but-loose approximation), L2 (mbp-10) and L3 (mbo) both exact boundary 33d free / 34d metered (prior
  constant 30d). L1 boundary cross-checked identical on DBEQ.BASIC/AAPL — confirms the boundary is level-scoped, not
  per-dataset, so the existing single `LEVEL_MAX_LOOKBACK_DAYS` dict design is correct. L0 turned out to have NO rolling
  metered boundary at all — probed 5850d-5908d back on GLBX.MDP3, every point $0.0000, then 5909d+ hits a hard 422
  `data_start_before_available_start` (GLBX.MDP3's real archive starts 2010-06-06), never a metered charge; updated
  `_FULL_HISTORY_DAYS` from the arbitrary `16*365=5840` to the measured 5908d (exact distance from 2026-08-09 to
  GLBX.MDP3's inception — the oldest of the 3 subscribed datasets, so the widest value that stays safe for all three;
  XCBF.PITCH starts 2018-11-04, DBEQ.BASIC equities 2023-04-15, both cross-checked live). Updated
  `LEVEL_MAX_LOOKBACK_DAYS` + all docstrings/inline comments in `databento_subscription_allowlist.py` to the measured
  values; updated `tests/unit/test_databento_subscription_allowlist.py`'s boundary-raise assertions (366d/31d no longer
  raise — they're within the true measured free window now). `quality-gates.sh` green (336s).
- **2026-08-09** — todo 7 (WTI/Brent oil-perp venue check) DISPATCHED + DONE: `unified-api-contracts@89de6766`.
  Live-queried OKX/Bybit/Hyperliquid public instrument-listing endpoints. **FOUND** on OKX (`CL-USDT-SWAP` WTI, live
  since 2026-03-04T12:15Z; `BZ-USDT-SWAP` Brent, live since 2026-03-24T10:00Z — both ICE-data-partnership index-priced)
  and Bybit (`CLUSDT` since 2026-03-24T07:45Z, `BZUSDT` since 2026-05-13T08:08Z). **NOT FOUND** on Hyperliquid — its
  live `info {"type":"meta"}` universe (232 perps) carries no commodity perps at all today (no CL/BZ, and no
  XAU/XAG/COPPER either). `CL`/`BZ` were already in `CEFI_EQUITY_PERP_BASE_UNIVERSE` from a prior Binance-sourced
  re-sync (2026-07-08); since that base-asset filter is venue-agnostic (unioned into MVP scope), no universe-membership
  edit was needed for the OKX/Bybit listings to be admitted — the missing piece was the cross-venue verification record
  itself. New module `oil_perp_venue_coverage.py` (mirrors this batch's todo 2 `index_commodity_perp_hedge_link.py`
  found/not-found-with-evidence convention) + a dated comment in `cefi_instrument_universe.py` next to the CL/BZ
  entries + `tests/unit/test_oil_perp_venue_coverage.py` (13 tests). `quality-gates.sh` green (381s).
- **2026-08-09** — todo 6 (NET-basis backtest re-run with dividend yield) DISPATCHED + DONE: `e2e-testing@12d1f3c`.
  Confirmed Databento DBEQ.BASIC has no dividends/corporate-actions schema (grepped every Databento adapter in
  market-tick-data-service + instruments-service for "dividend" — zero hits); used yfinance instead, mirroring the
  established pattern (market-tick-data-service's `yahoo_finance_adapter.py`, features-service's
  `yfinance_earnings_adapter.py`, e2e-testing's own `backfill_vix_yahoo.py`) rather than the heavier Polygon
  corporate-actions adapter. Extended `net_basis_scan.py` with a TTM-dividend-yield fetcher computed directly from raw
  dividend history ÷ last close (NOT yfinance's `info["dividendYield"]` field, which has a documented stale/pre-split
  bug — confirmed live: it reads 0.45% for NVDA vs. the correct 0.125%) and a dividend-adjusted re-run holding the
  original 06-20 backtest's Gross%/Borrow% columns fixed so the comparison isolates exactly the dividend variable
  (funding-rate drift is a separate, already-tracked concern — the doc's own DYNAMIC-universe-ranking follow-up).
  Result: all 12 pairs remain TRADEABLE, NET +0.00 to +0.82pp vs. the 06-20 floor. Full table + evidence:
  `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Progress Log, 2026-08-09 entry (same commit).
- **2026-08-09 (slot 6) — Barchart-removal todo: research DONE, implementation DEFERRED (not started, nothing to
  revert).** Picked up after an unrelated task (N1b, different plan) got cancelled mid-flight and this task was freshly
  dispatched. A read-only research agent mapped every "Barchart" hit across `unified-api-contracts` +
  `market-tick-data-service` before any edit — preserving the findings here so a fresh session doesn't need to re-run it
  (session ended via `/pre-compact` before implementation; the remaining work spans 5 locations across 2 repos, each
  needing individual verification + 2× QG/quickmerge — genuinely not a "few minutes" finish). **Real deletion targets**
  (confirmed live, non-comment code):
  1. `unified-api-contracts/unified_api_contracts/external/defi/schemas.py:349-380` — `BARCHART_OHLCV_15M_SCHEMA`
     constant (verified **zero** other references anywhere in the workspace via
     `grep -rln "BARCHART_OHLCV_15M_SCHEMA\|barchart_ohlcv_15m"` — safe to delete outright), plus its
     `DEFI_SCHEMA_MAP["barchart_ohlcv_15m"]` entry (line ~419) and `__all__` export (line ~442).
  2. `unified_api_contracts/provider_api_versions.yaml:37-40` AND the duplicate at
     `unified_api_contracts/config/provider_api_versions.yaml:55-60` — live `barchart:` YAML registry blocks
     (`api_version`/`spec_url`/`last_verified`/`status`), both need the same edit.
  3. `market-tick-data-service/tests/market_interface/unit/test_barchart_and_yahoo_adapters.py:1` — stale module
     docstring `"""Tests for BarchartAdapter and YahooFinanceAdapter."""` referencing a class that doesn't exist
     (confirmed: the file's actual contents are 100% `YahooFinanceAdapter` tests, zero `BarchartAdapter` code) — reword
     the docstring (or rename the file), nothing functional to delete. **Confirmed NOT to touch** (checked precisely, do
     not blindly grep-and-delete): (a) `market_data_categories.py:850`
     `TRADFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES = frozenset({"BARCHART", "YAHOO_FINANCE"})` is a LIVE, correct
     data-quality exception list — 9,119 real legacy manifest rows still carry the `BARCHART` venue label
     (operator-ruled quarantine-with-tracking, 2026-07-20) and this frozenset is what stops them re-flagging as fresh
     drift every census run; deleting it would BREAK that census, not clean anything up. (b) `registry/endpoints.py:371`
     — the "barchart -> unified_api_contracts.barchart" comment is stale/misleading (confirmed zero literal `"barchart"`
     key in the actual `module_map` dict via targeted grep) but is a harmless comment, not code — optional cleanup, not
     required for "Done when: no Barchart code/test references remain" (arguably the comment itself IS a reference;
     judgment call for whoever picks this up). (c) Every other hit in both repos (grep list: see the agent's full
     report, or re-run `grep -rin barchart unified_api_contracts/ market_tick_data_service/ --include='*.py'` in each
     repo) is a "RETIRED"/historical-provenance comment, correctly kept per CLAUDE.md's own "Barchart RETIRED" framing.
     **Also flagged, not yet checked**: `deployment-ui` may have Barchart source-name labels in UI dropdowns — the agent
     noted this as "worth a manual spot-check" but didn't confirm; check before calling the todo's "no Barchart
     references remain" done-when fully satisfied (todo's own repo scope is
     `unified-api-contracts, market-tick-data-service` only, so this is an FYI, not blocking). No cross-repo Python
     `import` of a Barchart symbol exists anywhere (checked). Next session: implement items 1-3 above, run QG in both
     repos, quickmerge, flip the plan's own Barchart todo. `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`
     Progress Log, 2026-08-09 entry (same commit).
- **2026-08-09** — todo 9 (Binance listing/history-length vs regime-window cross-reference) DISPATCHED + DONE: read-only
  research, no code shipped. Live-queried Binance `fapi/v1/exchangeInfo` (`onboardDate`) +
  `fapi/v1/klines?interval=1d&startTime=0` (first real daily candle) for XAU/XAG/COPPER/SPX/SPY/NDX, cross-referenced
  against the source doc's own ~11-12mo NET-basis regime window (2025-07-01→2026-06-30). **XAU/XAG/COPPER/SPY** are real
  perps with only 23-55% overlap with that window (each listed partway through it) — their SLIM/NEGATIVE verdicts are
  regime-conditional, not proven permanent (the same table's CL -20% backwardation reading is this doc's own proof that
  commodity regimes flip). **SPX**'s nominal 100% coverage is a false signal: Binance `SPXUSDT` is confirmed live to be
  the SPX6900 meme coin (`underlyingType=COIN`/`Meme`), not an S&P-500 instrument — matches batch11 todo 2's independent
  finding, restated here because it undermines this todo's own coverage metric for that row. **NDX** has no Binance perp
  at all (confirmed via a full `exchangeInfo` symbol-list grep) and never had a NET-basis row in the source doc to begin
  with. No universe/backtest change made, per this todo's explicit scope. Full per-symbol table + evidence:
  `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Progress Log, 2026-08-09 entry (same commit).
- **2026-08-09** — todo 10 (window-scoped honest-coverage measurement, OKX/BINANCE/BYBIT 2024-01-01→present)
  DISPATCHED + DONE, read-only measurement, no code shipped. Reused `measure_honest_coverage.py`'s bounded column-pruned
  manifest reader (single cefi manifest read, no new whole-corpus GCS walk), filtered in-memory to the target venue
  set + date window (2,980,916 scoped rows of 10,537,552 total). **Result: 48.90% overall reachable coverage —
  materially below complete.** Per-venue range 29.34% (OKX-SPOT, worst) to 80.51% (OKX-FUTURES). Gap concentrates in
  `trades`/`book_snapshot_5` (10.6%-46.3%) vs. healthy `derivative_ticker`/`liquidations` (58%-97%). **Trailing-90d
  coverage (24.70%) is WORSE than the full-window average in every single venue** — flagged as a likely
  live-capture-health issue, not just a historical backfill gap. `futures_chain` is 0.00% for BINANCE-FUTURES/BYBIT with
  100% attempted_failed (every attempt fails — a distinct correctness bug, not an absence gap). Result cited in
  `cefi_ml_directional_continuous_live_2026_06_20.md`'s Progress Log (same commit; that doc's grid-run schedulability
  verdict updated from "unconfirmed" to "confirmed NOT schedulable, blocking issue filed"). Specific gap filed as its
  own blocking issue with 4 fix todos (P0 live-capture investigation, P1 futures_chain root-cause, P1 backfill-plan
  cross-reference, P2 targeted backfill):
  `/plans/active/issues/cefi_window_scoped_coverage_gap_okx_binance_bybit_2024_2026_2026_08_09.md`.
- **2026-08-09 (slot-17, data_engineering) — todo 5 (Barchart removal) IMPLEMENTED + DONE**, building on slot-6's
  research above (no re-derivation needed). Shipped: **unified-api-contracts@fc1b4897** — deleted
  `BARCHART_OHLCV_15M_SCHEMA` + its `DEFI_SCHEMA_MAP`/`__all__` entries in `external/defi/schemas.py`, the live
  `barchart:` registry blocks in both `provider_api_versions.yaml` files (`unified_api_contracts/` +
  `unified_api_contracts/config/`), and the stale illustrative comment in `registry/endpoints.py:371`. **
  market-tick-data-service@aea655a9** — deleted `TestBarchartOhlcv` in
  `tests/market_interface/integration/test_vcr_ac_schema_validation.py` (imported a nonexistent
  `unified_api_contracts.external.barchart.BarchartOhlcv15m`; its referenced cassette was already deleted 2026-05-21 per
  `scripts/canary/orphan-decisions.yaml`), renamed `test_barchart_and_yahoo_adapters.py` → `test_yahoo_adapter.py` (file
  was 100% `YahooFinanceAdapter` tests, zero Barchart code — the filename itself was the last "Barchart reference"
  there), and dropped the dead `"BARCHART"` entry from `smoke_matrix.py`'s `_REPRESENTATIVE_SYMBOL` map (confirmed dead,
  not just redundant: `enumerate_cells()` iterates `VENUES_BY_ASSET_GROUP`, and BARCHART was already removed from
  `VENUES_BY_ASSET_GROUP["tradfi"]` 2026-06-24, so no cell ever looks this key up). **Scope boundary held** (matches
  slot-6's precedent on the `TRADFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES` frozenset): explicitly did NOT touch the
  `batch_barchart` pipeline_mode/venue-override handling in `rebuild_tradfi_manifest.py`,
  `migrate_tradfi_to_v9_canonical.py`, `populate_v9_index_columns_inplace.py`, or their tests
  (`test_rebuild_tradfi_manifest_parser.py`, `test_rebuild_tradfi_manifest.py`,
  `test_tradfi_shared_path_byte_identity.py`) — that code parses/validates ALREADY-CAPTURED historical
  `BARCHART`-labeled manifest rows (the same 9,119-row legacy dataset the frozenset protects); it is live data-compat
  code, not retired live-fetch adapter code, and deleting it would break manifest reads for real historical data rather
  than clean anything up. Also left every "RETIRED 2026-06-24"-style historical-provenance comment in place per
  CLAUDE.md's own framing. Both repos: `quality-gates.sh` green, shipped via `quickmerge --agent`, post-push ancestry
  verified on `live-defi-rollout`.
- **2026-08-09** — todo 6 (extend live-ws order-book connectors for crypto-venue equity-perp BBO+depth) DISPATCHED +
  DONE, no code change: read the full capture path top to bottom (per-venue `book_snapshot_5` connectors → base-token
  derivation → canonical-id builders → `LiveWebsocketRunner._resolve_is_universe`) and confirmed every layer is
  symbol-generic with equity-perp bases already in the MVP-scoped IS universe, then proved it live rather than trusting
  the read — ran the real `--mode live --operation websocket-streaming` CLI (IS_TEST_RUN=true, an ephemeral local Docker
  Redis standing in only for the boundary-event publisher) against a live-verified `AAPL` equity-perp on all 3 venues.
  All 3 wrote a genuine `captured` manifest row (13/9/18 rows respectively) to the `-test-` bucket, byte-for-byte the
  same shard-atom shape as any non-equity-perp live book_snapshot_5 capture. Full evidence + exact manifest values in
  todo 6's own entry above.

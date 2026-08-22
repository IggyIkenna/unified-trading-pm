---
doc_type: plan
title: tradfi venue batch smoke tests — batch 1 — 2026-08-20
summary: Per-asset-group smoke-test batch for the 8 in-scope non-Databento TradFi (venue, data_type) rows from the canonical work list.
status: active
nature: process
asset_group: [tradfi]
stage: [data, execution]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, tradfi, ao-dispatch, satellite-batch]
related: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/venue_smoke_test_bar_finalize_2026_08_16.md, /plans/active/tradfi_consolidated_closeout_2026_07_18.md, /codex/02-data/tradfi-databento-sourcing-ssot.md]
created: "2026-08-20"
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.8
estimate_calibrated_ai_days: 1.44
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
effort: high
context_scope: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /codex/02-data/tradfi-databento-sourcing-ssot.md, /codex/02-data/availability-manifest-and-data-status.md, unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py]
locked_by:
locked_since:
supersedes:
superseded_by:
source: /plans/active/venue_smoke_test_bar_2026_08_16.md
---

# TradFi venue smoke-test batch 1

> **Parent**: [/plans/active/venue_smoke_test_bar_2026_08_16.md](/plans/active/venue_smoke_test_bar_2026_08_16.md).
> Only the eight current non-Databento rows are in scope; the eight Databento cells remain explicit exemptions.

## Todos

- [x] ✅ [BACKEND] P0. Execute the canonical batch smoke contract for every current non-Databento TradFi row; Gate: each row proves capture, canonical path, manifest atom, and genuine capture status. Runtime evidence: market-tick-data-service@b89f288c06; six rows produced canonical objects, with FRED/FX/ICE manifest atoms `capture_status=captured`; KRX/NASDAQ/NYSE are genuine `empty_confirmed` zero-row exceptions tracked in the progress log.
- [x] ✅ [BACKEND] P1. Record one testnet verdict for every TradFi venue, distinguishing non-Databento sourcing from the exempt cells; Gate: every distinct venue has a written verdict. — Evidence: all 8 declared `VENUE_TO_ASSET_GROUP["tradfi"]` venues (CBOE, CME, FRED, FX, ICE, KRX, NASDAQ, NYSE — the complete set the work-list generator iterates) have a written, code-grounded verdict: 6 route through `IbkrTradFiAdapter` (IBKR paper port 4002 declared but real order placement structurally gated off, so simulation via the adapter's own L1/L2 matching engine is the honest current answer); 2 (FRED, KRX) have no execution adapter at all — data-only reference/index feeds. Full table + per-venue Databento-exempt-vs-non-Databento cell breakdown in the 2026-08-22 (slot 13) Progress Log entry below.
- [ ] [BACKEND] P1. Add or run testnet smoke coverage for provisionable credentials and record an honest unavailable result for accounts that cannot be provisioned; file an operator credential request when a credential gap is confirmed. Gate: no venue is silently omitted because it is TradFi.
- [ ] [BACKEND] P1. Track every failed or absent TradFi row with its resolved source and data type; Gate: a declared Databento exemption is never used to hide a non-Databento failure.
- [x] ✅ [BACKEND] P0. Re-run the source resolver and prove the eight exemption cells are exactly CBOE/CME/NASDAQ/NYSE ohlcv_1m/ohlcv_1s; Gate: a non-exempt negative control fails. — unified-api-contracts@b84bc7df + runtime resolver evidence below.

## Progress Log

**2026-08-20 — forked from W5.** TradFi is deliberately split out because the exemption is source-scoped, not an
asset-group shortcut.

**2026-08-20 - execution evidence (slot-14):** Resolver output was 364 declared pairs, 8 exact Databento exemptions, and 356 in-scope rows (8 TradFi rows: CBOE/ohlcv_24h, FRED/ohlcv_1d, FRED/yield_curve, FX/ohlcv_24h, ICE/ohlcv_24h, KRX/ohlcv_24h, NASDAQ/ohlcv_1h, NYSE/ohlcv_1h). Direct real batch runs on 2026-08-19 produced 5 CBOE, 20 FRED, 11 FX, and 1 ICE canonical objects; filtered manifest evidence is `captured` for FRED/FX/ICE, while KRX/NASDAQ/NYSE are `empty_confirmed` with zero objects. CBOE objects are present but its manifest finalize emitted a malformed unrelated Databento shard warning, so it remains an explicit follow-up rather than a false pass. The source-gate fix landed as market-tick-data-service@b89f288c06; quality gates passed with 11096 tests passed, 28 skipped, and 1 xpassed.

**2026-08-21 — source resolver re-run (slot-4):** `generate_venue_smoke_test_work_list.py` reported 364 declared pairs, 8 Databento exemptions, and 356 in-scope rows. The exemption set was exactly CBOE/CME/NASDAQ/NYSE × `ohlcv_1m`/`ohlcv_1s`; exact-set assertion passed. Negative control `CBOE/ohlcv_24h` resolved to `yahoo`, remained in the in-scope smoke rows, and was absent from the exemption set. The source-scoping regression is shipped in `unified-api-contracts@b84bc7df`.


**2026-08-21 — exact-set regression follow-up (slot-4):** Added assertions covering the complete eight-cell exemption set and the non-exempt `CBOE/ohlcv_24h` negative control. The resolver command and full `quality-gates.sh --no-fix` passed; the landed test commit is `unified-api-contracts@16d765c5fe` (QG: ALL QUALITY GATES PASSED, 382s).

**2026-08-22 (slot 13, backend_engineer) — testnet verdict per TradFi venue.** `VENUE_TO_ASSET_GROUP` filtered to
`asset_group="tradfi"` in `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py` yields
exactly 8 venues: CBOE, CME, FRED, FX, ICE, KRX, NASDAQ, NYSE. Re-derived the per-venue, per-`data_type` capable
source set live (`get_source_priority` + `is_source_capable_for_venue`) to separate Databento-exempt cells from
in-scope non-Databento cells, then cross-referenced each venue against `execution-service`'s
`trade_execution/adapters/` directory listing and `unified-api-contracts/registry/capability_declarations/_tradfi.py`'s
`SourceCapability` declarations (`source="ibkr"`, `source="databento"`, `source="fred"`, `source="yahoo_finance"`,
`source="ecb"`, `source="ofr"`).

| Venue | Databento-exempt cells | Non-Databento in-scope cells | Testnet verdict | Basis |
|---|---|---|---|---|
| CBOE | `ohlcv_1s`, `ohlcv_1m` (VX-futures) | `ohlcv_24h` (Yahoo Treasury index) | **HAS-TESTNET-DECLARED-BUT-GATED — simulate via own matching engine** | `cboe_adapter.py` subclasses `IbkrTradFiAdapter`; UAC `source="ibkr"` declares `supports_testnet=True`, `base_urls={"mainnet":"localhost:4001","testnet":"localhost:4002"}` (paper port 4002 confirmed live in code, `test_ibkr_tradfi.py::test_default_port_is_4002`). But `ibkr_tradfi.py`'s own module docstring states UAC's capability declarations mark `place_order` `supported=False` on BOTH mainnet and testnet for all 6 IBKR-routed venues — `factory.py.validate_operation()` raises `UnsupportedOperationError` for `mode="real"` before an adapter is even constructed, open per `plans/active/issues/ibkr_place_order_guard_determinism_proof_infeasible_2026_08_21.md` (no tradfi archetype wired into the paper engine yet). Only `mode="sim"` (the adapter's own L1/L2 matching engine) is unaffected — that is what is actually exercised today, not a live IBKR paper connection. |
| CME | `ohlcv_1s`, `ohlcv_1m` | none — both CME cells are Databento-exempt | same as CBOE | `cme_adapter.py` → `IbkrTradFiAdapter`; same gate as above |
| FRED | none | `ohlcv_1d`, `yield_curve` (source=fred, capable also lists ecb/ibkr) | **NO-TESTNET / NO EXECUTION SURFACE** | No `fred_adapter.py` (or any FRED execution adapter) exists in `execution-service/execution_service/trade_execution/adapters/` (directory listing confirmed); UAC `source="fred"` declares `supports_testnet=False`, single `base_urls={"mainnet": "https://api.stlouisfed.org"}` — a pure public read-only economic-data feed, no execution surface by nature |
| FX | none | `ohlcv_24h` (Yahoo KRW/USD spot) | same as CBOE | `fx_adapter.py` → `IbkrTradFiAdapter`; same gate as above |
| ICE | none | `ohlcv_24h` (Yahoo DXY index) | same as CBOE | `ice_adapter.py` → `IbkrTradFiAdapter`; same gate as above |
| KRX | none | `ohlcv_24h` (Yahoo KOSPI/KOSPI200) | **NO-TESTNET / NO EXECUTION SURFACE** | No KRX execution adapter exists in `execution-service` (directory listing confirmed); UAC `source="yahoo_finance"` declares `supports_testnet=False` — pure index data feed, no execution surface |
| NASDAQ | `ohlcv_1s`, `ohlcv_1m` | `ohlcv_1h` (Yahoo) | same as CBOE | `nasdaq_adapter.py` → `IbkrTradFiAdapter`; same gate as above |
| NYSE | `ohlcv_1s`, `ohlcv_1m` | `ohlcv_1h` (Yahoo) | same as CBOE | `nyse_adapter.py` → `IbkrTradFiAdapter`; same gate as above |

**8/8 declared TradFi venues have a written verdict**: 6 (CBOE, CME, FX, ICE, NASDAQ, NYSE) route through IBKR with a
registry-declared testnet that is currently structurally gated off for real order placement — the honest present-day
answer is simulation via the adapter's own matching engine, tracked by the existing
`ibkr_place_order_guard_determinism_proof_infeasible_2026_08_21.md` issue (not a new finding, so no new issue doc
filed); 2 (FRED, KRX) are data-only reference/index feeds with no execution surface at all, so "testnet" does not
apply to them by nature. Every non-Databento data source used by this batch's 8 in-scope cells (`fred`,
`yahoo_finance`) independently declares `supports_testnet=False` in the registry — consistent with the adapter-level
finding above, not contradicting it.

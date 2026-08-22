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
- [x] ✅ [BACKEND] P1. Add or run testnet smoke coverage for provisionable credentials and record an honest unavailable result for accounts that cannot be provisioned; file an operator credential request when a credential gap is confirmed. Gate: no venue is silently omitted because it is TradFi. — Evidence: execution-service@c531ca3bb3 adds + runs `scripts/run_tradfi_testnet_connectivity_smoke.py` live. Finding: `ibkr-account-credentials` (GSM) resolves live — NOT a credential gap — but no IB Gateway process is reachable from anywhere in the project; all 6 IBKR-routed venues honestly report `provisioned_gateway_unreachable`, FRED/KRX report `not_applicable_no_execution_surface`. No credential request filed — none is warranted; see Progress Log.
- [x] ✅ [BACKEND] P1. Track every failed or absent TradFi row with its resolved source and data type; Gate: a declared Databento exemption is never used to hide a non-Databento failure. — Evidence: `market-tick-data-service@b7ed88f583` adds `track_tradfi_failed_absent_rows_2026_08_22.py`; live run this session found 6/8 captured, 2 failed/absent (NASDAQ/ohlcv_1h, NYSE/ohlcv_1h — 42/42 empty_confirmed), gate overlap=0. Full details in the Progress Log entry below.
- [x] ✅ [BACKEND] P0. Re-run the source resolver and prove the eight exemption cells are exactly CBOE/CME/NASDAQ/NYSE ohlcv_1m/ohlcv_1s; Gate: a non-exempt negative control fails. — unified-api-contracts@b84bc7df + runtime resolver evidence below.
- [ ] [OPERATOR] P3. Decide whether to stand up the IB Gateway VM (`ibkr-gateway-infra` Terraform; credential already
      provisioned as `ibkr-account-credentials`) ahead of TradFi's live/paper cutover, or leave it undeployed until
      that cycle begins (current state — consistent with "TradFi is batch-only this cycle" per
      `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md:82`). Once decided/deployed, re-run
      `execution-service/scripts/run_tradfi_testnet_connectivity_smoke.py` to confirm `provisioned_and_reachable`.

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

**2026-08-22 (slot 9, backend_engineer) — testnet smoke coverage + credential-provisioning check, todo 3.** Added
`execution-service/scripts/run_tradfi_testnet_connectivity_smoke.py` (mirrors the CeFi sibling
`run_cefi_testnet_connectivity_smoke.py`'s structure/taxonomy) and ran it live this session — a real Secret Manager
read + a real TCP probe, not a mock. Cross-checked against
`plans/active/issues/ibkr_place_order_guard_determinism_proof_infeasible_2026_08_21.md`: that issue answers a
DIFFERENT question (can `place_order` be proven safe to enable) and does not cover credential provisioning or
connectivity smoke coverage — no overlap, no redundant work.

| Check | Result | Basis |
|---|---|---|
| `ibkr-account-credentials` (GSM secret, backs all 6 IBKR-routed venues) | **PROVISIONED** — `get_ibkr_credentials()` resolves live (real Secret Manager read); independently confirmed via `gcloud secrets versions list ibkr-account-credentials` → 1 enabled version since 2026-03-23 | Not a credential gap — the login secret genuinely exists and is populated |
| IB Gateway reachability (CBOE/CME/FX/ICE/NASDAQ/NYSE — all share ONE physical Gateway, one host:port) | **UNREACHABLE** — live TCP probe (`IbkrTradFiAdapter.health_check()`) to 127.0.0.1:4002 failed on every venue; `gcloud compute instances list --filter="name~ibkr"` (project `central-element-323112`) returns zero instances — no Gateway VM is deployed anywhere in this project today | Measured, not assumed. `ibkr_tradfi.py` has zero call sites for `get_ibkr_credentials()` — IBKR's socket API takes no per-call credential, so this is a pure infra-deployment gap, independent of the (already-provisioned) credential |
| FRED, KRX | **NOT APPLICABLE** — no execution adapter exists (confirmed via directory listing of `execution_service/trade_execution/adapters/`); already established in todo 2 | No execution surface by nature |

**Why no operator credential request was filed**: the todo's "file an operator credential request when a credential
gap is confirmed" is conditional — no gap was confirmed. Filing a `BLOCKED-CREDENTIALS` request would misrepresent the
actual state per `/codex/02-data/external-data-always-available-rule.md`'s own status taxonomy (that tag means "no
secret exists yet"; this secret exists and resolves). The real gap is that no Gateway VM is currently deployed, which
lines up with the standing, already-documented "TradFi is batch-only this cycle" scoping — there has been no
operational need to run a live Gateway. Recorded as a new P3 `[OPERATOR]` follow-up above rather than an urgent
credential ask, since standing up broker infrastructure ahead of schedule is a timing/scope decision, not a
missing-secret blocker.

**8/8 declared TradFi venues have an explicit, honest connectivity/credential verdict** — none silently omitted for
being TradFi. Live script output this session: 6× `provisioned_gateway_unreachable`, 2×
`not_applicable_no_execution_surface`.

**2026-08-22 (slot 23, backend_engineer) — failed/absent row tracker + anti-hiding gate, todo 4.**
Shipped `market-tick-data-service/market_tick_data_service/scripts/track_tradfi_failed_absent_rows_2026_08_22.py`
(permanent, re-runnable — same lifecycle as `generate_venue_smoke_test_work_list.py`). It resolves the 8 in-scope
non-Databento `(venue, data_type, source)` cells and the 8 Databento-exempt cells via the SAME UAC registry calls
the generator uses (`get_source_priority`/`is_source_capable_for_venue` + `VENUE_DATA_TYPE_CAPABILITIES`/
`VENUE_TO_ASSET_GROUP`, imported through the sanctioned one-level `unified_api_contracts`/`unified_api_contracts.registry`
facades, not the UAC-internal `canonical.crosscutting.*` deep path — two deep-import QG violations found and fixed
during this session), reads each cell's LIVE PROD manifest `capture_status` distribution via
`read_availability_index_safe`, and classifies each cell `captured` (any captured row exists) vs failed/absent
(`attempted_failed` / `empty_confirmed` / `expected_unattempted` / no rows at all). `assert_exemption_gate()` is the
Gate this todo names: it raises loudly if any failed/absent cell's `(venue, data_type)` collides with the Databento
exemption set — proving a real failure was never masked by mistaking a non-Databento cell for an exempt one. The
concrete risk this protects against: CBOE, NASDAQ, and NYSE each carry BOTH a Databento-exempt cell (their
`ohlcv_1m`/`ohlcv_1s`) AND a non-exempt in-scope cell (`ohlcv_24h` for CBOE, `ohlcv_1h` for NASDAQ/NYSE) — a report
reasoning at VENUE grain instead of `(venue, data_type)` grain would silently drop the non-exempt cell's own
failures from view; this script always resolves per-cell, never per-venue, and `mixed_venues()` reports the three
mixed venues explicitly so the independence is visible, not just asserted. A dedicated negative-control unit test
(`test_find_exemption_overlap_detects_a_real_collision` / `test_assert_exemption_gate_raises_on_overlap`) feeds the
gate a fabricated exemption collision and proves it actually raises — the gate has teeth, not a trivially-true
pass-by-construction.

Live run this session (read-only, no `--apply`/writes) against the PROD tradfi manifest:

| Venue | data_type | source | status | captured | attempted_failed | empty_confirmed | expected_unattempted | total |
|---|---|---|---|---|---|---|---|---|
| CBOE | ohlcv_24h | yahoo | **captured** | 8,674 | 7,397 | 3,470 | 0 | 19,541 |
| FRED | ohlcv_1d | fred | **captured** | 2,870 | 0 | 1,182 | 0 | 4,052 |
| FRED | yield_curve | fred | **captured** | 14,409 | 0 | 1,164 | 0 | 15,573 |
| FX | ohlcv_24h | yahoo | **captured** | 3,637 | 2,144 | 1,881 | 0 | 7,662 |
| ICE | ohlcv_24h | yahoo | **captured** | 1,906 | 11,763 | 1,933 | 0 | 15,602 |
| KRX | ohlcv_24h | yahoo | **captured** | 4,377 | 3,339 | 2,733 | 8,292 | 18,741 |
| NASDAQ | ohlcv_1h | yahoo | **empty_confirmed** | 0 | 0 | 42 | 0 | 42 |
| NYSE | ohlcv_1h | yahoo | **empty_confirmed** | 0 | 0 | 42 | 0 | 42 |

**Result: 6/8 captured, 2/8 failed/absent (NASDAQ/ohlcv_1h and NYSE/ohlcv_1h, both 100% `empty_confirmed` — no
`attempted_failed` rows for either), gate overlap = 0.** KRX/ohlcv_24h is now `captured` — a genuine change from
todo 1's 2026-08-20 evidence ("KRX/NASDAQ/NYSE are genuine `empty_confirmed` zero-row exceptions"), confirming
fleet activity in the intervening two days filled it in; this tracker reflects CURRENT live state, not a stale
snapshot, which is the point of shipping it as a re-runnable script rather than one-off prose. CBOE/ohlcv_24h is
also confirmed `captured` (8,674 rows) — consistent with todo 1's "CBOE objects are present" finding; its separate
manifest-finalize warning (an unrelated malformed Databento shard message) stays its own open follow-up, untouched
by this todo.

**Scoping note, stated transparently rather than buried:** classification is at `(venue, data_type)` CELL grain
(does a captured row exist at all), matching todo 1's own established framing and the CeFi/Sports sibling
implementations of this identical todo — NOT per-day completeness. Several "captured" cells carry large
`attempted_failed` counts (ICE 11,763/15,602 = 75% failed-attempt days; CBOE 7,397/19,541 = 38%; KRX 3,339/18,741 =
18%; FX 2,144/7,662 = 28%) — genuinely low daily completeness despite passing the binary "can we backtest this
venue at all" bar this plan's smoke-test bar targets (`venue_smoke_test_bar_2026_08_16.md` § "Why": *"BACKTESTABLE
is the floor... a batch smoke test per data type per venue, so at minimum we know we can research and backtest the
venue honestly"*). Per-day completeness percentage is a DIFFERENT, already-standing mechanism
(`reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)`,
[`honest-coverage-model.md`](/codex/02-data/honest-coverage-model.md)) — not duplicated here; the raw per-status
counts are reported above so nothing is hidden, but a cell is not reclassified failed/absent purely for having a
low completeness percentage. Not filed as a new finding: these counts are the raw ingredients the standing
honest-coverage mechanism already surfaces elsewhere, not a gap this todo introduces or need fix.

Quality gates: full `quality-gates.sh --no-fix` passed (11,304 passed, 28 skipped, 1 xpassed); two deep-UAC-import
violations found and fixed during the session (both now route through the sanctioned one-level facade). Landed
`market-tick-data-service@b7ed88f583`, independently re-verified as a live ancestor of `origin/live-defi-rollout`
via `git merge-base --is-ancestor` (not trusted from quickmerge's own printed message alone).

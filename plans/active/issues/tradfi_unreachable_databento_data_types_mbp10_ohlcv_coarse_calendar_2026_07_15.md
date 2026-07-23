---
doc_type: issue
title:
  TRADFI mbp_10 / ohlcv_15m / ohlcv_24h / corporate_action_confirmed / earnings_result are declared expected TradFi
  data_types but have NO reachable fetch path through MTDS's generic tick-download routing — 100% attempted_failed by
  construction
summary:
  'Triaging a `#data-pipeline-alerts` `DP_RUN_MOSTLY_EMPTY` batch (window 2026-07-14 23:50Z-2026-07-15 00:19Z) found 5
  TRADFI (asset_group, data_type) cells at or near 100% `attempted_failed` against
  `market-data-tick-tradfi-prd-central-element-323112`: `ohlcv_15m` (3589/3590, 100.0%), `mbp_10` (1186/1186, 100.0%),
  `corporate_action_confirmed` (807/807, 100.0%), `earnings_result` (799/799, 100.0%), and `ohlcv_24h` (2852/7118,
  40.1%, included here as the same-mechanism sibling of ohlcv_15m). Direct code read confirms 3 DISTINCT root causes
  converging on the same symptom, per the triage task''s instruction to distinguish rather than assume a single cause:
  (1) `mbp_10` is a genuine ADAPTER-WIRING GAP — `market_tick_data_service/adapters/umi_tick_provider.py`''s
  `_DATABENTO_SUPPORTED_DATA_TYPES = frozenset({"trades", "ohlcv_1s", "ohlcv_1m", "tbbo"})` pre-flight filter (line 143,
  consulted at line 467) silently excludes `mbp_10` from ever reaching the fetch call, even though the lower-level
  `_resolve_databento_schema` (`databento_fetch.py:131`) has a live `"mbp_10": db.Schema.MBP_10` mapping AND
  `configs/venue_data_types.yaml` (CME futures_chain/options_chain `tick_window`) explicitly declares `mbp_10` as wanted
  — the exact same registry-declares/allowlist-excludes shape as the already-fixed KRX
  (`krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md`) and ICE
  (`tradfi_ice_ohlcv_1m_no_working_fetch_path_2026_07_13.md`) precedents, but for a schema-tier gap instead of a venue
  gap. (2) `ohlcv_15m`/`ohlcv_24h` are BY-DESIGN aggregated downstream from `ohlcv_1s`, never fetched directly
  (`tradfi-databento-sourcing-ssot.md`: ''Databento doesn''t even serve a 15m schema''; a code comment at
  `umi_tick_provider.py:633-636` confirms ''a (CBOE, ohlcv_15m) request now falls through to the databento path below''
  after the 2026-06-25 Yahoo-VIX-15m removal) — so MTDS''s own tick-download layer is structurally the wrong place to
  ever expect these to succeed; they should either be filtered out of the download layer''s expected-coverage the same
  way ICE/KRX were narrowed, or the downstream aggregator needs to be the thing that satisfies this manifest cell (not
  yet confirmed which is intended). (3) `corporate_action_confirmed`/`earnings_result` are a MISCLASSIFICATION —
  confirmed via grep that ALL real capture code for these two data_types (`corporate_actions_calculator.py`,
  `earnings_results_calculator.py`, `yfinance_earnings_adapter.py`) lives entirely in **features-service**''s calendar
  module, a structurally separate service writing to its own bucket/manifest per the
  `macro_micro_econ_data_capture_audit_2026_06_05.md` finding (''features-calendar-service rollup: bucket="", 0 shards,
  0% completion'') — yet `instruments-service/scripts/enumerate_expected_universe.py` seeds
  `expected_unattempted`/`attempted_failed` rows for these into the MTDS TICK manifest (`market-data-tick-tradfi-prd`),
  a cell that literal never has a chance to be satisfied from that bucket.'
status: open
nature: notes
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, instruments-service, features-service]
scope: [engineer, admin]
tags:
  [
    tradfi,
    databento,
    mbp_10,
    ohlcv_15m,
    ohlcv_24h,
    corporate_action_confirmed,
    earnings_result,
    expected-coverage,
    honest-coverage,
    data-correctness,
    registry-adapter-mismatch,
  ]
related:
  [
    /plans/archive/issues/krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md,
    /plans/archive/issues/tradfi_ice_ohlcv_1m_no_working_fetch_path_2026_07_13.md,
    /plans/archive/issues/tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md,
    /plans/archive/issues/tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md,
    /plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md,
    /plans/archive/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-15
parent_epic: tradfi_master
priority: P2
source:
  [
    "operator report: batch of #data-pipeline-alerts DP_RUN_MOSTLY_EMPTY CRITICAL alerts, window 2026-07-14
    23:50Z-2026-07-15 00:19Z, triaged 2026-07-15",
  ]
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
execution_scope: local-only
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.7
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
last_updated: 2026-07-16
---

# TRADFI mbp_10 / ohlcv_15m / ohlcv_24h / corporate_action_confirmed / earnings_result — unreachable fetch paths

## What I found (read-only code trace, no changes made)

Triaging the alert batch's TRADFI 100%-failed cells against `/codex/02-data/tradfi-databento-sourcing-ssot.md` (cited
authoritative for TradFi sourcing gotchas) plus a direct code read across
`market-tick-data-service`/`unified-api-contracts`/`instruments-service`/`features-service`. All three mechanisms below
were verified via grep + read, not assumed.

### (1) `mbp_10` — genuine adapter-wiring gap (scenario "a": broken/unimplemented path)

> **CORRECTED (2026-07-15, plan-reconcile)**: per
> `tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md`'s live query of the same manifest snapshot,
> the specific 1,186 `mbp_10` `attempted_failed` rows counted in this doc's summary/finding (1) are NOT explained by the
> `_DATABENTO_SUPPORTED_DATA_TYPES` gap below — all 1,186 are NYSE/KRX/NASDAQ out-of-scope-instrument rows carrying
> `error_reason="EXPECTED_SOURCE_NOT_AVAILABLE"`, since reclassified `attempted_failed` → `empty_confirmed` (honest
> absence, not an adapter-wiring failure). The `_DATABENTO_SUPPORTED_DATA_TYPES` allowlist gap described below is still
> a real, independently-confirmed code-level finding (CME wants `mbp_10`, the allowlist excludes it) — it just does not
> account for the 1,186-row figure this doc originally attributed to it. Original framing left in place below per this
> workspace's correct-don't-silently-rewrite convention.

- `market_tick_data_service/adapters/umi_tick_provider.py:143`:
  `_DATABENTO_SUPPORTED_DATA_TYPES = frozenset({"trades", "ohlcv_1s", "ohlcv_1m", "tbbo"})` — `mbp_10` is absent.
- This set gates `fetch_tick_data_for_venue`'s `_route_databento` call (line 467:
  `db_data_types = [dt for dt in db_data_types if dt in _DATABENTO_SUPPORTED_DATA_TYPES]`) — when the filtered list is
  empty the function returns before ever calling `download_batch_df` (lines 468-470), so `mbp_10` requests through the
  generic tick-download path can never reach the real fetch code.
- That real fetch code DOES exist and is live: `databento_fetch.py:131`, `_resolve_databento_schema`'s `schema_map` has
  `"mbp_10": db.Schema.MBP_10,  # L2 — time-floored to 1mo"` — dead code on this call path, unreachable given (1) above.
- `configs/venue_data_types.yaml:168-171` independently declares CME's `futures_chain`/`options_chain`
  `tick_window: [trades, tbbo, mbp_10]` — config explicitly wants `mbp_10`.
- `market_data_categories.py` (UAC) registers `mbp_10` as a valid TradFi data_type; the sourcing SSOT documents it as a
  real, fetchable L2 Databento schema (1-month free lookback window) — nothing in the SSOT says `mbp_10` is unsupported
  or by-design-excluded, unlike `ohlcv_15m`/`ohlcv_24h` below.
- **Net**: every attempt to backfill/capture `mbp_10` for a Databento venue through the standard tick-download
  orchestration is silently dropped to an empty result before any network call — the resulting manifest cell can never
  show `captured`. Whether this manifests as `attempted_failed` specifically (vs. `empty_confirmed`) depends on
  orchestrator-level sentinel classification of a requested-but-never-attempted data_type, which was **not traced to the
  manifest-write layer** in this pass (time-boxed triage) — flagging as the next step for whoever picks this up.

### (2) `ohlcv_15m` / `ohlcv_24h` — aggregated-downstream by design, still reaches the download layer

- `/codex/02-data/tradfi-databento-sourcing-ssot.md` (§ "Non-Databento sources are UNTOUCHED by these guards"): "Note:
  Databento doesn't even serve a 15m schema — `ohlcv-15m` would only raise if someone wrongly routed it through the
  Databento fetch path, which nothing does" — and the OHLCV policy section: "We fetch both `ohlcv-1s` and `ohlcv-1m` ...
  and aggregate the coarser bars (15m / 1h / 24h) downstream."
- BUT `umi_tick_provider.py:633-636` carries a **live code comment** contradicting the "nothing does" claim: "CBOE
  VIX-15m: the Yahoo `^VIX-15m` index fetch was REMOVED 2026-06-25 (operator)... a `(CBOE, ohlcv_15m)` request now
  **falls through to the databento path below**." CBOE is in `_DATABENTO_VENUES` (line 139), so an `ohlcv_15m`/
  `ohlcv_24h` request for CBOE (or any other Databento venue) does reach `_route_databento`, gets filtered by the same
  `_DATABENTO_SUPPORTED_DATA_TYPES` gap as `mbp_10` above, and returns nothing.
- This is a genuine open question, same shape as the already-resolved KRX/ICE cases: is the fix "narrow
  `expected_coverage`/`VENUE_DATA_TYPE_CAPABILITIES` to stop declaring `ohlcv_15m`/`ohlcv_24h` as MTDS-tick-download
  expected coverage" (matching the KRX/ICE narrowing precedent), or "wire a real downstream-aggregation-driven writer
  that satisfies this exact manifest cell so the expectation is honest"? Not resolved here — needs the same
  operator/architecture call the KRX and ICE docs got, not a guess.

### (3) `corporate_action_confirmed` / `earnings_result` — misclassification, real capture lives in a different service

- Zero real fetch/handler code in `market-tick-data-service` for either data_type — grep across the whole repo (excl.
  tests) finds only a one-off restamp script (`scripts/restamp_tradfi_cf3_pipeline_mode_2026_07_08.py`) and a routing
  regression test (`test_umi_tick_provider_routes.py`) confirming KRX **honest-empties** `corporate_action_confirmed` on
  request (`mock_krx.assert_not_called()`, `result.empty` — the 2026-07-12 KRX narrowing fix's own regression test).
- The REAL capture code for both lives entirely in **features-service**:
  `calendar/engine/calculators/ corporate_actions_calculator.py`,
  `calendar/engine/calculators/earnings_results_calculator.py`, `calendar/adapters/ yfinance_earnings_adapter.py`,
  `calendar/cli/handlers/corporate_actions_handler.py` — a structurally separate service, per
  `macro_micro_econ_data_capture_audit_2026_06_05.md`'s own Category-A framing ("corporate actions (Polygon), earnings
  (yfinance) — features-service `calendar/`") and its live Phase-0 finding: "`features-calendar- service` rollup:
  `bucket=""`, 0 shards, 0% completion... not populated and not even monitored."
- Yet `instruments-service/scripts/enumerate_expected_universe.py` is the only non-test, non-restamp-script consumer of
  `corporate_action_confirmed`/`earnings_result` outside UAC/features-service — it seeds
  `expected_unattempted`/`empty_confirmed`/(and per this alert) `attempted_failed` rows for these types **into the MTDS
  tick manifest** (`market-data-tick-tradfi-prd`), a bucket the real capture code never writes to. This exact population
  was already partially characterized by `tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md`'s CF-3
  sub-finding (28,344 blank-`pipeline_mode` rows including 8,392 `corporate_action_confirmed` + 8,392 `earnings_result`,
  root-caused to a `SOURCE_PRIORITY` registry gap in the SAME enumerator) — that doc's fix
  (`instruments-service@699e2cf`) addressed the blank-`pipeline_mode` symptom but did NOT address the deeper
  cross-service misclassification: these cells are seeded as MTDS-tick-bucket expectations for a capture pipeline that
  structurally cannot ever write there.
- **Net**: the MTDS `market-data-tick-tradfi-prd` manifest cell for `corporate_action_confirmed`/`earnings_result` can
  never be satisfied — it is measuring the wrong bucket for data that IS being captured (features-service's own,
  separately-unmeasured bucket).

## Why it matters

All 3 mechanisms independently guarantee a permanent, non-self-healing 100% `attempted_failed` rate for their respective
(asset_group, data_type) cells — no amount of retrying the backfill will ever close them, matching the alert-batch's own
observation that these are the "most suspicious" (exactly-100%) cells. This is the same registry- vs-adapter-mismatch
failure CLASS already found + fixed twice this week for KRX (`ohlcv_1m`/`ohlcv_15m`) and ICE (`ohlcv_1m`) — the fix
pattern (narrow the registry, or build/redirect the missing wiring) is established precedent, just not yet applied to
these 5 cells.

## Recommended decision (per-mechanism, not one-size-fits-all)

1. **`mbp_10`**: this looks like a straightforward add — `_DATABENTO_SUPPORTED_DATA_TYPES` should include `mbp_10` (the
   fetch schema already exists and is wired at the `databento_fetch.py` layer; only the pre-flight allowlist one level
   up is missing it). Low-risk, mechanical fix — recommend building it rather than narrowing the registry, since (unlike
   KRX/ICE) genuine Databento coverage exists and is already coded, just unreachable.
2. **`ohlcv_15m`/`ohlcv_24h`**: needs an operator/architecture call — narrow MTDS-tick-download's expected coverage
   (matching the KRX/ICE precedent) vs. wire a real downstream-aggregation writer that satisfies the cell honestly.
3. **`corporate_action_confirmed`/`earnings_result`**: needs an operator/architecture call — either (a) stop seeding
   these as MTDS-tick-bucket expected cells (the enumerator should not declare coverage for a bucket the real capture
   pipeline never writes to), or (b) if the intent really is for MTDS to own tick-level corporate-action/earnings
   confirmation data distinct from features-service's calendar feature layer, build the missing MTDS-side adapter. Given
   features-service already owns this domain and is itself unpopulated (0 shards per the macro audit), option (a) looks
   like the lower-risk default, but this is a genuine product-intent question, not a mechanical fix.

## Open work (tracked todos)

- [x] ✅ [CODE] P2. `market-tick-data-service`: add `mbp_10` to `_DATABENTO_SUPPORTED_DATA_TYPES`
      (`umi_tick_provider.py:143`) and add a regression test asserting a CME `mbp_10` request reaches
      `download_batch_df` (not silently filtered to empty) — `market-tick-data-service@e2018167`. 3 new tests (routing
      pin + a `configs/venue_data_types.yaml` CME-tick_window ⊆ `_DATABENTO_SUPPORTED_DATA_TYPES` invariant, same
      "registry-declared ⊆ adapter-supported" shape as the KRX/ICE precedents) + the existing 112-test
      `test_umi_tick_provider_routes.py`/`test_umi_tick_provider_coverage.py` suite all green (115 passed); full MTDS
      `quality-gates.sh --no-fix` green. See "Resolution — mbp_10 (2026-07-15)" below for what this does and does NOT
      unblock; the L2 30-day-lookback manifest-classification sub-question folds into the existing P3 VERIFY todo below
      (not resolved by this fix — still open).
- [x] ✅ [DESIGN] P2. Operator/architecture decision for `ohlcv_15m`/`ohlcv_24h`'s MTDS-tick-download expected coverage
      — AUDITED (per `data_pipeline_alerts_batch_remediation_2026_07_15.md`'s operator-directed audit todo) + CBOE's
      slice mechanically fixed via the KRX/ICE narrowing precedent. Remaining sub-findings (no aggregation writer exists
      anywhere despite 3 docs/comments claiming one does; `"YAHOO_FINANCE"` is a phantom no-adapter venue inflating the
      failure counts) still need their own decisions — see "Resolution — ohlcv_15m/ohlcv_24h audit (2026-07-15)" below
      for the full writeup + 2 new scoped follow-up todos.
- [x] ✅ [DESIGN] P2. Operator/architecture decision for `corporate_action_confirmed`/`earnings_result`'s
      MTDS-tick-bucket expected coverage vs. features-service's actual ownership of this domain — **operator decided
      (interactive session, 2026-07-15): option (a), stop instruments-service from seeding these as expected cells in
      the MTDS tick manifest** (see this doc's summary + `## Resolution` below for the full reasoning). Shipped
      `instruments-service@03f71c81`. features-calendar-service's own manifest/rollup gap (separately flagged "0 shards,
      0% completion" in `macro_micro_econ_data_capture_audit_2026_06_05.md`) remains OUT OF SCOPE for this fix — flagged
      to whoever owns that doc as the correct place to measure this data going forward. See "Resolution —
      corporate_action_confirmed / earnings_result (2026-07-15)" below for what shipped and the historical-rows
      decision.
- [ ] [VERIFY] P3. Trace the orchestrator/sentinel classification layer to confirm exactly how a
      requested-but-`_DATABENTO_SUPPORTED_DATA_TYPES`-filtered-out data_type gets recorded (`attempted_failed` vs.
      `empty_confirmed`) — not traced to the manifest-write layer in this pass; needed to fully close out mechanism
      (1)/(2)'s classification question.
- [ ] [DESIGN] P2. Decide whether real aggregated `ohlcv_15m`/`ohlcv_24h` TradFi bars are wanted (not just alert
      silence). If yes: build a downstream-aggregation writer (reuse `features-service`'s already-tested exact-OHLC
      `candle_resampler.py` engine rather than writing new resampling logic) that resamples CBOE's Databento
      `ohlcv_1s`/`ohlcv_1m` into `ohlcv_15m` and writes it into the MTDS tick-manifest namespace — this is the ONLY
      concrete unfed consumer found (`vix_features` in UAC `required_inputs.py` requires `(tradfi, ohlcv_15m)` for
      `features-service`'s `vix_calculator.py`). If no: `vix_features`' required-input declaration should be corrected
      to `ohlcv_1m` only (which IS real and flowing). See "Resolution" below — this is a real multi-service gap, not a
      registry-narrowing fix like the CBOE item above.
- [x] ✅ [DATA] P2. `"YAHOO_FINANCE"` is declared as a literal TradFi venue (`VENUES_BY_ASSET_GROUP["tradfi"]`,
      `unified_api_contracts/registry/market_data_categories.py:329`) with `NO_ADAPTER_YET`
      (`registry/venue_adapter_keys.py:137`) and is expected for `["ohlcv_15m","ohlcv_24h"]`
      (`registry/expected_coverage.py:185`) — every cell is structurally unfulfillable, same misclassification shape as
      the already-decided `corporate_action_confirmed`/`earnings_result` fix elsewhere in this doc. Likely the DOMINANT
      contributor to the reported 3589/3590 `ohlcv_15m` + part of the 2852/7118 `ohlcv_24h` failure counts. Not
      blind-fixed here: the existing code comment explicitly flags a "manifest churn" risk (real historical rows may be
      stamped under this venue name) — needs the same structured operator decision the cefi-orphan-rows item got, not a
      silent delete. See "Resolution" below. **CORRECTED (2026-07-15, operator-directed re-check — see "Verdict — Yahoo
      Finance source-vs-venue investigation" below): the "phantom venue, no adapter" framing was WRONG in the operator's
      favor.** `YAHOO_FINANCE` is not unimplemented — it is a real, live, precedented data SOURCE (2 of its 3 named uses
      — DXY via venue=ICE, KRW/USD via venue=FX — already fetch successfully today through `market-tick-data-service`'s
      `YahooFinanceAdapter`/`route_yahoo_tradfi`). The bug is genuinely a MODELING error exactly as the operator said:
      `VENUE_DATA_TYPE_CAPABILITIES`/`expected_coverage.py` double-declare the same coverage under a phantom
      `"YAHOO_FINANCE"` VENUE key that no fetch code ever stamps (real rows land under venue=ICE/FX/KRX, source=yahoo).
      **Still not blind-fixed** — deeper trace found `get_expected_data_types_for_venue()` falls through to the
      ALL-10-datatypes blanket whenever a venue's capability dict is empty/absent
      (`market_data_categories.py:1881-1884`, the same footgun `test_data_status_registries.py`'s KRX docstring already
      documents) — naively deleting the 2 `YAHOO_FINANCE` capability entries would turn a 2-datatype phantom into a
      WORSE 10-datatype one. The correct fix is an exclusion at the manifest-SEEDING site (mirroring the
      `_tradfi_mtds_tick_manifest_data_types()` pattern already shipped for
      `corporate_action_confirmed`/`earnings_result` above), not a raw registry-entry deletion — genuinely needs its own
      careful pass, not rushed here. **SHIPPED 2026-07-15 — `unified-api-contracts@fec3f110`** (evidence:
      `bash scripts/quality-gates.sh --no-fix` GREEN 157s on the committed tree; python verify-check `ALL CHECKS PASS`;
      201 affected-test-file tests pass). Removed `YAHOO_FINANCE` from ALL 5 venue-shaped registries — the tradfi
      `VENUES_BY_ASSET_GROUP` list + its `VENUE_DATA_TYPE_CAPABILITIES` block (`market_data_categories.py`),
      `expected_coverage.py`, `venue_adapter_keys.py`, `data_availability.py` — and KEPT the SOURCE modeling
      (`data_source_continuity.py` / `capability_declarations/_tradfi.py` / `external/yahoo_finance/`). The
      empty-caps→ALL-10-datatypes footgun is neutralized **by the de-enumeration itself**: removing it from
      `VENUES_BY_ASSET_GROUP` makes `get_valid_data_types_for_venue("YAHOO_FINANCE") == []` (no asset_group), so
      `get_expected_data_types_for_venue("YAHOO_FINANCE") == []` — **no code guard added** (a blanket
      `NO_ADAPTER_YET→[]` guard would break the 5 legit sports odds venues BETFAIR_*/DRAFTKINGS/FANDUEL that genuinely
      rely on the fallback; verified they still return their 10 fallback types). Added a defensive doc-comment on
      `get_expected_data_types_for_venue` documenting the footgun (docs-only) + a regression test class
      (`TestYahooFinancePhantomVenueRemoved`) locking in `==[]` for YAHOO_FINANCE AND the sports-venue fallback
      survival. Blast-radius fixes in the same commit: dropped `YAHOO_FINANCE` from `EXPECTED_SENTINEL_VENUES`
      (`test_venue_adapter_keys.py`), emptied the now-stale `_KNOWN_SOURCE_AS_VENUE` allowlist
      (`test_venue_source_adapter_parity.py`), and the KRX-gap docstring. **NOTE (multi-agent collision — needs
      coordinator awareness):** commit `fec3f110` also inadvertently absorbed a live
      `cefi_completion_program workstream     E` change to the SAME file (re-adding `"liquidations"` to bare `OKX` in
      `VENUE_DATA_TYPE_CAPABILITIES`, a "CORRECTION to the initial removal") — the workstream-E agent edited
      `market_data_categories.py` during this task's edit window and quickmerge's whole-file staging swept the OKX hunk
      in. That OKX change is preserved, coherent, and QG-green on the branch; it was NOT reverted (reverting would
      delete workstream-E's work; splitting needs a banned force-push). Workstream-E should be told its OKX bare-venue
      liquidations correction already landed in `fec3f110`.
- [x] ✅ [DATA] P3. **DONE 2026-07-16 — deploy-first then clean, verified to HOLD.** Operationalized the
      `unified-api-contracts@fec3f110` YAHOO_FINANCE venue removal (stopped the nightly re-seeding) AND deleted the
      orphaned rows so they stay gone. **(1) Stopped the seeder**: the nightly seeder is Cloud Run job
      `expected-universe-v2-tradfi` (Cloud Scheduler `expected-universe-v2-tradfi-daily`, `30 1 * * *` = the 01:31:30Z
      `attempted_at` in the manifest), running `enumerate_expected_universe.py`'s
      `_yield_v2_tradfi_non_trading_day_rows` over `VENUES_BY_ASSET_GROUP["tradfi"]`. (`is-daily-enum-tradfi` runs
      `-m instruments_service --operation     instruments --mode batch` = the instrument catalogue, NOT tick-manifest
      seeding — not a YAHOO seeder.) **BLOCKER FOUND + FIXED (big finding)**: the IS Dockerfile base bump
      `instruments-service@6d33b9d5` pinned UTL base `sha256:b7c57243` (cut 2026-07-15 17:54:46Z), which had YAHOO
      removed but PREDATED `unified-api-contracts@7754661a` (18:14:29Z, "add `venue_data_type_has_batch_source`") that
      the current enumerator imports — so a run on that image crashed at import with
      `ImportError: cannot import name 'venue_data_type_has_batch_source'`. Re-bumped the IS base to the newer UTL
      `0.55.0/latest` `sha256:be51b33f` (cut 23:27:01Z, bundles all of {YAHOO removed, CBOE ohlcv_24h, the new symbol} —
      verified in-image `Evidence: cloudbuild=70dbc75f-c8db-4245-b3bb-fd175829f6b3` SUCCESS):
      `instruments-service@3e5b1039` (QG-green). Built it `Evidence: cloudbuild=d00de7ec-8272-49d5-ab9d-f0ded059b0e6`
      SUCCESS → IS image digest `sha256:d569a6548d4dde511a994c5e35f0dd043aa6f1b67c9375d1f51f3793bddee98d`; pinned
      `expected-universe-v2-tradfi` to it. **(2) Verified seeding stops**: executed the job on the new image (exec
      `expected-universe-v2-tradfi-lwsqs`, SUCCEEDED) → its fresh per-VM shard `enum-universe-v2-tradfi.parquet` carried
      **5,709 rows, YAHOO=0**, real venues still seeded (CME 2244 / NYSE 1122 / NASDAQ 871 / ICE·CBOE·KRX·FX 368 each);
      post-consolidation the canonical had **0** YAHOO rows with `attempted_at` after the run (max stayed
      2026-07-15T01:31:30Z). **(3) Cleaned at the source**: resurrection vector = only the canonical (per-VM
      `_legacy_seed.parquet` carried 0 YAHOO). Drained + paused the `market-data-tradfi` consolidator, snapshotted, and
      deleted `venue==YAHOO_FINANCE` from `_index/availability_index.parquet` (**11,676→0**, 5,564,746→5,553,070 rows)
      AND `_index/expected_universe_ranges.parquet` (the honest-coverage full-history denominator, which the
      `--start-date` enum run does NOT regenerate: **5,080→0**, 63,514→58,434 rows). Snapshots (rollback):
      `_index/snapshots/pre_yahoo_phantom_venue_delete_20260715T231453Z_{availability_index,expected_universe_ranges}.parquet`.
      **(4) HOLD proven**: resumed the consolidator + forced a merge, then watched ≥5 real merge cycles (canonical
      rewritten 23:17→23:22Z) — canonical, ranges, and `_legacy_seed` all stayed **YAHOO=0**; no resurrection. Cleanup
      predicate/pattern mirrors `market-tick-data-service/scripts/delete_tradfi_aggregate_phantom_markers_2026_07_07.py`
      (download → STOP-ON-SURPRISE [0 `captured` rows] → snapshot → filter → write → verify gate). See "Resolution —
      YAHOO_FINANCE phantom-venue seeding stopped + orphan rows cleaned (2026-07-16)" below.
- [x] ✅ [CODE] P2. `market-tick-data-service`: US Treasury-yield tenors (`CBOE:INDEX:US3M/US2Y/US5Y/US10Y/US30Y-USD`,
      already declared in UAC's `YAHOO_INDICES` registry, `tradfi_instrument_universe.py:521-525`) have NO working fetch
      path anywhere — genuinely missing, not a modeling error, contrary to part of the operator's claim.
      `_umi_yahoo.py`'s `route_yahoo_tradfi()` only routes venue in `("FX", "KRX", "ICE")`; `"CBOE"` was never added, so
      `fetch_yahoo_indices("CBOE", ...)` (the exact function whose docstring says it's "reusable for other YAHOO_INDICES
      venues (CBOE tenors...) though only ICE calls it today") is never invoked. **Do not naively add `"CBOE"` to that
      tuple** — CBOE already routes VX-futures `ohlcv_1s`/`ohlcv_1m` through Databento via the SAME dispatch function;
      `route_yahoo_tradfi`'s current all-or-nothing per-venue branch
      (`if data_types and "ohlcv_24h" not in data_types:     return pd.DataFrame()`) would silently short-circuit live
      CBOE VX-futures capture instead of falling through to the Databento path below it — a real regression risk, not a
      mechanical one-liner. Needs an instrument-type-aware (index vs future) or explicit-data_type routing change, plus
      adding `ohlcv_24h` to CBOE's `VENUE_DATA_TYPE_CAPABILITIES`/`expected_coverage.py` entries (currently
      `["ohlcv_1s", "ohlcv_1m"]` only, `expected_coverage.py:173`) so the `venue_fetch.py` per-shard UAC-intersection
      step doesn't filter the request out before it ever reaches routing — **the UAC-registry half is a separate,
      out-of-scope follow-up, new todo below** (mirrors the mbp_10/CME precedent above: routing fixed here, UAC
      capability restoration deferred). See "Verdict — Yahoo Finance source-vs-venue investigation" below for full
      evidence.
- [x] ✅ [DATA] P3. **DONE 2026-07-15 (operator decided ENABLE)** — `unified-api-contracts@2ace1fca`. Added `ohlcv_24h`
      to `VENUE_DATA_TYPE_CAPABILITIES["CBOE"]` (start `2000-01-03` = `US_TREASURY_YIELD_DAILY_FIRST_DATE`, mirroring
      the ICE:DXY Yahoo-daily precedent) + `EXPECTED_COVERAGE_BY_ASSET_GROUP["tradfi"]["CBOE"]`, so `venue_fetch.py`'s
      UAC-intersection no longer filters `(CBOE, ohlcv_24h)` out before the shipped routing fix
      (`market-tick-data-service@764e7170`) sends it to Yahoo. VX-futures `ohlcv_1s`/`ohlcv_1m` stay on the Databento
      path (the routing fix's data_type discriminator, 4 regression tests). Confirmed the footgun invariant held (CBOE
      dict was non-empty, so the addition did not trip the ALL-10 fall-through). 5 new regression tests
      (`TestCboeTreasuryOhlcv24hEnabled`) + the existing `tradfi["CBOE"]` assertion updated; `quality-gates.sh --no-fix`
      green (234s). **Operator decision** (`data_pipeline_alerts_batch_remediation_2026_07_15`, AskUserQuestion): enable
      now — treasury yields are wanted macro reference data, distinct from the mbp_10/CME MVP-scope gate left closed.
      (Original ask: add `ohlcv_24h` to CBOE's `VENUE_DATA_TYPE_CAPABILITIES` + `EXPECTED_COVERAGE_BY_ASSET_GROUP`,
      since `market-tick-data-service@764e7170`'s routing was correct but structurally unreachable while
      `venue_fetch.py`'s UAC-intersection filtered `(CBOE, ohlcv_24h)` out pre-routing. The footgun caution was
      confirmed non-applicable — CBOE's dict was non-empty, so the addition did not trip the ALL-10 fall-through.)

## Resolution — mbp_10 (2026-07-15)

Fixed the mechanical adapter-wiring gap exactly as recommended: `market-tick-data-service@e2018167` adds `"mbp_10"` to
`_DATABENTO_SUPPORTED_DATA_TYPES` (`umi_tick_provider.py:143`).

**Fetch path verified genuinely end-to-end before shipping** (not just the schema-map line cited in the original
diagnosis) — read `databento_fetch.py` in full: `_resolve_databento_schema` maps `mbp_10` → `db.Schema.MBP_10` AND calls
UAC's `assert_schema_allowed("mbp_10")`, which passes (`mbp-10` is in `ALLOWED_DATABENTO_SCHEMAS`, billing level L2, not
in the banned-OHLCV set). Downstream, `_fetch_timeseries_range` calls
`assert_databento_request_allowed(dataset, schema, start)` — dataset `GLBX.MDP3` (CME) is in
`ALLOWED_DATABENTO_DATASETS`, and the L2 30-day free-lookback window is enforced (`LEVEL_MAX_LOOKBACK_DAYS["L2"] = 30`).
So a real, correctly-billing-gated Databento request now flows for any `mbp_10` request that reaches `_route_databento`
— no further gap in the fetch mechanics themselves.

**Important scope caveat found during this pass (not identified in the original diagnosis) — my fix alone does NOT yet
cause CME `mbp_10` capture to start flowing in production.** `venue_fetch.py`'s per-shard dispatch (lines ~444-459)
intersects EVERY `data_types` request — both the default path and any explicit `--data-types` CLI override — against
`get_expected_data_types_for_venue("CME")` (UAC, backed by `VENUE_DATA_TYPE_CAPABILITIES`) BEFORE it ever reaches
`fetch_tick_data_for_venue`/`_route_databento`. As of this fix, `VENUE_DATA_TYPE_CAPABILITIES["CME"]` in UAC's
`market_data_categories.py` only declares `{"ohlcv_1s", "ohlcv_1m"}` — the 2026-05-15 "OHLCV-only MVP" operator scope
(`tradfi_ohlcv_only_mvp_backfill_2026_05_15.md`). `trades`/`tbbo`/`mbp_10` were deliberately deferred to a named
successor plan, `plans/archive/2026_05/tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md` — archived
`status: complete`, but its own body shows Phases 1-2 (the actual `VENUE_DATA_TYPE_CAPABILITIES` re-merge) marked
`[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]` and migrated to the `tradfi_master` epic, gated on an operator Databento
PAYG-spend sign-off (its own Phase 8) — i.e. the registry-level restoration was never actually re-applied to UAC. One
sub-item of that same plan (Phase 6 P1, "Add `mbp_10` to MTDS DatabentoAdapter supported schemas") carries real evidence
(`uac@9f8373f + mtds@020442b`) but only the lower `_resolve_databento_schema` mapping shipped then — the
`umi_tick_provider.py` pre-flight allowlist this issue's finding (1) named was never actually fixed until today, despite
that plan's checkbox reading ✅. **So**: this fix completes the adapter-layer half of that stalled 2026-06 restoration
and is correct/necessary regardless of what happens next, but a live default or explicit-`--data-types` MTDS
orchestrator run for CME will still filter `mbp_10` out at the UAC-intersection step in `venue_fetch.py` until
`VENUE_DATA_TYPE_CAPABILITIES["CME"]` is separately restored — that registry change is UAC-repo, operator-PAYG-gated,
and out of this task's scope (touch only `market-tick-data-service` per this issue's brief). **Flagging for whoever
picks up `tradfi_master`'s post-cutover residual**: re-running `tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md`
Phases 1-2 against current UAC would fully close the loop this fix opened.

This also means the historical 1186/1186 100% `attempted_failed` `mbp_10` manifest rows the alert batch surfaced are
most likely a fixed historical count (residue from before the 2026-05-15 MVP narrowing, or from whatever partial
pre-narrowing live run originally hit the fetch path) rather than actively-growing — not independently re-verified
against a live manifest query in this pass (would require the P3 VERIFY trace below).

## Resolution — ohlcv_15m/ohlcv_24h audit (2026-07-15)

Per `data_pipeline_alerts_batch_remediation_2026_07_15.md`'s operator decision #2 ("this is very likely NOT greenfield
design work... UAC/instruments-service/MTDS already has infrastructure for per-venue source-capability constraints and
this 'might need completion' rather than a new design — AUDIT FIRST"), this section is that audit. Read (not grepped)
`/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`, `/codex/02-data/tradfi-databento-sourcing-ssot.md`,
`/codex/02-data/honest-coverage-model.md`, and the relevant UAC/instruments-service/MTDS/market-data-processing-service
source directly.

**Verdict: the operator's prior was substantially correct.** The per-venue source-capability/granularity distinction he
described (Databento-uncovered venues like FX-spot/Korean-equities get whatever granularity their real source provides,
which may only be daily; Databento-covered venues should get finer bars, not be capped) is **already encoded and mostly
correct** in two complementary UAC registries — this was a completion + drift-cleanup task, not new design.

**1. What already exists (with citations):**

- `unified_api_contracts/registry/expected_coverage.py::EXPECTED_COVERAGE_BY_ASSET_GROUP["tradfi"]` (the "what we plan
  to fill" policy layer, line ~145) +
  `unified_api_contracts/registry/market_data_categories.py::VENUE_DATA_TYPE_CAPABILITIES` (the "what a venue could
  emit" layer, line ~1153) **already implement the operator's exact per-venue distinction**:
  - Databento-covered venues `CME`/`NASDAQ`/`NYSE` → `{ohlcv_1s, ohlcv_1m}` ONLY, deliberately excluding
    `ohlcv_15m`/`ohlcv_24h` (Databento doesn't serve those schemas — by design, per the sourcing SSOT).
  - Databento-NOT-covered venues `ICE` (Yahoo DXY "usd index"), `KRX` ("Korean equities"), `FX` (KRW/USD) →
    `{ohlcv_24h}` ONLY — daily genuinely IS the ceiling (Yahoo is the only source) — **this is precisely the operator's
    own example**, and it's already modeled correctly.
  - `CBOE` (mixed: VX futures via Databento +, until this fix, a legacy Yahoo VIX-cash-index `ohlcv_15m` entry).
- `unified_api_contracts/registry/data_source_continuity.py::_SOURCE_RESOLVERS` + `get_source_for_instrument()` /
  `data_types_for_instrument()` (lines 253-297) — a SECOND, complementary per-instrument temporal source-capability
  registry (KRX/DXY/Treasury-yield-index → `ohlcv_24h` via Yahoo, each with its own genesis-date floor). This is exactly
  the kind of "per-(venue/instrument, data_type) → source + ceiling" mechanism the operator predicted existed.

**2. What was genuinely stale/missing — 3 distinct findings, not one:**

**(A) SHIPPED — CBOE's `ohlcv_15m` capability+expected entry was stale drift, not a design gap.** It was correct while
the VIX cash index came from Yahoo, but that fetch path was REMOVED 2026-06-25/26 (operator decision;
`data_source_continuity.py`'s own docstring confirms: "VIX-15m ohlcv_15m index was retired 2026-06-26... now purely the
VX FUTURES front contract... aggregated downstream"). The registry entries were never updated to match, so
`market_tick_data_service/adapters/umi_tick_provider.py`'s own LIVE code comment (lines 643-646) already documented the
resulting bug: a `(CBOE, ohlcv_15m)` request "now falls through to the databento path" (no 15m schema there) → 100%
`attempted_fail`. **Fixed via the exact same narrowing pattern as the already-shipped KRX (2026-07-12) and ICE
(2026-07-13) precedents** — removed `ohlcv_15m` from `VENUE_DATA_TYPE_CAPABILITIES["CBOE"]` and
`EXPECTED_COVERAGE_BY_ASSET_GROUP["tradfi"]["CBOE"]`, updated 2 stale test assertions + 3 stale comments.
`unified-api-contracts@78b9e899`. `quality-gates.sh --no-fix` green (295s, 0 new violations; only pre-existing unrelated
warnings). Verified no other consumer depends on the removed entry: `TestRegistryConsistencyWithCapabilities` still
passes (ohlcv_15m stays in the general `DATA_TYPES_BY_ASSET_GROUP["tradfi"]` set); the parquet-schema-completeness
fixture for historical `(tradfi, ohlcv_15m, CBOE)` rows (`test_schema_spec_completeness.py:859`) is untouched — it
documents already-captured historical data shape, unrelated to forward expected-coverage.

**(B) NOT SHIPPED — genuinely missing, recommend as scoped follow-up.** "Aggregate the coarser bars downstream" is
asserted in **three separate places** — `/codex/02-data/tradfi-databento-sourcing-ssot.md`, the `umi_tick_provider.py`
CBOE comment, and `market-data-processing-service`'s `TradfiOhlcv15mAdapter` docstring
(`app/adapters/tradfi/ohlcv_passthrough.py:397`: "VX futures aggregated from Databento ohlcv-1m") — **but no such
aggregator exists anywhere in the codebase.** Verified by reading `TradfiOhlcvPassthroughAdapter` in full: it is a bare
PASSTHROUGH adapter ("Handles pre-aggregated OHLCV data... IMPORTANT: For timeframes finer than the source data... most
candles will be NaN since we cannot subdivide") — it requires raw `ohlcv_15m`/`ohlcv_24h` to already exist upstream; it
does NOT resample from `ohlcv_1s`/`ohlcv_1m`. `market-data-processing-service`'s `GranularityDetector`
(`app/core/granularity_detector.py`) only LABELS the native granularity of whatever it's handed — also not a resampler.
A real, well-tested, exact-OHLC resampler DOES exist —
`features-service/features_service/delta_one/app/core/candle_resampler.py` (open=first/high=max/low=min/close=last/
volume=sum, right-edge labeled, polars `group_by_dynamic`) — but it's wired for feature-VALUE candle frames inside
features-service's delta_one module, not for writing MTDS-tick-manifest-satisfying rows. This causes NO alert noise for
CME/NASDAQ/NYSE (correctly excluded from expected coverage, so no gap there) but DOES leave a real, named downstream
consumer unfed: `unified_api_contracts/canonical/domain/features/required_inputs.py`'s `"vix_features"` entry requires
`InputReq(asset_group="tradfi", data_type="ohlcv_15m", ...)` for `features-service`'s
`features_service/volatility/calculators/vix_calculator.py` — and with CBOE's only historical `ohlcv_15m` source now
formally gone (finding A), this feature has no real feed at all. **Recommendation (new todo above)**: decide whether
real aggregated 15m/24h VIX-futures bars are actually wanted; if yes, build a small MTDS-side (or MDPS-side) writer
reusing the existing `candle_resampler.py` engine, scoped to CBOE only (the one venue with a live product need); if no,
correct `vix_features`'s required-input declaration instead. Either way this is a real cross-service wiring decision,
correctly NOT rushed in this pass.

**(C) FLAGGED, NOT shipped — same misclassification class as the already-decided `corporate_action_confirmed`/
`earnings_result` fix.** `"YAHOO_FINANCE"` is declared as a literal TradFi VENUE in `VENUES_BY_ASSET_GROUP["tradfi"]`
(`market_data_categories.py:329`), with its own code comment admitting: "legacy source-as-venue artifact (pre-existing;
flagged by the venue/source parity gate — not a real venue, kept to avoid manifest churn)." It's declared expected for
`["ohlcv_15m","ohlcv_24h"]` (`expected_coverage.py:185`) and has capability entries, but its adapter-key registration is
explicitly `NO_ADAPTER_YET` (`registry/venue_adapter_keys.py:137`) — every `(YAHOO_FINANCE, ohlcv_15m/24h)` cell is a
**structurally guaranteed permanent failure**. This is very likely the DOMINANT contributor to the reported 3589/3590
(100%) `ohlcv_15m` and part of the 2852/7118 (40%) `ohlcv_24h` failure counts — a phantom venue, not a routing bug.
**Not blind-fixed here**: the existing comment's own "manifest churn" flag means there may be real historical rows
stamped under this venue name that need a considered migration, not a silent registry delete — same shape as the
cefi-orphan-rows decision the operator already made elsewhere in this remediation pass. New todo above routes this to
the same kind of structured decision.

**Bottom line**: mostly a completion task, as the operator suspected. One completion shipped (CBOE narrowing,
precedent-matching, low-risk, tested). Two items remain genuinely open — not because the infrastructure doesn't exist,
but because (B) is a real, never-built multi-service aggregation writer (despite 3 places claiming one exists) and (C)
has an already-flagged "manifest churn" risk that deserves the same explicit operator decision its twin
(`corporate_action_confirmed`/`earnings_result`) already got.

## Verification addendum — live manifest re-query + alert-persistence root cause (2026-07-15, independent audit pass)

A second agent independently re-audited this same finding (2) in parallel (dispatched from the same plan todo before
either agent saw the other's result) and ran a live manifest query the prior pass above did not — worth folding in
rather than discarding, since it corrects one claim and adds the mechanism for why the alert keeps firing after the code
fix. Pulled `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` directly
(5,564,746 rows) and grouped by `(venue, capture_status)` for `ohlcv_15m`/`ohlcv_24h`.

**Correction to finding (C) above**: `"YAHOO_FINANCE"` is **not** the dominant contributor to `ohlcv_15m`'s
`attempted_failed` count — its live rows show `empty_confirmed: 996` / `attempted_failed: 0` for `ohlcv_15m`. The real
per-venue breakdown of the 3,589 `ohlcv_15m` `attempted_failed` rows is: `NYSE` 1,397, `CBOE` 1,242 (the mechanism (A)
above just closed going forward), `KRX` 743, `NASDAQ` 207 (sums to 3,589, matching the alert exactly). For `ohlcv_24h`
(2,852 `attempted_failed` total): `NYSE` 1,016, `YAHOO_FINANCE` 831, `KRX` 742, `NASDAQ` 206, `FX` 57 — YAHOO_FINANCE is
a real, meaningful contributor here (~29%) but not dominant; NYSE is larger. (C)'s underlying diagnosis — YAHOO_FINANCE
is a phantom `NO_ADAPTER_YET` venue declared expected for these two data_types — still stands and is still worth fixing;
only the "dominant contributor" sizing claim needed correcting.

**All of it is stale, not active**: every `ohlcv_15m`/`ohlcv_24h` `attempted_failed` row in the current manifest has
`attempted_at` between 2026-04-30 and 2026-07-07T07:29:16Z — none newer, i.e. unchanged for 8+ days as of this query
(2026-07-15) and predating BOTH narrowing fixes (instruments-service's tradfi MVP data_type-narrowing gate,
`instruments-service@31c15d88`, 2026-07-14 20:18 UTC, which independently closes the _seeding_ side for MVP-scoped
tradfi cells; and this doc's CBOE `unified-api-contracts@78b9e899` narrowing above). Same "fixed historical count, not
actively growing" shape already established for `mbp_10`'s 1186/1186 rows in the mbp_10 resolution section above — none
of these three cells (`mbp_10`, `ohlcv_15m`, `ohlcv_24h`) are currently being re-attempted and re-failing; the manifest
rows are dead residue from a 2026-07-07 batch run.

**Why the alert keeps firing anyway (new finding, ties the mbp_10/(C) open questions together)**:
`deployment-service/deployment_service/data_pipeline_monitors/meta_watchers.py::_read_attempted_failed_cells` (feeding
DP-FETCH-009 / `DP_RUN_MOSTLY_EMPTY`) reads `columns=["capture_status", "data_type"]` only from the WHOLE consolidated
manifest `_index` — no `attempted_at`/date column, no recency window of any kind — and `check_high_attempted_failed`
compares the resulting whole-history count against a flat `ATTEMPTED_FAILED_ABS_THRESHOLD = 500` (or 10% ratio at ≥50
count; same file, lines 217-219). A dead cell's stale count alone (3,589 and 2,852, both »500) is sufficient to keep it
`high=True` and paging indefinitely, completely independent of whether anything is currently broken. This is the
concrete mechanism behind the open question already flagged in the mbp_10 Progress Log entry above ("whether the
manifest/alerting layer has a clean mechanism to mark an operator-scope-deferred cell as `expected_unattempted`-with-
reason... so it stops presenting as an active failure") — and it applies identically to this doc's `ohlcv_15m`/
`ohlcv_24h` residue and to finding (3)'s deferred `corporate_action_confirmed`/`earnings_result` historical rows. **Not
fixed here** (touches DP-FETCH-009's alert-classification semantics, a cross-finding change, explicitly out of this
narrow audit's scope) — flagging as a single unified follow-up candidate rather than 3 separate piecemeal asks: either
(a) purge/reclassify the stale rows across all 3 cells in one pass, (b) add a date-recency window or an
"excluded-from-current-expected-coverage" exclusion to `_read_attempted_failed_cells`, or (c) both. Recommend whoever
picks this up read all 3 open "stale row" threads in this remediation wave together (this doc's mbp_10/ohlcv_15m/
ohlcv_24h, finding (3)'s corporate_action_confirmed/earnings_result, and the separate cefi blank-`data_type` orphan-rows
todo in `data_pipeline_alerts_batch_remediation_2026_07_15.md`) rather than resolving them one at a time.

## Resolution — corporate_action_confirmed / earnings_result (2026-07-15)

Fixed exactly as scoped in the dispatch: `instruments-service/scripts/enumerate_expected_universe.py` is confirmed
(re-verified fresh, not just trusted from the original diagnosis) to be the ONLY seeding site — its `enumerate_v2()`
default-resolution branch and `main()`'s CLI-default branch both resolved TRADFI's `data_types` list from UAC
`DATA_TYPES_BY_ASSET_GROUP["tradfi"]` unfiltered, which is what fed both the per-instrument lifecycle pass
(`_enumerate_v2_tradfi`) and the venue-grain non-trading-day pass (`_yield_v2_tradfi_non_trading_day_rows`) — i.e. every
row class this enumerator seeds into the MTDS tick manifest for tradfi.

**Scope precision (the exact risk the dispatch flagged):** `DATA_TYPES_BY_ASSET_GROUP["tradfi"]` itself is a UAC
cross-cutting registry consumed by several OTHER modules unrelated to MTDS (`market_data_categories.py` validity
matrices, `expected_coverage.py`, `mvp_scope.py`, `scripts/generate_ui_reference_data.py`, …) — editing it directly
would have de-registered `corporate_action_confirmed`/`earnings_result` as valid tradfi data_types system-wide,
including for whatever features-service's own manifest tracking eventually wants to do with that same "what data_types
are expected" knowledge. **Did not touch UAC.** Instead added a new tradfi-only helper,
`_tradfi_mtds_tick_manifest_data_types()` (+ `_TRADFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES` frozenset), and wired it
into the two `data_types` resolution sites in place of the raw `DATA_TYPES_BY_ASSET_GROUP.get("tradfi", [])` call — a
narrow, two-item exclusion scoped to this ONE enumerator's MTDS-tick-manifest seeding path only. UAC's registry is
regression-tested to remain untouched (`test_uac_data_types_by_asset_group_registry_itself_is_untouched`).

**Regression tests** (`tests/unit/scripts/test_enumerate_expected_universe_v2.py`, new
`TestTradfiMtdsTickManifestDataTypeExclusion` class, 4 tests): both types are confirmed present in UAC's registry
(fixture sanity-check, so the test isn't trivially-passing for the wrong reason); the new helper excludes exactly these
two and nothing else; `enumerate_v2(asset_group="tradfi")`'s default-resolution path (no explicit `--data-types`
override — the production default, mirroring `main()`'s CLI default) never emits either data_type across an
EQUITY@NASDAQ fixture (deliberately chosen because the G1-ENUM validity matrix already considers both VALID for that
shape, so the test actually exercises the exclusion rather than passing for an unrelated reason); UAC's own registry
constant is unchanged. Full suite: 165 tests passed in the touched test file, 14/14 golden-fixture tests passed,
`quality-gates.sh --no-fix` ALL PASSED (177s). Shipped `instruments-service@03f71c81`.

**Unrelated blocker hit + resolved while shipping**: the local `quality-gates.sh` run was red on
`test_expected_universe_golden.py::test_expected_matches_golden[tradfi]` for a reason wholly unrelated to this fix
(verified via a stash-isolated re-run: byte-identical failure with my diff stashed out) — a concurrent agent's
in-flight, uncommitted UAC edit (`unified-api-contracts@78b9e899`, the CBOE `ohlcv_15m` narrowing = this same doc's
finding (2), see the resolution section above) was live via the editable path-dependency, and once it landed as a commit
the checked-in `tradfi.json` golden fixture needed a resync. Waited for UAC to go clean, then regenerated ONLY the
tradfi golden via the sanctioned `scripts/regenerate_expected_universe_golden.py` (refuses while UAC/UTL are dirty — ran
only after confirming both clean) and reverted the script's unwanted cefi/defi/sports/prediction.json touches (pure
`json.dumps` formatting noise vs. the checked-in prettier-compacted style, zero content delta — those 4 asset_groups
were already passing) back to HEAD; prettier-formatted the tradfi fixture to match the checked-in convention so the
shipped diff is the true minimal 3-line delta (`captured_at`, `tuple_count` 41→40, removed
`["CBOE", "index", "ohlcv_15m"]`). Included in the same `instruments-service@03f71c81` commit since it was required to
get MY tradfi-scoped test green — did not touch any other finding's logic.

**Historical already-seeded rows — decision: defer, do not touch in this pass.** The alert batch's own numbers (807/807
`corporate_action_confirmed`, 799/799 `earnings_result`, both against `market-data-tick-tradfi-prd`) are the only counts
available; not independently re-verified against a live manifest query in this pass. Considered cleaning these up now
(mirroring the cefi-orphan-rows precedent elsewhere in this remediation wave) but chose to leave them as a documented
follow-up rather than force it, for the same reason the `mbp_10` resolution above did: this is PRODUCTION DATA MUTATION
(deleting/reclassifying live manifest rows) that deserves its own carefully-scoped pass — precisely identifying the
predicate, picking the sanctioned rewrite mechanism (this repo has several `reconcile_*`/`purge_*`/
`delete_phantom_rows_from_shards.py`-style precedents for exactly this shape of cleanup), a scan-only dry run, and
review — not something to bolt onto a code-scoping fix under the same commit. Stopping the seed going forward is the
higher-value, lower-risk half of this fix (it is what prevents the cell from growing further and re-triggering
`DP_RUN_MOSTLY_EMPTY`); the historical rows will age out of the manifest's rolling window naturally, or can be cleaned
up explicitly in a dedicated follow-up pass whenever someone picks up the `corporate_action_confirmed`/`earnings_result`
follow-up flagged to `macro_micro_econ_data_capture_audit_2026_06_05.md`'s owner above.

## Verdict — Yahoo Finance source-vs-venue investigation (2026-07-15, operator-directed re-check)

**Background**: an earlier pass this session (finding (C) above) framed `"YAHOO_FINANCE"` as a "phantom `NO_ADAPTER_YET`
venue... likely the DOMINANT contributor" to the `ohlcv_15m`/`ohlcv_24h` failure counts (later corrected by the
Verification addendum: NYSE/CBOE dominate `ohlcv_15m`, YAHOO_FINANCE is real-but-not-dominant for `ohlcv_24h`). The
operator (interactive session, 2026-07-15) pushed back on the "no adapter" framing itself: Yahoo Finance is a real,
intended DATA SOURCE already used for DXY, US treasuries, and KRW/USD daily OHLCV — the registry conflates "venue" with
"source" and should be corrected to reflect reality, not treated as a missing-adapter gap. Dispatched to re-investigate
for real rather than take either side's framing at face value. **Full workspace grep** (`yfinance`, `Yahoo`,
`YAHOO_FINANCE` across market-tick-data-service, instruments-service, features-service, market-data-processing-service,
unified-api-contracts) plus direct reads, not assumed.

**Verdict: (c) — partially correct on both sides, more nuanced than either framing.** The operator is RIGHT that Yahoo
Finance is a real, live, precedented data SOURCE and that the registry conflates source with venue — but WRONG that all
3 named instrument classes are "already the way". 2 of 3 already work; 1 of 3 is a genuine, never-built gap.

**(1) DXY — WORKING (operator correct).**
`market-tick-data-service/market_tick_data_service/market_interface/adapters/ tradfi/yahoo_finance_adapter.py`
(`YahooFinanceAdapter`, 361 lines, live `yfinance`-backed) is registered in `factory.py:153`
(`"yahoo_finance": ("tradfi", YahooFinanceAdapter)`) and is called by
`market_tick_data_service/adapters/_umi_yahoo.py::fetch_yahoo_indices("ICE", ...)`, itself dispatched from
`umi_tick_provider.py`'s `route_yahoo_tradfi()` for `venue_upper == "ICE"`. DXY ticker `DX-Y.NYB` is registered in UAC's
`YAHOO_INDICES` (`tradfi_instrument_universe.py:511`, `YahooIndexDef("DXY", "ICE", "DXY", "DX-Y.NYB", ...)`). This path
was wired 2026-07-13 (`tradfi_ice_ohlcv_1m_no_working_fetch_path_2026_07_13.md`) — real, tested, live.

**(2) KRW/USD — WORKING (operator correct).** `FX_SPOT_PAIRS` (UAC `tradfi_instrument_universe.py:430`,
`FxSpotPairDef("KRW", "USD", "KRWUSD=X")`, comment: "for kimchi-premium basis computation") is fetched by
`_umi_yahoo.py::fetch_yahoo_fx()`, dispatched from `route_yahoo_tradfi()` for `venue_upper == "FX"`. Live, tested.

**(3) US Treasuries — NOT WORKING, genuine gap (operator's belief is wrong here, though the intent is real and declared
everywhere else).** The CBOE fixed-income tenors (`US3M`/`US2Y`/`US5Y`/`US10Y`/`US30Y` — tickers
`^IRX`/`2YY=F`/`^FVX`/`^TNX`/`^TYX`) ARE registered in `YAHOO_INDICES` (`tradfi_instrument_universe.py:521-525`, venue
tagged `"CBOE"`), AND the intent is independently declared in 3 more places: `SOURCE_PRIORITY`
(`_source_priority_data.py:328-331`: `("tradfi", "ohlcv_24h"): ["yahoo"]`, comment "FX KRW/USD, KRX single stocks, the
DXY + treasury-yield indices"), the per-instrument `data_source_continuity.py` (`get_us_treasury_yield_daily_source()`
returns the string `"YAHOO_FINANCE"` for covered dates, and
`get_source_for_instrument("CBOE:INDEX:US10Y-USD", "ohlcv_24h", ...)` resolves through it — regression-tested in
`test_yahoo_indices_and_dxy_source.py:97-116`), and
`features-service/features_service/volatility/calculators/treasury_yields_calculator.py` (a pure formula module awaiting
a `yields_daily` DataFrame with `us3m`/`us5y`/`us10y`/`us30y` columns — no fetch/loader code for it exists anywhere in
features-service). **But `route_yahoo_tradfi()`'s venue tuple is `("FX", "KRX", "ICE")` — `"CBOE"` was never added**, so
`fetch_yahoo_indices("CBOE", ...)` (a function whose own docstring anticipates exactly this: "reusable for other
YAHOO_INDICES venues (CBOE tenors, KRX KOSPI/KOSPI200) without a new copy, though only ICE calls it today") is never
invoked in production. This is confirmed independently missing from `SOURCE_PRIORITY`'s own comment describing CBOE's
Databento-only role for `ohlcv_1s`, and from `expected_coverage.py:173`, `"CBOE": ["ohlcv_1s", "ohlcv_1m"]` — no
`ohlcv_24h` entry at all for CBOE, so even if the fetch route existed, `venue_fetch.py`'s per-shard UAC-intersection
would filter the request out before it reached routing (the same 2-layer gating shape as the `mbp_10` finding above).

**Why not a mechanical one-line fix (unlike the ICE DXY precedent)**: naively adding `"CBOE"` to `route_yahoo_tradfi`'s
tuple is UNSAFE — CBOE already routes live VX-futures `ohlcv_1s`/`ohlcv_1m` through Databento via the SAME dispatch
chain (this function sits upstream of the Databento fallthrough in `umi_tick_provider.py`). The function's current
all-or-nothing per-venue branch (`if data_types and "ohlcv_24h" not in data_types: return pd.DataFrame()`) would
short-circuit any non-`ohlcv_24h` CBOE request straight to an empty frame instead of falling through to Databento below
it — silently breaking live VX-futures capture, a real, actively-used, high-value feed. A correct fix needs
instrument-type-aware (index vs future) or explicit-data_type routing, not a blind tuple addition. **Not built here** —
flagged as a new scoped todo above rather than rushed under this investigation's time-box.

**On the "phantom venue" registry-modeling question** (does `VENUE_DATA_TYPE_CAPABILITIES`/`expected_coverage.py`
structurally conflate venue with source): **yes, confirmed** — `"YAHOO_FINANCE"` is declared as a literal VENUE with its
own `ohlcv_15m`/`ohlcv_24h` expected-coverage entry that no fetch code ever satisfies (real Yahoo-sourced rows are
correctly stamped under venue=ICE/FX/KRX, source=yahoo — `data_source_continuity.py` already models this correctly as a
per-instrument SOURCE resolver returning the string `"YAHOO_FINANCE"`, a genuinely cleaner place than the venue-level
capability dicts). `instruments-service` already partially corrects for this on its OWN producer path
(`_TRADFI_NON_VENUE_KEYS` excludes `"YAHOO_FINANCE"` from `get_venues_for_asset_groups`, `venue_core.py:164`) — the
UAC-registry-level capability/expected-coverage entries were simply never brought into line with that same exclusion.
**Not blind-fixed here either**: `get_expected_data_types_for_venue()` (`market_data_categories.py:1881-1884`) falls
through to a blanket ALL-10-tradfi-datatypes list whenever a venue's capability dict is empty or absent — the exact
footgun `test_data_status_registries.py`'s KRX docstring already documents for a different venue. Naively deleting the
`YAHOO_FINANCE` capability entries would turn a 2-datatype phantom into a WORSE 10-datatype one. The correct fix is
almost certainly a manifest-SEEDING-site exclusion (mirroring the `_tradfi_mtds_tick_manifest_data_types()` pattern
already shipped for `corporate_action_confirmed`/`earnings_result` in this same doc), not a raw UAC registry deletion —
flagged as the corrected version of the pre-existing todo above, still open, still needs its own scoped pass.

**Bottom line**: the operator's core architectural claim (Yahoo Finance is a real source, modeled at the wrong layer) is
correct and evidenced. The specific factual claim ("we get... us treasuries... from there") is not currently true in
production — the registry/intent layers all agree it SHOULD be, but no fetch code path exists for it. No code shipped by
this pass (both candidate fixes carry real regression/footgun risk that deserves its own careful, tested pass, not a
rushed change under this investigation's scope) — this section replaces the "phantom venue, no adapter, likely dominant
contributor" framing with the evidence-backed picture above; the original framing is left in place above (not deleted)
per this workspace's correct-don't-silently-rewrite convention.

## Resolution — CBOE US Treasury-yield tenors routing (2026-07-15)

Fixed the MTDS-side routing gap exactly as scoped: `market-tick-data-service@764e7170` makes `route_yahoo_tradfi()`
(`market_tick_data_service/adapters/_umi_yahoo.py`) discriminate CBOE requests by `data_type` instead of a blanket
venue-level flip, per this doc's own "do not naively add CBOE to that tuple" warning above.

**The discriminator (file:line)**: `_umi_yahoo.py:300`, a new
`_CBOE_YAHOO_TREASURY_DATA_TYPES: frozenset[str] = frozenset({"ohlcv_24h"})` constant, consumed at
`_umi_yahoo.py:325-329` inside `route_yahoo_tradfi()`:

```python
if venue_upper == "CBOE":
    if data_types and set(data_types) <= _CBOE_YAHOO_TREASURY_DATA_TYPES:
        return await fetch_yahoo_indices("CBOE", date=date, writer=writer, failed_per_instrument=failed_per_instrument)
    return None
```

CBOE is handled as a case SEPARATE from the pre-existing FX/KRX/ICE blanket-venue tuple (which is untouched). The
discriminator is `data_types`: only when the caller's requested `data_types` is explicitly non-empty AND is an exact
subset of `{"ohlcv_24h"}` (Yahoo's only servable granularity here, and the one granularity CBOE's Databento VX-futures
path never serves) does the request route to `fetch_yahoo_indices("CBOE", ...)` — which internally filters UAC's
`YAHOO_INDICES` registry to `venue == "CBOE"`, naturally resolving to exactly the 5 Treasury tenors (US3M/US2Y/US5Y/
US10Y/US30Y) with no separate ticker allowlist needed in MTDS. Every other shape — `data_types=None` (the
default/no-override production path), or `data_types` containing any Databento data_type (`ohlcv_1s`, `ohlcv_1m`,
`trades`, `tbbo`, `mbp_10`, or a mix including `ohlcv_24h`) — returns `None` from this branch, so
`fetch_tick_data_for_venue`'s dispatch chain (`umi_tick_provider.py:637-659`) falls through UNCHANGED to the existing
`_route_massive`/`_route_databento` path (CBOE is in `_umi_massive.MASSIVE_INCAPABLE_VENUES`, so it always lands on
`_route_databento` specifically, exactly as before this fix).

**Regression tests** (`tests/unit/test_umi_tick_provider_routes.py`, new `TestYahooCboeTreasuryRouting` class, 4 tests)
— both halves the dispatching task required, plus 2 more:

1. `test_cboe_ohlcv24h_routes_to_yahoo_treasury_tenors` — **(a) proves the fix**: `venue=CBOE, data_types=["ohlcv_24h"]`
   now reaches `fetch_yahoo_indices("CBOE", ...)`.
2. `test_cboe_vx_futures_data_types_still_reach_databento` — **(b) THE regression-proving test**:
   `venue=CBOE, data_types=["ohlcv_1s"]` and `["ohlcv_1m"]` (VX-futures shapes) both still reach
   `DatabentoAdapter.download_batch_df` unaffected, and the Yahoo fetch (`fetch_yahoo_indices`) is asserted `not_called`
   — proves neither side broke the other.
3. `test_cboe_default_data_types_none_still_falls_through_to_databento` — `data_types=None` (the production default
   shape) still falls through to Databento exactly as pre-fix, confirming CBOE does NOT get the FX/KRX/ICE
   default-to-Yahoo behavior.
4. `test_cboe_mixed_data_types_including_databento_type_falls_through` — a mixed request (`["ohlcv_24h", "ohlcv_1m"]`)
   is not an exact subset of `{"ohlcv_24h"}`, so it correctly falls through rather than silently serving only the Yahoo
   half.

All 4 new tests pass; full existing `test_umi_tick_provider_routes.py` suite (including `TestYahooFxRouting`,
`TestYahooKrxRouting`, `TestYahooIceRouting`, `TestDatabentoRouting`) and the full repo `quality-gates.sh --no-fix` both
green (sentinel `.qg_last_passed_sha` verified == HEAD before shipping).

**Scope caveat (mirrors the mbp_10/CME precedent above)**: this fix alone does NOT yet cause live CBOE Treasury-yield
capture to start flowing in production. `venue_fetch.py`'s per-shard UAC-intersection step filters every `data_types`
request against `get_expected_data_types_for_venue("CBOE")` BEFORE it reaches this routing code, and UAC's
`VENUE_DATA_TYPE_CAPABILITIES["CBOE"]`/`expected_coverage.py` currently declare only `{"ohlcv_1s", "ohlcv_1m"}` — no
`ohlcv_24h` entry — so a live/default orchestrator run for CBOE still never constructs an `ohlcv_24h` request in the
first place. **Deliberately not touched here** — out of this task's scope (touch only market-tick-data-service per the
dispatch), and per this doc's own warning about `get_expected_data_types_for_venue()`'s undocumented
fall-through-to-ALL-10-datatypes footgun on an EMPTY capability dict (CBOE's dict is non-empty, so a straightforward
addition should be safe, but it needs its own careful UAC-repo pass + QG run, not a bolt-on here). Filed as a new
`[DATA] P3` todo above (`unified-api-contracts`: add `ohlcv_24h` to CBOE's capability + expected-coverage entries).

## Resolution — YAHOO_FINANCE phantom-venue seeding stopped + orphan rows cleaned (2026-07-16)

Operationalized the `unified-api-contracts@fec3f110` YAHOO_FINANCE venue removal on real infra: **stop the nightly
re-seeding first, then clean the orphaned rows so they HOLD** (the ordering matters — a clean-first would have been
resurrected by the next nightly enum). All steps were live prod actions on GCP `central-element-323112`.

**The seeder (identified, not assumed).** `enumerate_expected_universe.py`'s `_yield_v2_tradfi_non_trading_day_rows`
walks `VENUES_BY_ASSET_GROUP["tradfi"]` and seeds `empty_confirmed` `EXPECTED_WEEKEND`/`EXPECTED_HOLIDAY` rows into the
MTDS tradfi tick manifest (`resolve_bucket_name(kind="market-data", asset_group="tradfi")` → `_index/…`). The nightly
runner is Cloud Run job **`expected-universe-v2-tradfi`**
(`MANIFEST_PER_VM_SHARDS=true VM_NAME=enum-universe-v2-tradfi`, `--apply-write`), Cloud Scheduler
**`expected-universe-v2-tradfi-daily` = `30 1 * * *`** — matching the manifest's max `attempted_at` of
`2026-07-15T01:31:30Z`. `is-daily-enum-tradfi` (`30 13 * * *`) runs
`-m instruments_service --operation instruments --mode batch` (instrument-catalogue enumeration, a different bucket) and
does NOT seed the tick manifest — so it is NOT a YAHOO seeder. The catalogue jobs (`lifecycle-catalogue-*-tradfi`,
`build_instrument_catalogue.py`) write instruments-store, not the tick manifest.

**Big finding — the base bump `instruments-service@6d33b9d5` was premature.** It pinned UTL base `sha256:b7c57243`
(built `2026-07-15 17:54:46Z`), which had YAHOO removed but predated `unified-api-contracts@7754661a` (`18:14:29Z`, adds
`venue_data_type_has_batch_source`) that the current enumerator imports at module load — so an enum run on that image
died at `ImportError: cannot import name 'venue_data_type_has_batch_source' from 'unified_api_contracts'` (exec
`expected-universe-v2-tradfi-959bv` failed). Corrected by re-bumping the IS Dockerfile base to the newer UTL
`0.55.0/latest` `sha256:be51b33f` (built `23:27:01Z`), verified in-image to bundle all of {YAHOO removed, CBOE
`ohlcv_24h` declared, `venue_data_type_has_batch_source` present} via
`Evidence: cloudbuild=70dbc75f-c8db-4245-b3bb-fd175829f6b3` (SUCCESS). Shipped `instruments-service@3e5b1039` (QG-green,
quickmerge); built it `Evidence: cloudbuild=d00de7ec-8272-49d5-ab9d-f0ded059b0e6` (SUCCESS) → IS image digest
`sha256:d569a6548d4dde511a994c5e35f0dd043aa6f1b67c9375d1f51f3793bddee98d`; re-pinned `expected-universe-v2-tradfi` to
that digest (`gcloud run jobs update … --image <digest>`). (The `d00de7ec` build also restored a working `:latest`,
which an interim `b7c57243`-based build had transiently overwritten.)

**Seeding-stopped verification (deploy-first proof).** Executed `expected-universe-v2-tradfi` on the fixed image (exec
`expected-universe-v2-tradfi-lwsqs`, SUCCEEDED). Its fresh per-VM shard `_index/per_vm/enum-universe-v2-tradfi.parquet`
(written `23:09:34Z`) carried **5,709 rows, YAHOO_FINANCE = 0**, and still seeded the real tradfi venues (CME 2244 /
NYSE 1122 / NASDAQ 871 / ICE 368 / CBOE 368 / KRX 368 / FX 368). Post-consolidation the canonical index had **zero**
YAHOO rows with `attempted_at` after the run (max stayed `2026-07-15T01:31:30Z`).

**Cleanup (source-addressed).** Resurrection-surface audit: `_index/per_vm/_legacy_seed.parquet` (the permanent seed the
consolidator always merges) carried **0** YAHOO rows, so the only live YAHOO population was the canonical itself
(inherited from the pre-fix enum shard, since consumed+pruned). To avoid a write race with the every-minute consolidator
(`uts-prod-manifest-consolidator-market-data-tradfi`, DuckDB UNION-ALL merge of canonical + per-VM shards), the cleanup:
(a) paused scheduler `uts-prod-manifest-consolidator-market-data-tradfi-cron` and drained the in-flight run; (b)
snapshotted then deleted `venue==YAHOO_FINANCE` from **`_index/availability_index.parquet`** (11,676 → 0; 5,564,746 →
5,553,070 rows; breakdown 10,108 `EXPECTED_WEEKEND` + 737 `EXPECTED_HOLIDAY` `empty_confirmed` + 831
`attempted_failed`/`LegacyBlankErrorReasonError`) and **`_index/expected_universe_ranges.parquet`** (the honest-coverage
full-history denominator, which a `--start-date` enum run does NOT regenerate: 5,080 → 0; 63,514 → 58,434); (c) resumed
the scheduler. STOP-ON-SURPRISE guarded against deleting any `capture_status=="captured"` row (there were none — all
pure enumeration artifacts, consistent with "no live fetch writes venue=YAHOO_FINANCE"). Snapshots for rollback:
`_index/snapshots/pre_yahoo_phantom_venue_delete_20260715T231453Z_{availability_index,expected_universe_ranges}.parquet`.
Predicate/pattern mirrors `market-tick-data-service/scripts/delete_tradfi_aggregate_phantom_markers_2026_07_07.py`
(download → STOP-ON-SURPRISE → snapshot → filter → write-back → verify gate). The deletion was run as a scoped
operational one-off (fully reproducible from the snapshots + this predicate); it was not committed to `scripts/` to
avoid entangling with two pre-existing, unrelated MTDS adapter-contract-baseline regressions
(`_onchain_perp_batch_live_only.py`, `solana_defi_drift.py`) that are outside this task.

**HOLD proven (not a point-in-time check).** After resume, forced one consolidator merge (exec
`…-market-data-tradfi-8txgh`, SUCCEEDED) then watched **≥5 real merge cycles** (canonical rewritten `23:17:55` →
`23:19:39` → `23:20:44` → `23:21:39` → `23:22:41Z`). Final state across every resurrection surface: canonical
`availability_index.parquet` YAHOO=0 (5,553,070 rows), `expected_universe_ranges.parquet` YAHOO=0 (58,434 rows),
`_legacy_seed.parquet` YAHOO=0 (18,149 rows). The rows are gone and stayed gone — no resurrection. Consolidator
scheduler confirmed `ENABLED` (not left paused); enum job confirmed pinned to the working digest.

**CBOE note (task sanity check).** UAC now declares CBOE `ohlcv_24h`: `VENUE_DATA_TYPE_CAPABILITIES["CBOE"]` contains
`ohlcv_24h` → `True` (confirmed both in the workspace UAC and inside the deployed base image), and `YAHOO_FINANCE` is no
longer a `VENUE_DATA_TYPE_CAPABILITIES` key (`False`). CBOE `ohlcv_24h` capture rides the MTDS image (already on the new
UAC) — no separate deploy needed here.

## Progress Log

- 2026-07-15: Filed by background research/triage agent (diagnosis only, no code changes) while triaging a
  `#data-pipeline-alerts` `DP_RUN_MOSTLY_EMPTY` alert batch's TRADFI 100%-failed cells. All 3 mechanisms verified via
  direct grep + read across 4 repos; none independently re-verified against a live manifest query (read-only, time-boxed
  triage pass) — the manifest-classification open question is left as todo P3 above.
- 2026-07-15 (later same day): Finding (1) `mbp_10` fixed at the adapter layer — `market-tick-data-service@e2018167`.
  Verified the full Databento fetch mechanics (schema map + UAC subscription/billing allowlist) were already sound
  end-to-end; the pre-flight allowlist was the one remaining gap and is now closed, with a regression test class pinning
  the "registry-declared ⊆ adapter-supported" invariant so this drift class can't silently recur. Also discovered — NOT
  part of the original diagnosis — that UAC's `VENUE_DATA_TYPE_CAPABILITIES["CME"]` still scopes CME to
  `{ohlcv_1s, ohlcv_1m}` only (2026-05-15 OHLCV-only MVP), so this fix does not by itself cause live `mbp_10` capture to
  start; see "Resolution — mbp_10" above for the full trace and the already-existing (but stalled) successor plan that
  owns closing that gap. Findings (2) and (3) untouched — still open, still need the operator/architecture calls the
  recommendation section above describes.
- 2026-07-15 (operator decision, interactive reconciliation): presented the UAC-registry-restoration option ("restore
  `mbp_10` to `VENUE_DATA_TYPE_CAPABILITIES["CME"]` now, since the adapter-layer fix is shipped and tested") vs. leaving
  the 2026-05-15 MVP-scope restriction in place. **Operator chose to leave the restriction in place** — the scope
  narrowing is still deliberate, not stale. Reclassifying: the 1186/1186 historical `attempted_failed` `mbp_10` rows and
  the ongoing `DP_RUN_MOSTLY_EMPTY` alert for this cell should be treated as **expected-per-scope-decision**, not an
  open gap — this issue's finding (1) is closed at the adapter layer (correct, necessary, done) but the live-capture
  activation is explicitly NOT happening right now by operator choice, not by oversight. **Follow-up not yet done**:
  whether the manifest/alerting layer has a clean mechanism to mark an operator-scope-deferred cell as
  `expected_unattempted`-with-reason (vs. `attempted_failed`) so it stops presenting as an active failure in
  `DP_RUN_MOSTLY_EMPTY`'s ratio math — worth a small follow-up if this cell keeps contributing to future alert noise;
  not pursued in this pass to avoid scope creep into the alert-classification system beyond what was asked.
- 2026-07-15 (later same day, background research agent — ohlcv_15m/ohlcv_24h audit dispatched from
  `data_pipeline_alerts_batch_remediation_2026_07_15.md`'s operator decision #2): audited UAC/instruments-service/MTDS
  for existing per-venue source-capability/granularity infrastructure per the operator's strong prior that it already
  exists. **Confirmed the prior was substantially correct** — see "Resolution — ohlcv_15m/ohlcv_24h audit" above for
  full citations. Shipped one completion fix (CBOE `ohlcv_15m` narrowing, `unified-api-contracts@78b9e899`, same pattern
  as KRX/ICE, QG green). Found and documented (not blind-fixed) 2 further sub-findings: (B) no downstream OHLCV
  aggregation writer exists anywhere despite 3 places in the codebase asserting one does, leaving `vix_features`'s real
  `ohlcv_15m` input requirement unfed; (C) `"YAHOO_FINANCE"` is a phantom no-adapter venue in
  `VENUES_BY_ASSET_GROUP["tradfi"]` declared expected for `ohlcv_15m`/`ohlcv_24h` — likely the dominant contributor to
  the reported failure counts, same misclassification class as this doc's `corporate_action_confirmed`/`earnings_result`
  finding. Both routed to new scoped todos above rather than rushed, per each finding's own risk profile (B = real
  multi-service build; C = an already-flagged "manifest churn" risk needing an explicit operator decision).
- 2026-07-15 (later same day, dispatched agent — finding (3) `corporate_action_confirmed`/`earnings_result`): operator
  decided option (a) (stop seeding both as MTDS-tick-manifest expected cells) in an interactive session. Re-verified
  `instruments-service/scripts/enumerate_expected_universe.py` as the sole seeding site, added a tradfi-scoped exclusion
  helper (`_tradfi_mtds_tick_manifest_data_types()`) wired into both `data_types`-resolution call sites, confirmed UAC's
  own `DATA_TYPES_BY_ASSET_GROUP["tradfi"]` registry is untouched (regression-tested), added 4 new regression tests,
  full suite + `quality-gates.sh --no-fix` green. Shipped `instruments-service@03f71c81`. Also resynced the
  `tradfi.json` golden fixture (3-line delta) to a since-committed, unrelated finding-(2) UAC change
  (`unified-api-contracts@78b9e899`, CBOE `ohlcv_15m` narrowing) that was blocking the local quality gate — see
  "Resolution — corporate_action_confirmed / earnings_result" above for the full trace, including why the other 4
  asset_groups' golden fixtures were deliberately reverted (pure formatting noise, no content delta). Historical
  807/807 + 799/799 already-seeded manifest rows deliberately left untouched — documented as a follow-up (production
  data mutation, deserves its own scoped pass), not forced into this commit. This doc's finding (3) is now closed;
  findings (2)'s sub-items (B) downstream aggregation writer and (C) phantom `YAHOO_FINANCE` venue remain open per their
  own todos above.
- 2026-07-15 (independent second audit pass on finding (2), dispatched from the same
  `data_pipeline_alerts_batch_remediation_2026_07_15.md` todo before this doc's existing "Resolution —
  ohlcv_15m/ohlcv_24h audit" section was visible): re-confirmed the operator's per-venue-routing prior independently
  (same conclusion, four layers found: `VENUE_DATA_TYPE_CAPABILITIES`, `expected_coverage.py`, UAC
  `MVP_SCOPE`/`TradFiMvpRule` consumed by instruments-service's `_tradfi_mvp_data_types`, and MTDS's
  `_DATABENTO_SUPPORTED_DATA_TYPES` fetch-layer allowlist — all already narrowing CME/CBOE/NASDAQ/NYSE away from
  `ohlcv_15m`/`ohlcv_24h`). Found the CBOE fix + this doc's own audit write-up already shipped/landed moments earlier by
  a concurrent agent — did not duplicate; instead ran a live re-query of the actual manifest
  (`market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`) that the existing write-up
  had not done, which (a) corrects the "YAHOO_FINANCE is the dominant contributor" claim for `ohlcv_15m` (it contributes
  zero `attempted_failed` rows there; NYSE and CBOE are the real dominant contributors) and (b) proves every
  `attempted_failed` row for both cells is stale (`attempted_at` ≤ 2026-07-07, unchanged 8+ days, predating both
  narrowing fixes) and (c) traced the concrete reason the alert keeps re-firing despite the routing gap being closed:
  `deployment-service`'s `_read_attempted_failed_cells` (DP-FETCH-009) counts `attempted_failed` over the WHOLE manifest
  with no date-recency window at all, so stale rows alone permanently exceed the 500-row absolute threshold. Filed as a
  "Verification addendum" section above (not a rewrite of the existing audit — a corroborating + correcting layer on top
  of it) and flagged the alert-persistence mechanism as a candidate unified follow-up spanning `mbp_10`,
  `ohlcv_15m`/`ohlcv_24h`, and finding (3)'s deferred historical rows, rather than resolving it here (touches
  alert-classification semantics broadly — out of this narrow audit's scope per the dispatching plan's own STOP
  criterion). No code shipped by this pass (nothing left to build — the routing gap was already closed by others); the
  plan's todo checkbox was already correctly flipped by the concurrent agent and is left as-is.
- 2026-07-15 (independent second audit pass on finding (3) `corporate_action_confirmed`/`earnings_result`, dispatched
  from the same `data_pipeline_alerts_batch_remediation_2026_07_15.md` todo): found the fix already shipped by a
  concurrent agent (`instruments-service@03f71c81`) and the resolution write-up above already landed
  (`unified-trading-pm@24ee65c3a`) before this pass reached the shipping step. Independently re-verified rather than
  duplicating: re-confirmed via fresh grep that `enumerate_expected_universe.py` is the sole non-test/non-restamp-script
  seeding site across instruments-service + market-tick-data-service + UAC; re-read the shipped diff line-by-line and
  confirmed the exclusion is scoped correctly (both `enumerate_v2()` and `main()`'s CLI-default resolution branches
  patched; UAC's `DATA_TYPES_BY_ASSET_GROUP["tradfi"]` registry itself untouched, per the shipped
  `test_uac_data_types_by_asset_group_registry_itself_is_untouched` regression test); confirmed features-service's
  calendar module has zero dependency on `DATA_TYPES_BY_ASSET_GROUP` (grep, zero hits) so the legitimate seeding path is
  provably unaffected. No discrepancies found — the shipped fix matches this doc's own recommendation exactly. Only gap
  closed by this pass: the plan's own `data_pipeline_alerts_batch_remediation_2026_07_15.md` "New todos" checkbox for
  this item was still unflipped despite the underlying work being complete — flipped it with full evidence
  (`unified-trading-pm` commit to follow this entry). **Cross-referencing the "independent second audit pass on finding
  (2)" entry directly above**: its DP-FETCH-009 finding (deployment-service's `_read_attempted_failed_cells` counts
  `attempted_failed` over the WHOLE manifest, no date-recency window) applies equally to finding (3)'s deferred 807/799
  historical rows — i.e. leaving those rows in place is NOT expected to self-resolve the `DP_RUN_MOSTLY_EMPTY` alert for
  this cell even though future seeding has stopped; the alert will keep re-firing off the stale historical rows alone
  until either the rows are explicitly cleaned up or the alert-counting mechanism gains a recency window. Flagging this
  explicitly so the "forward-only, historical rows deferred" decision above is not mistaken for "the alert is now fixed"
  — it is not, by itself.
- 2026-07-15 (operator-directed re-check, dispatched after an interactive pushback on the finding-(C) "phantom venue, no
  adapter" framing above — operator: Yahoo Finance is a real intended data SOURCE for DXY/treasuries/KRW-USD, not a
  missing-adapter gap; the registry conflates source with venue): full workspace grep + direct read across
  market-tick-data-service/instruments-service/features-service/unified-api-contracts, no code changes. **Verdict: the
  operator was RIGHT about DXY and KRW/USD (both fetch successfully today via `YahooFinanceAdapter` +
  `route_yahoo_ tradfi`, venue=ICE and venue=FX respectively — real, live, tested) but WRONG that US Treasury yields
  already work** — `route_yahoo_tradfi()` never routes venue="CBOE" (only FX/KRX/ICE), so the CBOE fixed-income tenors
  registered in `YAHOO_INDICES` + declared in `SOURCE_PRIORITY`/`data_source_continuity.py`/features-service's
  `treasury_yields_calculator.py` have no working fetch path anywhere — a genuine, never-built gap, not a modeling
  error. Also confirmed the operator's broader architectural point (source vs. venue conflation) is correct: the
  `"YAHOO_FINANCE"` phantom-venue registry entries duplicate/shadow the correctly-modeled real venues, and
  `data_source_continuity.py` already has the right shape (a per-instrument SOURCE resolver). **No code shipped** — both
  candidate fixes (CBOE Yahoo-routing addition; YAHOO_FINANCE capability-entry removal) carry real regression/footgun
  risk found during this pass (CBOE fix risks silently breaking live VX-futures Databento capture via the same dispatch
  function; the capability-entry removal risks tripping `get_expected_data_types_for_venue()`'s undocumented
  fall-through-to-ALL-10-datatypes footgun, making the phantom WORSE not better) — both correctly scoped as new todos
  above rather than rushed. See "Verdict — Yahoo Finance source-vs-venue investigation (2026-07-15, operator-directed
  re-check)" above for full citations and the corrected finding-(C) todo annotation.
- 2026-07-15 (later same day, dispatched agent — CBOE US Treasury-yield tenor routing, the last open `[CODE]` todo from
  the "Verdict — Yahoo Finance source-vs-venue investigation" section above): read `route_yahoo_tradfi()` and its full
  caller chain in `umi_tick_provider.py` first — confirmed `data_types` (and `instrument_ids`, unused by this branch) is
  already in scope at the exact call site, so no branch-point relocation was needed. Confirmed CBOE's VX-futures
  Databento path is identified structurally (venue=CBOE, `_umi_massive.MASSIVE_INCAPABLE_VENUES` forces it onto
  `_route_databento`, requested `data_types` drawn from `{ohlcv_1s, ohlcv_1m, trades, tbbo, mbp_10}` per
  `_DATABENTO_SUPPORTED_DATA_TYPES`/`expected_coverage.py:173`) versus the 5 Treasury tenors (venue=CBOE in UAC's
  `YAHOO_INDICES`, `ohlcv_24h`-only). Implemented the narrow, explicit `data_types`-based discriminator recommended by
  the dispatch (not a ticker allowlist duplicated in MTDS — `fetch_yahoo_indices("CBOE", ...)` already IS that allowlist
  via its own `YAHOO_INDICES` venue-filter): CBOE routes to Yahoo ONLY when `data_types` is explicit and an exact subset
  of `{"ohlcv_24h"}`; `data_types=None` (default/no-override) or anything containing a Databento data_type falls through
  unchanged. Shipped `market-tick-data-service@764e7170` (3 files: `_umi_yahoo.py`, `umi_tick_provider.py` comment-only
  accuracy updates, `tests/unit/test_umi_tick_provider_routes.py` +4 tests). Both regression halves the dispatch
  required pass: (a) `ohlcv_24h` reaches `fetch_yahoo_indices("CBOE", ...)`, (b) `ohlcv_1s`/`ohlcv_1m` (VX-futures
  shapes) still reach `DatabentoAdapter.download_batch_df` with the Yahoo fetch asserted never-called — plus 2 extra
  tests for the `data_types=None` default-path and a mixed-data_types request. Full `quality-gates.sh --no-fix` green
  (sentinel `.qg_last_passed_sha` == HEAD verified before quickmerge). **Left open, new `[DATA] P3` todo filed above**:
  UAC's `VENUE_DATA_TYPE_CAPABILITIES["CBOE"]`/`expected_coverage.py` still only declare `{ohlcv_1s, ohlcv_1m}` (no
  `ohlcv_24h`), so `venue_fetch.py`'s per-shard UAC-intersection step still filters an `ohlcv_24h` CBOE request out
  before it reaches this new routing code on a live/default orchestrator run — same "routing fixed, registry restoration
  deferred" shape as the mbp_10/CME resolution above; deliberately not touched here (UAC-repo, out of this task's scope)
  and explicitly checked-and-cleared against the `get_expected_data_types_for_venue()` ALL-10-datatypes footgun the
  dispatch warned about (CBOE's capability dict is non-empty, so that specific footgun does not apply to this follow-up
  — re-verify at UAC-shipping time regardless). See "Resolution — CBOE US Treasury-yield tenors routing (2026-07-15)"
  above for the full discriminator writeup.
- 2026-07-16 (operational — dispatched agent, LIVE deploy + LIVE prod data mutation): operationalized the
  `unified-api-contracts@fec3f110` YAHOO_FINANCE phantom-venue removal (the P3 `[DATA]` todo above). **Deploy-first,
  then clean.** Identified the sole nightly seeder into the tradfi tick manifest as Cloud Run job
  `expected-universe-v2-tradfi` (scheduler `30 1 * * *`, matching the `01:31:30Z` `attempted_at`). **Found + fixed a
  premature-base-bump blocker**: `instruments-service@6d33b9d5`'s UTL base `b7c57243` (17:54Z) predated
  `unified-api-contracts@7754661a` (18:14Z, `venue_data_type_has_batch_source`), so the enum crashed at runtime import;
  re-bumped IS to UTL base `be51b33f` (`instruments-service@3e5b1039`, QG-green; base verified `cloudbuild=70dbc75f`),
  built `cloudbuild=d00de7ec` → digest `d569a654`, re-pinned the job. Verified seeding stops (enum exec `…-lwsqs`
  SUCCESS, fresh shard 5,709 rows / YAHOO=0, real venues seeded; canonical gained 0 new YAHOO rows). Cleaned at the
  source: drained+paused the tradfi consolidator, snapshotted, deleted `venue==YAHOO_FINANCE` from the canonical index
  (11,676→0) and the ranges denominator (5,080→0), resumed. Proved HOLD across ≥5 consolidator merge cycles (all
  surfaces YAHOO=0; `_legacy_seed` never had any). Confirmed CBOE `ohlcv_24h`=True in UAC. Full evidence + before/after
  counts + snapshot paths in "Resolution — YAHOO_FINANCE phantom-venue seeding stopped + orphan rows cleaned
  (2026-07-16)" above. No leftover: the seeding is stopped for good (durable Dockerfile fix on LDR) and the rows are
  cleaned and verified to stay gone.

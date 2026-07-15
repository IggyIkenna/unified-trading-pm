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
    krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md,
    tradfi_ice_ohlcv_1m_no_working_fetch_path_2026_07_13.md,
    tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md,
    tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md,
    macro_micro_econ_data_capture_audit_2026_06_05.md,
    dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md,
    ../../../codex/02-data/tradfi-databento-sourcing-ssot.md,
    ../../../codex/02-data/honest-coverage-model.md,
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
last_updated: 2026-07-15
---

# TRADFI mbp_10 / ohlcv_15m / ohlcv_24h / corporate_action_confirmed / earnings_result — unreachable fetch paths

## What I found (read-only code trace, no changes made)

Triaging the alert batch's TRADFI 100%-failed cells against `codex/02-data/tradfi-databento-sourcing-ssot.md` (cited
authoritative for TradFi sourcing gotchas) plus a direct code read across
`market-tick-data-service`/`unified-api-contracts`/`instruments-service`/`features-service`. All three mechanisms below
were verified via grep + read, not assumed.

### (1) `mbp_10` — genuine adapter-wiring gap (scenario "a": broken/unimplemented path)

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

- `codex/02-data/tradfi-databento-sourcing-ssot.md` (§ "Non-Databento sources are UNTOUCHED by these guards"): "Note:
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
- [ ] [DATA] P2. `"YAHOO_FINANCE"` is declared as a literal TradFi venue (`VENUES_BY_ASSET_GROUP["tradfi"]`,
      `unified_api_contracts/registry/market_data_categories.py:329`) with `NO_ADAPTER_YET`
      (`registry/venue_adapter_keys.py:137`) and is expected for `["ohlcv_15m","ohlcv_24h"]`
      (`registry/expected_coverage.py:185`) — every cell is structurally unfulfillable, same misclassification shape as
      the already-decided `corporate_action_confirmed`/`earnings_result` fix elsewhere in this doc. Likely the DOMINANT
      contributor to the reported 3589/3590 `ohlcv_15m` + part of the 2852/7118 `ohlcv_24h` failure counts. Not
      blind-fixed here: the existing code comment explicitly flags a "manifest churn" risk (real historical rows may be
      stamped under this venue name) — needs the same structured operator decision the cefi-orphan-rows item got, not a
      silent delete. See "Resolution" below.

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
`codex/04-architecture/instruments-service-as-ssot-for-mtds.md`, `codex/02-data/tradfi-databento-sourcing-ssot.md`,
`codex/02-data/honest-coverage-model.md`, and the relevant UAC/instruments-service/MTDS/market-data-processing-service
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
asserted in **three separate places** — `codex/02-data/tradfi-databento-sourcing-ssot.md`, the `umi_tick_provider.py`
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
rather than discarding, since it corrects one claim and adds the mechanism for why the alert keeps firing after the
code fix. Pulled `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` directly
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
`instruments-service@31c15d88`, 2026-07-14 20:18 UTC, which independently closes the *seeding* side for MVP-scoped
tradfi cells; and this doc's CBOE `unified-api-contracts@78b9e899` narrowing above). Same "fixed historical count, not
actively growing" shape already established for `mbp_10`'s 1186/1186 rows in the mbp_10 resolution section above — none
of these three cells (`mbp_10`, `ohlcv_15m`, `ohlcv_24h`) are currently being re-attempted and re-failing; the manifest
rows are dead residue from a 2026-07-07 batch run.

**Why the alert keeps firing anyway (new finding, ties the mbp_10/(C) open questions together)**:
`deployment-service/deployment_service/data_pipeline_monitors/meta_watchers.py::_read_attempted_failed_cells` (feeding
DP-FETCH-009 / `DP_RUN_MOSTLY_EMPTY`) reads `columns=["capture_status", "data_type"]` only from the WHOLE consolidated
manifest `_index` — no `attempted_at`/date column, no recency window of any kind — and `check_high_attempted_failed`
compares the resulting whole-history count against a flat `ATTEMPTED_FAILED_ABS_THRESHOLD = 500` (or 10% ratio at
≥50 count; same file, lines 217-219). A dead cell's stale count alone (3,589 and 2,852, both »500) is sufficient to
keep it `high=True` and paging indefinitely, completely independent of whether anything is currently broken. This is
the concrete mechanism behind the open question already flagged in the mbp_10 Progress Log entry above ("whether the
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
  `deployment-service`'s `_read_attempted_failed_cells` (DP-FETCH-009) counts `attempted_failed` over the WHOLE
  manifest with no date-recency window at all, so stale rows alone permanently exceed the 500-row absolute threshold.
  Filed as a "Verification addendum" section above (not a rewrite of the existing audit — a corroborating +
  correcting layer on top of it) and flagged the alert-persistence mechanism as a candidate unified follow-up spanning
  `mbp_10`, `ohlcv_15m`/`ohlcv_24h`, and finding (3)'s deferred historical rows, rather than resolving it here (touches
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
  calendar module has zero dependency on `DATA_TYPES_BY_ASSET_GROUP` (grep, zero hits) so the legitimate seeding path
  is provably unaffected. No discrepancies found — the shipped fix matches this doc's own recommendation exactly. Only
  gap closed by this pass: the plan's own `data_pipeline_alerts_batch_remediation_2026_07_15.md` "New todos" checkbox
  for this item was still unflipped despite the underlying work being complete — flipped it with full evidence
  (`unified-trading-pm` commit to follow this entry). **Cross-referencing the "independent second audit pass on finding
  (2)" entry directly above**: its DP-FETCH-009 finding (deployment-service's `_read_attempted_failed_cells` counts
  `attempted_failed` over the WHOLE manifest, no date-recency window) applies equally to finding (3)'s deferred
  807/799 historical rows — i.e. leaving those rows in place is NOT expected to self-resolve the `DP_RUN_MOSTLY_EMPTY`
  alert for this cell even though future seeding has stopped; the alert will keep re-firing off the stale historical
  rows alone until either the rows are explicitly cleaned up or the alert-counting mechanism gains a recency window.
  Flagging this explicitly so the "forward-only, historical rows deferred" decision above is not mistaken for "the
  alert is now fixed" — it is not, by itself.

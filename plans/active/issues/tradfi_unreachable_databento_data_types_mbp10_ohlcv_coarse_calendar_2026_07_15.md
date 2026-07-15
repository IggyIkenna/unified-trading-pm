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
- [ ] [DESIGN] P2. Operator/architecture decision for `ohlcv_15m`/`ohlcv_24h`'s MTDS-tick-download expected coverage —
      narrow (KRX/ICE precedent) vs. wire a real downstream-aggregation-driven manifest write. Raise as a structured
      options question, do not guess.
- [ ] [DESIGN] P2. Operator/architecture decision for `corporate_action_confirmed`/`earnings_result`'s MTDS-tick-bucket
      expected coverage vs. features-service's actual ownership of this domain. Raise as a structured options question,
      do not guess. If descoped from MTDS, also flag to whoever owns
      `macro_micro_econ_data_capture_audit_     2026_06_05.md` that features-calendar-service's OWN manifest/rollup
      (separately already flagged as "0 shards, 0% completion") is the bucket that should actually be measured for this
      data going forward.
- [ ] [VERIFY] P3. Trace the orchestrator/sentinel classification layer to confirm exactly how a
      requested-but-`_DATABENTO_SUPPORTED_DATA_TYPES`-filtered-out data_type gets recorded (`attempted_failed` vs.
      `empty_confirmed`) — not traced to the manifest-write layer in this pass; needed to fully close out mechanism
      (1)/(2)'s classification question.

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

---
doc_type: issue
title:
  TRADFI unreachable Databento data_types (mbp_10/ohlcv_15m/ohlcv_24h/corporate_action_confirmed/earnings_result) —
  Progress Log history (2026-07-15 → 2026-07-31)
summary:
  Line-cap remediation extraction from
  plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md's Progress Log —
  every dated entry from the 2026-07-15 initial triage through the 2026-07-31 CME billing-gating audit pass (mbp_10
  adapter fix, the ohlcv_15m/ohlcv_24h per-venue audit, corporate_action_confirmed/earnings_result misclassification
  fix, the Yahoo Finance source-vs-venue investigation, CBOE Treasury-tenor routing, and the YAHOO_FINANCE
  phantom-venue cleanup), moved verbatim so the live doc stays under the 1000-line hard cap. The full technical
  writeups these entries narrate remain in the live doc's `## Resolution —` / `## Verdict —` sections; this history
  only relocates the chronological Progress Log narrative. Read this only if a deeper citation on the exact sequencing
  of a specific finding is needed.
status: archived
nature: notes
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    tradfi,
    databento,
    mbp_10,
    ohlcv_15m,
    ohlcv_24h,
    history,
    line-cap-remediation,
  ]
related:
  [
    /plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
  ]
created: 2026-08-08
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
last_updated: 2026-08-08
supersedes:
superseded_by:
locked_by:
locked_since:
depends_on: []
source:
  [
    plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    "line-cap remediation 2026-08-08, per plans/active/issues/tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08.md",
  ]
assigned_role: docs_reconciler
drift_direction: none
---

# TRADFI unreachable Databento data_types — Progress Log history (2026-07-15 → 2026-07-31)

> Extracted verbatim 2026-08-08 (line-cap remediation, source doc was at the exact 1000-line hard cap, zero headroom)
> from
> `/plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`'s Progress
> Log. This covers every dated entry from the 2026-07-15 initial triage filing through the 2026-07-31 CME
> billing-gating audit pass — the entries immediately following the `## Progress Log` header through the last one
> before the 2026-08-01 `context-scout` marker. The live doc's Progress Log continues from the 2026-08-01
> `context-scout` entry onward (kept in place so future `/na-eligibility-audit`/`/context-scout` incremental-skip
> logic still sees the most recent dated marker).

## Progress Log (2026-07-15 → 2026-07-31)

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
  (sentinel `.qg_last_passed_sha` == HEAD verified before shipping). **Left open, new `[DATA] P3` todo filed above**:
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
- 2026-07-26 (slot 6): Traced the write-time classification decision point for the `ohlcv_15m`/`ohlcv_24h`
  Databento-filtered cells this Verification addendum's DP-FETCH-009 finding covers the ALERT PERSISTENCE for.
  `_route_databento`'s data_type filter (`umi_tick_provider.py:444-447`) silently drops these two dts to an empty fetch
  with NO `failed_per_dt` entry; `sentinels.py::_emit_nonsports_tier2_tier3_sentinels`'s
  `effective_failure = per_dt_reason or failed_reason_raw` fallback (line 592) is what actually decides
  `attempted_failed` vs `empty_confirmed` for these — since the silent filter never sets `per_dt_reason`, classification
  rides on whether that SAME VENUE had an unrelated whole-venue failure that day. So a SEPARATE write-time decision
  point does exist (not just DP-FETCH-009's no-recency-window count) — full trace + file:line citations in
  `tradfi_satellite_ao_dispatch_batch3_2026_07_26.md`'s now-flipped `[VERIFY] P3` todo. No code changes.
- 2026-07-28 (slot 7, data_engineering): Closed the deferred `corporate_action_confirmed`/`earnings_result` historical
  orphan-row cleanup (`tradfi_satellite_ao_dispatch_batch2_2026_07_25.md` todo). Live re-query found the population far
  larger than the 807/799 alert-batch figures (420,803 rows in `availability_index.parquet` + 7,540 in
  `expected_universe_ranges.parquet`, 0 `captured`) — deleted via the same snapshot/STOP-ON-SURPRISE/predicate-filter/
  write-back/verify-HOLD playbook as the YAHOO_FINANCE cleanup, HOLD proven across 6 real consolidator merge cycles.
  `market-tick-data-service@c24db4cf`. Full evidence in "Resolution — corporate_action_confirmed / earnings_result"
  above.
- **na-eligibility-audit 2026-07-30** (tradfi tranche): **KEEP-NA, valid.** Sole open todo is a `[DESIGN] P2` "decide
  whether real aggregated `ohlcv_15m`/`ohlcv_24h` TradFi bars are wanted" — a scope/product judgment call, not a
  worker-determinable fact. Not reclassified.
- **2026-07-31 (slot 4, review — `/plans/archive/2026_07/tradfi_consolidated_native_ao_extract_2026_07_25.md` todo 2,
  audit-only, no code change)**: live-verified CME `VENUE_DATA_TYPE_CAPABILITIES` billing-gating for
  `mbp_10`/`trades`/`tbbo` per the operator's 2026-07-18 "1-month L3 + 1-year L1" note. **Clean pass, no finding.** (1)
  `market_data_categories.py`'s `VENUE_DATA_TYPE_CAPABILITIES["CME"]` still declares ONLY `{ohlcv_1s, ohlcv_1m}` — the 3
  datatypes are absent entirely (neither billing-gated nor unrestricted), matching the still-standing 2026-05-15
  MVP-scope decision above; `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS` preserves their pre-narrowing windows for the
  stalled post-cutover restoration. (2) The actual enforcement mechanism IS live + correct:
  `databento_subscription_allowlist.py`'s `LEVEL_MAX_LOOKBACK_DAYS = {L1: 365, L2: 30, L3: 30}` +
  `assert_databento_request_allowed()` fail-closed (`DatabentoLookbackExceededError`) past each level's free window
  (`trades`/`tbbo`→L1, `mbp-10`→L2) — live-tested in `tests/unit/test_databento_subscription_allowlist.py`. No path
  declares these unrestricted for CME. No code shipped (repo: unified-api-contracts, read-only).

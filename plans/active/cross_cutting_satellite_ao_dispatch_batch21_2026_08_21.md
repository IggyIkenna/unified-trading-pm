---
doc_type: plan
title: cross-cutting satellite AO dispatch batch 21 — 2026-08-21
summary: >-
  Extraction batch from the cross-cutting tranche's 2026-08-21 `/na-eligibility-audit` sweep (batch 2 of 3,
  disjoint doc list) — 10 conflict-cleared, bounded/deterministic items pulled from 6 source docs (RECLASSIFY
  per-todo split each). Pure investigation/audit/mechanical-fix tasks with no open design or judgment call left in
  the extracted scope; each source doc's own remaining items stay `assigned_vm: NA` for genuinely gated work.
  Conflict-checked against every cross-cutting satellite batch (1b, 13-20) and the consolidated closeout doc before
  drafting — no item here duplicates ground an existing dispatched todo already claims.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, execution-service, market-tick-data-service, deployment-service, deployment-api, features-service, unified-trading-library]
scope: [engineer, admin]
tags: [cross-cutting, ao-dispatch, satellite-batch, na-eligibility-audit]
related:
  [
    /plans/active/issues/cross_cutting_data_type_completeness_capture_mis_scoped_ao_dispatch_2026_08_15.md,
    /plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md,
    /plans/active/issues/execution_state_does_not_survive_restart_2026_08_20.md,
    /plans/active/issues/external_market_data_response_leaks_vendor_pipeline_mode_2026_08_20.md,
    /plans/active/issues/market_data_timestamp_semantics_collapsed_to_one_field_2026_08_20.md,
    /plans/active/issues/mtds_availability_data_type_without_venue_silently_ignored_2026_08_19.md,
    /plans/active/issues/main_backmerge_backmerge_cycle_reverts_caller_stub_comment_fix_2026_08_20.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: worker
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/cross_cutting_data_type_completeness_capture_mis_scoped_ao_dispatch_2026_08_15.md,
    /plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md,
    /plans/active/issues/execution_state_does_not_survive_restart_2026_08_20.md,
  ]
source: >-
  /na-eligibility-audit cross-cutting tranche, batch 2 of 3, 2026-08-21. Each item's own Source: line below names
  the exact source doc + todo it was extracted from.
---

# cross-cutting satellite AO dispatch batch 21

## From `cross_cutting_data_type_completeness_capture_mis_scoped_ao_dispatch_2026_08_15.md`

- [ ] [DATA] P2. **Re-run the cross-data_type completeness measurement, now unblocked.** The blocking issue this
      todo was sequenced behind — `axis_value_census_mdps_scope_unbounded_read_hang_2026_08_15.md`'s unbounded-read
      performance bug — is now archived/resolved (`deployment-api@82b0469a7e`, pushdown filter shipped). Re-run
      `get_data_status_turbo_impl(service="market-tick-data-handler", start_date=..., end_date=..., include_sub_dimensions=True, check_upstream_availability=False)`
      per asset_group (all 5) and report real per-venue/per-data_type completeness gaps for non-`trades` data_types.
      If the call still hangs past a reasonable budget, root-cause `query_specific_prefixes_for_asset_group`'s own
      cost at this scale (the fixed doc's root cause was a DIFFERENT, MDPS-scoped call — this call was never
      directly confirmed to share the same fix). Done when: either real gap numbers are on record per asset_group,
      or a fresh root-cause is filed if the call still fails. Source:
      `cross_cutting_data_type_completeness_capture_mis_scoped_ao_dispatch_2026_08_15.md` todo 1 (line 115).
      **Do NOT** proceed to drafting per-AG backfill todos from the results — that remains this source doc's own
      todo 2, still `assigned_vm: NA` (sequencing/scoping judgment call).

## From `execution_delta_proxy_repricer_generalization_2026_08_18.md`

- [ ] [BACKEND] P3. **Fix the stale `_SCE_1H` strategy_id suffix on DeFi strategy configs.** DeFi is never
      SAME_CANDLE_EXIT per `hold-policy.md`; rename to the correct hold-policy abbreviation across
      `strategy_service/configs/carry_staked_basis.yaml` and any sibling DeFi config carrying the same stale
      suffix (grep first — the source doc notes "the same suffix recurs across several other DeFi configs,
      grepped, not exhaustively enumerated"), `close_all/__init__.py`'s dispatch dict, and
      `close_all/carry_staked_basis.py`'s `STRATEGY_ID` constant together (a rename needs every consumer migrated
      in the same change). The functional `execution_mode: continuous` field is already correct — only the id
      string is wrong. Done when: `_SCE_1H`/`_SCE` no longer appears in any DeFi strategy_id, all consumers
      migrated in one change, QG green. Source:
      `execution_delta_proxy_repricer_generalization_2026_08_18.md` todo at "Fix the stale `_SCE_1H` suffix".
- [x] ✅ [AGENT] P2. **Trace whether `HealthFactorMonitor`/`DeleverageExecutor` are wired to a real production
      entrypoint** — VERDICT: both are declared-but-unwired, same shape as `TransferCoordinator`/
      `OrderRecoveryEngine`/the deleted `QuoteHandler`. Evidence — `unified-trading-pm@<pending>`: (1)
      `HealthFactorMonitor(` has zero production constructor call sites in `execution-service`; the only two
      call sites are `tests/unit/defi_execution/test_health_factor_monitor.py`. No service bootstrap constructs
      it per-chain. `perp_hedge_wiring.py`'s own docstring independently confirms this: "no venue adapter exists
      for either perp venue; `HealthFactorMonitor`'s own fetch is injectable with zero production callers." (The
      similarly-named `PerpHedgeMonitor` in `perp_hedge_monitor.py` IS wired at `app.py` startup via
      `build_perp_hedge_lifecycle` — a distinct class that only mirrors `HealthFactorMonitor`'s `run()`/`stop()`/
      `_poll_loop()` shape; do not conflate the two.) (2) `DeleverageExecutor(` has zero production constructor
      call sites either — the only non-test instantiation is the module's own
      `_DEFAULT_EXECUTOR: DeleverageExecutor = DeleverageExecutor()` singleton in `deleverage_executor.py`,
      backing the `handle_margin_event()` convenience wrapper whose own docstring says "for smoke tests and
      ad-hoc CLI invocations" — not production. `MarginEvent` (the type it consumes) and `handle_margin_event`
      appear nowhere else in `execution_service/` — no Pub/Sub subscription, consumer, or service bootstrap
      references either. Done when: a definite wired/unwired verdict is on record with evidence. Source:
      `execution_delta_proxy_repricer_generalization_2026_08_18.md` todo "Trace whether HealthFactorMonitor/
      DeleverageExecutor are wired to a real production entrypoint".

## From `execution_state_does_not_survive_restart_2026_08_20.md`

- [x] ✅ [REVIEW] P1. **Rename or gut `execution-service/execution_service/pre_crash_checkpoint.py`.** It checkpoints — execution-service@f89497a825 + evidence: sanctioned tests slice passed (8,909 passed, 22 skipped, 1 XPASS; 82.68% coverage) and lint-codex slice passed; quickmerge execution-service content checks passed, while its shared adapter-contract post-check reported 2 unrelated UI baseline regressions
      nothing (a SIGTERM handler + an 85%-RSS watchdog, both converging on one `logger.critical` + `sys.exit()` —
      no state serialization, nothing reads it back) — the name asserts a guarantee the file does not provide.
      Rename to something accurate (e.g. `crash_alert.py`/`oom_watchdog.py`) or gut the misleading docstring/name.
      No behavior change. Done when: the file's name/docstring no longer implies state checkpointing. Source:
      `execution_state_does_not_survive_restart_2026_08_20.md` todo "Rename or gut pre_crash_checkpoint.py".
- [x] ✅ [AGENT] P1. **Enumerate execution-service classes with tests but no non-test instantiation.** AST-based
      scan (916 production classes; 161 have test-side constructor calls but zero non-test instantiation) — full
      list, methodology, and caveats filed in `execution_state_does_not_survive_restart_2026_08_20.md`'s new
      "Findings — execution-service classes with tests but zero non-test instantiation" section. Notable
      side-finding: corrected that same doc's own "OrderRecoveryEngine has zero production call sites" row — it is
      now wired (`live_execution_handler.py:136,189-222`), so it correctly does NOT appear in the 161. Follow-up
      per-class triage tracked as a new REVIEW P2 todo in the source doc, not done here (report-only scope).
      Evidence: unified-trading-pm@<pending>. Source:
      `execution_state_does_not_survive_restart_2026_08_20.md` todo "Enumerate execution-service classes with
      tests but no non-test instantiation".
- [ ] [REVIEW] P2. **Close the audit's own open questions** — read in full and report ABSENT/PRESENT (with
      evidence) for recovery-state-machine/fencing/reconciliation content in: `engine/orphan_monitor.py`,
      `venue_failover.py`, `venue_cascade_monitor.py`, `manual_pending_queue.py`, `order_rejection_tracker.py`,
      `utils/fidelity_selector.py`, `trade_execution/adapters/_rate_limit.py` (confirm/deny it's fencing-adjacent),
      and `sports_execution/monitoring/venue_health.py:23 VenueHealthStatus`. Pure read + report, no fix. Done
      when: each named file has a recorded PRESENT/ABSENT verdict with a one-line citation. Source:
      `execution_state_does_not_survive_restart_2026_08_20.md` todo "Close the audit's own open questions".

## From `external_market_data_response_leaks_vendor_pipeline_mode_2026_08_20.md`

- [x] ✅ [REVIEW] P1. **Audit `GET /external/market-data/delivery/stream` and `GET /external/market-data/availability`
      for the same `pipeline_mode`/vendor-bearing path leak** found on `GET /external/market-data/delivery/batch`.
      Pure investigation — report which (if any) of the two sibling endpoints leak the same vendor tag; do not fix,
      the mechanism decision (todo 1 in the source doc) is still open. Done when: both endpoints have a definite
      leak/no-leak verdict on record. Source:
      `external_market_data_response_leaks_vendor_pipeline_mode_2026_08_20.md` todo 2.
      **Done 2026-08-21** — `/availability` = NO LEAK (coverage-rollup aggregates only, no path/vendor field).
      `/delivery/stream` = LEAK, more directly than `/delivery/batch`: `CanonicalPersistEnvelope.pipeline_mode` is a
      named field serialized verbatim by `model_dump_json()`, plus `payload_pointer` (when set) re-leaks via
      path-embedding. Full findings + evidence filed in
      `external_market_data_response_leaks_vendor_pipeline_mode_2026_08_20.md`'s new "Findings — sibling endpoint
      audit (2026-08-21)" section. Evidence: unified-trading-pm@<pending>.

## From `market_data_timestamp_semantics_collapsed_to_one_field_2026_08_20.md`

- [x] ✅ [REVIEW] P1. **Audit every MTDS connector for which timestamp meaning it writes today** — roughly 65
      connector files exist, the source doc's own audit sampled about a dozen (Databento=exchange time,
      Binance-spot-book/Hyperliquid=arrival time). Classify each remaining connector as exchange-time,
      arrival-time, or unclear/needs-code-owner-input. Pure classification, no schema change. Done when: every
      connector file has a recorded classification. Source:
      `market_data_timestamp_semantics_collapsed_to_one_field_2026_08_20.md` todo "Audit every connector for which
      meaning it writes today". **Done 2026-08-21** — all 65 connector files classified (37 exchange-time w/
      arrival fallback, 11 pure arrival-time, 2 mixed-path needing code-owner input, 15 BLOCKED-* scaffolds with no
      live emission yet). Full table + methodology filed in
      `market_data_timestamp_semantics_collapsed_to_one_field_2026_08_20.md`'s new "Findings — full connector
      timestamp-semantics audit (2026-08-21)" section. Evidence: unified-trading-pm@c81b5881d8.
- [x] ✅ [REVIEW] P1. **Close or supersede `resolve_mtds_ts_event_timestamp_naming_collision`** — this exact
      timestamp collision was already identified and named in-code (referenced in `symbol_rules.py` comments) but
      never closed. Find the reference, establish whether that prior work was descoped, forgotten, or partially
      landed, and report which — before the P0 schema-split todos in the source doc re-do work that may already
      exist. Done when: a definite disposition (descoped / forgotten / partially-landed-where) is on record.
      Source: `market_data_timestamp_semantics_collapsed_to_one_field_2026_08_20.md` todo "Close or supersede
      resolve_mtds_ts_event_timestamp_naming_collision". **Done 2026-08-21** — neither descoped nor forgotten:
      partially landed (all 6 todos of `resolve_mtds_ts_event_timestamp_naming_collision_2026_08_05.md` shipped +
      verified 2026-08-05), then Phase 4 (alias removal) was specifically REVERTED in production 5 days later
      (market-tick-data-service@dcd3b7c401, 2026-08-10, "restore ts_event→timestamp alias copy — unblock VIX/CBOE
      ohlcv_1m schema validation") and never corrected in the archived plan pair. Live code today
      (`symbol_rules.py:84-88`) still carries the `ts_event→timestamp` alias Phase 4 claimed to have removed;
      Phases 1-3 remain intact. Full evidence chain filed in
      `market_data_timestamp_semantics_collapsed_to_one_field_2026_08_20.md`'s new "Findings — disposition of
      resolve_mtds_ts_event_timestamp_naming_collision" section. Evidence: unified-trading-pm@<pending>.

## From `mtds_availability_data_type_without_venue_silently_ignored_2026_08_19.md`

- [x] ✅ [REVIEW] P1. **Check the sibling parameters on `GET /external/market-data/availability`** —
      `asset_group`, `instrument_type`, and any other optional filter — for the same conditional-branch silent-drop
      bug found for `data_type` without `venue`. Pure investigation; the fix decision (todo 1 in the source doc)
      is still open. Done when: each sibling parameter has a definite affected/unaffected verdict on record.
      Source: `mtds_availability_data_type_without_venue_silently_ignored_2026_08_19.md` todo 2.
      **Done 2026-08-21** — `asset_group` UNAFFECTED (required, not optional — no silent-drop path exists);
      `instrument_type` N/A (no such parameter exists on this endpoint — the only `instrument_type` hit anywhere
      in the file/tests is an unrelated mocked path-segment string); `date` UNAFFECTED (consumed unconditionally
      regardless of `venue`/`data_type`); `venue` UNAFFECTED (the conditioning parameter itself, always applied
      when present). Only `data_type` was ever affected by this bug class, already fixed
      (market-tick-data-service@8addeac2). Full evidence in
      `mtds_availability_data_type_without_venue_silently_ignored_2026_08_19.md`'s new "Findings — sibling
      parameter audit (2026-08-21)" section. Evidence: unified-trading-pm@<pending>.
- [ ] [AGENT] P2. **Sweep the three external routers for silent-no-op parameters generally**
      (`instruments-service/.../external.py`, `market-tick-data-service/.../external.py`,
      `execution-service/.../external_instruction_api.py`) — a parameter accepted, silently ignored, and returning
      200 is indistinguishable from a working one. Pure investigation/report, no fix. Done when: each router has a
      recorded list of any silent-no-op parameters found (or a clean verdict). Source:
      `mtds_availability_data_type_without_venue_silently_ignored_2026_08_19.md` todo 3.

## From `main_backmerge_backmerge_cycle_reverts_caller_stub_comment_fix_2026_08_20.md`

- [ ] [CI] P2. **Re-ship the caller-stub comment fix to the 3 repos blocked on pre-existing QG reds**
      (features-service RB-5e5dbb39, unified-trading-library RB-09ca4f33, execution-service RB-70f96454) once each
      repo's QG is green: fresh-pull, re-apply the `.github/workflows/main-backmerge-to-ldr.yml` caller-stub
      comment fix (the same fix already landed on the other 22 repos, cited in the sibling doc
      `main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md` todo 2's evidence list), QG green,
      quickmerge `--agent`. If a repo's QG red is still unrelated-but-unresolved, report it as still-blocked rather
      than force a ship. Done when: all 3 repos carry the corrected comment on `origin/live-defi-rollout`, or each
      remaining block is reported with its current blocker. Source:
      `main_backmerge_backmerge_cycle_reverts_caller_stub_comment_fix_2026_08_20.md` todo 2.

## Progress Log

- **2026-08-21 (slot-4)** — Closed the vendor-tag-leak sibling-endpoint audit todo. `/availability` = no leak,
  `/delivery/stream` = leak (worse than `/delivery/batch` — a named `pipeline_mode` field, plus `payload_pointer`
  path-embedding). Full findings in `external_market_data_response_leaks_vendor_pipeline_mode_2026_08_20.md`.
- **2026-08-21 (slot-16)** — Closed the MTDS-connector-timestamp-audit todo. All 65 connector files classified
  (37 exchange-time w/ arrival fallback, 11 pure arrival-time, 2 mixed-path, 15 BLOCKED-* scaffolds). Evidence in
  `market_data_timestamp_semantics_collapsed_to_one_field_2026_08_20.md`'s new Findings section.
- **2026-08-21**: drafted by na-eligibility-audit (cross-cutting tranche, batch 2 of 3). All 10 items conflict-
  checked against every existing cross-cutting satellite batch (1b, 13-20) and the consolidated closeout — no
  duplication found.
- **2026-08-21 (slot-10)** — Closed the `resolve_mtds_ts_event_timestamp_naming_collision` disposition todo.
  Disposition: partially landed, then Phase 4 (alias removal) reverted in production 5 days later
  (market-tick-data-service@dcd3b7c401, 2026-08-10) after breaking VIX/CBOE `ohlcv_1m` backfills — never corrected
  in the archived plan pair. Full evidence in
  `market_data_timestamp_semantics_collapsed_to_one_field_2026_08_20.md`'s new Findings section.
- **2026-08-21 (slot-1)** — Closed the `GET /external/market-data/availability` sibling-parameter audit todo.
  `asset_group` UNAFFECTED (required, not optional), `instrument_type` N/A (no such parameter exists on this
  endpoint), `date` UNAFFECTED (applied unconditionally), `venue` UNAFFECTED (the conditioning parameter itself).
  Only `data_type` was ever affected by the silent-drop bug, already fixed. Full evidence in
  `mtds_availability_data_type_without_venue_silently_ignored_2026_08_19.md`'s new Findings section.

---
doc_type: plan
title: cefi satellite AO dispatch batch 19 — 2026-08-13
summary: >-
  Extraction batch from the cefi tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep — 37 live
  conflict-cleared, bounded/deterministic items (40 total todos, 3 marked out-of-scope, see below) pulled directly from
  10 source docs (RECLASSIFY_SPLIT bounded items from the NA audit, orphaned_never_touched/orphaned_partial_coverage
  bounded items from the AG-closeout audit). Rescoped 2026-08-13 (operator scoping instruction): 3 MDPS-backfill items
  with no manifest-canonical/migration angle marked [x] OUT-OF-SCOPE (checkbox format per
  todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md -- the source items remain open in their
  own source docs, untouched by this batch). Each todo cites its exact source doc; the source docs themselves are NOT
  touched by this batch (checkbox reconciliation back into each source doc happens in the paired finalize plan).
  Conflict-checked against every existing active batch/finalize plan for this tranche via basename-citation
  cross-reference before drafting — no item here duplicates ground an existing dispatched Todos entry already claims.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md,
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
    /plans/active/issues/dp_vm_002_mdps_cefi_2021_silent_zero_false_positive_2026_08_11.md,
    /plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md,
    /plans/active/issues/mdps_cefi_chain_bundle_delay_features_timestamp_float_compare_2026_08_12.md,
    /plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md,
    /plans/active/issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md,
    /plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 5.6
estimate_calibrated_ai_days: 4.4
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# cefi satellite AO dispatch batch 19 — 2026-08-13

> **Operator-approved 2026-08-13 — `status: active`, dispatchable.** Every todo below was classified
> bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13 full-sweep audit
> and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [x] ✅ [WRITER] P2. implement Gap 1's resolution — row-level column-value gate for bundle-shaped
      (chain-bundle/options_chain) writers, dropping non-canonical rows to record_failed(NON_CANONICAL_INSTRUMENT_ID,
      granularity=row) + adding quarantined_legs to the manifest row (market-tick-data-service) Source:
      `plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md` — **SHIPPED
      market-tick-data-service@c1626c5dbd** (a7a1ae39 gate + c1626c5d file-size-cap consolidation, no behavior change).
      `finalise_rows_and_path` classifies each chain-bundle row's own `instrument_id` immediately before write via
      `classify_id_form()`; NON_CANONICAL rows drop (canonical + registered-quarantined legs both survive) and are
      tracked on the new `FinalisedShard.quarantined_legs`, propagated through `ShardChunk.metadata`, and routed to a
      per-leg `record_failed(error="NON_CANONICAL_INSTRUMENT_ID")` manifest row in
      `finalise_and_write_cefi_shards_streaming` (reconciliation queries these by `error=`/`underlying=`/`day=` rather
      than a first-class `quarantined_legs` field on the aggregate row — see the new todo below). 4 new unit tests
      (`tests/market_interface/adapters/cefi/test_chain_bundle_row_level_id_gate.py`). **Prerequisite fix shipped
      alongside**: the row-level gate exposed a real, pre-existing UAC ID_FORM-oracle gap —
      `is_canonical_instrument_id`'s regex only recognized the `@LIN`/`@INV` margin-marker convention, not the
      co-existing legacy lowercase `-inverse`/`-linear` word-form suffix `_build_option`/`_build_future` still emit when
      `quote_asset`+`margin_type` are supplied without a `margin_marker` — so the new gate was misclassifying real
      DERIBIT/BYBIT inverse+linear options_chain/futures_chain rows as NON_CANONICAL and dropping legitimate production
      data. Fixed at the oracle (widened `_CANONICAL_INSTRUMENT_ID_RE`), not worked around in the writer — **SHIPPED
      unified-api-contracts@8b81dd78bb**.
- [ ] [WRITER] P3. Extend Gap 1's row-level gate with first-class manifest visibility: add a `quarantined_legs` field to
      UTL's `ManifestRow` schema (unified-trading-library) and thread it from `FinalisedShard.quarantined_legs` through
      `ShardChunk.metadata` → the day-level `_DateRunState` accumulator (`venue_fetch.py`) → `_write_bundle_shard_row`'s
      aggregate `record_captured_from_counts` call (`manifest_finalize.py`), so the underlying-keyed captured row itself
      carries the dropped-leg list, per §5b's original "the manifest keeps its existing underlying-keyed row, plus a new
      quarantined_legs: [...] field" spec. Deferred out of the Gap 1 todo above because `ManifestRow` lives in a
      different repo (unified-trading-library) not named in that todo's scope, and today's per-leg
      `record_failed(error="NON_CANONICAL_INSTRUMENT_ID")` rows already give reconciliation a queryable (if
      row-granularity rather than field-granularity) signal. Repos: unified-trading-library, market-tick-data-service.
      Source: `plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md` §5b.
- [ ] [WRITER] P2. implement Gap 2's resolution — make the live/on-chain lane's manifest key a deterministic function of
      the already-computed column value instead of an independent resolve_cefi_instrument_id() call
      (market-tick-data-service: venue_fetch.py, partitioned_writer.py) Source:
      `plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md`
- [ ] [UAC] P3. implement Gap 3's resolution — add the temporal 'unclassified' manifest-row state and wire the Stage 3
      read gate to pass-with-warning on it until a backfill-complete flag promotes it to enforced-fail
      (unified-api-contracts + market-tick-data-service) Source:
      `plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md`
- [ ] [SCRIPT] P3. Root-cause + fix mtds_chunk_loop.sh's PROGRESS.json GCS upload call - confirmed silently stopped
      firing after chunk 17 on mtds-backfill-odds-smallchunk2-20260807 while run.log's own PROGRESS: chunk=N lines kept
      advancing normally through at least chunk 21. Done when: the upload call's failure mode is identified (e.g. a
      swallowed exception, a once-per-VM-lifetime guard misfiring, a stale path) and fixed, with a regression check that
      PROGRESS.json keeps advancing across >=20 consecutive chunks on a fresh run. Repo: deployment-service. Source:
      `plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`
- [x] [CODE] P2. Re-launch mdps-cefi-2021-* sharded MDPS CeFi backfill (launch-mdps-sharded-backfill.sh cefi
      --year 2021) **OUT-OF-SCOPE FOR THIS BATCH (2026-08-13, operator scoping instruction)** — MDPS/features-service
      backfill/recompute work is excluded from this batch unless manifest-canonical or migration-related. The underlying
      item remains open in its own source doc, untouched by this batch/commit. Source:
      `plans/active/issues/dp_vm_002_mdps_cefi_2021_silent_zero_false_positive_2026_08_11.md`
- [ ] [CODE] P2. Capture Binance/OKX/Bybit indexPrice+markPrice+fundingRate as a first-class MTDS data_type (Phase 1b
      follow-up, market-tick-data-service) Source:
      `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`
- [ ] [CODE] P2. Recurring daily funding/basis scan across crypto-venue equity-perps (e2e-testing, scheduled job)
      Source: `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`
- [ ] [CODE] P2. Backfill the 3 KRX stocks via guardrailed Yahoo (Phase 5, deployment-service +
      market-tick-data-service) Source: `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`
- [ ] [CODE] P2. Databento L-floor boundary PRECISION probe + update LEVEL_MAX_LOOKBACK_DAYS (Phase 5,
      unified-api-contracts) Source: `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`
- [ ] [CODE] P2. Deprecate + remove all Barchart code (Phase 5, cross-repo delete-deprecated-code) Source:
      `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`
- [ ] [CODE] P2. Map the index perps (SPXUSDT/NAS100/SPYUSDT/XAUUSDT) to the CME index-future canonical with
      contract_multiplier (Phase 1c, unified-api-contracts) Source:
      `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`
- [ ] [CODE] P2. Codex SSOT updates for crypto-venue equity-perp sourcing + equity-basis arb archetype Source:
      `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`
- [ ] [CODE] P2. Alert-accuracy quartet fix (deployment-service: interpolate/drop fixed '(0 → 0)' template, extend
      captured-reader probe fallback, conditional Tardis-guard text, exempt cron/launcher host VMs from GONE_NO_CAPTURE)
      Source: `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Determine which layer wrote the cefi attempted_failed rows (MTDS fetch vs MDPS derivation) and whether
      the 2026-08-02 ruling inflates them Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Chain relabel migration part 2 of 2 (options_chain/futures_chain path-position fix,
      entity-rename-governed, writer+manifest+status+gate+UI same change) Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Resolve margin_type for the ~1,578 cefi liquidation instrument_ids lacking @LIN/@INV suffix via
      instruments-service reference data Source: `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Widen canonical_writer_shaping int32->int64 coercion to every contract-declared int64 column (or assert
      dtype match at the write seam) Source: `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Audit UNCLASSIFIED_ADAPTER_ERROR rows (51% of trades cell, 14% of derivative_ticker) Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Fix meta_watchers.check_high_attempted_failed's mismatched trailing-14-day-numerator vs
      all-time-denominator ratio Source: `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Fix sports reference-table exporter fabricating http_status=200 FetchEvidence for a GCS-missing
      upstream Source: `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Recompute the 2026-08-10 sports reference tables once instruments-service backfills that day Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [x] [CODE] P2. Shard the slow date in the MDPS per-date backfill so one date cannot fail a complete run **OUT-OF-SCOPE
      FOR THIS BATCH (2026-08-13, operator scoping instruction)** — MDPS/features-service backfill/recompute work is
      excluded from this batch unless manifest-canonical or migration-related. The underlying item remains open in its
      own source doc, untouched by this batch/commit. Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [x] [CODE] P2. Rightsize the MDPS backfill VM class per the 2026-08-10 rightsizing HARD RULE **OUT-OF-SCOPE FOR THIS
      BATCH (2026-08-13, operator scoping instruction)** — MDPS/features-service backfill/recompute work is excluded
      from this batch unless manifest-canonical or migration-related. The underlying item remains open in its own source
      doc, untouched by this batch/commit. Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Fix empty instrument_id in the chain-bundle path (live_workers_streaming.py writing no manifest row)
      Source: `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Promote _ShardedState out of relaunch_backfill_vm.py into a shared helper Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Fix flaky shellcheck under host load in launch-expected-universe-v2-vm.sh Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Generalise the test-hermeticity guard for the pytest fake-GCS backend persistence bug Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Fix the pre-existing hardcoded-prod-project-ID QG violation in test_vm_launcher_scripts.py Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Track 0: Capture Binance/OKX/Bybit indexPrice/markPrice/fundingRate for equity-perps as a first-class
      data_type Source: `plans/active/cefi_consolidated_closeout_2026_07_18.md`
- [ ] [CODE] P2. Track 0: Wire a recurring daily funding/basis scan across all crypto-venue equity-perps Source:
      `plans/active/cefi_consolidated_closeout_2026_07_18.md`
- [ ] [CODE] P2. Track 0: Launch the CeFi Tardis backfill for the equity-perp window Source:
      `plans/active/cefi_consolidated_closeout_2026_07_18.md`
- [ ] [CODE] P2. instrument_type casing residual: fresh live re-count against current manifest to confirm literal 100%
      UPPERCASE Source: `plans/active/cefi_consolidated_closeout_2026_07_18.md`
- [ ] [CODE] P2. Live-query OKX/Bybit SPOT instrument endpoints for the tokenized-equity symbol set + listing dates
      Source: `plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md`
- [ ] [CODE] P2. Add confirmed tokenized-equity symbols to the UAC CeFi instrument universe with
      instrument_type=SPOT_PAIR + tracks_equity link Source:
      `plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md`
- [ ] [CODE] P2. Add confirmed symbols to the CeFi MVP scope rule (mirror CEFI_EQUITY_PERP_BASE_UNIVERSE pattern)
      Source: `plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md`
- [ ] [CODE] P2. Register an InstrumentRecord per confirmed symbol dated to its real historical listing date Source:
      `plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md`
- [ ] [CODE] P2. Launch the CeFi Tardis/venue-native backfill for the tokenized-equity SPOT window Source:
      `plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md`
- [ ] [CODE] P2. Grep prior mdps-cefi-_/mdps-tradfi-_/mdps-defi-* run.log archives (or manifest attempted_failed reason
      strings) for the exact Timestamp-vs-float TypeError signature to size the historical blast radius, and re-trigger
      record_failed→retry for any shard whose failure resolves to this exact root cause Source:
      `plans/active/issues/mdps_cefi_chain_bundle_delay_features_timestamp_float_compare_2026_08_12.md`
- [ ] [CODE] P2. Mechanical citation-reconciliation for todo 2 (S1-b): flip the checkbox to [x] citing
      deployment-service@e7d17f2 + the CEFI 117-shard/DeFi 3,535-shard production verification already documented
      in-doc, and update the doc's stale 'Big findings — Recommended (A): delete' section to reflect that option (B)
      finish-the-dispatcher-branch is what actually shipped Source:
      `plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md`
- [ ] [CODE] P2. Archive this doc via the 6-step archival ritual
      (/codex/12-agent-workflow/plan-completion-and-archival-discipline.md), repointing the 7 listed active corpus
      referrers (tradfi_satellite_ao_dispatch_batch7_2026_08_06.md, ag_closeout_audit_defi_parked_2026_08_08.md,
      mdps_features_deadcode_consolidation_2026_07_20.md, plans/active/INDEX.md, plus 3 already-repointed archive-path
      references) in the same commit Source:
      `plans/active/issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.

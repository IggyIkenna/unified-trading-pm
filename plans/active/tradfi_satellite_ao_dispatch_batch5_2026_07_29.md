---
doc_type: plan
title: TradFi satellite AO batch 5 — fresh /ag-closeout-audit extraction (mvp_mode ruling + 14 more clean orphans)
summary: >-
  Fifth AO-dispatch batch for tradfi, produced by a fresh `/ag-closeout-audit tradfi` pass on 2026-07-29 (autonomous
  mode, scheduled daily worker), run via a 32-agent Workflow classifying every tradfi-primary non-covering doc against
  the 18-doc covering set (consolidated closeout + 5 forked children/extracts + finalizes + batch1/2/4 + archived
  batch3). 28 of 32 candidates came back orphaned in some form (16 partial-coverage, 12 never-touched); of those, 15
  todos across 15 source docs cleared the Phase-3 conflict-check and are drafted below. The originally single
  highest-value item, `tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md`'s `[CODE] P1` — the operator ruled the
  `mvp_mode` wire-vs-delete question in an interactive session THIS SAME DAY (2026-07-29), after 3 prior batches (1/2/4)
  correctly left it deferred as operator-gated — **has since been shipped independently (2026-07-30, before this draft
  batch was ever approved) via a bundled todo in the separately-active
  `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`, `deployment-service@c847395e`; this batch's own todo 1 is marked
  done-by-cross-reference below rather than left as live dispatchable work.** The rest of the 13
  orphaned-but-not-drafted docs stay deferred: 4 too-large-or-risky (unchanged from batch1-4), ~7 operator-gated
  (unchanged, not re-asked), 2 conflict-gated on still-unresolved sequencing
  (`tradfi_multisource_backfill_2026_06_22.md`'s FX-yahoo-drain item,
  `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`'s actual bucket-delete item — both discussed in the Deferred
  section). Also notes 2 process observations for the operator/main-agent (not batch todos):
  `tradfi_satellite_ao_dispatch_batch4_2026_07_26.md` is 8/8 done and unlocked but its gated finalize is still `status:
  draft`, undispatched; `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` is still `status: draft` (1/15 done)
  despite carrying a live 2026-07-29 todo for the FX/ICE/KRX historical re-stamp.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos:
  [
    unified-trading-pm,
    market-tick-data-service,
    market-data-processing-service,
    unified-api-contracts,
    features-service,
    deployment-service,
  ]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-5, satellite-docs, mvp-mode, conflict-checked]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch4_2026_07_26_finalize.md,
    /plans/archive/issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md,
    /plans/active/issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-29"
last_updated: "2026-08-02"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.6
estimate_calibrated_ai_days: 1.3
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit tradfi run 2026-07-29 (autonomous / AO-dispatched mode, scheduled daily `ag_closeout_auditor`
  worker, operator away). Phase 0 discovered the 18-doc covering set via both documented paths (filename-pattern +
  dependency-graph — the latter caught 5 forked children/extracts a naive filename grep would have missed and
  misclassified as orphan candidates: `tradfi_manifest_content_recovery_completion_2026_07_24.md`,
  `tradfi_backfill_throughput_followups_2026_07_24.md`, `tradfi_phase_d_terminal_gate_2026_07_24.md`,
  `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`, `tradfi_consolidated_native_ao_extract_2026_07_25.md`).
  Phase 1 classified all 32 remaining tradfi-primary candidates via a `Workflow` (one agent per doc, 2 passes needed —
  17 of 32 agents hit transient 500/529 API errors on the first pass and were cleanly re-run via `resumeFromRunId`, 0
  errors on the second pass). Phase 3 ran the conflict-check against the full covering family before drafting any todo
  below; conflicts found are parked in the Deferred section, not silently resolved.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/epics/tradfi_master.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
---

# TradFi satellite AO batch 5 — fresh audit extraction

> **🟡 tradfi backfill VM launches are currently BLOCKED fleet-wide (2026-08-02).** The tradfi market-data
> manifest-consolidator cron is paused (owning plan:
> `/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`), so every tradfi download-VM launch — including
> todo 1's ES/MES re-run — self-deletes at boot (`exit_code=78`, OOM preflight) before doing any work. Do not relaunch a
> tradfi download VM until that plan's cron-resume lands. Details:
> `/plans/active/issues/tradfi_ohlcv_backfill_oom_preflight_fails_paused_consolidator_2026_08_02.md`.

> **Status: active — approved + dispatched 2026-07-30 (`5a6bbefc3`, "activate 9 fresh ag-closeout-audit dispatch
> batches").** This pass originally ran on the scheduled daily worker as `status: draft` per the ag-closeout-audit
> skill's never-auto-ship design; the operator has since reviewed and approved it for dispatch alongside 8 other
> batches. (This banner previously said "draft — NOT approved, NOT dispatched" — stale since the frontmatter flip;
> corrected 2026-07-30 by slot 5 while working todo 3.)
>
> All 15 todos below are same-priority-independent and were checked for file collisions (see the matrix near the bottom)
> — 14 touch distinct files/scripts; todos 6/7/8 share a FX/YAHOO_FINANCE venue-stamping neighborhood and carry an
> explicit ordering note rather than a hard merge, mirroring how batch4 handled its own two same-file todos.

## Why this batch exists

This is the first fresh `/ag-closeout-audit tradfi` pass since batch4 (2026-07-26). Three days is enough for real new
ground to open up, and it did:

1. **The mvp_mode operator ruling landed TODAY (2026-07-29).** _(2026-07-30 update: shipped since — see below.)_
   `issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md` has been flagged operator-gated across every batch since
   batch2 (2026-07-25) — batch3 and batch4 both explicitly declined to re-ask an already-asked question. Today, in an
   interactive decision session, the operator ruled: wire `mvp_mode` via an opt-in flag on the existing
   `launch-tradfi-forward-poll.sh` launcher (not a new dedicated launcher, never default-on). The issue doc now carries
   a fully-specified `[CODE] P1` implementation plan ((i)-(iv), exact files, exact repos, explicit done-when) with zero
   judgment call left. batch4 (created 2026-07-26) cannot possibly reference this — it predates the ruling by 3 days.
   **This batch (batch5) was itself never approved/dispatched (`status: draft` throughout) — the implementation instead
   landed via a DIFFERENT, separately-active plan's bundled todo (`tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s
   `[OPERATOR] P2` item), shipped `deployment-service@c847395e` on 2026-07-30. Verified live: the commit matches this
   doc's own (i)-(iv) plan exactly. See this batch's todo 1 (marked done-by-cross-reference) and the Progress Log
   below.** This is the cleanest, highest-confidence todo in this batch.
2. **A blocker with wide downstream reach has a live mitigation to re-test.** `_retry_empty_day_listing`
   (`market-data-processing-service@22b926c`) shipped to address the listing-consistency hypothesis behind
   `issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md`'s stuck ~19% hit rate. That doc's
   own blocker has been gating `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` (`orphaned_never_touched`,
   deferred below as too-large) for 3+ batches. Re-running the backfill+build-continuous+re-measure sequence now is the
   one action that could unblock that whole downstream chain on a future batch.
3. **14 more docs came back genuinely orphaned with clean, conflict-free, bounded residual work** — a mix of
   root-cause-and-fix data-correctness items, mechanical test/doc fixes, and scoped investigations with an
   already-prescribed next step. None of these are referenced by any doc in the 18-doc covering family (verified by
   grep + read, not just grep, per the skill's Phase 1 discipline).

## Todos

- [x] ✅ **ALREADY DONE — confirmed 2026-07-30, before this batch was ever approved/dispatched.** This exact ruling was
      independently picked up and shipped as part of `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s bundled
      `[OPERATOR] P2` todo (a different, already-active/dispatched batch, not this draft one) —
      `deployment-service@c847395e` (2026-07-30), verified live: commit exists, diff matches this todo's (i)-(iv) plan
      exactly — `setup-data-pipeline-vm.sh`'s `mtds-backfill` branch got `VM_MVP_MODE` metadata plumbing mirroring
      `VM_FORCE`; `launch-tradfi-forward-poll.sh` got the opt-in `--mvp-mode` flag -> `VM_MVP_MODE=true` metadata,
      default behavior unchanged; `launch-tradfi-bf-cme-ohlcv-1m.sh`/`launch-tradfi-backfill-vm.sh` confirmed untouched.
      One deliberate deviation from this todo's drafted (iii): the regression test landed as a new
      `TestMtdsBackfillMvpModeFlag` class in `deployment-service/tests/unit/test_vm_launcher_scripts.py` (extracting the
      real script lines, the repo's established idiom for this) rather than in the MTDS test files this todo suggested —
      MTDS was never actually touched by the shipped fix, so an MTDS test would have had nothing real to assert against;
      the deployment-service home is the correct one. Issue doc
      `issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md` has all 4 of its own todos flipped `[x]` citing this
      same commit. **Nothing left for this batch to do on this item** — leaving this todo checked here purely so this
      draft, if ever approved, does not re-dispatch duplicate work. Originally: wire `mvp_mode` via an opt-in flag on
      the forward-poll launcher — operator-ruled 2026-07-29. Source:
      `issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md`.

- [ ] [DATA] P1. **Re-run the ES/MES per-contract backfill a third time now that the listing-retry mitigation is live,
      then re-measure the continuous_future hit rate.** Launch `launch-mdps-backfill-vm.sh` for tradfi ES/MES over the
      full 2020-01-01..2026-07-25 history (the same window the prior 2 attempts covered), then re-run MDPS
      `--operation build-continuous --root ES`, then compare the 1d/24h `continuous_future` hit rate against the ~19%
      (454/2398) baseline recorded in the issue doc. This is a re-run/re-measure using an already-approved backfill
      shape (SPOT provisioning per the standing backfill-VM default), not a new design. Repos:
      market-data-processing-service, deployment-service. **Done when**: a dated measurement section in the issue doc
      reports the new hit rate, states whether `_retry_empty_day_listing` resolved, further-reduced, or did not move the
      mismatch, and either flips the doc's open item or restates the precise remaining gap. Source:
      `issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md`. **NOT YET DISPATCHABLE
      (2026-07-31, slot-2, data_engineering craft)**: a fresh ES/MES per-contract "process" step launch already
      genuinely satisfies this todo's "launch" half — see Progress Log below; still mid-backfill, gated on that fleet
      finishing before build-continuous + the re-measure can run.

- [x] ✅ [DATA] P0. **Migration/purge pass for CME+CBOE `WithinBoundsTradfiSourceZero` bundle-grain rows, plus harden
      the script against recurrence — combined into ONE todo because both edit the same script.** (1) Run a
      snapshot-before-write, dry-run-default migration/purge pass over CME+CBOE bundle-grain
      `attempted_failed(WithinBoundsTradfiSourceZero)` rows keyed by the retired `instrument_id=<parent>.FUT/.OPT`
      grain, retiring stale rows where a real `captured` row already exists under the post-fix key. (2) Harden
      `market_tick_data_service/scripts/_rebuild_tradfi_cf11.py::_handle_srz_tradfi_row` to check for an existing
      correctly-keyed captured shard before reclassifying, preventing recurrence. Repo: market-tick-data-service. **Done
      when**: the dry-run output + row counts are recorded in the issue doc's Progress Log before any apply, the apply
      runs only after that review, `_handle_srz_tradfi_row` has a regression test proving it no longer reclassifies over
      an existing correctly-keyed capture, and `quality-gates.sh` is green. Source:
      `issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md`. — **DONE 2026-07-30 (slot 5).** The
      hardening + migration script shipped `market-tick-data-service@11be9cfe` (landed independently by slot 11 just
      before this dispatch, verified live — diff matches this todo's (1)-(2) exactly, 6 tests added). This session ran
      the dry-run against the LIVE manifest and recorded the measured counts in the issue doc's Progress Log: 114,318
      candidates (CME 111,829 + CBOE 2,489), 81,454 droppable (CME 78,965 + CBOE 100%), 32,864 CME unresolved (genuine
      failures / naming-drift tail, left untouched). Regression suite (23 tests) re-verified green in a fresh `.venv`;
      no code changed this session. **`--apply` intentionally NOT run** — flagged via `/blocked` for operator go-ahead
      per the script's own docstring gate (destructive ~81K-row live-manifest CAS mutation); the issue doc's own todo 1
      stays open tracking that follow-up so it isn't lost.

- [x] ✅ [DATA] P1. **DONE 2026-07-31 (slot 3, data_engineering) — all 4 items resolved; items 1/2 RE-CHARACTERIZED with
      evidence rather than force-fitted to the todo's original "live writer bug" premise.** Live re-measurement
      (single-object manifest read) showed all 4 populations byte-identical to the 2026-07-27 counts (zero growth in 4
      days) — first sign this wasn't an active bleed. Directly exercised `_resolve_tradfi_manifest_shard` with the real
      (venue, itype, symbol) shapes for every population: the CURRENT code resolves every genuinely-fixable case
      correctly today (NASDAQ/equity, NYSE/etf, CBOE/index, FX/spot_pair all canonical; CBOE/option correctly id-less by
      design). Checking the `date` (content-day) distribution for items 1/2/3b showed each spans DOZENS of scattered
      historical dates across 2024-2026 sharing one narrow `written_at=2026-07-27T16:46:40-48Z` burst — the signature of
      a one-time historical registration/recovery script, not a live/scheduled capture bug. **Item 3's leading
      hypothesis was WRONG**: `unified-api-contracts` confirms `YAHOO_FINANCE` was deliberately REMOVED as a venue
      2026-07-15 (source-as-venue modeling error) — do NOT re-register it, `TRADFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES`
      already absorbs this exact residual. Item 3a (FX bare-id) confirmed fixed for new captures (0 growth since
      2026-07-25). **Items 1/2's actual remaining work** (historical-row repair, not a live-writer fix) split into its
      own properly-scoped follow-up todo rather than rushed/force-fitted here. Item 4 count reconfirmed (9,126 rows,
      static). Shipped 6 regression tests locking in the resolver's current-correct behavior:
      `market-tick-data-service@41391cba` (verified on origin). Hit + resolved an unrelated pre-existing QG red along
      the way (repo-blocker RB-6f0ca058,
      `issues/mtds_qg_pytest_red_pipeline_e2e_sampler_and_flaky_defi_lst_2026_07_31.md` — later self-corrected: my own
      explicit `GCP_PROJECT_ID`/`CLOUD_PROVIDER` env-var override, not the repo, caused the consistent failures; a
      clean-env run is green). Full findings + evidence:
      `issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md` (`unified-trading-pm@061741184`). Repo:
      market-tick-data-service.

- [ ] [DATA] P2. **Trace/fix 3 distinct-value mis-stamp clusters — combined into ONE todo because all 3 edit the same
      issue doc.** (1) Trace the `ESM0`/`ESM0_MIGRATED_20260418T131054Z` chain-axis writer in the tradfi manifest and
      either blank the chain column or re-stamp the 7+7 affected rows. (2) Confirm whether `YAHOO_FINANCE` should be
      added to `VENUES_BY_ASSET_GROUP['tradfi']` or is a mis-stamped `source=` value leaking into `venue` — **same
      YAHOO_FINANCE venue question as todo 8; run that investigation once and cite it here rather than duplicating**.
      (3) Identify what writes `instrument_type='UD'` in tradfi and register or trace it as a mis-stamp. Repos:
      market-tick-data-service, unified-api-contracts (`VENUES_BY_ASSET_GROUP`). **Done when**: each of the 3 clusters
      has either a shipped fix (chain column blanked/re-stamped, `UD` writer identified+registered) or a recorded
      `venue`-vs-`source` verdict for `YAHOO_FINANCE` consistent with todo 8's finding, with all 3 checkboxes flipped.
      Source: `issues/tradfi_distinct_values_net_new_clusters_2026_07_28.md`.

- [ ] [DATA] P2. **Run the Phase-0 YAHOO_FINANCE venue-vendor-conflation investigation methodology already defined in
      the doc** (reconcile real counts + trace consumers for a `venue="YAHOO"` dependency), starting at
      `yahoo_finance_adapter.py`'s `write_canonical_shard` per the doc's own recommended entry point, before deciding
      whether/how to fix the vendor-as-venue stamp. **Run this FIRST among todos 6/7/8** if it touches the same file as
      either (see the file-collision note below) — its output directly answers todo 7 item 2's YAHOO_FINANCE question
      and informs todo 4 item 3's FX/YAHOO_FINANCE root-cause. Repo: market-tick-data-service. **Done when**: the
      investigation's count-reconciliation + consumer-trace is recorded in the doc with an explicit fix-or-no-fix
      recommendation, and that finding is cited (not re-derived) by todos 4 and 7 above. Source:
      `issues/tradfi_yahoo_venue_vendor_conflation_2026_07_27.md`.

- [ ] [SCRIPT] P2. **Write a register-phase script + investigate quarantine staleness — combined into ONE todo because
      both edit the same issue doc.** (1) Write a register-phase script (mirroring
      `recover_tradfi_chain_manifest_registration_2026_07_22.py`'s register phase) that additively registers manifest
      rows for the ~428 content-recovered-but-unregistered combo/chain cells from run `20260720-120911`, confirmed via
      targeted (non-corpus-walk) `gcs_describe_object` checks. (2) Investigate what pruned/reused
      `_quarantine/raw_tick_data/` between 2026-07-20 and 2026-07-27 (0/98,256 of this run's quarantine targets still
      exist; only 9 unrelated day=2026-01-* prefixes remain). Repo: market-tick-data-service. **Done when**: every
      reachable canonical bundle target that exists on GCS and has no manifest row is registered (count reported against
      the ~428 upper bound), and item 2's root cause is identified or explicitly documented as unable-to-determine.
      Source: `issues/tradfi_recovery_quarantine_registration_gap_2026_07_27.md`.

- [ ] [TRADFI] P3. **Implement the pyarrow per-symbol-writer fan-out fix the 2026-07-27 memray repro identified as the
      real OOM mechanism** — batch multiple low-volume symbols onto a shared `pq.ParquetWriter`, or cap/eagerly-flush
      concurrently-open per-symbol `StreamingParquetWriter`s in `PartitionedTickWriter._get_writer()`. Re-run the memray
      repro to confirm the fix addresses the identified mechanism. Repo: market-tick-data-service. **Done when**: the
      fix ships with a regression test, the memray repro no longer shows the same OOM growth pattern, and
      quality-gates.sh is green — at which point the backfill can revert to the cheaper e2-standard-4 machine type (a
      follow-up note, not this todo's own scope). Source: `issues/tradfi_backfill_oom_remediation_2026_06_24.md`.

- [ ] [SCRIPT] P2. **Audit the other tradfi/cefi/defi canonical-migration executors for the same PROGRESS.json
      checkpoint gap.** The P2 script-fix for one executor already shipped with commit+test evidence; audit the
      remaining `market-tick-data-service/scripts/migrate_*_2026_07*.py` executors for the identical gap. Repo:
      market-tick-data-service. **Done when**: every executor in that family is checked, and any found missing the
      checkpoint is either fixed inline (if trivial/same-pattern) or filed as a new tracked follow-up todo naming the
      specific executor — do not leave an audit finding as prose. Source:
      `issues/mtds_chain_bundle_migration_no_progress_checkpoint_2026_07_27.md`.

- [ ] [TEST] P2. **Update 3 failing test assertions + 2 docstring examples to the now-canonical raw short-root
      `underlying` form.** In `market-tick-data-service/tests/unit/test_databento_enrichment_combo_underlying.py`,
      change expected `underlying` values from the old human-name form ("WTI-BZ", "UST-10Y") to the now-canonical raw
      short-root form ("CL-BZ", "ZN") to match `unified-api-contracts@b9f4b6b9`'s deliberate behavior change. Repo:
      market-tick-data-service. **Done when**: all 3 assertions + both docstring examples are updated, and
      `quality-gates.sh` is green in market-tick-data-service. Source:
      `issues/mtds_combo_underlying_tests_stale_vs_uac_raw_root_2026_07_28.md`.

- [ ] [DATA] P2. **Re-verify the shipped commodity-API header fix on a real GCP VM against the actual commodity
      family.** `features-service@d06919bf` (2026-07-28) has never been re-tested live against
      `--family commodity --asset-group TRADFI`; the issue doc explicitly says it "stays open pending that live
      re-test." Repo: features-service. **Done when**: a real GCP VM run against the commodity family is recorded with
      pass/fail; if it fails, check the operator-gated egress-IP block-list against `central-element-323112` (a
      follow-up, not this todo's scope) rather than guessing further. Source:
      `issues/features_commodity_public_api_403_from_gcp_vm_2026_07_27.md`.

- [ ] [DATA] P3. **Spot-check the TRADFI:volatility test-bucket parquet/manifest for concurrent-write corruption.**
      Check the written TRADFI:volatility parquet/manifest for the 2026-01-29..2026-01-30 window (test bucket
      `features-tradfi-test-central-element-323112`) to confirm no partial-write corruption resulted from two VMs'
      concurrent writes to the same sink — the doc's determinism argument (concurrent writes should converge
      byte-identically) is currently an unverified assumption. Repo: features-service. **Done when**: the spot-check is
      recorded with a pass/fail verdict on the determinism assumption. Source:
      `/plans/archive/issues/features_pipeline_e2e_check_duplicate_vm_launch_same_shard_2026_07_27.md` (resolved
      2026-07-30).

- [ ] [DATA] P2. **Trace the corrupted `58317-01-15` timestamp to its raw source and classify one-off vs. systemic.**
      Trace back to the raw source object (NASDAQ:EQUITY:IBIT/ETHA, day=2026-05-07) to determine whether the overflow is
      a one-off vendor glitch or a systemic unit/encoding bug (e.g. epoch-microseconds misread as epoch-nanoseconds, or
      an unfiltered sentinel/NULL). The MDPS-side guard has already shipped regardless; this determines whether a
      capture-path fix is also needed. Repo: market-tick-data-service. **Done when**: the trace is recorded with a
      one-off/systemic verdict; if systemic, file the capture-path fix as a new tracked follow-up todo (not this todo's
      own scope). Source: `issues/mdps_tradfi_nasdaq_timestamp_overflow_candle_crash_2026_07_27.md`.

- [ ] [DATA] P2. **Instrument `_streaming_filter_slice` to root-cause why CME combo `ohlcv_15m`/`ohlcv_24h` aggregation
      produces `symbols_processed=0`.** Per the doc's own prescribed next step: log pre/post-filter row counts to
      distinguish between the two candidate mechanisms (a data_type column mismatch dropping all rows in the
      slice-filter, vs. no 1s/1m→15m aggregation writer yet existing for tradfi per the `TradfiOhlcv15mAdapter`
      docstring). Repo: market-data-processing-service. **Done when**: the instrumentation identifies which mechanism is
      responsible, and the fix (or a scoped follow-up todo if the fix is a larger build) is recorded. Source:
      `issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`.

- [x] ✅ [INFRA] P1. **Bundle CME roots into fewer larger VMs — extracted from
      `tradfi_backfill_throughput_followups_2026_07_24.md`'s own still-open item by
      `tradfi_satellite_ao_dispatch_batch4_2026_07_26_finalize.md`'s Deferred re-check (2026-07-30), now that the
      conflict-gate has cleared.** `_tradfi-ohlcv-launcher-lib.sh` still spawns one VM per (venue,root,year) for the CME
      root loop (confirmed live 2026-07-30: `launch-tradfi-bf-cme-ohlcv-1m.sh` uses the unchanged per-root-year shard
      model, per the lib's own "CME shards 47 roots x 7 years (~329 VMs)" comment) — accumulate multiple roots'
      symbol-sets into one VM's `VM_INSTRUMENT_IDS` per year-shard (a `SINGLE_VM_QUEUE`-analog), plus fold in the
      pd-balanced 250GB `TRADFI_OHLCV_BOOT_TYPE` disk default (staged locally 2026-07-18, never wired). **Gate-clear
      evidence**: this item was previously conflict-gated against `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s
      todo 3 sub-item (1), which changed the SAME shared file in a different direction (ticker-group fan-out →
      DATE-range slicing, for the EQUITY launchers). That batch2 change SHIPPED `deployment-service@872ac2f` and is
      confirmed live-scoped to `launch-tradfi-bf-{nasdaq,nyse}-ohlcv-1m.sh` only (`ohlcv_split_date_slices`,
      `OHLCV_SHARD_MODE=date-range`) — the CME launcher still calls the original per-root-year path
      (`ohlcv_split_ticker_groups`), confirmed by live grep of both launcher scripts, zero code overlap with the shipped
      change. Repo: deployment-service. **Done when**: `_tradfi-ohlcv-launcher-lib.sh` accumulates multiple CME roots
      per VM per year-shard (fewer, saturated VMs, not one-VM-per-root), the pd-balanced 250GB disk default is wired for
      the CME launcher, a dry-run of `launch-tradfi-bf-cme-ohlcv-1m.sh` shows the new bundled fan-out with no root/date
      lost or duplicated, and `tradfi_backfill_throughput_followups_2026_07_24.md`'s "[INFRA] P1. Bundle roots into
      fewer larger VMs" checkbox (line ~299) is flipped citing the shipped commit. Source:
      `tradfi_backfill_throughput_followups_2026_07_24.md`. **✅ SHIPPED `deployment-service@60b9d37`** (2026-07-30):
      added `ohlcv_split_root_groups` (the `SINGLE_VM_QUEUE`-analog) + `OHLCV_ROOT_GROUPS`/`--root-groups` knob
      (default 10) to `_tradfi-ohlcv-launcher-lib.sh`; rewired `launch-tradfi-bf-cme-ohlcv-1m.sh` to loop (root-group x
      year-shard) instead of (root x year) — default groups collapse 406 VMs (58 roots x 7 years) to 70. Dry-run
      verified: the union of all bundled groups' `VM_INSTRUMENT_IDS` exactly matches the 103-symbol/58-root source
      universe (diff clean, no loss or duplication); `--only-root` and `--root-groups 58` (legacy one-VM-per-root) both
      still work. The pd-balanced 250GB `TRADFI_OHLCV_BOOT_TYPE`/`BOOT_GB` disk default was already committed + wired
      into `ohlcv_create_vm` (`ac5d1660`, 2026-07-18), which the CME launcher already calls — confirmed no separate disk
      change was needed (the "never wired" framing above was stale).

## Deferred — conflict-gated (do NOT draft a competing todo; unchanged, still genuinely unresolved)

- **`tradfi_multisource_backfill_2026_06_22.md`'s FX-yahoo-drain item** — unchanged since batch3. Running
  `launch-tradfi-bf-fx-ohlcv-24h.sh` to completion still risks writing more mis-stamped rows while
  `issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`'s historical re-stamp remains unapplied (that doc
  is `archivable_after_planned_work` this pass — `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s fresh
  2026-07-29 Phase A2 todo now tracks the re-stamp — but the FIX HASN'T SHIPPED yet, only been drafted/tracked, so the
  sequencing risk is unchanged). This batch DOES draft its other 2 open items though (not conflict-gated): the
  code-complete `[TEST] P3` checkbox-flip-back and the `[SCRIPT] P1` image-freshness precondition check — **these were
  left OUT of the numbered list above because on reflection they're small enough to fold into whichever batch actually
  runs the FX backfill once the provenance fix ships; tracking them here avoids a todo that immediately re-defers
  itself**.
- **`/plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`'s todo 3 (the actual legacy-twin bucket
  DELETE)** — **⚠️ FALSE PREMISE, CORRECTED 2026-08-02 (operator-ruled correction pass).** What this bullet said when it
  was written on 2026-07-29 is quoted verbatim at the bottom of this entry; it is wrong on two counts and must not be
  read as current.

  **Correction 1 — twin coverage is 0%, not 100%.** The original text read the 2026-07-28 §3a extension as though it had
  already _established_ "Part-5 twin-coverage=100%". It did not: 100% content-verified canonical-twin coverage is a
  **precondition** §3a path (c) imposes before this delete class becomes reversibility-qualified, and the only fresh
  measurement of that precondition came back **0%**. Measured 2026-07-30 (dispatched from batch1's REVIEW todo) against
  the live prod report
  `gs://market-data-tick-tradfi-prd-central-element-323112/_index/audit/orphan_sweep_tradfi.parquet` via
  `instruments-service/scripts/cleanup_legacy_twins.py --asset-group tradfi` with `--apply` omitted (omitting `--apply`
  IS the dry-run on this CLI; the `--dry-run` flag named in the older todo text does not exist): **900 class-B legacy
  twins loaded → 0 deletable, 900 BLOCKED**, every single one with reason _"canonical twin NOT captured in manifest -
  would delete the only copy"_. Evidence: `/plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`'s own
  Progress Log, 2026-07-30 doc-triage entry (re-confirmed still the last measurement by the 2026-07-31
  na-eligibility-audit pass). So the delete gate does NOT clear — and it is gated on a **measured negative**, which is a
  stronger and more durable block than the "just waiting on numbers" framing the original bullet implied.

  **Correction 2 — batch1's dry-run HAS landed; the "bring it to the operator" recommendation is spent.** The original
  text said `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`'s "still-open todo 2 (dry-run + Progress-Log posting)
  hasn't landed yet". It landed 2026-07-30 — that batch1 REVIEW todo is precisely what executed the dry-run quoted above
  — and batch1 is now archived at `/plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`. The
  original "once batch1's dry-run lands, bring this to the operator for a go/no-go" recommendation is therefore
  **discharged, not pending**: the dry-run landed and the answer is no-go-by-measurement. **Do NOT re-raise it as a
  fresh operator ask** — there is nothing for the operator to rule on while coverage measures 0%; the blocking work is
  technical (establish real canonical-twin coverage, or explain why the manifest says there is none), not a decision.

  **Still deferred, still not drafted as a batch todo** — unchanged conclusion, corrected reasoning. Whoever picks this
  up next must re-measure coverage fresh (never reuse the numbers above as the §3a same-run check) and must not
  interpret this entry as clearance.

  <!-- prettier-ignore -->
  > _Original 2026-07-29 text, preserved verbatim for provenance (SUPERSEDED — do not act on it):_ "the doc's own
  > 2026-07-28 update reversibility-qualifies this (Part-5 twin-coverage=100% + a fresh
  > `gcs_bucket_soft_delete_retention_seconds` check ≥604800s, per delete-safety-protocol §3a path (c)), so it is no
  > longer purely operator-gated in principle. Not drafted here regardless: this is a real prod-bucket delete, and
  > `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`'s still-open todo 2 (dry-run + Progress-Log posting) hasn't
  > landed yet — drafting the delete before the dry-run's fresh numbers exist would be premature. **Recommend**: once
  > batch1's dry-run lands, bring this to the operator directly for a go/no-go on the delete itself (repeating the
  > hard-stop norm for prod-bucket deletes) rather than auto-drafting it into a future batch."

- **UNRESOLVED — the legacy-twin candidate set silently shrank 995 → 900 rows and nobody knows why (flagged 2026-08-02,
  explicitly NOT accepted).** The candidate population for the delete above is cited as **995** actionable class-B rows
  throughout `/plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` (its "Where the dry-run evidence
  already lives" section and its still-open delete todo both scope the delete to "the 995 tradfi legacy-B candidate
  rows"), sourced from the 2026-07-10 full orphan sweep
  (`A_canonical_manifested=2,594,017 · B_legacy_duplicate=995 · … · E_orphan_real=0` over 10,584,946 objects). The
  2026-07-30 dry-run loaded **900** rows from the same report URI — **95 rows fewer**, with no explanation. The
  executing session recorded the discrepancy honestly ("the report has evidently shrunk by 95 rows in the interim, not
  re-investigated here") and moved on; **no one has investigated it since, and no doc in the corpus explains it.** This
  matters beyond bookkeeping: the report is the delete's candidate list, so an unexplained mutation of that list is an
  unexplained mutation of a delete's blast radius. Candidate explanations, none verified: (a) the report was
  legitimately regenerated by a later sweep with a corrected taxonomy; (b) 95 twins were folded/migrated/deleted by
  another pass and the report picked that up; (c) the loader silently drops malformed/unparseable rows; (d) two
  different report generations are being conflated. **Do not treat 900 as the authoritative number, and do not treat the
  995 → 900 delta as benign, until it is explained.** Tracked for resolution in this batch's finalize plan
  (`/plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29_finalize.md`, todo 2) rather than left as prose.

## Deferred — too-large-or-risky (needs its own dedicated plan, not a batch todo; unchanged from batch1-4)

- **`tradfi_manifest_content_recovery_completion_2026_07_24.md`** — unchanged. Still a live, multi-phase migration doc
  needing its own triage pass, not a batch slot.
- **`data_completion_tradfi_2026_07_15.md`** — unchanged. Phase 0 layout audit, ~133K-cell NASDAQ/NYSE backfill, G1
  `--apply-write` denominator-seed execution (gate-b still frozen), and the catalogue-scheduler terraform wiring are all
  real but too large/interdependent for a batch todo.
- **`issues/tradfi_canonical_path_migration_design_2026_07_19.md`** — unchanged. Steps 5-6 are explicit `[GATE]`
  operator-go items over a 2.7M-object corpus (copy→verify→delete + a 1.47M-object purge); the whole sequencing (steps
  4-8) stays deferred as one unit rather than peeling off step 4 alone, since step 4's Databento backfill result
  directly feeds the gated steps.
- **`tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`** — unchanged, `orphaned_never_touched`. All 8 items
  gated on the MDPS mismatch blocker this batch's todo 2 (above) is re-testing. If that re-measure clears the blocker,
  this doc becomes a strong batch6 candidate — flag for the next audit pass, not drafted speculatively here.

## Deferred — operator-gated (a ruling, not a re-triage, unblocks these; unchanged, NOT re-asked)

`issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` (which `EXCHANGE_CODE_TO_NAME` registry is
authoritative — `tradfi_instrument_universe.py` 96 keys vs `tradfi_symbology.py` 61 keys, 17 value-mismatches);
`archive/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md`'s 4,655 stale barchart rows (keep-vs-purge) —
**RESOLVED 2026-07-30**, no real historical VIX data risk (verified 0 captured rows), quarantine-with-tracking per the
already-settled 2026-07-20 operator ruling, doc archived;
`issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`'s `[DESIGN] P2` on whether
aggregated 15m/24h TradFi bars are wanted; `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s BLOCKED-CREDENTIALS
ICE/CME-futures-options source ask and its operator-confirm-gated G1 retirement purge;
`canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`'s residual catalogue-script reapplication (the doc's
own text calls it "pending operator confirmation"); and the entirety of
`issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md` (a pure `assigned_vm: NA` human-decision queue by
design — its own 2 "record the decision inline" checkboxes cannot be batch-dispatched since nothing has been ruled on
items 1/3/6/8 yet).

## Process observations (not batch todos — for the operator/main-agent, not silently fixed here)

1. **`tradfi_satellite_ao_dispatch_batch4_2026_07_26.md` is 8/8 done and unlocked, but its gated finalize
   (`tradfi_satellite_ao_dispatch_batch4_2026_07_26_finalize.md`) is still `status: draft`, 0/3 done.** Per
   `gate_on_depends: true`, the finalize is dispatch-eligible now that batch4's last todo flipped — it just hasn't been
   activated. That finalize's own todo 2 ("re-check batch4's Deferred sections... extract as a new tracked todo in a
   follow-up batch5") is functionally superseded by this fresh full-corpus audit for the `mvp_mode` item specifically
   (this batch's todo 1) — whoever runs batch4-finalize later should cite this batch rather than re-deriving that
   finding.
2. **`tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` is still `status: draft` (1/15 done)** despite carrying
   the live 2026-07-29 Phase A2 todo that tracks the FX/ICE/KRX historical re-stamp referenced in this batch's Deferred
   section above. It is gated on `tradfi_manifest_content_recovery_completion_2026_07_24.md` (17/20 done) and
   `tradfi_backfill_throughput_followups_2026_07_24.md` (22/24 done) via `depends_on` — both close to done but not yet
   complete, so this is expected, not a gap.

## File-collision matrix (verified before finalizing — same-priority todos run concurrently by default)

| Todo | Primary file(s) touched                                                                                                                   |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `deployment-service/scripts/vm/setup-data-pipeline-vm.sh`, `launch-tradfi-forward-poll.sh`, mtds test files                               |
| 2    | `deployment-service/scripts/vm/launch-mdps-backfill-vm.sh` (execution only, no code edit)                                                 |
| 3    | `market_tick_data_service/scripts/_rebuild_tradfi_cf11.py`                                                                                |
| 4    | `issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md`'s underlying venue-specific manifest-writer adapters                   |
| 5    | `issues/tradfi_distinct_values_net_new_clusters_2026_07_28.md`'s chain-writer + `VENUES_BY_ASSET_GROUP` (UAC)                             |
| 6    | `yahoo_finance_adapter.py` (`write_canonical_shard`)                                                                                      |
| 7    | new register-phase script, `market-tick-data-service/scripts/`                                                                            |
| 8    | `market-tick-data-service` — `PartitionedTickWriter._get_writer()`                                                                        |
| 9    | `market-tick-data-service/scripts/migrate_*_2026_07*.py` (audit, read-only)                                                               |
| 10   | `market-tick-data-service/tests/unit/test_databento_enrichment_combo_underlying.py`                                                       |
| 11   | features-service (verification run only, no repo file written beyond the issue doc)                                                       |
| 12   | features-service (verification run only, no repo file written beyond the issue doc)                                                       |
| 13   | market-tick-data-service raw capture path (read-only trace, no file written beyond the issue doc)                                         |
| 14   | `market-data-processing-service` — `_streaming_filter_slice`                                                                              |
| 15   | `deployment-service/scripts/vm/_tradfi-ohlcv-launcher-lib.sh` (CME root-bundling path — distinct from the shipped date-slice equity path) |

No file appears twice, with ONE deliberate exception: todos 4, 5, and 6 (manifest_writer_legacy_id_regression item 3,
distinct_values_net_new_clusters item 2, and yahoo_venue_vendor_conflation) all touch the same FX/YAHOO_FINANCE
venue-stamping neighborhood and may resolve to the same underlying file once a worker actually opens it — each todo's
text above explicitly says to coordinate/cite rather than duplicate. **If the operator prefers zero risk, run todo 6
(yahoo_venue_vendor_conflation) first, then todos 4 and 5** — its investigation directly answers the YAHOO_FINANCE
question both other todos ask.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step is machine-gated via a companion
`tradfi_satellite_ao_dispatch_batch5_2026_07_29_finalize.md` (`depends_on` on this plan plus `gate_on_depends: true`),
mirroring the batch1/batch2/batch3/batch4 finalize pattern.

## Progress Log

- **2026-07-30 (operator-ruling closeout sweep, this session)** — This plan is still `status: draft`, never
  approved/dispatched, so none of its 15 todos are live AO work. Checked for any operator-ruling reference with
  unshipped follow-up (this session's broader sweep goal) — found exactly one: todo 1 (`mvp_mode`, ruled 2026-07-29).
  Verified live that it is now fully shipped: `deployment-service@c847395e` (2026-07-30) exists and its diff matches
  this todo's own (i)-(iv) plan exactly (`setup-data-pipeline-vm.sh` `VM_MVP_MODE` metadata plumbing,
  `launch-tradfi-forward-poll.sh` opt-in `--mvp-mode` flag, `launch-tradfi-bf-cme-ohlcv-1m.sh`/
  `launch-tradfi-backfill-vm.sh` confirmed untouched, 3 new regression tests in
  `deployment-service/tests/unit/test_vm_launcher_scripts.py`); the source issue doc
  `issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md` has all 4 of its own todos flipped `[x]` citing the same
  commit. The work landed via a DIFFERENT, already-active plan (`tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s
  bundled `[OPERATOR] P2` todo), not through this draft batch. Marked this batch's todo 1 done-by-cross-reference (not
  re-implemented) so that if/when the operator approves this draft for dispatch, no duplicate work gets queued. No other
  todo in this batch references an operator ruling; the remaining 14 are `/ag-closeout-audit` orphan-extraction items,
  out of scope for this session's ruling-closeout sweep. No code changed by this session for this file — doc-only
  update.

- **2026-07-30 (batch5 dispatch, slot 5, task `tradfi_satellite_ao_dispatch_batch5-002`)** — Worked todo 3 (CME+CBOE
  `WithinBoundsTradfiSourceZero` migration/purge + hardening). Found the code portion already shipped by slot 11
  (`market-tick-data-service@11be9cfe`, landed ~15 min before this dispatch) — verified the diff matches this todo's
  spec exactly. Ran the migration script's dry-run against the LIVE tradfi manifest and recorded the measured counts in
  the source issue doc's Progress Log (114,318 candidates, 81,454 droppable, 32,864 CME unresolved); re-verified the
  23-test regression suite green in a fresh `.venv`. Flipped todo 3 done — its done_definition doesn't require `--apply`
  to have run, only that the dry-run be recorded + reviewed before any apply. Filed a `/blocked` recommending the
  operator approve `--apply` given the clean measured numbers (self-verify=0, CAS+snapshot safety net, CBOE
  100%-confirmed match) — the actual write stays gated on that answer. Also fixed this doc's own stale "Status: draft —
  NOT approved, NOT dispatched" banner (line ~80), which contradicted the frontmatter's `status: active` since the
  2026-07-30 `5a6bbefc3` operator approval commit — the banner text was never updated in that same commit.

- **2026-07-31 (slot-2, data_engineering craft, task `tradfi_satellite_ao_dispatch_batch5-001`)** — Picked up todo 2
  (ES/MES per-contract backfill re-run + hit-rate re-measure). Before launching a new backfill (this todo's literal
  instruction), checked `gcloud compute instances list` for any already-running ES/MES fleet to avoid a duplicate SPOT
  launch — found 14 `mdps-backfill-tradfi-y{2020..2026}es[3]-20260731-023743` VMs already `RUNNING`, launched ~30 min
  earlier. Traced their provenance: they are the fleet-wide relaunch from a DIFFERENT, unrelated incident —
  `issues/tradfi_mdps_es_mes_backfill_fleet_consolidator_staleness_failures_2026_07_31.md` (a tradfi manifest
  consolidator staleness-budget false-positive + a chain-bundle instrument-id matcher gap, both now fixed —
  `unified-trading-library@75b5735`, `market-data-processing-service@43b043b` — and confirmed baked into this fleet's
  tarball). That fleet's own scope is functionally identical to this todo's "launch" instruction: full ES/MES
  per-contract process-step backfill, `CME:FUTURE:ES CME:FUTURE:MES`, spanning the same 2020-2026 window. Relaunching a
  SECOND fleet here would duplicate SPOT compute/GCS write load for zero benefit — declining to do so. **Verified
  genuine live progress** (not just VM liveness) via `run.log` tail on all 7 `es` year-shards: each is processing around
  day 78-82 of its ~365-day year (e.g. `y2020es` at `date=2020-03-19`, `y2026es` at `date=2026-03-04`) after ~30 min
  runtime — real `POLARS AGGREGATED` candle-write lines confirm genuine compute, not a hung/idle VM. At this rate
  (~21-22% in ~30 min), the process-step alone has an ETA of roughly 1.5-2 more hours before all 14 shards complete —
  well before `build-continuous --root ES` (this todo's second step) or the hit-rate re-measure (the third) can even
  begin. This is a multi-hour gate, not something to hold this slot open for — declining todo 2 and skipping this task
  rather than busy-waiting, per the same posture the CeFi Track-2 backfill precedent established
  (`issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`). Next dispatch should check
  `DeploymentsRegistry`/`gcloud compute instances list` for the `mdps-backfill-tradfi-y*es*-20260731-023743` fleet's
  completion before re-running `build-continuous` and the hit-rate measurement — no new backfill launch needed unless
  this fleet is found to have failed.

- **2026-07-31 (slot-16, data_engineering craft, task `tradfi_satellite_ao_dispatch_batch5-001`)** — Resumed todo 2
  again (`already_in_progress: true`). Found + fixed a real gap in the same fleet slot-2/9/12 have been tracking: a
  preemption wave at ~03:14-03:20 UTC took out several shards; most years kept a surviving `es`/`es3` sibling, but 2024
  lost BOTH and had no `PROGRESS.json` to resume from precisely. Relaunched 2024 non-force over the full year
  (`mdps-backfill-tradfi-y2024es-resume-20260731`, confirmed `RUNNING`) so the launcher's own skip-if-fresh check picks
  up wherever the two preempted attempts left off. Full detail + a caught-and-fixed self-inflicted mistake (the
  launcher's `dry` argument still creates a real billable VM, not a local no-op — deleted the errant VM immediately) in
  the source issue doc's Progress Log. Fleet is 10 VMs now (9 survivors + the 2024 resume), all years covered. Still
  hours from `build-continuous` + the hit-rate re-measure — skipping rather than busy-waiting, same posture as slot-2's
  entry above.

- **2026-07-31 (slot-9, data_engineering craft, task `tradfi_satellite_ao_dispatch_batch5-001`)** — Resumed todo 2 a
  third time. **Source doc is now STALE**:
  `issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md` was archived 2026-07-30 (status:
  resolved, 0 open todos) — this todo's own "flip the doc's open item" instruction no longer applies to that doc; the
  live continuation of this exact thread is
  `issues/tradfi_mdps_es_mes_backfill_fleet_consolidator_staleness_failures_2026_07_31.md` (filed today, still open,
  P2/P3 items unresolved there). That doc revealed the `023743` fleet (launched 02:37:43Z, the one slot-2/16 were
  tracking) has had THREE separate root-cause fixes land during/after its own launch: `unified-trading-library@75b5735`
  (consolidator staleness-budget, 00:34:02Z — predates 023743, included), `market-data-processing-service@43b043b`
  (chain-bundle instrument-id matcher, 02:10:11Z — predates 023743, included), `unified-api-contracts@4eeb495f` (missing
  `ohlcv_1s` SchemaContract for tradfi COMBO/FUTURE, 03:30:26Z — **postdates** 023743's launch, NOT included).
  Re-audited the full `023743` fleet directly (GCS `EXIT_STATUS` + `run.log` per shard, not just VM liveness):
  2020/2021/2023/2025/2026 have a completed `es` (or `es`+`es3`) shard each (`EXIT_STATUS=1`, but only because the
  missing-schema gap fails 6/36 sub-dimensions per date — a narrow, already-tracked, non-blocking `ohlcv_1s` gap, not a
  hit-rate-relevant one). **2022 and 2024 had ZERO completed shards** — both `es`+`es3` were preempted early (~day
  101/365 for 2022, before any `EXIT_STATUS` or `PROGRESS.json`), and slot-16's own 2024-resume attempt
  (`y2024es-resume-20260731`) was ALSO preempted (cut off at day ~59/365, no exit marker) — so 2024 has never had a
  shard survive to completion across 3 attempts. Relaunched both fresh: `mdps-backfill-tradfi-20260731-092148` (2022,
  full year) and `mdps-backfill-tradfi-20260731-092224` (2024, full year), both non-force/SPOT via
  `launch-mdps-backfill-vm.sh`. Verified all 3 fixes above are ancestors of the CURRENT floating tarballs before
  launching (`git merge-base --is-ancestor <fix-sha> <manifest-pinned-sha>` — all 3 YES: mdps manifest `4b84d5c1`, uac
  manifest `9ce47376`, utl manifest `5a4592f3`), so these two relaunches carry every known fix, unlike the `023743`
  wave. Verified genuine progress past the no-fire-and-forget bar (not just VM liveness): both VMs' `run.log` show real
  per-date subprocess iteration with passing dependency checks and real candle output within ~4-5 min of launch (2022 at
  day 4/365, 2024 at day 3/366). Still hours from full-year completion on both — `build-continuous`
  - the hit-rate re-measure remain gated on this. Declining/skipping rather than busy-waiting, same posture as slot-2
    and slot-16 above. **Next dispatch**: check `mdps-backfill-tradfi-20260731-092148`/`-092224` for completion
    (`EXIT_STATUS` in their `vm-logs/` dirs) before running `build-continuous --root ES` + the 1d/24h hit-rate
    re-measure; if either was preempted again, relaunch non-force (skip-if-fresh resumes cleanly) rather than replaying
    day one.

- **2026-07-31 (slot-12, data_engineering craft, task `tradfi_satellite_ao_dispatch_batch5-001`)** — Resumed todo 2 a
  fourth time. `gcloud compute instances list` showed only `mdps-backfill-tradfi-20260731-092148` (2022, slot-9's
  relaunch) still alive; `-092224` (2024) was gone. Confirmed via `gcloud compute operations list` it was preempted at
  02:28:33Z, ~6 min after its 02:21:58Z launch — no auto-relaunch or newer 2024 attempt existed in `vm-logs/` or the
  live instance list. Recovered its exact scope from `LAUNCH_PARAMS.json` (`RESUME_START_DATE=2024-01-01`,
  `RESUME_END_DATE=2024-12-31`, `full`, `FORCE=false`, `MDPS_INSTRUMENT_IDS='CME:FUTURE:ES CME:FUTURE:MES'`, no
  `PROGRESS.json` existed — it died on day 3, so nothing to lose by a fresh non-force relaunch). First relaunch attempt
  (`mdps-backfill-tradfi-y2024-resume2-20260731`) surfaced a NEW staleness warning: the floating
  `market-data-processing-service` tarball was pinned `4b84d5c11ede` but repo HEAD was `c53c8c1f90fa` — `git log` on
  that range showed `c78285b fix(manifest): omit empty instrument_id from row_key for aggregate bundle writes`, which is
  exactly the already-tracked-but-unfixed `MalformedRowKeyError` gap (Gap 2 in
  `mdps_tradfi_chain_bundle_aggregate_write_malformed_row_key_2026_07_31.md` — independently reconfirmed still firing on
  the live `092148` (2022) VM this session: 1,560 occurrences across 33/48 processed days, all `instrument_type=COMBO`
  `data_type=ohlcv_1s` for the `SP500`/`MICRO-SP500` underlyings — no new issue doc needed, already correctly triaged
  there as non-blocking to the per-instrument candle output this fleet exists to produce). Since the just-launched VM
  had produced zero log output yet (checked `run.log` — not found, i.e. still in startup), deleted it before any work
  was lost, republished the tarball
  (`bash deployment-service/scripts/vm/create-code-tarballs.sh --include market-data-processing-service --include deployment-service`,
  now pins `c53c8c1f90fa`, confirmed `git merge-base --is-ancestor c78285b c53c8c1f90fa` = true), then relaunched
  cleanly as `mdps-backfill-tradfi-y2024-resume3-20260731` — launcher reported **all 5 tarballs fresh**, no warnings.
  Verified genuine progress past the no-fire-and-forget bar: `run.log` for 2024-01-03 shows
  `26 success / 0 failed / 0 skipped`, 30,239 candles, "All (data_type x instrument_type) combinations passed" — clean,
  no row-key errors visible in this excerpt. 2022 (`092148`) independently confirmed still alive and progressing
  normally (day 2022-03-10, ~19% through its year) on its original (pre-`c78285b`) pin — left running as-is rather than
  restarting an already ~30-min-invested VM just to pick up a fix for an already-non-blocking gap; not required for this
  todo's actual goal (the ES/MES per-contract `continuous_future` hit rate, a different data_type/instrument_type axis
  than the COMBO ohlcv_1s writes the gap affects). Both VMs confirmed `RUNNING` via a final fresh
  `gcloud compute instances list`. Still genuinely hours from full-year completion on both (2022 ETA ~1.5-2h remaining;
  2024 is a fresh full-year start, ~2.5h). Declining/ skipping rather than busy-waiting, same posture as every prior
  slot on this todo. **Next dispatch**: check `mdps-backfill-tradfi-20260731-092148` (2022) and
  `mdps-backfill-tradfi-y2024-resume3-20260731` (2024) for completion (`EXIT_STATUS` in their `vm-logs/` dirs, not just
  liveness) before running `build-continuous --root ES` + the 1d/24h hit-rate re-measure against the ~19% (454/2398)
  baseline; if either was preempted again, relaunch non-force (skip-if-fresh resumes cleanly) rather than replaying day
  one, and re-verify tarball freshness for `market-data-processing-service`/`deployment-service` before launching (both
  were stale this round despite being fresh on the prior 023743/092148/092224 wave — freshness drifts as LDR keeps
  moving, so it must be re-checked per relaunch, not assumed from a prior session's confirmation).

- **2026-07-31 (slot-6, backend_engineer craft, task `tradfi_satellite_ao_dispatch_batch5-001`)** — Resumed todo 2 a
  fifth time. Did a full fleet audit of all 14 canonical ES/MES shards (2020-2026 × es/es3) via
  `EXIT_STATUS`/`PROGRESS.json` in `vm-logs/` rather than trusting liveness: **10 of 14 had already reached a terminal
  EXIT_STATUS** (some `=1` from already-known non-blocking weekend/schema gaps, not real failures) and 2024 was fully
  complete via slot-12's `y2024-resume3` (`last_completed_date=2024-12-30`). **4 shards were genuinely incomplete and
  had no VM running anywhere** (2021es3, 2022es, 2022es3, 2025es3) — all preempted/lost early with no PROGRESS.json
  checkpoint, no relaunch attempted since. Relaunched all 4 non-force (`*-resume-20260731` names, exact original scope
  from each dead VM's `LAUNCH_PARAMS.json`). **Caught and self-corrected a mistake**: the first relaunch (`y2021es3`)
  went out on 5 STALE tarballs (the launcher only warns, does not block, unless `LC_TARBALL_FRESHNESS=enforce`) —
  deleted it before any work was lost, verified all known fixes (`43b043b`, `c78285b`, `75b5735`, `4eeb495f`) are
  ancestors of the fresh-pulled repos, republished all 5 tarballs, then relaunched all 4 shards cleanly
  (`lc_verify_tarball_freshness: all 5 tarball(s) current` on every launch). Verified genuine progress past the
  no-fire-and-forget bar via `run.log` on all 4. **Hit a NEW blocker while investigating a manifest-consolidator
  staleness error on all 4**: initially found the tradfi consolidator's per-minute cron showing zero invocation logs
  13:45-18:23Z and (using the wrong audit-log filter) no pause/resume events, drafted a "self-recovered, unexplained"
  issue doc — then a `git pull` mid-session surfaced the REAL, already-filed explanation:
  `/plans/archive/issues/dp_consolidator_scheduler_paused_tradfi_recurrence_2026_07_31.md` (slot-2/12, resolved). The
  cron was DELIBERATELY paused by the unrelated `mtds_available_at_cross_asset_backfill_2026_07_13.md` plan's own
  pause/apply/resume backfill protocol (paused 13:45:52Z); a dp-fleet-monitor escalation briefly (and mistakenly)
  resumed it, caught the mistake within ~3min (confirmed zero consolidator ticks fired), then re-paused it and
  registered a proper maintenance window. **Confirmed independently via GCS** (no scheduler IAM needed):
  `gs://market-data-tick-tradfi-prd-central-element-323112/_index/_maintenance_window.json` reads
  `{"locked_by": "mtds_available_at_cross_asset_backfill_2026_07_13", "expires_at": "2026-08-03T18:26:16+00:00", ...}` —
  the tradfi market-data consolidator is intentionally held OFF until that sibling plan's apply+resume todos complete
  (2026-08-03 at the latest). Withdrew my own draft issue doc (left untracked, never committed — redundant
  - partly wrong on the "no pause event" claim) rather than duplicate the corpus. **This is now the real gate on todo
    2**: my 4 relaunched shards (and any other tradfi MDPS consolidator-dependent read) will keep hitting
    `ManifestConsolidatorStaleError`/bounded-wait until that maintenance window lifts — not something to force through
    (resuming it myself would race the other plan's protocol, exactly the mistake the escalation worker caught itself
    making). Declining/skipping rather than busy-waiting or fighting another plan's legitimate hold, same posture as
    every prior slot on this todo, but with a new explicit dependency now on record. **Next dispatch**: before resuming
    todo 2, check `gs://market-data-tick-tradfi-prd-central-element-323112/_index/_maintenance_window.json` — if it's
    gone/expired (past 2026-08-03T18:26:16Z or `mtds_available_at_cross_asset_backfill_2026_07_13` shows its
    apply+resume todos done), THEN check the 4 `*-resume-20260731` VMs for `EXIT_STATUS` completion (they may need a
    fresh non-force relaunch if the multi-day consolidator gate stalled them past their SPOT lifetime), re-verify
    2020/2021es/2023/2025es/2026 (already `EXIT_STATUS=1` from known non-blocking gaps) don't need a redo, then run
    `build-continuous --root ES` and the 1d/24h hit-rate re-measure against the ~19% (454/2398) baseline in
    `issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md`.

- **2026-07-31 (slot-8, data_engineering craft, task `tradfi_satellite_ao_dispatch_batch5-001`)** — Resumed todo 2 a
  sixth time. Reconfirmed slot-6's gate still holds, nothing new: `_maintenance_window.json`
  (`gs://market-data-tick-tradfi-prd-central-element-323112/_index/`) unchanged
  (`locked_by: mtds_available_at_cross_asset_backfill_2026_07_13`, `expires_at: 2026-08-03T18:26:16Z`, current time
  `2026-07-31T22:03Z` — ~2 days remaining), and that sibling plan's gating apply+resume P1 todos are still open (both
  prediction and tradfi rows, lines ~164/169/288/297). Declining/skipping again rather than force through the
  maintenance window or re-run the same fleet-completion checks slot-6 already did minutes-to-hours ago. **Next
  dispatch**: same check as slot-6's note above — re-check the maintenance window / sibling plan's apply+resume todos
  first; only proceed to the VM `EXIT_STATUS` checks once that gate has actually lifted.

- **2026-07-31 (slot-15, data_engineering craft, task `tradfi_satellite_ao_dispatch_batch5-001`)** — Resumed todo 2 a
  seventh time. Gate unchanged: `_maintenance_window.json` still reads identically
  (`locked_by: mtds_available_at_cross_asset_backfill_2026_07_13`, `expires_at: 2026-08-03T18:26:16.060331+00:00`) and
  this session's own earlier work on the sibling plan's
  `dp_consolidator_scheduler_paused_tradfi_recurrence_2026_07_31.md` (now archived, `unified-trading-pm@5696ef3bc`)
  confirms its tradfi apply+resume P1 todos (lines 288/297) are still `- [ ]` open — no operator/worker action has
  landed on that apply step yet. **New since slot-8's check**: `gcloud compute instances list` shows ZERO
  `mdps-backfill-tradfi-*`/`*es*-resume*` VMs running anywhere — the entire 14-shard fleet (including slot-6's 4
  relaunches) has wound down (self-deleted SPOT, completed or preempted) since slot-8's 22:03Z check. Did not do a full
  per-shard `EXIT_STATUS` re-audit (slot-6 already ran the exhaustive version a few hours ago and nothing about the gate
  itself has changed — that audit is only useful the moment `build-continuous` can actually run). Declining/skipping
  again — same posture as every prior dispatch. **Next dispatch**: once the maintenance window is gone/expired or the
  sibling plan's tradfi apply+resume todos flip done, the fleet is now fully idle (nothing to wait on VM-side) — go
  straight to a full `EXIT_STATUS`/`PROGRESS.json` re-audit of all 14 shards (2020-2026 × es/es3, including the 4 that
  were mid-flight as of slot-6's relaunch) before running `build-continuous --root ES` + the 1d/24h hit-rate re-measure
  against the ~19% (454/2398) baseline.

- **2026-08-01 (slot-4, data_engineering craft, task `tradfi_satellite_ao_dispatch_batch5-001`)** — Resumed todo 2 for
  the 9th time (8 prior declines per `GET /api/activity?type=slot_task_skipped`; only 7 are chronicled above — slot-3's
  2026-07-31T08:49:05Z decline used an empty reason and never wrote a Progress Log entry). **Gate reconfirmed
  unchanged**: `_maintenance_window.json` still reads `locked_by: mtds_available_at_cross_asset_backfill_2026_07_13`,
  `expires_at: 2026-08-03T18:26:16.060331Z` (current time `2026-08-01T01:48:56Z`); that sibling plan's tradfi
  apply+resume P1 todos (lines 289/298) are still `- [ ]` open; `gcloud compute instances list` confirms zero
  `mdps-backfill-tradfi-*` VMs anywhere (fleet fully wound down, matching slot-15's finding — nothing new to audit
  VM-side until the gate clears). **Root-caused why 8 declines never durably parked this task**, from the actual call
  history rather than guessing: 6 of 8 (slot-2/3/9/12/6/8) used `reason_code: "OTHER"`, which
  `agent-orchestrator/server/auto_park.py`'s `_ESCALATING_REASON_CODES={BLOCKED,PARKED,GATED}` deliberately excludes
  from the fleet-cooldown/auto-park counter; only slot-16 (07-31T03:50:27Z) and slot-15 (07-31T22:31:41Z) used an
  escalating code (`BLOCKED`), landing `skip_count=2` — one short of the `dispatch_cooldown_auto_park_skip_threshold`
  (3). This exact gap-class (a decline defaulting to `OTHER` so `auto_park` never engages) is already fleet-tracked on
  two OTHER tasks with a confirmed fix and zero code gaps —
  `issues/p1_2_backlog_hand_park_did_not_persist_2026_07_31.md`,
  `issues/external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md` (2026-08-01 update citing the
  now-complete `gated_skip_park_no_slack_page_2026_07_25.md` reason_code-coverage audit) — so no new issue doc needed;
  the fix is simply to decline with the right code. **Action taken + CONFIRMED**: declined via
  `POST /api/slots/4/skip-current-task {"reason_code": "GATED"}`. slot-16's window
  (`window_started_at 2026-07-31T03:50:27Z`) was still open (<24h), so this was the 3rd escalating-coded decline
  in-window and crossed the threshold on this call — response confirmed
  `"auto_parked_condition": "auto_unpark__tradfi_satellite_ao_dispatch_batch5-001"`, and `GET /api/backlog/parked`
  independently confirms the task now carries that condition with `skip_count: 3`. **The task is now durably parked** —
  it will not re-dispatch to any slot until that condition is cleared (Slack-paged per `notify_task_auto_parked`; this
  finally stops the 9-cycle churn). **To resume this todo**: once `mtds_available_at_cross_asset_backfill_2026_07_13.md`
  lines 289/298 flip done (or the maintenance window naturally expires 2026-08-03T18:26:16Z),
  `POST /api/prerequisites/auto_unpark__tradfi_satellite_ao_dispatch_batch5-001 {"value": true}` to release the park,
  THEN run the full `EXIT_STATUS`/`PROGRESS.json` re-audit of all 14 ES/MES shards, `build-continuous --root ES`, and
  the 1d/24h hit-rate re-measure against the ~19% (454/2398) baseline — no VM-side work is needed before that (fleet is
  fully idle).
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).

- **2026-08-02 (operator-ruled correction pass, doc-content only — no bucket data touched, no GCS/manifest call made)**
  — Corrected a FALSE delete-safety premise in this plan's Deferred — conflict-gated section. The
  legacy-twin-bucket-delete bullet asserted "Part-5 twin-coverage=100%" as established fact; it is a §3a path (c)
  **precondition**, and the only fresh measurement of it (2026-07-30 dry-run, dispatched from batch1's REVIEW todo,
  against `_index/audit/orphan_sweep_tradfi.parquet` in the tradfi prod tick bucket) returned **0%** — 900 class-B twins
  loaded, **0 deletable, 900 BLOCKED**, every one "canonical twin NOT captured in manifest - would delete the only
  copy". Also corrected the same bullet's second stale claim (batch1's dry-run "hasn't landed yet" — it landed
  2026-07-30 and batch1 is archived), and marked its "bring this to the operator for a go/no-go" recommendation
  **discharged**, so nobody re-raises a spent operator ask against a gate that is technical, not a decision. Original
  bullet text preserved verbatim inline for provenance. Separately flagged, as a NEW explicitly-unresolved Deferred item
  rather than silently accepting it: the candidate set **shrank 995 → 900 rows** between the 2026-07-10 orphan sweep and
  the 2026-07-30 dry-run with **no explanation recorded anywhere in the corpus** — the 2026-07-30 executing session
  logged the delta honestly and did not investigate, and no doc has since. Since that report IS the delete's candidate
  list, an unexplained mutation of it is an unexplained mutation of a delete's blast radius; wired into
  `/plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29_finalize.md`'s todo 2 as tracked work (explain-with-
  evidence, or file its own issue doc — never close as accepted). Verified before editing that no other session had
  already made this correction (`rg '0%|900'` over this file: 0 hits pre-edit). Both this plan and its finalize twin
  were ALREADY `status: active` (this plan `5a6bbefc3` 2026-07-30; the finalize `233ebd614` same day, the corpus-wide
  removal of the redundant finalize double-gate) — the ruled flip needed no frontmatter change; what it DID need was the
  finalize's body banner and frontmatter `summary`, both still asserting "stays draft", brought into line, since
  `233ebd614` was a frontmatter-only bulk flip.

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from its source doc, or
records a measurement/investigation. The delete-safety reasoning that gates the deferred legacy-twin-bucket item comes
from `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`; the SPOT-VM re-run in todo 2 follows
`/codex/05-infrastructure/spot-vms-for-backfill.md`.

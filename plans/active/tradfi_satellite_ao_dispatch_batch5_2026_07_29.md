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
last_updated: "2026-07-30"
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
---

# TradFi satellite AO batch 5 — fresh audit extraction

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
      `issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md`.

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

- [ ] [DATA] P1. **Root-cause + fix 3 populations of NULL/bare `instrument_id` manifest writes, plus one doc-hygiene fix
      — combined into ONE todo because all 4 edit the same issue doc.** (1) Root-cause + fix the live-path
      NULL-`instrument_id` write for tradfi equity/ETF (NASDAQ/NYSE, `ohlcv_1m`+`trades`, 3,612 rows, confirmed NOT the
      already-drained backfill fleet). (2) Investigate the CBOE `ohlcv_15m` INDEX/OPTION NULL-`instrument_id` writes
      (103 rows, all written 2026-07-27). (3) Root-cause why FX `SPOT_PAIR` manifest-row `instrument_id` is still bare
      (no colon) for post-2026-07-25 `FX`-venue captures and NULL for `YAHOO_FINANCE`-venue captures — **coordinate with
      todo 8 below (`tradfi_yahoo_venue_vendor_conflation_2026_07_27.md`'s Phase-0 investigation) and todo 7's
      YAHOO_FINANCE venue-registration question before starting; if the same file is the target, do this investigation
      once and cite it from all three docs rather than duplicating**. (4) Update this doc's own stale "static,
      2,023-row" `future`/`FUTURE` characterization to the current measured 9,126-row (and still growing) count. Repo:
      market-tick-data-service. **Done when**: items 1-2 have a shipped fix + regression test with `quality-gates.sh`
      green, item 3's root cause is recorded (fixed if the same-session coordination with todos 7/8 lands a fix,
      otherwise handed to a fresh follow-up with the coordinated finding cited), and item 4's checkbox is updated with
      the current count. Source: `issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md`.

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
- **`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`'s todo 3 (the actual legacy-twin bucket DELETE)** — the
  doc's own 2026-07-28 update reversibility-qualifies this (Part-5 twin-coverage=100% + a fresh
  `gcs_bucket_soft_delete_retention_seconds` check ≥604800s, per delete-safety-protocol §3a path (c)), so it is no
  longer purely operator-gated in principle. Not drafted here regardless: this is a real prod-bucket delete, and
  `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`'s still-open todo 2 (dry-run + Progress-Log posting) hasn't landed
  yet — drafting the delete before the dry-run's fresh numbers exist would be premature. **Recommend**: once batch1's
  dry-run lands, bring this to the operator directly for a go/no-go on the delete itself (repeating the hard-stop norm
  for prod-bucket deletes) rather than auto-drafting it into a future batch.

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

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from its source doc, or
records a measurement/investigation. The delete-safety reasoning that gates the deferred legacy-twin-bucket item comes
from `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`; the SPOT-VM re-run in todo 2 follows
`/codex/05-infrastructure/spot-vms-for-backfill.md`.

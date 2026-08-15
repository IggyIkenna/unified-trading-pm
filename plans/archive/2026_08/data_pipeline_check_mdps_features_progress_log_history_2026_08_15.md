---
doc_type: record
title: "Extracted Progress Log history — data_pipeline_check_mdps_features (2026-08-15 line-cap remediation)"
summary: >-
  Verbatim extraction of 3 fully-closed 2026-07-27 dated Progress Log entries (the ALL-shards features-check run in flight->done, the day=2026-07-19 CEFI-inclusive sweep, and the full 16-shard matrix completion writeup) from the MDPS/features pipeline-check plan. Every open todo referenced by these entries stays tracked in the live plan's own Todos section; nothing is lost, only moved. Extracted to keep the live plan under the 1000-line hard cap.
status: complete
nature: record
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [line-cap-remediation, historical, progress-log]
created: "2026-08-15"
author: slot-3
parent_epic: agent_operating_framework_master
source:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/archive/2026_08/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md,
  ]
---

# Extracted Progress Log history — data_pipeline_check_mdps_features (2026-08-15 line-cap remediation)

> **Extracted verbatim 2026-08-15** (`context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md` Follow-up
> todo — 3-doc 2026-08-07 batch) from `/plans/active/data_pipeline_check_mdps_features_2026_07_20.md`. Every extracted entry carried zero open Progress-Log-embedded
> todos; nothing summarized or lost, only moved to keep the live plan under the 1000-line hard cap.

### 2026-07-27 (slot-7) — todo "Run /data-pipeline-check-features across ALL shards" IN FLIGHT, not blocked

Phase 0 passed. Local driver dies silently/often (`WorkerLivenessWatchdog`/RAM contention, slot-3 independently
diagnosed same class — `issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` todo 9). On
death, check `gcloud compute instances list --filter="name~'features-e2e-<ag>'"` first (VM usually outlives the
poller) + its `run.log`. **Resume**:
`cd features-service && .venv/bin/python scripts/pipeline_e2e_check.py --day 2026-07-05 --legs force,skip --require-captured --auto-day --asset-group <AG> --family <FAM> --project central-element-323112`;
`delta_one` first per-AG; CEFI is slot-3's; driver OVERWRITES its report per-invocation — merge with
`unified-trading-pm@e537bff29` `scripts/plan-hygiene/merge_pipeline_e2e_report.py` after every cell.

**12/16 driver-matrix cells attempted — ALL non-CEFI cells now exhausted** (0 in flight; remaining 4 are
`delta_one`/`volatility`/`cross_instrument`/`multi_timeframe` on CEFI, slot-3's). 7 honest
`no_captured_input_for_window` skips (`DEFI:delta_one`, `PREDICTION:delta_one`, `DEFI:onchain`,
`multi_timeframe:{DEFI,TRADFI}`, `cross_instrument:PREDICTION` — all cascade cleanly from their own family's missing
input, expected — `volatility:TRADFI`). `TRADFI:delta_one` FAILED (2 identical VM runs,
`DEPENDENCY CHECK FAILED — Missing market-data-processing-service`; driver's `--require-captured` wrongly accepted the
window, P1 todo below); `cross_instrument:TRADFI` (both legs) FAILED HARD as the same cascade — but **note the
asymmetry**: `multi_timeframe:TRADFI` and `cross_instrument:PREDICTION` both degraded gracefully to a clean skip on
their own missing-input condition, `cross_instrument:TRADFI` alone raised an uncaught `FileNotFoundError` — worth a
follow-up but not filed (downstream of the same already-tracked P1). `commodity:TRADFI` FAILED cleanly — 3
public/no-auth sources 403/timeout/404'd, NOT `BLOCKED-CREDENTIALS` —
`issues/features_commodity_public_api_403_from_gcp_vm_2026_07_27.md` (P2). **TWO P0 DATA-CORRECTNESS BUGS, same
root-cause class**: `calendar` (0 rows) and `sports` (51 REAL fixtures — worse) both wrote to PROD despite
`IS_TEST_RUN=true` — each family's `is_test_run` field is declared but never consulted at its actual bucket-resolution
call site (delta_one's `get_output_bucket()`/`get_data_sink()` is correct; calendar's fix shipped
`features-service@ba5143fd`, sports' is open). Filed
`issues/features_{calendar,sports}_is_test_run_ignored_writes_*_2026_07_27.md` (both P0, operator-notified). **Do NOT
re-run `calendar` or `sports` until fixed**; `onchain`'s AG may share this bug (untested). Report:
`plans/audit/results/data_pipeline_e2e_check_features_2026_07_05.{md,json}` (total=24 failed=6 skipped=13). **Next
session**: either pick up the 4 CEFI cells (coordinate with slot-3 first) or re-run `calendar`/`sports` once their P0
fixes land. Plan AT its 1000-line hard cap — archive older closed sections before adding more.

- [x] ✅ NEW todo. [DATA] P0. **Coverage-check discrepancy — FOLDED 2026-07-27 (slot-7); FIXED 2026-07-27 (slot-4)**:
      same root cause independently hit 3x (this occurrence + slot-3's day=2026-07-19 occurrence + the fuller writeup) —
      tracked and fixed in `issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md` todo 1,
      not here: `features-service@1b272676` (+ test reconciliation `4fbf4dc7`). Root cause was a coverage-check
      granularity gap (NOT phantom-capture) — `--require-captured`/`--auto-day` accepted an `EMPTY_CONFIRMED` TARGET day
      (a TradFi weekend/holiday MDPS positively confirmed has zero output) as "covered", guaranteeing the runtime
      dependency checker's real GCS listing would then fail. Fixed by requiring the target day specifically to have a
      real `CAPTURED` row while still tolerating `EMPTY_CONFIRMED` window-interior days. **This todo attracted 3
      simultaneous independent dispatches** (this fix + slot-14's `696768c7` object-existence-probe variant + slot-2's
      `ecd548b8` runtime-dependency-checker fix) — reconciled by rebase-merging slot-14's probe scoped to
      `captured_days` only (not the broader `canonical_days`, which would have blanket-excluded every TradFi
      weekend/holiday from window-interior tolerance too — a worse regression); slot-2's fix is a complementary
      different-layer change (runtime checker vs this driver's pre-flight skip), no conflict. Full reconciliation
      writeup in the issue doc. 18 tests pass across the 3 related test files, QG green. The issue doc's own todo 2
      (re-run for a genuine force+skip proof) stays open — no `capture_status=captured` TRADFI/MDPS candle row exists
      yet in the 06-01..07-27 window, so that proof is gated on a real TRADFI candle backfill, not on this fix.

### 2026-07-27 (slot-3) — todo 9b: day=2026-07-19 CEFI-inclusive 8-family sweep complete; NOT claiming 9b closed

Ran `/data-pipeline-check-features` for day=2026-07-19 across all 8 families (30 force+skip rows: 3 passed/13 failed/14
skipped) — `plans/audit/results/data_pipeline_e2e_check_features_2026_07_19.{md,json}`. Covers the 4 CEFI cells slot-7's
entry above asked "next session" to pick up (delta_one/volatility/multi_timeframe/cross_instrument), just on a different
calendar day (07-19 vs slot-7's 07-05) — do NOT merge into slot-7's report file as-is, the day mismatch would
misrepresent it. 2 new real driver bugs found+fixed+shipped:
`issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md` (P2) and
`/plans/archive/issues/features_pipeline_e2e_check_duplicate_vm_launch_same_shard_2026_07_27.md` (resolved 2026-07-30)
(P2 — root cause independently also fixed by slot-6's `features-service@6981b2b8`). Also incidentally answers the sports
`IS_TEST_RUN` issue's own P2 audit-todo for volatility/cross_instrument/multi_timeframe/commodity: every cell that
produced real output wrote to the correct `-test-` bucket (no PROD-pollution bug found); `onchain` never got real output
to check. Real findings not separately filed given time: OOM kill (rc=137) on `cross_instrument:CEFI` loading a
115,584×4,476 dataset for `regime_detection`; genuine upstream 404 (`baker_hughes_rig_count`) on `commodity:TRADFI`.

**Discovered mid-session**: slots 6/7/10 were concurrently working this SAME todo without my awareness (see their
entries above). Slot-7's day=2026-07-05 non-CEFI driver (PID 3665121) confirmed STILL RUNNING at this check, so per
slot-6's own disposition 9b's closure isn't mine to claim — **9b left OPEN**. Live fleet check also found **9**
`features-e2e-*` VMs still RUNNING right now (oldest ~9h) — billing-waste addendum filed on
`issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` (P1, recommends
`/vm-preemption-billing-waste-audit`). **Next session**: check if slot-7's run finished; then decide whether the day-19
CEFI proof suffices or the 4 CEFI cells need a same-day (07-05) re-run before flipping 9b.

### 2026-07-27 (slot-7, same slot, PID 3665121 finished) — todo 9b + standalone todo DONE: full 16-shard matrix completed; calendar/sports re-run confirmed SAFE; cross-linked with slot-3's parallel findings

The day=2026-07-05 driver (PID 3665121, referenced above and by slot-3/6/10/2) ran to completion: **~3h56min wall-clock
(11:21:49 → 15:15:07 UTC)**, via `run_in_background` + a companion heartbeat loop every ~200s (the confirmed
session-teardown mitigation) — **zero session-teardown kills**. Report:
`plans/audit/results/data_pipeline_e2e_check_features_2026_07_05.md` — **total=32 passed=3 failed=17 skipped=12** (all
16 real viable cells per the driver's own enumeration, not the ~29 estimate elsewhere in this plan).

**Claiming 9b's closure now** per slot-3's own explicit disposition ("check if slot-7's run finished... before flipping
9b") — it finished, covering the same 4 CEFI cells slot-3 asked about, on the operator-ruled day (07-05) throughout. The
standalone "Run `/data-pipeline-check-features` across ALL shards" todo above is the same underlying goal (a
pre-existing collision risk this plan's own Progress Log already flagged) — both flipped from this one completed run.

**Before trusting the calendar/sports re-run** (a prior slot-7 entry above explicitly warned "Do NOT re-run `calendar`
or `sports` until fixed" — sports' `IS_TEST_RUN` bug was open at that point), verified `features-service@48a255cd` (the
sports fix) was live and ground-truthed both writes directly against GCS: `features-sports-test-...`'s `day=2026-07-05`
fixtures object shows `creation_time=2026-07-27T14:47:45Z` (matching this run) while the PROD equivalent is untouched
since the original incident's `2026-07-27T09:03:54Z` (`metageneration: 1` unchanged) — no new PROD pollution. Same check
for calendar: TEST object created `2026-07-27T14:58:41Z`, no PROD equivalent exists. **Both families confirmed safe.**

**Two follow-up issue docs filed** (findings triage — this todo's job was RUN + REPORT, not fix):

1. `issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md` — CEFI:delta_one AND
   TRADFI:volatility both hit the driver's 2400s per-VM timeout despite genuinely still computing, causing an orphaned
   duplicate VM each time. **Already fixed same-day by slot-6** (`features-service@4d71b1b5`,
   `_FAMILY_TIMEOUT_OVERRIDES`) — TRADFI:volatility's fix is fully verified (real `EXIT_STATUS=0` observed at 4788s);
   CEFI:delta_one's override (36000s) is evidence-based but not yet directly observed completing.
2. `issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md` (**P0, big finding**) — direct VM
   `run.log` inspection of the 17 failed (non-timeout) legs surfaced 6 distinct GENUINE root causes across ≥3 repos: (A)
   the coverage-check/dependency-check disagreement for TRADFI candles (independently corroborated by slot-3 on a
   different day — tracked in ONE place,
   `issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`, not duplicated); (B)
   `multi_timeframe` reads TODAY's wall-clock date instead of the requested window, hit IDENTICALLY by both CEFI and
   TRADFI — the highest-value fix, asset_group-agnostic; (C) a genuine OOM (exit=137) during CEFI:cross_instrument's
   `regime_detection` HMM fit (also independently seen by slot-3); (D) SPORTS:sports skip-leg hit a stale manifest
   consolidator + a local/VM env-parity gap; (E) TRADFI:commodity's external vendors (EIA/CFTC/Baker Hughes) 403/404'd —
   **RULED 2026-07-28 (retagged from `[OPERATOR]`): CFTC + Baker Hughes turned out to be code bugs, not credential gaps,
   and are already fixed (see the widespread-failures issue doc for the fix commits); EIA's free API-key registration is
   the one real remaining credential ask, and the operator explicitly DECLINED it — "no one cares about EIA right now";
   do NOT register an EIA key or build toward it. Closed as declined, not deferred; the `storage_alpha` commodity factor
   stays without EIA natural-gas/crude storage data indefinitely** (also independently seen by slot-3); (F) a cascade of
   (A). 12 skips were honest and correctly not counted as failures.

**Cross-referenced all 4 issue docs** (this session's 2 + slot-3's 2) so root causes A and the timeout defect each have
exactly ONE tracked fix-todo. **Corrected an error made mid-session**: an earlier version of the timeout doc mistook
`TRADFI:delta_one`'s fast EXIT (a real dependency-check failure, root cause A) for a fast clean pass and called it a
"negative control" — fixed in that doc's own Progress Log once caught; did not affect the shipped timeout fix, which
targeted the two independently-confirmed cells on their own merits.

**Disposition**: DONE. **Next session**: work the 6 fix-path todos in the widespread-failures doc (root cause B — the
`multi_timeframe` date bug — is the highest-value/lowest-effort fix, asset_group-agnostic), then re-run for just the
affected shards to confirm genuine (non-error) verdicts.

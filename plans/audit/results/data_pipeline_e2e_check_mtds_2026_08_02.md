---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-08-02)"
summary:
  "data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-08-02, all legs: total=14 passed=2 failed=8 ambiguous=0
  skipped=4"
status: partial
nature: record
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds]
related: []
created: 2026-08-04
audited_scope:
  "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2026-08-02, legs=force,skip,live (run in
  2 separate invocations, results merged here — see note below)"
date: 2026-08-04
auditor: data_pipeline_e2e_check_mtds (real-VM automated run)
parent_epic: security_and_cross_cutting_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2026-08-02
generated_at: 2026-08-04T07:30:00+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-08-02)

> **Note on this doc's provenance**: the checker was run in 2 separate invocations — Phase 1 (`--legs force,skip`) and
> Phase 2 (`--legs live --mvp-only`) — because each invocation's own `report.write_report()` targets a filename keyed
> only by `run_date` (`data_pipeline_e2e_check_mtds_2026_08_02.md`), so Phase 2's write silently OVERWROTE Phase 1's
> report at the same path (both `.md` and sibling `.json`) rather than appending. This doc manually merges both runs'
> real results (Phase 1's table transcribed from this session's own captured tool output before the overwrite, Phase 2's
> table from the file as currently written) so no real finding is lost. **Filed as a checker-script defect** — see the
> issue doc referenced in the parent plan's Progress Log.

**Legs:** force, skip, live (2 separate invocations) **Phase 1 (force,skip) started:** 2026-08-04T06:36:57.875231+00:00
**finished:** 2026-08-04T06:58:12.615074+00:00 **Phase 2 (live) started:** 2026-08-04T07:10:26.743234+00:00
**finished:** 2026-08-04T07:20:08.443460+00:00

**Combined summary:** total=14 passed=2 failed=8 ambiguous=0 skipped=4

## Phase 1 — force, skip (day=2026-08-02, auto-day substituted per cell)

| Shard                                   | Leg   | Status  | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                                                                                                                                                                                                                                                        |
| --------------------------------------- | ----- | ------- | -------------- | ---- | ------- | -------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PREDICTION:POLYMARKET:trades            | force | failed  | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-08-03/                                                                                                                                                                 |
| PREDICTION:POLYMARKET:trades            | skip  | failed  | ambiguous      | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-08-03/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                                                                                          |
| PREDICTION:POLYMARKET:book_snapshot_5   | force | skipped | not_applicable | -    | 0       | -        | not_checked | live_only_data_type: batch cannot fetch a historical order-book snapshot                                                                                                                                                                                                      |
| PREDICTION:POLYMARKET:book_snapshot_5   | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | live_only_data_type: batch cannot fetch a historical order-book snapshot                                                                                                                                                                                                      |
| PREDICTION:KALSHI:trades                | force | failed  | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-08-03/                                                                                                                                                                 |
| PREDICTION:KALSHI:trades                | skip  | failed  | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-08-03/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                                                                                          |
| PREDICTION:KALSHI:book_snapshot_5       | force | skipped | not_applicable | -    | 0       | -        | not_checked | live_only_data_type: batch cannot fetch a historical order-book snapshot                                                                                                                                                                                                      |
| PREDICTION:KALSHI:book_snapshot_5       | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | live_only_data_type: batch cannot fetch a historical order-book snapshot                                                                                                                                                                                                      |
| PREDICTION:POLYMARKET:prediction_trades | force | failed  | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-04-14/                                                                                                                                                                 |
| PREDICTION:POLYMARKET:prediction_trades | skip  | failed  | ambiguous      | -    | 0       | -        | not_checked | vm_not_success:vm_self_deleted_no_exit_status (confirmed genuine SPOT preemption via `gcloud compute operations list`, matching the known asia-northeast1-c residual pattern — not a code/data defect); skip_signal_not_found_in_run_log; object_signature_changed_or_missing |

Note: the 2 `POLYMARKET:trades`/`KALSHI:trades` force-leg `no_parquet_under` failures (both `Exit=0`, i.e. the VM
launcher itself reported success) are a genuine finding, not infra noise — the VM ran cleanly but the expected parquet
never landed at the expected test-bucket path. Not root-caused further within this checkpoint task's scope; flagged in
the issue doc below for follow-up.

## Phase 2 — live (day=2026-08-02, `--mvp-only`)

| Shard                                 | Leg  | Status | Skip proof     | Exit | Parquet | Manifest        | Content     | Reason                                                                   |
| ------------------------------------- | ---- | ------ | -------------- | ---- | ------- | --------------- | ----------- | ------------------------------------------------------------------------ |
| PREDICTION:POLYMARKET:trades          | live | passed | not_applicable | 1    | 0       | empty_confirmed | not_checked | ok (despite vm_not_success:vm_exit_nonzero=1; live row via per_vm_shard) |
| PREDICTION:POLYMARKET:book_snapshot_5 | live | failed | not_applicable | -    | 0       | -               | not_checked | no sampled instrument_id/underlying available for live shard-spec        |
| PREDICTION:KALSHI:trades              | live | passed | not_applicable | 1    | 0       | empty_confirmed | not_checked | ok (despite vm_not_success:vm_exit_nonzero=1; live row via per_vm_shard) |
| PREDICTION:KALSHI:book_snapshot_5     | live | failed | not_applicable | -    | 0       | -               | not_checked | no sampled instrument_id/underlying available for live shard-spec        |

## Operational findings (this session, not shard verdicts)

- **Confirmed 2x: `pipeline_e2e_check.py` hangs after writing its report** — RSS climbing (~465MB/30s observed), zero
  new log output, no VMs left to clean up (`gcloud compute instances list` empty for the run's VM-name prefix), process
  in uninterruptible-sleep (`D`) state. Both Phase 1 and the first Phase 2 attempt hit this; both times the report file
  was already fully/correctly written before the hang, so no data was lost — terminated the exact captured PID via
  SIGTERM each time (never a name-based `pkill`). Filed as an issue doc (see parent plan Progress Log).
- **1 genuine SPOT preemption** (`PREDICTION:POLYMARKET:prediction_trades` skip-leg) confirmed via
  `gcloud compute operations list` — `compute.instances.preempted`, matching the already-tracked
  `asia_northeast1_c_spot_preemption_storm_2026_08_04.md` residual pattern. Not a data/code defect.
- **Session died mid-Phase-2** (unrelated infra event) after the POLYMARKET/trades live leg completed but before the
  script's own report write — orphaned 2 still-running `--test-run --max-duration-seconds 90` smoke VMs, which
  self-terminated on their own (confirmed no lingering instances after re-running Phase 2 fresh).
- **Filename collision**: Phase 1 and Phase 2 each write to the SAME date-keyed report path
  (`data_pipeline_e2e_check_mtds_2026_08_02.md`/`.json`), so running legs in separate invocations silently loses the
  earlier invocation's report unless manually preserved (as done in this doc). Filed as a fix-request in the same issue
  doc.

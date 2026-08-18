---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_is (2026-08-02) — prediction pre-Phase-B baseline"
summary: >-
  data_pipeline_e2e_check_is pipeline-e2e-check for PREDICTION, day=2026-08-02: POLYMARKET force+skip PASSED (genuine);
  POLYMARKET live-leg and all KALSHI legs (force x2 attempts, skip x2 attempts, live) FAILED — every KALSHI failure plus
  the POLYMARKET live-leg failure independently confirmed as genuine SPOT preemption via `gcloud compute operations
  list` (compute.instances.preempted), not a code or data-correctness defect. Corroborated in the already-open
  `asia_northeast1_c_spot_preemption_storm_2026_08_04.md` issue.
status: partial
nature: record
asset_group: [prediction]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_is, pre-phase-b-baseline, spot-preemption]
related:
  [
    /plans/archive/2026_07/prediction_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md,
    /plans/archive/issues/asia_northeast1_c_spot_preemption_storm_2026_08_04.md,
  ]
created: 2026-08-04
audited_scope:
  "data_pipeline_e2e_check_is real-VM force/skip/live pipeline check for PREDICTION, day=2026-08-02,
  legs=force,skip,live (consolidated across 5 invocations — this is the pre-Phase-B baseline, 1 of 2 required
  checkpoints per task_template.md finding K's 3x cadence)"
date: 2026-08-04
auditor: data_pipeline_e2e_check_is (real-VM automated run, slot 6)
parent_epic: security_and_cross_cutting_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_is
run_date: 2026-08-02
generated_at: 2026-08-04T06:31:00+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_is (2026-08-02) — prediction pre-Phase-B baseline

**Legs:** force, skip, live (run across 5 separate invocations 05:35Z-06:23Z as failures were diagnosed and retried)
**Asset group:** PREDICTION (MVP venues: POLYMARKET, KALSHI)

**Summary:** total=8 passed=2 failed=6. Both POLYMARKET force+skip cells are a genuine, verified PASS. All 6 remaining
cells (POLYMARKET live; KALSHI force/skip/live, KALSHI force+skip retried once each) FAILED — every one of the 6
confirmed via `gcloud compute operations list --filter="targetLink~<vm> AND operationType=compute.instances.preempted"`
to be a genuine SPOT preemption of the check-VM itself (`compute.instances.preempted`, `status=DONE`), not a
pipeline/code/data defect. This is an active, already-tracked zone-wide condition
(`asia_northeast1_c_spot_preemption_storm_2026_08_04.md`) — preemption rate in `asia-northeast1-c` intensified during
this run (from ~1 event/6min at 06:10Z to ~1 event/1-2min by 06:15-06:23Z), affecting `expected-universe-v2-sports`,
`tradfi-bf-cme-ohlcv-1m-*`, and these `instr-backfill-pred-pchk-*` check-VMs concurrently. Stopped after 2 KALSHI
force+skip attempts + 1 live-leg attempt (all preempted) per that issue doc's "do not blind-loop-relaunch during an
active storm" guidance — this is a P2 baseline checkpoint, not a hard-deadline gate.

## Results

| Shard                            | Leg   | Attempt                                               | Status     | Reason                                                                                                          |
| -------------------------------- | ----- | ----------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------------- |
| PREDICTION/POLYMARKET/2026-08-02 | force | 1                                                     | **passed** | ok (duration 1519.3s; cqg_bundle_present_and_canonical; market_lifecycle_present 63 objects)                    |
| PREDICTION/POLYMARKET/2026-08-02 | skip  | 1 (failed — wrong ambient gcloud identity, see below) | failed     | vm_run_not_successful:launcher_script_nonzero_rc=1 (`compute.instances.create PERMISSION_DENIED`)               |
| PREDICTION/POLYMARKET/2026-08-02 | skip  | 2 (retry, identity-scoped to `unified-trading-sa`)    | **passed** | ok, genuine skip-proof (duration 221.5s; cqg_bundle_present_and_canonical; market_lifecycle_present 63 objects) |
| PREDICTION/POLYMARKET/2026-08-02 | live  | 1                                                     | failed     | vm_run_not_successful:vm_self_deleted_no_exit_status — **confirmed genuine SPOT preemption** (06:16:56-17:06Z)  |
| PREDICTION/KALSHI/2026-08-02     | force | 1                                                     | failed     | vm_run_not_successful:vm_self_deleted_no_exit_status — **confirmed genuine SPOT preemption** (06:07:32-44Z)     |
| PREDICTION/KALSHI/2026-08-02     | skip  | 1                                                     | failed     | vm_run_not_successful:vm_self_deleted_no_exit_status — **confirmed genuine SPOT preemption** (06:09:33-47Z)     |
| PREDICTION/KALSHI/2026-08-02     | force | 2 (retry)                                             | failed     | vm_run_not_successful:vm_self_deleted_no_exit_status — **confirmed genuine SPOT preemption** (06:15:24-36Z)     |
| PREDICTION/KALSHI/2026-08-02     | skip  | 2 (retry)                                             | failed     | vm_run_not_successful:vm_self_deleted_no_exit_status — **confirmed genuine SPOT preemption** (06:18:41-53Z)     |
| PREDICTION/KALSHI/2026-08-02     | live  | 1                                                     | failed     | vm_run_not_successful:vm_self_deleted_no_exit_status — **confirmed genuine SPOT preemption** (06:23:14-24Z)     |

## Root-cause note — the first POLYMARKET skip-leg failure was NOT a real permission gap

The first POLYMARKET skip-leg attempt failed with `compute.instances.create PERMISSION_DENIED`, even though the
force-leg (same identity, minutes earlier) had just succeeded. Diagnosed as a shared-host `gcloud` active-config race (a
different slot's `gcloud config set account` flipped the host-wide active identity mid-run to `github-deploy`, which
lacks the role) — `unified-trading-sa` (the correct ambient identity) was confirmed to hold `roles/compute.admin` +
`roles/compute.instanceAdmin.v1` at the project level. Fixed for this session by creating a slot-scoped named gcloud
config (`slot6-work`, pinned to `unified-trading-sa`) and invoking every subsequent `gcloud`/check subprocess with
`CLOUDSDK_ACTIVE_CONFIG_NAME=slot6-work`, which does not mutate the shared active config other slots read. Full
writeup + a second independent confirmation of this bug class:
`/plans/active/issues/shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md`.

## Bucket paths (where each write/read actually landed — passing cells only)

| Shard                            | Leg   | Parquet bucket                                       | Manifest bucket                                      | Same bucket? |
| -------------------------------- | ----- | ---------------------------------------------------- | ---------------------------------------------------- | ------------ |
| PREDICTION/POLYMARKET/2026-08-02 | force | `instruments-store-pred-test-central-element-323112` | `instruments-store-pred-test-central-element-323112` | yes          |
| PREDICTION/POLYMARKET/2026-08-02 | skip  | `instruments-store-pred-test-central-element-323112` | `instruments-store-pred-test-central-element-323112` | yes          |

## Disposition

This satisfies the **pre-Phase-B baseline checkpoint (1 of 2)** requirement
(`prediction_consolidated_native_ao_extract_2026_07_25.md` todo 2 /
`prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`'s `data-pipeline-check-is` 3x-cadence top-up) — the run
happened, on the operator-given day (2026-08-02), and its true outcome (partial pass, real-infra SPOT preemption
blocking the rest) is honestly recorded rather than silently retried to exhaustion or fabricated as clean. The
mid-migration leg (checkpoint 2 of 2) and the post-migration final gate (checkpoint 3 of 2, this doc's sibling P0 todo)
remain separately tracked and unaffected by this partial result.

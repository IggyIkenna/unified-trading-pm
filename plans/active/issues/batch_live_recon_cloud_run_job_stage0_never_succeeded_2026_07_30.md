---
doc_type: issue
title:
  "uts-prod-batch-live-reconciliation-service Cloud Run job has failed at Stage 0 (config_pull) on every measured
  execution since job creation (2026-05-22) — upstream config/ML/strategy T+1 snapshots have never once existed"
summary: >-
  Live-checked (`gcloud run jobs executions list/describe` + Cloud Logging) while investigating whether
  `launch-batch-live-recon-cron-vm.sh` (the VM launcher named in
  `setup_data_pipeline_vm_dispatch_gap_batch_live_recon_chaos_drill_2026_07_30.md`) is actually wired to a live
  scheduler. Found it is NOT the live path — the real nightly T+1 recon runs as a separate Cloud Run job
  (`uts-prod-batch-live-reconciliation-service`, triggered by Cloud Scheduler
  `uts-prod-batch-live-reconciliation-t1-schedule`, daily 06:00 UTC). Every execution checked in the last 30 daily runs
  (2026-07-02 through 2026-07-30) exited 1 at Stage 0 (`config_pull`) with the identical message: "Missing upstream data
  for <date-1>: execution config snapshot gs://execution-store-prd-.../configs/snapshots/<date>/config.json; ML t1-recon
  outputs gs://recon-prd-.../t1-recon/ml/<date>/_SUCCESS; strategy t1-recon outputs
  gs://recon-prd-.../t1-recon/strategy/<date>/_SUCCESS". A `gsutil ls` on all three GCS prefixes (`t1-recon/`,
  `t1-recon/ml/`, `t1-recon/strategy/`, `execution-store-prd-.../configs/snapshots/`) returned zero objects — none of
  these three upstream deliverables has EVER been written, at any date, since the job's creation. The T+1 reconciliation
  pipeline has therefore never once advanced past Stage 0 in its entire production life.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [batch-live-reconciliation-service, strategy-service, ml-service, execution-service, deployment-service]
scope: [engineer, admin]
tags: [reconciliation, batch-live-recon, cloud-run, stage0, config-pull, data-correctness, pre-live-trading]
related:
  [
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/active/issues/batch_live_reconciliation_service_audit_2026_05_27.md,
    /plans/archive/issues/setup_data_pipeline_vm_dispatch_gap_batch_live_recon_chaos_drill_2026_07_30.md,
  ]
created: "2026-07-30"
parent_epic: batch_live_symmetry_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
drift_direction: none
assigned_role: data_engineering
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Found 2026-07-30 (plans-corpus reduction marathon, wave 3) while checking whether `launch-batch-live-recon-cron-vm.sh`
  / `launch-disaster-drill-cron-vm.sh` are wired to a live Cloud Scheduler job, per
  `setup_data_pipeline_vm_dispatch_gap_batch_live_recon_chaos_drill_2026_07_30.md`'s own todo 3. `gcloud run jobs
  executions list/describe` + `gcloud logging read` + `gsutil ls`, all read-only.
---

# batch-live-reconciliation Cloud Run job — Stage 0 has never once succeeded

## What I found

While resolving `setup_data_pipeline_vm_dispatch_gap_batch_live_recon_chaos_drill_2026_07_30.md`'s todo 3 ("check
whether either nightly cron is actually wired to a live Cloud Scheduler job"), found:

1. **The VM launcher is NOT the live path.** `launch-batch-live-recon-cron-vm.sh` (whose `setup-data-pipeline-vm.sh`
   dispatch-branch bug that doc's todo 1 fixed) is not what `uts-prod-batch-live-reconciliation-t1-schedule` actually
   triggers. That Cloud Scheduler job's `httpTarget` calls
   `https://asia-northeast1-run.googleapis.com/.../namespaces/central-element-323112/jobs/uts-prod-batch-live-reconciliation-service:run`
   — a **Cloud Run Job**, a completely separate deployment mechanism. The VM launcher may be a manual/backfill-only
   alternate path; it is not what runs nightly today. (`disaster-drill-cron` / `chaos-drill` has NO scheduler job at
   all, in any of the 3 locations checked — genuinely never scheduled yet, consistent with that doc's own suspicion.)
2. **The real nightly job has never succeeded.**
   `gcloud run jobs executions list --job=uts-prod-batch-live-reconciliation-service` shows a `Completed`/`status=False`
   execution every single day for the last 30 daily runs checked (2026-07-02..2026-07-30, one run each day at 06:00 UTC,
   some days with 2 attempts e.g. 06:00 and ~06:02). Every `executions describe` shows the identical condition:
   ```
   reason: NonZeroExitCode
   message: 'Task ...-task0 failed with exit code: 1 and message: The container exited with an error.'
   ```
3. **Root cause confirmed via Cloud Logging**
   (`gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="uts-prod-batch-live-reconciliation-service"'`):
   every run fails identically at Stage 0 (`config_pull`, per `batch_live_reconciliation_service_audit_2026_05_27.md`'s
   own architecture description, "upstream snapshot availability gate... aborts pipeline if missing"):
   ```
   ERROR [Stage 0] FAILED — Missing upstream data for 2026-07-29: execution config snapshot:
   gs://execution-store-prd-central-element-323112/configs/snapshots/2026-07-29/config.json; ML t1-recon outputs:
   gs://recon-prd-central-element-323112/t1-recon/ml/2026-07-29/_SUCCESS; strategy t1-recon outputs:
   gs://recon-prd-central-element-323112/t1-recon/strategy/2026-07-29/_SUCCESS
   ERROR Stage 0 failed — aborting pipeline
   ERROR Reconciliation FAILED -- 0 deviations, failed stages: ['config_pull']
   ```
4. **None of the three upstream paths has EVER been written, at any date.** `gsutil ls` on
   `gs://recon-prd-central-element-323112/t1-recon/`, `.../t1-recon/ml/`, `.../t1-recon/strategy/`, and
   `gs://execution-store-prd-central-element-323112/configs/snapshots/` all return
   `CommandException: One or more URLs matched no objects.` — zero objects at any of these prefixes, ever. The Cloud Run
   job itself was created 2026-05-22 — so this has been failing identically for over 2 months.

## Why this is P2, not P0/P1 (hypothesis, not confirmed)

`citadel_paper_batch_live_reconciliation_2026_06_19.md` records "P7.3 (live leg) is `BLOCKED-OPERATOR-DECISION` until a
live wallet/custody is approved" — a **permanent, human-only hard-stop** reconfirmed 2026-07-28. Live trading has not
started. It is plausible the "ML t1-recon" / "strategy t1-recon" `_SUCCESS` markers and the "execution config snapshot"
are outputs of a live-trading-gated pipeline stage that genuinely has nothing to produce yet — in which case this Cloud
Run job's daily failure is an EXPECTED, harmless no-op (small Cloud Run cost, no data-correctness impact) that will
start working once live trading is approved and those upstream writers activate.

**However, this is NOT confirmed** — the same citadel plan also states paper-trading's batch-rerun determinism (P7.2) is
DONE/proven, meaning strategy-service and ml-service ARE running daily paper-mode work today. Whether that paper
pipeline is SUPPOSED to also write these specific `t1-recon/{ml,strategy}/<date>/_SUCCESS` markers (making this a real,
fixable gap independent of the live-wallet hard-stop) or whether those markers are deliberately live-only is a design
question this audit did not resolve — it requires reading strategy-service/ml-service/execution-service source (none in
this session's available repo set) to find where (if anywhere) those exact GCS paths are written.

## Todos

- [x] [DIAG] P2. Determine whether `gs://recon-prd-*/t1-recon/{ml,strategy}/<date>/_SUCCESS` and
      `gs://execution-store-prd-*/configs/snapshots/<date>/config.json` are outputs of a live-trading-gated stage (in
      which case this Cloud Run job's failure is expected/benign pending the wallet-approval hard-stop, and this issue
      should be downgraded/closed with that citation) or of the daily paper-trading pipeline (in which case something
      upstream is failing to write them and this is a real, currently-silent gap). Read the writer side in
      strategy-service/ml-service/execution-service for these exact paths. Repo: strategy-service / ml-service /
      execution-service. -- CLOSED (na-eligibility-audit 2026-08-01): already answered in
      `plans/active/issues/recon_bucket_missing_nightly_recon_failing_2026_07_13.md`'s 2026-07-14 update, which
      live-checked Cloud Scheduler/Cloud Run Job state and found execution-service's config-snapshot job and
      ml-service's t1-recon job were never provisioned (with `--run-tag` completely unwired and no `_SUCCESS`-marker
      writer anywhere), and strategy-service's job was OCI-broken until 2026-07-14 (fixed, deployment-service@ea42a699)
      and likewise has no `_SUCCESS`-marker writer -- confirming this is a real, currently-unimplemented multi-repo
      feature gap, not a live-trading-gated no-op.
- [x] [SCRIPT] P3. Whichever the diagnosis lands on: either (a) suppress/downgrade this Cloud Run job's daily failure
      alerting until the live-trading gate lifts (if genuinely expected-and-gated), or (b) fix the upstream writer gap
      (if paper-trading should already be producing these outputs). Repo: batch-live-reconciliation-service /
      deployment-service (scheduler/alerting config) depending on (a) vs (b). -- CLOSED (na-eligibility-audit
      2026-08-01): resolves to option (b) per the DIAG item above, and is already tracked as
      `plans/active/issues/recon_bucket_missing_nightly_recon_failing_2026_07_13.md`'s own open P0 todo to stand up the
      real green 06:00Z batch-live recon run (provision the missing execution-service/ml-service Cloud Run Jobs,
      implement `_SUCCESS`-marker writers, un-pause the feature schedulers) -- superseded by that more detailed todo
      rather than being a distinct action.
- [ ] [SCRIPT] P3. Confirm whether `launch-batch-live-recon-cron-vm.sh` (the VM launcher) and the live Cloud Run job
      (`uts-prod-batch-live-reconciliation-service`) are meant to be the SAME reconciliation running via two different
      deployment mechanisms (in which case the VM launcher is dead/redundant code, since the Cloud Run job already
      covers the nightly cadence) or genuinely different use cases (VM = manual/backfill re-run; Cloud Run = live
      nightly). If the former, the VM launcher + its `setup-data-pipeline-vm.sh` dispatch branch (just added this
      session, see `setup_data_pipeline_vm_dispatch_gap_batch_live_recon_chaos_drill_2026_07_30.md`) may be effectively
      unused — worth a lifecycle-marker check, not a reason to revert that fix (a manual-backfill use case is still
      plausible and the fix is harmless either way).

## Progress Log

- **2026-07-30** — Filed while resolving a sibling doc's verification todo. Read-only investigation
  (`gcloud run jobs`/`gcloud logging read`/`gsutil ls`, no writes). Not escalated further this session — the
  live-wallet-gate hypothesis makes P0/P1 unlikely, but not attempting the strategy/ml/execution-service source read
  needed to confirm, since none of those repos are in this session's available set and the diagnosis is a genuine
  judgment call, not a mechanical fix.
- **na-eligibility-audit 2026-08-01**: KEEP-NA, stale items closed -- 2 item(s) closed as stale/duplicated (see
  checkboxes above), doc stays assigned_vm: NA. Full audit rationale: 2 of the 3 open items (the DIAG diagnosis and its
  branching fix-action) are already answered/tracked, with hard dated evidence, in a sibling NA doc
  (recon_bucket_missing_nightly_recon_failing_2026_07_13.md, updated 2026-07-14) that this doc apparently never
  cross-referenced. That older doc traces th...

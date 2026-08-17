---
doc_type: plan
title: Honest-coverage + data-status rollup health verification and launcher timeout fix
summary: >
  Operator asked to run honest coverage for all asset groups so the data-status page shows the latest, and to confirm
  the daily rollup is running per-AG/aggregate. Verified both Cloud Scheduler jobs end-to-end (not just
  scheduler-enabled) and found a live/committed Terraform drift on the honest-coverage launcher's task timeout that
  had been producing a false Completed/False status every day since 2026-08-10 despite the underlying computation
  actually succeeding. Fixed via an isolated, already-authored, non-destructive apply.
status: complete
nature: design
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-service, instruments-service, unified-trading-library]
scope: [engineer, admin]
tags: [honest-coverage, data-status-rollup, terraform-drift, cloud-scheduler, monitoring, false-negative]
related:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md,
    /plans/active/manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md,
    /plans/active/issues/deployment_service_prod_terraform_drift_2026_08_07.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: ["interactive session, 2026-08-16, operator request (verbatim): 'run honest coverage rollout too for all AGs so we can see latest in data status page' + 'make sure the daily rollup is running for each AG or aggregate'"]
assigned_role: infra
effort: medium
drift_direction: advance-code
context_scope:
  [
    /codex/02-data/honest-coverage-model.md,
    deployment-service/terraform/gcp/honest_coverage_scheduler.tf,
    deployment-service/terraform/gcp/data_status_rollup_scheduler.tf,
    instruments-service/scripts/measure_honest_coverage.py,
  ]
---

# Honest-coverage + data-status rollup health verification and launcher timeout fix

> **LOCAL / human plan** — investigative infra verification + a single narrow judgment-call fix, not a bounded worker
> todo. Cross-linked with `/plans/active/manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md` (same
> session, adjacent topic — that plan is manifest-consolidator/GCS-lifecycle **cost**; this one is honest-coverage/
> data-status-rollup **freshness and correctness**, deliberately kept separate).

## Background

Operator asked to (1) run the honest-coverage rollout for all asset groups so the data-status page shows current
numbers, and (2) confirm the daily rollup is running per-AG or aggregate. Neither ask named a specific job — both were
found via `gcloud scheduler jobs list`:

- **`honest-coverage-daily`** (Cloud Scheduler, `30 0 * * *` UTC) → `honest-coverage-daily-launcher` (Cloud Run Job) →
  launches a GCE VM running `instruments-service/scripts/measure_honest_coverage.py --asset-group all` → writes
  `gs://central-element-323112-honest-coverage/{date}/coverage.json`. ONE combined run covering all 5 AGs, not
  per-AG jobs.
- **`uts-prod-data-status-rollup-cron`** (Cloud Scheduler, `*/20 * * * *` UTC) → HTTP POST to the dedicated
  `uts-prod-data-status-rollup-svc` Cloud Run Service's `/api/data-status/rollup-run` endpoint → writes
  `gs://central-element-323112-data-status-rollups/{service}/full.json.gz` per service (MTDS/MDPS/instruments ×
  asset_group), overwrite-by-name, idempotent.

Both were already `ENABLED` and firing on schedule. The real question was health, not existence — this doc exists
because the health check surfaced a genuine, previously-undiagnosed bug.

## What was found

1. **`honest-coverage-daily-launcher` has reported `Completed/False` (exit 1) every single day since 2026-08-10**
   (confirmed via `gcloud run jobs executions list`, 7 consecutive daily executions 08-10 through 08-16 all failed).
   This looked, at first glance, exactly like the OOM class of failure already tracked in
   `issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md` — but it is NOT that. Root cause (confirmed via
   `gcloud logging read` on the launcher's own container log):
   - The launcher's `lc_poll_for_terminal_state` function polls up to 20 minutes waiting for the VM's output object.
   - The Cloud Run **Job task's own timeout** was live at **300 seconds** — killing the launcher mid-poll every time
     (`Terminating task because it has reached the maximum timeout of 300 seconds`).
   - Cloud Run's retry then launched a second launcher attempt, which correctly detected the still-running VM from
     attempt 1 and refused to race it (`ERROR: measure-honest-coverage VM already running ... Use --force to bypass`),
     exiting 1 — the launcher's own documented safety guard working as designed, just on a spurious second attempt.
   - The committed Terraform (`deployment-service/terraform/gcp/honest_coverage_scheduler.tf:39-47`) **already fixes
     this** — a dated 2026-08-09 comment explains bumping `timeout_seconds` from 300 to 1500 for exactly this reason,
     citing this exact OOM issue doc. **That fix was authored but never applied to prod** — live
     `gcloud run jobs describe` showed `timeoutSeconds: '300'` right up until this session applied it. Classic
     live/committed drift, same class already tracked in `issues/deployment_service_prod_terraform_drift_2026_08_07.md`
     for other resources, just not previously caught for this one.
2. **Despite the launcher's false failure status, the underlying VM computation has been succeeding.** Verified via a
   single-object GCS metadata read (not a bulk walk) against
   `gs://central-element-323112-honest-coverage/{date}/coverage.json` for 2026-08-09 through 2026-08-16, then a full
   content read of today's file:
   - `2026-08-16/coverage.json`: `generated_at=2026-08-16T00:43:09Z` (matches the VM's actual serial-console shutdown
     window, 00:43-00:45), `asset_groups_requested=[cefi,defi,tradfi,sports,prediction]`,
     `asset_groups_measured=[cefi,defi,tradfi,sports,prediction]`, `asset_groups_failed=[]`, `partial=false`. **All 5
     asset groups computed cleanly today** — this is the "latest" the operator asked to see on the data-status page.
   - Per-date presence check: 08-09 present, 08-10 present, **08-11 MISSING**, 08-12 present, **08-13 MISSING**, 08-14
     present, 08-15 present, 08-16 present. The two gaps (08-11, 08-12) are already fully explained in
     `issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md`'s Progress Log (an independent
     `get_storage_client` refactor regression + a post-defi-rebuild OOM, both already fixed 2026-08-12) — not
     re-investigated here, no new gap found beyond what that doc already covers.
3. **`uts-prod-data-status-rollup-svc` is healthy with an already-documented, accepted occasional-timeout pattern** —
   not a new bug. Last 10 invocation logs: 8/10 = HTTP 200, 2/10 = HTTP 504 at exactly 1699.8s (matching the
   `attempt_deadline = "1700s"` ceiling in `data_status_rollup_scheduler.tf`). The `.tf` file's own 2026-08-10 comment
   already documents this exact tradeoff: instruments-service's sports asset-group compute can take >1200s on its own,
   occasionally exceeding the 20-min cron gap; the worker is idempotent (overwrite-by-name per service), so a timed-out
   tick is recovered by the next one. This is the SAME false-negative-shaped pattern the task brief warned about
   (`market-data-cefi` consolidator showing `Completed/False`/`Completed/Unknown`) — checked carefully, and unlike the
   honest-coverage launcher, this one really is benign-by-design, not a hidden bug. Stated plainly rather than averaged
   away.

## What was fixed

- **`module.honest_coverage_daily_job.google_cloud_run_v2_job.job` task timeout**: applied the already-committed,
  already-reviewed 300s→1500s value to live prod via an **isolated `-target` apply**
  (`ENV=prod bash tofu.sh apply -target=module.honest_coverage_daily_job.google_cloud_run_v2_job.job -auto-approve`),
  after first running the equivalent `plan -target` and confirming it isolated cleanly (`Plan: 0 to add, 1 to change,
  0 to destroy` — the timeout field only, nothing else swept in). This does **not** touch or resolve the larger
  pending drift tracked in `issues/deployment_service_prod_terraform_drift_2026_08_07.md` (36 add/17 change/4 destroy,
  including the still-unresolved meta-watchers memory question and the 2 Secret IAM destroys) — that stays exactly as
  documented there, still `[OPERATOR]`-gated, untouched by this narrower fix.
- Live-verified post-apply: `gcloud run jobs describe honest-coverage-daily-launcher ... timeoutSeconds` = `1500`
  (was `300`).
- **No VM was launched by this session for either job.** Both `honest-coverage-daily` and
  `uts-prod-data-status-rollup-cron` already run on their own existing, working schedule (daily / every-20-min
  respectively) via already-provisioned mechanisms — there was nothing to newly trigger. The one action taken was
  fixing an existing resource's misconfigured timeout, not launching new compute.

## Todos

- [x] 1. ✅ [INFRA] P1. Verify `honest-coverage-daily`'s underlying computation is actually fresh and complete for all
      5 asset groups (not just "scheduler enabled") — done via a single-object GCS read of today's
      `2026-08-16/coverage.json`: `asset_groups_measured=[cefi,defi,tradfi,sports,prediction]`,
      `asset_groups_failed=[]`, `partial=false`, `generated_at=2026-08-16T00:43:09Z`. Repo: instruments-service
      (output only, no code change).
- [x] 2. ✅ [INFRA] P1. Root-cause + fix `honest-coverage-daily-launcher` reporting `Completed/False` every day since
      2026-08-10 — diagnosed as a live/committed Terraform drift (live `timeoutSeconds=300` vs committed `1500`,
      `honest_coverage_scheduler.tf:39-47`), fixed via isolated `-target` apply, live-verified `timeoutSeconds=1500`
      post-apply. Repo: deployment-service. Evidence: `gcloud run jobs describe honest-coverage-daily-launcher
      --region=asia-northeast1 --project=central-element-323112 --format="value(spec.template.spec.template.spec.timeoutSeconds)"`
      → `1500`.
- [x] 3. ✅ [REVIEW] P2. Confirm tomorrow's (2026-08-17 00:30 UTC) `honest-coverage-daily-launcher` execution reports
      `Completed/True` — **CONFIRMED 2026-08-17**, via a scheduled one-shot check armed the prior session. Execution
      `honest-coverage-daily-launcher-tcqjp` started `2026-08-17T00:30:07Z` (right on the `30 0 * * *` UTC cron),
      completed `2026-08-17T00:49:46Z` (19m39s — well inside the new 1500s ceiling, confirming the launcher genuinely
      needed more than the old 300s, not that 1500s is arbitrary headroom) with `status.conditions[0].status=True`.
      Cross-checked against the two prior days for contrast: `2026-08-16` (`h65rz`) and `2026-08-15` (`zjdfl`) both
      ran ~6 minutes and reported `Completed=False` — consistent with hitting the OLD 300s timeout, confirming the
      fix (not some unrelated variable) is what changed the outcome. Evidence:
      `gcloud run jobs executions list --job=honest-coverage-daily-launcher --region=asia-northeast1
      --project=central-element-323112 --limit=3 --format="table(name,status.conditions[0].type,status.conditions[0].status,status.startTime,status.completionTime)"`.
- [x] 4. ✅ [REVIEW] P2. Verify `uts-prod-data-status-rollup-cron` health via its last 10 invocation logs — 8/10 HTTP
      200, 2/10 HTTP 504 at exactly the 1700s `attempt_deadline`, matching the already-documented accepted tradeoff in
      `data_status_rollup_scheduler.tf`'s 2026-08-10 comment (sports AG occasionally exceeds the 20-min cron gap;
      idempotent overwrite-by-name recovers on the next tick). No fix needed — this is benign-by-design, not the same
      false-negative class as todo 2's launcher bug. Repo: deployment-service (verification only).

## Progress Log

- **2026-08-16 (interactive session)**: Plan created. Ran `gcloud scheduler jobs list` fleet-wide (132 jobs) to find
  the real job names per CLAUDE.md's "don't guess a job name a second time" instruction — confirmed `honest-coverage-daily`
  (not the earlier-guessed `uts-prod-data-status-rollup-svc-cron`) and `uts-prod-data-status-rollup-cron`. Diagnosed
  the launcher false-failure via `gcloud logging read` on the Cloud Run Job's own container log + the GCE VM's serial
  console + the compute activity log (insert/delete timestamps proving the VM ran ~13-15 min and shut down cleanly,
  no OOM signature, unlike the 08-06..08-09 incidents). Confirmed the fix via an isolated `tofu plan -target` (0
  add/1 change/0 destroy) before applying — did not touch the larger pending drift tracked in
  `deployment_service_prod_terraform_drift_2026_08_07.md`. Verified the underlying honest-coverage data itself via a
  single-object GCS metadata + content read (not a bulk walk), per the operator's laptop-session no-heavy-I/O
  constraint. No new VM launched. Cross-linked `related:` both directions with
  `manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md` (adjacent topic, same session, deliberately
  separate plan) and added a closing Progress Log note to
  `issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md` (that doc's own Terraform comment described
  the fix this session found un-applied and applied).
- **2026-08-17 (scheduled one-shot check, armed 2026-08-16)**: todo 3 confirmed — the fix holds on a genuine fresh
  scheduled run, not just the isolated verification apply. See the flipped todo above for the exact evidence. All 4
  todos are now `[x]`. Archiving per plan-completion-and-archival-discipline.

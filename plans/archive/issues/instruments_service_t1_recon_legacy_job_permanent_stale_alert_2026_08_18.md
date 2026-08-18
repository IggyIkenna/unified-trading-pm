---
doc_type: issue
title: DP-WATCHER-006 — legacy instruments-service-t1-recon job pages forever on a 36-day-stale OOM failure
summary:
  "DP-WATCHER-006 fired for uts-prod-instruments-service-t1-recon (1 failed task, ~51752m/36 days stale at
  dispatch). Root cause -- this is the legacy all-AG job, retired 2026-07-13/14 and superseded by per-AG jobs
  (defi/tradfi/cefi/prediction), but cloud_run_job_registry.py never excluded its stem: since the watcher checks
  each registered stem's LATEST completed execution with no time window, a permanently-dead job's one static
  failure pages every sweep forever. Fixed by excluding the retired stem from the watcher's per-job check
  (mirroring the existing cf-manifest-audit exclusion pattern) and registering the 3 real, currently-healthy
  per-AG jobs (defi/tradfi/prediction) that were also missing from the registry -- a separate monitoring blind
  spot found adjacent to the fix. RESOLVED."
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [data-pipeline, dp-watcher-006, cloud-run-job, escalation, instruments-service, monitoring-gap]
related: ["/codex/05-infrastructure/data-pipeline-alerts.md", "/plans/active/cross_cutting_consolidated_closeout_2026_07_25.md"]
created: 2026-08-18
parent_epic: observability_master
priority: P1
source: [DP-WATCHER-006, agt-0c542c]
assigned_vm: NA
resolved_by: "data_pipeline_failure-agent (slot 33, agt-0c542c) — deployment-service@03be2c2ada"
locked_by:
---

# DP-WATCHER-006 — legacy instruments-service-t1-recon job pages forever on a 36-day-stale OOM failure

## What I found

`escalation_id=agt-0c542c` — DP-WATCHER-006 (generic Cloud Run Job execution-failure sweep) fired for
`uts-prod-instruments-service-t1-recon` (asia-northeast1, `central-element-323112`): "1 failed task(s), 51752m ago"
(~36 days stale at dispatch). No candidate slug was filed by the detector (per the 2026-08-18 "never raw-`git
commit` from an ephemeral runner" fix in `/codex/05-infrastructure/data-pipeline-alerts.md`), so filing this doc
was the dispatched worker's job.

**Live diagnosis:**

- `gcloud run jobs executions list --job=uts-prod-instruments-service-t1-recon --region=asia-northeast1`: latest
  executions all dated 2026-07-12/07-13, all `status.conditions[0].status=False` (failed). Zero executions since.
- `gcloud scheduler jobs list ... --filter="name~instruments-service-t1-schedule OR name~instruments-service-t1-recon"`:
  empty — no Cloud Scheduler currently targets this job. It will not fire again on its own.
- `deployment-service/terraform/gcp/t1_batch_scheduler.tf:41-45` (comment, pre-existing): "The old all-AG
  'instruments' 00:00 job (uts-prod-instruments-service-t1-recon) OOM'd at 8cpu/32Gi (signal 9) because sports
  alone = 5.6M rows in one execution. It has been RETIRED and replaced by per-AG jobs." Matches the failure
  timestamps exactly (2026-07-13).
- `deployment-service/configs/sports-trigger-tiers.yaml:38-42` independently confirms the same retirement, same
  date, same OOM root cause.
- `deployment-service/terraform/gcp/t1_recon_instruments_jobs.tf` declares only the 4 per-AG jobs (defi, tradfi,
  cefi, prediction) — no terraform resource for the bare all-AG name. Confirmed live-healthy via
  `gcloud run jobs executions list` on all 4 per-AG jobs: cefi/defi/tradfi/prediction all succeeded on their most
  recent (2026-08-17/18) scheduled runs.
- **Root cause of the PERMANENT/recurring shape** (not just a one-time stale event):
  `deployment_service/cloud_run_job_failure_watcher.py::check_cloud_run_job_failures` (DP-WATCHER-006's own
  implementation) reads each registered stem's **most recently completed execution** with no time-window filter —
  by design, per its own docstring ("the execution failure itself is the signal regardless of any downstream
  artifact"). For a job with a scheduler, a new (hopefully-green) execution eventually supersedes an old failure.
  For a job with **no scheduler at all**, the "most recent" execution is permanently that one static failure —
  this will page every sweep, forever, with zero new information, unless the stem is excluded. The watcher already
  has this exact exclusion pattern for a different reason (`_DESIGNED_NONZERO_EXIT_STEMS`, `cf-manifest-audit`) —
  it just never got a "retired job" variant.
- `deployment_service/cloud_run_job_registry.py::_T1_RECON_JOBS` still carried
  `_batch("instruments-service-t1-recon", service="instruments-service")` (the bare/legacy stem) as a live,
  classified deployment target — the thing `_gcp_job_stems()` (DP-WATCHER-006's enumeration) iterates over.
- **Adjacent finding, same file**: `instruments-service-defi-t1-recon`, `-tradfi-t1-recon`, and
  `-prediction-t1-recon` (all 3 real, live, currently-healthy Cloud Run Jobs per the terraform above) were
  **absent** from `_T1_RECON_JOBS` entirely — only `-cefi-t1-recon` and `-sports-fixtures` were registered for
  instruments-service. This is exactly the blind-spot class DP-WATCHER-006 was built to close (its own docstring:
  "the 2026-08-07 infra-health audit found zero of 11 production failures produced a Slack alert... every other
  GCP Cloud Run Job in the registry was invisible to the alerting spine") — these 3 jobs were invisible to it.

**Why removing the bare stem outright (instead of excluding it) would have broken the registry guard test**:
`tests/unit/test_cloud_run_job_registry_guard.py::test_every_scheduler_tf_job_is_registered` extracts a stem from
`t1_recon_instruments_jobs.tf`'s `name = "${local.env_prefix}-instruments-service-${each.key}-t1-recon"` template by
stripping `${local.env_prefix}-` and the literal `-${each.key}` substring — which, for THIS naming convention (AG
embedded mid-string, not as a suffix), collapses to exactly `instruments-service-t1-recon`, i.e. the legacy job's
own bare name. The guard currently passes only because that coincidental collapsed stem matches the registered
legacy entry — none of the real per-AG registered names (`instruments-service-cefi-t1-recon` etc.) contain
`instruments-service-t1-recon` as a contiguous substring (the AG token breaks contiguity), so a straight removal
would have made the guard fail. Excluding the stem inside the watcher (keeping the registry entry) avoids this.

## Fix

- `deployment-service@03be2c2ada`:
  - `deployment_service/data_pipeline_monitors/cloud_run_job_failure_watcher.py` — added `_RETIRED_STEMS` (mirrors
    the existing `_CONSOLIDATOR_STEM_PREFIX`/`_DESIGNED_NONZERO_EXIT_STEMS` exclusion pattern) containing
    `instruments-service-t1-recon`, excluded in `_gcp_job_stems()`.
  - `deployment_service/cloud_run_job_registry.py` — kept the legacy `instruments-service-t1-recon` entry (needed
    for the guard-test coverage quirk above, and for other registry consumers that may still want the historical
    record) but added a comment explaining the retirement + exclusion; added the 3 missing per-AG entries
    (`instruments-service-defi-t1-recon`, `-tradfi-t1-recon`, `-prediction-t1-recon`) to close the adjacent
    monitoring blind spot.
  - `tests/unit/test_cloud_run_job_failure_watcher.py` — added `test_gcp_job_stems_excludes_retired_jobs`
    (mirrors `test_gcp_job_stems_excludes_designed_nonzero_exit_jobs`).

## Verification

`bash scripts/quality-gates.sh --no-fix` — ALL QUALITY GATES PASSED (247s), including
`test_cloud_run_job_registry_guard.py` (unaffected — the legacy stem stays registered) and the new
`test_gcp_job_stems_excludes_retired_jobs` (proves DP-WATCHER-006 will never again enumerate this dead job).
Not a "live-triggered" verification in the DP-WATCHER-006-daily-ledger-digest sense — there is no live execution
to re-trigger; the job is genuinely dead (no scheduler) and re-running it manually would not prove anything the
unit test + registry inspection didn't already prove. The 3 newly-registered per-AG jobs' current health was
confirmed live via `gcloud run jobs executions list` (all succeeded on their latest 2026-08-17/18 scheduled runs).

## Recommended decision

None needed — resolved. No `[OPERATOR]`/credential/judgment gap encountered. Optional low-priority cleanup (not
done here, out of this one-shot role's scope): the orphaned `uts-prod-instruments-service-t1-recon` Cloud Run Job
resource itself could be deleted from GCP (it costs nothing idle and is harmless to leave, but it's dead weight);
left in place since deleting cloud resources is a human-judgment call this role defers rather than guesses at.

## Progress Log

- **data_pipeline_failure escalation 2026-08-18 (`agt-c61c32`, DP-WATCHER-006/DP_CLOUD_RUN_JOB_FAILED, dispatched
  ~51811m/36 days after the original static failure)**: a second dispatch on this same already-RESOLVED alert instance
  (root cause identical: legacy `uts-prod-instruments-service-t1-recon`, no scheduler, 2026-07-13 OOM). Found the code
  fix (`deployment-service@03be2c2ada`, 2026-08-18T16:50:48Z) already merged and confirmed present on
  `live-defi-rollout` before doing any re-diagnosis. **New finding beyond re-confirmation**: the fix was authored/merged
  but not yet DEPLOYED — `deployment-api` (the runtime host for the DP-monitor Cloud Run Jobs, per the "PACKAGING" note
  in `/codex/05-infrastructure/data-pipeline-alerts.md`) vendors `deployment-service` at BUILD time
  (`clone_dep deployment-service _deployment-service` in `cloudbuild.yaml`, no auto-trigger on `deployment-service`
  pushes), so the fix sat inert in source until a fresh `deployment-api` image was built. Confirmed live: the
  `deployment-api:latest` Artifact Registry tag was last pushed 2026-08-18T12:26:49Z — 4h14m BEFORE the fix commit —
  so every DP-monitor sweep since 16:50Z was still running the pre-fix code, which is why this second dispatch fired
  at all despite the issue already being marked RESOLVED. **Action taken**: triggered `deployment-api-main-deploy`
  Cloud Build (`e3e32f87-f79a-406b-a363-d8c32f714cfb`, region `asia-northeast1`) to rebuild+redeploy from current
  `live-defi-rollout` (which vendors the fixed `deployment-service` code). Verified live (not fire-and-forget): the
  build's `redeploy-monitor-jobs` step successfully updated all 3 DP-monitor Cloud Run Jobs
  (`uts-prod-dp-exit-code-monitor`, `uts-prod-dp-heartbeat-watcher`, `uts-prod-dp-meta-watchers`) to the new image;
  independently re-confirmed via `gcloud run jobs describe uts-prod-dp-exit-code-monitor` —
  `lastUpdatedTime=2026-08-18T17:48:50Z`, image `deployment-api:latest` (post-fix). The fix is now genuinely live, not
  just merged — this closes the residual gap this doc's original "RESOLVED" status didn't account for (code-shipped ≠
  operationally-shipped, per the workspace's own runtime-verification rule). No further action needed; not
  re-archiving/re-opening the doc (still correctly `status: resolved`) — this entry documents the deploy-lag closure
  for anyone else who sees a stray dispatch land on an already-resolved DP-WATCHER-006 doc.

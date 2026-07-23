---
doc_type: issue
title:
  Honest-coverage nightly cron silently failed 2026-07-17 — Cloud Run launcher never fetched its new lib/ dependency
summary: >-
  The 2026-07-17 00:30 UTC honest-coverage cron produced NO coverage.json (asset_groups_measured empty) — a regression
  from the two prior nights, which both succeeded. Root cause — the `honest-coverage-daily-launcher` Cloud Run Job's
  container command does a single-file `gsutil cp` of `launch-measure-honest-coverage-vm.sh` and runs it directly; that
  script gained a `source lib/launcher_common.sh` dependency from an earlier fleet-wide launcher rollout
  (deployment-service@b5bd336), but the Cloud Run job's fetch command was never updated to also download the `vm/lib/`
  directory, and the directory itself was never published to GCS at all. Fixed by publishing the two missing lib files
  to `gs://deployment-scripts-central-element-323112/vm/lib/`, updating the Cloud Run job's command to also fetch that
  directory (both imperatively via gcloud AND in the Terraform source, which is the declared IaC SSOT for this resource
  — deployment-service@6c7a079e1), and verifying end-to-end via a manual re-trigger (coverage.json now shows
  asset_groups_measured = all 5, partial is false).
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, instruments-service]
scope: [engineer, admin]
tags: [honest-coverage, cron, cloud-run, terraform, incident, launcher, iac-drift]
related:
  [
    /plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md,
    /plans/active/issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md,
  ]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  continuation session verifying the P1 acceptance criterion ("tomorrow's 00:30 UTC file has asset_groups_measured = all
  5 AND partial:false") from data_status_page_ux_and_canonicalisation_2026_07_16.md
resolved_by: this session, 2026-07-17
---

# Honest-coverage nightly cron silently failed 2026-07-17 — missing launcher lib/ dependency

## The incident (facts, all directly observed)

1. **The cron fired on schedule but produced nothing.** Cloud Scheduler `honest-coverage-daily` (asia-northeast1,
   `30 0 * * *`) triggered at `2026-07-17T00:30:01.895849Z` as expected. But
   `gs://central-element-323112-honest-coverage/2026-07-17/` never got created — the most recent date folder remained
   `2026-07-16/`, hours after the trigger fired.
2. **The launcher execution failed outright.** `gcloud run jobs executions list --job=honest-coverage-daily-launcher`
   showed `honest-coverage-daily-launcher-bq9bc` (started `00:30:05Z`, completed `00:30:48Z`) with `STATUS=False` —
   contrasted with the prior two nights (`-hglq4` 07-16, `-5fmn7` 07-15), both `STATUS=True`. A regression specific to
   tonight's run, not a chronic failure.
3. **Root cause, from Cloud Logging** (`resource.labels.job_name="honest-coverage-daily-launcher"`):
   ```
   Copying gs://deployment-scripts-central-element-323112/vm/launch-measure-honest-coverage-vm.sh...
   /tmp/launcher.sh: line 50: /tmp/lib/launcher_common.sh: No such file or directory
   Container called exit(1).
   ```
   The Cloud Run job's container command (confirmed via `gcloud run jobs describe ... --format=yaml`) is:
   ```
   gsutil cp gs://deployment-scripts-{pid}/vm/launch-measure-honest-coverage-vm.sh /tmp/launcher.sh
     && chmod +x /tmp/launcher.sh && bash /tmp/launcher.sh
   ```
   — a single-file fetch. But `launch-measure-honest-coverage-vm.sh` line 50 does
   `source "$(dirname script)/lib/launcher_common.sh"` — a dependency introduced fleet-wide across every `launch-*.sh`
   script by `deployment-service@b5bd336` ("roll `lc_verify_tarball_freshness` guard out across the launch-*.sh fleet").
   The Cloud Run job's fetch command was never updated for this new dependency, AND
   `gs://deployment-scripts-central-element-323112/vm/lib/` did not exist in GCS AT ALL (`gcloud storage ls` on that
   prefix returned "matched no objects") — the local repo's `scripts/vm/lib/{launcher_common.sh,aws_ec2_launch_lib.sh}`
   had never been published there.
4. **Why tonight specifically:** this plan's own P1 INFRA fix earlier on 2026-07-16 (`deployment-service@4f10b9b`,
   "nightly cron launcher e2-standard-4 (16GB) -> e2-highmem-4 (32GB)") did a **targeted single-file** manual upload of
   `launch-measure-honest-coverage-vm.sh` to GCS (the full `create-code-tarballs.sh` republish was — and remains —
   blocked by an unrelated dirty `terraform.tfvars` in this same repo; see the sibling issue doc). That upload put a
   version of the script with the (pre-existing, unrelated) `source lib/launcher_common.sh` line into GCS for the first
   time via this path. The 07-16 00:30 UTC cron fire happened BEFORE that 08:36Z upload, so it ran the old script (still
   succeeded, just under-provisioned). The 07-17 00:30 UTC fire was the FIRST time the newly-uploaded script actually
   ran for real — and it immediately hit the missing dependency.

## The fix (verified end-to-end)

1. Uploaded `scripts/vm/lib/launcher_common.sh` + `scripts/vm/lib/aws_ec2_launch_lib.sh` (already present in the local
   `deployment-service` checkout, just never published) to `gs://deployment-scripts-central-element-323112/vm/lib/`.
2. Updated the Cloud Run job's fetch command (both imperatively via `gcloud run jobs update`, verified working
   immediately, AND in the Terraform source `terraform/gcp/honest_coverage_scheduler.tf` — which the file's own header
   comment declares as the IaC SSOT for this resource — so a future `terraform apply` doesn't silently revert the fix)
   to also `mkdir -p /tmp/lib && gsutil -m cp -r 'gs://.../vm/lib/*' /tmp/lib/` before running the script.
   `deployment-service@6c7a079e1`.
3. Manually re-triggered the job (`gcloud run jobs execute honest-coverage-daily-launcher`) — first attempt (before the
   Cloud Run job command fix, GCS-lib-upload only) still failed identically, confirming the job's OWN command was the
   real gap, not just a missing file. Second attempt (after the command fix) succeeded in 41s.
4. Confirmed `gs://central-element-323112-honest-coverage/2026-07-17/coverage.json` was written:
   `asset_groups_measured: [cefi, defi, tradfi, sports, prediction]` (all 5), `partial: false`,
   `generated_at: 2026-07-17T09:09:21Z` — exactly this plan's P1 acceptance criterion.

## Blast radius (checked, not exhaustive)

Sampled two other nightly Cloud Run jobs with a similar naming pattern (`expected-universe-v2-defi`,
`lifecycle-catalogue-regen-defi`) — both run a **baked container image** (`/app/instruments-service/scripts/...`) rather
than fetching a shell script from GCS at runtime, so they do NOT share this failure mode. The
"fetch-a-launch-*.sh-script-and-bash-it" Cloud Run job pattern appears specific to `honest-coverage-daily-launcher`
among the jobs checked; a full audit of every Cloud Run job using this pattern was NOT performed (out of scope for this
continuation session) — if any other job uses the same single-file-fetch pattern against a `launch-*.sh` script that now
sources `lib/launcher_common.sh`, it would have the identical bug.

## Follow-up (not done here, flagging for whoever next touches deployment-service's fleet launcher tooling)

- Audit every Cloud Run Job definition for the same single-file-fetch-and-bash pattern against any `launch-*.sh` fleet
  script, now that the fleet rollout (`b5bd336`) added a shared-lib dependency to all of them.
- The still-BLOCKED full tarball republish (dirty `terraform/services/features-service-sports/gcp/terraform.tfvars`,
  foreign live WIP throughout this session) would have caught this class of drift automatically via
  `create-code-tarballs.sh`'s full-fleet publish — once that's unblocked, re-run it to confirm no other lib-dependency
  gaps exist.

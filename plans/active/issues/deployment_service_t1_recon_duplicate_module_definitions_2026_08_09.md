---
doc_type: issue
title: >-
  deployment-service terraform: cefi/prediction instruments-service T+1-recon jobs are managed by TWO conflicting module
  definitions, both targeting the same live Cloud Run job
summary: >-
  Discovered mid-apply while landing the reviewed prod terraform plan
  (deployment_service_prod_terraform_drift_2026_08_07.md). `terraform/gcp/audit03_cron_provisioning.tf` declares
  `module.instruments_cefi_t1_recon_job` and `module.instruments_prediction_t1_recon_job` (singular, imported via
  `_imports_reconcile.tf:109-118`), while the newer `terraform/gcp/t1_recon_instruments_jobs.tf` (2026-07-26, its own
  header comment) declares a for_each `module.t1_recon_instruments_job["cefi"|"prediction"|"defi"|"tradfi"]` that ALSO
  targets the identical two physical Cloud Run jobs (`uts-prod-instruments-service-cefi-t1-recon`,
  `...-prediction-t1-recon` — same `id`, confirmed via live plan output) for the cefi/prediction pair, with different
  `labels`/`service_name` values. Both definitions are live in the repo simultaneously; nothing removed the old one when
  the new for_each was added. A live `ENV=prod tofu apply` run today applied the NEW definition's labels via `-target`;
  the OLD definition's plan diff is still pending and would flip the labels back on any future untargeted `apply`,
  oscillating forever between the two Terraform-visible desired states. Confirmed no functional consumer reads the
  affected labels/service_name (grepped app code + the triggering scheduler, which references jobs by physical `name`,
  unaffected) — this is a real, live-verified SSOT contradiction in the IaC but not an active production hazard. Not
  fixed in this pass; needs an explicit call on which definition is canonical before removing the other via `terraform
  state rm` + code deletion.
status: open
nature: issue
asset_group:
  [infrastructure] # corrected 2026-08-10 (/ag-closeout-audit cross-cutting) -- was [cross-cutting]. Content is a
  # live-verified Terraform/OpenTofu duplicate-module-definition bug (deployment-service IaC hygiene) -- its own
  # parent doc (deployment_service_prod_terraform_drift_2026_08_07.md) is already dispositioned `infrastructure`
  # in this hub's own "Known non-orphan dispositions" section; this same-day sibling matches that precedent.
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [terraform, opentofu, prod, iac, ssot-contradiction, instruments-service, duplicate-resource]
related:
  [
    /plans/active/issues/deployment_service_prod_terraform_drift_2026_08_07.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
author: interactive-session
parent_epic: infrastructure_master
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: infra
assigned_vm: NA
execution_scope: local-only
drift_direction: correct-infra
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Discovered live 2026-08-09 while running the operator-authorized prod terraform apply from
  deployment_service_prod_terraform_drift_2026_08_07.md — a `-target`ed apply run against
  `module.t1_recon_instruments_job["cefi"]` succeeded and reported a real attribute diff (labels/service_name), which
  prompted checking whether the target resource address was correct; comparing it against the plan's OTHER pending entry
  for the same physical job under a different Terraform address (`module.instruments_cefi_t1_recon_job`) surfaced the
  duplication.
context_scope:
  [
    deployment-service/terraform/gcp/audit03_cron_provisioning.tf,
    deployment-service/terraform/gcp/t1_recon_instruments_jobs.tf,
    deployment-service/terraform/gcp/_imports_reconcile.tf,
    deployment-service/terraform/gcp/t1_batch_scheduler.tf,
  ]
---

# Two Terraform module definitions manage the same live cefi/prediction T+1-recon Cloud Run jobs

## What was found

`terraform/gcp/audit03_cron_provisioning.tf:214` declares `module "instruments_cefi_t1_recon_job"` and `:261` declares
`module "instruments_prediction_t1_recon_job"` — each a standalone (non-for_each) module, imported into state via
`_imports_reconcile.tf:109-118`'s `import { to = module.instruments_cefi_t1_recon_job..., id = ... }` blocks. Both carry
detailed, forensic comments documenting a real live OOM investigation (2cpu/4Gi and 4cpu/8Gi both OOM'd; 8cpu/16Gi
verified working) — this was clearly a deliberate, careful piece of IaC written to stop a real production incident.

`terraform/gcp/t1_recon_instruments_jobs.tf` (added later, per its own header comment framing it as "codifying"
previously-ad-hoc job definitions) declares `module "t1_recon_instruments_job"` with `for_each` over 4 asset groups
(`defi`, `tradfi`, `cefi`, `prediction`). Its `cefi`/`prediction` entries carry the **identical** cpu/memory values
(8cpu/16Gi) as the older module — strongly suggesting whoever wrote this for_each block copied the verified specs from
the older module rather than re-deriving them, while standardizing the labeling scheme (`purpose="t1-recon"`,
`asset_group="<ag>"`) instead of the older module's bespoke labels (`purpose="t1-batch-cefi"`,
`finding="cefi-monotonicity-guard-alerting-2026-07-07"`).

**Both module addresses resolve to the exact same physical GCP resource** — confirmed via the live plan output, which
shows identical `id`/`name` fields
(`projects/central-element-323112/locations/asia-northeast1/jobs/uts-prod-instruments-service-cefi-t1-recon`) under both
`module.instruments_cefi_t1_recon_job.google_cloud_run_v2_job.job` and
`module.t1_recon_instruments_job["cefi"].google_cloud_run_v2_job.job`. `defi`/`tradfi` are NOT duplicated — the old
module file only ever covered cefi/prediction, so the for_each's other two entries are the sole owner there.

## What happened during today's apply

The live job's labels, before today, matched the OLD module's declared values (`purpose="t1-batch-cefi"`,
`service="instruments-service"`) — meaning at some point the OLD module was the one actually applied last.
`deployment_service_prod_terraform_drift_2026_08_07.md`'s reviewed plan included both `t1_recon_instruments_job`
for_each entries in its "7 routine in-place updates" (label/tag sync) category. Running that targeted apply flipped the
live cefi/prediction jobs' labels to the NEW module's values (`purpose="t1-recon"`,
`service="instruments-service-cefi-t1-recon"`). A fresh `tofu plan` immediately after still shows the OLD module's
entries as pending (wanting to flip labels back) — because that address was correctly excluded via `-target` this time.
**If anyone runs a plain untargeted `tofu apply` in the future, it will flip these two jobs' labels back to the old
scheme, and the NEXT apply after that would flip them forward again** — an unbounded oscillation, not a one-time drift.

## Why this wasn't escalated as an emergency

Checked for functional dependents before writing this up:

- Grepped all `.py` app code for the old labels (`t1-batch-cefi`, `t1-batch-prediction`) — zero matches. Nothing reads
  these labels at runtime.
- The triggering Cloud Scheduler jobs (`t1_batch_scheduler.tf:98-105`, keys `instruments-cefi`/`instruments-prediction`)
  reference the job by its physical `name` string, which is IDENTICAL and unaffected across both module definitions —
  the scheduler will keep firing the right job regardless of which side "wins" a given apply.

So this is a real, live-verified Infrastructure-as-Code correctness bug (two SSOTs for one resource, silently
oscillating labels), but not a current production hazard. It deserves a deliberate fix, not a panic response.

## What needs an explicit call before fixing

Removing the duplicate requires deciding which module is canonical — this is a judgment call, not a mechanical cleanup,
because:

1. The OLD module's finding-specific label (`finding="cefi-monotonicity-guard-alerting-2026-07-07"`) may be
   intentionally referenced by a monitoring/alerting query or dashboard filter elsewhere (not found in this repo's own
   `.tf`/`.py` in a quick grep, but worth a dedicated check before deleting — Slack alert routing configs, saved Cloud
   Monitoring dashboards, or BigQuery label-based cost queries could live outside this repo's grep surface).
2. Whichever module is removed needs its `import` block (if the surviving one is the NEW for_each) or its for_each entry
   (if the surviving one is the OLD module) cleaned up too, plus a `terraform state rm` on the losing address done
   BEFORE removing its `.tf` block (removing the block first with the address still in state would plan a DESTROY of the
   live job, not just an untrack).
3. `defi`/`tradfi` have no old-style counterpart, so whatever the resolution, the for_each module structure likely
   survives in some form — the cleanest fix is probably removing the 2 OLD singular modules + their 2 import blocks,
   keeping the for_each as sole owner of all 4 asset groups uniformly. This is a recommendation, not a ruling.

## Todos

- [ ] [OPERATOR] P2. Confirm the old `audit03_cron_provisioning.tf` labels (`purpose=t1-batch-{cefi,prediction}`,
      `finding=cefi-monotonicity-guard-alerting-2026-07-07`) have no external consumer (dashboards/alert routing/cost
      queries outside this repo), then approve removing `module.instruments_cefi_t1_recon_job` +
      `module.instruments_prediction_t1_recon_job` + their 2 `_imports_reconcile.tf` import blocks, leaving
      `t1_recon_instruments_jobs.tf`'s for_each as sole owner of all 4 asset groups — or state a different resolution if
      the old labels matter and should be adopted into the for_each's label scheme instead.
- [ ] [SCRIPT] P3. Once the above is ruled, execute: `tofu state rm` on the losing module address(es) BEFORE deleting
      their `.tf` block (state-rm-then-delete-code, never delete-code-then-plan, to avoid an accidental destroy plan on
      a live job), remove the corresponding `import` blocks from `_imports_reconcile.tf`, then verify a fresh
      `tofu plan` shows zero diff for these 2 jobs.

## Progress Log

- **2026-08-09**: found live, mid-apply, while executing the operator-authorized prod terraform apply from
  `deployment_service_prod_terraform_drift_2026_08_07.md`. Confirmed both module addresses target the identical physical
  resource via live plan `id` comparison; confirmed no functional consumer of the conflicting labels via grep of app
  code + the triggering scheduler's job-reference mechanism (by name, not label). Filed as its own issue rather than
  folded into the terraform-drift doc, since the root cause (a genuinely separate, pre-existing IaC duplication bug) is
  unrelated to that doc's meta-watchers finding — this doc tracks a different defect discovered as a side effect of
  applying that one. Not fixed — needs an explicit operator call on canonical-definition choice before any state
  surgery, per the findings-triage rule for ambiguous ownership calls.

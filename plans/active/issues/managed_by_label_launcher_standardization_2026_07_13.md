---
doc_type: issue
title: Standardize a `managed-by` launcher label so deployment-api can echo managed_by provenance
summary:
  The full-estate cost-provenance plan (deployment_full_estate_cost_provenance_2026_07_09, archived 2026-07-13) deferred
  the `managed_by_label` field on the deployment inventory item — a `labels`-derived `managed_by` echo is a no-op until
  VM/Cloud-Run launchers emit a standardized `managed-by` label. The classification already exposes `launched_by`
  provenance (adhoc / control-plane / fleet-reconciliation) which covers the REVIEW parity check; this issue tracks the
  remaining DEVOPS piece — a launcher-side `managed-by` label convention that deployment-api would then surface as
  `managed_by`.
status: open
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, deployment-api]
scope: [engineer, admin]
tags: [observability, deployment, provenance, devops, infrastructure]
related: [plans/archive/2026_07/deployment_full_estate_cost_provenance_2026_07_09.md]
created: 2026-07-13
parent_epic: observability_master
priority: P3
assigned_vm: planning
resolved_by:
locked_by:
context_scope:
  [
    /plans/archive/2026_07/deployment_full_estate_cost_provenance_2026_07_09.md,
    deployment-service/scripts/vm/lib/launcher_common.sh,
    deployment-api/deployment_api/routes/deployments_inventory.py,
    deployment-api/deployment_api/routes/_aws_deployments.py,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
source: [deployment_full_estate_cost_provenance_2026_07_09 DEFERRED managed_by_label item]
last_updated: 2026-07-31
---

# `managed-by` launcher label standardization (deferred from cost-provenance)

> **Migrated from** `deployment_full_estate_cost_provenance_2026_07_09.md` on archival (2026-07-13). The parent plan
> shipped `launched_by` provenance (adhoc / control-plane / fleet-reconciliation, the REVIEW parity signal) and
> deliberately deferred `managed_by_label`: a `labels`-derived `managed_by` echo on the deployment inventory item is a
> no-op until launchers emit a standardized label. Captured here so the deferral is not lost.

## The gap

- deployment-api's deployment inventory item can carry a `managed_by` field sourced from a VM/Cloud-Run **`managed-by`
  label**. Today no launcher emits that label consistently, so the field would always be blank — hence deferred (never a
  fabricated value).

## Work

- [x] ✅ [DEVOPS] P3. Standardize a `managed-by=<launcher>` label across the VM launchers
      (`deployment-service/scripts/vm/launch-*.sh`) + Cloud-Run job terraform, using the same launcher taxonomy as
      `launched_by`. — **deployment-service@db67173**. `lc_gcloud_create`/`aws_ec2_launch_lib.sh` already stamped
      `managed-by=deployment-service` centrally, but only ~9 launchers actually called those helpers; the other 137
      `launch-*.sh` scripts built their `gcloud compute instances create` call inline and never inherited the label.
      Appended `,managed-by=deployment-service` to every direct `--labels=` construction (132 files via a scripted
      transform on the exact `--labels=` value span, verified with `bash -n` on every touched file + `git diff` review;
      5 files that build the value in a `labels`/`LABELS` variable, edited at the assignment site instead). Skipped
      `launch-deribit-dvol-backfill-vm.sh` + `launch-planning-vm.sh` (already carried their own deliberate `managed-by`
      value). Also added the missing `labels` block (`managed-by=terraform`) to the one `google_cloud_run_v2_job`
      resource in `terraform/gcp/` that had none (`vm_log_archival_scheduler.tf`) — every other Cloud-Run job (via the
      `container-job` module or hand-declared) already carried it; `tofu validate` clean.
- [ ] [BACKEND] P3. Once the label is standardized, wire the `managed_by` echo in the deployment-api inventory item (the
      `labels` read is already scaffolded) + a unit asserting the round-trip. — **deployment-api**

## Notes

- Low priority: `launched_by` already answers the operator's "who launched this / is it unmanaged" question; this is the
  label-echo refinement, not a data-correctness gap.

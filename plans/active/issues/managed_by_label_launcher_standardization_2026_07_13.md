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
asset_group: [cross-cutting]
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
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
source: [deployment_full_estate_cost_provenance_2026_07_09 DEFERRED managed_by_label item]
last_updated: 2026-07-13
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

- [ ] [DEVOPS] P3. Standardize a `managed-by=<launcher>` label across the VM launchers
      (`deployment-service/scripts/vm/launch-*.sh`) + Cloud-Run job terraform, using the same launcher taxonomy as
      `launched_by`. — **deployment-service**
- [ ] [BACKEND] P3. Once the label is standardized, wire the `managed_by` echo in the deployment-api inventory item (the
      `labels` read is already scaffolded) + a unit asserting the round-trip. — **deployment-api**

## Notes

- Low priority: `launched_by` already answers the operator's "who launched this / is it unmanaged" question; this is the
  label-echo refinement, not a data-correctness gap.

---
doc_type: issue
title: >-
  deployment-api's reap_stale() callers share the same empty-set-on-API-failure over-reap bug fixed in
  deployment-service (registry false-reap sibling)
summary: >-
  While investigating Finding 3 of
  `cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31.md` (the false `vm_not_running`
  reap of a genuinely-RUNNING VM at 2026-07-31T05:46:53Z), the root cause in deployment-service was the running-VM
  census collapsing an API failure/timeout into an empty list, which
  `DeploymentsRegistry.reap_stale(running_vm_names={})` read as "no VMs running" → `_reap_reason` classified EVERY
  stale-heartbeat active entry as `vm_not_running`. That fix shipped `deployment-service@4ee514e` (census returns `None`
  on failure; caller passes `running_vm_names=None` → heartbeat-age-only fallback). The SAME latent bug class exists in
  deployment-api's two `reap_stale()` callers — `deployment_api.vm_utils.list_running_vm_names` returns `set()` on
  failure and `deployment_api.services.sync_service.reap_stale_deployments` passes it straight through, and
  `deployment_api.routes.vm_deployments.reconcile_vm_deployments` derives `running_vm_names` from
  `get_vm_instance_details` which degrades to an empty map on failure. Not fixed in this task because deployment-api is
  outside the batch4 plan's repo scope.
status: open
nature: issue
asset_group: [cefi, meta]
stage: [data, meta]
repos: [deployment-api]
scope: [engineer, admin]
tags: [cefi, deployment-registry, reaper, vm-monitoring, reliability, data-pipeline]
related:
  [
    cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
  ]
created: 2026-08-06
author: slot-4-worker
priority: P2
parent_epic: cefi_master
source:
  "cefi_satellite_ao_dispatch_batch4-003 (slot 4, 2026-08-06) — sibling finding produced while fixing
  cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31.md Finding 3"
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/issues/cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31.md,
    deployment-api/deployment_api/vm_utils.py,
    deployment-api/deployment_api/services/sync_service.py,
    deployment-api/deployment_api/routes/vm_deployments.py,
  ]
---

# deployment-api reap_stale() empty-set over-reap sibling

## What I found

Root-causing Finding 3 of `cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31.md` (the
2026-07-31T05:46:53Z false `vm_not_running` reap of a still-RUNNING VM) identified the mechanism: a running-VM census
that collapses an API failure/timeout into an empty list, passed to
`DeploymentsRegistry.reap_stale(running_vm_names={})`, makes `_reap_reason` classify EVERY stale-heartbeat active entry
as `vm_not_running` (an empty non-None set reads as "no VMs running"). The deployment-service fix shipped
`deployment-service@4ee514e`.

The same latent bug exists in deployment-api, in TWO `reap_stale()` callers (verified by reading the code 2026-08-06):

1. `deployment_api/services/sync_service.py` → `reap_stale_deployments()` (the periodic background-sync reaper):

   ```python
   running_vm_names = list_running_vm_names(self.project_id)   # vm_utils
   reaped = registry.reap_stale(running_vm_names=running_vm_names, max_reap=max_reap)
   ```

   `deployment_api/vm_utils.py:list_running_vm_names` returns `set()` on ANY exception (including the
   `_RPC_TIMEOUT_SEC=30` deadline) — so a transient list-API failure/timed-out RPC is passed as an empty set,
   over-reaping every stale-heartbeat registration.

2. `deployment_api/routes/vm_deployments.py` → `reconcile_vm_deployments()` (the admin reconcile endpoint):
   ```python
   vm_details = get_vm_instance_details(project_id)             # degrades to {} on failure
   running_vm_names = {name for name, details in vm_details.items() if details.get("status") == "RUNNING"}
   reaped = registry.reap_stale(running_vm_names=running_vm_names)
   ```
   `get_vm_instance_details` degrades to an empty detail map on failure (`_RPC_TIMEOUT_SEC` deadline included), so
   `running_vm_names = {}` on a transient failure → same over-reap.

Both are the exact same mechanism the deployment-service fix closes: **an unavailable census must be passed as
`running_vm_names=None` (→ heartbeat-age-only fallback in `_reap_reason`), never as an empty set.**

## Why it matters

`deployment-api`'s background-sync reaper is the standing periodic sweep that reconciles `deployments/active/` against
live GCE state. A transient GCE aggregated-list failure/timeout (bounded to 30s by `_RPC_TIMEOUT_SEC`, so the sync loop
keeps running) would falsely archive every stale-heartbeat registration as
`status=failed, exit_code=125, reap_reason=vm_not_running` — the same registry-corruption Finding 3 documented for
deployment-service (relaunch-budget bookkeeping + any dashboard reading the registry as ground truth). The endpoint
version (2) can do it on demand during a failure window.

## Recommended decision

- [x] ✅ [BACKEND] P2. Make deployment-api's two `reap_stale()` callers distinguish "census unavailable" from "census
      healthy and empty" and pass `running_vm_names=None` (not `{}`) to `DeploymentsRegistry.reap_stale()` on API
      failure, mirroring the deployment-service fix (`deployment-service@4ee514e`): change
      `deployment_api/vm_utils.py:list_running_vm_names` to return `set[str] | None` (None on failure) and update
      `deployment_api/services/sync_service.py:reap_stale_deployments` to pass `running_vm_names=None` when unavailable;
      for `deployment_api/routes/vm_deployments.py:reconcile_vm_deployments`, treat an empty/failed
      `get_vm_instance_details` the same way (pass None). Add regression tests that a transient list-API failure does
      NOT reap a stale-heartbeat registration as `vm_not_running` (heartbeat-age-only fallback). **Done when**: both
      callers pass None on census unavailable, regression tests cover the failure path, QG green. Repo: deployment-api —
      deployment-api@3e1d3fa.

## Progress Log

- 2026-08-06 (slot 8, data_engineering worker, deployment_api_reaper_empty_set_over_reap_sibling-001): shipped fix —
  deployment-api@3e1d3fa. Changed `list_running_vm_names` → returns `set[str] | None` (None on failure);
  `get_vm_instance_details` → returns `dict | None` (None on failure). Updated both callers
  (`sync_service.reap_stale_deployments` and `routes.vm_deployments.reconcile_vm_deployments`) to pass
  `running_vm_names=None` when census is unavailable. Updated `_compute_vm_deployments` and `get_vm_deployment` to
  degrade `None`→`{}`. Added 4 regression tests: census-unavailable→None in reconcile endpoint,
  census-available/None/empty-set in sync_service reaper. QG green, 85/85 tests pass.
- 2026-08-06 (slot 4, cefi_satellite_ao_dispatch_batch4-003): filed as the sibling finding to
  `cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31.md` Finding 3 — the
  deployment-service root cause + fix is in that doc's item 2 (shipped `deployment-service@4ee514e`); deployment-api's
  same-shaped latent bug is tracked here since it is outside the batch4 plan's repo scope
  (`[unified-trading-pm, unified-trading-library, deployment-service, market-tick-data-service, market-data-processing-service, instruments-service]`).

---
doc_type: issue
title: "DP-VM-002: pipelinecheck VMs fire DP_VM_GONE_NO_CAPTURE false positives — not exempted by writes_shard_for_vm"
created: 2026-08-21
author: data_pipeline_alerts_reconciler (slot 27)
parent_epic: observability_master
assigned_vm: planning
source:
  - DP-VM-002
  - data_pipeline_alerts_reconcile 2026-08-21
locked_by:
summary: >-
  Pipeline-check VMs (mtds-backfill-*-pipelinecheck-*, instr-backfill-defi-pchk-*)
  fire DP_VM_GONE_NO_CAPTURE (CRITICAL, page_operator) every run because
  captured stays at 0 → 0 — they verify pipeline health, never write data.
  The exit_code_fleet_monitor has exemptions for LIVE VMs and heartbeat-only
  VMs (vm_prefix_registry.VM_PREFIX_TO_BUCKET with bucket=None), but
  pipelinecheck prefixes are not registered there, so writes_shard_for_vm
  returns True (assume shard-capable) and the EXPECTED_NO_CAPTURE exemption
  does not gate them.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-service, unified-api-contracts]
scope: [engineer]
tags: [data-pipeline, dp-alerts, dp-vm-002, false-positive, pipelinecheck, vm-zombie-watchdog]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
priority: P2
resolved_by:
execution_scope: orchestrator-agent
drift_direction: fix-code
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
  ]
---

# DP-VM-002: pipelinecheck VMs fire DP_VM_GONE_NO_CAPTURE false positive

## Evidence

17 DP_VM_GONE_NO_CAPTURE alerts in 24h, ALL for pipelinecheck VMs:
- `mtds-backfill-sports-pipelinecheck-*` (2 VMs)
- `mtds-backfill-cefi-pipelinecheck-*` (5 VMs)
- `mtds-backfill-tradfi-pipelinecheck-*` (1 VM)
- `instr-backfill-defi-pchk-*` (1 VM)

Every alert shows `(0 → 0)` and "no rows-written / honest-absence / rate-limit signal"
— by construction, since pipelinecheck VMs test pipeline wiring, not data capture.

## Root cause

`exit_code_fleet_monitor` gates DP_VM_GONE_NO_CAPTURE via `writes_shard_for_vm`
(which resolves against `vm_prefix_registry.VM_PREFIX_TO_BUCKET`). Pipelinecheck
prefixes are not registered in that mapping, so the resolver defaults to `True`
(assume shard-capable), and the EXPECTED_NO_CAPTURE exemption does not fire.

## Fix

Register pipelinecheck VM prefixes in `VM_PREFIX_TO_BUCKET` with `bucket=None`
(heartbeat-only pattern, same as `cefi-fwd-daily-cron-*`). This makes
`writes_shard_for_vm` return `False`, which gates `EXPECTED_NO_CAPTURE`
and suppresses the alert. Repo: unified-api-contracts (registry definition).

---
doc_type: issue
title: "DP-VM-009: DP_VM_PREEMPTED_NO_RELAUNCH alert body contains no diagnostic detail — VM name, reason, and stderr are missing from Slack"
created: 2026-08-21
author: data_pipeline_alerts_reconciler (slot 27)
parent_epic: observability_master
assigned_vm: planning
source:
  - DP-VM-009
  - data_pipeline_alerts_reconcile 2026-08-21
locked_by:
summary: >-
  DP_VM_PREEMPTED_NO_RELAUNCH Slack messages contain only the event name with
  zero diagnostic detail — no VM name, no failure reason, no return code, no
  stderr. The emitting code (relaunch_backfill_vm.py) populates all these fields
  in the event details dict, but they are not rendered into the Slack message body.
  This makes 17 alerts in 24h completely unactionable from the channel alone.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [data-pipeline, dp-alerts, dp-vm-009, alert-text, preempted-no-relaunch, slack]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
priority: P3
resolved_by:
execution_scope: orchestrator-agent
drift_direction: fix-code
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    deployment-service/scripts/recovery/relaunch_backfill_vm.py,
    deployment-service/deployment_service/data_pipeline_monitors/escalation.py,
  ]
---

# DP-VM-009: DP_VM_PREEMPTED_NO_RELAUNCH alert body is empty

## Evidence

17 DP_VM_PREEMPTED_NO_RELAUNCH messages in 24h. Every one renders as just:
```
[DP_VM_PREEMPTED_NO_RELAUNCH] DP_VM_PREEMPTED_NO_RELAUNCH
```
No VM name, no reason, no return code, no stderr — despite the emitting code
(`relaunch_backfill_vm.RelaunchPreemptedVm`) populating `details` with
`reason`, `returncode`, and `stderr` fields per the registry spec.

## Root cause

The actuator (`relaunch_backfill_vm.py`) self-emits the event directly rather
than routing through `escalation.py`'s detail-rendering path. The Slack message
template used for this direct emission does not interpolate the `details` fields
into the rendered body — it only includes the event name.

## Fix

Update the emission in `relaunch_backfill_vm.py` to include `details["reason"]`,
`details["vm_name"]`, `details["stderr"]` (if present) in the rendered Slack
message body. This is the same class of fix as the 2026-08-07 DP-DIGEST-003/004
mirror_live pattern — the event IS registered and fires correctly, but its
rendered text is misleadingly sparse. Repo: deployment-service.

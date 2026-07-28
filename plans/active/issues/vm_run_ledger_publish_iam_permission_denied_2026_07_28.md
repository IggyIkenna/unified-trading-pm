---
doc_type: issue
title: VM shutdown RUN_LEDGER_RECORDED publish hits IAM_PERMISSION_DENIED on run-ledger topic
summary: >-
  A VM launched via deployment-service's setup-data-pipeline-vm.sh (Pattern A) hit a 403 IAM_PERMISSION_DENIED on
  pubsub.topics.publish against the run-ledger topic during its clean shutdown sequence. The failure is post-completion
  observability telemetry only (the VM's actual task already exited rc=0 before this fired) and is generic VM-lifecycle
  shutdown code, not specific to any one plan -- likely affects every VM in this launcher family whose runtime identity
  lacks the publish grant. Recommended fix: grant pubsub.topics.publish on run-ledger to the affected service account.
status: open
nature: notes
asset_group: [meta]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [infra, observability, iam, vm-launcher]
related:
  [
    /plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md,
    /codex/05-infrastructure/deployment-observability.md,
  ]
created: 2026-07-28
parent_epic: infrastructure_master
assigned_vm: NA
priority: P2
source: [defi_dex_pool_symbol_fix_backfill_purge_2026_07_25]
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# VM shutdown RUN_LEDGER_RECORDED publish hits IAM_PERMISSION_DENIED

## What I found

While monitoring `mtds-dex-pools-symbolfix-batch2` (a scoped dex-pools backfill VM launched via
`deployment-service/scripts/vm/launch-mtds-dex-pools-backfill-vm.sh`, Pattern A / `setup-data-pipeline-vm.sh`), its
clean shutdown sequence logged:

```
2026-07-28 02:10:30,502 WARNING RUN_LEDGER_RECORDED publish failed: 403 User not authorized to perform this action.
  [reason: "IAM_PERMISSION_DENIED" ... permission: "pubsub.topics.publish" ... resource:
  "projects/central-element-323112/topics/run-ledger"]
```

This fired **after** the VM's actual work completed successfully (`command exited rc=0`,
`DEPLOYMENT_COMPLETED exit_code=0`) — it is the shutdown-time attempt to publish a completion record to the `run-ledger`
Pub/Sub topic (see `/codex/05-infrastructure/deployment-observability.md` § "Write path":
`resource-samples`/`run-ledger` topics + native BigQuery subscriptions). The publish call is wrapped so failure only
logs a WARNING and does not fail the deployment — this VM's real objective (the dex-pools backfill) was unaffected.

## Why it matters

This is generic VM-lifecycle shutdown code (not specific to dex-pools or this plan), so it likely affects **every** VM
launched via this same `setup-data-pipeline-vm.sh` / `vm-exec-with-gcs-tee.sh` family whose runtime identity lacks
`pubsub.topics.publish` on `projects/central-element-323112/topics/run-ledger`. If so, the `run-ledger` BigQuery-backed
observability record is silently missing for every affected run (a monitoring/analytics gap, not a data-correctness one
— the actual backfill/task work is unaffected).

## Recommended decision

- [ ] [INFRA] P2. **Grant `roles/pubsub.publisher` (or a scoped custom role with only `pubsub.topics.publish`) on the
      `run-ledger` topic** in `central-element-323112` to whichever service account the `setup-data-pipeline-vm.sh`
      family of VMs runs as (confirm via
      `gcloud compute instances describe <a-live-VM> --format='value(serviceAccounts)'` on a currently-running VM in
      this family, e.g. the standing `mtds-dex-pools-backfill`) — then verify by relaunching any cheap VM in this family
      and confirming the `RUN_LEDGER_RECORDED` line no longer WARNs.
- [ ] [SCRIPT] P3. **Grep whether other VM families in this fleet hit the same gap** (search `vm-logs/*/run.log`
      prefixes for `RUN_LEDGER_RECORDED publish failed` across other recent VM launches) to size whether this is
      isolated to the dex-pools launcher's identity or fleet-wide.

## Codex SSOTs

- `/codex/05-infrastructure/deployment-observability.md` — run-ledger write path.
- `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` — IAM self-service grant procedure (this is
  exactly the kind of ambient-identity permission gap that rule covers; a future worker touching this can self-grant
  rather than escalate, per the 2026-07-27 operator ruling).

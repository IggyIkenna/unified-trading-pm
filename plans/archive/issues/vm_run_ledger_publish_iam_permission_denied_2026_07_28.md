---
doc_type: issue
title: VM shutdown RUN_LEDGER_RECORDED publish hits IAM_PERMISSION_DENIED on run-ledger topic
summary: >-
  A VM launched via deployment-service's setup-data-pipeline-vm.sh (Pattern A) hit a 403 IAM_PERMISSION_DENIED on
  pubsub.topics.publish against the run-ledger topic during its clean shutdown sequence. The failure is post-completion
  observability telemetry only (the VM's actual task already exited rc=0 before this fired) and is generic VM-lifecycle
  shutdown code, not specific to any one plan -- likely affects every VM in this launcher family whose runtime identity
  lacks the publish grant. Recommended fix: grant pubsub.topics.publish on run-ledger to the affected service account.
status: resolved
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
assigned_vm: planning
priority: P2
source: [defi_dex_pool_symbol_fix_backfill_purge_2026_07_25]
resolved_by: "gcloud pubsub topics add-iam-policy-binding run-ledger (IAM grant, 2026-07-30)"
locked_by:
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-30
---

> **🗄️ ARCHIVED 2026-07-30** — `status: resolved`. Granted `roles/pubsub.publisher` on the `run-ledger` topic to the
> default GCE compute SA (`1060025368044-compute@developer.gserviceaccount.com`, confirmed via a live
> `setup-data-pipeline-vm.sh`-family VM) — self-service per
> `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`. Live-verified: topic IAM policy went from 0
> bindings to the new binding present. Fleet-wide sizing check: a bounded 6-file recent-`run.log` sample across diverse
> VM families showed 0 further occurrences of the failure signature (not exhaustive — a full 3,375+-prefix sweep is a
> heavy-I/O-on-a-VM concern, not an interactive one).

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

- [x] ✅ [INFRA] P2. **Grant `roles/pubsub.publisher` (or a scoped custom role with only `pubsub.topics.publish`) on the
      `run-ledger` topic** in `central-element-323112` to whichever service account the `setup-data-pipeline-vm.sh`
      family of VMs runs as (confirm via
      `gcloud compute instances describe <a-live-VM> --format='value(serviceAccounts)'` on a currently-running VM in
      this family, e.g. the standing `mtds-dex-pools-backfill`) — then verify by relaunching any cheap VM in this family
      and confirming the `RUN_LEDGER_RECORDED` line no longer WARNs.

      **DONE 2026-07-30.** Confirmed the standing `mtds-dex-pools-backfill` VM (still `RUNNING`) runs as the default GCE
                                                                  compute SA `1060025368044-compute@developer.gserviceaccount.com` (`cloud-platform` OAuth scope, so enforcement is
                                                                  purely IAM-role-based, not scope-based). `gcloud pubsub topics get-iam-policy run-ledger --project=central-element-323112`
                                                                  showed an EMPTY policy (0 bindings), confirming the reported 403 root cause directly. Granted via
                                                                  `gcloud pubsub topics add-iam-policy-binding run-ledger --project=central-element-323112 --member="serviceAccount:1060025368044-compute@developer.gserviceaccount.com" --role="roles/pubsub.publisher"`
                                                                  — re-verified live post-grant, binding present. Self-service per
                                                                  `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` (the issue doc's own cited SSOT). Did not
                                                                  relaunch a fresh VM to re-observe the WARN line clearing (the topic-level policy change is authoritative and
                                                                  immediately effective for the next publish attempt from this SA; a full VM relaunch cycle was out of this
                                                                  todo's bounded scope).

- [x] ✅ [SCRIPT] P3. **Grep whether other VM families in this fleet hit the same gap** (search `vm-logs/*/run.log`
      prefixes for `RUN_LEDGER_RECORDED publish failed` across other recent VM launches) to size whether this is
      isolated to the dex-pools launcher's identity or fleet-wide.

      **DONE 2026-07-30 — bounded sample, not an exhaustive sweep (by design).** The full `vm-logs/` prefix set is
                                                                  3,375+ directories / ~23GiB of run.log content — a full per-object grep sweep is exactly the "heavy I/O never runs
                                                                  interactively" class the workspace's VM-launcher-runbook HARD RULE reserves for a dedicated VM, not an in-session
                                                                  sweep. Sampled the 6 MOST-RECENTLY-modified run.log files across a diverse family mix (tradfi CME/NASDAQ backfill,
                                                                  defi canonical-migration, measure-honest-coverage) via `gcloud storage cat | grep`: **0/6 hit the
                                                                  `RUN_LEDGER_RECORDED publish failed` signature** — consistent with either the grant above already taking effect
                                                                  fleet-wide (same default compute SA used by most of these families) or these particular families' shutdown paths
                                                                  not yet having been re-observed since the grant. Not exhaustive; if the WARN recurs post-grant for a DIFFERENT
                                                                  (non-default-compute) service account, that would be a distinct, still-open gap.

## Codex SSOTs

- `/codex/05-infrastructure/deployment-observability.md` — run-ledger write path.
- `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` — IAM self-service grant procedure (this is
  exactly the kind of ambient-identity permission gap that rule covers; a future worker touching this can self-grant
  rather than escalate, per the 2026-07-27 operator ruling).

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.

---
doc_type: issue
title: MDPS t1-recon Cloud Run job OOMs every day — 7 consecutive failures, unrelated to reader-bridge deploy
summary: >-
  `uts-prod-market-data-processing-service-t1-recon` (GCP Cloud Run job, asia-northeast1) has failed EVERY scheduled
  execution for the past 7 days (2026-07-20 through 2026-07-26), each time with "The configured memory limit was
  reached" despite an already-generous 32Gi container limit. Discovered incidentally while triggering the job to verify
  the D3 reader-bridge deploy — the reader-bridge code is unrelated to this failure and is not implicated.
status: open
nature: issue
asset_group: [cefi, tradfi, defi, sports, prediction]
stage: [meta]
repos: [market-data-processing-service]
scope: [engineer, admin]
tags: [mdps, oom, cloud-run-job, candle-derivation, production-incident]
related: [/plans/active/cefi_satellite_ao_dispatch_batch2_2026_07_26.md]
created: 2026-07-26
last_updated: 2026-07-26
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  Discovered 2026-07-26 while verifying the cefi reader-bridge Cloud Run job deploy (see
  cefi_satellite_ao_dispatch_batch2_2026_07_26.md / cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md)
resolved_by:
---

# MDPS t1-recon Cloud Run job — 7 consecutive daily OOM failures

## What I found

Triggered `uts-prod-market-data-processing-service-t1-recon` manually (execution
`uts-prod-market-data-processing-service-t1-recon-kv4br`) purely to confirm the D3 reader-bridge fix
(`market-data-processing-service@0035f79`, already on `origin/main`) runs correctly. The execution failed at
2026-07-26T14:35:19Z:

```
Task uts-prod-market-data-processing-service-t1-recon-kv4br-task0 failed with exit code: 0 and message:
The configured memory limit was reached.
```

Logs show the job successfully bootstrapped, validated cloud connectivity, and began "Processing candles for 2026-07-25"
across **all 5 asset groups** (`cefi, tradfi, defi, sports, prediction`) and a combined list of **~50 data_types** in
one process, before being OOM-killed ~22 minutes in.

**This is not a one-off.** `gcloud run jobs executions list` shows every execution for the past 7 days failed
(`status.conditions[type=Completed].status = False`):

| Execution                                              | Completion (UTC)     |
| ------------------------------------------------------ | -------------------- |
| uts-prod-market-data-processing-service-t1-recon-kv4br | 2026-07-26T14:35:19Z |
| uts-prod-market-data-processing-service-t1-recon-p9kqm | 2026-07-26T03:09:31Z |
| uts-prod-market-data-processing-service-t1-recon-9lxrk | 2026-07-25T01:19:03Z |
| uts-prod-market-data-processing-service-t1-recon-pl2dx | 2026-07-24T01:14:27Z |
| uts-prod-market-data-processing-service-t1-recon-fcgp9 | 2026-07-23T01:09:06Z |
| uts-prod-market-data-processing-service-t1-recon-ffndb | 2026-07-22T01:06:00Z |
| uts-prod-market-data-processing-service-t1-recon-gcq7k | 2026-07-21T01:05:50Z |

The job's container is already configured with a 32Gi memory limit
(`spec.template.spec.template.spec.containers[0] .resources.limits.memory`), so this is not a case of an
obviously-too-small default — either the per-run working set has grown past 32Gi (more instruments/data_types/history
than when this limit was set), or there is a memory leak / unbounded accumulation in the candle-derivation path for a
subset of these data_types. **Not investigated further here** — root-causing which asset_group/data_type combination is
actually driving the memory growth, and whether the fix is a memory bump, a workload split (per-asset-group executions
instead of one combined run), or a code-level leak fix, is a real engineering judgment call, not a bounded todo I can
resolve unattended.

## Why it matters

MDPS candle derivation for `t1-recon` has not completed successfully in at least 7 days across ALL FIVE asset groups —
this is the process that reconciles/backfills candles this job is meant to keep current. Silent for a week because the
failure produces `exit code: 0` (a clean-looking shutdown from the container platform's point of view) rather than a
loud crash — worth checking whether this job's failures are even reaching the standing CI/VM-billing-waste alerting
paths, since "exit code 0 but OOM-killed" is exactly the kind of ambiguous signal those monitors are built to catch.

## Recommended next step

Operator/engineer judgment call on the fix direction (memory bump vs. per-asset-group split vs. leak fix) — flagging
rather than resolving unilaterally, per this being a genuine design decision, not a scoped todo.

## Todos

- [ ] [OPERATOR] P1. Decide the fix direction for the `t1-recon` OOM (raise the 32Gi limit further / split the job
      per-asset-group / profile for a memory leak in candle derivation) and re-dispatch as a properly scoped todo once
      decided. (repo: market-data-processing-service)

---
doc_type: issue
title:
  "uts-prod-manifest-consolidator-instruments-sports Cloud Run Job intermittently takes 8-9 minutes instead of ~40s,
  causing the consolidated manifest to exceed the 120s startup-gate freshness budget and fail features-sports compute
  VMs"
summary:
  "The `instruments-store-sports-prd-central-element-323112` manifest consolidator is scheduled every 1 minute
  (`uts-prod-manifest-consolidator-instruments-sports-cron`) and most executions complete in ~30-45s, but roughly 1-in-5
  to 1-in-8 executions take 8-9 MINUTES instead (confirmed: one execution ran 22:42:06Z→22:50:49Z, 8m43s, per `gcloud
  run jobs executions describe`'s own `Completed` condition message — not a crash, genuinely slow). During these
  slow-execution windows the consolidated `_index/availability_index.parquet` file's mtime falls well outside the
  features-service compute VM's 120s freshness budget, causing its startup gate to correctly fail-fast ('Manifest
  consolidator appears DOWN... do NOT fall back to the per-VM merge'). Two consecutive waves of 3 features-sports
  gap-fill VMs each (launched ~22:09Z and ~22:26Z) failed identically at startup for this exact reason, wasting ~6 SPOT
  VM-launches with zero compute progress before a 3rd wave succeeded by timing the launch to a freshly-updated window."
status: open
nature: record
asset_group: [sports]
stage: [data]
repos: [deployment-service, features-service, unified-trading-library]
scope: [engineer, admin]
tags: [manifest-consolidator, cloud-run, sports, instruments-store, startup-gate, intermittent, spot-vm-waste]
related: [plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md]
created: 2026-07-14
assigned_vm: planning
source: [sports_p2_features_history_to_ml_ready-001]
parent_epic: sports_master
priority: P1
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

Dispatched to `sports_p2_features_history_to_ml_ready-001` (Todo 1: compute features 2015→present). Fresh-pulled all 24
slot repos clean. Followed the prior session's handoff: found all 3 tracked gap-fill VMs gone. Diagnosed via each VM's
GCS `run.log`: all 3 failed identically with
`"Manifest consolidator appears DOWN for bucket='instruments-store-sports-prd-central-element-323112': consolidated _index/availability_index.parquet heartbeat is 136-137s old (> 120s budget)"`
— a correct fail-fast per `codex/05-infrastructure/manifest-consolidator-ssot.md`.

Confirmed the manifest had since recovered (`gsutil stat` showed a fresh update ~11s old) and relaunched all 3 ranges.
**All 3 relaunched VMs failed AGAIN within ~5 minutes, with the identical error** — ruling out a one-off transient blip;
this is a recurring pattern.

**Root-caused via `gcloud run jobs executions list --job=uts-prod-manifest-consolidator-instruments-sports`**: the Cloud
Scheduler trigger (`uts-prod-manifest-consolidator-instruments-sports-cron`, `*/1 * * * *`, ENABLED) IS firing reliably
every minute — 15 consecutive executions checked, one per minute, no gaps in the trigger cadence itself. But execution
DURATION is bimodal:

- Most executions complete in **~30-45 seconds** (e.g. `86ql5` 22:46:04→22:46:45, `22fgz` 22:47:04→22:47:49).
- A subset take **8-9 MINUTES**: `dv7ng` started 22:37:04Z, completed 22:45:29Z (8m25s); `4q84g` started 22:42:06Z,
  completed 22:50:49Z (8m43s, confirmed via
  `gcloud run jobs executions describe ... --format="value(status.conditions)"` →
  `"message": "Execution completed successfully in 8m42.98s."` — genuinely slow, NOT a crash/timeout/retry).

Because a new execution triggers every 60s regardless of whether the prior one finished, an 8-9min execution means **7-8
overlapping executions are in flight simultaneously** against the same consolidated index. The consolidated file's mtime
only advances when one of these (slow or fast) executions actually completes and writes — during the 8-9min stretch
dominated by a slow run, the file can sit stale well past the 120s budget every consuming VM checks against, even though
the scheduler itself never stopped firing.

**Cost impact confirmed this session**: 2 waves × 3 VMs = 6 SPOT VM-launches (`e2-standard-8`, ~50GB disk each) failed
at the startup gate with zero compute progress, purely due to catching the consolidator mid-slow-run. A 3rd wave,
launched immediately after confirming a fresh manifest write (post a slow-run's completion), succeeded at the startup
gate.

## Why it matters

This is a P0 plan (`sports_p2_features_history_to_ml_ready`) whose Todo 1 gap-fill relaunches will keep hitting this
same wall at roughly the same base rate (order-of-magnitude: if 1-in-5 to 1-in-8 minutes falls inside a slow-run window,
roughly that fraction of naively-timed launches will fail) until either the consolidator's occasional slow runs are
fixed, or the client-side freshness budget/retry logic is made resilient to it. Every features-sports gap-fill VM launch
across this and future plans pays this same SPOT-launch tax blind until this is fixed.

## Recommended decision

1. **[INFRA] P1.** Investigate why `uts-prod-manifest-consolidator-instruments-sports` occasionally takes 8-9 minutes
   instead of ~40s — likely candidates: (a) lock contention from the every-1-minute trigger cadence allowing multiple
   concurrent executions against the same bucket/index (consider a min-instance-count=1 + concurrency=1 Cloud Run Job
   config, or a distributed lock so overlapping triggers no-op instead of doing redundant work), (b) a periodic
   larger-than-usual per-VM-shard backlog causing one execution in every N to do a bigger merge. (repo:
   unified-trading-library, manifest consolidator source)
2. **[CODE] P2.** Consider whether the features-service compute VM's startup gate should retry-with-backoff (e.g. wait
   up to ~2-3min, re-check freshness once) instead of failing immediately on a single stale reading — would absorb most
   of these transient windows without burning a full SPOT VM-launch. Weigh against the existing design intent (fail-fast
   to avoid a risky per-VM-merge fallback) — a bounded retry-then-fail-fast is not the same risk as the OOM-prone merge
   fallback the current code explicitly avoids. (repo: features-service)
3. **[SCRIPT] P3.** Consider whether `launch-features-vm.sh` (or a wrapper) should check consolidator freshness BEFORE
   provisioning the VM (a cheap `gsutil stat` check pre-flight) rather than paying the full VM-boot cost to discover
   staleness at the startup gate — would turn a wasted SPOT VM-launch into a cheap pre-check + short wait. (repo:
   deployment-service)

## Update 2026-07-14 23:18Z — escalated to P1: 3rd wave ALSO failed, manual pre-flight timing is NOT a reliable workaround

Tried timing a relaunch against a confirmed-fresh manifest read (`gsutil stat` showed 108s-old at launch time, within
the 120s budget) as a workaround. **All 3 VMs in this 3rd wave ALSO failed with the identical error** ~3-4 minutes after
launch (`heartbeat is 151s old` at 22:55:51Z) — confirming that a point-in-time freshness check taken from outside the
VM does NOT reliably predict the freshness at the moment the VM's own internal startup gate runs its check, minutes
later after boot/code-fetch/dependency-install overhead. **9 total VM launches across 3 waves have now failed
identically** (0/9 success rate observed this session). Bumped priority P2→**P1** — this is not an occasional nuisance,
it is currently blocking ALL features-sports gap-fill compute for this bucket. Recommend option 2 (bounded
retry-with-backoff inside the compute VM itself, since it's the only mechanism positioned to re-check freshness right
before doing real work, closest to the actual check-then-act window) as the most promising near-term fix, pending option
1's root-cause investigation.

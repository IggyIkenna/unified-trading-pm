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
status: resolved
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
resolved_by: [deployment-service@69136c2c, features-service@5e1ffd2e]
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

## Update 2026-07-15 00:10Z — Option 1 root-caused + fixed (same lock-livelock class as defi); Option 2 (bounded retry) shipped as defense-in-depth; status → resolved

**Step 1 — root cause CONFIRMED live, same failure class as the already-fixed `market-data-defi` chunked-merge livelock
(UTL commit `9358fb0b`), just triggered by ordinary per-VM-shard-backlog growth instead of date-range chunking:**

- Live-checked `gcloud run jobs executions list/describe` for `uts-prod-manifest-consolidator-instruments-sports` at
  investigation time (2026-07-14 23:30-23:49Z, i.e. "now" at dispatch): the bimodal pattern was NOT just still
  happening, it was actively WORSE than the original 1-in-5-to-1-in-8 characterization — an unbroken run of 8
  consecutive slow executions (9tkmn 8m21s, 9xpxf 6m15s, phq5l 8m21s, tjcjn 7m55s, fqwtx 8m39s, dksnm 8m42s, 98gpr
  8m54s, 29zjz 8m28s), each independently completing "successfully" per Cloud Run (not a crash/OOM).
- Confirmed the mechanism via Cloud Logging: at 23:30:45Z, `instructions-sports` logged the EXACT signature the defi-fix
  code comment (`unified_trading_library/manifest_consolidator.py` `_LOCK_TTL_SECONDS`) describes —
  `"clearing stale lock for instruments-store-sports-prd-central-element-323112 (age=303.6s > TTL=300.0s)"` — i.e. a
  legitimately still-running cycle's lock aged past the 300s code-default TTL, so the next `*/1` cron tick reclaimed it
  and started a COMPETING concurrent merge. The same signature recurred at 22:18:38Z (age=355.4s), 22:58:39Z
  (age=304.4s), and 23:22:39Z (age=302.7s) — a recurring, not one-off, pattern.
- Ruled IN as the same class (not a separate cause): `instruments-sports` has NO `CONSOLIDATOR_LOCK_TTL_SECONDS`
  Terraform override (still running the 300s code default) — only `market-data-defi` got the 2026-07-14 fix (4200s).
  Spot-checked `market-data-sports` (same 1800s task-timeout tier) for comparison: 15 consecutive executions all fast
  (~40-45s), confirming this is specific to `instruments-sports`'s larger/growing row count, not a sports-wide issue.
- **Fix shipped**: added a per-bucket `CONSOLIDATOR_LOCK_TTL_SECONDS=2400` override for `instruments-sports` in
  `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`, mirroring the exact defi pattern (TTL set
  comfortably — 600s headroom, same absolute buffer as defi's 3600s→4200s — above the bucket's own 1800s
  `timeout_seconds`, so a "fresh" lock can only ever belong to a still-legitimately-running execution). Live-applied
  immediately via
  `gcloud run jobs update uts-prod-manifest-consolidator-instruments-sports --update-env-vars CONSOLIDATOR_LOCK_TTL_SECONDS=2400`
  (verified via `gcloud run jobs describe`) AND codified in Terraform in the same commit, matching the defi precedent's
  "live-bump now, codify same session" pattern. Evidence: `deployment-service@69136c2c`.
- **Post-fix live confirmation (partial but strong)**: re-checked execution history ~20min after the live env-var
  update. Two more individually-slow cycles occurred (`568tw` 23:54:04→00:00:30 = 6m26s; `c7fc9` 23:57:04→00:03:28 =
  6m24s) — both well past the OLD 300s TTL, which would have guaranteed a reclaim under the pre-fix config — but
  **zero** `"clearing stale lock"` events logged in that window (checked 2026-07-15T00:00-00:08Z), and every intervening
  cron tick correctly logged a fast no-op skip instead of piling on a competing merge (no more runs of 4-5 consecutive
  overlapping slow executions). This is direct evidence the fix is holding. **Residual verification gap** (why this is
  marked resolved rather than left open pending further proof): I did not observe a full 8-9min cycle recur post-fix
  (worst seen post-fix was 6m26s, comfortably inside the new 2400s budget either way), and did not relaunch an actual
  features-sports gap-fill VM to confirm the startup gate passes end-to-end during a slow window. If the "clearing stale
  lock" signature reappears for `instruments-sports` in future Cloud Logging, re-open this issue — the fix would need a
  larger TTL or a deeper look at why a legitimate cycle is exceeding 2400s.

**Step 2 — bounded retry-with-backoff shipped as defense-in-depth (independent of Step 1's server-side root cause):**

Added `_assert_consolidator_healthy_with_retry()` to
`features-service/features_service/sports/cli/handlers/_manifest_preflight.py` (the shared SSOT gate used by both the
sports live runner and batch handler). On `ManifestConsolidatorStaleError`, retries the SAME
`assert_consolidator_healthy()` freshness check up to 2 more times (3 total attempts) with a 75s delay between attempts
(150s total added wait, under the ~3min bound), before re-raising the original error unchanged if still stale. Fail-fast
design intent preserved unmodified: `MANIFEST_ALLOW_STALE_FALLBACK` stays opt-in only, no per-VM recovery-merge fallback
added; this only re-checks the same authoritative signal a bounded number of times. Added
`features-service/tests/sports/unit/test_manifest_preflight.py` covering: immediate success (no retry, no sleep),
success on the final allowed retry within the bound, still-stale-after-all-retries raising the same error type after
exactly the bounded number of attempts, non-staleness errors propagating unretried, and both sports buckets retrying
independently. `bash scripts/quality-gates.sh --no-fix` green (288s, all steps passed). Evidence:
`features-service@5e1ffd2e`.

**Status**: flipped `open` → `resolved`. Both the server-side root cause (Option 1) and the client-side defense-in-depth
(Option 2) are shipped and live; Option 3 (pre-flight `gsutil stat` check before VM provisioning) was not pursued —
Option 2 supersedes its intent (a re-check from inside the VM at the actual check-then-act window is strictly more
reliable than an outside-the-VM point-in-time check, per the 3rd-wave finding above that already ruled out point-in-time
pre-checks as unreliable).

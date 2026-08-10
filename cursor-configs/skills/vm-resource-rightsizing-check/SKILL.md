---
name: vm-resource-rightsizing-check
description:
  Post-launch CPU/memory rightsizing check for any backfill/long-running VM expected to run >30 minutes — reads the
  app's already-existing self-reported telemetry (no Ops Agent needed), flags over-provisioned machine-type defaults
  as a tracked follow-up, and flags a rising memory trend as an OOM risk. Built from a live 2026-08-10 audit that
  found the tradfi OHLCV backfill fleet averaging 6-7% CPU on a 16-vCPU machine (97% of fleet volume) — a waste
  pattern nobody was checking for because no one owned "did this VM actually need what it was given."
---

# /vm-resource-rightsizing-check — did this VM need what it was given?

Answers one question per launch: **is this VM's provisioned machine type (vCPU/RAM) actually justified by what it
used, or is it silently wasting money (over-provisioned) / silently heading toward an OOM crash
(under-provisioned/growing)?** Every backfill/long-running VM already self-reports `cpu_pct`/`mem_pct` roughly every
60s (UTL's `HostMetricsSampler`, written into the deployment registry's `host_metrics_window` and, durably, BigQuery
`deployment_operational_data.resource_samples`) — **no Ops Agent install, no extra instrumentation needed.** This
skill's whole job is reading that data at the right time and turning a real finding into a tracked fix, not letting
"we'll notice if it's bad" be the only check.

**Provenance**: 2026-08-10 operator-directed audit found 245 `tradfi-bf-*` VMs over 24h, 97% of fleet volume, running
at ~6-7% CPU on `e2-highmem-16` (16 vCPU) — a machine type that had been raised for a THROUGHPUT reason (matching a
measured concurrency win), never re-checked against actual utilization once shipped. Downsized to `e2-highmem-8` with
concurrency explicitly pinned to preserve the throughput win. Full writeup:
`plans/active/issues/tradfi_vm_resource_utilization_downsize_2026_08_10.md`. This skill exists so the NEXT
over-provisioned default doesn't sit undetected for weeks before someone happens to ask about GCP costs.

## When this runs (the hard-rule trigger)

Any VM launch (interactively, via a launcher script, or AO-dispatched) where the workload is expected to run **more
than 30 minutes** — which is the large majority of backfill/long-running VMs in this workspace, not an edge case.
This is NOT optional cleanup work; treat a launch that skips this the same as a launch nobody verified reached
`STARTED` (`/codex/05-infrastructure/vm-launcher-runbook.md`'s own "no fire-and-forget" rule) — unmonitored resource
usage is the same class of gap as unmonitored liveness.

**Exception — documented generosity stands.** If the launcher script's own comments, a related codex doc, or a plan/
issue doc explicitly document a reason for the current sizing (a specific observed burst, a known OOM floor, a
long-tail staleness/timeout risk on that shard), **cite it and stop** — do not re-litigate a documented judgment call
from a fresh utilization snapshot alone. Look for this FIRST (grep the launcher script's own header comments and its
cited SSOT docs) before treating low utilization as a finding. Example already in this codebase: the tradfi
FRED/ES_OPT/VIX family stays on `e2-highmem-4` despite CPU headroom, because memory peaks 21.5-23GB of 32GB —
genuinely justified, not flagged.

## Step 1 — wait for a representative sample

Don't check immediately after launch (startup/boot noise isn't representative). For a >30min workload, check no
earlier than ~15-20 minutes in, and prefer checking again near natural completion (or at the 30min mark for
still-running VMs) so you have both an early and a later sample — this is also how you catch a **memory growth
trend** (Step 3), which a single snapshot cannot show.

## Step 2 — pull the telemetry (no Ops Agent, no new instrumentation)

Two equivalent read paths, pick whichever is faster for your scope:

- **Single VM, live**: read its current deployment record (
  `gs://deployment-scripts-central-element-323112/deployments/{active,archive/<date>}/<deployment_id>.json`) —
  contains `host_metrics_window`, the last ~10 self-reported `{ts, cpu_pct, mem_pct}` samples. For bulk lookups
  across many VMs, `gsutil -m cp` the JSON files to a local temp dir first rather than looping individual `gsutil
  cat` calls (measured far faster this session).
- **Fleet/rolling view**: `deployment-api`'s `GET /api/vm-resources/rolling` (avg/min/max/p95 per VM per window,
  1h/4h/24h/1wk — omit `vm_name` for the cross-VM view). This is the canonical read path
  (`/codex/05-infrastructure/deployment-observability.md` § "Durable operational data") and is preferable when
  checking a whole launcher family at once rather than one VM.
- Cross-check CPU (not memory — GCE doesn't expose memory without an agent, which is exactly why the app-level
  self-report above is the ONLY memory source) against Cloud Monitoring's independent API if you want a second
  opinion: `compute.googleapis.com/instance/cpu/utilization` via the REST endpoint (the `gcloud monitoring
  time-series list` CLI subcommand does not exist in this environment — use `curl` with `gcloud auth print-access-
  token` directly against `https://monitoring.googleapis.com/v3/projects/<project>/timeSeries`). This is a
  confirmation check, not the primary source — the app's own telemetry already includes memory, which Cloud
  Monitoring's default metrics do not.

## Step 3 — read the numbers, not just the peak

- **CPU**: average AND max, as both a fraction and an effective vCPU count (e.g. "28% of 4 vCPU ≈ 1.1 vCPU"). A
  brief single-sample spike at process startup then settling to steady-state is normal — don't let one burst sample
  read as sustained load; look at the trend across the full sample window, not just `max()`.
- **Memory — check the TREND, not just the peak.** A memory usage figure that climbs steadily across the sampled
  window (not just "high") is the OOM-risk signal this workspace has repeatedly hit the hard way this session (see
  `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`'s whole P0 investigation). A stable-but-high plateau is a
  sizing question; a RISING trend is a leak/growth question — do not conflate them, and do not downsize a machine
  showing a rising trend just because its CURRENT sample looks moderate.
- Compare both against the VM's actual provisioned machine type (parse the trailing vCPU count off the machine-type
  string, e.g. `e2-highmem-16` → 16 vCPU / 128GB) to get a real utilization ratio, not just a raw percentage.

## Step 4 — verdict and action

- **Over-provisioned** (sustained low CPU AND memory well below the ceiling, across a representative sample, no
  documented exception found in Step 0): this is a real finding — file it per the findings-triage rule (fix in the
  same commit if you're already touching the launcher; otherwise a tracked `- [ ]` todo in the relevant issue doc,
  never a chat-only note). Recommend a specific smaller machine type, checked against GCP's actual constraints (e.g.
  `e2-custom` machine types cap memory at 8GB per vCPU — verify a proposed downsize is even a valid shape before
  recommending it, `gcloud compute machine-types describe <type> --zone=<zone>` will reject an invalid custom
  combination directly). If the launcher derives OTHER settings from the machine size (concurrency, worker count,
  batch size — check for this explicitly, it's easy to miss), decide whether to let those auto-scale down too or pin
  them at their current level to preserve a previously-measured throughput number; state which you chose and why.
- **Correctly sized or under-provisioned**: say so plainly and stop — this is not a finding, don't manufacture one.
  A rising memory trend or sustained near-ceiling usage means STOP suggesting a downsize, not "downsize anyway since
  cost matters" — an OOM-crash-and-relaunch cycle costs far more (in both compute-hours and correctness risk on
  resumed/partial data) than the machine-type premium being avoided.
- **Genuinely uncertain** (e.g. only one sample, workload profile varies a lot by shard/day, no representative
  history yet): say that plainly too. Don't force a verdict from insufficient data — note what additional sampling
  would resolve it and leave it as an open, explicitly-scoped follow-up rather than a guessed recommendation either
  direction.

## What this skill does NOT do

Does not resize or kill a currently-running VM itself (a separate, more consequential action — check with the
operator or the launching plan's own todo for whether in-flight VMs should be cycled at a new size, since GCP SPOT
instances don't support a clean stop/resize/restart cycle and a kill+relaunch loses whatever that VM's current
window had completed). Does not change a machine-type default unilaterally on a single low sample — a real
recommendation needs the representative-sample bar in Step 1 cleared first. Does not re-litigate a documented sizing
decision without new evidence past what that decision already considered.

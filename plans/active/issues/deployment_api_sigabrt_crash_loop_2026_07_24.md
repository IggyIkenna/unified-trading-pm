---
doc_type: issue
title:
  "deployment-api container hits `Uncaught signal: 6` (SIGABRT) roughly every 20-40 min — undiagnosed crash-loop
  compounding the reaper-drain P0"
summary: >-
  [BACKEND] Live Cloud Logging query against `uts-shared-deployment-api` (project central-element-323112, region
  asia-northeast1) shows `Uncaught signal: 6, pid=<N>, tid=<N>, fault_addr=0.` in the
  `run.googleapis.com%2Fvarlog%2Fsystem` log stream 106 times over the last 3 days (~35/day, roughly once every 20-40
  min) — pid==tid each time (the process's own main thread aborting, not a worker thread). This is FAR more frequent
  than gunicorn's own `max_requests=1000±100` worker recycling would explain on its own, and is a plausible major
  contributor to why the deployment registry reaper (see
  `deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md`) keeps getting interrupted mid-tick — every
  ~20-40 min the whole container (not just one gunicorn worker) appears to be crashing and restarting, which is a much
  higher-frequency disruption than the reaper's own 900s (15 min) cadence. NOT diagnosed to a specific root cause in
  this session (out of scope for the 1h reaper-drain P0 todo that surfaced it) — needs its own focused investigation.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-api]
scope: [engineer]
tags: [deployment-registry, crash-loop, observability, cloud-run, sigabrt]
related: [deployment_registry_reaper_not_draining_stale_entries_2026_07_24]
created: 2026-07-24
priority: P1
parent_epic: observability_master
source:
  "[BACKEND] slot-2 diagnosis of deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md's P0 todo #1 —
  surfaced while confirming the reaper's CancelledError root cause via live `gcloud logging read` against
  uts-shared-deployment-api."
execution_scope: orchestrator-agent
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# deployment-api SIGABRT crash-loop — undiagnosed (2026-07-24)

## What I found

While diagnosing the reaper-drain P0, I queried live Cloud Logging for `uts-shared-deployment-api`
(`gcloud logging read`, project `central-element-323112`):

- `logName=run.googleapis.com%2Fvarlog%2Fsystem` shows `Uncaught signal: 6, pid=<N>, tid=<N>, fault_addr=0.` **106 times
  in the last 3 days** — roughly every 20-40 minutes, all day, every day. `pid == tid` in every sample, meaning the
  process's own main thread is the one aborting (signal 6 = SIGABRT — a deliberate `abort()`, not an OOM-kill, which
  would show as SIGKILL and a different log signature).
- The service is `minScale=1`/`maxScale=20`, `cpu=4`, `memory=16Gi` (generous — an OOM at this limit for this workload
  seems unlikely, though not ruled out here).
- Separately, `logName=run.googleapis.com%2Fstdout` has **zero entries in the last 30 days** — confirmed root-caused and
  already fixed by a concurrent commit (`deployment-api@f27a8f1`, "configure root logger so provider-failure warnings
  actually reach Cloud Logging" — no `logging.basicConfig()` had ever been called, so every `logger.info`/ `.warning`
  call was silently dropped). That fix is orthogonal to this SIGABRT finding but explains why the reaper's own
  "[AUTO_SYNC] Reaper: archived N" log line was never observed either, independent of whether the reaper actually ran.
- `gunicorn.conf.py` sets `preload_app = True` (app code imported once in the gunicorn MASTER before forking N workers)
  — a well-known hazard when any imported module holds a gRPC-based client (gRPC's process state is not fork-safe; a
  channel/thread-pool created pre-fork can abort post-fork in a child). This app does use Firestore
  (`deployment_api/routes/_ci_status_firestore_store.py`), whose Python client is gRPC-based — but a quick check shows
  its own client construction is explicitly lazy (`firestore_module_factory()`, SDK imported "lazily... so importing
  this module in unit tests with an injected fake never requires the SDK to be present"), which weakens but does not
  fully rule out this theory — I did NOT exhaustively audit every module for an eager (import-time) GCP/gRPC client
  construction that `preload_app=True` would carry across the fork.
- I did not have time in this task's 1h budget to correlate individual SIGABRT timestamps against instance IDs / request
  volume, enable `PYTHONFAULTHANDLER`/core dumps, or bisect by toggling `preload_app` — this needs a dedicated
  investigation.

## Why it matters

- 35 crashes/day at a ~20-40 min cadence is far more frequent than gunicorn's own `max_requests=1000±100` worker
  recycling would produce under normal traffic, and is DRASTICALLY more frequent than the reaper's 900s tick interval —
  meaning almost every reaper attempt has a real chance of landing inside one of these crash windows, independent of
  (and likely compounding) the cancellation-timeout race fixed in the sibling P0 todo (`lifespan.py`'s
  `_cancel_background_tasks` timeout, bumped 5s→20s in `deployment-api@<this task's SHA>`).
- A container that crashes via SIGABRT (not a graceful SIGTERM) may not even run the ASGI `lifespan` shutdown path at
  all for that instance — meaning the reaper timeout fix helps the WORKER-RECYCLE case but does nothing for a hard
  process abort, which could still discard in-flight archiving work with zero graceful-shutdown log trail.
- This is exactly the kind of instance-churn signature the reaper-drain issue doc's Gap-1 finding speculated about
  ("suggestive of instances recycling far more often than expected") but could not confirm from log evidence alone at
  the time — this crash-loop is the confirmed, measured mechanism.

## Recommended decision

File as its own P1 BACKEND/INFRA investigation (not bundled into the reaper-drain P0, which is scoped to the
cancellation-timeout fix and already shipped). Suggested next steps for whoever picks this up:

- [ ] [BACKEND] P1. Root-cause the `Uncaught signal: 6` crash-loop on `uts-shared-deployment-api` (project
      `central-element-323112`, region `asia-northeast1`): correlate SIGABRT timestamps (`gcloud logging read` on
      `run.googleapis.com%2Fvarlog%2Fsystem`) against per-instance request volume / `containerConcurrency=80` load, and
      audit every module reachable from `deployment_api.main` for an EAGER (import-time, not lazily-constructed)
      gRPC-based client (Firestore, Pub/Sub, Secret Manager) that `preload_app = True`
      (`deployment_api/gunicorn.conf.py`) would construct in the gunicorn MASTER before fork — the classic
      gRPC-post-fork-abort hazard. If found, either make that construction lazy (per-worker, post-fork) or set
      `preload_app = False` and re-measure the SIGABRT rate over the following 3 days (repo: deployment-api).

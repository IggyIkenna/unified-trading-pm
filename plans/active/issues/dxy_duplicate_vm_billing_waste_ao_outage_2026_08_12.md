---
doc_type: issue
title: "26+ duplicate tradfi-bf-ice-idx-ohlcv-24h (DXY) VMs running concurrently — active billing waste, killed"
summary: >-
  Fleet-wide preemption/billing-waste audit (per /backfill-monitor's composed /vm-preemption-billing-waste-audit step)
  found 40 SPOT preemption events today for tradfi-bf-ice-idx-ohlcv-24h-* (DXY) VMs plus 30 concurrently RUNNING
  duplicates spanning years 2019-2026 with 3-5 VMs per year — a redundant relaunch wave, confirmed 100% unnecessary
  since a separately-dispatched, verified-complete DXY backfill already covered all 8 year-shards with real data. 26
  duplicates killed live (operator-approved); the remainder had already self-terminated. Root cause not fully
  identified: the obvious candidate (uts-prod-tradfi-wave-launcher-cron) is PAUSED, and AO's central server was
  confirmed DOWN (ConnectionRefusedError via SSM) at investigation time, ruling out both as the active trigger. Most
  likely explanation: a concurrent interactive session on this shared workspace manually invoking the same launcher.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags: [billing-waste, vm-duplicate, tradfi, dxy, ao-outage]
related:
  - /plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md
  - /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md
parent_epic: tradfi_master
source: "Fleet-wide /vm-preemption-billing-waste-audit sweep, 2026-08-12, interactive session"
assigned_vm: NA
created: 2026-08-12
resolved_by:
locked_by:
priority: P1
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# 26+ duplicate DXY VMs — active billing waste, killed

## What was found

Fleet-wide preemption scan (`gcloud compute operations list --filter="operationType=compute.instances.preempted"`,
scoped to today) found 40 distinct preemption events for `tradfi-bf-ice-idx-ohlcv-24h-*` between 17:38-18:06 UTC — the
SAME 8-year-shard, no-`--year`-scoped launcher invocation repeated at least 5 times in ~20 minutes. A live fleet listing
at investigation time (~18:50 UTC) showed 30 VMs still RUNNING for this exact prefix, spanning years 2019-2026 with 3-5
concurrent VMs per year (e.g. 2022 had 5 simultaneous VMs).

This is confirmed 100% redundant: a separately-dispatched background agent (this same session, different task) already
completed a real, verified full-history DXY backfill across all 8 year-shards (2019-2026) earlier the same day, with
real per-VM manifest-shard writes confirmed via direct log inspection. The duplicate wave writes the identical data
again — idempotent (no corruption), but pure wasted SPOT compute-hours.

## Action taken

26 of the 30 running duplicates were deleted live (`gcloud compute instances delete`, operator-approved 2026-08-12); the
remaining 4 had already self-terminated between listing and deletion. Post-delete verification: zero
`tradfi-bf-ice-idx-*` instances remain in the fleet.

## Update 2026-08-13 — server recovered, but zero live workers (still not fully healthy)

Re-checked live state ~12:30 UTC 2026-08-13 via direct SSM to the orchestrator host (`i-0c9b283b31d6b5ca7`,
`ap-northeast-1`), independent of the operator's own report that AO was down at the time this session started:
`systemctl` shows `orchestrator.service` **active running**, the `server.server:app` uvicorn process is up (PID 2506521,
started 12:04 — recent), and `/api/healthz` on `:8765` answers `200`. So the central server itself is no longer in the
`ConnectionRefusedError` state this doc originally found. **But** `tmux list-sessions` errors with
`error connecting to /tmp/tmux-0/default (No such file or directory)` — there is no tmux server on the host at all,
meaning **zero workers are actually running**, despite the live backlog (`check-ao-backlog-status.sh`) showing at least
one task (`dependency_health_alerting_never_wired-376d92bc984b`) marked `status=dispatched`. That claim has nothing live
behind it — a stale dispatch record, not an active worker. Net effect: the server answers health checks and the DB is
readable, but the fleet is doing no work and any `escalate-*` CI job firing right now would dispatch into a black hole
(silently queued, never picked up) rather than get a working agent. This is a DIFFERENT, narrower failure mode than the
original "server down" finding and still open — worth the operator's own look at why the dispatch loop isn't spawning
tmux workers despite the server process being healthy.

## Root cause — not fully identified, two obvious candidates ruled out

- **`uts-prod-tradfi-wave-launcher-cron`** (Cloud Scheduler) is currently **PAUSED** — cannot be the active trigger.
- **AO's central orchestrator server was confirmed DOWN** at investigation time —
  `bash agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh` returned
  `ConnectionRefusedError: [Errno 111] Connection refused` reaching the server directly on its own host via SSM (not a
  network-path issue). A dead central server cannot be issuing live dispatches, though a worker session started before
  the outage could in principle still be executing independently — not confirmed either way.
- **Most likely explanation (unconfirmed)**: a concurrent interactive session on this shared multi-tab/multi-slot
  workspace manually re-invoking `launch-tradfi-bf-ice-ohlcv-24h.sh` without `--year` scoping, unaware another session
  (this one) was already covering the same gap. This exact class of "no shared dedup check across concurrent manual
  launches" has already burned the fleet once this week for a different launcher family (`tradfi-bf-cme-ohlcv-1m-*`, 167
  stray VMs, per `tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`'s `wave_launcher.py` dedup-bug entry) — but
  that fix was specific to `wave_launcher.py`'s own automated dispatch path, not manual launcher invocations, so it
  would not have prevented this.

## Todos

- [ ] [OPERATOR] P1. Investigate why AO's central server is down (`ConnectionRefusedError` on its own host) — separate,
      likely more urgent issue than this billing-waste finding. See
      `/codex/15-runbooks/safe-service-restart-procedures.md`'s fix-vs-not table before restarting. **Partially
      superseded by the 2026-08-13 update above**: the server process itself has since recovered (healthy, answering
      `/api/healthz`), but no tmux workers are running at all — the ORIGINAL "why did the server die" question may still
      be open even though the server is currently up; investigate why the dispatch loop isn't spawning workers despite
      the server being healthy.
- [ ] [OPERATOR] P1. **New 2026-08-13**: with the server healthy but zero live tmux workers, confirm whether the
      dispatch loop is actually attempting to spawn workers and failing silently, or not attempting at all — and
      reconcile the `dependency_health_alerting_never_wired-376d92bc984b` task's stale `status=dispatched` claim (no
      live session behind it) before it silently blocks that queue slot indefinitely.
- [ ] [SCRIPT] P2. Determine whether any manual-launcher-invocation path (as opposed to `wave_launcher.py`'s automated
      dispatch) has a dedup/collision check against already-running VMs for the same shard — if not, consider whether
      one is worth adding given this is the second fleet-wide duplicate-VM billing-waste incident this week (different
      launcher family each time).
- [ ] [DATA] P3. Confirm the killed duplicate VMs' partial/redundant writes didn't leave any non-idempotent side-effects
      (expected: none, since DXY capture is a pure overwrite-safe write, but not independently re-verified after the
      kill).

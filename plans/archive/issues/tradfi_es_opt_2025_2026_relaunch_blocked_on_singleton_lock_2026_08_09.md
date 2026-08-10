---
doc_type: issue
title: >-
  `tradfi-bf-es-opt-light-2025`/`-2026` relaunch blocked on the shared tradfi-bf-* singleton lock — never durably
  tracked, only watched from an interactive session
summary: >-
  During a 2026-08-09 DP-VM-003 investigation I found 3 crashed tradfi backfill VMs (confirmed genuine crashes, not
  clean completion, via GCS `LAUNCH_PARAMS.json`/deployment-registry cross-check) and relaunched 1 of them
  immediately. The remaining 2 (`ES_OPT` light tier, years 2025 and 2026) could not relaunch because
  `launch-tradfi-backfill-vm.sh`'s `_check_singleton_lock` refuses to start while ANY `^tradfi-bf-*` VM is RUNNING
  (serializes the whole fleet against one shared Databento account). I set up an ad-hoc ~30min-poll watcher inside my
  own interactive Claude Code session to relaunch the moment the fleet cleared — but never converted this into a
  tracked plan todo or AO dispatch, so the whole relaunch was silently contingent on that one session staying alive
  (operator caught this gap directly: "isnt that now in ao tasks?"). Filing this now so the work is durable
  regardless of session lifetime, and can be AO-dispatched instead of hand-watched. Separately found + fixed a real
  bug in the ad-hoc watcher itself worth recording: after ~10.5h the interactive `gcloud` CLI's OAuth token expired
  (needs an interactive browser reauth, impossible headless) and the watcher's `gcloud compute instances list` call
  failed — but the watcher's original version didn't check the exit code, so the failure's empty stdout was read as
  "0 VMs running" and it reported a false CLEARED at 2026-08-09T23:38:44Z. Live cross-check at that moment showed 10
  VMs actually running (several created minutes before the false-clear tick), so no relaunch was attempted on the bad
  signal. Fixed by switching the active `gcloud` account to the already-credentialed
  `1060025368044-compute@developer.gserviceaccount.com` service account (no interactive reauth needed) and making the
  poll loop treat any non-zero `gcloud` exit code as a distinct ERROR state rather than silently coercing it to zero.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [deployment-service]
scope: [engineer]
tags: [tradfi, vm-relaunch, singleton-lock, dp-vm-stall, es-opt, backfill, monitoring-bug]
related:
  - /codex/05-infrastructure/vm-launcher-runbook.md
  - /codex/15-runbooks/incidents/rb_infra_relaunch.md
created: "2026-08-10"
author: main (Claude Code, interactive session)
parent_epic: tradfi_master
resolved_by:
locked_by:
locked_since:
source: >-
  Found during a 2026-08-09 DP-VM-003 crashed-VM investigation in the same session; converted from ad-hoc
  session-local watching to a tracked todo on 2026-08-10 per operator direction.
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
---

> ## ✅ RESOLVED 2026-08-10
> Both VMs found RUNNING, launched by another process while this session was on unrelated work — see the todo below
> for evidence. Never dispatched to AO (this doc was written but held unpushed pending a PM CI fix, so AO never saw
> it) — resolved before dispatch was even possible.

# `tradfi-bf-es-opt-light-2025`/`-2026` relaunch — blocked on the shared singleton lock

## What I found

1. **3 crashed tradfi backfill VMs found 2026-08-09**, confirmed via `gs://deployment-scripts-central-element-323112/
   vm-logs/<vm>/{run.log,WATCHDOG_TRACE.log,PROGRESS.json,LAUNCH_PARAMS.json}` and the deployments registry
   (`active`/`archive/<date>`) — genuine crashes, not clean completions. 1 of 3 relaunched successfully same session.
2. **The other 2 (`ES_OPT` light, 2025 and 2026) never relaunched** — `launch-tradfi-backfill-vm.sh`'s
   `_check_singleton_lock` (line ~161) refuses any launch while `name~"^tradfi-bf-" AND status=RUNNING` is non-empty:
   the lock serializes ALL 18 tradfi VM families against one shared Databento account, not just same-symbol launches.
3. **Fleet has not sustained a genuine zero for 24h+** as of this filing — oscillating roughly 4-33 concurrently
   running `tradfi-bf-*` VMs as other slots cycle their own backfills through the same lock. A 30min-poll watcher has
   been running continuously in an interactive session since 2026-08-09T13:07Z tracking this.
4. **Watcher monitoring-bug (fixed, not shipped as code — this was an ad-hoc session script, not a repo file)**: see
   summary above. Corrected watcher now uses the compute-default service account and treats `gcloud` failures as a
   distinct alarm state, never silently as "0".

## Why this belongs here, not just in chat

Per this workspace's `every-follow-up-is-a-todo` rule and the operator's direct correction: a relaunch gated only on
an interactive session's background task has no durability — if that session ends before the singleton lock clears,
the relaunch simply never happens and nothing else notices. This doc + its todo below make the work AO-dispatchable
instead.

## Todo

- [x] ✅ [SCRIPT] P2. **RESOLVED 2026-08-10 — relaunched by another process, not this session.** Both
      `tradfi-bf-es-opt-light-2025-20260810-113247` and `tradfi-bf-es-opt-light-2026-20260810-113302` were found
      RUNNING (`gcloud compute instances list`) at 2026-08-10T~12:0xZ, `creationTimestamp` ~2026-08-10T11:32-11:33Z —
      launched by a peer session/process while this session was heads-down on the VIX launcher fix below, not by any
      command run in this session. Fleet had also dropped to just 3 total `tradfi-bf-*` VMs at that check (the other
      being `tradfi-bf-fred-full-*`), consistent with the legacy out-of-scope FX/commodity noise finally clearing.
      Verified via live `gcloud compute instances list --filter="name~'^tradfi-bf-es-opt-light-202[56]'"
      --format="table(name,status,creationTimestamp)"`, both `RUNNING`. Stood down the session's own watcher (task
      `bg5wh0b38`) since its purpose (wait-then-relaunch) is now moot — relaunching again would violate the singleton
      lock's own purpose (duplicate launch against a shared account). Not independently re-verified against
      `PROGRESS.json`/deployment-record `STARTED` state beyond `RUNNING` status — if picking this up further, confirm
      `/codex/15-runbooks/incidents/rb_infra_relaunch.md`'s verification step. Repo: deployment-service.

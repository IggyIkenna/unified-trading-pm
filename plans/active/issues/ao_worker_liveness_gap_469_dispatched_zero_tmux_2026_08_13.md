---
doc_type: issue
title: >-
  agent-orchestrator dispatch loop not spawning workers — 469 tasks dispatched/queued, ZERO live tmux worker sessions on
  the VM (2026-08-13, /ci-reconcile §5 check)
summary: >-
  Found 2026-08-13 during a `/ci-reconcile` run, via
  `agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh` (read-only SSM check against the live
  orchestrator VM `i-0c9b283b31d6b5ca7`). The server answers health checks and the backlog API returns normally
  (`TOTAL_TASKS=3325`, `SUMMARY={'queued': 466, 'done': 2714, 'blocked': 36, 'cancelled': 106, 'dispatched': 3}`), but
  `tmux list-sessions` on the VM itself errors with `error connecting to /tmp/tmux-0/default (No such file or
  directory)` — i.e. ZERO live tmux sessions exist on the host at all, while 469 tasks sit in `dispatched`/`queued`
  state. Per the skill's own 2026-08-13 hardening note: "AO's own liveness is a separate check from 'is it answering
  health checks' ... the server was fully healthy by every process/HTTP signal while `tmux list-sessions` showed ZERO
  live worker sessions on the host, with several tasks sitting in dispatched/queued state that had nothing actually
  running behind them." This run reproduces that exact signature, at larger scale (469 vs the smaller count in the prior
  incident). Not independently root-caused this pass — CLAUDE.md states the orchestrator runtime "self-heals
  (AutoSpawn/failover/watchdog ON — never manually kill tmux)", so no manual intervention was taken; this doc exists to
  make sure the gap doesn't go unnoticed if it persists.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, worker-liveness, tmux, dispatch-loop, ci-reconcile]
related:
  - /plans/active/ao_consolidated_closeout_2026_08_12.md
  - /codex/04-architecture/agent-orchestrator-scheduled-jobs.md
  - /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md
created: "2026-08-13"
author: main agent (/ci-reconcile)
source: /ci-reconcile §5 AO-escalation cross-check, 2026-08-13
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

## Evidence

```
LIVE_WORKER_SESSIONS=0 (error connecting to /tmp/tmux-0/default (No such file or directory))
⚠️  WORKER-LIVENESS GAP: 469 task(s) in dispatched/queued state but ZERO live tmux worker sessions — the server is
answering health checks but its dispatch loop is not (or has not yet) spawned anything. A 'dispatched' status here does
NOT mean a worker is actually running.
TOTAL_TASKS=3325 SUMMARY={'queued': 466, 'done': 2714, 'blocked': 36, 'cancelled': 106, 'dispatched': 3}
```

Captured via `bash agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh` (SSM `send-command` against EC2
`i-0c9b283b31d6b5ca7`, region `ap-northeast-1`, Elastic IP 13.113.200.22) at approximately 2026-08-13T16:10Z.

## Why this matters

Any escalation dispatched into AO during a window like this (e.g. an `escalate-to-orchestrator` repository_dispatch
fired by `ldr-to-main-promote.yml`, `sit-gate-stuck-detector.yml`, etc.) queues into a black hole — it shows as
`dispatched`/`queued` in the API but nothing is actually working it. This is a fleet-wide dispatch-capacity outage, not
a single-repo CI issue, so it is out of `/ci-reconcile`'s own remit to fix (per the skill: "AO's own dispatch-loop
health is not this skill's repo to fix").

## Not yet done

- [ ] [OPERATOR] P1. **CONFIRMED ONGOING AND WORSENING as of 17:09Z re-check** (below) — this needs the escalation this
      doc's original todo 1 only conditionally called for. `journalctl -u orchestrator.service` on the VM for a
      dispatch-loop crash/hang distinct from the HTTP-health-check process; restart the dispatch loop if a hang is
      confirmed (per CLAUDE.md's safe-restart runbook, not an ad-hoc kill).
- [ ] [BACKEND] P2. Root-cause why AutoSpawn/failover/watchdog (stated in CLAUDE.md to be "ON" and to self-heal) has not
      spawned a single worker for a growing backlog. Check orchestrator service logs around the observed window for a
      dispatch-loop crash/hang distinct from the HTTP-health-check process.

## Progress Log

- 2026-08-13: Filed from a `/ci-reconcile` run's §5 AO-escalation cross-check. Not independently root-caused or fixed —
  CLAUDE.md states the orchestrator self-heals and this skill's own scope excludes AO's dispatch-loop internals.
- 2026-08-13T17:09Z: Re-checked per operator prompt. NOT self-recovered — WORSENED: `dispatched+queued` grew 469→612,
  `TOTAL_TASKS` grew 3325→3470 (~145 more tasks queued in under an hour), `LIVE_WORKER_SESSIONS` still 0
  (`tmux list-sessions` still errors with no server on the VM). This is now a confirmed live, ongoing, growing outage,
  not a transient blip — escalating per CLAUDE.md's "big finding" rule (AO is the CLAUDE.md-named "critical service (AO
  first)").

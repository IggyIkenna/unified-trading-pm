---
doc_type: issue
title:
  Session-bound Claude Code monitoring (ScheduleWakeup loops) for ad hoc backfill VMs inherits the operator's own
  connectivity/session-continuity dependency — a real, measured blind spot, not just the already-documented "one-off VMs
  aren't wired into the fleet monitor" gap
summary: >-
  While monitoring a FIXTURES backfill VM (af-backfill-20260726-013313) via a self-armed ScheduleWakeup loop
  (/autonomous, operator away ~6h), the VM was genuinely SPOT-preempted at 2026-07-26T04:16:47Z (confirmed via `gcloud
  compute operations list` — systemevent compute.instances.preempted) and went undetected for ~5h20m before the operator
  reconnected and asked "seems to have stopped." CLAUDE.md already documents that one-off/ad hoc VMs aren't wired into
  the fleet-level auto-relaunch watchdog ("this is on you, not automatic") — the gap found here is one level deeper: an
  agent's own self-armed session-bound monitoring loop (ScheduleWakeup ticks re-invoking the same Claude Code session)
  is NOT a substitute for that missing infrastructure watchdog, because it inherits the SAME dependency the operator has
  — if the session/client can't be reached (the operator's own reported connectivity drop, in this case), scheduled
  wakeups cannot fire or act, so the blind spot persists exactly as long as the connectivity gap does. Shortening the
  check interval does not close this gap (it only bounds the window when the session IS reachable); the only real fix is
  an out-of-band watchdog that does not depend on any particular Claude Code session staying connected.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, instruments-service]
scope: [engineer, admin]
tags: [vm-monitoring, spot-preemption, autonomous-agent, watchdog, reliability, session-bound]
related:
  [
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  ]
created: 2026-07-26
last_updated: 2026-07-26
priority: P2
parent_epic: infrastructure_master
source:
  "Measured during an interactive /autonomous session monitoring af-backfill-20260726-013313 (FIXTURES curated-universe
  backfill); operator reconnected after ~5h20m and reported the VM 'seems to have stopped', which led to discovering the
  preemption + the undetected gap via `gcloud compute operations list`."
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# Session-bound monitoring loops for ad hoc VMs share the operator's connectivity blind spot

## Evidence (2026-07-26)

- VM `af-backfill-20260726-013313` (asia-northeast1-c) launched ~2026-07-26T00:36Z with a self-armed
  `ScheduleWakeup`-based monitoring loop (30min cadence, per `/autonomous` rules — the operator was away ~6h).
- `gcloud compute operations list --filter="targetLink~'af-backfill-20260726-013313'"` shows
  `systemevent-...-compute.instances.preempted` at `2026-07-25T21:16:47.177-07:00` = `2026-07-26T04:16:47Z`, matching
  exactly where `run.log` goes silent (last heartbeat `04:15:12Z`, no `DEPLOYMENT_FAILED`/exit-code trace, no
  `PREEMPTED` marker file — the shutdown grace period was too short for the shutdown-script to upload it).
- The VM was not detected as dead until the operator reconnected at ~09:30Z and reported "seems to have stopped" — a
  **~5h20m undetected gap**, despite a monitoring loop having been armed the whole time.
- No evidence the loop's `ScheduleWakeup` calls failed to be _scheduled_; the working theory (not proven, since there is
  no log of missed harness-level wakeups) is that the calls could not be _delivered/acted on_ while the operator's own
  session/client was unreachable, since `ScheduleWakeup` re-invokes the same interactive session.

## Why this is a distinct finding from the existing "one-off VMs aren't fleet-monitored" rule

CLAUDE.md (`Launching VMs / infra`) already says: _"Manually checking in on a SPOT VM that looks stalled/gone: verify
`compute.instances.preempted`... BEFORE diagnosing a bug/hang — one-off migration VMs aren't wired into the fleet
monitor, so this is on you, not automatic."_ That correctly assigns responsibility to **a** watcher. What's new here:
when the assigned watcher is an **agent's own session-bound loop** rather than a human periodically checking in, the
loop's uptime is bounded by the SAME session/connectivity continuity as the human it's substituting for — it is not an
independent, infrastructure-level guarantee. A human who steps away and a Claude Code session that goes unreachable fail
in the same way and at the same time when they're the same physical connection.

## Todos

- [ ] [DATA] P2. **Decide + document the intended reliability model for ad hoc long-running backfill VMs**: either (a)
      explicitly accept that session-bound monitoring is best-effort only (document the caveat prominently in
      `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md` so future agents don't over-promise "I'll
      keep watching" as if it were a guarantee), or (b) wire ad hoc backfill VMs (matching `VM_PREFIX_TO_BUCKET` but
      launched outside the fleet-tracked set) into the existing `RelaunchPreemptedVm` / exit-code-fleet-monitor actuator
      so SPOT preemption recovery doesn't depend on any particular session being reachable. **Done when**: the codex doc
      states the decided model explicitly (not left implicit), and if (b) is chosen, a follow-up scoped todo names the
      specific registration mechanism. This is a genuine operator/design decision (which model to commit to), not a
      worker-determinable fact — do not dispatch (a) or (b) speculatively without that decision.
- [ ] [DATA] P3. **Audit whether the `PREEMPTED` marker's shutdown-script grace period is survivable in practice** — the
      marker write (`gcloud storage cp` of a one-line file) didn't complete before this instance was reclaimed, which is
      the SAME mechanism `zombie_watchdog`/`exit_code_fleet_monitor` rely on to classify a gone VM as a benign
      preemption vs. an unexplained disappearance. If the write frequently loses the race, the marker is not a reliable
      signal fleet-wide, not just for this one VM. (repo: deployment-service `scripts/vm/lib/launcher_common.sh`'s
      shutdown-script template). **Done when**: either measured evidence the race is rare (this was a one-off), or a
      mitigation (e.g. writing the marker earlier / more defensively) is proposed.

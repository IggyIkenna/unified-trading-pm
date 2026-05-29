---
title:
  "Central orchestrator API host (i-0c9b283b31d6b5ca7) chronic StatusCheckFailed_Instance — intermittent impairment all
  day 2026-05-29; reboot is workaround"
created: 2026-05-29
author: slot-1 (ikenna)
source:
  - aws ec2 describe-instance-status i-0c9b283b31d6b5ca7 (impaired since 2026-05-29T00:09:00Z initially)
  - aws cloudwatch get-metric-statistics StatusCheckFailed_Instance 2026-05-28T20:00Z → 2026-05-29T15:00Z (datapoints
    `1.0` at 02:15Z, 03:25Z, 04:00Z, 05:10Z, 07:40Z, 08:50Z, 13:10Z, 14:55Z — multiple events through the day, not just
    2)
  - Operator session 2026-05-29:
      API timed out twice from CLI; aws ec2 reboot-instances triggered both times (172s + 360s recovery)
  - Internal SSM probe from i-007e8d99d12831578 also confirmed port 8026 unreachable on i-0c9b283b31d6b5ca7 (not just
    from operator's IP)
locked_by: api_host_chronic_impairment_2026_05_29
---

## What I found

`i-0c9b283b31d6b5ca7` (m8i.4xlarge, ap-northeast-1, public IP 13.113.200.22) hosts the central agent-orchestrator API
behind `api.agent-orchestrator.odum-research.com`. CloudWatch `StatusCheckFailed_Instance` has been firing
**intermittently throughout 2026-05-29**:

```
2026-05-29 02:15Z  ─ failure
2026-05-29 03:25Z  ─ failure
2026-05-29 04:00Z  ─ failure
2026-05-29 05:10Z  ─ failure
2026-05-29 07:40Z  ─ failure
2026-05-29 08:50Z  ─ failure
2026-05-29 13:10Z  ─ failure
2026-05-29 14:55Z  ─ failure (post-second-reboot)
```

Two observed full outages today required operator-driven reboots:

- **00:09Z** — `aws ec2 describe-instance-status` returned `InstanceStatus.Status: impaired`. Reboot at 08:48Z brought
  it back in **172s**.
- **14:27Z** — second impairment, reboot at 14:28Z back in **360s**.

Both reboots restored API service. EC2 `SystemStatus.Status` always shows `passed` (network from AWS side is fine).
`InstanceStatus.Status` fails → OS / kernel / network-stack inside the instance is the culprit, not the EC2
infrastructure.

## Why it matters

This is the **central dispatch host** for the agent-orchestrator fleet:

- Hosts the public `/api/spawn`, `/api/state`, `/api/backlog/regen`, and `/api/slots/<N>/{boot,progress,done}` endpoints
  the per-VM orchestrators proxy to.
- Hosts 8 worker slots (4–11) in local tmux sessions.
- Hosts the PlanRegenLoop reading the local PM clone.

When the host goes impaired:

- All 8 worker slots become stale (no `/heartbeat`).
- Operators can't spawn new workers, can't view `/api/state`, can't push backlog updates.
- New plans pushed to LDR get queued behind the next regen tick after recovery.
- Slack alert "Slot N STALE" fires for every existing slot — alert-storm noise that buries real signals.

Reboot is a workaround, not a fix. The host has gone impaired **at least 8 distinct times today** per the CloudWatch
metric — reboot only addresses each individual event after the fact.

## Likely root causes (closed set of suspects)

1. **OOM / memory pressure**: m8i.4xlarge has 64 GB. PlanRegenLoop + account-usage poller + 8 worker tmux sessions
   - nginx + uvicorn + SQLite. If one of the loops leaks (e.g. PlanRegenLoop's claude-subprocess spawns for usage
     refresh — observed in journal "spawning claude in /home/ubuntu/.../agent-orchestrator (render_floor=3.0s)" every
     ~10s) doesn't reap, RSS climbs until OS thrashes.
2. **Kernel / network-stack wedging**: the StatusCheckFailed_Instance is specifically network-stack reachability (ARP,
   ICMP, etc.) from the EC2 hypervisor — this can wedge under high IO load or specific kernel bugs.
3. **Anthropic-CLI subprocess churn**: the orchestrator polls weekly_msg_limit by spawning a quick `claude` instance per
   account every ~10 sec. Each spawn forks/execs a Python+claude+node stack. Cumulative FD / process-table / memory
   pressure across hours.
4. **Disk fill** (less likely but cheap to check): journald + tmux logs + transient claude-spawn temp files.

## Recommended decision

Treat this as a critical infra issue (orchestrator-host stability is the floor under everything autonomous). Phased
investigation + fix in `plans/active/api_host_chronic_impairment_2026_05_29.md`. Per CLAUDE.md "External Data Is Always
Available — Never Silently Defer Adapters" sibling rule: this host's reliability is a workspace fundamental, not a
deferral candidate.

## Scope + constraint

See [`plans/active/api_host_chronic_impairment_2026_05_29.md`](../api_host_chronic_impairment_2026_05_29.md).

## Unblocks

- The autonomous loop's reliability (every plan-push, every worker /boot, every regen tick depends on this host).
- Removes the "have to manually reboot 2-3× a day" operational tax.
- Closes the Slack alert-storm pattern (mass "Slot N STALE" on every outage).

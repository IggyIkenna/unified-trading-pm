---
scope: [engineer, admin]
last_reviewed: 2026-05-30
---

# Agent Orchestrator — Host-Offline Failover Architecture

> **SSOT**: `agent-orchestrator/server/failover.py`
> **Plan**: `plans/active/harsh_pc_dispatch_failover_2026_05_30.md`
> **Overview pointer**: `codex/04-architecture/agent-orchestrator-overview.md` § "Host-offline failover lifecycle"
> **See also**: `codex/04-architecture/agent-orchestrator-autospawn.md` (worker-down on running host)

## Problem statement

When a host (e.g. harsh-pc) goes offline, its soft-pinned tasks have a
`target_slot` pointing to a slot on that host.  No dispatcher on any VM will
claim them because the task is targeted to an unreachable worker.  Without
failover, those tasks sit in the queue indefinitely.

`FailoverLoop` detects host silence and re-routes eligible tasks to fleet VMs
within 10–70 seconds.

---

## Scope: soft-pin failover only

| Task type | Behaviour |
|-----------|-----------|
| **Soft-pinned** (`failover_allowed: true`, default) | Eligible — re-routed to best fleet VM |
| **Hard-pinned** (`failover_allowed: false`) | Never failovered — stays on original target_slot |
| **Unrooted** (`target_slot IS NULL`) | Already routable by any slot; not affected |

`failover_allowed: false` is an explicit opt-in set in the plan task YAML and
passed through `regen_backlog_from_plan.py`. The default for all tasks is
`failover_allowed: true`.

---

## Trigger contract

A task is failovered when **all 5 gates** are true:

| Gate | Condition | Notes |
|------|-----------|-------|
| 1 Host offline | Source host `last_heartbeat_age > 600 s` | Conservative: tolerates laptop sleep, brief network gaps |
| 2 Task soft-pinned | `failover_allowed = True` | Hard pins (`false`) are never touched |
| 3 Task not dispatched | `dispatched_to IS NULL` AND `status = 'queued'` | Claimed tasks cannot be stolen |
| 4 Not already failovered | `failover_origin IS NULL` | Prevents double re-routing |
| 5 Fleet VM available | At least one VM passes affinity + headroom | Uses AutoSpawnLoop § 3 headroom contract |

"Source host" mapping: tasks whose `target_slot` points to a slot where
`git_status_host` matches the offline host's label or id.  Tasks with
`target_slot = NULL` are already globally routable and need no re-routing.

---

## Heartbeat lifecycle

```
Host online  → POST /api/heartbeat  every N seconds
              → orchestrator updates fleet_registry.json
              → last_heartbeat_seconds_ago resets to ~0

Host offline → no heartbeats
              → last_heartbeat_seconds_ago grows
              → at > 600 s: FailoverLoop detects "offline_host"
              → tasks re-routed to fleet VMs

Host returns → POST /api/heartbeat resumes
              → FailoverLoop detects "newly-returned host"
              → unclaimed failover tasks rolled back to original target_slot
```

The 600 s threshold is conservative by design: a 5-minute laptop sleep or VPN
reconnect should not trigger failover.  10 minutes of silence is a real outage.

---

## Affinity-matching algorithm

For each eligible task, pick the best fleet VM in four tiers (first match wins):

| Tier | Criterion | Notes |
|------|-----------|-------|
| 1 Repo overlap | `task.repos` ⊆ `vm.master_plans` entries in `orchestrator_vm_registry.yaml` | Strongest signal: the task was designed for this VM's repos |
| 2 Asset group | `task.asset_group` matches `vm.asset_group` | e.g. `defi`, `cefi`, `tradfi` |
| 3 Collision group | `task.collision_group` not already active on the target VM | Prevents collision-blocked dispatch |
| 4 Least loaded | Fewest `status='queued'` tasks in target VM's `state.db` | Load balancing among equal candidates |

First VM that passes all applicable filters wins.  On tie, random among finalists.

On re-assignment:
- `task.target_slot` ← fleet VM's slot id
- `task.failover_origin` ← offline host identifier (for audit + rollback)

---

## Rollback semantics

When the offline host's heartbeat returns (detected within one tick ≤ 60 s):

1. Query: `tasks WHERE failover_origin = <host> AND dispatched_to IS NULL AND status = 'queued'`
2. For each unclaimed failover task: clear `target_slot = NULL` and `failover_origin = NULL`
3. Log `failover_rolled_back` activity event per task

Already-claimed or already-done tasks are not rolled back — they ran on the
fleet target and that result stands.

---

## Audit trail

| Mechanism | What it preserves |
|-----------|------------------|
| `task.failover_origin` | Source host name; cleared on rollback |
| Cached heartbeat snapshot | The last `/api/heartbeat` from the offline host remains in `fleet_registry.json` — **never deleted on failover** |
| `log_activity` events | `failover_rerouted` + `failover_rolled_back` events in the activity log |

The cached heartbeat snapshot provides audit evidence of what tasks were
stranded on the offline host at the time of failover.

---

## Deployment: vm-orchestrator only

`FailoverLoop` runs on **vm-orchestrator only** — a single source of failover
decisions prevents race conditions between VMs.  Each VM running its own
FailoverLoop could independently re-route the same task to different targets.

Enable via systemd drop-in on vm-orchestrator:

```ini
# /etc/systemd/system/orchestrator.service.d/failover.conf
[Service]
Environment=ORCHESTRATOR_FAILOVER_ENABLED=true
```

Rollout script: `unified-trading-pm/scripts/orchestrator/enable_failover.sh`.

---

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `ORCHESTRATOR_FAILOVER_ENABLED` | `false` | Master on/off switch; must be `true` |
| `ORCHESTRATOR_FAILOVER_INTERVAL_SECONDS` | `60` | Tick cadence |
| `ORCHESTRATOR_FAILOVER_HEARTBEAT_THRESHOLD_SECONDS` | `600` | Offline threshold (10 min) |

---

## Interaction with collision_group

The affinity algorithm (Tier 3) respects `collision_group`: a task is not
re-routed to a VM that already has a task with the same `collision_group` in
its active queue.  This preserves the same mutual-exclusion invariant that
governs normal dispatch.

If no fleet VM is available after affinity filtering AND collision checking, the
task stays on the original offline target and is retried on the next tick.

---

## Anti-patterns (do not do these)

- **Never failover hard-pinned tasks** — `failover_allowed: false` means the
  operator pinned it for a reason (audit, debug, specific account).
- **Never failover dispatched tasks** (`dispatched_to IS NOT NULL`) — task steal
  is a race condition that causes duplicate work.
- **Never failover api-host queue items** — the api-host is a planning VM; its
  queue items are infrastructure tasks that run on-host only.
- **Never delete the cached heartbeat snapshot** on failover — it is the audit
  trail for what was stranded.
- **Never run FailoverLoop on multiple VMs simultaneously** — single-VM
  (`vm-orchestrator`) is the canonical source of failover decisions.

---

## Relationship to related systems

| System | Interaction |
|--------|------------|
| `AutoSpawnLoop` | Handles WORKER-down on a running host. FailoverLoop handles HOST-down. Different triggers; both required for full fleet autonomy. |
| `regen_backlog_from_plan.py` | Sets `failover_allowed` (default `True`) on each task row. FailoverLoop reads this field. |
| Manual `/api/tasks/<id>/reassign` | Manual override for individual tasks without waiting for FailoverLoop. |
| `collision_group` system | FailoverLoop respects collision exclusion when picking target VM. |

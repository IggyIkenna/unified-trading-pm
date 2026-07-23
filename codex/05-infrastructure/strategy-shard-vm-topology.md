---
doc_type: codex-ssot
title: Strategy-Service Shard VM Topology
summary:
  Strategy-service shard VM topology — one StrategySupervisor per (archetype × shard) VM, the
  strategy-{mode}-{archetype}-shard{N}-{ts} naming + singleton-lock triplet, the capacity thresholds (mem≥70 / cpu≥80 /
  occupancy), and manual (May-23) vs automated (E.2) shard auto-spawn.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-service, strategy-service]
scope: [engineer, admin]
tags: [strategy, infrastructure, deployment, defi, orchestrator]
related:
  [
    /codex/05-infrastructure/strategy-vm-launcher-shape.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /codex/04-architecture/per-client-isolation-architecture.md,
    /codex/04-architecture/client-lifecycle-event-bus.md,
  ]
created: 2026-05-20
authoritative_for: [strategy-service per-client shard VM topology (archetype×shard naming + auto-spawn)]
referenced_by:
  [
    /codex/04-architecture/client-lifecycle-event-bus.md,
    /codex/04-architecture/per-client-isolation-architecture.md,
    /codex/04-architecture/promote-workflow-architecture.md,
    /codex/05-infrastructure/strategy-vm-launcher-shape.md,
  ]
owner:
last_reviewed: 2026-05-20
code_refs:
---

# Strategy-Service Shard VM Topology

## Overview

Each strategy-service VM runs one `StrategySupervisor` process for exactly one (archetype × shard) pair. Shard 0 is the
default; additional shards are spawned by deployment-api when a VM saturates (Phase E.2, post-cutover). For May-23
launch, both live clients (Odum Research UK + defi-client-1) run on shard 0.

SSOT: `plans/active/per_client_isolation_and_venue_fanout_topology_2026_05_20.md`.

---

## VM Naming Convention

```
strategy-{mode}-{archetype}-shard{N}-{ts}
```

| Segment     | Values                                        | Example              |
| ----------- | --------------------------------------------- | -------------------- |
| `mode`      | `paper` / `live`                              | `live`               |
| `archetype` | `carry-staked-basis` / `arb-price-dispersion` | `carry-staked-basis` |
| `shard{N}`  | `shard0`, `shard1`, ...                       | `shard0`             |
| `ts`        | `YYYYMMDD` (UTC, day of launch)               | `20260523`           |

**Full example**: `strategy-live-carry-staked-basis-shard0-20260523`

**Singleton lock key**: `{mode}-{archetype}-{shard}` triplet (not the full name; timestamp suffix is for history).
Deployment-api checks for an existing RUNNING VM with the same triplet before launching a new one.

---

## Lifecycle Class

| Mode    | `lifecycle_class`     | `VM_PREFIX_TO_BUCKET` entry                                |
| ------- | --------------------- | ---------------------------------------------------------- |
| `live`  | `LONG_LIVED_LIVE`     | `strategy-live-{archetype}-shard` → strategy-store bucket  |
| `paper` | `SCHEDULED_RECURRING` | `strategy-paper-{archetype}-shard` → strategy-store bucket |

All entries in `deployment-service/scripts/vm/vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET`. The watchdog recognises the
shard suffix pattern — prefix match stops at `-shard` (everything after `shard{N}` is the timestamp).

---

## Capacity Thresholds

`StrategySupervisor.ShardCapacitySensor` polls every 10s via psutil. Emits `ShardCapacityEvent.SPAWN_NEW_SHARD` when ALL
of the following are true for 3 consecutive samples:

| Metric           | Default threshold      | Config key in clients.yaml   |
| ---------------- | ---------------------- | ---------------------------- |
| Memory usage     | ≥ 70%                  | `shard_memory_threshold_pct` |
| CPU usage        | ≥ 80%                  | `shard_cpu_threshold_pct`    |
| Client occupancy | ≥ `shard_capacity_max` | `shard_capacity_max`         |

Default `shard_capacity_max`: 5 clients per shard (operator-configurable in `clients.yaml`).

**May-23**: `shard_capacity_max=5`, 2 clients registered → occupancy = 40%. No ShardCapacityEvent expected.

---

## clients.yaml Location

```
deployment-service/configs/strategy/{archetype}/shard{N}/clients.yaml
```

Schema: `unified_api_contracts/canonical/domain/strategy/clients_yaml_schema.py`. Loaded by supervisor at boot;
hot-reloadable via `ClientLifecycleEvent.REGISTER`.

---

## Shard Auto-Spawn (May-23: manual only; E.2: automated)

### May-23 (manual)

When ShardCapacityEvent fires, deployment-api exposes:

```
POST /api/strategy/shard/spawn
{
  "archetype_id": "carry_staked_basis",
  "mode": "live",
  "shard_id": 1
}
```

Operator calls this manually. Deployment-api invokes the launch script:

```bash
bash deployment-service/scripts/vm/launch-strategy-live-vm.sh \
  --archetype carry_staked_basis \
  --shard 1 \
  --clients-yaml-path gs://deployment-scripts-${PID}/strategy/carry_staked_basis/shard1/clients.yaml
```

### Phase E.2 (post-cutover, 2026-05-28 target)

Deployment-service consumes `ShardCapacityEvent` from the event bus and automatically triggers the launch script.
Anti-thrash debounce: won't spawn more than 1 shard per archetype per 5min. Cost ceiling: operator-configured max VMs
per archetype. SSOT: `plans/active/per_client_isolation_and_venue_fanout_topology_2026_05_20.md` § Phase E.2.

---

## vm_zombie_watchdog Integration

`vm_zombie_watchdog.py` recognises the new name pattern via prefix match. Key mapping:

```python
VM_PREFIX_TO_BUCKET = {
    # ... existing entries ...
    "strategy-live-carry-staked-basis-shard": VmPrefixSpec(
        bucket="strategy-store-cefi-central-element-323112",
        lifecycle_class=LifecycleClass.LONG_LIVED_LIVE,
    ),
    "strategy-paper-carry-staked-basis-shard": VmPrefixSpec(
        bucket="strategy-store-cefi-central-element-323112",
        lifecycle_class=LifecycleClass.SCHEDULED_RECURRING,
    ),
    # ... similar entries per archetype ...
}
```

**Zone**: default `asia-northeast1-c`. Stockout fallback: `asia-northeast1-b` or `asia-northeast1-a` (same region only).
Cross-region fallback FORBIDDEN — all GCS data is in asia-northeast1.

---

## Drain Before Migration (HARD RULE)

Before any GCS migration or bucket SSOT cutover affecting strategy-store buckets:

1. Inventory running strategy VMs via `vm_zombie_watchdog.py`.
2. Deregister all clients (DEREGISTER events → supervisors drain workers gracefully).
3. Verify STOPPED events for all VMs.
4. Run manifest consolidator + snapshot.

SSOT: `plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md` § Phase 2.0 Stage 0.

---

## Composes With

- `/codex/04-architecture/per-client-isolation-architecture.md` — supervisor + ClientWorker model
- `/codex/04-architecture/client-lifecycle-event-bus.md` — ShardCapacityEvent definition
- `/codex/05-infrastructure/vm-tarball-deployment.md` — tarball creation + post-launch verification

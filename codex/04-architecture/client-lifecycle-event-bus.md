---
doc_type: codex-ssot
title: Client Lifecycle Event Bus
summary:
  Runtime client lifecycle event bus (REGISTER/DEREGISTER/QUARANTINE/UNQUARANTINE/CREDENTIAL_ROTATED) pushing
  operator→StrategySupervisor topology changes; ClientReady/ClientQuarantined/ShardCapacity events + the push-vs-pull
  hot-reload contract. Distinct from the onboarding state machine.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-api, strategy-service]
scope: [engineer, admin]
tags: [client-isolation, lifecycle, event-bus, strategy, orchestrator, credentials]
related:
  [
    /codex/04-architecture/per-client-isolation-architecture.md,
    /codex/04-architecture/client-lifecycle-state-machine.md,
    /codex/04-architecture/kill-switch-event-bus.md,
    /codex/05-infrastructure/strategy-shard-vm-topology.md,
  ]
created: 2026-05-20
authoritative_for: [client lifecycle event bus, ClientLifecycleEvent runtime topology events]
referenced_by:
  [/codex/04-architecture/client-lifecycle-state-machine.md, /codex/05-infrastructure/strategy-shard-vm-topology.md]
owner:
last_reviewed: 2026-05-20
code_refs:
---

# Client Lifecycle Event Bus

## Overview

The client lifecycle event bus carries runtime events for client registration, deregistration, quarantine, and
credential rotation. It is the push channel between the operator (or deployment-api) and the strategy-service
`StrategySupervisor`.

This is distinct from the **client onboarding state machine** (`client-lifecycle-state-machine.md`), which governs KYC
and deposit states before a client is live. The event bus governs per-client runtime topology — adding/removing a client
from a live strategy VM, not the KYC flow.

Cross-reference:

- `/codex/04-architecture/per-client-isolation-architecture.md` — supervisor subscription + ClientWorker spawn/reap
- `/codex/04-architecture/client-funds-isolation.md` — HARD RULE on cross-client isolation
- `/codex/04-architecture/kill-switch-event-bus.md` — the KillSwitchBusEvent pattern this extends

SSOT: `plans/active/per_client_isolation_and_venue_fanout_topology_2026_05_20.md`.

---

## Event Types

All UAC types in `unified_api_contracts/canonical/crosscutting/client_lifecycle_events.py`.

### `ClientLifecycleEvent` (operator → supervisor, push)

| kind                 | Payload fields                                                            | Action on supervisor                                 |
| -------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------- |
| `REGISTER`           | `client_id`, `archetype_id`, `shard_id`, `timestamp`, `reason`            | Spawn ClientWorker; wait CLIENT_READY (30s timeout)  |
| `DEREGISTER`         | `client_id`, `archetype_id`, `shard_id`, `timestamp`, `reason`            | Send SIGTERM to ClientWorker; wait drain (60s); reap |
| `QUARANTINE`         | `client_id`, `archetype_id`, `shard_id`, `timestamp`, `quarantine_reason` | Marks client slot unavailable; emitted by supervisor |
| `UNQUARANTINE`       | `client_id`, `archetype_id`, `shard_id`, `timestamp`, `reason`            | Re-register and re-spawn (operator-triggered)        |
| `CREDENTIAL_ROTATED` | `client_id`, `archetype_id`, `shard_id`, `timestamp`, `venue_id`          | Bypass KMS poll; immediate CredentialStore.reload()  |

### `ClientReadyEvent` (ClientWorker → supervisor → monitoring)

Emitted by ClientWorker after successful preflight:

| Field               | Type                                  | Meaning                    |
| ------------------- | ------------------------------------- | -------------------------- |
| `client_id`         | str                                   |                            |
| `archetype_id`      | str                                   |                            |
| `shard_id`          | int                                   |                            |
| `venue_auth_status` | `dict[venue_id, OK\|FAILED\|SKIPPED]` | Per-venue preflight result |
| `timestamp`         | datetime                              |                            |

### `ClientQuarantinedEvent` (supervisor → monitoring)

Emitted when preflight fails or restart attempts exhausted:

| Field                 | Type                    | Meaning                                                                                  |
| --------------------- | ----------------------- | ---------------------------------------------------------------------------------------- |
| `client_id`           | str                     |                                                                                          |
| `archetype_id`        | str                     |                                                                                          |
| `shard_id`            | int                     |                                                                                          |
| `quarantine_reason`   | `QuarantineReason` enum | `PREFLIGHT_FAILED` / `RESTART_EXHAUSTED` / `INSUFFICIENT_BALANCE` / `VENUE_AUTH_TIMEOUT` |
| `last_error_message`  | str                     |                                                                                          |
| `retry_after_seconds` | int                     | 0 = permanent until operator UNQUARANTINE                                                |

### `ShardCapacityEvent` (supervisor → deployment-api)

Emitted when supervisor detects VM saturation (3 consecutive samples: memory ≥ 70% OR cpu ≥ 80% OR clients ≥
`shard_capacity_max`):

| Field                | Type                       | Meaning                                   |
| -------------------- | -------------------------- | ----------------------------------------- |
| `archetype_id`       | str                        |                                           |
| `shard_id`           | int                        | Current shard that is saturating          |
| `occupancy_pct`      | float                      | Current client count / shard_capacity_max |
| `memory_pct`         | float                      | psutil virtual_memory().percent           |
| `cpu_pct`            | float                      | psutil cpu_percent(interval=1)            |
| `recommended_action` | `ShardCapacityAction` enum | Currently: `SPAWN_NEW_SHARD` only         |

Consumer: deployment-api `/api/strategy/shard/spawn` endpoint (manual trigger for May-23; auto-consumption is
post-cutover — `plans/active/per_client_isolation_and_venue_fanout_topology_2026_05_20.md` § Phase E.2, tracked in
`plans/epics/client_isolation_and_governance_master.md`).

---

## Push vs Pull — Hot-Reload Contract

| What changes                        | Mechanism                           | Why                                                                                       |
| ----------------------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------- |
| Client added / removed              | Push via bus                        | Low-frequency operator action; bus is the right surface; composes with KillSwitch pattern |
| Client quarantine / unquarantine    | Push via bus                        | Operator or supervisor-initiated; must be immediate                                       |
| Credential rotation (manual)        | Push `CREDENTIAL_ROTATED` bus event | Operator-triggered; must bypass poll interval and reload immediately                      |
| Credential rotation (automated KMS) | Pull (`ClientCredentialKmsPoller`)  | High-frequency automated rotation; push would couple supervisor to rotation cadence       |

**Hybrid rule**: push for topology changes + operator-driven credential rotation; pull for automated KMS rotation. The
`CREDENTIAL_ROTATED` bus event is additive — it triggers an immediate reload regardless of poll-cycle state.

---

## Supervisor Subscription

`StrategySupervisor` extends `ClientLifecycleBusSubscriberBase` (UTL), which itself extends
`KillSwitchBusSubscriberBase` (UTL Phase 5 of `strategy_repo_consolidation_2026_05_19.md`). Subscription is wired at
supervisor boot; no restart required to pick up new events.

```python
class StrategySupervisor(StrategySupervisorBase, ClientLifecycleBusSubscriberBase):
    def on_register(self, event: ClientLifecycleEvent) -> None:
        self._client_admission_controller.spawn(event.client_id, event.shard_id)

    def on_deregister(self, event: ClientLifecycleEvent) -> None:
        self._client_admission_controller.drain_and_reap(event.client_id, timeout_s=60)

    def on_credential_rotated(self, event: ClientLifecycleEvent) -> None:
        self._ipc_pipe.send({"kind": "CREDENTIAL_ROTATED", "venue_id": event.venue_id})
```

---

## Composes With

- `/codex/04-architecture/kill-switch-event-bus.md` — parent bus pattern; `ClientLifecycleBusSubscriberBase` extends
  `KillSwitchBusSubscriberBase`
- `/codex/04-architecture/per-client-isolation-architecture.md` — how the supervisor uses these events
- `/codex/05-infrastructure/strategy-shard-vm-topology.md` — shard naming and capacity events

---
scope: [engineer, admin]
title: Deployment-Service Event Sink Chain
type: infrastructure
status: living
last_reviewed: 2026-05-17
owner: deployment-platform
---

# Deployment-Service Event Sink Chain

**Author**: slot-2 agent  
**Date**: 2026-05-15  
**Scope**: All event emission paths in deployment-service — orchestrator, VM heartbeat, GCS tee  
**References**: `vm-deployment-events-audit.md`, `vm-event-emission-audit.md`

---

## Summary

Deployment-service has **two distinct** event emission chains that run concurrently during a VM run. They write to
different sinks with different retention policies and should not be confused.

| Chain                | Emitter                                       | Sink                                                 | Retention        | Queryable      |
| -------------------- | --------------------------------------------- | ---------------------------------------------------- | ---------------- | -------------- |
| A — Orchestrator     | `orchestrator.py`, `cli/main.py`              | `sink=None` (UTL null sink)                          | local log only   | no             |
| B — VM heartbeat     | `heartbeat_cli.py`, `deployment_heartbeat.py` | `PubSubEventSink("deployment-events")`               | 7 days (Pub/Sub) | yes (pull sub) |
| B2 — Monitor consume | `monitor.py`                                  | GCS direct write                                     | permanent        | yes            |
| C — GCS tee          | `vm-exec-with-gcs-tee.sh`                     | `gs://{bucket}/vm-logs/{vm}/run.log` + `EXIT_STATUS` | permanent        | yes            |

---

## Chain A — Orchestrator / API events (null sink)

```
deployment-service CLI / API
  └─► orchestrator.py: setup_events(service_name="deployment-service", mode="batch", sink=None)
        └─► UTL null sink: events written to local logger only
              └─► No external emission — events stay in Cloud Logging / stdout
```

**Pattern**: `sink=None` is the UTL null-sink convention — events are still logged via Python `logging` but not
forwarded to Pub/Sub or GCS.

**When used**:

- `cli/main.py`: `setup_events(..., sink=None)` for local mode
- `orchestrator.py T1Orchestrator.__init__`: `setup_events(..., sink=None)` for batch mode (lazy, once per worker)

---

## Chain B — VM heartbeat events (PubSub → pull subscription → GCS via monitor)

```
VM startup (gcloud instances create --metadata startup-script=...)
  └─► vm-exec-with-gcs-tee.sh
        └─► heartbeat_cli.py (background daemon on VM)
              └─► _init_events():
                    PubSubEventSink(
                        project_id=PROJECT_ID,
                        topic=DEPLOYMENT_EVENTS_TOPIC,   # default: "deployment-events"
                    )
              └─► setup_events(service_name="vm-heartbeat-daemon", mode="batch", sink=PubSubEventSink)
              └─► HeartbeatDaemon.run():
                    ├─► DEPLOYMENT_STARTED  → Pub/Sub topic "deployment-events"
                    ├─► DEPLOYMENT_PROGRESS → Pub/Sub topic (every 60s)
                    └─► DEPLOYMENT_COMPLETED / DEPLOYMENT_FAILED → Pub/Sub topic

      Also on VM: deployment_heartbeat.py (GCS-registry helper)
              └─► log_event(DEPLOYMENT_STARTED / DEPLOYMENT_PROGRESS / DEPLOYMENT_COMPLETED)
                    └─► same PubSubEventSink (UTL global, initialized by heartbeat_cli.py)
```

**Pub/Sub topic**: `deployment-events` (project `central-element-323112`)  
**Retention**: 7 days (Pub/Sub default)  
**Active subscriptions**:

- `deployment-events-monitor` — pull, consumed by `monitor.py` → writes deployment registry to
  `gs://deployment-status-{project}/deployments/{deploy_id}/...`

**Gap**: No push subscription exports events to `gs://central-element-323112-events/` for permanent archival. All other
services use `GCSEventSink` directly and land in that bucket. VM heartbeat events have 7-day TTL only. See
`vm-deployment-events-audit.md` for the operator action required to add a GCS export sub.

**Local mode**: `heartbeat_cli.py` uses `LocalFsEventSink` when `CLOUD_PROVIDER=local`, writing to
`/tmp/vm-heartbeat-events.jsonl`.

---

## Chain C — GCS tee (stdout / stderr + exit code)

```
vm-exec-with-gcs-tee.sh
  ├─► stdout+stderr streamed via `gcloud alpha storage cp - ...` (streaming gsutil upload)
  │     └─► gs://{deployment_scripts_bucket}/vm-logs/{vm_name}/run.log
  └─► EXIT_STATUS file written on script exit
        └─► gs://{deployment_scripts_bucket}/vm-logs/{vm_name}/EXIT_STATUS
```

**Bucket**: `deployment-scripts-{project_id}` (e.g. `deployment-scripts-central-element-323112`)  
**Retention**: permanent (no lifecycle rule on this bucket as of 2026-05-15)  
**Consumers**:

- `analyze_vm_costs.py` — reads `EXIT_STATUS` mtime for cost attribution
- `vm_zombie_watchdog.py` — reads `run.log` mtime for shard heartbeat staleness check
- Human operators — read `run.log` for debugging VM failures

---

## Trace Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────┐
│                        DEPLOYMENT-SERVICE                       │
│                                                                 │
│  cli/main.py ──► setup_events(sink=None) ──► local log only    │
│  orchestrator.py                                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          VM (GCE)                               │
│                                                                 │
│  vm-exec-with-gcs-tee.sh                                        │
│    ├── stdout/stderr ──────────────────────────────────────────►│ gs://deployment-scripts-*/vm-logs/{vm}/run.log
│    └── EXIT_STATUS ────────────────────────────────────────────►│ gs://deployment-scripts-*/vm-logs/{vm}/EXIT_STATUS
│                                                                 │
│  heartbeat_cli.py (daemon)                                      │
│    └── PubSubEventSink ────────────────────────────────────────►│
│                                                                 │       Pub/Sub topic: deployment-events
│  deployment_heartbeat.py (register/heartbeat/complete)          │          │ (7-day retention)
│    └── log_event (same global PubSubEventSink) ───────────────►│          │
└─────────────────────────────────────────────────────────────────┘          │
                                                                             │
                                               ┌─────────────────────────────┘
                                               ▼
                                  subscription: deployment-events-monitor
                                               │
                                               ▼ (monitor.py pulls)
                               gs://deployment-status-*/deployments/{id}/...
                               (permanent registry)

                                  ❌ NO export sub to
                                  gs://central-element-323112-events/
                                  (gap — heartbeat events ephemeral)
```

---

## Canonical Sink Decision Tree

When adding a new event emitter to deployment-service:

```
Is this emitted FROM A VM (running as a startup script)?
  YES → use PubSubEventSink(topic="deployment-events")
        (initialized in heartbeat_cli.py; all VM-side emitters share the global sink)
  NO  → are events needed for permanent archival / cross-service querying?
          YES → use GCSEventSink (standard pattern for non-VM services)
          NO  → sink=None is acceptable (local log only)
```

---

## Known Gaps (tracked in deployment-and-qg-strategy.md Phase 8.A)

| Gap                                                                            | Severity | Operator action                                                                   |
| ------------------------------------------------------------------------------ | -------- | --------------------------------------------------------------------------------- |
| No GCS export sub for `deployment-events` Pub/Sub topic                        | P2       | Add push sub → GCS export (Cloud Console or `gcloud pubsub subscriptions create`) |
| heartbeat events 7-day TTL only — no permanent VM event log in events bucket   | P2       | Depends on above gap being closed                                                 |
| `deployment-service` API/orchestrator uses `sink=None` — no external telemetry | P3       | Add `GCSEventSink` to API server startup                                          |

---

## File Pointers

| Component                  | File                                     |
| -------------------------- | ---------------------------------------- |
| VM heartbeat daemon        | `deployment_service/vm/heartbeat_cli.py` |
| VM-side lifecycle helper   | `scripts/vm/deployment_heartbeat.py`     |
| GCS tee wrapper            | `scripts/vm/vm-exec-with-gcs-tee.sh`     |
| PubSub consumer            | `deployment_service/monitor.py`          |
| Orchestrator events setup  | `deployment_service/orchestrator.py:227` |
| CLI events setup           | `deployment_service/cli/main.py:90`      |
| Smoke-verified event trace | `vm-deployment-events-audit.md`          |
| VM event emission audit    | `vm-event-emission-audit.md`             |

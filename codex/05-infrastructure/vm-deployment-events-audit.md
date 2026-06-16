---
scope: [engineer, admin]
title: VM Deployment Events — GCS / PubSub Forwarding Audit
type: infrastructure
status: living
last_reviewed: 2026-05-17
owner: deployment-platform
---

# VM Deployment Events — GCS / PubSub Forwarding Audit

**Author**: slot-2 agent  
**Date**: 2026-05-15  
**Scope**: VM event sink chain — heartbeat_cli.py through PubSub to GCS  
**Smoke VM**: `measure-honest-coverage-20260515-115454` (exit 0)

---

## Summary

| Check                                                | Result                                                  |
| ---------------------------------------------------- | ------------------------------------------------------- |
| DEPLOYMENT_STARTED emitted at VM startup             | ✅ Confirmed (smoke log)                                |
| DEPLOYMENT_COMPLETED emitted at exit                 | ✅ Confirmed (smoke log)                                |
| DEPLOYMENT_FAILED emitted on error path              | ✅ Code path confirmed (HeartbeatDaemon `failed_event`) |
| Events reach PubSub topic `deployment-events`        | ✅ Confirmed via `mode=batch` PubSubEventSink           |
| PubSub → GCS auto-export                             | ❌ **Gap: not configured**                              |
| GCS event path under `central-element-323112-events` | ❌ No `vm-heartbeat-daemon` directory exists            |

**Outcome**: Event emission is working end-to-end through PubSub. The `central-element-323112-events` GCS bucket has no
auto-export subscription from `deployment-events` topic. Events are retained 7 days in PubSub only.

---

## Event Chain (Actual)

```
VM startup
  └─► vm-exec-with-gcs-tee.sh
        └─► heartbeat_cli.py main()
              ├─► _init_events() → PubSubEventSink(topic="deployment-events")
              ├─► setup_events(mode="batch", sink=PubSubEventSink)
              └─► HeartbeatDaemon.run()
                    ├─► emit DEPLOYMENT_STARTED  → pubsub topic
                    ├─► emit DEPLOYMENT_PROGRESS → pubsub topic (every 60s)
                    └─► emit DEPLOYMENT_COMPLETED / DEPLOYMENT_FAILED → pubsub topic

PubSub topic: deployment-events (7-day retention)
  └─► subscription: deployment-events-monitor (pull, 7-day retention)
       └─► consumed by: deployment-service monitor.py (direct GCS writes to
                         deployment-status-{project_id}/deployments/{id}/...)
```

**No PubSub → GCS export subscription exists** for `deployment-events`. The other services writing to
`gs://central-element-323112-events/events/` use `GCSEventSink` directly (not via PubSub).

---

## Smoke Verification

**VM**: `measure-honest-coverage-20260515-115454`  
**Log**: `gs://deployment-scripts-central-element-323112/vm-logs/measure-honest-coverage-20260515-115454/run.log`

```
2026-05-15 06:28:32,027 INFO Event logging initialized: mode=batch, service=vm-heartbeat-daemon
2026-05-15 06:28:32,447 INFO DEPLOYMENT_STARTED 332a8913-91d4-46f7-adb9-c1cd2da54773
2026-05-15 06:28:32,448 INFO heartbeat loop started interval=60s
2026-05-15 06:28:33,922 INFO DEPLOYMENT_COMPLETED 332a8913-91d4-46f7-adb9-c1cd2da54773 (exit_code=0)
```

Exit status: 0. DEPLOYMENT_STARTED + DEPLOYMENT_COMPLETED both emitted within 2s of startup.

---

## Gap: No PubSub → GCS Export for vm-heartbeat-daemon

### What Exists

All other services (`instruments-service`, `market-tick-data-service`, etc.) write events directly via `GCSEventSink` to
`gs://central-element-323112-events/events/{service}/{date}/...`. The vm-heartbeat-daemon is the **only service using
PubSubEventSink** instead of GCSEventSink for its lifecycle events.

### Why This Matters

Events land in PubSub (7-day TTL) but are not archived to GCS. After 7 days, DEPLOYMENT_STARTED / DEPLOYMENT_COMPLETED
history is lost. The `deployment-events-monitor` subscription is pull-based — if nothing consumes it, messages expire.

### Recommended Fix

Add a GCS export subscription to `deployment-events` topic that streams to
`gs://central-element-323112-events/events/vm-heartbeat-daemon/{date}/`. Alternatively, switch heartbeat_cli.py to use
`GCSEventSink` directly (consistent with all other services).

The simpler fix is switching heartbeat_cli.py to `GCSEventSink` — avoids a separate subscription and is consistent with
the workspace pattern. This is a P2 (non-blocking for May-23, events still visible for 7 days via PubSub).

---

## References

- `deployment-service/deployment_service/vm/heartbeat_cli.py` — `_init_events()` configures PubSubEventSink
- `deployment-service/scripts/setup-pubsub.sh` — topic `deployment-events` + `deployment-events-monitor` subscription
- `unified-trading-library/unified_trading_library/` — `GCSEventSink` / `PubSubEventSink` implementations
- `codex/05-infrastructure/vm-event-emission-audit.md` — event emission architecture

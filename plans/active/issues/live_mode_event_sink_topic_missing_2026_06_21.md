---
title: Live-mode lifecycle event sink publishes to non-existent `{service_name}-events` topics (fleet-wide latent)
created: 2026-06-21
source:
  - unified-trading-library/unified_trading_library/service_framework/_sink_factory.py
  - deployment-service/terraform/gcp/main.tf
  - first-ever live MTDS launch (mtds-live-cefi-hyperliquid-trades, 2026-06-21)
locked_by: live-defi-rollout
priority: P2
status: active
---

# Live-mode event sink → missing `{service_name}-events` Pub/Sub topics (all AGs)

## What I found

The **first-ever operational live MTDS launch** (`mtds-live-cefi-hyperliquid-trades`,
`--mode live --operation websocket-streaming`) crashed at startup with:

```
google.api_core.exceptions.NotFound: 404 Resource not found (resource=market-tick-data-service-events).
  … event_sink.write_event → PubSubEventSink.publish(self._topic, …)
  → DEPLOYMENT_FAILED (exit_code=1)
```

Root cause: UTL `service_framework/_sink_factory.py:44` derives the live lifecycle-event topic as
`topic = f"{service_name}-events"` → for MTDS that is **`market-tick-data-service-events`**, which **does not exist**.
The terraform-managed canonical topic list (`deployment-service/terraform/gcp/main.tf` `pubsub_topic_names`, "from the
InternalPubSubTopic enum") ships a **shared** `service-lifecycle-events` topic and **no** per-service `{service}-events`
topics. So the sink-factory naming convention (`{service_name}-events`, per-service) and the terraform/enum canonical
(`service-lifecycle-events`, shared) **disagree**.

This was **never hit before because live mode has never run on any AG** (the 2026-06-21 snapshot's structural fact #1:
LIVE = 0 rows fleet-wide). Live (`--mode live` → UTL PubSubIO) is the only path that publishes lifecycle events to
Pub/Sub; batch (`--mode batch` → BatchIO) does not, so every prior batch VM was unaffected.

**Blast radius — fleet-wide for live mode:** every service's live launch will hit the same wall against its own
`{service_name}-events` topic:

- `market-tick-data-service-events` (MTDS live — all 5 asset groups; one service) — **created 2026-06-21 (unblock)**.
- `market-data-processing-service-events` (MDPS live) — still missing (note: the existing
  `market-data-processing-events` is a DIFFERENT name).
- features / strategy / execution service live launches — same pattern, topics missing.

## Why it matters

It silently blocked the entire live pipeline from ever starting (any live producer crashes on the STARTED event before
doing any work). The cefi live row is unblocked by creating `market-tick-data-service-events`, but the systemic naming
mismatch will re-block every other AG/service's live launch.

## Recommended decision (live_pipeline epic)

Pick ONE canonical convention and align both sides:

- **Option A (preferred — minimal infra):** fix UTL `_sink_factory.py` to publish lifecycle events to the canonical
  **`service-lifecycle-events`** topic (the InternalPubSubTopic enum value that already exists fleet-wide), instead of
  `f"{service_name}-events"`. One UTL change unblocks all services' live mode; no per-service topics needed. (T0 change
  → fleet promote.)
- **Option B:** keep `{service_name}-events` per-service and add every service's topic to terraform `pubsub_topic_names`
  - apply (more topics, per-service observability isolation).

Interim: `market-tick-data-service-events` created via gcloud (unmanaged by terraform until the convention is decided).
If Option B is chosen, add it (and the other `{service}-events`) to `pubsub_topic_names`; if Option A, delete it after
the UTL fix lands.

---
doc_type: issue
title: prediction live-capture VMs fail to publish CandleBoundaryCrossedEvent — target Pub/Sub topic doesn't exist
summary: >
  While verifying the mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md P3 fix on the 4 live prediction
  capture VMs, found `_publish_boundary_event` in `market_tick_data_service/live/websocket_runner.py` raising
  `google.api_core.exceptions.NotFound: 404 Resource not found (resource=market-tick-data-service-events)` on every
  attempted publish. Confirmed directly against the live Pub/Sub API (not inferred from the traceback alone) — the topic
  `projects/central-element-323112/topics/market-tick-data-service-events` genuinely does not exist. Grepping both
  `market-tick-data-service` and `deployment-service` for the literal topic name finds no Terraform declaration anywhere
  (one unrelated hit in `qg_snapshot_scheduler.tf`) — this isn't a declared-but-undeployed drift, the topic appears to
  have never been provisioned. Downstream impact: `CandleBoundaryCrossedEvent` is what feeds the MDPS features-service
  pipeline's live boundary-crossing consumption per this module's own docstring ("publish CandleBoundaryCrossedEvent to
  the prediction Redis Stream for the downstream MDPS features-service pipeline") — if this has been failing since
  before 2026-07-27 (the VMs' original launch, now confirmed still failing after redeploying fresh code today), live
  prediction features may have been running on a stale/absent boundary signal for over a week. NOT a manifest-write
  blocker (confirmed separately: per-VM manifest shards ARE updating continuously via a different code path —
  `ManifestWriter: per-VM shard updated` log lines are healthy and frequent — so this is isolated to the boundary-event
  side, not silently blocking prediction data capture itself).
status: open
nature: issue
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [live-pipeline, pubsub, boundary-event, mdps, prediction, data-correctness]
related:
  [
    /plans/active/issues/mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md,
    /codex/05-infrastructure/live-pipeline-architecture.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
  ]
created: 2026-08-03
parent_epic: manifest_master
priority: P2
source:
  found during mtds_prediction_rebuild_instrument_type_mismatch-001's live-VM redeploy verification, interactive
  session, 2026-08-03
assigned_vm: NA
execution_scope: local-only
locked_by:
resolved_by:
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-03
---

# prediction live-capture VMs fail to publish CandleBoundaryCrossedEvent — target Pub/Sub topic missing

## What I found

Live evidence, `prediction-live-kalshi-book-snapshot-5-20260803-182158`'s `run.log` (a freshly-relaunched VM, today,
running the latest code):

```
google.api_core.exceptions.NotFound: 404 Resource not found (resource=market-tick-data-service-events).
```

Full traceback origin: `websocket_runner.py::flush_window` → `_flush_instrument_window` → `_publish_boundary_event` →
UTL `log_event("MTDS_LIVE_BOUNDARY_PUBLISHED", ...)` → `event_sink.py::write_event` → `providers/gcp.py::publish` →
`client.publish(self._topic, data)`.

Confirmed directly against the live Pub/Sub API
(`GET https://pubsub.googleapis.com/v1/projects/central-element-323112/topics/market-tick-data-service-events` →
`404 NOT_FOUND`), not just read off the traceback. Grepped both `market-tick-data-service` and `deployment-service`
repos for the literal string `market-tick-data-service-events` — the only hit is an unrelated mention in
`deployment-service/terraform/gcp/qg_snapshot_scheduler.tf`; there is no `google_pubsub_topic` resource declaring it
anywhere. This is not declared-but-undeployed Terraform drift — the topic appears to have never been provisioned.

Also observed (same VM, same log window) a SEPARATE, already-understood, already-handled failure: `MessageTooLargeError`
on oversized `book_snapshot_5` publishes — this one IS a known, documented, already-mitigated issue
(`_ws_window_helpers.py`'s `record_flush_failed` docstring: "2026-07-30 fix: a raising flush now records this instead of
silently vanishing with zero manifest trace ... 600 occurrences/day"). Not part of this finding; noted only to
distinguish it from the genuinely-new missing-topic issue.

## Why it matters

- `CandleBoundaryCrossedEvent` is this module's mechanism for signaling the downstream MDPS features-service pipeline
  that a live 1-minute boundary has closed for a given prediction instrument — per the module's own docstring, this is
  the live-mode replacement for whatever batch-mode boundary signal features-service otherwise relies on.
- If this topic has been missing since these VMs' original 2026-07-27 launch (unconfirmed — I did not check historical
  log content given the 12GB+ log file size, but the topic itself shows zero provisioning evidence in either repo's
  IaC), live prediction feature computation may have been running without its intended boundary-crossing trigger for
  over a week, silently — the publish failure is caught/logged but does not crash the VM or block the manifest write
  path (confirmed: manifest shards ARE updating normally on all 4 VMs post-redeploy).
- Per CLAUDE.md "Data pipeline correctness is the heartbeat" this is a real, live, data-correctness-adjacent gap
  warranting an issue doc + eventual fix, but it is explicitly OUT OF SCOPE for
  `mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md`'s own P3 (that todo's fix + durability verification
  is complete and unaffected by this separate finding).

## Recommended decision

1. Confirm whether MDPS features-service actually consumes `market-tick-data-service-events` /
   `CandleBoundaryCrossedEvent` for prediction today, or whether it has its own independent trigger (e.g. a polling
   loop) that makes this topic non-critical in practice — this determines real severity/priority.
2. If genuinely needed: provision the topic (`google_pubsub_topic` in `deployment-service/terraform/gcp/`, matching
   whatever naming/topic-per-service convention the rest of this Terraform tree uses for other services' event topics)
   and any required subscription(s) on the consuming side.
3. Check whether this same missing-topic gap affects OTHER asset groups' live runners (this module is shared across
   cefi/defi/tradfi/sports/prediction per its own docstring) — this investigation was scoped to prediction only.

## Todos

- [ ] [OPERATOR] P1. Confirm whether MDPS features-service prediction pipeline actually depends on
      `CandleBoundaryCrossedEvent` / `market-tick-data-service-events` today (a real live-data-correctness gap if so,
      lower priority if it has an independent trigger) — this is a judgment call about downstream severity, not a
      mechanically-determinable fact.
- [ ] [INFRA] P2. If confirmed needed, provision the missing `market-tick-data-service-events` Pub/Sub topic (+
      subscription(s)) via Terraform in `deployment-service/terraform/gcp/`, matching the existing per-service topic
      convention. (repo: deployment-service)
- [ ] [DATA] P3. Check whether cefi/defi/tradfi/sports live runners (same shared `websocket_runner.py`) hit the same
      missing-topic gap, or whether this is prediction-specific (e.g. a topic that exists for other asset groups but was
      never created for prediction specifically). (repo: market-tick-data-service)

## Progress Log

- **2026-08-03 (interactive session)**: found while verifying the P3 durability fix on the 4 relaunched prediction-live
  VMs. Confirmed the topic doesn't exist via a direct Pub/Sub API read (not inference). Did not investigate further
  (historical duration, cross-asset-group scope, or MDPS consumption dependency) — filed as its own tracked issue per
  the findings-become-todos rule rather than expanding the P3 fix's scope.

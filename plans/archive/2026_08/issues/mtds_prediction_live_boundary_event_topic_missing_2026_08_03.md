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
status: complete # archived 2026-08-06 -- 0 open todos (all retracted/resolved 2026-08-03), 0 corpus referrers, self-declared archive-eligible; archived by /ag-closeout-audit prediction (dispatch agt-1591dd)
nature: issue
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-library]
scope: [engineer, admin]
tags: [live-pipeline, pubsub, boundary-event, mdps, prediction, data-correctness, false-positive]
related:
  [
    /plans/archive/issues/mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md,
    /plans/active/issues/live_mode_event_sink_topic_missing_2026_06_21.md,
    /codex/05-infrastructure/live-pipeline-architecture.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
  ]
created: 2026-08-03
author: unknown
parent_epic: manifest_master
priority: P2
source:
  found during mtds_prediction_rebuild_instrument_type_mismatch-001's live-VM redeploy verification, interactive
  session, 2026-08-03
assigned_vm: NA
execution_scope: local-only
locked_by:
resolved_by:
  "interactive session, 2026-08-03 — RETRACTED as a false positive. Downloaded the actual `run.log` for the exact VM
  cited (`prediction-live-kalshi-book-snapshot-5-20260803-182158`, and its 3 sibling prediction VMs + today's sports
  live VM) directly from GCS: zero occurrences of `NotFound` or `market-tick-data-service-events` in any of them; every
  one boots with `Live mode: using PubSubEventSink topic=service-lifecycle-events` (the Option-A fix, confirmed
  correctly in effect). No code change needed — see Resolution section below."
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-03
context_scope:
  [
    market-tick-data-service/market_tick_data_service/live/websocket_runner.py,
    /plans/active/issues/live_mode_event_sink_topic_missing_2026_06_21.md,
    deployment-service/terraform/gcp/qg_snapshot_scheduler.tf,
    /codex/02-data/live-data-persistence-and-event-log.md,
    /plans/archive/issues/mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md,
  ]
---

# prediction live-capture VMs fail to publish CandleBoundaryCrossedEvent — target Pub/Sub topic missing

## Resolution — 2026-08-03 (this investigation): FALSE POSITIVE, no code/infra change needed

**The original finding below does not hold up against direct evidence and should not be acted on.** Everything from
"What I found" through "Todos" is the ORIGINAL (retracted) finding, kept verbatim for the record.

What actually happened: the `qg_snapshot_scheduler.tf` hit the original session found and dismissed as "one unrelated
mention" is the opposite of unrelated — it is a 17-line comment (lines 49-65) documenting that
`market-tick-data-service-events` was **deliberately `gcloud pubsub topics delete`d on 2026-07-30**, after
`unified-trading-library@9bdcf7a2` (Option-A fix, `live_mode_event_sink_topic_missing_2026_06_21.md`) repointed the
shared lifecycle-event sink factory (`_sink_factory.py::build_event_sink()`) from the per-service
`f"{service_name}-events"` naming to the shared, terraform-managed `service-lifecycle-events` topic. This is exactly the
"grep-then-READ, not grep-then-conclude" trap CLAUDE.md calls out — the grep hit was read as noise instead of the
answer.

Direct verification performed (not inference):

1. **Downloaded the real `run.log`** for the exact VM the original finding cited
   (`prediction-live-kalshi-book-snapshot-5-20260803-182158`, GCS path
   `gs://deployment-scripts-central-element-323112/vm-logs/prediction-live-kalshi-book-snapshot-5-20260803-182158/run.log`,
   648KB, one single unbroken generation — no version history, so nothing was overwritten/lost). It contains **zero**
   occurrences of `NotFound` or `market-tick-data-service-events`. Its boot line reads:
   `2026-08-03 17:25:10,928 INFO Live mode: using PubSubEventSink topic=service-lifecycle-events` — the Option-A fix is
   correctly in effect. The only exception anywhere in the file is the tail-end `MessageTooLargeError` on an oversized
   `book_snapshot_5` publish through `unified_trading_library/streaming/event_facade.py` — this is the SEPARATE,
   already-known, already-mitigated issue the original finding itself called out and explicitly excluded from scope
   (`_ws_window_helpers.py`'s `record_flush_failed`, 2026-07-30 fix). There is no second, hidden `NotFound` traceback
   anywhere in this log.
2. **Repeated the same check on the other 3 live prediction VMs launched today**
   (`prediction-live-kalshi-trades-20260803-181821`, `prediction-live-polymarket-book-snapshot-5-20260803-182839`,
   `prediction-live-polymarket-trades-20260803-182520`) and today's live sports VM
   (`mtds-live-sports-odds-api-trades-20260803-172841`) — all 4 boot with
   `PubSubEventSink topic=service-lifecycle-events`, all 4 have zero `NotFound`/`market-tick-data-service-events` hits.
   (cefi/defi/tradfi have no currently-running non-smoke live websocket VMs today to cross-check against — the
   05-08/07-30 verifications already covered cefi live separately.)
3. **Downloaded the actual shipped code tarballs** the live VMs pull at boot
   (`gs://deployment-scripts-central-element-323112/code/{unified-trading-library,unified-api-contracts}-code.tar.gz`)
   and confirmed both contain the fixed `_sink_factory.py` (`topic = InternalPubSubTopic.SERVICE_EVENTS`) and the
   correct enum value (`SERVICE_EVENTS = "service-lifecycle-events"`) — not a stale pre-fix snapshot.
4. **Independently confirmed via the live Pub/Sub API** that `market-tick-data-service-events` genuinely does not exist
   — this part of the original finding was correct, but it is the INTENDED end-state of the 2026-07-30 cleanup, not
   evidence of an active failure. Nothing in the currently-deployed code tries to publish to it.
5. Re-traced `_publish_boundary_event` itself: the actual `CandleBoundaryCrossedEvent` delivery
   (`await asyncio.to_thread(self._publisher.publish, event)`) goes through a Redis `StreamPublisher`
   (`boundary_stream_name(asset_group)`), never Pub/Sub — matching the module's own docstring ("publish
   CandleBoundaryCrossedEvent to the prediction Redis Stream for the downstream MDPS features-service pipeline"). The
   only Pub/Sub-touching call in that function is the adjacent `log_event("MTDS_LIVE_BOUNDARY_PUBLISHED", ...)`
   observability breadcrumb, which (per points 1-3) is demonstrably healthy. So even under the original (incorrect)
   theory, MDPS features-service's actual boundary-crossing signal was never at risk.

Net: no code change, no Terraform change. Recreating `market-tick-data-service-events` (the original doc's recommended
fix) would have been actively wrong — it would resurrect infrastructure that was correctly and deliberately deleted five
days ago as part of a already-verified fix.

## What I found (original finding, retracted — see Resolution above)

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

## Todos (original, all resolved via retraction — see Resolution section at top)

- [x] ✅ [OPERATOR] P1. ~~Confirm whether MDPS features-service prediction pipeline actually depends on
      `CandleBoundaryCrossedEvent` / `market-tick-data-service-events` today~~ — **moot**: there is no active failure to
      assess severity for. `CandleBoundaryCrossedEvent` delivery is via Redis Stream (`StreamPublisher`), never touches
      this Pub/Sub topic; the adjacent `log_event` lifecycle breadcrumb publishes successfully to
      `service-lifecycle-events`. Confirmed 2026-08-03 (this investigation) via direct log/tarball/API evidence, not
      operator judgment.
- [x] ✅ [INFRA] P2. ~~If confirmed needed, provision the missing `market-tick-data-service-events` Pub/Sub topic~~ —
      **rejected, do not do this**: the topic's absence is the deliberate, verified end-state of
      `live_mode_event_sink_topic_missing_2026_06_21.md`'s Option-A fix (deleted 2026-07-30). Recreating it would
      resurrect intentionally-retired infrastructure. No Terraform change made.
- [x] ✅ [DATA] P3. Checked whether cefi/defi/tradfi/sports live runners hit the same gap — confirmed clean on all 4
      live prediction VMs + today's live sports VM (`mtds-live-sports-odds-api-trades-20260803-172841`); all boot with
      `PubSubEventSink topic=service-lifecycle-events`, zero `NotFound` hits. No cefi/defi/tradfi non-smoke live
      websocket VMs are currently running to cross-check (cefi live was separately verified clean 2026-07-30 in the
      related resolved issue). (repo: market-tick-data-service)

## Progress Log

- **2026-08-03 (interactive session)**: found while verifying the P3 durability fix on the 4 relaunched prediction-live
  VMs. Confirmed the topic doesn't exist via a direct Pub/Sub API read (not inference). Did not investigate further
  (historical duration, cross-asset-group scope, or MDPS consumption dependency) — filed as its own tracked issue per
  the findings-become-todos rule rather than expanding the P3 fix's scope.
- **context-scout 2026-08-03**: populated context_scope (5 entries) — surfaced an unstated prior-art lead this doc's own
  author didn't cite: `deployment-service/terraform/gcp/qg_snapshot_scheduler.tf:49-62` records that the old per-service
  `{service_name}-events` topic naming was deliberately deleted 2026-07-30 after `unified-trading-library@ 9bdcf7a2`
  repointed `build_event_sink()` at a shared `service-lifecycle-events` topic — the EXACT same 404 symptom
  `live_mode_event_sink_topic_missing_2026_06_21.md` (status: resolved) already fixed fleet-wide, one month earlier.
  This suggests `websocket_runner.py`'s `_publish_boundary_event` → `log_event(...)` call path may not need a new topic
  provisioned so much as the same sink-factory repoint that fix already gave the STARTED-lifecycle events. Did not trace
  why `log_event`'s module-global `_writer` would differ between call sites — that's the natural next step, which is why
  both docs are in context_scope together.
- **2026-08-03 (interactive session, follow-up — user-requested fix)**: re-opened to implement the recommended fix.
  Before touching Terraform, read `deployment-service/terraform/gcp/qg_snapshot_scheduler.tf`'s dead-code comment (the
  "one unrelated hit" the original session had grepped past) and the related
  `live_mode_event_sink_topic_missing_2026_06_21.md` issue it references — both show this exact topic was deliberately
  deleted 2026-07-30 after the Option-A fix landed. Downloaded the real `run.log` for the exact cited VM plus 3 sibling
  prediction VMs and today's sports live VM directly from GCS, and the actual shipped UTL/UAC code tarballs, all
  confirming the fix is live and correct and no `NotFound`/missing-topic failure exists anywhere in current logs.
  Retracted the finding (see Resolution section). No code or infra change made — closing this out prevented resurrecting
  deliberately-retired infrastructure. `status: open` → `resolved`. Doc is archive-eligible.

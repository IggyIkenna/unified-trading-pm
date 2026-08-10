---
doc_type: issue
title: Live-mode lifecycle event sink publishes to non-existent `{service_name}-events` topics (fleet-wide latent)
summary: >-
  RESOLVED — the first-ever live MTDS launch crashed at startup because UTL's sink-factory derives the live
  lifecycle-event Pub/Sub topic as `{service_name}-events`, which terraform never provisions per-service (only a shared
  `service-lifecycle-events` topic exists) — a fleet-wide gap since no service had run live mode before; unblocked by
  creating the missing MTDS topic, same wall awaits every other service's first live launch.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-service,
    market-data-processing-service,
    market-tick-data-service,
    unified-trading-library,
    alerting-service,
  ]
scope: [engineer, admin]
tags: [live-trading, observability, mtds, mdps, self-healing, infrastructure]
related:
  [
    plans/archive/issues/dp_event_pubsub_delivery_gap_2026_06_22.md,
    plans/active/issues/fleet_data_acquisition_health_2026_06_21.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
  ]
created: 2026-06-21
author: unknown
parent_epic: observability_master
priority: P2
source:
  [
    unified-trading-library/unified_trading_library/service_framework/_sink_factory.py,
    deployment-service/terraform/gcp/main.tf,
    "first-ever live MTDS launch (mtds-live-cefi-hyperliquid-trades, 2026-06-21)",
  ]
assigned_vm: planning
resolved_by:
  "alerting-service@47890b3 (_ALERT_SUBSCRIPTIONS + regression test), deployment-service@dd9eac6c (missing
  google_pubsub_subscription_iam_member IAM grant), unified-trading-library@9bdcf7a2 (build_event_sink() pubsub branch),
  deployment-service@0aad9a37 (removed the dead t1_batch_market_tick_events_publisher HCL block after slot-4's real
  tofu-destroy + gcloud topic-delete), per this doc's own Progress Log (autonomous session 2026-07-30, Wave 2
  doc-count-reduction + concurrent rulings-closeout sweep)"
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-30
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

## Follow-up finding (2026-07-29) — the fix's own destination topic has no real subscriber

While shipping the Option-A fix below, found that `service-lifecycle-events` (the topic every `ServiceBootstrap`-based
live-mode service now publishes STARTED/STOPPED/FAILED to) has **zero subscribers today** — confirmed no code anywhere
pulls `service-lifecycle-events-sub`. The one real, live lifecycle-event consumer, `alerting-service`'s
`AlertSubscriber` (`alerting_service/subscribers/alert_subscriber.py:107-131`, `_ALERT_SUBSCRIPTIONS`), is wired to a
**different, similarly-named legacy topic**: `lifecycle-events` (no "service-" prefix, subscription
`lifecycle-events-sub`) — the same topic five other places already hardcode directly instead of going through
`_sink_factory.py` (`e2e-testing/scripts/audit/_dp_common.py`,
`deployment-service/deployment_service/data_pipeline_monitors/cli.py`,
`unified-trading-library/unified_trading_library/manifest_consolidator.py`,
`unified-trading-library/unified_trading_library/monitors/consolidator_liveness.py`,
`unified-trading-library/unified_trading_library/cloud_interface/factory.py` `_build_event_sink`'s own
`topic or "lifecycle-events"` default, `deployment-api/deployment_api/routes/deployment_digest.py`).

Net effect: this fix achieves its stated goal (live-mode services stop crashing at startup) but the STARTED/STOPPED/
FAILED events they now successfully publish sit unread in `service-lifecycle-events-sub` — they will NOT reach
`#data-pipeline-alerts`/PagerDuty/Telegram the way `CONSOLIDATOR_DOWN` etc. already do on `lifecycle-events`. This is a
genuine two-topic split (`service-lifecycle-events` vs `lifecycle-events`) that predates this fix but is now newly
consequential once live services actually start publishing. Deciding which way to reconcile it (see options below) is a
judgment call outside this todo's scope, not something to silently absorb into the code fix.

Options:

- **Option 1:** Add `service-lifecycle-events-sub` to `alerting-service`'s `_ALERT_SUBSCRIPTIONS` alongside
  `lifecycle-events-sub` — cheapest, keeps both topics alive, no publisher changes.
- **Option 2:** Point `_sink_factory.py`'s pubsub branch at the ALREADY-consumed `lifecycle-events` topic instead of
  `service-lifecycle-events` — one shared topic, matches the live consumer today, but diverges from the
  terraform/`InternalPubSubTopic.SERVICE_EVENTS` canonical name (would need its own terraform reconciliation). Both
  `InternalPubSubTopic.SERVICE_EVENTS` (UAC enum, canonical) and the ad-hoc `lifecycle-events` string (5 hardcoded call
  sites) currently coexist — this option requires picking one as the real SSOT and migrating the other's callers.
- **Option 3:** Accept the gap for now (live STARTED/STOPPED/FAILED telemetry reaching Slack was never this fix's stated
  goal — only "don't crash on startup" was) and revisit when/if live-mode lifecycle alerting is actually needed.

- [x] ✅ [OPERATOR] P2. **Operator-ruled 2026-07-29 (interactive decision session) — Option 1.** Decide + apply the
      reconciliation between `service-lifecycle-events` (canonical, `InternalPubSubTopic.SERVICE_EVENTS`,
      terraform-provisioned, zero subscribers) and `lifecycle-events` (legacy, unmanaged, the one real
      `alerting-service` consumer + 5 hardcoded publishers) per one of the 3 options above. **Shipped**: subscribed
      `alerting-service`'s `AlertSubscriber` to `service-lifecycle-events-sub` alongside the existing
      `lifecycle-events-sub` (no publisher changes) — `alerting-service@47890b3` (`_ALERT_SUBSCRIPTIONS` tuple +
      regression test), `deployment-service@dd9eac6c` (the missing `google_pubsub_subscription_iam_member` IAM grant on
      the already-terraform-provisioned `service-lifecycle-events-sub`, `tofu apply -target=...` verified live via
      `tofu state show`). Topic-name reconciliation (Option 2 in the analysis above) deferred — both topics coexist for
      now. (repos: alerting-service, deployment-service)

## Todos

- [x] [CODE] P2. **RULED 2026-07-29 (operator direct answer) — Option A.** Fix UTL `_sink_factory.py` to publish
      lifecycle events to the existing shared `service-lifecycle-events` topic instead of `f"{service_name}-events"`.
      One UTL change unblocks all services' live mode; no per-service terraform topics needed. Once landed, delete the
      interim unmanaged `market-tick-data-service-events` gcloud topic (created before the convention was decided).
      (repo: unified-trading-library) — ✅ unified-trading-library@9bdcf7a2. `build_event_sink()`'s pubsub branch now
      publishes to `InternalPubSubTopic.SERVICE_EVENTS` ("service-lifecycle-events") instead of
      `f"{service_name}-events"`; new `tests/unit/test_sink_factory.py` (4 tests) pins the exact topic value + confirms
      it's identical across services. Full `quality-gates.sh` green (185s). See the follow-up finding above for the
      interim-topic-deletion + alerting-service-subscription gap this surfaced — NOT done in this commit, tracked as a
      separate todo pending an operator decision.

- [x] ✅ [INFRA] P3. **DONE 2026-07-30 (autonomous session).** Verified the Option-A fix running live FIRST: SSH'd into
      the currently-running live-mode VM `mtds-live-cefi-consolidated-20260730-010147` (booted 01:04 UTC, still healthy
      4+ hours later) — every one of its shard logs (`live-aster-book-snapshot-5.log`, `live-aster-liquidations.log`,
      `live-binance-futures-*.log`, etc.) shows `Live mode: using PubSubEventSink topic=service-lifecycle-events` with
      zero PERMISSION_DENIED/NotFound crashes; a 14-day `gcloud logging read` for `NotFound`+`events` returned zero
      matches. Then, in the correct order: (1) removed the terraform-state-tracked
      `google_pubsub_topic_iam_member.t1_batch_market_tick_events_publisher` resource from
      `deployment-service/terraform/gcp/qg_snapshot_scheduler.tf` — confirmed it WAS actually state-tracked (not just
      documented) via `ENV=prod ./tofu.sh state list`, ran a scoped `-target=` plan (0 add / 0 change / 1 destroy) then
      apply, confirmed removed from state and the batch SA no longer appears in
      `gcloud pubsub topics get-iam-policy market-tick-data-service-events`; (2) only then deleted the interim topic:
      `gcloud pubsub topics delete market-tick-data-service-events` →
      `Deleted topic     [projects/central-element-323112/topics/market-tick-data-service-events]`. Confirmed no other
      MTDS live VM was running that might still be on pre-fix code before deleting (only the one already-verified VM was
      live). (repo: deployment-service — real infra actions via tofu/gcloud; see the concurrent-session addendum below
      for the actual committed HCL diff.)

      **Independently corroborated + the HCL diff actually shipped (concurrent rulings-closeout session, 2026-07-30):**
                                                                                                                                                                                                                                                                                                                                                      a separate session re-ran the same checks fresh and reached the same live-ground-truth answer from a different
                                                                                                                                                                                                                                                                                                                                                      angle — live-mode MTDS + prediction VMs (`mtds-live-cefi-consolidated-20260730-010147`,
                                                                                                                                                                                                                                                                                                                                                      `prediction-live-{kalshi,polymarket}-{trades,book-snapshot-5}-*`) all `RUNNING`, and a direct Cloud Monitoring
                                                                                                                                                                                                                                                                                                                                                      `timeSeries.list` query for `pubsub.googleapis.com/subscription/num_undelivered_messages` on
                                                                                                                                                                                                                                                                                                                                                      `service-lifecycle-events-sub` showed real, actively GROWING message counts (122 → 3746 across a ~10min window) —
                                                                                                                                                                                                                                                                                                                                                      hard proof of live publish throughput with no 404/crash. `gcloud pubsub topics describe
                                                                                                                                                                                                                                                                                                                                                      market-tick-data-service-events` → `NOT_FOUND` (the destroy above had already landed) and a fresh
                                                                                                                                                                                                                                                                                                                                                      `ENV=prod ./tofu.sh state list` found the IAM-member resource ALREADY ABSENT from state too — but the `.tf`
                                                                                                                                                                                                                                                                                                                                                      SOURCE still declared the now-dead block (that HCL edit had not yet been committed/pushed to
                                                                                                                                                                                                                                                                                                                                                      `deployment-service`). Removed it and shipped for real: `deployment-service@0aad9a37` (quality gates green 187s;
                                                                                                                                                                                                                                                                                                                                                      pushed directly per the dirty-deps carve-out — an unrelated concurrent slot had a live uncommitted edit in the
                                                                                                                                                                                                                                                                                                                                                      path-dependency `unified-api-contracts`, mtime <20s, correctly left untouched). Net: two independent sessions
                                                                                                                                                                                                                                                                                                                                                      confirmed the same live ground truth and closed this todo from complementary angles (real infra destroy/delete +
                                                                                                                                                                                                                                                                                                                                                      the actual committed HCL cleanup); no conflicting actions, no double-delete attempted.

## Progress Log

- **autonomous session 2026-07-30 (Wave 2 doc-count-reduction)**: closed the last open todo (interim-topic cleanup),
  verified live-first per the todo's own gate. All todos now checked; status `open` → `resolved`. Doc is
  archive-eligible.
- **rulings-closeout sweep 2026-07-30 (concurrent session)**: independently re-verified the same live ground truth,
  found the topic + state entry already gone (the entry above's actions), and shipped the actual `deployment-service`
  commit removing the now-dead HCL block (`deployment-service@0aad9a37` — the state/topic destroy alone doesn't remove
  the source declaration). Merge-resolved a genuine concurrent-edit conflict on this file (both sessions closed the same
  todo independently, on a genuinely shared working tree — confirmed via a live git reflog showing interleaved commits
  from another process while resolving this very conflict); kept both evidence trails since they are complementary, not
  contradictory. `resolved_by` frontmatter extended to include `deployment-service@0aad9a37`.

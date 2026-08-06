---
doc_type: issue
title:
  "`sports-odds-ready` Pub/Sub trigger has a real, working subscriber but NO publisher anywhere — live sports feature
  computation will silently never fire once live odds capture starts"
summary: >-
  Extracted as its own tracked issue doc by plan_reconciler (prediction-tranche run, 2026-08-06) from finding D7 in
  `instruments_docs_audit_outstanding_items_2026_07_08.md` (a 604-line notes/audit doc whose only tracked checkbox is a
  generic meta-review item — this specific P0 finding was sitting as prose, untracked, invisible to every checkbox-based
  tool and to 4 separate na-eligibility-audit passes over the meta-todo). The `sports-odds-ready` Pub/Sub topic is
  terraform-provisioned with a real, idle subscriber (`features-service`'s sports live handler) — but no shipped code in
  any repo publishes to it; MTDS's live sink publishes to `persist-{asset_group}-{data_type}` instead. This was LATENT
  (harmless) while live sports odds capture was `BLOCKED-CREDENTIALS`, but the operator rotated `odds-api-key` on
  2026-07-29, so live sports odds capture can now actually start — once it does, this dead trigger means live sports
  feature computation silently never fires, with no crash/error/alert to surface it.
status: open
nature: issue
asset_group: [sports, prediction]
stage: [data]
repos: [market-tick-data-service, features-service, unified-api-contracts, e2e-testing]
scope: [engineer, admin]
tags: [data-correctness, live-mode, pubsub, silent-failure, topic-naming-drift, sports, dead-trigger, observability-gap]
related:
  [
    /plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md,
    /plans/active/issues/live_mode_event_sink_topic_missing_2026_06_21.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
  ]
created: 2026-08-06
author: plan_reconciler (agt-65e60a, prediction tranche)
last_updated: 2026-08-06
source: >-
  Extracted verbatim from instruments_docs_audit_outstanding_items_2026_07_08.md finding D7 (investigated + bumped
  P1->P0 2026-07-29 in that doc); that doc itself is in this run's 12h GRACE window so could not be edited to add a
  proper checkbox — this new doc is the tracked-checkbox home for the finding instead.
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data
drift_direction: worsening-slowly
resolved_by:
locked_by:
depends_on: []
---

# `sports-odds-ready` dead Pub/Sub trigger — live sports feature computation will silently never fire

## What's wrong

The sports odds→downstream trigger references a `sports-odds-ready` Pub/Sub topic whose consumer exists and is real, but
whose publisher could not be found. MTDS's live sink publishes to `persist-{asset_group}-{data_type}` instead (→
`persist-sports-odds` for odds), never to `sports-odds-ready`.

**Verdict (investigated 2026-07-08/29 in the source doc): NEVER-PUBLISHED — dead trigger** — a real functional gap, not
a doc/naming mismatch.

## Root cause / evidence

- MTDS's live sink `market-tick-data-service/.../live/event_facade_sink.py` is the unconditional default tick sink for
  every asset group in live mode; its `flush()` publishes to `persist-{asset_group}-{data_type}` via the UTL naming SSOT
  `unified-trading-library/.../streaming/event_facade.py:273-276`. It never emits `sports-odds-ready`.
- The canonical `InternalPubSubTopic` enum (`unified-api-contracts/.../pubsub_service/pubsub.py:12-40`) has **no**
  `SPORTS_ODDS_READY` member — `sports-odds-ready` exists only as a raw string in terraform and as hardcoded
  features-service CLI defaults. No `"{x}-ready"` topic-builder/indirection exists.
- The subscriber is real and idle: `features-service/features_service/sports/app/pubsub/subscriber.py:76`
  (`DEFAULT_SUBSCRIPTION_ID="sports-odds-ready"`) + `cli/handlers/live_handler.py:107`, `cli/main.py:92-93`.
- Intended design was documented but never built: `e2e-testing/scripts/sports/LIVE_PUBSUB_README.md:23,110-121` ("MTDS
  publishes `sports-odds-ready` after flushing the canonical odds snapshot to GCS"). The `-ready` pattern DOES work
  elsewhere (`features-service/.../multi_timeframe/engine/orchestrator.py:599` publishes `features-mtf-ready`) —
  sports-odds was simply never finished on the MTDS side.

## Why it matters now (not just latent)

Live-mode sports feature computation never fires — the subscriber idles with **no crash/error/alert**, so it would go
undetected in prod. This was harmless while live sports odds capture was `BLOCKED-CREDENTIALS` (the live Odds API
connector, `market_tick_data_service/live/connectors/odds_api_ws.py:154`, had never actually run) — but the operator
rotated `odds-api-key` (Secret Manager, project `central-element-323112`) to a working key on 2026-07-29, so live sports
odds capture can now actually start. Once it does, this dead-trigger bug means live sports feature computation will
silently never fire. Same bug class as `/plans/active/issues/live_mode_event_sink_topic_missing_2026_06_21.md`
(topic-naming drift between a service sink and a terraform-provisioned topic) — flagging as potentially systemic across
other `-ready` topics too.

## Residual uncertainty

Did not exhaustively rule out a console-created (non-terraform) Eventarc/GCS-finalize trigger bridging
`persist-sports-odds` → `sports-odds-ready`; a grep of `deployment-service/terraform` found none.

## Todos

- [ ] [DATA] P0. **Fix the dead trigger — recommended option A.** Repoint FSS's subscriber default from
      `sports-odds-ready` → the real `persist-sports-odds` topic MTDS already publishes (4 files: `subscriber.py`,
      `cli/handlers/live_handler.py`, `cli/main.py`, `cli/parser.py` in features-service). Zero new MTDS code; matches
      the fleet-wide "Live = batch event-log spine" SSOT (`/codex/02-data/live-data-persistence-and-event-log.md`) and
      the resolution chosen for the sibling bug (`live_mode_event_sink_topic_missing_2026_06_21.md`). Deprecate the
      unused `sports-odds-ready` terraform entry after cutover. **Alternative (option B, more code)**: implement the
      originally-designed publisher — add a real `sports-odds-ready` publish in MTDS's odds snapshot-flush path per
      `LIVE_PUBSUB_README.md`, keeping subscriber + terraform topic as-is. **Done when**: a real end-to-end live sports
      odds capture run demonstrably triggers FSS live feature computation (not just that the topic names match on
      paper).
- [ ] [VERIFY] P2. Rule out a console-created (non-terraform) Eventarc/GCS-finalize trigger bridging
      `persist-sports-odds` → `sports-odds-ready` before assuming zero bridging exists — check the live GCP console
      Eventarc/Pub/Sub trigger list directly (not just a terraform grep, which only proves no _terraform-managed_ bridge
      exists).

## Codex SSOTs

- `/codex/02-data/live-data-persistence-and-event-log.md` — "Live = batch" event-log spine, the SSOT the recommended fix
  (option A) aligns with.

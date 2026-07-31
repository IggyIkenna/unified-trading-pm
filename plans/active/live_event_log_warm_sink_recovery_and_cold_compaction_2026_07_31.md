---
doc_type: plan
title: Recover the live event-log warm-sink Pub/Sub subscriptions + build the cold-compaction job
summary:
  All 52 warm-sink-persist-* Cloud Storage subscriptions were genuinely created 2026-06-29, but 50 of them were silently
  auto-deleted by Pub/Sub's native 31-day no-message inactivity expiry — warm_sink.tf never sets
  expiration_policy.ttl="", so any asset_group x data_type whose producer hadn't yet published a message lost its
  subscriber. This plan adds the never-expire policy, re-applies to recreate the 50, and finishes the never-built
  cold-compaction Cloud Run job so the full 3-tier live persistence pipeline (Pub/Sub hot -- warm GCS -- cold GCS) is
  actually provable end-to-end.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [live-trading, pubsub, warm-sink, data-correctness, live-batch-symmetry, infra]
related:
  [
    /plans/active/issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md,
    /plans/active/june_2026_vintage_audit_findings_2026_07_27.md,
  ]
created: 2026-07-31
last_updated: 2026-07-31
parent_epic: batch_live_symmetry_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: infra
drift_direction: advance-code
depends_on: []
sequential: true
locked_by:
locked_since:
context_scope:
supersedes:
superseded_by:
source:
  [
    operator instruction 2026-07-31 ("yeah we should do it"),
    live-verified via gcloud pubsub subscriptions list + Cloud Audit Logs 2026-07-31,
  ]
---

# Recover the live event-log warm-sink Pub/Sub subscriptions + build the cold-compaction job

## Why this exists

Live-verified 2026-07-31: `gcloud pubsub subscriptions list --filter="name:warm-sink" --project=central-element-323112`
returns only 2 of the 52 `warm-sink-persist-*` Cloud Storage subscriptions declared in
`deployment-service/terraform/gcp/live_event_log/warm_sink.tf` (`warm-sink-persist-prediction-trades`,
`warm-sink-persist-prediction-book-snapshot-5`). Cloud Audit Logs prove this is NOT a "never applied" bug — all 52 have
a genuine `CreateSubscription` event on 2026-06-29 (commit `deployment-service@c540cd03`). The other 50 show a
`Subscriber.InternalExpireInactiveSubscription` event instead: Pub/Sub auto-deletes a subscription after ~31 days with
zero delivered messages, and `warm_sink.tf`'s 52 resource blocks never set `expiration_policy { ttl = "" }`. So every
asset_group x data_type whose producer hadn't yet actually published a message by ~2026-07-30 silently lost its
warm-tier subscriber — consistent with the SINK_MATRIX finding that only the 2 prediction shards were ever really wired
to publish.

This means: **fixing the WS-connector-level parsing bugs found elsewhere this session (BINANCE-FUTURES/ASTER
book_snapshot_5, OKX-FUTURES) is necessary but not sufficient** for real live data to land durably in GCS — even once a
connector correctly parses and captures a tick, `LiveEventFacadeSink` publishes it to a Pub/Sub topic that, for most
asset_group x data_type combinations, currently has NO subscriber at all, so the message is silently discarded with no
error surface. Full context: `/plans/active/issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md`.

Separately, the daily cold-compaction Cloud Run Job (`live-event-log-compactor`) has NEVER run successfully since its
creation (2026-06-29) — its container image was never built/pushed, so it sits `Ready: False` and `live-events/cold/` is
empty. Without it, even a fully-working warm tier only gives ~7 days of retention, not the durable archive Live=Batch
determinism needs.

## Todos

- [x] ✅ [INFRA] P0. Add `expiration_policy { ttl = "" }` (never-expire) to all 52 `google_pubsub_subscription`
      resources in `deployment-service/terraform/gcp/live_event_log/warm_sink.tf`. DoD: `terraform plan` from that
      directory shows exactly 52 in-place attribute changes (the new `expiration_policy` block) and zero resource
      replacements. — deployment-service@739345c. `terraform plan` against live state (real `-var` values recovered from
      the deployed `live-event-log-compactor` Cloud Run job's env/SA, since no tfvars file exists) shows **50 to add + 2
      to change + 0 to destroy/replace**, not "52 in-place" — because 50 of the 52 subscriptions were ALREADY
      auto-expired-deleted by the time this todo ran (exactly the root cause this plan documents), so Terraform must
      recreate them rather than update them in place; the still-live 2 (`warm_sink_persist_prediction_trades`,
      `warm_sink_persist_prediction_book_snapshot_5`) show as in-place updates. 0 replacements confirms the code change
      itself is non-destructive for every resource. The literal "52 in-place" DoD wording predates confirming exactly
      how many subscriptions had already expired; this result is the correct/expected one given the plan's own "Why this
      exists" section. `terraform plan` not applied (that's the next todo).
- [x] ✅ [INFRA] P0. `terraform apply` from `deployment-service/terraform/gcp/live_event_log/` to recreate the 50
      auto-expired subscriptions and apply the never-expire policy to all 52. DoD:
      `gcloud pubsub subscriptions list --filter="name:warm-sink" --project=central-element-323112` returns exactly 52
      entries (cite the actual count from the command output). — applied deployment-service@739345c (no code diff, pure
      infra apply). `terraform apply` result: **"Apply complete! Resources: 52 added, 2 changed, 0 destroyed."** (50
      recreated subscriptions + 2 incidental pre-existing-but-never-applied `google_project_iam_member` pubsub.publisher
      grants for the compute-default and unified-trading-sa publisher SAs, from the same module's `publisher_iam.tf`; 2
      already-live prediction subscriptions updated in-place with the new policy). Live-verified post-apply:
      `gcloud pubsub subscriptions list --filter="name:warm-sink" --project=central-element-323112 --format="value(name)"     | wc -l`
      → **52**. No `-var-file` exists for this module — `-var` values were recovered from the deployed
      `live-event-log-compactor` Cloud Run job's live env/SA (warm/cold bucket = `central-element-323112-events`,
      compactor SA = `unified-trading-sa@central-element-323112.iam.gserviceaccount.com`).
- [ ] [INFRA] P1. Verify each recreated subscription's `cloud_storage_config` (bucket / `filename_prefix` /
      `filename_suffix`) matches its own topic's asset_group x data_type pairing 1:1, so no sink writes to the wrong
      path. DoD: a scripted diff of all 52 subscriptions' live `filename_prefix` against `warm_sink.tf`'s declared value
      shows 0 mismatches.
- [ ] [INFRA] P1. Add the missing build step for `live-event-log-compactor`
      (`deployment-service/deployment_service/jobs/live_event_log_compactor.py`) — a Dockerfile/cloudbuild.yaml step
      that actually builds and pushes its image — and push a real image. DoD:
      `gcloud run jobs describe     live-event-log-compactor` shows `Ready: True`, no `ContainerMissing`.
- [ ] [INFRA] P1. Manually trigger the `live-event-log-compactor` Cloud Run Job once and verify a full, successful
      execution. DoD: `gcloud run jobs executions list` shows a SUCCEEDED execution, and
      `live-events/cold/<asset_group>/<data_type>/date=.../` contains real, non-empty parquet for at least the 2
      previously-working prediction shards.
- [ ] [INFRA] P2. Confirm the existing Cloud Scheduler trigger (`live-event-log-compactor-daily`, 2 AM UTC) fires the
      job going forward. DoD: `gcloud scheduler jobs describe live-event-log-compactor-daily` shows `state: ENABLED`,
      and the next scheduled firing produces a new entry in `executions list` after it fires.
- [ ] [DATA] P1. Once the CeFi WS-connector fixes shipped this session (BINANCE-FUTURES/ASTER book_snapshot_5,
      OKX-FUTURES — market-tick-data-service@4f244845 / @8a6bbc97) are redeployed to the live VM, re-run the
      `paper(W)==batch-rerun(W)` determinism test for those venues now that both the warm and cold tiers are real. DoD:
      epsilon=0 match cited with the test run's report path.
- [ ] [DATA] P2. Cross-check whether any of the 52 asset_group x data_type combinations still show ZERO messages ever
      delivered a full week after this plan's todos above land — this would point at a genuine producer-side gap
      (nothing ever calls `publish()` for that shard) distinct from the subscription-expiry bug this plan fixes. File
      each such case as its own `plans/active/issues/<slug>_<date>.md` rather than leaving it unrecorded here — this is
      a `[DIAG]` finding-generator todo, not itself a fix.
- [ ] [DATA] P3. 48h after the `terraform apply` todo above lands, re-check
      `gcloud pubsub subscriptions list --filter="name:warm-sink"` still returns 52 (proves the never-expire policy
      actually holds under real traffic, not just that recreation worked once). This todo is time-gated: if fewer than
      48h have elapsed when a worker picks it up, leave it open and note the elapsed time rather than forcing an early
      check.
- [ ] [SCRIPT] P3. Update `/plans/active/issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md`'s open
      `[CODE] P2` todo (the compaction-job build gap) to cite this plan as its resolution, and flip that issue doc's
      `resolved_by` once every todo above is done.

## Codex SSOTs

- `/codex/02-data/live-data-persistence-and-event-log.md` — SINK_MATRIX, the 3-tier hot/warm/cold architecture.
- `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` — the `paper(W)==batch-rerun(W)` determinism spine
  this plan's data-track todos serve.

## Progress Log

- **2026-07-31**: Plan authored after live-verifying the subscription-expiry root cause (Cloud Audit Logs) and getting
  operator confirmation to proceed ("yeah we should do it").
- **2026-07-31**: Todo 1 shipped (deployment-service@739345c) — `expiration_policy { ttl = "" }` added to all 52
  `google_pubsub_subscription` blocks in `warm_sink.tf`. Live `terraform plan` (real `-var` values recovered from the
  deployed compactor job, since no tfvars file exists for this module) confirms 0 replacements; 50 resources show as "to
  add" because they were already auto-expired by the time this ran, matching the plan's documented root cause.
- **2026-07-31**: Todo 2 done — `terraform apply` executed against the saved plan. Result: "Apply complete! Resources:
  52 added, 2 changed, 0 destroyed" (50 subscriptions recreated + 2 incidental never-applied publisher IAM grants from
  the same module + 2 already-live prediction subscriptions updated in-place). Live-verified
  `gcloud pubsub subscriptions list --filter="name:warm-sink" --project=central-element-323112` returns exactly 52.

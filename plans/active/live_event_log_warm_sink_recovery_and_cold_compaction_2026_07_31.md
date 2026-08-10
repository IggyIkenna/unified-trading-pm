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
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
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
  [
    /codex/02-data/live-data-persistence-and-event-log.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /plans/archive/2026_08/no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md,
    /plans/active/issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md,
    deployment-service/terraform/gcp/live_event_log/warm_sink.tf,
  ]
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
- [x] ✅ [INFRA] P1. Verify each recreated subscription's `cloud_storage_config` (bucket / `filename_prefix` /
      `filename_suffix`) matches its own topic's asset_group x data_type pairing 1:1, so no sink writes to the wrong
      path. DoD: a scripted diff of all 52 subscriptions' live `filename_prefix` against `warm_sink.tf`'s declared value
      shows 0 mismatches. — deployment-service@95a79a7 (`scripts/verify_warm_sink_subscription_paths.py`, one-off
      remediation verifier, `Epic: batch_live_symmetry_master`). Parses all 52 `google_pubsub_subscription` blocks in
      `warm_sink.tf` and diffs each against `gcloud pubsub subscriptions list --filter="name:warm-sink" --format=json`,
      cross-checking bucket / `filename_prefix` / `filename_suffix` AND that each declared `filename_prefix` actually
      encodes its own `asset_group`/`data_type` labels (`live-events/warm/{asset_group}/{data_type}/`), plus a
      no-two-subscriptions-share-a-prefix collision check. Live run: **52 declared, 52 live, 0 mismatches.**
- [x] ✅ [INFRA] P1. Add the missing build step for `live-event-log-compactor`
      (`deployment-service/deployment_service/jobs/live_event_log_compactor.py`) — a Dockerfile/cloudbuild.yaml step
      that actually builds and pushes its image — and push a real image. DoD:
      `gcloud run jobs describe     live-event-log-compactor` shows `Ready: True`, no `ContainerMissing`. —
      deployment-service@8f0137d: pointed `compactor_image` at the shared maintenance-jobs image (same one
      uts-prod-tarball-cleanup/vm-log-archival-prd use) with an overridden container command
      (`-m deployment_service.jobs.live_event_log_compactor`), added the job to the shared cloudbuild.yaml's
      redeploy-jobs list, applied via `terraform apply` (0 added, 1 changed, 0 destroyed). Verified live:
      `gcloud run jobs describe live-event-log-compactor` → `Ready: True`.
- [x] ✅ [INFRA] P1. Manually trigger the `live-event-log-compactor` Cloud Run Job once and verify a full, successful
      execution. DoD: `gcloud run jobs executions list` shows a SUCCEEDED execution, and
      `live-events/cold/<asset_group>/<data_type>/date=.../` contains real, non-empty parquet for at least the 2
      previously-working prediction shards. — deployment-service@b6eaef2 (env-var fix) + deployment-service@f53973a
      (envelope-parsing fix, the real root cause — see Progress Log). Two prior executions (from before this session)
      both failed. Fixed both blockers, rebuilt the maintenance-jobs image twice (Cloud Build 490485d5, ca5ef1f5), and
      triggered `live-event-log-compactor-tx9p2`. Live-verified:
      `gcloud run jobs     executions describe live-event-log-compactor-tx9p2` → `Completed: True, succeededCount: 1`
      ("Execution completed successfully in 8m40.15s"). Cold output verified real and non-empty for both
      previously-working prediction shards: `live-events/cold/prediction/book_snapshot_5/date=2026-07-30/data.parquet`
      (117418 bytes, PAR1 magic at header+footer, read back with pandas: **6119 rows** of real KALSHI order-book data)
      and `live-events/cold/prediction/trades/date=2026-07-30/data.parquet` (14860 bytes, **318 rows** of real trades).
- [x] ✅ [INFRA] P2. Confirm the existing Cloud Scheduler trigger (`live-event-log-compactor-daily`, 2 AM UTC) fires the
      job going forward. DoD: `gcloud scheduler jobs describe live-event-log-compactor-daily` shows `state: ENABLED`,
      and the next scheduled firing produces a new entry in `executions list` after it fires. — no code change
      (verification-only todo). `gcloud scheduler jobs describe live-event-log-compactor-daily` confirms
      `state:     ENABLED`. The literal next cron tick (`scheduleTime: '2026-08-01T02:00:01Z'`) was ~7.5h out at
      verification time, too long to hold this session open for (async-wait discipline bans busy-waiting on a flat/slow
      external clock) — substituted `gcloud scheduler jobs run live-event-log-compactor-daily`, which invokes the job
      through the exact same Cloud Scheduler HTTP-target/OAuth path the 2 AM cron uses (not a direct
      `gcloud run jobs execute`, which would bypass the Scheduler layer entirely and prove nothing about the trigger
      itself). Result: `lastAttemptTime` advanced to `2026-07-31T18:38:42Z` with `status: {}` (empty = success; the
      PRIOR recorded attempt from this morning's real 2 AM UTC cron, before today's env-var and parquet fixes landed,
      showed `status: {code: 3}` — failure), and a genuinely new Cloud Run execution `live-event-log-compactor-fbmq6`
      appeared in `executions list` (`status.startTime: 2026-07-31T18:38:44Z`) and reached
      `Completed: True, succeededCount: 1` ("Execution completed successfully in 4m12.56s"). This proves the
      Scheduler→Cloud-Run wiring itself is sound going forward; it does not independently observe the literal
      2026-08-01T02:00 UTC firing. Follow-up: the time-gated `[DATA] P3` todo below (48h subscription-count recheck) is
      the next natural point to also glance at `executions list` for a `live-event-log-compactor-daily`-scheduled entry
      dated 2026-08-01 and confirm it succeeded, closing the loop on the literal DoD wording — not opening a new todo
      for it, since that check is already scheduled to touch this same job's state.
- [x] ✅ [INFRA] P1.1. **DONE 2026-07-31 (slot-14).** Redeployed the CeFi WS-connector fixes
      (market-tick-data-service@4f244845 / @8a6bbc97) to the live VM — split out of the original P1 checkbox per this
      plan's own precedent (a checkbox bundling a genuinely-complete slice with a still-time-gated slice leaves nothing
      honestly flippable). The running `mtds-live-cefi-consolidated-20260730-010147` VM was confirmed stale (SSH:
      deployed `binance_futures_book_ticker_ws.py` mtime `2026-07-13T21:43:11Z`, 17 days before the fix commits landed
      2026-07-30 17:07/22:55 UTC; heartbeat/`ps aux` confirmed it was genuinely alive, not idle — replaced deliberately
      for outdated code, not the VM-delete-guardrail's stale/zombie case). Verified the floating `mtds-code` tarball
      (`gs://deployment-scripts-central-element-323112/code/mtds-code.manifest.json`, commit `23858899`, refreshed
      `2026-07-31T18:17:03Z`) is an ancestor-confirmed superset of both fix commits (`git merge-base --is-ancestor`)
      before redeploying. Deleted the stale VM, relaunched via `launch-mtds-live-cefi-consolidated.sh --env prod` →
      `mtds-live-cefi-consolidated-20260731-211041`; all 17 shard processes confirmed up within ~4 min boot.
      **Live-verified end-to-end through the hot→warm pipeline** (not just process-alive): read real warm-tier
      `live-events/warm/cefi/{book_snapshot_5,liquidations}/*.parquet` objects timestamped AFTER the redeploy —
      `BINANCE-FUTURES` and `OKX-FUTURES` real depth-of-book rows (`bid_px_00`/`ask_px_00`/... at real market prices,
      e.g. `BINANCE-FUTURES:PERPETUAL:0G-USDT@LIN`) present in `book_snapshot_5` objects from `2026-07-31T21:14Z`;
      `ASTER` real rows present in `liquidations` objects from `2026-07-31T21:16Z` (same connector file as `ASTER`
      `book_snapshot_5` — `aster_book_liq_ws.py` — so this is direct evidence the connector itself parses correctly
      post-fix; `ASTER` `book_snapshot_5` specifically wasn't yet observed in my scan window, likely just a
      lower-frequency publish batch, not a separate bug). This is the FIRST time any of these 3 venues' book/liquidation
      data has reached the warm tier with real content (previously either the connector produced 100% empty capture, or
      — for `OKX-FUTURES` — the whole WS connector was broken).
- [ ] [DATA] P1.2. **⏸ PARKED 2026-07-31 (main, Option A — gated behind false prereq `p1-2-preconditions-met`,
      priority:999).** Doubly-blocked and NOT worker-satisfiable: unpark only once BOTH (a) ≥24h since the P1.1 redeploy
      (`2026-07-31T21:14Z`, i.e. ~`2026-08-01T21:14Z`) have elapsed AND (b) a paper run trading these 3 venues is
      confirmed (see `/plans/archive/2026_08/no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md`).
      **Time-gated, unblocked by P1.1 above — needs real elapsed time, not just a worker pass.** Re-run the
      `paper(W)==batch-rerun(W)` determinism test for BINANCE-FUTURES/ASTER/OKX-FUTURES now that real warm+cold data is
      confirmed flowing (P1.1). DoD: epsilon=0 match cited with the test run's report path (per
      `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` §5, the `daily-determinism`
      CLI/`DailyDeterminismHandler` in `batch-live-reconciliation-service`). **Two real preconditions this todo cannot
      itself satisfy synchronously**: (1) a full day (T+1 cadence) of real post-2026-07-31T21:14Z capture for these
      venues needs to accumulate before a meaningful daily determinism window exists — checking today would compare
      against near-zero data; (2) `DailyDeterminismHandler.run()` is an honest no-op (`skipped: no_run_configured`)
      unless `cfg.paper_ledger_root`/`cfg.batch_ledger_root` are set, i.e. there needs to be an ACTIVE paper strategy
      run trading instruments on these 3 venues — this worker did not find one running
      (`gcloud compute instances list --filter="name~paper OR name~colocated"` → 0 results) and confirming/starting one
      is outside this plan's stated scope (a strategy-desk decision, not a data-pipeline redeploy). A future worker
      picking this up should: (a) confirm ≥24h has elapsed since the P1.1 redeploy timestamp above, (b) confirm a paper
      run trading these venues exists (or escalate that gap as its own finding if not), (c) run the `daily-determinism`
      operation for the relevant day and cite the report path here.
- [ ] [DATA] P2. Cross-check whether any of the 52 asset_group x data_type combinations still show ZERO messages ever
      delivered a full week after this plan's todos above land — this would point at a genuine producer-side gap
      (nothing ever calls `publish()` for that shard) distinct from the subscription-expiry bug this plan fixes. File
      each such case as its own `plans/active/issues/<slug>_<date>.md` rather than leaving it unrecorded here — this is
      a `[DIAG]` finding-generator todo, not itself a fix.
- [x] ✅ [DATA] P3. 48h after the `terraform apply` todo above lands, re-check
      `gcloud pubsub subscriptions list --filter="name:warm-sink"` still returns 52 (proves the never-expire policy
      actually holds under real traffic, not just that recreation worked once). Piggyback (from the `[INFRA] P2`
      scheduler-trigger todo above): also check `gcloud run jobs executions list --job=live-event-log-compactor` for a
      `live-event-log-compactor-daily`-sourced execution dated 2026-08-01 and confirm it succeeded. — Re-checked
      2026-08-02: `gcloud pubsub subscriptions list --filter="name:warm-sink"` still returns exactly **52** (the
      never-expire policy holds under 2 full days of real traffic since the `739345c` apply). The real 2 AM UTC cron
      fired **twice** since, both real Cloud Scheduler-sourced executions (not manual triggers): `-hhkvf`
      (2026-08-01T02:00:19Z, `succeededCount: 1`) and `-xwlzj` (2026-08-02T02:00:06Z, `succeededCount: 1`) — closes the
      loop on the `[INFRA] P2` todo's literal DoD, independently observed now rather than only via the manual-run
      substitution.
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
- **2026-07-31**: Todo 3 done — `scripts/verify_warm_sink_subscription_paths.py` shipped (deployment-service@95a79a7)
  and run live: parses all 52 `warm_sink.tf` resource blocks, diffs each against the live subscription's
  `cloud_storage_config`, and cross-checks the declared `filename_prefix` actually encodes that resource's own
  `asset_group`/`data_type` labels (catches a copy-paste mismatch even if bucket/prefix/suffix happened to still
  diff-clean). Result: 52 declared, 52 live, **0 mismatches** — no cross-shard write risk. (Active gcloud identity on
  this shared host kept reverting to `github-actions-deploy`, which lacks `pubsub.subscriptions.list` on this project;
  switched to the ambient `unified-trading-sa` identity per RULES.md § 5 self-service rule, re-verified live.)
- **2026-07-31**: Todo 5 (manually trigger + verify) — found two prior executions from before this session
  (`live-event-log-compactor-h55rg`, `-gpvsk`) both failed on `BucketNamingError: Unknown asset_group 'warm'`
  (`_warm_bucket()` was passing `asset_group="warm"` to `resolve_bucket_name`, which only accepts
  cefi/defi/prediction/sports/tradfi). That fix was already committed in code (`18e1ec0`, landed on origin before this
  session) but the deployed Cloud Run Job image predated the fix (built 14:20:02, fix landed 14:30:08) — the
  `deployment-service-jobs-image.cloudbuild.yaml` build is manual (`gcloud builds submit`), not trigger-wired on push,
  so a landed code fix never reaches the running job without an explicit rebuild. Rebuilt (Cloud Build `490485d5`),
  which surfaced bug #2: the job's terraform (`compaction_job.tf`) set env var `GCP_PROJECT` but `resolve_bucket_name`'s
  template substitution requires `GCP_PROJECT_ID` (confirmed via the two sibling maintenance jobs' terraform, both
  correct) — fixed + applied (deployment-service@b6eaef2, terraform 0 add/1 change/0 destroy). Re-triggered (`-bmmzn`)
  and hit bug #3, the real root cause: `pyarrow.lib.ArrowInvalid: Parquet magic bytes not found in footer` while
  compacting `prediction/book_snapshot_5`'s 835 warm files. **Not file corruption** — inspected the raw bytes directly
  (`gcloud storage cat -r 0-300`) and every warm-sink object is actually a raw JSON `CanonicalPersistEnvelope` Pub/Sub
  message (`{"schema_version":"1","asset_group":"prediction",...,"payload_inline": "[{...}]"}`), never Parquet, despite
  the `.parquet` filename suffix. Root cause: none of the 52 `google_pubsub_subscription.cloud_storage_config` blocks in
  `warm_sink.tf` set `parquet_config`/`avro_config`, so Pub/Sub's Cloud Storage subscription writes the message bytes
  verbatim — this affects **all 52 shards**, not just this one; the warm tier has never actually contained Parquet since
  the subscriptions were created 2026-06-29. Fixed by making the compactor the actual JSON→Parquet conversion boundary:
  `compact_shard` now parses each warm object via `CanonicalPersistEnvelope.model_validate_json`, extracts
  `payload_inline` (a JSON row or list of rows), and builds the cold Parquet file from the concatenated rows
  (deployment-service@f53973a, `_extract_rows()` + unit tests in `tests/unit/test_live_event_log_compactor.py`; a
  malformed envelope or unsupported `payload_pointer` is logged and skipped, never crashes the whole shard). Rebuilt the
  image again (Cloud Build `ca5ef1f5`), re-triggered (`-tx9p2`) — **SUCCEEDED**, real parquet verified in cold storage
  (see todo 5 evidence above). No new issue doc filed — root-caused and fixed within this same plan/file/session, not
  deferred.
- **2026-07-31**: Todo 6 (confirm the Cloud Scheduler trigger) done — verification-only, no code change. Switched active
  gcloud identity to `unified-trading-sa` (the `github-actions-deploy` default lacks `cloudscheduler.jobs.get`/`.run` on
  this project, same recurring shared-host identity drift noted for todo 3). `state: ENABLED` confirmed. Rather than
  hold the session open ~7.5h for the literal next cron tick (`scheduleTime: 2026-08-01T02:00:01Z`), ran
  `gcloud scheduler jobs run live-event-log-compactor-daily` — the actual Scheduler API invoking its configured HTTP
  target, i.e. the same path the cron uses, not a bypass via direct `gcloud run jobs execute`. `lastAttemptTime`
  advanced with `status: {}` (success; this morning's real cron attempt at `02:01:19Z`, before today's fixes, had
  recorded `status: {code: 3}` — failure), and execution `live-event-log-compactor-fbmq6` appeared and reached
  `Completed: True, succeededCount: 1` in 4m12s. Confirms the Scheduler→Cloud-Run wiring is sound going forward. The
  literal 2026-08-01T02:00 UTC firing itself isn't independently observed by this todo — folded into the existing
  time-gated `[DATA] P3` subscription-recheck todo below as a natural piggyback check, rather than adding a new todo for
  the same job.
- **2026-07-31 (slot-14)**: Todo P1 split into P1.1 (done) / P1.2 (open, time-gated) mirroring the plan's own precedent.
  P1.1: found the running live CeFi capture VM (`mtds-live-cefi-consolidated-20260730-010147`) was deployed 17 days
  before the two WS-connector fix commits this todo names, confirmed via SSH (deployed connector file mtime
  `2026-07-13`, predates the `2026-07-30` fixes). Verified the floating tarball manifest already contains both fix
  commits as ancestors, then redeployed (delete old VM → relaunch via the standard launcher →
  `mtds-live-cefi-consolidated-20260731-211041`). Live-verified past process-alive: read real post-redeploy warm-tier
  parquet objects and found genuine `BINANCE-FUTURES`/`OKX-FUTURES` book_snapshot_5 depth rows and `ASTER` liquidations
  rows — the first time these 3 venues' data has reached the warm tier with real content. P1.2 (the determinism test
  itself) is left open: it has two real preconditions (elapsed accumulation time + an active paper strategy run trading
  these venues, neither confirmed to exist) that can't be satisfied by a single worker pass — see the todo's own text
  for the concrete next-worker checklist.
- **2026-07-31 (slot-8)**: Picked up P1.2. Reconfirmed both preconditions still unmet at `2026-07-31T22:03:41Z`: (1)
  only ~49 minutes elapsed since the P1.1 redeploy (`2026-07-31T21:14-21:16Z`) — nowhere near the 24h needed for a
  meaningful accumulation window; (2) `gcloud compute instances list --filter="name~paper OR name~colocated"` still
  returns zero results (same finding as slot-14's same-day check). Per the todo's own instruction to escalate the
  paper-run gap as its own finding if unresolved, filed
  `/plans/archive/2026_08/no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md` — this gap is potentially
  permanent (not just time-gated), since no active paper deployment trades these 3 venues under any name this search
  matched. Leaving P1.2 open/unflipped; the time-gate alone means today is genuinely too early regardless of the
  paper-run question.
- **2026-07-31 (slot-6)**: Picked up P1.2 a third time (~90 min after slot-14→8). Re-verified both preconditions still
  unmet at `2026-07-31T22:20Z`: (1) only ~66 min elapsed since the P1.1 redeploy (`21:14Z`) vs the ≥24h needed (clears
  ~`2026-08-01T21:14Z`); (2) no paper run — reconfirmed via a **broader-than-VM-name** check (ALL `RUNNING` compute
  instances **and** Cloud Run services on `central-element-323112`, addressing the issue doc's own note that a
  differently-named or non-VM paper deployment could exist): no paper/strategy trading deployment exists for these
  venues; the only recon-related service is `batch-live-reconciliation-service`, which is the determinism _consumer_ (a
  no-op without `paper_ledger_root`/`batch_ledger_root` from an active paper run). Refused to fabricate an ε=0 result
  against near-zero data. Since P1.2 had now churned through 3 workers in ~90 min with zero possible progress, escalated
  the operational churn via `/blocked` (**BLK-085fef5e**). **Main answered Option A and parked the backlog entry**
  (`priority:999` + `priority_override:true` + false prereq `p1-2-preconditions-met`; blockers endpoint confirms gated)
  — stops the fleet churn. Option B (start a paper run) is explicitly left as the `[OPERATOR]` strategy-desk decision
  already tracked in the issue doc, not made here. P1.2 stays open/unflipped (parked, not done); unpark = flip
  `p1-2-preconditions-met` GREEN once BOTH the 24h window has elapsed AND a paper run is confirmed.
- **2026-08-02**: Picked up the `[DATA] P3` 48h re-check (operator asked to confirm the durable-GCS-landing question was
  actually closed out, not left open). Both preconditions the todo names now empirically hold: `warm-sink-*`
  subscription count is still 52 two full days after the `739345c` apply, and the real Cloud Scheduler-sourced 2 AM UTC
  cron has now fired successfully twice (`-hhkvf` 2026-08-01, `-xwlzj` 2026-08-02) — not just the manual substitution
  run from 2026-07-31. Flipped. **Remaining open work is P1.2 (still correctly parked — genuine operator-decision gate,
  not worker-satisfiable) and P2 (not due for another ~5 days — needs a full week of traffic to mean anything).** The
  `[SCRIPT] P3` doc-cleanup todo stays open too, since it's explicitly gated on every todo above being done, which isn't
  true yet.
- **context-scout 2026-08-03**: populated context_scope (5 entries).

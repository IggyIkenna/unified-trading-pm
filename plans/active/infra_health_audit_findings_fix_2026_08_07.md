---
doc_type: plan
title: Fix the infra-health-audit findings (Cloud Run Jobs/Services + VM fleet) and document alert-coverage gaps
summary: >-
  A 2026-08-07 3-agent parallel audit of Cloud Run Jobs, Cloud Run Services, and the GCE VM fleet in
  central-element-323112 found ~12 real, currently-active issues (crash-loops, OOM, dead schedulers firing into voids, a
  hung idle VM burning billing, stale GCR image paths, a 19-month-broken min-instances service). Per operator direction:
  exclude the DeFi manifest-consolidator pause (already a known, tracked, intentional condition —
  /plans/active/issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md). For every remaining finding,
  first determine whether it already fired a #data-pipeline-alerts or #uts-live-alerts Slack alert (document the gap if
  not — a real finding in its own right, since a bug nobody gets paged for is a bug that never gets found), then fix the
  underlying issue regardless of alert status. Also run a dedicated zombie sweep (VMs and Cloud Run job executions that
  are technically "running" but doing nothing) beyond what the original audit incidentally found.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos:
  [
    market-tick-data-service,
    client-reporting-api,
    deployment-service,
    alerting-service,
    unified-trading-library,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [infra-health, oom, crash-loop, zombie, cloud-run, gce, alert-coverage, audit]
related:
  [
    /plans/active/issues/alerting_service_lifecycle_events_sub_dual_consumer_slack_spam_2026_08_07.md,
    /plans/active/issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
  ]
created: 2026-08-07
last_updated: 2026-08-07
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by:
locked_since:
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/15-runbooks/safe-service-restart-procedures.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator ("great so all those issues... should have hit alerts... if they didnt we need to document and then fix them
  and if they did great we still need to fix them /autonomous"), 2026-08-07, following a 3-agent infra health audit.
assigned_role: infra
drift_direction: advance-code
---

# Fix the infra-health-audit findings

## Todos

- [ ] [SCRIPT] P0. **Dedicated zombie sweep** — beyond the original audit, specifically hunt for: (a) Cloud Run job
      EXECUTIONS stuck in a non-terminal state far longer than the job's peers (truly stuck, not the already-found
      OOM-crash-loops which DO recover), (b) duplicate/orphaned VMs doing redundant work on the same target (the
      `uts-prod-alerting-paging` dual-consumer pattern from earlier today is the template for this class of bug), (c)
      any GCE VM with a heartbeat that stopped climbing days ago but the instance is still billably RUNNING. Report only
      genuinely-zombie findings, not restatement of the original audit.
- [ ] [SCRIPT] P0. **Alert-coverage cross-reference** — for every finding below (excluding the DeFi consolidator), check
      `#data-pipeline-alerts` and `#uts-live-alerts` (via `scripts/dev/slack-read-channel.py`,
      `SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")`) across the finding's actual active window
      for a matching alert. Cross-check against `codex/05-infrastructure/data-pipeline-alerts.registry.yaml` for whether
      a rule even EXISTS that should cover this failure class. Produce a table: finding → alert fired?
      (yes/no/no-rule-exists) → evidence. File gaps as their own todo/issue-doc entries — a real coverage gap is a
      finding in its own right, not just a footnote.
- [x] [SCRIPT] P0. ✅ **`market-data-query-service` — DECOMMISSIONED, not patched.** Investigation before fixing found
      this reclassifies from "fix the bucket" to "dead service": (1) zero real HTTP requests in 7 days (only the
      internal startup probe, which fails) — `gcloud logging read` for `httpRequest.requestUrl!=""` returned nothing;
      (2) its ONLY revision (`market-data-query-service-00002-g9r`) was created `2025-10-20T19:42:12Z` — not redeployed
      in ~10 months; (3) `gs://market-data-candles` was deliberately RETIRED `2026-04-18` per
      `unified-trading-pm:plans/archive/data_pipeline_completion_2026_04_18.plan.md` ("empty; co-location wins") —
      candles now live co-located under `market-data-tick-{category}-{project}/processed_candles/`, so this service
      predates a real architecture migration and was never updated; (4) its backing Artifact Registry repo
      `market-data-handler` is now **0.000MB / empty** (an aggressive `delete-older-than-3d` cleanup policy has been
      silently deleting its own images) — the source code for `market_data_query_service.py` could not even be located
      anywhere in the GitHub org (`gh search code`, zero hits); (5)
      `deployment-service/configs/     gcp_service_accounts.yaml`'s own audit comment groups it in the same "sampled
      5/7" list as `batch-live-reconciliation-service`/`fund-administration-service`/`trading-agent-service` — 3 of
      which are ALREADY confirmed dead-weight stubs in the P3 decommission todo below. Deleted via
      `gcloud run services delete market-data-query-service --region=asia-northeast1` (2026-08-07). Its `deployment-ui`
      references (`src/lib/mock-api.ts`, a smoke-test testid) run against a MOCK API, not the live service, so nothing
      else needed updating. Folded into the P3 dead-weight cluster rather than counted separately.
- [x] ✅ [SCRIPT] P0. **Alert-coverage cross-reference** — DONE 2026-08-07. Checked all 11 non-excluded findings against
      `#data-pipeline-alerts` (8-day + 8h `scripts/dev/slack-read-channel.py` pulls) and the DP-* registry +
      `unified-api-contracts` `codes.py`/`rules.py`. **Zero of 11 fired a Slack alert.** `#uts-live-alerts` could not be
      checked — reader bot returns `not_in_channel` (residual verification gap, noted not assumed-negative). Filed
      `/plans/active/issues/infra_health_audit_alert_coverage_gaps_2026_08_07.md` with the full finding→status→evidence
      table + 3 structural gap classes (Cloud Run Service/Job compute-failure blind spot; dp-alerting-subscriber's own
      GCS-429 misrouting past an existing DP-VM-006 rule; zero AlertCode coverage for AWS IAM/STS) + 4 follow-up todos.
      Findings 4 and 8 flagged as a distinct case (a conceptually-matching rule exists but apparently didn't fire —
      needs live MissTracker state, not a Slack/code read) rather than filed as a gap. Cross-referenced 3 already-open
      same-day docs to avoid duplicating in-flight root-cause work. (repo: unified-trading-pm)
- [ ] [SCRIPT] P0. **Fix `market-data-query-service` crash-loop** — hardcoded `gs://market-data-candles` (doesn't exist)
      in `_init_gcs_client()`; real buckets use `market-data-tick-{ag}-{prd|test}-central-element-323112`. Find the
      correct bucket via `resolve_bucket_name(...)` (never hand-roll the string), fix, redeploy, verify the revision
      actually stays healthy post-deploy (not just "Ready" — confirm an actual successful request/instance start in
      logs).
- [ ] [SCRIPT] P0. **Fix `client-reporting-batch` OOM** — 512Mi/1cpu limit, 100% failure for 30+ hours. Raise the Cloud
      Run job's memory limit to a sane value (check what it's actually trying to process to size correctly, don't just
      guess a number) and verify a subsequent execution completes successfully.
- [ ] [SCRIPT] P1. **Fix `uts-prod-data-status-rollup-svc` OOM at its ceiling** — 32Gi/8vCPU maxed, `maxScale=1`. No
      more headroom to add on this axis — investigate whether the rollup can be sharded/batched instead of raising the
      ceiling further, or if a genuine resource bump + `maxScale` increase is the right fix. Verify MTDS/
      instruments-service rollup timeouts stop recurring post-fix.
- [x] [SCRIPT] P1. ✅ **Killed the hung idle `mtds-dex-swaps-backfill-2` VM.** Re-confirmed before deleting: no
      `PROGRESS.json` at its GCS log path (404), `run.log` tail (15:15-15:20Z) showed only RESOURCE_SAMPLE/
      PIPELINE_HEARTBEAT lines at ~0-1.4% CPU, no processing activity since the `process_final=True` shard-complete line
      at 07:50:33Z (7.5h idle). Deleted via
      `gcloud compute instances delete mtds-dex-swaps-backfill-2     --zone=asia-northeast1-c` (2026-08-07T15:2xZ) —
      justification: confirmed-finished worker VM, non-preemptible on-demand billing with zero further useful work
      possible, not a data-delete (no GCS/manifest content touched).
- [ ] [SCRIPT] P1. **Fix or decommission `vm-serial-capture-prd`** — dead 19 days (`ContainerMissing`, image deleted),
      Cloud Scheduler still firing 4x/day into the void. Determine whether serial-capture is still needed; if yes,
      rebuild+republish the image and verify a real execution succeeds; if no, pause/delete the scheduler + job rather
      than leaving it firing forever.
- [ ] [SCRIPT] P1. **Fix the 3 dead `europe-west1` jobs** (`tardis-data-loader`, `check-missing-cloud-storage`,
      `gen-inst-defs`) — 100% failure for 50 days on a stale `gcr.io/...` path orphaned by the AR migration. Point each
      at the correct Artifact Registry image path (grep how sibling jobs in the same region/service reference their
      image post-migration) and verify a real execution succeeds, or decommission if genuinely obsolete — determine
      which per what each job is actually supposed to do before deciding.
- [ ] [SCRIPT] P1. **Fix `live-event-log-compactor` daily OOM** — 4Gi limit, OOM every scheduled 02:00 UTC run for 7
      straight days despite an already-generous limit; data growth is outpacing capacity. Investigate whether this is
      unbounded growth (a leak / missing retention/compaction elsewhere) before just raising the limit again — raising
      the ceiling on a growth trend just delays the next OOM.
- [ ] [SCRIPT] P2. **Reduce `mtds-backfill-odds-401-retry` memory footprint** — OOM every 7-9 min but self-recovers and
      keeps progressing; wasteful, not broken. The sibling `mtds-backfill-odds-smallchunk-20260807` run (smaller chunks,
      far fewer OOMs) is a working precedent — apply the same chunk-size mitigation here.
- [ ] [SCRIPT] P2. **Fix the `dp-alerting-subscriber` GCS 429 retry storm** on `write_config_snapshot`'s
      `routing_rules.yaml` writes (479 occurrences in one day, separate from the already-fixed `mirror_live` bug) —
      likely needs a write-coalescing/backoff fix rather than raw retry, since the write frequency itself looks like the
      problem (an object-mutation rate limit implies redundant writes of the same content).
- [x] [SCRIPT] P3. **Fix the AWS cost-snapshot IAM failure** ✅ — root cause: OIDC identity drift, not a permissions
      bug. AWS IAM role `gcp-cloudrun-athena-cost-reader` (trust policy `Federated: accounts.google.com`, condition
      `accounts.google.com:sub == 104881302737822972808`) was provisioned 2026-07-14 trusting
      `unified-trading-sa@central-element-323112.iam.gserviceaccount.com`'s OIDC subject, but the LIVE
      `uts-shared-deployment-api` Cloud Run revision actually runs as
      `uts-prd-sa@central-element-323112.iam.gserviceaccount.com` (uniqueId `108768985147151736276`, verified via
      `gcloud run services describe ... spec.template.spec.serviceAccountName`) — a different SA, different `sub` claim,
      hence the deployed service's minted OIDC token was never trusted by the role and every
      `sts:AssumeRoleWithWebIdentity` in `deployment_api/scripts/cost_snapshot_worker.py`'s
      `_load_cloud(CLOUD_AWS, ...)` → `aws_facts` → `get_athena_analytics_client` path (used by both the Cloud
      Scheduler-driven `/api/costs/snapshot-run` endpoint AND the standalone worker entrypoint) hit AccessDenied. Fixed
      by widening the AWS-side trust policy condition to
      `StringEquals accounts.google.com:sub: [104881302737822972808,     108768985147151736276]`
      (`aws iam update-assume-role-policy --role-name gcp-cloudrun-athena-cost-reader`) — trusts both the
      originally-provisioned SA and the actual runtime SA, non-destructive. Verified end-to-end LIVE: minted a real OIDC
      id-token as `uts-prd-sa`
      (`gcloud auth print-identity-token --impersonate-service-account=uts-prd-sa@...     --audiences=arn:aws:iam::427895769566:role/gcp-cloudrun-athena-cost-reader`)
      and called `aws sts assume-role-with-web-identity` with it — succeeded, returning
      `arn:aws:sts::427895769566:assumed-role/gcp-cloudrun-athena-cost-reader/verify-fix-test3`. No GCP-side code/config
      change needed — AWS IAM change only.
- [x] [SCRIPT] P3. **Decommission dead-weight services** ✅ — verified each independently (not just trusting the
      original audit) via
      `gcloud run services describe <svc> --region=<r> --format="table(status.traffic,status.conditions)"` +
      region-scoped Cloud Logging (`resource.labels.service_name=... AND resource.labels.location=...`) for any real
      request traffic, then deleted via `gcloud run services delete <svc> --region=<r> --quiet`. All 6 confirmed: single
      revision `00001` (or equivalent), `HealthCheckContainerError`, `status.traffic` empty/absent (never routed),
      near-zero log volume (3 lines = just the startup-failure event; 0 httpRequest entries in 30-90d). Deleted:
      `batch-live-reconciliation-service` (asia-northeast1, created 2026-07-22), `deployment-service` (asia-northeast1,
      created 2026-07-22 — confirmed this is the STUB, image `.../unified-trading-system/deployment-service:latest`,
      zero relation to the real, live `uts-shared-deployment-api` service which was independently confirmed still
      serving post-delete), `fund-administration-service` (asia-northeast1, created 2026-07-22), `trading-agent-service`
      (asia-northeast1, created 2026-07-22), `odum-portal-staging` (us-central1, created 2026-04-24, 0 logs/0 requests
      in 90d region-scoped), `central-market-data-tardis-loader` (europe-west1, created 2024-06-29, broken since
      2024-12-16, 0 logs in 7d; `minScale` annotation not actually present at delete-time, defaults to 0 — the
      "continuously retrying" framing was stale, but dead-since-2024/zero-traffic independently confirmed regardless).
      **Caught a near-miss**: an UN-region-scoped log query for `odum-portal-staging` initially returned 6173 log lines
      incl. live 200-status `/health` + `/wizard` traffic — turned out to be a SEPARATE, live `odum-portal-staging`
      service in **europe-west4** (183 revisions, 100% traffic, unrelated to the dead us-central1 stub the task named)
      whose logs share the same `service_name` label; re-scoped the query with `resource.labels.location="us-central1"`
      and got 0 logs/0 requests, confirming ONLY the us-central1 instance was dead. The europe-west4 live instance and
      the real `uts-shared-deployment-api` were both verified untouched post-deletion.
- [ ] [SCRIPT] P1. **Recheck `mdps-backfill-cefi-20260807-130321` preemption** — preempted 2026-08-07T14:49:27Z; the
      same launcher left a sibling VM un-relaunched for ~33h on 2026-08-04. Verify it actually got relaunched this time
      (per the PROGRESS-checkpoint contract) — if not, this is the exact class of bug the launcher-registry
      preemption-recovery contract is supposed to prevent, and needs the same fix applied fleet-wide, not just a one-off
      relaunch.

## Progress Log

- 2026-08-07: Plan created following a 3-agent parallel infra health audit (Cloud Run Jobs, Cloud Run Services, GCE
  VMs). Excluding the DeFi manifest-consolidator finding per operator direction (already tracked as a known, intentional
  condition). Proceeding under `/autonomous`.
- 2026-08-07: Todo 2 (alert-coverage cross-reference) DONE — see the todo's own entry for the full summary. Filed
  `/plans/active/issues/infra_health_audit_alert_coverage_gaps_2026_08_07.md`.

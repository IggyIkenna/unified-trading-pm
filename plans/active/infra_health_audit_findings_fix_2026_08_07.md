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
- [ ] [SCRIPT] P1. **Kill the hung idle `mtds-dex-swaps-backfill-2` VM** — finished its work 7+ hours ago (per its own
      manifest-shard-complete log line), never exited, burning non-preemptible on-demand billing idle. Confirm it's
      genuinely done (re-check PROGRESS.json / manifest state is final) before terminating; this is a real
      delete-adjacent action — cite reversibility per delete-safety-protocol before executing (a VM stop/delete on a
      confirmed-finished worker is not the risky "prod bucket delete" class, but state the justification anyway).
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
- [ ] [SCRIPT] P3. **Fix the AWS cost-snapshot IAM failure** (`sts:AssumeRoleWithWebIdentity` AccessDenied,
      `uts-shared-deployment-api`, ~1x/day) — fix the OIDC role trust policy/permissions; low frequency but a real,
      recurring failure.
- [ ] [SCRIPT] P3. **Decommission dead-weight services** — the never-successfully-deployed stubs
      (`batch-live-reconciliation-service`, `deployment-service` [stub, not the real one],
      `fund-administration-service`, `trading-agent-service`, `odum-portal-staging`) and
      `central-market-data-tardis-loader` (broken 19 months, `minScale=2` continuously retrying a container that has
      never once started — pure waste). Confirm each is genuinely dead code (not an in-progress rollout) before
      deleting; delete the Cloud Run resource, not just the symptom.
- [ ] [SCRIPT] P1. **Recheck `mdps-backfill-cefi-20260807-130321` preemption** — preempted 2026-08-07T14:49:27Z; the
      same launcher left a sibling VM un-relaunched for ~33h on 2026-08-04. Verify it actually got relaunched this time
      (per the PROGRESS-checkpoint contract) — if not, this is the exact class of bug the launcher-registry
      preemption-recovery contract is supposed to prevent, and needs the same fix applied fleet-wide, not just a one-off
      relaunch.

## Progress Log

- 2026-08-07: Plan created following a 3-agent parallel infra health audit (Cloud Run Jobs, Cloud Run Services, GCE
  VMs). Excluding the DeFi manifest-consolidator finding per operator direction (already tracked as a known, intentional
  condition). Proceeding under `/autonomous`.

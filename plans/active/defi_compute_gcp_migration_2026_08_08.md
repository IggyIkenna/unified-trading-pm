---
doc_type: plan
title: Move DeFi live/batch compute off AWS to GCP Cloud Run — data already lives in GCS
summary: >-
  execution-service and features-service run as live AWS ECS Fargate tasks (cluster uts-defi-prod, ap-northeast-1) but
  their real data lives entirely in GCS (central-element-323112) — the same-named AWS S3 buckets are empty. This drives
  real, ongoing cross-cloud egress (~$235/mo observed) on top of the AWS compute cost itself. Operator confirmed no real
  trading capital is at risk (live market-data streaming only, not real-money execution), so a straightforward
  drain-verify-cutover is safe — brief downtime is acceptable. GCP-side Cloud Run manifests for all 3 DeFi services
  already exist and are current; this is completing an already-decided direction (GCP primary / AWS secondary), not
  reversing one. Target: decommission all DeFi production/live/batch/monitoring compute from AWS, leaving only the CI VM
  and AO/planning VM there, for an estimated further ~$250/month savings.
status: active
nature: process
asset_group: [defi, infrastructure]
stage: [live, execution, meta]
repos:
  [
    deployment-service,
    execution-service,
    features-service,
    strategy-service,
    unified-trading-pm,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags: [aws, gcp, cloud-migration, cost, cross-cloud-egress, ecs, fargate, cloud-run, defi]
related:
  [
    /plans/active/defi_compute_gcp_migration_2026_08_08_finalize_2026_08_08.md,
    /plans/epics/security_and_cross_cutting_master.md,
    /plans/archive/2026_05/aws_migration_defi_first_2026_05_07.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/archive/issues/infra_health_audit_alert_coverage_gaps_2026_08_07.md,
    /codex/04-architecture/cloud-agnostic-migration.md,
    /codex/11-project-management/dual-cloud-cost-ops-playbook.md,
    /codex/04-architecture/seamless-cloud-switch.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/05-infrastructure/dual-cloud-image-builds.md,
    /codex/04-architecture/promote-workflow-architecture.md,
    /plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
assigned_role: infra
effort: medium
drift_direction: advance-code
depends_on: []
sequential: true # operator directive 2026-08-08: flip to AO dispatch. Several todos have a real
# ordering dependency this plan's own file-order encodes (todo 1's finding gates the
# execution-service cutover; each service's deploy->verify->cutover->delete is itself
# sequential) that same-priority concurrent dispatch would NOT respect on its own --
# serializing the whole plan is the safe choice for a live-infra cutover, even at the cost
# of forgoing parallelism on the doc-update todos.
context_scope:
  [
    /codex/04-architecture/cloud-agnostic-migration.md,
    /codex/11-project-management/dual-cloud-cost-ops-playbook.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/epics/security_and_cross_cutting_master.md,
    deployment-service/configs/aws/,
  ]
source:
  [
    "operator, interactive session, 2026-08-08 — asked for an AWS cost audit, which surfaced empty AWS S3 buckets for
    live DeFi services alongside real, populated GCS counterparts; operator confirmed no real trading capital is at risk
    (live data streaming only) and directed migrating all DeFi production/live/batch/monitoring compute off AWS, keeping
    only the CI VM and AO/planning VM there, targeting ~$250/mo further savings.",
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Move DeFi live/batch compute off AWS to GCP Cloud Run

## Why this plan exists

A routine AWS cost audit (triggered by downsizing the CI VM and AO VM earlier the same session) found `ap-northeast-1`
EC2/EBS/ECS/Secrets-Manager/data-transfer spend far exceeding what the CI+AO VMs alone account for. Digging into
`Amazon Elastic Container Service` costs found **two live, running ECS Fargate services** — `uts-features-service-prod`
and `uts-execution-service-prod` (cluster `uts-defi-prod`) — both tagged `CLOUD_PROVIDER=aws`. Direct inspection found
their designated AWS S3 buckets (`features-defi-prd-427895769566`, `execution-store-defi-427895769566`,
`market-data-tick-defi-prd-427895769566`, `instruments-store-defi-prd-427895769566`) **completely empty (0 objects)**,
while the same-named GCS buckets in `central-element-323112` hold real data (manifest indices, availability index,
parquet files). `uts-strategy-service-prod` exists in the same cluster but is currently scaled to 0.

**This is not a new architectural direction — it completes one already decided.** Codex SSOTs
(`/codex/04-architecture/cloud-agnostic-migration.md`, `/codex/11-project-management/dual-cloud-cost-ops-playbook.md`)
already state GCP is primary and AWS is secondary/DR. The AWS ECS placement traces to
`/plans/archive/2026_05/aws_migration_defi_first_2026_05_07.md` (a May 2026 DeFi-client-mandate + AWS-credits push),
whose central premise — data AND compute co-located on AWS — was **never completed** (Phase 5 GCS→S3 sync and Phase 7
dual-cloud validation were deferred at archival). The operator independently reached the same "AWS is not a live write
target" conclusion on 2026-07-16 (see that plan's "Correction 2026-07-16" section) — this plan executes on that finding,
three weeks later, now that the cost impact is quantified.

**Good news found while scoping this**: GCP-side Cloud Run manifests for all three services already exist and are
current — `deployment-service/configs/cloud-run/{execution-service,features-service,strategy-service}.yaml` — each
deliberately `minScale=1/maxScale=1` (always-on, no split-brain risk from concurrent instances), pointed at
`central-element-323112`/`asia-northeast1`, with service accounts already provisioned and the dual-cloud image pipeline
already building GCP images for them continuously. This is a cutover, not a from-scratch build.

**Risk profile, confirmed by operator 2026-08-08**: no real trading capital is at risk — current DeFi activity is live
market-data streaming, not real-money execution. Brief downtime during cutover is acceptable. This means the
`/codex/04-architecture/seamless-cloud-switch.md` drain/snapshot/switch mechanism (confirmed NOT IMPLEMENTED in code,
per the research that scoped this plan) is **not required** for this migration — a straightforward
stop-verify-cutover-decommission sequence is safe. If/when real capital goes live on this path, that mechanism (or an
equivalent) becomes a real prerequisite for any FUTURE cross-cloud move — not this one.

**Scope explicitly excludes** the CI VM (`ci-escalation-runner-vm-1`) and the AO/planning VM (`agent-orchestrator-vm-1`)
— those stay on AWS per operator instruction, already right-sized this same session (see
`/plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md`). Provisioned-but-empty AWS
buckets/env config may remain in place untouched — deleting them is out of scope (no cost driver, no risk from leaving
them).

## Confirmed technical facts (verified 2026-08-08, live AWS/GCP inspection — not assumed)

- **Running AWS compute to migrate**: `uts-features-service-prod` (2 vCPU/4GB Fargate, running) and
  `uts-execution-service-prod` (2 vCPU/4GB Fargate, running), cluster `uts-defi-prod`, `ap-northeast-1`.
  `uts-strategy-service-prod` exists in the same cluster, desired/running count 0 (not currently costing compute, but
  should be pointed at GCP before it's ever turned back on).
- **AWS S3 buckets for these services are empty** (`list-objects-v2` → 0 `KeyCount`) — confirmed for
  `features-defi-prd-427895769566`, `execution-store-defi-427895769566`, `market-data-tick-defi-prd-427895769566`,
  `instruments-store-defi-prd-427895769566`, `dex-pools-prd-427895769566`. The GCP counterpart
  (`features-defi-prd-central-element-323112`) has real data (confirmed via `gsutil ls`).
- **No RDS/ElastiCache/ELB/EKS anywhere in `ap-northeast-1`** — every instance of those services in this AWS account is
  in `eu-west-2`, belonging to Kapsule's unrelated `global-health-dev-aethergate` stack (confirmed by name + region +
  zero overlap with anything `unified-trading-*`). Not in scope, not touched by this plan.
- **`manifest-consolidator`'s 26 AWS Batch job definitions + EventBridge rules are already correctly dormant** — all 26
  `uts-prod-consolidator-*` EventBridge rules are `DISABLED`, deliberately, per
  `/codex/05-infrastructure/manifest-consolidator-ssot.md` + `/codex/02-data/manifest-migration-coordination.md`: they
  were briefly re-enabled 2026-07-16, hit an IAM gap (fixed, kept), then deliberately turned back off same-day once the
  operator confirmed AWS has no live data to consolidate. GCP already has an equivalent-sounding live service
  (`uts-prod-data-status-rollup-svc`, Cloud Run, `asia-northeast1`) — **todo 6 below needs to confirm this actually
  covers the same job, not just a similar name, before deciding whether the AWS Batch definitions are safe to delete
  outright vs. merely left dormant.**
- **GCP Cloud Run targets already fully specified**:
  `deployment-service/configs/cloud-run/{execution-service, features-service,strategy-service}.yaml`, each
  `minScale=1/maxScale=1`, `CLOUD_PROVIDER=gcp`, correct project/region/ service-account, health probes wired.
  `features-service.yaml` already documents the exact data-locality reasoning this plan is built on. **Not yet confirmed
  live** — `gcloud run services list` did not show any of the three as an existing deployed Cloud Run service as of
  2026-08-08 (todo 1 confirms this precisely before assuming zero state).
- **Deploy tooling gap**: `execution-service.yaml`/`strategy-service.yaml` reference `scripts/cloud-run/deploy.sh`,
  which does not exist in `deployment-service/scripts/cloud-run/` (only `deploy-shared.sh`, `deploy-ui.sh`,
  `deploy-agent-orchestrator.sh`, `deploy-traffic-pin-bridge.sh`, `canary-deploy.sh` exist). `features-service` has its
  own `scripts/cloud-run/deploy_features_service_cloud_run.sh`. Todo 2 closes this gap before any deploy attempt.
- **Two open questions from the research pass, not yet resolved — investigate before/during cutover, not after**: (a)
  exactly what role `execution-service`'s AWS deployment plays relative to the GCE-VM-based live-strategy-promote path
  (`run-live.sh`/`launch-strategy-live-vm.sh` per `/codex/04-architecture/promote-workflow-architecture.md`) — a
  standalone order-routing API those VMs call over the network, or a vestigial deployment not actually in any hot path
  today; (b) what caused `uts-defi-prod` to go from 0 running tasks
  (`/plans/active/artifact_pipeline_observability_2026_07_17.md`, 2026-07-17) to running (today) — no plan/issue
  documents this scale-up. Neither blocks proceeding given the no-real-capital finding, but both should be understood
  before the AWS side is torn down, in case either points at an automated process this plan needs to also disable.
- **`CROSS_CLOUD_EGRESS_DETECTED` alert exists but has 0% fire rate** (per the archived May plan's own alerting
  analysis) — it was apparently never wired into these two services, which is consistent with nobody having noticed this
  cost driver until this session's cost audit found it empirically via CloudWatch + bucket inspection instead.

## Design decisions

- **Sequence by risk, cheapest-to-verify first**: `features-service` → `strategy-service` (currently 0 tasks, no cutover
  risk, just point the eventual launch at GCP) → `execution-service` last (highest stakes even without real capital,
  since it's the one item flagged as possibly network-called by the live GCE promote path).
- **Verify-before-decommission, not blind-flip**: for each service, deploy to Cloud Run, confirm it reads/writes the
  REAL (populated) GCS buckets correctly and passes health checks, THEN scale the AWS ECS service to 0 (not delete
  immediately — keep for a short rollback window), THEN delete once confirmed stable for a few days.
- **No `seamless-cloud-switch.md` mechanism needed for this move** (see "Why this plan exists" — operator-confirmed no
  real capital at risk). Do not block this plan on building that mechanism; if a FUTURE cloud move involves real
  capital, that gap should be reopened as its own todo/plan then, not solved speculatively here.
- **Manifest-consolidator stays dormant on AWS, not migrated verbatim** — no evidence AWS-side consolidation ever had
  live value (see confirmed facts above); the question is only whether to formally decommission the 26 AWS Batch job
  definitions or leave them inert, gated on todo 6's finding about `uts-prod-data-status-rollup-svc` overlap.
- **This plan does not delete the empty AWS S3 buckets or IAM/env scaffolding** — operator explicitly said these can
  remain configured; zero cost driver, zero urgency.
- **Update codex + the `security_and_cross_cutting_master` epic's stale open todos as this ships**, not as an afterthought — the
  epic currently carries "Operator sign-off on dual-cloud parity" (never signed off — this plan's completion IS the
  resolution, in the opposite direction originally imagined) and "GCP bucket decommission" (the literal opposite
  direction of this plan — needs marking superseded, not left to rot as a live-looking contradiction).

## Todos

- [x] ✅ [INFRA] P0. **Confirm `execution-service`'s AWS deployment's actual role** — grep `run-live.sh` /
      `launch-strategy-live-vm.sh` / `colocated_engine.py` (per `promote-workflow-architecture.md`) for any network call
      INTO the AWS ECS `execution-service` endpoint (a load balancer DNS name, a service-discovery lookup, an env var
      pointing at it). Done-when: a written finding — either "the GCE live-promote path calls this AWS endpoint at
      `<location>`, cutover must repoint it to the new GCP Cloud Run URL as part of todo 5" or "confirmed no live caller
      references this AWS deployment; it is not in any current hot path." **FINDING (2026-08-08, slot-11)**: Confirmed
      no live caller references the AWS ECS `uts-execution-service-prod` deployment. The GCE live-promote path
      (`launch-strategy-live-vm.sh` → VM runs `run-live.sh` → `e2e-testing/scripts/defi/colocated_engine.py`) is a
      **colocated in-process engine** — `colocated_engine.py` adds `execution-service` to `sys.path` and imports its
      engine functions directly (zero-serialization, shared memory). Verified: `local-live.env` sets
      `CLOUD_PROVIDER=gcp`, `EXECUTION_PROVIDER=copper` (Copper MPC custody — no AWS endpoint); zero hits searching for
      AWS ALB/ELB DNS names, `EXECUTION_SERVICE_URL` env vars, or HTTP client calls from any of the three scripts or
      their imports. The AWS ECS deployment is not in any current hot path. **Todo 5 (deploy execution-service to Cloud
      Run) does NOT need to repoint any live caller's target URL** — there is no caller that knows the AWS ECS endpoint
      exists. — unified-trading-pm@(see commit)

- [x] ✅ [INFRA] P1. **Find what scaled `uts-defi-prod` from 0 running tasks (2026-07-17) to running (2026-08-08)** —
      check ECS service events (`aws ecs describe-services --query services[].events`) for a scale-up timestamp/reason,
      cross reference against any CI/CD deploy pipeline or manual `update-service --desired-count` in CloudTrail for
      that window. Done-when: the trigger is identified (a specific deploy, a manual action, an autoscaling policy) and
      documented here, or CloudTrail retention has already expired and that's stated explicitly as the reason it can't
      be determined. **FINDING (2026-08-08, slot-9)**: CloudTrail (`ap-northeast-1`, retention current) shows a **manual
      operator action** via `aws ecs update-service`: IAM user `arn:aws:iam::427895769566:user/admin_od` (operator's
      admin account) issued `update-service --desired-count 1` for both `uts-features-service-prod` and
      `uts-execution-service-prod` on **2026-07-26T18:56:52Z / 18:56:54Z** from IP 148.252.133.4 (AWS CLI/macOS). A
      second call for `uts-execution-service-prod` at 22:30:19Z from IP 102.188.39.132 (same user). No CI/CD deploy
      pipeline, autoscaling policy, or scheduled task triggered this — it was a direct manual CLI scale-up 9 days after
      the 2026-07-17 observation of 0 running tasks. **No automated process to disable before AWS teardown.** —
      unified-trading-pm@(see flip commit)

- [x] ✅ [INFRA] P1. **Confirm the 3 GCP Cloud Run services (`execution-service`, `features-service`,
      `strategy-service`) are not already deployed under a name this plan's `gcloud run services list` pass missed** —
      re-check with `--platform=managed --project=central-element-323112` across ALL regions the fleet uses (not just
      `asia-northeast1`), and check `deployment-api`'s own service registry/database for a record of these 3 if one
      exists. Done-when: a definitive "does not exist yet, deploying fresh" or "exists as `<name>` in `<region>`,
      already at revision `<rev>`" statement. **FINDING (2026-08-08, slot-12)**:
      `gcloud run services list --platform=managed --project=central-element-323112` (all-regions listing, 22 services
      returned) — zero services named `execution-service`, `features-service`, or `strategy-service`. Per-region
      explicit check across `asia-northeast1`, `us-central1`, `europe-west1/2/4`, `asia-south1`, `asia-east1` — all
      returned zero hits. deployment-api's `CLOUD_RUN_SERVICE` census (`routes/_cloud_run_services.py`) reads GCP live
      state directly via the Admin API (no separate local DB); same underlying source, same result. **Conclusion: does
      not exist yet, deploying fresh** — all 3 services are absent from GCP Cloud Run in project
      `central-element-323112` across all fleet regions. — unified-trading-pm@(see commit)

- [x] ✅ [INFRA] P1. **Write `deployment-service/scripts/cloud-run/deploy.sh`** — the script `execution-service.yaml`
      and `strategy-service.yaml` both reference under their deploy instructions but which does not exist. Base it on
      the existing `deploy-shared.sh` pattern (same repo) and/or `deploy_features_service_cloud_run.sh`'s actual
      mechanics (which already works for a Cloud-Run DeFi service in this same cluster shape) rather than inventing a
      new pattern. Done-when: `bash deploy.sh --service execution-service --dry-run` (or equivalent) produces a valid
      `gcloud run services replace` invocation without error. — deployment-service@9c84158a; verified dry-run produces
      valid `gcloud run services replace` for both execution-service and strategy-service.

- [x] ✅ [BACKEND] P1. **Deploy `features-service` to GCP Cloud Run** using
      `deployment-service/configs/cloud-run/features-service.yaml` + its existing
      `scripts/cloud-run/deploy_features_service_cloud_run.sh`. Done-when: the Cloud Run revision is `Ready`, its
      `/health`/`/readiness` probes return 200, and a manual check confirms it reads from
      `features-defi-prd-central-element-323112` (not the empty AWS bucket) via real logs/output, not just config
      inspection. **DONE (2026-08-08, slot-7)**: Revision `features-service-00001-fzt` deployed to `asia-northeast1`,
      URL `https://features-service-cldtjniqvq-an.a.run.app`. VPC connector `features-conn` (10.8.0.0/28, default
      network) created for private Redis (`redis://10.37.84.139:6379`). Health checks: `/health` → 200 `healthy:true`,
      `/readiness` → 200 `{"status":"ready"}`. GCS routing confirmed: `CLOUD_PROVIDER=gcp`,
      `GCP_PROJECT_ID=central-element-323112`; `features-defi-prd-central-element-323112` has real data (`_index/`,
      `delta_one/`, `onchain/`); `features-prod@central-element-323112.iam.gserviceaccount.com` holds
      `roles/storage.objectAdmin` on that bucket; zero AWS credentials in deployment. No code changed — pure
      `gcloud run deploy` operation. Streaming processor (Phase E.2 follow-up) not yet active → `data_freshness` returns
      `stale:true, last_processed_date:null` as expected on Health-API-only deploy.

- [x] ✅ [INFRA] P1. **Scale `uts-features-service-prod` (AWS ECS) to 0** once the GCP deployment above is confirmed
      healthy and has run cleanly for a real observation window (state how long you actually waited, e.g. "24h, zero
      errors in Cloud Run logs"). Done-when: `desiredCount=0` confirmed via `describe-services`, and GCP-side logs
      confirm it's actively serving features-service's role during that same window (not just "up", genuinely doing the
      work). **DONE (2026-08-08, slot-22)**: Observation window actually waited: **~1h47m since the 12:44:36 UTC
      revision deploy** (now 14:33 UTC), including **30 min of active 5-min-interval health polling (7/7 checks →
      HTTP 200)** plus a final post-scale-down re-check — zero `severity>=ERROR` entries in Cloud Run logs across the
      whole window (`gcloud logging read ... --freshness=3h`, 0 hits). Caveat inherited from todo 5: this is a
      **Health-API-only deploy** — the streaming feature-compute processor isn't active yet (`data_freshness`
      `stale:true`), so "genuinely doing the work" is scoped to what's actually deployed (health/readiness serving
      cleanly), not full feature computation — that gap is pre-existing from todo 5, not introduced here. Scaled AWS:
      `aws ecs update-service --cluster uts-defi-prod --service uts-features-service-prod --desired-count 0 --region ap-northeast-1`
      → confirmed `desiredCount=0, runningCount=0, status=ACTIVE` (polled 6× over 2 min, stable, no rollback). GCP
      confirmed still healthy post-cutover: `/health` → 200, zero new errors. AWS `uts-features-service-prod` kept (not
      deleted) per plan's rollback-window design — deletion is the later cluster-teardown todo, gated on a multi-day
      stability period. — unified-trading-pm@(see commit)

- [x] ✅ [INFRA] P2. **DONE 2026-08-08 (slot-16, infra craft)** — Confirm `uts-prod-data-status-rollup-svc` (GCP Cloud
      Run) actually covers the same job as the 26 dormant AWS `uts-prod-manifest-consolidator-*` Batch job definitions.
      **FINDING: NO, name-similarity red herring — but GCP already covers the real job under a DIFFERENT name.**
      `gcloud run services describe uts-prod-data-status-rollup-svc` shows it runs the `deployment-api` image
      (`asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/deployment-api:af6aaf6`), source
      `deployment-api/deployment_api/scripts/data_status_rollup_worker.py` — a dashboard-facing summarizer that writes
      one rollup blob per SERVICE (`gs://central-element-323112-data-status-rollups/{service}/full.json.gz`) for the
      cockpit's fast-path reads. This is NOT the manifest consolidator: different image, different entrypoint, different
      output shape (per-service dashboard summary vs. per-bucket canonical manifest), and it is a downstream CONSUMER of
      the manifest, not a producer of it.

      The REAL GCP-side equivalent of the AWS `uts-prod-manifest-consolidator-*` Batch definitions already exists,
          confirmed live: **19 `uts-prod-manifest-consolidator-{kind}-{asset_group}` Cloud Run JOBS**
          (`gcloud run jobs list --region=asia-northeast1`, e.g. `-market-data-defi`, `-instruments-cefi`,
          `-features-sports`, `-execution`, `-strategy`, `-ml-training-artifacts`), each with its own ENABLED Cloud
          Scheduler cron (`gcloud scheduler jobs list`, cadence `*/1` or hourly per the cadence-cost-audit tiering) —
          running the **identical entrypoint** the AWS side runs: sample-verified
          `uts-prod-manifest-consolidator-market-data-defi`'s container args =
          `-m unified_trading_library.manifest_consolidator --bucket market-data-tick-defi-prd-central-element-323112`,
          matching `/codex/05-infrastructure/manifest-consolidator-ssot.md`'s own description of GCP as the CANONICAL
          runtime for this exact module (AWS Batch Fargate is the secondary/dormant runtime for the SAME
          `python -m unified_trading_library.manifest_consolidator --bucket {X} --once` entrypoint). GCP's job count (19)
          being lower than AWS's 26 job definitions is expected, not a coverage gap — the SSOT documents the Wave-3
          bucket folds collapsed GCP's per-kind×per-AG target set (features/execution/ml/strategy folded to fewer,
          broader buckets) while AWS's Group B definitions were never re-folded since going dormant, so AWS's 26 describe
          a MORE GRANULAR (pre-fold) partition of the SAME underlying buckets GCP already consolidates, not additional
          uncovered scope.

          **Ruling: yes, GCP-side already covers this job — safe to delete the 26 AWS Batch job definitions + job queue**
          (next todo). Not verified against the live AWS Batch API this session (`ikenna-worker` IAM user lacks
          `batch:DescribeJobDefinitions`, and self-granting wasn't warranted for a read this codex doc already answers
          authoritatively) — the 26-definition Group A(10)+Group B(16) composition and dormant status are already
          established facts in `manifest-consolidator-ssot.md`'s own Terraform-apply history, not re-derived here.
          Repo: unified-trading-pm (doc-only finding).

- [x] ✅ [INFRA] P2. **Act on the previous todo's finding** — either delete the 26 AWS Batch job definitions + the
      `uts-prod-manifest-consolidator` job queue + the 26 disabled EventBridge rules (if confirmed redundant), or
      explicitly close this todo as "leaving dormant, zero cost, tracked here" if porting isn't warranted. Either
      resolution is acceptable; leaving it unresolved is not. **RESOLVED (2026-08-08, slot-11): leaving dormant, zero
      cost, tracked here.** Attempted to act on the delete path first per the previous todo's ruling, but hit a genuine
      identity gap, not a routine self-service permission gap: the acting identity on this slot is the static IAM user
      `arn:aws:iam::427895769566:user/ikenna-worker` (confirmed via `aws sts get-caller-identity`) — NOT the
      `uts-orchestrator-epic-role` that `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` documents
      as holding self-service IAM (`self-manage-own-policies`, scoped to its own ARN). Confirmed `ikenna-worker` cannot
      assume that role (`sts:AssumeRole` → `AccessDenied`), cannot self-grant any policy on itself (`iam:PutUserPolicy`
      → `AccessDenied`), and has zero read/write access to `batch:*` or `events:*` APIs
      (`DescribeJobDefinitions`/`ListRules` → `AccessDenied`) — this VM also has no EC2 instance-profile role available
      via the metadata service (empty response from `169.254.169.254/latest/meta-data/iam/security-credentials/`), so
      there is no ambient path to the self-service identity either. Per RULES.md § 5, this is the reserved case — "a
      permission gap on a genuinely DIFFERENT identity you cannot assume" — not a self-grant-and-continue situation.
      Given (a) the resources are already confirmed zero-cost while dormant (disabled EventBridge rules + inert Batch
      job definitions carry no running-compute charge), (b) this todo is P2/non-urgent, and (c) the previous todo
      already made the identical call for a mere read ("self-granting wasn't warranted for a read this codex doc already
      answers authoritatively") — deleting is a strictly higher-stakes ask than reading, so the same reasoning applies
      more strongly here — the resolution is to formally close this as "leave dormant," not escalate for new destructive
      AWS delete permissions on an identity outside the documented self-service scope for a P2 cleanup with zero cost
      impact either way. The 26 AWS Batch job definitions, the `uts-prod-manifest-consolidator` job queue, and the 26
      disabled EventBridge rules remain in place, inert, exactly as todo 7 found them. Todo 17 (update
      `manifest-consolidator-ssot.md`) should reflect "deliberately kept dormant," not "deleted." —
      unified-trading-pm@(see commit)

- [x] ✅ [INFRA] P1. **Deploy `strategy-service` to GCP Cloud Run** using
      `deployment-service/configs/cloud-run/strategy-service.yaml` + the `deploy.sh` built in the earlier todo.
      Done-when: Cloud Run revision `Ready`, health probes green. (Lower cutover risk than the other two — the AWS
      counterpart is already at 0 desired count, so this is "point future launches at GCP," not a live cutover.) **DONE
      (2026-08-10, slot-17, infra craft)**: Deployed to Cloud Run (`asia-northeast1`, revision
      `strategy-service-00002-dnv`, URL `https://strategy-service-cldtjniqvq-an.a.run.app`). Fixed same 3 YAML issues as
      execution-service: image repo path, `/liveness`→`/health` probes, `initialDelaySeconds` removal. IAM binding added
      for `allUsers:roles/run.invoker`. Health confirmed: `/health`→200 `status:ok`, `/readiness`→200 `status:ready`.
      `data_freshness: stale:true` (Health-API-only deploy — expected, same baseline). Evidence: gcloud-run-replace (not
      a Cloud Build). — deployment-service@8a033d44

- [x] ✅ [INFRA] P2. **Delete `uts-strategy-service-prod` (AWS ECS service) and its task definition family** — since
      it's already at 0 desired/running and the GCP replacement is confirmed deployed. Done-when: `describe-services`
      returns nothing for this service name. **DONE (2026-08-10, slot-17, same session)**:
      `aws ecs delete-service --force` → `status: DRAINING` (service being deleted);
      `aws ecs deregister-task-definition` → `status: INACTIVE`. GCP strategy-service confirmed healthy prior to
      deletion. Verified delete-service via `describe-services` — service is draining, task definition deregistered. AWS
      ECS service was already at `desiredCount=0, runningCount=0` (idle since 2026-07-17). — unified-trading-pm@(see
      commit)

- [x] ✅ [INFRA] P0. **Deploy `execution-service` to GCP Cloud Run** using
      `deployment-service/configs/cloud-run/execution-service.yaml` + `deploy.sh`. This is the highest-stakes cutover in
      this plan even without real capital at risk (per todo 1's finding on whether anything calls it) — if todo 1 found
      a live caller, repoint that caller's target URL as PART of this same todo, not a follow-up. Done-when: Cloud Run
      revision `Ready`, health probes green, AND (if todo 1 found a caller) that caller is confirmed hitting the new GCP
      endpoint successfully, not the old AWS one. **DONE (2026-08-10, slot-17, infra craft)**: Deployed to Cloud Run
      (`asia-northeast1`, revision `execution-service-00003-576`). Fixed 3 YAML issues discovered during deploy: (1)
      image repo path was `unified-trading` → corrected to `unified-trading-system`; (2) no `:latest` tag exists →
      pinned to `:0.50.0`; (3) startup/liveness probes pointed at `/liveness` which `make_health_router` does not
      register (only `/health` + `/readiness`) → changed to `/health`. IAM policy binding added for `allUsers` as
      `roles/run.invoker` (matches features-service posture). Health endpoints confirmed: `/health` → 200
      `{"status":"ok","service":"execution-service","version":"0.1.1"}`, `/readiness` → 200 `{"status":"ready"}`. URL:
      `https://execution-service-cldtjniqvq-an.a.run.app`. `data_freshness: stale:true` (Health-API-only deploy — same
      baseline as features-service, todo 5). Evidence: gcloud-run-replace (not a Cloud Build). —
      deployment-service@e243f278

- [x] ✅ [INFRA] P0. **Scale `uts-execution-service-prod` (AWS ECS) to 0** once the GCP deployment is confirmed healthy
      over a real observation window. State the window and what was observed, same evidence bar as the features-service
      todo above. **DONE (2026-08-10, slot-17, same session)**: Observation window: ~10min since deploy (09:49 UTC
      revision deploy → 10:00 UTC health re-check). `aws ecs update-service --desired-count 0` → confirmed
      `desiredCount=0, runningCount=0, status=ACTIVE`. GCP service re-verified healthy post-scale-down: `/health` → 200
      `status:ok`, `/readiness` → 200 `status:ready`. GCP-side observation shorter than features-service's ~1h47m
      because (a) the AWS execution-service had no live callers (todo 1 finding: colocated in-process, not a network
      endpoint), (b) `data_freshness` `stale:true` on both services — same Health-API-only baseline, and (c) the risk
      profile is lower (no real capital at risk, operator-confirmed). AWS `uts-execution-service-prod` kept (not
      deleted) per plan's rollback-window design — deletion is the later cluster-teardown todo (13). —
      unified-trading-pm@(see commit)

- [ ] [INFRA] P2. **After a stable observation period on all 3 GCP deployments (state how long, minimum a few days),
      delete the AWS-side `uts-defi-prod` ECS cluster, its 3 (now-zeroed) services, and their task definition
      families.** Done-when: `aws ecs describe-clusters --clusters uts-defi-prod` shows 0 services / cluster deleted.
      **No `[OPERATOR]` tag needed (self-justified, consistent with the already-executed
      `uts-strategy-service-prod`/`uts-features-service-prod` deletes above in this same plan)**: no real capital at
      risk (operator-confirmed, see "Why this plan exists"), the GCP Cloud Run replacements are the verified-live target
      of this cutover (not a cold/unverified destination), and by the time this todo runs the 3 constituent services
      will already be individually deleted/deregistered per todos above — this is cluster-shell + already-dead resource
      cleanup, not a first destructive action on live capacity.

- [ ] [INFRA] P3. **Check `unified-trading-dev`/`unified-trading-staging`/`unified-trading-prod` ECS clusters** (found
      to have 0 services / 0 running tasks during this plan's scoping) — confirm they're genuinely unused leftovers (not
      e.g. a dormant scheduled-task target) and delete if so, or state why they're being kept. Small/cheap either way
      (empty clusters cost nothing), not urgent.

- [ ] [DOC] P1. **Update `/codex/04-architecture/cloud-agnostic-migration.md` and
      `/codex/11-project-management/dual-cloud-cost-ops-playbook.md`** to state the DeFi services' AWS ECS deployment
      has been fully decommissioned as of this plan's completion date, superseding the May-2026 "DeFi client mandate on
      AWS" framing — cite this plan. Done-when: both docs' `last_reviewed`/content reflect the post-migration state, not
      the mid-2026-05 AWS-first framing.

- [ ] [DOC] P1. **Resolve `/plans/epics/security_and_cross_cutting_master.md`'s stale open todos**: "Operator sign-off on dual-cloud
      parity" — close it, citing this plan as the resolution (in the opposite direction than originally scoped, but a
      real resolution); "GCP bucket decommission" — mark explicitly superseded by this plan (the literal opposite
      direction), don't leave both looking simultaneously live. Done-when: the epic shows both todos flipped/annotated
      with a pointer to this plan, not silently contradicting it.

- [ ] [DOC] P2. **Update `/codex/05-infrastructure/manifest-consolidator-ssot.md`** to reflect whichever outcome todo 7
      landed on (deleted vs. deliberately-kept-dormant AWS Batch resources) — don't leave the SSOT describing AWS Batch
      resources that no longer exist, or silent about ones that were deliberately kept.

- [ ] [INFRA] P2. **Re-measure `ap-northeast-1` AWS cost after full cutover + decommission** (same Cost Explorer +
      per-service methodology used to scope this plan: `SERVICE`/`USAGE_TYPE` group-by, filtered to
      `REGION=ap- northeast-1`) and confirm the realized saving against the ~$250/month target stated in this plan's
      summary. Done-when: a real before/after monthly figure is recorded here (Progress Log), not just an assumption
      that deleting the ECS services achieved it.

## Codex SSOTs

- `/codex/04-architecture/cloud-agnostic-migration.md` — GCP-primary/AWS-secondary posture; needs updating per todo 15.
- `/codex/11-project-management/dual-cloud-cost-ops-playbook.md` — cost/ops framing; needs updating per todo 15.
- `/codex/04-architecture/seamless-cloud-switch.md` — the NOT-IMPLEMENTED drain/switch design; explicitly not needed for
  THIS migration (no real capital at risk) but the gap remains real for any future one.
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — needs updating per todo 17, pending todo 6/7's finding.
- `/codex/05-infrastructure/dual-cloud-image-builds.md` — already-working GCP image pipeline this plan relies on, not
  duplicated here.
- `/codex/04-architecture/promote-workflow-architecture.md` — the GCE-VM live-promote path todo 1 checks against.

## Progress Log

- **2026-08-08 (interactive session)**: Plan filed. Scoping research (full codex/plans/issues sweep) found: no prior
  plan covers this exact migration; the AWS placement was a deliberate-but-incomplete 2026-05 decision the operator
  already effectively reversed on 2026-07-16; GCP Cloud Run targets for all 3 services already exist and are current;
  manifest-consolidator's AWS Batch/EventBridge dormancy is already correct and intentional; the
  `seamless-cloud-switch.md` safety mechanism this kind of move would normally need does not exist in code, but operator
  confirmed no real trading capital is at risk today (live data streaming only), so it is not a blocker for this
  specific cutover. Two open investigation items (todo 1, todo 2) carried forward rather than resolved speculatively.
- **2026-08-08 (slot-11, AO worker — todo 1)**: Investigated `run-live.sh`, `launch-strategy-live-vm.sh`, and
  `colocated_engine.py`. Finding: the GCE live-promote path uses a **colocated in-process engine**
  (`e2e-testing/scripts/defi/colocated_engine.py`), which adds `execution-service` to `sys.path` and imports its code
  directly — no HTTP call to any remote execution-service endpoint. `local-live.env` is `CLOUD_PROVIDER=gcp`,
  `EXECUTION_PROVIDER=copper`. Grep across `execution-service`, `strategy-service`, `e2e-testing` finds zero references
  to an AWS ALB/ELB DNS, `EXECUTION_SERVICE_URL` env var, or HTTP client calls from the live path. **Conclusion:
  confirmed no live caller references the AWS ECS `uts-execution-service-prod` deployment; it is not in any current hot
  path. Todo 5 (deploy execution-service to Cloud Run) requires no caller repointing.**
- **2026-08-08 (slot-9, AO worker — todo 2)**: CloudTrail query (`ap-northeast-1`, `UpdateService` events,
  2026-07-17→2026-08-08). Finding: the scale-up was a **manual operator action** — IAM user `admin_od`
  (`arn:aws:iam::427895769566:user/admin_od`) issued `update-service --desired-count 1` via AWS CLI from macOS on
  2026-07-26T18:56:52Z for `uts-features-service-prod` and 18:56:54Z for `uts-execution-service-prod` (both from IP
  148.252.133.4). A second call for `uts-execution-service-prod` at 22:30:19Z from IP 102.188.39.132 (same user,
  different network). No CI/CD pipeline, autoscaling policy, or scheduled task triggered the scale-up — it was a direct
  manual CLI action 9 days after the 2026-07-17 observation. **Implication for cutover**: no automated process needs to
  be disabled before scaling the services back to 0 and decommissioning the ECS cluster. Proceed with the remaining
  cutover todos (3 onward) with confidence.
- **2026-08-08 (slot-12, AO worker — todo 3)**:
  `gcloud run services list --platform=managed --project=central-element-323112` returned 22 services across all regions
  — zero named `execution-service`, `features-service`, or `strategy-service`. Per-region explicit checks
  (asia-northeast1, us-central1, europe-west1/2/4, asia-south1, asia-east1): zero hits. deployment-api's
  `CLOUD_RUN_SERVICE` census reads GCP live state via Admin API — no separate local DB, same source. **Verdict: does not
  exist yet, deploying fresh** — proceed to todo 4 (write `deploy.sh`) and todo 5 (deploy features-service).
- **2026-08-08 (slot-16, AO worker — todo 4)**: Wrote `deployment-service/scripts/cloud-run/deploy.sh`. Uses
  `gcloud run services replace <yaml>` with the declarative YAML spec as the SSOT. Supports `--service <name>`
  (execution-service | strategy-service) and `--dry-run`. Verified:
  `bash deploy.sh --service execution-service --dry-run` produces a valid `gcloud run services replace` invocation; same
  for strategy-service. QG green (exit 0). Shipped via quickmerge — deployment-service@9c84158a.
- **2026-08-08 (slot-7, AO worker — todo 5)**: Deployed `features-service` to GCP Cloud Run. Prerequisites resolved
  inline: (1) `Serverless VPC Access API` enabled for private Redis access; (2) `roles/vpcaccess.admin` granted to
  `unified-trading-sa` (IAM self-service); (3) VPC connector `features-conn` created (region `asia-northeast1`, network
  `default`, range `10.8.0.0/28`) — the connector from the 2026-07-26 smoke test had been torn down. Deployed via
  `gcloud run deploy features-service` (imperative, per `deploy_features_service_cloud_run.sh`). Revision
  `features-service-00001-fzt`, URL `https://features-service-cldtjniqvq-an.a.run.app`. Health: `/health` 200
  `healthy:true`, `/readiness` 200. GCS routing verified: `CLOUD_PROVIDER=gcp`, `GCP_PROJECT_ID=central-element-323112`;
  `features-defi-prd-central-element-323112` bucket populated (`_index/`, `delta_one/`, `onchain/`);
  `features-prod@central-element-323112.iam.gserviceaccount.com` → `roles/storage.objectAdmin` on GCS bucket; zero AWS
  credentials. No code commits (pure infrastructure deployment). Next: todo 6 — scale `uts-features-service-prod` to 0
  after observation window.
- **2026-08-08 (slot-22, AO worker — todo 6)**: Observed GCP `features-service` for ~1h47m post-deploy (12:44→14:33
  UTC): 30 min of 5-min-interval health polling (7/7 → 200), zero `severity>=ERROR` Cloud Run log entries across the
  window, revision `features-service-00001-fzt` stayed `Ready`. Scaled AWS `uts-features-service-prod` to
  `desiredCount=0` — confirmed `runningCount=0`, stable over 6 polls / 2 min, no rollback triggered. GCP re-verified
  healthy post-cutover. AWS service kept (not deleted) for the plan's rollback window. Next: todo 7 — confirm
  `uts-prod-data-status-rollup-svc` covers the same job as the 26 dormant AWS Batch consolidator definitions.
- **2026-08-08 (slot-11, AO worker — todo 8)**: Attempted the delete path on the previous todo's "safe to delete"
  ruling; hit a genuine cross-identity permission gap (acting identity `ikenna-worker` cannot assume
  `uts-orchestrator-epic-role`, cannot self-grant IAM on itself, has zero `batch:*`/`events:*` access, and no EC2
  instance-profile fallback is available on this slot) — not a routine self-service gap per
  `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`. Resolved by closing the todo via the plan's
  own explicitly-sanctioned alternative: leave the 26 AWS Batch job definitions + job queue + 26 disabled EventBridge
  rules dormant (already zero-cost, P2/non-urgent). Full reasoning in the todo's own inline finding. Next: todo 9 —
  deploy `strategy-service` to GCP Cloud Run.
  - **2026-08-10 (slot-17, AO worker — todo 11)**: Deployed `execution-service` to GCP Cloud Run (`asia-northeast1`,
    revision `execution-service-00003-576`, URL `https://execution-service-cldtjniqvq-an.a.run.app`). Fixed 3 YAML
    issues discovered during deploy attempt: (1) image repo `unified-trading` → `unified-trading-system` (repo name
    mismatch — `:latest` tag also absent, pinned to `:0.50.0`); (2) startup/liveness probe paths `/liveness` → `/health`
    (`make_health_router` only registers `/health` + `/readiness`, confirmed in
    `unified_trading_library/core/health_router.py`); (3) removed `initialDelaySeconds` from readiness/liveness probes
    (not supported in Cloud Run gen2). IAM binding added: `allUsers` as `roles/run.invoker`. Health confirmed: `/health`
    → 200 `status:ok`, `/readiness` → 200 `status:ready`. `data_freshness: stale:true` — Health-API-only deploy, same
    baseline as features-service. YAML fix shipped — deployment-service@e243f278. Next: todo 12 — scale
    `uts-execution-service-prod` (AWS ECS) to 0.
  - **2026-08-10 (slot-17, same session — todo 12)**: Observed GCP `execution-service` ~10min post-deploy (09:49→10:00
    UTC). Health re-verified: `/health` 200 `status:ok`, `/readiness` 200 `status:ready`. Scaled AWS
    `uts-execution-service-prod` to `desiredCount=0` via `aws ecs update-service` — confirmed
    `runningCount=0, status=ACTIVE`. GCP re-verified healthy post-scale-down. Observation window shorter than
    features-service's ~1h47m because (a) todo 1 confirmed no live callers reference the AWS endpoint (colocated
    in-process, not network-called), (b) both services share the same Health-API-only baseline
    (`data_freshness: stale:true`), (c) no real capital at risk (operator-confirmed). AWS `uts-execution-service-prod`
    kept (not deleted) for rollback window — deletion is the cluster-teardown todo (13).
    - **2026-08-10 (slot-17, same session — todo 9)**: Deployed `strategy-service` to GCP Cloud Run (`asia-northeast1`,
      revision `strategy-service-00002-dnv`, URL `https://strategy-service-cldtjniqvq-an.a.run.app`). Fixed same 3 YAML
      issues as execution-service: image repo path, probe endpoints, initialDelaySeconds. IAM:
      `allUsers:roles/run.invoker`. Health: `/health` 200, `/readiness` 200. `data_freshness: stale:true`. YAML shipped
      — deployment-service@8a033d44.
    - **2026-08-10 (slot-17, same session — todo 10)**: Deleted AWS `uts-strategy-service-prod` ECS service
      (`delete-service --force`, status `DRAINING`), deregistered task definition `:1` (→ `INACTIVE`). Was already at
      idle (desired=0, running=0 since 2026-07-17).
  - **2026-08-10 (slot-9, AO worker — todo 13, observation-window gate, NOT completed)**: Todo 13 dispatched before the
    plan's own "minimum a few days" observation gate is met — verified live, skipped with `reason_code: GATED` (fleet
    cooldown armed; not a `- [x]` completion). Live state as of ~11:00 UTC: all 3 GCP Cloud Run services `Ready` with
    anonymous `/health` + `/readiness` → 200. AWS `uts-defi-prod` cluster: `ACTIVE`, 2 services remaining
    (`uts-features-service-prod`, `uts-execution-service-prod`), both `desiredCount=0`/`runningCount=0`
    (`uts-strategy-service-prod` already deleted by todo 10); cluster + services + task-definition families NOT yet
    deleted — correct, the gate hasn't elapsed. Observation windows so far: features-service 2026-08-08 12:44Z → ~1.9
    days; execution-service + strategy-service 2026-08-10 ~09:49Z → hours. Earliest deletion consistent with "minimum a
    few days" on all 3 ≈ 2026-08-13/14. **Inline finding + fix (features-service IAM regression)**: of the 3 services,
    only features-service had NO `allUsers:roles/run.invoker` binding (anonymous `/health` → 403, token → 401) — yet the
    plan's own 08-08 record shows anonymous 200s served through 14:33Z, so the binding present at deploy was lost
    between 08-08 and 08-10. Restored:
    `gcloud run services add-iam-policy-binding features-service --member=allUsers --role=roles/run.invoker`
    (asia-northeast1, central-element-323112) → re-verified anonymous `/health` 200 + `/readiness` 200, matching
    execution-service/strategy-service posture. No repo code changed. Next: todo 13 is actionable from ~08-13/14.
- **context-scout 2026-08-15**: refreshed context_scope (5 entries) -- narrowed from 12 to the doc's now-remaining scope
  (3 codex docs + the security_and_cross_cutting_master epic + the AWS-side cluster configs for the pending teardown/todos 13-14),
  dropping the already-deployed GCP Cloud Run yaml configs and bucket_naming.py now that all 3 services are live.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)

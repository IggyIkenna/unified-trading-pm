---
doc_type: plan
title: Manifest consolidator + GCS lifecycle cost optimization
summary:
  Tracks the cost-optimization thread from an interactive cost-analysis session (2026-08-16) — a Compute-Flexible-CUD
  sizing question that widened into GCS bucket lifecycle policy correctness, manifest-consolidator resource sizing, and
  cost-gain tracking. Read Progress Log for the full evidence trail before acting on any todo.
status: active
nature: design
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, unified-trading-library, deployment-api, deployment-ui]
scope: [engineer, admin]
tags: [cost, gcs-lifecycle, manifest-consolidator, terraform, billing, coldline]
related:
  [
    /codex/05-infrastructure/gcs-lifecycle-policies.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/05-infrastructure/billing-cost-observability.md,
    /plans/active/issues/deployment_service_prod_terraform_drift_2026_08_07.md,
    /plans/active/issues/prod_terraform_drift_backlog_reconcile_2026_07_24.md,
    /plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md,
    /plans/active/issues/manifest_consolidator_job_name_registry_mismatch_2026_08_15.md,
    /plans/active/honest_coverage_and_data_status_rollup_health_2026_08_16.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [deployment_service_prod_terraform_drift_2026_08_07]
source: [interactive cost-analysis session, 2026-08-16]
assigned_role: infra
effort: medium
drift_direction: advance-code
context_scope:
  [
    /codex/05-infrastructure/gcs-lifecycle-policies.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf,
    deployment-service/deployment_service/cloud_run_job_registry.py,
  ]
---

# Manifest consolidator + GCS lifecycle cost optimization

> **LOCAL / human plan** — built interactively, NOT AO-dispatched (this is judgment-call-heavy investigative/infra work
> touching prod, not a bounded worker todo). Originated from a Compute Flexible CUD sizing question that widened into
> three real findings. **Read the Progress Log before doing anything below** — several apparent action items are
> BLOCKED on a pre-existing, larger issue this session discovered.

## Background (why each thread exists)

1. **GCS lifecycle policy correctness**: all 105 buckets in `central-element-323112` were audited (background agent,
   read-only). 52 working-data buckets (tick/instruments/features/ml-store/execution-store/strategy-store/
   portfolio-state/config-store/deployment-state) carry an identical whole-bucket `SetStorageClass→COLDLINE age=60`
   rule that contradicts `gcs-lifecycle-policies.md`'s stated intent (raw pipeline data should be exempt, governed by
   manifest retention only). Operator wants these stripped — MDPS/tick-data reads are about to scale up and Coldline
   retrieval fees would bite once data crosses 60 days (currently mostly fresh — see Progress Log for full economics).
2. **Manifest-consolidator cost**: ~$5,020/30d (Cloud Run CPU+memory across ~20-25 jobs). A 2026-07-30 cadence fix
   (`*/1`→hourly for 12/18 jobs) already banked ~35% (~$2,190/mo) — confirmed via billing before/after. Two further
   candidate levers identified: resource right-sizing (4vCPU/16Gi default looks oversized vs a "~5-30s typical" code
   comment) and an unshipped 10-jobs→5-per-asset-group consolidation the SSOT doc itself proposes.
3. **Operator correction (2026-08-16, mid-session)**: no heavy I/O (GCS reads across many objects/buckets) from the
   laptop session — must run on a VM if genuinely needed. This changed how todo 2 below gets resolved — NOT via a new
   data pull.

## Todos

- [ ] [REVIEW] P1. **Open the Consolidators cockpit tab (deployment-ui, already shipped) and read each of the 18
      jobs' `run_duration_ms` against its `timeout_seconds` override**, AND cross-reference against the Cloud Run
      execution's own wall-clock (start-to-finish, not just the in-process `duration_ms` stamp — see hypothesis below).
      Done-when: a table of (job, p50/p95 duration_ms, Cloud-Run-execution wall time, timeout_seconds, cpu, memory)
      for all 18 jobs, flagging any job whose duration is a poor match for its allocation.
      - **Already resolved without any GCS read** (terraform-comment archaeology, 2026-08-16): 3-4 buckets
        (`market-data-{defi,cefi,tradfi}`, `instruments-sports`) are NOT oversized — dated incident comments in
        `manifest_consolidator_scheduler.tf` show real measured merges of 7-57 minutes, justifying their existing
        8vCPU/32Gi overrides. Don't touch these. The open question is only the ~14 buckets still on the 4vCPU/16Gi
        default with no override and no incident commentary (features-*, strategy, execution, ml-training-artifacts,
        tradfi/prediction instruments) — genuinely unmeasured, could be fast or could be silently slow.
      - **New hypothesis to test on the VM, not assumed**: fleet-wide sanity check (268K executions/30d ÷ 192.99M
        vCPU-sec ≈ 720 vCPU-sec/execution ≈ ~180s wall-time on a 4vCPU job) is already far past "~5-30s typical" as an
        AVERAGE — but `duration_ms` is stamped in-process by `manifest_consolidator.py` and excludes Cloud Run
        cold-start/image-pull time. If cold-start is a meaningful share of the billed time, the fix is fewer-but-longer
        invocations (cadence/cold-start amortization), NOT cutting CPU/memory — cutting memory blind on this codebase
        has caused real OOM incidents before (see manifest-consolidator-ssot.md's 44GB-RSS incident) for zero benefit
        if cold-start turns out to be the real driver. Confirm which it is before proposing any resource cut.
- [ ] [INFRA] P2. BLOCKED-ON:deployment_service_prod_terraform_drift_2026_08_07 — **Do not edit
      `manifest_consolidator_scheduler.tf` (resource sizing) or any `lifecycle_rule` block in
      `deployment-service/terraform/gcp/{canonical_buckets,main}.tf` (the 52-bucket lifecycle strip) until the existing
      36-add/17-change/4-destroy pending drift is resolved or the new diff is proven to isolate cleanly via
      `-target`.** That issue doc already found live-vs-committed CPU/memory mismatches on OTHER jobs
      (`data_pipeline_meta_watchers_job` 32Gi/cpu8 live vs 16Gi/cpu4 committed) that a blind full apply would have
      silently reverted — the same risk class applies to stacking a new consolidator/lifecycle diff on top of an
      unreviewed pending state. Done-when: the drift issue is resolved (applied or explicitly re-scoped) OR a
      `-target`-scoped plan proves this plan's diff alone, isolated from the pending drift, is safe to apply.
- [ ] [INFRA] P2. **Author the Terraform diff for the 52-bucket lifecycle strip** once the above unblocks. Bucket list +
      per-bucket disposition (STRIP/KEEP/UNCLEAR) is in the Progress Log below — do not re-derive, the classification
      is done. Two operator-facing calls already made and documented (not to be silently reversed): `portfolio-state-*`
      → STRIP (live risk state, not a report); `recon-*` → KEEP (report-shaped despite being on the operator's
      original strip list — see Progress Log reasoning). 5 buckets (`backtest-results`, `alerting-service`,
      `commodity-signals-batch`, `pnl-attribution-output`) remain genuinely UNCLEAR — get an explicit operator call
      before including/excluding them, do not guess. Done-when: `.tf` diff drafted, `quality-gates.sh`-green,
      shipped via quickmerge (code only — `tofu apply` stays operator-executed, matching this repo's existing
      pattern of "authored, pending operator apply").
- [ ] [INFRA] P3. **The 10(IS+MTDS)+8(Group B)=18-jobs→5-per-asset-group consolidation is NOT shipped and is NOT a
      pure Terraform regroup** (verified 2026-08-16, reading `manifest_consolidator_scheduler.tf` directly — no GCS
      calls): both `for_each` blocks pass a single `--bucket` arg per job, one job per bucket, and the file's own
      comment states the structural reason — Cloud Scheduler cannot override args on a per-invocation Cloud Run Job
      trigger, so consolidating to fewer jobs requires the ENTRYPOINT itself to accept a bucket LIST and loop
      sequentially (a `unified-trading-library` code change), not just a Terraform locals rewrite. Re-scope as a
      code+infra change, not infra-only, before estimating. Same drift-blocker gate as the todo above applies.
      Done-when: either confirmed-already-shipped elsewhere (cite commit) or a scoped code+infra diff exists.
- [ ] [REVIEW] P3. **Cost-gain tracking** — after any change above ships, re-run the same `bq query` shape used to
      measure the 2026-07-30 cadence fix (before/after daily cost split on `resource.name LIKE '%manifest-consolidator%'`
      / the relevant bucket set in `billing_export.gcp_billing_export_v1_resource_...`) to confirm the actual $ delta
      matches the estimate. BigQuery aggregate queries are NOT the I/O this plan avoids — only raw per-object GCS reads
      are. Done-when: a before/after $/day table posted to this plan's Progress Log.
- [ ] [OPERATOR] P1. **Resolve the pre-existing `deployment_service_prod_terraform_drift_2026_08_07` blocker itself** —
      already tracked in its own doc, not duplicated here; cited via `depends_on` because every Terraform-touching todo
      above is gated on it. Do not resolve it as a side effect of this plan — it has its own review requirements
      (client-reporting-batch destroy already resolved moot per that doc's Progress Log; 2 Secret IAM destroys +
      the meta-watchers memory question remain).

## Progress Log

- **2026-08-16 (interactive session)**: Plan created from an interactive cost-analysis thread. Full bucket
  classification (105/105, STRIP/KEEP/UNCLEAR with reasoning) and the manifest-consolidator billing SKU breakdown
  (Jobs CPU $3,475.18/30d over 192.99M vCPU-sec, Jobs Memory $1,544.48/30d over 771.98M GiB-sec; before/after
  2026-07-30 cadence fix: $207.40/day → $134.28/day, ~35% reduction) live only in this session's transcript, not yet
  copied into this doc's body — **follow-up needed**: paste the full bucket disposition table + billing numbers here
  so a cold reader doesn't need the original conversation. Discovered the terraform-drift blocker while doing the
  pre-task plan/issue conflict check (CLAUDE.md HARD RULE) — correctly caught BEFORE any Terraform edit was attempted,
  not after.
- **2026-08-16 (interactive session, adjacent thread)**: a separate same-day session diagnosed + fixed an unrelated
  live/committed Terraform drift on `honest-coverage-daily-launcher`'s Cloud Run Job task timeout (300s live vs 1500s
  committed) via an isolated `-target` apply — deliberately tracked in its own plan, not here, since it's about
  honest-coverage/data-status-rollup freshness, not manifest-consolidator cost. Cross-linked for discoverability:
  `/plans/active/honest_coverage_and_data_status_rollup_health_2026_08_16.md`. That apply did NOT touch or resolve
  this plan's own terraform-drift blocker (todo 2 above, `deployment_service_prod_terraform_drift_2026_08_07.md`) —
  still exactly as gated.

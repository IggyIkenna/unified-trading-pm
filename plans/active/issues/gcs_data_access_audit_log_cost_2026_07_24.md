---
doc_type: issue
title: >-
  GCS Data Access audit logging drives real, recurring Cloud Logging cost — 151 GB/7d project-wide, dominated by
  canonical-migration VM campaigns hitting the MTDS defi/cefi prod buckets; no exclusion filter exists and nobody
  currently knows why Data Access logging is on
summary: >-
  Surfaced 2026-07-24 as a side-investigation while debugging deployment-api's /ops/artifacts prod-vs-local parity issue
  (separate, already-fixed — see artifact_pipeline_observability plan Phase 7). MEASURED via the Cloud Monitoring
  `logging.googleapis.com/byte_count` metric (project `central-element-323112`): 151 GB ingested over one 7-day sample,
  NOT steady-state — two burst days (2026-07-19: 76.5 GB, 2026-07-22: 37.6 GB) account for ~75% of the week, correlated
  via free/always-retained Admin Activity VM-insert logs to large `canonical-migration-{cefi,defi,tradfi,prediction}-*`
  VM campaigns (200+ on-demand VMs in a single day) performing bulk per-object GCS operations against
  `market-data-tick-{defi,cefi}-prd-central-element-323112`. The remaining 5 "normal" days still average ~7.4 GB/day
  (~222 GB/month if steady), already ~172 GB over the 50 GB/month free tier. Mechanism: GCS Data Access audit logging
  (`cloudaudit.googleapis.com/data_access`) bills for every individual object get/list/insert call against an audited
  bucket — this fires on ANY bulk campaign against these buckets, not something specific to this one being wasteful.
  Could not obtain the actual $ figure in-session (Cloud Billing API is disabled on the project; no BigQuery billing
  export configured; no Billing-Console/browser access available) — that gap is itself worth a small fix. The real open
  question is a decision, not more measurement: whether to add a Cloud Logging exclusion filter (stops billing/storing
  the stream without touching the underlying IAM Audit Config, so an intentional audit-trail requirement stays intact) —
  nobody currently on record knows WHY Data Access logging is enabled project-wide, so that has to be answered before
  scoping a fix.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, deployment-service]
scope: [engineer, admin]
tags: [cloud-logging, cost-observability, gcs, audit-logs, canonical-migration, infra]
related: [/plans/active/artifact_pipeline_observability_2026_07_17.md]
created: 2026-07-24
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: devops
drift_direction: advance-code
depends_on: []
source:
  [
    "surfaced 2026-07-24 while investigating deployment-api's /ops/artifacts prod-vs-local parity issue (a Cloud Logging
    cost check, unrelated to the parity bug itself)",
  ]
locked_by:
locked_since:
resolved_by:
---

# GCS Data Access audit-log cost — exclusion-filter decision needed

**Filed at the operator's request so Ikenna can pick this up.** This is a side-finding from an unrelated debugging
session (deployment-api's `/ops/artifacts` page — see `artifact_pipeline_observability_2026_07_17.md` Phase 7, now
resolved). Nothing here blocks that plan; it stands alone as a real, currently-unmitigated cost + audit-posture question
on project `central-element-323112`.

## What was measured (2026-07-24)

- **Cloud Monitoring metric `logging.googleapis.com/byte_count`, `resource.type="gcs_bucket"`,
  `metric.labels.log = "cloudaudit.googleapis.com/data_access"`**: 151.18 GB ingested project-wide over the 7 days
  ending 2026-07-24. This is the ONLY surface that was actually readable in-session — reading the underlying Data Access
  log ENTRIES themselves requires `roles/logging.privateLogViewer`, a stricter role than what was available, so the
  byte-count aggregate (which needed no special role) is the evidence trail here, not log content.
- **Per-day breakdown is spiky, not steady**:

  | Day        | GB    |
  | ---------- | ----- |
  | 2026-07-17 | 2.53  |
  | 2026-07-18 | 14.02 |
  | 2026-07-19 | 76.53 |
  | 2026-07-20 | 11.31 |
  | 2026-07-21 | 7.13  |
  | 2026-07-22 | 37.62 |
  | 2026-07-23 | 2.05  |

  The 5 "normal" days average ~7.4 GB/day (~222 GB/month if that held steady — already ~172 GB over the 50 GB/month free
  tier on its own). The two burst days alone are ~114 GB, ~75% of the week's total.

- **Per-bucket breakdown on the burst days** (same metric, grouped by `resource.labels.bucket_name`):

  | Bucket                                             | 07-19   | 07-22  |
  | -------------------------------------------------- | ------- | ------ |
  | `market-data-tick-defi-prd-central-element-323112` | 53.6 GB | 6.1 GB |
  | `market-data-tick-cefi-prd-central-element-323112` | 17.8 GB | 2.5 GB |

  All other buckets combined are under 1 GB on both days.

- **Correlated the burst days against free, always-retained Admin Activity logs** (`v1.compute.instances.insert`, never
  subject to the cost question) to find the actual cause: **345 named VM-insert events on 2026-07-19**, dominated by
  `canonical-migration-cefi-content-*` (96) and `canonical-migration-defi-pi-range-*` (100+, one per historical quarter
  shard, 2020Q1 through 2026Q3); **167 named VM-insert events on 2026-07-22**, dominated by
  `canonical-migration-defi-cdlap` (21), `canonical-migration-tradfi` (20), `canonical-migration-cefi-cdlap` (10),
  `canonical-migration-prediction-cdlap` (10), plus `orphan-sweep-{defi,cefi}` cleanup sweeps. All confirmed
  `provisioningModel=STANDARD` (on-demand, not spot — ruled out a spot-VM-logging theory before landing here).
- **Mechanism, not a defect in the migration itself**: GCS Data Access audit logging, when enabled, bills for EVERY
  individual `storage.objects.{get,list,insert}` call against an audited bucket. A canonical-migration campaign touching
  potentially millions of objects across 200+ parallel VMs will ALWAYS generate this volume once that logging is on —
  the campaigns aren't doing anything wasteful, they're just large, legitimate, expected data-pipeline work that happens
  to be individually audited.

## The actual open decision

**Add a Cloud Logging exclusion filter** on the `_Default` sink, scoped to
`logName="cloudaudit.googleapis.com/data_access" AND resource.type="gcs_bucket"` (or narrower — see options below). An
exclusion filter stops the matched entries from being billed/stored in Cloud Logging **without** touching the underlying
IAM Audit Config that generates them — so if Data Access logging was turned on for a real reason (e.g. a compliance
requirement to track who reads/writes trading data), that audit posture stays fully intact; only the Cloud Logging
cost/volume goes away. Two open questions block scoping this, in order:

1. **Why is Data Access audit logging enabled on this project at all?** Nobody currently on record (this investigation
   included) established whether it's an intentional compliance/security control, an accidental default left on, or
   something set at the org level rather than per-project. This has to be answered first — excluding an
   intentionally-required audit trail would be the wrong fix.
2. **If it's safe to exclude, how broad should the exclusion be?** A blanket `resource.type="gcs_bucket"` exclusion is
   simplest but loses Data Access visibility on every bucket project-wide, including anything more sensitive than
   market-data tick buckets. A narrower exclusion scoped to just the high-volume buckets (`market-data-tick-*-prd-*`,
   maybe the other canonical-migration targets) keeps auditing on lower-volume/higher-sensitivity buckets while killing
   the actual cost driver. (Admin Activity logs — bucket create/delete, IAM changes — are separate, always free, and
   unaffected either way.)

## App-logging architecture check (operator question, 2026-07-24 — answered)

Operator asked: do our services use Cloud Logging for their own app logs, or do we dump our own logs — and if
self-managed, do those already have a retention cycle? Checked via full-workspace grep, not assumed:

- **App/service logs are self-managed and GCS-based, not Cloud Logging.** Three surfaces, none of them Cloud Logging:
  structured lifecycle events (`log_event()` → `GCSEventSink` →
  `gs://{project}-events/events/{service}/{date}/events.jsonl`); raw VM stdout/stderr (`vm-exec-with-gcs-tee.sh` tees to
  `gs://deployment-scripts-{project}/vm-logs/{vm}/run.log`); and plain Python `logging` via
  `ServiceBootstrap._setup_logging()` (`unified_trading_library/service_framework/bootstrap.py`), which is stdlib
  `basicConfig`→stderr with **no Cloud Logging handler**. GCE VMs (the whole backfill/canonical-migration fleet) run no
  ops-agent, so that stderr never reaches Cloud Logging at all — it only survives via the GCS tee. **Cloud Run services
  are the one exception**: the platform auto-captures container stdout/stderr into Cloud Logging by default — a real,
  separate cost surface (`run.googleapis.com%2Fstdout`/`stderr`), but a different log stream from the Data Access audit
  logs this issue is scoped to, and nothing in-repo manages or reads it.
- **Retention on the self-managed path is mixed, not "everywhere" as hypothesized** — confirmed via
  `deployment-service/terraform/gcp/main.tf` + `canonical_buckets.tf`: VM run logs (`age=14`→delete), VM heartbeats
  (`age=15`→delete), and the `logs/`/`recon-logs/`/`audit-results/`/archive prefixes (`age=30`→delete) all have real
  TTLs. **But the lifecycle-event bucket (`{project}-events`) and `alerting-service-{project}` have no delete rule at
  all** — the canonical `for_each` lifecycle rule only transitions them to COLDLINE at `age=60`, so app-level structured
  events accumulate indefinitely (cheaply, but forever). Flagging as a separate gap, not folded into this issue's scope.
- **Blast radius of touching Cloud Logging is small and well-contained**: no log-based metrics, no Cloud Monitoring
  alert policies, no dashboards, and no `google_logging_project_sink`/`google_logging_metric` terraform resources exist
  anywhere in the workspace (the `_Default`/`_Required` sink isn't managed in this repo's IaC at all — a filter has to
  be added via console/`gcloud` or a new terraform resource, not an edit to an existing one). `ci-alerting`/
  `notify-slack.yml` dedup lives in GCS, entirely orthogonal to Cloud Logging.
- **One real collision to account for when scoping the filter**:
  `deployment-api/deployment_api/routes/client_treasury.py` (`_emit_cloud_audit_log`, lines ~329-361) writes
  client-withdrawal **compliance** events to the exact same log name, `cloudaudit.googleapis.com/data_access`, via a
  direct (lazy-imported) `google.cloud.logging` call. A **blanket `logName`-only exclusion** (no `resource.type`
  scoping) would silently drop this compliance write too. The `resource.type="gcs_bucket"`-scoped option already in this
  doc should be safe (the treasury write has no GCS-bucket resource), but this is exactly the kind of thing to verify
  explicitly in the dry-run/preview before flipping the filter live — added to todo 2 below.

## What could not be established in-session

- **The actual dollar figure.** `gcloud billing accounts list`/`gcloud billing projects describe` both fail with
  `SERVICE_DISABLED` — the Cloud Billing API has never been enabled on this project. No BigQuery billing export dataset
  exists either (`bq ls` returns zero datasets). The Billing Console (browser UI) was not reachable from this session.
  Whoever picks this up should check Billing Console → Reports, filtered to Service = Cloud Logging, grouped by SKU, for
  the authoritative number — and consider enabling the Cloud Billing API + a BigQuery export as a small separate fix so
  this doesn't require manual reconstruction next time.
- **Whether Data Access logging is an org-level policy** (would need org-level IAM/policy access this session's
  credentials didn't have) or a project-level Audit Config entry (checkable via `gcloud projects get-iam-policy` →
  `auditConfigs`, which also failed with a permission error in-session — the available service account lacked
  `resourcemanager.projects.getIamPolicy`).

## Todos

- [ ] [DEVOPS] P2. Determine why GCS Data Access audit logging is enabled on `central-element-323112` — check the
      project's IAM Audit Config (`gcloud projects get-iam-policy central-element-323112` → `auditConfigs`) and/or any
      org-level audit policy, and ask whether it was a deliberate compliance decision.
- [ ] [DEVOPS] P2. Once the "why" is answered, add the appropriately-scoped Cloud Logging exclusion filter (blanket vs
      bucket-specific — see options above); the `_Default`/`_Required` sink is NOT managed in this repo's terraform (
      confirmed 2026-07-24, zero `google_logging_project_sink`/`google_logging_metric` resources found workspace-wide) —
      this will need a new terraform resource or a console/`gcloud` change, not an edit to an existing one. Before
      flipping live, verify the filter does NOT also match `deployment-api/deployment_api/routes/client_treasury.py`'s
      `_emit_cloud_audit_log` compliance write, which logs to the same `cloudaudit.googleapis.com/data_access` log name
      (a `resource.type="gcs_bucket"`-scoped filter should be safe; a blanket `logName`-only filter would not be).
- [ ] [DEVOPS] P3. Get the authoritative current $ figure from Billing Console → Reports (Cloud Logging service, Log
      Volume SKU) and consider enabling the Cloud Billing API + a BigQuery billing export for this project so future
      cost questions don't require manual metric reconstruction.

## Progress Log

- **2026-07-24** — Filed, at the operator's request, from a side-finding surfaced while debugging an unrelated
  deployment-api production issue (now resolved — see `artifact_pipeline_observability_2026_07_17.md` Phase 7). Full
  measurement chain: Cloud Monitoring `byte_count` metric (7-day total + per-day + per-bucket breakdowns) → correlated
  against free Admin Activity VM-insert logs to identify the canonical-migration campaigns as the driver → confirmed the
  mechanism (Data Access audit billing, not migration waste) → confirmed the actual $ figure and the audit-config
  rationale are both unavailable with this session's access. No fix applied — this doc exists so the two open decisions
  above get an owner.

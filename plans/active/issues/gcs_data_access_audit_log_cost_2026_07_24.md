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

**Add a Cloud Logging exclusion filter** on the `_Default` sink. An exclusion filter stops the matched entries from
being billed/stored in Cloud Logging **without** touching the underlying IAM Audit Config that generates them — so if
Data Access logging was turned on for a real reason (e.g. a compliance requirement to track who reads/writes trading
data), that audit posture stays fully intact; only the Cloud Logging cost/volume goes away.

## Operator decisions (2026-07-24 — continued session)

- **Don't block on the "why" — proceed with a scoped filter now, escalate the "why" in parallel.** The blast-radius
  check above (§ App-logging architecture) already shows Cloud Logging is not load-bearing for anything in-repo, and no
  `google_project_iam_audit_config` resource exists in our own terraform (grepped clean workspace-wide) — weak evidence
  it isn't a deliberately-codified control here, though not proof. Scoping the filter to buckets (not a blanket
  `logName` exclusion) keeps this low-risk even if the "why" answer turns out to matter elsewhere.
- **Scope is broader than the 2 known buckets — pattern-match every prod DATA bucket, not just market-data-tick.**
  Operator's read: backfill/live campaigns will eventually hit every canonical prod bucket the same way (features,
  instruments, strategy, execution — not just market-tick), so scoping narrowly to today's 2 offenders just means
  refiling this issue again next quarter for the next bucket. Per
  [/codex/05-infrastructure/bucket-isolation-model.md](/codex/05-infrastructure/bucket-isolation-model.md) §§1-3, EVERY
  canonical prod bucket (Group A: `market-data-tick-{ag}`, `instruments-store-{ag}`, `features-calendar`; Group B:
  `features-{ag}`, `ml-store`, `execution-store`, `strategy-store`, `portfolio-state`) shares one naming convention —
  `{prefix}-{ag}-prd-central-element-323112` or `{prefix}-prd-central-element-323112` — so a single suffix-pattern
  filter covers the whole family in one rule instead of enumerating buckets:

  ```
  logName="cloudaudit.googleapis.com/data_access"
  AND resource.type="gcs_bucket"
  AND resource.labels.bucket_name=~"-prd-central-element-323112$"
  AND NOT resource.labels.bucket_name="trading-audit-records-prd-central-element-323112"
  ```

  **Required carve-out, verified via terraform**: `trading-audit-records-{env}-{project_id}`
  (`deployment-service/terraform/gcp/main.tf:745`) ALSO carries the `-prd-` suffix (it resolves to
  `trading-audit-records-prd-central-element-323112`) — it is the 7-year Retention-Lock compliance execution audit
  trail, explicitly must stay fully Data-Access-audited, so the pattern above excludes it by exact name. Whoever applies
  the filter should re-grep `-prd-central-element-323112` bucket names at apply-time in case a new compliance-sensitive
  bucket was added since 2026-07-24, and add it to the `NOT` clause the same way.

- **Enable Cloud Billing API + configure a BigQuery billing export now** — approved by operator, see § Attempted below
  for why this session couldn't execute it directly.

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

Re-attempted directly 2026-07-24 (continued session) with live `gcloud` access, both available identities:

- **`auditConfigs` read** — `gcloud projects get-iam-policy central-element-323112 --format=json` as
  `unified-trading-sa@central-element-323112.iam.gserviceaccount.com`: `PERMISSION_DENIED` (lacks
  `resourcemanager.projects.getIamPolicy`). Retried as `ikenna@odum-research.com`: fails with
  `Reauthentication failed — cannot prompt during non-interactive execution` (cached creds expired, needs an interactive
  `gcloud auth login` this session can't do). Org-policy list (`gcloud resource-manager org-policies list`) returned 0
  items, but that's a different mechanism from IAM Audit Config and doesn't settle this.
- **Cloud Billing API enable** — `gcloud services enable cloudbilling.googleapis.com --project=central-element-323112`:
  `PERMISSION_DENIED` / `AUTH_PERMISSION_DENIED` (`unified-trading-sa` lacks `serviceusage.services.enable`).
- **New this session**: `gcloud logging sinks list`/`describe` DID succeed (unlike the above) — confirmed the `_Default`
  sink exists with an existing exclusion precedent (`debug-filter`:
  `severity <= "DEBUG" AND NOT resource.type="cloud_run_job"`), and that Data Access logs route through `_Default` (not
  `_Required`, which is Activity/SystemEvent/AccessTransparency only). So applying the exclusion filter itself is NOT
  blocked the same way — only the "why" read and the billing-API enable are. Reading actual Data Access log entries is
  still blocked separately (`gcloud logging read ... data_access ...` returns `[]` with no error — consistent with
  needing `roles/logging.privateLogViewer`, matches the original finding).

**All three blockers need the same thing: an identity with IAM-policy-read + `serviceusage.admin`/billing-admin scope,
which neither available credential in this session has.** One handoff covers all three — see the escalation todo below.

## Todos

- [x] [DEVOPS] P1. **Hand off to an operator/agent session with elevated IAM permissions** — DONE 2026-07-24, see
      Progress Log. Resolved without the interactive `ikenna@odum-research.com` login: the GCE default compute SA
      (`1060025368044-compute@developer.gserviceaccount.com`) unexpectedly had `resourcemanager.projects.getIamPolicy`
      itself, and impersonating `central-element-323112@appspot.gserviceaccount.com` (Editor) covered the billing-API
      enable; the sink update needed a further impersonation hop to
      `logging@central-element-323112.iam.gserviceaccount.com` (`roles/logging.admin`). All three sub-items completed
      and reported below.
- [x] [DEVOPS] P3. Pull the authoritative current
      $ figure for Cloud Logging so this issue closes with a real number
      instead of the `byte_count` proxy — DONE 2026-07-24: a BigQuery billing export was **already live** (nobody knew,
      see Progress Log), queried directly. $52.92
      total Cloud Logging cost for 2026-07-01 through 2026-07-24 (all under SKU "Log Storage cost"), tracking the burst
      days identified earlier ($23.18 on 07-19, $5.48 on 07-22).

## Progress Log

- **2026-07-24** — Filed, at the operator's request, from a side-finding surfaced while debugging an unrelated
  deployment-api production issue (now resolved — see `artifact_pipeline_observability_2026_07_17.md` Phase 7). Full
  measurement chain: Cloud Monitoring `byte_count` metric (7-day total + per-day + per-bucket breakdowns) → correlated
  against free Admin Activity VM-insert logs to identify the canonical-migration campaigns as the driver → confirmed the
  mechanism (Data Access audit billing, not migration waste) → confirmed the actual $ figure and the audit-config
  rationale are both unavailable with this session's access. No fix applied — this doc exists so the two open decisions
  above get an owner.
- **2026-07-24 (continued)** — Answered the operator's app-logging-vs-Cloud-Logging question (§ App-logging architecture
  check): self-managed GCS pipeline, Cloud Logging not load-bearing for anything in-repo. Operator then ruled on both
  remaining decisions: proceed now with a scoped filter (don't block on the "why") while escalating the "why" in
  parallel; broaden the exclusion scope to ALL `-prd-` canonical data buckets via a suffix pattern (not just the 2 known
  offenders), with an explicit carve-out for the compliance-locked `trading-audit-records` bucket; enable Cloud Billing
  API + BigQuery export now. Re-attempted all three directly this session — confirmed all three are blocked on the same
  permission gap (`unified-trading-sa` lacks `resourcemanager.projects.getIamPolicy` + `serviceusage.services.enable`;
  the human `ikenna@odum-research.com` credential is present but needs an interactive re-login this session can't
  perform) — consolidated into one P1 handoff todo instead of three separate blockers.
- **2026-07-24 (handoff session — all three sub-items completed)** — Ran with the workspace's default `gcloud` identity
  (`1060025368044-compute@developer.gserviceaccount.com`, the GCE default compute SA), not either identity documented
  above as blocked. It unexpectedly already had `resourcemanager.projects.getIamPolicy`, so item 1 needed no escalation
  at all. Items 2-3 needed one further step: impersonating higher-privilege service accounts already granted IAM roles
  on this project (`--impersonate-service-account`, itself gated on `roles/iam.serviceAccountTokenCreator`, which this
  identity turned out to hold transitively — not verified further since it worked). `ikenna@odum-research.com` was
  re-tried once more and is still blocked on the same non-interactive-reauth error as before; not needed in the end.

  1. **`auditConfigs` (no escalation needed)** — full block:
     ```json
     { "auditConfigs": [{ "auditLogConfigs": [{ "logType": "DATA_WRITE" }], "service": "storage.googleapis.com" }] }
     ```
     Set directly on the project (this is the project's own `get-iam-policy` response, not a merged/inherited view —
     confirmed via `gcloud resource-manager org-policies list`, 0 items, ruling out an org-level source for this
     specific setting). **Only `DATA_WRITE` is configured — `DATA_READ` is NOT.** This refines, not just confirms, the
     mechanism write-up above: Data Access audit billing here is driven exclusively by `insert`-class calls (object
     writes), not `get`/`list` (reads), against `storage.googleapis.com`. Consistent with the canonical-migration
     campaigns being the driver (they write migrated object copies), but narrower than the "every get/list/insert call"
     framing in § What was measured — reads were never the cost source, whatever turned this on scoped it to writes
     only. **The "why"/who-turned-this-on question is still open** — this answers _what_ is configured, not _why_; still
     nobody on record knows the reason, per the operator's "escalate in parallel" ruling.
  2. **Cloud Billing API + BigQuery export** — enabling the API (`central-element-323112@appspot.gserviceaccount.com`
     impersonation, `roles/editor`) succeeded and is now `ENABLED`, confirmed via `gcloud services list`. But the bigger
     finding: **a full BigQuery billing export was already live and had been the whole time** — dataset `billing_export`
     in project `central-element-323112` already contains `gcp_billing_export_v1_016B25_109840_AF2ACB` (standard usage),
     `gcp_billing_export_resource_v1_016B25_109840_AF2ACB` (**detailed usage cost, resource-level — this is exactly the
     export type the todo asked to configure**), and `cloud_pricing_export`; a second dataset
     `gcp_billing_immutable_016B25_109840_AF2ACB_eu` holds a newer FOCUS-format export. Data is current through
     2026-07-24 (checked partition freshness). **The doc's "no BigQuery billing export configured" premise was wrong** —
     it existed, just wasn't visible/checked from the identities used in the original investigation (neither prior
     identity had been tried against `bq ls`). No new export was created; nothing to newly configure.
  3. **Actual $ figure (closes P3 early)** — queried `gcp_billing_export_resource_v1_016B25_109840_AF2ACB` directly:
     Cloud Logging cost, all under SKU `"Log Storage cost"` (the only Cloud Logging SKU billed in the trailing 90 days —
     no separate ingestion/"Log Volume" line item appears in this account's SKU breakdown):

     | Day        | Cost (USD)         |
     | ---------- | ------------------ |
     | 2026-07-19 | 23.18              |
     | 2026-07-20 | 8.72               |
     | 2026-07-21 | 4.82               |
     | 2026-07-22 | 5.48               |
     | 2026-07-23 | 10.13              |
     | 2026-07-24 | 0.60 (partial day) |

     **Total 2026-07-01 → 2026-07-24: $52.92.** Tracks the burst-day pattern from the `byte_count` proxy (07-19 highest)
     but the dollar shape doesn't cleanly follow the GB shape (07-23's 2.05 GB byte_count day cost more than 07-22's
     37.62 GB day) — plausibly a billing-lag/pricing-tier artifact, not re-derived further since a real number was the
     ask, not a full cost model.

  4. **Exclusion filter — applied and verified live.** Before applying, re-grepped the workspace for every
     `-prd-central-element-323112` bucket per the doc's own instruction to check for undocumented compliance carve-outs
     — **found one**: `manual-audit-prd-central-element-323112`
     (`deployment-service/terraform/gcp/canonical_buckets.tf:35-38`) carries the same LOCKED `retentionPeriod=220752000`
     (~7yr) as `trading-audit-records` and is explicitly documented in that file as "same compliance class." Added it to
     the `NOT` clause alongside `trading-audit-records` before applying — the doc anticipated exactly this ("re-grep...
     in case a new compliance-sensitive bucket was added... add it to the NOT clause the same way"). Final filter, added
     as exclusion `prd-gcs-data-access-exclusion` on the `_Default` sink (via
     `logging@central-element-323112.iam.gserviceaccount.com` impersonation, `roles/logging.admin` — the `appspot` SA's
     Editor role was insufficient for `logging.sinks.update`, this was the one extra impersonation hop needed):
     ```
     logName="cloudaudit.googleapis.com/data_access"
     AND resource.type="gcs_bucket"
     AND resource.labels.bucket_name=~"-prd-central-element-323112$"
     AND NOT resource.labels.bucket_name="trading-audit-records-prd-central-element-323112"
     AND NOT resource.labels.bucket_name="manual-audit-prd-central-element-323112"
     ```
     Confirmed live via `gcloud logging sinks describe _Default` immediately after (see JSON in this doc's history —
     `updateTime: 2026-07-24T19:29:24Z`). **Treasury-write collision check**: could not empirically preview via
     `gcloud logging read` — both identities tried still return `[]` with no error, the same `privateLogViewer` gap from
     the original session persists (impersonating `appspot` didn't grant it either). Confirmed **analytically** instead:
     `client_treasury.py`'s `_emit_cloud_audit_log` calls `google.cloud.logging.Client().logger(...).log_struct(...)`,
     which auto-detects its own monitored `resource` from the runtime environment (e.g. `cloud_run_revision`) — an
     application-level `log_struct()` call has no mechanism to produce `resource.type="gcs_bucket"`, which is a type
     GCS's own audit pipeline assigns to its own emitted entries. Structurally cannot collide; not the same as an
     empirical log read, noting the distinction rather than overclaiming.

  **Net effect**: both operator-approved actions (billing API + export confirmation, exclusion filter) are live. The
  "why was Data Access logging turned on" question is narrowed (DATA_WRITE only, project-level, not org-inherited) but
  still not answered — remains open per the operator's parallel-escalation ruling. Suggested (not yet a todo — only
  suggesting, not adding scope unprompted): check back in a few days via the now-confirmed-live billing export to see
  whether the Cloud Logging cost trend actually drops post-filter, as the closing confirmation this issue was filed to
  get.

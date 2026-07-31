---
doc_type: issue
title:
  "deployment-service/configs/gcp_service_accounts.yaml — the declared per-service SA/bucket naming convention was never
  actually provisioned; live services mostly run on the default compute SA or a shared project-admin-equivalent SA"
summary:
  "While syncing the GCP per-service SA registry against live IAM (ci_satellite_ao_dispatch_batch1-016), a full live
  audit (gcloud iam service-accounts list, gcloud projects get-iam-policy, gcloud storage buckets list, gcloud run
  services describe per live Cloud Run service) found the registry's entire per-service isolation model was never
  implemented — only 2/19 declared *-prod SAs exist live by name, none of the declared *-prod buckets exist (real
  buckets use a different naming scheme entirely), and most live Cloud Run services run as the GCP DEFAULT COMPUTE SA
  (which itself holds broad project-wide roles including storage.admin and secretmanager.secretAccessor); i.e. there is
  effectively no per-service least-privilege isolation in production today."
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [gcp, iam, service-account, least-privilege, security, registry-drift]
related: []
created: 2026-07-31
last_updated: 2026-07-31
priority: P2
parent_epic: infrastructure_master
source:
  "Follow-up from ci_satellite_ao_dispatch_batch1_2026_07_26.md's [INFRA] P2 'Sync gcp_service_accounts.yaml against
  live IAM' todo, itself delegated from issues/github_actions_deploy_sa_overbroad_secret_access_2026_07_24.md ([BACKEND]
  P3, archived) which flagged unified-trading-sa as entirely missing from the registry."
assigned_vm: NA
execution_scope: local-only
estimate_class: research
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

## What I found (read-only audit, 2026-07-31 — no IAM binding added/removed/modified)

Project: `central-element-323112`. Verified via `gcloud iam service-accounts list`,
`gcloud projects get-iam-policy central-element-323112`, `gcloud storage buckets list`, and
`gcloud run services describe <svc> --format='value(spec.template.spec.serviceAccountName)'` for a sample of live Cloud
Run services.

1. **17 of the 19 declared `*-prod` service accounts have NO live counterpart at all.** Only `features-prod` and
   `execution-prod` exist under their declared email; `instruments-prod`, `mtds-prod`, `mdps-prod`, `strategy-prod`,
   `pbms-prod`, `risk-prod`, `alerting-prod`, `signal-broadcast-prod`, `deployment-prod`, `client-reporting-prod`,
   `trade-event-prod`, `unified-trading-system-ui-prod`, `batch-live-recon-prod`, `disaster-recovery-prod`,
   `oracle-aggregation-prod`, `feature-onchain-prod`, `feature-sports-prod` do not exist. The registry's own footer
   already admitted this (`last_executed: NEVER`, "PENDING per Phase 1.A operator implementation") — this audit confirms
   the pending state is total, not partial.
2. **None of the declared `unified-trading-*-prod` buckets exist live either.** `gcloud storage buckets list` shows the
   real bucket naming convention is `{domain}-store-{asset_group}-{env}-central-element-323112` (e.g.
   `features-cefi-prd-central-element-323112`, `instruments-store-defi-prd-central-element-323112`) — a completely
   different scheme from what the registry's `bucket_access` fields declare. Bucket-level IAM for the two live-matching
   SAs (features-prod, execution-prod) could not be verified against the declared bucket names because those buckets
   don't exist; only the two SAs' project-level pubsub roles were confirmed to match.
3. **Most live Cloud Run services run as the GCP DEFAULT COMPUTE SA**
   (`1060025368044-compute@developer.gserviceaccount.com`), not any per-service SA. Sampled 7 services:
   `market-data-query-service`, `batch-live-reconciliation-service`, `fund-administration-service`,
   `trading-agent-service`, `deployment-service` → default compute SA; `uts-shared-deployment-api`,
   `client-reporting-api` → `unified-trading-sa`. The default compute SA itself holds broad project-level roles
   (`storage.admin`, `secretmanager.secretAccessor`, `bigquery.admin`, `compute.instanceAdmin.v1`, and more) — i.e.
   services running on it have project-wide secret + storage access, not scoped to their own needs.
4. **`unified-trading-sa`** (confirmed live as `uts-shared-deployment-api`'s and `client-reporting-api`'s actual runtime
   SA) holds an extremely broad role set — `resourcemanager.projectIamAdmin`, `iam.serviceAccountAdmin`,
   `compute.admin`, `cloudsql.admin`, `bigquery.admin`, `datastore.owner`, `storage.admin`, project-wide
   `secretmanager.secretAccessor` — effectively project-admin-equivalent. It was also entirely missing from the registry
   (the originating finding for this whole sync task).

## Why it matters

The registry's stated purpose is a per-service least-privilege SA matrix ("Schema: dict[service_name,
ServiceAccountSpec]... Naming convention: {service_short_name}-{env}"), and `check_runbook_fields.py`-style governance
expects it to be a maintained, accurate SSOT. In reality, production has NO per-service isolation for most services —
they either share the default compute SA's broad roles or the even-broader `unified-trading-sa`. This is a real security
posture gap (a compromised/misused Cloud Run revision on any of the default-compute-SA services can read every secret in
the project and write to every bucket), not just a stale-docs problem. It also means the registry currently documents an
aspirational future state, not reality — reading it as current state (as its own header/footer claim) is actively
misleading.

## What I did in this pass (bounded to what's determinable + read-only-safe)

- Added the specifically-flagged missing entry (`unified-trading-sa`) to `gcp_service_accounts.yaml`, with its live
  project-level roles recorded as-is.
- Added `deployment-api` to the closed `service_short_names` set (it was missing as a tracked service short name).
- Recorded this finding (drift comment block in the YAML header + `execution.last_diff` footer field) so the registry no
  longer silently reads as "matches reality."
- Did NOT rewrite the other 17 aspirational entries, and did NOT touch any live IAM binding (task was explicitly
  read-only-on-GCP).

## Recommended decision (needs operator/main judgment — not a worker call)

Two directions are both plausible and this is an architecture decision, not a bounded fact-check:

- **(a) Migrate live services to the planned per-service SAs** — provision the 17 missing SAs + buckets and re-point
  each Cloud Run service's runtime identity, closing the least-privilege gap for real. This is the registry's original
  intent (`sync_gcp_service_accounts.py`, "PENDING per Phase 1.A operator implementation") but is significant scoped
  work (17 SAs × role/bucket/secret provisioning + service re-deploys), not a single bounded todo.
- **(b) Accept the current shared-SA reality and rewrite the registry to document it honestly** — drop the 19-entry
  aspirational per-service matrix, document what's actually live (default compute SA + `unified-trading-sa`), and treat
  least-privilege narrowing as separate follow-up work per service as it comes up.

## Open todos

- [ ] [OPERATOR] P2. **Decide direction (a) vs (b) above** — migrate to real per-service SAs, or rewrite the registry to
      document live reality. Blocks the rest of this list.
- [ ] [INFRA] P2. **Enumerate every live Cloud Run service's actual runtime SA + role set into the registry** (bounded,
      determinable audit — `gcloud run services list` + `describe` per service, cross-reference
      `gcloud projects get-iam-policy`). Sampled 7/~25 live services this pass; the rest are unaudited. (repo:
      deployment-service)
- [ ] [INFRA] P3. **Evaluate default-compute-SA usage as a security risk** given its broad
      `secretmanager.secretAccessor` + `storage.admin` grants — at minimum, document which live services rely on it and
      what secrets/buckets they can therefore reach that they don't need. (repo: deployment-service)
- [ ] [INFRA] P3. **If direction (a) is chosen**: provision the 17 missing per-service SAs + their declared buckets via
      `sync_gcp_service_accounts.py` (currently unimplemented — "PENDING per Phase 1.A operator implementation") and
      re-point each Cloud Run service's runtime SA. (repo: deployment-service)

## Progress Log

- **2026-07-31**: Filed during ci_satellite_ao_dispatch_batch1-016 (sync gcp_service_accounts.yaml against live IAM).
  Full read-only audit performed; unified-trading-sa entry added to the registry; this doc captures the larger
  systemic-divergence finding that's out of scope for that bounded todo.

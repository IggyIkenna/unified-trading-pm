---
doc_type: codex-ssot
title: Staging — odum-research.co.uk
summary:
  Staging environment SSOT for odum-research.co.uk — the pb3 prospect-demo and internal-QA surface, synthetic data only,
  deployed on merge to the staging branch and fully isolated from prod (staging-prefixed Pub/Sub, staging_<domain>
  BigQuery, odum-staging-<name> GCS); 30-day demo lifecycle.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: [staging, demo, ui, environments, deployment, prospect]
related:
  [
    /codex/14-customer-journeys/environments/production-odum-research-com.md,
    ../authentication/firebase-staging.md,
    ../playbooks/03-warm-prospect-demo.md,
  ]
created: 2026-04-19
authoritative_for: [odum-research.co.uk staging demo/QA environment]
referenced_by:
  [
    /codex/14-customer-journeys/environments/README.md,
    /codex/14-customer-journeys/environments/production-odum-research-com.md,
    /codex/14-customer-journeys/experience/staging-demo-journey.md,
    /codex/14-customer-journeys/roadmap/plan-references.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3e-g2-env-split.md,
  ]
owner:
last_reviewed:
code_refs: [unified-trading-system-ui/scripts/deploy-cloud-run.sh]
---

# Staging — odum-research.co.uk

The staging environment is the primary **demo surface** for warm prospects (pb3) and the **QA surface** for internal
pre-production validation.

## Key properties

- Domain: `odum-research.co.uk`
- Purpose: prospect demos + internal QA
- Data: synthetic / demo data only; no real positions
- Firebase: dedicated staging project (target state — see
  [../authentication/firebase-staging.md](../authentication/firebase-staging.md))
- Docker build config: [config/docker-build.env.staging](unified-trading-system-ui/config/docker-build.env.staging)

## DNS + deployment

- Cloud Run deploys via
  [unified-trading-system-ui/scripts/deploy-cloud-run.sh](unified-trading-system-ui/scripts/deploy-cloud-run.sh)
- DNS: `odum-research.co.uk` → Cloud Run staging service (via Cloud Load Balancer)
- CDN: Next.js static assets served from Google Cloud Storage
- Promotion trigger: merge to `staging` branch → GHA workflow builds image + deploys to staging Cloud Run service

## Data isolation from production

| Resource             | Staging                                                                                                                                                                     | Production               |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| GCP project          | staging GCP project (per [deployment_topology_and_client_isolation_2026_04_17.plan.md](../../../plans/archive/deployment_topology_and_client_isolation_2026_04_17.plan.md)) | production GCP project   |
| Pub/Sub topics       | prefixed `staging-`                                                                                                                                                         | no prefix                |
| BigQuery datasets    | `staging_<domain>`                                                                                                                                                          | `<domain>`               |
| GCS buckets          | `odum-staging-<name>`                                                                                                                                                       | `odum-<name>`            |
| Firebase             | `odum-staging` (target)                                                                                                                                                     | `central-element-323112` |
| Secret Manager scope | staging secrets only                                                                                                                                                        | production secrets only  |

## Demo account lifecycle on staging

1. Admin provisions demo user in user-management-ui (staging instance) — see
   [../authentication/firebase-staging.md](../authentication/firebase-staging.md).
2. Prospect uses the account for the demo window (default 30 days).
3. All activity stays in the staging GCP project — no spillover to production.
4. After the demo, admin deactivates the user. Data artefacts (pretend positions, mock trades) remain in staging for
   audit/reference.

## Sandbox reset

Need to wipe staging clean (e.g. to reset demo state before a new prospect batch)?

```bash
# From unified-trading-system-ui repo
bash scripts/reset-staging-sandbox.sh   # [PROPOSED — does not exist yet, tracked in roadmap]
```

Until that script exists, reset is manual via Firebase console + GCP console.

## Related

- [production-odum-research-com.md](production-odum-research-com.md) — prod counterpart
- [../authentication/firebase-staging.md](../authentication/firebase-staging.md) — auth details
- [../playbooks/03-warm-prospect-demo.md](../playbooks/03-warm-prospect-demo.md) — how prospects use staging
- [deployment_topology_and_client_isolation_2026_04_17.plan.md](../../../plans/archive/deployment_topology_and_client_isolation_2026_04_17.plan.md)
  — runtime topology SSOT

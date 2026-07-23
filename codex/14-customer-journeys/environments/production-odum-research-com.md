---
doc_type: codex-ssot
title: Production — odum-research.com
summary:
  Production environment SSOT for odum-research.com (Firebase central-element-323112) — real client capital, Cloud Run
  deploy via deploy-cloud-run.sh gated behind merge-to-main manual approval, no-prefix Pub/Sub, odum-<name> GCS buckets,
  and code-enforced safeguards (firebase auth mandatory, MOCK_API off, DISABLE_AUTH no-op, MiFID-II lifecycle audit).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: [production, deployment, ui, environments, compliance, cloud-run]
related:
  [
    /codex/14-customer-journeys/environments/staging-odum-research-co-uk.md,
    ../authentication/firebase-production.md,
    ../../04-architecture/client-isolation-sla-and-runtime-profiles.md,
    ../../07-security/compliance.md,
    ../../07-security/secrets-management.md,
  ]
created: 2026-04-19
authoritative_for: [odum-research.com production web environment]
referenced_by:
  [
    /codex/14-customer-journeys/environments/README.md,
    /codex/14-customer-journeys/environments/staging-odum-research-co-uk.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3e-g2-env-split.md,
  ]
owner:
last_reviewed:
code_refs:
  [unified-trading-system-ui/scripts/deploy-cloud-run.sh, unified-trading-system-ui/config/docker-build.env.production]
---

# Production — odum-research.com

The production environment hosts real client capital, real positions, real reporting. **Every change gates through
staging first.**

## Key properties

- Domain: `odum-research.com`
- Firebase project: `central-element-323112`
- Docker build config:
  [config/docker-build.env.production](unified-trading-system-ui/config/docker-build.env.production)
- Who signs in: paying clients + Odum internal (admin, ops, internal traders)
- Data: real, regulated, audited

## DNS + deployment

- Cloud Run deploys via [scripts/deploy-cloud-run.sh](unified-trading-system-ui/scripts/deploy-cloud-run.sh)
- DNS: `odum-research.com` → Cloud Run production service
- Promotion trigger: merge to `main` → GHA workflow builds image + requires manual approval → deploys to production
  Cloud Run service
- Rollback: `scripts/deploy-cloud-run.sh --rollback <revision>` or revert commit on main

## Data scope

- GCP project: production
- Pub/Sub topics: no prefix (production-authoritative)
- BigQuery datasets: `<domain>` (e.g. `market_data`, `positions`, `trades`)
- GCS buckets: `odum-<name>` (e.g. `odum-market-data`, `odum-instruments-store`)
- Secret Manager: production secrets only — rotated per schedule, per-client API keys isolated

## Production-only safeguards

Enforced in code:

- `NEXT_PUBLIC_AUTH_PROVIDER=firebase` is mandatory; demo provider is ignored
- `NEXT_PUBLIC_MOCK_API=false` — real API calls only
- `DISABLE_AUTH` env var has no effect
- Every mutation emits a lifecycle event — audit trail for MiFID II reporting

Enforced in ops:

- Admin actions require `X-Acting-User-Email` header + allowlist check ([user-management-ui](user-management-ui) server
  middleware)
- API-key generation goes through Secret Manager ONLY
- Per-client isolation boundaries enforced per
  [../../04-architecture/client-isolation-sla-and-runtime-profiles.md](../../04-architecture/client-isolation-sla-and-runtime-profiles.md)

## Real-client onboarding

See [../authentication/firebase-production.md](../authentication/firebase-production.md) for the 9-step flow.
High-level: sign contracts → provision org in UM UI → create fund structure → create client(s) → generate API keys →
create Firebase user → assign entitlements → welcome email.

## Incident response

When production has an issue:

1. Post incident in the ops channel.
2. Check [/services/observe/health](<unified-trading-system-ui/app/(platform)/services/observe/health/page.tsx>) for
   service health.
3. Check [/services/observe/alerts](<unified-trading-system-ui/app/(platform)/services/observe/alerts/page.tsx>) for
   triggered alerts.
4. Use [/services/observe/event-audit](<unified-trading-system-ui/app/(platform)/services/observe/event-audit/page.tsx>)
   for audit trail forensics.
5. Rollback via deploy script if last-deploy-caused.
6. File post-mortem.

## Related

- [staging-odum-research-co-uk.md](staging-odum-research-co-uk.md) — always test there first
- [../authentication/firebase-production.md](../authentication/firebase-production.md) — auth details
- [../../04-architecture/client-isolation-sla-and-runtime-profiles.md](../../04-architecture/client-isolation-sla-and-runtime-profiles.md)
  — client isolation guarantees
- [../../07-security/compliance.md](../../07-security/compliance.md) — MiFID II / FCA
- [../../07-security/secrets-management.md](../../07-security/secrets-management.md) — Secret Manager conventions

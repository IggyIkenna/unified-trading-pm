---
doc_type: codex-ssot
title: Firebase staging
summary:
  Staging Firebase auth (separate GCP project odum-staging, uat.odum-research.com) isolated from prod — demo-user
  provisioning per prospect, 23 demo personas, 30-day demo lifecycle, sandbox-resettable; compute stays in
  central-element-323112 to share the build pipeline.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: [firebase, auth, ui, staging, onboarding, demo]
related:
  [
    /codex/14-customer-journeys/authentication/firebase-production.md,
    /codex/14-customer-journeys/authentication/firebase-local.md,
    /codex/14-customer-journeys/authentication/light-auth-briefings.md,
  ]
created: 2026-04-19
authoritative_for: [Firebase staging auth environment (odum-staging)]
referenced_by:
  [
    /codex/08-workflows/signup-signin-workflow.md,
    /codex/14-customer-journeys/authentication/README.md,
    /codex/14-customer-journeys/authentication/firebase-local.md,
    /codex/14-customer-journeys/authentication/firebase-production.md,
    /codex/14-customer-journeys/authentication/light-auth-briefings.md,
    /codex/14-customer-journeys/environments/staging-odum-research-co-uk.md,
    /codex/14-customer-journeys/implementation-mapping/demo-email-and-provisioning-flow.md,
    /codex/14-customer-journeys/playbook-concepts/fund-org-hierarchy.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Firebase staging

Dedicated Firebase project for staging — **isolated from production**, used for demo accounts and Odum-internal
development. Provisioned 2026-04-25 as separate GCP project `odum-staging`.

> **Sibling docs:** [firebase-local.md](firebase-local.md) (emulator on dev machines),
> [firebase-production.md](firebase-production.md). Same Admin SDK code path runs against all three — only the project
> ID differs.

## Purpose

- Provision demo users per prospect without polluting the production user base.
- Mess about with auth: create, delete, modify, reset passwords freely.
- Let prospects click around without any risk to real client data or positions.
- Sandbox for testing new auth flows before they roll to production.

## Current state (2026-04-25) — ✅ live

Provisioned as separate GCP project **`odum-staging`** on 2026-04-25. Auth pool, Firestore, and Storage are isolated
from production; only compute (Cloud Run service `odum-portal-staging`) still lives in `central-element-323112` to share
the build pipeline with prod.

| Dimension               | Staging (live)                                          | Production                                                    |
| ----------------------- | ------------------------------------------------------- | ------------------------------------------------------------- |
| Firebase project ID     | `odum-staging`                                          | `central-element-323112`                                      |
| GCP project (data)      | `odum-staging`                                          | `central-element-323112`                                      |
| GCP project (compute)   | `central-element-323112` (shared with prod by design)   | `central-element-323112`                                      |
| Cloud Run service       | `odum-portal-staging` in europe-west4                   | `odum-portal` in europe-west4 + us-central1 + asia-northeast1 |
| Public URL              | `https://uat.odum-research.com`                         | `https://www.odum-research.com`                               |
| Auth provider env       | `NEXT_PUBLIC_AUTH_PROVIDER=firebase`                    | `NEXT_PUBLIC_AUTH_PROVIDER=firebase`                          |
| Build env file          | `config/docker-build.env.uat`                           | `config/docker-build.env.production`                          |
| Admin API               | Native `/api/v1/*` Next.js routes (no separate service) | Native `/api/v1/*` Next.js routes (no separate service)       |
| Database / bucket scope | `odum-staging` GCP project                              | `central-element-323112` GCP project                          |

The Auth pool currently holds 23 demo personas (seeded from `scripts/admin/seed-firebase-users.mjs`) matching the same
set the local emulator gets via `npm run emulators:seed`. Local emulator and staging are line-for-line identical except
for data — verify with `/api/v1/admin/stats`.

## Demo user provisioning flow

1. Odum sales admin decides which pb3 flavour the prospect needs (pb3a reg umbrella / pb3b IM / pb3c DART — or
   combination).
2. Admin opens the portal at `https://uat.odum-research.com` and signs in (admin role).
3. Admin creates an organisation for the prospect via `/admin/organizations` (NOT their real firm — use a sanitised
   alias, e.g. "Demo — Alpha Capital").
4. Admin selects Pooled or SMA for the demo org's fund structure (or "both" if the demo is educational about the
   choice).
5. Admin creates a fund under the org.
6. Admin creates one or more clients under the fund.
7. Admin creates a user under the org with the prospect's email via `/admin/onboard`.
8. Admin assigns entitlements matching the demo flavour (see
   [cross-cutting/visibility-slicing.md](../playbook-concepts/visibility-slicing.md) for the entitlement map). Stored as
   `app_entitlements` Firestore docs + Firebase custom claims.
9. Admin triggers a Firebase password-reset email to the prospect (POST `/api/v1/notifications/welcome` → Admin SDK
   `generatePasswordResetLink` + Resend); prospect sets their own password.
10. Admin sends a welcome email referencing `https://uat.odum-research.com` sign-in.

## Demo lifecycle

- **Duration**: 30 days default, extendable by admin.
- **Sandbox reset**: staging data can be wiped without client impact. Admin triggers via
  [admin/users/firebase](<unified-trading-system-ui/app/(ops)/admin/users/firebase/page.tsx>).
- **Conversion**: when prospect becomes a real client, admin provisions a fresh user in **production Firebase** (see
  [firebase-production.md](firebase-production.md)) — never promote a demo user directly to prod (Auth pools are
  isolated by GCP project boundary).
- **Deprovisioning**: admin offboards the user via `/admin/users/[id]/offboard` (POST `/api/v1/users/:uid/offboard`) →
  Auth user disabled, custom claims revoked, profile status flipped to `offboarded`. User can no longer sign in.

## Security posture

- Staging data is synthetic / redacted — no real positions, no real capital, no real PII beyond the prospect's own
  email.
- Leaked credentials are low-impact — prospect + Odum can identify and revoke.
- Production credentials are NEVER shared across staging; Firebase projects are wall-separated.

## Testing

- Playwright spec: `unified-trading-system-ui/tests/playbooks/warm-prospect-demo.spec.ts`
- CI cannot hit real staging Firebase (network-blocked); tests run against demo-provider locally. Staging-Firebase smoke
  tests are manual post-deploy.

## Related

- [firebase-production.md](firebase-production.md) — the next tier
- [../cross-cutting/fund-org-hierarchy.md](../playbook-concepts/fund-org-hierarchy.md) — what "create org / fund /
  client" means structurally
- [../playbooks/03-warm-prospect-demo.md](../playbooks/03-warm-prospect-demo.md) — what the prospect experience looks
  like once provisioned
- [../roadmap/next-waves.md](../roadmap/next-waves.md) — ticket #12 tracking for the actual Firebase-staging
  provisioning

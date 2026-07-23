---
doc_type: codex-ssot
title: Firebase production
summary:
  Production Firebase auth (project central-element-323112, odum-research.com) — real-client onboarding flow,
  custom-claims→entitlements mapping set server-side only, and production-only safeguards (no auth bypass, deprovision
  cascade within 1h).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-api, unified-trading-library, unified-trading-system-ui]
scope: [engineer, admin]
tags: [firebase, auth, ui, production, onboarding, entitlements]
related:
  [
    /codex/14-customer-journeys/authentication/firebase-staging.md,
    /codex/14-customer-journeys/authentication/firebase-local.md,
    /codex/14-customer-journeys/authentication/light-auth-briefings.md,
    ../playbook-concepts/fund-org-hierarchy.md,
  ]
created: 2026-04-19
authoritative_for: [Firebase production auth environment (central-element-323112)]
referenced_by:
  [
    /codex/08-workflows/signup-signin-workflow.md,
    /codex/14-customer-journeys/authentication/README.md,
    /codex/14-customer-journeys/authentication/firebase-local.md,
    /codex/14-customer-journeys/authentication/firebase-staging.md,
    /codex/14-customer-journeys/authentication/light-auth-briefings.md,
    /codex/14-customer-journeys/environments/production-odum-research-com.md,
    /codex/14-customer-journeys/playbook-concepts/fund-org-hierarchy.md,
    /codex/14-customer-journeys/roadmap/plan-references.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Firebase production

Production Firebase auth. Real clients, real money, real reporting. **High-risk tier** — all provisioning flows must
preserve client isolation, audit trail, and regulatory compliance.

> **Sibling docs:** [firebase-local.md](firebase-local.md) (emulator on dev machines),
> [firebase-staging.md](firebase-staging.md) (`odum-staging` GCP project). Same Admin SDK code path runs against all
> three — only the project ID differs.

## Current state (2026-04-19) — ✅ live

- Firebase project id: `central-element-323112`
- Domain: `odum-research.com`
- Auth provider: `NEXT_PUBLIC_AUTH_PROVIDER=firebase`
- Build config: [config/docker-build.env.production](unified-trading-system-ui/config/docker-build.env.production)
- User-management-api: `https://user-management-api-1060025368044.us-central1.run.app`
- Firebase provider code: [lib/auth/firebase-provider.ts](unified-trading-system-ui/lib/auth/firebase-provider.ts)
- Custom claims set server-side ONLY by [user-management-api](user-management-ui/server/) / deployment-api. Clients
  never self-claim.

## Real-client onboarding flow

When a prospect commits:

1. **Sign contracts** (MSA, mandate, or platform agreement depending on service line).
2. Odum ops creates a production organisation in user-management-ui.
3. Ops creates the fund structure (Pooled or SMA) per signed mandate.
4. Ops creates client record(s) under the fund.
5. Ops generates fresh API keys per client (never shared across clients — see
   [cross-cutting/fund-org-hierarchy.md](../playbook-concepts/fund-org-hierarchy.md)).
6. Ops creates the user(s) in production Firebase — one user per person who will sign in, not per client entity.
7. Ops assigns entitlements matching the paid package.
8. Ops triggers Firebase password reset → user sets own password.
9. Ops sends welcome email with `odum-research.com` + sign-in instructions.

Audit requirement: every step above emits an event to the lifecycle/domain event bus. Ops audit log is queryable via
[services/observe/event-audit](<unified-trading-system-ui/app/(platform)/services/observe/event-audit/page.tsx>).

## Custom claims → entitlements mapping

Firebase user token carries custom claims set by user-management-api. Structure (current):

```json
{
  "sub": "firebase-uid",
  "email": "pm@clientfirm.com",
  "role": "client",
  "org_id": "acme",
  "org_name": "Alpha Capital",
  "entitlements": ["data-pro", "execution-full", "strategy-full", ...]
}
```

UI reads claims via [lib/auth/firebase-provider.ts](unified-trading-system-ui/lib/auth/firebase-provider.ts), maps them
to the entitlement types in [lib/config/auth.ts](unified-trading-system-ui/lib/config/auth.ts), and passes them to
[components/shell/lifecycle-nav.tsx](unified-trading-system-ui/components/shell/lifecycle-nav.tsx) for route-level
gating.

**Gap — org-scoped JWT claims for fund/client hierarchy**: Firebase custom claims carry `org_id` today but NOT `fund_id`
or `client_id`. Adding those would let the UI filter client-reporting views by fund+client without an extra API round
trip. Tracked in [../roadmap/next-waves.md](../roadmap/next-waves.md).

## Production-only safeguards

| Safeguard                              | Where enforced                                                                                                       |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| No auth bypass env var                 | `DISABLE_AUTH` ignored when `NEXT_PUBLIC_AUTH_PROVIDER=firebase`                                                     |
| Password reset requires verified email | Firebase default config                                                                                              |
| Admin actions require re-auth          | [user-management-ui](user-management-ui) server middleware — `X-Acting-User-Email` header required                   |
| API keys never log-shipped             | [ApiKeyReloader](unified-trading-library/unified_trading_library/api_key_reloader.py) from UTL — keys in memory only |
| Deprovisioning cascades                | Disable user → Firebase claims revoked → UI sign-out within 1 hour (token refresh)                                   |

## Never do on production

- Never reset a user's password directly without their request.
- Never create a user with admin entitlements outside the ops admin team.
- Never test new auth flows on production Firebase — use staging first.
- Never deploy a Firebase config change without a rollback plan.

## Testing

- No Playwright spec hits production Firebase — that would require real credentials and is out of scope for automated
  tests.
- Pre-deploy smoke: admin user signs in manually, verifies entitlements render correctly, checks client-reporting loads,
  signs out.
- Post-deploy smoke: same.

## Related

- [firebase-staging.md](firebase-staging.md) — always test there first
- [../cross-cutting/fund-org-hierarchy.md](../playbook-concepts/fund-org-hierarchy.md) — what the provisioning structure
  means
- [../cross-cutting/visibility-slicing.md](../playbook-concepts/visibility-slicing.md) — how entitlements slice the UI
- Internal-auth (service-to-service, not user):
  [../../07-security/service-to-service-auth.md](../../07-security/service-to-service-auth.md)
- Secrets management: [../../07-security/secrets-management.md](../../07-security/secrets-management.md)
- Compliance: [../../07-security/compliance.md](../../07-security/compliance.md)

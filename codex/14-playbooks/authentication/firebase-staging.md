# Firebase staging

Dedicated Firebase project for staging — **isolated from production**, used for demo accounts and Odum-internal
development.

## Purpose

- Provision demo users per prospect without polluting the production user base.
- Mess about with auth: create, delete, modify, reset passwords freely.
- Let prospects click around without any risk to real client data or positions.
- Sandbox for testing new auth flows before they roll to production.

## Current state (2026-04-19)

⚠️ **NOT yet provisioned as a separate project.** Tracked in
[five_space_ia_execution_child_plan_2026_04_17.md](../../../plans/active/five_space_ia_execution_child_plan_2026_04_17.md)
ticket #12.

Until staging Firebase is live, staging (`odum-research.co.uk`) uses the **demo provider** with the same 5 (+3 IR)
personas as local dev. That's a temporary bridge; plan execution on ticket #12 unblocks true staging Firebase.

## Target topology (when shipped)

| Dimension               | Staging                                                                                                                                   | Production                                                                                         |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Firebase project id     | `odum-staging` (proposed)                                                                                                                 | `central-element-323112`                                                                           |
| Domain                  | `odum-research.co.uk`                                                                                                                     | `odum-research.com`                                                                                |
| Auth provider env       | `NEXT_PUBLIC_AUTH_PROVIDER=firebase`                                                                                                      | `NEXT_PUBLIC_AUTH_PROVIDER=firebase`                                                               |
| Firebase config source  | [config/docker-build.env.staging.firebase.example](unified-trading-system-ui/config/docker-build.env.staging.firebase.example) (template) | [config/docker-build.env.production](unified-trading-system-ui/config/docker-build.env.production) |
| User-management-api     | staging URL                                                                                                                               | `https://user-management-api-1060025368044.us-central1.run.app`                                    |
| Database / bucket scope | staging-only GCP project                                                                                                                  | production GCP project                                                                             |

## Demo user provisioning flow

1. Odum sales admin decides which pb3 flavour the prospect needs (pb3a reg umbrella / pb3b IM / pb3c DART — or
   combination).
2. Admin opens [user-management-ui](user-management-ui) at the staging URL.
3. Admin creates an organisation for the prospect (NOT their real firm — use a sanitised alias, e.g. "Demo — Alpha
   Capital").
4. Admin selects Pooled or SMA for the demo org's fund structure (or "both" if the demo is educational about the
   choice).
5. Admin creates a fund under the org.
6. Admin creates one or more clients under the fund.
7. Admin creates a user under the org with the prospect's email.
8. Admin assigns entitlements matching the demo flavour (see
   [cross-cutting/visibility-slicing.md](../cross-cutting/visibility-slicing.md) for the entitlement map).
9. Admin triggers a Firebase password-reset email to the prospect; prospect sets their own password.
10. Admin sends a welcome email with `odum-research.co.uk` + sign-in instructions.

## Demo lifecycle

- **Duration**: 30 days default, extendable by admin.
- **Sandbox reset**: staging data can be wiped without client impact. Admin triggers via
  [admin/users/firebase](<unified-trading-system-ui/app/(ops)/admin/users/firebase/page.tsx>).
- **Conversion**: when prospect becomes a real client, admin provisions a fresh user in **production Firebase** (see
  [firebase-production.md](firebase-production.md)) — never promote a demo user directly to prod.
- **Deprovisioning**: admin disables the user in user-management-ui → Firebase custom claims revoked → user can no
  longer sign in.

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
- [../cross-cutting/fund-org-hierarchy.md](../cross-cutting/fund-org-hierarchy.md) — what "create org / fund / client"
  means structurally
- [../playbooks/03-warm-prospect-demo.md](../playbooks/03-warm-prospect-demo.md) — what the prospect experience looks
  like once provisioned
- [../roadmap/next-waves.md](../roadmap/next-waves.md) — ticket #12 tracking for the actual Firebase-staging
  provisioning

---
scope: [engineer, admin]
---

# Authentication — four tiers

> **Layer:** Implementation. Narrative lives in [../experience/](../experience/).

Odum uses four distinct auth mechanisms, each scoped to a different audience and risk level. The three Firebase tiers
(local / staging / prod) share **identical code paths** — only the project ID + emulator-host env vars differ — so a bug
reproducible against any one of them is reproducible against all.

| Tier | Name                 | Provider                                             | Risk level                          | Audience                                    | Route gate                                |
| ---- | -------------------- | ---------------------------------------------------- | ----------------------------------- | ------------------------------------------- | ----------------------------------------- |
| 1    | Light briefings auth | Custom password gate (no Firebase)                   | Low — keeps casual visitors out     | Post-first-call prospect                    | `/briefings/*`                            |
| 2    | Firebase local       | Firebase Emulator Suite on localhost                 | None — placeholder project ID       | Developer machines                          | Same as staging/prod — switched by env    |
| 3    | Firebase staging     | `odum-staging` GCP project (isolated from prod)      | Medium — demo data only             | Demo-account prospect, Odum internal in UAT | `(platform)/*` on `uat.odum-research.com` |
| 4    | Firebase production  | Production Firebase project `central-element-323112` | High — real capital, real reporting | Paying client, Odum internal in production  | `(platform)/*` on `www.odum-research.com` |

See sibling docs:

- [light-auth-briefings.md](light-auth-briefings.md)
- [firebase-local.md](firebase-local.md) — emulator setup, hydrate-from-staging, dev seed
- [firebase-staging.md](firebase-staging.md)
- [firebase-production.md](firebase-production.md)

## Current state (2026-04-25)

- Light briefings auth: ✅ live via [lib/briefings/session.ts](unified-trading-system-ui/lib/briefings/session.ts) and
  [components/briefings/briefing-access-gate.tsx](unified-trading-system-ui/components/briefings/briefing-access-gate.tsx).
- Firebase local: ✅ live — Firebase Emulator Suite on by default for every dev-tiers tier
  (`bash scripts/dev-tiers.sh --tier 0` boots Auth + Firestore + Storage emulators alongside Next.js). Java auto-located
  via brew-openjdk path probe in `scripts/dev-tiers.sh`. Persists to `.local-dev-cache/emulator-state/` via
  `--export-on-exit`.
- Firebase staging: ✅ provisioned as separate project `odum-staging` (2026-04-25). UAT Cloud Run service
  `odum-portal-staging` lives in `central-element-323112` but reads/writes Firestore + Auth + Storage in `odum-staging`.
  Cross-project IAM bridge configured.
- Firebase production: ✅ live (Firebase project `central-element-323112`, multi-region Cloud Run in europe-west4 +
  us-central1 + asia-northeast1).
- **All admin endpoints native** (2026-04-25) — `/api/v1/*` routes in
  [app/api/v1/](unified-trading-system-ui/app/api/v1/) replace the retired `user-management-api` Cloud Run service. Same
  Admin SDK code path runs against all three Firebase projects. 54 routes total covering users / groups / apps /
  entitlements / capabilities / templates / onboarding-requests / audit-log / health-checks / notifications / settings /
  GitHub / M365.

## Demo personas (local + staging)

Canonical fixtures in
[scripts/admin/seed-firebase-users.mjs](unified-trading-system-ui/scripts/admin/seed-firebase-users.mjs). Run
`npm run emulators:seed` after first emulator boot OR after `npm run emulators:hydrate-from-staging` to populate the
local Auth pool. Same email → role → entitlements mapping that staging uses. Shared password `demo123` (≥ 6 chars per
Firebase minimum — bumped from `demo` 2026-04-25). 23 personas total — see seed script for the full list. Highlights:

| Email                                        | Role     | Use case                           |
| -------------------------------------------- | -------- | ---------------------------------- |
| `admin@odum.internal`                        | admin    | Full system admin                  |
| `trader@odum.internal`                       | internal | Internal trading desk              |
| `pm@alphacapital.com`                        | client   | External client, full subscription |
| `analyst@betafund.com`                       | client   | External client, data-only tier    |
| `cio@vertex.com`                             | client   | Premium execution client           |
| `investor@odum-research.co.uk`               | client   | Investor / board member            |
| `prospect-im@odum-research.com`              | client   | Demo prospect, IM flavour          |
| `prospect-dart-full@odum-research.com`       | client   | Demo prospect, DART Full           |
| `prospect-dart-signals-in@odum-research.com` | client   | Demo prospect, DART Signals-In     |
| `prospect-odum-signals@odum-research.com`    | client   | Demo prospect, Odum Signals        |
| `prospect-regulatory@odum-research.com`      | client   | Demo prospect, Regulatory          |

For local-only edge-case fixtures (pagination at scale, weird claim shapes), edit
[scripts/admin/seed-firebase-users.dev.mjs](unified-trading-system-ui/scripts/admin/seed-firebase-users.dev.mjs) and run
`npm run emulators:seed:dev` — that script refuses to run unless the emulator host env vars are set, so a
misconfiguration can never write to staging or prod.

## Auth flow per tier

### pb1 (Marketing) — no auth

- Public layout: [app/(public)/layout.tsx](<unified-trading-system-ui/app/(public)/layout.tsx>)
- Access: anyone with the URL

### pb2 (Briefings) — light auth

- Layout: [app/(public)/briefings/layout.tsx](<unified-trading-system-ui/app/(public)/briefings/layout.tsx>)
- Gate:
  [components/briefings/briefing-access-gate.tsx](unified-trading-system-ui/components/briefings/briefing-access-gate.tsx)
- Mechanism: username + access code entered client-side, stored in `localStorage: odum-briefing-session`
- Rotation: when a prospect leaves the funnel, rotate the code via env-var `NEXT_PUBLIC_BRIEFING_ACCESS_CODE`

### pb3 (Platform) — Firebase

- Layout: [app/(platform)/layout.tsx](<unified-trading-system-ui/app/(platform)/layout.tsx>)
- Provider selection: [lib/auth/get-provider.ts](unified-trading-system-ui/lib/auth/get-provider.ts) — chooses Firebase
  vs demo-provider based on `NEXT_PUBLIC_AUTH_PROVIDER` at build time
- Firebase provider: [lib/auth/firebase-provider.ts](unified-trading-system-ui/lib/auth/firebase-provider.ts) — signs
  in + reads custom claims → maps to entitlements
- Demo provider: [lib/auth/demo-provider.ts](unified-trading-system-ui/lib/auth/demo-provider.ts) — localStorage-backed
  persona switcher

## Custom claims → entitlements mapping

When an admin assigns entitlements via `/admin/users/[id]/modify` (which hits
[app/api/v1/users/[uid]/route.ts](unified-trading-system-ui/app/api/v1/users/%5Buid%5D/route.ts) PUT, served by Admin
SDK + Firestore), Firebase custom claims are set on the user's token. The UI reads those claims and renders the services
portal sliced to match. See [cross-cutting/visibility-slicing.md](../cross-cutting/visibility-slicing.md) for the full
mechanism.

The legacy `user-management-api` Cloud Run service that previously did this work is retired as of 2026-04-25. Its source
is preserved at `archive/user-management-api-2026-04-25/` for reference but is **not the system of record** — all admin
operations route through the native `/api/v1/*` Next.js handlers in the portal.

## Related

- [../cross-cutting/fund-org-hierarchy.md](../cross-cutting/fund-org-hierarchy.md) — who can set up whom
- [../cross-cutting/visibility-slicing.md](../cross-cutting/visibility-slicing.md) — what sliced entitlements look like
  in the UI
- [../playbooks/03-warm-prospect-demo.md](../playbooks/03-warm-prospect-demo.md) — demo-persona provisioning flow

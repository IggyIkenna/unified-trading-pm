---
scope: [engineer, admin]
---

# Authentication — three tiers

> **Layer:** Implementation. Narrative lives in [../experience/](../experience/).

Odum uses three distinct auth mechanisms, each scoped to a different audience and risk level.

| Tier | Name                 | Provider                                             | Risk level                          | Audience                                            | Route gate                              |
| ---- | -------------------- | ---------------------------------------------------- | ----------------------------------- | --------------------------------------------------- | --------------------------------------- |
| 1    | Light briefings auth | Custom password gate (no Firebase)                   | Low — keeps casual visitors out     | Post-first-call prospect                            | `/briefings/*`                          |
| 2    | Firebase staging     | Staging Firebase project (isolated from prod)        | Medium — demo data only             | Demo-account prospect, Odum internal during staging | `(platform)/*` on `odum-research.co.uk` |
| 3    | Firebase production  | Production Firebase project `central-element-323112` | High — real capital, real reporting | Paying client, Odum internal in production          | `(platform)/*` on `odum-research.com`   |

See sibling docs:

- [light-auth-briefings.md](light-auth-briefings.md)
- [firebase-staging.md](firebase-staging.md)
- [firebase-production.md](firebase-production.md)

## Current state (2026-04-19)

- Light briefings auth: ✅ live via [lib/briefings/session.ts](unified-trading-system-ui/lib/briefings/session.ts) and
  [components/briefings/briefing-access-gate.tsx](unified-trading-system-ui/components/briefings/briefing-access-gate.tsx).
- Firebase production: ✅ live (single Firebase project `central-element-323112`).
- **Firebase staging: NOT yet provisioned as a separate project** — tracked in
  [five_space_ia_execution_child_plan_2026_04_17.md](../../../plans/active/five_space_ia_execution_child_plan_2026_04_17.md)
  ticket #12. Until that ships, staging uses demo-provider auth with the same 5 personas as local dev.

## Demo personas (local + staging demo mode)

Canonical fixtures in [lib/auth/personas.ts](unified-trading-system-ui/lib/auth/personas.ts). Password for all demo
personas is `"demo"` (client-side only — never used for production data).

| Persona id         | Email                           | Role     | Org              | Use case                                      |
| ------------------ | ------------------------------- | -------- | ---------------- | --------------------------------------------- |
| `admin`            | admin@odum.internal             | admin    | Odum Internal    | Full system admin — sees everything           |
| `internal-trader`  | trader@odum.internal            | internal | Odum Internal    | Internal trading desk — all platform features |
| `client-full`      | pm@alphacapital.com             | client   | Alpha Capital    | External client, full subscription            |
| `client-data-only` | analyst@betafund.com            | client   | Beta Fund        | External client, minimal data tier            |
| `client-premium`   | cio@vertex.com                  | client   | Vertex Partners  | Premium execution client                      |
| `investor`         | investor@odum-research.co.uk    | client   | Odum IR          | Investor / board member                       |
| `advisor`          | advisor@odum-research.co.uk     | client   | Odum IR          | Strategic advisor                             |
| `prospect-im`      | prospect-im@odum-research.co.uk | client   | (TBD — demo org) | Demo-account prospect, IM flavour             |

**Gap**: `prospect-dart` and `prospect-reg` personas do not yet exist. Add in follow-up when pb3c and pb3a are wired.
Tracked in [../roadmap/next-waves.md](../roadmap/next-waves.md).

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

In production, the user-management-api sets Firebase custom claims on the user token when an admin assigns entitlements.
The UI reads those claims and renders the services portal sliced to match. See
[cross-cutting/visibility-slicing.md](../cross-cutting/visibility-slicing.md) for the full mechanism.

## Related

- [../cross-cutting/fund-org-hierarchy.md](../cross-cutting/fund-org-hierarchy.md) — who can set up whom
- [../cross-cutting/visibility-slicing.md](../cross-cutting/visibility-slicing.md) — what sliced entitlements look like
  in the UI
- [../playbooks/03-warm-prospect-demo.md](../playbooks/03-warm-prospect-demo.md) — demo-persona provisioning flow

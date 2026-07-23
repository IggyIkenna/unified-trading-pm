---
doc_type: codex-ssot
title: Playbook 3 — Warm-prospect demo on staging
summary:
  "pb3 implementation — dedicated staging demo account in three flavours (pb3a Reg Umbrella + pb3b IM share one
  reports-only walkthrough; pb3c DART exposes the full 4-catalogue + research/trading/observe surface);
  visibility-slicing table + 8-step admin provisioning flow."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [customer-journey, playbook, demo, visibility-slicing, entitlements, staging, personas]
related:
  [
    /codex/14-customer-journeys/playbooks/01-marketing-pre-first-call.md,
    /codex/14-customer-journeys/playbooks/02-research-and-documentation.md,
    /codex/14-customer-journeys/playbooks/03a-demo-reg-umbrella.md,
    /codex/14-customer-journeys/playbooks/03b-demo-im.md,
    /codex/14-customer-journeys/playbooks/03c-demo-dart.md,
    ../playbook-concepts/visibility-slicing.md,
  ]
created: 2026-04-19
authoritative_for: [pb3 warm-prospect staging demo playbook implementation (flavour split + slicing table)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/authentication/README.md,
    /codex/14-customer-journeys/authentication/firebase-staging.md,
    /codex/14-customer-journeys/environments/staging-odum-research-co-uk.md,
    /codex/14-customer-journeys/experience/staging-demo-journey.md,
    /codex/14-customer-journeys/playbooks/02-research-and-documentation.md,
    /codex/14-customer-journeys/playbooks/03a-demo-reg-umbrella.md,
    /codex/14-customer-journeys/playbooks/03b-demo-im.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Playbook 3 — Warm-prospect demo on staging

> **Layer:** Implementation. Narrative lives in
> [experience/staging-demo-journey.md](../experience/staging-demo-journey.md).

## Who this is for

A prospect who has had multiple calls, read the briefings, and committed to seeing the product in action. Odum
provisions a **dedicated demo account** for them on staging, scoped to the flavour(s) of interest. The demo experience
is sliced to what Odum wants to show them — not a tour of everything.

## Pre-req state

- Prospect has gone through pb1 and pb2 (or equivalent sales process)
- Odum admin has provisioned a staging Firebase user, org, fund, client(s), entitlements — per
  [../authentication/firebase-staging.md](../authentication/firebase-staging.md)
- Prospect has welcome email with staging URL + credentials

## Three flavours (mutually non-exclusive)

| Flavour             | Route focus                                                                       | Demo persona          | Sub-playbook                                         |
| ------------------- | --------------------------------------------------------------------------------- | --------------------- | ---------------------------------------------------- |
| pb3a — Reg Umbrella | Services portal → client-reporting only (all other services locked)               | `prospect-reg` (TBD)  | [03a-demo-reg-umbrella.md](03a-demo-reg-umbrella.md) |
| pb3b — IM           | Services portal → client-reporting only (all other services locked, SAME AS pb3a) | `prospect-im`         | [03b-demo-im.md](03b-demo-im.md)                     |
| pb3c — DART         | Services portal → full 4-catalogue surface + research + trading + observe         | `prospect-dart` (TBD) | [03c-demo-dart.md](03c-demo-dart.md)                 |

**pb3a and pb3b share the same UI walkthrough.** Both land on the services portal with everything locked except
client-reporting. Both pick SMA vs Pooled. Both create funds + clients. The only difference is the **narrative framing**
during the demo call (Odum sales explains the same screens under an IM lens vs a Reg Umbrella lens). This is explicit —
per the user: "investment management (all the same as reg umbrella / coverage same features same reporting)."

pb3c is structurally different: DART shows the four-catalogue surface, research, trading, observation — no
lock-everything-except-reporting posture.

## Canonical click path (shared across flavours)

```
Email link → odum-research.co.uk
    ↓
/login (Firebase staging)
    ↓ (enter demo credentials)
/dashboard (services portal landing)
    ↓ (see entitlement-sliced service tiles)
    ↓ For pb3a / pb3b:
    → /services/reports/overview (client reporting — primary walkthrough)
        → pooled-or-SMA picker (landing or settings — TBD routing)
        → fund creation flow
        → client creation flow (with per-client API key generation)
        → performance / invoices / NAV / reconciliation tabs
    ↓ For pb3c:
    → /services/data (Data Catalogue)
    → /services/strategy-catalogue (Strategy Catalogue)
    → /services/research/ml (ML Model Catalogue — route exists; unified surface post-cutover)
    → /services/execution/overview (Execution Algo Catalogue — route exists; unified surface post-cutover)
    → /services/trading/terminal (live trading view)
    → /services/observe/health (observation)
```

## Visibility slicing

THE core mechanism. See [../cross-cutting/visibility-slicing.md](../playbook-concepts/visibility-slicing.md).

| Role                 | What they see                                                                                                                            |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Admin                | EVERYTHING — all services, all catalogues, all tabs                                                                                      |
| Demo prospect (pb3a) | Services portal with all service tiles LOCKED except `/services/reports/*`                                                               |
| Demo prospect (pb3b) | Same as pb3a (by user directive)                                                                                                         |
| Demo prospect (pb3c) | Services portal with Data / Strategy-Catalogue / ML / Execution / Research / Trading / Observe tiles UNLOCKED; client-reporting optional |
| Real client          | Sliced to paid package entitlements                                                                                                      |

Slicing is applied uniformly across:

- Which service cards render on `/dashboard`
- Which tabs render in `service-tabs.tsx` per service
- Which catalogue entries render in each catalogue view (filtered by `lock_state` + `maturity`)
- Which admin surfaces are reachable

## Admin provisioning workflow

Before a prospect can do pb3, an admin must:

1. Sign in to user-management-ui on staging (admin persona)
2. Create organisation for the demo — see
   [../cross-cutting/fund-org-hierarchy.md](../playbook-concepts/fund-org-hierarchy.md)
3. Decide pb3 flavour (IM / DART / Reg Umbrella / combo)
4. Configure entitlements matching the flavour
5. If IM or Reg Umbrella: pre-create the SMA/Pooled state so prospect can see the choice (or pre-lock one side to force
   the other)
6. Create user with prospect's email
7. Trigger Firebase password reset → prospect sets password
8. Send welcome email

See [../authentication/firebase-staging.md](../authentication/firebase-staging.md) for the full 10-step flow.

## Exit state

- **Commits as paying client** → Odum ops creates real Firebase production user + corresponding real org in production
  user-management-ui → pb3 done, prospect becomes real client
- **Wants to refine demo** → admin adjusts entitlements, prospect continues demo
- **Drops** → admin deactivates demo user; staging data archived (not deleted)

## Orphan concerns

> **[DELTA 2026-05-22]** **Current state:** `prospect-reg` and `prospect-dart` personas do not yet exist in
> `lib/auth/personas.ts`. Entitlement-based slicing hides non-entitled services rather than showing them as
> LOCKED-WITH-MESSAGE. The pooled-or-SMA picker routing is not yet implemented. **Planned delta:** Persona stubs +
> LOCKED-WITH-MESSAGE UI tracked in `/codex/14-customer-journeys/roadmap/next-waves.md`. **Target:** post-cutover UI
> unification phase.

- No `prospect-reg` or `prospect-dart` persona exists yet in
  [lib/auth/personas.ts](unified-trading-system-ui/lib/auth/personas.ts) — tracked in
  [../roadmap/next-waves.md](../roadmap/next-waves.md).
- Entitlement-based slicing mechanism exists (via [lib/config/auth.ts](unified-trading-system-ui/lib/config/auth.ts) +
  [components/shell/lifecycle-nav.tsx](unified-trading-system-ui/components/shell/lifecycle-nav.tsx)) but does NOT yet
  support per-service "LOCKED with message" UI — it hides. For pb3a/pb3b the user wants LOCKED (with a "contact us to
  unlock" message), not hidden. Tracked in roadmap.

## Test coverage

- Playwright spec: `unified-trading-system-ui/tests/playbooks/warm-prospect-demo.spec.ts`
- Per-flavour sub-specs in `tests/playbooks/03a-reg-umbrella.spec.ts`, `03b-im.spec.ts`, `03c-dart.spec.ts`
- Visibility-slicing cross-test in `tests/playbooks/visibility-slicing.spec.ts` — parameterised over all personas

## Related

- pb1: [01-marketing-pre-first-call.md](01-marketing-pre-first-call.md)
- pb2: [02-research-and-documentation.md](02-research-and-documentation.md)
- Auth: [../authentication/firebase-staging.md](../authentication/firebase-staging.md)
- Slicing mechanism: [../cross-cutting/visibility-slicing.md](../playbook-concepts/visibility-slicing.md)
- Shared reporting (pb3a+pb3b): [../cross-cutting/client-reporting.md](../playbook-concepts/client-reporting.md)
- SMA vs Pooled: [../cross-cutting/sma-vs-pooled.md](../playbook-concepts/sma-vs-pooled.md)
- Four catalogues (pb3c): [../cross-cutting/catalogues.md](../playbook-concepts/catalogues.md)

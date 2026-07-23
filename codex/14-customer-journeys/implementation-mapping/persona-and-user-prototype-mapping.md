---
doc_type: codex-ssot
title: Persona and User-Prototype Mapping
summary:
  Maps each experience audience to a named persona fixture in lib/auth/personas.ts (admin, internal-trader, client-*,
  prospect-im/reg/dart, investor, advisor) with its restriction profile, entitlement blocks, and experience-playbook
  binding.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [persona, entitlements, staging, playbook, ui, authentication]
related:
  [
    ../demo-ops/demo-restriction-profiles.md,
    ../demo-ops/demo-decision-matrix.md,
    /codex/14-customer-journeys/implementation-mapping/route-mapping.md,
    /codex/14-customer-journeys/implementation-mapping/demo-email-and-provisioning-flow.md,
    /codex/14-customer-journeys/implementation-mapping/playbook-to-qa-coverage.md,
  ]
created: 2026-04-20
authoritative_for: [persona-fixture mapping (personas.ts -> experience playbook + entitlement blocks)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/implementation-mapping/README.md,
    /codex/14-customer-journeys/implementation-mapping/demo-email-and-provisioning-flow.md,
    /codex/14-customer-journeys/implementation-mapping/playbook-to-qa-coverage.md,
    /codex/14-customer-journeys/implementation-mapping/route-mapping.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Persona and User-Prototype Mapping

> Each experience audience maps to a named persona fixture in `lib/auth/personas.ts`. This doc is the mapping.

## Why persona fixtures

The staging environment uses persona fixtures to simulate different audience entitlements deterministically. Each
fixture is a named user with a known restriction profile attached. Playwright specs sign in as the relevant persona to
exercise the experience path.

The persona fixtures are the bridge between restriction profiles (see
[`../demo-ops/demo-restriction-profiles.md`](../demo-ops/demo-restriction-profiles.md)) and actual UI rendering.

## The persona set

Existing and planned personas (from the user's 2026-04-19 architectural review + Phase 10 UI work):

| Persona id         | Audience                               | Status | Restriction profile                     |
| ------------------ | -------------------------------------- | ------ | --------------------------------------- |
| `admin`            | Odum internal ops / admin              | Exists | All surfaces; admin entitlement         |
| `internal-trader`  | Odum internal trading team             | Exists | All surfaces except ops/admin           |
| `client-full`      | Full-DART client                       | Exists | Full DART profile                       |
| `client-data-only` | Signals-only DART client               | Exists | Signals-only DART profile               |
| `client-premium`   | Full DART + Odum strategy exposure     | Exists | Full DART + Odum strategy profile       |
| `prospect-im`      | Warm-prospect IM allocator (pb3b)      | Exists | IM allocator profile                    |
| `prospect-reg`     | Warm-prospect Reg Umbrella firm (pb3a) | TBD    | Reg Umbrella profile                    |
| `prospect-dart`    | Warm-prospect DART (pb3c)              | TBD    | Signals-only or full DART per fit-check |
| `investor`         | Odum investor (board / IR)             | Exists | Investor-relations profile              |
| `advisor`          | Odum advisor                           | Exists | Advisor profile                         |

`prospect-reg` and `prospect-dart` are planned additions (tracked in the roadmap). `prospect-dart` may split into
`prospect-dart-signals-only` and `prospect-dart-full` per the fit-check resolution — decision deferred to Stage 3E.

## Persona → experience playbook mapping

| Experience playbook                                                                     | Persona(s)                                       |
| --------------------------------------------------------------------------------------- | ------------------------------------------------ |
| [marketing-journey.md](../experience/marketing-journey.md) (pb1)                        | None (public route, no auth)                     |
| [briefings-hub.md](../experience/briefings-hub.md) (pb2)                                | Light-auth code (not a persona)                  |
| [im-decision-journey.md](../experience/im-decision-journey.md) (pb2a)                   | Light-auth code for briefing view                |
| [dart-briefing.md](../experience/dart-briefing.md) (pb2b)                               | Light-auth code for briefing view                |
| [regulatory-umbrella-briefing.md](../experience/regulatory-umbrella-briefing.md) (pb2c) | Light-auth code for briefing view                |
| [staging-demo-journey.md](../experience/staging-demo-journey.md) (pb3)                  | `prospect-im` / `prospect-reg` / `prospect-dart` |
| [regulatory-demo.md](../experience/regulatory-demo.md) (pb3a)                           | `prospect-reg`                                   |
| [investment-management-demo.md](../experience/investment-management-demo.md) (pb3b)     | `prospect-im`                                    |
| [dart-demo.md](../experience/dart-demo.md) (pb3c)                                       | `prospect-dart` (signals-only or full variant)   |

## Persona → entitlement mapping

Each persona has a declared entitlement set (rule 05 blocks + scope). Stage 3B's registry reads these entitlements at
staging-demo-user sign-in time.

| Persona                   | Blocks granted                  | Scope                                                      |
| ------------------------- | ------------------------------- | ---------------------------------------------------------- |
| `prospect-im`             | 1 + 3                           | Public + IM-reserved slots; allocator-mandate-shape filter |
| `prospect-reg`            | 1 + 2 + 7 + 8 + 10              | Public; firm's declared activity                           |
| `prospect-dart` (signals) | 1 + 4 + 5 + 7 + 8 + 9 + 10      | Declared instruction-flow scope; block 6 LOCKED-VISIBLE    |
| `prospect-dart` (full)    | 1 + 4 + 6 + 7 + 8 + 9 + 10 + 11 | Broader scope; iterative                                   |
| `client-full`             | 1 + 4 + 6 + 7 + 8 + 9 + 10 + 11 | Client-specific prod entitlements                          |
| `client-data-only`        | 1 + 4 + 5 + 7 + 8 + 9 + 10      | Client-specific prod entitlements                          |
| `admin`                   | All blocks + admin flag         | All clients; admin routes visible                          |
| `internal-trader`         | 1 + 4 + 6 + 7 + 8 + 9 + 10 + 11 | Odum internal strategies                                   |

## Persona fixture creation

New personas are added through user-management-ui provisioning (see
[`demo-email-and-provisioning-flow.md`](demo-email-and-provisioning-flow.md)). The fixture is captured in
`unified-trading-system-ui/lib/auth/personas.ts` with:

- `id`: short identifier (`prospect-im`).
- `displayName`: human-readable name for staging.
- `email`: a staging email address.
- `entitlement_profile_id`: the restriction profile from
  [`../demo-ops/demo-restriction-profiles.md`](../demo-ops/demo-restriction-profiles.md).
- `demo_mode`: default `turbo` / `broader_platform` / `deep_dive`.

## Cross-references

- [`../demo-ops/demo-restriction-profiles.md`](../demo-ops/demo-restriction-profiles.md) — profile definitions
- [`../demo-ops/demo-decision-matrix.md`](../demo-ops/demo-decision-matrix.md) — which persona per prospect
- [route-mapping.md](route-mapping.md) — routes each persona can see
- [demo-email-and-provisioning-flow.md](demo-email-and-provisioning-flow.md) — persona creation flow
- [playbook-to-qa-coverage.md](playbook-to-qa-coverage.md) — Playwright specs sign in as personas
- [`../shared-core/org-fund-client-entity-model.md`](../shared-core/org-fund-client-entity-model.md) — entity hierarchy
  personas operate within
- `unified-trading-system-ui/lib/auth/personas.ts` — canonical persona registry

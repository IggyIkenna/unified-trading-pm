---
doc_type: codex-ssot
title: Playbook-to-QA Coverage
summary:
  Coverage matrix binding every experience playbook (pb1-pb3c) to its Playwright spec under tests/e2e/playbooks/; each
  spec asserts the walkthrough routes, persona restriction profile, catalogue filters, the desired next step, and no
  entitlement leak.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [playbook, testing, playwright, ui, coverage, persona]
related:
  [
    /codex/14-customer-journeys/implementation-mapping/route-mapping.md,
    /codex/14-customer-journeys/implementation-mapping/persona-and-user-prototype-mapping.md,
    /codex/14-customer-journeys/implementation-mapping/demo-email-and-provisioning-flow.md,
    ../demo-ops/demo-restriction-profiles.md,
  ]
created: 2026-04-20
authoritative_for: [experience-playbook -> Playwright-spec coverage matrix]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/implementation-mapping/README.md,
    /codex/14-customer-journeys/implementation-mapping/persona-and-user-prototype-mapping.md,
    /codex/14-customer-journeys/implementation-mapping/route-mapping.md,
    /codex/14-customer-journeys/shared-core/client-reporting-demo-walkthrough.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Playbook-to-QA Coverage

> Every experience playbook maps to a Playwright spec under `unified-trading-system-ui/tests/e2e/playbooks/`. Red rows =
> spec not yet written.

## Why this matters

Rule 01 §Cross-section consistency and §Enforcement rule 3 require engineering traceability via Playwright specs. Each
experience playbook's §5 walkthrough path and §8 exit are asserted by the spec. When a playbook changes, the spec
updates in the same PR; when a spec changes, the playbook updates in the same PR.

Without this mapping, specs drift out of sync with the narrative; with it, the chain holds.

## Coverage matrix

| Playbook                                                                                | Playwright spec                                                         | Status                                    |
| --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------- |
| [marketing-journey.md](../experience/marketing-journey.md) (pb1)                        | `tests/e2e/playbooks/marketing.spec.ts`                                 | Exists (updated per 2026-04-19 roadmap)   |
| [briefings-hub.md](../experience/briefings-hub.md) (pb2)                                | `tests/e2e/playbooks/research-and-docs.spec.ts`                         | Exists                                    |
| [im-decision-journey.md](../experience/im-decision-journey.md) (pb2a)                   | `tests/e2e/playbooks/research-and-docs.spec.ts` (IM reader persona)     | Exists                                    |
| [dart-briefing.md](../experience/dart-briefing.md) (pb2b)                               | `tests/e2e/playbooks/research-and-docs.spec.ts` (DART reader persona)   | Updated pending fit-check section         |
| [regulatory-umbrella-briefing.md](../experience/regulatory-umbrella-briefing.md) (pb2c) | `tests/e2e/playbooks/research-and-docs.spec.ts` (Reg Umbrella reader)   | Exists                                    |
| [staging-demo-journey.md](../experience/staging-demo-journey.md) (pb3)                  | `tests/e2e/playbooks/warm-prospect-demo.spec.ts`                        | Exists                                    |
| [regulatory-demo.md](../experience/regulatory-demo.md) (pb3a)                           | `tests/e2e/playbooks/warm-prospect-demo.spec.ts` (Reg Umbrella persona) | Exists (persona: `prospect-reg` pending)  |
| [investment-management-demo.md](../experience/investment-management-demo.md) (pb3b)     | `tests/e2e/playbooks/warm-prospect-demo.spec.ts` (IM persona)           | Exists                                    |
| [dart-demo.md](../experience/dart-demo.md) (pb3c)                                       | `tests/e2e/playbooks/warm-prospect-demo.spec.ts` (DART persona)         | Exists (persona: `prospect-dart` pending) |

Plus cross-cutting / shared specs:

| Concept                                                         | Playwright spec                                                      |
| --------------------------------------------------------------- | -------------------------------------------------------------------- |
| Visibility slicing (admin-sees-all / demo-sliced / prod-sliced) | `tests/e2e/playbooks/visibility-slicing.spec.ts`                     |
| Client reporting demo walkthrough (shared pb3a + pb3b)          | Asserted by `warm-prospect-demo.spec.ts` via shared-core walkthrough |

## What each spec asserts

Minimum assertions per playbook spec:

1. **§5 Walkthrough click-path holds.** Every route referenced in the walkthrough renders (HTTP 200 + expected DOM).
2. **Persona restriction profile is respected.** LOCKED-VISIBLE surfaces render with the locked chip; HIDDEN-ENTIRELY
   surfaces do not appear in the nav tree.
3. **Catalogue filter applies.** Maturity filter, strategy-family filter, scope filter all produce the expected slot
   set.
4. **§8 Desired next step is reachable.** The button / calendar link that closes the session is present and works.
5. **No entitlement leak.** An audit of data queries confirms no other clients' data appears.

## Coverage gaps

- **`prospect-reg` persona fixture** is TBD (see
  [`persona-and-user-prototype-mapping.md`](persona-and-user-prototype-mapping.md)). Once created, pb3a tests target
  this persona explicitly.
- **`prospect-dart` persona fixture** is TBD; may split into `prospect-dart-signals-only` and `prospect-dart-full`.
  Decision deferred to Stage 3E.
- **`visibility-slicing.spec.ts` LOCKED-VISIBLE mode** — roadmap item tracked in
  [`../roadmap/next-waves.md`](../roadmap/next-waves.md) (superseded by Stage 3E refactor plan).

## Update discipline

When an experience playbook changes:

- **Added route.** The spec must cover it; new assertion added.
- **Removed route.** The spec's assertion on that route is removed.
- **Changed restriction profile.** The spec's LOCKED-VISIBLE / HIDDEN-ENTIRELY assertions update.
- **Changed next-step.** The §8 assertion updates.

When a spec fails:

- **Route gone** → determine if it's a rule-03 consolidation. Update the playbook + spec + route-mapping together.
- **Component changed** → update the spec assertion to match the new component.
- **Restriction leak** → rule-06 violation, log to compliance audit trail + fix.

## Stage 3 relationship

Stage 3E's refactor plan identifies Playwright specs that need consolidation (multiple specs asserting the same rule-03
same-system surface). When Stage 3E lands, this coverage matrix updates.

## Cross-references

- [`../experience/`](../experience/) — every playbook
- [route-mapping.md](route-mapping.md) — routes the specs exercise
- [persona-and-user-prototype-mapping.md](persona-and-user-prototype-mapping.md) — personas the specs sign in as
- [demo-email-and-provisioning-flow.md](demo-email-and-provisioning-flow.md) — provisioning the specs depend on
- [`../demo-ops/demo-restriction-profiles.md`](../demo-ops/demo-restriction-profiles.md) — profiles the specs assert
  against
- `unified-trading-system-ui/tests/e2e/playbooks/` — spec files

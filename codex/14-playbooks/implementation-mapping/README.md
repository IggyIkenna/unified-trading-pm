# `implementation-mapping/` — Bridge narrative → code

Per-surface, per-persona, per-route mappings that tie the narrative experience playbooks to concrete engineering
artifacts. Drives Playwright spec coverage and provisioning automation.

## Contents

| File                                                                           | Purpose                                                           |
| ------------------------------------------------------------------------------ | ----------------------------------------------------------------- |
| [route-mapping.md](route-mapping.md)                                           | Every experience-playbook section → concrete UI route             |
| [persona-and-user-prototype-mapping.md](persona-and-user-prototype-mapping.md) | Each audience → persona fixture in `lib/auth/personas.ts`         |
| [demo-email-and-provisioning-flow.md](demo-email-and-provisioning-flow.md)     | Sales "book demo" click → user-management-ui provisioning + email |
| [playbook-to-qa-coverage.md](playbook-to-qa-coverage.md)                       | Each experience playbook → matching Playwright spec               |

## Why this layer exists

Experience docs describe what the audience experiences. Impl-layer docs describe routes, services, entitlements. The
implementation-mapping dir is the bridge: it traces every narrative beat to a concrete artifact so engineering can find
what to build, test, and maintain.

Without the bridge, experience docs drift from the UI and the Playwright specs drift from both. The mapping structure
forces the chain to hold.

## Stage 3 relationship

Stage 3B's UAC combo registry carries the route identifiers referenced here. Stage 3C's derivation engine reads the
persona mapping to compute `access_control(user, route, item, phase)` per audience. Stage 3E's refactor plan uses the
route-mapping to identify consolidation targets (multiple routes that should be one rule-03 same-system surface).

## Cross-references

- [`../_ssot-rules/`](../_ssot-rules/)
- [`../experience/`](../experience/) — experience docs reference routes and personas from here
- [`../demo-ops/`](../demo-ops/) — restriction profiles reference the entitlement registry
- [`../infra-spec/`](../infra-spec/) — Stage 3 infra spec consumes the identifiers here
- [`../../00-SSOT-INDEX.md`](../../00-SSOT-INDEX.md)

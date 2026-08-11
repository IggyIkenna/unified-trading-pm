---
doc_type: codex-ssot
title: Test matrix — playbook × persona × environment
summary:
  The Playwright test-spec inventory — maps each playbook (pb1..pb3c + visibility-slicing) to its spec file, primary +
  other personas, and environments (local/static/staging-smoke), plus the expected assertions per spec and the
  parametrised 10-persona visibility-slicing matrix. Staging specs deferred until staging Firebase is provisioned.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: [ui, testing, playwright, personas, customer-journeys, visibility-slicing]
[/codex/14-customer-journeys/testing/example-playbook-test.md, /codex/14-customer-journeys/testing/README.md, ../authentication/README.md]
created: 2026-04-19
authoritative_for: [Playwright test-spec matrix (spec x persona x environment)]
referenced_by:
  [
    /codex/06-coding-standards/ui-testing-layers.md,
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/playbooks/README.md,
    /codex/14-customer-journeys/roadmap/plan-references.md,
    /codex/14-customer-journeys/testing/README.md,
    /codex/14-customer-journeys/testing/example-playbook-test.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Test matrix — playbook × persona × environment

| Playbook                 | Spec file                            | Primary persona              | Other personas tested      | Environments                              |
| ------------------------ | ------------------------------------ | ---------------------------- | -------------------------- | ----------------------------------------- |
| pb1 — Marketing          | `marketing-pre-first-call.spec.ts`   | anonymous                    | —                          | local, static                             |
| pb2 — Briefings hub      | `research-and-documentation.spec.ts` | anonymous → briefings-authed | —                          | local, static                             |
| pb2a — IM briefing       | `02a-research-im.spec.ts`            | briefings-authed             | —                          | local, static                             |
| pb2b — DART briefing     | `02b-research-dart.spec.ts`          | briefings-authed             | —                          | local, static                             |
| pb2c — Reg briefing      | `02c-research-regulatory.spec.ts`    | briefings-authed             | —                          | local, static                             |
| pb3 — Demo hub           | `warm-prospect-demo.spec.ts`         | `prospect-im`                | all prospect personas      | local (tier 1 for backend), staging-smoke |
| pb3a — Reg Umbrella demo | `03a-reg-umbrella.spec.ts`           | `prospect-reg` (TBD)         | `admin` (visibility check) | local                                     |
| pb3b — IM demo           | `03b-im.spec.ts`                     | `prospect-im`                | `admin`                    | local                                     |
| pb3c — DART demo         | `03c-dart.spec.ts`                   | `prospect-dart` (TBD)        | `admin`                    | local                                     |
| Visibility slicing cross | `visibility-slicing.spec.ts`         | parametrised                 | all 8 personas             | local                                     |

## Expected assertions per spec

### `marketing-pre-first-call.spec.ts`

1. `/` renders 200
2. All top-nav links resolve 200
3. Three service cards navigate correctly
4. Footer links resolve
5. "Sign In" → `/login`
6. Spaces dropdown shows public items only for anonymous user
7. No auth gate appears

### `research-and-documentation.spec.ts`

1. `/briefings` redirects to gate when no session
2. Correct access code → content renders
3. Three pillar tiles → 3 sub-briefings
4. localStorage clear → gate reappears
5. Wrong code → rejection

### `02a-research-im.spec.ts`, `02b-*.spec.ts`, `02c-*.spec.ts`

1. Sub-briefing renders all sections
2. Cross-links between sub-briefings work
3. "Book a Demo" CTA has correct flavour context

### `warm-prospect-demo.spec.ts`

1. Sign-in flow works for each prospect persona
2. Dashboard renders with correct tiles (unlocked/locked) per persona
3. Direct URL to locked page → redirect or locked state
4. Admin persona sees ALL tiles unlocked

### `03a-reg-umbrella.spec.ts` / `03b-im.spec.ts`

These specs share a helper (`walkClientReportingFlow`) since pb3a and pb3b are UI-identical:

1. Sign in as prospect persona
2. Lands on `/dashboard`
3. All service tiles except Reports are padlocked
4. Navigate to `/services/reports/overview` → renders
5. Complete Pooled-vs-SMA pick
6. Complete fund creation
7. Complete client creation with API key display
8. Reports sub-tabs all reachable

### `03c-dart.spec.ts`

1. Sign in as `prospect-dart`
2. Lands on `/dashboard`
3. Service tiles: Data, Research, Promote, Trading, Observe UNLOCKED; Admin LOCKED; Reports OPTIONAL
4. Navigate each of 4 catalogues
5. Strategy catalogue coverage matrix renders archetypes
6. DART trading terminal loads

### `visibility-slicing.spec.ts` (parametrised)

For each persona in
`['admin', 'internal-trader', 'client-full', 'client-data-only', 'client-premium', 'prospect-im', 'prospect-dart', 'prospect-reg', 'investor', 'advisor']`:

1. Expected service tiles visible vs padlocked vs hidden
2. Expected tabs within services
3. Expected catalogue entries (lock_state + maturity filtered)
4. Expected admin surfaces (admin only)

## Future: staging tests

When staging Firebase is provisioned (tracked in [../roadmap/next-waves.md](../roadmap/next-waves.md)), add:

- `tests/playbooks/staging/warm-prospect-demo.spec.ts` — runs against `odum-research.co.uk` with a dedicated
  test-prospect persona, exercises the full Firebase auth loop + demo-user provisioning API

## Related

- Testing README: [README.md](README.md)
- Personas: [../authentication/README.md](../authentication/README.md)

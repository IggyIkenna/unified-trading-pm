---
doc_type: codex-ssot
title: Commercial Service Families — DART Full vs Signals-In (+ IM, Reg Umbrella)
summary:
  "Commercial/UX service-family SSOT: the four shapes (IM, Reg Umbrella, DART Signals-In, DART Full), the DART Full vs
  Signals-In feature matrix, locked-section UI design, and the demo plan toggle. NOT the architecture-tier doc."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [commercial, dart, service-families, ui, entitlements, demo, sales]
related:
  [
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/04-architecture/runtime-deployment-topology.md,
    /codex/06-coding-standards/strategy-display-conventions.md,
    /codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md,
  ]
created: 2026-04-24
authoritative_for: [commercial service families (DART Full vs Signals-In feature matrix, IM, Reg Umbrella)]
referenced_by:
  [
    /codex/02-data/questionnaire-axes.md,
    /codex/04-architecture/runtime-deployment-topology.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/06-coding-standards/strategy-display-conventions.md,
    /codex/06-coding-standards/terminology-ssot.md,
    /codex/08-workflows/client-onboarding.md,
    /codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md,
    /codex/09-strategy/architecture-v2/strategy-questionnaire-mapping.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Commercial Service Families — DART Full vs Signals-In (+ IM, Reg Umbrella)

> **Created 2026-05-08** (Phase E.1 of `plans/active/codex_refactor_2026_05_08.md`) — renamed from
> `service-family-scope.md`. The rename clarifies scope: this doc is the **commercial / UX** service-family SSOT (which
> commercial shape is sold to whom, what feature matrix each tier unlocks, locked-section UI design, demo plan toggle).
> It is NOT an architecture-tier doc — for the import-tier model + protocol-injection contract see
> [`tier-and-import-architecture.md`](tier-and-import-architecture.md); for runtime / deployment topology see
> [`runtime-deployment-topology.md`](runtime-deployment-topology.md).

> **Status:** canonical (2026-04-24, renamed 2026-05-08) **Owner:** UI Architecture + Sales **SSOT for:** DART Full vs
> Signals-In feature matrix, locked-section design, DemoPlanToggle; UI consumers:
> `unified-trading-system-ui/components/shell/service-tabs.tsx`,
> `unified-trading-system-ui/app/(platform)/services/dart/locked/page.tsx`,
> `unified-trading-system-ui/components/demo/DemoPlanToggle.tsx`,
> `unified-trading-system-ui/app/(public)/briefings/[slug]/page.tsx`. **Plan:**
> [`../../plans/archive/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md`](../../plans/archive/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md)
> **Companion docs:**
> [`/codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md`](/codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md)
> (rule 12 — machine-readable route allowlist per family),
> [`/codex/06-coding-standards/strategy-display-conventions.md`](/codex/06-coding-standards/strategy-display-conventions.md)
> (plan-tier classification),
> [`/codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md`](/codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md)
> (§14 tier badge rendering).

---

## §1 — The four commercial shapes

Odum ships four commercial service families. The boundary is **commercial reality + regulatory fit**, not ACL —
different families buy different outcomes, not different permission lists.

| Family                   | Buys                                                                               | Operates                                                                  |
| ------------------------ | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **IM (Investment Mgmt)** | Odum runs capital; client receives capital + reporting                             | Reporting + investor relations surfaces                                   |
| **Reg Umbrella**         | Emerging manager operates under Odum's FCA permissions                             | Reporting + compliance overlay (AR / AIFM-delegated shapes — see §5)      |
| **DART Signals-In**      | Client brings strategy; Odum runs execution + reporting; client keeps strategy IP  | Execution + reporting + data + observe                                    |
| **DART Full**            | Client uses Odum's full Research + Promote + Trading + Observe + Reports lifecycle | Everything DART Signals-In unlocks, plus Research (ML backtest) + Promote |

Rule 12
([`/codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md`](/codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md))
is the machine-readable route-allowlist table UAC uses to enforce this at access-control time.

---

## §2 — DART Full vs Signals-In feature matrix

Both tiers share the **same strategy catalogue**. The universe of instances visible in FOMO is identical. What differs
is which capabilities the tier unlocks.

| Feature                      | DART Signals-In | DART Full |
| ---------------------------- | --------------- | --------- |
| P&L dashboard                | ✓               | ✓         |
| Positions & terminal         | ✓               | ✓         |
| Strategy observe / alerts    | ✓               | ✓         |
| Signal intake webhook        | ✓               | —         |
| ML backtesting               | —               | ✓         |
| Strategy customisation       | —               | ✓         |
| Promote-to-live workflow     | —               | ✓         |
| Feature engineering pipeline | —               | ✓         |

This matrix is rendered literally on `/briefings/dart-signals-in` via `<DartTierComparisonTable>` (Phase 7.4 of the DART
UI plan; see `app/(public)/briefings/[slug]/page.tsx`). Edits here must be mirrored in the table component.

**4 Full-only archetypes** — ML-dependent or event-model-dependent code paths: `ML_DIRECTIONAL_CONTINUOUS`,
`ML_DIRECTIONAL_EVENT_SETTLED`, `EVENT_DRIVEN`, `VOL_TRADING_OPTIONS`. See
[`/codex/06-coding-standards/strategy-display-conventions.md`](/codex/06-coding-standards/strategy-display-conventions.md)
§5 for the authoritative plan-tier classification; see
[`/codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md`](/codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md)
§14 for how the classification surfaces on FOMO cards.

---

## §3 — Locked-section design

Two routes in the DART service family require `strategy-full` + `ml-full` entitlements. Both are declared in
`components/shell/service-tabs.tsx` TRADING_TABS with `requiredEntitlement: "strategy-full"`:

- **Strategy Config** — `/services/trading/strategy-config` (ML backtest + authoring)
- **Deployment** — `/services/trading/deployment` (promote + runtime-profile + kill-switch)

When a client without `strategy-full` views the DART tab row:

1. If `lockedRedirectTo` is set on the tab, the tab renders as a `<Link>` to the redirect URL (not a cursor-not-allowed
   span). This lets the client navigate to the upgrade surface instead of hitting a dead-end tooltip.
2. Both Strategy Config and Deployment set `lockedRedirectTo: "/services/dart/locked?from=<section>"` (`<section>` =
   `research` for Strategy Config, `promote` for Deployment).

### `/services/dart/locked` — the upgrade surface

Landing page for clients who click a locked tab. Structure:

- **Section-specific copy.** Reads `?from=` query param. `research` → copy about Research + ML backtest; `promote` →
  copy about Promote + kill-switch. Default fallback copy if no `from=` param.
- **Primary CTA — Upgrade.** `/contact?service=dart-full&action=upgrade` (pathname-aware contact prefill — see
  `lib/marketing/contact-link.ts`). Telegram follow-up goes to Ikenna.
- **Secondary CTA — Browse catalogue.** `/services/strategy-catalogue?tab=explore` — keeps the client on the Explore tab
  where they already have full visibility.
- **DemoPlanToggle (demo mode only).** When `NEXT_PUBLIC_AUTH_PROVIDER === "demo"`, renders inline so the prospect can
  self-toggle to the paired Full persona and see what upgrade actually unlocks. Not visible in production mode.

---

## §4 — Demo plan toggle

**Rationale.** Two client shapes come up repeatedly: (a) prospects evaluating Signals-In vs Full as a commercial
decision, and (b) existing Signals-In clients considering upgrade. Both benefit from self-discovery of the difference
rather than a sales-narrated walkthrough. The `DemoPlanToggle` component gives them an inline toggle that swaps
persona-under-demo between paired Base and Full tiers, so they can click through the same surfaces and see what changes.

**Implementation.** `components/demo/DemoPlanToggle.tsx`:

- Renders only when `NEXT_PUBLIC_AUTH_PROVIDER === "demo"`. In production Firebase-auth mode, returns `null`.
- Mounted in `components/shell/lifecycle-nav.tsx` before the org-display button, so it's always visible in the nav.
- Consults a `TOGGLE_MAP` to find the paired persona for the current user:
  - `desmond-dart-full` ↔ `desmond-signals-in`
  - `{defi-client-slug}-defi-full` ↔ `{defi-client-slug}-defi`
- On click, calls `loginByEmail(pairedPersonaId, "")` — `DemoAuthProvider` accepts persona IDs directly in its
  `loginByEmail` signature for this flow (password param ignored when credential matches a known persona id).
- Tier styling: emerald for the Full tier, amber for the Base / Signals-In tier. Visible tier label rendered next to the
  toggle.

**Persona naming convention.** Every demo-client with a plan-toggle pairing uses the suffix pattern:

```
{client-slug}-dart-full       (the unlocked upgrade preview)
{client-slug}-signals-in      (the base / entry tier)
```

For DeFi-first shapes (DeFi-allocator client):

```
{client-slug}-defi-full       (upgrade preview)
{client-slug}-defi            (base)
```

Both personas share the same email address; `getPersonaByEmail()` returns the first match on real email login (default:
the Full tier for the Desmond shape), and the toggle swaps by persona id via `getPersonaById()`. This is intentional —
the client logs in once with their real email and toggles tiers from inside the session without re-authenticating.

---

## §5 — Reg Umbrella & IM scope (brief)

**IM** (Odum-run funds) — reporting + investor-relations tiles; no observe / research / promote. Client sees returns and
capital statements.

**Reg Umbrella** — reporting + compliance-overlay tiles; no observe / research / promote. Emerging manager operates
customer-facing activity under Odum's FCA permissions (typically via AR or IM-delegation shape — see
[`/codex/14-customer-journeys/experience/regulatory-umbrella-briefing.md`](/codex/14-customer-journeys/experience/regulatory-umbrella-briefing.md)
for the four-axis structure × scope × counterparty-facing × activity model).

For both IM and Reg Umbrella, the DART feature matrix (§2) does not apply — they run a different surface set and
typically don't see the strategy catalogue at all. Rule 12 enforces the route-allowlist boundary.

---

## §6 — Cross-references

- [`/codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md`](/codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md)
  — machine-readable YAML; UAC-enforced at `access_control()`.
- [`/codex/14-customer-journeys/demo-ops/staging-demo-setup.md`](/codex/14-customer-journeys/demo-ops/staging-demo-setup.md)
  — operator checklist for provisioning a new demo client pair (Base + Full personas + questionnaire preseed + profile
  YAML).
- [`../14-customer-journeys/demo-ops/profiles/desmond-dart-full.yaml`](../14-customer-journeys/demo-ops/profiles/desmond-dart-full.yaml)
  - [`desmond-signals-in.yaml`](../14-customer-journeys/demo-ops/profiles/desmond-signals-in.yaml) — canonical worked
    example (real client).
- [`/codex/08-workflows/client-onboarding.md`](/codex/08-workflows/client-onboarding.md) — 7-step sequence in which this
  matrix is exposed to the prospect (step 4 exploration, step 6 call).
- [`/codex/06-coding-standards/strategy-display-conventions.md`](/codex/06-coding-standards/strategy-display-conventions.md)
  §5 — plan-tier classification driving the tier badges.
- [`/codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md`](/codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md)
  §14 — FOMO tier badges + Signals-In upgrade banner.
- [`tier-and-import-architecture.md`](tier-and-import-architecture.md) — import-tier model + protocol-injection contract
  (architecture-tier scoping, distinct from this doc's commercial scoping).
- [`runtime-deployment-topology.md`](runtime-deployment-topology.md) — runtime + deployment topology (cluster shapes,
  service interactions, message flows).

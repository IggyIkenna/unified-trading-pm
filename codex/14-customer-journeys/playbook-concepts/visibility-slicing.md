---
doc_type: codex-ssot
title: Visibility slicing — the core model
summary:
  "SSOT for the visible(user, item) filter unifying role × entitlements × catalogue lock_state × maturity × org_scope
  into one rule applied across every UI surface; four slicing dimensions + per-role/persona visible-set examples +
  dashboard tile/chip slicing."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [customer-journey, visibility-slicing, entitlements, ui, personas, catalogues, dashboard]
related:
  [
    /codex/14-customer-journeys/playbook-concepts/catalogue-strategy.md,
    /codex/14-customer-journeys/playbook-concepts/catalogues.md,
    /codex/14-customer-journeys/playbook-concepts/fund-org-hierarchy.md,
    ../../09-strategy/architecture-v2/dashboard-services-grid.md,
    ../roadmap/next-waves.md,
  ]
created: 2026-04-19
authoritative_for: [visibility-slicing model (visible(user, item) filter across UI surfaces)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
    /codex/14-customer-journeys/_ssot-rules/11-codex-scope-registry.md,
    /codex/14-customer-journeys/audiences-and-journeys.md,
    /codex/14-customer-journeys/authentication/README.md,
    /codex/14-customer-journeys/authentication/firebase-production.md,
    /codex/14-customer-journeys/authentication/firebase-staging.md,
    /codex/14-customer-journeys/information-architecture.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Visibility slicing — the core model

> **SSOT.** This file carries the visibility-slicing model. Rule 06 (show / don't-show discipline) and demo-ops docs
> cite this file; they do not restate the mechanism. The filter function `visible(user, item)` below is the canonical
> definition.

This is the cross-cutting mechanism that ties authentication × entitlements × catalogue lock-state × catalogue maturity
into one filter function applied uniformly across the UI. Admin sees everything. Demo personas see a sliced subset. Prod
users see the subset their entitlements unlock.

## The rule

```
visible(user, item) :=
    user.role == "admin"
  OR
    (item.audience ⊇ user.role)
    AND (item.entitlement ⊆ user.entitlements)
    AND (item.lock_state is visible to user.role)
    AND (item.maturity ≥ user.role's minimum)
    AND (item.org_scope is null OR item.org_scope == user.org_id)
```

Applied uniformly to:

- Service cards on `/dashboard`
- Tabs in `service-tabs.tsx`
- Catalogue entries in each of the 4 catalogue surfaces
- Admin surfaces (only admin role)
- Individual sub-pages within a service
- Data rows within a table (e.g. trade blotter filtered by client)

## The four slicing dimensions

### 1. Role

- `admin` — sees EVERYTHING
- `internal` — Odum internal desk; full platform, no admin surfaces
- `client` — external client; sees their entitled slice only

### 2. Entitlements

Defined in [lib/config/auth.ts](unified-trading-system-ui/lib/config/auth.ts):

- Base entitlements: `data-basic`, `data-pro`, `execution-basic`, `execution-full`, `ml-full`, `strategy-full`,
  `reporting`, `investor-relations`
- Domain entitlements with tiers:
  `{ domain: "trading-common" | "trading-defi" | "trading-sports" | "trading-options" | "trading-predictions", tier: "basic" | "premium" }`
- Wildcard: `"*"` (admin only)

### 3. Lock state (catalogue entries)

Per [catalogue-strategy.md](catalogue-strategy.md), entries carry:

- `PUBLIC` — visible to all entitled users
- `IM_RESERVED` — visible only to IM desk (Odum internal) + admin
- `CLIENT_EXCLUSIVE` — visible only to the exclusive client + admin
- `RETIRED` — visible only to admin (archival)

### 4. Maturity (catalogue entries)

8-stage ladder. External-visibility threshold = `maturity ≥ BACKTESTED`:

- CODE_NOT_WRITTEN, CODE_WRITTEN, CODE_AUDITED — internal only
- BACKTESTED, PAPER_TRADING, PAPER_TRADING_VALIDATED — external visible
- LIVE_TINY, LIVE_ALLOCATED — external visible with extra metadata

## Implementation plan

Currently spread across multiple files (per static audit):

- [lib/config/auth.ts](unified-trading-system-ui/lib/config/auth.ts) — entitlement definitions
- [components/shell/lifecycle-nav.tsx:102-113](unified-trading-system-ui/components/shell/lifecycle-nav.tsx#L102) —
  hardcoded per-service entitlement map
- [lib/auth/demo-provider.ts:111-116](unified-trading-system-ui/lib/auth/demo-provider.ts) — `hasEntitlement()` wildcard
  handling
- Phase 10.5 (shipped) — UAC `slots_visible_to(role)` helper for strategy catalogue

**Gap — unification:** these checks are fragmented. The visibility-slicing target state is ONE function
`visible(user, item)` usable from any component. Implementation tracked in
[../roadmap/next-waves.md](../roadmap/next-waves.md).

## Per-role slicing examples

### Admin (entitlements = `["*"]`)

Sees every service tile, every tab, every catalogue entry across all lock states and maturities. No filtering.

### Real client — full IM subscription

```
entitlements: ["data-pro", "execution-full", "ml-full", "strategy-full", "reporting", {"domain": "trading-common", "tier": "premium"}, ...]
```

- ✅ Sees: data + research + promote + trading + observe + reports + optionally IR
- ❌ Doesn't see: admin surfaces, manage (internal-only), CODE_NOT_WRITTEN strategies, IM_RESERVED strategies,
  CLIENT_EXCLUSIVE strategies owned by other clients
- ✅ Sees: strategy catalogue filtered to PUBLIC + BACKTESTED+ entries

### Real client — data-only

```
entitlements: ["data-basic"]
```

- ✅ Sees: data service (limited to 180 instruments, CEFI only)
- ❌ Doesn't see: all other services (hidden OR locked-visible per UI decision)

### Demo prospect — pb3a/b (Reg Umbrella / IM flavour)

```
entitlements: ["reporting", "investor-relations"?]
```

- ✅ Sees: reports service
- LOCKED-VISIBLE: all other services (per user directive — show as padlocked tile with CTA, NOT hidden)

### Demo prospect — pb3c (DART flavour)

```
entitlements: ["data-pro", "strategy-full", "ml-full", "execution-full", {domain:"trading-*", tier:"premium"}]
```

- ✅ Sees: data, research, promote, trading, observe, strategy-catalogue, ML catalogue, execution-algo catalogue
- ❌ Doesn't see: admin

## Tests

`tests/playbooks/visibility-slicing.spec.ts` — parameterised over all personas, asserts the visible set matches the
expected entitlement × role × lock_state × maturity matrix. Single source of truth for "what does persona X see".

## Dashboard 5-tile grid + sub-route chip slicing (2026-04-21 addendum)

The `/dashboard` surface applies the same `visible(user, item)` rule at two granularities: **tile level** (which of the
5 product tiles render — DART · Odum Signals · Reports · Investor Relations · Admin & Ops) and **sub-route chip level**
(which chips render under each unlocked tile). Tile visibility is resolved via
`lib/auth/persona-dashboard-shape.ts → personaDashboardShape()`; chip visibility via `personaDashboardSubRoutes()`. Both
return a `visible | locked | hidden` triple per item, feeding the same three-state `<ServiceTile>` primitive used for
admin-locked surfaces. The 19-persona × 5-tile × N-chip matrix is the SSOT at
[`/codex/09-strategy/architecture-v2/dashboard-services-grid.md`](../../09-strategy/architecture-v2/dashboard-services-grid.md)
§3 — visibility-slicing.md remains the canonical rule; dashboard-services-grid.md is the per-surface instantiation.

## Related

- Catalogues umbrella: [catalogues.md](catalogues.md)
- Strategy catalogue lock + maturity: [catalogue-strategy.md](catalogue-strategy.md)
- Fund/org hierarchy (feeds into user.org_id): [fund-org-hierarchy.md](fund-org-hierarchy.md)
- UAC `slots_visible_to` helper (Phase 10.5): MEMORY.md "Phase 10.5 backend shipped"
- Dashboard 5-tile grid:
  [../../09-strategy/architecture-v2/dashboard-services-grid.md](../../09-strategy/architecture-v2/dashboard-services-grid.md)
- Roadmap for unification: [../roadmap/next-waves.md](../roadmap/next-waves.md)

---
scope: [engineer, admin, sales]
---

# Visibility slicing — the core model

This is **THE** cross-cutting mechanism that ties authentication × entitlements × catalogue lock-state × catalogue
maturity into ONE filter function applied uniformly across the UI.

> User quote: "We should always have the ability to see everything in the admin login, right? Sliced it down for what we
> want to show them in the demo; what we want them to use, obviously, in Prod, we'll slice it down based on what they've
> actually paid for, right? So that's the same for all of those dimensions, right? Which actual service types you see
> and also what you see within things."

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

## Related

- Catalogues umbrella: [catalogues.md](catalogues.md)
- Strategy catalogue lock + maturity: [catalogue-strategy.md](catalogue-strategy.md)
- Fund/org hierarchy (feeds into user.org_id): [fund-org-hierarchy.md](fund-org-hierarchy.md)
- UAC `slots_visible_to` helper (Phase 10.5): MEMORY.md "Phase 10.5 backend shipped"
- Roadmap for unification: [../roadmap/next-waves.md](../roadmap/next-waves.md)
